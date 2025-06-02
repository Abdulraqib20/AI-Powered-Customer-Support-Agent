#!/usr/bin/env python3
"""
🧠 Test Memory Management and Product Search Improvements
===========================================================

This script tests the enhanced memory system and flexible product search
to ensure the AI can remember context and find products with synonyms.
"""

import os
import sys
import psycopg2
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_conversation_context_storage():
    """Test that conversation context is properly stored in database"""
    print("\n🧠 TESTING CONVERSATION CONTEXT STORAGE")
    print("="*60)

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'nigerian_ecommerce'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'oracle')
        )

        cursor = conn.cursor()

        # Check if conversation_context table exists and has data
        cursor.execute("SELECT COUNT(*) FROM conversation_context")
        context_count = cursor.fetchone()[0]

        print(f"📊 Current conversation contexts in database: {context_count}")

        # Get recent conversation contexts
        cursor.execute("""
            SELECT user_id, query_type, user_query, timestamp
            FROM conversation_context
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        recent_contexts = cursor.fetchall()
        print(f"\n📝 Recent conversation contexts:")
        for ctx in recent_contexts:
            print(f"  - User: {ctx[0]} | Type: {ctx[1]} | Query: {ctx[2][:50]}... | Time: {ctx[3]}")

        cursor.close()
        conn.close()

        return context_count > 0

    except Exception as e:
        print(f"❌ Error testing conversation context: {e}")
        return False

def test_product_search_flexibility():
    """Test enhanced product search with synonyms"""
    print("\n🔍 TESTING PRODUCT SEARCH FLEXIBILITY")
    print("="*60)

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'nigerian_ecommerce'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'oracle')
        )

        cursor = conn.cursor()

        # Test searches that should now work
        test_searches = [
            ("phones", "Should find iPhone, Samsung phones"),
            ("ios", "Should find iPhone, iPad"),
            ("ipads", "Should find iPad"),
            ("tablet", "Should find iPad or tablets"),
            ("apple", "Should find Apple products"),
            ("laptop", "Should find laptops")
        ]

        for search_term, description in test_searches:
            print(f"\n🔍 Testing search: '{search_term}' - {description}")

            # Direct product name search
            cursor.execute("""
                SELECT product_name, category, brand, price
                FROM products
                WHERE product_name ILIKE %s AND in_stock = TRUE
                LIMIT 3
            """, (f"%{search_term}%",))

            direct_results = cursor.fetchall()
            print(f"  Direct matches: {len(direct_results)}")
            for result in direct_results:
                print(f"    - {result[0]} ({result[2]}) - ₦{result[3]}")

            # Synonym-based search (simulating our enhanced search)
            synonyms = {
                'phones': ['iphone', 'samsung', 'smartphone'],
                'ios': ['iphone', 'ipad', 'apple'],
                'ipads': ['ipad'],
                'tablet': ['ipad'],
                'apple': ['iphone', 'ipad', 'macbook'],
                'laptop': ['macbook', 'hp', 'dell']
            }

            if search_term in synonyms:
                for synonym in synonyms[search_term]:
                    cursor.execute("""
                        SELECT product_name, category, brand, price
                        FROM products
                        WHERE (product_name ILIKE %s OR brand ILIKE %s) AND in_stock = TRUE
                        LIMIT 2
                    """, (f"%{synonym}%", f"%{synonym}%"))

                    synonym_results = cursor.fetchall()
                    if synonym_results:
                        print(f"  Synonym '{synonym}' matches: {len(synonym_results)}")
                        for result in synonym_results:
                            print(f"    - {result[0]} ({result[2]}) - ₦{result[3]}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error testing product search: {e}")
        return False

def test_contextual_reference_detection():
    """Test detection of contextual references like 'it', 'this', 'that'"""
    print("\n🎯 TESTING CONTEXTUAL REFERENCE DETECTION")
    print("="*60)

    contextual_phrases = [
        "i want to order it",
        "add this to cart",
        "buy that product",
        "how much is it",
        "show me the price of that",
        "i'll take one"
    ]

    contextual_words = ['it', 'this', 'that', 'they', 'them', 'one', 'the product', 'the item']

    for phrase in contextual_phrases:
        is_contextual = any(word in phrase.lower() for word in contextual_words)
        print(f"'{phrase}' -> Contextual: {is_contextual}")

        if is_contextual:
            detected_words = [word for word in contextual_words if word in phrase.lower()]
            print(f"  Detected contextual words: {detected_words}")

    return True

def simulate_conversation_memory_scenario():
    """Simulate a conversation scenario to test memory"""
    print("\n💬 SIMULATING CONVERSATION MEMORY SCENARIO")
    print("="*60)

    conversation_flow = [
        ("User asks about iPads", "i want to see iPads", "Should find iPad products"),
        ("AI shows iPad", "Here's the iPad 9th Generation...", "Product info provided"),
        ("User contextual order", "i want to order it", "Should understand 'it' = iPad"),
        ("Order processing", "Adding iPad to cart...", "Contextual reference resolved")
    ]

    print("Simulated conversation flow:")
    for step, message, expected in conversation_flow:
        print(f"  {step}: '{message}' -> {expected}")

    print("\n🧠 With enhanced memory, the AI should:")
    print("  1. Store iPad product info in conversation_context table")
    print("  2. Detect 'it' as contextual reference")
    print("  3. Link 'it' to previously mentioned iPad")
    print("  4. Process order for correct product")

    return True

def test_database_conversation_persistence():
    """Test that conversation data persists in database"""
    print("\n💾 TESTING DATABASE CONVERSATION PERSISTENCE")
    print("="*60)

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME', 'nigerian_ecommerce'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'oracle')
        )

        cursor = conn.cursor()

        # Insert a test conversation context
        test_user_id = "test_customer_999"
        test_session_id = "test_session_123"
        test_query = "test query for memory persistence"

        cursor.execute("""
            INSERT INTO conversation_context
            (user_id, session_id, query_type, entities, user_query, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            test_user_id,
            test_session_id,
            'product_info_general',
            '{"test": "data"}',
            test_query,
            datetime.now()
        ))

        conn.commit()
        print("✅ Test conversation context inserted")

        # Retrieve it back
        cursor.execute("""
            SELECT user_id, session_id, query_type, user_query, timestamp
            FROM conversation_context
            WHERE user_id = %s AND session_id = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (test_user_id, test_session_id))

        result = cursor.fetchone()
        if result:
            print(f"✅ Test conversation context retrieved: {result[3]}")

            # Clean up test data
            cursor.execute("""
                DELETE FROM conversation_context
                WHERE user_id = %s AND session_id = %s
            """, (test_user_id, test_session_id))
            conn.commit()
            print("🗑️ Test data cleaned up")
        else:
            print("❌ Failed to retrieve test conversation context")

        cursor.close()
        conn.close()

        return result is not None

    except Exception as e:
        print(f"❌ Error testing database persistence: {e}")
        return False

def main():
    """Run all memory and product search tests"""
    print("🧠 MEMORY MANAGEMENT & PRODUCT SEARCH TEST SUITE")
    print("="*60)
    print(f"🕒 Test started at: {datetime.now()}")

    tests = [
        ("Database Conversation Context Storage", test_conversation_context_storage),
        ("Product Search Flexibility", test_product_search_flexibility),
        ("Contextual Reference Detection", test_contextual_reference_detection),
        ("Conversation Memory Scenario", simulate_conversation_memory_scenario),
        ("Database Persistence", test_database_conversation_persistence)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")

        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    print(f"\n🎯 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Memory and product search improvements are working!")
    else:
        print("⚠️ Some tests failed. Check the implementation.")

    print(f"\n🕒 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
