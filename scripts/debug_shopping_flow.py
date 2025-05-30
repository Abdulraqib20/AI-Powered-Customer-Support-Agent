#!/usr/bin/env python3
"""
🛠️ Debug Shopping Flow
================================================================================

Add debug logging to see exactly where the shopping detection is failing.
"""

def add_debug_logging():
    """Add debug logging to shopping detection"""
    print("🛠️ Adding debug logging to shopping detection...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Add debug logging after the shopping keywords check
    old_pattern = '''user_query_lower = user_query.lower()
                    if any(keyword in user_query_lower for keyword in shopping_keywords):'''

    new_pattern = '''user_query_lower = user_query.lower()
                    matched_keywords = [keyword for keyword in shopping_keywords if keyword in user_query_lower]
                    logger.info(f"🔍 Shopping keyword check: query='{user_query[:50]}...', matched={matched_keywords}")

                    if any(keyword in user_query_lower for keyword in shopping_keywords):
                        logger.info(f"🎯 SHOPPING ACTION TRIGGERED! Keywords matched: {matched_keywords}")'''

    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("✅ Added shopping detection debug logging")
    else:
        print("⚠️ Could not find shopping detection pattern")

    # Also add debug logging for the import check
    old_import_pattern = '''if order_ai_available and session_context and session_context.get('user_authenticated'):'''

    new_import_pattern = '''logger.info(f"🔍 Shopping check: order_ai_available={order_ai_available}, session_context={bool(session_context)}, user_authenticated={session_context.get('user_authenticated') if session_context else False}")

            if order_ai_available and session_context and session_context.get('user_authenticated'):
                logger.info("✅ All shopping prerequisites met - checking keywords...")'''

    if old_import_pattern in content:
        content = content.replace(old_import_pattern, new_import_pattern)
        print("✅ Added import/session debug logging")
    else:
        print("⚠️ Could not find import pattern")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🎉 Debug logging added!")

if __name__ == "__main__":
    print("🛠️ ADDING DEBUG LOGGING TO SHOPPING FLOW")
    print("=" * 60)
    add_debug_logging()
    print("\n✅ Now run the test again to see detailed shopping detection logs!")
