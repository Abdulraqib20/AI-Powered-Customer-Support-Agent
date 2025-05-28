"""
AI-Powered Customer Support Agent for Nigerian E-commerce
Flask Web Application

This application provides a modern web interface for customer support agents
to interact with Nigerian e-commerce customers, leveraging AI-powered chat,
customer management, analytics, and real-time monitoring.

Features:
- AI-driven chat using Groq LLaMA 3.1 8B
- Context-aware responses with Mem0 and Qdrant
- PostgreSQL database integration
- Nigerian market-specific configurations
- Real-time analytics and monitoring
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Flask imports
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_cors import CORS
import redis

# AI and ML imports
from groq import Groq
import google.generativeai as genai
from mem0 import Memory
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

# Local imports
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from config.database_config import DatabaseManager, CustomerRepository, OrderRepository, AnalyticsRepository
from config.appconfig import QDRANT_URL_CLOUD, QDRANT_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY
from config.logging_config import setup_logging

# Initialize loggers
app_logger, api_logger, error_logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)

# Flask Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'nigerian-ecommerce-support-2025')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'support_agent:'

# Initialize extensions
Session(app)
CORS(app)

# Initialize AI services
try:
    # Groq client for chat
    groq_client = Groq(api_key=GROQ_API_KEY)

    # Google AI for embeddings
    genai.configure(api_key=GOOGLE_API_KEY)

    # Qdrant client for vector search - Use local instance
    qdrant_client = QdrantClient(
        url="http://localhost:6333",
        # api_key=QDRANT_API_KEY,  # Local Qdrant doesn't need API key
    )

    # Test Qdrant connection
    try:
        collections = qdrant_client.get_collections()
        app_logger.info(f"✅ Connected to local Qdrant with {len(collections.collections)} collections")
    except Exception as e:
        app_logger.warning(f"⚠️ Qdrant connection test failed: {e}")

    # Mem0 for conversation memory - Use simplified configuration
    try:
        mem0_config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "url": "http://localhost:6333",
                    "collection_name": "conversation_memory"
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.1
                }
            }
        }
        memory = Memory.from_config(mem0_config)
        app_logger.info("✅ Mem0 memory initialized successfully")
    except Exception as mem_error:
        app_logger.warning(f"⚠️ Mem0 initialization failed: {mem_error}")
        memory = None

    app_logger.info("✅ AI services initialized successfully")

except Exception as e:
    error_logger.error(f"❌ Failed to initialize AI services: {e}")
    raise

# Initialize database
try:
    db_manager = DatabaseManager()
    customer_repo = CustomerRepository(db_manager)
    order_repo = OrderRepository(db_manager)
    analytics_repo = AnalyticsRepository(db_manager)

    app_logger.info("✅ Database services initialized successfully")

except Exception as e:
    error_logger.error(f"❌ Failed to initialize database: {e}")
    raise

# Initialize Redis for caching
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
    redis_client.ping()
    app_logger.info("✅ Redis cache initialized successfully")
except Exception as e:
    error_logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
    redis_client = None

# Nigerian States for filtering
NIGERIAN_STATES = [
    'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
    'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Gombe', 'Imo',
    'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos',
    'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers',
    'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'FCT'
]

# Payment methods specific to Nigeria
PAYMENT_METHODS = ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay']

# Order statuses
ORDER_STATUSES = ['Pending', 'Processing', 'Delivered', 'Returned']

# Account tiers
ACCOUNT_TIERS = ['Bronze', 'Silver', 'Gold', 'Platinum']


class APIUsageTracker:
    """Track API usage for Groq and Google services"""

    def __init__(self):
        self.groq_quotas = {
            "requests_per_minute": 30,
            "tokens_per_minute": 100000,
            "requests_per_day": 14400,
        }

        self.usage_data = {
            "groq_api": {
                "requests_today": 0,
                "tokens_today": 0,
                "requests_this_minute": 0,
                "tokens_this_minute": 0,
                "last_reset": datetime.now().date(),
                "last_minute_reset": datetime.now().replace(second=0, microsecond=0),
            }
        }

    def track_groq_request(self, tokens_used=0):
        """Track Groq API usage"""
        current_date = datetime.now().date()
        current_minute = datetime.now().replace(second=0, microsecond=0)

        # Reset daily counters
        if current_date != self.usage_data["groq_api"]["last_reset"]:
            self.usage_data["groq_api"]["requests_today"] = 0
            self.usage_data["groq_api"]["tokens_today"] = 0
            self.usage_data["groq_api"]["last_reset"] = current_date

        # Reset minute counters
        if current_minute != self.usage_data["groq_api"]["last_minute_reset"]:
            self.usage_data["groq_api"]["requests_this_minute"] = 0
            self.usage_data["groq_api"]["tokens_this_minute"] = 0
            self.usage_data["groq_api"]["last_minute_reset"] = current_minute

        # Update counters
        self.usage_data["groq_api"]["requests_today"] += 1
        self.usage_data["groq_api"]["tokens_today"] += tokens_used
        self.usage_data["groq_api"]["requests_this_minute"] += 1
        self.usage_data["groq_api"]["tokens_this_minute"] += tokens_used

        api_logger.info(f"📊 GROQ API Call - Tokens: {tokens_used}, "
                       f"RPM: {self.usage_data['groq_api']['requests_this_minute']}, "
                       f"TPM: {self.usage_data['groq_api']['tokens_this_minute']}")

    def get_usage_stats(self):
        """Get current usage statistics"""
        return self.usage_data

# Initialize usage tracker
usage_tracker = APIUsageTracker()


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        return super(DateTimeEncoder, self).default(obj)


def safe_json_dumps(obj):
    """Safely serialize objects to JSON, handling datetime objects"""
    try:
        return json.dumps(obj, cls=DateTimeEncoder, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        # If still can't serialize, convert to string representation
        error_logger.warning(f"⚠️ JSON serialization fallback: {e}")
        return json.dumps(str(obj))


def get_embedding(text: str) -> List[float]:
    """Generate embeddings using Google Text-Embedding-004"""
    try:
        # Check cache first
        cache_key = f"embedding:{hash(text)}"
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        # Generate embedding using the correct Google AI API
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        embedding = result['embedding']

        # Cache the result
        if redis_client:
            redis_client.setex(cache_key, 3600, json.dumps(embedding))  # Cache for 1 hour

        return embedding

    except Exception as e:
        error_logger.error(f"❌ Embedding generation failed: {e}")
        app_logger.info("🔄 Using fallback embedding method...")

        # Fallback: Simple text-based embedding (for development/testing)
        try:
            # Create a simple hash-based embedding as fallback
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to a list of floats (384 dimensions for compatibility)
            fallback_embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 32), 2)]
            # Pad to 384 dimensions
            while len(fallback_embedding) < 384:
                fallback_embedding.append(0.0)

            app_logger.info(f"✅ Generated fallback embedding with {len(fallback_embedding)} dimensions")
            return fallback_embedding[:384]  # Ensure exactly 384 dimensions

        except Exception as fallback_error:
            error_logger.error(f"❌ Fallback embedding also failed: {fallback_error}")
            return []


def get_ai_response(query: str, context: str = "", user_id: str = "anonymous") -> str:
    """Generate AI response using Groq LLaMA 3.1 8B"""
    try:
        # Check cache first
        cache_key = f"ai_response:{hash(query + context)}"
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return cached

        # Prepare system prompt for Nigerian e-commerce context
        system_prompt = """You are an AI customer support agent for a Nigerian e-commerce platform.

        Key guidelines:
        1. Use Nigerian English and be culturally aware
        2. Reference Nigerian states, payment methods (Pay on Delivery, RaqibTechPay, etc.)
        3. Format currency in Naira (₦)
        4. Be helpful, professional, and empathetic
        5. Provide specific, actionable solutions
        6. If you need database information, clearly state what data is needed

        Context: {context}

        Respond professionally and helpfully to the user's query."""

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt.format(context=context)},
            {"role": "user", "content": query}
        ]

        # Add conversation memory if available
        if memory:
            try:
                memory_context = memory.get(user_id)
                if memory_context:
                    # Take only the last 3 memories to keep context manageable
                    recent_memories = memory_context[-3:] if len(memory_context) > 3 else memory_context
                    memory_text = "\n".join([str(m) for m in recent_memories])
                    messages.insert(1, {"role": "system", "content": f"Previous conversation context: {memory_text}"})
                    app_logger.info(f"📚 Added {len(recent_memories)} memories to context")
            except Exception as e:
                app_logger.warning(f"⚠️ Memory retrieval failed: {e}")
        else:
            # Fallback: Use Redis for simple conversation history
            if redis_client:
                try:
                    history_key = f"chat_history:{user_id}"
                    history = redis_client.lrange(history_key, -6, -1)  # Last 3 exchanges (6 messages)
                    if history:
                        history_text = "\n".join(history)
                        messages.insert(1, {"role": "system", "content": f"Recent conversation: {history_text}"})
                        app_logger.info(f"📚 Added Redis chat history to context")
                except Exception as e:
                    app_logger.warning(f"⚠️ Redis history retrieval failed: {e}")

        # Generate response
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        # Track usage
        usage_tracker.track_groq_request(response.usage.total_tokens)

        # Store in memory
        if memory:
            try:
                memory.add(f"User: {query}\nAI: {ai_response}", user_id=user_id)
                app_logger.info("💾 Stored conversation in Mem0")
            except Exception as e:
                app_logger.warning(f"⚠️ Memory storage failed: {e}")
        else:
            # Fallback: Store in Redis
            if redis_client:
                try:
                    history_key = f"chat_history:{user_id}"
                    redis_client.lpush(history_key, f"User: {query}")
                    redis_client.lpush(history_key, f"AI: {ai_response}")
                    redis_client.ltrim(history_key, 0, 19)  # Keep last 20 messages
                    redis_client.expire(history_key, 86400)  # Expire after 24 hours
                    app_logger.info("💾 Stored conversation in Redis")
                except Exception as e:
                    app_logger.warning(f"⚠️ Redis storage failed: {e}")

        # Cache the response
        if redis_client:
            redis_client.setex(cache_key, 1800, ai_response)  # Cache for 30 minutes

        return ai_response

    except Exception as e:
        error_logger.error(f"❌ AI response generation failed: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact our technical support team."


def format_currency(amount: float) -> str:
    """Format amount as Nigerian Naira"""
    return f"₦{amount:,.2f}"


def search_vector_database(query: str, collection_name: str = "customer_data") -> List[Dict]:
    """Search Qdrant vector database for relevant information"""
    try:
        # Generate query embedding
        query_embedding = get_embedding(query)
        if not query_embedding:
            app_logger.warning("⚠️ No embedding generated, skipping vector search")
            return []

        # Check if collection exists
        try:
            collections = qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if collection_name not in collection_names:
                app_logger.info(f"📝 Collection '{collection_name}' doesn't exist, creating it...")

                # Create collection with proper vector configuration
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=len(query_embedding), distance=Distance.COSINE)
                )
                app_logger.info(f"✅ Created collection '{collection_name}' with {len(query_embedding)} dimensions")

                # For now, return empty results as there's no data yet
                return []

        except Exception as collection_error:
            app_logger.warning(f"⚠️ Collection check failed: {collection_error}")
            return []

        # Search Qdrant
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=5
        )

        search_results = [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]
        app_logger.info(f"🔍 Vector search returned {len(search_results)} results")

        return search_results

    except Exception as e:
        error_logger.error(f"❌ Vector search failed: {e}")
        return []


