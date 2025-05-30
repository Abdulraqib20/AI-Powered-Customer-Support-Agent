"""
  Enhanced Database Querying System for Nigerian E-commerce Customer Support Agent
===================================================================================

Multi-Stage Pipeline Architecture:
1. Intent Classification & Query Processing
2. Nigerian Context-Aware SQL Generation
3. Database Execution with Comprehensive Error Handling
4. Context Storage & Memory Management
5. Natural Language Response Generation

Features:
- Nigerian states, LGAs, and business context awareness
- Naira currency formatting and Nigerian payment methods
- Robust fallback mechanisms and error recovery
- Conversation memory with structured "notepad" format
- Time-aware query generation with Nigerian timezone
- Professional business intelligence responses

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

class EnhancedDatabaseQuerying:
    """
    🚀 Enhanced Database Querying System for Nigerian E-commerce
    Multi-stage pipeline with Nigerian business intelligence
    """

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

        # Initialize Redis for conversation memory
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using memory fallback: {e}")
            self.redis_client = None
            self._memory_store = {}

        # Nigerian business intelligence helper
        self.ni_intelligence = NigerianBusinessIntelligence()

    def classify_query_intent(self, user_query: str, conversation_history: List[Dict] = None) -> Tuple[QueryType, Dict[str, Any]]:
        """
        🎯 Classify user query intent using Nigerian business context
        Enhanced with conversation history for context inheritance
        """
        query_lower = user_query.lower()
        entities = {
            'states': [],
            'payment_methods': [],
            'time_period': None,
            'amount_range': None,
            'product_categories': [],
            'order_id': None,
            'customer_id': None,  # Added customer_id for context inheritance
            'brands': [],
            'product_keywords': [],
            'price_query': False,
            'inventory_query': False
        }

        # Extract Nigerian states
        for state in NIGERIAN_STATES:
            if state.lower() in query_lower:
                entities['states'].append(state)

        # Extract payment methods
        for payment in NIGERIAN_PAYMENT_METHODS:
            if payment.lower() in query_lower:
                entities['payment_methods'].append(payment)

        # 🆕 Extract product categories
        for category in NIGERIAN_PRODUCT_CATEGORIES:
            if category.lower() in query_lower:
                entities['product_categories'].append(category)

        # 🆕 Extract brands
        for brand in NIGERIAN_POPULAR_BRANDS:
            if brand.lower() in query_lower:
                entities['brands'] = entities.get('brands', [])
                entities['brands'].append(brand)

        # 🆕 Extract product-related terms
        product_keywords = ['product', 'item', 'goods', 'phone', 'laptop', 'dress', 'shoe', 'book', 'car', 'electronics']
        for keyword in product_keywords:
            if keyword in query_lower:
                entities['product_keywords'] = entities.get('product_keywords', [])
                entities.get('product_keywords').append(keyword)

        # 🆕 Extract price-related terms
        if any(term in query_lower for term in ['price', 'cost', 'naira', '₦', 'cheap', 'expensive', 'budget']):
            entities['price_query'] = True

        # 🆕 Extract stock/inventory terms
        if any(term in query_lower for term in ['stock', 'available', 'inventory', 'out of stock', 'in stock']):
            entities['inventory_query'] = True

        # Extract time periods
        time_indicators = {
            'today': 'today',
            'yesterday': 'yesterday',
            'this week': 'week',
            'this month': 'month',
            'this year': 'year',
            'last week': 'last_week',
            'last month': 'last_month',
            'last year': 'last_year'
        }

        for indicator, period in time_indicators.items():
            if indicator in query_lower:
                entities['time_period'] = period
                break

        # Extract order_id if present (simple regex for "order id is XXXXX" or "order #XXXXX")
        order_id_match = re.search(r'(?:order id is|order #|order number|order no\.|order id)\s*([0-9]+)', query_lower)
        if order_id_match:
            entities['order_id'] = order_id_match.group(1)
            logger.info(f"Extracted order_id: {entities['order_id']}")

        # 🔧 CRITICAL FIX: NEVER inherit conversation history for authenticated users
        # Only inherit context for guest users when no specific entities are found
        if conversation_history and not entities['order_id']:
            # 🔧 FIX: Only inherit if this is truly a guest user (no customer_id in session)
            # This should be controlled by the calling function, but double-check here

            # Look for order_id or customer_id from recent conversation (ONLY for guests)
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

        elif any(keyword in query_lower for keyword in ['car', 'auto', 'battery', 'tire', 'engine']):
            entities['product_categories'].append('Automotive')
            return QueryType.PRODUCT_PERFORMANCE, entities

        else:
            return QueryType.GENERAL_CONVERSATION, entities

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
You are a SQL expert for a Nigerian e-commerce platform. Generate PRECISE PostgreSQL queries based on user requests.

{schema_context}

{time_context}

NIGERIAN BUSINESS CONTEXT:
- Currency: Nigerian Naira (₦)
- Geographic Focus: Nigerian states and LGAs
- Payment Methods: Optimized for Nigerian market
- Time Zone: West Africa Time (WAT, UTC+1)

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
16. 🆕 PRODUCT QUERIES: When users ask about products, prices, categories, brands, or inventory:
    - Use products table for product information queries
    - JOIN with orders table for purchase history and popularity analysis
    - Include product details like brand, price, description, stock status
    - For product searches: Use ILIKE for partial matches on product_name, brand, or category
    - For price queries: Format prices in Naira and include currency symbol ₦
    - For inventory queries: Check stock_quantity and in_stock status
17. 🆕 PRODUCT-ORDER RELATIONSHIPS: For queries involving both products and orders:
    - JOIN orders and products on product_id for detailed order information
    - Include customer information when showing order details with products
    - For popular products: COUNT orders by product_id and ORDER BY count DESC
18. 🆕 CATEGORY AND BRAND QUERIES: When filtering by categories or brands:
    - Use exact matches for categories: Electronics, Fashion, Beauty, Computing, Automotive, Books
    - Use ILIKE for brand searches to handle case variations
    - Group by category for category-level analytics
19. 🆕 STOCK AND AVAILABILITY: For inventory and stock queries:
    - Check both in_stock boolean and stock_quantity integer
    - Show stock status: 'Out of Stock', 'Low Stock' (<=10), 'Medium Stock' (<=50), 'High Stock' (>50)
    - Include stock_quantity in results for inventory management
20. 🆕 PRICE AND REVENUE QUERIES: For pricing and financial analysis:
    - Use products.price for individual product pricing
    - Use orders.total_amount for actual transaction amounts
    - Calculate revenue by product: SUM(orders.total_amount) grouped by product_id
    - Format all monetary values with ₦ symbol

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

USER QUERY: "{user_query}"
QUERY TYPE: {query_type.value}
EXTRACTED ENTITIES: {json.dumps(entities)}
GEOGRAPHIC CONTEXT: {json.dumps(geo_context)}

Generate ONLY the SQL query, no explanations or markdown formatting.
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

            # Clean up the SQL query
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()

            logger.info(f"🔍 Generated SQL: {sql_query}")
            return sql_query

        except Exception as e:
            logger.error(f"❌ SQL generation error: {e}")
            return self._get_fallback_query(query_type, entities)

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
        """
          Generate Nigerian business-aware natural language response with enhanced emotional intelligence
        """

        # 🎭 STEP 1: Analyze user sentiment and emotional state
        sentiment_data = self.detect_user_sentiment(query_context.user_query)
        empathetic_style = self.get_empathetic_response_style(sentiment_data, query_context)

        logger.info(f"🎭 Detected emotion: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})")

        # Continue with normal processing - scope already checked in process_enhanced_query
        # Prepare execution results summary
        results_summary = ""
        if query_context.execution_result:
            results_count = len(query_context.execution_result)
            results_summary = f"Found {results_count} records. "

            # DEBUG: Log the actual database result being passed to AI
            logger.info(f"🔍 DEBUG: Database result passed to AI: {safe_json_dumps(query_context.execution_result, max_items=3)}")

            # Format monetary values in Naira
            for result in query_context.execution_result[:3]:  # Show first 3 results
                for key, value in result.items():
                    if key in ['total_amount', 'revenue', 'total_revenue'] and isinstance(value, (int, float)):
                        result[f'{key}_formatted'] = self.ni_intelligence.format_naira(value)

        # Get Nigerian time context
        time_context = self.ni_intelligence.get_nigerian_timezone_context()

        # Prepare conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = f"Recent conversation history: {safe_json_dumps(conversation_history[-2:])}"

        # Extract authentication status from session_context
        customer_verified = session_context.get('customer_verified', False) if session_context else False
        customer_id = session_context.get('customer_id', 'None') if session_context else 'None'
        customer_name = session_context.get('customer_name', 'valued customer') if session_context else 'valued customer'

        # 🔧 GUEST USER HANDLING: Provide different context for guest vs authenticated users
        if not customer_verified and query_context.query_type == QueryType.ORDER_ANALYTICS:
            # For guest users asking about orders, provide platform information instead
            response_prompt = f"""
