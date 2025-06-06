"""
🔐 Authentication Manager for RaqibTech Customer Support System
Integrates with existing database and provides role-based session management
"""

import hashlib
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from config.database_config import DatabaseManager
from src.user_roles import UserRole, determine_user_role

logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """User session data structure"""
    customer_id: int
    name: str
    email: str
    user_role: UserRole
    is_staff: bool
    is_admin: bool
    permissions: list
    access_description: str
    session_token: str
    login_time: datetime

class AuthenticationManager:
    """🔐 Manages user authentication and role-based sessions"""

    def __init__(self):
        """Initialize authentication manager with database connection"""
        self.db_manager = DatabaseManager()
        self.active_sessions = {}  # In-memory session store

    def authenticate_user(self, email: str, password: str = None) -> Tuple[bool, Optional[UserSession], str]:
        """
        Authenticate user and create session

        Args:
            email: User email address
            password: User password (for future password implementation)

        Returns:
            (success, user_session, message)
        """
        try:
            # For now, we'll use email-based authentication
            # In production, add proper password hashing and verification

            # Query user data using the database function
            query = "SELECT * FROM authenticate_user(%s)"
            results = self.db_manager.execute_query(query, (email,))

            if not results:
                return False, None, "User not found or account inactive"

            user_data = results[0]

            # Create session token
            session_token = self._generate_session_token()

            # Determine user role
            user_role = UserRole(user_data['user_role'])

            # Create user session
            user_session = UserSession(
                customer_id=user_data['customer_id'],
                name=user_data['name'],
                email=user_data['email'],
                user_role=user_role,
                is_staff=user_data['is_staff'],
                is_admin=user_data['is_admin'],
                permissions=user_data['permissions'] or [],
                access_description=user_data['access_description'],
                session_token=session_token,
                login_time=datetime.now()
            )

            # Store session
            self.active_sessions[session_token] = user_session

            logger.info(f"✅ User authenticated: {email} as {user_role.value}")
            return True, user_session, f"Welcome {user_data['name']}! Logged in as {user_session.access_description}"

        except Exception as e:
            logger.error(f"❌ Authentication failed for {email}: {e}")
            return False, None, f"Authentication error: {str(e)}"

    def get_session_context(self, session_token: str) -> Optional[Dict]:
        """
        Get session context for RBAC system

        Args:
            session_token: Session token from login

        Returns:
            Session context dictionary for enhanced_db_querying
        """
        if session_token not in self.active_sessions:
            return None

        session = self.active_sessions[session_token]

        # Return session context in the format expected by enhanced_db_querying
        return {
            "user_authenticated": True,
            "customer_id": session.customer_id,
            "customer_name": session.name,
            "customer_email": session.email,
            "user_role": session.user_role.value,
            "is_staff": session.is_staff,
            "is_admin": session.is_admin,
            "permissions": session.permissions,
            "session_id": session_token,
            "login_time": session.login_time.isoformat()
        }

    def logout_user(self, session_token: str) -> bool:
        """
        Logout user and clear session

        Args:
            session_token: Session token to logout

        Returns:
            Success status
        """
        if session_token in self.active_sessions:
            user_email = self.active_sessions[session_token].email
            del self.active_sessions[session_token]
            logger.info(f"🚪 User logged out: {user_email}")
            return True
        return False

    def require_role(self, session_token: str, required_role: UserRole) -> Tuple[bool, str]:
        """
        Check if user has required role

        Args:
            session_token: Session token
            required_role: Required user role

        Returns:
            (has_access, message)
        """
        if session_token not in self.active_sessions:
            return False, "Not authenticated"

        session = self.active_sessions[session_token]
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.CUSTOMER: 1,
            UserRole.SUPPORT_AGENT: 2,
            UserRole.ADMIN: 3,
            UserRole.SUPER_ADMIN: 4
        }

        user_level = role_hierarchy.get(session.user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        if user_level >= required_level:
            return True, "Access granted"
        else:
            return False, f"Requires {required_role.value} role or higher"

    def get_user_info(self, session_token: str) -> Optional[Dict]:
        """
        Get user information for display

        Args:
            session_token: Session token

        Returns:
            User information dictionary
        """
        if session_token not in self.active_sessions:
            return None

        session = self.active_sessions[session_token]
        return {
            "customer_id": session.customer_id,
            "name": session.name,
            "email": session.email,
            "role": session.user_role.value,
            "role_display": session.access_description,
            "is_staff": session.is_staff,
            "is_admin": session.is_admin,
            "login_time": session.login_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def create_guest_session(self) -> Dict:
        """
        Create guest session context for unauthenticated users

        Returns:
            Guest session context
        """
        return {
            "user_authenticated": False,
            "customer_id": None,
            "customer_name": None,
            "customer_email": None,
            "user_role": "guest",
            "is_staff": False,
            "is_admin": False,
            "permissions": [],
            "session_id": "guest_session"
        }

    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

    def get_all_roles(self) -> Dict[str, str]:
        """Get all available roles for admin interface"""
        return {
            "customer": "Customer - Own data only",
            "support_agent": "Support Agent - Cross-customer support",
            "admin": "Administrator - Business analytics",
            "super_admin": "Super Administrator - Full system access"
        }

# Global authentication manager instance
auth_manager = AuthenticationManager()

def require_auth(required_role: UserRole = UserRole.CUSTOMER):
    """
    Decorator for Flask routes requiring authentication

    Usage:
        @require_auth(UserRole.ADMIN)
        def admin_only_route():
            pass
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify, session

            session_token = request.headers.get('Authorization') or session.get('session_token')

            if not session_token:
                return jsonify({"error": "Authentication required"}), 401

            has_access, message = auth_manager.require_role(session_token, required_role)

            if not has_access:
                return jsonify({"error": message}), 403

            return f(*args, **kwargs)

        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
