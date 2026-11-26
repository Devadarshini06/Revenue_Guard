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
from backend.auth.audit import log_audit_event, AuditEvent


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
            log_audit_event(
                AuditEvent.LOGIN_FAILED,
                actor_email=clean_email,
                ip_address=identifier,
                status="FAILED",
                details={"reason": "Invalid credentials"}
            )
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            record_failed_attempt(throttle_key)
            log_audit_event(
                AuditEvent.LOGIN_FAILED,
                actor_id=user.id,
                actor_email=user.email,
                ip_address=identifier,
                status="FAILED",
                details={"reason": "Invalid credentials"}
            )
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            record_failed_attempt(throttle_key)
            log_audit_event(
                AuditEvent.LOGIN_FAILED,
                actor_id=user.id,
                actor_email=user.email,
                ip_address=identifier,
                status="FAILED",
                details={"reason": "Account deactivated"}
            )
            raise PermissionError("Account is deactivated. Please contact your system administrator.")

        # Successful authentication: reset rate limiter and update last login
        reset_attempts(throttle_key)
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(user)

        log_audit_event(
            AuditEvent.LOGIN_SUCCESS,
            actor_id=user.id,
            actor_email=user.email,
            ip_address=identifier,
            status="SUCCESS",
            details={"role": user.role}
        )

        return user

    @staticmethod
    def create_user_tokens(db: Session, user: User) -> Tuple[str, str, datetime]:
        """
        Generates access token and persistent refresh token.
        Returns (access_token, raw_refresh_token, expires_at).
        """
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            token_version=user.token_version or 1,
        )

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
            # Revoke all active sessions (refresh tokens + access tokens) for this user
            user.token_version = (user.token_version or 1) + 1
            user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
            db.commit()
            log_audit_event(
                AuditEvent.TOKEN_REUSE_DETECTED,
                actor_id=user.id,
                actor_email=user.email,
                status="REVOCATION_ALERT",
                details={"action": "All active user sessions and access tokens revoked due to reuse detection"}
            )
            raise PermissionError("Refresh token has already been used. All sessions have been revoked for security.")

        if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            db_token.is_revoked = True
            db.commit()
            raise ValueError("Refresh token has expired. Please log in again.")

        # Revoke the old token
        db_token.is_revoked = True

        # Generate new token pair
        new_access = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            token_version=user.token_version or 1,
        )
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
    def logout_user(db: Session, user: User, raw_token: Optional[str] = None) -> None:
        """Revokes the presented refresh token (if any) and bumps token_version to invalidate access tokens."""
        if raw_token:
            token_hash = hash_refresh_token(raw_token)
            db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
            if db_token:
                db_token.is_revoked = True
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            db_user.token_version = (db_user.token_version or 1) + 1
            db_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

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
        user.token_version = (user.token_version or 1) + 1
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Invalidate existing refresh tokens upon password change for session security
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"is_revoked": True})
        db.commit()

        log_audit_event(
            AuditEvent.PASSWORD_CHANGE,
            actor_id=user.id,
            actor_email=user.email,
            status="SUCCESS",
            details={"action": "Password changed and all existing sessions revoked"}
        )

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        role: str,
        is_active: bool = True,
        acting_user: Optional[User] = None
    ) -> User:
        """Creates a new platform user with privilege escalation guards."""
        clean_email = email.lower().strip()
        existing = db.query(User).filter(User.email == clean_email).first()
        if existing:
            raise ValueError(f"User with email '{clean_email}' already exists.")

        if role not in ALL_ROLES:
            raise ValueError(f"Invalid role '{role}'. Allowed roles are: {', '.join(ALL_ROLES)}")

        # Privilege escalation prevention: only Super Admin can create another Super Admin
        if role == Role.SUPER_ADMIN.value and acting_user and acting_user.role != Role.SUPER_ADMIN.value:
            raise ValueError("Only Super Admins can provision Super Admin accounts.")

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

        log_audit_event(
            AuditEvent.USER_CREATED,
            actor_id=acting_user.id if acting_user else user.id,
            actor_email=acting_user.email if acting_user else clean_email,
            status="SUCCESS",
            details={"created_user_id": user.id, "created_email": clean_email, "role": role}
        )

        return user

    @staticmethod
    def update_user_status(db: Session, user_id: int, is_active: bool, acting_user: User) -> User:
        """Activates or deactivates a user account with Super Admin protection."""
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            raise ValueError("Target user not found.")

        if target.id == acting_user.id and not is_active:
            raise ValueError("Administrators cannot deactivate their own account.")

        # Super Admin protection
        if target.role == Role.SUPER_ADMIN.value and acting_user.role != Role.SUPER_ADMIN.value:
            raise ValueError("Only Super Admins can modify Super Admin account status.")

        if target.role == Role.SUPER_ADMIN.value and not is_active:
            super_admin_count = db.query(User).filter(
                User.role == Role.SUPER_ADMIN.value,
                User.is_active == True
            ).count()
            if super_admin_count <= 1:
                raise ValueError("Cannot deactivate the last active Super Admin on the platform.")

        target.is_active = is_active
        target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if not is_active:
            # Invalidate all active sessions and access tokens for deactivated user
            target.token_version = (target.token_version or 1) + 1
            db.query(RefreshToken).filter(RefreshToken.user_id == target.id).update({"is_revoked": True})
        db.commit()
        db.refresh(target)

        log_audit_event(
            AuditEvent.STATUS_CHANGED,
            actor_id=acting_user.id,
            actor_email=acting_user.email,
            status="SUCCESS",
            details={"target_user_id": target.id, "target_email": target.email, "is_active": is_active}
        )

        return target

    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: str, acting_user: User) -> User:
        """Updates a user's role with privilege escalation prevention."""
        if new_role not in ALL_ROLES:
            raise ValueError(f"Invalid role '{new_role}'. Allowed: {', '.join(ALL_ROLES)}")

        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            raise ValueError("Target user not found.")

        # Non-Super-Admins cannot touch Super Admin accounts
        if target.role == Role.SUPER_ADMIN.value and acting_user.role != Role.SUPER_ADMIN.value:
            raise ValueError("Only Super Admins can alter Super Admin accounts.")

        # Non-Super-Admins cannot promote anyone to Super Admin
        if new_role == Role.SUPER_ADMIN.value and acting_user.role != Role.SUPER_ADMIN.value:
            raise ValueError("Only Super Admins can promote users to Super Admin.")

        # Prevent demoting the last active Super Admin
        if target.role == Role.SUPER_ADMIN.value and new_role != Role.SUPER_ADMIN.value:
            super_admin_count = db.query(User).filter(
                User.role == Role.SUPER_ADMIN.value,
                User.is_active == True
            ).count()
            if super_admin_count <= 1:
                raise ValueError("Cannot demote the last active Super Admin on the platform.")

        old_role = target.role
        target.role = new_role
        target.token_version = (target.token_version or 1) + 1
        target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(target)

        log_audit_event(
            AuditEvent.ROLE_CHANGED,
            actor_id=acting_user.id,
            actor_email=acting_user.email,
            status="SUCCESS",
            details={
                "target_user_id": target.id,
                "target_email": target.email,
                "old_role": old_role,
                "new_role": new_role
            }
        )

        return target

    @staticmethod
    def revoke_user_sessions(db: Session, user_id: int, acting_user: User) -> User:
        """Administratively revokes all active access and refresh tokens for a target user."""
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            raise ValueError("Target user not found.")

        if target.role == Role.SUPER_ADMIN.value and acting_user.role != Role.SUPER_ADMIN.value:
            raise ValueError("Only Super Admins can revoke Super Admin sessions.")

        target.token_version = (target.token_version or 1) + 1
        target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        revoked_count = db.query(RefreshToken).filter(
            RefreshToken.user_id == target.id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        db.commit()
        db.refresh(target)

        log_audit_event(
            AuditEvent.SESSION_REVOKED,
            actor_id=acting_user.id,
            actor_email=acting_user.email,
            status="SUCCESS",
            details={
                "target_user_id": target.id,
                "target_email": target.email,
                "revoked_refresh_tokens": revoked_count,
                "new_token_version": target.token_version,
            }
        )

        return target
