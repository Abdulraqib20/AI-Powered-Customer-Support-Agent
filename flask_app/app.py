"""
AI-Powered Customer Support Agent for Nigerian E-commerce
Flask Web Application

This application provides a modern web interface for customer support agents
to interact with Nigerian e-commerce customers, leveraging AI-powered chat,
customer management, analytics, and real-time monitoring.

Features:
- AI-driven chat using LLaMA models via Groq API
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
import uuid

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
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter(action='ignore')

# Local imports
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from config.database_config import DatabaseManager, CustomerRepository, OrderRepository, AnalyticsRepository
from config.appconfig import QDRANT_URL_CLOUD, QDRANT_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY
from config.logging_config import setup_logging

# Add enhanced database querying import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.enhanced_db_querying import EnhancedDatabaseQuerying

# Add session manager import
from src.session_manager import session_manager

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
                "provider": "litellm",
                "config": {
                    "model": "gemini/gemini-2.0-flash",
                    "temperature": 0.2,
                    "max_tokens": 1500,
                }
            },
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

# Initialize API usage tracker
api_tracker = APIUsageTracker()

# Session Management Functions
@app.before_request
def before_request():
    """Initialize session for each request"""
    # Skip session handling for static files
    if request.endpoint and request.endpoint.startswith('static'):
        return

    # Initialize session if not exists
    if 'session_id' not in session:
        try:
            session_id = session_manager.create_session()
            session['session_id'] = session_id
            session['current_conversation_id'] = None
            app_logger.info(f"🆕 Created new session: {session_id}")
        except Exception as e:
            error_logger.error(f"❌ Failed to create session: {e}")
            # Use fallback session ID
            session['session_id'] = f"fallback_{uuid.uuid4()}"
            session['current_conversation_id'] = None
    else:
        # Update session activity if it exists in database
        try:
            session_manager.update_session_activity(session['session_id'])
        except Exception as e:
            # If session update fails, it might not exist in DB, recreate it
            app_logger.warning(f"⚠️ Session update failed, recreating: {e}")
            try:
                session_id = session_manager.create_session()
                session['session_id'] = session_id
                session['current_conversation_id'] = None
            except Exception as create_error:
                error_logger.error(f"❌ Failed to recreate session: {create_error}")
                # Keep existing session ID as fallback


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
        # Check if Google AI is configured
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'your-google-api-key-here':
            app_logger.warning("⚠️ Google API key not configured, using fallback embedding")
            # Create a simple hash-based embedding as fallback
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to a list of floats (384 dimensions for compatibility)
            fallback_embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 32), 2)]
            # Pad to 384 dimensions
            while len(fallback_embedding) < 384:
                fallback_embedding.append(0.0)
            return fallback_embedding[:384]  # Ensure exactly 384 dimensions

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
    """
    Generate AI response using Llama models via Groq API with Nigerian e-commerce context
    """
    try:
        if groq_client is None:
            return "I'm currently operating in limited mode. AI chat functionality requires API configuration. However, I can still help you with basic customer support tasks and database queries."

        # raqibtech.com customer support context
        system_prompt = """You are a friendly customer support AI assistant for raqibtech.com, a Nigerian e-commerce platform.
        You help customers with their orders, account questions, payment issues, delivery tracking, and shopping assistance.

        Platform context:
        - raqibtech.com: Nigerian e-commerce platform
        - User: Customer who shops on the platform (not internal staff)
        - Serving customers across all 36 Nigerian states + FCT
        - Payment methods: Pay on Delivery, Bank Transfer, Card, RaqibTechPay
        - Currency: Nigerian Naira (₦)
        - Business hours: 8 AM - 8 PM WAT (West Africa Time)

        Customer service style:
        - Warm, friendly, and professional tone
        - Help customers with their specific needs
        - Address customers directly ("your order", "your account")
        - Provide clear, actionable guidance
        - Show that raqibtech.com cares about their experience
        - Use conversational Nigerian English
        """

        # Prepare the conversation
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Relevant data context: {context}"
            })

        # Add user query
        messages.append({"role": "user", "content": query})

        # Generate response using Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Faster model for real-time customer chat
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
            top_p=0.9,
            stream=False
        )

        response = completion.choices[0].message.content

        # Track API usage
        usage_tracker.track_groq_request(completion.usage.total_tokens if completion.usage else 0)

        # Store conversation in memory if available
        if memory:
            try:
                memory.add(
                    messages=[
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": response}
                    ],
                    user_id=user_id
                )
            except Exception as mem_error:
                app_logger.warning(f"Memory storage failed: {mem_error}")

        return response

    except Exception as e:
        error_logger.error(f"❌ AI response generation failed: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again or contact support for assistance."


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


# Initialize enhanced database querying system - Now using session-aware instances
# try:
#     enhanced_db_querying = EnhancedDatabaseQuerying()
#     app_logger.info("✅ Enhanced database querying initialized successfully")
# except Exception as e:
#     app_logger.warning(f"⚠️ Enhanced database querying failed to initialize: {e}")
#     enhanced_db_querying = None


# Routes

@app.route('/')
def dashboard():
    """Main dashboard with customer support interface"""
    try:
        # Get overview statistics
        customers = customer_repo.get_all_customers()
        recent_orders = order_repo.get_recent_orders(limit=10)
        analytics_data = analytics_repo.get_overview_analytics()

        # 🔧 FIX: Isolate guest sessions from authenticated user conversations
        conversations = []
        current_conversation_id = None

        # Only load conversations for authenticated users
        if session.get('user_authenticated', False):
            conversations = session_manager.get_user_conversations(session['session_id'])

            # Create a default conversation if none exists for authenticated users
            if not conversations:
                try:
                    conversation_id = session_manager.create_conversation(session['session_id'], "New Chat")
                    session['current_conversation_id'] = conversation_id
                    conversations = session_manager.get_user_conversations(session['session_id'])
                except Exception as conv_error:
                    app_logger.warning(f"⚠️ Failed to create default conversation: {conv_error}")
                    conversations = []
                    session['current_conversation_id'] = None
            else:
                # Use the most recent conversation if no current one is set
                if not session.get('current_conversation_id'):
                    session['current_conversation_id'] = conversations[0].conversation_id

            current_conversation_id = session.get('current_conversation_id')
        else:
            # 🆕 Guest users start fresh with no conversation history
            app_logger.info("👤 Guest user - starting fresh session without conversation history")
            session['current_conversation_id'] = None

        # Calculate summary statistics
        stats = {
            'total_customers': len(customers) if customers else 0,
            'total_orders': len(recent_orders) if recent_orders else 0,
            'pending_orders': len([o for o in recent_orders if o['order_status'] == 'Pending']) if recent_orders else 0,
            'active_conversations': len(conversations)
        }

        app_logger.info(f"Dashboard loaded with {stats['total_customers']} customers, {stats['total_orders']} orders, {stats['active_conversations']} conversations")

        return render_template('dashboard.html',
                             customers=customers[:5],  # Show first 5 customers
                             recent_orders=recent_orders[:5],  # Show first 5 orders
                             stats=stats,
                             conversations=conversations,
                             current_conversation_id=current_conversation_id)

    except Exception as e:
        error_logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html',
                             customers=[],
                             recent_orders=[],
                             stats={'total_customers': 0, 'total_orders': 0, 'pending_orders': 0, 'active_conversations': 0},
                             conversations=[],
                             current_conversation_id=None)


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
    """🇳🇬 Enhanced AI Chat API endpoint with sophisticated database querying"""
    try:
        data = request.json
        query = data.get('message', '').strip()
        user_id = session.get('user_id', 'anonymous')

        if not query:
            return jsonify({'success': False, 'message': 'Message is required'}), 400

        # 🚀 NEW: Use enhanced database querying system for sophisticated analysis
        # if enhanced_db_querying is not None:
        #     enhanced_result = enhanced_db_querying.process_query(query, user_id)
        #
        #     if enhanced_result['success'] and enhanced_result.get('has_results', False):
        #         # Use the sophisticated pipeline result
        #         ai_response = enhanced_result['response']
        #
        #         # Generate quick action buttons based on query type
        #         quick_actions = []
        #         query_type = enhanced_result.get('query_type', '')
        #
        #         if query_type == 'customer_analysis':
        #             quick_actions.extend([
        #                 {'text': 'View Customer Details', 'action': 'view_customer_details'},
        #                 {'text': 'Customer Distribution by State', 'action': 'customer_distribution'}
        #             ])
        #         elif query_type == 'order_analytics':
        #             quick_actions.extend([
        #                 {'text': 'Track Order Status', 'action': 'track_order'},
        #                 {'text': 'Payment Analysis', 'action': 'payment_analysis'}
        #             ])
        #         elif query_type == 'revenue_insights':
        #             quick_actions.extend([
        #                 {'text': 'Revenue Breakdown', 'action': 'revenue_breakdown'},
        #                 {'text': 'State Performance', 'action': 'state_performance'}
        #             ])
        #         elif query_type == 'geographic_analysis':
        #             quick_actions.extend([
        #                 {'text': 'Regional Analytics', 'action': 'regional_analytics'},
        #                 {'text': 'Delivery Insights', 'action': 'delivery_insights'}
        #             ])
        #
        #         return jsonify({
        #             'success': True,
        #             'response': ai_response,
        #             'quick_actions': quick_actions,
        #             'query_type': query_type,
        #             'results_count': enhanced_result.get('results_count', 0),
        #             'execution_time': enhanced_result.get('execution_time', ''),
        #             'timestamp': datetime.now().isoformat(),
        #             'enhanced': True  # Flag to indicate enhanced processing
        #         })

        # Fallback to original logic for non-database queries or errors
        context = ""

        # Extract context based on query intent (original logic)
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
            'timestamp': datetime.now().isoformat(),
            'enhanced': False  # Flag to indicate fallback processing
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


@app.route('/api/enhanced-query', methods=['POST'])
def api_enhanced_query():
    """Enhanced query API with advanced database querying and AI responses"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        include_sql = data.get('include_sql', False)

        if not user_query:
            return jsonify({
                'success': False,
                'message': 'Query is required'
            }), 400

        # Get session context for AI
        session_context = session_manager.get_session_context_for_ai(session['session_id'])

        # 🔧 FIX: Add Flask session authentication data to context
        if session.get('user_authenticated') and session.get('user_email'):
            session_context.update({
                'user_authenticated': True,
                'user_email': session['user_email'],
                'customer_id': session.get('customer_id'),
                'customer_verified': True  # If they logged in successfully, they're verified
            })

            # Also update the session manager with the email
            try:
                with session_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE user_sessions
                            SET user_identifier = %s
                            WHERE session_id = %s
                        """, (session['user_email'], session['session_id']))
                        conn.commit()
            except Exception as session_update_error:
                app_logger.warning(f"⚠️ Failed to update session with email: {session_update_error}")

        # Get or create conversation
        conversation_id = session.get('current_conversation_id')
        if not conversation_id:
            try:
                conversation_id = session_manager.create_conversation(session['session_id'], "New Chat")
                session['current_conversation_id'] = conversation_id
            except Exception as conv_error:
                app_logger.warning(f"⚠️ Failed to create conversation: {conv_error}")
                conversation_id = None
        else:
            # Verify conversation exists
            try:
                conversations = session_manager.get_user_conversations(session['session_id'])
                if not any(conv.conversation_id == conversation_id for conv in conversations):
                    # Conversation doesn't exist, create a new one
                    conversation_id = session_manager.create_conversation(session['session_id'], "New Chat")
                    session['current_conversation_id'] = conversation_id
            except Exception as verify_error:
                app_logger.warning(f"⚠️ Failed to verify conversation: {verify_error}")
                conversation_id = None

        # Add user message to conversation (if conversation exists)
        message_added = False
        if conversation_id:
            try:
                session_manager.add_message(conversation_id, 'user', user_query)
                message_added = True
            except Exception as msg_error:
                app_logger.warning(f"⚠️ Failed to add user message: {msg_error}")

        # Initialize enhanced query engine
        enhanced_querying = EnhancedDatabaseQuerying()

        # 🔄 Use the enhanced process_enhanced_query method with session context
        result = enhanced_querying.process_enhanced_query(user_query, session_context)

        # Add AI response to conversation (if conversation exists)
        if conversation_id and message_added:
            try:
                ai_metadata = {
                    'query_type': result.get('query_type'),
                    'execution_time': result.get('execution_time'),
                    'results_count': result.get('results_count')
                }
                session_manager.add_message(conversation_id, 'ai', result['response'], ai_metadata)
            except Exception as ai_msg_error:
                app_logger.warning(f"⚠️ Failed to add AI message: {ai_msg_error}")

        # Auto-generate conversation title from first user message (if conversation exists)
        if conversation_id:
            try:
                conversations = session_manager.get_user_conversations(session['session_id'])
                current_conv = next((c for c in conversations if c.conversation_id == conversation_id), None)
                if current_conv and current_conv.conversation_title == "New Chat" and current_conv.message_count >= 2:
                    # Generate title from first 5 words of user query
                    title_words = user_query.split()[:5]
                    title = ' '.join(title_words) + ('...' if len(title_words) == 5 else '')
                    session_manager.update_conversation_title(conversation_id, title)
            except Exception as title_error:
                app_logger.warning(f"⚠️ Failed to update conversation title: {title_error}")

        # Include SQL in response if requested
        if include_sql:
            result['sql_query'] = result.get('sql_query', '')

        api_logger.info(f"Enhanced query processed: {result.get('query_type', 'unknown')} - {result.get('execution_time', 'N/A')}")

        # Return enhanced response with full pipeline details
        return jsonify({
            'success': result.get('success', True),
            'response': result.get('response', 'No response generated'),
            'query_type': result.get('query_type', 'unknown'),
            'sql_query': result.get('sql_query', '') if include_sql else '',
            'results_count': result.get('results_count', 0),
            'execution_time': result.get('execution_time', 'N/A'),
            'entities': result.get('entities', {}),
            'has_results': result.get('has_results', False),
            'timestamp': result.get('timestamp', datetime.now().isoformat()),
            'session_authenticated': session.get('user_authenticated', False),
            'session_user': session.get('user_email', 'guest'),
            'conversation_id': conversation_id,
            'message_added': message_added,
            'pipeline_stages': {
                'intent_classification': f"Query Type: {result.get('query_type', 'unknown')}",
                'sql_generation': 'SQL query generated' if result.get('sql_query') else 'No SQL needed',
                'database_execution': f"Found {result.get('results_count', 0)} results",
                'response_generation': 'AI response generated successfully'
            }
        })

    except Exception as e:
        error_logger.error(f"Enhanced query API error: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/conversation-history', methods=['GET'])
def api_conversation_history():
    """🗂️ Get conversation history for a user"""
    try:
        # if enhanced_db_querying is None:
        #     return jsonify({
        #         'success': False,
        #         'message': 'Conversation history service is not available',
        #         'history': [],
        #         'count': 0
        #     })

        user_id = request.args.get('user_id', session.get('user_id', 'anonymous'))
        limit = int(request.args.get('limit', 10))

        # Use session manager to get conversation history
        conversations = session_manager.get_user_conversations(session['session_id'])

        # Format conversations for response
        formatted_history = []
        for conv in conversations[:limit]:
            formatted_history.append({
                'conversation_id': conv.conversation_id,
                'title': conv.conversation_title,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': conv.message_count
            })

        return jsonify({
            'success': True,
            'history': formatted_history,
            'count': len(formatted_history),
            'user_id': user_id
        })

    except Exception as e:
        error_logger.error(f"❌ Conversation history error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve conversation history',
            'history': [],
            'count': 0
        }), 500


@app.route('/api/query-suggestions', methods=['GET'])
def api_query_suggestions():
    """💡 Get suggested queries based on Nigerian e-commerce context"""
    try:
        category = request.args.get('category', 'general')

        suggestions = {
            'customer_analysis': [
                "Update my account information",
                "Check my account tier and benefits",
                "What are the benefits of upgrading my account?",
                "How do I change my account details?",
                "Show me my account summary"
            ],
            'order_analytics': [
                "Track my recent order",
                "Where is my delivery?",
                "Check status of order #12345",
                "Show my order history",
                "Cancel or modify my order"
            ],
            'revenue_insights': [
                "Show my spending history",
                "What payment methods can I use?",
                "Check my payment status",
                "How much have I spent this month?",
                "Update my payment information"
            ],
            'geographic_analysis': [
                "Update my delivery address",
                "What delivery options are available in my area?",
                "Check delivery charges to my location",
                "Change my shipping address",
                "Find nearest pickup location"
            ],
            'general': [
                "Help me track my order",
                "Update my account details",
                "Check my payment status",
                "What products do you recommend?",
                "How do I contact customer service?"
            ]
        }

        return jsonify({
            'success': True,
            'suggestions': suggestions.get(category, suggestions['general']),
            'category': category,
            'available_categories': list(suggestions.keys())
        })

    except Exception as e:
        error_logger.error(f"❌ Query suggestions API error: {e}")
        return jsonify({
            'success': False,
            'message': 'Query suggestions service unavailable'
        }), 500


@app.route('/api/business-intelligence', methods=['GET'])
def api_business_intelligence():
    """📊 Advanced Business Intelligence Dashboard API"""
    try:
        # Get comprehensive business intelligence data
        intelligence_data = {}

        # Customer Intelligence
        try:
            customer_dist = customer_repo.get_customer_distribution()
            intelligence_data['customer_distribution'] = customer_dist
        except Exception as e:
            error_logger.warning(f"Customer distribution error: {e}")
            intelligence_data['customer_distribution'] = []

        # Revenue Intelligence
        try:
            revenue_data = order_repo.get_revenue_by_state()
            # Format revenue in Naira
            for item in revenue_data:
                if 'total_revenue' in item and item['total_revenue']:
                    from src.enhanced_db_querying import NigerianBusinessIntelligence
                    ni_intel = NigerianBusinessIntelligence()
                    item['formatted_revenue'] = ni_intel.format_naira(float(item['total_revenue']))

            intelligence_data['revenue_by_state'] = revenue_data
        except Exception as e:
            error_logger.warning(f"Revenue data error: {e}")
            intelligence_data['revenue_by_state'] = []

        # Order Intelligence
        try:
            order_summary = order_repo.get_order_summary()[:20]  # Last 20 orders
            intelligence_data['recent_orders'] = order_summary
        except Exception as e:
            error_logger.warning(f"Order summary error: {e}")
            intelligence_data['recent_orders'] = []

        # Nigerian Business Context
        from src.enhanced_db_querying import NigerianBusinessIntelligence
        ni_intel = NigerianBusinessIntelligence()
        intelligence_data['nigerian_context'] = {
            'timezone_info': ni_intel.get_nigerian_timezone_context(),
            'supported_states': NIGERIAN_STATES,
            'payment_methods': ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay']
        }

        return jsonify({
            'success': True,
            'data': intelligence_data,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_states_covered': len(set([item.get('state') for item in intelligence_data.get('customer_distribution', []) if item.get('state')])),
                'total_customers': sum([item.get('customer_count', 0) for item in intelligence_data.get('customer_distribution', [])]),
                'total_revenue': sum([float(item.get('total_revenue', 0)) for item in intelligence_data.get('revenue_by_state', []) if item.get('total_revenue')])
            }
        })

    except Exception as e:
        error_logger.error(f"❌ Business intelligence API error: {e}")
        return jsonify({
            'success': False,
            'message': 'Business intelligence service temporarily unavailable',
            'error': str(e)
        }), 500


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get user conversations"""
    try:
        # 🔧 FIX: Only authenticated users can access conversations
        if not session.get('user_authenticated', False):
            return jsonify({
                'success': True,
                'conversations': [],
                'message': 'Please log in to access conversation history'
            })

        conversations = session_manager.get_user_conversations(session['session_id'])

        # Convert to serializable format
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                'conversation_id': conv.conversation_id,
                'title': conv.conversation_title,
                'message_count': conv.message_count,
                'updated_at': conv.updated_at.isoformat(),
                'is_active': conv.is_active
            })

        return jsonify({
            'success': True,
            'conversations': conversation_list
        })

    except Exception as e:
        app_logger.error(f"❌ Error getting conversations: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/conversations/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation"""
    try:
        # 🔧 FIX: Only authenticated users can access conversation messages
        if not session.get('user_authenticated', False):
            return jsonify({
                'success': False,
                'message': 'Please log in to access conversation messages'
            }), 401

        messages = session_manager.get_conversation_messages(conversation_id)

        message_list = []
        for msg in messages:
            message_list.append({
                'message_id': msg.message_id,
                'sender_type': msg.sender_type,
                'content': msg.message_content,
                'metadata': msg.metadata,
                'timestamp': msg.created_at.isoformat()
            })

        return jsonify({
            'success': True,
            'messages': message_list
        })

    except Exception as e:
        app_logger.error(f"❌ Error getting conversation messages: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/conversations/new', methods=['POST'])
def create_new_conversation():
    """Create a new conversation"""
    try:
        # 🔧 FIX: Only authenticated users can create conversations
        if not session.get('user_authenticated', False):
            return jsonify({
                'success': False,
                'message': 'Please log in to create conversation history'
            }), 401

        conversation_id = session_manager.create_conversation(session['session_id'])
        session['current_conversation_id'] = conversation_id

        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        })

    except Exception as e:
        app_logger.error(f"❌ Error creating conversation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/conversations/<conversation_id>/switch', methods=['POST'])
def switch_conversation(conversation_id):
    """Switch to a different conversation"""
    try:
        # 🔧 FIX: Only authenticated users can switch conversations
        if not session.get('user_authenticated', False):
            return jsonify({
                'success': False,
                'message': 'Please log in to access conversation history'
            }), 401

        session['current_conversation_id'] = conversation_id

        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        })

    except Exception as e:
        app_logger.error(f"❌ Error switching conversation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/login')
def login_page():
    """Simple login page"""
    # Provide default stats to prevent template errors
    default_stats = {'total_customers': 0, 'total_orders': 0, 'pending_orders': 0, 'active_conversations': 0}
    return render_template('login.html', stats=default_stats)


@app.route('/api/login', methods=['POST'])
def login_api():
    """Simple login API - only allows existing customers"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        # Check if customer exists in database
        try:
            customer = customer_repo.get_customer_by_email(email)
            if not customer:
                return jsonify({
                    'success': False,
                    'message': 'Customer not found. Please make sure you\'re using the email address associated with your raqibtech.com orders.'
                }), 404
        except Exception as db_error:
            error_logger.error(f"Database error during customer lookup: {db_error}")
            return jsonify({'success': False, 'message': 'Database connection issue. Please try again.'}), 500

        # Update session with user identifier
        session_id = session['session_id']
        try:
            with session_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_sessions
                        SET user_identifier = %s
                        WHERE session_id = %s
                    """, (email, session_id))
                    conn.commit()
        except Exception as session_error:
            error_logger.error(f"Session update error: {session_error}")
            # Continue with login even if session update fails
            app_logger.warning("Session update failed but continuing with login")

        session['user_email'] = email
        session['user_authenticated'] = True
        session['customer_id'] = customer['customer_id']  # Store customer ID for queries

        return jsonify({
            'success': True,
            'message': f'Welcome back, {customer["name"]}!',
            'user_email': email,
            'customer_name': customer['name']
        })

    except Exception as e:
        error_logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': f'Login failed: {str(e)}'}), 500


@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user_email', None)
    session.pop('user_authenticated', None)
    return redirect(url_for('dashboard'))


# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'session_id': session.get('session_id', 'none')
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    # Provide default stats to prevent template errors
    default_stats = {'total_customers': 0, 'total_orders': 0, 'pending_orders': 0, 'active_conversations': 0}
    return render_template('404.html', stats=default_stats), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    error_logger.error(f"❌ Internal server error: {error}")
    # Provide default stats to prevent template errors
    default_stats = {'total_customers': 0, 'total_orders': 0, 'pending_orders': 0, 'active_conversations': 0}
    return render_template('500.html', stats=default_stats), 500


if __name__ == '__main__':
    # Initialize session
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
