#!/usr/bin/env python3
"""
🧪 Test Products Integration with Enhanced AI System
Test script to verify the AI system works with the new products table
"""

import sys
import os
import json
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent.resolve()))
sys.path.append(str(Path(__file__).parent / "src"))

from src.enhanced_db_querying import EnhancedDatabaseQuerying

def test_product_queries():
    """Test various product-related queries"""

    print("🧪 Testing Enhanced AI System with Products Table")
    print("=" * 60)

    # Initialize the enhanced querying system
    enhanced_db = EnhancedDatabaseQuerying()

    # Test queries
    test_queries = [
        # Product catalog queries
        "Show me electronics products",
        "What Samsung phones do you have?",
        "Browse fashion items",
        "Check prices for laptops",

        # Inventory queries
        "What products are in stock?",
        "Show me low stock items",
        "Check availability of iPhone",

        # Category browsing
        "Show me beauty products",
        "What books are available?",
        "Browse automotive accessories",

        # Brand searches
        "Search for Nike products",
        "Show me Apple devices",
        "Find Tecno smartphones",

        # Price-related queries
        "What are your cheapest products?",
        "Show products under ₦100,000",
        "Most expensive items in catalog"
    ]

    print("\n🎯 Testing Product Query Classification and Processing...")
    print("-" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        try:
            # Test the complete pipeline
            result = enhanced_db.process_enhanced_query(query)

            print(f"   ✅ Query Type: {result.get('query_type', 'unknown')}")
            print(f"   📊 Results Count: {result.get('results_count', 0)}")
            print(f"   ⏱️ Execution Time: {result.get('execution_time', 'N/A')}")
            print(f"   🤖 AI Response Preview: {result.get('response', 'No response')[:100]}...")

            if result.get('entities'):
                entities = result['entities']
                extracted_info = []
                if entities.get('product_categories'):
                    extracted_info.append(f"Categories: {entities['product_categories']}")
                if entities.get('brands'):
                    extracted_info.append(f"Brands: {entities['brands']}")
                if entities.get('price_query'):
                    extracted_info.append("Price Query: Yes")
                if entities.get('inventory_query'):
                    extracted_info.append("Inventory Query: Yes")

                if extracted_info:
                    print(f"   🎯 Extracted: {', '.join(extracted_info)}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    print("\n🎉 Product Integration Test Complete!")
    print("=" * 60)

    # Test scope checking
    print("\n🎯 Testing Scope Recognition...")
    scope_tests = [
        ("Show me iPhone prices", True),  # Should be in scope
        ("What is the capital of Nigeria?", False),  # Should be out of scope
        ("Browse electronics catalog", True),  # Should be in scope
        ("Tell me about politics", False),  # Should be out of scope
        ("Check Samsung phone stock", True),  # Should be in scope
    ]

    for query, should_be_in_scope in scope_tests:
        is_in_scope = enhanced_db.is_query_within_scope(query)
        status = "✅" if is_in_scope == should_be_in_scope else "❌"
        print(f"{status} '{query}' -> {'In Scope' if is_in_scope else 'Out of Scope'}")

    print("\n🎯 Testing Fallback Queries...")
    # Test fallback queries for product performance
    from src.enhanced_db_querying import QueryType

    test_entities = [
        {'product_categories': ['Electronics']},
        {'brands': ['Samsung']},
        {'price_query': True},
        {'inventory_query': True},
        {}  # General product query
    ]

    for entities in test_entities:
        try:
            fallback_sql = enhanced_db._get_fallback_query(QueryType.PRODUCT_PERFORMANCE, entities)
            print(f"✅ Fallback SQL generated for entities: {entities}")
            print(f"   SQL Preview: {fallback_sql[:100]}...")
        except Exception as e:
            print(f"❌ Fallback error for {entities}: {e}")

    print("\n🌟 All Tests Completed!")

if __name__ == "__main__":
    test_product_queries()
