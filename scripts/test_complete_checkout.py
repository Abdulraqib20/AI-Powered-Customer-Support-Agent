#!/usr/bin/env python3
"""
🧪 Test Complete Checkout Flow
================================================================================

This script tests the enhanced checkout flow to ensure:
1. Shopping actions are detected for delivery/payment patterns
2. Cart items are preserved across messages
3. Orders are actually placed in the database
"""

import sys
import os
sys.path.append('src')

from enhanced_db_querying import EnhancedDatabaseQuerying

def test_complete_checkout():
    """Test the complete checkout flow"""
    print("🧪 TESTING COMPLETE CHECKOUT FLOW")
    print("=" * 60)

    # Initialize the enhanced database querying system
    enhanced_db = EnhancedDatabaseQuerying()

    # Simulate authenticated session
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,
        'user_id': 'customer_1503'
    }

    # Test queries that should trigger shopping actions
    test_queries = [
        "I want to buy a Samsung phone",
        "Add the Samsung Galaxy A24 to cart",
        "My delivery address is Anyim Pius Anyim Street, Lugbe, Abuja. The payment method I want to use is RaqibTechPay"
    ]

    print("🎯 TESTING CHECKOUT FLOW:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        print("-" * 40)

        try:
            result = enhanced_db.process_enhanced_query(query, session_context)

            print(f"✅ Success: {result['success']}")
            print(f"🎯 Query Type: {result.get('query_type', 'N/A')}")

            if 'shopping_action' in result:
                print(f"🛒 Shopping Action: {result['shopping_action']}")
                shopping_data = result.get('shopping_data', {})
                print(f"💬 Action: {shopping_data.get('action', 'N/A')}")
                if 'order_id' in shopping_data:
                    print(f"🎉 ORDER PLACED! Order ID: {shopping_data['order_id']}")

            print(f"📝 Response Preview: {result['response'][:150]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("🏁 CHECKOUT FLOW TEST COMPLETED")

def test_shopping_keywords():
    """Test that the new shopping keywords are detected"""
    print("\n🔍 TESTING ENHANCED SHOPPING KEYWORDS")
    print("=" * 60)

    enhanced_db = EnhancedDatabaseQuerying()
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,
        'user_id': 'customer_1503'
    }

    # Test the exact message from your logs
    test_message = "my delivery address is Anyim Pius Anyim Street, Lugbe, Abuja. The payment method I want to use is RaqibTechPay"

    print(f"Testing message: '{test_message}'")

    try:
        result = enhanced_db.process_enhanced_query(test_message, session_context)

        if result.get('query_type') == 'shopping_action':
            print("✅ DETECTED AS SHOPPING ACTION!")
            print(f"🛒 Shopping Action: {result.get('shopping_action', 'N/A')}")

            shopping_data = result.get('shopping_data', {})
            if shopping_data.get('success'):
                print("🎉 SHOPPING ACTION SUCCESSFUL!")
                if 'order_id' in shopping_data:
                    print(f"📦 Order placed: {shopping_data['order_id']}")
            else:
                print(f"⚠️ Shopping action failed: {shopping_data.get('message', 'Unknown')}")
        else:
            print(f"❌ NOT detected as shopping action. Type: {result.get('query_type', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_complete_checkout()
    test_shopping_keywords()
