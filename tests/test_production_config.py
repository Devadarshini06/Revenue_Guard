"""
RevenueGuard Production Configuration, PostgreSQL Compatibility & Safety Test Suite
=====================================================================================
Validates production environment isolation, strict CORS wildcard rejection,
PostgreSQL query dialect adaptation, safe error handling, and robust
SQLite backup/restore safety under WAL mode with rollback verification.
"""

import os
import unittest
import tempfile
import sqlite3
import shutil
from unittest.mock import patch
from sqlalchemy import text
from sqlalchemy.dialects import postgresql, sqlite
from backend.config import Settings
from backend.database_backup import backup_sqlite, restore_sqlite, check_target_lock_and_concurrency
from backend.analytics.sql_queries import (
    get_query,
    MONTHLY_REVENUE_TREND_QUERY_SQLITE,
    MONTHLY_REVENUE_TREND_QUERY_POSTGRES,
    RECENT_TRANSACTIONS_QUERY_SQLITE,
    RECENT_TRANSACTIONS_QUERY_POSTGRES,
    KPI_SUMMARY_QUERY,
    PRODUCT_PERFORMANCE_QUERY,
    CATEGORY_PERFORMANCE_QUERY,
    REGIONAL_PERFORMANCE_QUERY,
    CUSTOMER_SEGMENTATION_QUERY,
    DISCOUNT_ANALYSIS_QUERY,
    REFUND_ANALYSIS_QUERY
)
from tests.asgi_client import ASGITestClient
from backend.main import app


class TestProductionConfiguration(unittest.TestCase):
    """Verifies strict production configuration behaviors."""

    def test_debug_disabled_in_production(self):
        """Confirm DEBUG is forced to False in production even if requested otherwise."""
        cfg = Settings({"ENVIRONMENT": "production", "DEBUG": "true"})
        self.assertFalse(cfg.DEBUG)

        cfg_dev = Settings({"ENVIRONMENT": "development", "DEBUG": "true"})
        self.assertTrue(cfg_dev.DEBUG)

    def test_wildcard_cors_rejected_in_production(self):
        """Confirm wildcard '*' in ALLOWED_ORIGINS raises ValueError and fails startup in production."""
        # Standalone wildcard
        cfg = Settings({"ENVIRONMENT": "production", "ALLOWED_ORIGINS": "*"})
        with self.assertRaises(ValueError) as ctx:
            _ = cfg.CORS_ORIGINS
        self.assertIn("Wildcard '*' in ALLOWED_ORIGINS is strictly prohibited in production mode", str(ctx.exception))

        # Wildcard embedded in allowlist
        cfg2 = Settings({"ENVIRONMENT": "production", "ALLOWED_ORIGINS": "https://analytics.corp.com, *"})
        with self.assertRaises(ValueError) as ctx2:
            _ = cfg2.CORS_ORIGINS
        self.assertIn("Wildcard '*' in ALLOWED_ORIGINS is strictly prohibited in production mode", str(ctx2.exception))

    def test_production_cors_allowlist_handling(self):
        """Confirm valid comma-separated production origins are parsed cleanly without wildcards."""
        cfg = Settings({
            "ENVIRONMENT": "production",
            "ALLOWED_ORIGINS": "https://dashboard.example.com, https://admin.example.com "
        })
        self.assertEqual(cfg.CORS_ORIGINS, ["https://dashboard.example.com", "https://admin.example.com"])

    def test_api_docs_disabled_by_default_in_production(self):
        """Confirm DOCS_ENABLED is False by default in production and True in dev."""
        prod_cfg = Settings({"ENVIRONMENT": "production"})
        self.assertFalse(prod_cfg.DOCS_ENABLED)

        dev_cfg = Settings({"ENVIRONMENT": "development"})
        self.assertTrue(dev_cfg.DOCS_ENABLED)

    def test_explicit_configuration_override(self):
        """Confirm DOCS_ENABLED can be explicitly overridden in production if needed."""
        override_cfg = Settings({"ENVIRONMENT": "production", "DOCS_ENABLED": "true"})
        self.assertTrue(override_cfg.DOCS_ENABLED)

    def test_missing_required_production_environment_variables(self):
        """Confirm validation identifies insecure/missing settings in production."""
        # Insecure default configuration
        insecure_cfg = Settings({"ENVIRONMENT": "production"})
        issues = insecure_cfg.validate_production_configuration()
        self.assertTrue(any("SECRET_KEY" in issue for issue in issues))
        self.assertTrue(any("ALLOWED_ORIGINS" in issue for issue in issues))

        # Properly hardened configuration
        hardened_cfg = Settings({
            "ENVIRONMENT": "production",
            "SECRET_KEY": "a-secure-random-token-exceeding-32-chars-long!",
            "ALLOWED_ORIGINS": "https://analytics.revenueguard.internal"
        })
        self.assertEqual(len(hardened_cfg.validate_production_configuration()), 0)

    def test_safe_database_connection_failure_handling(self):
        """Confirm readiness probe returns 503 without leaking connection strings on DB failure."""
        client = ASGITestClient(app)
        with patch("backend.main.engine.connect", side_effect=Exception("FATAL: connection to server on socket failed")):
            res = client.get("/api/health/ready")
            self.assertEqual(res.status_code, 503)
            data = res.json()
            self.assertEqual(data["status"], "unhealthy")
            self.assertEqual(data["database"], "disconnected")
            # Ensure sensitive database stack traces or credentials are not in response
            self.assertNotIn("FATAL", str(data))
            self.assertNotIn("socket", str(data))

    def test_no_sensitive_info_in_error_responses(self):
        """Confirm unhandled exceptions in production return generic error without stack trace."""
        client = ASGITestClient(app)
        with patch.object(Settings, "ENVIRONMENT", "production"), patch.object(Settings, "DEBUG", False):
            with patch("backend.analytics.engine.AnalyticsEngine.calculate_dashboard_kpis", side_effect=RuntimeError("Internal secret DB password leak")):
                res = client.get("/api/overview/kpis")
                self.assertEqual(res.status_code, 500)
                body = res.json()
                self.assertIn("detail", body)
                self.assertEqual(body["detail"], "Internal server error occurred.")
                self.assertIn("request_id", body)
                self.assertNotIn("Internal secret DB password leak", str(body))


