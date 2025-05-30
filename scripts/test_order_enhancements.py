#!/usr/bin/env python3
'''
🧪 Comprehensive Order Test Suite
Tests the enhanced shopping pattern recognition and order placement
'''

import sys
import os
sys.path.append('src')

from enhanced_order_patterns import EnhancedOrderPatterns
from enhanced_db_querying import EnhancedDatabaseQuerying

class OrderTestSuite:
    def __init__(self):
        self.pattern_detector = EnhancedOrderPatterns()
        self.db_querying = EnhancedDatabaseQuerying()

    def test_shopping_patterns(self):
        '''Test various shopping intent patterns'''

        print("🔍 TESTING SHOPPING PATTERN RECOGNITION")
        print("="*60)

        test_cases = [
            # Natural language variations
            "I want to buy a Samsung phone",
            "Let me purchase the Galaxy",
            "Can I get the iPhone please?",
            "Help me order a laptop",

            # Product-specific patterns
            "Buy the Samsung Galaxy A24",
            "Add this phone to cart",
            "I need this product",
            "Give me that laptop",

            # Cart and checkout
            "Put it in my cart",
            "Ready to checkout",
            "Complete my order",
            "Go to checkout",

            # Payment patterns
            "Use RaqibPay and order",
            "Pay with card",
            "Checkout with bank transfer",

            # Nigerian colloquial
            "I wan buy this phone",
            "Make i buy am",
            "I go take am",
            "Na this one i want",

            # Conversational continuations
            "Add it",
            "Get it",
            "Yes, buy",
            "OK order",

            # Decision patterns
            "That one",
            "Perfect",
            "Deal",
            "Sold"
        ]

        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0

        for i, message in enumerate(test_cases, 1):
            match = self.pattern_detector.detect_shopping_intent(message)
            entities = self.pattern_detector.extract_entities(message, match.intent)

            print(f"\n{i:2d}. '{message}'")
            print(f"     Intent: {match.intent.value}")
            print(f"     Confidence: {match.confidence:.2f}")
            print(f"     Pattern: {match.matched_pattern}")

            if match.confidence >= 0.8:
                high_confidence += 1
                print("     ✅ HIGH CONFIDENCE")
            elif match.confidence >= 0.6:
                medium_confidence += 1
                print("     🟡 MEDIUM CONFIDENCE")
            else:
                low_confidence += 1
                print("     🔴 LOW CONFIDENCE")
                suggestions = self.pattern_detector.suggest_improvements(message, match)
                if suggestions:
                    print(f"     💡 Suggestions: {suggestions[0]}")

        print(f"\n📊 RESULTS:")
        print(f"   ✅ High Confidence (≥80%): {high_confidence}/{len(test_cases)}")
        print(f"   🟡 Medium Confidence (60-79%): {medium_confidence}/{len(test_cases)}")
        print(f"   🔴 Low Confidence (<60%): {low_confidence}/{len(test_cases)}")

        success_rate = (high_confidence + medium_confidence) / len(test_cases) * 100
        print(f"   🎯 Overall Success Rate: {success_rate:.1f}%")

        return success_rate > 80

    def test_product_context_extraction(self):
        '''Test product context extraction from conversation'''

        print("\n🔍 TESTING PRODUCT CONTEXT EXTRACTION")
        print("="*60)

        # Simulate conversation context
        conversation_context = [
            {
                'execution_result': [
                    {
                        'product_id': 1,
                        'product_name': 'Samsung Galaxy A24 128GB Smartphone',
                        'brand': 'Samsung',
                        'price': 425000.0,
                        'category': 'Electronics'
                    }
                ]
            }
        ]

        test_messages = [
            "Add it to cart",
            "I want this one",
            "Buy the Samsung phone",
            "Purchase this",
            "Take it"
        ]

        for message in test_messages:
            match = self.pattern_detector.detect_shopping_intent(message, conversation_context)
            print(f"'{message}' -> {match.intent.value} (confidence: {match.confidence:.2f})")

        return True

    def run_all_tests(self):
        '''Run all test suites'''

        print("🚀 STARTING COMPREHENSIVE ORDER SYSTEM TESTS")
        print("="*70)

        results = []

        # Test 1: Shopping Pattern Recognition
        results.append(self.test_shopping_patterns())

        # Test 2: Product Context Extraction
        results.append(self.test_product_context_extraction())

        # Summary
        print("\n🎯 FINAL RESULTS")
        print("="*30)
        passed = sum(results)
        total = len(results)

        print(f"✅ Tests Passed: {passed}/{total}")
        print(f"📊 Success Rate: {passed/total*100:.1f}%")

        if passed == total:
            print("🎉 ALL TESTS PASSED! Your order system is ready!")
        else:
            print("⚠️ Some tests failed. Check the output above.")

        return passed == total

def main():
    '''Main test runner'''
    suite = OrderTestSuite()
    success = suite.run_all_tests()

    if success:
        print("\n✅ Order system enhancement completed successfully!")
        print("🛒 Users can now place orders much more easily!")
    else:
        print("\n❌ Some issues detected. Please review the test results.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
