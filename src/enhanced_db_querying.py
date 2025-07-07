"""
🚀 Advanced Database Querying and Nigerian Customer Support System
================================================================================

Intelligent Customer Support for Nigerian E-commerce Platform with:
1. Natural Language Query Processing
2. Context-Aware Conversation Management
3. Nigerian Cultural and Regional Intelligence
4. Emotional Intelligence and Empathy
5. Multi-language Support (English + Nigerian Pidgin)
6. 🆕 ACTUAL ORDER PLACEMENT AND SHOPPING ASSISTANCE
7. Account Tier Management and Progression
8. Real-time Analytics and Business Intelligence

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from groq import Groq
import logging
import decimal
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app_logger as an alias to logger for compatibility
app_logger = logger

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

class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime and decimal objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DateTimeJSONEncoder, self).default(obj)

def safe_json_dumps(obj, max_items=5):
    """Safely serialize objects to JSON, handling datetime and limiting items"""
    try:
        # If it's a list, limit the number of items
        if isinstance(obj, list):
            limited_obj = obj[:max_items]
        else:
            limited_obj = obj

        return json.dumps(limited_obj, cls=DateTimeJSONEncoder, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        logger.warning(f"⚠️ JSON serialization fallback: {e}")
        return str(limited_obj)

# Nigerian States for context awareness
NIGERIAN_STATES = [
    'Lagos', 'Kano', 'Rivers', 'Oyo', 'Kaduna', 'Abia', 'Adamawa', 'Akwa Ibom',
    'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno', 'Cross River', 'Delta',
    'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Gombe', 'Imo', 'Jigawa', 'Kebbi',
    'Kogi', 'Kwara', 'Nasarawa', 'Niger', 'Ondo', 'Osun', 'Ogun', 'Plateau',
    'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'Abuja'
]

# Nigerian Payment Methods
NIGERIAN_PAYMENT_METHODS = [
    'Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'
]

# # 🆕 PRODUCT CATEGORIES for Nigerian E-commerce
# NIGERIAN_PRODUCT_CATEGORIES = [
#     'Electronics', 'Fashion', 'Beauty', 'Computing', 'Automotive', 'Books'
# ]

# 🆕 PRODUCT CATEGORIES for Nigerian E-commerce
NIGERIAN_PRODUCT_CATEGORIES = [
    'Automotive', 'Beauty', 'Books', 'Computing', 'Electronics', 'Fashion', 'Food Items', 'Home & Kitchen',
]

# 🆕 POPULAR BRANDS in Nigerian Market
NIGERIAN_POPULAR_BRANDS = [
    'Samsung', 'Apple', 'Tecno', 'Infinix', 'LG', 'Sony', 'Haier Thermocool', 'Scanfrost',
    'Nike', 'Adidas', 'Zara', 'MAC Cosmetics', 'Maybelline', 'L\'Oreal', 'HP', 'Dell',
    'Canon', 'Logitech', 'Mobil 1', 'Exide', 'Dunlop', 'Bosch', 'Philips'
]

class QueryType(Enum):
    """Query classification types"""
    CUSTOMER_ANALYSIS = "customer_analysis"
    ORDER_ANALYTICS = "order_analytics"
    CUSTOMER_SUPPORT = "customer_support"  # NEW: Customer support queries
    REVENUE_INSIGHTS = "revenue_insights"
    GEOGRAPHIC_ANALYSIS = "geographic_analysis"
    PRODUCT_PERFORMANCE = "product_performance"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    GENERAL_CONVERSATION = "general_conversation"
    PRODUCT_INFO_GENERAL = "product_info_general"
    SHOPPING_ASSISTANCE = "shopping_assistance"
    ORDER_PLACEMENT = "order_placement"
    PRODUCT_RECOMMENDATIONS = "product_recommendations"
    PRICE_INQUIRY = "price_inquiry"
    STOCK_CHECK = "stock_check"
    SHOPPING_CART = "shopping_cart"

@dataclass
class QueryContext:
    """Structured context for database queries"""
    query_type: QueryType
    intent: str
    entities: Dict[str, Any]
    sql_query: str
    execution_result: List[Dict]
    response: str
    timestamp: datetime
    user_query: str
    error_message: Optional[str] = None

class NigerianBusinessIntelligence:
    """Nigerian business context and intelligence helper"""

    @staticmethod
    def format_naira(amount: float, whatsapp_format: bool = False) -> str:
        """Format amount in Nigerian Naira with optional WhatsApp full format"""
        if whatsapp_format:
            # For WhatsApp, always use full format for better readability
            return f"₦{amount:,.0f}"
        else:
            # Original abbreviated format for other contexts
            if amount >= 1_000_000:
                return f"₦{amount/1_000_000:.1f}M"
            elif amount >= 100_000:  # 🔧 CRITICAL FIX: Only use K for amounts ≥ 100,000
                return f"₦{amount/1_000:.0f}K"
            else:
                return f"₦{amount:,.0f}"  # Show full amount for values less than 100,000

    @staticmethod
    def get_nigerian_timezone_context() -> str:
        """Get current Nigerian time context"""
        # Nigeria is UTC+1 (West Africa Time)
        now = datetime.now()
        nigerian_time = now + timedelta(hours=1)  # Approximate WAT

        return f"""
