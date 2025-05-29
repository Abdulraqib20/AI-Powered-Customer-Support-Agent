#!/usr/bin/env python3
"""
Test Session Management System
"""

import requests
import json
import time

def test_session_management():
    """Test the session management system"""

    base_url = "http://127.0.0.1:5000"

    print("🧪 Testing Session Management System...")

    # Create a session for making requests
    session = requests.Session()

    try:
        # Test 1: Health check
        print("\n1️⃣ Testing health endpoint...")
        response = session.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"📋 Session ID: {data.get('session_id', 'Not provided')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return

        # Test 2: Dashboard load
        print("\n2️⃣ Testing dashboard load...")
        response = session.get(base_url)
        if response.status_code == 200:
            print("✅ Dashboard loaded successfully")
        else:
            print(f"❌ Dashboard load failed: {response.status_code}")

        # Test 3: Get conversations (should be empty initially)
        print("\n3️⃣ Testing conversations API...")
        response = session.get(f"{base_url}/api/conversations")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conversations API working: {len(data.get('conversations', []))} conversations")
        else:
            print(f"❌ Conversations API failed: {response.status_code}")

        # Test 4: Create new conversation
        print("\n4️⃣ Testing new conversation creation...")
        response = session.post(f"{base_url}/api/conversations/new")
        if response.status_code == 200:
            data = response.json()
            conversation_id = data.get('conversation_id')
            print(f"✅ New conversation created: {conversation_id}")
        else:
            print(f"❌ Conversation creation failed: {response.status_code}")
            return

        # Test 5: Send a test message
        print("\n5️⃣ Testing enhanced query with session...")
        test_query = {
            "query": "Hello, can you help me track my order?",
            "include_sql": False
        }

        response = session.post(
            f"{base_url}/api/enhanced-query",
            json=test_query,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Enhanced query successful")
            print(f"📝 Response: {data.get('response', '')[:100]}...")
            print(f"🔍 Query Type: {data.get('query_type', 'Unknown')}")
        else:
            print(f"❌ Enhanced query failed: {response.status_code}")
            if response.text:
                print(f"Error: {response.text}")

        # Test 6: Get conversation messages
        print("\n6️⃣ Testing conversation messages...")
        response = session.get(f"{base_url}/api/conversations/{conversation_id}/messages")
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            print(f"✅ Messages retrieved: {len(messages)} messages")
            for msg in messages:
                print(f"   {msg['sender_type']}: {msg['content'][:50]}...")
        else:
            print(f"❌ Messages retrieval failed: {response.status_code}")

        # Test 7: Test login functionality
        print("\n7️⃣ Testing login functionality...")
        login_data = {"email": "test.customer@raqibtech.com"}
        response = session.post(
            f"{base_url}/api/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful: {data.get('message')}")
            print(f"👤 User: {data.get('user_email')}")
        else:
            print(f"❌ Login failed: {response.status_code}")

        # Test 8: Test authenticated query
        print("\n8️⃣ Testing authenticated query...")
        auth_query = {
            "query": "Show me my recent orders",
            "include_sql": False
        }

        response = session.post(
            f"{base_url}/api/enhanced-query",
            json=auth_query,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authenticated query successful")
            print(f"📝 Response: {data.get('response', '')[:100]}...")
            print(f"🔐 Session authenticated: {data.get('session_authenticated', False)}")
        else:
            print(f"❌ Authenticated query failed: {response.status_code}")

        print("\n🎉 Session Management Test Complete!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_session_management()
