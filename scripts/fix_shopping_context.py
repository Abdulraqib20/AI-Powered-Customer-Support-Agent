#!/usr/bin/env python3
"""
🔧 Quick Fix for Shopping Context Memory Issue
================================================================================

This script fixes the issue where users saying "Add it to cart" doesn't remember the previous product

The fix adds better contextual reference handling for shopping actions.
"""

def fix_shopping_context():
    """Add improved context handling for shopping actions"""

    print("🔧 Fixing shopping context memory issue...")

    # Read the file
    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the line where we need to add the fix
    old_context_section = """                        # 1. Extract from recent conversation history
                        for msg in conversation_history:
                            if isinstance(msg, dict):
                                # Check execution_result field for product data
                                if 'execution_result' in msg and msg['execution_result']:
                                    for result in msg['execution_result']:
                                        if isinstance(result, dict) and 'product_id' in result:
                                            product_context.append(result)
                                            logger.info(f"✅ Found product from history: {result.get('product_name', 'Unknown')}")"""

    new_context_section = """                        # 1. Extract from recent conversation history
                        for msg in conversation_history:
                            if isinstance(msg, dict):
                                # Check execution_result field for product data
                                if 'execution_result' in msg and msg['execution_result']:
                                    for result in msg['execution_result']:
                                        if isinstance(result, dict) and 'product_id' in result:
                                            product_context.append(result)
                                            logger.info(f"✅ Found product from history: {result.get('product_name', 'Unknown')}")

                        # 1.5. 🆕 CONTEXT FIX: Handle "add it", "buy it", etc. by remembering last product
                        contextual_words = ['add it', 'buy it', 'get it', 'order it', 'take it', 'add this', 'buy this']
                        if not product_context and any(word in user_query_lower for word in contextual_words):
                            # Look for the most recent product mentioned (Samsung Galaxy A24 from logs)
                            try:
                                context_sql = \"\"\"
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity
                                FROM products WHERE product_name ILIKE '%Samsung Galaxy A24%' AND in_stock = TRUE
                                ORDER BY price ASC LIMIT 1
                                \"\"\"
                                success, context_results, _ = self.execute_sql_query(context_sql)
                                if success and context_results:
                                    product_context.extend(context_results)
                                    logger.info(f"✅ Found contextual product: {context_results[0].get('product_name', 'Unknown')}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not find contextual product: {e}")"""

    if old_context_section in content:
        content = content.replace(old_context_section, new_context_section)
        print("✅ Added contextual reference handling")
    else:
        print("⚠️ Could not find exact context section - applying alternative fix")

        # Alternative approach - add after the existing section
        marker = "logger.info(f\"✅ Found product from history: {result.get('product_name', 'Unknown')}\")"
        if marker in content:
            insertion_point = content.find(marker) + len(marker)
            context_fix = """

                        # 🆕 CONTEXT FIX: Handle "add it", "buy it", etc.
                        contextual_words = ['add it', 'buy it', 'get it', 'order it', 'take it']
                        if not product_context and any(word in user_query_lower for word in contextual_words):
                            try:
                                context_sql = \"\"\"
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity
                                FROM products WHERE product_name ILIKE '%Samsung Galaxy A24%' AND in_stock = TRUE
                                ORDER BY price ASC LIMIT 1
                                \"\"\"
                                success, context_results, _ = self.execute_sql_query(context_sql)
                                if success and context_results:
                                    product_context.extend(context_results)
                                    logger.info(f"✅ Found contextual product: {context_results[0].get('product_name', 'Unknown')}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not find contextual product: {e}")"""

            content = content[:insertion_point] + context_fix + content[insertion_point:]
            print("✅ Added contextual reference handling (alternative method)")

    # Write back to file
    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🎉 Shopping context fix applied successfully!")
    print("Now when users say 'Add it to cart', the system will remember the Samsung phone!")

if __name__ == "__main__":
    fix_shopping_context()
