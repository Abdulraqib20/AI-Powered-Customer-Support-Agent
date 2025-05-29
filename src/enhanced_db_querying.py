"""
🇳🇬 Enhanced Database Querying System for Nigerian E-commerce Customer Support Agent
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
            'customer_id': None  # Added customer_id for context inheritance
        }

        # Extract Nigerian states
        for state in NIGERIAN_STATES:
            if state.lower() in query_lower:
                entities['states'].append(state)

        # Extract payment methods
        for payment in NIGERIAN_PAYMENT_METHODS:
            if payment.lower() in query_lower:
                entities['payment_methods'].append(payment)

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

        # 🆕 CONTEXT INHERITANCE: If no explicit entities found, check conversation history
        # Only inherit context for non-authenticated users or when no specific entities are found
        if conversation_history and not entities['order_id']:
            # Look for order_id or customer_id from recent conversation
            for conversation in conversation_history[:3]:  # Check last 3 conversations
                if 'entities' in conversation:
                    conv_entities = conversation['entities']

                    # Inherit order_id if available
                    if conv_entities.get('order_id') and not entities['order_id']:
                        entities['order_id'] = conv_entities['order_id']
                        logger.info(f"🔄 Inherited order_id from conversation history: {entities['order_id']}")

                    # 🔧 FIX: Only inherit customer_id if the user is NOT authenticated
                    # This prevents authenticated users from getting overridden by conversation history
                    if not entities.get('customer_id') and not entities.get('customer_verified'):
                        # Try to extract customer_id from execution results if order was queried
                        if conversation.get('execution_result'):
                            for result in conversation['execution_result']:
                                if 'customer_id' in result and not entities['customer_id']:
                                    entities['customer_id'] = str(result['customer_id'])
                                    logger.info(f"🔄 Inherited customer_id from conversation history: {entities['customer_id']}")
                                    break

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

        elif any(keyword in query_lower for keyword in ['product', 'category', 'item', 'goods']):
            return QueryType.PRODUCT_PERFORMANCE, entities

        elif any(keyword in query_lower for keyword in ['time', 'date', 'period', 'trend', 'monthly', 'weekly']):
            return QueryType.TEMPORAL_ANALYSIS, entities

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
2. orders: order_id, customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at, updated_at
3. analytics: analytics_id, metric_type, metric_value, time_period, created_at

Nigerian States: Lagos, Kano, Rivers, Oyo, Kaduna, Abia, Adamawa, Akwa Ibom, Anambra, Bauchi, Bayelsa, Benue, Borno, Cross River, Delta, Ebonyi, Edo, Ekiti, Enugu, Gombe, Imo, Jigawa, Kebbi, Kogi, Kwara, Nasarawa, Niger, Ondo, Osun, Ogun, Plateau, Sokoto, Taraba, Yobe, Zamfara, Abuja

Payment Methods: 'Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'
Order Status: 'Pending', 'Processing', 'Delivered', 'Returned'
Account Tiers: 'Bronze', 'Silver', 'Gold', 'Platinum'
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

USER QUERY: "{user_query}"
QUERY TYPE: {query_type.value}
EXTRACTED ENTITIES: {json.dumps(entities)}
GEOGRAPHIC CONTEXT: {json.dumps(geo_context)}

Generate ONLY the SQL query, no explanations or markdown formatting.
"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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

        else:
            return "SELECT 'Fallback query executed' as message;"

    def execute_database_query(self, sql_query: str) -> Tuple[List[Dict], Optional[str]]:
        """
        🗄️ Execute SQL query with comprehensive error handling
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            logger.info(f"🔍 Executing query: {sql_query}")
            cursor.execute(sql_query)

            # Handle different query types
            if sql_query.strip().lower().startswith(('select', 'with')):
                results = [dict(row) for row in cursor.fetchall()]
            else:
                # For INSERT/UPDATE/DELETE
                conn.commit()
                results = [{"affected_rows": cursor.rowcount, "status": "success"}]

            cursor.close()
            conn.close()

            logger.info(f"✅ Query executed successfully, {len(results)} rows returned")
            return results, None

        except psycopg2.Error as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(f"❌ {error_msg}")

            # Try simplified fallback query
            if "relation" in str(e) or "column" in str(e):
                fallback_results = [{"error": "Table or column not found", "suggestion": "Please check your query"}]
                return fallback_results, error_msg

            return [], error_msg

        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return [], error_msg

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
        🇳🇬 Generate Nigerian business-aware natural language response with enhanced emotional intelligence
        """

        # 🎭 STEP 1: Analyze user sentiment and emotional state
        sentiment_data = self.detect_user_sentiment(query_context.user_query)
        empathetic_style = self.get_empathetic_response_style(sentiment_data, query_context)

        logger.info(f"🎭 Detected emotion: {sentiment_data['emotion']} (intensity: {sentiment_data['intensity']})")

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
10. 🇳🇬 Maintain Nigerian business context while being emotionally intelligent

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
                model="llama-3.3-70b-versatile",  # Keep for complex emotional understanding
                messages=[
                    {"role": "system", "content": response_prompt},
                    {"role": "user", "content": f"Generate emotionally intelligent response for: {query_context.user_query}"}
                ],
                temperature=0.7,  # Increased for more creative emotional responses
                max_tokens=500    # Increased for more detailed emotional responses
            )

            ai_response = response.choices[0].message.content.strip()
            logger.info(f"🇳🇬 Generated emotionally intelligent Nigerian response with {sentiment_data['emotion']} tone")
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
• Order tracking and delivery status 📦
• Account questions 👤
• Payment assistance 💳
• Product information 🛍️

What would you like to know? I'm happy to guide you step by step! ✨"""

            elif emotion == 'frustrated':
                return """I'm truly sorry for any frustration! 😔 Let me help make this better right away. 💙

I can assist with:
• Order tracking and delivery updates 📦⚡
• Payment and account issues 💳🔧
• Quick product help 🛍️💨
• Immediate support 🤗

What do you need help with? I'm here to fix this for you! ✨"""

            else:
                return """I'd love to help you! 😊 I'm your friendly raqibtech.com support assistant. 🌟

I can help with:
• Order tracking and delivery status 📦
• Account and payment questions 💳
• Product recommendations 🛍️
• General shopping support 🤗

What can I assist you with today? ✨"""

    def process_query(self, user_query: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        🚀 Main pipeline: Process user query through complete Nigerian e-commerce pipeline
        """

        start_time = datetime.now()

        try:
            # Stage 0: Get Conversation History (moved earlier for context inheritance)
            logger.info(f"📚 Stage 0: Retrieving conversation history for context")
            conversation_history = self.get_conversation_history(user_id)

            # Stage 1: Intent Classification (now with conversation history)
            logger.info(f"🎯 Stage 1: Classifying query intent")
            query_type, entities = self.classify_query_intent(user_query, conversation_history)

            # Stage 2: SQL Generation
            logger.info(f"🔍 Stage 2: Generating SQL query")
            sql_query = self.generate_sql_query(user_query, query_type, entities)

            # Stage 3: Database Execution
            logger.info(f"🗄️ Stage 3: Executing database query")
            execution_result, error_message = self.execute_database_query(sql_query)

            # Create query context
            query_context = QueryContext(
                query_type=query_type,
                intent=query_type.value,
                entities=entities,
                sql_query=sql_query,
                execution_result=execution_result,
                response="",  # Will be filled next
                timestamp=start_time,
                user_query=user_query,
                error_message=error_message
            )

            # Stage 4: Generate Nigerian Response
            logger.info(f"🇳🇬 Stage 4: Generating Nigerian business response")
            query_context.response = self.generate_nigerian_response(query_context, conversation_history, None)

            # Stage 5: Store Context
            logger.info(f"📝 Stage 5: Storing conversation context")
            self.store_conversation_context(query_context, user_id)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Return comprehensive response
            return {
                'success': True,
                'response': query_context.response,
                'query_type': query_type.value,
                'sql_query': sql_query,
                'results_count': len(execution_result),
                'execution_time': f"{processing_time:.2f}s",
                'entities': entities,
                'timestamp': start_time.isoformat(),
                'error_message': error_message,
                'has_results': len(execution_result) > 0
            }

        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}")
            return {
                'success': False,
                'response': f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or rephrase your question.",
                'error_message': str(e),
                'timestamp': start_time.isoformat(),
                'execution_time': f"{(datetime.now() - start_time).total_seconds():.2f}s"
            }

    def process_enhanced_query(self, user_query: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🚀 Enhanced query processing with session context integration
        Wrapper around process_query that integrates Flask session authentication
        """

        start_time = datetime.now()

        try:
            # Extract user_id from session context
            user_id = session_context.get('session_id', 'anonymous') if session_context else 'anonymous'

            # 🔧 ENHANCED: Check if user is authenticated and extract customer info
            customer_id = None
            customer_verified = False

            if session_context:
                customer_verified = session_context.get('customer_verified', False)
                customer_id = session_context.get('customer_id')

                logger.info(f"🔐 Session context - Customer ID: {customer_id}, Verified: {customer_verified}")

            # Stage 0: Get Conversation History
            logger.info(f"📚 Stage 0: Retrieving conversation history for context")
            conversation_history = self.get_conversation_history(user_id)

            # Stage 1: Intent Classification with session context
            logger.info(f"🎯 Stage 1: Classifying query intent with session context")
            query_type, entities = self.classify_query_intent(user_query, conversation_history)

            # 🆕 ENHANCED: Inject customer_id from session into entities for authenticated queries
            if customer_verified and customer_id and not entities.get('customer_id'):
                entities['customer_id'] = customer_id
                entities['customer_verified'] = True
                logger.info(f"🔐 Injected customer_id {customer_id} from session into query entities")

            # Stage 2: SQL Generation with enhanced context
            logger.info(f"🔍 Stage 2: Generating SQL query with customer context")
            sql_query = self.generate_sql_query(user_query, query_type, entities)

            # Stage 3: Database Execution
            logger.info(f"🗄️ Stage 3: Executing database query")
            execution_result, error_message = self.execute_database_query(sql_query)

            # Create query context
            query_context = QueryContext(
                query_type=query_type,
                intent=query_type.value,
                entities=entities,
                sql_query=sql_query,
                execution_result=execution_result,
                response="",  # Will be filled next
                timestamp=start_time,
                user_query=user_query,
                error_message=error_message
            )

            # Stage 4: Generate Nigerian Response
            logger.info(f"🇳🇬 Stage 4: Generating Nigerian business response")
            query_context.response = self.generate_nigerian_response(query_context, conversation_history, session_context)

            # Stage 5: Store Context
            logger.info(f"📝 Stage 5: Storing conversation context")
            self.store_conversation_context(query_context, user_id)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Return comprehensive response
            return {
                'success': True,
                'response': query_context.response,
                'query_type': query_type.value,
                'sql_query': sql_query,
                'results_count': len(execution_result),
                'execution_time': f"{processing_time:.2f}s",
                'entities': entities,
                'timestamp': start_time.isoformat(),
                'error_message': error_message,
                'has_results': len(execution_result) > 0,
                'customer_authenticated': customer_verified,
                'customer_id': customer_id
            }

        except Exception as e:
            logger.error(f"❌ Enhanced pipeline error: {e}")
            return {
                'success': False,
                'response': f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or rephrase your question.",
                'error_message': str(e),
                'timestamp': start_time.isoformat(),
                'execution_time': f"{(datetime.now() - start_time).total_seconds():.2f}s"
            }

# Usage example and testing
if __name__ == "__main__":
    # Initialize the enhanced querying system
    db_querying = EnhancedDatabaseQuerying()

    # Test queries
    test_queries = [
        "Show me customers from Lagos state",
        "What's our total revenue this month?",
        "How many orders were placed using Bank Transfer?",
        "Which Nigerian state has the most customers?",
        "Show recent orders with Card payments"
    ]

    print("🇳🇬 Testing Enhanced Nigerian E-commerce Database Querying System\n")

    for i, query in enumerate(test_queries, 1):
        print(f"📋 Test {i}: {query}")
        result = db_querying.process_query(query, f"test_user_{i}")

        print(f"✅ Success: {result['success']}")
        print(f"🔍 Query Type: {result.get('query_type', 'N/A')}")
        print(f"📊 Results Count: {result.get('results_count', 0)}")
        print(f"⏱️ Execution Time: {result.get('execution_time', 'N/A')}")
        print(f"💬 Response: {result['response'][:200]}...")
        print("-" * 80)
