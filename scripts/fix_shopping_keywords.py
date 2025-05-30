#!/usr/bin/env python3
"""
🛠️ Fix Shopping Keywords
================================================================================

Add missing shopping keywords like 'add', 'buy', etc. to ensure proper detection.
"""

def fix_shopping_keywords():
    """Add missing shopping keywords"""
    print("🛠️ Fixing shopping keywords...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the shopping keywords section
    old_keywords = '''shopping_keywords = [
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

                        # 🆕 COMPLETE CHECKOUT PATTERNS - Auto-place order
                        'address is', 'method is', 'payment method i want',
                        'delivery address', 'using raqibpay', 'pay with raqibpay',
                        'lugbe', 'abuja', 'lagos', # Common Nigerian locations
                        'raqibtech pay', 'raqib tech pay'
                    ]'''

    new_keywords = '''shopping_keywords = [
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
                    ]'''

    if old_keywords in content:
        content = content.replace(old_keywords, new_keywords)
        print("✅ Updated shopping keywords with missing patterns")
    else:
        print("⚠️ Could not find exact shopping keywords pattern")

    # Also remove duplicate code blocks
    duplicate_pattern = '''# 🆕 DIRECT ORDER PLACEMENT: When user says "place order for X", auto-extract product and place order
                        direct_order_patterns = ['place order for', 'order for', 'place the order for', 'buy the', 'purchase the']
                        is_direct_order = any(pattern in user_query_lower for pattern in direct_order_patterns)

                        if is_direct_order:
                            logger.info(f"🎯 DIRECT ORDER DETECTED: {user_query[:100]}...")
                            # Auto-set delivery and payment for direct orders
                            user_query = f"{user_query} delivery_address:Lagos payment_method:RaqibTechPay"
                            logger.info("🚀 Auto-adding default delivery and payment for direct order")
                        # 🆕 DIRECT ORDER PLACEMENT: When user says "place order for X", auto-extract product and place order
                        direct_order_patterns = ['place order for', 'order for', 'place the order for', 'buy the', 'purchase the']
                        is_direct_order = any(pattern in user_query_lower for pattern in direct_order_patterns)

                        if is_direct_order:
                            logger.info(f"🎯 DIRECT ORDER DETECTED: {user_query[:100]}...")
                            # Auto-set delivery and payment for direct orders
                            user_query = f"{user_query} delivery_address:Lagos payment_method:RaqibTechPay"
                            logger.info("🚀 Auto-adding default delivery and payment for direct order")
                        # 🆕 DIRECT ORDER PLACEMENT: When user says "place order for X", auto-extract product and place order
                        direct_order_patterns = ['place order for', 'order for', 'place the order for', 'buy the', 'purchase the']
                        is_direct_order = any(pattern in user_query_lower for pattern in direct_order_patterns)

                        if is_direct_order:
                            logger.info(f"🎯 DIRECT ORDER DETECTED: {user_query[:100]}...")
                            # Auto-set delivery and payment for direct orders
                            user_query = f"{user_query} delivery_address:Lagos payment_method:RaqibTechPay"
                            logger.info("🚀 Auto-adding default delivery and payment for direct order")'''

    clean_pattern = '''# 🆕 DIRECT ORDER PLACEMENT: When user says "place order for X", auto-extract product and place order
                        direct_order_patterns = ['place order for', 'order for', 'place the order for', 'buy the', 'purchase the']
                        is_direct_order = any(pattern in user_query_lower for pattern in direct_order_patterns)

                        if is_direct_order:
                            logger.info(f"🎯 DIRECT ORDER DETECTED: {user_query[:100]}...")
                            # Auto-set delivery and payment for direct orders
                            user_query = f"{user_query} delivery_address:Lagos payment_method:RaqibTechPay"
                            logger.info("🚀 Auto-adding default delivery and payment for direct order")'''

    if duplicate_pattern in content:
        content = content.replace(duplicate_pattern, clean_pattern)
        print("✅ Removed duplicate code blocks")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🎉 Shopping keywords fixed!")

if __name__ == "__main__":
    print("🛠️ FIXING SHOPPING KEYWORDS")
    print("=" * 60)
    fix_shopping_keywords()
    print("\n✅ Now 'Add Samsung Galaxy A24 to my cart' should work!")
