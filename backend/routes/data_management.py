from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import io
from datetime import datetime
from backend.database import get_db
from backend.models import DataUpload, Order, OrderItem, Product, Customer, Region, Category
from backend.seed_data import seed_database

router = APIRouter(prefix="/data", tags=["Data Management"])

REQUIRED_COLUMNS = [
    "order_number", "order_date", "customer_code", "product_sku",
    "quantity", "unit_price", "discount_amount"
]

@router.post("/validate")
async def validate_dataset(file: UploadFile = File(...)):
    """Pre-upload validation: checks schema, types, missing values, duplicates, and returns quality report."""
    contents = await file.read()
    filename = file.filename or "uploaded_data.csv"

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    total_rows = len(df)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    missing_counts = df.isnull().sum().to_dict()
    missing_total = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    # Check for invalid rows (e.g. negative prices or negative quantities)
    invalid_rows = 0
    if "quantity" in df.columns:
        invalid_rows += int((df["quantity"] <= 0).sum())
    if "unit_price" in df.columns:
        invalid_rows += int((df["unit_price"] <= 0).sum())

    valid_rows = max(0, total_rows - duplicate_rows - invalid_rows)
    
    # Calculate Data Quality Score (0 - 100%)
    penalty = (missing_total * 2 + duplicate_rows * 5 + invalid_rows * 10)
    score = max(0.0, round(100.0 - (penalty / max(1, total_rows) * 10.0), 1))

    preview_records = df.head(10).replace({np.nan: None}).to_dict(orient="records")

    return {
        "filename": filename,
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
        "missing_columns": missing_cols,
        "missing_values": {k: int(v) for k, v in missing_counts.items() if v > 0},
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "quality_score": score,
        "preview": preview_records
    }

@router.post("/upload")
async def upload_and_import_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parses, validates, and stores upload history metadata."""
    validation = await validate_dataset(file)

    upload_record = DataUpload(
        filename=validation["filename"],
        rows_count=validation["total_rows"],
        valid_rows=validation["valid_rows"],
        invalid_rows=validation["invalid_rows"],
        duplicate_rows=validation["duplicate_rows"],
        status="Completed",
        summary_notes=f"Data Quality Score: {validation['quality_score']}%. Validated {validation['valid_rows']} clean rows."
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)

    return {
        "success": True,
        "upload_id": upload_record.id,
        "summary": validation
    }

@router.get("/history")
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

@router.post("/reseed-sample-data")
def trigger_reseed(db: Session = Depends(get_db)):
    """Allows one-click regenerating of the 5,200 synthetic enterprise orders."""
    seed_database(target_orders=5200, force_recreate=True)
    return {"message": "Database reseeded successfully with 5,200 enterprise transactions."}

@router.post("/execute-sql")
def execute_custom_sql(
    payload: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Executes analytical SQL queries from the UI Query Runner."""
    query = payload.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="SQL query cannot be empty.")
    
    # Read-only guard
    low_q = query.lower()
    for forbidden in ["drop", "delete", "truncate", "update", "insert", "alter"]:
        if low_q.startswith(forbidden) or f" {forbidden} " in low_q:
            raise HTTPException(status_code=403, detail="Only SELECT and WITH analytical queries are permitted.")

    try:
        result = db.execute(text(query)).mappings().all()
        rows = [dict(r) for r in result[:100]] # Limit to 100 rows for display
        columns = list(rows[0].keys()) if rows else []
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {str(e)}")

