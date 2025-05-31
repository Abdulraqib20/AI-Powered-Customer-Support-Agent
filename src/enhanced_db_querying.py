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

# 🆕 PRODUCT CATEGORIES for Nigerian E-commerce
NIGERIAN_PRODUCT_CATEGORIES = [
    'Electronics', 'Fashion', 'Beauty', 'Computing', 'Automotive', 'Books'
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
    def format_naira(amount: float) -> str:
        """Format amount in Nigerian Naira"""
        if amount >= 1_000_000:
            return f"₦{amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"₦{amount/1_000:.1f}K"
        else:
            return f"₦{amount:,.2f}"

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
    logger.info("✅ Successfully imported enhanced components")
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

        logger.info("🚀 Enhanced Database Querying System initialized successfully")

    def classify_query_intent(self, user_query: str, conversation_history: List[Dict] = None) -> Tuple[QueryType, Dict[str, Any]]:
        """
        🧠 Intelligent query classification using AI with Nigerian e-commerce context
        """
        user_query_lower = user_query.lower()
        query_lower = user_query_lower  # Alias for consistent naming

        # Initialize entities dict early to prevent reference errors
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

        # 🆕 CUSTOMER SUPPORT CONTACT QUERIES - Handle these specially
        if any(phrase in user_query_lower for phrase in [
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
- Products: Electronics, Fashion, Beauty, Computing, Automotive, Books
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

        # 🔧 CRITICAL FIX: Conversation history inheritance (only for guest users with missing context)
        if conversation_history and not entities['order_id']:
            # Look for order_id from recent conversation
            for conversation in conversation_history[:3]:  # Check last 3 conversations
                if 'entities' in conversation:
                    conv_entities = conversation['entities']

                    # Inherit order_id if available (for both guest and authenticated users)
                    if conv_entities.get('order_id') and not entities['order_id']:
                        entities['order_id'] = conv_entities['order_id']
                        logger.info(f"🔄 Inherited order_id from conversation history: {entities['order_id']}")

                    # 🔧 CRITICAL FIX: NEVER inherit customer_id from conversation history
                    # This was causing cross-user contamination
                    # Let the calling function handle customer_id from session instead

        # 🆕 ADDITIONAL CONTEXT: If we have order_id from history but need customer_id for order history
        if entities.get('order_id') and not entities.get('customer_id') and 'history' in query_lower:
            # For order history queries, we need the customer_id associated with the order_id
            # This will be handled in SQL generation or we can mark this as needing a lookup
            entities['needs_customer_lookup'] = True
            logger.info(f"🔍 Order history query detected - will lookup customer_id for order_id: {entities['order_id']}")

        # Classify query type based on keywords
        if any(keyword in query_lower for keyword in ['customer', 'customers', 'profile', 'account']):
            if any(keyword in query_lower for keyword in ['where', 'from', 'in', 'state', 'location']):
                return QueryType.GEOGRAPHIC_ANALYSIS, entities
            else:
                return QueryType.CUSTOMER_ANALYSIS, entities

        elif any(keyword in query_lower for keyword in ['order', 'orders', 'purchase', 'transaction', 'history', 'delivery', 'track', 'tracking', 'where is', 'status', 'shipped', 'shipping']):
            return QueryType.ORDER_ANALYTICS, entities

        elif any(keyword in query_lower for keyword in ['revenue', 'sales', 'money', 'naira', '₦', 'income']):
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

        # 🆕 ENHANCED QUERY CLASSIFICATION WITH SHOPPING CAPABILITIES
        # Check for shopping intent first (highest priority for e-commerce)
        if entities.get('shopping_intent') or any(keyword in query_lower for keyword in ['buy', 'purchase', 'place order', 'checkout', 'add to cart']):
            return QueryType.ORDER_PLACEMENT, entities

        # Check for recommendation requests
        elif entities.get('recommendation_intent') or any(keyword in query_lower for keyword in ['recommend', 'suggest', 'what should i buy', 'best product', 'popular', 'trending', 'help me choose']):
            return QueryType.PRODUCT_RECOMMENDATIONS, entities

        # Check for price inquiries
        elif entities.get('price_query') or entities.get('max_budget') or any(keyword in query_lower for keyword in ['how much', 'price of', 'cost of', 'budget']):
            return QueryType.PRICE_INQUIRY, entities

        # Check for stock/availability queries
        elif entities.get('inventory_query') or any(keyword in query_lower for keyword in ['in stock', 'available', 'out of stock', 'availability']):
            return QueryType.STOCK_CHECK, entities

        # Check for general shopping assistance
        elif any(keyword in query_lower for keyword in ['shopping', 'browse', 'catalog', 'categories', 'brands', 'what do you have', 'show me']):
            return QueryType.SHOPPING_ASSISTANCE, entities

        # Existing classification logic continues below...

    def generate_sql_query(self, user_query: str, query_type: QueryType, entities: Dict[str, Any]) -> str:
        """
        🔍 Generate Nigerian context-aware SQL queries using AI
        """

        # Get current Nigerian time context
        time_context = self.ni_intelligence.get_nigerian_timezone_context()

        # Get geographic context
        geo_context = self.ni_intelligence.get_geographic_context(user_query)

        # Database schema context
        schema_context = """
DATABASE SCHEMA FOR NIGERIAN E-COMMERCE PLATFORM:

Tables:
1. customers: customer_id, name, email, phone, state, lga, address, account_tier, preferences, created_at, updated_at
2. orders: order_id, customer_id, order_status, payment_method, total_amount, delivery_date, product_category, product_id, created_at, updated_at
3. analytics: analytics_id, metric_type, metric_value, time_period, created_at
4. products: product_id, product_name, category, brand, description, price, currency, in_stock, stock_quantity, weight_kg, dimensions_cm, created_at, updated_at

🔗 RELATIONSHIPS:
- orders.customer_id → customers.customer_id (Foreign Key)
- orders.product_id → products.product_id (Foreign Key)
- orders.product_category matches products.category

🏪 PRODUCT CATALOG:
Categories: Electronics, Fashion, Beauty, Computing, Automotive, Books
Popular Brands: Samsung, Apple, Tecno, Infinix, LG, Sony, Haier Thermocool, Scanfrost, Nike, Adidas, Zara, MAC Cosmetics, Maybelline, L'Oreal, HP, Dell, Canon, Logitech, Mobil 1, Exide, Dunlop, Bosch, Philips
Currency: All prices in Nigerian Naira (NGN)

Nigerian States: Lagos, Kano, Rivers, Oyo, Kaduna, Abia, Adamawa, Akwa Ibom, Anambra, Bauchi, Bayelsa, Benue, Borno, Cross River, Delta, Ebonyi, Edo, Ekiti, Enugu, Gombe, Imo, Jigawa, Kebbi, Kogi, Kwara, Nasarawa, Niger, Ondo, Osun, Ogun, Plateau, Sokoto, Taraba, Yobe, Zamfara, Abuja

Payment Methods: 'Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'
Order Status: 'Pending', 'Processing', 'Delivered', 'Returned'
Account Tiers: 'Bronze', 'Silver', 'Gold', 'Platinum'

PRODUCT CATEGORIES: Electronics, Fashion, Beauty, Computing, Automotive, Books
POPULAR BRANDS: Samsung, Apple, Tecno, Infinix, LG, Sony, Haier Thermocool, Scanfrost, Nike, Adidas, Zara, MAC Cosmetics, Maybelline, L'Oreal, HP, Dell, Canon, Logitech, Mobil 1, Exide, Dunlop, Bosch, Philips
"""

        system_prompt = f"""
You are a SQL expert for a Nigerian e-commerce platform. Generate ONLY the SQL query - no explanations, comments, or additional text.

{schema_context}

{time_context}

NIGERIAN BUSINESS CONTEXT:
- Currency: Nigerian Naira (₦)
- Geographic Focus: Nigerian states and LGAs
- Payment Methods: Optimized for Nigerian market
- Time Zone: West Africa Time (WAT, UTC+1)

🔒 CRITICAL PRIVACY PROTECTION RULES:
1. NEVER query the customers table for support contact information
2. If user asks for "customer support contact" or similar, return: SELECT 'PRIVACY_PROTECTED' as message;
3. Customer support queries should NOT access customer personal data
4. Support contact information is handled by application layer, not database

QUERY GENERATION RULES:
1. Always use proper PostgreSQL syntax
2. Include appropriate WHERE clauses for Nigerian context. If 'order_id' is present in EXTRACTED ENTITIES, prioritize filtering by `orders.order_id`.
3. If 'customer_id' is present in EXTRACTED ENTITIES (from conversation history), use it to filter customer-related queries.
4. For "order history" queries with customer_id: SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.customer_id = [customer_id]
5. If 'needs_customer_lookup' is true and order_id is available: First get customer_id from the order, then get all orders for that customer
6. Use date functions for time-based queries (e.g., CURRENT_DATE, DATE_TRUNC)
7. Format monetary values appropriately
8. Consider Nigerian geographic divisions (states, LGAs)
9. Handle partitioned tables correctly (orders table is partitioned by created_at). If querying by a specific 'order_id', a broad or no filter on `created_at` might be appropriate, as `order_id` should be unique.
10. Use proper JOINs when needed
11. Limit results appropriately (usually 10-50 rows unless a specific ID is queried)
12. Order results logically
13. Handle NULL values gracefully
14. NEVER use CURRENT_USER - use actual customer_id values from context when available
15. For delivery/tracking queries: Use order_status IN ('Processing', 'Delivered') and join with customer data

🚨 CRITICAL PRODUCT NAME SEARCH RULES:
16. **PRESERVE EXACT SPACING**: When searching for products, ALWAYS preserve exact spacing in product names
    - CORRECT: "Tecno Camon 20 Pro 5G" → '%Tecno Camon 20 Pro 5G%'
    - WRONG: "Tecno Camon 20 Pro 5G" → '%Tecno Camon20 Pro5G%' (DO NOT remove spaces!)
    - Use the exact product name as mentioned by the user, including all spaces and special characters
17. **PRODUCT QUERIES**: When users ask about products, prices, categories, brands, or inventory:
    - Use products table for product information queries
    - JOIN with orders table for purchase history and popularity analysis
    - Include product details like brand, price, description, stock status
    - For product searches: Use ILIKE for partial matches on product_name, brand, or category
    - ALWAYS preserve original spacing in ILIKE patterns: ILIKE '%exact product name with spaces%'
    - For price queries: Format prices in Naira and include currency symbol ₦
    - For inventory queries: Check stock_quantity and in_stock status
18. **MULTIPLE SEARCH PATTERNS**: For better product matching, use multiple ILIKE patterns:
    - Search product_name, brand, and description fields
    - Example: WHERE (p.product_name ILIKE '%Tecno Camon 20 Pro 5G%' OR p.brand ILIKE '%Tecno%' OR p.description ILIKE '%Camon 20%')

19. **PRODUCT-ORDER RELATIONSHIPS**: For queries involving both products and orders:
    - JOIN orders and products on product_id for detailed order information
    - Include customer information when showing order details with products
    - For popular products: COUNT orders by product_id and ORDER BY count DESC
20. **CATEGORY AND BRAND QUERIES**: When filtering by categories or brands:
    - Use exact matches for categories: Electronics, Fashion, Beauty, Computing, Automotive, Books
    - Use ILIKE for brand searches to handle case variations
    - Group by category for category-level analytics
21. **STOCK AND AVAILABILITY**: For inventory and stock queries:
    - Check both in_stock boolean and stock_quantity integer
    - Show stock status: 'Out of Stock', 'Low Stock' (<=10), 'Medium Stock' (<=50), 'High Stock' (>50)
    - Include stock_quantity in results for inventory management
22. **PRICE AND REVENUE QUERIES**: For pricing and financial analysis:
    - Use products.price for individual product pricing
    - Use orders.total_amount for actual transaction amounts
    - Calculate revenue by product: SUM(orders.total_amount) grouped by product_id
    - Format all monetary values with ₦ symbol

🔍 EXAMPLE PRODUCT SEARCH PATTERNS:
- User: "Tecno Camon 20 Pro 5G" → ILIKE '%Tecno Camon 20 Pro 5G%' (preserve all spaces!)
- User: "iPhone 14 Pro Max" → ILIKE '%iPhone 14 Pro Max%' (preserve all spaces!)
- User: "Samsung Galaxy S22" → ILIKE '%Samsung Galaxy S22%' (preserve all spaces!)

🆕 PRODUCT INFORMATION HANDLING:
- For product queries: Use database results to provide detailed product information with prices in ₦
- Include product names, brands, categories, prices, and stock status when available
- For inventory queries: Show stock levels and availability status with appropriate urgency
- For category browsing: List products by category with brief descriptions and prices
- For brand searches: Highlight brand-specific products with competitive pricing
- For price comparisons: Show products in price ranges (Budget ₦0-50K, Mid-range ₦50K-200K, Premium ₦200K+)
- Always mention Nigeria-wide delivery and multiple payment options
- Use product database results to make personalized recommendations
- If no specific products found: Guide to browse categories or suggest popular items

🆕 SHOPPING AND ORDER ASSISTANCE:
23. For ORDER_PLACEMENT queries: Get product details for ordering assistance
24. For PRODUCT_RECOMMENDATIONS queries: Use collaborative filtering and popularity data
25. For PRICE_INQUIRY queries: Focus on price comparisons and budget-friendly options
26. For STOCK_CHECK queries: Prioritize availability status and alternative suggestions
27. For SHOPPING_ASSISTANCE queries: Provide category browsing and general product information
28. Include customer tier discounts and delivery information when relevant
29. Format results to help customers make informed purchasing decisions
30. Always check stock availability before suggesting products
31. Include estimated delivery times and payment options in shopping assistance

IMPORTANT:
1. Output ONLY the SQL query - nothing else
2. No explanatory text, comments, or suggestions
3. Start with SELECT, INSERT, UPDATE, DELETE, WITH, CREATE, ALTER, or DROP
4. End with semicolon (;)
5. Use proper PostgreSQL syntax
6. Include appropriate WHERE clauses for Nigerian context
7. Use date functions for time-based queries
8. Format monetary values appropriately
9. Handle NULL values gracefully
10. Limit results appropriately (usually 10-50 rows)

USER QUERY: "{user_query}"
QUERY TYPE: {query_type.value}
EXTRACTED ENTITIES: {json.dumps(entities)}
GEOGRAPHIC CONTEXT: {json.dumps(geo_context)}

Generate ONLY the SQL query - no explanations or markdown formatting.
"""

        try:
            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate SQL query for: {user_query}"}
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
            # 🔧 FIX: Proper guest user handling
            customer_verified = entities.get('customer_verified', False)
            customer_id = entities.get('customer_id')

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
            elif entities.get('customer_id') and not customer_verified:
                customer_id = entities['customer_id']
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
                WHERE p.category = '{category}' AND p.in_stock = true
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
                WHERE p.category = '{category}'
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
                WHERE p.category = '{category}' AND p.in_stock = true AND p.stock_quantity > 0
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
        📝 Store conversation context in "notepad" format
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

        # Store in Redis or memory
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

            logger.info(f"📝 Context stored for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Context storage error: {e}")

    def get_conversation_history(self, user_id: str = "anonymous", limit: int = 5) -> List[Dict]:
        """Get recent conversation history for context"""

        try:
            if self.redis_client:
                history_key = f"conversation_history:{user_id}"
                recent_keys = self.redis_client.lrange(history_key, 0, limit-1)

                history = []
                for key in recent_keys:
                    entry_data = self.redis_client.get(key)
                    if entry_data:
                        history.append(json.loads(entry_data))

                return history
            else:
                # Memory fallback
                return self._memory_store.get(user_id, [])[-limit:]

        except Exception as e:
            logger.error(f"❌ History retrieval error: {e}")
            return []

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

    def generate_nigerian_response(self, query_context: QueryContext, conversation_history: List[Dict], session_context: Dict[str, Any] = None) -> str:
        """🇳🇬 Generate Nigerian-style empathetic response with intelligent recommendations"""
        try:
            customer_id = session_context.get('customer_id') if session_context else None

            # 🆕 DETECT USER SENTIMENT AND GET EMOTIONAL RESPONSE STYLE
            sentiment_data = self.detect_user_sentiment(query_context.user_query)
            empathetic_style = self.get_empathetic_response_style(sentiment_data, query_context)
            logger.info(f"🎭 Detected emotion: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})")

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
                'conversation_history': conversation_history[-3:],  # Last 3 exchanges
                'nigerian_time_context': NigerianBusinessIntelligence.get_nigerian_timezone_context(),
                'session_context': session_context or {},
                'recommendations': recommendations_data,
                'customer_mood': sentiment_data['emotion'],  # 🆕 Add detected emotion
                'sentiment_data': sentiment_data,  # 🆕 Add full sentiment data
                'empathetic_style': empathetic_style,  # 🆕 Add emotional response style
                'support_context': None
            }

            # Add support context if available
            if customer_id and recommendations_data and 'support_context' in recommendations_data:
                enhanced_context['support_context'] = recommendations_data['support_context']

            # Generate response with enhanced context
            system_prompt = self._build_enhanced_system_prompt(enhanced_context)

            # Generate AI response
            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
                    Based on the customer query: "{query_context.user_query}"

                    Query results: {safe_json_dumps(query_context.execution_result, max_items=3)}

                    Customer emotion detected: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})

                    {f"Intelligent recommendations available: {recommendations_data['total_recommendations']} products across {len(recommendations_data.get('recommendations', {}))} categories" if recommendations_data and recommendations_data.get('success') else ""}

                    Provide a helpful, empathetic Nigerian customer support response following the emotional style guidelines. Use appropriate emojis based on the detected emotion.
                    """}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            ai_response = response.choices[0].message.content.strip()

            # 🔧 Strip markdown formatting while keeping emojis
            ai_response = self._strip_markdown_formatting(ai_response)

            # 🆕 LOG AI RESPONSE IN TERMINAL (matching user query format)
            logger.info(f"🤖 AI: {ai_response}")

            # Enhance response with recommendation details if available
            if recommendations_data and recommendations_data.get('success') and recommendations_data.get('recommendations'):
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
        session_context = context.get('session_context', {})
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

                memory_guidance += f"""
                🧠 CONVERSATION MEMORY CONTEXT:
                - Previous user input: "{last_user_input[:100]}..."
                - Previous AI response: "{last_ai_response[:100]}..."
                - Recent conversation turns: {len(recent_turns)}
                - CRITICAL: Reference what was just discussed to maintain context!
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

        return f"""
        You are a caring customer support agent for raqibtech.com, Nigeria's leading e-commerce platform.

        PLATFORM IDENTITY:
        - Always mention "raqibtech.com" naturally in responses to build brand familiarity
        - Position raqibtech.com as a trusted Nigerian e-commerce destination
        - Highlight our nationwide delivery across all 36 states + FCT
        - Mention our multiple payment options including RaqibTechPay

        PERSONALITY:
        - Warm, understanding, and emotionally intelligent
        - Concise but caring - keep responses under 3 sentences when possible
        - Focus on the customer's feelings and immediate needs first
        - Nigerian cultural awareness with authentic warmth
        - Never use markdown formatting (no **, ##, etc.) - use plain text only
        - ALWAYS include appropriate emojis based on customer emotion

        {emotion_guidance}

        {mood_guidance}

        {recommendations_guidance}

        {memory_guidance}

        RESPONSE STYLE:
        1. 💙 Lead with genuine empathy - acknowledge their feelings with appropriate emojis
        2. 🎯 Address their specific need directly and concisely
        3. 🛍️ If relevant, mention 1-2 helpful products naturally
        4. 💰 Use ₦ format for prices
        5. 🤝 End with supportive next step mentioning raqibtech.com

        EMOJI USAGE RULES:
        - Use emojis that match the customer's detected emotion
        - For frustrated customers: 😔, 💙, 🤗, ✨
        - For worried customers: 🤗, 💙, ✨, 🌟
        - For confused customers: 😊, 💡, 🎯, ✨
        - For happy customers: 😊, 🎉, ✨, 🌟, 💚
        - For impatient customers: ⚡, 🚀, 💨, ⏰
        - Maximum 3-4 emojis per response

        CONVERSATION FLOW RULES:
        - ALWAYS reference what was just discussed in previous turns
        - If user just added product to cart, help with checkout process
        - If user provided delivery/payment info, continue that flow
        - Maintain conversation continuity at all costs
        - Never forget what was just mentioned in the immediate previous interaction

        FORMATTING RULES:
        - Use plain text only - NO markdown formatting
        - NO bold (**text**), NO headers (###), NO code blocks
        - Keep emojis for warmth but no markdown styling
        - Simple sentences with natural flow

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
        🔧 Strip markdown formatting from AI responses while keeping emojis
        Based on OpenAI community recommendations for plain text output
        """
        try:
            import re

            # Remove markdown bold (**text** or __text__)
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'__(.*?)__', r'\1', text)

            # Remove markdown italic (*text* or _text_)
            text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
            text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'\1', text)

            # Remove headers (### Header)
            text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)

            # Remove code blocks (```code```)
            text = re.sub(r'```[\s\S]*?```', '', text)

            # Remove inline code (`code`)
            text = re.sub(r'`([^`]+)`', r'\1', text)

            # Remove markdown links [text](url)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

            # Remove blockquotes (> text)
            text = re.sub(r'^>\s+(.+)$', r'\1', text, flags=re.MULTILINE)

            # Remove unordered list markers (- item, * item)
            text = re.sub(r'^[-*+]\s+(.+)$', r'• \1', text, flags=re.MULTILINE)

            # Remove ordered list markers (1. item)
            text = re.sub(r'^\d+\.\s+(.+)$', r'• \1', text, flags=re.MULTILINE)

            # Clean up extra whitespace but preserve line breaks
            text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
            text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space

            return text.strip()

        except Exception as e:
            logger.warning(f"⚠️ Error stripping markdown formatting: {e}")
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

            if self.order_ai_assistant and session_context and session_context.get('user_authenticated'):
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

                            if shopping_result.get('success'):
                                enhanced_response_text = self._generate_shopping_response(shopping_result)

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
                return {
                    'success': False,
                    'response': f"I encountered an issue processing your request: {error_message}. Please try rephrasing your question or contact our support team!",
                    'query_type': 'error',
                    'execution_time': f"{time.time() - start_time:.3f}s",
                    'error': error_message
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

                    # Check if the specific order exists (either by formatted ID or database ID)
                    if order_id.startswith('RQB'):
                        # This is a formatted order ID, extract the numeric part
                        numeric_part = order_id.replace('RQB', '').replace(datetime.now().strftime('%Y%m%d'), '')
                        try:
                            db_order_id = int(numeric_part)
                            cursor.execute("SELECT * FROM orders WHERE order_id = %s", (db_order_id,))
                        except:
                            cursor.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC LIMIT 1", (customer_id,))
                    else:
                        cursor.execute("SELECT * FROM orders WHERE customer_id = %s ORDER BY created_at DESC LIMIT 1", (customer_id,))

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

