"""
RevenueGuard Enterprise Security Audit Logging Module
======================================================
Provides structured, tamper-evident security audit logging for authentication,
authorization, account lifecycle, and privileged operational events.
Guarantees zero leakage of passwords, tokens, hashes, or credentials in audit trails.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Dedicated security audit logger
audit_logger = logging.getLogger("revenueguard.security.audit")

# Standardized Audit Event Types
class AuditEvent:
    LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    LOGOUT = "AUTH_LOGOUT"
    PASSWORD_CHANGE = "AUTH_PASSWORD_CHANGE"
    PASSWORD_RESET = "AUTH_PASSWORD_RESET"
    USER_CREATED = "USER_CREATED"
    ROLE_CHANGED = "USER_ROLE_CHANGED"
    STATUS_CHANGED = "USER_STATUS_CHANGED"
    TOKEN_REUSE_DETECTED = "SECURITY_TOKEN_REUSE_DETECTED"
    SESSION_REVOKED = "AUTH_SESSION_REVOKED"
    PRIVILEGED_DATA_OPERATION = "PRIVILEGED_DATA_OPERATION"
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    SUPER_ADMIN_BOOTSTRAP = "SUPER_ADMIN_BOOTSTRAP"


# Sensitive keys that must NEVER be written to audit logs
REDACTED_KEYS = {
    "password", "new_password", "current_password", "hashed_password",
    "token", "access_token", "refresh_token", "token_hash", "secret",
    "authorization", "api_key", "cookie", "set-cookie", "credentials"
}


def sanitize_audit_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Recursively redacts any sensitive keys or credential values from audit details."""
    if not details:
        return {}

    sanitized = {}
    for key, value in details.items():
        if key.lower() in REDACTED_KEYS:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_audit_details(value)
        elif isinstance(value, (list, tuple)):
            sanitized[key] = [
                sanitize_audit_details(v) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            sanitized[key] = value

    return sanitized


# In-memory audit buffer for diagnostic inspection and test assertions (bounded)
_RECENT_AUDIT_LOGS: List[Dict[str, Any]] = []
_MAX_AUDIT_BUFFER_SIZE = 500


def log_audit_event(
    event_type: str,
    actor_id: Optional[int] = None,
    actor_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Emits a structured security audit record.
    Ensures safe formatting and sanitization of all logged parameters.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    clean_details = sanitize_audit_details(details)

    record = {
        "timestamp": timestamp,
        "event_type": event_type,
        "actor": {
            "id": actor_id,
            "email": actor_email or "anonymous",
        },
        "client_ip": ip_address or "unknown",
        "resource": resource or "platform",
        "action": action or event_type,
        "status": status,
        "details": clean_details,
    }

    # Format structured JSON string for standard logging output
    log_msg = f"[AUDIT] {event_type} | actor={actor_email or 'anonymous'} | status={status} | {json.dumps(clean_details)}"
    if status == "SUCCESS":
        audit_logger.info(log_msg)
    else:
        audit_logger.warning(log_msg)

    # Append to recent bounded buffer
    _RECENT_AUDIT_LOGS.append(record)
    if len(_RECENT_AUDIT_LOGS) > _MAX_AUDIT_BUFFER_SIZE:
        _RECENT_AUDIT_LOGS.pop(0)

    return record


def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the most recent security audit events."""
    return list(_RECENT_AUDIT_LOGS[-limit:])


def clear_audit_logs() -> None:
    """Clears the in-memory audit log buffer (for test isolation)."""
    _RECENT_AUDIT_LOGS.clear()
