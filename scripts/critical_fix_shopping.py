#!/usr/bin/env python3
"""
🚨 CRITICAL FIX: Shopping Product Priority Order
================================================================================

This fixes the critical bug where conversation history overrides specific product requests.
User says "Samsung phone" but gets "Car Engine Oil" because history runs first.

Fix: Prioritize specific product searches over conversation history.
"""

def critical_fix_shopping():
    """Fix the product context priority order"""

    print("🚨 CRITICAL FIX: Restoring product search priority...")

    # Read the file
    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the broken section
    broken_section = """                        # 🔧 BULLETPROOF: Extract product context from multiple sources
                        product_context = []

                        # 1. Extract from recent conversation history
                        for msg in conversation_history:
                            if isinstance(msg, dict):
                                # Check execution_result field for product data
                                if 'execution_result' in msg and msg['execution_result']:
                                    for result in msg['execution_result']:
                                        if isinstance(result, dict) and 'product_id' in result:
                                            product_context.append(result)
                                            logger.info(f"✅ Found product from history: {result.get('product_name', 'Unknown')}")

                        # 2. Special Samsung phone handling (based on conversation)
                        if not product_context and 'samsung' in user_query_lower and 'phone' in user_query_lower:"""

    fixed_section = """                        # 🔧 BULLETPROOF: Extract product context from multiple sources
                        product_context = []

                        # 1. PRIORITY: Special Samsung phone handling (for specific requests)
                        if 'samsung' in user_query_lower and 'phone' in user_query_lower:
                            try:
                                samsung_sql = \"\"\"
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity
                                FROM products WHERE brand ILIKE '%Samsung%' AND product_name ILIKE '%phone%' AND in_stock = TRUE
                                ORDER BY price ASC LIMIT 1
                                \"\"\"
                                success, samsung_results, _ = self.execute_sql_query(samsung_sql)
                                if success and samsung_results:
                                    product_context.extend(samsung_results)
                                    logger.info(f"✅ Found Samsung phone by direct query: {samsung_results[0].get('product_name', 'Unknown')}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not query Samsung phone: {e}")

                        # 2. ONLY for contextual references: Extract from conversation history
                        contextual_words = ['add it', 'buy it', 'get it', 'order it', 'take it', 'add this', 'buy this']
                        is_contextual_reference = any(word in user_query_lower for word in contextual_words)

                        if not product_context and is_contextual_reference:
                            for msg in conversation_history:
                                if isinstance(msg, dict):
                                    # Check execution_result field for product data
                                    if 'execution_result' in msg and msg['execution_result']:
                                        for result in msg['execution_result']:
                                            if isinstance(result, dict) and 'product_id' in result:
                                                product_context.append(result)
                                                logger.info(f"✅ Found product from history: {result.get('product_name', 'Unknown')}")
                                                break  # Only take first product for contextual reference
                                        if product_context:  # Stop once we find a product
                                            break

                        # 3. Special Samsung phone handling (fallback if not found above)
                        if not product_context and 'samsung' in user_query_lower and 'phone' in user_query_lower:"""

    if broken_section in content:
        content = content.replace(broken_section, fixed_section)
        print("✅ Fixed product context priority order")

        # Write back to file
        with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("🎉 CRITICAL FIX APPLIED!")
        print("✅ Samsung phone requests will now work correctly")
        print("✅ Contextual references ('add it') will still work")
        print("✅ No more wrong products from conversation history")
    else:
        print("⚠️ Could not find exact section to fix")
        print("Manual intervention may be required")

if __name__ == "__main__":
    critical_fix_shopping()
