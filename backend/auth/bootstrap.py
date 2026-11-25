"""
RevenueGuard Initial Super Admin Provisioning & Credential Rotation Utility
===========================================================================
Controlled CLI bootstrapping process to create or rotate the platform Super Admin.
Enforces Argon2id hashing, strict complexity rules, and instant session invalidation.
Prohibits known default credentials.
"""

import sys
import argparse
import getpass
import secrets
import string
from datetime import datetime, timezone
from backend.database import SessionLocal, engine, Base
from backend.models import User, RefreshToken
from backend.auth.service import AuthService
from backend.auth.rbac import Role
from backend.auth.security import hash_password, validate_password_strength
from backend.auth.audit import log_audit_event, AuditEvent

DISALLOWED_PASSWORDS = {
    "admin", "password", "superadmin", "administrator", "12345678",
    "password123", "admin1234", "superadmin2026!", "revenueguard",
    "root", "changeme", "default"
}


def generate_secure_password(length: int = 24) -> str:
    """Generates a high-entropy cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        valid, _ = validate_password_strength(pwd)
        if valid:
            return pwd


def bootstrap_super_admin(
    email: str,
    full_name: str,
    password: str,
    force: bool = False
) -> None:
    """Provisions the initial Super Admin user in the database."""
    clean_pwd = password.strip()
    if clean_pwd.lower() in DISALLOWED_PASSWORDS:
        print("[X] Security Error: Selected password is a known weak/default credential.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_super_admin = db.query(User).filter(
            User.role == Role.SUPER_ADMIN.value,
            User.is_active == True
        ).first()

        if existing_super_admin and not force:
            print(f"[!] A Super Admin user already exists ({existing_super_admin.email}).")
            print("    Use --rotate to rotate credentials, or --force to provision an additional Super Admin.")
            sys.exit(1)

        user = AuthService.create_user(
            db=db,
            email=email,
            password=clean_pwd,
            full_name=full_name,
            role=Role.SUPER_ADMIN.value,
            is_active=True
        )

        log_audit_event(
            AuditEvent.SUPER_ADMIN_BOOTSTRAP,
            actor_id=user.id,
            actor_email=user.email,
            action="BOOTSTRAP_PROVISION",
            status="SUCCESS",
            details={"email": user.email, "role": user.role}
        )

        print(f"[✓] Successfully provisioned Super Admin: {user.email} (ID: {user.id})")
        print("    Role: Super Admin | Platform permissions: Full Access")
    except Exception as exc:
        print(f"[X] Failed to provision Super Admin: {exc}")
        sys.exit(1)
    finally:
        db.close()


def rotate_super_admin_password(email: str, new_password: str) -> None:
    """Securely rotates an existing Super Admin's password and revokes all active sessions."""
    clean_pwd = new_password.strip()
    if clean_pwd.lower() in DISALLOWED_PASSWORDS:
        print("[X] Security Error: Selected password is a known weak/default credential.")
        sys.exit(1)

    valid, errors = validate_password_strength(clean_pwd)
    if not valid:
        print(f"[X] Password complexity validation failed: {'; '.join(errors)}")
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == email.lower().strip(),
            User.role == Role.SUPER_ADMIN.value
        ).first()

        if not user:
            print(f"[X] No active Super Admin found with email: {email}")
            sys.exit(1)

        user.hashed_password = hash_password(clean_pwd)
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Invalidate all active sessions / refresh tokens
        revoked_count = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})

        db.commit()

        log_audit_event(
            AuditEvent.PASSWORD_RESET,
            actor_id=user.id,
            actor_email=user.email,
            action="CREDENTIAL_ROTATION",
            status="SUCCESS",
            details={"revoked_sessions": revoked_count}
        )

        print(f"[✓] Super Admin password successfully rotated for: {user.email}")
        print(f"[✓] Revoked {revoked_count} active session(s) in accordance with credential rotation policy.")
    except Exception as exc:
        print(f"[X] Failed to rotate Super Admin password: {exc}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="RevenueGuard Super Admin Provisioning & Rotation CLI")
    parser.add_argument("--email", type=str, help="Super Admin email address")
    parser.add_argument("--name", type=str, default="Platform Administrator", help="Full name")
    parser.add_argument("--password", type=str, help="Password (will prompt securely if omitted)")
    parser.add_argument("--generate-password", action="store_true", help="Generate a cryptographically secure random password")
    parser.add_argument("--rotate", action="store_true", help="Rotate credentials of an existing Super Admin")
    parser.add_argument("--force", action="store_true", help="Force provisioning even if a Super Admin already exists")
    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Enter Super Admin email: ").strip()

    if args.generate_password:
        password = generate_secure_password()
        print("\n" + "=" * 60)
        print("GENUINE CRYPTOGRAPHIC CREDENTIAL GENERATED")
        print("=" * 60)
        print(f"Generated Password: {password}")
        print("Store this credential immediately in a secure corporate password vault.")
        print("=" * 60 + "\n")
    elif args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter secure password: ").strip()
        confirm = getpass.getpass("Confirm password: ").strip()
        if password != confirm:
            print("[X] Passwords do not match.")
            sys.exit(1)

    if args.rotate:
        rotate_super_admin_password(email=email, new_password=password)
    else:
        bootstrap_super_admin(email=email, full_name=args.name, password=password, force=args.force)


if __name__ == "__main__":
    main()