class TestPostgreSQLQueryCompatibility(unittest.TestCase):
    """Verifies PostgreSQL and SQLite dialect query adaptation and compilation."""

    def test_monthly_trend_query_dialect_adaptation(self):
        """Confirm monthly revenue query adapts between SQLite substr and PostgreSQL TO_CHAR."""
        sqlite_query = get_query("MONTHLY_REVENUE_TREND_QUERY", dialect="sqlite")
        postgres_query = get_query("MONTHLY_REVENUE_TREND_QUERY", dialect="postgresql")

        self.assertIn("substr(o.order_date, 1, 7)", sqlite_query)
        self.assertIn("TO_CHAR(o.order_date, 'YYYY-MM')", postgres_query)

        # Verify SQLAlchemy compiles both variants
        sqlite_stmt = text(sqlite_query).compile(dialect=sqlite.dialect())
        postgres_stmt = text(postgres_query).compile(dialect=postgresql.dialect())
        self.assertIsNotNone(sqlite_stmt)
        self.assertIsNotNone(postgres_stmt)

    def test_recent_transactions_query_dialect_adaptation(self):
        """Confirm recent transactions query adapts between SQLite GROUP_CONCAT and PostgreSQL STRING_AGG."""
        sqlite_query = get_query("RECENT_TRANSACTIONS_QUERY", dialect="sqlite")
        postgres_query = get_query("RECENT_TRANSACTIONS_QUERY", dialect="postgresql")

        self.assertIn("GROUP_CONCAT(p.name, ', ')", sqlite_query)
        self.assertIn("STRING_AGG(p.name, ', ')", postgres_query)

        # Verify SQLAlchemy compiles both variants
        sqlite_stmt = text(sqlite_query).compile(dialect=sqlite.dialect())
        postgres_stmt = text(postgres_query).compile(dialect=postgresql.dialect())
        self.assertIsNotNone(sqlite_stmt)
        self.assertIsNotNone(postgres_stmt)

    def test_all_analytical_queries_compile_against_both_dialects(self):
        """Verifies that all 9 analytical queries compile with PostgreSQL and SQLite dialects."""
        query_names = [
            "KPI_SUMMARY_QUERY",
            "MONTHLY_REVENUE_TREND_QUERY",
            "PRODUCT_PERFORMANCE_QUERY",
            "CATEGORY_PERFORMANCE_QUERY",
            "REGIONAL_PERFORMANCE_QUERY",
            "CUSTOMER_SEGMENTATION_QUERY",
            "DISCOUNT_ANALYSIS_QUERY",
            "REFUND_ANALYSIS_QUERY",
            "RECENT_TRANSACTIONS_QUERY",
        ]
        for qname in query_names:
            q_sqlite = get_query(qname, dialect="sqlite")
            q_postgres = get_query(qname, dialect="postgresql")
            self.assertTrue(len(q_sqlite) > 0, f"{qname} SQLite query is empty")
            self.assertTrue(len(q_postgres) > 0, f"{qname} PostgreSQL query is empty")

            c_sqlite = text(q_sqlite).compile(dialect=sqlite.dialect())
            c_postgres = text(q_postgres).compile(dialect=postgresql.dialect())
            self.assertIsNotNone(c_sqlite)
            self.assertIsNotNone(c_postgres)