You are a helpful customer support guide for raqibtech.com. You're speaking with a guest user who isn't logged in.

🎭 EMOTIONAL INTELLIGENCE CONTEXT:
User's Current Emotion: {sentiment_data['emotion']} (Intensity: {sentiment_data['intensity']})
Empathy Required: {sentiment_data['empathy_needed']}
Emotional Keywords Detected: {sentiment_data['keywords']}

{empathetic_style}

PLATFORM: raqibtech.com (Nigerian e-commerce platform)
GUEST USER CONTEXT: This user is not authenticated and cannot access personal order data.

CUSTOMER'S QUESTION: "{query_context.user_query}"

STRICT SCOPE RESTRICTIONS:
- ONLY respond to raqibtech.com customer support related questions
- DO NOT provide general knowledge, news, politics, or unrelated information
- If asked about non-platform topics, redirect to raqibtech.com services
- Focus exclusively on e-commerce, orders, payments, account, and platform help

🌟 GUEST USER RESPONSE GUIDELINES:
1. 🎭 Respond according to their emotional state with appropriate emojis
2. 🔒 Explain that personal order tracking requires logging in or providing order ID
3. 🛍️ Instead, provide helpful information about raqibtech.com's services:
   - Nigeria-wide delivery (all 36 states + FCT)
   - Payment options: Pay on Delivery, Bank Transfer, Card, RaqibTechPay
   - Account tiers: Bronze, Silver, Gold, Platinum with increasing benefits
   - 24/7 customer support availability
