"""
RevenueGuard Enterprise Authentication Service
=============================================
Orchestrates credential validation, token rotation, reuse detection,
and RBAC user lifecycle management.
"""

from datetime import datetime, timezone
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from backend.models import User, RefreshToken
from backend.auth.security import hash_password, verify_password, validate_password_strength
from backend.auth.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    get_refresh_token_expiration,
)
from backend.auth.rbac import ALL_ROLES, Role, get_role_permissions
from backend.auth.rate_limiter import is_rate_limited, record_failed_attempt, reset_attempts


class AuthService:
    """Enterprise authentication and user session management service."""

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
        identifier: str = ""
    ) -> User:
        """
        Validates user credentials against stored Argon2id hashes with rate limiting.
        Uses generic error messages to eliminate account enumeration vectors.
        """
        throttle_key = identifier or email.lower().strip()
        limited, retry_after = is_rate_limited(throttle_key)
        if limited:
            raise PermissionError(f"Too many failed login attempts. Please try again in {retry_after} seconds.")

        clean_email = email.lower().strip()
        user = db.query(User).filter(User.email == clean_email).first()

        # Dummy verify to equalize timing against timing attacks if user does not exist
        if not user:
            record_failed_attempt(throttle_key)
            verify_password("dummy-password", "$argon2id$v=19$m=65536,t=2,p=2$dummy$dummy")
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            record_failed_attempt(throttle_key)
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            record_failed_attempt(throttle_key)
            raise PermissionError("Account is deactivated. Please contact your system administrator.")

        # Successful authentication: reset rate limiter and update last login
        reset_attempts(throttle_key)
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def create_user_tokens(db: Session, user: User) -> Tuple[str, str, datetime]:
        """
        Generates access token and persistent refresh token.
        Returns (access_token, raw_refresh_token, expires_at).
        """
        access_token = create_access_token(user_id=user.id, email=user.email, role=user.role)

        raw_refresh = generate_refresh_token()
        token_hash = hash_refresh_token(raw_refresh)
        expires_at = get_refresh_token_expiration()

        db_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(db_token)
        db.commit()

        return (access_token, raw_refresh, expires_at)

    @staticmethod
    def rotate_refresh_token(db: Session, raw_token: str) -> Tuple[str, str, User]:
        """
        Rotates an existing refresh token with reuse detection.
        If a revoked token is presented, invalidates all tokens for that user (token theft defense).
        Returns (new_access_token, new_raw_refresh_token, user).
        """
        token_hash = hash_refresh_token(raw_token)
        db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

        if not db_token:
            raise ValueError("Invalid refresh token.")

        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user or not user.is_active:
            raise ValueError("User account is inactive or not found.")

        # Refresh token reuse detection
        if db_token.is_revoked:
            # Revoke all active sessions for this user as a security safeguard
            db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
            db.commit()
            raise PermissionError("Refresh token has already been used. All sessions have been revoked for security.")

        if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            db_token.is_revoked = True
            db.commit()
            raise ValueError("Refresh token has expired. Please log in again.")

        # Revoke the old token
        db_token.is_revoked = True

        # Generate new token pair
        new_access = create_access_token(user_id=user.id, email=user.email, role=user.role)
        new_raw_refresh = generate_refresh_token()
        new_hash = hash_refresh_token(new_raw_refresh)
        new_expires = get_refresh_token_expiration()

        db_token.replaced_by = new_hash

        new_db_token = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires,
            is_revoked=False
        )
        db.add(new_db_token)
        db.commit()

        return (new_access, new_raw_refresh, user)

    @staticmethod
    def revoke_refresh_token(db: Session, raw_token: str) -> bool:
        """Revokes a refresh token upon user logout."""
        token_hash = hash_refresh_token(raw_token)
        db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
            return True
        return False

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        current_password: str,
        new_password: str
    ) -> None:
        """Changes user password after validating current password and strength rules."""
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect.")

        valid, errors = validate_password_strength(new_password)
        if not valid:
            raise ValueError(f"Password does not meet complexity requirements: {'; '.join(errors)}")

        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Invalidate existing refresh tokens upon password change for session security
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
        db.commit()

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        role: str,
        is_active: bool = True
    ) -> User:
        """Creates a new platform user."""
        clean_email = email.lower().strip()
        existing = db.query(User).filter(User.email == clean_email).first()
        if existing:
            raise ValueError(f"User with email '{clean_email}' already exists.")

        if role not in ALL_ROLES:
            raise ValueError(f"Invalid role '{role}'. Allowed roles are: {', '.join(ALL_ROLES)}")

        valid, errors = validate_password_strength(password)
        if not valid:
            raise ValueError(f"Password does not meet complexity requirements: {'; '.join(errors)}")

        hashed = hash_password(password)
        user = User(
            email=clean_email,
            hashed_password=hashed,
            full_name=full_name.strip(),
            role=role,
            is_active=is_active,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_status(db: Session, user_id: int, is_active: bool, acting_user: User) -> User:
        """Activates or deactivates a user account."""
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            raise ValueError("Target user not found.")

        if target.id == acting_user.id and not is_active:
            raise ValueError("Administrators cannot deactivate their own account.")

        target.is_active = is_active
        target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if not is_active:
            # Invalidate all active sessions for deactivated user
            db.query(RefreshToken).filter(RefreshToken.user_id == target.id).update({"is_revoked": True})
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: str, acting_user: User) -> User:
        """Updates a user's role with privilege escalation prevention."""
        if new_role not in ALL_ROLES:
            raise ValueError(f"Invalid role '{new_role}'. Allowed: {', '.join(ALL_ROLES)}")

        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            raise ValueError("Target user not found.")

        # Prevent demoting the last active Super Admin
        if target.role == Role.SUPER_ADMIN.value and new_role != Role.SUPER_ADMIN.value:
            super_admin_count = db.query(User).filter(
                User.role == Role.SUPER_ADMIN.value,
                User.is_active == True
            ).count()
            if super_admin_count <= 1:
                raise ValueError("Cannot demote the last active Super Admin on the platform.")

        target.role = new_role
        target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(target)
        return target
