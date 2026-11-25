"""
RevenueGuard Role-Based Access Control (RBAC) Architecture
==========================================================
Defines enterprise roles, granular permissions, and authorization matrix.
"""

from enum import Enum
from typing import Dict, Set, List


class Role(str, Enum):
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin"
    ANALYST = "Analyst"
    VIEWER = "Viewer"


class Permission(str, Enum):
    VIEW_ANALYTICS = "view:analytics"       # Dashboards, KPIs, analytics charts, filters
    EXPORT_REPORTS = "export:reports"       # CSV / Excel / Power BI downloads
    EXECUTE_SQL = "execute:sql"             # Read-only analytical SQL query execution
    MANAGE_DATA = "manage:data"             # Ingest CSV/Excel datasets, view upload logs
    MANAGE_USERS = "manage:users"           # User provisioning, deactivation, role assignments
    MANAGE_SYSTEM = "manage:system"         # Platform settings, database reseed/restore


# Matrix mapping each role to its authorized set of permissions
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    Role.SUPER_ADMIN.value: {
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
        Permission.EXECUTE_SQL,
        Permission.MANAGE_DATA,
        Permission.MANAGE_USERS,
        Permission.MANAGE_SYSTEM,
    },
    Role.ADMIN.value: {
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
        Permission.EXECUTE_SQL,
        Permission.MANAGE_DATA,
    },
    Role.ANALYST.value: {
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
        Permission.EXECUTE_SQL,
    },
    Role.VIEWER.value: {
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
    },
}

ALL_ROLES = [r.value for r in Role]


def has_permission(role: str, permission: Permission) -> bool:
    """Verifies whether a given role holds the specified permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms


def get_role_permissions(role: str) -> List[str]:
    """Returns sorted list of permission keys for a given role."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return sorted([p.value for p in perms])

