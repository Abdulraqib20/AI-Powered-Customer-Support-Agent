#!/usr/bin/env python3
"""
Test Login Security - Verify only existing customers can login
"""

import requests
import json

def test_login_security():
    """Test login security with valid and invalid emails"""

    base_url = "http://127.0.0.1:5000"

    print("🔐 Testing Login Security...")

    # Create a session for making requests
    session = requests.Session()

    # Test 1: Try to login with an email that doesn't exist
    print("\n1️⃣ Testing login with non-existent email...")
    invalid_login_data = {"email": "nonexistent@example.com"}
    response = session.post(
        f"{base_url}/api/login",
        json=invalid_login_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 404:
        data = response.json()
        print(f"✅ PASS: Non-existent email rejected: {data.get('message')}")
    else:
        print(f"❌ FAIL: Non-existent email was accepted! Status: {response.status_code}")
        print(f"Response: {response.text}")

    # Test 2: Try to login with the valid test customer email
    print("\n2️⃣ Testing login with valid customer email...")
    valid_login_data = {"email": "abdulraqibshakir03@gmail.com"}
    response = session.post(
        f"{base_url}/api/login",
        json=valid_login_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ PASS: Valid customer email accepted: {data.get('message')}")
        print(f"👤 Customer: {data.get('customer_name')}")
    else:
        print(f"❌ FAIL: Valid customer email was rejected! Status: {response.status_code}")
        print(f"Response: {response.text}")

    # Test 3: Try to access personal data without login
    print("\n3️⃣ Testing personal data access without login...")
    session_without_login = requests.Session()
    test_query = {
        "query": "Show me my recent orders",
        "include_sql": False
    }

    response = session_without_login.post(
        f"{base_url}/api/enhanced-query",
        json=test_query,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        if "log in first" in data.get('response', '').lower() or "authentication" in data.get('response', '').lower():
            print("✅ PASS: Personal data access requires authentication")
        else:
            print(f"❌ FAIL: Personal data was accessible without login: {data.get('response')}")
    else:
        print(f"❌ ERROR: Unexpected response status: {response.status_code}")

    # Test 4: Try to access personal data with valid login
    print("\n4️⃣ Testing personal data access with valid login...")
    response = session.post(  # Using session with login from Test 2
        f"{base_url}/api/enhanced-query",
        json=test_query,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        if "order" in data.get('response', '').lower() and not ("log in" in data.get('response', '').lower()):
            print("✅ PASS: Personal data accessible after valid login")
        else:
            print(f"🔍 INFO: Response for authenticated user: {data.get('response')}")
    else:
        print(f"❌ ERROR: Unexpected response status: {response.status_code}")

    print("\n🔐 Login Security Test Complete!")

if __name__ == "__main__":
    test_login_security()
