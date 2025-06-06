"""
🔐 User Role-Based Access Control (RBAC) System
Secure role management for raqibtech.com customer support platform
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """Enumeration of user roles with hierarchical permissions"""
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    GUEST = "guest"

class Permission(Enum):
    """Granular permissions for different operations"""
    # Customer Data Access
    READ_OWN_DATA = "read_own_data"
    UPDATE_OWN_DATA = "update_own_data"

    # Order Management
    READ_OWN_ORDERS = "read_own_orders"
    CANCEL_OWN_ORDERS = "cancel_own_orders"

    # Cross-Customer Operations (Staff Only)
    READ_ALL_CUSTOMERS = "read_all_customers"
    READ_ALL_ORDERS = "read_all_orders"
    UPDATE_ANY_ORDER = "update_any_order"

    # Business Analytics (Admin Only)
    VIEW_BUSINESS_ANALYTICS = "view_business_analytics"
    VIEW_REVENUE_DATA = "view_revenue_data"
    VIEW_CUSTOMER_RANKINGS = "view_customer_rankings"

    # System Administration
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"

    # Product Management
    READ_PRODUCTS = "read_products"
    MANAGE_PRODUCTS = "manage_products"

@dataclass
class UserRoleInfo:
    """Complete user role information"""
    role: UserRole
    permissions: Set[Permission]
    description: str
    max_data_access_level: str

class RoleBasedAccessControl:
    """🔐 Role-Based Access Control Manager"""

    # 🔒 PERMISSION MATRIX - Define what each role can do
    ROLE_PERMISSIONS = {
        UserRole.GUEST: {
            Permission.READ_PRODUCTS,
        },

        UserRole.CUSTOMER: {
            Permission.READ_OWN_DATA,
            Permission.UPDATE_OWN_DATA,
            Permission.READ_OWN_ORDERS,
            Permission.CANCEL_OWN_ORDERS,
            Permission.READ_PRODUCTS,
        },

        UserRole.SUPPORT_AGENT: {
            Permission.READ_OWN_DATA,
            Permission.UPDATE_OWN_DATA,
            Permission.READ_OWN_ORDERS,
            Permission.CANCEL_OWN_ORDERS,
            Permission.READ_PRODUCTS,
            Permission.READ_ALL_CUSTOMERS,
            Permission.READ_ALL_ORDERS,
            Permission.UPDATE_ANY_ORDER,
        },

        UserRole.ADMIN: {
            Permission.READ_OWN_DATA,
            Permission.UPDATE_OWN_DATA,
            Permission.READ_OWN_ORDERS,
            Permission.CANCEL_OWN_ORDERS,
            Permission.READ_PRODUCTS,
            Permission.MANAGE_PRODUCTS,
            Permission.READ_ALL_CUSTOMERS,
            Permission.READ_ALL_ORDERS,
            Permission.UPDATE_ANY_ORDER,
            Permission.VIEW_BUSINESS_ANALYTICS,
            Permission.VIEW_REVENUE_DATA,
            Permission.VIEW_CUSTOMER_RANKINGS,
        },

        UserRole.SUPER_ADMIN: {
            # Super admin has all permissions
            permission for permission in Permission
        }
    }

    @classmethod
    def get_user_role_info(cls, role: UserRole) -> UserRoleInfo:
        """Get complete role information"""
        permissions = cls.ROLE_PERMISSIONS.get(role, set())

        descriptions = {
            UserRole.GUEST: "Unauthenticated user with basic product browsing access",
            UserRole.CUSTOMER: "Regular customer with access to own data only",
            UserRole.SUPPORT_AGENT: "Customer support agent with cross-customer read access",
            UserRole.ADMIN: "Administrator with business analytics and management access",
            UserRole.SUPER_ADMIN: "Super administrator with full system access"
        }

        access_levels = {
            UserRole.GUEST: "Public data only",
            UserRole.CUSTOMER: "Own data only",
            UserRole.SUPPORT_AGENT: "Cross-customer read access",
            UserRole.ADMIN: "Full business analytics",
            UserRole.SUPER_ADMIN: "Full system access"
        }

        return UserRoleInfo(
            role=role,
            permissions=permissions,
            description=descriptions.get(role, "Unknown role"),
            max_data_access_level=access_levels.get(role, "No access")
        )

    @classmethod
    def has_permission(cls, user_role: UserRole, permission: Permission) -> bool:
        """Check if a user role has a specific permission"""
        role_permissions = cls.ROLE_PERMISSIONS.get(user_role, set())
        return permission in role_permissions

    @classmethod
    def can_access_business_analytics(cls, user_role: UserRole) -> bool:
        """Check if user can access business analytics"""
        return cls.has_permission(user_role, Permission.VIEW_BUSINESS_ANALYTICS)

    @classmethod
    def can_access_cross_customer_data(cls, user_role: UserRole) -> bool:
        """Check if user can access other customers' data"""
        return cls.has_permission(user_role, Permission.READ_ALL_CUSTOMERS)

    @classmethod
    def get_allowed_query_scope(cls, user_role: UserRole, customer_id: Optional[int] = None) -> Dict[str, any]:
        """Get the data scope a user role can access"""
        if user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            return {
                "scope": "platform_wide",
                "customer_filter": None,
                "business_analytics": True,
                "cross_customer": True
            }
        elif user_role == UserRole.SUPPORT_AGENT:
            return {
                "scope": "cross_customer",
                "customer_filter": None,
                "business_analytics": False,
                "cross_customer": True
            }
        elif user_role == UserRole.CUSTOMER:
            return {
                "scope": "customer_specific",
                "customer_filter": customer_id,
                "business_analytics": False,
                "cross_customer": False
            }
        else:  # GUEST
            return {
                "scope": "public_only",
                "customer_filter": None,
                "business_analytics": False,
                "cross_customer": False
            }

    @classmethod
    def validate_query_authorization(cls, user_role: UserRole, query_type: str,
                                   customer_id: Optional[int], target_customer_id: Optional[int] = None) -> Dict[str, any]:
        """Validate if a query is authorized for the user role"""

        query_scope = cls.get_allowed_query_scope(user_role, customer_id)

        # Business analytics queries
        if query_type in ["customer_analysis", "revenue_insights"] and target_customer_id is None:
            if not query_scope["business_analytics"]:
                return {
                    "authorized": False,
                    "reason": f"Role '{user_role.value}' cannot access business analytics",
                    "alternative": "Request access from administrator or query your own data"
                }

        # Cross-customer queries
        if target_customer_id and target_customer_id != customer_id:
            if not query_scope["cross_customer"]:
                return {
                    "authorized": False,
                    "reason": f"Role '{user_role.value}' cannot access other customers' data",
                    "alternative": "You can only access your own account data"
                }

        # Customer-specific queries without authentication
        if query_type in ["order_analytics", "revenue_insights"] and customer_id is None:
            if user_role == UserRole.GUEST:
                return {
                    "authorized": False,
                    "reason": "Authentication required for personal data access",
                    "alternative": "Please log in to access your account information"
                }

        return {
            "authorized": True,
            "scope": query_scope,
            "reason": "Query authorized for user role"
        }

