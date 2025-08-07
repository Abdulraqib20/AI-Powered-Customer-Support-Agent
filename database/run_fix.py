#!/usr/bin/env python3
"""
Apply database fixes directly using psycopg2
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

def apply_fix():
    """Apply the database fix"""
    try:
        # Read the fix script
        fix_file = Path(__file__).parent / 'fix_database.sql'

        if not fix_file.exists():
            logger.error("❌ Fix file not found")
            return False

        with open(fix_file, 'r', encoding='utf-8') as f:
            fix_sql = f.read()

        # Connect and execute
        logger.info("🔗 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)

        with conn.cursor() as cursor:
            logger.info("🔧 Applying database fixes...")

            # Execute the fix script
            cursor.execute(fix_sql)
            conn.commit()

            logger.info("✅ Database fixes applied successfully!")

            # Verify the fix
            logger.info("🔍 Verifying fixes...")

            # Check if view exists now
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.views
                    WHERE table_schema = 'public'
                    AND table_name = 'customer_distribution_view'
                );
            """)

            view_exists = cursor.fetchone()[0]
            logger.info(f"✅ customer_distribution_view exists: {view_exists}")

            # Check customer count
            cursor.execute("SELECT COUNT(*) FROM customers;")
            customer_count = cursor.fetchone()[0]
            logger.info(f"👥 Customers in database: {customer_count}")

            # Test the view
            if view_exists and customer_count > 0:
                cursor.execute("SELECT * FROM customer_distribution_view LIMIT 3;")
                results = cursor.fetchall()
                logger.info(f"📊 Customer distribution records: {len(results)}")
                for row in results:
                    logger.info(f"   {row[0]} - {row[1]}: {row[2]} customers")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Fix application failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting database fix application...")

    if apply_fix():
        logger.info("🎉 Database fix completed successfully!")

        # Test with repositories
        try:
            from config.database_config import get_repositories

            repositories = get_repositories()

            # Test customer distribution view
            distribution = repositories['customers'].get_customer_distribution()
            logger.info(f"✅ Repository test successful: {len(distribution)} distribution records")

            logger.info("🏆 All tests passed! Database is ready.")

        except Exception as e:
            logger.error(f"❌ Repository test failed: {e}")

    else:
        logger.error("❌ Database fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
