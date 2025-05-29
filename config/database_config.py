"""
Database Configuration for Nigerian E-commerce Customer Support Agent
PostgreSQL connection settings and utilities
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, date

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'oracle'),
    'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
    'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
}

# Connection pool settings
POOL_CONFIG = {
    'minconn': int(os.getenv('DB_POOL_MIN', '2')),
    'maxconn': int(os.getenv('DB_POOL_MAX', '20')),
}

# Initialize logger
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for PostgreSQL operations"""

    def __init__(self):
        self.pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                **POOL_CONFIG,
                **DATABASE_CONFIG
            )
            logger.info("✅ Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Database connection error: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit=True):
        """Get a cursor with automatic connection management"""
        with self.get_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    yield cursor
                    if commit:
                        conn.commit()
            except Exception as e:
                conn.rollback()
                raise

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_command(self, command: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE command and return affected rows"""
        with self.get_cursor() as cursor:
            cursor.execute(command, params)
            return cursor.rowcount

    def close_pool(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("🔒 Database connection pool closed")

class CustomerRepository:
    """Repository for customer-related database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_customer(self, customer_data: Dict) -> int:
        """Create a new customer and return customer_id"""
        query = """
        INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences)
        VALUES (%(name)s, %(email)s, %(phone)s, %(state)s, %(lga)s, %(address)s, %(account_tier)s, %(preferences)s)
        RETURNING customer_id
        """

        with self.db.get_cursor() as cursor:
            cursor.execute(query, {
                'name': customer_data['name'],
                'email': customer_data['email'],
                'phone': customer_data['phone'],
                'state': customer_data['state'],
                'lga': customer_data['lga'],
                'address': customer_data['address'],
                'account_tier': customer_data.get('account_tier', 'Bronze'),
                'preferences': Json(customer_data.get('preferences', {}))
            })
            return cursor.fetchone()['customer_id']

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        query = "SELECT * FROM customers WHERE customer_id = %s"
        results = self.db.execute_query(query, (customer_id,))
        return results[0] if results else None

    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """Get customer by email"""
        query = "SELECT * FROM customers WHERE email = %s"
        results = self.db.execute_query(query, (email,))
        return results[0] if results else None

    def search_customers(self, search_term: str, state: str = None) -> List[Dict]:
        """Search customers by name or email with optional state filter"""
        if state:
            query = """
            SELECT * FROM customers
            WHERE (name ILIKE %s OR email ILIKE %s) AND state = %s
            ORDER BY name
            """
            params = (f'%{search_term}%', f'%{search_term}%', state)
        else:
            query = """
            SELECT * FROM customers
            WHERE name ILIKE %s OR email ILIKE %s
            ORDER BY name
            """
            params = (f'%{search_term}%', f'%{search_term}%')

        return self.db.execute_query(query, params)

    def update_customer(self, customer_id: int, updates: Dict) -> bool:
        """Update customer information"""
        set_clauses = []
        params = []

        for field, value in updates.items():
            if field in ['name', 'email', 'phone', 'state', 'lga', 'address', 'account_tier']:
                set_clauses.append(f"{field} = %s")
                params.append(value)
            elif field == 'preferences':
                set_clauses.append("preferences = %s")
                params.append(Json(value))

        if not set_clauses:
            return False

        query = f"UPDATE customers SET {', '.join(set_clauses)} WHERE customer_id = %s"
        params.append(customer_id)

        affected_rows = self.db.execute_command(query, tuple(params))
        return affected_rows > 0

    def get_customers_by_state(self, state: str) -> List[Dict]:
        """Get all customers from a specific state"""
        query = "SELECT * FROM customers WHERE state = %s ORDER BY name"
        return self.db.execute_query(query, (state,))

    def get_customer_distribution(self) -> List[Dict]:
        """Get customer distribution by state and tier"""
        query = "SELECT * FROM customer_distribution_view"
        return self.db.execute_query(query)

    def get_all_customers(self, limit: int = 100) -> List[Dict]:
        """Get all customers with optional limit"""
        query = "SELECT * FROM customers ORDER BY created_at DESC LIMIT %s"
        return self.db.execute_query(query, (limit,))

class OrderRepository:
    """Repository for order-related database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_order(self, order_data: Dict) -> int:
        """Create a new order and return order_id"""
        query = """
        INSERT INTO orders (customer_id, order_status, payment_method, total_amount,
                           delivery_date, product_category)
        VALUES (%(customer_id)s, %(order_status)s, %(payment_method)s, %(total_amount)s,
                %(delivery_date)s, %(product_category)s)
        RETURNING order_id
        """

        with self.db.get_cursor() as cursor:
            cursor.execute(query, order_data)
            return cursor.fetchone()['order_id']

    def get_orders_by_customer(self, customer_id: int, limit: int = 10) -> List[Dict]:
        """Get orders for a specific customer"""
        query = """
        SELECT * FROM orders
        WHERE customer_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        return self.db.execute_query(query, (customer_id, limit))

    def get_orders_by_status(self, status: str) -> List[Dict]:
        """Get orders by status"""
        query = "SELECT * FROM orders WHERE order_status = %s ORDER BY created_at DESC"
        return self.db.execute_query(query, (status,))

    def update_order_status(self, order_id: int, new_status: str) -> bool:
        """Update order status"""
        query = "UPDATE orders SET order_status = %s WHERE order_id = %s"
        affected_rows = self.db.execute_command(query, (new_status, order_id))
        return affected_rows > 0

    def get_order_summary(self) -> List[Dict]:
        """Get order summary analytics"""
        query = "SELECT * FROM order_summary_view ORDER BY month DESC"
        return self.db.execute_query(query)

    def get_revenue_by_state(self, start_date: date = None, end_date: date = None) -> List[Dict]:
        """Get revenue by state for a date range"""
        if start_date and end_date:
            query = """
            SELECT o.customer_state as state, SUM(o.total_amount) as total_revenue, COUNT(*) as order_count
            FROM orders o
            WHERE o.created_at BETWEEN %s AND %s
            GROUP BY o.customer_state
            ORDER BY total_revenue DESC
            """
            params = (start_date, end_date)
        else:
            query = "SELECT * FROM revenue_by_state_view"
            params = ()

        return self.db.execute_query(query, params)

    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
        """Get recent orders with optional limit"""
        query = "SELECT * FROM orders ORDER BY created_at DESC LIMIT %s"
        return self.db.execute_query(query, (limit,))

class AnalyticsRepository:
    """Repository for analytics-related database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_metric(self, metric_type: str, metric_value: Dict, time_period: str) -> int:
        """Save an analytics metric"""
        query = """
        INSERT INTO analytics (metric_type, metric_value, time_period)
        VALUES (%s, %s, %s)
        RETURNING analytics_id
        """

        with self.db.get_cursor() as cursor:
            cursor.execute(query, (metric_type, Json(metric_value), time_period))
            return cursor.fetchone()['analytics_id']

    def get_metrics_by_type(self, metric_type: str, limit: int = 10) -> List[Dict]:
        """Get metrics by type"""
        query = """
        SELECT * FROM analytics
        WHERE metric_type = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        return self.db.execute_query(query, (metric_type, limit))

    def get_customer_lifetime_value(self) -> List[Dict]:
        """Get customer lifetime value analytics"""
        query = "SELECT * FROM customer_lifetime_value_view LIMIT 100"
        return self.db.execute_query(query)

    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics of each type"""
        query = """
        SELECT DISTINCT ON (metric_type) metric_type, metric_value, time_period, created_at
        FROM analytics
        ORDER BY metric_type, created_at DESC
        """
        results = self.db.execute_query(query)
        return {row['metric_type']: row for row in results}

    def get_overview_analytics(self) -> Dict[str, Any]:
        """Get overview analytics for dashboard"""
        try:
            # Get basic counts and metrics
            overview = {
                'total_customers': 0,
                'total_orders': 0,
                'total_revenue': 0,
                'pending_orders': 0,
                'active_conversations': 0
            }

            # Get customer count
            customer_query = "SELECT COUNT(*) as count FROM customers"
            customer_result = self.db.execute_query(customer_query)
            if customer_result:
                overview['total_customers'] = customer_result[0]['count']

            # Get order statistics
            order_query = """
                SELECT
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    COUNT(CASE WHEN order_status = 'Pending' THEN 1 END) as pending_orders
                FROM orders
            """
            order_result = self.db.execute_query(order_query)
            if order_result:
                overview['total_orders'] = order_result[0]['total_orders'] or 0
                overview['total_revenue'] = float(order_result[0]['total_revenue'] or 0)
                overview['pending_orders'] = order_result[0]['pending_orders'] or 0

            # Get active conversations count
            try:
                conversation_query = "SELECT COUNT(*) as count FROM chat_conversations WHERE is_active = true"
                conversation_result = self.db.execute_query(conversation_query)
                if conversation_result:
                    overview['active_conversations'] = conversation_result[0]['count']
            except:
                # If chat tables don't exist, just set to 0
                overview['active_conversations'] = 0

            return overview

        except Exception as e:
            print(f"❌ Error getting overview analytics: {e}")
            return {
                'total_customers': 0,
                'total_orders': 0,
                'total_revenue': 0,
                'pending_orders': 0,
                'active_conversations': 0
            }

# Global database manager instance
db_manager = None

def initialize_database():
    """Initialize the global database manager"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_repositories():
    """Get repository instances"""
    if db_manager is None:
        initialize_database()

    return {
        'customers': CustomerRepository(db_manager),
        'orders': OrderRepository(db_manager),
        'analytics': AnalyticsRepository(db_manager)
    }

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

# Utility functions for data migration from existing system
def migrate_synthetic_data_to_db(synthetic_data: Dict, repositories: Dict):
    """Migrate synthetic customer data to PostgreSQL"""
    try:
        customer_repo = repositories['customers']
        order_repo = repositories['orders']

        # Extract customer info
        customer_info = synthetic_data['customer_info']
        customer_data = {
            'name': customer_info['name'],
            'email': customer_info['email'],
            'phone': customer_info['phone'],
            'state': customer_info['state'],
            'lga': customer_info['lga'],
            'address': customer_info['shipping_address'],
            'account_tier': synthetic_data['account']['tier'],
            'preferences': {
                'member_since': synthetic_data['account']['member_since'],
                'points': synthetic_data['account']['points']
            }
        }

        # Create customer
        customer_id = customer_repo.create_customer(customer_data)

        # Create current order if exists
        if 'current_order' in synthetic_data:
            current_order = synthetic_data['current_order']
            order_data = {
                'customer_id': customer_id,
                'order_status': 'Processing',  # Default status
                'payment_method': current_order['payment_method'],
                'total_amount': float(current_order['total'].replace('₦', '').replace(',', '')),
                'delivery_date': datetime.strptime(current_order['expected_delivery'], '%B %d, %Y').date(),
                'product_category': 'Mixed'  # Default category
            }
            order_repo.create_order(order_data)

        # Create historical orders
        if 'order_history' in synthetic_data:
            for hist_order in synthetic_data['order_history']:
                order_data = {
                    'customer_id': customer_id,
                    'order_status': hist_order['status'],
                    'payment_method': 'Pay on Delivery',  # Default for historical
                    'total_amount': float(hist_order['total'].replace('₦', '').replace(',', '')),
                    'delivery_date': datetime.strptime(hist_order['date'], '%Y-%m-%d').date(),
                    'product_category': 'Mixed',
                    'created_at': datetime.strptime(hist_order['date'], '%Y-%m-%d')
                }
                order_repo.create_order(order_data)

        logger.info(f"✅ Successfully migrated customer: {customer_info['name']}")
        return customer_id

    except Exception as e:
        logger.error(f"❌ Failed to migrate customer data: {e}")
        raise

# Test connection function
def test_database_connection():
    """Test the database connection"""
    try:
        db = initialize_database()
        with db.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            logger.info("✅ Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False
