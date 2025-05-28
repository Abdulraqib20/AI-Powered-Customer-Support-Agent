#!/usr/bin/env python3
"""
Add remaining customers with valid Nigerian phone numbers
"""

import sys
from pathlib import Path
import logging
import psycopg2

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database_config import DATABASE_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_customers_with_valid_phones():
    """Add customers with valid Nigerian phone numbers"""
    try:
        logger.info("🔗 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)

        # Valid Nigerian phone numbers following the pattern ^(\+234|0)[7-9][0-1][0-9]{8}$
        customers = [
            {
                'name': 'Adebayo Okonkwo',
                'email': 'adebayo.okonkwo@gmail.com',
                'phone': '+2348012345678',  # 8 (network) + 0 + 12345678 = valid
                'state': 'Lagos',
                'lga': 'Ikeja',
                'address': '15 Adeniyi Jones Avenue, Ikeja, Lagos State',
                'account_tier': 'Gold',
                'preferences': '{"language": "English", "preferred_categories": ["Electronics", "Fashion"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Home Delivery"}'
            },
            {
                'name': 'Chioma Okechukwu',
                'email': 'chioma.okechukwu@gmail.com',
                'phone': '09087654321',  # 0 + 9 (network) + 0 + 87654321 = valid
                'state': 'Anambra',
                'lga': 'Awka South',
                'address': '7 Zik Avenue, Awka, Anambra State',
                'account_tier': 'Platinum',
                'preferences': '{"language": "Igbo", "preferred_categories": ["Electronics", "Food Items"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Express Delivery"}'
            },
            {
                'name': 'Ibrahim Hassan',
                'email': 'ibrahim.hassan@yahoo.com',
                'phone': '+2347012345678',  # +234 + 7 (network) + 0 + 12345678 = valid
                'state': 'Abuja',
                'lga': 'Municipal Area Council',
                'address': '12 Gimbiya Street, Area 11, Garki, Abuja',
                'account_tier': 'Bronze',
                'preferences': '{"language": "English", "preferred_categories": ["Books", "Electronics"], "notifications": {"email": true, "sms": false}, "delivery_preference": "Pickup Station"}'
            }
        ]

        with conn.cursor() as cursor:
            for customer in customers:
                try:
                    # Check if customer already exists
                    cursor.execute("SELECT COUNT(*) FROM customers WHERE email = %s", (customer['email'],))
                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        logger.info(f"👤 Adding customer: {customer['name']} (phone: {customer['phone']})")

                        insert_sql = """
                        INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::account_tier_enum, %s::jsonb)
                        """

                        cursor.execute(insert_sql, (
                            customer['name'],
                            customer['email'],
                            customer['phone'],
                            customer['state'],
                            customer['lga'],
                            customer['address'],
                            customer['account_tier'],
                            customer['preferences']
                        ))
                        conn.commit()
                        logger.info(f"✅ Added {customer['name']}")
                    else:
                        logger.info(f"ℹ️ Customer {customer['name']} already exists")

                except Exception as e:
                    logger.error(f"❌ Failed to add {customer['name']}: {e}")
                    conn.rollback()

        # Check final count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM customers;")
            count = cursor.fetchone()[0]
            logger.info(f"👥 Total customers: {count}")

            # Test the view with actual data
            cursor.execute("SELECT * FROM customer_distribution_view;")
            distribution = cursor.fetchall()
            logger.info(f"📊 Customer distribution:")
            for row in distribution:
                logger.info(f"   {row[0]} - {row[1]}: {row[2]} customers ({row[3]}%)")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Customer addition failed: {e}")
        return False

def add_sample_orders():
    """Add sample orders for the customers"""
    try:
        logger.info("🔗 Adding sample orders...")
        conn = psycopg2.connect(**DATABASE_CONFIG)

        with conn.cursor() as cursor:
            # Get customer IDs
            cursor.execute("SELECT customer_id, name FROM customers ORDER BY customer_id;")
            customers = cursor.fetchall()

            if len(customers) < 3:
                logger.warning("⚠️ Not enough customers to add orders")
                return False

            # Sample orders for each customer
            orders = [
                # Customer 1 orders
                (customers[0][0], 'Delivered', 'Pay on Delivery', 185000.00, '2024-11-20', 'Electronics', '2024-11-15 10:30:00'),
                (customers[0][0], 'Processing', 'Card', 42500.00, '2024-12-28', 'Fashion', '2024-12-25 14:15:00'),

                # Customer 2 orders
                (customers[1][0], 'Delivered', 'RaqibTechPay', 420000.00, '2024-10-05', 'Electronics', '2024-09-28 11:00:00'),
                (customers[1][0], 'Processing', 'Bank Transfer', 95000.00, '2024-12-29', 'Beauty', '2024-12-26 13:30:00'),

                # Customer 3 orders
                (customers[2][0], 'Pending', 'Pay on Delivery', 75000.00, '2024-12-30', 'Books', '2024-12-26 16:20:00'),
            ]

            for order in orders:
                try:
                    insert_sql = """
                    INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at)
                    VALUES (%s, %s::order_status_enum, %s::payment_method_enum, %s, %s::date, %s, %s::timestamp)
                    """

                    cursor.execute(insert_sql, order)
                    conn.commit()
                    logger.info(f"✅ Added order for customer {order[0]}: ₦{order[3]:,.2f}")

                except Exception as e:
                    logger.error(f"❌ Failed to add order: {e}")
                    conn.rollback()

            # Check order count
            cursor.execute("SELECT COUNT(*) FROM orders;")
            order_count = cursor.fetchone()[0]
            logger.info(f"📦 Total orders: {order_count}")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Order addition failed: {e}")
        return False

def test_final_setup():
    """Test the complete database setup"""
    try:
        from config.database_config import get_repositories

        logger.info("🧪 Testing repository functionality...")
        repositories = get_repositories()

        # Test customer distribution view
        distribution = repositories['customers'].get_customer_distribution()
        logger.info(f"✅ Customer distribution: {len(distribution)} records")

        # Test order summary
        order_summary = repositories['orders'].get_order_summary()
        logger.info(f"✅ Order summary: {len(order_summary)} records")

        # Test analytics
        analytics = repositories['analytics'].get_latest_metrics()
        logger.info(f"✅ Analytics: {len(analytics)} metric types")

        # Test customer search
        search_results = repositories['customers'].search_customers("Adebayo")
        logger.info(f"✅ Customer search for 'Adebayo': {len(search_results)} results")

        return True

    except Exception as e:
        logger.error(f"❌ Repository test failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Adding remaining customers and testing setup...")

    # Step 1: Add customers with valid phone numbers
    logger.info("\n1️⃣ Adding customers with valid Nigerian phone numbers...")
    if not add_customers_with_valid_phones():
        logger.error("❌ Customer addition failed!")
        return

    # Step 2: Add sample orders
    logger.info("\n2️⃣ Adding sample orders...")
    if not add_sample_orders():
        logger.error("❌ Order addition failed!")
        return

    # Step 3: Test everything
    logger.info("\n3️⃣ Testing complete setup...")
    if test_final_setup():
        logger.info("🎉 Database setup completed successfully!")
        logger.info("\n✅ Your PostgreSQL database is ready for the AI hackathon!")
        logger.info("✅ All views, customers, orders, and analytics are working.")
        logger.info("✅ You can now update your main2.py to use PostgreSQL instead of synthetic data.")
    else:
        logger.error("❌ Final test failed!")

if __name__ == "__main__":
    main()
