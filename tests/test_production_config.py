"""
RevenueGuard Production Configuration & Safety Test Suite
=========================================================
Tests production environment isolation, CORS allowlist enforcement,
safe error handling, and backup/restore safety under WAL mode.
"""

import os
import unittest
import tempfile
import sqlite3
import shutil
from unittest.mock import patch
from sqlalchemy import create_engine
from backend.config import Settings
from backend.database_backup import backup_sqlite, restore_sqlite
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
        """Confirm wildcard '*' in ALLOWED_ORIGINS is stripped out in production."""
        cfg = Settings({"ENVIRONMENT": "production", "ALLOWED_ORIGINS": "*"})
        # Should strip wildcard and fall back to safe localhost origins
        self.assertNotIn("*", cfg.CORS_ORIGINS)
        self.assertEqual(cfg.CORS_ORIGINS, ["http://localhost", "https://localhost"])

        # Wildcard with explicit origins
        cfg2 = Settings({"ENVIRONMENT": "production", "ALLOWED_ORIGINS": "https://analytics.corp.com, *"})
        self.assertNotIn("*", cfg2.CORS_ORIGINS)
        self.assertEqual(cfg2.CORS_ORIGINS, ["https://analytics.corp.com"])

    def test_production_cors_allowlist_handling(self):
        """Confirm comma-separated production origins are parsed cleanly."""
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


class TestBackupAndRestoreSafety(unittest.TestCase):
    """Verifies WAL-mode online backup, integrity checking, and rollback safety."""

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

    def test_online_backup_under_wal_mode(self):
        """Confirm online backup operates while WAL file is active and passes integrity check."""
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

    def test_restore_preserves_original_on_corrupt_backup(self):
        """Confirm restore aborts and preserves original database if backup is corrupted."""
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

    def test_restore_cleans_up_stale_wal_sidecars(self):
        """Confirm restore removes stale WAL and SHM sidecars from target."""
        backup_file = backup_sqlite(self.src_db, backup_dir=self.backup_dir)

        # Simulate existing target with valid initial DB and stale wal/shm files
        t_conn = sqlite3.connect(self.target_db)
        t_conn.execute("CREATE TABLE placeholder (id INT)")
        t_conn.commit()
        t_conn.close()

        wal_file = f"{self.target_db}-wal"
        shm_file = f"{self.target_db}-shm"
        with open(wal_file, "w") as f:
            f.write("stale_wal")
        with open(shm_file, "w") as f:
            f.write("stale_shm")

        restore_sqlite(backup_file, target_path=self.target_db)

        # The target must be a valid DB and stale sidecars removed
        self.assertFalse(os.path.exists(wal_file))
        self.assertFalse(os.path.exists(shm_file))
        res_conn = sqlite3.connect(self.target_db)
        count = res_conn.execute("SELECT count(*) FROM orders").fetchone()[0]
        res_conn.close()
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
