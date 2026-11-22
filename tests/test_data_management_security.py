import io
import os
import tempfile
import unittest
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.models import Category, Region, Product, Customer, Order, OrderItem, DataUpload
from tests.asgi_client import ASGITestClient


class TestDataManagementSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database for tests
        cls.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = cls.temp_db_file.name
        cls.temp_db_file.close()

        cls.test_engine = create_engine(
            f"sqlite:///{cls.temp_db_path}",
            connect_args={"check_same_thread": False}
        )
        cls.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.test_engine)

        # Create all tables in the isolated test DB
        Base.metadata.create_all(bind=cls.test_engine)

        # Seed minimal reference data
        db = cls.TestSessionLocal()
        try:
            cat = Category(name="Cloud & Infrastructure", code="CAT-CLOUD", description="Cloud solutions")
            db.add(cat)
            db.flush()

            region = Region(name="North America - Central", code="REG-NA-C", country="United States")
            db.add(region)
            db.flush()

            prod = Product(
                category_id=cat.id,
                sku="PRD-CLD-01",
                name="Dedicated Kubernetes Cluster",
                unit_price=1499.0,
                unit_cost=720.0,
                target_margin=52.0,
                is_active=True
            )
            db.add(prod)

            prod2 = Product(
                category_id=cat.id,
                sku="PRD-CLD-02",
                name="Object Storage Node",
                unit_price=450.0,
                unit_cost=180.0,
                target_margin=60.0,
                is_active=True
            )
            db.add(prod2)

            cust = Customer(
                customer_code="CUST-00001",
                name="Alpha Systems",
                email="admin@alphasys.com",
                segment="Enterprise",
                region_id=region.id
            )
            db.add(cust)
            db.flush()

            # Existing order to test duplicate conflict
            existing_order = Order(
                order_number="ORD-EXISTING-001",
                customer_id=cust.id,
                region_id=region.id,
                order_date=datetime(2026, 1, 15, 10, 0, 0),
                status="Completed",
                payment_method="Credit Card",
                shipping_cost=0.0,
                total_gross_amount=1499.0,
                total_discount_amount=0.0,
                total_refund_amount=0.0,
                total_net_amount=1499.0
            )
            db.add(existing_order)
            db.commit()
        finally:
            db.close()

        # Override get_db dependency to point to the isolated test database
        def override_get_db():
            test_db = cls.TestSessionLocal()
            try:
                yield test_db
            finally:
                test_db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = ASGITestClient(app)

    @classmethod
    def tearDownClass(cls):
        # Remove dependency override
        app.dependency_overrides.pop(get_db, None)
        cls.test_engine.dispose()
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # 1. Ingestion Pipeline & Validation Tests
    # -------------------------------------------------------------------------
    def test_valid_csv_upload_and_ingestion(self):
        csv_content = (
            "order_number,order_date,customer_code,product_sku,quantity,unit_price,discount_amount\n"
            "ORD-NEW-101,2026-06-01,CUST-00001,PRD-CLD-01,2,1499.0,100.0\n"
            "ORD-NEW-101,2026-06-01,CUST-00001,PRD-CLD-02,1,450.0,0.0\n"
        ).encode("utf-8")

        # 1. Pre-upload validation
        res_val = self.client.post_file("/api/data/validate", filename="batch_orders.csv", file_bytes=csv_content)
        self.assertEqual(res_val.status_code, 200)
        val_data = res_val.json()
        self.assertEqual(val_data["total_rows"], 2)
        self.assertEqual(val_data["valid_rows"], 2)
        self.assertEqual(val_data["invalid_rows"], 0)
        self.assertEqual(len(val_data["missing_columns"]), 0)
        self.assertGreaterEqual(val_data["quality_score"], 90.0)

        # 2. Upload and atomic ingestion
        res_up = self.client.post_file("/api/data/upload", filename="batch_orders.csv", file_bytes=csv_content)
        self.assertEqual(res_up.status_code, 200)
        up_data = res_up.json()
        self.assertTrue(up_data["success"])
        self.assertEqual(up_data["orders_ingested"], 1)
        self.assertEqual(up_data["items_ingested"], 2)

        # 3. Verify record was stored in isolated DB
        db = self.TestSessionLocal()
        saved_order = db.query(Order).filter(Order.order_number == "ORD-NEW-101").first()
        self.assertIsNotNone(saved_order)
        self.assertEqual(len(saved_order.items), 2)
        self.assertEqual(saved_order.total_gross_amount, 3448.0) # (2*1499) + (1*450)
        self.assertEqual(saved_order.total_discount_amount, 100.0)
        db.close()

    def test_valid_excel_upload(self):
        # Create Excel file in-memory using openpyxl
        df = pd.DataFrame([
            {
                "order_number": "ORD-XLS-201",
                "order_date": "2026-06-15",
                "customer_code": "CUST-00001",
                "product_sku": "PRD-CLD-01",
                "quantity": 1,
                "unit_price": 1499.0,
                "discount_amount": 0.0
            }
        ])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        excel_bytes = buffer.getvalue()

        res = self.client.post_file(
            "/api/data/upload",
            filename="quarterly_data.xlsx",
            file_bytes=excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["items_ingested"], 1)

    def test_invalid_file_extension_rejected(self):
        script_bytes = b"print('malicious file')"
        res = self.client.post_file(
            "/api/data/validate",
            filename="payload.py",
            file_bytes=script_bytes,
            content_type="text/plain"
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Unsupported file format", res.json()["detail"])

    def test_oversized_file_rejected(self):
        # Create bytes exceeding 10MB limit (10MB + 1KB)
        oversized_bytes = b"0" * (10 * 1024 * 1024 + 1024)
        res = self.client.post_file(
            "/api/data/validate",
            filename="massive_dump.csv",
            file_bytes=oversized_bytes
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("File size exceeds maximum allowed limit", res.json()["detail"])

    def test_missing_required_columns(self):
        csv_content = (
            "order_number,order_date,quantity\n"
            "ORD-BAD-01,2026-01-01,5\n"
        ).encode("utf-8")

        res = self.client.post_file("/api/data/validate", filename="missing_cols.csv", file_bytes=csv_content)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["valid_rows"], 0)
        self.assertIn("customer_code", data["missing_columns"])
        self.assertIn("product_sku", data["missing_columns"])
        self.assertIn("unit_price", data["missing_columns"])
        self.assertEqual(data["quality_score"], 0.0)

    def test_invalid_numeric_values(self):
        csv_content = (
            "order_number,order_date,customer_code,product_sku,quantity,unit_price,discount_amount\n"
            "ORD-NEG-01,2026-01-01,CUST-00001,PRD-CLD-01,-2,1499.0,0.0\n"
            "ORD-NEG-02,2026-01-01,CUST-00001,PRD-CLD-01,1,-500.0,0.0\n"
        ).encode("utf-8")

        res = self.client.post_file("/api/data/validate", filename="negative_vals.csv", file_bytes=csv_content)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["valid_rows"], 0)
        self.assertEqual(data["invalid_rows"], 2)
        self.assertGreater(len(data["row_errors"]), 0)

    def test_duplicate_records_detection(self):
        csv_content = (
            "order_number,order_date,customer_code,product_sku,quantity,unit_price,discount_amount\n"
            "ORD-DUP-01,2026-01-01,CUST-00001,PRD-CLD-01,1,1499.0,0.0\n"
            "ORD-DUP-01,2026-01-01,CUST-00001,PRD-CLD-01,1,1499.0,0.0\n"  # Duplicate in file
            "ORD-EXISTING-001,2026-01-15,CUST-00001,PRD-CLD-01,1,1499.0,0.0\n" # Duplicate in DB
        ).encode("utf-8")

        res = self.client.post_file("/api/data/validate", filename="duplicates.csv", file_bytes=csv_content)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["duplicate_rows"], 0)
        self.assertGreater(data["invalid_rows"], 0)

    def test_foreign_key_failures(self):
        csv_content = (
            "order_number,order_date,customer_code,product_sku,quantity,unit_price,discount_amount\n"
            "ORD-FK-01,2026-01-01,CUST-NONEXISTENT,PRD-CLD-01,1,1499.0,0.0\n"
            "ORD-FK-02,2026-01-01,CUST-00001,PRD-NONEXISTENT,1,1499.0,0.0\n"
        ).encode("utf-8")

        res = self.client.post_file("/api/data/validate", filename="fk_fails.csv", file_bytes=csv_content)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["valid_rows"], 0)
        errors_str = str(data["row_errors"])
        self.assertIn("Customer code 'CUST-NONEXISTENT' does not exist", errors_str)
        self.assertIn("Product SKU 'PRD-NONEXISTENT' does not exist", errors_str)

    def test_upload_history_recorded(self):
        # Create an upload first
        db = self.TestSessionLocal()
        record = DataUpload(
            filename="audit_sample.csv",
            rows_count=10,
            valid_rows=10,
            invalid_rows=0,
            duplicate_rows=0,
            status="Completed",
            summary_notes="Initial baseline test"
        )
        db.add(record)
        db.commit()
        db.close()

        res = self.client.get("/api/data/history")
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertIn("filename", history[0])
        self.assertIn("status", history[0])

    # -------------------------------------------------------------------------
    # 2. SQL Query Runner Security Tests
    # -------------------------------------------------------------------------
    def test_sql_runner_safe_select(self):
        res = self.client.post("/api/data/execute-sql", json={"query": "SELECT name, code FROM categories;"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("rows", data)
        self.assertIn("columns", data)
        self.assertIn("execution_time_ms", data)
        self.assertGreater(len(data["rows"]), 0)

    def test_sql_runner_safe_cte(self):
        query = (
            "WITH cat_summary AS (\n"
            "    SELECT code, name FROM categories\n"
            ")\n"
            "SELECT * FROM cat_summary;"
        )
        res = self.client.post("/api/data/execute-sql", json={"query": query})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data["rows"]), 0)

    def test_sql_runner_blocks_drop_table(self):
        res = self.client.post("/api/data/execute-sql", json={"query": "DROP TABLE categories;"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("DROP", res.json()["detail"])

    def test_sql_runner_blocks_delete(self):
        res = self.client.post("/api/data/execute-sql", json={"query": "DELETE FROM orders WHERE id = 1;"})
        self.assertEqual(res.status_code, 403)

    def test_sql_runner_blocks_update(self):
        res = self.client.post("/api/data/execute-sql", json={"query": "UPDATE orders SET total_net_amount = 0;"})
        self.assertEqual(res.status_code, 403)

    def test_sql_runner_blocks_insert(self):
        res = self.client.post(
            "/api/data/execute-sql",
            json={"query": "INSERT INTO categories (name, code) VALUES ('Bad', 'BAD');"}
        )
        self.assertEqual(res.status_code, 403)

    def test_sql_runner_blocks_alter(self):
        res = self.client.post(
            "/api/data/execute-sql",
            json={"query": "ALTER TABLE orders ADD COLUMN back_door text;"}
        )
        self.assertEqual(res.status_code, 403)

    def test_sql_runner_blocks_multi_statement(self):
        res = self.client.post(
            "/api/data/execute-sql",
            json={"query": "SELECT * FROM categories; DROP TABLE orders;"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Multi-statement execution is strictly prohibited", res.json()["detail"])

    def test_sql_runner_blocks_comment_bypass(self):
        res = self.client.post(
            "/api/data/execute-sql",
            json={"query": "SELECT 1; -- inline comment\nDROP TABLE orders;"}
        )
        self.assertEqual(res.status_code, 403)

    def test_sql_runner_blocks_internal_sqlite_master(self):
        res = self.client.post(
            "/api/data/execute-sql",
            json={"query": "SELECT * FROM sqlite_master;"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access to internal database catalog", res.json()["detail"])

    def test_sql_runner_blocks_pragma(self):
        res = self.client.post(
            "/api/data/execute-sql",
            json={"query": "PRAGMA table_info(orders);"}
        )
        self.assertEqual(res.status_code, 403)

    # -------------------------------------------------------------------------
    # 3. Reseed Safeguard Tests
    # -------------------------------------------------------------------------
    def test_reseed_without_confirmation_rejected(self):
        res = self.client.post("/api/data/reseed-sample-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("requires explicit confirmation parameter", res.json()["detail"])

    def test_reseed_empty_body_rejected(self):
        res = self.client.post("/api/data/reseed-sample-data", json={})
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
