#!/usr/bin/env python3
"""
Add sample orders with valid future delivery dates
"""

import sys
from pathlib import Path
import logging
import psycopg2
from datetime import datetime, date, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database_config import DATABASE_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_valid_orders():
    """Add sample orders with valid dates"""
    try:
        logger.info("🔗 Adding sample orders with valid dates...")
        conn = psycopg2.connect(**DATABASE_CONFIG)

        with conn.cursor() as cursor:
            # Get customer IDs
            cursor.execute("SELECT customer_id, name FROM customers ORDER BY customer_id;")
            customers = cursor.fetchall()

            if len(customers) < 3:
                logger.warning("⚠️ Not enough customers to add orders")
                return False

            # Today and future dates
            today = date.today()
            future_date_1 = today + timedelta(days=5)
            future_date_2 = today + timedelta(days=10)
            future_date_3 = today + timedelta(days=15)

            # Current date for orders created today
            now = datetime.now()

            # Sample orders with current and future dates
            orders = [
                # Current orders (created today, delivery in future)
                (customers[0][0], 'Processing', 'Card', 185000.00, future_date_1, 'Electronics', now),
                (customers[0][0], 'Pending', 'Pay on Delivery', 42500.00, future_date_2, 'Fashion', now),

                # Customer 2 orders
                (customers[1][0], 'Processing', 'RaqibTechPay', 420000.00, future_date_1, 'Electronics', now),
                (customers[1][0], 'Pending', 'Bank Transfer', 95000.00, future_date_3, 'Beauty', now),

                # Customer 3 orders
                (customers[2][0], 'Pending', 'Pay on Delivery', 75000.00, future_date_2, 'Books', now),

                # Customer 4 (Fatima) orders
                (customers[3][0], 'Processing', 'Card', 125000.00, future_date_1, 'Home & Kitchen', now),
            ]

            for i, order in enumerate(orders):
                try:
                    insert_sql = """
                    INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at)
                    VALUES (%s, %s::order_status_enum, %s::payment_method_enum, %s, %s, %s, %s)
                    """

                    cursor.execute(insert_sql, order)
                    conn.commit()
                    logger.info(f"✅ Added order {i+1} for customer {order[0]}: ₦{order[3]:,.2f} ({order[4]})")

                except Exception as e:
                    logger.error(f"❌ Failed to add order {i+1}: {e}")
                    conn.rollback()

            # Check order count
            cursor.execute("SELECT COUNT(*) FROM orders;")
            order_count = cursor.fetchone()[0]
            logger.info(f"📦 Total orders: {order_count}")

            # Show order summary
            cursor.execute("""
                SELECT
                    c.name,
                    o.order_status,
                    o.payment_method,
                    o.total_amount,
                    o.delivery_date,
                    o.product_category
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                ORDER BY o.created_at DESC
            """)

            orders_data = cursor.fetchall()
            logger.info("📋 Current orders:")
            for order in orders_data:
                logger.info(f"   {order[0]}: {order[1]} - ₦{order[3]:,.2f} ({order[4]}) - {order[2]}")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Order addition failed: {e}")
        return False

def test_views_with_data():
    """Test all views now that we have data"""
    try:
        from config.database_config import get_repositories

        logger.info("🧪 Testing all views with actual data...")
        repositories = get_repositories()

        # Test customer distribution view
        distribution = repositories['customers'].get_customer_distribution()
        logger.info(f"📊 Customer distribution view: {len(distribution)} records")

        # Test order summary view (now should have data)
        order_summary = repositories['orders'].get_order_summary()
        logger.info(f"📈 Order summary view: {len(order_summary)} records")

        # Test customer lifetime value view
        clv = repositories['analytics'].get_customer_lifetime_value()
        logger.info(f"💰 Customer lifetime value view: {len(clv)} records")

        # Show some actual data
        logger.info("\n📋 Sample data from views:")

        # Customer distribution
        for record in distribution[:3]:
            logger.info(f"   📍 {record['state']} - {record['account_tier']}: {record['customer_count']} customers")

        # Customer LTV
        for record in clv[:3]:
            logger.info(f"   💰 {record['name']}: ₦{record['lifetime_value']:,.2f} ({record['total_orders']} orders)")

        return True

    except Exception as e:
        logger.error(f"❌ View testing failed: {e}")
        return False

def run_final_test():
    """Run the original setup test to ensure everything works"""
    try:
        logger.info("🔄 Running final setup test...")
        from setup_database import test_database_setup

        if test_database_setup():
            logger.info("✅ Original setup test passed!")
            return True
        else:
            logger.error("❌ Original setup test failed!")
            return False

    except Exception as e:
        logger.error(f"❌ Final test error: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Adding valid sample orders...")

    # Step 1: Add orders with valid dates
    logger.info("\n1️⃣ Adding orders with future delivery dates...")
    if not add_valid_orders():
        logger.error("❌ Order addition failed!")
        return

    # Step 2: Test all views
    logger.info("\n2️⃣ Testing all views with data...")
    if not test_views_with_data():
        logger.error("❌ View testing failed!")
        return

    # Step 3: Run final test
    logger.info("\n3️⃣ Running final database test...")
    if run_final_test():
        logger.info("\n🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("✅ PostgreSQL database is fully configured")
        logger.info("✅ All customers, orders, and analytics are working")
        logger.info("✅ All views and constraints are functioning properly")
        logger.info("✅ Your AI-Powered Customer Support Agent is ready for the hackathon!")
        logger.info("="*60)
        logger.info("\n🔗 Next steps:")
        logger.info("1. Update your main2.py to use PostgreSQL instead of synthetic data")
        logger.info("2. Replace the generate_synthetic_data() calls with database queries")
        logger.info("3. Use the repository classes from config/database_config.py")
        logger.info("4. Test your Streamlit app with real database data")
    else:
        logger.error("❌ Final test failed!")

if __name__ == "__main__":
    main()
