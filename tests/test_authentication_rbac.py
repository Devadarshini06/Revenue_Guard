"""
RevenueGuard Enterprise Authentication & RBAC Test Suite
=========================================================
Tests Argon2id password hashing, JWT lifecycle, refresh token rotation,
reuse detection, rate limiting, and granular RBAC role-permission enforcement.
"""

import os
import unittest
import tempfile
import sqlite3
import shutil
import jwt
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.models import User, RefreshToken
from backend.auth.security import hash_password, verify_password, validate_password_strength
from backend.auth.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    decode_access_token,
)
from backend.auth.rbac import Role, Permission, has_permission, get_role_permissions
from backend.auth.service import AuthService
from backend.auth.rate_limiter import clear_all_rate_limits
from tests.asgi_client import ASGITestClient


class TestAuthenticationAndRBAC(unittest.TestCase):
    """Full-coverage authentication, token lifecycle, and RBAC test suite."""

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database for authentication testing
        cls.test_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.test_dir, "auth_test.db")
        cls.db_url = f"sqlite:///{cls.db_path}"

        cls.engine = create_engine(cls.db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = ASGITestClient(app, default_auth=False)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        clear_all_rate_limits()
        self.db = self.TestingSessionLocal()
        # Clean tables for fresh test state
        self.db.query(RefreshToken).delete()
        self.db.query(User).delete()
        self.db.commit()

        # Seed test users for each role
        self.super_admin = AuthService.create_user(
            db=self.db,
            email="superadmin@example.com",
            password="SuperPassword123!",
            full_name="Super Administrator",
            role=Role.SUPER_ADMIN.value
        )
        self.admin = AuthService.create_user(
            db=self.db,
            email="admin@example.com",
            password="AdminPassword123!",
            full_name="Business Admin",
            role=Role.ADMIN.value
        )
        self.analyst = AuthService.create_user(
            db=self.db,
            email="analyst@example.com",
            password="AnalystPassword123!",
            full_name="Data Analyst",
            role=Role.ANALYST.value
        )
        self.viewer = AuthService.create_user(
            db=self.db,
            email="viewer@example.com",
            password="ViewerPassword123!",
            full_name="Dashboard Viewer",
            role=Role.VIEWER.value
        )

        # Pre-generate access tokens for RBAC tests
        self.super_admin_token = create_access_token(self.super_admin.id, self.super_admin.email, self.super_admin.role)
        self.admin_token = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        self.analyst_token = create_access_token(self.analyst.id, self.analyst.email, self.analyst.role)
        self.viewer_token = create_access_token(self.viewer.id, self.viewer.email, self.viewer.role)

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------
    # 1. Password Hashing & Complexity Tests
    # -------------------------------------------------------------
    def test_argon2id_password_hashing(self):
        """Confirm Argon2id hashing produces valid verifier strings."""
        raw_password = "ComplexPassword99!"
        hashed = hash_password(raw_password)
        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertTrue(verify_password(raw_password, hashed))
        self.assertFalse(verify_password("WrongPassword123!", hashed))

    def test_password_complexity_validator(self):
        """Confirm password strength rules enforce length, upper, lower, number, special."""
        self.assertTrue(validate_password_strength("ValidStrongP@ss1")[0])
        self.assertFalse(validate_password_strength("short1!")[0])  # < 8 chars
        self.assertFalse(validate_password_strength("nouppercase1!")[0])
        self.assertFalse(validate_password_strength("NOLOWERCASE1!")[0])
        self.assertFalse(validate_password_strength("NoNumbersAtAll!")[0])
        self.assertFalse(validate_password_strength("NoSpecialChar123")[0])

    # -------------------------------------------------------------
    # 2. Authentication (Login / Logout / Tokens)
    # -------------------------------------------------------------
    def test_successful_login(self):
        """Valid credentials return JWT access token, refresh token, and user summary."""
        res = self.client.post("/api/auth/login", json_data={
            "email": "superadmin@example.com",
            "password": "SuperPassword123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "Bearer")
        self.assertEqual(data["user"]["email"], "superadmin@example.com")
        self.assertEqual(data["user"]["role"], "Super Admin")

    def test_invalid_credentials_rejected_with_generic_message(self):
        """Wrong password or nonexistent email returns 401 with generic message."""
        # Nonexistent email
        res1 = self.client.post("/api/auth/login", json_data={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        })
        self.assertEqual(res1.status_code, 401)
        self.assertEqual(res1.json()["detail"], "Invalid email or password.")

        # Wrong password
        res2 = self.client.post("/api/auth/login", json_data={
            "email": "superadmin@example.com",
            "password": "WrongPassword999!"
        })
        self.assertEqual(res2.status_code, 401)
        self.assertEqual(res2.json()["detail"], "Invalid email or password.")

    def test_inactive_account_login_rejected(self):
        """Deactivated user account is rejected upon login."""
        self.viewer.is_active = False
        self.db.commit()

        res = self.client.post("/api/auth/login", json_data={
            "email": "viewer@example.com",
            "password": "ViewerPassword123!"
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("deactivated", res.json()["detail"].lower())

    def test_token_expiration_validation(self):
        """Expired access token is rejected with HTTP 401."""
        expired_token = create_access_token(
            user_id=self.viewer.id,
            email=self.viewer.email,
            role=self.viewer.role,
            expires_delta=timedelta(seconds=-10)
        )
        res = self.client.get(
            "/api/auth/me",
            headers={"authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("expired", res.json()["detail"].lower())

    def test_tampered_jwt_rejected(self):
        """Tampered JWT signature is rejected with HTTP 401."""
        parts = self.viewer_token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature_string"
        res = self.client.get(
            "/api/auth/me",
            headers={"authorization": f"Bearer {tampered_token}"}
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("invalid", res.json()["detail"].lower())

    def test_refresh_token_rotation(self):
        """Confirm /refresh endpoint returns new tokens and revokes the old refresh token."""
        # Log in to get tokens
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst@example.com",
            "password": "AnalystPassword123!"
        })
        initial_refresh = login_res.json()["refresh_token"]

        # Call refresh
        refresh_res = self.client.post("/api/auth/refresh", json_data={
            "refresh_token": initial_refresh
        })
        self.assertEqual(refresh_res.status_code, 200)
        new_data = refresh_res.json()
        self.assertIn("access_token", new_data)
        self.assertIn("refresh_token", new_data)
        self.assertNotEqual(initial_refresh, new_data["refresh_token"])

        # Old refresh token is revoked and cannot be used again
        old_hash = hash_refresh_token(initial_refresh)
        db_token = self.db.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()
        self.assertTrue(db_token.is_revoked)

    def test_refresh_token_reuse_detection(self):
        """Presenting an already revoked refresh token triggers reuse detection and revokes all sessions."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "admin@example.com",
            "password": "AdminPassword123!"
        })
        initial_refresh = login_res.json()["refresh_token"]

        # Rotate once
        rot_res = self.client.post("/api/auth/refresh", json_data={"refresh_token": initial_refresh})
        self.assertEqual(rot_res.status_code, 200)

        # Attacker presents already used token
        reuse_res = self.client.post("/api/auth/refresh", json_data={"refresh_token": initial_refresh})
        self.assertEqual(reuse_res.status_code, 401)
        self.assertIn("revoked", reuse_res.json()["detail"].lower())

    def test_logout_behavior(self):
        """Logging out revokes the refresh token."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "viewer@example.com",
            "password": "ViewerPassword123!"
        })
        tokens = login_res.json()

        logout_res = self.client.post(
            "/api/auth/logout",
            json_data={"refresh_token": tokens["refresh_token"]},
            headers={"authorization": f"Bearer {tokens['access_token']}"}
        )
        self.assertEqual(logout_res.status_code, 200)

        # Refreshing with logged out token must fail
        ref_res = self.client.post("/api/auth/refresh", json_data={"refresh_token": tokens["refresh_token"]})
        self.assertEqual(ref_res.status_code, 401)

    def test_change_password(self):
        """Changing password requires valid current password and strong new password."""
        # Wrong current password fails
        res1 = self.client.post(
            "/api/auth/change-password",
            json_data={"current_password": "WrongPassword!", "new_password": "NewStrongP@ssword123"},
            headers={"authorization": f"Bearer {self.analyst_token}"}
        )
        self.assertEqual(res1.status_code, 400)
        self.assertIn("current password is incorrect", res1.json()["detail"].lower())

        # Weak new password fails (meets length but lacks special char/upper/digit)
        res2 = self.client.post(
            "/api/auth/change-password",
            json_data={"current_password": "AnalystPassword123!", "new_password": "weakpasswordonlylowercase"},
            headers={"authorization": f"Bearer {self.analyst_token}"}
        )
        self.assertEqual(res2.status_code, 400)

        # Valid password change succeeds
        res3 = self.client.post(
            "/api/auth/change-password",
            json_data={"current_password": "AnalystPassword123!", "new_password": "NewBrandStrongP@ss2026!"},
            headers={"authorization": f"Bearer {self.analyst_token}"}
        )
        self.assertEqual(res3.status_code, 200)

        # Can now log in with new password
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst@example.com",
            "password": "NewBrandStrongP@ss2026!"
        })
        self.assertEqual(login_res.status_code, 200)

    def test_login_rate_limiting(self):
        """Confirm 5 consecutive failed login attempts trigger HTTP 429."""
        for _ in range(5):
            res = self.client.post("/api/auth/login", json_data={
                "email": "analyst@example.com",
                "password": "BadPassword123!"
            })
            self.assertEqual(res.status_code, 401)

        # 6th attempt should be rate limited
        blocked_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst@example.com",
            "password": "BadPassword123!"
        })
        self.assertEqual(blocked_res.status_code, 429)
        self.assertIn("too many failed login attempts", blocked_res.json()["detail"].lower())

    # -------------------------------------------------------------
    # 3. RBAC & Granular Permission Tests
    # -------------------------------------------------------------
    def test_unauthorized_access_without_token(self):
        """Protected endpoints return 401 Unauthorized when accessed without credentials."""
        res = self.client.get("/api/overview/filters", headers={"authorization": ""})
        self.assertEqual(res.status_code, 401)
        self.assertIn("authentication required", res.json()["detail"].lower())

    def test_super_admin_has_full_access(self):
        """Super Admin can access all modules, execute SQL, and manage users."""
        # Can access analytics
        res_overview = self.client.get("/api/overview/filters", headers={"authorization": f"Bearer {self.super_admin_token}"})
        self.assertEqual(res_overview.status_code, 200)

        # Can access user management
        res_users = self.client.get("/api/auth/users", headers={"authorization": f"Bearer {self.super_admin_token}"})
        self.assertEqual(res_users.status_code, 200)

        # Can execute SQL
        res_sql = self.client.post(
            "/api/data/execute-sql",
            json_data={"query": "SELECT count(*) FROM categories"},
            headers={"authorization": f"Bearer {self.super_admin_token}"}
        )
        self.assertEqual(res_sql.status_code, 200)

    def test_admin_cannot_manage_users(self):
        """Admin can access business modules and data uploads, but CANNOT manage platform users."""
        # User management is blocked for Admin
        res = self.client.get("/api/auth/users", headers={"authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("lacks required permission 'manage:users'", res.json()["detail"])

    def test_analyst_cannot_upload_data(self):
        """Analyst can view analytics and run SQL, but CANNOT upload datasets or manage users."""
        # Can execute SQL
        res_sql = self.client.post(
            "/api/data/execute-sql",
            json_data={"query": "SELECT count(*) FROM regions"},
            headers={"authorization": f"Bearer {self.analyst_token}"}
        )
        self.assertEqual(res_sql.status_code, 200)

        # Cannot upload data
        res_upload = self.client.post_file(
            "/api/data/upload",
            filename="test_upload.csv",
            file_bytes=b"order_id,customer_id\n1,10\n",
            headers={"authorization": f"Bearer {self.analyst_token}"}
        )
        self.assertEqual(res_upload.status_code, 403)
        self.assertIn("lacks required permission 'manage:data'", res_upload.json()["detail"])

    def test_viewer_has_strictly_read_only_access(self):
        """Viewer can view analytics dashboards, but CANNOT execute custom SQL or upload data."""
        # Can view analytics
        res_view = self.client.get("/api/overview/filters", headers={"authorization": f"Bearer {self.viewer_token}"})
        self.assertEqual(res_view.status_code, 200)

        # Cannot execute SQL runner
        res_sql = self.client.post(
            "/api/data/execute-sql",
            json_data={"query": "SELECT 1"},
            headers={"authorization": f"Bearer {self.viewer_token}"}
        )
        self.assertEqual(res_sql.status_code, 403)
        self.assertIn("lacks required permission 'execute:sql'", res_sql.json()["detail"])

    def test_user_creation_and_role_management(self):
        """Super Admin can provision new users, update status, and change roles."""
        # Create user
        create_res = self.client.post(
            "/api/auth/users",
            json_data={
                "email": "newuser@example.com",
                "password": "NewUserPassword1!",
                "full_name": "New Junior Analyst",
                "role": "Analyst"
            },
            headers={"authorization": f"Bearer {self.super_admin_token}"}
        )
        self.assertEqual(create_res.status_code, 201)
        created_id = create_res.json()["id"]

        # Update role to Admin
        role_res = self.client.put(
            f"/api/auth/users/{created_id}/role",
            json_data={"role": "Admin"},
            headers={"authorization": f"Bearer {self.super_admin_token}"}
        )
        self.assertEqual(role_res.status_code, 200)
        self.assertEqual(role_res.json()["role"], "Admin")

        # Deactivate user
        status_res = self.client.put(
            f"/api/auth/users/{created_id}/status",
            json_data={"is_active": False},
            headers={"authorization": f"Bearer {self.super_admin_token}"}
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertFalse(status_res.json()["is_active"])

    def test_cannot_demote_last_super_admin(self):
        """Prevents demoting the last active Super Admin on the platform."""
        res = self.client.put(
            f"/api/auth/users/{self.super_admin.id}/role",
            json_data={"role": "Admin"},
            headers={"authorization": f"Bearer {self.super_admin_token}"}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot demote the last active super admin", res.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
