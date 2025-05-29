#!/usr/bin/env python3
"""
Test script to check Flask app functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_imports():
    """Test if all imports work"""
    print("🧪 Testing imports...")

    try:
        from flask import Flask
        print("✅ Flask import successful")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False

    try:
        from config.database_config import DatabaseManager
        print("✅ Database config import successful")
    except ImportError as e:
        print(f"❌ Database config import failed: {e}")
        return False

    try:
        from src.enhanced_db_querying import EnhancedDatabaseQuerying
        print("✅ Enhanced DB querying import successful")
    except ImportError as e:
        print(f"❌ Enhanced DB querying import failed: {e}")
        return False

    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing database connection...")

    try:
        from config.database_config import DatabaseManager
        db_manager = DatabaseManager()
        print("✅ Database manager initialized")

        # Test a simple query
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers LIMIT 1")
            result = cursor.fetchone()
            print(f"✅ Database query successful: {result[0]} customers found")

        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_enhanced_querying():
    """Test enhanced database querying system"""
    print("\n🧠 Testing enhanced database querying...")

    try:
        from src.enhanced_db_querying import EnhancedDatabaseQuerying
        enhanced_db = EnhancedDatabaseQuerying()
        print("✅ Enhanced DB querying initialized")

        # Test a simple query
        result = enhanced_db.process_query("How many customers do we have?", "test_user")
        print(f"✅ Enhanced query successful: {result['success']}")
        if result['success']:
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"   Error: {result.get('error_message', 'Unknown error')}")

        return result['success']
    except Exception as e:
        print(f"❌ Enhanced querying failed: {e}")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    print("\n🌐 Testing Flask app...")

    try:
        # Set environment variables if needed
        os.environ.setdefault('FLASK_ENV', 'development')

        from app import app
        print("✅ Flask app imported successfully")

        # Test app configuration
        with app.app_context():
            print("✅ Flask app context created")

        return True
    except Exception as e:
        print(f"❌ Flask app initialization failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Flask App Tests\n")

    tests = [
        ("Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("Enhanced Querying", test_enhanced_querying),
        ("Flask App", test_flask_app)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    print("\n📊 Test Results:")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Flask app should work correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