# Routes

@app.route('/')
def dashboard():
    """Main dashboard with 4 tabs"""
    try:
        # Get basic analytics for dashboard
        customer_count = len(customer_repo.search_customers("", ""))
        order_summary = order_repo.get_order_summary()

        stats = {
            'total_customers': customer_count,
            'total_orders': len(order_summary) if order_summary else 0,
            'usage_stats': usage_tracker.get_usage_stats()
        }

        return render_template('dashboard.html',
                             states=NIGERIAN_STATES,
                             account_tiers=ACCOUNT_TIERS,
                             order_statuses=ORDER_STATUSES,
                             payment_methods=PAYMENT_METHODS,
                             stats=stats)

    except Exception as e:
        error_logger.error(f"❌ Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html',
                             states=NIGERIAN_STATES,
                             account_tiers=ACCOUNT_TIERS,
                             order_statuses=ORDER_STATUSES,
                             payment_methods=PAYMENT_METHODS,
                             stats={})


# API Routes

@app.route('/api/customers', methods=['GET', 'POST'])
def api_customers():
    """Customer API endpoint"""
    try:
        if request.method == 'GET':
            # Get customers with optional filters
            search_term = request.args.get('search', '')
            state = request.args.get('state', '')
            tier = request.args.get('tier', '')

            if state and state != 'all':
                customers = customer_repo.get_customers_by_state(state)
            else:
                customers = customer_repo.search_customers(search_term)

            # Filter by tier if specified
            if tier and tier != 'all':
                customers = [c for c in customers if c.get('account_tier') == tier]

            return jsonify({
                'success': True,
                'data': customers,
                'count': len(customers)
            })

        elif request.method == 'POST':
            # Update customer profile
            data = request.json
            customer_id = data.get('customer_id')
            updates = {k: v for k, v in data.items() if k != 'customer_id'}

            if customer_repo.update_customer(customer_id, updates):
                return jsonify({'success': True, 'message': 'Customer updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Update failed'}), 400

    except Exception as e:
        error_logger.error(f"❌ Customer API error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/orders', methods=['GET', 'POST'])
def api_orders():
    """Orders API endpoint"""
    try:
        if request.method == 'GET':
            # Get orders with optional filters
            status = request.args.get('status', '')
            customer_id = request.args.get('customer_id', '')

            if status and status != 'all':
                orders = order_repo.get_orders_by_status(status)
            elif customer_id:
                orders = order_repo.get_orders_by_customer(int(customer_id))
            else:
                orders = order_repo.get_order_summary()

            # Format currency in response
            for order in orders:
                if 'total_amount' in order:
                    order['formatted_amount'] = format_currency(float(order['total_amount']))

            return jsonify({
                'success': True,
                'data': orders,
                'count': len(orders)
            })

        elif request.method == 'POST':
            # Update order status
            data = request.json
            order_id = data.get('order_id')
            new_status = data.get('status')

            if order_repo.update_order_status(order_id, new_status):
                return jsonify({'success': True, 'message': 'Order status updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Update failed'}), 400

    except Exception as e:
        error_logger.error(f"❌ Orders API error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    """Analytics API endpoint"""
    try:
        metric_type = request.args.get('type', 'summary')

        if metric_type == 'summary':
            # Get summary analytics
            customer_dist = customer_repo.get_customer_distribution()
            revenue_by_state = order_repo.get_revenue_by_state()
            clv = analytics_repo.get_customer_lifetime_value()

            return jsonify({
                'success': True,
                'data': {
                    'customer_distribution': customer_dist,
                    'revenue_by_state': revenue_by_state,
                    'customer_lifetime_value': clv[:10]  # Top 10
                }
            })

        elif metric_type == 'usage':
            # Get API usage metrics
            usage_stats = usage_tracker.get_usage_stats()
            return jsonify({
                'success': True,
                'data': usage_stats
            })

        else:
            # Get specific metrics from analytics table
            metrics = analytics_repo.get_metrics_by_type(metric_type)
            return jsonify({
                'success': True,
                'data': metrics
            })

    except Exception as e:
        error_logger.error(f"❌ Analytics API error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """AI Chat API endpoint"""
    try:
        data = request.json
        query = data.get('message', '').strip()
        user_id = session.get('user_id', 'anonymous')

        if not query:
            return jsonify({'success': False, 'message': 'Message is required'}), 400

        # Check for database queries and gather context
        context = ""

        # Extract context based on query intent
        if any(word in query.lower() for word in ['customer', 'customers', 'profile']):
            # If asking about customers, get relevant customer data
            search_term = ""
            state = ""

            # Simple intent extraction
            for state_name in NIGERIAN_STATES:
                if state_name.lower() in query.lower():
                    state = state_name
                    break

            customers = customer_repo.get_customers_by_state(state) if state else customer_repo.search_customers(search_term)[:5]
            context += f"Recent customers: {safe_json_dumps(customers[:3])}\n"

        if any(word in query.lower() for word in ['order', 'orders', 'payment', 'delivery']):
            # If asking about orders, get relevant order data
            orders = order_repo.get_order_summary()[:5]
            context += f"Recent orders: {safe_json_dumps(orders)}\n"

        if any(word in query.lower() for word in ['analytics', 'revenue', 'sales', 'metrics']):
            # If asking about analytics, get relevant data
            revenue_data = order_repo.get_revenue_by_state()[:5]
            context += f"Revenue by state: {safe_json_dumps(revenue_data)}\n"

        # Search vector database for additional context
        vector_results = search_vector_database(query)
        if vector_results:
            context += f"Related information: {safe_json_dumps(vector_results[:2])}\n"

        # Generate AI response
        ai_response = get_ai_response(query, context, user_id)

        # Generate quick action buttons based on query
        quick_actions = []
        if any(word in query.lower() for word in ['payment', 'refund', 'issue']):
            quick_actions.append({'text': 'Resolve Payment Issue', 'action': 'resolve_payment'})
        if any(word in query.lower() for word in ['delivery', 'shipping']):
            quick_actions.append({'text': 'Track Delivery', 'action': 'track_delivery'})
        if any(word in query.lower() for word in ['customer', 'profile']):
            quick_actions.append({'text': 'View Customer Profile', 'action': 'view_profile'})

        return jsonify({
            'success': True,
            'response': ai_response,
            'quick_actions': quick_actions,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        error_logger.error(f"❌ Chat API error: {e}")
        return jsonify({'success': False, 'message': 'Chat service temporarily unavailable'}), 500


@app.route('/api/quick-action', methods=['POST'])
def api_quick_action():
    """Handle quick action buttons"""
    try:
        data = request.json
        action = data.get('action')
        context = data.get('context', {})

        if action == 'resolve_payment':
            # Payment resolution logic
            response = "I've initiated the payment resolution process. Please provide the order ID for specific assistance."

        elif action == 'track_delivery':
            # Delivery tracking logic
            response = "Let me check the delivery status. Please provide the order ID or customer details."

        elif action == 'view_profile':
            # Customer profile logic
            response = "I can help you access customer profiles. Please provide the customer ID or email address."

        else:
            response = "I'm here to help! What specific action would you like me to take?"

        return jsonify({
            'success': True,
            'response': response
        })

    except Exception as e:
        error_logger.error(f"❌ Quick action error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    error_logger.error(f"❌ Internal server error: {error}")
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Initialize session
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