4. 💡 Guide them on how to:
   - Create an account for personalized service
   - Track orders with order ID (if they have one)
   - Contact support for immediate help
5. 😊 Be warm, helpful, and encouraging about signing up
6. 🎯 Focus on platform capabilities rather than personal data
7. ✨ End with encouragement to join the platform for better service

🆕 PRODUCT CATALOG GUIDANCE:
8. 🏪 For product questions, showcase our amazing catalog:
   - Electronics: Samsung, Apple, Tecno, Infinix phones, laptops, TVs
   - Fashion: Ankara dresses, traditional wear, Nike, Adidas
   - Beauty: Nigerian shea butter, MAC cosmetics, skincare
   - Computing: HP, Dell laptops, monitors, accessories
   - Automotive: Car parts, batteries, tires, accessories
   - Books: Nigerian literature, textbooks, children's books
9. 💰 Mention competitive prices in Nigerian Naira (₦)
10. 📦 Highlight our extensive inventory and fast delivery
11. 🎁 Encourage browsing our product categories

Keep responses under 100 words but pack them with helpful information and appropriate emotion.

Respond as a caring, helpful customer support guide:
"""
        else:
            # Standard response prompt for authenticated users or general queries
            response_prompt = f"""
You are a caring, empathetic customer support agent for raqibtech.com. You are having a real-time conversation with a {customer_name}.

