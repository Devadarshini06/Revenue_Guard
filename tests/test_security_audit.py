"""
RevenueGuard Enterprise Security Audit & Credential Remediation Test Suite
===========================================================================
Validates credential remediation, RBAC boundaries, Super Admin protections,
token lifecycle, audit logging, and anti-tamper security controls.
Runs in complete isolation against temporary test databases.
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.models import User, RefreshToken, Category, Region
from backend.auth.service import AuthService
from backend.auth.rbac import Role, Permission
from backend.auth.tokens import create_access_token
from backend.auth.security import hash_password, verify_password, validate_password_strength
from backend.auth.bootstrap import bootstrap_super_admin, rotate_super_admin_password, DISALLOWED_PASSWORDS
from backend.auth.audit import log_audit_event, get_recent_audit_logs, clear_audit_logs, AuditEvent
from tests.asgi_client import ASGITestClient
from backend.main import app


class TestSecurityAuditAndCredentialRemediation(unittest.TestCase):
    """Rigorous security test suite exercising credential safety and authorization boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, "test_security_audit.db")
        cls.test_engine = create_engine(
            f"sqlite:///{cls.test_db_path}",
            connect_args={"check_same_thread": False}
        )
        cls.TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.test_engine,
            expire_on_commit=False
        )

        Base.metadata.create_all(bind=cls.test_engine)

        # Seed minimal required lookup data
        db = cls.TestSessionLocal()
        try:
            if not db.query(Category).first():
                db.add(Category(id=1, name="Hardware", code="HW", description="Core hardware"))
            if not db.query(Region).first():
                db.add(Region(id=1, name="North America", code="NA", country="United States"))
            db.commit()
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        cls.test_engine.dispose()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        clear_audit_logs()
        # Override dependency with test DB session
        def override_get_db():
            db = self.TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = ASGITestClient(app)

        # Provision distinct role users for isolation
        db = self.TestSessionLocal()
        try:
            db.query(RefreshToken).delete()
            db.query(User).delete()
            db.commit()

            self.superadmin = AuthService.create_user(
                db=db,
                email="superadmin.audit@revenueguard.test",
                password="SuperAdminSecureP@ss2026!",
                full_name="Lead Auditor Admin",
                role=Role.SUPER_ADMIN.value,
                is_active=True
            )
            self.admin = AuthService.create_user(
                db=db,
                email="admin.audit@revenueguard.test",
                password="AdminSecureP@ss2026!",
                full_name="Operations Admin",
                role=Role.ADMIN.value,
                is_active=True
            )
            self.analyst = AuthService.create_user(
                db=db,
                email="analyst.audit@revenueguard.test",
                password="AnalystSecureP@ss2026!",
                full_name="Staff Financial Analyst",
                role=Role.ANALYST.value,
                is_active=True
            )
            self.viewer = AuthService.create_user(
                db=db,
                email="viewer.audit@revenueguard.test",
                password="ViewerSecureP@ss2026!",
                full_name="Executive Viewer",
                role=Role.VIEWER.value,
                is_active=True
            )
        finally:
            db.close()

        self.superadmin_token = create_access_token(self.superadmin.id, self.superadmin.email, self.superadmin.role)
        self.admin_token = create_access_token(self.admin.id, self.admin.email, self.admin.role)
        self.analyst_token = create_access_token(self.analyst.id, self.analyst.email, self.analyst.role)
        self.viewer_token = create_access_token(self.viewer.id, self.viewer.email, self.viewer.role)

    def tearDown(self):
        app.dependency_overrides.clear()

    # -------------------------------------------------------------
    # 1. Credential Remediation & Source Code Audit
    # -------------------------------------------------------------

    def test_frontend_login_page_has_no_demo_credentials(self):
        """Verify that frontend login source code contains zero demo credentials or quick-fill buttons."""
        login_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "pages", "Login.jsx")
        )
        self.assertTrue(os.path.exists(login_path), "Login.jsx must exist")
        with open(login_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("SuperAdmin2026!", content, "Hardcoded Super Admin password found in Login.jsx")
        self.assertNotIn("Analyst2026!", content, "Hardcoded Analyst password found in Login.jsx")
        self.assertNotIn("Viewer2026!", content, "Hardcoded Viewer password found in Login.jsx")
        self.assertNotIn("Quick Login Credentials", content, "Demo quick-fill section found in Login.jsx")
        self.assertNotIn("handleQuickFill", content, "Demo credential autofill handler found in Login.jsx")

    def test_bootstrap_rejects_known_default_credentials(self):
        """Bootstrap CLI and service reject known weak or default passwords."""
        for weak in ["admin", "password", "12345678", "superadmin2026!", "default"]:
            with self.subTest(weak_pwd=weak):
                valid, errors = validate_password_strength(weak)
                self.assertFalse(valid, f"Weak password '{weak}' must be rejected by password strength policy")

    def test_credential_rotation_invalidates_prior_password_and_sessions(self):
        """Rotating a user's password makes the old password immediately invalid and revokes existing sessions."""
        db = self.TestSessionLocal()
        try:
            user = db.query(User).filter(User.id == self.superadmin.id).first()
            # Generate session tokens
            _, refresh_raw, _ = AuthService.create_user_tokens(db, user)

            # Change password
            AuthService.change_password(
                db=db,
                user=user,
                current_password="SuperAdminSecureP@ss2026!",
                new_password="NewRotatedP@ssword2026#Secure"
            )

            # Old password must fail authentication
            with self.assertRaises(ValueError):
                AuthService.authenticate_user(db, user.email, "SuperAdminSecureP@ss2026!")

            # New password succeeds
            authed_user = AuthService.authenticate_user(db, user.email, "NewRotatedP@ssword2026#Secure")
            self.assertEqual(authed_user.id, user.id)

            # Prior refresh token must be revoked (raises PermissionError on reuse detection)
            with self.assertRaises(PermissionError):
                AuthService.rotate_refresh_token(db, refresh_raw)
        finally:
            db.close()

    # -------------------------------------------------------------
    # 2. Token Security & HttpOnly Cookie Flow
    # -------------------------------------------------------------

    def test_login_sets_httponly_refresh_cookie(self):
        """Login endpoint sets secure HttpOnly SameSite cookie for the refresh token."""
        res = self.client.post("/api/auth/login", json_data={
            "email": "superadmin.audit@revenueguard.test",
            "password": "SuperAdminSecureP@ss2026!"
        })
        self.assertEqual(res.status_code, 200)
        set_cookie = res.headers.get("set-cookie", "")
        self.assertIn("refresh_token=", set_cookie)
        self.assertIn("httponly", set_cookie.lower())
        self.assertIn("samesite=lax", set_cookie.lower())

    def test_logout_clears_httponly_cookie(self):
        """Logout endpoint deletes the HttpOnly refresh token cookie on client."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "superadmin.audit@revenueguard.test",
            "password": "SuperAdminSecureP@ss2026!"
        })
        tokens = login_res.json()

        logout_res = self.client.post(
            "/api/auth/logout",
            json_data={"refresh_token": tokens["refresh_token"]},
            headers={"authorization": f"Bearer {tokens['access_token']}"}
        )
        self.assertEqual(logout_res.status_code, 200)
        set_cookie = logout_res.headers.get("set-cookie", "")
        # Cookie deletion sets max-age=0 or empty value
        self.assertTrue(
            "refresh_token=" in set_cookie and ("max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower())
        )

    # -------------------------------------------------------------
    # 3. RBAC Privilege Enforcement & Escalation Guards
    # -------------------------------------------------------------

    def test_unauthenticated_request_to_sensitive_endpoint_fails(self):
        """Unauthenticated request to protected endpoint strictly returns 401."""
        res = self.client.get("/api/overview/kpis", headers={"authorization": ""})
        self.assertEqual(res.status_code, 401)
        self.assertIn("authentication required", res.json()["detail"].lower())

    def test_viewer_cannot_execute_sql(self):
        """Viewer role lacks execute:sql permission and cannot invoke query runner."""
        res = self.client.post(
            "/api/data/execute-sql",
            json_data={"query": "SELECT count(*) FROM categories"},
            headers={"authorization": f"Bearer {self.viewer_token}"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("execute:sql", res.json()["detail"])

    def test_viewer_cannot_upload_data(self):
        """Viewer role lacks manage:data permission and cannot upload datasets."""
        res = self.client.post_file(
            "/api/data/upload",
            filename="data.csv",
            file_bytes=b"dummy,header\n1,2",
            headers={"authorization": f"Bearer {self.viewer_token}"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("manage:data", res.json()["detail"])

    def test_analyst_cannot_manage_users(self):
        """Analyst role lacks manage:users permission and cannot list or create users."""
        res = self.client.get(
            "/api/auth/users",
            headers={"authorization": f"Bearer {self.analyst_token}"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("manage:users", res.json()["detail"])

    def test_admin_cannot_access_user_management(self):
        """Admin role lacks manage:users permission (reserved exclusively for Super Admin)."""
        res = self.client.get(
            "/api/auth/users",
            headers={"authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("manage:users", res.json()["detail"])

    def test_non_superadmin_cannot_promote_to_superadmin(self):
        """Non-Super Admin users cannot escalate privileges or promote users to Super Admin."""
        db = self.TestSessionLocal()
        try:
            with self.assertRaises(ValueError) as ctx:
                AuthService.create_user(
                    db=db,
                    email="escalated@revenueguard.test",
                    password="StrongP@ss2026!Escalate",
                    full_name="Escalated Account",
                    role=Role.SUPER_ADMIN.value,
                    acting_user=self.admin
                )
            self.assertIn("Only Super Admins can provision Super Admin accounts", str(ctx.exception))
        finally:
            db.close()

    def test_admin_cannot_alter_superadmin_role(self):
        """Admin cannot alter or demote a Super Admin account."""
        db = self.TestSessionLocal()
        try:
            with self.assertRaises(ValueError) as ctx:
                AuthService.update_user_role(
                    db=db,
                    user_id=self.superadmin.id,
                    new_role=Role.ADMIN.value,
                    acting_user=self.admin
                )
            self.assertIn("Only Super Admins can alter Super Admin accounts", str(ctx.exception))
        finally:
            db.close()

    def test_last_superadmin_cannot_be_demoted_or_deactivated(self):
        """The platform strictly prevents demoting or deactivating the last active Super Admin."""
        db = self.TestSessionLocal()
        try:
            # Cannot demote
            with self.assertRaises(ValueError) as ctx_demote:
                AuthService.update_user_role(
                    db=db,
                    user_id=self.superadmin.id,
                    new_role=Role.ADMIN.value,
                    acting_user=self.superadmin
                )
            self.assertIn("Cannot demote the last active Super Admin", str(ctx_demote.exception))

            # Cannot self-deactivate
            with self.assertRaises(ValueError) as ctx_deact:
                AuthService.update_user_status(
                    db=db,
                    user_id=self.superadmin.id,
                    is_active=False,
                    acting_user=self.superadmin
                )
            self.assertIn("Administrators cannot deactivate their own account", str(ctx_deact.exception))
        finally:
            db.close()

    # -------------------------------------------------------------
    # 4. Security Audit Logging Verification
    # -------------------------------------------------------------

    def test_audit_logging_captures_security_events(self):
        """Security events (login, user creation, role change, privileged operations) produce audit logs."""
        clear_audit_logs()

        # Login event
        self.client.post("/api/auth/login", json_data={
            "email": "superadmin.audit@revenueguard.test",
            "password": "SuperAdminSecureP@ss2026!"
        })

        logs = get_recent_audit_logs(limit=10)
        login_events = [l for l in logs if l["event_type"] == AuditEvent.LOGIN_SUCCESS]
        self.assertTrue(len(login_events) >= 1)
        self.assertEqual(login_events[0]["actor"]["email"], "superadmin.audit@revenueguard.test")

    def test_audit_logs_never_contain_plaintext_passwords_or_tokens(self):
        """Audit log details strictly redact sensitive fields like password or token."""
        record = log_audit_event(
            AuditEvent.LOGIN_SUCCESS,
            actor_email="audit.check@revenueguard.test",
            details={
                "password": "SuperSecretPassword123!",
                "access_token": "eyJh...sample.jwt",
                "refresh_token": "raw-refresh-entropy",
                "safe_field": "operational_ok"
            }
        )
        self.assertEqual(record["details"]["password"], "[REDACTED]")
        self.assertEqual(record["details"]["access_token"], "[REDACTED]")
        self.assertEqual(record["details"]["refresh_token"], "[REDACTED]")
        self.assertEqual(record["details"]["safe_field"], "operational_ok")

    def test_token_reuse_detection_triggers_revocation_and_audit(self):
        """Reusing a revoked refresh token revokes all user sessions and logs a security alert."""
        clear_audit_logs()
        db = self.TestSessionLocal()
        try:
            _, raw_refresh, _ = AuthService.create_user_tokens(db, self.viewer)

            # First rotation succeeds
            _, new_refresh, _ = AuthService.rotate_refresh_token(db, raw_refresh)

            # Attacker presents already rotated token -> triggers reuse detection
            with self.assertRaises(PermissionError):
                AuthService.rotate_refresh_token(db, raw_refresh)

            # Verify all tokens for this user are revoked
            active_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_id == self.viewer.id,
                RefreshToken.is_revoked == False
            ).count()
            self.assertEqual(active_tokens, 0, "All sessions must be revoked upon token reuse attempt")

            # Check audit event was logged
            logs = get_recent_audit_logs(limit=10)
            reuse_events = [l for l in logs if l["event_type"] == AuditEvent.TOKEN_REUSE_DETECTED]
            self.assertTrue(len(reuse_events) >= 1)
            self.assertEqual(reuse_events[0]["status"], "REVOCATION_ALERT")
        finally:
            db.close()

    # -------------------------------------------------------------
    # 4. Immediate Access-Token Revocation Verification
    # -------------------------------------------------------------

    def test_access_token_rejected_immediately_after_logout(self):
        """Previously issued access token must be rejected immediately after logout."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst.audit@revenueguard.test",
            "password": "AnalystSecureP@ss2026!"
        })
        self.assertEqual(login_res.status_code, 200)
        tokens = login_res.json()
        headers = {"authorization": f"Bearer {tokens['access_token']}"}

        # Valid before logout
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 200)

        # Logout
        logout_res = self.client.post(
            "/api/auth/logout",
            json_data={"refresh_token": tokens["refresh_token"]},
            headers=headers
        )
        self.assertEqual(logout_res.status_code, 200)

        # Previously issued access token is immediately rejected
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)
        self.assertEqual(self.client.get("/api/overview/kpis", headers=headers).status_code, 401)

    def test_access_token_rejected_immediately_after_password_change(self):
        """Previously issued access token must be rejected immediately after password change."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst.audit@revenueguard.test",
            "password": "AnalystSecureP@ss2026!"
        })
        tokens = login_res.json()
        headers = {"authorization": f"Bearer {tokens['access_token']}"}
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 200)

        # Change password
        cp_res = self.client.post(
            "/api/auth/change-password",
            json_data={
                "current_password": "AnalystSecureP@ss2026!",
                "new_password": "AnalystNewP@ssword2026#"
            },
            headers=headers
        )
        self.assertEqual(cp_res.status_code, 200)

        # Prior access token is immediately rejected
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)
        self.assertEqual(self.client.get("/api/overview/kpis", headers=headers).status_code, 401)

    def test_access_token_rejected_immediately_after_deactivation(self):
        """Previously issued access token must be rejected immediately after account deactivation."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "viewer.audit@revenueguard.test",
            "password": "ViewerSecureP@ss2026!"
        })
        tokens = login_res.json()
        viewer_headers = {"authorization": f"Bearer {tokens['access_token']}"}
        self.assertEqual(self.client.get("/api/auth/me", headers=viewer_headers).status_code, 200)

        # Super Admin deactivates viewer
        deact_res = self.client.put(
            f"/api/auth/users/{self.viewer.id}/status",
            json_data={"is_active": False},
            headers={"authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(deact_res.status_code, 200)

        # Prior access token is immediately rejected
        res = self.client.get("/api/overview/kpis", headers=viewer_headers)
        self.assertIn(res.status_code, (401, 403))

    def test_access_token_rejected_immediately_after_refresh_reuse_detection(self):
        """Previously issued access tokens must be rejected immediately when refresh token reuse is detected."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "viewer.audit@revenueguard.test",
            "password": "ViewerSecureP@ss2026!"
        })
        initial = login_res.json()

        # Legitimate rotation
        rot_res = self.client.post("/api/auth/refresh", json_data={"refresh_token": initial["refresh_token"]})
        self.assertEqual(rot_res.status_code, 200)
        rotated = rot_res.json()

        # Replay initial refresh token -> triggers reuse detection
        reuse_res = self.client.post("/api/auth/refresh", json_data={"refresh_token": initial["refresh_token"]})
        self.assertEqual(reuse_res.status_code, 401)

        # Both initial and rotated access tokens are now rejected immediately
        self.assertEqual(
            self.client.get("/api/auth/me", headers={"authorization": f"Bearer {initial['access_token']}"}).status_code,
            401
        )
        self.assertEqual(
            self.client.get("/api/auth/me", headers={"authorization": f"Bearer {rotated['access_token']}"}).status_code,
            401
        )

    def test_access_token_rejected_immediately_after_admin_session_revocation(self):
        """Administrative session revocation must immediately invalidate both access and refresh tokens."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst.audit@revenueguard.test",
            "password": "AnalystSecureP@ss2026!"
        })
        tokens = login_res.json()
        analyst_headers = {"authorization": f"Bearer {tokens['access_token']}"}
        self.assertEqual(self.client.get("/api/auth/me", headers=analyst_headers).status_code, 200)

        # Super Admin revokes all sessions for analyst
        rev_res = self.client.post(
            f"/api/auth/users/{self.analyst.id}/revoke-sessions",
            headers={"authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(rev_res.status_code, 200)

        # Access token and refresh token are both rejected immediately
        self.assertEqual(self.client.get("/api/auth/me", headers=analyst_headers).status_code, 401)
        self.assertEqual(
            self.client.post("/api/auth/refresh", json_data={"refresh_token": tokens["refresh_token"]}).status_code,
            401
        )

    # -------------------------------------------------------------
    # 5. Account Deactivation & Reactivation Session Isolation
    # -------------------------------------------------------------

    def test_deactivated_account_blocked_and_reactivation_does_not_restore_sessions(self):
        """Deactivated accounts cannot login, refresh, or use existing tokens; reactivation keeps old sessions dead."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "analyst.audit@revenueguard.test",
            "password": "AnalystSecureP@ss2026!"
        })
        self.assertEqual(login_res.status_code, 200)
        tokens = login_res.json()
        analyst_headers = {"authorization": f"Bearer {tokens['access_token']}"}

        # Deactivate account
        deact = self.client.put(
            f"/api/auth/users/{self.analyst.id}/status",
            json_data={"is_active": False},
            headers={"authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(deact.status_code, 200)

        # 1. Cannot log in
        login_blocked = self.client.post("/api/auth/login", json_data={
            "email": "analyst.audit@revenueguard.test",
            "password": "AnalystSecureP@ss2026!"
        })
        self.assertEqual(login_blocked.status_code, 403)

        # 2. Cannot refresh access token
        refresh_blocked = self.client.post("/api/auth/refresh", json_data={"refresh_token": tokens["refresh_token"]})
        self.assertEqual(refresh_blocked.status_code, 401)

        # 3. Cannot access protected endpoints with existing access token
        self.assertEqual(self.client.get("/api/overview/kpis", headers=analyst_headers).status_code, 403)

        # Reactivate account
        react = self.client.put(
            f"/api/auth/users/{self.analyst.id}/status",
            json_data={"is_active": True},
            headers={"authorization": f"Bearer {self.superadmin_token}"}
        )
        self.assertEqual(react.status_code, 200)

        # 4. Previously issued access token and refresh token MUST STILL FAIL after reactivation
        self.assertEqual(self.client.get("/api/auth/me", headers=analyst_headers).status_code, 401)
        self.assertEqual(
            self.client.post("/api/auth/refresh", json_data={"refresh_token": tokens["refresh_token"]}).status_code,
            401
        )

    # -------------------------------------------------------------
    # 6. CSRF, Cookie Security & CORS Verification
    # -------------------------------------------------------------

    def test_cookie_authenticated_refresh_and_logout_csrf_protection(self):
        """Cookie-authenticated refresh and logout reject missing X-Requested-With, untrusted Origin, and cross-site Sec-Fetch-Site."""
        login_res = self.client.post("/api/auth/login", json_data={
            "email": "viewer.audit@revenueguard.test",
            "password": "ViewerSecureP@ss2026!"
        })
        tokens = login_res.json()
        cookie_hdr = f"refresh_token={tokens['refresh_token']}"

        # Missing X-Requested-With header on cookie-authenticated refresh -> 403
        res_no_header = self.client.post(
            "/api/auth/refresh",
            headers={"authorization": "", "cookie": cookie_hdr}
        )
        self.assertEqual(res_no_header.status_code, 403)

        # Untrusted Origin even with X-Requested-With -> 403
        res_bad_origin = self.client.post(
            "/api/auth/refresh",
            headers={
                "authorization": "",
                "cookie": cookie_hdr,
                "origin": "https://evil.attacker.example",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.assertEqual(res_bad_origin.status_code, 403)

        # Cross-site Sec-Fetch-Site -> 403
        res_cross_site = self.client.post(
            "/api/auth/refresh",
            headers={
                "authorization": "",
                "cookie": cookie_hdr,
                "sec-fetch-site": "cross-site",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.assertEqual(res_cross_site.status_code, 403)

        # Untrusted Origin on cookie-authenticated logout -> 403
        res_logout_evil = self.client.post(
            "/api/auth/logout",
            headers={
                "authorization": "",
                "cookie": f"{cookie_hdr}; access_token={tokens['access_token']}",
                "origin": "https://evil.attacker.example",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.assertEqual(res_logout_evil.status_code, 403)

        # Trusted Origin + X-Requested-With -> 200
        res_trusted = self.client.post(
            "/api/auth/refresh",
            headers={
                "authorization": "",
                "cookie": cookie_hdr,
                "origin": "http://localhost:5173",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.assertEqual(res_trusted.status_code, 200)

    def test_cors_preflight_blocks_untrusted_origin_and_allows_trusted_origin(self):
        """CORS preflight rejects untrusted origins and allows configured origins with credentials."""
        bad_preflight = self.client.request(
            "OPTIONS",
            "/api/auth/refresh",
            headers={
                "origin": "https://evil.attacker.example",
                "access-control-request-method": "POST",
                "access-control-request-headers": "X-Requested-With, Content-Type",
            }
        )
        self.assertEqual(bad_preflight.status_code, 400)
        self.assertIsNone(bad_preflight.headers.get("access-control-allow-origin"))

        good_preflight = self.client.request(
            "OPTIONS",
            "/api/auth/refresh",
            headers={
                "origin": "http://localhost:5173",
                "access-control-request-method": "POST",
                "access-control-request-headers": "X-Requested-With, Content-Type",
            }
        )
        self.assertEqual(good_preflight.status_code, 200)
        self.assertEqual(good_preflight.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertEqual(good_preflight.headers.get("access-control-allow-credentials"), "true")

    def test_cookie_attributes_in_development_and_production(self):
        """Refresh cookie has HttpOnly, SameSite=Lax, Path=/api/auth, and Secure=True in production."""
        from backend.config import settings
        original_env = settings._env
        try:
            # Development mode
            settings._env = {"ENVIRONMENT": "development"}
            dev_res = self.client.post("/api/auth/login", json_data={
                "email": "viewer.audit@revenueguard.test",
                "password": "ViewerSecureP@ss2026!"
            })
            dev_cookie = dev_res.headers.get("set-cookie", "").lower()
            self.assertIn("httponly", dev_cookie)
            self.assertIn("samesite=lax", dev_cookie)
            self.assertIn("path=/api/auth", dev_cookie)
            self.assertNotIn("; secure", dev_cookie)

            # Production mode
            settings._env = {"ENVIRONMENT": "production"}
            prod_res = self.client.post("/api/auth/login", json_data={
                "email": "viewer.audit@revenueguard.test",
                "password": "ViewerSecureP@ss2026!"
            })
            prod_cookie = prod_res.headers.get("set-cookie", "").lower()
            self.assertIn("httponly", prod_cookie)
            self.assertIn("samesite=lax", prod_cookie)
            self.assertIn("path=/api/auth", prod_cookie)
            self.assertIn("secure", prod_cookie)
        finally:
            settings._env = original_env

    def test_metrics_not_exposed_and_protected_endpoints_require_auth(self):
        """Verify /metrics is not exposed and business/admin endpoints reject anonymous requests."""
        self.assertEqual(self.client.get("/metrics", headers={"authorization": ""}).status_code, 404)
        for path in [
            "/api/overview/kpis",
            "/api/revenue/summary",
            "/api/reports/export/transactions/csv",
            "/api/data/history",
            "/api/auth/users",
            "/api/auth/audit-logs",
        ]:
            res = self.client.get(path, headers={"authorization": ""})
            self.assertEqual(res.status_code, 401, f"Expected 401 for unauthenticated GET {path}")


if __name__ == "__main__":
    unittest.main()
