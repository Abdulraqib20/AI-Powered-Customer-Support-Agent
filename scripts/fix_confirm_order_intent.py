#!/usr/bin/env python3
"""
🛠️ Fix Confirm Order Intent
================================================================================

Fix the intent parsing so 'confirm order' is recognized as place_order.
"""

def fix_confirm_order_intent():
    """Fix the intent parsing for confirm order"""
    print("🛠️ Fixing confirm order intent parsing...")

    with open('src/order_ai_assistant.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and enhance the place_order patterns
    old_patterns = '''            'place_order': [
                'place order', 'checkout', 'proceed to checkout', 'complete order',
                'finalize order', 'confirm order', 'submit order', 'buy now',
                'complete purchase', 'finish order', 'pay and order', 'order now',
                'use raqibpay', 'pay with raqibpay', 'raqibpay payment'
            ],'''

    new_patterns = '''            'place_order': [
                'place order', 'checkout', 'proceed to checkout', 'complete order',
                'finalize order', 'confirm order', 'submit order', 'buy now',
                'complete purchase', 'finish order', 'pay and order', 'order now',
                'use raqibpay', 'pay with raqibpay', 'raqibpay payment',
                'confirm', 'place', 'order', 'proceed', 'complete'
            ],'''

    if old_patterns in content:
        content = content.replace(old_patterns, new_patterns)
        print("✅ Enhanced place_order patterns")
    else:
        print("⚠️ Could not find place_order patterns")

    # Also enhance the add_to_cart patterns to be more specific
    old_add_patterns = '''            'add_to_cart': [
                'add to cart', 'add the', 'put in cart', 'add this', 'I want to buy',
                'purchase', 'buy', 'order', 'get this', 'add it', 'cart it',
                'add samsung', 'buy samsung', 'purchase samsung', 'get samsung',
                'add phone', 'buy phone', 'add galaxy', 'buy galaxy'
            ],'''

    new_add_patterns = '''            'add_to_cart': [
                'add to cart', 'add the', 'put in cart', 'add this', 'I want to buy',
                'purchase', 'buy', 'get this', 'add it', 'cart it',
                'add samsung', 'buy samsung', 'purchase samsung', 'get samsung',
                'add phone', 'buy phone', 'add galaxy', 'buy galaxy'
            ],'''

    if old_add_patterns in content:
        content = content.replace(old_add_patterns, new_add_patterns)
        print("✅ Made add_to_cart patterns more specific")
    else:
        print("⚠️ Could not find add_to_cart patterns")

    with open('src/order_ai_assistant.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🎉 Intent parsing fixed!")

if __name__ == "__main__":
    print("🛠️ FIXING CONFIRM ORDER INTENT")
    print("=" * 60)
    fix_confirm_order_intent()
    print("\n✅ Now 'confirm order' should trigger place_order intent!")
