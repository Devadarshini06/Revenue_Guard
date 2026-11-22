import io
import math
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models import (
    DataUpload, Order, OrderItem, Product, Customer, Region,
    Discount, Refund, Transaction
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ROW_COUNT = 50000
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}

REQUIRED_COLUMNS = [
    "order_number", "order_date", "customer_code", "product_sku",
    "quantity", "unit_price", "discount_amount"
]


class IngestionError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def parse_upload_file(filename: str, contents: bytes, content_type: Optional[str] = None) -> pd.DataFrame:
    """
    Validates file extension, size, and content type, then parses into a pandas DataFrame.
    """
    if len(contents) > MAX_FILE_SIZE:
        raise IngestionError(
            f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
            status_code=400
        )

    # Validate file extension
    lower_name = (filename or "").lower()
    ext = next((e for e in ALLOWED_EXTENSIONS if lower_name.endswith(e)), None)
    if not ext:
        raise IngestionError(
            f"Unsupported file format '{filename}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}.",
            status_code=400
        )

    # Validate MIME type if provided
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise IngestionError(
            f"Invalid content type '{content_type}'. Must be a valid CSV or Excel spreadsheet.",
            status_code=400
        )

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
    except Exception as e:
        raise IngestionError(f"Failed to parse file: {str(e)}", status_code=400)

    if len(df) > MAX_ROW_COUNT:
        raise IngestionError(
            f"Row count ({len(df)}) exceeds maximum limit of {MAX_ROW_COUNT} rows.",
            status_code=400
        )

    return df


def validate_dataframe(df: pd.DataFrame, db: Session, filename: str) -> Dict[str, Any]:
    """
    Performs comprehensive schema, foreign key, numeric, date, and duplicate validation.
    Returns structured validation report including row-level errors and quality score.
    """
    total_rows = len(df)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_cols:
        return {
            "filename": filename,
            "total_rows": total_rows,
            "valid_rows": 0,
            "invalid_rows": total_rows,
            "duplicate_rows": 0,
            "missing_columns": missing_cols,
            "missing_values": {},
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "quality_score": 0.0,
            "errors": [f"Missing required columns: {', '.join(missing_cols)}"],
            "row_errors": [],
            "preview": []
        }

    # Pre-fetch lookup dictionaries for FK validation
    catalog_products = {p.sku: p for p in db.query(Product).all()}
    catalog_customers = {c.customer_code: c for c in db.query(Customer).all()}
    existing_orders = set(r[0] for r in db.query(Order.order_number).all())

    missing_counts = df[REQUIRED_COLUMNS].isnull().sum().to_dict()
    missing_total = int(sum(missing_counts.values()))

    # Track duplicates within file
    file_duplicates = int(df.duplicated(subset=["order_number", "product_sku"]).sum())

    row_errors = []
    valid_indices = []
    seen_order_items = set()

    for idx, row in df.iterrows():
        errors_for_row = []
        row_num = idx + 1

        # 1. Null check on required fields
        for col in REQUIRED_COLUMNS:
            val = row.get(col)
            if pd.isna(val) or val is None or (isinstance(val, str) and not val.strip()):
                errors_for_row.append(f"Missing required value for '{col}'.")

        if errors_for_row:
            row_errors.append({"row": row_num, "errors": errors_for_row})
            continue

        order_num = str(row["order_number"]).strip()
        sku = str(row["product_sku"]).strip()
        cust_code = str(row["customer_code"]).strip()

        # 2. Duplicate within file
        item_key = (order_num, sku)
        if item_key in seen_order_items:
            errors_for_row.append(f"Duplicate order item (order: '{order_num}', sku: '{sku}') in file.")
        else:
            seen_order_items.add(item_key)

        # 3. Existing order conflict in DB
        if order_num in existing_orders:
            errors_for_row.append(f"Order '{order_num}' already exists in database.")

        # 4. Foreign Key validation
        if sku not in catalog_products:
            errors_for_row.append(f"Product SKU '{sku}' does not exist in catalog.")

        if cust_code not in catalog_customers:
            errors_for_row.append(f"Customer code '{cust_code}' does not exist in database.")

        # 5. Numeric validations
        try:
            qty = float(row["quantity"])
            if qty <= 0 or not qty.is_integer():
                errors_for_row.append(f"Quantity must be a positive integer (> 0), got '{row['quantity']}'.")
        except (ValueError, TypeError):
            errors_for_row.append(f"Invalid numeric format for quantity: '{row['quantity']}'.")

        try:
            price = float(row["unit_price"])
            if price <= 0:
                errors_for_row.append(f"Unit price must be greater than zero, got '{row['unit_price']}'.")
        except (ValueError, TypeError):
            errors_for_row.append(f"Invalid numeric format for unit_price: '{row['unit_price']}'.")

        try:
            discount = float(row.get("discount_amount", 0.0) or 0.0)
            if discount < 0:
                errors_for_row.append(f"Discount amount cannot be negative, got '{discount}'.")
            elif "unit_price" in row and "quantity" in row:
                gross = float(row["unit_price"]) * float(row["quantity"])
                if discount > gross:
                    errors_for_row.append(f"Discount (${discount:.2f}) exceeds gross amount (${gross:.2f}).")
        except (ValueError, TypeError):
            errors_for_row.append(f"Invalid numeric format for discount_amount: '{row.get('discount_amount')}'.")

        # 6. Date validation
        raw_date = str(row["order_date"])
        try:
            pd.to_datetime(raw_date)
        except Exception:
            errors_for_row.append(f"Invalid date format for order_date: '{raw_date}'.")

        if errors_for_row:
            row_errors.append({"row": row_num, "errors": errors_for_row})
        else:
            valid_indices.append(idx)

    invalid_rows = len(row_errors)
    valid_rows = len(valid_indices)

    # Data Quality Score calculation
    penalty = (missing_total * 2 + file_duplicates * 5 + invalid_rows * 10)
    score = max(0.0, round(100.0 - (penalty / max(1, total_rows) * 10.0), 1)) if total_rows > 0 else 0.0

    preview_records = (
        df.iloc[valid_indices[:10]]
        .replace({np.nan: None})
        .to_dict(orient="records")
        if valid_indices else []
    )

    return {
        "filename": filename,
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "duplicate_rows": file_duplicates,
        "missing_columns": missing_cols,
        "missing_values": {k: int(v) for k, v in missing_counts.items() if v > 0},
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "quality_score": score,
        "errors": [err["errors"][0] for err in row_errors[:10]],
        "row_errors": row_errors[:50],  # Return up to 50 row-level errors
        "valid_indices": valid_indices,
        "preview": preview_records
    }


