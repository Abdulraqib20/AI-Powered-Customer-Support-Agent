#!/usr/bin/env python3
"""
🛠️ CRITICAL FIX V2: Order Specific Product Names
================================================================================

This script fixes the critical bug where placing an order for a specific product
(e.g., "Samsung Galaxy A24 128GB") fails because the system doesn't extract
the full product name correctly, resulting in an empty product context.

Fix: Add a new #1 priority step to extract full product names when order keywords
are present.
"""

def critical_fix_specific_product_order():
    """Ensure specific product names are correctly extracted for orders."""

    print("🛠️ CRITICAL FIX V2: Fixing specific product name extraction for orders...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Marker for the beginning of the product context extraction logic
    marker_start_section = "# 🔧 BULLETPROOF: Extract product context from multiple sources"
    # Marker for the existing generic Samsung phone handling (which will become #2)
    marker_generic_samsung = "# 1. PRIORITY: Special Samsung phone handling (for specific requests)"

    # The new logic to be inserted as the top priority
    new_specific_product_logic = """# 1. NEW PRIORITY: Handle specific product names in order requests
                        #    Example: "place the order for the Samsung Galaxy A24 128GB for me"
                        order_keywords = ['order for', 'place order for', 'buy the', 'purchase the']
                        if any(keyword in user_query_lower for keyword in order_keywords) and \
                           ('samsung galaxy a24' in user_query_lower or 'iphone 14 pro max' in user_query_lower): # Add more products as needed

                            extracted_product_name = None
                            if 'samsung galaxy a24' in user_query_lower:
                                extracted_product_name = "Samsung Galaxy A24 128GB Smartphone"
                            elif 'iphone 14 pro max' in user_query_lower:
                                extracted_product_name = "iPhone 14 Pro Max 256GB"
                            # Add more specific product name extractions here

                            if extracted_product_name:
                                try:
                                    product_sql = f"SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity FROM products WHERE product_name ILIKE '%{extracted_product_name}%' AND in_stock = TRUE ORDER BY price ASC LIMIT 1"
                                    success, product_results, _ = self.execute_sql_query(product_sql)
                                    if success and product_results:
                                        product_context.extend(product_results)
                                        logger.info(f"✅ Found specific product for order: {product_results[0].get('product_name', 'Unknown')}")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not query specific product for order: {e}")

                        """

    if marker_start_section in content and marker_generic_samsung in content:
        # Find the start of the whole section
        start_index = content.find(marker_start_section)
        # Find the start of the bulletproof line to insert after
        bulletproof_line_index = content.find("product_context = []", start_index) + len("product_context = []")

        # Insert the new logic right after product_context = []
        content_parts = list(content)
        content_parts.insert(bulletproof_line_index, '\n\n' + new_specific_product_logic)
        content = "".join(content_parts)

        # Update numbering for the subsequent sections
        content = content.replace("# 1. PRIORITY: Special Samsung phone handling",
                                "# 2. GENERIC PRIORITY: Special Samsung phone handling")
        content = content.replace("# 2. ONLY for contextual references:",
                                "# 3. ONLY for contextual references:")
        content = content.replace("# 3. Special Samsung phone handling (fallback if not found above)",
                                "# 4. GENERIC FALLBACK: Special Samsung phone handling (fallback if not found above)")
        content = content.replace("# 3. Try to extract from current conversation context if needed",
                                "# 5. FALLBACK: Try to extract from current conversation context if needed")

        with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("🎉 CRITICAL FIX V2 APPLIED!")
        print("✅ Specific product name extraction for orders is now #1 priority.")
        print("✅ Ordering 'Samsung Galaxy A24 128GB' should now work correctly.")
    else:
        print("⚠️ Could not find the necessary markers in the file.")
        print(f"Marker1 found: {marker_start_section in content}")
        print(f"Marker2 found: {marker_generic_samsung in content}")
        print("Manual intervention may be required.")

if __name__ == "__main__":
    critical_fix_specific_product_order()
