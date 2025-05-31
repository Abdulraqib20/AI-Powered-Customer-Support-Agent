#!/usr/bin/env python3
"""
🧪 Test Complete Order Flow
===========================

Test the complete order flow from chat to database to ensure
orders are properly saved when placed through the AI chat interface.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append('src')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_order_ai_assistant():
    """Test the Order AI Assistant directly"""
    logger.info("🧪 Testing Order AI Assistant...")

    try:
        from order_ai_assistant import order_ai_assistant
        logger.info("✅ Order AI Assistant imported successfully")

        # Test adding to cart
        test_product = {
            'product_id': 1,
            'product_name': 'Samsung Galaxy A24 128GB Smartphone',
            'category': 'Electronics',
            'brand': 'Samsung',
            'price': 425000.00
        }

        # Add to cart
        cart_result = order_ai_assistant.add_to_cart(1, test_product)
        logger.info(f"Add to cart result: {cart_result.get('success', False)}")

        if cart_result['success']:
            # Place order
            delivery_address = {
                'street': 'Test Street',
                'city': 'Lagos',
                'state': 'Lagos',
                'country': 'Nigeria'
            }

            order_result = order_ai_assistant.place_order(1, delivery_address, 'RaqibTechPay')
            logger.info(f"Order placement result: {order_result.get('success', False)}")

            if order_result['success']:
                logger.info(f"✅ Order placed successfully! Order ID: {order_result.get('order_id')}")
                return True
            else:
                logger.error(f"❌ Order placement failed: {order_result.get('message')}")
        else:
            logger.error(f"❌ Add to cart failed: {cart_result.get('message')}")

        return False

    except Exception as e:
        logger.error(f"❌ Order AI Assistant test failed: {e}")
        return False

def test_enhanced_db_querying():
    """Test the enhanced database querying with shopping"""
    logger.info("🧪 Testing Enhanced Database Querying...")

    try:
        from enhanced_db_querying import EnhancedDatabaseQuerying
        enhanced_db = EnhancedDatabaseQuerying()

        # Test session context
        test_session = {
            'user_authenticated': True,
            'customer_verified': True,
            'customer_id': 1,
            'customer_name': 'Test User',
            'user_id': 'test_user_123'
        }

        # Test shopping query
        test_query = "I want to buy the Samsung Galaxy A24"

        result = enhanced_db.process_enhanced_query(test_query, test_session)
        logger.info(f"Enhanced query result: {result.get('success', False)}")

        if result.get('success'):
            logger.info("✅ Enhanced database querying works")
            return True
        else:
            logger.error(f"❌ Enhanced query failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Enhanced DB test failed: {e}")
        return False

def check_database_orders():
    """Check recent orders in database"""
    logger.info("🔍 Checking database for recent orders...")

    try:
        from config.database_config import DATABASE_CONFIG
        import psycopg2
        from psycopg2.extras import RealDictCursor

        with psycopg2.connect(**DATABASE_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT order_id, customer_id, order_status, total_amount, created_at
                    FROM orders
                    WHERE customer_id = 1
                    ORDER BY created_at DESC
                    LIMIT 5
                """)

                orders = cursor.fetchall()
                logger.info(f"📋 Found {len(orders)} recent orders for customer 1")

                for order in orders:
                    logger.info(f"   Order {order['order_id']}: {order['order_status']} - ₦{order['total_amount']} ({order['created_at']})")

                return len(orders) > 0

    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting Complete Order Flow Test...")

    # Test 1: Order AI Assistant
    logger.info("\n=== Test 1: Order AI Assistant ===")
    ai_test = test_order_ai_assistant()

    # Test 2: Enhanced Database Querying
    logger.info("\n=== Test 2: Enhanced Database Querying ===")
    db_test = test_enhanced_db_querying()

    # Test 3: Check Database
    logger.info("\n=== Test 3: Database Orders Check ===")
    db_check = check_database_orders()

    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Order AI Assistant: {'✅ PASS' if ai_test else '❌ FAIL'}")
    logger.info(f"Enhanced DB Querying: {'✅ PASS' if db_test else '❌ FAIL'}")
    logger.info(f"Database Orders: {'✅ FOUND' if db_check else '❌ NONE'}")

    if ai_test and db_test:
        logger.info("🎉 ORDER SYSTEM IS WORKING!")
        logger.info("👉 You can now test the chat interface")
        return True
    else:
        logger.error("❌ Some tests failed - check logs above")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
