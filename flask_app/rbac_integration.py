"""
Flask RBAC Integration - Seamless Integration with Existing App
Extends your existing Flask authentication with role-based access control
"""

from functools import wraps
from flask import session, request, jsonify, g, redirect, url_for
import logging
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from rbac_core import rbac_manager, UserRole, UserSession

logger = logging.getLogger(__name__)

def get_current_user_session():
    """
    Get current user session from Flask session - EXTENDS your existing auth
    """
    if not session.get('user_authenticated', False):
        return None

    try:
        # Extract user data from your existing Flask session
        user_data = {
            'customer_id': session.get('customer_id'),
            'name': session.get('customer_name', ''),
            'email': session.get('customer_email', ''),
            'user_role': session.get('user_role', 'customer'),
            'is_staff': session.get('is_staff', False),
            'is_admin': session.get('is_admin', False),
        }

        # Create RBAC session from existing Flask session data
        rbac_session = rbac_manager.create_session_from_customer_data(user_data)
        return rbac_session

    except Exception as e:
        logger.error(f"Failed to create RBAC session: {e}")
        return None

def require_login(f):
    """
    Decorator to require user login - EXTENDS your existing auth decorators
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_authenticated', False):
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role: UserRole):
    """
    Decorator to require specific role - NEW RBAC FUNCTIONALITY
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_session = get_current_user_session()
            if not user_session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login_page'))

            if user_session.role != required_role:
                if request.is_json:
                    return jsonify({
                        'error': f'Access denied - {required_role.value} role required',
                        'current_role': user_session.role.value
                    }), 403
                return jsonify({'error': 'Access denied'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin(f):
    """
    Decorator to require admin access - NEW RBAC FUNCTIONALITY
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_session = get_current_user_session()
        if not user_session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login_page'))

        if user_session.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            if request.is_json:
                return jsonify({
                    'error': 'Admin access required',
                    'current_role': user_session.role.value
                }), 403
            return jsonify({'error': 'Access denied'}), 403

        return f(*args, **kwargs)
    return decorated_function

def get_rbac_context_for_session():
    """
    Get RBAC context for session_context in enhanced_db_querying
    SEAMLESSLY INTEGRATES with your existing session system
    """
    user_session = get_current_user_session()

    if not user_session:
        return {
            'user_authenticated': False,
            'user_role': 'guest',
            'customer_id': None,
            'can_access_analytics': False,
        }

    return {
        'user_authenticated': True,
        'user_role': user_session.role.value,
        'customer_id': user_session.user_id,
        'customer_name': user_session.name,
        'customer_email': user_session.email,
        'is_staff': user_session.is_staff,
        'is_admin': user_session.is_admin,
        'can_access_analytics': user_session.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN],
    }

def load_user_from_database(email, password_hash):
    """
    Load user from database with RBAC fields - EXTENDS your existing user loading
    """
    try:
        # Import your existing database config
        from config.database_config import DATABASE_CONFIG
        import psycopg2

        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        # Use the authentication function from the migration
        cursor.execute("""
            SELECT customer_id, name, email, user_role, is_staff, is_admin,
                   account_status, last_login
            FROM customers
            WHERE email = %s AND password_hash = %s
              AND account_status = 'active'
              AND user_role IN ('support_agent', 'admin', 'super_admin')
        """, (email, password_hash))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'customer_id': result[0],
                'name': result[1],
                'email': result[2],
                'user_role': result[3],
                'is_staff': result[4],
                'is_admin': result[5],
                'account_status': result[6],
                'last_login': result[7]
            }

        return None

    except Exception as e:
        logger.error(f"Database user loading failed: {e}")
        return None

def create_rbac_aware_session_context(existing_session_context=None):
    """
    Create session context that includes RBAC information
    SEAMLESSLY EXTENDS your existing session_context
    """
    # Start with existing session context or empty dict
    context = existing_session_context.copy() if existing_session_context else {}

    # Add RBAC context
    rbac_context = get_rbac_context_for_session()
    context.update(rbac_context)

    return context