🎭 EMOTIONAL INTELLIGENCE CONTEXT:
User's Current Emotion: {sentiment_data['emotion']} (Intensity: {sentiment_data['intensity']})
Empathy Required: {sentiment_data['empathy_needed']}
Emotional Keywords Detected: {sentiment_data['keywords']}

{empathetic_style}

PLATFORM: raqibtech.com (Nigerian e-commerce platform)
CONVERSATION TYPE: Live customer support chat

STRICT SCOPE RESTRICTIONS:
- ONLY respond to raqibtech.com customer support related questions
- DO NOT provide general knowledge, news, politics, entertainment, or unrelated information
- If asked about non-platform topics, politely redirect to raqibtech.com services
- Focus exclusively on e-commerce, orders, payments, account, platform help, and Nigerian business context
- Never answer questions about presidents, celebrities, general facts, homework, etc.

CUSTOMER AUTHENTICATION STATUS:
- Authenticated: {customer_verified}
- Customer ID: {customer_id}
- Customer Name: {customer_name}

CONVERSATION HISTORY: {safe_json_dumps(conversation_history[-3:]) if conversation_history else "This is the start of the conversation"}

CUSTOMER'S CURRENT MESSAGE: "{query_context.user_query}"
AVAILABLE DATABASE INFO: {safe_json_dumps(query_context.execution_result, max_items=3) if query_context.execution_result else "No data found"}

🌟 ENHANCED EMOTIONAL RESPONSE GUIDELINES:
1. 🎭 ALWAYS respond according to the detected emotional state using appropriate emojis and tone
2. 💝 If empathy is needed, start with emotional acknowledgment before providing information
3. 😊 Use emojis throughout the response to match the customer's emotional state and brighten their day
4. 🤗 Be a reliable support friend - warm, caring, and genuinely helpful
5. 🌟 End responses with encouraging, positive energy and offer continued support
6. 💙 If customer shows frustration, apologize sincerely and focus on immediate solutions
7. 🎉 If customer is happy, share their joy and maintain the positive energy
8. 💡 If customer is confused, be extra patient and break things down clearly with helpful emojis
9. ⚡ If customer is impatient, acknowledge urgency and provide quick, actionable solutions
10.   Maintain Nigerian business context while being emotionally intelligent

CRITICAL: Do not give me any information about topics not related to raqibtech.com customer support. Do not justify your answers about non-platform topics. If the question is not about raqibtech.com services, politely redirect to platform-related assistance.

TECHNICAL RESPONSE LOGIC:
- If customer is NOT authenticated and asking about orders: Guide them warmly to log in or provide order ID
- If customer IS authenticated and database has their order data: Use that data to help them enthusiastically
- If database shows "Guest user - authentication required": Ask customer to log in with friendly guidance
- If customer is asking about orders but you only have guest fallback data: Ask for authentication with understanding
- Use database information directly to answer customer questions ONLY if it's legitimate customer data
- If database shows order_status for a legitimate order: provide that exact status with appropriate emotional response
- If customer provided order ID and you found real database results: use that information with matching emotion
- Don't show random orders to guests - guide them to proper authentication with empathy
- Keep responses under 100 words but pack them with emotion and helpfulness
- Format currency as ₦ for Nigerian Naira

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

EMOJI USAGE BY EMOTION:
- Frustrated: 😔, 💙, 🤗, ✨ (calming, supportive)
- Worried: 🤗, 💙, ✨, 🌟 (comforting, reassuring)
- Confused: 😊, 💡, 🎯, ✨ (helpful, clarifying)
- Happy: 😊, 🎉, ✨, 🌟, 💚 (joyful, celebratory)
- Impatient: ⚡, 🚀, 💨, ⏰ (urgent, action-oriented)
- Neutral: 😊, ✨, 💙, 🌟 (warm, friendly)

ORDER STATUS MEANINGS WITH EMOTIONAL CONTEXT:
- "Pending": Order received and being prepared (use reassuring tone with ⏳, ✨)
- "Processing": Order is being processed and prepared for delivery (use excited tone with 🚀, 📦)
- "Delivered": Order has been delivered to customer (use celebratory tone with 🎉, ✅)
- "Returned": Order was returned (use understanding tone with 🤗, 💙)