Current Date & Time Context (West Africa Time):
- Today: {nigerian_time.strftime('%A, %B %d, %Y')}
- Current Time: {nigerian_time.strftime('%I:%M %p WAT')}
- Week: Week {nigerian_time.isocalendar()[1]} of {nigerian_time.year}
- Quarter: Q{(nigerian_time.month-1)//3 + 1} {nigerian_time.year}
- Nigerian Business Hours: 8:00 AM - 6:00 PM WAT
"""

    @staticmethod
    def get_geographic_context(query: str) -> Dict[str, Any]:
        """Extract Nigerian geographic context from query"""
        context = {
            'states': [],
            'regions': [],
            'is_geographic_query': False
        }

        query_lower = query.lower()

        # Check for specific states
        for state in NIGERIAN_STATES:
            if state.lower() in query_lower:
                context['states'].append(state)
                context['is_geographic_query'] = True

        # Check for regional terms
        if any(term in query_lower for term in ['north', 'northern']):
            context['regions'].append('Northern Nigeria')
            context['is_geographic_query'] = True

        if any(term in query_lower for term in ['south', 'southern']):
            context['regions'].append('Southern Nigeria')
            context['is_geographic_query'] = True

        if any(term in query_lower for term in ['west', 'western']):
            context['regions'].append('Western Nigeria')
            context['is_geographic_query'] = True

        return context

# Import the enhanced recommendation engine
try:
    from .recommendation_engine import ProductRecommendationEngine, CustomerSupportContext
    from .order_ai_assistant import OrderAIAssistant, SessionState
    from .conversation_memory_system import world_class_memory, WorldClassMemorySystem
    from .user_roles import (
        UserRole, Permission, RoleBasedAccessControl,
        determine_user_role, get_role_appropriate_response
    )
    logger.info("✅ Successfully imported enhanced components and RBAC system")
except ImportError:
    try:
        from recommendation_engine import ProductRecommendationEngine, CustomerSupportContext
        from order_ai_assistant import OrderAIAssistant, SessionState
        from conversation_memory_system import world_class_memory, WorldClassMemorySystem
        logger.info("✅ Successfully imported enhanced components (direct)")
    except ImportError:
        logger.warning("⚠️ Enhanced components not available, using basic functionality")
        ProductRecommendationEngine = None
        CustomerSupportContext = None
        OrderAIAssistant = None

        # Mock world-class memory system
        class WorldClassMemorySystem:
            def __init__(self): pass
            def get_conversation_context(self, session_id, max_tokens=2000): return {}
            def store_conversation_turn(self, session_id, user_input, ai_response, intent, entities, session_state): return "mock_turn_id"
            def update_session_state(self, session_id, updates): return True

        world_class_memory = WorldClassMemorySystem()

class EnhancedDatabaseQuerying:
    """🚀 Advanced Nigerian E-commerce Database Querying with AI Intelligence"""

    # 🆕 OFFICIAL CUSTOMER SUPPORT CONTACT INFORMATION
    CUSTOMER_SUPPORT_CONTACTS = {
        'primary_email': 'support@raqibtech.com',
        'primary_phone': '+234 (702) 5965-922',
        'business_hours': 'Monday - Friday: 8:00 AM - 6:00 PM (WAT)',
        'emergency_support': '+234 (702) 5965-922',
        'support_portal': 'https://raqibtech.com/support',
        'live_chat': 'Available on raqibtech.com during business hours',
        'whatsapp': '+234 (702) 5965-922',
        'response_time': '24 hours for email, immediate for live chat',
        'languages': 'English, Hausa, Yoruba, Igbo'
    }

    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

        # Initialize Groq client
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

        # 🧠 Initialize World-Class Memory System
        try:
            self.memory_system = world_class_memory
            logger.info("🧠 World-Class Memory System integrated successfully")
        except Exception as e:
            logger.warning(f"⚠️ Memory system integration failed: {e}")
            self.memory_system = None

        # Initialize conversation context for legacy compatibility
        self.conversation_context = {}

        # Initialize Enhanced ProductRecommendationEngine
        try:
            from .recommendation_engine import ProductRecommendationEngine
            self.recommendation_engine = ProductRecommendationEngine()
            logger.info("✅ Enhanced ProductRecommendationEngine initialized")
        except ImportError:
            logger.warning("⚠️ Enhanced ProductRecommendationEngine not available")
            self.recommendation_engine = None

        # Initialize Order AI Assistant
        try:
            if OrderAIAssistant and self.memory_system: # Ensure memory_system is available
                self.order_ai_assistant = OrderAIAssistant(memory_system=self.memory_system) # Pass memory_system
                logger.info("✅ OrderAIAssistant initialized with memory system")
            elif OrderAIAssistant:
                logger.warning("⚠️ OrderAIAssistant initialized WITHOUT memory system due to self.memory_system not being available. This WILL cause issues.")
                self.order_ai_assistant = OrderAIAssistant(memory_system=None)
            else:
                self.order_ai_assistant = None
                logger.warning("⚠️ OrderAIAssistant class not available")
        except Exception as e:
            logger.error(f"❌ OrderAIAssistant initialization failed: {e}", exc_info=True)
            self.order_ai_assistant = None

        # Initialize Nigerian Business Intelligence
        self.ni_intelligence = NigerianBusinessIntelligence()

        # Initialize Redis for conversation memory (fallback)
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis conversation memory initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available for conversation memory: {e}")
            self.redis_client = None

        # 🔧 CRITICAL FIX: Initialize in-memory store for Redis fallback
        self._memory_store = {}

        logger.info("🚀 Enhanced Database Querying System initialized successfully")

    def classify_query_intent(self, user_query: str, conversation_history: List[Dict] = None) -> Tuple[QueryType, Dict[str, Any]]:
        """
        🎯 Enhanced query classification with cart operation detection
        """
        query_lower = user_query.lower()

        # 🔧 CRITICAL FIX: Handle order-related follow-up questions
        if conversation_history:
            # Check if the previous query was about orders
            last_turn = conversation_history[0]
            if last_turn.get('query_type') == 'ORDER_ANALYTICS' or 'order' in last_turn.get('user_query', '').lower():
                # Check if current query is asking about contents/items in the order
                order_content_keywords = [
                    'what are in', 'what is in', 'what\'s in', 'contents of', 'items in',
                    'products in', 'food items', 'what did i order', 'what did i buy',
                    'show me the items', 'list the items', 'what products',
                    'what are the items', 'what items are', 'which products',
                    'contents', 'what\'s inside', 'what am i getting'
                ]

                if any(keyword in query_lower for keyword in order_content_keywords):
                    logger.info(f"🎯 ORDER FOLLOW-UP DETECTED: User asking about order contents after order query")

                    # Initialize entities
                    entities = {
                        'order_id': None,
                        'order_content_inquiry': True,
                        'customer_id': None,
                        'product_categories': [],
                        'brands': [],
                        'product_keywords': [],
                        'price_query': False,
                        'inventory_query': False,
                        'shopping_intent': False,
                        'recommendation_intent': False,
                        'max_budget': None,
                        'delivery_date': None,
                        'payment_method': None,
                        'order_status': None,
                        'geographic_location': None,
                        'needs_customer_lookup': False
                    }

                    # Extract order ID from previous conversation
                    order_id = None
                    if 'execution_result' in last_turn and last_turn['execution_result']:
                        for result in last_turn['execution_result']:
                            if isinstance(result, dict) and 'order_id' in result:
                                order_id = result['order_id']
                                break

                    # Also check if order ID was mentioned in the response
                    if not order_id and 'response' in last_turn:
                        import re
                        order_match = re.search(r'order\s+#?(\d+)', last_turn['response'], re.IGNORECASE)
                        if order_match:
                            order_id = order_match.group(1)

                    if order_id:
                        entities['order_id'] = order_id
                        logger.info(f"🎯 CONTEXT: User asking about contents of order #{order_id}")
                        return QueryType.ORDER_ANALYTICS, entities

        # 🚨 ADMIN CONTEXT-AWARENESS FIX: Handle short, contextual follow-up queries from admins
        if conversation_history and len(user_query.split()) < 5: # Short query
            last_turn = conversation_history[0]
            if last_turn.get('query_type') in ['REVENUE_INSIGHTS', 'CUSTOMER_ANALYSIS', 'GEOGRAPHIC_ANALYSIS']:
                logger.info(f"🧠 ADMIN CONTEXT: Inheriting intent '{last_turn['query_type']}' for short follow-up query.")

                # Inherit entities but look for a new tier/category/etc. in the current query
                new_entities = last_turn.get('entities', {}).copy()

                # Example: If last query was about 'Platinum', and new is 'what of bronze'
                tier_keywords = ['platinum', 'gold', 'silver', 'bronze']
                for tier in tier_keywords:
                    if tier in query_lower:
                        new_entities['account_tier'] = tier.capitalize()
                        logger.info(f"🎯 Found new tier in follow-up: {tier.capitalize()}")
                        return QueryType(last_turn['query_type']), new_entities

                # If no specific new entity found, assume it's a continuation of the same query type
                return QueryType(last_turn['query_type']), new_entities



        # Initialize entities dictionary with all required fields
        entities = {
            'order_id': None,
            'customer_id': None,
            'product_categories': [],
            'brands': [],
            'product_keywords': [],
            'price_query': False,
            'inventory_query': False,
            'shopping_intent': False,
            'recommendation_intent': False,
            'max_budget': None,
            'delivery_date': None,
            'payment_method': None,
            'order_status': None,
            'geographic_location': None,
            'needs_customer_lookup': False
        }

        # 💰 REVENUE INSIGHTS KEYWORD-BASED DETECTION
        revenue_keywords = [
            'revenue', 'sales', 'profit', 'financial', 'performance',
            'worst performing month', 'best performing month', 'top selling',
            'highest sales', 'lowest sales', 'monthly sales'
        ]
        if any(keyword in query_lower for keyword in revenue_keywords):
            logger.info("💰 Revenue-related keyword detected. Classifying as REVENUE_INSIGHTS.")
            entities['financial_query'] = True
            return QueryType.REVENUE_INSIGHTS, entities

        # 🛒 ENHANCED CART OPERATION DETECTION
        cart_keywords = [
            'add to cart', 'add to my cart', 'add item to cart',
            'remove from cart', 'delete from cart', 'clear cart',
            'view cart', 'show cart', 'cart contents', 'what\'s in my cart',
            'update cart', 'modify cart', 'change quantity in cart'
        ]

        if any(keyword in query_lower for keyword in cart_keywords):
            logger.info(f"🛒 CART OPERATION DETECTED: Query should be handled by OrderAIAssistant, not SQL layer")
            entities['shopping_intent'] = True
            return QueryType.SHOPPING_CART, entities

        # 🛍️ Enhanced shopping intent detection
        shopping_patterns = [
            'i want to buy', 'i need to purchase', 'i\'d like to order',
            'can i buy', 'how do i buy', 'purchase', 'order now',
            'add this to', 'checkout', 'place order', 'buy this'
        ]

        if any(pattern in query_lower for pattern in shopping_patterns):
            logger.info(f"🛍️ SHOPPING INTENT DETECTED: Should be handled by OrderAIAssistant")
            entities['shopping_intent'] = True
            return QueryType.ORDER_PLACEMENT, entities

        # 🆕 TIER BENEFIT QUERIES - Handle these specially (no database query needed)
        tier_benefit_patterns = [
            'benefits of', 'what are the benefits', 'tier benefits', 'gold tier benefits',
            'silver tier benefits', 'bronze tier benefits', 'platinum tier benefits',
            'what benefits', 'membership benefits', 'tier perks', 'account tier benefits',
            'gold member benefits', 'silver member benefits', 'platinum member benefits',
            'bronze member benefits', 'what do i get', 'tier advantages', 'membership perks'
        ]

        if any(pattern in query_lower for pattern in tier_benefit_patterns):
            # Extract mentioned tier if any
            mentioned_tier = None
            tier_keywords = ['bronze', 'silver', 'gold', 'platinum']
            for tier in tier_keywords:
                if tier in query_lower:
                    mentioned_tier = tier.capitalize()
                    break

            return QueryType.GENERAL_CONVERSATION, {
                'intent': 'tier_benefits_inquiry',
                'mentioned_tier': mentioned_tier,
                'privacy_safe': True,
                'no_database_query': True
            }

        # 🆕 CUSTOMER SUPPORT CONTACT QUERIES - Handle these specially
        if any(phrase in query_lower for phrase in [
            'contact customer support', 'customer support contact', 'support contact',
            'how to contact support', 'customer service contact', 'support phone',
            'support email', 'how to reach support', 'customer care contact',
            'help desk contact', 'technical support contact'
        ]):
            return QueryType.GENERAL_CONVERSATION, {
                'intent': 'customer_support_contact_request',
                'contact_type': 'support_team',
                'privacy_safe': True,
                'no_database_query': True
            }

        # Get Nigerian business context
        geo_context = self.ni_intelligence.get_geographic_context(user_query)
        time_context = self.ni_intelligence.get_nigerian_timezone_context()

        # Enhanced context for AI classification
        system_prompt = f"""
You are an AI classifier for a Nigerian e-commerce platform (raqibtech.com). Classify user queries into appropriate categories.

Nigerian E-commerce Context:
- Platform: raqibtech.com
- Currency: Nigerian Naira (₦)
- Geographic Focus: 36 Nigerian states + FCT
- Products: 'Automotive', 'Beauty', 'Books', 'Computing', 'Electronics', 'Fashion', 'Food Items', 'Home & Kitchen',
- Payment Methods: Pay on Delivery, Bank Transfer, Card, RaqibTechPay

{time_context}

Geographic Context: {json.dumps(geo_context)}

CRITICAL PRIVACY RULE:
- NEVER classify customer support contact requests as customer_analysis
- Customer support queries should be general_conversation
- Customer data should NOT be accessed for support contact requests

Query Classification Categories:
1. CUSTOMER_ANALYSIS: Customer behavior, demographics, account tiers, purchase patterns
2. ORDER_ANALYTICS: Order status, delivery tracking, payment methods, order history
3. REVENUE_INSIGHTS: Sales data, profit analysis, financial metrics
4. GEOGRAPHIC_ANALYSIS: State-wise sales, delivery patterns, regional preferences
5. PRODUCT_PERFORMANCE: Product popularity, inventory, categories, brands
6. TEMPORAL_ANALYSIS: Time-based trends, seasonal patterns, daily/monthly stats
7. GENERAL_CONVERSATION: General questions, platform info, policies, customer support contacts
8. PRODUCT_INFO_GENERAL: Product details, prices, availability
9. SHOPPING_ASSISTANCE: Shopping guidance, product recommendations
10. ORDER_PLACEMENT: Creating orders, checkout assistance
11. PRODUCT_RECOMMENDATIONS: Personalized product suggestions
12. PRICE_INQUIRY: Price comparisons, budget queries
13. STOCK_CHECK: Inventory availability
14. SHOPPING_CART: Cart management, item additions

IMPORTANT EXAMPLES:
- "How to contact customer support" → GENERAL_CONVERSATION (NOT customer_analysis)
- "Customer support phone number" → GENERAL_CONVERSATION (NOT customer_analysis)
- "Who are your support team" → GENERAL_CONVERSATION (NOT customer_analysis)
- "Customer service contacts" → GENERAL_CONVERSATION (NOT customer_analysis)

User Query: "{user_query}"

Classify this query and extract relevant entities. Return JSON format:
{{
    "query_type": "category_name",
    "confidence": 0.0-1.0,
    "entities": {{
        "key": "value"
    }},
    "intent": "specific_intent"
}}
"""

        # 🔧 CRITICAL FIX: Conversation context extraction for customer support
        if conversation_history:
            # 🆕 ENHANCED CONTEXT EXTRACTION: Check for contextual references first
            contextual_references = ['their', 'them', 'they', 'those customers', 'these customers', 'the customers', 'those', 'these', 'too', 'also']
            is_contextual_query = any(ref in query_lower for ref in contextual_references)

            if is_contextual_query:
                logger.info(f"🔍 CONTEXTUAL REFERENCE DETECTED in query: {user_query}")

                # Look for previous business analytics query with customer results
                for conversation in conversation_history[:2]:  # Check last 2 conversations
                    if 'execution_result' in conversation and conversation['execution_result']:
                        results = conversation['execution_result']

                        # Check if previous results contain customer data
                        if results and isinstance(results, list) and len(results) > 0:
                            first_result = results[0]

                            # If previous query returned customer data (has customer_id/name)
                            if isinstance(first_result, dict) and ('customer_id' in first_result or 'name' in first_result):
                                # Extract all customer IDs from previous results
                                customer_ids = []
                                for result in results:
                                    if isinstance(result, dict) and 'customer_id' in result:
                                        customer_ids.append(result['customer_id'])

                                if customer_ids:
                                    entities['context_customer_ids'] = customer_ids  # Multiple customers
                                    entities['contextual_reference'] = True
                                    logger.info(f"🎯 CONTEXT EXTRACTED: Previous query returned {len(customer_ids)} customers: {customer_ids}")
                                    break

            # Look for customer references in recent conversation
            for conversation in conversation_history[:3]:  # Check last 3 conversations
                if 'entities' in conversation:
                    conv_entities = conversation['entities']

                    # Inherit order_id if available (for both guest and authenticated users)
                    if conv_entities.get('order_id') and not entities['order_id']:
                        entities['order_id'] = conv_entities['order_id']
                        logger.info(f"🔄 Inherited order_id from conversation history: {entities['order_id']}")

                # 🆕 NEW: Extract customer ID from conversation context for support agents
                if 'user_query' in conversation or 'query' in conversation:
                    prev_query = conversation.get('user_query', conversation.get('query', ''))
                    if prev_query:
                        # Look for customer ID patterns in previous conversation
                        import re
                        customer_match = re.search(r'customer\s+(?:id\s+)?(\d+)', prev_query.lower())
                        if customer_match and not entities.get('context_customer_id'):
                            entities['context_customer_id'] = int(customer_match.group(1))
                            logger.info(f"🔄 Extracted customer context from conversation: {entities['context_customer_id']}")

                        # 🔧 CRITICAL FIX: NEVER inherit logged-in customer_id from conversation history
                        # This was causing cross-user contamination
                        # Let the calling function handle customer_id from session instead

        # 🆕 DIRECT CUSTOMER ID EXTRACTION from current query
        import re
        # Enhanced pattern to catch various customer ID formats
        current_query_customer_patterns = [
            r'customer\s+id\s+(\d+)',          # "customer id 2"
            r'customer\s+(\d+)',               # "customer 2"
            r'customer\s*#\s*(\d+)',          # "customer #2"
            r'customer\s+number\s+(\d+)',      # "customer number 2"
            r'cust\s+(\d+)',                   # "cust 2"
        ]

        for pattern in current_query_customer_patterns:
            customer_match = re.search(pattern, query_lower)
            if customer_match and not entities.get('context_customer_id'):
                entities['context_customer_id'] = int(customer_match.group(1))
                logger.info(f"🔍 Extracted customer ID from current query: {entities['context_customer_id']}")
                break

        # 🆕 ADDITIONAL CONTEXT: If we have order_id from history but need customer_id for order history
        if entities.get('order_id') and not entities.get('customer_id') and 'history' in query_lower:
            # For order history queries, we need the customer_id associated with the order_id
            # This will be handled in SQL generation or we can mark this as needing a lookup
            entities['needs_customer_lookup'] = True
            logger.info(f"🔍 Order history query detected - will lookup customer_id for order_id: {entities['order_id']}")

        # Classify query type based on keywords - PRIORITIZE CUSTOMER_SUPPORT over CUSTOMER_ANALYSIS
        if any(keyword in query_lower for keyword in ['order', 'orders', 'purchase', 'transaction', 'history', 'delivery', 'track', 'tracking', 'where is', 'status', 'shipped', 'shipping']):
            return QueryType.ORDER_ANALYTICS, entities

        # 🆕 NEW: Customer support queries (support agents asking about customer details for support)
        elif any(keyword in query_lower for keyword in ['name of', 'customer name', 'customer details', 'payment method', 'contact information', 'address', 'phone number', 'email', 'account information', 'customer info', 'profile details', 'who is', 'customer profile', 'this customer', 'what payment', 'which customer', 'customer use', 'account tier', 'tier', 'when did', 'joined', 'products has', 'purchase history', 'buying history', 'my account', 'my tier', 'my spending', 'my profile', 'my details', 'my information', 'my orders', 'how much have i', 'total i spent', 'what i bought', 'my purchases', 'update my', 'change my', 'modify my']):
            return QueryType.CUSTOMER_SUPPORT, entities

        elif any(keyword in query_lower for keyword in ['customer', 'customers', 'profile', 'account']):
            # Removed business analytics bypass - now handled by RBAC
            if any(keyword in query_lower for keyword in ['where', 'from', 'in', 'state', 'location']):
                return QueryType.GEOGRAPHIC_ANALYSIS, entities
            else:
                return QueryType.CUSTOMER_ANALYSIS, entities

        elif any(keyword in query_lower for keyword in ['revenue', 'sales', 'money', 'naira', '₦', 'income', 'spent', 'spending', 'spend', 'total spent', 'how much', 'breakdown', 'calculation', 'calculate', 'are you sure', 'verify', 'double check', 'give me the details', 'details', 'confirm']):
            return QueryType.REVENUE_INSIGHTS, entities

        elif any(keyword in query_lower for keyword in ['product', 'category', 'item', 'goods']) or entities.get('product_categories') or entities.get('brands') or entities.get('product_keywords'):
            # 🆕 Enhanced product query detection
            if entities.get('price_query'):
                return QueryType.PRODUCT_PERFORMANCE, entities  # Price-related product queries
            elif entities.get('inventory_query'):
                return QueryType.PRODUCT_PERFORMANCE, entities  # Stock/inventory queries
            else:
                return QueryType.PRODUCT_PERFORMANCE, entities  # General product queries

        elif any(keyword in query_lower for keyword in ['time', 'date', 'period', 'trend', 'monthly', 'weekly']):
            return QueryType.TEMPORAL_ANALYSIS, entities

        # 🆕 Additional product-specific classifications
        elif any(keyword in query_lower for keyword in ['phone', 'laptop', 'computer', 'tv', 'electronics']):
            entities['product_categories'].append('Electronics')
            return QueryType.PRODUCT_PERFORMANCE, entities

        elif any(keyword in query_lower for keyword in ['dress', 'clothes', 'fashion', 'shoe', 'bag']):
            entities['product_categories'].append('Fashion')
            return QueryType.PRODUCT_PERFORMANCE, entities

        elif any(keyword in query_lower for keyword in ['beauty', 'cosmetics', 'makeup', 'cream', 'soap']):
            entities['product_categories'].append('Beauty')
            return QueryType.PRODUCT_PERFORMANCE, entities

        elif any(keyword in query_lower for keyword in ['book', 'novel', 'textbook', 'reading']):
            entities['product_categories'].append('Books')
            return QueryType.PRODUCT_PERFORMANCE, entities

        elif any(keyword in query_lower for keyword in ['car', 'auto', 'automotive', 'battery', 'tire', 'tires', 'engine']):
            entities['product_categories'].append('Automotive')
            return QueryType.PRODUCT_PERFORMANCE, entities

        else:
            return QueryType.GENERAL_CONVERSATION, entities

    def generate_sql_query(self, user_query: str, query_type: QueryType, entities: Dict[str, Any]) -> str:
        """
        🔍 Generate Nigerian context-aware SQL queries using AI
        """

        # 🚨 CRITICAL: Handle order content inquiries FIRST - bypass AI generation entirely
        if entities.get('order_content_inquiry') and entities.get('order_id'):
            order_id = entities.get('order_id')
            print_log(f"🎯 ORDER CONTENT INQUIRY: Generating enhanced order details SQL with product info for order #{order_id}", 'info')
            return f"""SELECT o.order_id, o.total_amount, o.order_status, o.payment_method, o.delivery_date, o.created_at,
                              p.product_name, p.brand, p.description, p.price as unit_price, p.category as product_category
                      FROM orders o
                      LEFT JOIN products p ON o.product_id = p.product_id
                      WHERE o.order_id = {order_id}"""

        # 🚨 EARLY INTERCEPT: Platinum tier "how much more" queries - NUCLEAR OPTION
        customer_id = entities.get('customer_id') or entities.get('context_customer_id')
        if (customer_id and 'platinum' in user_query.lower() and
            ('how much more' in user_query.lower() or 'much more' in user_query.lower() or 'need to spend' in user_query.lower())):

            print_log(f"🚨 PLATINUM TIER QUERY INTERCEPTED: Bypassing AI generation entirely", 'info')
            return f"""SELECT CASE WHEN c.account_tier = 'Platinum' THEN 0
                      ELSE GREATEST(0, 2000000 - COALESCE(SUM(o.total_amount), 0))
                      END AS amount_needed
                      FROM customers c
                      LEFT JOIN orders o ON c.customer_id = o.customer_id
                      WHERE c.customer_id = {customer_id}
                      AND (o.order_status != 'Returned' OR o.order_status IS NULL)
                      GROUP BY c.account_tier;"""

        # Get current Nigerian time context
        time_context = self.ni_intelligence.get_nigerian_timezone_context()

        # Get geographic context
        geo_context = self.ni_intelligence.get_geographic_context(user_query)

        # Database schema context

        schema_context = self._get_comprehensive_database_schema()

        system_prompt = f"""
You are a SQL expert for a Nigerian e-commerce platform. Generate ONLY the SQL query - no explanations, comments, or additional text.

{schema_context}

{time_context}

NIGERIAN BUSINESS CONTEXT:
- Currency: Nigerian Naira (₦)
- Geographic Focus: Nigerian states and LGAs
- Payment Methods: Optimized for Nigerian market
- Time Zone: West Africa Time (WAT, UTC+1)

🔍 FLEXIBLE PRODUCT SEARCH GUIDELINES:
- ALWAYS use ILIKE for product searches instead of exact matching (=)
- For category searches: Use ILIKE '%keyword%' OR search product_name ILIKE '%keyword%'
- For oil products: Search BOTH category ILIKE '%oil%' AND product_name ILIKE '%oil%'
- For cooking oil: Search product_name ILIKE '%cooking%' OR product_name ILIKE '%oil%'
- For automotive: Search category ILIKE '%automotive%' OR product_name ILIKE '%automotive%'
- Combine multiple search strategies for better results
- Examples:
  * "oil" → WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%')
  * "cooking oil" → WHERE (product_name ILIKE '%cooking%' OR product_name ILIKE '%oil%')
  * "electronics" → WHERE (category ILIKE '%electronics%' OR product_name ILIKE '%electronics%')

🛒 ENHANCED PRODUCT QUERY PATTERNS:
Instead of: WHERE category = 'Oil'
Use: WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%' OR description ILIKE '%oil%')

Instead of: WHERE category = 'Computing'
Use: WHERE (category ILIKE '%computing%' OR category ILIKE '%computer%' OR product_name ILIKE '%computer%' OR product_name ILIKE '%laptop%')
- ALWAYS use ILIKE for product searches instead of exact matching (=)
- For category searches: Use ILIKE '%keyword%' OR search product_name ILIKE '%keyword%'
- For oil products: Search BOTH category ILIKE '%oil%' AND product_name ILIKE '%oil%'
- For cooking oil: Search product_name ILIKE '%cooking%' OR product_name ILIKE '%oil%'
- For automotive: Search category ILIKE '%automotive%' OR product_name ILIKE '%automotive%'
- Combine multiple search strategies for better results
- Examples:
  * "oil" → WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%')
  * "cooking oil" → WHERE (product_name ILIKE '%cooking%' OR product_name ILIKE '%oil%')
  * "electronics" → WHERE (category ILIKE '%electronics%' OR product_name ILIKE '%electronics%')

🛒 ENHANCED PRODUCT QUERY PATTERNS:
Instead of: WHERE category = 'Oil'
Use: WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%' OR description ILIKE '%oil%')

🔒 CRITICAL PRIVACY PROTECTION RULES:
1. NEVER query the customers table for support contact information
2. If user asks for "customer support contact" or similar, return: SELECT 'PRIVACY_PROTECTED' as message;
3. Customer support queries should NOT access customer personal data
4. Support contact information is handled by application layer, not database

🚫 CRITICAL: DO NOT GENERATE QUERIES FOR THESE OPERATIONS (handled by application layer):
- Cart operations (add to cart, remove from cart, view cart)
- Order placement operations
- Shopping cart management
- Payment processing
- User authentication operations
For these operations, return: SELECT 'APPLICATION_LAYER_OPERATION' as message;

🚨 AUTHENTICATION STATE VALIDATION:
- customer_verified: {entities.get('customer_verified', False)}
- user_authenticated: {entities.get('user_authenticated', False)}
- customer_id: {entities.get('customer_id', 'None')}

🔐 ROLE-BASED ACCESS CONTROL (RBAC) CONTEXT:
- user_role: {entities.get('user_role', 'guest')}
- can_access_analytics: {entities.get('can_access_analytics', False)}
- rbac_customer_filter: {entities.get('rbac_customer_filter', 'None')}
- rbac_restrict_to_own: {entities.get('rbac_restrict_to_own', True)}
- context_customer_id: {entities.get('context_customer_id', 'None')} (customer being discussed in support conversation)
- context_customer_ids: {entities.get('context_customer_ids', 'None')} (multiple customers from previous business analytics query)
- contextual_reference: {entities.get('contextual_reference', False)} (user referring to previous query results)

🛡️ RBAC SQL GENERATION RULES:
1. For user_role='customer': ALWAYS add WHERE customer_id = {entities.get('rbac_customer_filter', 'NULL')} to queries accessing customer data
2. For user_role='guest': NO access to customer-specific data, return generic queries only
3. For user_role in ['support_agent', 'admin', 'super_admin']: Full access to all customer data
4. For support agents with context_customer_id: Use WHERE customer_id = {entities.get('context_customer_id', 'NULL')} when querying about "this customer"
5. If can_access_analytics=False: BLOCK queries for revenue, business analytics, customer rankings
6. For business analytics queries when can_access_analytics=False: Return 'SELECT 'Access Denied: Insufficient privileges for business analytics' as message;'

CRITICAL SQL GENERATION RULES:
1. Always use proper PostgreSQL syntax
2. For authenticated customers with customer_id in entities, use it directly in WHERE clauses
3. 🔧 CRITICAL: For support agents discussing specific customer(s):
   - ALWAYS prioritize context_customer_id over customer_id when both exist
   - If context_customer_id exists in entities: Use WHERE customer_id = {entities.get('context_customer_id')}
   - If context_customer_ids exists (multiple customers): Use WHERE customer_id IN ({', '.join(map(str, entities.get('context_customer_ids', [])))})
   - If query mentions "this customer" or "the customer": Use context_customer_id from conversation
   - If query mentions "their", "them", "those customers", "these customers": Use context_customer_ids from previous query results
   - If query asks about "when did customer join" or "customer details": Use context_customer_id
   - If query asks about payment methods for "this customer": Use context_customer_id, not logged-in customer_id
   - Example: context_customer_id=1503, customer_id=1505 → Use WHERE customer_id = 1503
   - Example: context_customer_ids=[1481, 1406, 381], contextual_reference=True → Use WHERE customer_id IN (1481, 1406, 381)
4. For "track my order" or "order history" without specific order_id:
   - If customer_id is available: SELECT * FROM orders WHERE customer_id = {entities.get('customer_id', 'NULL')}
   - If no customer_id: Ask user to provide order ID
5. NEVER use placeholders like 'provided_order_id' or undefined variables
6. Always use actual entity values or return appropriate queries for missing data
7. For order tracking without order_id, show ALL orders for the authenticated customer
8. If 'needs_customer_lookup' is true and order_id is available: First get customer_id from the order, then get all orders for that customer
9. For product browsing/search queries: Use products table with appropriate filters

EXAMPLES:
- "Track my order" with customer_id=1503: SELECT * FROM orders WHERE customer_id = 1503
- "Order history" with customer_id=1503: SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.customer_id = 1503
- "Track order 12345": SELECT * FROM orders WHERE order_id = 12345
- "What are in the food items?" with order_content_inquiry=True, order_id=34662: SELECT o.order_id, o.product_category, o.total_amount, o.order_status, o.payment_method, o.delivery_date FROM orders o WHERE o.order_id = 34662
- "When did customer 1503 join us" with context_customer_id=1503: SELECT created_at FROM customers WHERE customer_id = 1503
- "What is their account tier" with context_customer_id=1503: SELECT account_tier FROM customers WHERE customer_id = 1503
- "When did this customer join" with context_customer_id=1503, customer_id=1505: SELECT created_at FROM customers WHERE customer_id = 1503
- "Customer details" with context_customer_id=1503, customer_id=1505: SELECT name, email, account_tier FROM customers WHERE customer_id = 1503
- "How much have I spent" with customer_id=1503: SELECT COALESCE(SUM(total_amount), 0) AS total_spent FROM orders WHERE customer_id = 1503;
- "Total spending breakdown" with customer_id=1503: SELECT COALESCE(product_category, 'Uncategorized') as product_category, SUM(total_amount) as category_spending FROM orders WHERE customer_id = 1503 GROUP BY COALESCE(product_category, 'Uncategorized') ORDER BY category_spending DESC;
- "Which products have I spent most on" with customer_id=1503: SELECT COALESCE(product_category, 'Uncategorized') as product_category, SUM(total_amount) as total_spent FROM orders WHERE customer_id = 1503 GROUP BY COALESCE(product_category, 'Uncategorized') ORDER BY total_spent DESC;
- "Are you sure that is the total?" with customer_id=1503: SELECT COALESCE(SUM(total_amount), 0) AS total_spent FROM orders WHERE customer_id = 1503;
- "Verify my total spending" with customer_id=1503: SELECT COALESCE(SUM(total_amount), 0) AS total_spent FROM orders WHERE customer_id = 1503;
- "Double check my spending" with customer_id=1503: SELECT COALESCE(SUM(total_amount), 0) AS total_spent FROM orders WHERE customer_id = 1503;
- "Give me the details" with customer_id=1503: SELECT COALESCE(product_category, 'Uncategorized') as product_category, SUM(total_amount) as category_spending FROM orders WHERE customer_id = 1503 GROUP BY COALESCE(product_category, 'Uncategorized') ORDER BY category_spending DESC;
- "Categories I purchased from" with customer_id=1503: SELECT DISTINCT COALESCE(product_category, 'Uncategorized') as product_category FROM orders WHERE customer_id = 1503 ORDER BY product_category;
- "Who is the top spending customer" (ADMIN ONLY): SELECT c.customer_id, c.name, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.name ORDER BY total_spent DESC LIMIT 10;
- "Which customers spend the most" (ADMIN ONLY): SELECT c.customer_id, c.name, c.account_tier, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.name, c.account_tier ORDER BY total_spent DESC LIMIT 10;
- "Debug total calculation" with customer_id=1503: SELECT 'Individual orders' as source, COUNT(*) as order_count, SUM(total_amount) as total_spent FROM orders WHERE customer_id = 1503 UNION ALL SELECT 'Category breakdown' as source, COUNT(DISTINCT order_id) as order_count, SUM(total_amount) as total_spent FROM orders WHERE customer_id = 1503;
- "What are their account tiers too?" with context_customer_ids=[1481, 1406, 381]: SELECT customer_id, name, account_tier FROM customers WHERE customer_id IN (1481, 1406, 381) ORDER BY customer_id;
- "How much did they spend?" with context_customer_ids=[1481, 1406, 381]: SELECT c.customer_id, c.name, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id IN (1481, 1406, 381) GROUP BY c.customer_id, c.name ORDER BY total_spent DESC;
- "What's my current account tier?" with customer_id=1503: SELECT account_tier FROM customers WHERE customer_id = 1503;
- "Show me my account information" with customer_id=1503: SELECT name, email, phone, account_tier, state, lga FROM customers WHERE customer_id = 1503;
- "When did I join?" with customer_id=1503: SELECT created_at FROM customers WHERE customer_id = 1503;
- "What is my account status?" with customer_id=1503: SELECT account_tier, account_status FROM customers WHERE customer_id = 1503;
- "Show me my spending breakdown by month" with customer_id=1503: SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as monthly_spending FROM orders WHERE customer_id = 1503 GROUP BY month ORDER BY month DESC;
- "I want to update my phone number" with customer_id=1503: SELECT 'UPDATE_OPERATION_REQUIRED' as message; -- Handle via application layer
- "Update my address" with customer_id=1503: SELECT 'UPDATE_OPERATION_REQUIRED' as message; -- Handle via application layer
- "give me monthly revenue report" (ADMIN with user_role=super_admin, can_access_analytics=True): SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as revenue FROM orders GROUP BY month ORDER BY month DESC;
- "monthly revenue report" (ADMIN with user_role=super_admin, can_access_analytics=True): SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as revenue FROM orders GROUP BY month ORDER BY month DESC;
- "which month did we make the most revenue" (ADMIN with user_role=super_admin, can_access_analytics=True): SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as revenue FROM orders GROUP BY month ORDER BY revenue DESC LIMIT 1;
- "total platform revenue" (ADMIN with user_role=super_admin, can_access_analytics=True): SELECT SUM(total_amount) as total_revenue FROM orders;
- "business revenue insights" (ADMIN with user_role=super_admin, can_access_analytics=True): SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as revenue FROM orders GROUP BY month ORDER BY revenue DESC;

🔍 FLEXIBLE PRODUCT SEARCH EXAMPLES:
- "do you have oil?": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%' OR description ILIKE '%oil%') AND in_stock = TRUE;
- "what oil do you have?": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%' OR description ILIKE '%oil%') AND in_stock = TRUE;
- "cooking oil": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (product_name ILIKE '%cooking%oil%' OR product_name ILIKE '%cooking%' OR (category ILIKE '%oil%' AND description ILIKE '%cooking%')) AND in_stock = TRUE;
- "automotive products": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (category ILIKE '%automotive%' OR product_name ILIKE '%automotive%' OR product_name ILIKE '%car%') AND in_stock = TRUE;

🔍 FLEXIBLE PRODUCT SEARCH EXAMPLES:
- "do you have oil?": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%' OR description ILIKE '%oil%') AND in_stock = TRUE;
- "what oil do you have?": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (category ILIKE '%oil%' OR product_name ILIKE '%oil%' OR description ILIKE '%oil%') AND in_stock = TRUE;
- "cooking oil": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (product_name ILIKE '%cooking%oil%' OR product_name ILIKE '%cooking%' OR (category ILIKE '%oil%' AND description ILIKE '%cooking%')) AND in_stock = TRUE;
- "automotive products": SELECT product_id, product_name, category, brand, price, stock_quantity FROM products WHERE (category ILIKE '%automotive%' OR product_name ILIKE '%automotive%' OR product_name ILIKE '%car%') AND in_stock = TRUE;

🚨 CRITICAL ADMIN BUSINESS QUERY RULE:
For user_role in ['admin', 'super_admin'] with can_access_analytics=True AND business-wide queries:
- NEVER include WHERE customer_id = anything in revenue/business analytics queries
- These are PLATFORM-WIDE queries, not customer-specific
- Keywords triggering this: "platform revenue", "total revenue", "business revenue", "monthly revenue", "most revenue", "which month", "revenue in sales"

⚠️ CRITICAL AUTHENTICATION RULES:
1. If customer_verified=False OR user_authenticated=False:
   - NEVER use specific customer_id values in WHERE clauses
   - NEVER hardcode customer_id numbers like "1503", "2", etc.
   - For order tracking by unauthenticated users: return "SELECT 'Please log in to view your order information' as message;"
   - For general product/payment queries: use generic queries without customer-specific data

2. If customer_verified=True AND user_authenticated=True AND customer_id is provided:
   - Only then use customer_id in WHERE clauses
   - Use the exact customer_id from entities: {entities.get('customer_id')}

3. For authentication status queries ("am I authenticated?"):
   - Return: SELECT '{entities.get('user_authenticated', False)}' as is_authenticated;

📊 CRITICAL SQL SYNTAX RULES:
- Use IS NULL instead of = NULL for null checks
- Use IS NOT NULL instead of != NULL for not null checks
- Never use = None or WHERE customer_id = None
- Never use WHERE customer_id = NULL (use IS NULL instead)
- For missing customer_id: omit the WHERE clause entirely or use appropriate filters

🚨 CRITICAL SHIPPING FEE RULES:
- NEVER generate SQL queries that treat payment_method conditions as shipping fees
- NEVER use SUM(total_amount) and call it "shipping fees" or "delivery fees"
- The orders table does NOT have separate shipping_fee or delivery_fee columns
- Shipping costs are included in the total amount field
- For shipping fee questions: Use informational responses, NOT database queries
- Example WRONG: SELECT SUM(CASE WHEN payment_method = 'Pay on Delivery' THEN 0 ELSE total_amount END) AS shipping_fees
- Example CORRECT: SELECT 'Standard rates: Lagos ₦2,000, Abuja ₦2,500, Major Cities ₦3,000, Other States ₦4,000. Gold/Platinum get free delivery!' as shipping_info

🛒 QUERY GUIDELINES:
- For product information: Use SELECT from products table (no customer restrictions)
- For payment methods: USE: SELECT DISTINCT payment_method FROM orders;
- For general information: Use public data only
- For customer-specific data: Require authentication
- For shipping fee queries: Use informational responses, NOT SUM calculations

📊 EXAMPLES OF CORRECT QUERIES:
- Unauthenticated order request: SELECT 'Please log in to view your order information' as message;
- Product search: SELECT * FROM products WHERE product_name ILIKE '%search_term%';
- Payment methods: SELECT DISTINCT payment_method FROM orders;
- Authenticated user orders: SELECT * FROM orders WHERE customer_id = [actual_customer_id];
- Shipping fee inquiry: SELECT 'Standard shipping rates: Lagos ₦2,000, Abuja ₦2,500, Major Cities ₦3,000, Other States ₦4,000. Free delivery for Gold/Platinum members!' as shipping_rates;

🚚 SHIPPING RATE INFORMATION QUERIES (NOT APPLICATION LAYER):
- "What are your shipping rates to Abuja?": SELECT 'Lagos Metro: ₦2,500 (1 day), Abuja FCT: ₦3,100 (2 days), Major Cities: ₦3,700 (3 days), Other States: ₦4,800 (5 days). Free delivery for Gold/Platinum members!' as shipping_rates;
- "shipping rates to Lagos": SELECT 'Lagos Metro: ₦2,500 (1-day delivery). Free for Gold/Platinum tier customers!' as shipping_rates;
- "delivery cost to Kano": SELECT 'Major Cities (Kano): ₦3,700 (3-day delivery). Free for Gold/Platinum tier customers!' as shipping_rates;
- "What does it cost to ship": SELECT 'Shipping rates: Lagos ₦2,500, Abuja ₦3,100, Major Cities ₦3,700, Other States ₦4,800. Free delivery for Gold/Platinum members!' as shipping_rates;

🏪 DELIVERY POLICY INFORMATION QUERIES (NOT APPLICATION LAYER):
- "Can I change delivery address for shipped order?": SELECT 'Unfortunately, once an order has shipped, we cannot change the delivery address. However, you can: 1) Ask someone to receive it at the original address, 2) Contact our delivery partner to arrange pickup from a nearby depot, 3) Contact customer support for special assistance. We apologize for any inconvenience!' as delivery_policy;
- "I won't be home for delivery": SELECT 'No worries! Here are your options: 1) Ask a neighbor or family member to receive it, 2) Reschedule delivery through our delivery partner, 3) Pick up from nearest depot/office, 4) Leave specific delivery instructions. Contact our support team for assistance!' as delivery_options;
- "Can you arrange delivery to my office": SELECT 'We can arrange office delivery! Please provide: 1) Complete office address, 2) Office phone number, 3) Contact person name, 4) Best delivery time (9am-5pm weekdays). There may be additional charges for commercial addresses.' as office_delivery;
- "Can I pick up from warehouse": SELECT 'Yes! Warehouse pickup is available Monday-Friday 9am-4pm at our Lagos facility. You will need: 1) Valid ID, 2) Order confirmation number, 3) 24-hour advance notice. Contact support to arrange pickup appointment.' as warehouse_pickup;
- "My package arrived damaged": SELECT 'We sincerely apologize! For damaged packages: 1) Take photos of damage immediately, 2) Do not throw away packaging, 3) Contact support within 48 hours, 4) We will arrange return pickup and replacement/refund. Your satisfaction is our priority!' as damage_policy;

RESPONSE FORMAT: Return ONLY the SQL query, nothing else."""

        try:
            # 🔧 CRITICAL FIX: Include entity context in user message for better context awareness
            context_info = ""
            if entities:
                context_parts = []
                user_role = entities.get('user_role')
                is_analytics_query = query_type in [
                    QueryType.REVENUE_INSIGHTS, QueryType.CUSTOMER_ANALYSIS,
                    QueryType.GEOGRAPHIC_ANALYSIS, QueryType.TEMPORAL_ANALYSIS,
                    QueryType.PRODUCT_PERFORMANCE
                ]

                if entities.get('context_customer_id'):
                    context_parts.append(f"context_customer_id={entities.get('context_customer_id')}")
                if entities.get('context_customer_ids'):
                    context_parts.append(f"context_customer_ids={entities.get('context_customer_ids')}")
                if entities.get('contextual_reference'):
                    context_parts.append(f"contextual_reference={entities.get('contextual_reference')}")

                # 🚨 THE ACTUAL FIX: Only add customer_id to context if NOT an admin doing analytics
                if entities.get('customer_id'):
                    if not (user_role in ['admin', 'super_admin'] and is_analytics_query):
                        context_parts.append(f"customer_id={entities.get('customer_id')}")
                    else:
                        logger.info(f"🏢 ADMIN ANALYTICS: Scrubbing admin customer_id from AI prompt context.")

                if entities.get('user_authenticated'):
                    context_parts.append(f"user_authenticated={entities.get('user_authenticated')}")

                if context_parts:
                    context_info = f" (Context: {', '.join(context_parts)})"

            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate SQL query for: {user_query}{context_info}"}
                ],
                temperature=0.1,
                max_tokens=512
            )

            sql_query = response.choices[0].message.content.strip()

            # Clean up the SQL query - remove markdown and extract actual SQL
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()

            # 🔧 CRITICAL FIX: Extract only the SQL query from explanatory text
            lines = sql_query.split('\n')
            sql_lines = []
            in_sql_block = False

            for line in lines:
                line = line.strip()
                # Skip empty lines and explanatory text
                if not line:
                    continue

                # 🆕 ENHANCED FILTERING: Skip lines with explanatory keywords
                if any(phrase in line.lower() for phrase in [
                    'however', 'since the query', 'for a more accurate', 'given the provided',
                    'assuming', 'consider the', 'note:', 'explanation:', 'this query',
                    'the query type', 'a more suitable query', 'adjustment to retrieve'
                ]):
                    continue

                # Look for SQL keywords to identify actual SQL statements
                if any(line.upper().startswith(keyword) for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'CREATE', 'ALTER', 'DROP']):
                    in_sql_block = True
                    sql_lines.append(line)
                elif in_sql_block and any(keyword in line.upper() for keyword in ['FROM', 'WHERE', 'JOIN', 'ORDER BY', 'GROUP BY', 'HAVING', 'UNION', 'LIMIT', 'OFFSET']):
                    sql_lines.append(line)
                elif in_sql_block and line.endswith(';'):
                    sql_lines.append(line)
                    break  # End of SQL statement
                elif in_sql_block and not any(phrase in line.lower() for phrase in ['however', 'since', 'given', 'assuming']):
                    # Only add if it's part of SQL and not explanatory text
                    sql_lines.append(line)

            if sql_lines:
                sql_query = ' '.join(sql_lines)

                # 🆕 ADDITIONAL CLEANING: Remove trailing explanatory text after semicolon
                if '; However' in sql_query or '; Since' in sql_query or '; Given' in sql_query:
                    sql_query = sql_query.split(';')[0] + ';'

                # Basic syntax validation - check for common SQL errors
                sql_upper = sql_query.upper()
                if 'UNION ALL' in sql_upper and ',UNION' in sql_upper.replace(' ', ''):
                    # Fix malformed UNION syntax
                    sql_query = sql_query.replace(', UNION', ' UNION')
                    logger.info("🔧 Fixed malformed UNION syntax in SQL query")

            # Ensure it ends with semicolon
            if not sql_query.endswith(';'):
                sql_query += ';'

            # 🆕 PARAMETER SUBSTITUTION: Replace placeholders with actual values from entities
            if entities:
                # 🔧 CRITICAL FIX: Handle context_customer_id for support agents first
                context_customer_id = entities.get('context_customer_id')
                customer_id = entities.get('customer_id')
                user_role = entities.get('user_role', 'guest')
                can_access_analytics = entities.get('can_access_analytics', False)

                # 🚨 CRITICAL FIX: For admin revenue/analytics queries, DON'T substitute customer_id
                # This was causing platform-wide queries to become customer-specific
                is_analytics_query = query_type in [QueryType.REVENUE_INSIGHTS, QueryType.CUSTOMER_ANALYSIS,
                                                  QueryType.GEOGRAPHIC_ANALYSIS, QueryType.TEMPORAL_ANALYSIS]

                if is_analytics_query and user_role in ['admin', 'super_admin'] and can_access_analytics:
                    # For admin analytics queries, DON'T substitute customer_id - keep platform-wide
                    logger.info(f"🏢 ADMIN ANALYTICS: Preserving platform-wide scope for {user_role}")
                    # 🚨 CRITICAL FIX: Check if this is truly a business-wide query
                    query_lower = entities.get('user_query', '').lower()
                    business_keywords = ['platform revenue', 'total revenue', 'all revenue', 'business revenue',
                                       'monthly revenue', 'revenue by month', 'most revenue', 'highest revenue',
                                       'platform sales', 'total sales', 'business analytics', 'company revenue',
                                       'which month', 'revenue in sales', 'make the most revenue']

                    is_business_wide_query = any(keyword in query_lower for keyword in business_keywords)

                    if is_business_wide_query:
                        # Remove customer_id filters entirely for true business queries
                        sql_query = sql_query.replace('WHERE customer_id = [customer_id]', '')
                        sql_query = sql_query.replace('WHERE customer_id = {customer_id}', '')
                        sql_query = sql_query.replace('customer_id = [customer_id] AND', '')
                        sql_query = sql_query.replace('customer_id = {customer_id} AND', '')
                        sql_query = sql_query.replace('AND customer_id = [customer_id]', '')
                        sql_query = sql_query.replace('AND customer_id = {customer_id}', '')
                        sql_query = sql_query.replace('[customer_id]', 'NULL')
                        sql_query = sql_query.replace('{customer_id}', 'NULL')
                        logger.info(f"🏢 BUSINESS QUERY: Removed all customer_id filters for platform-wide analytics")
                    elif context_customer_id:
                        # Only substitute if this is customer-specific admin query
                        sql_query = sql_query.replace('[customer_id]', str(context_customer_id))
                        sql_query = sql_query.replace('{customer_id}', str(context_customer_id))
                        logger.info(f"🔧 Substituted context_customer_id: {context_customer_id} in SQL query")
                else:
                    # Priority order: context_customer_id (from conversation) > logged-in customer_id
                    effective_customer_id = context_customer_id or customer_id

                    if effective_customer_id is not None:
                        sql_query = sql_query.replace('[customer_id]', str(effective_customer_id))
                        sql_query = sql_query.replace('{customer_id}', str(effective_customer_id))
                        if context_customer_id:
                            logger.info(f"🔧 Substituted context_customer_id: {context_customer_id} in SQL query")
                        else:
                            logger.info(f"🔧 Substituted customer_id: {customer_id} in SQL query")

                # Handle order_id substitution
                order_id = entities.get('order_id')  # Define in proper scope
                if order_id is not None:
                    sql_query = sql_query.replace('[order_id]', f"'{order_id}'")
                    sql_query = sql_query.replace('{order_id}', f"'{order_id}'")
                    logger.info(f"🔧 Substituted order_id: {order_id} in SQL query")

            # 🚨 COMPREHENSIVE SQL FIXES
            sql_query = self._apply_critical_sql_fixes(sql_query, entities)

            logger.info(f"🔍 Generated SQL: {sql_query}")
            return sql_query

        except Exception as e:
            logger.error(f"❌ SQL generation error: {e}")
            return self._get_fallback_query(query_type, entities)

    def _fix_product_name_spacing(self, sql_query: str, user_query: str) -> str:
        """🔧 Fix product name spacing issues in generated SQL"""
        try:
            # Common product patterns that lose spaces
            problematic_patterns = {
                # Tecno products
                r"'%Tecno Camon(\d+)\s*Pro(\d*)G%'": r"'%Tecno Camon \1 Pro \2G%'",
                r"'%TecnoCamon(\d+)\s*Pro(\d*)G%'": r"'%Tecno Camon \1 Pro \2G%'",
                r"'%Tecno(\w+)(\d+)\s*Pro(\d*)G%'": r"'%Tecno \1 \2 Pro \3G%'",

                # iPhone products
                r"'%iPhone(\d+)\s*Pro\s*Max%'": r"'%iPhone \1 Pro Max%'",
                r"'%iPhone(\d+)Pro\s*Max%'": r"'%iPhone \1 Pro Max%'",
                r"'%iPhone(\d+)\s*Pro%'": r"'%iPhone \1 Pro%'",
                r"'%iPhone(\d+)Pro%'": r"'%iPhone \1 Pro%'",

                # Samsung products
                r"'%Samsung\s*Galaxy\s*([A-Z]\d+)%'": r"'%Samsung Galaxy \1%'",
                r"'%SamsungGalaxy([A-Z]\d+)%'": r"'%Samsung Galaxy \1%'",

                # Generic number-letter combinations
                r"'%(\w+)(\d+)\s*([A-Z]+)%'": r"'%\1 \2 \3%'",
                r"'%(\w+)\s*(\d+)([A-Z]+)%'": r"'%\1 \2 \3%'",
            }

            # Apply fixes
            original_query = sql_query
            for pattern, replacement in problematic_patterns.items():
                import re
                sql_query = re.sub(pattern, replacement, sql_query, flags=re.IGNORECASE)

            # Additional specific fixes based on user query
            if "tecno camon 20 pro 5g" in user_query.lower():
                # Ensure correct spacing for this specific product
                sql_query = re.sub(r"'%Tecno\s*Camon\s*20\s*Pro\s*5\s*G%'", "'%Tecno Camon 20 Pro 5G%'", sql_query, flags=re.IGNORECASE)
                sql_query = re.sub(r"'%TecnoCamon20Pro5G%'", "'%Tecno Camon 20 Pro 5G%'", sql_query, flags=re.IGNORECASE)

            if "iphone" in user_query.lower() and "pro" in user_query.lower():
                # Fix iPhone Pro patterns
                sql_query = re.sub(r"'%iPhone\s*(\d+)\s*Pro\s*Max%'", r"'%iPhone \1 Pro Max%'", sql_query, flags=re.IGNORECASE)
                sql_query = re.sub(r"'%iPhone\s*(\d+)\s*Pro%'", r"'%iPhone \1 Pro%'", sql_query, flags=re.IGNORECASE)

            if sql_query != original_query:
                logger.info(f"🔧 Fixed product name spacing in SQL query")

            return sql_query

        except Exception as e:
            logger.warning(f"⚠️ Error fixing product name spacing: {e}")
            return sql_query

    def _get_fallback_query(self, query_type: QueryType, entities: Dict[str, Any]) -> str:
        """Generate fallback SQL queries for error scenarios"""

        if query_type == QueryType.CUSTOMER_ANALYSIS:
            if entities.get('states'):
                state = entities['states'][0]
                return f"SELECT * FROM customers WHERE state = '{state}' LIMIT 10;"
            return "SELECT * FROM customers ORDER BY created_at DESC LIMIT 10;"

        elif query_type == QueryType.ORDER_ANALYTICS:
            # 🔧 FIX: Proper guest user handling with safe variable scoping
            customer_verified = entities.get('customer_verified', False)
            customer_id = entities.get('customer_id')  # Always define in this scope

            # If we have customer_id from session (authenticated user), get their orders
            if customer_verified and customer_id:
                return f"""
                SELECT o.order_id, o.order_status, o.payment_method, o.total_amount,
                       o.delivery_date, o.created_at, o.product_category, c.name as customer_name,
                       c.address, c.state, c.lga
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.customer_id = {customer_id}
                ORDER BY o.created_at DESC
                LIMIT 20;
                """
            # If we have customer_id from conversation history, use it for order history
            elif customer_id and not customer_verified:
                # customer_id already defined above, no reassignment needed
                return f"""
                SELECT o.order_id, o.order_status, o.payment_method, o.total_amount,
                       o.delivery_date, o.created_at, c.name as customer_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.customer_id = {customer_id}
                ORDER BY o.created_at DESC
                LIMIT 20;
                """
            # If we need to lookup customer from order_id for order history
            elif entities.get('needs_customer_lookup') and entities.get('order_id'):
                order_id = entities['order_id']
                return f"""
                SELECT o2.order_id, o2.order_status, o2.payment_method, o2.total_amount,
                       o2.delivery_date, o2.created_at, c.name as customer_name
                FROM orders o1
                JOIN customers c ON o1.customer_id = c.customer_id
                JOIN orders o2 ON c.customer_id = o2.customer_id
                WHERE o1.order_id = {order_id}
                ORDER BY o2.created_at DESC
                LIMIT 20;
                """
            # If we have order_id, get specific order
            elif entities.get('order_id'):
                order_id = entities['order_id']
                return f"""
                SELECT o.*, c.name as customer_name, c.email
                FROM orders o
                JOIN customers c ON o.customer_id = c.customer_id
                WHERE o.order_id = {order_id};
                """
            # 🆕 GUEST USER FALLBACK: Return empty result for guest users asking about orders
            else:
                return "SELECT 'Guest user - authentication required' as message, 'Please provide your order ID or log in to view your orders' as suggestion;"

        elif query_type == QueryType.REVENUE_INSIGHTS:
            # 🔧 CRITICAL FIX: Handle customer spending queries properly
            customer_verified = entities.get('customer_verified', False)
            customer_id = entities.get('customer_id')

            # If authenticated customer asking about their spending
            if customer_verified and customer_id:
                return f"""
                SELECT
                    'Total Spending' as metric,
                    COALESCE(SUM(total_amount), 0) as total_spent,
                    COUNT(*) as total_orders,
                    COALESCE(AVG(total_amount), 0) as avg_order_value
                FROM orders
                WHERE customer_id = {customer_id};
                """
            else:
                # General revenue insights (business-wide)
                return """
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    SUM(total_amount) as total_revenue,
                    COUNT(*) as order_count
                FROM orders
                WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC;
                """

        elif query_type == QueryType.GEOGRAPHIC_ANALYSIS:
            return """
            SELECT
                c.state,
                COUNT(c.customer_id) as customer_count,
                COUNT(o.order_id) as order_count,
                COALESCE(SUM(o.total_amount), 0) as total_revenue
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.state
            ORDER BY total_revenue DESC
            LIMIT 20;
            """

        elif query_type == QueryType.PRODUCT_PERFORMANCE:
            # 🆕 PRODUCT-RELATED FALLBACK QUERIES
            if entities.get('product_categories'):
                category = entities['product_categories'][0]
                return f"""
                SELECT p.product_id, p.product_name, p.brand, p.price, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 10 THEN 'Low Stock'
                           WHEN p.stock_quantity <= 50 THEN 'Medium Stock'
                           ELSE 'High Stock'
                       END as stock_status,
                       COUNT(o.order_id) as order_count
                FROM products p
                LEFT JOIN orders o ON p.product_id = o.product_id
                WHERE (p.category ILIKE '%{category}%' OR p.product_name ILIKE '%{category}%') AND p.in_stock = true
                GROUP BY p.product_id, p.product_name, p.brand, p.price, p.stock_quantity
                ORDER BY order_count DESC, p.price ASC
                LIMIT 20;
                """
            elif entities.get('brands'):
                brand = entities['brands'][0]
                return f"""
                SELECT p.product_id, p.product_name, p.category, p.price, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 10 THEN 'Low Stock'
                           WHEN p.stock_quantity <= 50 THEN 'Medium Stock'
                           ELSE 'High Stock'
                       END as stock_status
                FROM products p
                WHERE p.brand ILIKE '%{brand}%' AND p.in_stock = true
                ORDER BY p.price ASC
                LIMIT 20;
                """
            elif entities.get('price_query'):
                return """
                SELECT p.category, p.brand, p.product_name, p.price,
                       CASE
                           WHEN p.price < 50000 THEN 'Budget-Friendly'
                           WHEN p.price < 200000 THEN 'Mid-Range'
                           WHEN p.price < 500000 THEN 'Premium'
                           ELSE 'Luxury'
                       END as price_category,
                       p.stock_quantity
                FROM products p
                WHERE p.in_stock = true
                ORDER BY p.price ASC
                LIMIT 25;
                """
            elif entities.get('inventory_query'):
                return """
                SELECT p.category, p.product_name, p.brand, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 10 THEN 'Low Stock'
                           WHEN p.stock_quantity <= 50 THEN 'Medium Stock'
                           ELSE 'High Stock'
                       END as stock_status,
                       p.price, p.in_stock
                FROM products p
                ORDER BY p.stock_quantity ASC, p.category
                LIMIT 25;
                """
            else:
                # General product query
                return """
                SELECT p.category, COUNT(*) as product_count,
                       AVG(p.price) as avg_price,
                       SUM(p.stock_quantity) as total_stock,
                       COUNT(CASE WHEN p.stock_quantity = 0 THEN 1 END) as out_of_stock_count
                FROM products p
                WHERE p.in_stock = true
                GROUP BY p.category
                ORDER BY product_count DESC;
                """

        # 🆕 NEW SHOPPING-RELATED FALLBACK QUERIES
        elif query_type == QueryType.PRODUCT_RECOMMENDATIONS:
            # Get popular products for recommendations
            customer_verified = entities.get('customer_verified', False)
            customer_id = entities.get('customer_id')
            if customer_id and customer_verified:
                return f"""
                SELECT p.product_id, p.product_name, p.category, p.brand, p.price,
                       p.description, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 10 THEN 'Low Stock'
                           ELSE 'In Stock'
                       END as stock_status,
                       COUNT(o.order_id) as popularity_score
                FROM products p
                LEFT JOIN orders o ON p.product_id = o.product_id
                WHERE p.in_stock = true AND p.stock_quantity > 0
                AND p.product_id NOT IN (
                    SELECT DISTINCT product_id FROM orders WHERE customer_id = {customer_id}
                )
                GROUP BY p.product_id, p.product_name, p.category, p.brand, p.price, p.description, p.stock_quantity
                ORDER BY popularity_score DESC, p.price ASC
                LIMIT 15;
                """
            else:
                return """
                SELECT p.product_id, p.product_name, p.category, p.brand, p.price,
                       p.description, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 10 THEN 'Low Stock'
                           ELSE 'In Stock'
                       END as stock_status,
                       COUNT(o.order_id) as popularity_score
                FROM products p
                LEFT JOIN orders o ON p.product_id = o.product_id
                WHERE p.in_stock = true AND p.stock_quantity > 0
                GROUP BY p.product_id, p.product_name, p.category, p.brand, p.price, p.description, p.stock_quantity
                ORDER BY popularity_score DESC, p.price ASC
                LIMIT 15;
                """

        elif query_type == QueryType.PRICE_INQUIRY:
            max_budget = entities.get('max_budget')
            if max_budget:
                return f"""
                SELECT p.product_id, p.product_name, p.category, p.brand, p.price,
                       p.description, p.stock_quantity,
                       CASE
                           WHEN p.price < 25000 THEN 'Very Affordable'
                           WHEN p.price < 50000 THEN 'Budget-Friendly'
                           WHEN p.price < 100000 THEN 'Mid-Range'
                           WHEN p.price < 200000 THEN 'Premium'
                           ELSE 'Luxury'
                       END as price_category
                FROM products p
                WHERE p.price <= {max_budget} AND p.in_stock = true AND p.stock_quantity > 0
                ORDER BY p.price ASC
                LIMIT 20;
                """
            else:
                return """
                SELECT p.category, MIN(p.price) as min_price, MAX(p.price) as max_price,
                       AVG(p.price) as avg_price, COUNT(*) as product_count
                FROM products p
                WHERE p.in_stock = true AND p.stock_quantity > 0
                GROUP BY p.category
                ORDER BY avg_price ASC;
                """

        elif query_type == QueryType.STOCK_CHECK:
            if entities.get('product_categories'):
                category = entities['product_categories'][0]
                return f"""
                SELECT p.product_id, p.product_name, p.brand, p.price, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock - Hurry!'
                           WHEN p.stock_quantity <= 15 THEN 'Limited Stock'
                           ELSE 'In Stock'
                       END as stock_status,
                       p.in_stock
                FROM products p
                WHERE (p.category ILIKE '%{category}%' OR p.product_name ILIKE '%{category}%')
                ORDER BY p.stock_quantity ASC, p.price ASC
                LIMIT 20;
                """
            else:
                return """
                SELECT p.product_id, p.product_name, p.category, p.brand, p.price, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock - Hurry!'
                           WHEN p.stock_quantity <= 15 THEN 'Limited Stock'
                           ELSE 'In Stock'
                       END as stock_status
                FROM products p
                WHERE p.in_stock = true
                ORDER BY p.stock_quantity ASC, p.category, p.price ASC
                LIMIT 25;
                """

        elif query_type == QueryType.SHOPPING_ASSISTANCE:
            return """
            SELECT p.category, COUNT(*) as total_products,
                   MIN(p.price) as min_price, MAX(p.price) as max_price,
                   AVG(p.price) as avg_price,
                   SUM(CASE WHEN p.stock_quantity > 0 THEN 1 ELSE 0 END) as available_products,
                   STRING_AGG(DISTINCT p.brand, ', ') as popular_brands
            FROM products p
            WHERE p.in_stock = true
            GROUP BY p.category
            ORDER BY total_products DESC;
            """

        elif query_type == QueryType.ORDER_PLACEMENT:
            # For order placement, get product details if specific products mentioned
            if entities.get('product_categories'):
                category = entities['product_categories'][0]
                return f"""
                SELECT p.product_id, p.product_name, p.brand, p.price, p.description,
                       p.stock_quantity, p.weight_kg,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock'
                           ELSE 'Available for Order'
                       END as availability_status
                FROM products p
                WHERE (p.category ILIKE '%{category}%' OR p.product_name ILIKE '%{category}%') AND p.in_stock = true AND p.stock_quantity > 0
                ORDER BY p.price ASC
                LIMIT 15;
                """
            else:
                return """
                SELECT p.product_id, p.product_name, p.category, p.brand, p.price,
                       p.description, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock'
                           ELSE 'Available for Order'
                       END as availability_status
                FROM products p
                WHERE p.in_stock = true AND p.stock_quantity > 0
                ORDER BY p.category, p.price ASC
                LIMIT 20;
                """

        elif query_type == QueryType.PRODUCT_INFO_GENERAL:
            # 🆕 ENHANCED: More flexible product search with synonyms
            product_synonyms = {
                'phone': ['smartphone', 'mobile', 'iphone', 'samsung'],
                'phones': ['smartphone', 'mobile', 'iphone', 'samsung', 'cell phone'],
                'ios': ['iphone', 'ipad', 'apple'],
                'apple': ['iphone', 'ipad', 'macbook'],
                'ipads': ['ipad'],
                'tablet': ['ipad', 'samsung tab'],
                'laptop': ['macbook', 'hp', 'dell', 'lenovo'],
                'computer': ['laptop', 'macbook', 'hp', 'dell'],
                'android': ['samsung', 'tecno', 'infinix']
            }

            if entities.get('product_keywords'):
                # Enhanced product search with multiple strategies
                keywords = entities['product_keywords']
                search_conditions = []
                search_params = []

                for keyword in keywords[:3]:  # Limit to first 3 keywords
                    keyword_lower = keyword.lower()

                    # Direct product name matching
                    search_conditions.append("p.product_name ILIKE %s")
                    search_params.append(f"%{keyword}%")

                    # Brand matching
                    search_conditions.append("p.brand ILIKE %s")
                    search_params.append(f"%{keyword}%")

                    # Category matching
                    search_conditions.append("p.category ILIKE %s")
                    search_params.append(f"%{keyword}%")

                    # Synonym expansion
                    if keyword_lower in product_synonyms:
                        for synonym in product_synonyms[keyword_lower]:
                            search_conditions.append("p.product_name ILIKE %s")
                            search_params.append(f"%{synonym}%")
                            search_conditions.append("p.brand ILIKE %s")
                            search_params.append(f"%{synonym}%")

                where_clause = " OR ".join(search_conditions)

                # Add the primary keyword for ordering
                primary_keyword = keywords[0] if keywords else ''

                # Build the enhanced SQL query
                search_params_str = []
                for param in search_params:
                    search_params_str.append(f"'{param.replace('%', '')}'")

                # Replace parameters in where clause
                where_clause_with_params = where_clause
                param_index = 0
                while '%s' in where_clause_with_params and param_index < len(search_params):
                    where_clause_with_params = where_clause_with_params.replace('%s', f"'{search_params[param_index]}'", 1)
                    param_index += 1

                sql_query = f"""
                SELECT p.product_id, p.product_name, p.category, p.brand, p.description,
                       p.price, p.currency, p.in_stock, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock'
                           WHEN p.stock_quantity <= 15 THEN 'Limited Stock'
                           ELSE 'In Stock'
                       END as stock_status
                FROM products p
                WHERE ({where_clause_with_params}) AND p.in_stock = TRUE
                ORDER BY
                    -- Prioritize exact matches
                    (p.product_name ILIKE '%{primary_keyword}%') DESC,
                    -- Then prioritize by stock availability
                    p.stock_quantity DESC,
                    -- Finally by price
                    p.price ASC
                LIMIT 10;
                """

                logger.info(f"🔍 Enhanced product search SQL generated for keywords: {keywords}")
                return sql_query

            elif entities.get('brands'):
                brand = entities['brands'][0]
                return f"""
                SELECT p.product_id, p.product_name, p.category, p.brand, p.description,
                       p.price, p.currency, p.in_stock, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock'
                           WHEN p.stock_quantity <= 15 THEN 'Limited Stock'
                           ELSE 'In Stock'
                       END as stock_status
                FROM products p
                WHERE p.brand ILIKE '%{brand}%' AND p.in_stock = TRUE
                ORDER BY p.price ASC
                LIMIT 10;
                """
            else:
                # Fallback: show popular products
                return """
                SELECT p.product_id, p.product_name, p.category, p.brand, p.description,
                       p.price, p.currency, p.in_stock, p.stock_quantity,
                       CASE
                           WHEN p.stock_quantity = 0 THEN 'Out of Stock'
                           WHEN p.stock_quantity <= 5 THEN 'Low Stock'
                           ELSE 'In Stock'
                       END as stock_status,
                       COUNT(o.order_id) as popularity
                FROM products p
                LEFT JOIN orders o ON p.product_id = o.product_id
                WHERE p.in_stock = TRUE AND p.stock_quantity > 0
                GROUP BY p.product_id, p.product_name, p.category, p.brand, p.description,
                         p.price, p.currency, p.in_stock, p.stock_quantity
                ORDER BY popularity DESC, p.price ASC
                LIMIT 15;
                """

        else:
            return "SELECT 'Fallback query executed' as message;"

    def get_database_connection(self):
        """Get database connection with comprehensive error handling"""
        try:
            conn = psycopg2.connect(**self.db_config)
            app_logger.info("✅ Database connection established")
            return conn
        except psycopg2.OperationalError as oe:
            app_logger.error(f"❌ Database operational error: {oe}")
            raise Exception(f"Database connection failed: {oe}")
        except psycopg2.DatabaseError as de:
            app_logger.error(f"❌ Database error: {de}")
            raise Exception(f"Database error: {de}")
        except Exception as e:
            app_logger.error(f"❌ Unexpected database connection error: {e}")
            raise Exception(f"Database connection error: {e}")

    def execute_sql_query(self, sql_query: str, max_retries: int = 3) -> Tuple[bool, List[Dict], str]:
        """
        Execute SQL query with comprehensive error handling and retry logic
        Returns: (success, results, error_message)
        """
        for attempt in range(max_retries):
            try:
                with self.get_database_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        app_logger.info(f"🔍 Executing query: {sql_query}")

                        try:
                            cursor.execute(sql_query)

                            # 🔧 CRITICAL FIX: Handle different types of SQL queries
                            if sql_query.strip().upper().startswith(('UPDATE', 'DELETE', 'INSERT')):
                                # For modification queries, get row count instead of results
                                affected_rows = cursor.rowcount
                                conn.commit()  # Commit the transaction

                                # Return success message with affected rows count
                                json_results = [{"message": f"Query executed successfully", "affected_rows": affected_rows}]
                                app_logger.info(f"✅ {sql_query.split()[0]} query executed successfully, {affected_rows} rows affected")
                                return True, json_results, ""
                            else:
                                # For SELECT queries, fetch results normally
                                results = cursor.fetchall()
                                # Convert RealDictRow to regular dict for JSON serialization
                                json_results = [dict(row) for row in results]
                                app_logger.info(f"✅ Query executed successfully, {len(json_results)} rows returned")
                                return True, json_results, ""

                        except psycopg2.ProgrammingError as pe:
                            error_msg = f"SQL programming error: {pe}"
                            app_logger.error(f"❌ {error_msg}")
                            return False, [], error_msg

                        except psycopg2.DataError as de:
                            error_msg = f"SQL data error: {de}"
                            app_logger.error(f"❌ {error_msg}")
                            return False, [], error_msg

                        except psycopg2.IntegrityError as ie:
                            error_msg = f"SQL integrity error: {ie}"
                            app_logger.error(f"❌ {error_msg}")
                            return False, [], error_msg

            except psycopg2.OperationalError as oe:
                error_msg = f"Database operational error (attempt {attempt + 1}/{max_retries}): {oe}"
                app_logger.warning(f"⚠️ {error_msg}")

                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    return False, [], f"Database connection failed after {max_retries} attempts: {oe}"

            except psycopg2.DatabaseError as de:
                error_msg = f"Database error: {de}"
                app_logger.error(f"❌ {error_msg}")
                return False, [], error_msg

            except Exception as e:
                error_msg = f"Unexpected error executing query: {e}"
                app_logger.error(f"❌ {error_msg}")
                return False, [], error_msg

        return False, [], "Maximum retry attempts exceeded"

    def store_conversation_context(self, query_context: QueryContext, user_id: str = "anonymous"):
        """
        📝 Store conversation context in both Redis and database for persistent memory
        """

        notepad_entry = {
            "timestamp": query_context.timestamp.isoformat(),
            "user_query": query_context.user_query,
            "intent": query_context.intent,
            "query_type": query_context.query_type.value,
            "entities": query_context.entities,
            "sql_query": query_context.sql_query,
            "execution_result": query_context.execution_result,
            "response": query_context.response,
            "error_message": query_context.error_message
        }

        # Store in Redis or memory (existing functionality)
        try:
            if self.redis_client:
                key = f"conversation:{user_id}:{query_context.timestamp.strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.setex(key, 3600, safe_json_dumps(notepad_entry))  # 1 hour TTL

                # Maintain conversation history list
                history_key = f"conversation_history:{user_id}"
                self.redis_client.lpush(history_key, key)
                self.redis_client.ltrim(history_key, 0, 49)  # Keep last 50 entries
                self.redis_client.expire(history_key, 86400)  # 24 hours TTL
            else:
                # Memory fallback
                if user_id not in self._memory_store:
                    self._memory_store[user_id] = []
                self._memory_store[user_id].append(notepad_entry)

                # Keep only last 20 entries in memory
                if len(self._memory_store[user_id]) > 20:
                    self._memory_store[user_id] = self._memory_store[user_id][-20:]

            logger.info(f"📝 Context stored in Redis for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Context storage error in Redis: {e}")

        # 🆕 CRITICAL FIX: Also store in database for persistent memory
        try:
            conn = self.get_database_connection()
            if conn:
                cursor = conn.cursor()

                # Extract session_id from user_id if available
                session_id = query_context.entities.get('session_id', user_id)

                cursor.execute("""
                    INSERT INTO conversation_context
                    (user_id, session_id, query_type, entities, sql_query, execution_result, response_text, user_query, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    session_id,
                    query_context.query_type.value,
                    safe_json_dumps(query_context.entities),
                    query_context.sql_query,
                    safe_json_dumps(query_context.execution_result),
                    query_context.response,
                    query_context.user_query,
                    query_context.timestamp
                ))

                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"✅ Context stored in database for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Database context storage error: {e}")

    def store_shopping_conversation_context(self, user_query: str, response: str, user_id: str, session_id: str,
                                          shopping_data: Dict[str, Any] = None):
        """Store shopping conversation context in Redis with enhanced product context tracking"""
        try:
            key = f"shopping_conversation_{user_id}_{session_id}"

            # Get existing context
            if hasattr(self, 'redis_client') and self.redis_client:
                existing_data = self.redis_client.get(key)
                conversation_history = json.loads(existing_data) if existing_data else {'turns': [], 'session_state': {}}
            else:
                conversation_history = {'turns': [], 'session_state': {}}

            # 🔧 CRITICAL FIX: Extract product context from multiple sources
            extracted_product_context = None

            # Method 1: Check shopping_data for product information
            if shopping_data and 'execution_result' in shopping_data:
                for result in shopping_data['execution_result']:
                    if isinstance(result, dict) and result.get('product_id'):
                        extracted_product_context = {
                            'product_id': result.get('product_id'),
                            'product_name': result.get('product_name'),
                            'price': result.get('price'),
                            'category': result.get('category'),
                            'brand': result.get('brand'),
                            'in_stock': result.get('in_stock', True),
                            'stock_quantity': result.get('stock_quantity', 0),
                            'mentioned_at': datetime.now().isoformat()
                        }
                        logger.info(f"🧠 EXTRACTED PRODUCT FROM SHOPPING DATA: {extracted_product_context['product_name']}")
                        break

            # Method 2: Check if shopping_data has product_added information (from successful cart operations)
            if not extracted_product_context and shopping_data and shopping_data.get('product_added'):
                product_data = shopping_data['product_added']
                extracted_product_context = {
                    'product_id': product_data.get('product_id'),
                    'product_name': product_data.get('product_name'),
                    'price': product_data.get('price'),
                    'category': product_data.get('category'),
                    'brand': product_data.get('brand'),
                    'in_stock': product_data.get('in_stock', True),
                    'stock_quantity': product_data.get('stock_quantity', 0),
                    'mentioned_at': datetime.now().isoformat()
                }
                logger.info(f"🧠 EXTRACTED PRODUCT FROM CART OPERATION: {extracted_product_context['product_name']}")

            # Method 3: If no product in current results, check if user is asking about products
            product_keywords = ['product', 'phone', 'laptop', 'dress', 'shoe', 'rice', 'book', 'oil', 'cream', 'samsung', 'iphone', 'tecno']
            if not extracted_product_context and any(keyword in user_query.lower() for keyword in product_keywords):
                # This was likely a product inquiry, store the query for AI to understand context
                logger.info(f"🤔 Product inquiry detected but no specific product found: {user_query}")

            # Store current turn
            current_turn = {
                'user_input': user_query,
                'ai_response': response,
                'timestamp': datetime.now().isoformat(),
                'shopping_data': shopping_data,
                'extracted_product': extracted_product_context
            }

            # Add to conversation history
            conversation_history['turns'].append(current_turn)

            # 🔧 CRITICAL FIX: Update last mentioned product in session state
            if extracted_product_context:
                conversation_history['session_state']['last_mentioned_product'] = extracted_product_context
                conversation_history['session_state']['last_product_query'] = user_query
                logger.info(f"🧠 STORED PRODUCT CONTEXT: {extracted_product_context['product_name']} (ID: {extracted_product_context['product_id']})")

            # Keep only last 10 turns to avoid memory bloat
            conversation_history['turns'] = conversation_history['turns'][-10:]

            # Store in Redis with TTL
            if hasattr(self, 'redis_client') and self.redis_client:
                self.redis_client.setex(key, 3600, json.dumps(conversation_history, cls=DateTimeJSONEncoder))  # 1 hour TTL

            logger.info(f"✅ Shopping conversation context stored for session {session_id}")

        except Exception as e:
            logger.error(f"❌ Error storing shopping conversation context: {e}")
            print_log(f"❌ Failed to store shopping context: {e}", 'error')

    def get_last_mentioned_product(self, user_id: str, session_id: str = None) -> Optional[Dict[str, Any]]:
        """🎯 Get the last mentioned product from conversation context for pronoun resolution"""
        try:
            # First try Redis
            if hasattr(self, 'redis_client') and self.redis_client:
                key = f"shopping_conversation_{user_id}_{session_id}"
                existing_data = self.redis_client.get(key)
                if existing_data:
                    conversation_history = json.loads(existing_data)
                    last_mentioned = conversation_history.get('session_state', {}).get('last_mentioned_product')
                    if last_mentioned:
                        logger.info(f"🧠 RETRIEVED LAST PRODUCT FROM REDIS: {last_mentioned.get('product_name')}")
                        return last_mentioned

            # Fallback to database
            conn = self.get_database_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT execution_result, user_query, timestamp
                    FROM conversation_context
                    WHERE (user_id = %s OR session_id = %s)
                    AND execution_result IS NOT NULL
                    AND timestamp >= NOW() - INTERVAL '1 hour'
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, (user_id, session_id or user_id))

                for row in cursor.fetchall():
                    execution_result_data = row[0]
                    if isinstance(execution_result_data, str):
                        try:
                            execution_result_data = json.loads(execution_result_data)
                        except (json.JSONDecodeError, TypeError):
                            continue
                    elif not isinstance(execution_result_data, list):
                        continue

                    # Look for product information in the execution results
                    for result in execution_result_data:
                        if isinstance(result, dict) and result.get('product_id'):
                            product_context = {
                                'product_id': result.get('product_id'),
                                'product_name': result.get('product_name'),
                                'price': result.get('price'),
                                'category': result.get('category'),
                                'brand': result.get('brand'),
                                'in_stock': result.get('in_stock', True),
                                'stock_quantity': result.get('stock_quantity', 0),
                            }
                            logger.info(f"🧠 RETRIEVED LAST PRODUCT FROM DB: {product_context['product_name']}")
                            return product_context

                cursor.close()
                conn.close()

        except Exception as e:
            logger.error(f"❌ Error retrieving last mentioned product: {e}")

        return None

    def get_conversation_history(self, user_id: str = "anonymous", limit: int = 5) -> List[Dict]:
        """Get recent conversation history with enhanced database fallback"""

        # First try Redis
        try:
            if self.redis_client:
                history_key = f"conversation_history:{user_id}"
                recent_keys = self.redis_client.lrange(history_key, 0, limit-1)

                history = []
                for key in recent_keys:
                    entry_data = self.redis_client.get(key)
                    if entry_data:
                        history.append(json.loads(entry_data))

                if history:
                    logger.info(f"🔍 Retrieved {len(history)} conversation entries from Redis for {user_id}")
                    return history
            else:
                # Memory fallback
                memory_history = self._memory_store.get(user_id, [])[-limit:]
                if memory_history:
                    logger.info(f"🔍 Retrieved {len(memory_history)} conversation entries from memory for {user_id}")
                    return memory_history

        except Exception as e:
            logger.error(f"❌ Redis history retrieval error: {e}")

        # 🆕 ENHANCED: Fallback to database for persistent memory
        try:
            conn = self.get_database_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_query, response_text, entities, execution_result, query_type, timestamp
                    FROM conversation_context
                    WHERE user_id = %s OR session_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, user_id, limit))

                db_history = []
                for row in cursor.fetchall():
                    # 🔧 ENHANCED: Safely handle JSON data that might be already parsed
                    entities_data = row[2]
                    if isinstance(entities_data, str):
                        try:
                            entities_data = json.loads(entities_data)
                        except (json.JSONDecodeError, TypeError):
                            entities_data = {}
                    elif not isinstance(entities_data, dict):
                        entities_data = {}

                    execution_result_data = row[3]
                    if isinstance(execution_result_data, str):
                        try:
                            execution_result_data = json.loads(execution_result_data)
                        except (json.JSONDecodeError, TypeError):
                            execution_result_data = []
                    elif not isinstance(execution_result_data, list):
                        execution_result_data = []

                    db_history.append({
                        "user_query": row[0],
                        "response": row[1],
                        "entities": entities_data,
                        "execution_result": execution_result_data,
                        "query_type": row[4],
                        "timestamp": row[5].isoformat() if row[5] else ""
                    })

                cursor.close()
                conn.close()

                if db_history:
                    logger.info(f"🔍 Retrieved {len(db_history)} conversation entries from database for {user_id}")
                    return db_history

        except Exception as e:
            logger.error(f"❌ Database history retrieval error: {e}")

        logger.warning(f"⚠️ No conversation history found for {user_id}")
        return []

    def get_enhanced_conversation_memory(self, user_id: str, session_id: str = None, limit: int = 10) -> Dict[str, Any]:
        """🧠 Get enhanced conversation memory with context-aware product and entity tracking"""

        try:
            conn = self.get_database_connection()
            if not conn:
                return {"recent_context": [], "mentioned_products": [], "conversation_summary": "No database connection"}

            cursor = conn.cursor()

            # Get recent conversation with product mentions
            cursor.execute("""
                SELECT user_query, response_text, entities, execution_result, query_type, timestamp
                FROM conversation_context
                WHERE (user_id = %s OR session_id = %s)
                AND timestamp >= NOW() - INTERVAL '2 hours'
                ORDER BY timestamp DESC
                LIMIT %s
            """, (user_id, session_id or user_id, limit))

            recent_conversations = []
            mentioned_products = []
            last_product_context = None

            for row in cursor.fetchall():
                # 🔧 CRITICAL FIX: Handle both string and dict data types properly
                entities_data = row[2]
                if isinstance(entities_data, str):
                    try:
                        entities_data = json.loads(entities_data)
                    except (json.JSONDecodeError, TypeError):
                        entities_data = {}
                elif not isinstance(entities_data, dict):
                    entities_data = {}

                execution_result_data = row[3]
                if isinstance(execution_result_data, str):
                    try:
                        execution_result_data = json.loads(execution_result_data)
                    except (json.JSONDecodeError, TypeError):
                        execution_result_data = []
                elif not isinstance(execution_result_data, list):
                    execution_result_data = []

                conv_entry = {
                    "user_query": row[0],
                    "response": row[1],
                    "entities": entities_data,
                    "execution_result": execution_result_data,
                    "query_type": row[4],
                    "timestamp": row[5].isoformat() if row[5] else ""
                }
                recent_conversations.append(conv_entry)

                # Extract product information from execution results
                if conv_entry["execution_result"]:
                    for result in conv_entry["execution_result"]:
                        if isinstance(result, dict) and 'product_name' in result:
                            product_info = {
                                "product_name": result.get('product_name'),
                                "product_id": result.get('product_id'),
                                "price": result.get('price'),
                                "category": result.get('category'),
                                "brand": result.get('brand'),
                                "mentioned_in_query": conv_entry["user_query"],
                                "timestamp": conv_entry["timestamp"]
                            }
                            mentioned_products.append(product_info)
                            last_product_context = product_info

            cursor.close()
            conn.close()

            # Create conversation summary
            conversation_summary = ""
            if recent_conversations:
                last_query = recent_conversations[0]["user_query"]
                if mentioned_products:
                    last_product = mentioned_products[0]["product_name"]
                    conversation_summary = f"Recent discussion about {last_product}. Last query: {last_query[:100]}..."
                else:
                    conversation_summary = f"Recent conversation. Last query: {last_query[:100]}..."

            return {
                "recent_context": recent_conversations,
                "mentioned_products": mentioned_products,
                "last_product_context": last_product_context,
                "conversation_summary": conversation_summary,
                "context_available": len(recent_conversations) > 0
            }

        except Exception as e:
            logger.error(f"❌ Error getting enhanced conversation memory: {e}")
            return {"recent_context": [], "mentioned_products": [], "conversation_summary": "Error retrieving memory"}

    def _get_user_friendly_error_message(self, error_message: str, user_query: str) -> str:
        """
        🛡️ Convert technical SQL errors into user-friendly messages
        Following OWASP security guidelines to prevent information disclosure

        🚀 Enhanced error handling with debugging support
        Based on Python debugging best practices from the tutorial
        """
        try:
            # Enhanced debugging: Log the full error context
            logger.error(f"🐛 DEBUG INFO - User query: '{user_query}', Error: '{error_message}'")

            # Handle specific database operation errors
            if "does not exist" in error_message.lower():
                # Check if it's a cart operation that should be handled by application layer
                if "cart" in error_message.lower():
                    logger.warning(f"🔧 DEBUGGING: Cart operation detected in SQL layer - should be handled by OrderAIAssistant")
                    return "I see you're trying to manage your cart! Let me handle that properly for you. Please try your request again, and I'll use our shopping system. 🛒✨"

                # Check for other missing tables
                table_name = self._extract_table_name_from_error(error_message)
                if table_name:
                    logger.error(f"🚨 DATABASE SCHEMA ERROR: Table '{table_name}' does not exist in database")
                    return f"I'm experiencing a technical issue with our database. Our team has been notified. Please try a different query or contact support at +234 (702) 5965-922. 🔧💙"

            # Handle permission/access errors
            if "permission denied" in error_message.lower() or "access" in error_message.lower():
                logger.error(f"🔒 DATABASE ACCESS ERROR: {error_message}")
                return "I don't have permission to access that information for security reasons. Please contact our support team for assistance! 🔒💙"

            # Handle SQL syntax errors with debugging info
            if "syntax error" in error_message.lower():
                logger.error(f"📝 SQL SYNTAX ERROR: Generated invalid SQL for query '{user_query}'")
                return "I'm having trouble understanding your request. Could you try rephrasing it? Our team has been notified of this issue. 🤔💙"

            # Handle connection errors
            if "connection" in error_message.lower() or "timeout" in error_message.lower():
                logger.error(f"🌐 DATABASE CONNECTION ERROR: {error_message}")
                return "I'm having trouble connecting to our database right now. Please try again in a moment! 🔄💙"

            # Handle constraint violations (like foreign key errors)
            if "constraint" in error_message.lower() or "foreign key" in error_message.lower():
                logger.error(f"🔗 DATABASE CONSTRAINT ERROR: {error_message}")
                return "There's a data consistency issue. Our technical team has been notified. Please try a different approach! 🔧💙"

            # Enhanced debugging for column errors
            if "column" in error_message.lower() and "does not exist" in error_message.lower():
                column_name = self._extract_column_name_from_error(error_message)
                logger.error(f"📊 DATABASE COLUMN ERROR: Column '{column_name}' not found - schema mismatch detected")
                return "I'm having trouble accessing the requested information due to a database structure issue. Our team has been notified! 📊💙"

            # Generic fallback with enhanced debugging
            logger.error(f"🔍 UNHANDLED DATABASE ERROR: {error_message} | User Query: {user_query}")
            return "I encountered an unexpected issue while processing your request. Our technical team has been notified and will investigate! Please try again or contact support. 🚀💙"

        except Exception as debug_error:
            # Handle errors in error handling (meta-debugging)
            logger.error(f"❌ ERROR IN ERROR HANDLER: {debug_error}")
            return "I'm experiencing technical difficulties. Please contact our support team at +234 (702) 5965-922 for immediate assistance! 😊💙"

    def _extract_table_name_from_error(self, error_message: str) -> str:
        """Extract table name from database error for debugging"""
        try:
            import re
            # Pattern to match 'relation "table_name" does not exist'
            match = re.search(r'relation "([^"]+)" does not exist', error_message)
            if match:
                return match.group(1)

            # Pattern to match 'table "table_name" doesn't exist'
            match = re.search(r'table "([^"]+)" doesn\'t exist', error_message)
            if match:
                return match.group(1)

            return ""
        except Exception:
            return ""

    def _extract_column_name_from_error(self, error_message: str) -> str:
        """Extract column name from database error for debugging"""
        try:
            import re
            # Pattern to match 'column "column_name" does not exist'
            match = re.search(r'column "([^"]+)" does not exist', error_message)
            if match:
                return match.group(1)
            return ""
        except Exception:
            return ""

    def detect_user_sentiment(self, user_query: str) -> Dict[str, Any]:
        """
        🎭 Detect user sentiment and emotional state for empathetic responses
        """
        sentiment_data = {
            'emotion': 'neutral',
            'intensity': 'medium',
            'keywords': [],
            'empathy_needed': False
        }

        query_lower = user_query.lower()

        # Frustrated/Angry indicators
        if any(word in query_lower for word in ['urgent', 'frustrated', 'angry', 'annoyed', 'terrible', 'awful', 'hate', 'worst', 'stupid', 'ridiculous']):
            sentiment_data.update({
                'emotion': 'frustrated',
                'intensity': 'high',
                'empathy_needed': True,
                'keywords': ['urgent', 'frustrated', 'angry']
            })

        # Worried/Anxious indicators
        elif any(word in query_lower for word in ['worried', 'anxious', 'concerned', 'scared', 'nervous', 'help me', 'please help', 'urgent']):
            sentiment_data.update({
                'emotion': 'worried',
                'intensity': 'high',
                'empathy_needed': True,
                'keywords': ['worried', 'anxious', 'help needed']
            })

        # Confused indicators
        elif any(word in query_lower for word in ['confused', 'don\'t understand', 'unclear', 'lost', 'what does', 'how do']):
            sentiment_data.update({
                'emotion': 'confused',
                'intensity': 'medium',
                'empathy_needed': True,
                'keywords': ['confused', 'needs guidance']
            })

        # Happy/Positive indicators
        elif any(word in query_lower for word in ['thank', 'thanks', 'great', 'awesome', 'wonderful', 'perfect', 'love', 'amazing']):
            sentiment_data.update({
                'emotion': 'happy',
                'intensity': 'medium',
                'empathy_needed': False,
                'keywords': ['positive', 'grateful']
            })

        # Impatient indicators
        elif any(word in query_lower for word in ['still waiting', 'taking too long', 'when will', 'hurry', 'asap', 'immediately']):
            sentiment_data.update({
                'emotion': 'impatient',
                'intensity': 'high',
                'empathy_needed': True,
                'keywords': ['time-sensitive', 'waiting']
            })

        return sentiment_data

    def get_empathetic_response_style(self, sentiment_data: Dict[str, Any], query_context: QueryContext) -> str:
        """
        💝 Generate empathetic response style based on detected sentiment
        """
        emotion = sentiment_data['emotion']
        intensity = sentiment_data['intensity']

        if emotion == 'frustrated':
            return """
EMOTIONAL CONTEXT: Customer is frustrated and needs immediate empathy
RESPONSE STYLE:
- Start with sincere apology and acknowledgment: "I completely understand your frustration 😔"
- Use calming emojis: 😔, 💙, 🤗
- Be extra helpful and solution-focused
- Offer immediate assistance: "Let me help you right away"
- End with reassurance: "I'm here to make this right for you ✨"
"""
        elif emotion == 'worried':
            return """
EMOTIONAL CONTEXT: Customer is worried/anxious and needs reassurance
RESPONSE STYLE:
- Acknowledge their concern: "I understand you're worried 🤗"
- Use comforting emojis: 🤗, 💙, ✨, 🌟
- Provide clear, step-by-step guidance
- Offer continuous support: "I'm here to help you through this"
- End with positive assurance: "Everything will be okay! 🌟"
"""
        elif emotion == 'confused':
            return """
EMOTIONAL CONTEXT: Customer is confused and needs patient guidance
RESPONSE STYLE:
- Show understanding: "No worries, I'm here to help clarify! 😊"
- Use friendly emojis: 😊, 💡, 🎯, ✨
- Break down information clearly
- Use simple, easy-to-understand language
- Encourage questions: "Feel free to ask if anything is unclear! 💡"
"""
        elif emotion == 'happy':
            return """
EMOTIONAL CONTEXT: Customer is positive and happy
RESPONSE STYLE:
- Mirror their positivity: "So happy to help! 😊"
- Use joyful emojis: 😊, 🎉, ✨, 🌟, 💚
- Be enthusiastic and energetic
- Share in their satisfaction
- Keep the positive momentum: "Glad I could help! 🎉"
"""
        elif emotion == 'impatient':
            return """
EMOTIONAL CONTEXT: Customer is impatient and needs quick action
RESPONSE STYLE:
- Acknowledge urgency: "I understand time is important! ⚡"
- Use action emojis: ⚡, 🚀, 💨, ⏰
- Be direct and efficient
- Provide immediate next steps
- Show speed: "Let me get this sorted quickly for you! 🚀"
"""
        else:
            return """
EMOTIONAL CONTEXT: Neutral customer interaction
RESPONSE STYLE:
- Be warm and friendly: "Happy to help! 😊"
- Use supportive emojis: 😊, ✨, 💙, 🌟
- Maintain professional warmth
- Be solution-oriented
- End positively: "Hope this helps! ✨"
"""

    def generate_nigerian_response(self, query_context: QueryContext, conversation_history: List[Dict] = None, session_context: Dict[str, Any] = None) -> str:
        """🇳🇬 Generate Nigerian-style empathetic response with intelligent recommendations"""

        # 🚨 CRITICAL ERROR HANDLING: Check for processing errors first
        if query_context.error_message:
            logger.error(f"❌ Error detected in query context, generating safe fallback response: {query_context.error_message}")

            # Determine user role for tailored error response
            user_role = determine_user_role(session_context).value

            if user_role in ['admin', 'super_admin']:
                # For admins, provide a concise, professional error message
                return "📊 **Data Unavailable**: I was unable to retrieve the requested analytics due to an internal system error. Please try again later or contact technical support if the issue persists."
            else:
                # For customers and support agents, provide a user-friendly, empathetic error message
                return "I'm sorry, but I encountered a technical issue and couldn't get the information you requested. 😔 Our team has been notified. Please try again in a little while! 🙏"

        try:
            # 🆕 ENHANCED: Get enhanced conversation memory
            user_id = session_context.get('user_id', 'anonymous') if session_context else 'anonymous'
            session_id = session_context.get('session_id') if session_context else None

            enhanced_memory = self.get_enhanced_conversation_memory(user_id, session_id, limit=5)

            # Detect if this is a contextual reference (like "it", "this", "that product")
            contextual_words = ['it', 'this', 'that', 'they', 'them', 'one', 'the product', 'the item']
            user_query_lower = query_context.user_query.lower()
            is_contextual_reference = any(word in user_query_lower for word in contextual_words)

            # Enhanced memory guidance for AI
            memory_guidance = ""
            if enhanced_memory.get("context_available"):
                memory_guidance = f"""
                🧠 ENHANCED CONVERSATION MEMORY:
                - {enhanced_memory['conversation_summary']}
                - Products recently discussed: {len(enhanced_memory['mentioned_products'])} items
                """

                # If user is making contextual reference and we have product context
                if is_contextual_reference and enhanced_memory.get('last_product_context'):
                    last_product = enhanced_memory['last_product_context']
                    memory_guidance += f"""
                - ⚠️ CONTEXTUAL REFERENCE DETECTED: User likely referring to "{last_product['product_name']}"
                - Last mentioned product: {last_product['product_name']} (₦{last_product.get('price', 'N/A')})
                - CRITICAL: When user says "it", "this", or "that", they mean: {last_product['product_name']}
                """

                    # If it's an order/purchase request with contextual reference
                    order_intents = ['order', 'buy', 'purchase', 'add to cart', 'want to order']
                    if any(intent in user_query_lower for intent in order_intents) and is_contextual_reference:
                        memory_guidance += f"""
                - 🛒 SHOPPING ACTION WITH CONTEXT: User wants to {user_query_lower} the {last_product['product_name']}
                - Provide shopping assistance for: {last_product['product_name']}
                """

            customer_id = session_context.get('customer_id') if session_context else None

            # 🆕 DETECT USER SENTIMENT AND GET EMOTIONAL RESPONSE STYLE
            sentiment_data = self.detect_user_sentiment(query_context.user_query)
            empathetic_style = self.get_empathetic_response_style(sentiment_data, query_context)
            logger.info(f"🎭 Detected emotion: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})")

            # Get conversation context for reference
            conversation_memory = None
            if self.memory_system:
                try:
                    conversation_memory = self.memory_system.get_conversation_context(session_id or user_id)
                except Exception as e:
                    logger.warning(f"⚠️ Could not get conversation memory: {e}")

            if conversation_memory:
                buffer_memory = conversation_memory.get('buffer_memory', {})
                session_state = conversation_memory.get('session_state', {})
                entity_memory = conversation_memory.get('entity_memory', {})

                # Recent conversation awareness
                if buffer_memory.get('recent_turns'):
                    recent_turns = buffer_memory['recent_turns'][:3]  # Last 3 turns
                    last_user_input = buffer_memory.get('last_user_input', '')
                    last_ai_response = buffer_memory.get('last_ai_response', '')

                    memory_guidance += f"""
                    🧠 CONVERSATION MEMORY CONTEXT:
                    - Previous user input: "{last_user_input[:100]}..."
                    - Previous AI response: "{last_ai_response[:100]}..."
                    - Recent conversation turns: {len(recent_turns)}
                    - CRITICAL: Reference what was just discussed to maintain context!
                    """

            # Get intelligent recommendations for product-related queries
            recommendations_data = None
            if query_context.query_type in [QueryType.PRODUCT_PERFORMANCE, QueryType.PRODUCT_RECOMMENDATIONS,
                                          QueryType.SHOPPING_ASSISTANCE, QueryType.PRODUCT_INFO_GENERAL]:
                if customer_id:
                    recommendations_data = self.get_intelligent_product_recommendations(
                        customer_id, query_context.user_query, query_context)

            # Build context for AI response generation
            enhanced_context = {
                'query_result': query_context.execution_result,
                'query_type': query_context.query_type.value,
                'user_query': query_context.user_query,
                'conversation_history': conversation_history[-3:] if conversation_history else [],  # Last 3 exchanges
                'nigerian_time_context': NigerianBusinessIntelligence.get_nigerian_timezone_context(),
                'session_context': session_context or {},
                'recommendations': recommendations_data,
                'customer_mood': sentiment_data['emotion'],  # 🆕 Add detected emotion
                'sentiment_data': sentiment_data,  # 🆕 Add full sentiment data
                'empathetic_style': empathetic_style,  # 🆕 Add emotional response style
                'support_context': None,
                'enhanced_memory': enhanced_memory,  # 🆕 Add enhanced memory
                'memory_guidance': memory_guidance  # 🆕 Add memory guidance
            }

            # Add support context if available
            if customer_id and recommendations_data and 'support_context' in recommendations_data:
                enhanced_context['support_context'] = recommendations_data['support_context']

            # Generate response with enhanced context
            system_prompt = self._build_enhanced_system_prompt(enhanced_context)

            # 🚨 CRITICAL FIX: Enforce strict, non-verbose, factual persona for admins
            user_role = determine_user_role(session_context).value
            if user_role in ['admin', 'super_admin']:
                system_prompt = f"""You are a Business Intelligence Assistant. Your only goal is to answer the user's question based *strictly* on the provided data.

                **RULES:**
                1.  **Direct Answer:** Look at the "Query results" and directly answer the "customer query".
                2.  **Stick to the Data:** Do NOT mention any information, numbers, or details not explicitly present in the "Query results".
                3.  **No Hallucination:** Do not make up customer names, IDs, or any other details.
                4.  **Be Concise:** Do not use conversational filler. Provide a direct, data-driven response. Use tables if appropriate.
                """

            # 🔧 SPECIAL HANDLING: Check if this is an order cancellation/update query
            is_order_cancellation = (
                'cancel' in query_context.user_query.lower() or
                'no longer interested' in query_context.user_query.lower()
            ) and any(
                result.get('message') == 'Query executed successfully' and
                result.get('affected_rows', 0) > 0
                for result in query_context.execution_result
            )

            # Generate AI response with special handling for order operations
            if is_order_cancellation:
                affected_rows = next(
                    (result.get('affected_rows', 0) for result in query_context.execution_result
                     if result.get('affected_rows')), 0
                )

                # Special response for order cancellation
                response_content = f"""
                Based on the customer query: "{query_context.user_query}"

                ✅ Order cancellation successful: {affected_rows} order(s) have been cancelled/returned.

                Customer emotion detected: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})

                {memory_guidance}

                Provide a compassionate, understanding response about order cancellation. Acknowledge their decision,
                confirm the cancellation, and offer assistance for future orders. Use appropriate emojis for the emotional tone.
                """
            else:
                # 🚨 ADMIN RESPONSE GENERATION: Use a separate, brutally direct prompt
                if user_role in ['admin', 'super_admin']:
                    # Format currency values in the results
                    formatted_results = self._format_currency_in_results(query_context.execution_result, session_context)

                    # Determine if we should use table format (5+ items)
                    result_count = len(query_context.execution_result)
                    format_instruction = ""

                    if result_count >= 5:
                        format_instruction = "- Present the results in a simple markdown table (5+ items detected)."
                    elif result_count == 1:
                        format_instruction = "- Give a direct answer (single result detected). No table needed."
                    else:
                        format_instruction = "- List the results clearly without table format (2-4 items detected)."

                    response_content = f"""
                    User Query: "{query_context.user_query}"
                    Database Results: {safe_json_dumps(formatted_results, max_items=50)}

                    INSTRUCTIONS FOR ADMIN RESPONSE:
                    - Answer using ONLY the provided Database Results.
                    - Be DIRECT and CONCISE. No conversational filler.
                    - Use Nigerian Naira format (₦) for monetary values.
                    - Use business emojis sparingly: 📊, 📈, 💰
                    {format_instruction}
                    - Do not say "Not Available" or make up data.
                    - Do not mention that you are an AI.
                    """
                else:
                    # Original response generation for customers and support agents
                    # 🔧 DYNAMIC RESULT LIMITING: Show more results for specific query types
                    max_items_to_show = 5  # Default
                    query_lower = query_context.user_query.lower()

                    if any(keyword in query_lower for keyword in ['full order history', 'all orders', 'complete history', 'entire history']):
                        max_items_to_show = 10  # Show up to 10 orders for full history requests
                    elif any(keyword in query_lower for keyword in ['order history', 'my orders', 'orders for customer']):
                        max_items_to_show = 7   # Show up to 7 orders for general order history
                    elif query_context.query_type == QueryType.ORDER_ANALYTICS:
                        max_items_to_show = 7   # Show more orders for analytics queries
                    elif any(keyword in query_lower for keyword in ['customers on', 'platinum tier', 'gold tier', 'silver tier', 'bronze tier', 'list customers', 'customers are on', 'tier customers', 'how many customers']):
                        max_items_to_show = 15  # Show up to 15 customers for tier/customer listing queries
                    elif query_context.query_type == QueryType.CUSTOMER_ANALYSIS:
                        max_items_to_show = 10  # Show up to 10 customers for customer analysis queries

                    # Format currency values in the results
                    formatted_results = self._format_currency_in_results(query_context.execution_result[:max_items_to_show], session_context)

                    # Determine formatting based on result count
                    result_count = len(query_context.execution_result)
                    format_instruction = ""

                    if result_count >= 5:
                        format_instruction = "Use a clear table format to organize the data (5+ items detected)."
                    elif result_count == 1:
                        format_instruction = "Provide a direct, conversational answer without tables (single result)."
                    else:
                        format_instruction = "List the results in a clear, conversational format without tables (2-4 items)."

                    # Check if this is a customer listing query to provide specific instructions
                    customer_listing_instruction = ""
                    if any(keyword in query_lower for keyword in ['customers on', 'platinum tier', 'gold tier', 'silver tier', 'bronze tier', 'list customers', 'customers are on', 'tier customers', 'how many customers']):
                        actual_count = len(query_context.execution_result)
                        customer_listing_instruction = f"""
                        IMPORTANT: This is a customer listing query. The database returned {actual_count} customers.
                        - Show ALL {actual_count} customers in your response
                        - {format_instruction}
                        - State the correct total count: {actual_count} customers
                        - Do NOT limit to just a few examples - show the complete list
                        """

                    # 🚨 CRITICAL: Check if we have actual results to prevent hallucination
                    has_results = len(query_context.execution_result) > 0

                    response_content = f"""
                    Customer Query: "{query_context.user_query}"
                    Database Results: {safe_json_dumps(formatted_results, max_items=max_items_to_show)}

                    🚨 CRITICAL ANTI-HALLUCINATION RULES:
                    {"- Database returned " + str(len(query_context.execution_result)) + " results"}
                    {"- You HAVE data to work with - show what's available" if has_results else "- NO RESULTS FOUND - DO NOT make up products, prices, or recommendations"}
                    {"- Only mention products that exist in the database results above" if has_results else "- Be honest: 'We don't currently have that item in stock'"}
                    {"- Use actual prices from database results only" if has_results else "- DO NOT suggest alternative products unless they're in the database results"}
                    {"- NEVER invent products, prices, or availability information" if not has_results else ""}

                    RESPONSE REQUIREMENTS:
                    - Customer emotion detected: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})
                    - Always use Nigerian Naira format (₦) for monetary values
                    - {format_instruction}
                    - Use appropriate emojis based on detected emotion
                    - Be warm and conversational but TRUTHFUL
                    {"- If no results: politely explain we don't have the item and suggest they contact support or check back later" if not has_results else ""}

                    {customer_listing_instruction}

                    {memory_guidance if has_results else ""}

                    {f"Intelligent recommendations available: {recommendations_data['total_recommendations']} products across {len(recommendations_data.get('recommendations', {}))} categories" if recommendations_data and recommendations_data.get('success') and has_results else ""}

                    Provide a helpful, honest Nigerian customer support response. NEVER make up products or prices.
                    """

            # Generate AI response
            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": response_content}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            ai_response = response.choices[0].message.content.strip()

            # 🔧 Strip markdown formatting while keeping emojis
            ai_response = self._strip_markdown_formatting(ai_response)

            # 🆕 LOG AI RESPONSE IN TERMINAL (matching user query format)
            logger.info(f"🤖 AI: {ai_response}")

            # 🚨 CRITICAL: Only enhance with recommendations if we have actual database results
            # This prevents AI from suggesting fake products when no results found
            if (recommendations_data and recommendations_data.get('success') and
                recommendations_data.get('recommendations') and len(query_context.execution_result) > 0):
                ai_response = self._enhance_response_with_recommendations(ai_response, recommendations_data)
                # Strip markdown again after enhancement
                ai_response = self._strip_markdown_formatting(ai_response)

            return ai_response

        except Exception as e:
            logger.error(f"❌ Error generating Nigerian response: {e}")
            sentiment_fallback = {'emotion': 'neutral', 'intensity': 0.5}
            return self._get_fallback_emotional_response(query_context, sentiment_fallback)

    def generate_customer_support_contact_response(self, user_query: str) -> str:
        """🆕 Generate customer support contact information response"""
        try:
            # Detect user sentiment for appropriate tone
            sentiment_data = self.detect_user_sentiment(user_query)
            emotion = sentiment_data['emotion']

            # Choose appropriate emojis based on emotion
            if emotion == 'frustrated':
                emojis = ['😔', '💙', '🤗', '✨']
                tone = "I completely understand your frustration. Let me help you get the support you need right away!"
            elif emotion == 'worried':
                emojis = ['🤗', '💙', '✨', '🌟']
                tone = "Don't worry, our support team is here to help you!"
            elif emotion == 'impatient':
                emojis = ['⚡', '🚀', '💨']
                tone = "I understand time is important! Here's how to reach our support team quickly:"
            else:
                emojis = ['😊', '✨', '💙', '🌟']
                tone = "Happy to help you get in touch with our support team!"

            # Format contact information with emojis
            contact_info = f"""
{tone} {emojis[0]}

Here are the ways to contact raqibtech.com customer support:

📧 Email: {self.CUSTOMER_SUPPORT_CONTACTS['primary_email']}
📞 Phone: {self.CUSTOMER_SUPPORT_CONTACTS['primary_phone']}
💬 WhatsApp: {self.CUSTOMER_SUPPORT_CONTACTS['whatsapp']}
🌐 Support Portal: {self.CUSTOMER_SUPPORT_CONTACTS['support_portal']}
💬 Live Chat: {self.CUSTOMER_SUPPORT_CONTACTS['live_chat']}

⏰ Business Hours: {self.CUSTOMER_SUPPORT_CONTACTS['business_hours']}
🔄 Response Time: {self.CUSTOMER_SUPPORT_CONTACTS['response_time']}
🗣️ Languages: {self.CUSTOMER_SUPPORT_CONTACTS['languages']}

Our team is ready to assist you with orders, delivery, payments, and any questions about raqibtech.com! {emojis[1]}
            """.strip()

            logger.info(f"🤖 AI: {contact_info}")
            return contact_info

        except Exception as e:
            logger.error(f"❌ Error generating support contact response: {e}")
            return f"You can contact our customer support team at {self.CUSTOMER_SUPPORT_CONTACTS['primary_email']} or {self.CUSTOMER_SUPPORT_CONTACTS['primary_phone']} for assistance! 😊✨"

    def _build_enhanced_system_prompt(self, context: Dict[str, Any]) -> str:
        """🎯 Build enhanced system prompt with recommendation and emotion context"""

        # 🔧 CRITICAL FIX: Extract authentication info from nested session_context
        session_context = context.get('session_context', {})
        user_authenticated = session_context.get('user_authenticated', False)
        customer_id = session_context.get('customer_id')
        user_id = session_context.get('user_id', 'anonymous')

        # 🆕 EMOTIONAL RESPONSE INTEGRATION
        emotion_guidance = ""
        if context.get('sentiment_data'):
            sentiment = context['sentiment_data']
            emotion = sentiment['emotion']
            intensity = sentiment['intensity']

            emotion_guidance = f"""
            🎭 CUSTOMER EMOTION DETECTED: {emotion.upper()} (Intensity: {intensity})

            {context.get('empathetic_style', '')}

            CRITICAL: Follow the emotional style guidelines above - use the suggested emojis and tone!
            MANDATORY: Include appropriate emojis in your response based on the customer's emotional state.
            """

        mood_guidance = ""
        if context.get('customer_mood'):
            mood = context['customer_mood']
            if mood == "frustrated":
                mood_guidance = """
                🔥 CUSTOMER MOOD: FRUSTRATED - Be genuinely empathetic and solution-focused.
                - Start with sincere apology: "I completely understand your frustration 😔"
                - Use calming emojis: 😔, 💙, 🤗, ✨
                - Focus on solving their immediate problem first
                - End with reassurance: "I'm here to make this right for you ✨"
                """
            elif mood == "worried":
                mood_guidance = """
                😰 CUSTOMER MOOD: WORRIED - Be reassuring and supportive.
                - Acknowledge concern: "I understand you're worried 🤗"
                - Use comforting emojis: 🤗, 💙, ✨, 🌟
                - Provide clear guidance and continuous support
                - End with positive assurance: "Everything will be okay! 🌟"
                """
            elif mood == "confused":
                mood_guidance = """
                🤔 CUSTOMER MOOD: CONFUSED - Be patient and clear.
                - Show understanding: "No worries, I'm here to help clarify! 😊"
                - Use friendly emojis: 😊, 💡, 🎯, ✨
                - Break down information clearly
                - Encourage questions: "Feel free to ask if anything is unclear! 💡"
                """
            elif mood == "happy":
                mood_guidance = """
                😊 CUSTOMER MOOD: HAPPY - Mirror their positivity.
                - Share their joy: "So happy to help! 😊"
                - Use joyful emojis: 😊, 🎉, ✨, 🌟, 💚
                - Be enthusiastic and energetic
                - Keep positive momentum: "Glad I could help! 🎉"
                """
            elif mood == "impatient":
                mood_guidance = """
                ⏰ CUSTOMER MOOD: IMPATIENT - Be quick and action-oriented.
                - Acknowledge urgency: "I understand time is important! ⚡"
                - Use action emojis: ⚡, 🚀, 💨, ⏰
                - Be direct and efficient
                - Show speed: "Let me get this sorted quickly for you! 🚀"
                """
            else:
                # Default neutral mood with friendly emojis
                mood_guidance = """
                😊 CUSTOMER MOOD: NEUTRAL - Be warm and helpful.
                - Be welcoming: "Happy to help! 😊"
                - Use supportive emojis: 😊, ✨, 💙, 🌟
                - Maintain professional warmth
                - End positively: "Hope this helps! ✨"
                """

        recommendations_guidance = ""
        if context.get('recommendations') and context['recommendations'].get('success'):
            recs = context['recommendations']['recommendations']
            recommendations_guidance = f"""
            RECOMMENDATIONS AVAILABLE: {context['recommendations']['total_recommendations']} products
            - Only mention 2-3 most relevant products maximum
            - Integrate naturally into conversation, don't create separate sections
            - Focus on how they help solve the customer's specific need
            - Include price in Nigerian Naira format
            """

        # 🧠 CONVERSATION MEMORY CONTEXT
        memory_guidance = ""
        conversation_memory = session_context.get('conversation_memory', {})

        if conversation_memory:
            buffer_memory = conversation_memory.get('buffer_memory', {})
            session_state = conversation_memory.get('session_state', {})
            entity_memory = conversation_memory.get('entity_memory', {})

            # Recent conversation awareness
            if buffer_memory.get('recent_turns'):
                recent_turns = buffer_memory['recent_turns'][:3]  # Last 3 turns
                last_user_input = buffer_memory.get('last_user_input', '')
                last_ai_response = buffer_memory.get('last_ai_response', '')

                # 🚨 CRITICAL: Only provide recent memory context if it's relevant to current query
                # This prevents inappropriate context mixing from unrelated conversations
                current_query_lower = context.get('user_query', '').lower()
                last_input_lower = last_user_input.lower()

                # Check if previous context is relevant (similar topic or continuation)
                is_relevant_context = any([
                    len(set(current_query_lower.split()) & set(last_input_lower.split())) >= 2,  # Common words
                    any(keyword in current_query_lower for keyword in ['continue', 'also', 'what about', 'and', 'too']),  # Continuation signals
                    len(last_user_input.strip()) < 10  # Very short previous input
                ])

                if is_relevant_context:
                    memory_guidance += f"""
                    🧠 RELEVANT CONVERSATION CONTEXT:
                    - Previous user input: "{last_user_input[:100]}..."
                    - Previous AI response: "{last_ai_response[:100]}..."
                    - CRITICAL: Reference what was just discussed to maintain context!
                    """
                else:
                    memory_guidance += f"""
                    🧠 CONVERSATION CONTEXT:
                    - New topic detected - treat as fresh conversation
                    - Previous context not relevant to current query
                    - Focus on current user query only
                    """

            # Shopping session state awareness
            if session_state.get('session_exists'):
                cart_items = session_state.get('cart_item_count', 0)
                conversation_stage = session_state.get('conversation_stage', 'browsing')
                last_product_mentioned = session_state.get('last_product_mentioned')
                delivery_address = session_state.get('delivery_address')
                payment_method = session_state.get('payment_method')

                memory_guidance += f"""

                🛒 SHOPPING SESSION STATE:
                - Cart items: {cart_items}
                - Conversation stage: {conversation_stage}
                - Last product mentioned: {last_product_mentioned.get('product_name') if last_product_mentioned else 'None'}
                - Delivery address: {delivery_address.get('full_address') if delivery_address else 'Not set'}
                - Payment method: {payment_method or 'Not selected'}
                - CRITICAL: Continue the shopping flow based on current stage!
                """

            # Entity memory awareness
            entities = entity_memory.get('entities', {})
            if entities:
                memory_guidance += f"""

                🏷️ ENTITY MEMORY:
                - Products mentioned: {entities.get('product_info', {}).get('product_name', 'None')}
                - Delivery preferences: {entities.get('delivery_address', 'None')}
                - Payment preferences: {entities.get('payment_method', 'None')}
                - CRITICAL: Use this context to provide relevant responses!
            """

        # 🎯 DYNAMIC PERSONA BASED ON USER ROLE
        user_role = determine_user_role(session_context).value

        if user_role in ['admin', 'super_admin']:
            persona_intro = f"""You are a Business Intelligence Assistant for raqibtech.com executives. Your goal is to provide direct, data-driven answers.

            🎯 RESPONSE STYLE FOR ADMINS:
            - Be CONCISE and DIRECT - no fluff or verbose explanations
            - Use business emojis sparingly: 📊, 📈, 💰
            - Start with direct answer, then provide supporting data
            - No marketing language or customer service tone
            - Format data in simple tables when relevant

            ❌ AVOID: Long explanations, customer service language, excessive emojis, promotional content
            ✅ PROVIDE: Direct answers, key metrics, actionable data

            - Always refer to customers in third person (they/their/them) when talking to support agents.

            **RULES:**
            - **BE CONCISE:** Provide short, direct answers. No verbose explanations.
            - **STICK TO THE FACTS:** Base your response *only* on the data provided in the `Query results`.
            - **NO HALLUCINATION:** Do not add any information not present in the results. If asked for revenue, give only the revenue. Do not add customer lists or other details unless the query explicitly asks for them.
            - **DO NOT BE CHATTY:** Avoid conversational filler. Get straight to the point.

            """

        elif user_role == 'support_agent':
            persona_intro = f"""You are a Customer Support Agent's AI Assistant for raqibtech.com.
 THE FACTS:** Base your response *only* on the data provided in the `Query results`.
            - **NO HALLUCINATION:** Do not add any information not present in the results. If asked for revenue, give only the revenue. Do not add customer lists or other details unless the query explicitly asks for them.
            - **USE MARKDOWN:** Use tables and lists for clarity.
            Your role is to assist the support agent by providing accurate information quickly and efficiently.
            - Provide clear, factual answers based on the query results.
            - Use a professional and helpful tone.
            - You can provide additional relevant information if it helps the agent solve the customer's problem.
            """
        else: # Customer
            persona_intro = f"""You are a friendly and empathetic Nigerian Customer Support Assistant for raqibtech.com.

            Your goal is to help customers with their orders and provide a great experience.
            - Always be polite and use a warm, conversational tone.
            - Use Nigerian colloquialisms and slang where appropriate to sound authentic and friendly.
            - Use emojis to convey tone.
            - Address the customer by name if available.

            🚨 CRITICAL ANTI-HALLUCINATION RULES FOR CUSTOMERS:
            - **NEVER make up products, prices, or availability information**
            - **Only mention products that exist in the database query results**
            - **If no products found, be honest: "We don't currently have that item"**
            - **Never suggest alternative products unless they're in the actual database results**
            - **Do not invent prices, discounts, or product features**
            - **Be truthful about stock status - only use database information**
            """

        return f"""
        {persona_intro}

        🚨 CRITICAL AUTHORIZATION & SECURITY RULES - MUST FOLLOW:
        🔐 ROLE-BASED ACCESS CONTROL (RBAC):
        - User Role: {user_role}
        - Access Level: {RoleBasedAccessControl.get_user_role_info(determine_user_role(session_context)).max_data_access_level}

        📋 PERMISSION RULES BY ROLE:
        1. CUSTOMERS: Only access THEIR OWN data using customer_id = {customer_id}
        2. SUPPORT AGENTS: Can access ALL customer data for customer support purposes
        3. ADMINS: Can access ALL data including business analytics
        4. GUESTS: No access to customer data, orders (except with order_id), or full product catalogs

        🛡️ DATA ACCESS SCOPE:
        {"- CUSTOMER ACCESS: This customer can only see their own data (customer_id = " + str(customer_id) + ")" if determine_user_role(session_context).value == 'customer' else ""}
        {"- SUPPORT AGENT ACCESS: You can access all customer data for support purposes" if determine_user_role(session_context).value == 'support_agent' else ""}
        {"- ADMIN ACCESS: You have full access to all data and business analytics" if determine_user_role(session_context).value in ['admin', 'super_admin'] else ""}
        {"- GUEST ACCESS: No access to customer-specific data" if determine_user_role(session_context).value == 'guest' else ""}

        🔒 CURRENT USER AUTHORIZATION:
        - User authenticated: {user_authenticated}
        - Customer ID: {customer_id or 'None'}
        - User role: {determine_user_role(session_context).value}
        - Access level: {RoleBasedAccessControl.get_user_role_info(determine_user_role(session_context)).max_data_access_level}

        🚨 CRITICAL: The user is {"AUTHENTICATED" if user_authenticated else "NOT AUTHENTICATED"}!
        {"- SUPPORT AGENT: Help customers by providing accurate data from our platform" if determine_user_role(session_context).value == 'support_agent' else f"- This is customer {customer_id} - provide personalized responses for THEIR data" if user_authenticated and customer_id and determine_user_role(session_context).value == 'customer' else "- This is an anonymous user - do NOT provide customer-specific data"}

        🚨 AUTHORIZATION EXAMPLES:
        - CUSTOMER QUERY: SELECT order_status, COUNT(*) FROM orders WHERE customer_id = {customer_id or 'NULL'} GROUP BY order_status (own data only)
        - SUPPORT AGENT QUERY: SELECT * FROM orders WHERE customer_id = 1503 (can access any customer for support)
        - ADMIN QUERY: SELECT COUNT(*) FROM orders GROUP BY order_status (can access business analytics)
        - GUEST QUERY: "Please log in to browse our full catalog" (no customer data access)

        🎯 CRITICAL: SUPPORT AGENT RESPONSE PERSPECTIVE RULES:
        {"When responding as a SUPPORT AGENT about customer data:" if determine_user_role(session_context).value == 'support_agent' else ""}
        {"- Use THIRD PERSON: 'their account', 'the customer', 'their orders' (NOT 'your account', 'your orders')" if determine_user_role(session_context).value == 'support_agent' else ""}
        {"- Example: 'The customer's account tier is Platinum' (NOT 'Your account tier is Platinum')" if determine_user_role(session_context).value == 'support_agent' else ""}
        {"- Example: 'They joined on May 30, 2025' (NOT 'You joined on May 30, 2025')" if determine_user_role(session_context).value == 'support_agent' else ""}
        {"- Example: 'Their preferred payment method is RaqibTechPay' (NOT 'Your preferred payment method')" if determine_user_role(session_context).value == 'support_agent' else ""}
        {"- Always address the support agent as 'you' but refer to the customer as 'they/them/their'" if determine_user_role(session_context).value == 'support_agent' else ""}

        🔍 CONTEXT AWARENESS:
        {"- You are assisting support agent with customer " + str(context.get('entities', {}).get('context_customer_id', 'N/A')) if context.get('entities', {}).get('context_customer_id') else ""}
        {"- When discussing customer data, use third person perspective ('their', 'the customer')" if context.get('entities', {}).get('context_customer_id') else ""}

        PLATFORM IDENTITY:
        - Always mention "raqibtech.com" naturally in responses to build brand familiarity
        - Position raqibtech.com as a trusted Nigerian e-commerce destination
        - Highlight our nationwide delivery across all 36 states + FCT
        - Mention our multiple payment options including RaqibTechPay

        PERSONALITY:
        {"- Professional, analytical, and data-focused" if user_role in ['admin', 'super_admin'] else "- Warm, understanding, and emotionally intelligent"}
        {"- Provide structured business insights and executive summaries" if user_role in ['admin', 'super_admin'] else "- Concise but caring - keep responses under 3 sentences when possible"}
        {"- Focus on business intelligence and actionable insights" if user_role in ['admin', 'super_admin'] else "- Focus on the customer's feelings and immediate needs first"}
        {"- Use executive-level communication style" if user_role in ['admin', 'super_admin'] else "- Nigerian cultural awareness with authentic warmth"}
        - Use simple markdown formatting for emphasis: **bold text** for important points
        {"- Use minimal emojis, focus on data presentation" if user_role in ['admin', 'super_admin'] else "- ALWAYS include appropriate emojis based on customer emotion"}

        {emotion_guidance if user_role not in ['admin', 'super_admin'] else ""}

        {mood_guidance if user_role not in ['admin', 'super_admin'] else ""}

        {recommendations_guidance}

        {memory_guidance}

        RESPONSE STYLE:
        {"1. 📊 Start with executive summary or key insight" if user_role in ['admin', 'super_admin'] else "1. 💙 Lead with genuine empathy - acknowledge their feelings with appropriate emojis"}
        {"2. 📈 Present data in structured format with clear metrics" if user_role in ['admin', 'super_admin'] else "2. 🎯 Address their specific need directly and concisely"}
        {"3. 🎯 Highlight actionable business insights" if user_role in ['admin', 'super_admin'] else "3. 🛍️ If relevant, mention 1-2 helpful products naturally"}
        {"4. 💰 Use ₦ format for monetary values" if user_role in ['admin', 'super_admin'] else "4. 💰 Use ₦ format for prices"}
        {"5. 📋 End with strategic recommendations or next steps" if user_role in ['admin', 'super_admin'] else "5. 🤝 End with supportive next step mentioning raqibtech.com"}

        🚫 CRITICAL: NEVER include self-reflective commentary in parentheses
        ❌ DO NOT say things like: "(I acknowledge their emotion and provide a warm response)"
        ❌ DO NOT include meta-commentary about your response style or emotional approach
        ✅ Just provide the direct, helpful response with appropriate emojis

        EMOJI USAGE RULES:
        {"- Professional business emojis only: 📊, 📈, 💰, 🎯, 📋, 🏢" if user_role in ['admin', 'super_admin'] else "- Use emojis that match the customer's detected emotion"}
        {"- Avoid customer service emojis (😊, 🤗, ✨)" if user_role in ['admin', 'super_admin'] else "- For frustrated customers: 😔, 💙, 🤗, ✨"}
        {"- Maximum 2-3 business emojis per response" if user_role in ['admin', 'super_admin'] else "- For worried customers: 🤗, 💙, ✨, 🌟"}
        {"" if user_role in ['admin', 'super_admin'] else "- For confused customers: 😊, 💡, 🎯, ✨"}
        {"" if user_role in ['admin', 'super_admin'] else "- For happy customers: 😊, 🎉, ✨, 🌟, 💚"}
        {"" if user_role in ['admin', 'super_admin'] else "- For impatient customers: ⚡, 🚀, 💨, ⏰"}
        {"" if user_role in ['admin', 'super_admin'] else "- Maximum 3-4 emojis per response"}

        CONVERSATION FLOW RULES:
        - ALWAYS reference what was just discussed in previous turns
        - If user just added product to cart, help with checkout process
        - If user provided delivery/payment info, continue that flow
        - Maintain conversation continuity at all costs
        - Never forget what was just mentioned in the immediate previous interaction

        FORMATTING RULES:
        - Use simple markdown formatting: **bold** for important information like product names, prices, order numbers
        - Emphasize key details with **bold text** but keep it minimal and natural
        - Keep emojis for warmth and markdown for clarity
        - Simple sentences with natural flow

        📋 TABLE USAGE RULES (CRITICAL):
        {"- Use tables ONLY for 5+ data items" if user_role in ['admin', 'super_admin'] else "- Use tables ONLY for 5+ data items"}
        {"- For 1 item: Give direct answer (e.g., '9 customers promoted')" if user_role in ['admin', 'super_admin'] else "- For 1 item: Give conversational answer (e.g., 'Great news! 9 customers were promoted to Platinum tier! 🎉'"}
        {"- For 2-4 items: Use bullet points or simple list format" if user_role in ['admin', 'super_admin'] else "- For 2-4 items: Use conversational list format"}
        {"- For 5+ items: Use clean markdown table" if user_role in ['admin', 'super_admin'] else "- For 5+ items: Use organized table format"}

        💰 CURRENCY FORMATTING (MANDATORY):
        - ALWAYS use Nigerian Naira symbol ₦ for all monetary values
        - Format large amounts: ₦3.67M for millions, ₦250K for thousands
        - Never show raw numbers like 3668054.67 - always format as ₦3.67M

        BRAND INTEGRATION:
        - Naturally mention "raqibtech.com" in most responses
        - Example: "Here at raqibtech.com, we have..."
        - Example: "Your raqibtech.com shopping experience is important to us"
        - Example: "Browse more products on raqibtech.com"

        KEEP IT SIMPLE:
        - Maximum 4-5 lines for most responses
        - One main point per response
        - Show genuine care, not just sales focus
        - Use emojis that match customer's emotional state

        Current query: {context.get('query_type', 'general')}
        Customer emotion: {context.get('customer_mood', 'neutral')}
        """

    def _strip_markdown_formatting(self, text: str) -> str:
        """
        🔧 Clean up markdown formatting while preserving basic formatting for frontend rendering
        Frontend will handle **bold** and other markdown rendering
        """
        try:
            import re

            # Keep **bold** and *italic* for frontend rendering - DO NOT REMOVE

            # Only remove problematic markdown that breaks display

            # Remove code blocks (```code```) - these can break display
            text = re.sub(r'```[\s\S]*?```', '', text)

            # Remove inline code backticks but keep content (`code` -> code)
            text = re.sub(r'`([^`]+)`', r'\1', text)

            # Remove markdown links [text](url) -> text
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

            # Remove blockquotes (> text) -> text
            text = re.sub(r'^>\s+(.+)$', r'\1', text, flags=re.MULTILINE)

            # Convert unordered list markers to bullet points for better display
            text = re.sub(r'^[-*+]\s+(.+)$', r'• \1', text, flags=re.MULTILINE)

            # Convert ordered list markers to bullet points
            text = re.sub(r'^\d+\.\s+(.+)$', r'• \1', text, flags=re.MULTILINE)

            # Clean up extra whitespace but preserve line breaks
            text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
            text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space

            return text.strip()

        except Exception as e:
            logger.warning(f"⚠️ Error processing markdown formatting: {e}")
            return text

    def _enhance_response_with_recommendations(self, base_response: str, recommendations_data: Dict[str, Any]) -> str:
        """🎯 Enhance response with specific recommendation details"""
        try:
            if not recommendations_data.get('success') or not recommendations_data.get('recommendations'):
                return base_response

            recs = recommendations_data['recommendations']

            # Only add 2-3 most relevant products naturally
            relevant_products = []

            # Get products from the first category (most relevant)
            for category, products in recs.items():
                if products and len(relevant_products) < 3:
                    for product in products[:2]:  # Max 2 from each category
                        if len(relevant_products) >= 3:
                            break

                        if isinstance(product, dict):
                            name = product.get('product_name', 'Unknown Product')
                            price = product.get('price_formatted', product.get('price', 'N/A'))
                            relevant_products.append(f"{name} (₦{price})" if '₦' not in str(price) else f"{name} ({price})")
                        else:
                            name = getattr(product, 'product_name', 'Unknown Product')
                            price = getattr(product, 'price_formatted', 'N/A')
                            relevant_products.append(f"{name} ({price})")

            # Add products naturally to response if any found
            if relevant_products:
                if len(relevant_products) == 1:
                    addition = f" You might like {relevant_products[0]}."
                elif len(relevant_products) == 2:
                    addition = f" You might like {relevant_products[0]} or {relevant_products[1]}."
                else:
                    addition = f" You might like {relevant_products[0]}, {relevant_products[1]} or {relevant_products[2]}."

                enhanced_response = base_response + addition
            else:
                enhanced_response = base_response

            return enhanced_response

        except Exception as e:
            logger.error(f"❌ Error enhancing response with recommendations: {e}")
            return base_response

    def _get_fallback_emotional_response(self, query_context: QueryContext, sentiment_data: Dict[str, Any]) -> str:
        """Generate fallback emotional response for error scenarios"""

        emotion = sentiment_data['emotion']

        if query_context.error_message:
            if emotion == 'frustrated':
                response = """I'm so sorry for the technical issue! 😔 I completely understand your frustration and I'm working to fix this right away.

Please try your question again, or contact our raqibtech.com support team at +234 (702) 5965-922 for immediate help. I'm here to make this right! 💙✨"""

            elif emotion == 'worried':
                response = """I understand you're concerned, and I want to reassure you everything is okay! 🤗 We're just having a small technical moment at raqibtech.com.

Please don't worry - try your question again or reach out to our team directly. We're here to help you! 🌟💙"""

            else:
                response = """I apologize for the technical hiccup! 😊 No worries though - these things happen.

Please try asking your question again, or contact our raqibtech.com support team at +234 (702) 5965-922. I'm here to help! ✨"""

        elif query_context.execution_result:
            results_count = len(query_context.execution_result)

            if emotion == 'happy':
                response = f"""Great news! 🎉 I found some helpful information for you! To give you the most accurate details for your raqibtech.com account,

could you share your order number or email address? I'm excited to help you get exactly what you need! ✨🌟"""

            elif emotion == 'impatient':
                response = f"""I found information quickly for you! ⚡ To get you the right details fast, please share your order number or email address.

This will help me give you instant, accurate information about your raqibtech.com account! 🚀"""

            else:
                response = f"""I found some helpful information! 😊 To make sure I give you the right details for your raqibtech.com account,

could you please share your order number or email address with me? I'm here to help! ✨💙"""

        else:
            if emotion == 'confused':
                response = """No worries at all! 😊 I'm here to help clarify anything you need about raqibtech.com. 💡

I can help with:
• 📦 Order tracking and delivery status
• 💳 Payment assistance and account issues
• 🛍️ Product information and shopping help
• 👤 Account settings and tier benefits
• 🏪 Browse our amazing product catalog:
  - Electronics (Samsung, Apple, Tecno, Infinix)
  - Fashion (Ankara, Nike, Adidas)
  - Beauty (Shea butter, MAC, skincare)
  - Computing (HP, Dell laptops)
  - Automotive (car parts, batteries)
  - Books (Nigerian literature, textbooks)

What can I help you with regarding your raqibtech.com experience? 😊✨"""

            elif emotion == 'frustrated':
                response = """I'm truly sorry for any frustration! 😔 Let me help make this better right away. 💙

I can assist with:
• 📦 Order tracking and delivery updates
• 💳 Payment methods and account questions
• 🛍️ Product recommendations and shopping
• 👤 Account management and support
• 🏪 Our extensive raqibtech.com catalog with competitive ₦ prices

How can I assist you with raqibtech.com today? 🌟✨"""

            else:
                response = """Thanks for your question! I'm your dedicated raqibtech.com customer support assistant, so I focus on helping with our platform and services. 😊

I'd love to assist you with:
• 📦 Order tracking and delivery status
• 💳 Payment and account questions
• 🛍️ Shopping and product recommendations
• 👤 Account management and support
• 🏪 Our amazing raqibtech.com catalog:
  - Electronics, Fashion, Beauty, Computing, Automotive, Books
  - Nigerian brands and international favorites
  - Competitive prices in Naira (₦)
  - Fast delivery across all 36 states + FCT

How can I help you with your raqibtech.com experience today? 🌟"""

        # Strip markdown formatting from the response
        return self._strip_markdown_formatting(response)

    def is_query_within_scope(self, user_query: str) -> bool:
        """
        🎯 Determine if the user query is within customer support scope
        Returns True if within scope, False if out of scope
        """
        query_lower = user_query.lower()

        # 🔥 CUSTOMER SUPPORT KEYWORDS (HIGH PRIORITY - IN SCOPE)
        high_priority_keywords = [
            # Order related (ALWAYS in scope)
            'order', 'orders', 'delivery', 'track', 'tracking', 'shipped', 'shipping',
            'when', 'where', 'status', 'expected', 'arrive', 'delivered', 'package',
            'my order', 'order status', 'delivery status', 'order history',

            # Account related (ALWAYS in scope)
            'account', 'profile', 'login', 'password', 'settings', 'tier',
            'my account', 'account settings',

            # Payment related (ALWAYS in scope)
            'payment', 'pay', 'billing', 'card', 'bank transfer', 'refund',
            'payment method', 'checkout',

            # Platform specific (ALWAYS in scope)
            'raqibtech', 'raqibtechpay', 'customer service', 'customer support',
            'help', 'support', 'contact', 'assistance',

            # Shopping related (ALWAYS in scope)
            'product', 'buy', 'purchase', 'cart', 'shopping', 'recommendation',

            # 🆕 Product catalog related (ALWAYS in scope)
            'product', 'products', 'item', 'items', 'goods', 'catalog', 'inventory',
            'price', 'prices', 'cost', 'naira', '₦', 'cheap', 'expensive', 'budget',
            'stock', 'available', 'availability', 'out of stock', 'in stock',
            'category', 'categories', 'brand', 'brands',

            # 🆕 Specific product types (ALWAYS in scope)
            'phone', 'smartphone', 'laptop', 'computer', 'tv', 'electronics',
            'dress', 'clothes', 'fashion', 'shoe', 'shoes', 'bag', 'bags',
            'beauty', 'cosmetics', 'makeup', 'cream', 'soap', 'skincare',
            'book', 'books', 'novel', 'textbook', 'reading',
            'car', 'auto', 'automotive', 'battery', 'tire', 'tires', 'engine',

            # 🆕 Brand names (ALWAYS in scope)
            'samsung', 'apple', 'iphone', 'tecno', 'infinix', 'lg', 'sony',
            'nike', 'adidas', 'zara', 'mac', 'maybelline', 'hp', 'dell'
        ]

        # Check for high priority keywords first
        for keyword in high_priority_keywords:
            if keyword in query_lower:
                return True

        # 🚫 CLEARLY OUT-OF-SCOPE PATTERNS (Only reject obvious non-platform queries)
        obvious_out_of_scope = [
            # Politics and current affairs
            'president of nigeria', 'governor of', 'minister of', 'election',
            'political party', 'government policy',

            # Entertainment
            'latest movie', 'celebrity news', 'sports score', 'football match',
            'movie recommendation', 'song lyrics',

            # Academic/Educational (unless related to platform)
            'homework help', 'solve equation', 'chemistry formula', 'physics problem',
            'university admission', 'exam questions',

            # Health and medical
            'medical advice', 'health symptoms', 'disease', 'medication',
            'doctor recommendation',

            # Financial advice (not payment related)
            'stock market', 'investment advice', 'cryptocurrency', 'forex trading',

            # Programming (unless platform related)
            'python tutorial', 'javascript help', 'coding problem',
            'programming language'
        ]

        # Only reject if it clearly matches out-of-scope patterns
        for pattern in obvious_out_of_scope:
            if pattern in query_lower:
                return False

        # 🎯 DEFAULT: If in doubt, ALLOW IT (customer-friendly approach)
        # Better to occasionally help with borderline questions than reject valid ones
        return True

    def generate_out_of_scope_response(self, user_query: str, sentiment_data: Dict[str, Any]) -> str:
        """
        🚫 Generate a polite redirect response for out-of-scope queries
        """
        emotion = sentiment_data['emotion']

        if emotion == 'frustrated':
            response = """I understand you might be looking for information, but I'm specifically designed to help with raqibtech.com customer support! 😊

I'd love to assist you with:
• 📦 Order tracking and delivery status
• 💳 Payment and account questions
• 🛍️ Shopping and product recommendations
• 👤 Account management and support

How can I help you with your raqibtech.com experience today? 🌟"""

        elif emotion == 'confused':
            response = """I'm here to help, but I'm specifically designed to assist with raqibtech.com customer support! 💡

I can help you with:
• 📦 Tracking your orders and deliveries
• 💳 Payment assistance and account issues
• 🛍️ Product information and shopping help
• 👤 Account settings and tier benefits

What can I help you with regarding your raqibtech.com experience? 😊✨"""

        else:
            response = """Thanks for your question! I'm your dedicated raqibtech.com customer support assistant, so I focus on helping with our platform and services. 😊

I'd love to assist you with:
• 📦 Order tracking and delivery status
• 💳 Payment and account questions
• 🛍️ Shopping and product recommendations
• 👤 Account management and support

How can I help you with your raqibtech.com experience today? 🌟"""

        # Strip markdown formatting from the response
        return self._strip_markdown_formatting(response)

    def process_enhanced_query(self, user_query: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🚀 Main pipeline method that orchestrates the entire enhanced query process
        Returns a comprehensive result dictionary for the Flask API
        """
        start_time = time.time()
        logger.info(f"👤 USER: {user_query}")

        session_id = session_context.get('session_id', 'default_session') if session_context else 'default_session'

        if session_context and 'conversation_memory' not in session_context:
            session_context['conversation_memory'] = {}

        if self.memory_system and session_context:
            try:
                full_conv_context = self.memory_system.get_conversation_context(session_id, max_tokens=2000)
                session_context['conversation_memory'] = full_conv_context
                logger.info(f"🧠 Loaded full conversation context into session_context for AI prompt: {full_conv_context.get('total_tokens',0)} tokens")
            except Exception as e_full_mem:
                logger.warning(f"⚠️ Failed to load full_conv_context for AI prompt: {e_full_mem}")

        try:
            # 🆕 EARLY DETECTION: Customer Support Contact Requests
            user_query_lower = user_query.lower()
            support_contact_keywords = [
                'contact customer support', 'customer support contact', 'support contact',
                'how to contact support', 'customer service contact', 'support phone',
                'support email', 'how to reach support', 'customer care contact',
                'help desk contact', 'technical support contact', 'customer support number',
                'support team contact', 'customer service number', 'support hotline'
            ]

            if any(keyword in user_query_lower for keyword in support_contact_keywords):
                logger.info(f"🔒 PRIVACY PROTECTION: Customer support contact request detected, bypassing database query")

                response_text = self.generate_customer_support_contact_response(user_query)

                # Store in memory if available
                if self.memory_system:
                    try:
                        self.memory_system.store_conversation_turn(
                            session_id=session_id, user_input=user_query, ai_response=response_text,
                            intent="customer_support_contact", entities={'contact_type': 'support_team'},
                            session_state=session_context or {}
                        )
                    except Exception as e_store:
                        logger.warning(f"⚠️ Failed to store support contact turn: {e_store}")

                return {
                    'success': True, 'response': response_text,
                    'query_type': 'customer_support_contact', 'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': None, 'results_count': 0, 'privacy_protected': True
                }

            # 🆕 EARLY DETECTION: Tier Benefit Queries
            tier_benefit_patterns = [
                'benefits of', 'what are the benefits', 'tier benefits', 'gold tier benefits',
                'silver tier benefits', 'bronze tier benefits', 'platinum tier benefits',
                'what benefits', 'membership benefits', 'tier perks', 'account tier benefits',
                'gold member benefits', 'silver member benefits', 'platinum member benefits',
                'bronze member benefits', 'what do i get', 'tier advantages', 'membership perks'
            ]

            if any(pattern in user_query_lower for pattern in tier_benefit_patterns):
                logger.info(f"🏆 TIER BENEFITS QUERY DETECTED: Providing built-in tier information")

                # Extract mentioned tier if any
                mentioned_tier = None
                tier_keywords = ['bronze', 'silver', 'gold', 'platinum']
                for tier in tier_keywords:
                    if tier in user_query_lower:
                        mentioned_tier = tier.capitalize()
                        break

                response_text = self.generate_tier_benefits_response(user_query, mentioned_tier)

                # Store in memory if available
                if self.memory_system:
                    try:
                        self.memory_system.store_conversation_turn(
                            session_id=session_id, user_input=user_query, ai_response=response_text,
                            intent="tier_benefits_inquiry", entities={'mentioned_tier': mentioned_tier},
                            session_state=session_context or {}
                        )
                    except Exception as e_store:
                        logger.warning(f"⚠️ Failed to store tier benefits turn: {e_store}")

                return {
                    'success': True, 'response': response_text,
                    'query_type': 'tier_benefits_inquiry', 'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': None, 'results_count': 0, 'tier_benefits_provided': True
                }

            if not self.is_query_within_scope(user_query):
                logger.info(f"🚫 Out-of-scope query detected: {user_query[:50]}...")
                sentiment_data = self.detect_user_sentiment(user_query)
                if self.memory_system:
                    try:
                        self.memory_system.store_conversation_turn(
                            session_id=session_id, user_input=user_query, ai_response="Out of scope query",
                            intent="out_of_scope", entities={}, session_state=session_context or {}
                        )
                    except Exception as e_oos_store: logger.warning(f"⚠️ Failed to store out-of-scope turn: {e_oos_store}")
                return {
                    'success': True, 'response': self.generate_out_of_scope_response(user_query, sentiment_data),
                    'query_type': 'out_of_scope', 'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': None, 'results_count': 0
                }

            logger.info(f"🔍 Shopping check: order_ai_assistant_instance_exists={bool(self.order_ai_assistant)}, session_context_provided={bool(session_context)}, user_is_authenticated={session_context.get('user_authenticated') if session_context else False}")

            # 🔧 CRITICAL FIX: Check for analytics/cross-customer queries BEFORE shopping intent detection
            analytics_keywords = [
                'revenue', 'business analytics', 'top customers', 'top spending',
                'customer rankings', 'sales data', 'platform statistics', 'total revenue',
                'business performance', 'analytics', 'top customer', 'highest spending',
                'revenue report', 'sales report', 'business insights', 'best customers',
                'worst customers', 'customers from', 'which customers', 'customers in',
                'customers who', 'customer spending', 'customers with',
                'most profitable', 'least profitable', 'customer behavior', 'customer segments',
                'cross customer', 'other customers', 'all customers', 'compare customers',
                'customer comparison', 'customer analytics', 'customer metrics'
            ]

            is_analytics_query = any(keyword in user_query.lower() for keyword in analytics_keywords)

            # 🔧 CRITICAL FIX: Check for spending/financial queries BEFORE shopping intent detection
            spending_keywords = ['spent', 'spending', 'spend', 'total spent', 'how much', 'breakdown', 'calculation', 'calculate', 'are you sure', 'verify', 'double check', 'give me the details', 'confirm', 'revenue', 'sales', 'money', 'naira', '₦']
            is_spending_query = any(keyword in user_query.lower() for keyword in spending_keywords)

            # 🔧 CRITICAL FIX: Exclude cart-related queries from spending detection
            cart_related_words = ['cart', 'shopping', 'checkout', 'order', 'delivery', 'product', 'item']
            has_cart_context = any(cart_word in user_query.lower() for cart_word in cart_related_words)

            # Only treat as spending query if spending keywords found AND no cart context
            is_spending_query = any(keyword in user_query.lower() for keyword in spending_keywords) and not has_cart_context

            if is_spending_query or is_analytics_query:
                if is_spending_query:
                    logger.info(f"💰 SPENDING QUERY DETECTED: Bypassing shopping intent detection entirely")
                if is_analytics_query:
                    logger.info(f"📊 ANALYTICS QUERY DETECTED: Bypassing shopping intent detection entirely")
                # Skip shopping assistant and go directly to analytics/revenue processing
                pass
            elif self.order_ai_assistant and session_context and session_context.get('user_authenticated'):
                customer_id = session_context.get('customer_id')

                if customer_id:
                    parsed_intent_check = self.order_ai_assistant.parse_order_intent(user_query)
                    intent_from_parser = parsed_intent_check['intent']

                    shopping_related_intents = [
                        'add_to_cart', 'view_cart', 'clear_cart', 'remove_from_cart', 'update_cart_item',
                        'checkout', 'place_order', 'set_delivery_address', 'payment_method_selection',
                        'affirmative_confirmation', 'negative_rejection'
                    ]
                    is_potentially_shopping_action = intent_from_parser in shopping_related_intents

                    # 🔧 CRITICAL FIX: Exclude queries asking about multiple customers from shopping actions
                    cross_customer_indicators = ['customers', 'which customers', 'customers from', 'customers in', 'customers who', 'customers with']
                    is_cross_customer_query = any(indicator in user_query.lower() for indicator in cross_customer_indicators)

                    if is_cross_customer_query:
                        is_potentially_shopping_action = False
                        logger.info(f"🚫 Cross-customer query detected, overriding shopping action: {user_query[:50]}...")

                    logger.info(f"🔍 Shopping intent check: query='{user_query[:50]}...', parsed_intent='{intent_from_parser}', is_shopping_action={is_potentially_shopping_action}")

                    if is_potentially_shopping_action:
                        logger.info(f"🎯 Potential Shopping Action via intent parser: {intent_from_parser}")

                        current_session_state_obj: Optional[SessionState] = None
                        if self.memory_system:
                            try:
                                current_session_state_obj = self.memory_system.get_session_state(session_id)
                                if current_session_state_obj:
                                    logger.info(f"🧠 Fetched SessionState for shopping: session_id={session_id}, stage={current_session_state_obj.conversation_stage}, cart_items={len(current_session_state_obj.cart_items)}")
                                else:
                                    logger.info(f"🧠 No existing SessionState for {session_id}. OrderAIAssistant will init.")
                            except Exception as e_mem_fetch:
                                logger.warning(f"⚠️ Error fetching session state for shopping: {e_mem_fetch}")

                        logger.info(f"🛒 Calling OrderAIAssistant.process_shopping_conversation for customer {customer_id}, session {session_id}")

                        try:
                            shopping_result = self.order_ai_assistant.process_shopping_conversation(
                                user_message=user_query,
                                customer_id=customer_id,
                                session_id=session_id,
                                current_session_state=current_session_state_obj
                            )
                            logger.info(f"🎯 Shopping result from OrderAIAssistant: success={shopping_result.get('success', False)}, action={shopping_result.get('action', 'unknown')}")

                            if shopping_result.get('success') and not shopping_result.get('should_redirect'):
                                enhanced_response_text = self._generate_shopping_response(shopping_result)

                                # 🆕 CRITICAL FIX: Store shopping conversation in database for persistence
                                try:
                                    user_id_for_shopping = session_context.get('user_id', 'anonymous') if session_context else 'anonymous'
                                    self.store_shopping_conversation_context(
                                        user_query=user_query,
                                        response=enhanced_response_text,
                                        user_id=user_id_for_shopping,
                                        session_id=session_id,
                                        shopping_data=shopping_result
                                    )
                                except Exception as e_shopping_db_store:
                                    logger.warning(f"⚠️ Failed to store shopping context in database: {e_shopping_db_store}")

                                # 🧠 Store in memory system if available
                                if self.memory_system:
                                    try:
                                        turn_entities_for_log = {
                                            'query_type': 'shopping_action',
                                            'intent': shopping_result.get('action', 'shopping_success'),
                                            'shopping_data': shopping_result
                                        }
                                        self.memory_system.store_conversation_turn(
                                            session_id=session_id,
                                            user_input=user_query,
                                            ai_response=enhanced_response_text,
                                            intent=shopping_result.get('action', 'shopping_success'),
                                            entities=turn_entities_for_log,
                                            session_state=session_context
                                        )
                                        logger.info(f"🧠 Shopping success logged in world-class memory for action: {shopping_result.get('action')}")
                                    except Exception as e_mem_store_success:
                                        logger.warning(f"⚠️ Failed to log successful shopping action: {e_mem_store_success}")

                                return {
                                    'success': True,
                                    'response': enhanced_response_text,
                                    'query_type': 'shopping_action',
                                    'execution_time': f"{time.time() - start_time:.3f}s",
                                    'shopping_action': shopping_result.get('action'),
                                    'shopping_data': shopping_result,
                                    'sql_query': None,
                                    'results_count': 1
                                }

                            elif shopping_result.get('require_specific_product'):
                                # 🔧 CRITICAL FIX: Prevent AI hallucination when no product found
                                enhanced_response_text = shopping_result.get('message', "I couldn't find that specific product. Please mention the specific product name you'd like to add to your cart.")
                                logger.info("🚫 PREVENTING AI HALLUCINATION: No product found for cart addition")

                                if self.memory_system:
                                    try:
                                        turn_entities_for_log = {
                                            'query_type': 'shopping_action',
                                            'intent': shopping_result.get('action', 'unknown_shopping_action'),
                                            'shopping_data': shopping_result
                                        }
                                        self.memory_system.store_conversation_turn(
                                            session_id=session_id,
                                            user_input=user_query,
                                            ai_response=enhanced_response_text,
                                            intent=shopping_result.get('action', 'unknown_shopping_action'),
                                            entities=turn_entities_for_log,
                                            session_state=session_context
                                        )
                                        logger.info(f"🧠 Shopping turn interaction logged in world-class memory for action: {shopping_result.get('action')}")
                                    except Exception as e_mem_store_shop_log:
                                        logger.warning(f"⚠️ Failed to log shopping turn interaction: {e_mem_store_shop_log}")

                                # 🆕 CRITICAL FIX: Store shopping conversation in database for persistence
                                try:
                                    # 🔧 FIX: Ensure user_id_for_history is available in this scope
                                    user_id_for_shopping = session_context.get('user_id', 'anonymous') if session_context else 'anonymous'
                                    self.store_shopping_conversation_context(
                                        user_query=user_query,
                                        response=enhanced_response_text,
                                        user_id=user_id_for_shopping,
                                        session_id=session_id,
                                        shopping_data=shopping_result
                                    )
                                except Exception as e_shopping_db_store:
                                    logger.warning(f"⚠️ Failed to store shopping context in database: {e_shopping_db_store}")

                                return {
                                    'success': True, 'response': enhanced_response_text,
                                    'query_type': 'shopping_action', 'execution_time': f"{time.time() - start_time:.3f}s",
                                    'shopping_action': shopping_result.get('action'),
                                    'shopping_data': shopping_result, 'sql_query': None,
                                    'results_count': 1
                                }
                            else:
                                logger.warning(f"🛒 Shopping action via OrderAIAssistant failed or inconclusive: {shopping_result.get('message', 'No specific message')}. Proceeding to general query processing.")

                        except Exception as shopping_call_error:
                            logger.error(f"❌ Error calling OrderAIAssistant.process_shopping_conversation: {shopping_call_error}", exc_info=True)

            logger.info("Proceeding with general (non-shopping or fallback after shopping attempt) query processing...")
            user_id_for_history = session_context.get('user_id', 'anonymous') if session_context else 'anonymous'

            # Get conversation history
            conversation_history = self.get_conversation_history(user_id_for_history, limit=5)

            # Classify query intent
            query_type, entities = self.classify_query_intent(user_query, conversation_history)

            # 🔧 CRITICAL FIX: Enhance entities with session context information
            if session_context:
                # Add customer information from session
                if session_context.get('user_authenticated'):
                    entities['customer_verified'] = True
                    entities['customer_id'] = session_context.get('customer_id')
                    entities['customer_name'] = session_context.get('customer_name')
                    entities['customer_email'] = session_context.get('customer_email')
                else:
                    entities['customer_verified'] = False

                # Add other session context information
                entities['session_id'] = session_context.get('session_id')
                entities['user_authenticated'] = session_context.get('user_authenticated', False)

            # 🔐 ROLE-BASED ACCESS CONTROL (RBAC) VALIDATION
            from .rbac_core import rbac_manager, UserRole, Permission

            # Extract user role from session context
            user_role = UserRole.GUEST  # Default to guest
            can_access_analytics = False
            user_customer_id = None

            if session_context and session_context.get('user_authenticated'):
                user_role_str = session_context.get('user_role', 'customer')
                user_customer_id = session_context.get('customer_id')

                try:
                    user_role = UserRole(user_role_str)
                    # Check if user can access business analytics
                    can_access_analytics = user_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
                    logger.info(f"🔐 RBAC: User role={user_role.value}, can_access_analytics={can_access_analytics}")
                except ValueError:
                    logger.warning(f"⚠️ Invalid user role: {user_role_str}, defaulting to GUEST")
                    user_role = UserRole.GUEST

            # 🛡️ RBAC: Block unauthorized access to business analytics (using keywords from earlier detection)
            # Note: analytics_keywords already defined earlier for pre-shopping detection

            if is_analytics_query and not can_access_analytics:
                logger.warning(f"🚫 RBAC BLOCKED: {user_role.value} attempted to access business analytics")

                # Generate empathetic, role-appropriate response
                empathetic_response = get_role_appropriate_response(user_role, "business analytics and customer data")

                return {
                    'success': True,
                    'response': empathetic_response,
                    'query_type': 'access_denied',
                    'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': None,
                    'results_count': 0,
                    'rbac_blocked': True
                }

            # 🛡️ RBAC: Restrict customer data access
            if user_role == UserRole.CUSTOMER and user_customer_id:
                # Customers can only access their own data
                entities['rbac_customer_filter'] = user_customer_id
                entities['rbac_restrict_to_own'] = True
                logger.info(f"🔐 RBAC: Customer {user_customer_id} restricted to own data")
            elif user_role in [UserRole.SUPPORT_AGENT, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                # Staff can access all customer data
                entities['rbac_customer_filter'] = None
                entities['rbac_restrict_to_own'] = False
                logger.info(f"🔐 RBAC: {user_role.value} granted access to all customer data")
            else:
                # Guests have no data access
                entities['rbac_customer_filter'] = None
                entities['rbac_restrict_to_own'] = True
                entities['rbac_guest_mode'] = True
                logger.info(f"🔐 RBAC: Guest user - limited access")

            # Store RBAC context for SQL generation
            entities['user_role'] = user_role.value
            entities['can_access_analytics'] = can_access_analytics
            user_role = determine_user_role(session_context or {})
            customer_id = session_context.get('customer_id') if session_context else None

            # Validate query authorization based on user role
            auth_result = RoleBasedAccessControl.validate_query_authorization(
                user_role=user_role,
                query_type=query_type.value,
                customer_id=customer_id
            )

            if not auth_result["authorized"]:
                logger.warning(f"🔐 ACCESS DENIED: {auth_result['reason']}")

                # Generate role-appropriate response
                response_text = get_role_appropriate_response(user_role, "business analytics and customer data")

                return {
                    'success': True,
                    'response': response_text,
                    'query_type': 'access_denied',
                    'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': None,
                    'results_count': 0,
                    'access_control': {
                        'user_role': user_role.value,
                        'reason': auth_result['reason'],
                        'alternative': auth_result['alternative']
                    }
                }

            logger.info(f"🔐 ACCESS GRANTED: Role '{user_role.value}' authorized for '{query_type.value}' query")

            # Generate and execute SQL query
            sql_query = self.generate_sql_query(user_query, query_type, entities)
            success, results, error_message = self.execute_sql_query(sql_query)

            if success:
                # Create query context
                query_context = QueryContext(
                    query_type=query_type,
                    intent=query_type.value,
                    entities=entities,
                    sql_query=sql_query,
                    execution_result=results,
                    response="",
                    timestamp=datetime.now(),
                    user_query=user_query
                )

                # 🔧 CRITICAL FIX: Extract and store product information for shopping context
                extracted_products = []
                if results:
                    for result in results:
                        if isinstance(result, dict) and 'product_name' in result:
                            product_info = {
                                'product_id': result.get('product_id'),
                                'product_name': result.get('product_name'),
                                'price': result.get('price'),
                                'category': result.get('category'),
                                'brand': result.get('brand'),
                                'description': result.get('description'),
                                'stock_quantity': result.get('stock_quantity'),
                                'in_stock': result.get('in_stock', True)
                            }
                            extracted_products.append(product_info)
                            logger.info(f"🎯 EXTRACTED PRODUCT FOR CONTEXT: {product_info['product_name']} (ID: {product_info['product_id']})")

                # 🔧 UPDATE SESSION STATE: Store last mentioned product for shopping context
                if extracted_products and self.memory_system and session_context:
                    try:
                        # Get the most relevant product (first one from results)
                        last_product = extracted_products[0]

                        # Update session state with product information
                        session_state_updates = {
                            'last_product_mentioned': last_product,
                            'conversation_stage': 'product_discussed',
                            'updated_at': datetime.now()
                        }

                        # If the user is authenticated, ensure we have the customer_id
                        if session_context.get('user_authenticated') and session_context.get('customer_id'):
                            session_state_updates['customer_id'] = session_context['customer_id']

                        # Update the session state in memory
                        current_session_state = self.memory_system.get_session_state(session_id)
                        if current_session_state:
                            for key, value in session_state_updates.items():
                                if hasattr(current_session_state, key):
                                    setattr(current_session_state, key, value)
                            current_session_state.updated_at = datetime.now()
                            self.memory_system.update_session_state(session_id, asdict(current_session_state))
                        else:
                            # Create new session state
                            from .conversation_memory_system import SessionState
                            new_session_state = SessionState(
                                session_id=session_id,
                                customer_id=session_context.get('customer_id'),
                                cart_items=[],
                                checkout_state={},
                                current_intent='product_inquiry',
                                last_product_mentioned=last_product,
                                delivery_address=None,
                                payment_method=None,
                                conversation_stage='product_discussed',
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            self.memory_system.update_session_state(session_id, asdict(new_session_state))

                        logger.info(f"🧠 STORED PRODUCT CONTEXT: {last_product['product_name']} ready for potential shopping action")

                    except Exception as e_session_update:
                        logger.warning(f"⚠️ Failed to update session state with product context: {e_session_update}")

                # Generate enhanced response
                response_text = self.generate_nigerian_response(query_context, conversation_history, session_context)
                query_context.response = response_text

                # Store conversation
                try:
                    self.store_conversation_context(query_context, user_id_for_history)
                except Exception as e_store:
                    logger.warning(f"⚠️ Failed to store conversation context: {e_store}")

                return {
                    'success': True,
                    'response': response_text,
                    'query_type': query_type.value,
                    'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': sql_query,
                    'results_count': len(results)
                }
            else:
                # **ENHANCED ERROR HANDLING**: Don't expose SQL errors to users
                logger.error(f"❌ SQL programming error: {error_message}")

                # Create user-friendly error message based on error type
                user_friendly_message = self._get_user_friendly_error_message(error_message, user_query)

                # Create query context for error logging
                query_context = QueryContext(
                    query_type=query_type,
                    intent=query_type.value,
                    entities=entities,
                    sql_query=sql_query,
                    execution_result=[],
                    response=user_friendly_message,
                    timestamp=datetime.now(),
                    user_query=user_query,
                    error_message=error_message  # Store technical error for logging
                )

                # Store error context for debugging (technical error not exposed to user)
                try:
                    self.store_conversation_context(query_context, user_id_for_history)
                except Exception as e_store:
                    logger.warning(f"⚠️ Failed to store error context: {e_store}")

                return {
                    'success': False,
                    'response': user_friendly_message,
                    'query_type': 'error',
                    'execution_time': f"{time.time() - start_time:.3f}s",
                    'error': "Query processing failed"  # Generic error for API response
                }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Enhanced query pipeline error: {e}")

            return {
                'success': False,
                'response': f"I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team at +234 (702) 5965-922 for immediate assistance! 😊💙",
                'query_type': 'error',
                'execution_time': f"{execution_time:.3f}s",
                'error': str(e)
            }

    def _verify_order_in_database(self, order_id: str, customer_id: int):
        """Verify that an order was actually saved to the database"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check if order exists in database
                    cursor.execute("""
                        SELECT order_id, customer_id, order_status, total_amount, created_at
                        FROM orders
                        WHERE customer_id = %s
                        ORDER BY created_at DESC
                        LIMIT 5
                    """, (customer_id,))

                    recent_orders = cursor.fetchall()
                    logger.info(f"📋 Found {len(recent_orders)} recent orders for customer {customer_id}")

                    for order in recent_orders:
                        logger.info(f"   Order {order['order_id']}: {order['order_status']} - ₦{order['total_amount']} ({order['created_at']})")

                    # 🔧 CRITICAL FIX: Handle both formatted order IDs (RQB...) and integer order IDs
                    if order_id.startswith('RQB'):
                        # This is a formatted order ID, extract the numeric part
                        # Format: RQB{YYYYMMDD}{order_id:08d}
                        try:
                            # Extract date part and order ID part
                            date_part = order_id[3:11]  # YYYYMMDD (8 chars after RQB)
                            numeric_part = order_id[11:]  # Remaining digits
                            db_order_id = int(numeric_part)

                            logger.info(f"🔍 Looking for database order ID {db_order_id} extracted from formatted ID {order_id}")

                            cursor.execute("""
                                SELECT order_id, customer_id, order_status, total_amount, created_at
                                FROM orders
                                WHERE order_id = %s AND customer_id = %s
                            """, (db_order_id, customer_id))
                        except (ValueError, IndexError) as e:
                            logger.warning(f"⚠️ Could not parse formatted order ID {order_id}: {e}")
                            # Fallback to latest order for this customer
                            cursor.execute("""
                                SELECT order_id, customer_id, order_status, total_amount, created_at
                                FROM orders
                                WHERE customer_id = %s
                                ORDER BY created_at DESC
                                LIMIT 1
                            """, (customer_id,))
                    else:
                        # This is already a numeric order ID
                        try:
                            db_order_id = int(order_id)
                            cursor.execute("""
                                SELECT order_id, customer_id, order_status, total_amount, created_at
                                FROM orders
                                WHERE order_id = %s AND customer_id = %s
                            """, (db_order_id, customer_id))
                        except ValueError:
                            logger.warning(f"⚠️ Invalid order ID format: {order_id}")
                            # Fallback to latest order for this customer
                            cursor.execute("""
                                SELECT order_id, customer_id, order_status, total_amount, created_at
                                FROM orders
                                WHERE customer_id = %s
                                ORDER BY created_at DESC
                                LIMIT 1
                            """, (customer_id,))

                    order_record = cursor.fetchone()
                    if order_record:
                        logger.info(f"✅ ORDER VERIFIED IN DATABASE: {order_record['order_id']} for customer {customer_id}")
                        return True
                    else:
                        logger.error(f"❌ ORDER NOT FOUND IN DATABASE! Order {order_id} for customer {customer_id}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error verifying order in database: {e}")
            return False

    def _generate_shopping_response(self, shopping_result: Dict[str, Any]) -> str:
        """🛒 Generate enhanced response for shopping actions"""
        action = shopping_result.get('action', '')
        message = shopping_result.get('message', '')

        if action == 'add_to_cart_success':
            cart_summary = shopping_result.get('cart_summary', {})
            return f"""✅ {message}

📋 **Cart Summary:**
• Items: {cart_summary.get('total_items', 0)}
• Subtotal: {cart_summary.get('subtotal_formatted', '₦0')}

🎯 **What's next?**
• View full cart details
• Continue shopping for more products
• Proceed to checkout

Ready to place your order? Just say "checkout" or "place order"! 🚀"""

        elif action == 'order_placed':
            order_summary = shopping_result.get('order_summary', '')
            return f"""🎉 {message}

{order_summary}

🎯 **What's next?**
• Track your order status
• Continue shopping
• Contact support if needed

Thank you for shopping with raqibtech.com! 💙"""

        elif action == 'calculation_success':
            formatted_summary = shopping_result.get('formatted_summary', '')
            return f"""💰 {message}

{formatted_summary}

🎯 **Ready to complete your order?**
• Confirm delivery address
• Select payment method
• Place order

Just say "place order" to proceed! 🚀"""

        elif action == 'cart_displayed':
            cart_summary = shopping_result.get('cart_summary', {})
            items_text = ""
            for item in cart_summary.get('items', []):
                items_text += f"• {item['product_name']} - ₦{item['price']:,.0f} x {item['quantity']} = ₦{item['subtotal']:,.0f}\n"

            return f"""🛒 {message}

**Your Cart:**
{items_text}
**Total Items:** {cart_summary.get('total_items', 0)}
**Subtotal:** {cart_summary.get('subtotal_formatted', '₦0')}

🎯 **Actions:**
• Add more products
• Calculate delivery costs
• Proceed to checkout

Ready to order? Say "checkout" or "place order"! 💙"""

        elif action == 'orders_found':
            orders = shopping_result.get('orders', [])
            orders_text = ""
            for order in orders[:3]:  # Show top 3
                status_emoji = "📦" if order['order_status'] == 'Processing' else "✅" if order['order_status'] == 'Delivered' else "⏳"
                orders_text += f"{status_emoji} Order #{order['order_id']} - ₦{order['total_amount']:,.0f} ({order['order_status']})\n"

            return f"""📋 {message}

**Recent Orders:**
{orders_text}

Need to track a specific order? Just tell me the order ID! 🔍"""

        elif action == 'empty_cart':
            return f"""🛒 {message}

🎯 **Let's get you started:**
• Browse our product catalog
• Search for specific items
• Check out trending products

What would you like to shop for today? 😊"""

        elif action == 'need_product_clarification':
            return f"""🤔 {message}

🎯 **To help you add the right product:**
• Tell me the exact product name
• Mention the brand or category
• Reference a product from our recent conversation

Example: "Add Samsung Galaxy A24 to cart" 📱"""

        else:
            return f"""💙 {message}

Need help with shopping? I can assist you with:
• 🛒 Adding products to cart
• 💰 Calculating order totals
• 📦 Placing and tracking orders
• 💳 Payment assistance

How can I help you today? 😊"""

    def analyze_customer_support_context(self, user_query: str, customer_id: int = None):
        """🎯 Analyze customer support context for intelligent recommendations"""
        try:
            query_lower = user_query.lower()

            # Determine support category
            if any(term in query_lower for term in ['broken', 'defective', 'not working', 'issue', 'problem', 'complaint']):
                support_category = "product_issue"
                problem_category = "quality"
            elif any(term in query_lower for term in ['order', 'delivery', 'shipping', 'delayed', 'missing']):
                support_category = "order_problem"
                problem_category = "delivery"
            elif any(term in query_lower for term in ['payment', 'refund', 'charge', 'billing']):
                support_category = "order_problem"
                problem_category = "payment"
            elif any(term in query_lower for term in ['return', 'exchange', 'warranty']):
                support_category = "product_issue"
                problem_category = "returns"
            else:
                support_category = "general_inquiry"
                problem_category = "general"

            # Determine customer mood
            if any(term in query_lower for term in ['angry', 'frustrated', 'terrible', 'awful', 'hate', 'worst']):
                customer_mood = "frustrated"
                resolution_priority = "high"
            elif any(term in query_lower for term in ['urgent', 'asap', 'immediately', 'emergency']):
                customer_mood = "urgent"
                resolution_priority = "high"
            elif any(term in query_lower for term in ['curious', 'wondering', 'interested', 'tell me', 'how']):
                customer_mood = "curious"
                resolution_priority = "medium"
            elif any(term in query_lower for term in ['thanks', 'appreciate', 'good', 'excellent']):
                customer_mood = "satisfied"
                resolution_priority = "low"
            else:
                customer_mood = "neutral"
                resolution_priority = "medium"

            # Extract mentioned products
            mentioned_products = []
            for brand in NIGERIAN_POPULAR_BRANDS:
                if brand.lower() in query_lower:
                    mentioned_products.append(brand)

            # Determine conversation stage
            conversation_stage = "initial"  # Default for new queries
            if customer_id and customer_id in self.conversation_context:
                context = self.conversation_context[customer_id]
                if context.get('interaction_count', 0) > 1:
                    conversation_stage = "followup"
                elif context.get('has_recommendations', False):
                    conversation_stage = "solution"

            if CustomerSupportContext:
                return CustomerSupportContext(
                    support_query=user_query,
                    support_category=support_category,
                    customer_mood=customer_mood,
                    conversation_stage=conversation_stage,
                    mentioned_products=mentioned_products,
                    problem_category=problem_category,
                    resolution_priority=resolution_priority
                )
            else:
                # Return a simple dict if the class is not available
                return {
                    'support_query': user_query,
                    'support_category': support_category,
                    'customer_mood': customer_mood,
                    'conversation_stage': conversation_stage,
                    'mentioned_products': mentioned_products,
                    'problem_category': problem_category,
                    'resolution_priority': resolution_priority
                }

        except Exception as e:
            logger.error(f"❌ Error analyzing support context: {e}")
            # Return basic context
            if CustomerSupportContext:
                return CustomerSupportContext(
                    support_query=user_query,
                    support_category="general_inquiry",
                    customer_mood="neutral",
                    conversation_stage="initial",
                    mentioned_products=[],
                    problem_category="general",
                    resolution_priority="medium"
                )
            else:
                return {
                    'support_query': user_query,
                    'support_category': "general_inquiry",
                    'customer_mood': "neutral",
                    'conversation_stage': "initial",
                    'mentioned_products': [],
                    'problem_category': "general",
                    'resolution_priority': "medium"
                }

    def get_intelligent_product_recommendations(self, customer_id: int, user_query: str,
                                              query_context: QueryContext) -> Dict[str, Any]:
        """🎯 Get intelligent product recommendations based on customer support context"""
        try:
            if not self.recommendation_engine:
                return self._get_basic_product_recommendations(customer_id, user_query, query_context)

            # Analyze support context
            support_context = self.analyze_customer_support_context(user_query, customer_id)

            recommendations = {}

            # Get context-aware recommendations
            if hasattr(support_context, 'support_category'):
                support_recommendations = self.recommendation_engine.get_customer_support_recommendations(
                    customer_id, support_context, limit=8)
                if support_recommendations:
                    recommendations['support_focused'] = support_recommendations

            # Get comprehensive recommendations for comparison
            comprehensive_recs = self.recommendation_engine.get_comprehensive_recommendations(
                customer_id, limit=15)

            if comprehensive_recs:
                # Filter based on context
                context_mood = getattr(support_context, 'customer_mood', 'neutral') if hasattr(support_context, 'customer_mood') else support_context.get('customer_mood', 'neutral')

                if context_mood == "frustrated":
                    # Prioritize premium products for frustrated customers
                    recommendations['satisfaction_recovery'] = comprehensive_recs.get('upgrade_tier', [])[:4]
                    recommendations['reliable_alternatives'] = comprehensive_recs.get('for_you', [])[:4]
                elif context_mood == "curious":
                    # Show trending and diverse options
                    recommendations['trending_now'] = comprehensive_recs.get('trending', [])[:6]
                    recommendations['explore_categories'] = comprehensive_recs.get('popular', [])[:4]
                else:
                    # Standard personalized recommendations
                    recommendations['personalized'] = comprehensive_recs.get('for_you', [])[:6]
                    recommendations['popular_choices'] = comprehensive_recs.get('popular', [])[:4]

            # Add cross-sell and upsell for shopping contexts
            if any(term in user_query.lower() for term in ['buy', 'purchase', 'add to cart', 'checkout']):
                # Track browsing and get cross-sell recommendations
                if hasattr(support_context, 'mentioned_products') and support_context.mentioned_products:
                    product_name = support_context.mentioned_products[0] if support_context.mentioned_products else None
                elif support_context.get('mentioned_products'):
                    product_name = support_context['mentioned_products'][0] if support_context['mentioned_products'] else None
                else:
                    product_name = None

                if product_name:
                    # Find product ID for cross-sell
                    product_id = self._find_product_id_by_name(product_name)
                    if product_id:
                        cross_sell_recs = self.recommendation_engine.get_cross_sell_recommendations(
                            customer_id, product_id, limit=4)
                        if cross_sell_recs:
                            recommendations['frequently_bought_together'] = cross_sell_recs

                        upsell_recs = self.recommendation_engine.get_upsell_recommendations(
                            customer_id, product_id, limit=3)
                        if upsell_recs:
                            recommendations['premium_alternatives'] = upsell_recs

            # Update conversation context
            if customer_id:
                if customer_id not in self.conversation_context:
                    self.conversation_context[customer_id] = {'interaction_count': 0}

                self.conversation_context[customer_id]['interaction_count'] += 1
                self.conversation_context[customer_id]['has_recommendations'] = bool(recommendations)
                self.conversation_context[customer_id]['last_query'] = user_query
                self.conversation_context[customer_id]['last_mood'] = getattr(support_context, 'customer_mood', 'neutral') if hasattr(support_context, 'customer_mood') else support_context.get('customer_mood', 'neutral')

            return {
                'success': True,
                'recommendations': recommendations,
                'support_context': support_context.__dict__ if hasattr(support_context, '__dict__') else support_context,
                'total_recommendations': sum(len(recs) for recs in recommendations.values()),
                'context_aware': True
            }

        except Exception as e:
            logger.error(f"❌ Error getting intelligent recommendations: {e}")
            return self._get_basic_product_recommendations(customer_id, user_query, query_context)

    def _find_product_id_by_name(self, product_name: str) -> Optional[int]:
        """🔍 Find product ID by name similarity"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT product_id FROM products
                        WHERE product_name ILIKE %s OR brand ILIKE %s
                        LIMIT 1
                    """, (f"%{product_name}%", f"%{product_name}%"))

                    result = cursor.fetchone()
                    return result['product_id'] if result else None

        except Exception as e:
            logger.error(f"❌ Error finding product ID: {e}")
            return None

    def _get_basic_product_recommendations(self, customer_id: int, user_query: str,
                                         query_context: QueryContext) -> Dict[str, Any]:
        """📦 Basic product recommendations fallback"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    # Get popular products as fallback
                    cursor.execute("""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity,
                               COUNT(o.order_id) as popularity
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        WHERE p.in_stock = true AND p.stock_quantity > 0
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity
                        ORDER BY popularity DESC
                        LIMIT 10
                    """)

                    products = cursor.fetchall()

                    basic_recommendations = []
                    for product in products:
                        basic_recommendations.append({
                            'product_id': product['product_id'],
                            'product_name': product['product_name'],
                            'category': product['category'],
                            'brand': product['brand'],
                            'price': float(product['price']),
                            'price_formatted': NigerianBusinessIntelligence.format_naira(product['price']),
                            'description': product['description'] or "",
                            'stock_quantity': product['stock_quantity'],
                            'popularity': product['popularity'],
                            'recommendation_reason': f"Popular choice • {product['popularity']} orders"
                        })

                    return {
                        'success': True,
                        'recommendations': {'popular': basic_recommendations},
                        'total_recommendations': len(basic_recommendations),
                        'context_aware': False
                    }

        except Exception as e:
            logger.error(f"❌ Error getting basic recommendations: {e}")
            return {
                'success': False,
                'recommendations': {},
                'total_recommendations': 0,
                'context_aware': False,
                'error': str(e)
            }

    def clear_session_context(self, session_id: str):
        """Clear all conversation context for a session to prevent data leakage"""
        try:
            if self.memory_system:
                self.memory_system.clear_session_context(session_id)
                logger.info(f"🧹 Cleared session context for session: {session_id}")

            # Also clear from database
            conn = self.get_database_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversation_context WHERE session_id = %s OR user_id = %s",
                              (session_id, session_id))
                deleted_count = cursor.rowcount
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"🗂️ Cleared {deleted_count} conversation contexts from database for session: {session_id}")

        except Exception as e:
            logger.error(f"❌ Error clearing session context for {session_id}: {e}")

    def _get_comprehensive_database_schema(self) -> str:
        """
        🗄️ Get comprehensive database schema for AI SQL generation
        This provides full knowledge of all tables, columns, and their meanings
        """
        return """
