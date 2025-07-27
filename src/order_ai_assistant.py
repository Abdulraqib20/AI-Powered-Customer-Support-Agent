"""
🛒 AI-Powered Order Assistant for Nigerian E-commerce Platform
===============================================================================

Intelligent Shopping Assistant that can:
1. Add products to cart and manage shopping sessions
2. Calculate order totals with Nigerian context (delivery, taxes, discounts)
3. Actually place orders through the order management system
4. Provide order tracking and status updates
5. Handle payment method selection and validation
6. Manage delivery address and preferences

This AI assistant bridges the gap between conversational AI and actual order execution.

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import requests
import uuid
import re
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our existing systems
try:
    from .order_management import OrderManagementSystem, PaymentMethod, OrderStatus
    from .recommendation_engine import ProductRecommendationEngine
    from config.database_config import DatabaseManager, initialize_database
    from .conversation_memory_system import SessionState, WorldClassMemorySystem
    logger.info("✅ Successfully imported OrderManagementSystem, ProductRecommendationEngine, DatabaseManager, and SessionState with relative/config imports")
except ImportError as e1:
    logger.warning(f"⚠️ Relative/config import failed: {e1}")
    # Fallback for when imported directly
    try:
        from order_management import OrderManagementSystem, PaymentMethod, OrderStatus
        from recommendation_engine import ProductRecommendationEngine
        from config.database_config import DatabaseManager, initialize_database
        from conversation_memory_system import SessionState, WorldClassMemorySystem
        logger.info("✅ Successfully imported OrderManagementSystem, ProductRecommendationEngine, DatabaseManager, and SessionState with direct/config imports")
    except ImportError as e2:
        logger.error(f"❌ Direct/config import failed: {e2}")
        # Create mock classes if imports fail - but log this as an error
        logger.error("❌ CRITICAL: Using mock OrderManagementSystem - orders will NOT be saved to database!")

        class OrderManagementSystem:
            def check_product_availability(self, product_id, quantity):
                logger.error("❌ MOCK: check_product_availability called - real system not available")
                return {'available': True, 'product_info': {'product_name': 'Mock Product'}}

            def create_order(self, *args, **kwargs):
                logger.error("❌ MOCK: create_order called - NO DATABASE INSERTION HAPPENING!")
                return {'success': False, 'error': 'OrderManagementSystem not available - import failed'}

            def format_potential_order_summary(self, cart_summary, delivery_address, payment_method):
                """Format a potential order summary for checkout confirmation"""
                try:
                    items_text = ""
                    for item in cart_summary.get('items', []):
                        items_text += f"• {item['product_name']} - ₦{item['price']:,.2f} x{item['quantity']} = ₦{item['subtotal']:,.2f}\n"

                    summary = f"""
🛍️ **Order Summary**
{items_text}
📦 Total Items: {cart_summary.get('total_items', 0)}
💰 Subtotal: ₦{cart_summary.get('subtotal', 0):,.2f}

📍 **Delivery Address:** {delivery_address}
💳 **Payment Method:** {payment_method}
"""
                    return summary.strip()
                except Exception as e:
                    logger.error(f"❌ Error formatting order summary: {e}")
                    return f"Order Summary: {cart_summary.get('total_items', 0)} items, ₦{cart_summary.get('subtotal', 0):,.2f} total"

            def place_order(self, customer_id, cart_items, delivery_address, payment_method, notes=""):
                """Place an order and return order_id, order_details, error"""
                try:
                    # Generate a mock order ID
                    import time
                    order_id = f"ORD{int(time.time())}"

                    # Calculate total
                    total_amount = sum(item['subtotal'] for item in cart_items)

                    order_details = {
                        'order_id': order_id,
                        'customer_id': customer_id,
                        'items': cart_items,
                        'delivery_address': delivery_address,
                        'payment_method': payment_method.value if hasattr(payment_method, 'value') else str(payment_method),
                        'total_amount': total_amount,
                        'status': 'Pending',
                        'notes': notes
                    }

                    logger.warning(f"⚠️ MOCK ORDER PLACED: {order_id} for customer {customer_id} - Total: ₦{total_amount:,.2f}")
                    return order_id, order_details, None

                except Exception as e:
                    logger.error(f"❌ Error placing mock order: {e}")
                    return None, None, str(e)

            def format_order_summary(self, order_details):
                """Format order details into a readable summary"""
                try:
                    items_text = ""
                    for item in order_details.get('items', []):
                        items_text += f"• {item['product_name']} x{item['quantity']} - ₦{item['subtotal']:,.2f}\n"

                    summary = f"""
