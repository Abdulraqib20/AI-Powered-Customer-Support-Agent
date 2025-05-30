#!/usr/bin/env python3
"""
Test script to verify quick actions work correctly
"""

import requests
import json

def test_quick_action():
    """Test the enhanced query API endpoint with a pending orders query"""

    print("🧪 Testing Quick Action: Pending Orders")
    print("=" * 50)

    # Test the exact query that the "Pending Orders" button sends
    test_query = "Show orders with status Pending"

    try:
        # Make API request
        response = requests.post(
            'http://localhost:5000/api/enhanced-query',
            json={'query': test_query, 'include_sql': True},
            timeout=30
        )

        print(f"📡 API Request: POST /api/enhanced-query")
        print(f"📝 Query: '{test_query}'")
        print(f"🔄 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print("✅ API Response Success!")
            print(f"🎯 Query Type: {data.get('query_type', 'N/A')}")
            print(f"📊 Results Count: {data.get('results_count', 0)}")
            print(f"⏱️ Execution Time: {data.get('execution_time', 'N/A')}")
            print(f"✨ Has Results: {data.get('has_results', False)}")

            # Check SQL query
            if data.get('sql_query'):
                print(f"🗄️ Generated SQL: {data['sql_query']}")

            # Check response content
            response_text = data.get('response', '')
            if response_text:
                print(f"💬 AI Response: {response_text[:200]}...")
            else:
                print("⚠️ No response text generated")

            # Check for errors
            if data.get('error_message'):
                print(f"❌ Error: {data['error_message']}")
            else:
                print("✅ No errors reported")

        else:
            print(f"❌ API Request Failed")
            print(f"Response: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_quick_action()