=== COMPREHENSIVE DATABASE SCHEMA FOR NIGERIAN E-COMMERCE PLATFORM ===

📊 CUSTOMERS TABLE:
- customer_id (SERIAL PRIMARY KEY) - Auto-incrementing unique customer identifier
- name (VARCHAR(100)) - Full customer name (First + Last name)
- email (VARCHAR(255) UNIQUE) - Unique email address for customer identification
- phone (VARCHAR(15)) - Nigerian phone format (+234 or 080x format)
- state (VARCHAR(50)) - Nigerian state (Lagos, Abuja, Kano, Rivers, etc.)
- lga (VARCHAR(50)) - Local Government Area for precise location
- address (TEXT) - Full shipping address with street, area, city details
- account_tier (ENUM: 'Bronze', 'Silver', 'Gold', 'Platinum') - Customer loyalty tier
- preferences (JSONB) - Customer preferences (language, categories, notifications)
- created_at (TIMESTAMP) - Account creation timestamp
- updated_at (TIMESTAMP) - Last profile update timestamp

🛒 ORDERS TABLE (PARTITIONED BY created_at):
⚠️ CRITICAL: ORDERS TABLE DOES NOT HAVE product_name OR product_id COLUMNS!
- order_id (SERIAL) - Order identifier (part of composite primary key)
- customer_id (INTEGER) - Reference to customers.customer_id
- order_status (ENUM: 'Pending', 'Processing', 'Delivered', 'Returned') - Current order status
- payment_method (ENUM: 'Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay') - Nigerian payment methods
- total_amount (NUMERIC(10,2)) - Total order value in Nigerian Naira (₦)
- delivery_date (DATE) - Expected or actual delivery date
- product_category (VARCHAR(50)) - ONLY category, NOT specific product names!
- created_at (TIMESTAMP) - Order creation timestamp
- updated_at (TIMESTAMP) - Last order update timestamp