🎉 **Order Confirmation**
📋 Order ID: {order_details.get('order_id')}
{items_text}
💰 Total: ₦{order_details.get('total_amount', 0):,.2f}
📍 Delivery: {order_details.get('delivery_address')}
💳 Payment: {order_details.get('payment_method')}
📦 Status: {order_details.get('status')}
"""
                    return summary.strip()
                except Exception as e:
                    logger.error(f"❌ Error formatting order confirmation: {e}")
                    return f"Order {order_details.get('order_id', 'Unknown')} confirmed"

        class ProductRecommendationEngine:
            def __init__(self):
                logger.warning("⚠️ Using mock ProductRecommendationEngine")

        class PaymentMethod:
            PAY_ON_DELIVERY = "Pay on Delivery"
            RAQIB_TECH_PAY = "RaqibTechPay"

@dataclass
class CartItem:
    """Shopping cart item"""
    product_id: int
    product_name: str
    category: str
    brand: str
    price: float
    quantity: int
    subtotal: float

@dataclass
class ShoppingCart:
    """Customer shopping cart"""
    customer_id: int
    items: List[CartItem]
    subtotal: float
    delivery_state: str
    delivery_address: Dict[str, str]
    payment_method: str
    created_at: datetime
    updated_at: datetime

class OrderAIAssistant:
    """🤖 AI Assistant for Smart Order Management"""

    def __init__(self, memory_system: Optional[WorldClassMemorySystem]):
        try:
            self.order_system = OrderManagementSystem()
            logger.info("✅ OrderManagementSystem initialized successfully")
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to initialize OrderManagementSystem: {e}")
            raise Exception(f"OrderAIAssistant cannot function without OrderManagementSystem: {e}")

        try:
            self.recommendation_engine = ProductRecommendationEngine()
            logger.info("✅ ProductRecommendationEngine initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ ProductRecommendationEngine initialization failed: {e}")
            self.recommendation_engine = None

        self.active_carts = {}  # In-memory cart storage (use Redis in production)

        try:
            from config.database_config import DATABASE_CONFIG
            self.db_config = DATABASE_CONFIG
            logger.info("✅ Database configuration loaded successfully")
        except ImportError:
            # Fallback database configuration
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'oracle'),
                'sslmode': os.getenv('DB_SSLMODE', 'prefer'),
                'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
            }
            logger.warning("⚠️ Using fallback database configuration")

        # Handle memory system - create a mock one if None is passed
        if memory_system is not None:
            self.memory_system = memory_system
            logger.info("✅ OrderAIAssistant initialized successfully with WorldClassMemorySystem")
        else:
            logger.warning("⚠️ OrderAIAssistant initialized without memory system - using mock")
            # Create a mock memory system for compatibility
            class MockMemorySystem:
                def get_session_state(self, session_id): return None
                def update_session_state(self, session_id, state): pass
            self.memory_system = MockMemorySystem()

    def get_database_connection(self):
        """🔧 CRITICAL FIX: Get database connection for product searches"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise Exception(f"Database connection failed: {e}")

    def parse_order_intent(self, user_message: str) -> Dict[str, Any]:
        """🧠 Parse user message to determine shopping intent"""
        message_lower = user_message.lower()

        # 🔧 CRITICAL FIX: PRIORITY-BASED INTENT DETECTION
        # Check HIGH PRIORITY patterns first to avoid misclassification

        # 1. CUSTOMER QUERIES (view personal info, account details, order history) - HIGHEST PRIORITY
        customer_info_patterns = [
            "what's my tier", 'my account tier', 'account tier', 'what tier am i',
            'my information', 'my details', 'my profile', 'my account info',
            'show my', "what's my", 'view my', 'display my', 'tell me my',
            'my spending', 'how much have i spent', 'my orders', 'my purchase history',
            'confirm my', 'check my', 'verify my'  # Add confirmation patterns
        ]

        # 🔧 CRITICAL FIX: Account management vs product search disambiguation
        account_management_keywords = [
            'update my phone number', 'change my phone number', 'modify my phone',
            'update my email', 'change my email', 'modify my email',
            'update my address', 'change my address', 'modify my address',
            'update my details', 'change my details', 'update my profile'
        ]

        # Check for account management first (higher priority than product search)
        if any(pattern in message_lower for pattern in account_management_keywords):
            logger.info(f"🎯 Intent parsed: account_management (confidence: 0.9, pattern: 'account_management_pattern')")
            return {
                'intent': 'account_management',
                'confidence': 0.9,
                'matched_pattern': 'account_management_pattern',
                'entities': {},
                'raw_message': user_message
            }

        # 🔧 CRITICAL FIX: Address confirmation vs address setting
        address_viewing_patterns = [
            'confirm my delivery address', 'check my delivery address', 'verify my address',
            "what's my delivery address", 'show my delivery address', 'my delivery address',
            'confirm the delivery address for customer', 'check delivery address'
        ]

        if any(pattern in message_lower for pattern in address_viewing_patterns):
            logger.info(f"🎯 Intent parsed: view_address (confidence: 0.9, pattern: 'address_viewing_pattern')")
            return {
                'intent': 'view_address',
                'confidence': 0.9,
                'matched_pattern': 'address_viewing_pattern',
                'entities': {},
                'raw_message': user_message
            }

        # 1. HIGHEST PRIORITY: Payment method selection (must come before general "want")
        payment_patterns = [
            (r'payment method.*(is|set to|choose|select)\s*(.+)', 'payment_method_selection', 2),
            (r'pay\s*(with|using)\s*(.+)', 'payment_method_selection', 2),
            (r'(use|choose|select|want\s*to\s*use)\s*(raqibpay|raqibtechpay|pay\s*on\s*delivery|card\s*payment|bank\s*transfer|verve|mastercard|visa)', 'payment_method_selection', 2),
            (r'(verve|mastercard|visa|atm)\s*card', 'payment_method_selection', 0), # Card types
            (r'i\s*want\s*to\s*use\s*(.+)', 'payment_method_selection', 1), # Keep this for flexibility
            (r'payment\s*(option|preference)\s*is\s*(.+)', 'payment_method_selection', 2),
            (r'(raqibpay|raqibtechpay|pay\s*on\s*delivery|card\s*payment|bank\s*transfer)', 'payment_method_selection', 0) # Direct mention
        ]
        for pattern, intent, group_idx in payment_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entity = match.group(group_idx).strip() if group_idx > 0 and len(match.groups()) >= group_idx else match.group(0).strip()
                # Normalize payment method names
                if "raqib" in entity: entity = "RaqibTechPay"
                elif "delivery" in entity: entity = "Pay on Delivery"
                elif any(card_type in entity for card_type in ["card", "verve", "mastercard", "visa", "atm"]): entity = "Card"
                elif "bank" in entity: entity = "Bank Transfer"
                logger.info(f"🎯 Intent parsed: {intent} (confidence: 0.95, pattern: '{pattern}') - Entity: {entity}")
                return {'intent': intent, 'entities': {'payment_method': entity}, 'confidence': 0.95}

        # Check for shipping rate inquiries BEFORE delivery address patterns
        shipping_rate_patterns = [
            'shipping rates to', 'delivery cost to', 'delivery fee to', 'shipping cost to',
            'how much to ship to', 'what does it cost to ship to', 'delivery charges to',
            'what are your shipping rates', 'what are your delivery fees', 'shipping fees to'
        ]

        if any(pattern in message_lower for pattern in shipping_rate_patterns):
            logger.info(f"🎯 Intent parsed: general_inquiry (confidence: 0.9, pattern: 'shipping_rate_inquiry')")
            return {
                'intent': 'general_inquiry',
                'confidence': 0.9,
                'matched_pattern': 'shipping_rate_inquiry',
                'entities': {},
                'raw_message': user_message
            }

        # 2. HIGH PRIORITY: Delivery address (must come before general address mentions)
        # BUT EXCLUDE delivery policy questions, shipped order questions, and other non-address-setting queries
        delivery_exclusions = [
            'already shipped', 'has shipped', 'shipped order', 'change delivery', 'alter delivery',
            'modify delivery', 'update delivery', 'delivery options', 'delivery policy',
            "won't be home", 'not be home', 'pick up', 'pickup', 'warehouse pickup',
            'can i change', 'can you arrange', 'arrange for', 'package to be delivered',
            'what should i do', 'delivery instructions', 'damaged package', 'package arrived'
        ]

        # Only process delivery address patterns if it's NOT a delivery policy question
        if not any(exclusion in message_lower for exclusion in delivery_exclusions):
            delivery_patterns = [
                (r'(delivery|shipping)\s*address\s*(is|set to|for|:)\s*(.+)', 'set_delivery_address', 3),
                (r'my\s*address\s*(is|:)\s*(.+)', 'set_delivery_address', 2),
                (r'deliver\s*to\s*(.+)', 'set_delivery_address', 1),
                (r'send\s*to\s*(.+)', 'set_delivery_address', 1),
                (r'ship\s*to\s*(.+)', 'set_delivery_address', 1),
                (r'use\s*address\s*(.+)', 'set_delivery_address', 1), # For confirming saved address
                 # Common Nigerian locations as implicit address - BUT ONLY if NOT asking about rates/costs
                (r'(?<!shipping rates to )(?<!delivery cost to )(?<!shipping cost to )(?<!delivery fee to )\b(lugbe|abuja|lagos|ikeja|lekki|victoria island|ilorin|kano|kaduna|port harcourt|ibadan|benin city|onitsha|aba|enugu|jos|maiduguri|zaria|warri|uyo|calabar|owerri|akure|abeokuta|osogbo|minna|sokoto|bauchi|gombe|yola|jalingo|damaturu|dutse|lafia|makurdi|awka|asaba|yenagoa|abakaliki|Ado Ekiti)\b', 'set_delivery_address', 0)
            ]
        else:
            # Skip delivery address patterns for policy questions
            delivery_patterns = []
        for pattern, intent, group_idx in delivery_patterns:
            match = re.search(pattern, message_lower)
            if match:
                address_text = match.group(group_idx).strip() if group_idx > 0 and len(match.groups()) >= group_idx else match.group(0).strip()
                full_address, city, state = self._parse_nigerian_address(address_text)
                logger.info(f"🎯 Intent parsed: {intent} (confidence: 0.9, pattern: '{pattern}') - Address: {full_address}")
                return {'intent': intent, 'entities': {'delivery_address': {'full_address': full_address, 'city': city, 'state': state, 'raw': address_text}}, 'confidence': 0.9}

        # 3. HIGH PRIORITY: Place order / checkout (with typo tolerance)
        order_patterns = [
            (r'place\s*(my|the)?\s*order', 'place_order'),
            (r'confirm\s*(my|the)?\s*order', 'place_order'),
            (r'complete\s*(my|the)?\s*order', 'place_order'),
            (r'proceed\s*to\s*(order|ordering)', 'place_order'),  # Added this pattern
            (r'proceed\s*with\s*(my|the)?\s*order', 'place_order'),  # Added this pattern
            (r'proceed\s*to\s*che[ck]*out', 'checkout'),  # Handles "chekout", "checkout", "cheout" etc.
            (r'go\s*to\s*che[ck]*out', 'checkout'),
            (r'che[ck]*out\s*now', 'checkout'),
            (r'che[ck]*out', 'checkout')  # Broad checkout with typo tolerance
        ]
        for pattern, intent in order_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"🎯 Intent parsed: {intent} (confidence: 0.9, pattern: '{pattern}')")
                return {'intent': intent, 'entities': {}, 'confidence': 0.9}

        # 4. MEDIUM PRIORITY: Add to cart (explicit purchase intent only)
        cart_patterns = [
            (r'add\s+(.+?)\s+to\s+(my|the)?\s*cart', 'add_to_cart'),
            (r'put\s+(.+?)\s+in\s+(my|the)?\s*cart', 'add_to_cart'),
            (r'i\s*want\s*to\s*buy\s+(.+)', 'add_to_cart'),
            (r'buy\s+(.+?)\s*(now|please)', 'add_to_cart'),
            (r'add\s+(.+?)\s+to\s*my\s*order', 'add_to_cart'),
            (r'purchase\s+(.+)', 'add_to_cart'),
            # More specific order pattern to avoid false positives
            (r'^(order|i want to order)\s+(?:\d+\s+)?(.+)', 'add_to_cart')
        ]
        for pattern, intent in cart_patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Extract product name from the appropriate group
                if r'get\s+(me\s+)' in pattern:
                    product_name = match.group(2).strip() if len(match.groups()) >= 2 else match.group(1).strip()
                else:
                    product_name = match.group(1).strip()

                # Clean up common trailing phrases that might have been captured
                product_name = re.sub(r'\s*(to\s+(my|the)?\s*cart|for\s+me|please)$', '', product_name, flags=re.IGNORECASE).strip()

                logger.info(f"🎯 Intent parsed: {intent} (confidence: 0.85, pattern: '{pattern}') - Product: {product_name}")
                return {'intent': intent, 'entities': {'product_name': product_name}, 'confidence': 0.85}

        # 5. CHECKOUT FLOW PATTERNS (HIGH PRIORITY)
        checkout_patterns = [
            'proceed with checkout', 'continue checkout', 'proceed with my shopping',
            'continue with my order', 'proceed with order', 'continue shopping',
            'want to proceed', 'want to continue', 'proceed with my order',
            'finish checkout', 'complete my order', 'finalize order',
            'continue with payment', 'proceed to payment'
        ]

        for pattern in checkout_patterns:
            if pattern in message_lower:
                logger.info(f"🎯 Intent parsed: checkout (confidence: 0.95, pattern: '{pattern}')")
                return {'intent': 'checkout', 'entities': {}, 'confidence': 0.95}

        # 6. CONTEXT-AWARE AFFIRMATIVE/NEGATIVE RESPONSES
        # Clean message for matching (remove punctuation)
        clean_message = re.sub(r'[^\w\s]', '', message_lower).strip()

        if clean_message in ['yes', 'yeah', 'yep', 'yup', 'yea', 'ok', 'okay', 'sure', 'alright', 'y']:
            logger.info(f"🎯 Intent parsed: affirmative_confirmation (confidence: 0.95, pattern: 'affirmative_words')")
            return {'intent': 'affirmative_confirmation', 'entities': {}, 'confidence': 0.95}

        if clean_message in ['no', 'nope', 'nah', 'n', 'cancel', 'stop']:
            logger.info(f"🎯 Intent parsed: negative_rejection (confidence: 0.95, pattern: 'negative_words')")
            return {'intent': 'negative_rejection', 'entities': {}, 'confidence': 0.95}

        # 6. OTHER SPECIFIC INTENTS
        other_patterns = {
            'view_cart': [
                'view cart', 'show cart', 'cart contents', "what's in my cart",
                'shopping cart', 'cart status', 'show my cart', 'list cart',
                'list all the items in my cart', 'cart items', 'what did i add'
            ],
            'clear_cart': [
                'remove from cart', 'delete from cart', 'take out', 'remove this',
                'clear cart', 'empty cart', 'empty my cart', 'clear my cart',
                'remove all', 'delete all', 'clear everything', 'empty everything'
            ],
            'calculate_total': [
                'calculate total', 'show total', 'how much', 'total cost',
                'delivery fee', 'shipping cost', 'order total', 'final cost'
            ],
            'track_order': [
                'track order', 'order status', 'where is my order', 'delivery status',
                'check order', 'order tracking', 'order progress'
            ]
        }

        for intent, patterns in other_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    logger.info(f"🎯 Intent parsed: {intent} (confidence: 0.9, pattern: '{pattern}')")
                    return {
                        'intent': intent,
                        'confidence': 0.9,
                        'matched_pattern': pattern,
                        'raw_message': user_message
                    }

        # 7. CONTEXT-AWARE FALLBACK DETECTION
        # Check for delivery address mentions by location - BUT EXCLUDE shipping rate inquiries
        if (any(word in message_lower for word in ['lugbe', 'lagos', 'abuja', 'kano', 'port harcourt']) and
            not any(rate_word in message_lower for rate_word in ['rates', 'cost', 'fee', 'charge', 'price', 'how much'])):
            logger.info(f"🎯 Intent parsed: set_delivery_address (confidence: 0.8, pattern: 'location_mention')")
            return {
                'intent': 'set_delivery_address',
                'confidence': 0.8,
                'matched_pattern': "location_mention",
                'raw_message': user_message
            }

        # 8. PRODUCT INQUIRY (NOT automatic add to cart) - Show details first
        inquiry_words = ['want', 'need', 'looking for', 'show me', 'find', 'search for', 'get me']
        product_keywords = ['samsung', 'iphone', 'phone', 'galaxy', 'laptop', 'tecno', 'google', 'pixel',
                           'spag', 'rice', 'headphone', 'shoes', 'bag', 'watch', 'tablet', 'earphone',
                           'camera', 'speaker', 'charger', 'cable', 'mouse', 'keyboard']

        if (any(word in message_lower for word in inquiry_words) and
            any(product in message_lower for product in product_keywords)):
            # But exclude if it's clearly about payment or delivery
            if not any(payment_word in message_lower for payment_word in ['pay', 'payment', 'delivery', 'raqib', 'checkout']):
                logger.info(f"🎯 Intent parsed: product_inquiry (confidence: 0.8, pattern: 'product_search')")
                return {
                    'intent': 'product_inquiry',
                    'confidence': 0.8,
                    'matched_pattern': "product_search",
                    'raw_message': user_message
                }

        # 9. DEFAULT: General inquiry
        logger.info(f"🎯 Intent parsed: general_inquiry (confidence: 0.5, pattern: 'no_match')")
        return {
            'intent': 'general_inquiry',
            'confidence': 0.5,
            'matched_pattern': "no_match",
            'raw_message': user_message
        }

    def extract_product_info(self, user_message: str, product_name_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """🔍 Extract product information from user message with enhanced context awareness"""

        # 🔧 ENHANCED PRONOUN DETECTION: Handle "it", "this", "that" anywhere in the message
        pronouns = ['it', 'this', 'that', 'them']
        user_message_lower = user_message.lower().strip()
        words = user_message_lower.split()

        # Check for contextual phrases that indicate user is referring to a previously mentioned product
        context_indicators = [
            'add it to cart',
            'add to cart',
            'buy it',
            'get it',
            'want it',
            'need it',
            'add them to cart',
            'pieces and add',
            'quantity and add'
        ]

        is_referring_to_context = (
            any(pronoun in words for pronoun in pronouns) or  # Contains pronouns
            any(indicator in user_message_lower for indicator in context_indicators) or  # Contains context indicators
            (('add' in words or 'buy' in words) and len([w for w in words if len(w) >= 3]) <= 3)  # Short add/buy commands
        )

        if is_referring_to_context:
            logger.info(f"🎯 CONTEXT REFERENCE DETECTED: '{user_message}' - checking for last mentioned product")

            # Try to get last mentioned product from session context
            if hasattr(self, '_last_mentioned_product') and self._last_mentioned_product:
                logger.info(f"✅ USING CONTEXT: Found last mentioned product: {self._last_mentioned_product.get('product_name')}")
                return self._last_mentioned_product

            # 🔧 CRITICAL FIX: Try to get product context from enhanced database system
            try:
                from .enhanced_db_querying import EnhancedDatabaseQuerying
                enhanced_db = EnhancedDatabaseQuerying()

                # Use session ID if available (could be passed as parameter in future enhancement)
                session_id = getattr(self, '_current_session_id', 'unknown_session')
                customer_id = getattr(self, '_current_customer_id', None)
                user_id = f"customer_{customer_id}" if customer_id else "anonymous"

                if hasattr(enhanced_db, 'get_last_mentioned_product'):
                    last_product = enhanced_db.get_last_mentioned_product(user_id, session_id)
                    if last_product:
                        logger.info(f"✅ USING DATABASE CONTEXT: Found last mentioned product: {last_product.get('product_name')}")
                        # Store it locally for faster access next time
                        self._last_mentioned_product = last_product
                        return last_product
            except Exception as e:
                logger.warning(f"⚠️ Failed to retrieve product context from database: {e}")

            # If it's clearly a context reference but no context found, return None
            logger.warning(f"⚠️ CONTEXT REFERENCE WITHOUT CONTEXT: '{user_message}' but no previous product context found")
            return None

        if product_name_hint:
            target_product_name = product_name_hint.strip()
        else:
            # Extract potential product name from the message
            target_product_name = user_message.strip()

        # 🔧 CRITICAL FIX: Context-aware word filtering to prevent false matches
        context_exclusion_patterns = [
            r'\bphone\s+number\b',  # 'phone number' should not match phone products
            r'\bemail\s+address\b',  # 'email address' should not match email products
            r'\bupdate\s+my\b',     # 'update my X' is account management, not shopping
            r'\bchange\s+my\b',     # 'change my X' is account management
            r'\bmodify\s+my\b',     # 'modify my X' is account management
            r'\bconfirm\s+my\b',    # 'confirm my X' is viewing info, not shopping
            r'\bcheck\s+my\b',      # 'check my X' is viewing info
            r'\bverify\s+my\b',     # 'verify my X' is viewing info
        ]

        # Check if the user message contains account management context
        is_account_management = any(re.search(pattern, target_product_name, re.IGNORECASE)
                                  for pattern in context_exclusion_patterns)

        def print_log(message, level='info'):
            """Logs a message with a specified log level and colors."""
            levels = {
                'info': '\033[94m',   # Blue
                'warning': '\033[93m', # Yellow
                'error': '\033[91m',   # Red
                'success': '\033[92m', # Green
                'reset': '\033[0m'     # Reset color
            }
            color = levels.get(level, levels['info'])
            print(f"{color}[DB_QUERY] {level.upper()}: {message}{levels['reset']}")

        if is_account_management:
            print_log(f"❌ Account management context detected - not a product search: {target_product_name}")
            return None

        # Clean up common stop words from product name
        words_to_filter = ['add', 'to', 'cart', 'buy', 'purchase', 'get', 'me', 'want', 'to', 'order',
                          'please', 'can', 'you', 'i', 'my', 'the', 'a', 'an', 'give', 'pieces', 'and',
                          'put', 'place', 'proceed', 'checkout', 'confirm', 'continue', 'quantity', 'amount']

        # 🔧 ENHANCED FILTERING: Split and filter words, but preserve meaningful product terms
        # Don't filter if the word is longer than 3 characters or is a known product term
        important_product_terms = ['phone', 'rice', 'dress', 'shoe', 'bag', 'book', 'oil', 'cream', 'milk', 'bread', 'fish', 'meat']

        cleaned_words = []
        for word in target_product_name.lower().split():
            # Keep the word if:
            # 1. It's longer than 3 characters AND not in filter list, OR
            # 2. It's an important product term
            if ((len(word) >= 3 and word not in words_to_filter) or word in important_product_terms):
                cleaned_words.append(word)

        if not cleaned_words:
            print_log(f"❌ No meaningful product terms found in: {target_product_name}")
            return None

        cleaned_product_name = ' '.join(cleaned_words)

        try:
            print_log(f"🔍 Searching for product: '{cleaned_product_name}' (from: '{target_product_name}')")

            # Search product with multiple strategies
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    print_log(f"🔍 DEBUG: Starting Strategy 1 - Direct name match", 'info')
                    # Strategy 1: Direct name match (most reliable)
                    cursor.execute("""
                        SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity
                        FROM products WHERE LOWER(product_name) LIKE LOWER(%s) AND in_stock = TRUE
                        ORDER BY
                            CASE WHEN LOWER(product_name) = LOWER(%s) THEN 1 ELSE 2 END,
                            product_name
                        LIMIT 1
                    """, (f"%{cleaned_product_name}%", cleaned_product_name))

                    product = cursor.fetchone()
                    if product:
                        print_log(f"✅ Product found via Direct name match: {product['product_name']}", 'success')
                        product_dict = dict(product)

                        # 🔧 CRITICAL FIX: Store this as last mentioned product for context
                        self._last_mentioned_product = product_dict
                        logger.info(f"🎯 EXTRACTED PRODUCT FOR CONTEXT: {product_dict['product_name']} (ID: {product_dict['product_id']})")
                        logger.info(f"🧠 STORED PRODUCT CONTEXT: {product_dict['product_name']} ready for potential shopping action")

                        return product_dict

                    print_log(f"🔍 DEBUG: Strategy 1 failed, starting Strategy 2 - Smart category mapping", 'info')
                    # Strategy 2: Smart category and product search with exclusions
                    # Map search terms to actual categories in database + exclusions
                    category_mapping = {
                        'phone': {
                            'categories': ['Electronics'],  # Mobile phones are in Electronics, not Automotive
                            'exclude_terms': ['holder', 'mount', 'car'],  # Exclude car accessories
                            'exact_match_required': False,  # Allow flexible matching
                            'prefer_terms': ['smartphone', 'mobile', 'iphone', 'samsung', 'tecno', 'infinix'],  # Prioritize actual phones
                            'priority': 1  # High priority for actual phones
                        },
                        'smartphone': {
                            'categories': ['Electronics'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 1
                        },
                        'mobile': {
                            'categories': ['Electronics'],
                            'exclude_terms': ['holder', 'mount', 'car'],
                            'exact_match_required': False,
                            'priority': 1
                        },
                        'laptop': {
                            'categories': ['Computing', 'Electronics'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 2
                        },
                        'headphone': {
                            'categories': ['Electronics'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 2
                        },
                        'television': {
                            'categories': ['Electronics'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 2
                        },
                        'tv': {
                            'categories': ['Electronics'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 2
                        },
                        'rice': {
                            'categories': ['Food Items'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 3
                        },
                        'spag': {
                            'categories': ['Food Items'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 3
                        },
                        'spaghetti': {
                            'categories': ['Food Items'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 3
                        },
                        'car': {
                            'categories': ['Automotive'],
                            'exclude_terms': [],
                            'exact_match_required': False,
                            'priority': 4
                        }
                    }

                    # Check if search term matches a category with smart filtering
                    search_key = cleaned_product_name.lower()
                    category_config = None
                    matched_key = None

                    print_log(f"🔍 DEBUG: Processing search_key: '{search_key}'", 'info')

                    # Find the best matching category configuration with priority
                    best_match = None
                    best_priority = float('inf')

                    print_log(f"🔍 DEBUG: Starting category mapping search", 'info')
                    for key, config in category_mapping.items():
                        if key in search_key:
                            print_log(f"🔍 DEBUG: Found key '{key}' in search_key", 'info')
                            # Check for exclusion terms
                            exclude_terms = config.get('exclude_terms', [])
                            print_log(f"🔍 DEBUG: Checking exclusion terms: {exclude_terms}", 'info')
                            has_exclusion = any(exclude_term in search_key for exclude_term in exclude_terms)
                            if not has_exclusion:
                                priority = config.get('priority', 5)
                                print_log(f"🔍 DEBUG: No exclusions, priority: {priority}", 'info')
                                if priority < best_priority:
                                    best_match = config
                                    best_priority = priority
                                    matched_key = key
                                    print_log(f"🔍 DEBUG: New best match: {matched_key}", 'info')

                    print_log(f"🔍 DEBUG: Final best_match: {matched_key if best_match else None}", 'info')
                    if best_match:
                        category_config = best_match

                        print_log(f"🔍 DEBUG: Processing enhanced search logic", 'info')
                        # Enhanced search with preference for specific terms
                        prefer_terms = category_config.get('prefer_terms', [])
                        categories = category_config['categories']
                        exclude_terms = category_config.get('exclude_terms', [])

                        print_log(f"🔍 DEBUG: prefer_terms: {prefer_terms}, categories: {categories}, exclude_terms: {exclude_terms}", 'info')

                        # Build exclusion clause
                        exclusion_clause = ""
                        if exclude_terms:
                            exclusion_conditions = ' AND '.join([f"LOWER(product_name) NOT LIKE LOWER('%{term}%')" for term in exclude_terms])
                            exclusion_clause = f" AND ({exclusion_conditions})"
                            print_log(f"🔍 DEBUG: Built exclusion_clause: {exclusion_clause}", 'info')

                        # Build preference scoring for actual products vs accessories
                        preference_score = "0"
                        if prefer_terms:
                            preference_conditions = ' + '.join([f"(CASE WHEN LOWER(product_name) LIKE LOWER('%{term}%') THEN 10 ELSE 0 END)" for term in prefer_terms])
                            preference_score = f"({preference_conditions})"
                            print_log(f"🔍 DEBUG: Built preference_score: {preference_score}", 'info')

                        # Search with smart prioritization
                        category_placeholders = ' OR '.join(['LOWER(category) = LOWER(%s)'] * len(categories))
                        print_log(f"🔍 DEBUG: About to execute enhanced SQL query with {len(categories)} categories", 'info')

                        # Validate categories list before use
                        print_log(f"🔍 DEBUG: Categories validation - type: {type(categories)}, length: {len(categories)}, content: {categories}", 'info')

                        if not categories or len(categories) == 0:
                            print_log(f"❌ ERROR: Categories list is empty!", 'error')
                            return None

                        # Use direct string substitution for the complex CASE statements to avoid parameter conflicts
                        preference_conditions = []
                        for term in prefer_terms:
                            preference_conditions.append(f"(CASE WHEN LOWER(product_name) LIKE LOWER('%{term}%') THEN 10 ELSE 0 END)")
                        preference_score_sql = " + ".join(preference_conditions) if preference_conditions else "0"

                        # Build exclusion conditions with direct string substitution
                        exclusion_conditions = []
                        for term in exclude_terms:
                            exclusion_conditions.append(f"LOWER(product_name) NOT LIKE LOWER('%{term}%')")
                        exclusion_clause = f" AND ({' AND '.join(exclusion_conditions)})" if exclusion_conditions else ""

                        # Use the first category directly to avoid list indexing issues
                        primary_category = categories[0] if len(categories) > 0 else 'Electronics'
                        print_log(f"🔍 DEBUG: Using primary_category: '{primary_category}'", 'info')

                        # Simplified SQL without complex string substitution to avoid parameter issues
                        try:
                            # Basic safe query first
                            basic_sql = """
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity
                                FROM products
                                WHERE LOWER(category) = LOWER(%s) AND in_stock = TRUE
                                ORDER BY product_name
                                LIMIT 1
                            """
                            print_log(f"🔍 DEBUG: Executing basic safe SQL query", 'info')
                            cursor.execute(basic_sql, (primary_category,))

                            product = cursor.fetchone()
                            print_log(f"🔍 DEBUG: cursor.fetchone() completed, result type: {type(product)}", 'info')
                            print_log(f"🔍 DEBUG: Product result: {product is not None}", 'info')

                            if product:
                                print_log(f"🔍 DEBUG: About to process product result", 'info')

                                # Safe access to product fields
                                if hasattr(product, 'get'):  # It's a dict-like object
                                    product_name = product.get('product_name', 'Unknown Product')
                                elif hasattr(product, '__getitem__'):  # It's indexable
                                    try:
                                        product_name = product['product_name']
                                    except (KeyError, IndexError):
                                        product_name = str(product[1]) if len(product) > 1 else 'Unknown Product'
                                else:
                                    product_name = 'Unknown Product'

                                print_log(f"✅ Product found via Enhanced Smart mapping: {product_name}", 'success')

                                # Convert to dict safely
                                if hasattr(product, 'keys'):  # Already dict-like
                                    product_dict = dict(product)
                                else:  # Tuple result, need to map to dict
                                    product_dict = {
                                        'product_id': product[0] if len(product) > 0 else None,
                                        'product_name': product[1] if len(product) > 1 else 'Unknown Product',
                                        'category': product[2] if len(product) > 2 else 'Unknown',
                                        'brand': product[3] if len(product) > 3 else 'Unknown',
                                        'description': product[4] if len(product) > 4 else '',
                                        'price': product[5] if len(product) > 5 else 0,
                                        'currency': product[6] if len(product) > 6 else 'NGN',
                                        'in_stock': product[7] if len(product) > 7 else True,
                                        'stock_quantity': product[8] if len(product) > 8 else 0
                                    }

                                print_log(f"🔍 DEBUG: Product dict created successfully", 'info')

                                product_dict['match_priority'] = 1  # High priority for enhanced matching
                                self._last_mentioned_product = product_dict

                                logger.info(f"🎯 ENHANCED SMART MATCH: {product_dict['product_name']} for query: {cleaned_product_name}")
                                return product_dict
                            else:
                                print_log(f"🔍 DEBUG: No product found in enhanced search", 'info')

                        except Exception as sql_error:
                            print_log(f"❌ SQL EXECUTION ERROR: {str(sql_error)}", 'error')
                            import traceback
                            print_log(f"❌ SQL ERROR TRACEBACK: {traceback.format_exc()}", 'error')
                            # Continue to next strategy instead of failing completely

                    print_log(f"🔍 DEBUG: Starting Strategy 3 - Dynamic product discovery", 'info')
                    # Strategy 2: Dynamic database-aware product discovery
                    from product_discovery import get_product_discovery_engine

                    try:
                        discovery_engine = get_product_discovery_engine()
                        suggestion_result = discovery_engine.get_smart_suggestions(cleaned_product_name)

                        if suggestion_result and suggestion_result.get('found', False):
                            best_match = suggestion_result.get('best_match')
                            if best_match:
                                alternatives = suggestion_result.get('alternatives', [])

                                print_log(f"✅ Product found via Dynamic Discovery: {best_match['product_name']}", 'success')
                                product_dict = dict(best_match)

                                # Add world-class customer experience data
                                product_dict['alternatives'] = alternatives
                                product_dict['is_popular'] = True  # Default assumption
                                product_dict['world_class_response'] = True

                                self._last_mentioned_product = product_dict
                                logger.info(f"🎯 DYNAMIC DISCOVERY: {product_dict['product_name']} found for '{cleaned_product_name}'")
                                return product_dict

                    except Exception as discovery_error:
                        logger.warning(f"⚠️ Dynamic discovery failed: {discovery_error}")
                        print_log(f"❌ Dynamic discovery error: {str(discovery_error)}", 'error')

                    print_log(f"🔍 DEBUG: Starting Strategy 4 - Fallback customer intent mapping", 'info')
                    # Fallback to legacy smart mapping for specific cases
                    customer_intent_mapping = {
                        'phone': {
                            'customer_expects': 'mobile phones, smartphones, android phones, iphones',
                            'available_alternatives': ['Car Phone Holder'],
                            'explanation': "Let me find the best mobile phones available for you.",
                            'search_categories': ['Electronics'],
                            'exact_product_names': [],
                            'prefer_terms': ['smartphone', 'iphone', 'samsung', 'tecno', 'infinix', 'mobile'],
                            'exclude_terms': ['holder', 'mount', 'car']
                        },
                        'smartphone': {
                            'customer_expects': 'smartphones, mobile phones, android phones, iphones',
                            'available_alternatives': [],
                            'explanation': "We have excellent smartphones available.",
                            'search_categories': ['Electronics'],
                            'exact_product_names': [],
                            'prefer_terms': ['smartphone', 'iphone', 'samsung', 'tecno', 'infinix'],
                            'exclude_terms': ['holder', 'mount', 'car']
                        },
                        'mobile': {
                            'customer_expects': 'mobile phones, smartphones, android phones, iphones',
                            'available_alternatives': [],
                            'explanation': "Let me find the best mobile phones for you.",
                            'search_categories': ['Electronics'],
                            'exact_product_names': [],
                            'prefer_terms': ['smartphone', 'iphone', 'samsung', 'tecno', 'infinix', 'mobile'],
                            'exclude_terms': ['holder', 'mount', 'car']
                        },
                        'laptop': {
                            'customer_expects': 'laptops, computers, notebooks',
                            'available_alternatives': [],
                            'explanation': "Let me check what computing devices we have available.",
                            'search_categories': ['Computing', 'Electronics'],
                            'exact_product_names': [],
                            'prefer_terms': ['laptop', 'notebook', 'macbook'],
                            'exclude_terms': []
                        },
                        'headphone': {
                            'customer_expects': 'headphones, earphones, audio devices',
                            'available_alternatives': ['Bluetooth Headphones'],
                            'explanation': "We have audio devices available.",
                            'search_categories': ['Electronics'],
                            'exact_product_names': ['Bluetooth Headphones'],
                            'prefer_terms': ['headphone', 'bluetooth'],
                            'exclude_terms': []
                        },
                        'television': {
                            'customer_expects': 'televisions, smart TVs, displays',
                            'available_alternatives': [],
                            'explanation': "We have various TV options available.",
                            'search_categories': ['Electronics'],
                            'exact_product_names': [],
                            'prefer_terms': ['tv', 'television', 'smart tv', 'oled', 'led'],
                            'exclude_terms': []
                        },
                        'tv': {
                            'customer_expects': 'televisions, smart TVs, displays',
                            'available_alternatives': [],
                            'explanation': "We have various TV options available.",
                            'search_categories': ['Electronics'],
                            'exact_product_names': [],
                            'prefer_terms': ['tv', 'television', 'smart tv', 'oled', 'led'],
                            'exclude_terms': []
                        }
                    }

                    # Check if this is a known customer intent
                    matched_intent = None
                    for intent_key, intent_config in customer_intent_mapping.items():
                        if intent_key in search_key:
                            matched_intent = intent_config
                            break

                    if matched_intent:
                        # First try exact product names if available
                        exact_products = matched_intent['exact_product_names']
                        if exact_products:
                            exact_placeholders = ' OR '.join(['LOWER(product_name) = LOWER(%s)'] * len(exact_products))
                            cursor.execute(f"""
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity,
                                       1 as match_priority
                                FROM products
                                WHERE ({exact_placeholders}) AND in_stock = TRUE
                                ORDER BY product_name
                                LIMIT 1
                            """, exact_products)

                            product = cursor.fetchone()
                            if product:
                                print_log(f"✅ Product found via Smart mapping: {product['product_name']}", 'success')
                                product_dict = dict(product)
                                # Add customer education context
                                product_dict['customer_education'] = matched_intent['explanation']
                                product_dict['customer_expected'] = matched_intent['customer_expects']
                                self._last_mentioned_product = product_dict
                                logger.info(f"🎯 SMART MATCH: {product_dict['product_name']} for customer intent: {matched_intent['customer_expects']}")
                                return product_dict

                        # If no exact matches, search by category with enhanced logic
                        categories = matched_intent['search_categories']
                        prefer_terms = matched_intent.get('prefer_terms', [])
                        exclude_terms = matched_intent.get('exclude_terms', [])

                        if categories:
                            # Build exclusion clause
                            exclusion_clause = ""
                            if exclude_terms:
                                exclusion_conditions = ' AND '.join([f"LOWER(product_name) NOT LIKE LOWER('%{term}%')" for term in exclude_terms])
                                exclusion_clause = f" AND ({exclusion_conditions})"

                            # Build preference scoring for actual products vs accessories
                            preference_score = "0"
                            if prefer_terms:
                                preference_conditions = ' + '.join([f"(CASE WHEN LOWER(product_name) LIKE LOWER('%{term}%') THEN 10 ELSE 0 END)" for term in prefer_terms])
                                preference_score = f"({preference_conditions})"

                            category_placeholders = ' OR '.join(['LOWER(category) = LOWER(%s)'] * len(categories))
                            cursor.execute(f"""
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity,
                                       {preference_score} as preference_score,
                                       2 as match_priority
                                FROM products
                                WHERE ({category_placeholders}) AND in_stock = TRUE {exclusion_clause}
                                ORDER BY preference_score DESC, product_name
                                LIMIT 1
                            """, categories)

                        product = cursor.fetchone()
                        if product:
                            print_log(f"✅ Product found via Smart category mapping: {product['product_name']}", 'success')
                            product_dict = dict(product)
                            product_dict['match_priority'] = 1  # High priority for enhanced matching
                            self._last_mentioned_product = product_dict
                            logger.info(f"🎯 SMART CATEGORY MATCH: {product_dict['product_name']} for customer intent: {matched_intent['customer_expects']}")
                            return product_dict
                    else:
                        # Fallback to word boundary matching (avoid substring issues)
                        word_patterns = [f"\\y{word}\\y" for word in cleaned_words if len(word) > 2]  # Only words > 2 chars
                        if word_patterns:
                            # Simplified approach: score based on how many pattern words match
                            placeholders = ' OR '.join(['LOWER(product_name) ~ LOWER(%s)'] * len(word_patterns))
                            # Calculate match score using CASE statements instead of unnest
                            match_score_cases = ' + '.join([f"(CASE WHEN LOWER(product_name) ~ LOWER(%s) THEN 1 ELSE 0 END)" for _ in word_patterns])

                            cursor.execute(f"""
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity,
                                       ({match_score_cases}) as word_matches
                                FROM products
                                WHERE ({placeholders}) AND in_stock = TRUE
                                ORDER BY word_matches DESC, product_name
                                LIMIT 1
                            """, word_patterns + word_patterns)  # Parameters for match_score_cases + placeholders
                        else:
                            # Very basic fallback
                            cursor.execute("""
                                SELECT product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity,
                                       0 as word_matches
                                FROM products
                                WHERE LOWER(product_name) LIKE LOWER(%s) AND in_stock = TRUE
                                ORDER BY product_name
                                LIMIT 1
                            """, (f"%{cleaned_product_name}%",))

                    product = cursor.fetchone()
                    if product:
                        print_log(f"✅ Product found via Word matching: {product['product_name']}", 'success')
                        product_dict = dict(product)

                        # 🔧 CRITICAL FIX: Store this as last mentioned product for context
                        self._last_mentioned_product = product_dict
                        logger.info(f"🎯 EXTRACTED PRODUCT FOR CONTEXT: {product_dict['product_name']} (ID: {product_dict['product_id']})")

                        return product_dict

                    print_log(f"❌ No matching product found for: {cleaned_product_name}", 'warning')
                    return None

        except Exception as e:
            print_log(f"❌ Database error in extract_product_info: {e}", 'error')
            return None

    def add_to_cart(self, customer_id: int, product_info: Dict, quantity: int = 1) -> Dict[str, Any]:
        """🛒 Add product to customer's cart"""
        try:
            cart_key = f"cart_{customer_id}"  # Consistent cart key format

            # Initialize cart if it doesn't exist
            if cart_key not in self.active_carts:
                self.active_carts[cart_key] = {
                    'customer_id': customer_id,
                    'items': [],
                    'subtotal': 0.0,
                    'delivery_state': 'Lagos',  # Default
                    'delivery_address': {},
                    'payment_method': 'Pay on Delivery',  # Default
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }

            cart = self.active_carts[cart_key]

            # Create cart item
            cart_item = {
                'product_id': product_info.get('product_id'),
                'product_name': product_info.get('product_name'),
                'category': product_info.get('category', 'Electronics'),
                'brand': product_info.get('brand', ''),
                'price': float(product_info.get('price', 0)),
                'quantity': quantity,
                'subtotal': float(product_info.get('price', 0)) * quantity
            }

            # Check if product already in cart
            existing_item = None
            for item in cart['items']:
                if item['product_id'] == cart_item['product_id']:
                    existing_item = item
                    break

            if existing_item:
                # Update quantity
                existing_item['quantity'] += quantity
                existing_item['subtotal'] = existing_item['price'] * existing_item['quantity']
            else:
                # Add new item
                cart['items'].append(cart_item)

            # Recalculate cart totals
            cart['subtotal'] = sum(item['subtotal'] for item in cart['items'])
            cart['updated_at'] = datetime.now()

            # Save to in-memory storage (replace with Redis in production)
            self.active_carts[cart_key] = cart

            logger.info(f"✅ Added {product_info.get('product_name')} to cart for customer {customer_id}")

            return {
                'success': True,
                'message': f"✅ Added {product_info.get('product_name')} to your cart! 🎉",
                'action': 'add_to_cart_success',
                'cart_summary': self._get_cart_summary(cart),
                'product_added': cart_item
            }

        except Exception as e:
            logger.error(f"❌ Error adding to cart: {e}")
            return {
                'success': False,
                'message': "Sorry, I couldn't add that product to your cart. Please try again!",
                'action': 'add_to_cart_error',
                'error': str(e)
            }

    def calculate_order_preview(self, customer_id: int, delivery_state: str = "Lagos") -> Dict[str, Any]:
        """💰 Calculate order totals preview"""
        try:
            cart_key = f"cart_{customer_id}"
            if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Add some products first. 🛒",
                    'action': 'empty_cart'
                }

            # 🆕 ENHANCED LOGGING FOR CALCULATION
            logger.info(f"💰 CALCULATING ORDER PREVIEW for customer {customer_id}")
            logger.info(f"📦 Cart items: {len(self.active_carts[cart_key]['items'])}")
            logger.info(f"🚚 Delivery state: {delivery_state}")

            cart = self.active_carts[cart_key]

            # Convert cart items to order format
            order_items = []
            for item in cart['items']:
                order_items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity']
                })

            # Calculate totals using order management system
            calculation = self.order_system.calculate_order_totals(
                items=order_items,
                customer_id=customer_id,
                delivery_state=delivery_state
            )

            if not calculation['success']:
                return {
                    'success': False,
                    'message': f"Error calculating totals: {calculation['error']}",
                    'action': 'calculation_error'
                }

            return {
                'success': True,
                'message': "Order totals calculated successfully! 💰",
                'action': 'calculation_success',
                'calculation': calculation,
                'formatted_summary': self._format_order_summary(calculation)
            }

        except Exception as e:
            logger.error(f"❌ Error calculating order: {e}")
            return {
                'success': False,
                'message': "Error calculating order totals. Please try again!",
                'action': 'calculation_error'
            }

    def place_order(self, customer_id: int, delivery_address: Dict, payment_method: str) -> Dict[str, Any]:
        """🎯 Actually place the order"""
        try:
            cart_key = f"cart_{customer_id}"
            if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Add some products first. 🛒",
                    'action': 'empty_cart'
                }

            # 🆕 ENHANCED LOGGING FOR ORDER PLACEMENT
            logger.info(f"🎯 PLACING ORDER for customer {customer_id}")
            logger.info(f"📦 Cart items: {len(self.active_carts[cart_key]['items'])}")
            logger.info(f"🚚 Delivery: {delivery_address}")
            logger.info(f"💳 Payment: {payment_method}")

            cart = self.active_carts[cart_key]

            # Convert cart items to order format
            order_items = []
            for item in cart['items']:
                order_items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity']
                })

            # Place order using order management system
            logger.info("📞 Calling OrderManagementSystem.create_order()...")
            order_id, order_details, error = self.order_system.place_order(
                customer_id=customer_id,
                cart_items=order_items,
                delivery_address=delivery_address,
                payment_method=payment_method,
                notes="Order placed via AI Assistant"
            )

            logger.info(f"📋 Order creation result: {order_id is not None}")
            if order_id:
                # Clear cart after successful order
                del self.active_carts[cart_key]

                logger.info(f"✅ ORDER SUCCESSFULLY PLACED! Order ID: {order_id}")
                logger.info(f"💾 Database order ID: {order_details.get('database_order_id', 'N/A')}")

                order_summary = order_details.get('order_summary', order_details)
                return {
                    'success': True,
                    'message': f"🎉 Order placed successfully! Your order ID is {order_id}",
                    'action': 'order_placed',
                    'order_id': order_id,
                    'order_summary': self._format_placed_order_summary(order_summary),
                    'next_actions': ['Track order', 'Continue shopping', 'View order details']
                }
            else:
                return {
                    'success': False,
                    'message': f"Order placement failed: {error}",
                    'action': 'order_failed'
                }

        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return {
                'success': False,
                'message': "Error placing your order. Please try again or contact support!",
                'action': 'order_error'
            }

    def get_order_status(self, customer_id: int, order_id: str = None) -> Dict[str, Any]:
        """📦 Get order status and tracking"""
        try:
            if order_id:
                # Get specific order
                status_result = self.order_system.get_order_status(order_id, customer_id)
                if status_result['success']:
                    return {
                        'success': True,
                        'message': "Order found! 📦",
                        'action': 'order_status_found',
                        'order_details': status_result['order']
                    }
                else:
                    return {
                        'success': False,
                        'message': "Order not found or access denied. 😕",
                        'action': 'order_not_found'
                    }
            else:
                # Get recent orders
                orders_result = self.order_system.get_customer_orders(customer_id, limit=5)
                if orders_result['success'] and orders_result['orders']:
                    return {
                        'success': True,
                        'message': f"Found {len(orders_result['orders'])} recent orders! 📋",
                        'action': 'orders_found',
                        'orders': orders_result['orders']
                    }
                else:
                    return {
                        'success': True,
                        'message': "No orders found. Start shopping to place your first order! 🛍️",
                        'action': 'no_orders'
                    }

        except Exception as e:
            logger.error(f"❌ Error getting order status: {e}")
            return {
                'success': False,
                'message': "Error retrieving order information. Please try again!",
                'action': 'status_error'
            }

    def process_shopping_conversation(
        self,
        user_message: str,
        customer_id: int,
        session_id: str,
        current_session_state: Optional[SessionState] = None
    ) -> Dict[str, Any]:
        """🎯 Process shopping conversation with intelligent context awareness using passed SessionState"""

        # 🔧 CRITICAL FIX: Store session information for context tracking
        self._current_session_id = session_id
        self._current_customer_id = customer_id

        # 🔧 CRITICAL FIX: Set session context for product extraction
        self._current_session_id = session_id
        self._current_customer_id = customer_id

        active_session_state = self._get_or_initialize_session_state(session_id, customer_id, current_session_state)
        active_session_state.current_intent = user_message

        try:
            intent_data = self.parse_order_intent(user_message)
            intent = intent_data['intent']
            entities = intent_data.get('entities', {})
            active_session_state.current_intent = intent

            logger.info(f"🛒 Processing shopping intent: {intent} for customer {customer_id}, session {session_id}, stage: {active_session_state.conversation_stage}")

            response_data = {'success': False, 'message': "Could not process your request.", 'action': intent}

            if intent == 'product_inquiry':
                # Show product details and ask for confirmation (don't auto-add to cart)
                product_name_from_intent = entities.get('product_name')
                product_info = self.extract_product_info(user_message, product_name_hint=product_name_from_intent)

                if product_info and product_info.get('product_id'):
                    if product_info.get('stock_quantity', 0) > 0:
                        # Store the product for potential future reference
                        active_session_state.last_product_mentioned = product_info
                        active_session_state.conversation_stage = 'product_discussed'

                                                # Format world-class product response
                        price_formatted = f"₦{product_info['price']:,.0f}" if product_info.get('price') else "Price not available"
                        stock_count = product_info.get('stock_quantity', 0)

                        # World-class response template
                        if product_info.get('world_class_response'):
                            # Enhanced response for dynamic discovery
                            popularity_text = "It's a popular choice among our customers" if product_info.get('is_popular') else "It's available"

                            base_message = f"We have **{product_info['product_name']}** available for {price_formatted}. {popularity_text}, and we currently have {stock_count} units in stock."

                            # Add alternatives if available
                            alternatives = product_info.get('alternatives', [])
                            if alternatives:
                                alt_names = [alt['product_name'] for alt in alternatives[:2]]
                                alt_text = f"\n\n📱 **Similar options**: {', '.join(alt_names)}"
                                base_message += alt_text

                            base_message += f"\n\nWould you like to add this to your cart or explore other options on raqibtech.com?"

                        else:
                            # Legacy response with customer education
                            education_message = ""
                            if product_info.get('customer_education'):
                                education_message = f"\n\n💡 **Note**: {product_info['customer_education']}"

                            base_message = f"We have **{product_info['product_name']}** available for {price_formatted}. It's in stock with {stock_count} units available.{education_message}\n\nWould you like to add this to your cart or explore other options on raqibtech.com?"

                        response_data.update({
                            'success': True,
                            'message': base_message,
                            'action': 'product_details_shown',
                            'product_info': product_info
                        })
                    else:
                        response_data.update({
                            'success': True,
                            'message': f"😔 Sorry, {product_info['product_name']} is currently out of stock.",
                            'action': 'product_out_of_stock'
                        })
                        active_session_state.last_product_mentioned = product_info
                else:
                    response_data.update({
                        'success': True,
                        'message': "🤔 I couldn't find that specific product. Can you try being more specific or browse our catalog?",
                        'action': 'product_not_found'
                    })

            elif intent == 'add_to_cart':
                product_name_from_intent = entities.get('product_name')

                # 🔧 CRITICAL FIX: Check for pronoun usage and use session context
                pronouns = ['it', 'this', 'that', 'them']
                user_message_lower = user_message.lower().strip()

                # If user used a pronoun and we have last mentioned product in session, use it
                if (any(pronoun in user_message_lower.split()[:2] for pronoun in pronouns) and
                    active_session_state.last_product_mentioned and
                    active_session_state.last_product_mentioned.get('product_id')):

                    logger.info(f"🎯 PRONOUN RESOLUTION: Using session context product: {active_session_state.last_product_mentioned.get('product_name')}")
                    product_info = active_session_state.last_product_mentioned
                else:
                    product_info = self.extract_product_info(user_message, product_name_hint=product_name_from_intent)

                if product_info and product_info.get('product_id'):
                    if product_info.get('stock_quantity', 0) > 0:
                        existing_item = next((item for item in active_session_state.cart_items if item['product_id'] == product_info['product_id']), None)
                        if existing_item:
                            existing_item['quantity'] += 1
                            existing_item['subtotal'] = existing_item['price'] * existing_item['quantity']
                        else:
                            active_session_state.cart_items.append({
                                'product_id': product_info['product_id'],
                                'product_name': product_info['product_name'],
                                'price': float(product_info['price']),
                                'quantity': 1,
                                'subtotal': float(product_info['price'])
                            })
                        active_session_state.last_product_mentioned = product_info
                        active_session_state.conversation_stage = 'cart_updated'
                        response_data.update({
                            'success': True,
                            'message': f"✅ Added {product_info['product_name']} to your cart!",
                            'action': 'add_to_cart_success',
                            'product_added': product_info
                        })
                    else:
                        response_data['message'] = f"😔 Sorry, {product_info['product_name']} is currently out of stock."
                        active_session_state.last_product_mentioned = product_info
                else:
                    response_data['message'] = "🤔 I couldn't find that specific product. Can you try naming it again or browse our catalog? Please mention the specific product name you'd like to add."
                    response_data['action'] = 'need_product_clarification'
                    response_data['require_specific_product'] = True  # Flag to prevent AI hallucination

            elif intent == 'view_cart':
                if active_session_state.cart_items:
                    response_data.update({
                        'success': True,
                        'message': "🛒 Here's what's in your cart:",
                        'action': 'cart_displayed',
                    })
                else:
                    response_data.update({
                        'success': True,
                        'message': "🛒 Your cart is currently empty!",
                        'action': 'empty_cart',
                    })

            elif intent == 'clear_cart':
                active_session_state.cart_items = []
                active_session_state.conversation_stage = 'cart_cleared'
                response_data.update({
                    'success': True,
                    'message': "🗑️ Your cart has been cleared! Start fresh with your shopping.",
                    'action': 'cart_cleared',
                })

            # 🆕 NEW: Account management intents (redirect to general query processing)
            elif intent == 'account_management':
                response_data.update({
                    'success': True,
                    'message': "I understand you want to update your account details. Let me help you with that.",
                    'action': 'redirect_to_account_management',
                    'should_redirect': True  # Signal to main app to handle via general query processing
                })

            elif intent == 'view_address':
                response_data.update({
                    'success': True,
                    'message': "I'll help you view your delivery address information.",
                    'action': 'redirect_to_address_viewing',
                    'should_redirect': True  # Signal to main app to handle via general query processing
                })

            elif intent == 'set_delivery_address':
                address_entity = entities.get('delivery_address')
                if address_entity and isinstance(address_entity, dict) and address_entity.get('full_address'):
                    active_session_state.delivery_address = address_entity
                    active_session_state.conversation_stage = 'address_set'
                    response_data.update({
                        'success': True,
                        'message': f"✅ Delivery address updated to: {address_entity['full_address']}",
                        'action': 'delivery_address_set',
                        'delivery_address': address_entity
                    })
                elif user_message.lower() in ["yes", "yeah", "ok"] and active_session_state.conversation_stage == 'awaiting_address_confirmation' and active_session_state.delivery_address:
                    active_session_state.conversation_stage = 'address_set'
                    response_data.update({
                        'success': True,
                        'message': f"✅ Great! Using delivery address: {active_session_state.delivery_address.get('full_address', 'Saved Address')}",
                        'action': 'delivery_address_confirmed'
                    })
                else:
                    response_data['message'] = "🤔 I didn't catch that address. Could you please provide it again? e.g., 'Deliver to 123 Main St, Lagos'"
                    response_data['action'] = 'need_address_clarification'

            elif intent == 'payment_method_selection':
                payment_method_entity = entities.get('payment_method')
                if payment_method_entity:
                    # Map normalized payment methods to PaymentMethod enum values
                    payment_method_mapping = {
                        'RaqibTechPay': 'RaqibTechPay',
                        'Pay on Delivery': 'Pay on Delivery',
                        'Card Payment': 'Card',
                        'Bank Transfer': 'Bank Transfer'
                    }
                    mapped_payment_method = payment_method_mapping.get(payment_method_entity, payment_method_entity)

                    if any(pm.value.lower() == mapped_payment_method.lower() for pm in PaymentMethod):
                        active_session_state.payment_method = mapped_payment_method
                        active_session_state.conversation_stage = 'payment_method_set'
                        response_data.update({
                            'success': True,
                            'message': f"✅ Payment method set to: {payment_method_entity}",  # Show user-friendly name
                            'action': 'payment_method_set',
                            'payment_method': payment_method_entity
                        })
                    else:
                        response_data['message'] = f"🤔 '{payment_method_entity}' is not a recognized payment method. Please choose from RaqibTechPay, Pay on Delivery, Card, or Bank Transfer."
                        response_data['action'] = 'need_payment_clarification'
                elif user_message.lower() in ["yes", "yeah", "ok"] and active_session_state.conversation_stage == 'awaiting_payment_confirmation' and active_session_state.payment_method:
                    active_session_state.conversation_stage = 'payment_method_set'
                    response_data.update({
                        'success': True,
                        'message': f"✅ Understood! Using payment method: {active_session_state.payment_method}",
                        'action': 'payment_method_confirmed'
                    })
                else:
                    response_data['message'] = "🤔 Which payment method would you like to use? (RaqibTechPay, Pay on Delivery, Card, Bank Transfer)"
                    response_data['action'] = 'need_payment_clarification'

            elif intent == 'checkout' or intent == 'place_order' or \
                 (intent == 'affirmative_confirmation' and active_session_state.conversation_stage in ['awaiting_order_confirmation', 'checkout_summary_shown', 'payment_method_set', 'address_set']):
                checkout_result = self.progressive_checkout(user_message, customer_id, active_session_state)
                response_data.update(checkout_result)

            elif intent == 'affirmative_confirmation':
                logger.info(f"Affirmative confirmation. Current stage: {active_session_state.conversation_stage}")
                action_taken = False

                # 🔧 CRITICAL FIX: Handle checkout flow confirmations FIRST (prioritize checkout flow)
                if active_session_state.conversation_stage == 'awaiting_address_confirmation' and active_session_state.delivery_address:
                    active_session_state.conversation_stage = 'address_set'
                    checkout_result = self.progressive_checkout(user_message, customer_id, active_session_state)
                    response_data.update(checkout_result)
                    response_data['message'] = f"✅ Address confirmed! " + response_data.get('message', '')
                    action_taken = True

                elif active_session_state.conversation_stage == 'awaiting_payment_confirmation' and active_session_state.payment_method:
                    active_session_state.conversation_stage = 'payment_method_set'
                    checkout_result = self.progressive_checkout(user_message, customer_id, active_session_state)
                    response_data.update(checkout_result)
                    response_data['message'] = f"✅ Payment confirmed! " + response_data.get('message', '')
                    action_taken = True

                elif active_session_state.conversation_stage == 'awaiting_order_confirmation':
                    logger.info("Affirmative for order confirmation. Proceeding to place order.")
                    checkout_result = self.progressive_checkout(user_message, customer_id, active_session_state)
                    response_data.update(checkout_result)
                    action_taken = True

                # Handle general checkout progression when user says "yes" during checkout flow
                elif active_session_state.conversation_stage in ['address_set_need_payment', 'checkout_initiated_need_address']:
                    checkout_result = self.progressive_checkout(user_message, customer_id, active_session_state)
                    response_data.update(checkout_result)
                    action_taken = True

                # Handle "yes, add to cart" context-aware responses
                elif active_session_state.last_product_mentioned and active_session_state.conversation_stage in ['browsing', 'product_discussed']:
                    logger.info(f"🎯 CONTEXT-AWARE ADD TO CART: Using last mentioned product: {active_session_state.last_product_mentioned.get('product_name')}")
                    product_info = active_session_state.last_product_mentioned

                    if product_info and product_info.get('product_id'):
                        if product_info.get('stock_quantity', 0) > 0:
                            existing_item = next((item for item in active_session_state.cart_items if item['product_id'] == product_info['product_id']), None)
                            if existing_item:
                                existing_item['quantity'] += 1
                                existing_item['subtotal'] = existing_item['price'] * existing_item['quantity']
                            else:
                                active_session_state.cart_items.append({
                                    'product_id': product_info['product_id'],
                                    'product_name': product_info['product_name'],
                                    'price': float(product_info['price']),
                                    'quantity': 1,
                                    'subtotal': float(product_info['price'])
                                })
                            active_session_state.conversation_stage = 'cart_updated'
                            response_data.update({
                                'success': True,
                                'message': f"✅ Added {product_info['product_name']} to your cart!",
                                'action': 'add_to_cart_success',
                                'product_added': product_info
                            })
                            action_taken = True
                        else:
                            response_data['message'] = f"😔 Sorry, {product_info['product_name']} is currently out of stock."
                            action_taken = True

                if not action_taken: # Generic "yes", unsure what it's for
                    response_data['message'] = "Okay! What would you like to do next? You can view your cart, add more items, or ask for help."
                    response_data['action'] = 'generic_affirmation'

            elif intent == 'negative_rejection':
                logger.info(f"Negative rejection. Current stage: {active_session_state.conversation_stage}")
                if active_session_state.conversation_stage == 'awaiting_address_confirmation':
                    active_session_state.delivery_address = None
                    active_session_state.conversation_stage = 'checkout_initiated_need_address'
                    response_data['message'] = "Okay, what is the correct delivery address then?"
                    response_data['action'] = 'address_rejected_need_new'
                elif active_session_state.conversation_stage == 'awaiting_payment_confirmation':
                    active_session_state.payment_method = None
                    active_session_state.conversation_stage = 'address_set_need_payment'
                    response_data['message'] = "Alright, which payment method would you prefer?"
                    response_data['action'] = 'payment_rejected_need_new'
                elif active_session_state.conversation_stage == 'awaiting_order_confirmation':
                    active_session_state.conversation_stage = 'checkout_summary_shown' # Or perhaps 'cart_updated' to allow cart changes
                    response_data['message'] = "Okay, order cancelled. You can view your cart, add/remove items, or change delivery/payment details."
                    response_data['action'] = 'order_confirmation_rejected'
                else:
                    response_data['message'] = "Alright. How can I help you then? You can view products or ask about your cart."
                    response_data['action'] = 'generic_rejection'
                self._save_session_state(session_id, active_session_state) # Save state after rejection handling

            else: # General inquiry or unhandled shopping intent
                response_data['message'] = "I can help with shopping! You can add items, view your cart, or checkout."
                response_data['action'] = 'general_shopping_prompt'
                # No specific state change, but state is saved at the end of the method

            if response_data['success'] and active_session_state.cart_items:
                 cart_total_items = sum(item['quantity'] for item in active_session_state.cart_items)
                 cart_subtotal = sum(item['subtotal'] for item in active_session_state.cart_items)
                 cart_summary_dict = {
                     'items': active_session_state.cart_items,
                     'total_items': cart_total_items,
                     'subtotal': cart_subtotal,
                     'subtotal_formatted': f"₦{cart_subtotal:,.2f}"  # Direct formatting instead of order_system.format_price
                 }
                 response_data['cart_summary'] = cart_summary_dict

            self._save_session_state(session_id, active_session_state)
            return response_data

        except Exception as e:
            logger.error(f"❌ Error in process_shopping_conversation: {e}", exc_info=True)
            if 'active_session_state' in locals() and active_session_state:
                self._save_session_state(session_id, active_session_state)
            return {'success': False, 'message': f"An internal error occurred: {str(e)}", 'action': 'system_error'}

    def progressive_checkout(self, user_message: str, customer_id: int, session_state: SessionState) -> Dict[str, Any]:
        """
        🧠 Manages the progressive checkout flow based on current SessionState.
        This method will now primarily use the passed session_state.
        """
        action_result = {'success': False, 'message': "Let's get your order ready!", 'action': 'checkout_progress'}

        if not self.order_system:
            return {'success': False, 'message': "Order system is currently unavailable.", 'action': 'system_error'}

        # 🎯 FIXED: Handle "order_placed" stage properly - don't show annoying empty cart message
        if session_state.conversation_stage == 'order_placed':
            # Customer just placed an order successfully, provide helpful message instead of "cart is empty"
            last_order_id = session_state.checkout_state.get('last_order_id', 'Unknown') if session_state.checkout_state else 'Unknown'
            return {
                'success': True,
                'message': f"✅ Your order {last_order_id} was already placed successfully! 🎉\n\n🛍️ Want to start a new order? Just tell me what you'd like to buy!",
                'action': 'order_already_placed',
                'order_id': last_order_id
            }

        # Use passed session_state for cart items
        if not session_state.cart_items:
            session_state.conversation_stage = 'cart_empty_checkout_attempt'
            self._save_session_state(session_state.session_id, session_state) # Save updated stage
            return {'success': False, 'message': "Your cart is empty! Please add some products first. 🛒", 'action': 'empty_cart'}

        # 1. Check/Get Delivery Address from session_state
        if not session_state.delivery_address:
            intent_data = self.parse_order_intent(user_message)
            if intent_data['intent'] == 'set_delivery_address' and intent_data['entities'].get('delivery_address'):
                addr_entity = intent_data['entities']['delivery_address']
                session_state.delivery_address = addr_entity
                session_state.conversation_stage = 'address_set'
                logger.info(f"🚚 Address parsed during checkout: {addr_entity.get('full_address')}")
                self._save_session_state(session_state.session_id, session_state) # Save
                # Fall through to payment check
            else:
                # Try to get saved address for customer
                saved_address = self._get_customer_address(customer_id)
                if saved_address:
                    session_state.delivery_address = saved_address # Tentatively set, user needs to confirm
                    session_state.conversation_stage = 'awaiting_address_confirmation'
                    action_result.update({
                        'success': True,  # This is a successful checkout step, not a failure
                        'message': f"🚚 Should I use your saved address: {saved_address['full_address']} for delivery?",
                        'action': 'confirm_delivery_address'
                    })
                    self._save_session_state(session_state.session_id, session_state) # Save state before returning
                    return action_result
                else:
                    session_state.conversation_stage = 'checkout_initiated_need_address'
                    action_result.update({
                        'success': True,  # This is a successful checkout step, not a failure
                        'message': "🚚 What is your delivery address? (e.g., '123 Main St, Ikeja, Lagos')",
                        'action': 'request_delivery_address'
                    })
                    self._save_session_state(session_state.session_id, session_state) # Save state before returning
                    return action_result

        # Ensure conversation_stage reflects address is set if we passed the above block
        if session_state.delivery_address and session_state.conversation_stage not in ['address_set', 'payment_method_set', 'awaiting_payment_confirmation', 'checkout_summary_shown', 'awaiting_order_confirmation']:
            session_state.conversation_stage = 'address_set'
            self._save_session_state(session_state.session_id, session_state)


        # 2. Check/Get Payment Method from session_state
        if not session_state.payment_method:
            intent_data = self.parse_order_intent(user_message)
            if intent_data['intent'] == 'payment_method_selection' and intent_data['entities'].get('payment_method'):
                pm_entity = intent_data['entities']['payment_method']
                if any(pm.value.lower() == pm_entity.lower() for pm in PaymentMethod):
                    session_state.payment_method = pm_entity
                    session_state.conversation_stage = 'payment_method_set'
                    logger.info(f"💳 Payment method parsed during checkout: {pm_entity}")
                    self._save_session_state(session_state.session_id, session_state)
                    # Fall through to summary/placement
                else:
                    session_state.conversation_stage = 'address_set_need_payment' # Stay here but prompt again
                    action_result.update({
                        'success': True,  # This is a successful checkout step, not a failure
                        'message': f"🤔 '{pm_entity}' isn't valid. Choose RaqibTechPay, Pay on Delivery, Card, or Bank Transfer.",
                        'action': 'request_payment_method_invalid'
                    })
                    self._save_session_state(session_state.session_id, session_state) # Save state before returning
                    return action_result
            else:
                session_state.conversation_stage = 'address_set_need_payment'
                action_result.update({
                    'success': True,  # This is a successful checkout step, not a failure
                    'message': "💳 How would you like to pay? (RaqibTechPay, Pay on Delivery, Card, or Bank Transfer)",
                    'action': 'request_payment_method'
                })
                self._save_session_state(session_state.session_id, session_state) # Save state before returning
                return action_result

        # Ensure stage reflects payment is set
        if session_state.payment_method and session_state.conversation_stage not in ['payment_method_set', 'checkout_summary_shown', 'awaiting_order_confirmation']:
             session_state.conversation_stage = 'payment_method_set'
             self._save_session_state(session_state.session_id, session_state)

        # 3. All details collected - Show summary and ask for confirmation to place order
        cart_summary_dict = {
             'items': session_state.cart_items,
             'total_items': sum(item['quantity'] for item in session_state.cart_items),
             'subtotal': sum(item['subtotal'] for item in session_state.cart_items)
        }
        order_summary_text = self.order_system.format_potential_order_summary(
            cart_summary_dict,
            session_state.delivery_address,
            session_state.payment_method
        )

        # Check if user message is an attempt to place order (e.g. "place order", "confirm")
        # or if user said "yes" and stage was awaiting_order_confirmation
        is_place_order_command = self.parse_order_intent(user_message)['intent'] == 'place_order'
        is_affirmative_confirmation_for_order = (self.parse_order_intent(user_message)['intent'] == 'affirmative_confirmation' and
                                               session_state.conversation_stage == 'awaiting_order_confirmation')


        if is_place_order_command or is_affirmative_confirmation_for_order:
            logger.info(f"Attempting to place order for customer {customer_id} based on command or confirmation.")
            # Ensure all details are present one last time
            if not (session_state.cart_items and session_state.delivery_address and session_state.payment_method):
                 logger.warning(f"Missing details for order placement: Cart: {bool(session_state.cart_items)}, Addr: {bool(session_state.delivery_address)}, PM: {bool(session_state.payment_method)}")
                 action_result['message'] = "It seems some details are still missing. Let's review. What is your delivery address?"
                 session_state.conversation_stage = 'checkout_initiated_need_address' # Restart collection
                 session_state.delivery_address = None # Clear to re-prompt
                 session_state.payment_method = None # Clear to re-prompt
                 self._save_session_state(session_state.session_id, session_state)
                 action_result['action'] = 'request_delivery_address' # Go back to address collection
                 return action_result

            order_id, order_details, error = self.order_system.place_order(
                customer_id=customer_id,
                cart_items=session_state.cart_items,
                delivery_address=session_state.delivery_address,
                payment_method=session_state.payment_method,
                notes="Order placed via AI Assistant"
            )
            if order_id:
                session_state.cart_items = [] # Clear cart in current state
                session_state.conversation_stage = 'order_placed'
                session_state.checkout_state = {'last_order_id': order_id, 'details': order_details}
                action_result.update({
                    'success': True,
                    'message': f"🎉 Your order {order_id} has been placed successfully!",
                    'action': 'order_placed',
                    'order_id': order_id,
                    'order_summary': self.order_system.format_order_summary(order_details)
                })
            else:
                action_result.update({
                'success': False,
                    'message': f"💥 Error placing order: {error}. Please check details or try again.",
                    'action': 'order_placement_failed'
                })
        else:
            # Not a direct place order command, so show summary and await confirmation
            session_state.conversation_stage = 'awaiting_order_confirmation'
            action_result.update({
                'success': True, # Success in reaching this stage
                'message': f"📝 **Order Summary:**\\n{order_summary_text}\\n\\nIs everything correct? Say 'yes' to place your order or tell me what to change.",
                'action': 'confirm_order_details'
            })

        self._save_session_state(session_state.session_id, session_state) # Save final stage before returning
        return action_result

    def _get_or_initialize_session_state(self, session_id: str, customer_id: Optional[int], existing_state: Optional[SessionState]) -> SessionState:
        """ Helper to get existing session state or initialize a new one. """
        if existing_state:
            logger.info(f"🧠 Using existing session state for session {session_id}, stage: {existing_state.conversation_stage}")
            return existing_state

        logger.info(f"🧠 No existing session state passed for {session_id}, attempting to fetch or create new.")
        state_from_mem = self.memory_system.get_session_state(session_id)
        if state_from_mem:
            logger.info(f"🧠 Fetched session state from memory for session {session_id}, stage: {state_from_mem.conversation_stage}")
            return state_from_mem

        logger.info(f"🧠 Initializing new session state for session {session_id}")

        # 🔧 CRITICAL FIX: Try to retrieve last mentioned product from conversation context
        last_product_context = None
        try:
            # Get conversation memory from enhanced_db_querying system
            from .enhanced_db_querying import EnhancedDatabaseQuerying
            enhanced_db = EnhancedDatabaseQuerying()
            user_id = f"customer_{customer_id}" if customer_id else "anonymous"

            # First try the new dedicated method for last mentioned product
            if hasattr(enhanced_db, 'get_last_mentioned_product'):
                last_product_context = enhanced_db.get_last_mentioned_product(user_id, session_id)
                if last_product_context:
                    logger.info(f"🧠 RETRIEVED LAST PRODUCT FROM NEW METHOD: {last_product_context.get('product_name')}")

            # Fallback to enhanced conversation memory if needed
            if not last_product_context and hasattr(enhanced_db, 'get_enhanced_conversation_memory'):
                conversation_memory = enhanced_db.get_enhanced_conversation_memory(user_id, session_id, limit=5)

                # Look for the most recent product mentioned in conversation context
                if conversation_memory and conversation_memory.get('mentioned_products') and len(conversation_memory['mentioned_products']) > 0:
                    last_product_context = conversation_memory['mentioned_products'][0]  # Most recent
                    logger.info(f"🧠 RETRIEVED PRODUCT CONTEXT: {last_product_context.get('product_name')} from conversation memory")

                # Also check session state from conversation memory
                session_state_data = conversation_memory.get('session_state', {}) if conversation_memory else {}
                if not last_product_context and session_state_data.get('last_mentioned_product'):
                    last_product_context = session_state_data['last_mentioned_product']
                    logger.info(f"🧠 RETRIEVED PRODUCT CONTEXT: {last_product_context.get('product_name')} from session state")

        except Exception as e:
            logger.warning(f"⚠️ Failed to retrieve product context from conversation memory: {e}")

        return SessionState(
            session_id=session_id,
            customer_id=customer_id,
            cart_items=[],
            checkout_state={},
            current_intent='initial',
            last_product_mentioned=last_product_context,
            delivery_address=None,
            payment_method=None,
            conversation_stage='product_discussed' if last_product_context else 'browsing',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def _save_session_state(self, session_id: str, session_state: SessionState):
        """ Helper to save the session state using the memory system. """
        session_state.updated_at = datetime.now()
        logger.info(f"🧠 Saving session state for {session_id}, stage: {session_state.conversation_stage}, cart: {len(session_state.cart_items)} items.")
        self.memory_system.update_session_state(session_id, asdict(session_state))

    def _parse_nigerian_address(self, address_text: str) -> Tuple[str, str, str]:
        # This is a placeholder implementation. A real implementation would parse the address
        # and return the components (full_address, city, state). For now, we'll return a default.
        return ("1 RaqibTech Avenue", "Lagos", "Lagos")

    def get_order_history(self, customer_id: int) -> Dict[str, Any]:
        # This method is not provided in the original file or the new implementation
        # It's assumed to exist as it's called in the process_shopping_conversation method
        # A placeholder implementation is provided
        return {"orders": []}

    def _get_customer_address(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Get customer's default address from database"""
        try:
            db_manager = initialize_database()
            with db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT address, state, lga
                        FROM customers
                        WHERE customer_id = %s
                    """, (customer_id,))

                    result = cursor.fetchone()
                    if result and result['address']:
                        # Parse the address components
                        full_address = result['address']
                        state = result['state'] or 'Lagos'  # Default to Lagos if null
                        lga = result['lga'] or 'Unknown'

                        return {
                            'full_address': full_address,
                            'city': lga,
                            'state': state,
                            'raw': full_address
                        }
                    return None
        except Exception as e:
            logger.error(f"❌ Error getting customer address: {e}")
            return None

    def _format_placed_order_summary(self, order_summary: Any) -> str:
        """🎉 Format order confirmation with actual product details"""
        try:
            # Handle different order_summary formats
            if hasattr(order_summary, 'items') and order_summary.items:
                # Handle OrderSummary object with items
                items_text = ""
                for item in order_summary.items:
                    if hasattr(item, 'product_name'):
                        items_text += f"• {item.product_name} x{item.quantity} - ₦{item.subtotal:,.2f}\n"
                    else:
                        items_text += f"• {item.get('product_name', 'Product')} x{item.get('quantity', 1)} - ₦{item.get('subtotal', 0):,.2f}\n"

                order_id = getattr(order_summary, 'order_id', 'Unknown')
                total_amount = getattr(order_summary, 'total_amount', 0)
                payment_method = getattr(order_summary, 'payment_method', 'Not specified')
                delivery_info = getattr(order_summary, 'delivery_info', None)

                delivery_str = "Not specified"
                if delivery_info:
                    if hasattr(delivery_info, 'full_address'):
                        delivery_str = delivery_info.full_address
                    elif hasattr(delivery_info, 'state'):
                        delivery_str = f"{delivery_info.state}, Nigeria"

            elif isinstance(order_summary, dict):
                # Handle dictionary format
                items_text = ""
                items = order_summary.get('items', order_summary.get('order_items', []))

                for item in items:
                    if isinstance(item, dict):
                        product_name = item.get('product_name', 'Product')
                        quantity = item.get('quantity', 1)
                        subtotal = item.get('subtotal', item.get('price', 0))
                        items_text += f"• {product_name} x{quantity} - ₦{subtotal:,.2f}\n"
                    else:
                        # Handle object items
                        items_text += f"• {getattr(item, 'product_name', 'Product')} x{getattr(item, 'quantity', 1)} - ₦{getattr(item, 'subtotal', 0):,.2f}\n"

                order_id = order_summary.get('order_id', 'Unknown')
                total_amount = order_summary.get('total_amount', 0)
                payment_method = order_summary.get('payment_method', 'Not specified')
                delivery_info = order_summary.get('delivery_info', order_summary.get('delivery_address', 'Not specified'))

                delivery_str = str(delivery_info) if delivery_info else "Not specified"

            else:
                # Fallback for unexpected formats
                logger.warning(f"Unexpected order_summary format: {type(order_summary)}")
                return f"🎉 Order {getattr(order_summary, 'order_id', 'Unknown')} placed successfully! ₦{getattr(order_summary, 'total_amount', 0):,.2f}"

            # Format the payment method properly
            if hasattr(payment_method, 'value'):
                payment_method_str = payment_method.value
            elif hasattr(payment_method, 'name'):
                payment_method_str = payment_method.name
            else:
                payment_method_str = str(payment_method)

            summary = f"""🎉 **Order Confirmation**

📋 Order ID: {order_id}
{items_text}
💰 Total: ₦{float(total_amount):,.2f}
📍 Delivery: {delivery_str}
💳 Payment: {payment_method_str}
📦 Status: Pending

Your order has been successfully placed! 🚀
We'll send you updates as it progresses.

🎯 **What's next?**
• Track your order status
• Continue shopping
• Contact support if needed

Thank you for shopping with raqibtech.com! 💙"""

            return summary.strip()

        except Exception as e:
            logger.error(f"❌ Error formatting placed order summary: {e}")
            # Provide a safe fallback
            order_id = getattr(order_summary, 'order_id', 'Unknown') if hasattr(order_summary, 'order_id') else order_summary.get('order_id', 'Unknown')
            total_amount = getattr(order_summary, 'total_amount', 0) if hasattr(order_summary, 'total_amount') else order_summary.get('total_amount', 0) if isinstance(order_summary, dict) else 0

            return f"""🎉 **Order Confirmation**

📋 Order ID: {order_id}
💰 Total: ₦{float(total_amount):,.2f}
📦 Status: Pending

Your order has been successfully placed! 🚀
We'll send you updates as it progresses.

Thank you for shopping with raqibtech.com! 💙"""

    def _get_cart_summary(self, cart: Dict) -> Dict[str, Any]:
        """📋 Generate cart summary from cart data"""
        return {
            'items': cart['items'],
            'total_items': sum(item['quantity'] for item in cart['items']),
            'subtotal': cart['subtotal'],
            'subtotal_formatted': f"₦{cart['subtotal']:,.2f}"
        }

    def _format_order_summary(self, calculation: Dict) -> str:
        """💰 Format order calculation into readable summary"""
        try:
            if calculation.get('success'):
                return f"""
💰 **Order Summary**
• Subtotal: ₦{calculation.get('subtotal', 0):,.2f}
• Delivery: ₦{calculation.get('delivery_fee', 0):,.2f}
• Total: ₦{calculation.get('total_amount', 0):,.2f}
"""
            else:
                return f"Error calculating order: {calculation.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error formatting summary: {str(e)}"



# Global instance for use in Flask app
# Note: This will be created with a memory system when needed
# For now, we'll make it None to avoid import errors
order_ai_assistant = None

def get_order_ai_assistant():
    """Factory function to get OrderAIAssistant instance with proper memory system"""
    global order_ai_assistant
    if order_ai_assistant is None:
        try:
            from .conversation_memory_system import world_class_memory
            order_ai_assistant = OrderAIAssistant(world_class_memory)
        except ImportError:
            # Fallback: create a basic memory system if import fails
            try:
                from conversation_memory_system import world_class_memory
                order_ai_assistant = OrderAIAssistant(world_class_memory)
            except ImportError:
                # Last resort: create OrderAIAssistant with None (will need to handle this in __init__)
                logger.warning("⚠️ Could not import world_class_memory, creating OrderAIAssistant without memory system")
                order_ai_assistant = OrderAIAssistant(None)
    return order_ai_assistant
