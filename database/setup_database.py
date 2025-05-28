#!/usr/bin/env python3
"""
Database Setup Script for Nigerian E-commerce Customer Support Agent
Initialize PostgreSQL database and migrate existing data
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database_config import (
    test_database_connection,
    initialize_database,
    get_repositories,
    migrate_synthetic_data_to_db,
    DATABASE_CONFIG
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_postgresql_installed():
    """Check if PostgreSQL is installed and accessible"""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ PostgreSQL found: {result.stdout.strip()}")
            return True
        else:
            logger.error("❌ PostgreSQL not found in PATH")
            return False
    except FileNotFoundError:
        logger.error("❌ PostgreSQL not installed or not in PATH")
        return False

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    try:
        # Connect to default postgres database to create our database
        conn_params = DATABASE_CONFIG.copy()
        db_name = conn_params.pop('database')
        conn_params['database'] = 'postgres'

        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"✅ Created database: {db_name}")
            else:
                logger.info(f"ℹ️ Database already exists: {db_name}")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False

def run_schema_script():
    """Run the database schema creation script"""
    schema_file = Path(__file__).parent / 'database_schema.sql'

    if not schema_file.exists():
        logger.error(f"❌ Schema file not found: {schema_file}")
        return False

    try:
        # Use psql command to run schema
        cmd = [
            'psql',
            '-h', DATABASE_CONFIG['host'],
            '-p', DATABASE_CONFIG['port'],
            '-U', DATABASE_CONFIG['user'],
            '-d', DATABASE_CONFIG['database'],
            '-f', str(schema_file)
        ]

        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = DATABASE_CONFIG['password']

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ Database schema created successfully!")
            logger.info("Schema output:")
            for line in result.stdout.split('\n'):
                if line.strip() and 'NOTICE' in line:
                    logger.info(f"   {line.strip()}")
            return True
        else:
            logger.error("❌ Failed to create schema")
            logger.error(f"Error: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to run schema script: {e}")
        return False

def test_database_setup():
    """Test the database setup"""
    try:
        if not test_database_connection():
            return False

        # Test basic operations
        repos = get_repositories()

        # Test customer distribution view
        distribution = repos['customers'].get_customer_distribution()
        logger.info(f"✅ Found {len(distribution)} customer distribution records")

        # Test analytics
        analytics = repos['analytics'].get_latest_metrics()
        logger.info(f"✅ Found {len(analytics)} analytics metric types")

        return True

    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def migrate_existing_data():
    """Migrate existing synthetic data to PostgreSQL"""
    try:
        # This would be called from your main application
        # when you want to migrate existing in-memory data
        logger.info("ℹ️ Data migration function ready")
        logger.info("ℹ️ Call migrate_synthetic_data_to_db() from your application to migrate data")
        return True

    except Exception as e:
        logger.error(f"❌ Data migration preparation failed: {e}")
        return False

def setup_environment_file():
    """Create or update .env file with database configuration"""
    env_file = Path(__file__).parent / '.env'
    env_example = Path(__file__).parent / '.env_example'

    if env_file.exists():
        logger.info("ℹ️ .env file already exists")
        return True

    if env_example.exists():
        logger.info("ℹ️ Copying .env_example to .env")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            # Add database configuration
            content += "\n# PostgreSQL Database Configuration\n"
            content += f"DB_HOST={DATABASE_CONFIG['host']}\n"
            content += f"DB_PORT={DATABASE_CONFIG['port']}\n"
            content += f"DB_NAME={DATABASE_CONFIG['database']}\n"
            content += f"DB_USER={DATABASE_CONFIG['user']}\n"
            content += "DB_PASSWORD=your_password_here\n"
            content += f"DB_SSLMODE={DATABASE_CONFIG['sslmode']}\n"
            dst.write(content)

        logger.info("✅ Created .env file with database configuration")
        logger.warning("⚠️ Please update DB_PASSWORD in .env file")
        return True
    else:
        logger.warning("⚠️ .env_example file not found, creating basic .env")
        with open(env_file, 'w') as f:
            f.write("# PostgreSQL Database Configuration\n")
            f.write(f"DB_HOST={DATABASE_CONFIG['host']}\n")
            f.write(f"DB_PORT={DATABASE_CONFIG['port']}\n")
            f.write(f"DB_NAME={DATABASE_CONFIG['database']}\n")
            f.write(f"DB_USER={DATABASE_CONFIG['user']}\n")
            f.write("DB_PASSWORD=your_password_here\n")
            f.write(f"DB_SSLMODE={DATABASE_CONFIG['sslmode']}\n")
        return True

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup PostgreSQL database for Nigerian E-commerce Customer Support Agent')
    parser.add_argument('--skip-postgres-check', action='store_true', help='Skip PostgreSQL installation check')
    parser.add_argument('--skip-schema', action='store_true', help='Skip schema creation')
    parser.add_argument('--test-only', action='store_true', help='Only test database connection')

    args = parser.parse_args()

    logger.info("🚀 Starting database setup for Nigerian E-commerce Customer Support Agent")

    # Test only mode
    if args.test_only:
        logger.info("🔍 Testing database connection...")
        if test_database_setup():
            logger.info("✅ Database test completed successfully!")
        else:
            logger.error("❌ Database test failed!")
            sys.exit(1)
        return

    # Check PostgreSQL installation
    if not args.skip_postgres_check:
        logger.info("🔍 Checking PostgreSQL installation...")
        if not check_postgresql_installed():
            logger.error("❌ Please install PostgreSQL and ensure it's in your PATH")
            logger.info("Download PostgreSQL from: https://www.postgresql.org/download/")
            sys.exit(1)

    # Setup environment file
    logger.info("📁 Setting up environment configuration...")
    if not setup_environment_file():
        logger.error("❌ Failed to setup environment file")
        sys.exit(1)

    # Create database
    logger.info("🗃️ Creating database...")
    if not create_database_if_not_exists():
        logger.error("❌ Failed to create database")
        sys.exit(1)

    # Create schema
    if not args.skip_schema:
        logger.info("🏗️ Creating database schema...")
        if not run_schema_script():
            logger.error("❌ Failed to create schema")
            sys.exit(1)

    # Test setup
    logger.info("🧪 Testing database setup...")
    if not test_database_setup():
        logger.error("❌ Database setup test failed")
        sys.exit(1)

    # Prepare for data migration
    logger.info("📦 Preparing data migration...")
    if not migrate_existing_data():
        logger.error("❌ Data migration preparation failed")
        sys.exit(1)

    # Success message
    print("\n" + "="*60)
    print("🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("✅ PostgreSQL database schema created")
    print("✅ Sample data inserted")
    print("✅ Indexes and views configured")
    print("✅ Database connection tested")
    print("\n📋 NEXT STEPS:")
    print("1. Update DB_PASSWORD in .env file")
    print("2. Modify your main application to use the new database")
    print("3. Run data migration for existing customers")
    print("4. Update your AI agent to use PostgreSQL instead of synthetic data")
    print("\n🔗 FILES CREATED:")
    print("- database_schema.sql (Complete PostgreSQL schema)")
    print("- config/database_config.py (Database connection utilities)")
    print("- setup_database.py (This setup script)")
    print("- .env (Environment configuration)")
    print("="*60)

if __name__ == "__main__":
    main()