📦 PRODUCTS TABLE:
- product_id (SERIAL PRIMARY KEY) - Unique product identifier
- product_name (VARCHAR(255)) - Product name/title (EXISTS ONLY IN PRODUCTS TABLE!)
- category (VARCHAR(100)) - Product category (Electronics, Fashion, Books, etc.)
- brand (VARCHAR(100)) - Product brand/manufacturer
- description (TEXT) - Detailed product description
- price (NUMERIC(10,2)) - Product price in Nigerian Naira (₦)
- currency (VARCHAR(3)) - Currency code (NGN for Nigerian Naira)
- in_stock (BOOLEAN) - Product availability status
- stock_quantity (INTEGER) - Available quantity in inventory
- created_at (TIMESTAMP) - Product creation timestamp
- updated_at (TIMESTAMP) - Last product update timestamp

📊 ANALYTICS TABLE:
- analytics_id (SERIAL PRIMARY KEY) - Analytics record identifier
- metric_type (VARCHAR(50)) - Type of metric (revenue, customer_count, order_volume, etc.)
- metric_value (JSONB) - Metric data in flexible JSON format
- time_period (VARCHAR(20)) - Time period (daily, weekly, monthly, yearly)
- created_at (TIMESTAMP) - Metric calculation timestamp

💬 CONVERSATION CONTEXT TABLE:
- context_id (UUID PRIMARY KEY) - Unique context identifier
- user_id (VARCHAR(100)) - User identifier ('customer_123' or 'anonymous')
- session_id (VARCHAR(100)) - Session identifier
- query_type (VARCHAR(50)) - Type of query (order_analytics, product_info, etc.)
- entities (JSONB) - Extracted entities from conversation
- sql_query (TEXT) - Generated SQL query
- execution_result (JSONB) - Query results
- response_text (TEXT) - Generated AI response
- user_query (TEXT) - Original user query
- timestamp (TIMESTAMP) - Conversation timestamp

