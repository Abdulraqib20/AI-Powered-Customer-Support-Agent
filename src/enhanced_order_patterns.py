#!/usr/bin/env python3
"""
🛒 Enhanced Order Pattern Recognition System
================================================================================

Advanced shopping intent detection and command patterns for easier order placement.
This system significantly improves the AI's ability to detect when users want to:
- Browse products
- Add items to cart
- Place orders
- Check order status
- Make payments

The system uses multiple detection layers:
1. Exact phrase matching
2. Pattern-based recognition
3. Context-aware interpretation
4. Intent confidence scoring
5. Fallback pattern detection

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ShoppingIntent(Enum):
    """Shopping intent types with confidence levels"""
    BROWSE_PRODUCTS = "browse_products"
    ADD_TO_CART = "add_to_cart"
    VIEW_CART = "view_cart"
    PLACE_ORDER = "place_order"
    CHECK_PAYMENT = "check_payment"
    TRACK_ORDER = "track_order"
    PRICE_INQUIRY = "price_inquiry"
    STOCK_CHECK = "stock_check"
    PRODUCT_COMPARE = "product_compare"
    REMOVE_FROM_CART = "remove_from_cart"
    CLEAR_CART = "clear_cart"
    DELIVERY_INFO = "delivery_info"
    PAYMENT_METHODS = "payment_methods"
    ORDER_HISTORY = "order_history"
    CANCEL_ORDER = "cancel_order"
    MODIFY_ORDER = "modify_order"
    GENERAL_SHOPPING = "general_shopping"

@dataclass
class PatternMatch:
    """Pattern matching result"""
    intent: ShoppingIntent
    confidence: float
    matched_pattern: str
    extracted_entities: Dict[str, Any]
    trigger_words: List[str]

class EnhancedOrderPatterns:
    """Enhanced order pattern recognition with comprehensive shopping intent detection"""

    def __init__(self):
        # Initialize pattern dictionaries
        self.exact_patterns = self._build_exact_patterns()
        self.regex_patterns = self._build_regex_patterns()
        self.context_patterns = self._build_context_patterns()
        self.product_keywords = self._build_product_keywords()
        self.action_verbs = self._build_action_verbs()

    def _build_exact_patterns(self) -> Dict[ShoppingIntent, List[str]]:
        """Build exact phrase patterns for shopping intents"""
        return {
            ShoppingIntent.BROWSE_PRODUCTS: [
                "show me products", "browse catalog", "what do you have", "see products",
                "product list", "available items", "what can i buy", "show catalog",
                "browse items", "view products", "see all products", "product catalog",
                "what products", "show me what you have", "product categories",
                "browse your store", "what's available", "product selection"
            ],

            ShoppingIntent.ADD_TO_CART: [
                "add to cart", "add it to cart", "put in cart", "cart it",
                "add this", "add the", "i want this", "i'll take this",
                "add product", "put this in my cart", "cart this",
                "add item", "put in my cart", "i want to buy this",
                "add samsung", "buy samsung", "get samsung", "purchase samsung",
                "add phone", "buy phone", "get phone", "purchase phone",
                "add galaxy", "buy galaxy", "get galaxy", "add this product",
                "i want to buy", "let me buy", "i'll buy", "i need this"
            ],

            ShoppingIntent.VIEW_CART: [
                "view cart", "show cart", "my cart", "cart contents",
                "what's in my cart", "cart status", "show my cart",
                "cart items", "check cart", "see cart", "cart summary",
                "what did i add", "my items", "shopping cart"
            ],

            ShoppingIntent.PLACE_ORDER: [
                "place order", "checkout", "proceed to checkout", "buy now",
                "complete order", "finalize order", "confirm order", "submit order",
                "complete purchase", "finish order", "order now", "make order",
                "go to checkout", "ready to order", "complete my order",
                "finish checkout", "process order", "confirm purchase",
                "i want to order", "let me order", "order this", "purchase now"
            ],

            ShoppingIntent.CHECK_PAYMENT: [
                "payment method", "pay with", "use raqibpay", "raqibpay payment",
                "card payment", "bank transfer", "pay on delivery",
                "payment option", "how to pay", "payment methods",
                "use card", "pay by card", "transfer payment", "mobile payment"
            ],

            ShoppingIntent.TRACK_ORDER: [
                "track order", "order status", "where is my order", "order tracking",
                "check order", "order progress", "delivery status", "my order",
                "order update", "track my order", "order location", "shipping status"
            ],

            ShoppingIntent.PRICE_INQUIRY: [
                "how much", "price of", "cost of", "how much does", "what's the price",
                "price for", "cost for", "how much is", "price check",
                "what does it cost", "pricing", "how much cost", "price list"
            ],

            ShoppingIntent.STOCK_CHECK: [
                "in stock", "available", "out of stock", "availability",
                "is available", "do you have", "stock status", "in store",
                "can i get", "is it available", "have in stock"
            ]
        }

    def _build_regex_patterns(self) -> Dict[ShoppingIntent, List[str]]:
        """Build regex patterns for flexible matching"""
        return {
            ShoppingIntent.ADD_TO_CART: [
                r"add\s+(the\s+)?(samsung|phone|galaxy|laptop|product)\s+to\s+cart",
                r"buy\s+(the\s+)?(samsung|phone|galaxy|laptop|product)",
                r"purchase\s+(the\s+)?(samsung|phone|galaxy|laptop|product)",
                r"get\s+(the\s+)?(samsung|phone|galaxy|laptop|product)",
                r"i\s+want\s+(the\s+)?(samsung|phone|galaxy|laptop|product)",
                r"add\s+\w+\s+(phone|laptop|product)\s+to\s+cart",
                r"cart\s+(the\s+)?(samsung|phone|galaxy|laptop|product)"
            ],

            ShoppingIntent.PLACE_ORDER: [
                r"use\s+raqibpay\s+and\s+(place|make|complete)\s+order",
                r"pay\s+with\s+\w+\s+and\s+(order|checkout)",
                r"(place|make|complete)\s+order\s+with\s+\w+\s+payment",
                r"checkout\s+with\s+\w+",
                r"order\s+with\s+\w+\s+pay"
            ],

            ShoppingIntent.TRACK_ORDER: [
                r"track\s+order\s+#?(\w+)",
                r"where\s+is\s+order\s+#?(\w+)",
                r"check\s+order\s+#?(\w+)",
                r"status\s+of\s+order\s+#?(\w+)"
            ],

            ShoppingIntent.PRICE_INQUIRY: [
                r"how\s+much\s+(is|does|for)\s+(the\s+)?\w+",
                r"price\s+(of|for)\s+(the\s+)?\w+",
                r"cost\s+(of|for)\s+(the\s+)?\w+",
                r"what\s+(is\s+)?the\s+price\s+(of|for)\s+\w+"
            ]
        }

    def _build_context_patterns(self) -> Dict[str, ShoppingIntent]:
        """Build context-aware patterns"""
        return {
            "product_mention_with_action": ShoppingIntent.ADD_TO_CART,
            "price_with_product": ShoppingIntent.PRICE_INQUIRY,
            "payment_with_action": ShoppingIntent.PLACE_ORDER,
            "order_id_mention": ShoppingIntent.TRACK_ORDER,
            "cart_mention": ShoppingIntent.VIEW_CART,
            "stock_with_product": ShoppingIntent.STOCK_CHECK
        }

    def _build_product_keywords(self) -> List[str]:
        """Build comprehensive product keyword list"""
        return [
            # Electronics
            "samsung", "galaxy", "phone", "smartphone", "iphone", "apple",
            "laptop", "computer", "macbook", "dell", "hp", "lenovo",
            "tablet", "ipad", "tv", "television", "headphones", "earphones",
            "speaker", "camera", "watch", "smartwatch",

            # Fashion
            "dress", "shirt", "trouser", "shoes", "bag", "handbag",
            "jacket", "coat", "jeans", "shorts", "skirt", "blouse",

            # Beauty
            "cream", "lotion", "perfume", "makeup", "lipstick", "foundation",
            "soap", "shampoo", "conditioner", "oil", "powder",

            # Books
            "book", "novel", "textbook", "magazine", "journal", "bible",

            # Automotive
            "battery", "tire", "tyre", "oil", "filter", "spare part"
        ]

    def _build_action_verbs(self) -> Dict[str, ShoppingIntent]:
        """Build action verbs mapping to intents"""
        return {
            # Purchase actions
            "buy": ShoppingIntent.ADD_TO_CART,
            "purchase": ShoppingIntent.ADD_TO_CART,
            "get": ShoppingIntent.ADD_TO_CART,
            "order": ShoppingIntent.PLACE_ORDER,
            "add": ShoppingIntent.ADD_TO_CART,
            "cart": ShoppingIntent.ADD_TO_CART,

            # Information actions
            "show": ShoppingIntent.BROWSE_PRODUCTS,
            "see": ShoppingIntent.BROWSE_PRODUCTS,
            "view": ShoppingIntent.VIEW_CART,
            "check": ShoppingIntent.TRACK_ORDER,
            "track": ShoppingIntent.TRACK_ORDER,

            # Order management
            "place": ShoppingIntent.PLACE_ORDER,
            "complete": ShoppingIntent.PLACE_ORDER,
            "checkout": ShoppingIntent.PLACE_ORDER,
            "confirm": ShoppingIntent.PLACE_ORDER,

            # Payment actions
            "pay": ShoppingIntent.CHECK_PAYMENT,
            "payment": ShoppingIntent.CHECK_PAYMENT
        }

    def detect_shopping_intent(self, user_message: str, conversation_context: List[Dict] = None) -> PatternMatch:
        """
        Main method to detect shopping intent with multiple detection layers
        Returns the best matching pattern with confidence score
        """
        user_message_lower = user_message.lower().strip()

        # Layer 1: Exact phrase matching (highest confidence)
        exact_match = self._match_exact_patterns(user_message_lower)
        if exact_match.confidence >= 0.9:
            return exact_match

        # Layer 2: Regex pattern matching
        regex_match = self._match_regex_patterns(user_message_lower)
        if regex_match.confidence >= 0.8:
            return regex_match

        # Layer 3: Context-aware detection
        context_match = self._match_context_patterns(user_message_lower, conversation_context)
        if context_match.confidence >= 0.7:
            return context_match

        # Layer 4: Action verb + product keyword detection
        action_match = self._match_action_patterns(user_message_lower)
        if action_match.confidence >= 0.6:
            return action_match

        # Layer 5: Fallback general pattern detection
        fallback_match = self._match_fallback_patterns(user_message_lower)

        # Return the best match
        all_matches = [exact_match, regex_match, context_match, action_match, fallback_match]
        best_match = max(all_matches, key=lambda x: x.confidence)

        return best_match

    def _match_exact_patterns(self, user_message: str) -> PatternMatch:
        """Match exact phrase patterns"""
        for intent, patterns in self.exact_patterns.items():
            for pattern in patterns:
                if pattern in user_message:
                    return PatternMatch(
                        intent=intent,
                        confidence=0.95,
                        matched_pattern=pattern,
                        extracted_entities={"exact_match": pattern},
                        trigger_words=[pattern]
                    )

        return PatternMatch(
            intent=ShoppingIntent.GENERAL_SHOPPING,
            confidence=0.0,
            matched_pattern="",
            extracted_entities={},
            trigger_words=[]
        )

    def _match_regex_patterns(self, user_message: str) -> PatternMatch:
        """Match regex patterns"""
        for intent, patterns in self.regex_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    entities = {"regex_groups": match.groups()} if match.groups() else {}
                    return PatternMatch(
                        intent=intent,
                        confidence=0.85,
                        matched_pattern=pattern,
                        extracted_entities=entities,
                        trigger_words=[match.group(0)]
                    )

        return PatternMatch(
            intent=ShoppingIntent.GENERAL_SHOPPING,
            confidence=0.0,
            matched_pattern="",
            extracted_entities={},
            trigger_words=[]
        )

    def _match_context_patterns(self, user_message: str, conversation_context: List[Dict]) -> PatternMatch:
        """Match context-aware patterns"""
        entities = {}
        confidence = 0.0
        intent = ShoppingIntent.GENERAL_SHOPPING

        # Check for product mentions with actions
        has_product = any(keyword in user_message for keyword in self.product_keywords)
        has_action_verb = any(verb in user_message for verb in self.action_verbs.keys())

        if has_product and has_action_verb:
            # Determine the most likely intent based on action verbs
            for verb, verb_intent in self.action_verbs.items():
                if verb in user_message:
                    intent = verb_intent
                    confidence = 0.75
                    entities = {"product_mentioned": True, "action_verb": verb}
                    break

        # Check for order ID patterns
        order_id_pattern = r"(RQB\w+|\b\d{4,}\b)"
        order_match = re.search(order_id_pattern, user_message)
        if order_match:
            intent = ShoppingIntent.TRACK_ORDER
            confidence = 0.8
            entities = {"order_id": order_match.group(1)}

        # Check for payment method mentions
        payment_methods = ["raqibpay", "card", "transfer", "delivery", "pay on delivery"]
        if any(method in user_message for method in payment_methods):
            if any(action in user_message for action in ["pay", "use", "with", "order", "checkout"]):
                intent = ShoppingIntent.PLACE_ORDER
                confidence = 0.8
                entities = {"payment_method_mentioned": True}

        return PatternMatch(
            intent=intent,
            confidence=confidence,
            matched_pattern="context_aware",
            extracted_entities=entities,
            trigger_words=[]
        )

    def _match_action_patterns(self, user_message: str) -> PatternMatch:
        """Match action verb patterns"""
        for verb, intent in self.action_verbs.items():
            if verb in user_message:
                # Check if there's a product mentioned nearby
                words = user_message.split()
                verb_index = next((i for i, word in enumerate(words) if verb in word), -1)

                if verb_index != -1:
                    # Look for products within 3 words of the action verb
                    nearby_words = words[max(0, verb_index-3):min(len(words), verb_index+4)]
                    has_nearby_product = any(keyword in " ".join(nearby_words) for keyword in self.product_keywords)

                    confidence = 0.7 if has_nearby_product else 0.5

                    return PatternMatch(
                        intent=intent,
                        confidence=confidence,
                        matched_pattern=f"action_verb_{verb}",
                        extracted_entities={"action_verb": verb, "nearby_product": has_nearby_product},
                        trigger_words=[verb]
                    )

        return PatternMatch(
            intent=ShoppingIntent.GENERAL_SHOPPING,
            confidence=0.0,
            matched_pattern="",
            extracted_entities={},
            trigger_words=[]
        )

    def _match_fallback_patterns(self, user_message: str) -> PatternMatch:
        """Fallback pattern matching for edge cases"""
        # Shopping-related keywords
        shopping_keywords = [
            "shop", "shopping", "store", "buy", "purchase", "order", "cart",
            "product", "item", "goods", "catalog", "price", "cost", "payment"
        ]

        shopping_score = sum(1 for keyword in shopping_keywords if keyword in user_message)

        if shopping_score > 0:
            confidence = min(0.4, shopping_score * 0.1)
            return PatternMatch(
                intent=ShoppingIntent.GENERAL_SHOPPING,
                confidence=confidence,
                matched_pattern="fallback_shopping",
                extracted_entities={"shopping_keywords": shopping_score},
                trigger_words=[kw for kw in shopping_keywords if kw in user_message]
            )

        return PatternMatch(
            intent=ShoppingIntent.GENERAL_SHOPPING,
            confidence=0.1,
            matched_pattern="default",
            extracted_entities={},
            trigger_words=[]
        )

    def extract_entities(self, user_message: str, detected_intent: ShoppingIntent) -> Dict[str, Any]:
        """Extract relevant entities based on detected intent"""
        entities = {}
        user_message_lower = user_message.lower()

        # Extract product information
        mentioned_products = [kw for kw in self.product_keywords if kw in user_message_lower]
        if mentioned_products:
            entities["products"] = mentioned_products

        # Extract quantities
        quantity_pattern = r"(\d+)\s*(piece|pieces|unit|units|qty|quantity|x)"
        quantity_match = re.search(quantity_pattern, user_message_lower)
        if quantity_match:
            entities["quantity"] = int(quantity_match.group(1))

        # Extract price/budget information
        price_pattern = r"₦?(\d+(?:,\d+)*(?:k|m)?)"
        price_matches = re.findall(price_pattern, user_message_lower)
        if price_matches:
            entities["prices"] = price_matches

        # Extract order IDs
        order_id_pattern = r"(RQB\w+|\b\d{4,}\b)"
        order_match = re.search(order_id_pattern, user_message)
        if order_match:
            entities["order_id"] = order_match.group(1)

        # Extract payment methods
        payment_methods = {
            "raqibpay": "RaqibTechPay",
            "card": "Card Payment",
            "transfer": "Bank Transfer",
            "delivery": "Pay on Delivery",
            "cash": "Pay on Delivery"
        }

        for keyword, method in payment_methods.items():
            if keyword in user_message_lower:
                entities["payment_method"] = method
                break

        return entities

    def get_confidence_explanation(self, pattern_match: PatternMatch) -> str:
        """Get human-readable explanation of confidence score"""
        confidence = pattern_match.confidence

        if confidence >= 0.9:
            return f"Very High - Exact phrase match: '{pattern_match.matched_pattern}'"
        elif confidence >= 0.8:
            return f"High - Strong pattern match: '{pattern_match.matched_pattern}'"
        elif confidence >= 0.7:
            return f"Good - Context-based detection"
        elif confidence >= 0.6:
            return f"Moderate - Action verb pattern detected"
        elif confidence >= 0.4:
            return f"Low - Fallback pattern recognition"
        else:
            return f"Very Low - Default classification"

    def suggest_improvements(self, user_message: str, pattern_match: PatternMatch) -> List[str]:
        """Suggest improvements for better intent detection"""
        suggestions = []

        if pattern_match.confidence < 0.7:
            suggestions.append("Be more specific about the action you want to take")
            suggestions.append("Mention the exact product name or brand")
            suggestions.append("Use clear action words like 'add to cart', 'place order', or 'checkout'")

        if not any(kw in user_message.lower() for kw in self.product_keywords):
            suggestions.append("Include the product name or category in your request")

        if pattern_match.intent == ShoppingIntent.GENERAL_SHOPPING and pattern_match.confidence < 0.5:
            suggestions.append("Try phrases like 'I want to buy [product]' or 'Add [product] to cart'")

        return suggestions

# Example usage and testing
def test_enhanced_patterns():
    """Test the enhanced pattern recognition system"""
    patterns = EnhancedOrderPatterns()

    test_messages = [
        "I want to buy a Samsung phone",
        "Add the Samsung Galaxy to cart",
        "Place order with RaqibPay",
        "How much is the Samsung Galaxy A24?",
        "Track order RQB2025053000034295",
        "Show me available products",
        "Is the Samsung phone in stock?",
        "Proceed to checkout",
        "Use card payment and order",
        "Add it to my cart"
    ]

    print("🔍 Testing Enhanced Order Pattern Recognition")
    print("=" * 60)

    for i, message in enumerate(test_messages, 1):
        match = patterns.detect_shopping_intent(message)
        entities = patterns.extract_entities(message, match.intent)

        print(f"\n{i}. Message: '{message}'")
        print(f"   Intent: {match.intent.value}")
        print(f"   Confidence: {match.confidence:.2f}")
        print(f"   Pattern: {match.matched_pattern}")
        print(f"   Entities: {entities}")
        print(f"   Explanation: {patterns.get_confidence_explanation(match)}")

        if match.confidence < 0.7:
            suggestions = patterns.suggest_improvements(message, match)
            print(f"   Suggestions: {suggestions}")

if __name__ == "__main__":
    test_enhanced_patterns()
