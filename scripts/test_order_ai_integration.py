"""
🧪 Test Order AI Assistant Integration
====================================

This script tests the integration between the Order AI Assistant and the Enhanced Database Querying system
to ensure that order placement functionality works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_db_querying import EnhancedDatabaseQuerying
from src.order_ai_assistant import order_ai_assistant

def test_order_ai_integration():
    """Test the Order AI Assistant integration"""
    print("🧪 Testing Order AI Assistant Integration...")
    print("=" * 50)

    # Initialize the enhanced database querying system
    enhanced_db = EnhancedDatabaseQuerying()

    # Test session context (simulate authenticated user)
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,  # Using the customer from your logs
        'customer_verified': True,
        'user_id': 'customer_1503',
        'customer_email': 'abdulraqibshakir03@gmail.com'
    }

    # Test queries that should trigger shopping actions
    test_queries = [
        "Add the Samsung phone to cart",
        "Place order",
        "Proceed to checkout",
        "Use RaqibPay",
        "I want to buy the Samsung Galaxy A24"
    ]

    print("🛒 Testing shopping action detection and processing...")
    print()

    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: '{query}'")
        print("-" * 30)

        try:
            result = enhanced_db.process_enhanced_query(query, session_context)

            print(f"✅ Success: {result['success']}")
            print(f"🎯 Query Type: {result.get('query_type', 'N/A')}")
            print(f"⚡ Execution Time: {result.get('execution_time', 'N/A')}")

            if 'shopping_action' in result:
                print(f"🛒 Shopping Action: {result['shopping_action']}")
                print(f"📝 Shopping Data: {result.get('shopping_data', {}).get('action', 'N/A')}")

            print(f"💬 Response: {result['response'][:100]}...")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()

    print("🔍 Testing direct Order AI Assistant functions...")
    print("-" * 50)

    # Test direct order AI functions
    customer_id = 1503

    # Test intent parsing
    print("1. Testing intent parsing:")
    test_message = "Add Samsung phone to cart"
    intent_result = order_ai_assistant.parse_order_intent(test_message)
    print(f"   Intent: {intent_result['intent']}")
    print(f"   Confidence: {intent_result['confidence']}")
    print()

    # Test product extraction
    print("2. Testing product extraction:")
    product_info = order_ai_assistant.extract_product_info(test_message)
    print(f"   Extracted brands: {product_info.get('extracted_brands', [])}")
    print(f"   Found in context: {product_info.get('found_in_context', False)}")
    print()

    # Test cart operations (this will fail if product not found, which is expected)
    print("3. Testing cart operations:")
    try:
        # This should fail gracefully since we don't have product context
        cart_result = order_ai_assistant.add_to_cart(customer_id, {'product_id': 1}, 1)
        print(f"   Cart result: {cart_result['success']}")
        print(f"   Message: {cart_result['message']}")
    except Exception as e:
        print(f"   Expected error (no product context): {e}")
    print()

    print("✅ Integration test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_order_ai_integration()
