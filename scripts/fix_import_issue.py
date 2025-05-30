#!/usr/bin/env python3
"""
🛠️ Fix Import Issue
================================================================================

Fix the order AI assistant import in enhanced_db_querying.py
"""

def fix_import():
    """Fix the import statement"""
    print("🛠️ Fixing import statement...")

    with open('src/enhanced_db_querying.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the import statement
    old_import = '''try:
                from .order_ai_assistant import order_ai_assistant
                order_ai_available = True
            except ImportError:
                order_ai_available = False'''

    new_import = '''try:
                from order_ai_assistant import order_ai_assistant
                order_ai_available = True
            except ImportError:
                try:
                    from .order_ai_assistant import order_ai_assistant
                    order_ai_available = True
                except ImportError:
                    order_ai_available = False'''

    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✅ Fixed import statement")
    else:
        print("⚠️ Could not find import pattern")

    with open('src/enhanced_db_querying.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🎉 Import fixed!")

if __name__ == "__main__":
    print("🛠️ FIXING IMPORT ISSUE")
    print("=" * 60)
    fix_import()
    print("\n✅ Now the order AI assistant should import correctly!")
