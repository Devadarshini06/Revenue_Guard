"""
RevenueGuard Initial Super Admin Provisioning Utility
=====================================================
One-time controlled CLI bootstrapping process to create the initial platform Super Admin.
Does NOT create default passwords or expose public endpoints.
"""

import sys
import argparse
import getpass
from backend.database import SessionLocal, engine, Base
from backend.models import User
from backend.auth.service import AuthService
from backend.auth.rbac import Role


def bootstrap_super_admin(
    email: str,
    full_name: str,
    password: str,
    force: bool = False
) -> None:
    """Provisions the initial Super Admin user in the database."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_super_admin = db.query(User).filter(
            User.role == Role.SUPER_ADMIN.value,
            User.is_active == True
        ).first()

        if existing_super_admin and not force:
            print(f"[!] A Super Admin user already exists ({existing_super_admin.email}).")
            print("    Use --force to add an additional Super Admin account.")
            sys.exit(1)

        user = AuthService.create_user(
            db=db,
            email=email,
            password=password,
            full_name=full_name,
            role=Role.SUPER_ADMIN.value,
            is_active=True
        )
        print(f"[✓] Successfully provisioned Super Admin: {user.email} (ID: {user.id})")
        print("    Role: Super Admin | Platform permissions: Full Access")
    except Exception as exc:
        print(f"[X] Failed to provision Super Admin: {exc}")
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="RevenueGuard Super Admin Provisioning CLI")
    parser.add_argument("--email", type=str, help="Super Admin email address")
    parser.add_argument("--name", type=str, default="Platform Administrator", help="Full name")
    parser.add_argument("--password", type=str, help="Initial password (will prompt securely if omitted)")
    parser.add_argument("--force", action="store_true", help="Force provisioning even if a Super Admin already exists")
    args = parser.parse_args()

    email = args.email
    if not email:
        email = input("Enter Super Admin email: ").strip()

    name = args.name
    password = args.password
    if not password:
        password = getpass.getpass("Enter secure Super Admin password: ").strip()
        confirm = getpass.getpass("Confirm password: ").strip()
        if password != confirm:
            print("[X] Passwords do not match.")
            sys.exit(1)

    bootstrap_super_admin(email=email, full_name=name, password=password, force=args.force)


if __name__ == "__main__":
    main()