Respond as a caring, emotionally intelligent customer support friend (no quotes, no signatures):
"""

        try:
            response = self.groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",  # Keep for complex emotional understanding
                messages=[
                    {"role": "system", "content": response_prompt},
                    {"role": "user", "content": f"Generate emotionally intelligent response for: {query_context.user_query}"}
                ],
                temperature=0.7,  # Increased for more creative emotional responses
                max_tokens=500    # Increased for more detailed emotional responses
            )

            ai_response = response.choices[0].message.content.strip()
            logger.info(f"  Generated emotionally intelligent Nigerian response with {sentiment_data['emotion']} tone")
            return ai_response

        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            return self._get_fallback_emotional_response(query_context, sentiment_data)

    def _get_fallback_emotional_response(self, query_context: QueryContext, sentiment_data: Dict[str, Any]) -> str:
        """Generate fallback emotional response for error scenarios"""

        emotion = sentiment_data['emotion']

        if query_context.error_message:
            if emotion == 'frustrated':
                return """I'm so sorry for the technical issue! 😔 I completely understand your frustration and I'm working to fix this right away.

Please try your question again, or contact our support team at +234 (702) 5965-922 for immediate help. I'm here to make this right! 💙✨"""

            elif emotion == 'worried':
                return """I understand you're concerned, and I want to reassure you everything is okay! 🤗 We're just having a small technical moment.

Please don't worry - try your question again or reach out to our team directly. We're here to help you! 🌟💙"""

            else:
                return """I apologize for the technical hiccup! 😊 No worries though - these things happen.

Please try asking your question again, or contact our support team at +234 (702) 5965-922. I'm here to help! ✨"""

        elif query_context.execution_result:
            results_count = len(query_context.execution_result)

            if emotion == 'happy':
                return f"""Great news! 🎉 I found some helpful information for you! To give you the most accurate details for your raqibtech.com account,

could you share your order number or email address? I'm excited to help you get exactly what you need! ✨🌟"""

            elif emotion == 'impatient':
                return f"""I found information quickly for you! ⚡ To get you the right details fast, please share your order number or email address.

This will help me give you instant, accurate information about your raqibtech.com account! 🚀"""

            else:
                return f"""I found some helpful information! 😊 To make sure I give you the right details for your raqibtech.com account,

could you please share your order number or email address with me? I'm here to help! ✨💙"""

        else:
            if emotion == 'confused':
                return """No worries at all! 😊 I'm here to help clarify anything you need about raqibtech.com. 💡

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
                return """I'm truly sorry for any frustration! 😔 Let me help make this better right away. 💙

I can assist with:
• 📦 Order tracking and delivery updates
• 💳 Payment methods and account questions
• 🛍️ Product recommendations and shopping
• 👤 Account management and support
• 🏪 Our extensive product catalog with competitive ₦ prices

How can I assist you with raqibtech.com today? 🌟✨"""

            else:
                return """Thanks for your question! I'm your dedicated raqibtech.com customer support assistant, so I focus on helping with our platform and services. 😊

I'd love to assist you with:
• 📦 Order tracking and delivery status
• 💳 Payment and account questions
• 🛍️ Shopping and product recommendations
• 👤 Account management and support
• 🏪 Our amazing product catalog:
  - Electronics, Fashion, Beauty, Computing, Automotive, Books
  - Nigerian brands and international favorites
  - Competitive prices in Naira (₦)
  - Fast delivery across all 36 states + FCT

How can I help you with your raqibtech.com experience today? 🌟"""

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
            return """I understand you might be looking for information, but I'm specifically designed to help with raqibtech.com customer support! 😊

I'd love to assist you with:
• 📦 Order tracking and delivery status
• 💳 Payment and account questions
• 🛍️ Shopping and product recommendations
• 👤 Account management and support

How can I help you with your raqibtech.com experience today? 🌟"""

        elif emotion == 'confused':
            return """I'm here to help, but I'm specifically designed to assist with raqibtech.com customer support! 💡

