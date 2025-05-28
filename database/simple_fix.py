#!/usr/bin/env python3
"""
Simple step-by-step database fix
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

def fix_view_only():
    """Fix just the customer_distribution_view"""
    try:
        logger.info("🔗 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)

        with conn.cursor() as cursor:
            # Drop and recreate the view with correct syntax
            logger.info("🔧 Recreating customer_distribution_view...")

            view_sql = """
            DROP VIEW IF EXISTS customer_distribution_view;

            CREATE VIEW customer_distribution_view AS
            SELECT
                state,
                account_tier,
                COUNT(*) as customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
                ROUND(AVG(CURRENT_DATE - created_at::DATE), 0) as avg_days_since_registration,
                MIN(created_at) as first_customer_date,
                MAX(created_at) as latest_customer_date
            FROM customers
            GROUP BY state, account_tier
            ORDER BY state,
                CASE account_tier
                    WHEN 'Platinum' THEN 1
                    WHEN 'Gold' THEN 2
                    WHEN 'Silver' THEN 3
                    WHEN 'Bronze' THEN 4
                END;
            """

            cursor.execute(view_sql)
            conn.commit()
            logger.info("✅ View created successfully!")

            # Test the view
            cursor.execute("SELECT COUNT(*) FROM customer_distribution_view;")
            count = cursor.fetchone()[0]
            logger.info(f"📊 View has {count} records")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ View fix failed: {e}")
        return False

def add_sample_customers():
    """Add sample customers one by one"""
    try:
        logger.info("🔗 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)

        customers = [
            {
                'name': 'Adebayo Okonkwo',
                'email': 'adebayo.okonkwo@gmail.com',
                'phone': '+234813456789',  # 13 chars
                'state': 'Lagos',
                'lga': 'Ikeja',
                'address': '15 Adeniyi Jones Avenue, Ikeja, Lagos State',
                'account_tier': 'Gold',
                'preferences': '{"language": "English", "preferred_categories": ["Electronics", "Fashion"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Home Delivery"}'
            },
            {
                'name': 'Fatima Abdullahi',
                'email': 'fatima.abdullahi@yahoo.com',
                'phone': '08031234567',  # 11 chars
                'state': 'Kano',
                'lga': 'Municipal',
                'address': '23 Bompai Road, Nasarawa GRA, Kano State',
                'account_tier': 'Silver',
                'preferences': '{"language": "Hausa", "preferred_categories": ["Home & Kitchen", "Beauty"], "notifications": {"email": true, "sms": false}, "delivery_preference": "Pickup Station"}'
            },
            {
                'name': 'Chioma Okechukwu',
                'email': 'chioma.okechukwu@gmail.com',
                'phone': '+234901234567',  # 13 chars
                'state': 'Anambra',
                'lga': 'Awka South',
                'address': '7 Zik Avenue, Awka, Anambra State',
                'account_tier': 'Platinum',
                'preferences': '{"language": "Igbo", "preferred_categories": ["Electronics", "Food Items"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Express Delivery"}'
            }
        ]

        with conn.cursor() as cursor:
            for customer in customers:
                try:
                    # Check if customer already exists
                    cursor.execute("SELECT COUNT(*) FROM customers WHERE email = %s", (customer['email'],))
                    exists = cursor.fetchone()[0] > 0

                    if not exists:
                        logger.info(f"👤 Adding customer: {customer['name']}")

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

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Customer addition failed: {e}")
        return False

def test_everything():
    """Test the fixed database"""
    try:
        from config.database_config import get_repositories

        repositories = get_repositories()

        # Test customer distribution view
        distribution = repositories['customers'].get_customer_distribution()
        logger.info(f"✅ customer_distribution_view working: {len(distribution)} records")

        for record in distribution:
            logger.info(f"   {record['state']} - {record['account_tier']}: {record['customer_count']} customers")

        return True

    except Exception as e:
        logger.error(f"❌ Final test failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting simple database fix...")

    # Step 1: Fix the view
    logger.info("\n1️⃣ Fixing customer_distribution_view...")
    if not fix_view_only():
        logger.error("❌ View fix failed!")
        return

    # Step 2: Add sample customers
    logger.info("\n2️⃣ Adding sample customers...")
    if not add_sample_customers():
        logger.error("❌ Customer addition failed!")
        return

    # Step 3: Test everything
    logger.info("\n3️⃣ Testing final setup...")
    if test_everything():
        logger.info("🎉 Database fix completed successfully!")
    else:
        logger.error("❌ Final test failed!")

if __name__ == "__main__":
    main()
