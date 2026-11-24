import unittest
import sqlite3
from backend.main import app
from tests.asgi_client import ASGITestClient
from backend.config import settings
from backend.database import engine
from sqlalchemy import text


class TestProductionReadiness(unittest.TestCase):
    """
    Milestone 7: Production Readiness, Security Headers, and Health Monitoring Test Suite.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)

    def test_health_liveness_probe(self):
        """Container orchestrator liveness check."""
        res = self.client.get("/api/health/live")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "alive"})

    def test_health_readiness_probe(self):
        """Readiness check validating database connection responsiveness."""
        res = self.client.get("/api/health/ready")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["database"], "connected")
        self.assertIn("timestamp", data)

    def test_observability_and_security_headers(self):
        """Verifies that security headers and correlation IDs are attached to HTTP responses."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertIn("x-request-id", res.headers)
        self.assertIn("x-process-time", res.headers)
        self.assertEqual(res.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(res.headers.get("x-frame-options"), "DENY")
        self.assertEqual(res.headers.get("x-xss-protection"), "1; mode=block")
        self.assertEqual(res.headers.get("referrer-policy"), "strict-origin-when-cross-origin")

    def test_request_id_passthrough(self):
        """Verifies that an incoming X-Request-ID header is preserved through the response."""
        custom_id = "req-custom-trace-12345"
        res = self.client.get("/api/health", headers={"x-request-id": custom_id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("x-request-id"), custom_id)

    def test_database_sqlite_wal_and_fk_enabled(self):
        """Verifies that foreign keys and WAL mode are active on SQLite connections."""
        if settings.DATABASE_URL.startswith("sqlite"):
            with engine.connect() as conn:
                fk_status = conn.execute(text("PRAGMA foreign_keys")).scalar()
                journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
                self.assertEqual(fk_status, 1)
                self.assertEqual(journal_mode.lower(), "wal")

    def test_database_backup_and_restore_cycle_in_temp_db(self):
        """Verifies non-blocking online SQLite backup and restoration cycle on isolated test DB."""
        import tempfile
        import os
        from backend.database_backup import backup_sqlite, restore_sqlite

        # Create isolated source DB
        fd_src, path_src = tempfile.mkstemp(suffix=".db")
        os.close(fd_src)
        conn = sqlite3.connect(path_src)
        conn.execute("CREATE TABLE test_data (id INT, val TEXT)")
        conn.execute("INSERT INTO test_data VALUES (1, 'active_txn')")
        conn.commit()
        conn.close()

        # Backup into temp directory
        temp_backup_dir = tempfile.mkdtemp()
        backup_file = backup_sqlite(path_src, backup_dir=temp_backup_dir)
        self.assertTrue(os.path.exists(backup_file))

        # Restore into new isolated target DB
        fd_dst, path_dst = tempfile.mkstemp(suffix=".db")
        os.close(fd_dst)
        restore_sqlite(backup_file, target_path=path_dst)

        # Verify restored contents
        res_conn = sqlite3.connect(path_dst)
        row = res_conn.execute("SELECT id, val FROM test_data").fetchone()
        res_conn.close()
        self.assertEqual(row, (1, "active_txn"))

        # Cleanup isolated files
        for p in [path_src, path_dst, backup_file]:
            if os.path.exists(p):
                os.remove(p)
        if os.path.exists(temp_backup_dir):
            os.rmdir(temp_backup_dir)


if __name__ == "__main__":
    unittest.main()
