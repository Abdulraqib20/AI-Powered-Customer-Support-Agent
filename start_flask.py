#!/usr/bin/env python3
"""
Nigerian E-commerce Customer Support Agent - Startup Script
This script checks dependencies and starts the Flask application
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")

    required_packages = [
        'flask',
        'psycopg2',
        'redis',
        'groq',
        'google-generativeai'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False

    return True

def check_database_connection():
    """Check if PostgreSQL database is accessible"""
    print("\n🗄️ Checking database connection...")

    try:
        import psycopg2

        # Try to connect to the database
        conn = psycopg2.connect(
            host="localhost",
            database="nigerian_ecommerce",
            user="postgres",
            password="password"  # Default password, should be in env
        )
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and the database exists")
        return False

def check_redis_connection():
    """Check if Redis is accessible"""
    print("\n🔴 Checking Redis connection...")

    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("Redis is optional but recommended for caching")
        return True  # Don't fail startup for Redis

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🔧 Checking environment variables...")

    # Try to load from .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        print("📄 Loading .env file...")
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ.setdefault(key, value)

    required_vars = ['GROQ_API_KEY', 'GOOGLE_API_KEY']
    optional_vars = ['QDRANT_URL_LOCAL', 'QDRANT_API_KEY']

    missing_required = []

    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            print(f"❌ {var} - Missing")
            missing_required.append(var)

    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            print(f"⚠️ {var} - Optional, using defaults")

    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        print("Create a .env file or set these environment variables")
        return False

    return True

def start_flask_app():
    """Start the Flask application"""
    print("\n🚀 Starting Flask application...")

    # Change to flask_app directory
    flask_dir = Path('flask_app')
    if not flask_dir.exists():
        print("❌ flask_app directory not found")
        return False

    os.chdir(flask_dir)

    # Set Flask environment variables
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'

    try:
        # Import and run the Flask app
        sys.path.append('..')
        from app import app

        print("✅ Flask app imported successfully")
        print("\n🌐 Starting server on http://localhost:5000")
        print("Press Ctrl+C to stop the server")

        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to avoid double startup
        )

    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return False

def main():
    """Main startup function"""
    print("🇳🇬 Nigerian E-commerce Customer Support Agent")
    print("=" * 50)

    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Database", check_database_connection),
        ("Redis", check_redis_connection),
        ("Environment", check_environment_variables)
    ]

    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False

    if not all_passed:
        print("\n❌ Some checks failed. Please fix the issues above before starting.")
        return False

    print("\n✅ All checks passed!")
    time.sleep(1)

    # Start the Flask app
    return start_flask_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
