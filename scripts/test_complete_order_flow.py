#!/usr/bin/env python3
"""
🧪 Test Complete Order Flow with Progressive Checkout
================================================================================

This script tests:
1. User message logging ✅
2. AI response logging ✅
3. Progressive checkout flow
4. Database order insertion
5. Context preservation
"""

import sys
import os
sys.path.append('src')

def test_complete_order_flow():
    print("🧪 TESTING COMPLETE ORDER FLOW")
    print("=" * 80)

    from enhanced_db_querying import EnhancedDatabaseQuerying

    # Initialize system
    enhanced_db = EnhancedDatabaseQuerying()

    # Test session with proper authentication
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,
        'user_id': 'customer_1503',
        'customer_verified': True
    }

    # Test the complete progressive checkout flow
    test_scenarios = [
        {
            'step': 1,
            'query': "Add Samsung Galaxy A24 to my cart",
            'expected': "Should add to cart and ask for delivery address"
        },
        {
            'step': 2,
            'query': "My delivery address is Lugbe, Abuja",
            'expected': "Should confirm address and ask for payment method"
        },
        {
            'step': 3,
            'query': "I want to use RaqibTechPay",
            'expected': "Should confirm payment and show order summary"
        },
        {
            'step': 4,
            'query': "Confirm order",
            'expected': "Should place order in database and show order ID"
        }
    ]

    print("🎯 PROGRESSIVE CHECKOUT FLOW TEST")
    print("-" * 80)

    for scenario in test_scenarios:
        print(f"\n📋 Step {scenario['step']}: {scenario['query']}")
        print(f"🎯 Expected: {scenario['expected']}")
        print("-" * 40)

        try:
            result = enhanced_db.process_enhanced_query(scenario['query'], session_context)

            print(f"✅ Success: {result['success']}")
            print(f"🎭 Query Type: {result.get('query_type', 'N/A')}")

            if result.get('query_type') == 'shopping_action':
                shopping_data = result.get('shopping_data', {})
                print(f"🛒 Shopping Action: {shopping_data.get('action', 'N/A')}")

                if 'order_id' in shopping_data:
                    print(f"🎉 ORDER PLACED! Order ID: {shopping_data['order_id']}")
                    print(f"💾 Database ID: {shopping_data.get('database_order_id', 'N/A')}")
                    break  # Order completed successfully
                else:
                    print(f"📝 Message: {shopping_data.get('message', 'N/A')[:150]}...")
            else:
                print(f"📝 Response: {result['response'][:150]}...")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n" + "=" * 80)

def test_direct_order_placement():
    print("\n🎯 TESTING DIRECT ORDER PLACEMENT")
    print("=" * 80)

    from enhanced_db_querying import EnhancedDatabaseQuerying

    # Initialize system
    enhanced_db = EnhancedDatabaseQuerying()

    # Test session with proper authentication
    session_context = {
        'user_authenticated': True,
        'customer_id': 1503,
        'user_id': 'customer_1503',
        'customer_verified': True
    }

    # Test direct order placement (should auto-add delivery/payment)
    direct_order_query = "place the order for the Samsung phone for me"

    print(f"📋 Testing: '{direct_order_query}'")
    print("🎯 Expected: Should auto-add delivery/payment and place order directly")
    print("-" * 40)

    try:
        result = enhanced_db.process_enhanced_query(direct_order_query, session_context)

        print(f"✅ Success: {result['success']}")
        print(f"🎭 Query Type: {result.get('query_type', 'N/A')}")

        if result.get('query_type') == 'shopping_action':
            shopping_data = result.get('shopping_data', {})
            print(f"🛒 Shopping Action: {shopping_data.get('action', 'N/A')}")

            if 'order_id' in shopping_data:
                print(f"🎉 ORDER PLACED! Order ID: {shopping_data['order_id']}")
                print(f"💾 Database ID: {shopping_data.get('database_order_id', 'N/A')}")
            else:
                print(f"📝 Cart Action: {shopping_data.get('message', 'N/A')[:150]}...")
        else:
            print(f"📝 Response: {result['response'][:150]}...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_message_logging():
    print("\n🔍 TESTING MESSAGE LOGGING")
    print("=" * 80)
    print("✅ User message logging: Check terminal for '👤 USER:' messages")
    print("✅ AI response logging: Check terminal for '🤖 AI:' messages")
    print("📋 Both should appear in the terminal output above")

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE ORDER SYSTEM TEST")
    print("=" * 80)
    print("🎯 Testing all enhanced features:")
    print("   1. User/AI message logging")
    print("   2. Progressive checkout flow")
    print("   3. Direct order placement")
    print("   4. Database order insertion")
    print("   5. Context preservation")
    print("=" * 80)

    test_complete_order_flow()
    test_direct_order_placement()
    test_message_logging()

    print("\n🎉 TEST COMPLETE!")
    print("=" * 80)
    print("📋 Check the terminal output above for:")
    print("   👤 USER: messages (user logging)")
    print("   🤖 AI: messages (AI response logging)")
    print("   🎯 Order placement attempts")
    print("   💾 Database insertion results")