💬 CHAT TABLES:
- chat_conversations: conversation_id, session_id, conversation_title, created_at, updated_at, is_active
- chat_messages: message_id, conversation_id, sender_type, message_content, metadata, created_at
- user_sessions: session_id, user_identifier, created_at, last_active, session_data

🚨 CRITICAL TABLE RELATIONSHIPS & CONSTRAINTS:
- orders.customer_id → customers.customer_id (Foreign Key)
- ORDERS TABLE HAS NO DIRECT PRODUCT REFERENCE! No product_id or product_name!
- To get specific product info for orders, you CANNOT JOIN directly
- Orders only have product_category, not specific product names

⚠️ SCHEMA RESTRICTIONS:
1. NEVER use product_name in orders table - IT DOESN'T EXIST!
2. NEVER use product_id in orders table - IT DOESN'T EXIST!
3. Orders table only has product_category for product classification
4. For specific product queries, use products table separately
5. Cannot determine which specific products were ordered from orders table alone

📈 CORRECT QUERY PATTERNS:
- Customer orders by category: SELECT * FROM orders WHERE customer_id = X AND product_category = 'Electronics'
- Product search: SELECT * FROM products WHERE product_name ILIKE '%search%'
- Order analytics by category: SELECT product_category, COUNT(*) FROM orders GROUP BY product_category
- Geographic data: SELECT state, COUNT(*) FROM customers GROUP BY state
- Payment analytics: SELECT payment_method, COUNT(*) FROM orders GROUP BY payment_method

