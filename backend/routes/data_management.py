import time
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import get_db
from backend.models import DataUpload
from backend.seed_data import seed_database
from backend.security.sql_guard import (
    validate_and_sanitize_sql, SQLSecurityException, execute_read_only_sql
)
from backend.data_pipeline import (
    parse_upload_file, validate_dataframe, ingest_valid_records,
    IngestionError, MAX_FILE_SIZE, MAX_ROW_COUNT, ALLOWED_EXTENSIONS
)
from backend.auth.dependencies import require_permission, get_current_user
from backend.auth.rbac import Permission
from backend.auth.audit import log_audit_event, AuditEvent
from backend.models import User

router = APIRouter(prefix="/data", tags=["Data Management"])


@router.post("/validate", dependencies=[Depends(require_permission(Permission.MANAGE_DATA))])
async def validate_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Pre-upload validation: checks schema, MIME types, file size, foreign keys,
    data types, missing values, duplicates, and returns a comprehensive quality report.
    """
    filename = file.filename or "uploaded_dataset.csv"
    contents = await file.read()

    try:
        df = parse_upload_file(filename, contents, file.content_type)
        report = validate_dataframe(df, db, filename)
        return report
    except IngestionError as ie:
        raise HTTPException(status_code=ie.status_code, detail=ie.message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")


@router.post("/upload", dependencies=[Depends(require_permission(Permission.MANAGE_DATA))])
async def upload_and_import_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parses, validates, and atomically ingests valid records into the database.
    Rolls back transaction on failure and records upload status in data_uploads.
    """
    filename = file.filename or "uploaded_dataset.csv"
    contents = await file.read()

    try:
        df = parse_upload_file(filename, contents, file.content_type)
        validation = validate_dataframe(df, db, filename)

        if validation["valid_rows"] == 0 or validation["missing_columns"]:
            err_msg = validation["errors"][0] if validation["errors"] else "No valid records found in dataset."
            # Record failed upload in audit log
            failed_upload = DataUpload(
                filename=filename,
                rows_count=validation["total_rows"],
                valid_rows=0,
                invalid_rows=validation["invalid_rows"],
                duplicate_rows=validation["duplicate_rows"],
                status="Failed",
                summary_notes=f"Validation failed: {err_msg}"
            )
            db.add(failed_upload)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Upload rejected: {err_msg}")

        # Ingest valid records within an atomic database transaction
        result = ingest_valid_records(df, validation["valid_indices"], db, filename)

        log_audit_event(
            AuditEvent.PRIVILEGED_DATA_OPERATION,
            actor_id=current_user.id,
            actor_email=current_user.email,
            action="DATA_UPLOAD",
            status="SUCCESS",
            details={
                "filename": filename,
                "orders_ingested": result.get("orders_ingested", 0),
                "items_ingested": result.get("items_ingested", 0)
            }
        )

        return {
            "success": True,
            "upload_id": result["upload_id"],
            "orders_ingested": result["orders_ingested"],
            "items_ingested": result["items_ingested"],
            "message": result["message"],
            "summary": {
                "filename": validation["filename"],
                "total_rows": validation["total_rows"],
                "valid_rows": validation["valid_rows"],
                "invalid_rows": validation["invalid_rows"],
                "duplicate_rows": validation["duplicate_rows"],
                "missing_columns": validation["missing_columns"],
                "missing_values": validation["missing_values"],
                "column_types": validation["column_types"],
                "quality_score": validation["quality_score"],
                "preview": validation["preview"]
            }
        }
    except IngestionError as ie:
        raise HTTPException(status_code=ie.status_code, detail=ie.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ingestion error: {str(e)}")


@router.get("/history", dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS))])
def get_upload_history(db: Session = Depends(get_db)):
    """Retrieves dataset upload logs and historical processing statuses."""
    uploads = db.query(DataUpload).order_by(DataUpload.upload_date.desc()).all()
    return [
        {
            "id": u.id,
            "filename": u.filename,
            "rows_count": u.rows_count,
            "valid_rows": u.valid_rows,
            "invalid_rows": u.invalid_rows,
            "duplicate_rows": u.duplicate_rows,
            "status": u.status,
            "upload_date": u.upload_date.strftime("%Y-%m-%d %H:%M:%S") if u.upload_date else "",
            "summary_notes": u.summary_notes
        }
        for u in uploads
    ]


@router.post("/reseed-sample-data", dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))])
def trigger_reseed(
    confirm: bool = Query(False, description="Explicit confirmation required for destructive demonstration reset"),
    payload: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely regenerates the demonstration database.
    Requires explicit confirmation via query parameter (?confirm=true) or JSON body ({'confirm': true})
    to prevent accidental destruction of business records.
    """
    is_confirmed = confirm
    if payload and isinstance(payload, dict):
        if payload.get("confirm") is True or payload.get("confirm_reset") is True:
            is_confirmed = True

    if not is_confirmed:
        raise HTTPException(
            status_code=400,
            detail=(
                "Destructive operation rejected: Reseeding sample data requires "
                "explicit confirmation parameter 'confirm=true'. This safeguards "
                "existing user-uploaded records from accidental destruction."
            )
        )

    # Authorized confirmed reseed
    seed_database(target_orders=5200, force_recreate=True)

    log_audit_event(
        AuditEvent.PRIVILEGED_DATA_OPERATION,
        actor_id=current_user.id,
        actor_email=current_user.email,
        action="SYSTEM_RESEED",
        status="SUCCESS",
        details={"target_orders": 5200}
    )

    return {
        "success": True,
        "message": "Database reseeded successfully with 5,200 enterprise transactions."
    }


@router.post("/execute-sql", dependencies=[Depends(require_permission(Permission.EXECUTE_SQL))])
def execute_custom_sql(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes analytical SQL queries from the UI Query Runner.
    Enforces strict read-only execution:
      - Only SELECT and WITH/CTE queries are permitted.
      - Multiple statements (stacked queries) are rejected.
      - Modifying, administrative, and internal table accesses are blocked.
      - Query execution time and max row limits are enforced.
    """
    query = payload.get("query", "") if isinstance(payload, dict) else ""
    if not isinstance(query, str) or not query.strip():
        raise HTTPException(status_code=400, detail="SQL query cannot be empty.")

    start_time = time.time()
    try:
        columns, rows = execute_read_only_sql(db, query, max_rows=1000)
        exec_time_ms = round((time.time() - start_time) * 1000, 2)

        log_audit_event(
            AuditEvent.PRIVILEGED_DATA_OPERATION,
            actor_id=current_user.id,
            actor_email=current_user.email,
            action="EXECUTE_SQL",
            status="SUCCESS",
            details={
                "query_length": len(query),
                "rows_returned": len(rows),
                "execution_time_ms": exec_time_ms
            }
        )

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": exec_time_ms
        }
    except SQLSecurityException as se:
        raise HTTPException(status_code=403, detail=str(se))
    except Exception as e:
        clean_error = str(e).split("\n")[0].strip()
        if "not authorized" in clean_error.lower() or "prohibited" in clean_error.lower():
            raise HTTPException(
                status_code=403,
                detail=f"Security violation: {clean_error}"
            )
        if "[SQL:" in clean_error:
            clean_error = clean_error.split("[SQL:")[0].strip()
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {clean_error}")
