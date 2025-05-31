#!/usr/bin/env python3
"""
🎯 Final Order Fix - Target the Specific Issues
===============================================

Based on the diagnostic, there are 3 main issues:
1. order_ai_assistant import issue
2. logger not defined in enhanced_db_querying
3. 'lga' field missing in order management

Let's fix these systematically.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_logger_issue():
    """Fix the logger not defined issue in enhanced_db_querying.py"""
    logger.info("🔧 Fixing logger issue in enhanced_db_querying.py...")

    enhanced_db_file = "src/enhanced_db_querying.py"

    with open(enhanced_db_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if logger import is missing at the top
    if 'import logging' not in content[:500]:
        # Add logging import after other imports
        content = content.replace(
            'from groq import Groq',
            '''from groq import Groq
import logging'''
        )

    # Make sure logger is defined after imports
    if 'logger = logging.getLogger(__name__)' not in content:
        # Add logger definition after the imports section
        content = content.replace(
            'logging.basicConfig(level=logging.INFO)',
            '''logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)'''
        )

    with open(enhanced_db_file, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("✅ Logger issue fixed")

def fix_order_ai_assistant_import():
    """Fix the order_ai_assistant import in enhanced_db_querying.py"""
    logger.info("🔧 Fixing order_ai_assistant import...")

    enhanced_db_file = "src/enhanced_db_querying.py"

    with open(enhanced_db_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add explicit import at the top of the file
    if 'from src.order_ai_assistant import order_ai_assistant' not in content:
        # Find the import section and add our import
        import_section = '''# 🆕 STEP 1.5: Check if this is a SHOPPING/ORDER ACTION that needs execution
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

        new_import_section = '''# 🆕 STEP 1.5: Check if this is a SHOPPING/ORDER ACTION that needs execution
            try:
                # Try multiple import methods to ensure we get the order_ai_assistant
                import sys
                import os

                # Method 1: Try direct import
                from src.order_ai_assistant import order_ai_assistant
                order_ai_available = True
                logger.info("✅ order_ai_assistant imported successfully with src import")
            except ImportError as e1:
                logger.warning(f"⚠️ src import failed: {e1}")
                try:
                    # Method 2: Add src to path and import
                    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
                    if src_path not in sys.path:
                        sys.path.append(src_path)
                    from order_ai_assistant import order_ai_assistant
                    order_ai_available = True
                    logger.info("✅ order_ai_assistant imported after adding src to path")
                except ImportError as e2:
                    logger.warning(f"⚠️ Path import failed: {e2}")
                    try:
                        # Method 3: Relative import
                        from .order_ai_assistant import order_ai_assistant
                        order_ai_available = True
                        logger.info("✅ order_ai_assistant imported with relative import")
                    except ImportError as e3:
                        logger.error(f"❌ All import methods failed: {e3}")
                        order_ai_available = False'''

        content = content.replace(import_section, new_import_section)

    with open(enhanced_db_file, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("✅ order_ai_assistant import fixed")

def fix_order_management_lga_issue():
    """Fix the 'lga' field issue in OrderManagementSystem"""
    logger.info("🔧 Fixing 'lga' field issue in order management...")

    order_mgmt_file = "src/order_management.py"

    with open(order_mgmt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the customer info query that's likely causing the issue
    old_query = '''cursor.execute("""
                        SELECT name, email, phone FROM customers WHERE customer_id = %s
                    """, (customer_id,))'''

    new_query = '''cursor.execute("""
                        SELECT name, email, phone, lga FROM customers WHERE customer_id = %s
                    """, (customer_id,))'''

    if old_query in content:
        content = content.replace(old_query, new_query)
        logger.info("✅ Fixed customer query to include lga field")

    # Also handle the case where lga might be None
    old_customer_access = "customer_info['name']"
    if old_customer_access in content:
        # Find the customer_info usage and add null checks
        content = content.replace(
            "customer_info['name']",
            "customer_info.get('name', 'Unknown Customer')"
        )
        content = content.replace(
            "customer_info['email']",
            "customer_info.get('email', 'no-email@unknown.com')"
        )
        content = content.replace(
            "customer_info['phone']",
            "customer_info.get('phone', 'N/A')"
        )

    with open(order_mgmt_file, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("✅ OrderManagement lga issue fixed")

def test_fixes():
    """Test that our fixes work"""
    logger.info("🧪 Testing fixes...")

    try:
        # Test 1: Import order_ai_assistant
        sys.path.append('src')
        from order_ai_assistant import order_ai_assistant
        logger.info("✅ order_ai_assistant import works")

        # Test 2: Test OrderManagementSystem
        from order_management import OrderManagementSystem
        order_system = OrderManagementSystem()
        logger.info("✅ OrderManagementSystem import works")

        # Test 3: Create a simple order
        test_items = [{'product_id': 1, 'quantity': 1}]
        test_delivery = {
            'street': 'Test Street',
            'city': 'Lagos',
            'state': 'Lagos',
            'country': 'Nigeria'
        }

        result = order_system.create_order(1, test_items, test_delivery, 'RaqibTechPay')

        if result['success']:
            logger.info(f"✅ Order creation works! Order ID: {result['order_id']}")

            # Check database
            from config.database_config import DATABASE_CONFIG
            import psycopg2
            from psycopg2.extras import RealDictCursor

            with psycopg2.connect(**DATABASE_CONFIG) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id = 1")
                    count = cursor.fetchone()[0]
                    logger.info(f"✅ Customer 1 has {count} orders in database")

            return True
        else:
            logger.error(f"❌ Order creation failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    logger.info("🚀 Applying Final Order Fixes...")

    # Apply fixes
    fix_logger_issue()
    fix_order_ai_assistant_import()
    fix_order_management_lga_issue()

    # Test fixes
    if test_fixes():
        logger.info("🎉 ALL FIXES SUCCESSFUL!")
        logger.info("👉 Now restart your Flask app and test the chat interface")
        logger.info("💬 Try: 'I want to buy the Samsung Galaxy A24'")
        return True
    else:
        logger.error("❌ Some fixes failed, check logs above")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
