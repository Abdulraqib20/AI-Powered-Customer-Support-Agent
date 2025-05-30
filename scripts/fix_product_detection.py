#!/usr/bin/env python3
"""
🛠️ Fix Product Detection
================================================================================

Fix the product detection logic to properly detect Samsung Galaxy A24.
"""

def fix_product_detection():
    """Fix product detection for Samsung Galaxy A24"""
    print("🛠️ Fixing product detection logic...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the Samsung phone detection logic
    old_detection = '''# 2. GENERIC PRIORITY: Special Samsung phone handling (for specific requests)
                        if 'samsung' in user_query_lower and 'phone' in user_query_lower:'''

    new_detection = '''# 2. ENHANCED SAMSUNG DETECTION: Handle Samsung Galaxy A24 and other Samsung products
                        if ('samsung' in user_query_lower and ('phone' in user_query_lower or 'galaxy' in user_query_lower or 'a24' in user_query_lower)):'''

    if old_detection in content:
        content = content.replace(old_detection, new_detection)
        print("✅ Enhanced Samsung detection logic")
    else:
        print("⚠️ Could not find Samsung detection pattern")

    # Also fix the fallback Samsung detection
    old_fallback = '''# 4. GENERIC FALLBACK: Special Samsung phone handling (fallback if not found above)
                        if not product_context and 'samsung' in user_query_lower and 'phone' in user_query_lower:'''

    new_fallback = '''# 4. ENHANCED FALLBACK: Samsung product handling (fallback if not found above)
                        if not product_context and ('samsung' in user_query_lower and ('phone' in user_query_lower or 'galaxy' in user_query_lower or 'a24' in user_query_lower)):'''

    if old_fallback in content:
        content = content.replace(old_fallback, new_fallback)
        print("✅ Enhanced Samsung fallback detection")
    else:
        print("⚠️ Could not find Samsung fallback pattern")

    # Also add specific Samsung Galaxy A24 detection
    specific_detection = '''# 1.5. SPECIFIC SAMSUNG GALAXY A24 DETECTION
                        if 'samsung galaxy a24' in user_query_lower or ('samsung' in user_query_lower and 'galaxy' in user_query_lower and 'a24' in user_query_lower):
                            try:
                                samsung_a24_sql = """
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity
                                FROM products WHERE product_name ILIKE '%Samsung Galaxy A24%' AND in_stock = TRUE
                                ORDER BY price ASC LIMIT 1
                                """
                                success, samsung_a24_results, _ = self.execute_sql_query(samsung_a24_sql)
                                if success and samsung_a24_results:
                                    product_context.extend(samsung_a24_results)
                                    logger.info(f"✅ Found Samsung Galaxy A24 by specific query: {samsung_a24_results[0].get('product_name', 'Unknown')}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not query Samsung Galaxy A24: {e}")

                        '''

    # Insert this after the product_context = [] line
    insertion_point = "product_context = []"
    if insertion_point in content:
        content = content.replace(insertion_point, insertion_point + "\n\n" + specific_detection)
        print("✅ Added specific Samsung Galaxy A24 detection")
    else:
        print("⚠️ Could not find insertion point for specific detection")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🎉 Product detection fixed!")

if __name__ == "__main__":
    print("🛠️ FIXING PRODUCT DETECTION")
    print("=" * 60)
    fix_product_detection()
    print("\n✅ Now Samsung Galaxy A24 should be detected properly!")
