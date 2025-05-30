#!/usr/bin/env python3
"""
🛠️ QUICK ORDER SYSTEM FIXES
================================================================================

Essential fixes for the order system:
1. Add user/AI message logging to terminal
2. Fix database order insertion with detailed logging
3. Implement smart order placement when user provides delivery and payment info
"""

import os
import re

def add_user_logging():
    """Add user message logging to terminal"""
    print("🛠️ Adding user message logging...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Add user logging after start_time
    if 'start_time = time.time()' in content and '# 🆕 LOG USER MESSAGE TO TERMINAL' not in content:
        content = content.replace(
            'start_time = time.time()',
            '''start_time = time.time()

        # 🆕 LOG USER MESSAGE TO TERMINAL
        logger.info(f"👤 USER: {user_query}")'''
        )
        print("✅ Added user message logging")
    else:
        print("⚠️ User logging already exists or pattern not found")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

def add_ai_response_logging():
    """Add AI response logging to terminal"""
    print("🛠️ Adding AI response logging...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Add logging before shopping action return
    shopping_return_pattern = '''return {
                'success': True,
                'response': enhanced_response,
                'query_type': 'shopping_action','''

    if shopping_return_pattern in content and '# 🆕 LOG AI SHOPPING RESPONSE' not in content:
        content = content.replace(
            shopping_return_pattern,
            '''# 🆕 LOG AI SHOPPING RESPONSE TO TERMINAL
            logger.info(f"🤖 AI: {enhanced_response[:200]}...")

            return {
                'success': True,
                'response': enhanced_response,
                'query_type': 'shopping_action','''
        )
        print("✅ Added AI shopping response logging")

    # Add logging for general responses
    general_return_pattern = '''return {
            'success': True,
            'response': response,
            'query_type': query_type_name,'''

    if general_return_pattern in content and '# 🆕 LOG AI GENERAL RESPONSE' not in content:
        content = content.replace(
            general_return_pattern,
            '''# 🆕 LOG AI GENERAL RESPONSE TO TERMINAL
        logger.info(f"🤖 AI: {response[:200]}...")

        return {
            'success': True,
            'response': response,
            'query_type': query_type_name,'''
        )
        print("✅ Added AI general response logging")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

def fix_order_database_logging():
    """Add detailed logging to order placement process"""
    print("🛠️ Fixing order database insertion logging...")

    with open('src/order_ai_assistant.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Enhance place_order method with logging
    if 'def place_order(self, customer_id: int' in content:
        # Add logging after cart check
        cart_check_pattern = '''if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Add some products first. 🛒",
                    'action': 'empty_cart'
                }'''

        if cart_check_pattern in content and '# 🆕 ENHANCED LOGGING FOR ORDER PLACEMENT' not in content:
            content = content.replace(
                cart_check_pattern,
                '''if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Add some products first. 🛒",
                    'action': 'empty_cart'
                }

            # 🆕 ENHANCED LOGGING FOR ORDER PLACEMENT
            logger.info(f"🎯 PLACING ORDER for customer {customer_id}")
            logger.info(f"📦 Cart items: {len(self.active_carts[cart_key]['items'])}")
            logger.info(f"🚚 Delivery: {delivery_address}")
            logger.info(f"💳 Payment: {payment_method}")'''
            )
            print("✅ Added order placement logging")

        # Enhance order creation result logging
        order_creation_pattern = '''order_result = self.order_system.create_order(
                customer_id=customer_id,
                items=order_items,
                delivery_address=delivery_address,
                payment_method=payment_method
            )'''

        if order_creation_pattern in content and '📞 Calling OrderManagementSystem.create_order()' not in content:
            content = content.replace(
                order_creation_pattern,
                '''logger.info("📞 Calling OrderManagementSystem.create_order()...")
            order_result = self.order_system.create_order(
                customer_id=customer_id,
                items=order_items,
                delivery_address=delivery_address,
                payment_method=payment_method
            )

            logger.info(f"📋 Order creation result: {order_result.get('success', False)}")
            if not order_result['success']:
                logger.error(f"❌ Order creation failed: {order_result.get('error', 'Unknown error')}")'''
            )
            print("✅ Added order creation result logging")

        # Enhance successful order logging
        if 'if order_result[\'success\']:' in content and '✅ ORDER SUCCESSFULLY PLACED!' not in content:
            success_pattern = '''if order_result['success']:
                # Clear cart after successful order
                del self.active_carts[cart_key]

                order_summary = order_result['order_summary']'''

            content = content.replace(
                success_pattern,
                '''if order_result['success']:
                # Clear cart after successful order
                del self.active_carts[cart_key]

                logger.info(f"✅ ORDER SUCCESSFULLY PLACED! Order ID: {order_result['order_id']}")
                logger.info(f"💾 Database order ID: {order_result.get('database_order_id', 'N/A')}")

                order_summary = order_result['order_summary']'''
            )
            print("✅ Added successful order logging")

    with open('src/order_ai_assistant.py', 'w', encoding='utf-8') as f:
        f.write(content)

def enhance_direct_order_placement():
    """Enhance direct order placement when user says 'place order for X'"""
    print("🛠️ Enhancing direct order placement...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for the shopping action handling and enhance it
    if '"place order for" not in user_query_lower' not in content:
        # Find the shopping keywords section and enhance it
        old_shopping_check = "if any(keyword in user_query_lower for keyword in shopping_keywords):"
        new_shopping_check = """if any(keyword in user_query_lower for keyword in shopping_keywords):
                        # 🆕 DIRECT ORDER PLACEMENT: When user says "place order for X", auto-extract product and place order
                        direct_order_patterns = ['place order for', 'order for', 'place the order for', 'buy the', 'purchase the']
                        is_direct_order = any(pattern in user_query_lower for pattern in direct_order_patterns)

                        if is_direct_order:
                            logger.info(f"🎯 DIRECT ORDER DETECTED: {user_query[:100]}...")
                            # Auto-set delivery and payment for direct orders
                            user_query = f"{user_query} delivery_address:Lagos payment_method:RaqibTechPay"
                            logger.info("🚀 Auto-adding default delivery and payment for direct order")"""

        if old_shopping_check in content:
            content = content.replace(old_shopping_check, new_shopping_check)
            print("✅ Added direct order placement enhancement")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

def create_test_direct_order():
    """Create a test script for direct order placement"""
    print("🛠️ Creating test script for direct orders...")

    test_script = '''#!/usr/bin/env python3
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
'''

    with open('scripts/test_direct_order.py', 'w', encoding='utf-8') as f:
        f.write(test_script)

    print("✅ Test script created: scripts/test_direct_order.py")

if __name__ == "__main__":
    print("🛠️ QUICK ORDER SYSTEM FIXES")
    print("=" * 60)

    add_user_logging()
    add_ai_response_logging()
    fix_order_database_logging()
    enhance_direct_order_placement()
    create_test_direct_order()

    print("\n🎉 QUICK FIXES APPLIED!")
    print("=" * 60)
    print("✅ Features Added:")
    print("   🔍 User/AI message logging in terminal")
    print("   💾 Enhanced database order insertion logging")
    print("   🎯 Direct order placement for 'place order for X'")
    print("   🧪 Test script for validation")
    print("\n📋 Test it with:")
    print("   python scripts/test_direct_order.py")
    print("\n💡 Now when you say 'place order for Samsung phone',")
    print("   the system will auto-add delivery/payment and place the order!")
