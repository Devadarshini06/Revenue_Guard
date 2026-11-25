"""
RevenueGuard Authentication & RBAC API Router
=============================================
Endpoints for login, logout, token rotation, user profile, password management,
and Super Admin user administration.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.auth.service import AuthService
from backend.auth.dependencies import get_current_user, require_permission
from backend.auth.rbac import Permission, get_role_permissions
from backend.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    CreateUserRequest,
    UpdateUserStatusRequest,
    UpdateUserRoleRequest,
    UserSummary,
    PermissionsResponse,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticates user with email/password and returns JWT access + refresh tokens."""
    client_ip = request.client.host if request.client else "unknown"
    try:
        user = AuthService.authenticate_user(
            db=db,
            email=payload.email,
            password=payload.password,
            identifier=f"{client_ip}:{payload.email.lower()}"
        )
        access_token, refresh_token, _ = AuthService.create_user_tokens(db=db, user=user)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            user=UserSummary.model_validate(user)
        )
    except PermissionError as exc:
        status_code = status.HTTP_429_TOO_MANY_REQUESTS if "Too many" in str(exc) else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes the active refresh token and terminates the session."""
    revoked = AuthService.revoke_refresh_token(db=db, raw_token=payload.refresh_token)
    return MessageResponse(message="Successfully logged out.", detail="Refresh token revoked.")


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Rotates refresh token and returns new short-lived access token and refresh token."""
    try:
        new_access, new_refresh, _ = AuthService.rotate_refresh_token(
            db=db,
            raw_token=payload.refresh_token
        )
        return RefreshTokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="Bearer"
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me", response_model=UserSummary)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns profile information for the currently authenticated user."""
    return UserSummary.model_validate(current_user)


@router.get("/permissions", response_model=PermissionsResponse)
def get_current_user_permissions(current_user: User = Depends(get_current_user)):
    """Returns the effective permissions for the current authenticated user's role."""
    perms = get_role_permissions(current_user.role)
    return PermissionsResponse(role=current_user.role, permissions=perms)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely updates the authenticated user's password."""
    try:
        AuthService.change_password(
            db=db,
            user=current_user,
            current_password=payload.current_password,
            new_password=payload.new_password
        )
        return MessageResponse(
            message="Password updated successfully.",
            detail="All active sessions have been invalidated for security."
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# -------------------------------------------------------------
# Super Admin User Administration Endpoints
# -------------------------------------------------------------

@router.get("/users", response_model=List[UserSummary])
def list_users(
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db)
):
    """Lists all platform users (Super Admin only)."""
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserSummary.model_validate(u) for u in users]


@router.post("/users", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db)
):
    """Creates a new platform user with designated role (Super Admin only)."""
    try:
        new_user = AuthService.create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role
        )
        return UserSummary.model_validate(new_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/users/{user_id}/status", response_model=UserSummary)
def update_user_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db)
):
    """Activates or deactivates a user (Super Admin only)."""
    try:
        updated = AuthService.update_user_status(
            db=db,
            user_id=user_id,
            is_active=payload.is_active,
            acting_user=current_user
        )
        return UserSummary.model_validate(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/users/{user_id}/role", response_model=UserSummary)
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db)
):
    """Assigns a new role to an existing user (Super Admin only)."""
    try:
        updated = AuthService.update_user_role(
            db=db,
            user_id=user_id,
            new_role=payload.role,
            acting_user=current_user
        )
        return UserSummary.model_validate(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
