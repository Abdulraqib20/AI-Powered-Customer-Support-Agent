#!/usr/bin/env python3
"""
Setup script for WhatsApp Rate Limiting System
Initializes the database tables and configuration for rate limiting
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get database connection"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'oracle')
    }
    return psycopg2.connect(**db_config)

def run_sql_file(filename):
    """Execute SQL file"""
    try:
        sql_file_path = os.path.join(os.path.dirname(__file__), filename)

        if not os.path.exists(sql_file_path):
            logger.error(f"❌ SQL file not found: {sql_file_path}")
            return False

        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()

        with get_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_content)
                conn.commit()
                logger.info(f"✅ Successfully executed {filename}")
                return True

    except Exception as e:
        logger.error(f"❌ Error executing {filename}: {e}")
        return False

def verify_rate_limiting_setup():
    """Verify that rate limiting tables and functions exist"""
    try:
        with get_database_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if tables exist
                tables_to_check = [
                    'whatsapp_rate_limits',
                    'whatsapp_user_rate_tracking',
                    'whatsapp_rate_limit_events'
                ]

                for table in tables_to_check:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (table,))

                    exists = cursor.fetchone()['exists']
                    if exists:
                        logger.info(f"✅ Table {table} exists")
                    else:
                        logger.error(f"❌ Table {table} missing")
                        return False

                # Check if functions exist
                functions_to_check = [
                    'get_user_tier_for_rate_limiting',
                    'can_start_conversation',
                    'can_send_message',
                    'apply_temporary_block'
                ]

                for function in functions_to_check:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.routines
                            WHERE routine_name = %s AND routine_type = 'FUNCTION'
                        )
                    """, (function,))

                    exists = cursor.fetchone()['exists']
                    if exists:
                        logger.info(f"✅ Function {function} exists")
                    else:
                        logger.error(f"❌ Function {function} missing")
                        return False

                # Check if view exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.views
                        WHERE table_name = 'v_rate_limit_summary'
                    )
                """)

                exists = cursor.fetchone()['exists']
                if exists:
                    logger.info("✅ View v_rate_limit_summary exists")
                else:
                    logger.error("❌ View v_rate_limit_summary missing")
                    return False

                # Check if default rate limit tiers are configured
                cursor.execute("SELECT COUNT(*) as count FROM whatsapp_rate_limits")
                count = cursor.fetchone()['count']

                if count >= 4:  # Should have anonymous, authenticated, premium, vip
                    logger.info(f"✅ Rate limit tiers configured ({count} tiers)")
                else:
                    logger.warning(f"⚠️ Only {count} rate limit tiers found, expected at least 4")

                return True

    except Exception as e:
        logger.error(f"❌ Error verifying rate limiting setup: {e}")
        return False

def test_rate_limiting_functions():
    """Test rate limiting functions with sample data"""
    try:
        with get_database_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                test_phone = "+2348123456789"
                test_customer_id = 1

                logger.info("🧪 Testing rate limiting functions...")

                # Test conversation limit check
                cursor.execute("""
                    SELECT can_start_conversation(%s, %s) as result
                """, (test_phone, test_customer_id))

                result = cursor.fetchone()['result']
                logger.info(f"✅ Conversation check result: {result}")

                # Test message limit check
                cursor.execute("""
                    SELECT can_send_message(%s, %s) as result
                """, (test_phone, test_customer_id))

                result = cursor.fetchone()['result']
                logger.info(f"✅ Message check result: {result}")

                # Test user tier function
                cursor.execute("""
                    SELECT get_user_tier_for_rate_limiting(%s) as tier
                """, (test_customer_id,))

                tier = cursor.fetchone()['tier']
                logger.info(f"✅ User tier: {tier}")

                logger.info("🎉 All rate limiting functions working correctly!")
                return True

    except Exception as e:
        logger.error(f"❌ Error testing rate limiting functions: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 Setting up WhatsApp Rate Limiting System...")

    # Step 1: Run the rate limiting SQL file
    logger.info("📊 Creating rate limiting tables and functions...")
    if not run_sql_file('whatsapp_rate_limiting.sql'):
        logger.error("❌ Failed to create rate limiting tables")
        return False

    # Step 2: Verify the setup
    logger.info("🔍 Verifying rate limiting setup...")
    if not verify_rate_limiting_setup():
        logger.error("❌ Rate limiting setup verification failed")
        return False

    # Step 3: Test the functions
    logger.info("🧪 Testing rate limiting functions...")
    if not test_rate_limiting_functions():
        logger.error("❌ Rate limiting function tests failed")
        return False

    logger.info("🎉 Rate limiting system setup completed successfully!")
    logger.info("")
    logger.info("📋 Rate Limiting Configuration:")
    logger.info("• Anonymous users: 5 conversations/day, 20 messages/hour")
    logger.info("• Authenticated users: 20 conversations/day, 60 messages/hour")
    logger.info("• Premium users: 50 conversations/day, 120 messages/hour")
    logger.info("• VIP users: 999 conversations/day, 300 messages/hour")
    logger.info("")
    logger.info("🔧 Admin endpoints available at:")
    logger.info("• GET /api/admin/rate-limits/stats - View statistics")
    logger.info("• GET /api/admin/rate-limits/user/<phone> - Check user status")
    logger.info("• POST /api/admin/rate-limits/block - Block users")
    logger.info("• GET/POST /api/admin/rate-limits/config - Manage configuration")
    logger.info("• GET /api/admin/rate-limits/summary - View summary")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
