#!/usr/bin/env python3
"""
🧪 Test Direct Order Placement
"""

import sys
import os
sys.path.append('src')

def test_direct_order():
    print("🧪 TESTING DIRECT ORDER PLACEMENT")
    print("=" * 60)

    from enhanced_db_querying import EnhancedDatabaseQuerying

    # Initialize system
    enhanced_db = EnhancedDatabaseQuerying()

    # Test session
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,
        'user_id': 'customer_1503'
    }

    # Test direct order placement
    test_query = "place the order for the Samsung phone for me"

    print(f"🎯 Testing: '{test_query}'")
    print("-" * 40)

    try:
        result = enhanced_db.process_enhanced_query(test_query, session_context)

        print(f"✅ Success: {result['success']}")
        print(f"🎭 Query Type: {result.get('query_type', 'N/A')}")

        if result.get('query_type') == 'shopping_action':
            shopping_data = result.get('shopping_data', {})
            print(f"🛒 Shopping Action: {shopping_data.get('action', 'N/A')}")

            if 'order_id' in shopping_data:
                print(f"🎉 ORDER PLACED! Order ID: {shopping_data['order_id']}")
                print(f"💾 Database ID: {shopping_data.get('database_order_id', 'N/A')}")
            else:
                print(f"📝 Cart Action: {shopping_data.get('message', 'N/A')}")

        print(f"📝 Response: {result['response'][:300]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_order()