def determine_user_role(session_context: Dict[str, any]) -> UserRole:
    """Determine user role from session context"""

    # Check if user is authenticated
    user_authenticated = session_context.get('user_authenticated', False)

    if not user_authenticated:
        return UserRole.GUEST

    # Check for explicit role in session
    user_role = session_context.get('user_role')
    if user_role:
        try:
            return UserRole(user_role.lower())
        except ValueError:
            logger.warning(f"Invalid user role in session: {user_role}")

    # Check for admin indicators
    is_admin = session_context.get('is_admin', False)
    is_staff = session_context.get('is_staff', False)

    if is_admin:
        return UserRole.ADMIN
    elif is_staff:
        return UserRole.SUPPORT_AGENT

    # Default to customer for authenticated users
    if session_context.get('customer_id'):
        return UserRole.CUSTOMER

    return UserRole.GUEST

def get_role_appropriate_response(user_role: UserRole, denied_operation: str) -> str:
    """Get appropriate, empathetic response when access is denied"""

    # Create personalized responses based on the specific operation requested
    business_analytics_responses = {
        UserRole.GUEST: """
I appreciate your interest in our business insights! 📊 However, this type of information is confidential and only available to our internal team members.

**What I can help you with instead:**
• Browse our amazing product catalog 🛍️
• Get product information and prices 💰
• Learn about our services and policies 📋
• Create an account for personalized shopping experience 👤

Would you like me to show you our popular products or help you find something specific? I'm here to make your shopping experience wonderful! 😊
""",

        UserRole.CUSTOMER: """
Thank you for your curiosity about our business performance! 📈 I can see you're engaged with our platform, which means a lot to us.

However, as your customer support agent, I need to protect the privacy of all our customers. Business analytics contain sensitive information about other customers' purchases and our company's internal data.

**What I can absolutely help you with:**
• Your complete order history and tracking 📦
• Your spending summaries and loyalty points 💎
• Personalized product recommendations based on your preferences 🎯
• Account settings and delivery preferences ⚙️
• Any questions about your past or current orders 🛒

I'm here to give you the best possible service for YOUR account! What would you like to know about your shopping experience with us? 💙
""",

        UserRole.SUPPORT_AGENT: """
I understand you'd like to access business analytics data! 📊 As a support agent, you have excellent access to help all our customers, but business intelligence reports require administrative privileges to ensure data security and compliance.

**Your current access includes:**
• All customer order information for support 👥
• Customer account management capabilities 🔧
• Order modification and tracking tools 📦

For business analytics access, please reach out to your administrator or management team. They can review your request and provide the appropriate permissions if needed.

Is there anything else I can help you with regarding customer support? 🤝
""",

        UserRole.ADMIN: """
This specific operation requires super administrator privileges for enhanced security compliance. 🔐

Please contact your system administrator or the tech team for this level of access.

Meanwhile, you have full access to business analytics, customer management, and reporting tools available to administrators.

Is there anything else I can assist you with? 🚀
"""
    }

    # Check if this is a business analytics request
    if "business analytics" in denied_operation.lower() or "analytics" in denied_operation.lower():
        return business_analytics_responses.get(user_role,
            "I understand your interest, but access to this information is restricted. Please contact support for assistance. 🔐")

    # Fallback responses for other types of denied operations
    general_responses = {
        UserRole.GUEST: f"I'd be happy to help! To access {denied_operation}, please log in to your raqibtech.com account first. Once you're logged in, I'll have much more ways to assist you! 😊",

        UserRole.CUSTOMER: f"I understand you're interested in {denied_operation}, but as your customer support agent, I can only provide information about your own account for privacy and security reasons. I'd be happy to help with your personal account details and shopping needs! 💙",

        UserRole.SUPPORT_AGENT: f"You have support agent access, but {denied_operation} requires administrator privileges. Please contact your system administrator for this type of access. 🔐",

        UserRole.ADMIN: f"This operation requires super administrator privileges. Please contact your system administrator. 🔐"
    }

    return general_responses.get(user_role, "Access denied for this operation. Please contact support for assistance. 🔐")
