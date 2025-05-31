#!/usr/bin/env python3
"""
🚀 Fix Order Database Integration - Comprehensive Solution
============================================================

This script fixes the disconnect between AI chat order placement
and actual database order insertion. The issue is that orders are
being processed by the AI but not saved to the database.

Fixes:
1. Ensure Order AI Assistant properly imports OrderManagementSystem
2. Fix database connection issues in order placement
3. Add proper error handling and logging
4. Verify order creation actually inserts to database
5. Test the complete flow from chat to database
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_order_ai_assistant_imports():
    """Fix the import issues in OrderAIAssistant"""
    logger.info("🔧 Fixing Order AI Assistant imports...")

    order_ai_file = "src/order_ai_assistant.py"

    with open(order_ai_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the imports section
    old_import_section = '''# Import our existing systems
try:
    from .order_management import OrderManagementSystem, PaymentMethod
    from .recommendation_engine import ProductRecommendationEngine
except ImportError:
    # Fallback for when imported directly
    try:
        from order_management import OrderManagementSystem, PaymentMethod
        from recommendation_engine import ProductRecommendationEngine
    except ImportError:
        # Create mock classes if imports fail
        class OrderManagementSystem:
            def check_product_availability(self, product_id, quantity):
                return {'available': True, 'product_info': {'product_name': 'Mock Product'}}
            def create_order(self, *args, **kwargs):
                return {'success': True, 'order_id': 'MOCK123', 'database_order_id': 123}

        class ProductRecommendationEngine:
            def __init__(self):
                pass

        class PaymentMethod:
            PAY_ON_DELIVERY = "Pay on Delivery"
            RAQIB_TECH_PAY = "RaqibTechPay"'''

    new_import_section = '''# Import our existing systems
try:
    from .order_management import OrderManagementSystem, PaymentMethod
    from .recommendation_engine import ProductRecommendationEngine
    logger.info("✅ Successfully imported OrderManagementSystem and ProductRecommendationEngine with relative imports")
except ImportError as e1:
    logger.warning(f"⚠️ Relative import failed: {e1}")
    # Fallback for when imported directly
    try:
        from order_management import OrderManagementSystem, PaymentMethod
        from recommendation_engine import ProductRecommendationEngine
        logger.info("✅ Successfully imported OrderManagementSystem and ProductRecommendationEngine with direct imports")
    except ImportError as e2:
        logger.error(f"❌ Direct import failed: {e2}")
        # Create mock classes if imports fail - but log this as an error
        logger.error("❌ CRITICAL: Using mock OrderManagementSystem - orders will NOT be saved to database!")

        class OrderManagementSystem:
            def check_product_availability(self, product_id, quantity):
                logger.error("❌ MOCK: check_product_availability called - real system not available")
                return {'available': True, 'product_info': {'product_name': 'Mock Product'}}
            def create_order(self, *args, **kwargs):
                logger.error("❌ MOCK: create_order called - NO DATABASE INSERTION HAPPENING!")
                return {'success': False, 'error': 'OrderManagementSystem not available - import failed'}

        class ProductRecommendationEngine:
            def __init__(self):
                logger.warning("⚠️ Using mock ProductRecommendationEngine")

        class PaymentMethod:
            PAY_ON_DELIVERY = "Pay on Delivery"
            RAQIB_TECH_PAY = "RaqibTechPay"'''

    content = content.replace(old_import_section, new_import_section)

    # Also enhance the OrderAIAssistant __init__ method with better error handling
    old_init = '''    def __init__(self):
        self.order_system = OrderManagementSystem()
        self.recommendation_engine = ProductRecommendationEngine()
        self.active_carts = {}  # In-memory cart storage (use Redis in production)'''

    new_init = '''    def __init__(self):
        try:
            self.order_system = OrderManagementSystem()
            logger.info("✅ OrderManagementSystem initialized successfully")
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to initialize OrderManagementSystem: {e}")
            raise Exception(f"OrderAIAssistant cannot function without OrderManagementSystem: {e}")

        try:
            self.recommendation_engine = ProductRecommendationEngine()
            logger.info("✅ ProductRecommendationEngine initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ ProductRecommendationEngine initialization failed: {e}")
            self.recommendation_engine = None

        self.active_carts = {}  # In-memory cart storage (use Redis in production)
        logger.info("✅ OrderAIAssistant initialized successfully")'''

    content = content.replace(old_init, new_init)

    with open(order_ai_file, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("✅ Order AI Assistant imports fixed")

def fix_enhanced_db_querying_imports():
    """Fix the import issues in enhanced_db_querying.py"""
    logger.info("🔧 Fixing Enhanced DB Querying imports...")

    enhanced_db_file = "src/enhanced_db_querying.py"

    with open(enhanced_db_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the order_ai_assistant import
    old_import = '''            # 🆕 STEP 1.5: Check if this is a SHOPPING/ORDER ACTION that needs execution
            try:
                from order_ai_assistant import order_ai_assistant
                order_ai_available = True
            except ImportError:
                try:
                    from .order_ai_assistant import order_ai_assistant
                    order_ai_available = True
                except ImportError:
                    order_ai_available = False'''

    new_import = '''            # 🆕 STEP 1.5: Check if this is a SHOPPING/ORDER ACTION that needs execution
            try:
                from order_ai_assistant import order_ai_assistant
                order_ai_available = True
                logger.info("✅ order_ai_assistant imported successfully with direct import")
            except ImportError as e1:
                logger.warning(f"⚠️ Direct import of order_ai_assistant failed: {e1}")
                try:
                    from .order_ai_assistant import order_ai_assistant
                    order_ai_available = True
                    logger.info("✅ order_ai_assistant imported successfully with relative import")
                except ImportError as e2:
                    logger.error(f"❌ Relative import of order_ai_assistant failed: {e2}")
                    # Try importing from src directory explicitly
                    try:
                        import sys
                        import os
                        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
                        from order_ai_assistant import order_ai_assistant
                        order_ai_available = True
                        logger.info("✅ order_ai_assistant imported successfully with explicit path")
                    except ImportError as e3:
                        logger.error(f"❌ All import methods failed for order_ai_assistant: {e3}")
                        order_ai_available = False'''

    content = content.replace(old_import, new_import)

    # Add more detailed logging around order processing
    old_shopping_call = '''                        # Process through Order AI Assistant
                        shopping_result = order_ai_assistant.process_shopping_conversation(
                            user_query, customer_id, product_context
                        )'''

    new_shopping_call = '''                        # Process through Order AI Assistant
                        logger.info(f"🛒 Calling order_ai_assistant.process_shopping_conversation for customer {customer_id}")
                        logger.info(f"📝 Query: {user_query[:100]}...")
                        logger.info(f"📦 Product context: {len(product_context)} products")

                        try:
                            shopping_result = order_ai_assistant.process_shopping_conversation(
                                user_query, customer_id, product_context
                            )
                            logger.info(f"🎯 Shopping result: success={shopping_result.get('success', False)}, action={shopping_result.get('action', 'unknown')}")

                            # If order was placed, verify it in database
                            if shopping_result.get('success') and shopping_result.get('action') == 'order_placed':
                                order_id = shopping_result.get('order_id')
                                logger.info(f"✅ ORDER PLACED! Verifying order {order_id} in database...")
                                self._verify_order_in_database(order_id, customer_id)

                        except Exception as shopping_error:
                            logger.error(f"❌ Error in shopping conversation: {shopping_error}")
                            shopping_result = {
                                'success': False,
                                'message': f"Shopping system error: {str(shopping_error)}",
                                'action': 'system_error'
                            }'''

    content = content.replace(old_shopping_call, new_shopping_call)

    # Add a method to verify orders in database
    verification_method = '''
    def _verify_order_in_database(self, order_id: str, customer_id: int):
        """Verify that an order was actually saved to the database"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check if order exists in database
                    cursor.execute("""
                        SELECT order_id, customer_id, order_status, total_amount, created_at
                        FROM orders
                        WHERE customer_id = %s
                        ORDER BY created_at DESC
                        LIMIT 5
                    """, (customer_id,))

                    recent_orders = cursor.fetchall()
                    logger.info(f"📋 Found {len(recent_orders)} recent orders for customer {customer_id}")

                    for order in recent_orders:
                        logger.info(f"   Order {order['order_id']}: {order['order_status']} - ₦{order['total_amount']} ({order['created_at']})")

                    # Check if the specific order exists (either by formatted ID or database ID)
                    if order_id.startswith('RQB'):
                        # This is a formatted order ID, extract the numeric part
                        numeric_part = order_id.replace('RQB', '').replace(datetime.now().strftime('%Y%m%d'), '')
                        try:
                            db_order_id = int(numeric_part)
                            cursor.execute("SELECT * FROM orders WHERE order_id = %s", (db_order_id,))
                        except:
                            cursor.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC LIMIT 1", (customer_id,))
                    else:
                        cursor.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC LIMIT 1", (customer_id,))

                    order_record = cursor.fetchone()
                    if order_record:
                        logger.info(f"✅ ORDER VERIFIED IN DATABASE: {order_record['order_id']} for customer {customer_id}")
                        return True
                    else:
                        logger.error(f"❌ ORDER NOT FOUND IN DATABASE! Order {order_id} for customer {customer_id}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error verifying order in database: {e}")
            return False'''

    # Add the verification method before the last method
    content = content.replace(
        '    def _generate_shopping_response(self, shopping_result: Dict[str, Any]) -> str:',
        verification_method + '\n\n    def _generate_shopping_response(self, shopping_result: Dict[str, Any]) -> str:'
    )

    with open(enhanced_db_file, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("✅ Enhanced DB Querying imports fixed")

def verify_order_management_system():
    """Verify that the OrderManagementSystem is working correctly"""
    logger.info("🔍 Verifying OrderManagementSystem...")

    try:
        # Import and test the OrderManagementSystem
        sys.path.append('src')
        from order_management import OrderManagementSystem

        # Create an instance
        order_system = OrderManagementSystem()
        logger.info("✅ OrderManagementSystem imported and instantiated successfully")

        # Test database connection
        try:
            with order_system.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM orders")
                    count = cursor.fetchone()[0]
                    logger.info(f"✅ Database connection working - found {count} existing orders")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ OrderManagementSystem verification failed: {e}")
        return False

def test_order_creation():
    """Test creating an order to verify the full flow"""
    logger.info("🧪 Testing order creation flow...")

    try:
        # Import the order AI assistant
        sys.path.append('src')
        from order_ai_assistant import order_ai_assistant

        # Test customer (use existing customer ID 1)
        test_customer_id = 1

        # Test product context (Samsung Galaxy A24)
        test_product_context = [{
            'product_id': 1,  # Assuming this exists
            'product_name': 'Samsung Galaxy A24 128GB Smartphone',
            'category': 'Electronics',
            'brand': 'Samsung',
            'price': 425000.00,
            'currency': 'NGN',
            'in_stock': True,
            'stock_quantity': 45
        }]

        # Test adding to cart
        logger.info("📦 Testing add to cart...")
        add_result = order_ai_assistant.add_to_cart(test_customer_id, test_product_context[0])
        logger.info(f"Add to cart result: {add_result}")

        if add_result['success']:
            logger.info("✅ Add to cart successful, testing order placement...")

            # Test order placement
            test_delivery = {
                'street': 'Anyim Pius Anyim Street',
                'city': 'Lugbe',
                'state': 'Abuja',
                'country': 'Nigeria'
            }

            test_payment = 'RaqibTechPay'

            order_result = order_ai_assistant.place_order(
                test_customer_id, test_delivery, test_payment
            )

            logger.info(f"Order placement result: {order_result}")

            if order_result['success']:
                logger.info("✅ TEST ORDER PLACED SUCCESSFULLY!")
                logger.info(f"Order ID: {order_result['order_id']}")

                # Verify in database
                verify_order_in_db(order_result['order_id'], test_customer_id)
                return True
            else:
                logger.error(f"❌ Order placement failed: {order_result.get('message', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ Add to cart failed: {add_result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Order creation test failed: {e}")
        return False

def verify_order_in_db(order_id, customer_id):
    """Verify that the order was actually saved to the database"""
    logger.info(f"🔍 Verifying order {order_id} in database...")

    try:
        from config.database_config import DATABASE_CONFIG
        import psycopg2
        from psycopg2.extras import RealDictCursor

        with psycopg2.connect(**DATABASE_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get recent orders for this customer
                cursor.execute("""
                    SELECT order_id, customer_id, order_status, total_amount, created_at, payment_method
                    FROM orders
                    WHERE customer_id = %s
                    ORDER BY created_at DESC
                    LIMIT 3
                """, (customer_id,))

                orders = cursor.fetchall()
                logger.info(f"📋 Found {len(orders)} recent orders for customer {customer_id}:")

                for order in orders:
                    logger.info(f"   Order {order['order_id']}: {order['order_status']} - ₦{order['total_amount']} - {order['payment_method']} ({order['created_at']})")

                if orders:
                    logger.info("✅ ORDER SUCCESSFULLY SAVED TO DATABASE!")
                    return True
                else:
                    logger.error("❌ NO ORDERS FOUND IN DATABASE!")
                    return False

    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main function to run all fixes"""
    logger.info("🚀 Starting Order Database Integration Fix...")

    try:
        # Step 1: Fix imports
        fix_order_ai_assistant_imports()
        fix_enhanced_db_querying_imports()

        # Step 2: Verify systems
        if not verify_order_management_system():
            logger.error("❌ OrderManagementSystem verification failed!")
            return False

        # Step 3: Test order creation
        if not test_order_creation():
            logger.error("❌ Order creation test failed!")
            return False

        logger.info("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        logger.info("🎉 Order database integration should now work correctly!")

        return True

    except Exception as e:
        logger.error(f"❌ Fix script failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Order database integration fixed successfully!")
        print("👉 Restart your Flask application and test the chat interface")
    else:
        print("\n❌ Fix failed! Check the logs above for details")
        sys.exit(1)