class TestBackupAndRestoreSafety(unittest.TestCase):
    """
    Verifies 6 mandatory backup and recovery scenarios on isolated databases:
    1. Successful backup and restore.
    2. Corrupt backup rejection.
    3. Active database use / lock handling.
    4. Failed restoration and recovery of original database.
    5. WAL/SHM handling.
    6. Safety-copy preservation.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.src_db = os.path.join(self.test_dir, "test_source.db")
        self.target_db = os.path.join(self.test_dir, "test_target.db")
        self.backup_dir = os.path.join(self.test_dir, "backups")

        # Create source DB with WAL mode
        conn = sqlite3.connect(self.src_db)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE orders (id INT, amount FLOAT)")
        conn.execute("INSERT INTO orders VALUES (101, 550.0), (102, 1200.0)")
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_successful_backup_and_restore(self):
        """Scenario 1: Confirm online backup under WAL writes and offline restore cycle."""
        # Hold an open connection writing to source to simulate active production writes
        conn_active = sqlite3.connect(self.src_db)
        conn_active.execute("INSERT INTO orders VALUES (103, 300.0)")
        conn_active.commit()

        backup_file = backup_sqlite(self.src_db, backup_dir=self.backup_dir)
        self.assertTrue(os.path.exists(backup_file))

        # Check integrity of backup
        b_conn = sqlite3.connect(backup_file)
        integrity = b_conn.execute("PRAGMA integrity_check").fetchone()[0]
        count = b_conn.execute("SELECT count(*) FROM orders").fetchone()[0]
        b_conn.close()
        conn_active.close()

        self.assertEqual(integrity.lower(), "ok")
        self.assertEqual(count, 3)

        # Restore into new target database
        restore_sqlite(backup_file, target_path=self.target_db)
        res_conn = sqlite3.connect(self.target_db)
        res_count = res_conn.execute("SELECT count(*) FROM orders").fetchone()[0]
        res_conn.close()
        self.assertEqual(res_count, 3)

    def test_2_corrupt_backup_rejection(self):
        """Scenario 2: Confirm restore aborts and preserves original database if backup is corrupted."""
        # Create an existing target DB with original data
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("CREATE TABLE target_data (val TEXT)")
        t_conn.execute("INSERT INTO target_data VALUES ('original_data')")
        t_conn.commit()
        t_conn.close()

        # Create an invalid/corrupt backup file
        corrupt_backup = os.path.join(self.test_dir, "corrupt_backup.db")
        with open(corrupt_backup, "wb") as f:
            f.write(b"This is not a valid SQLite database file header at all.")

        with self.assertRaises(Exception):
            restore_sqlite(corrupt_backup, target_path=self.target_db)

        # Target database must remain untouched and readable
        chk_conn = sqlite3.connect(self.target_db)
        val = chk_conn.execute("SELECT val FROM target_data").fetchone()[0]
        chk_conn.close()
        self.assertEqual(val, "original_data")

    def test_3_active_database_lock_handling(self):
        """Scenario 3: Confirm active exclusive lock on target aborts restoration safely."""
        backup_file = backup_sqlite(self.src_db, backup_dir=self.backup_dir)

        # Initialize existing target
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("CREATE TABLE active_tbl (id INT)")
        t_conn.execute("INSERT INTO active_tbl VALUES (1)")
        t_conn.commit()

        # Hold exclusive transaction on target to simulate running active process
        t_conn.execute("BEGIN EXCLUSIVE")

        try:
            with self.assertRaises(RuntimeError) as ctx:
                restore_sqlite(backup_file, target_path=self.target_db)
            self.assertIn("Target database cannot be safely restored while active processes or locks exist", str(ctx.exception))
        finally:
            t_conn.rollback()
            t_conn.close()

        # Target table must remain intact
        chk_conn = sqlite3.connect(self.target_db)
        val = chk_conn.execute("SELECT id FROM active_tbl").fetchone()[0]
        chk_conn.close()
        self.assertEqual(val, 1)

    def test_4_failed_restoration_and_recovery_of_original(self):
        """Scenario 4: Confirm failure during staging replacement rolls back to safety copy."""
        backup_file = backup_sqlite(self.src_db, backup_dir=self.backup_dir)

        # Initialize target with distinct original state
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("CREATE TABLE original_state (marker TEXT)")
        t_conn.execute("INSERT INTO original_state VALUES ('pristine')")
        t_conn.commit()
        t_conn.close()

        # Mock shutil.copy2 to fail specifically during target replacement from staging
        original_copy2 = shutil.copy2
        def failing_copy2(src, dst, **kwargs):
            if str(src).endswith(".tmp") and dst == self.target_db:
                raise IOError("Simulated disk write failure during target replacement")
            return original_copy2(src, dst, **kwargs)

        with patch("shutil.copy2", side_effect=failing_copy2):
            with self.assertRaises(RuntimeError) as ctx:
                restore_sqlite(backup_file, target_path=self.target_db)
            self.assertIn("Database restoration failed; original database preserved", str(ctx.exception))

        # Target must be restored to pristine state from safety copy
        chk_conn = sqlite3.connect(self.target_db)
        marker = chk_conn.execute("SELECT marker FROM original_state").fetchone()[0]
        chk_conn.close()
        self.assertEqual(marker, "pristine")

    def test_5_wal_shm_handling(self):
        """Scenario 5: Confirm restore safely backs up and cleans up stale WAL and SHM sidecars."""
        backup_file = backup_sqlite(self.src_db, backup_dir=self.backup_dir)

        # Initialize target with WAL mode and create sidecars
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("PRAGMA journal_mode = WAL")
        t_conn.execute("CREATE TABLE placeholder (id INT)")
        t_conn.commit()
        t_conn.close()

        wal_file = f"{self.target_db}-wal"
        shm_file = f"{self.target_db}-shm"
        with open(wal_file, "w") as f:
            f.write("stale_wal_data")
        with open(shm_file, "w") as f:
            f.write("stale_shm_data")

        safety_path = restore_sqlite(backup_file, target_path=self.target_db)

        # Stale sidecars must be cleaned up from target
        self.assertFalse(os.path.exists(wal_file))
        self.assertFalse(os.path.exists(shm_file))

        # Safety copy must exist
        self.assertTrue(os.path.exists(safety_path))

        # Restored target database must be valid and queryable
        res_conn = sqlite3.connect(self.target_db)
        count = res_conn.execute("SELECT count(*) FROM orders").fetchone()[0]
        res_conn.close()
        self.assertEqual(count, 2)

    def test_6_safety_copy_preservation(self):
        """Scenario 6: Confirm safety copy is preserved on disk after successful restoration."""
        backup_file = backup_sqlite(self.src_db, backup_dir=self.backup_dir)

        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("CREATE TABLE pre_restore (tag TEXT)")
        t_conn.execute("INSERT INTO pre_restore VALUES ('can_be_recovered')")
        t_conn.commit()
        t_conn.close()

        safety_file = restore_sqlite(backup_file, target_path=self.target_db)

        # Safety copy must be on disk
        self.assertTrue(os.path.exists(safety_file))

        # Safety copy must contain the pre-restore data
        s_conn = sqlite3.connect(safety_file)
        tag = s_conn.execute("SELECT tag FROM pre_restore").fetchone()[0]
        s_conn.close()
        self.assertEqual(tag, "can_be_recovered")


if __name__ == "__main__":
    unittest.main()
