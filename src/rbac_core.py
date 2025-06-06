"""
RBAC Core System - Seamless Integration
Lightweight role-based access control that fits into existing workflow
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles matching database enum"""
    GUEST = "guest"
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class Permission(Enum):
    """System permissions"""
    READ_OWN_DATA = "read_own_data"
    READ_ALL_CUSTOMER_DATA = "read_all_customer_data"
    VIEW_BUSINESS_ANALYTICS = "view_business_analytics"
    GENERATE_REPORTS = "generate_reports"
    VIEW_PLATFORM_STATS = "view_platform_stats"
    MANAGE_CUSTOMER_ACCOUNTS = "manage_customer_accounts"
    SYSTEM_ADMINISTRATION = "system_administration"
    MODIFY_ORDERS = "modify_orders"
    VIEW_CROSS_CUSTOMER_DATA = "view_cross_customer_data"
    EXPORT_DATA = "export_data"
    VIEW_REVENUE_DATA = "view_revenue_data"
    MANAGE_STAFF_ACCOUNTS = "manage_staff_accounts"

@dataclass
class UserSession:
    """User session data for RBAC"""
    user_id: int
    name: str
    email: str
    role: UserRole
    is_staff: bool = False
    is_admin: bool = False
    permissions: Set[Permission] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ROLE_PERMISSIONS.get(self.role, set())

# Role-Permission Matrix (Hierarchical)
ROLE_PERMISSIONS = {
    UserRole.GUEST: {
        # No data access permissions for guests
    },
    UserRole.CUSTOMER: {
        Permission.READ_OWN_DATA,
    },
    UserRole.SUPPORT_AGENT: {
        Permission.READ_OWN_DATA,
        Permission.READ_ALL_CUSTOMER_DATA,
        Permission.MANAGE_CUSTOMER_ACCOUNTS,
        Permission.MODIFY_ORDERS,
    },
    UserRole.ADMIN: {
        Permission.READ_OWN_DATA,
        Permission.READ_ALL_CUSTOMER_DATA,
        Permission.VIEW_BUSINESS_ANALYTICS,
        Permission.GENERATE_REPORTS,
        Permission.VIEW_PLATFORM_STATS,
        Permission.MANAGE_CUSTOMER_ACCOUNTS,
        Permission.VIEW_CROSS_CUSTOMER_DATA,
        Permission.EXPORT_DATA,
        Permission.VIEW_REVENUE_DATA,
        Permission.MODIFY_ORDERS,
    },
    UserRole.SUPER_ADMIN: {
        # Super admin has all permissions
        Permission.READ_OWN_DATA,
        Permission.READ_ALL_CUSTOMER_DATA,
        Permission.VIEW_BUSINESS_ANALYTICS,
        Permission.GENERATE_REPORTS,
        Permission.VIEW_PLATFORM_STATS,
        Permission.MANAGE_CUSTOMER_ACCOUNTS,
        Permission.SYSTEM_ADMINISTRATION,
        Permission.VIEW_CROSS_CUSTOMER_DATA,
        Permission.EXPORT_DATA,
        Permission.VIEW_REVENUE_DATA,
        Permission.MODIFY_ORDERS,
        Permission.MANAGE_STAFF_ACCOUNTS,
    }
}

class RBACManager:
    """Main RBAC manager - integrates with your existing Flask app"""

    def __init__(self):
        self.current_session: Optional[UserSession] = None

    def create_session_from_customer_data(self, customer_data: Dict) -> UserSession:
        """Create session from your existing customer data structure"""
        try:
            # Extract role from your customer data
            role_str = customer_data.get('user_role', 'customer')
            role = UserRole(role_str)

            session = UserSession(
                user_id=customer_data['customer_id'],
                name=customer_data['name'],
                email=customer_data['email'],
                role=role,
                is_staff=customer_data.get('is_staff', False),
                is_admin=customer_data.get('is_admin', False)
            )

            logger.info(f"Created RBAC session for {session.name} ({session.role.value})")
            return session

        except Exception as e:
            logger.error(f"Failed to create RBAC session: {e}")
            # Return guest session as fallback
            return UserSession(
                user_id=0,
                name="Guest",
                email="",
                role=UserRole.GUEST
            )

    def set_current_session(self, session: UserSession):
        """Set current user session"""
        self.current_session = session

    def has_permission(self, permission: Permission, user_session: Optional[UserSession] = None) -> bool:
        """Check if user has specific permission"""
        session = user_session or self.current_session
        if not session:
            return False

        return permission in session.permissions

    def require_permission(self, permission: Permission, user_session: Optional[UserSession] = None) -> bool:
        """Require permission or raise error"""
        if not self.has_permission(permission, user_session):
            session = user_session or self.current_session
            role = session.role.value if session else "unknown"
            raise PermissionError(f"Access denied: {permission.value} required (current role: {role})")
        return True

    def can_access_customer_data(self, target_customer_id: int, user_session: Optional[UserSession] = None) -> bool:
        """Check if user can access specific customer's data"""
        session = user_session or self.current_session
        if not session:
            return False

        # Super admin and admin can access all data
        if session.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            return True

        # Support agents can access all customer data
        if session.role == UserRole.SUPPORT_AGENT:
            return True

        # Customers can only access their own data
        if session.role == UserRole.CUSTOMER:
            return session.user_id == target_customer_id

        return False

    def can_view_business_analytics(self, user_session: Optional[UserSession] = None) -> bool:
        """Check if user can view business analytics"""
        session = user_session or self.current_session
        if not session:
            return False

        return session.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

    def get_data_filter_context(self, user_session: Optional[UserSession] = None) -> Dict:
        """Get data filtering context for database queries"""
        session = user_session or self.current_session
        if not session:
            return {"role": "guest", "user_id": None, "can_access_all": False}

        return {
            "role": session.role.value,
            "user_id": session.user_id,
            "can_access_all": session.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SUPPORT_AGENT],
            "can_view_analytics": self.can_view_business_analytics(session),
            "permissions": [p.value for p in session.permissions]
        }

    def get_session_info(self) -> Dict:
        """Get current session info for frontend"""
        if not self.current_session:
            return {"authenticated": False, "role": "guest"}

        return {
            "authenticated": True,
            "user_id": self.current_session.user_id,
            "name": self.current_session.name,
            "email": self.current_session.email,
            "role": self.current_session.role.value,
            "is_staff": self.current_session.is_staff,
            "is_admin": self.current_session.is_admin,
            "permissions": [p.value for p in self.current_session.permissions]
        }

# Global RBAC manager instance
rbac_manager = RBACManager()

def get_rbac_manager() -> RBACManager:
    """Get the global RBAC manager"""
    return rbac_manager

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            rbac_manager.require_permission(permission)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            session = rbac_manager.current_session
            if not session or session.role != role:
                raise PermissionError(f"Access denied - {role.value} role required")
            return func(*args, **kwargs)
        return wrapper
    return decorator