I can help you with:
• 📦 Tracking your orders and deliveries
• 💳 Payment assistance and account issues
• 🛍️ Product information and shopping help
• 👤 Account settings and tier benefits

What can I help you with regarding your raqibtech.com experience? 😊✨"""

        else:
            return """Thanks for your question! I'm your dedicated raqibtech.com customer support assistant, so I focus on helping with our platform and services. 😊

I'd love to assist you with:
• 📦 Order tracking and delivery status
• 💳 Payment and account questions
• 🛍️ Shopping and product recommendations
• 👤 Account management and support

How can I help you with your raqibtech.com experience today? 🌟"""

    def process_enhanced_query(self, user_query: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🚀 Main pipeline method that orchestrates the entire enhanced query process
        Returns a comprehensive result dictionary for the Flask API
        """
        start_time = time.time()

        try:
            # 🎯 STEP 1: Check if query is within customer support scope FIRST
            if not self.is_query_within_scope(user_query):
                logger.info(f"🚫 Out-of-scope query detected: {user_query[:50]}...")
                sentiment_data = self.detect_user_sentiment(user_query)
                return {
                    'success': True,
                    'response': self.generate_out_of_scope_response(user_query, sentiment_data),
                    'query_type': 'out_of_scope',
                    'execution_time': f"{time.time() - start_time:.3f}s",
                    'sql_query': None,
                    'results_count': 0
                }

            # Step 2: Get conversation history for context
            user_id = session_context.get('user_id', 'anonymous') if session_context else 'anonymous'
            conversation_history = self.get_conversation_history(user_id, limit=5)

            # Step 3: Classify query intent and extract entities
            query_type, entities = self.classify_query_intent(user_query, conversation_history)

            # 🔧 CRITICAL FIX: Override entities with authenticated session data
            if session_context and session_context.get('customer_verified', False):
                # For authenticated users, ALWAYS use session customer_id, never conversation history
                authenticated_customer_id = session_context.get('customer_id')
                if authenticated_customer_id:
                    entities['customer_id'] = str(authenticated_customer_id)
                    entities['customer_verified'] = True
                    logger.info(f"🔐 Using authenticated customer_id: {authenticated_customer_id} (overriding any conversation history)")
                else:
                    logger.warning(f"⚠️ Authenticated user but no customer_id in session: {session_context}")
            else:
                # For guest users, mark as not verified
                entities['customer_verified'] = False
                logger.info(f"👤 Guest user - no authenticated customer_id")

            # Step 4: Generate SQL query based on classification
            sql_query = self.generate_sql_query(user_query, query_type, entities)

            # Step 5: Execute the database query
            success, execution_result, error_message = self.execute_sql_query(sql_query)

            if not success:
                # Query failed - try fallback
                fallback_sql = self._get_fallback_query(query_type, entities)
                app_logger.info(f"🔄 Trying fallback query: {fallback_sql}")
                success, execution_result, error_message = self.execute_sql_query(fallback_sql)

                if not success:
                    # Both original and fallback failed
                    execution_result = []
                    app_logger.error(f"❌ Both original and fallback queries failed: {error_message}")

            # Step 6: Create query context
            query_context = QueryContext(
                query_type=query_type,
                intent=entities.get('intent', 'general_inquiry'),
                entities=entities,
                sql_query=sql_query,
                execution_result=execution_result or [],
                response="",
                timestamp=datetime.now(),
                user_query=user_query,
                error_message=error_message
            )

            # Step 7: Generate natural language response
            response = self.generate_nigerian_response(query_context, conversation_history, session_context)
            query_context.response = response

            # Step 8: Store conversation context for future reference
            self.store_conversation_context(query_context, user_id)

            execution_time = time.time() - start_time

            # Step 9: Return comprehensive result
            return {
                'success': True,
                'response': response,
                'query_type': query_type.value,
                'sql_query': sql_query,
                'results_count': len(execution_result) if execution_result else 0,
                'execution_time': f"{execution_time:.3f}s",
                'entities': entities,
                'user_query': user_query
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