🚫 INCORRECT QUERY PATTERNS (WILL FAIL):
- SELECT * FROM orders WHERE product_name = 'iPhone' (product_name NOT in orders!)
- SELECT o.*, p.product_name FROM orders o JOIN products p... (NO foreign key to join!)
- UPDATE orders SET product_name = ... (column doesn't exist!)

⚠️ CRITICAL NOTES:
- Use IS NULL instead of = NULL for null checks
- customer_id should only be used when user is authenticated
- All monetary amounts are in Nigerian Naira (₦)
- Phone numbers follow Nigerian format (+234 or 080x)
- States refer to Nigerian states (36 states + FCT)
- Orders table is simplified - no direct product references
"""

    def _get_database_schema_context(self) -> str:
        """Get comprehensive database schema context for SQL generation"""
        schema_context = self._get_comprehensive_database_schema()

        # Add current timestamp and timezone info
        current_time = datetime.now()
        time_context = f"""
CURRENT TIME CONTEXT:
- Current timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S')} WAT (West Africa Time)
- Current date: {current_time.strftime('%Y-%m-%d')}
- Current year: {current_time.year}
- Current month: {current_time.strftime('%B %Y')}
- Time zone: WAT (UTC+1)
"""

        return f"{schema_context}\n{time_context}"

    def _format_currency_in_results(self, results: List[Dict], session_context: Dict[str, Any] = None) -> List[Dict]:
        """Format currency values in database results using Nigerian Naira"""
        if not results:
            return results

        # Check if this is a WhatsApp request
        is_whatsapp = False
        if session_context:
            is_whatsapp = session_context.get('channel') == 'whatsapp'

        # Currency field names that should be formatted
        currency_fields = [
            'total_amount', 'amount', 'price', 'cost', 'value', 'revenue',
            'total_spent', 'lifetime_value', 'total_revenue', 'average_order_value',
            'order_value', 'payment_amount', 'subtotal', 'discount_amount',
            'current_quarter_revenue', 'monthly_revenue', 'daily_revenue'
        ]

        formatted_results = []

        for result in results:
            formatted_result = {}
            for key, value in result.items():
                # Check if this field should be formatted as currency
                if key.lower() in currency_fields and value is not None:
                    try:
                        # Convert to float if it's not already
                        if isinstance(value, (int, float, decimal.Decimal)):
                            formatted_result[key] = NigerianBusinessIntelligence.format_naira(float(value), whatsapp_format=is_whatsapp)
                        else:
                            formatted_result[key] = value
                    except (ValueError, TypeError):
                        formatted_result[key] = value
                else:
                    formatted_result[key] = value

            formatted_results.append(formatted_result)

        return formatted_results

    def _apply_critical_sql_fixes(self, sql_query: str, entities: Dict[str, Any]) -> str:
        """
        🔧 Apply critical SQL fixes for PostgreSQL compatibility and security
        """
        try:
            fixed_query = sql_query.strip()

            # 🚨 CRITICAL AUTHORIZATION & SECURITY VALIDATION
            user_authenticated = entities.get('user_authenticated', False)
            customer_id = entities.get('customer_id')
            context_customer_id = entities.get('context_customer_id')
            # 🔧 CRITICAL FIX: Prioritize context_customer_id for support agents
            effective_customer_id = context_customer_id or customer_id
            user_query = entities.get('user_query', '').lower()

            # 🚨 CRITICAL SHIPPING FEE CALCULATION FIXES
            # Fix 1: Block incorrect "shipping fee" queries that try to use payment methods
            if ('shipping fee' in user_query or 'shipping cost' in user_query) and 'payment_method' in fixed_query:
                print_log("🔧 BLOCKED INCORRECT SHIPPING FEE QUERY: Cannot calculate shipping fees from payment methods", 'warning')
                return "SELECT 'Shipping fees are calculated based on delivery zones, not available in order history. Contact support for shipping rate information.' as shipping_info;"

            # Fix 2: Block queries trying to sum total_amount as "shipping fees"
            if ('total_shipping_fees' in fixed_query or 'shipping_fee' in fixed_query) and 'SUM(total_amount)' in fixed_query:
                print_log("🔧 BLOCKED INCORRECT SHIPPING FEE QUERY: Cannot use total_amount as shipping fees", 'warning')
                return "SELECT 'Shipping costs are included in order totals. Our database does not track shipping fees separately. Standard rates: Lagos ₦2,000, Abuja ₦2,500, Major Cities ₦3,000, Other States ₦4,000.' as shipping_info;"

            # Fix 3: Fix specific wrong shipping fee calculation patterns
            if 'CASE WHEN payment_method = \'Pay on Delivery\' THEN 0 ELSE total_amount END' in fixed_query:
                print_log("🔧 BLOCKED PAYMENT METHOD SHIPPING LOGIC: This makes no sense for shipping calculations", 'warning')
                return "SELECT 'Shipping fees are not calculated from payment methods. Our standard rates: Lagos ₦2,000, Abuja ₦2,500, Major Cities ₦3,000, Other States ₦4,000. Gold/Platinum members get free delivery!' as shipping_rates;"

            # 🚨 BUSINESS ANALYTICS PROTECTION: Prevent customers from accessing business-wide data
            # 🔧 CRITICAL FIX: Check for legitimate business analytics flag first
            is_business_analytics = entities.get('business_analytics', False)
            user_role = entities.get('user_role', 'customer')
            can_access_analytics = entities.get('can_access_analytics', False)

            if ('GROUP BY' in fixed_query.upper() and 'orders' in fixed_query.lower() and
                'WHERE customer_id' not in fixed_query and not is_business_analytics):
                if not user_authenticated:
                    print_log("🔒 SECURITY ALERT: Preventing business analytics access for unauthenticated user!", 'error')
                    return "SELECT 'Access denied: Business analytics require authentication.' as message;"
                elif user_authenticated and effective_customer_id and not can_access_analytics:
                    # 🔧 CRITICAL FIX: Only restrict for customers, NOT for super_admin/admin
                    if user_role in ['super_admin', 'admin']:
                        print_log(f"🏢 BUSINESS ANALYTICS APPROVED: Allowing platform-wide query for {user_role}", 'info')
                        # Let the query pass through without modification for admins
                    else:
                        print_log(f"🔒 SECURITY: Converting business analytics to customer-specific for customer {effective_customer_id} (role: {user_role})", 'warning')
                        # Convert business-wide analytics to customer-specific analytics (only for customers)
                        if 'SELECT order_status, COUNT(*)' in fixed_query:
                            return f"SELECT order_status, COUNT(*) as order_count, SUM(total_amount) as total_amount FROM orders WHERE customer_id = {effective_customer_id} GROUP BY order_status;"
                        elif 'SELECT COUNT(*), SUM(total_amount)' in fixed_query:
                            return f"SELECT COUNT(*) as order_count, SUM(total_amount) as total_amount FROM orders WHERE customer_id = {effective_customer_id};"
                        else:
                            # Default to customer's orders only
                            return f"SELECT * FROM orders WHERE customer_id = {effective_customer_id} ORDER BY created_at DESC;"
            elif is_business_analytics or can_access_analytics:
                print_log(f"🏢 BUSINESS ANALYTICS APPROVED: Allowing platform-wide query for legitimate business request (user_role: {user_role})", 'info')

            # 🚨 UNAUTHENTICATED USER RESTRICTIONS
            if not user_authenticated:
                # Prevent access to full product catalog for unauthenticated users
                if 'SELECT product_name FROM products' in fixed_query and 'WHERE' not in fixed_query.upper():
                    print_log("🔒 SECURITY: Limiting product access for unauthenticated user", 'warning')
                    fixed_query = "SELECT 'Please log in to browse our full product catalog. Contact us for assistance.' as message;"

                # Prevent access to customer data
                if 'FROM CUSTOMERS' in fixed_query.upper():
                    print_log("🔒 SECURITY ALERT: Blocking customer data access for unauthenticated user!", 'error')
                    return "SELECT 'Authentication required to access customer information.' as message;"

                # Prevent access to order data (except with specific order_id)
                if 'FROM ORDERS' in fixed_query.upper() and 'order_id =' not in fixed_query:
                    print_log("🔒 SECURITY: Blocking order data access for unauthenticated user", 'warning')
                    return "SELECT 'Please provide an order number or log in to view order information.' as message;"

            # 🚨 CRITICAL SCHEMA VALIDATION: Prevent column misuse between tables
            schema_violations = []

            # Check for product_name usage in orders table (CRITICAL ERROR!)
            if 'orders' in fixed_query.lower() and 'product_name' in fixed_query.lower():
                schema_violations.append("❌ SCHEMA ERROR: product_name column does not exist in orders table! Use product_category instead.")
                # Replace with product_category for orders table
                if 'WHERE' in fixed_query.upper() and 'product_name' in fixed_query:
                    fixed_query = fixed_query.replace('product_name', 'product_category')
                    fixed_query += " -- WARNING: Replaced product_name with product_category for orders table"

            # Check for product_id usage in orders table (CRITICAL ERROR!)
            if 'orders' in fixed_query.lower() and 'product_id' in fixed_query.lower():
                schema_violations.append("❌ SCHEMA ERROR: product_id column does not exist in orders table!")
                # Cannot fix this automatically - it's a fundamental schema error

            # Check for invalid JOINs between orders and products (no foreign key exists!)
            if ('JOIN products' in fixed_query.upper() and 'orders' in fixed_query.lower() and
                ('ON o.product_id = p.product_id' in fixed_query or 'ON orders.product_id = products.product_id' in fixed_query)):
                schema_violations.append("❌ SCHEMA ERROR: Cannot JOIN orders with products - no foreign key relationship exists!")

            # If critical schema violations found, return a safe fallback query
            if schema_violations:
                print_log(f"🚨 CRITICAL SCHEMA VIOLATIONS DETECTED: {'; '.join(schema_violations)}", 'error')

                # Return a safe fallback based on the original intent
                if user_authenticated and effective_customer_id:
                    return f"SELECT * FROM orders WHERE customer_id = {effective_customer_id} ORDER BY created_at DESC;"
                else:
                    return "SELECT 'Schema violation detected. Please rephrase your query.' as error_message;"

            # 1. Fix NULL comparison syntax (PostgreSQL compatibility)
            fixed_query = re.sub(r'\b(\w+)\s*=\s*NULL\b', r'\1 IS NULL', fixed_query, flags=re.IGNORECASE)
            fixed_query = re.sub(r'\b(\w+)\s*=\s*None\b', r'\1 IS NULL', fixed_query, flags=re.IGNORECASE)
            fixed_query = re.sub(r'\b(\w+)\s*!=\s*NULL\b', r'\1 IS NOT NULL', fixed_query, flags=re.IGNORECASE)
            fixed_query = re.sub(r'\b(\w+)\s*!=\s*None\b', r'\1 IS NOT NULL', fixed_query, flags=re.IGNORECASE)

            # 2. Replace problematic "column 'none'" references
            fixed_query = re.sub(r"WHERE\s+customer_id\s*=\s*'?none'?",
                               "WHERE customer_id IS NULL", fixed_query, flags=re.IGNORECASE)

            # 3. Security: Validate customer_id authentication
            # Prevent hard-coded customer IDs for unauthenticated users
            if not user_authenticated and 'customer_id' in fixed_query:
                # Check for specific hard-coded customer IDs (security risk!)
                hardcoded_patterns = re.findall(r'customer_id\s*=\s*(\d+)', fixed_query, re.IGNORECASE)
                if hardcoded_patterns:
                    print_log(f"🔒 SECURITY ALERT: Hard-coded customer_id detected for unauthenticated user!", 'error')
                    return "SELECT 'Authentication required to access customer data.' as message;"

            # 4. Handle authentication status queries properly
            if 'authentication status' in entities.get('user_query', '').lower():
                if user_authenticated and effective_customer_id:
                    return f"SELECT 'authenticated' as status, {effective_customer_id} as customer_id;"
                else:
                    return "SELECT 'unauthenticated' as status, NULL as customer_id;"

            # 5. Fix common PostgreSQL syntax issues
            fixed_query = re.sub(r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b',
                               r'OFFSET \2 LIMIT \1', fixed_query, flags=re.IGNORECASE)

            # 6. Handle placeholder detection and replacement
            if 'provided_order_id' in fixed_query or 'provided_customer_id' in fixed_query:
                if effective_customer_id:
                    fixed_query = fixed_query.replace('provided_customer_id', str(effective_customer_id))
                    fixed_query = fixed_query.replace('provided_order_id', 'NULL')  # Safe default

            # 7. Fix malformed WHERE clauses
            fixed_query = re.sub(r'WHERE\s*AND\s+', 'WHERE ', fixed_query, flags=re.IGNORECASE)
            fixed_query = re.sub(r'WHERE\s*OR\s+', 'WHERE ', fixed_query, flags=re.IGNORECASE)

            # 8. Ensure proper semicolon termination
            if not fixed_query.rstrip().endswith(';'):
                fixed_query += ';'

            # 9. Final validation: Check if query references actual tables
            valid_tables = ['customers', 'orders', 'products', 'analytics', 'conversation_context',
                          'chat_conversations', 'chat_messages', 'user_sessions']

            # Extract table references from query
            table_pattern = r'\b(?:FROM|JOIN|UPDATE|INSERT\s+INTO)\s+(\w+)'
            referenced_tables = re.findall(table_pattern, fixed_query, re.IGNORECASE)

            for table in referenced_tables:
                if table.lower() not in [t.lower() for t in valid_tables]:
                    print_log(f"⚠️ WARNING: Query references unknown table '{table}'", 'warning')

                        # 🚨 CRITICAL TIER CALCULATION FIXES
            # Fix 1: Correct Platinum tier threshold (₦1M → ₦2M) - MUST BE FIRST
            if '1000000' in fixed_query:
                fixed_query = fixed_query.replace('1000000', '2000000')
                print_log("🔧 FIXED: Corrected Platinum tier threshold from ₦1M to ₦2M", 'info')

            # Fix 2: Remove invalid order_status filter from customers table
            if 'FROM customers WHERE order_status' in fixed_query:
                # Remove the invalid order_status filter from customers table
                fixed_query = re.sub(r'FROM customers WHERE order_status != ["\']Returned["\'] AND', 'FROM customers WHERE', fixed_query)
                print_log("🔧 FIXED: Removed invalid order_status filter from customers table", 'info')

            # Fix 3: AGGRESSIVE PLATINUM TIER QUERY REPLACEMENT - NUCLEAR OPTION
            if ('platinum' in user_query.lower() and ('how much more' in user_query.lower() or 'much more' in user_query.lower()) and effective_customer_id):
                # FORCE REPLACE any Platinum tier query with the standard working pattern
                simple_query = f"""SELECT CASE WHEN c.account_tier = 'Platinum' THEN 0
                                  ELSE GREATEST(0, 2000000 - COALESCE(SUM(o.total_amount), 0))
                                  END AS amount_needed
                                  FROM customers c
                                  LEFT JOIN orders o ON c.customer_id = o.customer_id
                                  WHERE c.customer_id = {effective_customer_id}
                                  AND (o.order_status != 'Returned' OR o.order_status IS NULL)
                                  GROUP BY c.account_tier;"""
                fixed_query = simple_query
                print_log("🔧 NUCLEAR FIX: Completely replaced Platinum tier query with proven working pattern", 'info')

            # Fix 4: Block any analytics table queries with wrong column names
            if 'SELECT value FROM analytics' in fixed_query:
                fixed_query = fixed_query.replace('SELECT value FROM analytics', 'SELECT metric_value FROM analytics')
                print_log("🔧 FIXED: Corrected analytics column from 'value' to 'metric_value'", 'info')

            print_log(f"🔒 SECURITY CHECK PASSED: Query authorized for user (authenticated: {user_authenticated}, customer_id: {effective_customer_id})", 'success')
            return fixed_query

        except Exception as e:
            print_log(f"❌ Error in SQL fixes: {e}", 'error')
            # Return safe fallback
            if user_authenticated and effective_customer_id:
                return f"SELECT * FROM orders WHERE customer_id = {effective_customer_id};"
            return "SELECT 'Query processing error' as message;"

    def get_system_prompt(self) -> str:
        """🎯 Enhanced system prompt with comprehensive Nigerian e-commerce knowledge"""
        return f"""
You are a helpful AI assistant for raqibtech.com, a leading Nigerian e-commerce platform.
You help customers with orders, product information, account management, and business analytics.

=== ACCOUNT TIER SYSTEM (CRITICAL KNOWLEDGE) ===

**TIER PROGRESSION & BENEFITS:**

🥉 **BRONZE TIER** (Entry Level - ₦0 to ₦100K total spent):
- Standard customer service
- No discounts on orders
- Standard delivery fees apply
- Access to basic product catalog

🥈 **SILVER TIER** (₦100K+ total spent, 3+ orders):
- 2% discount on all orders
- Priority customer support
- Standard delivery fees
- Early access to sales events

🥇 **GOLD TIER** (₦500K+ total spent, 10+ orders):
- 5% discount on all orders
- FREE DELIVERY on all orders (normally ₦2K-₦4K)
- Premium customer support
- Exclusive Gold member promotions

💎 **PLATINUM TIER** (₦2M+ total spent, 20+ orders):
- 10% discount on all orders
- FREE DELIVERY + FREE EXPRESS SHIPPING
- Dedicated account manager
- VIP customer support hotline
- Exclusive Platinum-only products

**HOW TO UPGRADE TIERS:**
- Tiers are automatically upgraded based on total spending
- Bronze → Silver: Spend ₦100,000 total
- Silver → Gold: Spend ₦500,000 total
- Gold → Platinum: Spend ₦2,000,000 total
- Tier status is permanent once achieved

=== CUSTOMER ACCOUNT MANAGEMENT ===

**CUSTOMERS CAN ASK ABOUT:**
- Current account tier and benefits
- How much they've spent total
- Monthly/yearly spending breakdown
- How to upgrade to next tier
- Order history and tracking
- Delivery addresses and phone updates

**CUSTOMERS CAN UPDATE:**
- Phone number, Email address, Delivery address
- Password, Newsletter preferences, Notification settings

=== ACCOUNT TIER SYSTEM (CRITICAL KNOWLEDGE) ===

**TIER PROGRESSION & BENEFITS:**

🥉 **BRONZE TIER** (Entry Level - ₦0 to ₦100K total spent):
- Standard customer service
- No discounts on orders
- Standard delivery fees apply
- Access to basic product catalog
- Email notifications for promotions

🥈 **SILVER TIER** (₦100K+ total spent, 3+ orders):
- 2% discount on all orders
- Priority customer support
- Standard delivery fees
- Early access to sales events
- Enhanced return policy (14 days)

🥇 **GOLD TIER** (₦500K+ total spent, 10+ orders):
- 5% discount on all orders
- FREE DELIVERY on all orders (normally ₦2K-₦4K)
- Premium customer support
- Exclusive Gold member promotions
- Extended return policy (21 days)
- Birthday month special offers

💎 **PLATINUM TIER** (₦2M+ total spent, 20+ orders):
- 10% discount on all orders
- FREE DELIVERY + FREE EXPRESS SHIPPING
- Dedicated account manager
- VIP customer support hotline
- Exclusive Platinum-only products
- Extended return policy (30 days)
- Quarterly bonus rewards
- First access to new product launches

**HOW TO UPGRADE TIERS:**
- Tiers are automatically upgraded based on total spending
- Bronze → Silver: Spend ₦100,000 total
- Silver → Gold: Spend ₦500,000 total
- Gold → Platinum: Spend ₦2,000,000 total
- Tier status is permanent once achieved
- Bonuses: Long-term customers (1+ years) get 10% bonus towards tier progression
- Bonuses: Long-term customers (2+ years) get 20% bonus towards tier progression

=== CUSTOMER ACCOUNT MANAGEMENT ===

**CUSTOMERS CAN ASK ABOUT:**
- Current account tier and benefits
- How much they've spent total
- Monthly/yearly spending breakdown
- How to upgrade to next tier
- Order history and tracking
- Delivery addresses and phone updates
- Payment method preferences
- Account tier incentives and rewards

**CUSTOMERS CAN UPDATE:**
- Phone number
- Email address
- Delivery address
- Password
- Newsletter preferences
- Notification settings
- Preferred categories

**SPENDING & ANALYTICS QUERIES CUSTOMERS CAN MAKE:**
- "Show me my spending breakdown by month"
- "How much have I spent this year?"
- "What's my total spending since joining?"
- "How much more to reach Platinum tier?"
- "What are the benefits of Gold tier?"
- "How do I upgrade my account tier?"

=== SECURITY & PRIVACY ===
- Customers can ONLY access their own data (customer_id must match session)
- Never show other customers' information
- Always confirm identity before account changes
- Explain benefits clearly and encourage tier progression

=== DELIVERY ZONES & FEES ===
- Lagos Metro: ₦2,000 (1-day delivery)
- Abuja FCT: ₦2,500 (2-day delivery)
- Major Cities: ₦3,000 (3-day delivery)
- Other States: ₦4,000 (5-day delivery)
- FREE delivery for Gold & Platinum tiers
- FREE express shipping for Platinum tier

=== EXAMPLES FOR CUSTOMER QUERIES ===

Customer Tier Query Examples (use customer_id from session):
- "What's my current account tier?" → SELECT account_tier FROM customers WHERE customer_id = [session_customer_id];
- "Show me my account information" → SELECT name, email, phone, account_tier, state, lga FROM customers WHERE customer_id = [session_customer_id];
- "How much have I spent total?" → SELECT COALESCE(SUM(total_amount), 0) as total_spent FROM orders WHERE customer_id = [session_customer_id] AND order_status != 'Returned';
- "Show me my spending breakdown by month" → SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as monthly_spending FROM orders WHERE customer_id = [session_customer_id] GROUP BY month ORDER BY month DESC;
- "How much more do I need to spend to reach Platinum tier?" → SELECT CASE WHEN c.account_tier = 'Platinum' THEN 0 ELSE GREATEST(0, 2000000 - COALESCE(SUM(o.total_amount), 0)) END AS amount_needed FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE c.customer_id = [session_customer_id] AND (o.order_status != 'Returned' OR o.order_status IS NULL) GROUP BY c.account_tier;

For all customer queries, always:
1. Use the customer_id from the session context
2. Explain tier benefits clearly
3. Encourage tier progression when appropriate
4. Be helpful and encouraging about account management

=== COMPREHENSIVE PRODUCT CATALOG KNOWLEDGE ===

**FOOD & STAPLES CATEGORY:**
• **Grains & Cereals:** Golden Penny Semovita, Honeywell Wheat Flour, Mama Gold Rice (50kg), Cap Rice (25kg), Dangote Spaghetti, Cassava Flour (Garri)
• **Proteins:** Titus Fish (Frozen), Chicken (Whole), Beef (Fresh Cut), Dried Fish (Stockfish), Smoked Turkey, Corned Beef, Sardine in Tomato Sauce
• **Spices & Seasonings:** Maggi Cubes, Curry Powder, Thyme Leaves, Scotch Bonnet Pepper (Ata Rodo), Locust Beans (Iru)
• **Cooking Oils:** Devon Kings Vegetable Oil, Red Palm Oil, Groundnut Oil, Coconut Oil (Virgin)
• **Beverages:** Milo Chocolate Drink, Bournvita, Lipton Tea Bags, Peak Milk Powder, Hollandia Yoghurt
• **Snacks:** Plantain Chips, Chin Chin, Groundnut (Roasted), Kuli Kuli, Coconut Candy
• **Fresh Produce:** Yam Tuber (Medium), Sweet Potato, Plantain (Bunch)
• **Canned Foods:** Sweet Corn (Canned), Honey

**FASHION & APPAREL:**
• **Men's Fashion:** Polo shirts, dress shirts, traditional wear, shoes, belts, wallets
• **Women's Fashion:** Dresses, blouses, traditional wear, shoes, handbags, jewelry
• **Unisex Items:** Jeans, t-shirts, sneakers, watches, accessories

**ELECTRONICS & GADGETS:**
• **Mobile Phones:** Latest smartphones, accessories, cases, chargers
• **Computing:** Laptops, tablets, computer accessories, software
• **Audio/Visual:** Headphones, speakers, smart TVs, gaming devices
• **Home Appliances:** Refrigerators, washing machines, microwaves, fans

**BEAUTY & PERSONAL CARE:**
• **Skincare:** Moisturizers, cleansers, sunscreens, anti-aging products
• **Haircare:** Shampoos, conditioners, styling products, hair treatments
• **Cosmetics:** Makeup, nail polish, beauty tools, fragrances
• **Personal Hygiene:** Soaps, deodorants, oral care products

**HOME & LIVING:**
• **Furniture:** Chairs, tables, beds, storage solutions
• **Decor:** Wall art, lighting, rugs, curtains, decorative items
• **Kitchen:** Cookware, utensils, small appliances, dining sets
• **Bedding:** Sheets, pillows, comforters, mattresses

**BOOKS & STATIONERY:**
• **Educational:** Textbooks, workbooks, reference materials
• **Fiction/Non-fiction:** Novels, biographies, self-help books
• **Stationery:** Notebooks, pens, markers, office supplies

**HEALTH & WELLNESS:**
• **Supplements:** Vitamins, minerals, protein powders
• **Medical Supplies:** First aid, thermometers, health monitors
• **Fitness:** Exercise equipment, yoga mats, sports gear

**PRODUCT SEARCH INTELLIGENCE:**
When customers mention abbreviated terms, map them intelligently:
• "spag/spagh" → Dangote Spaghetti 500g
• "rice" → Mama Gold Rice or Cap Rice
• "oil" → Devon Kings Vegetable Oil, Red Palm Oil, etc.
• "milk" → Peak Milk Powder, Hollandia Yoghurt
• "phone" → Mobile phones category
• "laptop" → Computing category

**PRICING RANGES (Nigerian Naira ₦):**
• Food items: ₦1,500 - ₦85,000 (Rice 50kg being highest)
• Electronics: ₦15,000 - ₦500,000+
• Fashion: ₦5,000 - ₦75,000
• Beauty: ₦2,000 - ₦25,000
• Books: ₦3,000 - ₦15,000

CRITICAL RULES:
- ALWAYS exclude returned orders when calculating spending: AND order_status != 'Returned'
- Platinum tier threshold is EXACTLY ₦2,000,000 (TWO MILLION NAIRA) - NEVER use ₦1,000,000
- Gold tier threshold is ₦500,000, Silver tier threshold is ₦100,000
- Never show spending amounts that include returned orders
- When users ask about food, show food products. When they say "spag", understand they mean spaghetti
- Always check product availability with: AND in_stock = TRUE
- Use intelligent product matching for abbreviations and common terms

Current timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database schema: Customers, Orders, Products, Order_Items, Customer_Conversations, Analytics tables available.
Currency format: Nigerian Naira (₦) with proper thousand separators.
"""

    def generate_tier_benefits_response(self, user_query: str, mentioned_tier: str = None) -> str:
        """Generate tier benefits response using built-in tier information"""
        try:
            # Get customer's current tier if they're authenticated
            current_tier = None
            if hasattr(self, 'session_context') and self.session_context.get('customer_id'):
                customer_id = self.session_context['customer_id']
                with self.get_database_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("SELECT account_tier FROM customers WHERE customer_id = %s", (customer_id,))
                        result = cursor.fetchone()
                        if result:
                            current_tier = result['account_tier']

            # Tier benefits information
            tier_benefits = {
                'Bronze': {
                    'emoji': '🥉',
                    'name': 'BRONZE TIER',
                    'threshold': '₦0 to ₦100K total spent',
                    'benefits': [
                        'Standard customer service',
                        'No discounts on orders',
                        'Standard delivery fees apply',
                        'Access to basic product catalog',
                        'Email notifications for promotions'
                    ]
                },
                'Silver': {
                    'emoji': '🥈',
                    'name': 'SILVER TIER',
                    'threshold': '₦100K+ total spent, 3+ orders',
                    'benefits': [
                        '2% discount on all orders',
                        'Priority customer support',
                        'Standard delivery fees',
                        'Early access to sales events',
                        'Enhanced return policy (14 days)'
                    ]
                },
                'Gold': {
                    'emoji': '🥇',
                    'name': 'GOLD TIER',
                    'threshold': '₦500K+ total spent, 10+ orders',
                    'benefits': [
                        '5% discount on all orders',
                        'FREE DELIVERY on all orders (normally ₦2K-₦4K)',
                        'Premium customer support',
                        'Exclusive Gold member promotions',
                        'Extended return policy (21 days)',
                        'Birthday month special offers'
                    ]
                },
                'Platinum': {
                    'emoji': '💎',
                    'name': 'PLATINUM TIER',
                    'threshold': '₦2M+ total spent, 20+ orders',
                    'benefits': [
                        '10% discount on all orders',
                        'FREE DELIVERY + FREE EXPRESS SHIPPING',
                        'Dedicated account manager',
                        'VIP customer support hotline',
                        'Exclusive Platinum-only products',
                        'Extended return policy (30 days)',
                        'Quarterly bonus rewards',
                        'First access to new product launches'
                    ]
                }
            }

            # Determine which tier to display
            target_tier = mentioned_tier or current_tier or 'Gold'  # Default to Gold if not specified

            if target_tier not in tier_benefits:
                target_tier = 'Gold'

            tier_info = tier_benefits[target_tier]

            # Build response
            response = f"Here are the amazing benefits of being a **{tier_info['name']}** member on raqibtech.com! 🎉\n\n"
            response += f"{tier_info['emoji']} **{tier_info['name']}** ({tier_info['threshold']}):\n"

            for benefit in tier_info['benefits']:
                response += f"• {benefit}\n"

            # Add progression info if not Platinum
            if target_tier != 'Platinum':
                next_tier_map = {'Bronze': 'Silver', 'Silver': 'Gold', 'Gold': 'Platinum'}
                next_tier = next_tier_map.get(target_tier)
                if next_tier:
                    next_info = tier_benefits[next_tier]
                    response += f"\n🚀 **Want to upgrade to {next_info['name']}?**\n"
                    response += f"Reach {next_info['threshold']} to unlock even more exclusive benefits!\n"

            # Add current status if authenticated
            if current_tier:
                if current_tier == target_tier:
                    response += f"\n✨ You're currently enjoying all these {target_tier} tier benefits!"
                else:
                    response += f"\n📊 You're currently a {current_tier} tier member."

            response += "\n\nHope this helps! If you have any questions about your account or benefits, feel free to ask! 💙"

            return response

        except Exception as e:
            logger.error(f"❌ Error generating tier benefits response: {e}")
            return "I'd be happy to help you learn about our tier benefits! Please let me check your account status first, or feel free to ask about any specific tier you're interested in."

    def _format_whatsapp_order_table(self, results: List[Dict]) -> str:
        """Format order information specifically for WhatsApp in a mobile-friendly way"""
        if not results:
            return "No orders found. 📭"

        # Format header
        header = "📋 *Your Orders*\n" + "="*30 + "\n\n"

        formatted_orders = []
        for i, order in enumerate(results, 1):
            # Extract order information
            order_id = order.get('order_id', 'N/A')
            status = order.get('order_status', order.get('status', 'Unknown'))
            payment_method = order.get('payment_method', 'N/A')
            total_amount = order.get('total_amount', 0)
            delivery_date = order.get('delivery_date', order.get('expected_delivery', 'N/A'))
            category = order.get('product_category', order.get('category', 'N/A'))

            # Format amount with full display (no K abbreviation)
            if isinstance(total_amount, (int, float)):
                amount_str = f"₦{total_amount:,.0f}"
            else:
                amount_str = str(total_amount)

            # Choose appropriate emojis for status
            status_emoji = {
                'pending': '⏳',
                'processing': '⚙️',
                'shipped': '🚚',
                'delivered': '✅',
                'cancelled': '❌',
                'returned': '🔄'
            }.get(status.lower(), '📦')

            # Choose emoji for payment method
            payment_emoji = {
                'pay on delivery': '📦',
                'bank transfer': '🏦',
                'card': '💳',
                'raqibtechpay': '💰'
            }.get(payment_method.lower(), '💳')

            # Format each order
            order_text = f"*{i}. Order #{order_id}*\n"
            order_text += f"{status_emoji} Status: {status}\n"
            order_text += f"{payment_emoji} Payment: {payment_method}\n"
            order_text += f"💰 Total: {amount_str}\n"
            order_text += f"📅 Delivery: {delivery_date}\n"
            order_text += f"🏷️ Category: {category}\n"

            formatted_orders.append(order_text)

        # Combine all orders
        orders_text = "\n" + "─"*25 + "\n".join(formatted_orders)

        # Add footer
        footer = f"\n{'─'*30}\n"
        footer += f"📊 Total Orders: {len(results)}\n"
        footer += "💬 Reply with order number for details\n"
        footer += "🌐 Track all orders: raqibtech.com"

        return header + orders_text + footer

    def _should_use_whatsapp_format(self, session_context: Dict[str, Any], query_context: QueryContext) -> bool:
        """Determine if WhatsApp-specific formatting should be used"""
        if not session_context:
            return False

        # Check if this is a WhatsApp channel
        is_whatsapp = session_context.get('channel') == 'whatsapp'

        # Check if this is an order-related query
        is_order_query = (
            query_context.query_type == QueryType.ORDER_ANALYTICS or
            'order' in query_context.user_query.lower() or
            any(field in str(query_context.execution_result).lower()
                for field in ['order_id', 'order_status', 'payment_method'])
        )

        return is_whatsapp and is_order_query