def ingest_valid_records(df: pd.DataFrame, valid_indices: List[int], db: Session, filename: str) -> Dict[str, Any]:
    """
    Inserts validated records into the database in atomic transactions with batching.
    Rolls back on error and records ingestion audit trail in data_uploads.
    """
    if not valid_indices:
        raise IngestionError("Cannot import dataset: No valid records found.", status_code=400)

    # Filter to only valid rows
    valid_df = df.iloc[valid_indices].copy()

    catalog_products = {p.sku: p for p in db.query(Product).all()}
    catalog_customers = {c.customer_code: c for c in db.query(Customer).all()}

    # Group records by order_number
    orders_grouped = valid_df.groupby("order_number")

    created_orders = []
    created_order_items = []
    created_discounts = []
    created_refunds = []
    created_transactions = []

    try:
        for order_num, group in orders_grouped:
            first_row = group.iloc[0]
            cust = catalog_customers[str(first_row["customer_code"]).strip()]
            order_date = pd.to_datetime(first_row["order_date"]).to_pydatetime()

            payment_method = str(first_row.get("payment_method") or "Credit Card").strip()
            status = str(first_row.get("status") or "Completed").strip()
            shipping_cost = float(first_row.get("shipping_cost") or 0.0)

            # Accumulate totals
            total_gross = 0.0
            total_discount = 0.0
            total_refund = 0.0
            total_net = 0.0

            order_obj = Order(
                order_number=str(order_num).strip(),
                customer_id=cust.id,
                region_id=cust.region_id,
                order_date=order_date,
                status=status,
                payment_method=payment_method,
                shipping_cost=shipping_cost,
                total_gross_amount=0.0,
                total_discount_amount=0.0,
                total_refund_amount=0.0,
                total_net_amount=0.0
            )
            db.add(order_obj)
            db.flush()  # Generates order_obj.id

            for _, item_row in group.iterrows():
                prod = catalog_products[str(item_row["product_sku"]).strip()]
                qty = int(item_row["quantity"])
                unit_price = float(item_row["unit_price"])
                unit_cost = prod.unit_cost
                discount_amt = float(item_row.get("discount_amount") or 0.0)

                gross_rev = round(qty * unit_price, 2)
                net_rev = round(gross_rev - discount_amt, 2)
                cogs = round(qty * unit_cost, 2)
                profit = round(net_rev - cogs, 2)

                order_item_obj = OrderItem(
                    order_id=order_obj.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    discount_amount=discount_amt,
                    gross_revenue=gross_rev,
                    net_revenue=net_rev,
                    cogs=cogs,
                    profit=profit
                )
                db.add(order_item_obj)
                db.flush()

                # If discount exists, record in discounts table
                if discount_amt > 0:
                    disc_code = str(item_row.get("discount_code") or "UPLOAD_DISC").strip()
                    disc_type = str(item_row.get("discount_type") or "Percentage").strip()
                    pct = round((discount_amt * 100.0) / gross_rev, 2) if gross_rev > 0 else 0.0
                    disc_obj = Discount(
                        order_id=order_obj.id,
                        order_item_id=order_item_obj.id,
                        discount_code=disc_code,
                        discount_type=disc_type,
                        discount_percentage=pct,
                        discount_amount=discount_amt,
                        reason="Dataset Ingestion Discount"
                    )
                    db.add(disc_obj)

                # If refund exists, record in refunds table
                refund_amt = float(item_row.get("refund_amount") or 0.0)
                if refund_amt > 0:
                    refund_reason = str(item_row.get("refund_reason") or "Customer Request").strip()
                    ref_obj = Refund(
                        order_id=order_obj.id,
                        order_item_id=order_item_obj.id,
                        refund_date=order_date,
                        refund_amount=refund_amt,
                        refund_reason=refund_reason,
                        status="Approved"
                    )
                    db.add(ref_obj)
                    total_refund += refund_amt

                total_gross += gross_rev
                total_discount += discount_amt
                total_net += net_rev

            # Update Order totals
            order_obj.total_gross_amount = round(total_gross, 2)
            order_obj.total_discount_amount = round(total_discount, 2)
            order_obj.total_refund_amount = round(total_refund, 2)
            order_obj.total_net_amount = round(total_net - total_refund, 2)

            # Record Transaction
            tx_obj = Transaction(
                transaction_reference=f"TXN-{order_num}",
                order_id=order_obj.id,
                transaction_type="Charge",
                amount=round(total_net, 2),
                payment_method=payment_method,
                status="Settled",
                created_at=order_date
            )
            db.add(tx_obj)

        # Record upload audit log
        upload_record = DataUpload(
            filename=filename,
            rows_count=len(df),
            valid_rows=len(valid_indices),
            invalid_rows=len(df) - len(valid_indices),
            duplicate_rows=int(df.duplicated(subset=["order_number", "product_sku"]).sum()),
            status="Completed",
            summary_notes=f"Successfully ingested {len(valid_indices)} clean items across {len(orders_grouped)} orders."
        )
        db.add(upload_record)
        db.commit()

        return {
            "success": True,
            "upload_id": upload_record.id,
            "orders_ingested": len(orders_grouped),
            "items_ingested": len(valid_indices),
            "message": f"Dataset ingested successfully: {len(valid_indices)} items across {len(orders_grouped)} orders."
        }

    except Exception as e:
        db.rollback()
        # Record failure audit log
        try:
            fail_record = DataUpload(
                filename=filename,
                rows_count=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                duplicate_rows=0,
                status="Failed",
                summary_notes=f"Ingestion rollback due to error: {str(e)}"
            )
            db.add(fail_record)
            db.commit()
        except Exception:
            db.rollback()

        raise IngestionError(f"Database transaction rolled back. Ingestion error: {str(e)}", status_code=500)
