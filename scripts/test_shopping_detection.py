#!/usr/bin/env python3
"""
🧪 Test Shopping Keyword Detection
================================================================================

Simple test to verify shopping keywords are working.
"""

import sys
sys.path.append('src')

def test_shopping_detection():
    print("🧪 TESTING SHOPPING KEYWORD DETECTION")
    print("=" * 60)

    # Test shopping keywords
    shopping_keywords = [
        # 🆕 ADD TO CART PATTERNS (MOST IMPORTANT)
        'add', 'add samsung', 'add galaxy', 'add phone', 'add to my cart',
        'buy', 'buy samsung', 'buy phone', 'get samsung', 'get phone',
        'order samsung', 'order phone', 'want samsung', 'want phone',

        # Original order patterns
        'add to cart', 'place order', 'checkout', 'proceed to checkout',
        'buy now', 'purchase', 'place the order', 'complete order',
        'use raqibpay', 'pay with', 'payment method',

        # 🆕 DELIVERY ADDRESS PATTERNS - Auto-trigger checkout
        'delivery address is', 'my address is', 'deliver to',
        'shipping address', 'send to', 'address:', 'deliver at',
        'my delivery address', 'ship to', 'delivery location',

        # 🆕 PAYMENT METHOD PATTERNS - Auto-trigger checkout
        'payment method is', 'pay with', 'use raqibpay',
        'payment option', 'i want to pay', 'payment preference',
        'method i want', 'raqibpay', 'pay on delivery',
        'want to use', 'i want to use raqibpay',

        # 🆕 COMPLETE CHECKOUT PATTERNS - Auto-place order
        'address is', 'method is', 'payment method i want',
        'delivery address', 'using raqibpay', 'pay with raqibpay',
        'lugbe', 'abuja', 'lagos', # Common Nigerian locations
        'raqibtech pay', 'raqib tech pay', 'confirm order', 'confirm'
    ]

    test_queries = [
        "Add Samsung Galaxy A24 to my cart",
        "My delivery address is Lugbe, Abuja",
        "I want to use RaqibTechPay",
        "Confirm order",
        "place the order for the Samsung phone for me"
    ]

    for query in test_queries:
        query_lower = query.lower()
        matched_keywords = [keyword for keyword in shopping_keywords if keyword in query_lower]

        print(f"\n📋 Query: '{query}'")
        print(f"🔍 Matched keywords: {matched_keywords}")
        print(f"✅ Shopping detected: {'YES' if matched_keywords else 'NO'}")

        if not matched_keywords:
            print("❌ This query should trigger shopping but doesn't!")

    print("\n" + "=" * 60)
    print("🎯 Now testing with actual system...")

    from enhanced_db_querying import EnhancedDatabaseQuerying

    enhanced_db = EnhancedDatabaseQuerying()

    # Test session with proper authentication
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,
        'user_id': 'customer_1503',
        'customer_verified': True
    }

    test_query = "Add Samsung Galaxy A24 to my cart"
    print(f"\n🧪 Testing: '{test_query}'")

    try:
        result = enhanced_db.process_enhanced_query(test_query, session_context)
        print(f"✅ Success: {result['success']}")
        print(f"🎭 Query Type: {result.get('query_type', 'N/A')}")

        if result.get('query_type') == 'shopping_action':
            print("🎉 SHOPPING ACTION DETECTED!")
            shopping_data = result.get('shopping_data', {})
            print(f"🛒 Action: {shopping_data.get('action', 'N/A')}")
        else:
            print("❌ Shopping action NOT detected - this is the problem!")
            print(f"📝 Response: {result['response'][:100]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shopping_detection()
