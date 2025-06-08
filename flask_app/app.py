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
import psycopg2
from psycopg2.extras import RealDictCursor

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

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# 🆕 Import new systems
from src.recommendation_engine import ProductRecommendationEngine
from src.order_management import OrderManagementSystem
from src.email_service import EmailService

# Initialize loggers FIRST before any conditional imports
app_logger, api_logger, error_logger = setup_logging()

# Add import for the enhanced customer support recommendation system
try:
    from src.customer_support_recommendations import (
        CustomerSupportRecommendationEngine,
        SupportRecommendationRequest,
        SupportScenario,
        get_customer_support_recommendations
    )
    app_logger.info("✅ Successfully imported enhanced customer support recommendations")
    ENHANCED_SUPPORT_AVAILABLE = True
except ImportError as e:
    app_logger.warning(f"⚠️ Enhanced customer support recommendations not available: {e}")
    ENHANCED_SUPPORT_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)

# Flask Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'nigerian-ecommerce-support-2025')

# 🔧 CRITICAL FIX: Implement fallback session configuration for when Redis is unavailable
try:
    # Test Redis connection first
    test_redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    test_redis.ping()

    # Redis is available, use Redis sessions
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'support_agent:'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Keep sessions for 7 days

    app_logger.info("✅ Redis available - using Redis sessions")

except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
    app_logger.warning(f"⚠️ Redis not available ({e}), falling back to filesystem sessions")

    # Fallback to filesystem sessions
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'session_data')
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_FILE_THRESHOLD'] = 500
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Keep sessions for 7 days

    # Create session directory if it doesn't exist
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    app_logger.info("✅ Using filesystem sessions as fallback")

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

    # Initialize enhanced database querying
    db_querying = EnhancedDatabaseQuerying()

    app_logger.info("✅ Database services initialized successfully")

except Exception as e:
    error_logger.error(f"❌ Failed to initialize database: {e}")
    raise

# Initialize Email Service
try:
    email_service = EmailService()
    app_logger.info("✅ Email service initialized successfully")
except Exception as e:
    error_logger.warning(f"⚠️ Email service initialization failed: {e}")
    email_service = None

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
    """Initialize session for each request with comprehensive error handling"""
    # Skip session handling for static files
    if request.endpoint and request.endpoint.startswith('static'):
        return

    # 🔧 CRITICAL FIX: Ensure session persistence
    session.permanent = True

    # Initialize session if not exists
    if 'session_id' not in session:
        try:
            session_id = session_manager.create_session()
            session['session_id'] = session_id
            session['current_conversation_id'] = None
            app_logger.info(f"🆕 Created new session: {session_id}")
        except psycopg2.DatabaseError as db_error:
            app_logger.error(f"❌ Database error creating session: {db_error}")
            # Use fallback session without database backing
            session['session_id'] = f"fallback_{uuid.uuid4()}"
            session['current_conversation_id'] = None
            app_logger.warning("⚠️ Using fallback session due to database error")
        except Exception as e:
            app_logger.error(f"❌ Failed to create session: {e}")
            # Use fallback session ID
            session['session_id'] = f"fallback_{uuid.uuid4()}"
            session['current_conversation_id'] = None
            app_logger.warning("⚠️ Using fallback session due to error")
    else:
        # Update session activity if it exists in database
        try:
            session_manager.update_session_activity(session['session_id'])
        except psycopg2.DatabaseError as db_error:
            app_logger.warning(f"⚠️ Database error updating session activity: {db_error}")
            # Continue without updating - not critical
        except Exception as e:
            # If session update fails, it might not exist in DB, try to recreate it
            app_logger.warning(f"⚠️ Session update failed: {e}")
            try:
                session_id = session_manager.create_session()
                session['session_id'] = session_id
                session['current_conversation_id'] = None
                app_logger.info(f"🔄 Recreated session: {session_id}")
            except Exception as create_error:
                app_logger.error(f"❌ Failed to recreate session: {create_error}")
                # Keep existing session ID as fallback
                pass


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
        system_prompt = """You are a caring, empathetic customer support assistant for raqibtech.com, a Nigerian e-commerce platform.
        Your goal is to genuinely help customers feel heard and supported.

        Platform context:
        - raqibtech.com: Nigerian e-commerce serving all 36 states + FCT
        - Payment methods: Pay on Delivery, Bank Transfer, Card, RaqibTechPay
        - Currency: Nigerian Naira (₦)

        Your communication style:
        - Be genuinely empathetic - acknowledge their feelings first
        - Keep responses concise (2-4 sentences max)
        - Show you truly care about their experience
        - Use warm, authentic Nigerian tone
        - Focus on solving their immediate need
        - Avoid overwhelming them with too much information

        Remember: You're helping a real person with real concerns. Lead with empathy, be brief and helpful.
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
            max_tokens=300,  # Reduced for more concise responses
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


# Initialize Enhanced Database Querying system
enhanced_db = EnhancedDatabaseQuerying()
app_logger.info("Enhanced Database Querying system initialized")

# 🆕 Initialize new systems
recommendation_engine = ProductRecommendationEngine()
order_management = OrderManagementSystem()
app_logger.info("✅ Recommendation Engine and Order Management systems initialized")

# Initialize enhanced customer support recommendation engine
if ENHANCED_SUPPORT_AVAILABLE:
    try:
        support_recommendation_engine = CustomerSupportRecommendationEngine()
        app_logger.info("✅ Enhanced CustomerSupportRecommendationEngine initialized")
    except Exception as e:
        app_logger.error(f"❌ Error initializing CustomerSupportRecommendationEngine: {e}")
        support_recommendation_engine = None
        ENHANCED_SUPPORT_AVAILABLE = False
else:
    support_recommendation_engine = None

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
            user_email = session.get('customer_email')

            if user_email:
                # 🔧 FIX: Get conversations by email for authenticated users to maintain history across sessions
                conversations = session_manager.get_user_conversations_by_email(user_email)

                # 🔧 FIX: Link the most recent conversation to current session for seamless experience
                if conversations:
                    session_manager.link_conversations_to_current_session(user_email, session['session_id'])

                    # Set the most recent conversation as current if none is set
                    if not session.get('current_conversation_id'):
                        session['current_conversation_id'] = conversations[0].conversation_id
                        current_conversation_id = conversations[0].conversation_id
                        app_logger.info(f"🔄 Set most recent conversation as current: {current_conversation_id}")
                else:
                    # Create a default conversation if none exists for authenticated users
                    try:
                        conversation_id = session_manager.create_conversation(session['session_id'], "New Chat")
                        session['current_conversation_id'] = conversation_id
                        current_conversation_id = conversation_id
                        conversations = session_manager.get_user_conversations_by_email(user_email)
                        app_logger.info(f"✅ Created first conversation for user: {conversation_id}")
                    except Exception as conv_error:
                        app_logger.warning(f"⚠️ Failed to create default conversation: {conv_error}")
                        conversations = []
                        session['current_conversation_id'] = None

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


def parse_order_intent(query: str) -> Dict[str, Any]:
    """🛒 Parse order intent from user query using Groq LLaMA"""
    try:
        # Enhanced order intent parsing prompt
        order_parsing_prompt = f"""
        You are an expert Nigerian e-commerce order assistant. Parse this customer query for order intent:

        Query: "{query}"

        Extract and return ONLY a JSON object with these fields:
        {{
            "has_order_intent": true/false,
            "product_mentioned": "product name or null",
            "quantity": number or null,
            "location": "Nigerian state mentioned or null",
            "payment_preference": "Pay on Delivery/Bank Transfer/Card/RaqibTechPay or null",
            "urgency": "low/medium/high",
            "order_type": "new_order/inquiry/complaint/null"
        }}

        Examples:
        - "I want to order a laptop" → {{"has_order_intent": true, "product_mentioned": "laptop", "quantity": 1, "location": null, "payment_preference": null, "urgency": "medium", "order_type": "new_order"}}
        - "Order 2 phones to Lagos" → {{"has_order_intent": true, "product_mentioned": "phones", "quantity": 2, "location": "Lagos", "payment_preference": null, "urgency": "medium", "order_type": "new_order"}}
        - "What's the price of iPhone?" → {{"has_order_intent": false, "product_mentioned": "iPhone", "quantity": null, "location": null, "payment_preference": null, "urgency": "low", "order_type": "inquiry"}}
        """

        completion = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": order_parsing_prompt}],
            temperature=0.1,
            max_tokens=200
        )

        response_text = completion.choices[0].message.content.strip()

        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        # Fallback parsing
        return {
            "has_order_intent": any(word in query.lower() for word in ['order', 'buy', 'purchase', 'get me']),
            "product_mentioned": None,
            "quantity": 1,
            "location": None,
            "payment_preference": None,
            "urgency": "medium",
            "order_type": "inquiry"
        }

    except Exception as e:
        app_logger.warning(f"⚠️ Order intent parsing failed: {e}")
        return {
            "has_order_intent": any(word in query.lower() for word in ['order', 'buy', 'purchase']),
            "product_mentioned": None,
            "quantity": 1,
            "location": None,
            "payment_preference": None,
            "urgency": "medium",
            "order_type": "inquiry"
        }

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Enhanced AI Chat API endpoint with order intent recognition"""
    try:
        data = request.json
        query = data.get('message', '').strip()
        user_id = session.get('user_id', 'anonymous')
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not query:
            return jsonify({'success': False, 'message': 'Message is required'}), 400

        # 🛒 NEW: Parse order intent first
        order_intent = parse_order_intent(query)

        context = ""
        quick_actions = []

        # Handle order-related queries with enhanced logic
        if order_intent.get('has_order_intent'):
            if customer_id:
                # Get customer info for personalized response
                customer = customer_repo.get_customer_by_id(customer_id)
                if customer:
                    context += f"Customer: {customer['name']} ({customer['account_tier']} tier) from {customer['state']}\n"

                    # Add tier-specific benefits to context
                    tier_benefits = {
                        'Bronze': '0% discount',
                        'Silver': '5% discount',
                        'Gold': '10% discount + free delivery',
                        'Platinum': '15% discount + premium perks'
                    }
                    context += f"Tier benefits: {tier_benefits.get(customer['account_tier'], 'Standard')}\n"

            # Add product search if product mentioned
            if order_intent.get('product_mentioned'):
                # This would integrate with your product search
                context += f"Product inquiry: {order_intent['product_mentioned']}\n"
                quick_actions.extend([
                    {'text': f"Search {order_intent['product_mentioned']}", 'action': 'search_product', 'data': {'product': order_intent['product_mentioned']}},
                    {'text': 'Check Availability', 'action': 'check_stock', 'data': {'product': order_intent['product_mentioned']}}
                ])

            # Add order-specific quick actions
            if order_intent['order_type'] == 'new_order':
                quick_actions.extend([
                    {'text': '🛒 Start Order', 'action': 'start_order', 'data': order_intent},
                    {'text': '💰 Check Prices', 'action': 'check_prices'},
                    {'text': '📍 Delivery Info', 'action': 'delivery_info'}
                ])

            context += f"Order intent: {safe_json_dumps(order_intent)}\n"

        # Extract context based on query intent (existing logic enhanced)
        if any(word in query.lower() for word in ['customer', 'customers', 'profile']):
            search_term = ""
            state = ""
            for state_name in NIGERIAN_STATES:
                if state_name.lower() in query.lower():
                    state = state_name
                    break
            customers = customer_repo.get_customers_by_state(state) if state else customer_repo.search_customers(search_term)[:5]
            context += f"Recent customers: {safe_json_dumps(customers[:3])}\n"

        if any(word in query.lower() for word in ['order', 'orders', 'payment', 'delivery']):
            orders = order_repo.get_order_summary()[:5]
            context += f"Recent orders: {safe_json_dumps(orders)}\n"

        if any(word in query.lower() for word in ['analytics', 'revenue', 'sales', 'metrics']):
            revenue_data = order_repo.get_revenue_by_state()[:5]
            context += f"Revenue by state: {safe_json_dumps(revenue_data)}\n"

        # Search vector database for additional context
        vector_results = search_vector_database(query)
        if vector_results:
            context += f"Related information: {safe_json_dumps(vector_results[:2])}\n"

        # Generate AI response with enhanced context
        ai_response = get_ai_response(query, context, user_id)

        # Add general quick actions if none were added
        if not quick_actions:
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
            'order_intent': order_intent,
            'customer_authenticated': bool(customer_id),
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

        # 🆕 Product-related quick action handlers
        elif action == 'browse_products':
            response = "🏪 Browse our amazing product catalog! We have Electronics, Fashion, Beauty, Computing, Automotive, and Books. Which category interests you?"

        elif action == 'check_prices':
            response = "💰 Check our competitive prices! Products range from budget-friendly ₦3,500 to premium ₦2,850,000. What price range are you looking for?"

        elif action == 'browse_electronics':
            response = "📱 Our Electronics section features Samsung, Apple, Tecno, Infinix smartphones, laptops, TVs, and home appliances. What electronics are you interested in?"

        elif action == 'browse_fashion':
            response = "👗 Explore our Fashion collection! From beautiful Ankara dresses to Nike sneakers, traditional wear to modern styles. What fashion items can I help you find?"

        elif action == 'check_inventory':
            response = "📦 I can check stock levels for any product! Our inventory includes thousands of items across all categories. Which product would you like me to check?"

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
    """Enhanced query API using the new EnhancedDatabaseQuerying system"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()

        if not user_query:
            return jsonify({
                'success': False,
                'message': 'Query is required'
            }), 400

        # 🔧 CRITICAL FIX: Build proper session context for authentication with RBAC
        session_context = {
            'user_authenticated': session.get('user_authenticated', False),
            'customer_verified': session.get('user_authenticated', False),  # 🔧 FIX: Use correct key
            'customer_id': session.get('customer_id'),  # 🔧 FIX: Use authenticated customer_id
            'customer_name': session.get('customer_name', 'valued customer'),
            'customer_email': session.get('customer_email'),
            'user_role': session.get('user_role', 'guest'),  # 🆕 RBAC: User role
            'is_staff': session.get('is_staff', False),      # 🆕 RBAC: Staff status
            'is_admin': session.get('is_admin', False),      # 🆕 RBAC: Admin status
            'user_id': session.get('user_id', 'anonymous'),
            'session_id': session.get('session_id')
        }

        # 🔧 DEBUG: Log session context for troubleshooting
        app_logger.info(f"🔍 Session context: user_authenticated={session_context['user_authenticated']}, customer_id={session_context['customer_id']}, user_role={session_context['user_role']}, is_staff={session_context['is_staff']}")

        # Process the query with session context
        result = enhanced_db.process_enhanced_query(user_query, session_context)

        # Store message in chat if we have a conversation
        conversation_id = session.get('current_conversation_id')
        if conversation_id:
            try:
                # Add user message
                session_manager.add_message(
                    conversation_id=conversation_id,
                    content=user_query,
                    sender_type='user',
                    metadata={}
                )

                # 🏷️ Update conversation title if this is the first user message (ChatGPT-style)
                session_manager.update_conversation_title_if_new(conversation_id, user_query)

                # Add AI response
                ai_metadata = {
                    'query_type': result.get('query_type'),
                    'execution_time': result.get('execution_time'),
                    'results_count': result.get('results_count'),
                    'sql_query': result.get('sql_query')
                }

                session_manager.add_message(
                    conversation_id=conversation_id,
                    content=result.get('response', 'Sorry, I encountered an issue.'),
                    sender_type='ai',
                    metadata=ai_metadata
                )

            except Exception as msg_error:
                app_logger.error(f"❌ Message storage error: {msg_error}")

        # Update session with current conversation if needed
        if not conversation_id and session.get('user_authenticated'):
            try:
                # 🏷️ Create new conversation with intelligent title generation
                intelligent_title = session_manager.generate_conversation_title(user_query)
                new_conversation_id = session_manager.create_conversation(
                    session_id=session['session_id'],
                    title=intelligent_title
                )
                session['current_conversation_id'] = new_conversation_id
                app_logger.info(f"✅ Created new conversation: {new_conversation_id} with title: '{intelligent_title}'")

                # Add messages to new conversation
                session_manager.add_message(
                    conversation_id=new_conversation_id,
                    content=user_query,
                    sender_type='user',
                    metadata={}
                )

                ai_metadata = {
                    'query_type': result.get('query_type'),
                    'execution_time': result.get('execution_time'),
                    'results_count': result.get('results_count'),
                    'sql_query': result.get('sql_query')
                }

                session_manager.add_message(
                    conversation_id=new_conversation_id,
                    content=result.get('response', 'Sorry, I encountered an issue.'),
                    sender_type='ai',
                    metadata=ai_metadata
                )

            except Exception as conv_error:
                app_logger.error(f"❌ Conversation creation error: {conv_error}")

        # Log successful query processing
        app_logger.info(f"Enhanced query processed: {result.get('query_type')} - {result.get('execution_time')}")

        return jsonify(result)

    except Exception as e:
        app_logger.error(f"❌ Enhanced query API error: {e}")
        return jsonify({
            'success': False,
            'message': 'Query processing failed. Please try again.',
            'error': str(e)
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
            # 🆕 Product-related suggestions
            'product_performance': [
                "Show me electronics products",
                "What fashion items do you have?",
                "Browse beauty products",
                "Check Samsung phone prices",
                "Show me laptops under ₦500,000",
                "What books are available?",
                "Search for Nike products",
                "Check automotive accessories",
                "Show products in stock",
                "What are your cheapest products?"
            ],
            'product_search': [
                "Search for iPhone",
                "Show me Tecno phones",
                "Find Ankara dresses",
                "Look for HP laptops",
                "Search MAC cosmetics",
                "Find car batteries",
                "Show me African novels",
                "Search for Adidas shoes"
            ],
            'inventory_queries': [
                "Check stock for product #123",
                "What products are out of stock?",
                "Show low stock items",
                "Check availability of Samsung Galaxy",
                "Is this product in stock?",
                "Show inventory by category"
            ],
            'general': [
                "Help me track my order",
                "Update my account details",
                "Check my payment status",
                "What products do you recommend?",
                "How do I contact customer service?",
                "Browse your product catalog",
                "Show me popular products",
                "Check prices for electronics"
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
    """Get user conversations - supports both authenticated and guest users"""
    try:
        # 🔧 CRITICAL FIX: Support both authenticated and guest users
        if session.get('user_authenticated', False):
            # Authenticated user - use email-based lookup
            user_email = session.get('customer_email')
            if not user_email:
                return jsonify({
                    'success': True,
                    'conversations': [],
                    'message': 'User email not found in session'
                })

            conversations = session_manager.get_user_conversations_by_email(user_email)
            app_logger.info(f"🔍 Retrieved {len(conversations)} conversations for authenticated user {user_email}")
        else:
            # Guest user - use session-based lookup
            session_id = session.get('session_id')
            if not session_id:
                return jsonify({
                    'success': True,
                    'conversations': [],
                    'message': 'No session found'
                })

            conversations = session_manager.get_user_conversations(session_id)
            app_logger.info(f"🔍 Retrieved {len(conversations)} conversations for guest session {session_id}")

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
    """Get messages for a specific conversation - supports both authenticated and guest users"""
    try:
        # 🔧 CRITICAL FIX: Support both authenticated and guest users
        if session.get('user_authenticated', False):
            # Authenticated user - verify by email
            user_email = session.get('customer_email')
            if not user_email:
                return jsonify({
                    'success': False,
                    'message': 'User email not found in session'
                }), 401

            user_conversations = session_manager.get_user_conversations_by_email(user_email)
            conversation_belongs_to_user = any(conv.conversation_id == conversation_id for conv in user_conversations)

            if not conversation_belongs_to_user:
                app_logger.warning(f"🚨 Unauthorized conversation access attempt: User {user_email} tried to access conversation {conversation_id}")
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found or access denied'
                }), 403

            app_logger.info(f"✅ Authenticated user {user_email} accessing conversation {conversation_id}")
        else:
            # Guest user - verify by session
            session_id = session.get('session_id')
            if not session_id:
                return jsonify({
                    'success': False,
                    'message': 'No session found'
                }), 401

            user_conversations = session_manager.get_user_conversations(session_id)
            conversation_belongs_to_user = any(conv.conversation_id == conversation_id for conv in user_conversations)

            if not conversation_belongs_to_user:
                app_logger.warning(f"🚨 Unauthorized conversation access attempt: Guest session {session_id} tried to access conversation {conversation_id}")
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found or access denied'
                }), 403

            app_logger.info(f"✅ Guest session {session_id} accessing conversation {conversation_id}")

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
    """Create a new conversation - supports both authenticated and guest users"""
    try:
        # 🔧 CRITICAL FIX: Support both authenticated and guest users
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'No session found'
            }), 401

        conversation_id = session_manager.create_conversation(session_id)
        session['current_conversation_id'] = conversation_id

        if session.get('user_authenticated', False):
            app_logger.info(f"✅ Created new conversation {conversation_id} for authenticated user {session.get('customer_email')}")
        else:
            app_logger.info(f"✅ Created new conversation {conversation_id} for guest session {session_id}")

        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        })

    except Exception as e:
        app_logger.error(f"❌ Error creating conversation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/conversations/<conversation_id>/switch', methods=['POST'])
def switch_conversation(conversation_id):
    """Switch to a specific conversation - supports both authenticated and guest users"""
    try:
        # 🔧 CRITICAL FIX: Support both authenticated and guest users
        if session.get('user_authenticated', False):
            # Authenticated user - verify by email
            user_email = session.get('customer_email')
            if not user_email:
                return jsonify({
                    'success': False,
                    'message': 'User email not found in session'
                }), 401

            user_conversations = session_manager.get_user_conversations_by_email(user_email)
            conversation_belongs_to_user = any(conv.conversation_id == conversation_id for conv in user_conversations)

            if not conversation_belongs_to_user:
                app_logger.warning(f"🚨 Unauthorized conversation switch attempt: User {user_email} tried to switch to conversation {conversation_id}")
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found or access denied'
                }), 403

            app_logger.info(f"🔄 Authenticated user {user_email} switching to conversation: {conversation_id}")
        else:
            # Guest user - verify by session
            session_id = session.get('session_id')
            if not session_id:
                return jsonify({
                    'success': False,
                    'message': 'No session found'
                }), 401

            user_conversations = session_manager.get_user_conversations(session_id)
            conversation_belongs_to_user = any(conv.conversation_id == conversation_id for conv in user_conversations)

            if not conversation_belongs_to_user:
                app_logger.warning(f"🚨 Unauthorized conversation switch attempt: Guest session {session_id} tried to switch to conversation {conversation_id}")
                return jsonify({
                    'success': False,
                    'message': 'Conversation not found or access denied'
                }), 403

            app_logger.info(f"🔄 Guest session {session_id} switching to conversation: {conversation_id}")

        # Update session
        session['current_conversation_id'] = conversation_id

        return jsonify({
            'success': True,
            'message': f'Switched to conversation {conversation_id}',
            'conversation_id': conversation_id
        })

    except Exception as e:
        app_logger.error(f"❌ Error switching conversation: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to switch conversation'
        }), 500


@app.route('/login')
def login_page():
    """Simple login page"""
    # Provide default stats to prevent template errors
    default_stats = {'total_customers': 0, 'total_orders': 0, 'pending_orders': 0, 'active_conversations': 0}
    return render_template('login.html', stats=default_stats)


@app.route('/api/login', methods=['POST'])
def login_api():
    """Handle user login with comprehensive database error handling"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400

        # Database connection for authentication
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        try:
            # Step 1: Verify customer exists and get RBAC information
            cursor.execute("""
                SELECT customer_id, name, email, user_role, is_staff, is_admin, account_status
                FROM customers
                WHERE email = %s
            """, (email,))
            customer = cursor.fetchone()

            if not customer:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Email not found in our system. Please check your email address or contact support.'
                }), 401

            customer_id, customer_name, customer_email, user_role, is_staff, is_admin, account_status = customer

            # Check account status
            if account_status != 'active':
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'Account is {account_status}. Please contact support.'
                }), 401
            current_session_id = session.get('session_id')  # Get current Flask session_id

            if not current_session_id:
                current_session_id = str(uuid.uuid4())

            # Create session data with RBAC information
            session_data = {
                'customer_id': customer_id,
                'customer_name': customer_name,
                'customer_email': customer_email,
                'user_role': user_role,
                'is_staff': is_staff,
                'is_admin': is_admin,
                'authenticated': True,
                'login_time': datetime.now().isoformat()
            }

            # Step 2: Handle session management carefully to avoid constraint violations
            try:
                # Check if user already has a session
                cursor.execute("SELECT session_id FROM user_sessions WHERE user_identifier = %s", (email,))
                existing_user_session = cursor.fetchone()

                if existing_user_session:
                    # User already has a session - just update the session data, keep same session_id
                    existing_session_id = existing_user_session[0]
                    cursor.execute("""
                        UPDATE user_sessions
                        SET last_active = CURRENT_TIMESTAMP,
                            session_data = %s
                        WHERE user_identifier = %s
                        RETURNING session_id
                    """, (json.dumps(session_data), email))

                    result = cursor.fetchone()
                    if result:
                        authenticated_session_id = result[0]
                        app_logger.info(f"✅ Updated existing user session for {email}")
                    else:
                        raise Exception("Failed to update existing user session")

                else:
                    # No existing user session - check if current session exists
                    cursor.execute("SELECT session_id, user_identifier FROM user_sessions WHERE session_id = %s", (current_session_id,))
                    current_session = cursor.fetchone()

                    if current_session:
                        # Current session exists - update it with user authentication
                        cursor.execute("""
                            UPDATE user_sessions
                            SET user_identifier = %s,
                                last_active = CURRENT_TIMESTAMP,
                                session_data = %s
                            WHERE session_id = %s
                            RETURNING session_id
                        """, (email, json.dumps(session_data), current_session_id))

                        result = cursor.fetchone()
                        if result:
                            authenticated_session_id = result[0]
                            app_logger.info(f"✅ Updated current session {current_session_id} with user authentication")
                        else:
                            raise Exception("Failed to update current session")

                    else:
                        # No session exists - create new one
                        cursor.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, created_at, last_active, session_data)
                            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s)
                            RETURNING session_id
                        """, (current_session_id, email, json.dumps(session_data)))

                        result = cursor.fetchone()
                        if result:
                            authenticated_session_id = result[0]
                            app_logger.info(f"✅ Created new session {current_session_id} for user {email}")
                        else:
                            raise Exception("Failed to create new session")

                # Step 3: Commit the transaction
                conn.commit()
                app_logger.info(f"✅ Session authenticated for user: {email} -> customer_id: {customer_id}")

            except psycopg2.IntegrityError as ie:
                conn.rollback()
                app_logger.error(f"❌ Database integrity error during login: {ie}")
                return jsonify({
                    'success': False,
                    'message': 'Login failed due to data integrity issue. Please try again.'
                }), 500

            except psycopg2.OperationalError as oe:
                conn.rollback()
                app_logger.error(f"❌ Database operational error during login: {oe}")
                return jsonify({
                    'success': False,
                    'message': 'Database connection issue. Please try again.'
                }), 500

            except Exception as session_error:
                conn.rollback()
                app_logger.error(f"❌ Session management error: {session_error}")
                return jsonify({
                    'success': False,
                    'message': 'Session setup failed. Please try again.'
                }), 500

        finally:
            cursor.close()
            conn.close()

        # Step 4: Update Flask session with RBAC information
        session['user_authenticated'] = True
        session['customer_id'] = customer_id
        session['customer_name'] = customer_name
        session['customer_email'] = customer_email
        session['user_role'] = user_role
        session['is_staff'] = is_staff
        session['is_admin'] = is_admin
        session['session_id'] = authenticated_session_id
        session['user_id'] = f"customer_{customer_id}"

        # Clear any conversation contamination
        session.pop('current_conversation_id', None)

        # Step 5: Link existing conversations safely
        try:
            session_manager.link_conversations_to_current_session(email, authenticated_session_id)
            app_logger.info(f"🔗 Linked existing conversations to current session for {email}")
        except Exception as link_error:
            app_logger.warning(f"⚠️ Failed to link conversations: {link_error}")
            # Don't fail login for conversation linking issues

        app_logger.info(f"✅ User authenticated successfully: {customer_name} (ID: {customer_id}) - {email}")

        return jsonify({
            'success': True,
            'message': f'Welcome back, {customer_name}!',
            'customer_name': customer_name,
            'customer_id': customer_id,
            'redirect': '/'
        })

    except psycopg2.DatabaseError as db_error:
        app_logger.error(f"❌ Database error during login: {db_error}")
        return jsonify({
            'success': False,
            'message': 'Database service temporarily unavailable. Please try again.'
        }), 500

    except psycopg2.Error as pg_error:
        app_logger.error(f"❌ PostgreSQL error during login: {pg_error}")
        return jsonify({
            'success': False,
            'message': 'Authentication service error. Please try again.'
        }), 500

    except Exception as e:
        app_logger.error(f"❌ Unexpected login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Login failed. Please try again.'
        }), 500


@app.route('/logout')
def logout():
    """Handle user logout with complete session cleanup"""
    try:
        # 🔧 FIX: Log current session before clearing
        current_user = session.get('customer_name', 'Unknown')
        customer_id = session.get('customer_id', 'Unknown')
        session_id = session.get('session_id')
        app_logger.info(f"🚪 User logging out: {current_user} (ID: {customer_id})")

        # 🔧 CRITICAL FIX: Clear conversation context from AI memory system
        if session_id and enhanced_db:
            try:
                # Clear the conversation memory for this session
                if hasattr(enhanced_db, 'memory_system') and enhanced_db.memory_system:
                    enhanced_db.memory_system.clear_session_context(session_id)
                    app_logger.info(f"🧠 Cleared AI conversation memory for session: {session_id}")
            except Exception as memory_clear_error:
                app_logger.error(f"❌ Error clearing AI memory: {memory_clear_error}")

        # 🔧 CRITICAL FIX: Clear database conversation context
        try:
            # Clear conversation context from database to prevent leakage
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'oracle'),
            }

            import psycopg2
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()

            # Clear conversation context for this customer to prevent leakage
            if customer_id and customer_id != 'Unknown':
                cursor.execute("DELETE FROM conversation_context WHERE user_id = %s", (f"customer_{customer_id}",))
                deleted_contexts = cursor.rowcount
                app_logger.info(f"🗂️ Cleared {deleted_contexts} conversation contexts for customer {customer_id}")

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as db_clear_error:
            app_logger.error(f"❌ Error clearing database conversation context: {db_clear_error}")

        # 🔧 FIX: Clear ALL session data to prevent contamination
        session.clear()

        # 🔧 FIX: Create fresh anonymous session
        session['session_id'] = str(uuid.uuid4())
        session['user_authenticated'] = False
        session['user_id'] = 'anonymous'

        app_logger.info(f"✅ Session cleared - new anonymous session: {session['session_id']}")

        return redirect('/')

    except Exception as e:
        app_logger.error(f"❌ Logout error: {e}")
        # Force clear session even on error
        session.clear()
        session['session_id'] = str(uuid.uuid4())
        session['user_authenticated'] = False
        return redirect('/')


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


# 🆕 ADD: Delete conversation endpoint with proper authorization
@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a specific conversation and all its messages - WITH AUTHORIZATION CHECK"""
    try:
        # 🔧 CRITICAL SECURITY FIX: Only authenticated users can delete conversations
        if not session.get('user_authenticated', False):
            return jsonify({
                'success': False,
                'message': 'Please log in to delete conversations'
            }), 401

        user_email = session.get('customer_email')
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'User email not found in session'
            }), 401

        # 🔧 CRITICAL SECURITY FIX: Verify the conversation belongs to the current user
        user_conversations = session_manager.get_user_conversations_by_email(user_email)
        conversation_belongs_to_user = any(conv.conversation_id == conversation_id for conv in user_conversations)

        if not conversation_belongs_to_user:
            app_logger.warning(f"🚨 Unauthorized conversation deletion attempt: User {user_email} tried to delete conversation {conversation_id}")
            return jsonify({
                'success': False,
                'message': 'Conversation not found or access denied'
            }), 403

        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # First, delete all messages in the conversation
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = %s", (conversation_id,))
        messages_deleted = cursor.rowcount

        # Then, delete the conversation itself
        cursor.execute("DELETE FROM chat_conversations WHERE conversation_id = %s", (conversation_id,))
        conversation_deleted = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        # If this was the current conversation, clear it from session
        if session.get('current_conversation_id') == conversation_id:
            session.pop('current_conversation_id', None)

        app_logger.info(f"✅ User {user_email} deleted conversation {conversation_id}: {messages_deleted} messages, {conversation_deleted} conversation")

        return jsonify({
            'success': True,
            'message': f'Conversation deleted successfully',
            'messages_deleted': messages_deleted,
            'conversation_deleted': conversation_deleted
        })

    except Exception as e:
        app_logger.error(f"❌ Error deleting conversation {conversation_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete conversation',
            'error': str(e)
        }), 500


@app.route('/signup')
def signup_page():
    """Sign-up page for new customer registration"""
    # Provide default stats to prevent template errors
    default_stats = {'total_customers': 0, 'total_orders': 0, 'pending_orders': 0, 'active_conversations': 0}
    return render_template('signup.html', stats=default_stats)


@app.route('/api/signup', methods=['POST'])
def signup_api():
    """Handle new customer registration with comprehensive validation and database integration"""
    try:
        data = request.get_json()

        # Extract and validate required fields
        full_name = data.get('fullName', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        state = data.get('state', '').strip()
        lga = data.get('lga', '').strip()
        address = data.get('address', '').strip()
        preferences = data.get('preferences', [])

        # Validate required fields
        if not all([full_name, email, phone, state, lga, address]):
            return jsonify({
                'success': False,
                'message': 'All required fields must be filled'
            }), 400

        # Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address'
            }), 400

        # Validate Nigerian phone format
        phone_clean = re.sub(r'\s+', '', phone)
        nigerian_phone_regex = r'^(\+234|0)[7-9][0-1]\d{8}$'
        if not re.match(nigerian_phone_regex, phone_clean):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid Nigerian phone number (e.g., +234 802 123 4567 or 08021234567)'
            }), 400

        # Database connection for registration
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        try:
            # Check if email already exists
            cursor.execute("SELECT customer_id FROM customers WHERE email = %s", (email,))
            existing_customer = cursor.fetchone()

            if existing_customer:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'An account with this email address already exists. Please try logging in instead.'
                }), 409

            # Prepare preferences JSON
            preferences_json = json.dumps({
                'categories': preferences,
                'language': 'English',
                'notifications': True,
                'newsletter': True
            }) if preferences else json.dumps({
                'language': 'English',
                'notifications': True,
                'newsletter': True
            })

            # Insert new customer (customer_id will be auto-generated by SERIAL)
            cursor.execute("""
                INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING customer_id
            """, (full_name, email, phone, state, lga, address, 'Bronze', preferences_json))

            result = cursor.fetchone()
            if not result:
                raise Exception("Failed to create customer account")

            new_customer_id = result[0]
            conn.commit()

            app_logger.info(f"✅ New customer registered: ID {new_customer_id}, Email: {email}")

            # Automatically log in the new user (following the same pattern as login)
            current_session_id = session.get('session_id')
            if not current_session_id:
                current_session_id = str(uuid.uuid4())

            # Create session data for new user
            session_data = {
                'customer_id': new_customer_id,
                'customer_name': full_name,
                'customer_email': email,
                'authenticated': True,
                'login_time': datetime.now().isoformat(),
                'registration_time': datetime.now().isoformat()
            }

            # Handle session management (same logic as login)
            try:
                # Check if there's an existing session for this user (shouldn't be, but safety check)
                cursor.execute("SELECT session_id FROM user_sessions WHERE user_identifier = %s", (email,))
                existing_user_session = cursor.fetchone()

                if existing_user_session:
                    # Update existing session (rare case)
                    cursor.execute("""
                        UPDATE user_sessions
                        SET last_active = CURRENT_TIMESTAMP,
                            session_data = %s
                        WHERE user_identifier = %s
                        RETURNING session_id
                    """, (json.dumps(session_data), email))

                    authenticated_session_id = cursor.fetchone()[0]
                    app_logger.info(f"✅ Updated existing session for new user {email}")

                else:
                    # Check if current session exists
                    cursor.execute("SELECT session_id, user_identifier FROM user_sessions WHERE session_id = %s", (current_session_id,))
                    current_session = cursor.fetchone()

                    if current_session:
                        # Update current session with new user authentication
                        cursor.execute("""
                            UPDATE user_sessions
                            SET user_identifier = %s,
                                last_active = CURRENT_TIMESTAMP,
                                session_data = %s
                            WHERE session_id = %s
                            RETURNING session_id
                        """, (email, json.dumps(session_data), current_session_id))

                        authenticated_session_id = cursor.fetchone()[0]
                        app_logger.info(f"✅ Updated current session with new user registration")

                    else:
                        # Create new session
                        cursor.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, created_at, last_active, session_data)
                            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s)
                            RETURNING session_id
                        """, (current_session_id, email, json.dumps(session_data)))

                        authenticated_session_id = cursor.fetchone()[0]
                        app_logger.info(f"✅ Created new session for registered user {email}")

                conn.commit()

                # Update Flask session
                session['session_id'] = authenticated_session_id
                session['user_authenticated'] = True
                session['user_email'] = email
                session['customer_id'] = new_customer_id
                session['customer_name'] = full_name

                cursor.close()
                conn.close()

                # 📧 Send welcome email to new customer
                if email_service:
                    try:
                        customer_data = {
                            'name': full_name,
                            'customer_id': new_customer_id,
                            'email': email,
                            'account_tier': 'Bronze',
                            'state': state,
                            'lga': lga
                        }

                        email_sent = email_service.send_welcome_email(customer_data)
                        if email_sent:
                            app_logger.info(f"✅ Welcome email sent to {email}")
                        else:
                            app_logger.warning(f"⚠️ Failed to send welcome email to {email}")
                    except Exception as email_error:
                        app_logger.error(f"❌ Welcome email error for {email}: {email_error}")

                return jsonify({
                    'success': True,
                    'message': f'Welcome to raqibtech.com, {full_name}! Your account has been created successfully.',
                    'customer_id': new_customer_id,
                    'account_tier': 'Bronze',
                    'redirect': '/'
                })

            except Exception as session_error:
                app_logger.error(f"❌ Session creation error for new user {email}: {session_error}")

                # 🔧 CRITICAL FIX: Clean up any orphaned sessions for this email on error
                try:
                    cursor.execute("DELETE FROM user_sessions WHERE user_identifier = %s", (email,))
                    orphaned_count = cursor.rowcount
                    if orphaned_count > 0:
                        app_logger.info(f"🧹 Cleaned up {orphaned_count} orphaned sessions for {email}")
                    conn.commit()
                except Exception as cleanup_error:
                    app_logger.warning(f"⚠️ Failed to cleanup orphaned sessions: {cleanup_error}")

                # Even if session fails, customer is created, so we can still return success
                cursor.close()
                conn.close()
                return jsonify({
                    'success': True,
                    'message': f'Account created successfully! Customer ID: {new_customer_id}. Please log in to continue.',
                    'customer_id': new_customer_id,
                    'account_tier': 'Bronze',
                    'redirect': '/login'
                })

        except Exception as db_error:
            conn.rollback()

            # 🔧 CRITICAL FIX: Clean up any potential session contamination on database error
            email = data.get('email', '').strip().lower() if data else None
            if email:
                try:
                    cursor.execute("DELETE FROM user_sessions WHERE user_identifier = %s", (email,))
                    orphaned_count = cursor.rowcount
                    if orphaned_count > 0:
                        app_logger.info(f"🧹 Cleaned up {orphaned_count} contaminated sessions for failed DB registration: {email}")
                    conn.commit()
                except Exception as cleanup_error:
                    app_logger.warning(f"⚠️ Failed to cleanup sessions after DB error: {cleanup_error}")

            cursor.close()
            conn.close()
            app_logger.error(f"❌ Database error during registration for {email}: {db_error}")
            return jsonify({
                'success': False,
                'message': 'Registration failed due to a system error. Please try again later.'
            }), 500

    except Exception as e:
        # 🔧 CRITICAL FIX: Prevent session contamination on any signup error
        email = data.get('email', '').strip().lower() if data else None
        app_logger.error(f"❌ Registration API error for {email}: {e}")

        if email:
            try:
                # Clear Flask session for failed registration
                session.pop('user_authenticated', None)
                session.pop('customer_id', None)
                session.pop('customer_email', None)
                session.pop('customer_name', None)
                session.pop('current_conversation_id', None)

                app_logger.info(f"🧹 Cleared Flask session for failed registration: {email}")
            except Exception as clear_error:
                app_logger.warning(f"⚠️ Failed to clear Flask session: {clear_error}")

        return jsonify({
            'success': False,
            'message': 'Registration failed. Please check your information and try again.'
        }), 500


# 🆕 ================================
# SHOPPING & ORDER MANAGEMENT ENDPOINTS
# ================================

@app.route('/api/products/search', methods=['POST'])
def search_products():
    """🔍 Smart product search with personalization"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        category = data.get('category', '')
        max_price = data.get('max_price')
        limit = data.get('limit', 20)

        # Get customer ID from session for personalization
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        # Search products
        products = recommendation_engine.search_products(
            query=query,
            customer_id=customer_id,
            category=category if category else None,
            max_price=max_price,
            limit=limit
        )

        # Convert RecommendationResult objects to dict
        products_data = []
        for product in products:
            products_data.append({
                'product_id': product.product_id,
                'product_name': product.product_name,
                'category': product.category,
                'brand': product.brand,
                'price': product.price,
                'price_formatted': product.price_formatted,
                'description': product.description,
                'stock_quantity': product.stock_quantity,
                'stock_status': product.stock_status,
                'recommendation_score': product.recommendation_score,
                'recommendation_reason': product.recommendation_reason
            })

        return jsonify({
            'success': True,
            'products': products_data,
            'total_found': len(products_data),
            'search_query': query,
            'personalized': customer_id is not None
        })

    except Exception as e:
        app_logger.error(f"❌ Product search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to search products',
            'message': str(e)
        }), 500


@app.route('/api/products/recommendations', methods=['POST'])
def get_product_recommendations():
    """🎯 Get personalized product recommendations"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for personalized recommendations',
                'message': 'Please log in to get personalized recommendations'
            }), 401

        # Get comprehensive recommendations
        recommendations = recommendation_engine.get_comprehensive_recommendations(
            customer_id=customer_id,
            limit=20
        )

        # Convert to JSON-serializable format
        rec_data = {}
        for category, products in recommendations.items():
            rec_data[category] = []
            for product in products:
                rec_data[category].append({
                    'product_id': product.product_id,
                    'product_name': product.product_name,
                    'category': product.category,
                    'brand': product.brand,
                    'price': product.price,
                    'price_formatted': product.price_formatted,
                    'description': product.description,
                    'stock_quantity': product.stock_quantity,
                    'stock_status': product.stock_status,
                    'recommendation_score': product.recommendation_score,
                    'recommendation_reason': product.recommendation_reason,
                    'recommendation_type': product.recommendation_type.value,
                    'customer_tier_discount': product.customer_tier_discount
                })

        return jsonify({
            'success': True,
            'recommendations': rec_data,
            'customer_id': customer_id,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        app_logger.error(f"❌ Recommendations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate recommendations',
            'message': str(e)
        }), 500


@app.route('/api/orders/calculate', methods=['POST'])
def calculate_order_totals():
    """💰 Calculate order totals before placement"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for order calculation',
                'message': 'Please log in to calculate order totals'
            }), 401

        items = data.get('items', [])
        delivery_state = data.get('delivery_state', 'Lagos')  # Default to Lagos

        if not items:
            return jsonify({
                'success': False,
                'error': 'No items provided for calculation'
            }), 400

        # Calculate order totals
        calculation = order_management.calculate_order_totals(
            items=items,
            customer_id=customer_id,
            delivery_state=delivery_state
        )

        if not calculation['success']:
            return jsonify(calculation), 400

        # Convert OrderItem objects to dict for JSON serialization
        items_data = []
        for item in calculation['order_items']:
            items_data.append({
                'product_id': item.product_id,
                'product_name': item.product_name,
                'category': item.category,
                'brand': item.brand,
                'price': item.price,
                'quantity': item.quantity,
                'subtotal': item.subtotal,
                'availability_status': item.availability_status
            })

        calculation['order_items'] = items_data

        return jsonify(calculation)

    except Exception as e:
        app_logger.error(f"❌ Order calculation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate order totals',
            'message': str(e)
        }), 500


@app.route('/api/delivery-fee', methods=['POST'])
def calculate_delivery_fee():
    """🚚 Standardized delivery fee calculation endpoint"""
    try:
        data = request.get_json()
        state = data.get('state', 'Lagos')
        weight_kg = data.get('weight_kg', 1.0)
        order_value = data.get('order_value', 0)

        # Use the order management system's delivery calculator
        from src.order_management import NigerianDeliveryCalculator

        delivery_fee, delivery_days, delivery_zone = NigerianDeliveryCalculator.calculate_delivery_fee(
            state, weight_kg, order_value
        )

        return jsonify({
            'success': True,
            'delivery_fee': delivery_fee,
            'delivery_days': delivery_days,
            'delivery_zone': delivery_zone,
            'state': state,
            'weight_kg': weight_kg,
            'message': f'Delivery to {state}: ₦{delivery_fee:,.2f} ({delivery_days} days)'
        })

    except Exception as e:
        app_logger.error(f"❌ Delivery fee calculation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate delivery fee',
            'message': str(e)
        }), 500


@app.route('/api/orders/place', methods=['POST'])
def place_order():
    """🛒 Place a new order"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for order placement',
                'message': 'Please log in to place an order'
            }), 401

        # Extract order data
        items = data.get('items', [])
        delivery_address = data.get('delivery_address', {})
        payment_method = data.get('payment_method', 'Pay on Delivery')

        # Validate required fields
        if not items:
            return jsonify({
                'success': False,
                'error': 'No items provided for order'
            }), 400

        required_address_fields = ['state', 'lga', 'full_address']
        for field in required_address_fields:
            if not delivery_address.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required address field: {field}'
                }), 400

        # Create order
        order_result = order_management.create_order(
            customer_id=customer_id,
            items=items,
            delivery_address=delivery_address,
            payment_method=payment_method
        )

        if not order_result['success']:
            return jsonify(order_result), 400

        # Convert OrderSummary to dict for JSON serialization
        order_summary = order_result['order_summary']
        order_data = {
            'order_id': order_summary.order_id,
            'customer_id': order_summary.customer_id,
            'customer_name': order_summary.customer_name,
            'subtotal': order_summary.subtotal,
            'delivery_fee': order_summary.delivery_fee,
            'tier_discount': order_summary.tier_discount,
            'tax_amount': order_summary.tax_amount,
            'total_amount': order_summary.total_amount,
            'payment_method': order_summary.payment_method.value,
            'order_status': order_summary.order_status.value,
            'created_at': order_summary.created_at.isoformat(),
            'estimated_delivery': order_summary.estimated_delivery.isoformat(),
            'delivery_info': {
                'state': order_summary.delivery_info.state,
                'lga': order_summary.delivery_info.lga,
                'full_address': order_summary.delivery_info.full_address,
                'delivery_fee': order_summary.delivery_info.delivery_fee,
                'estimated_delivery_days': order_summary.delivery_info.estimated_delivery_days,
                'delivery_zone': order_summary.delivery_info.delivery_zone
            },
            'items': []
        }

        # Add items data
        for item in order_summary.items:
            order_data['items'].append({
                'product_id': item.product_id,
                'product_name': item.product_name,
                'category': item.category,
                'brand': item.brand,
                'price': item.price,
                'quantity': item.quantity,
                'subtotal': item.subtotal,
                'availability_status': item.availability_status
            })

        return jsonify({
            'success': True,
            'order': order_data,
            'message': order_result['message']
        })

    except Exception as e:
        app_logger.error(f"❌ Order placement error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to place order',
            'message': str(e)
        }), 500


@app.route('/api/orders/status/<order_id>', methods=['GET'])
def get_order_status(order_id):
    """📦 Get order status and tracking information"""
    try:
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        # Get order status
        order_result = order_management.get_order_status(
            order_id=order_id,
            customer_id=customer_id
        )

        if not order_result['success']:
            return jsonify(order_result), 404 if 'not found' in order_result.get('error', '').lower() else 500

        return jsonify(order_result)

    except Exception as e:
        app_logger.error(f"❌ Order status error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve order status',
            'message': str(e)
        }), 500


@app.route('/api/orders/my-orders', methods=['GET'])
def get_my_orders():
    """📋 Get customer's order history"""
    try:
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to view your orders'
            }), 401

        limit = request.args.get('limit', 20, type=int)

        # Get customer orders
        orders_result = order_management.get_customer_orders(
            customer_id=customer_id,
            limit=limit
        )

        return jsonify(orders_result)

    except Exception as e:
        app_logger.error(f"❌ Customer orders error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve orders',
            'message': str(e)
        }), 500


@app.route('/api/orders/cancel/<order_id>', methods=['POST'])
def cancel_order(order_id):
    """❌ Cancel an order"""
    try:
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to cancel orders'
            }), 401

        data = request.get_json()
        reason = data.get('reason', '') if data else ''

        # Cancel order
        cancel_result = order_management.cancel_order(
            order_id=order_id,
            customer_id=customer_id,
            reason=reason
        )

        if not cancel_result['success']:
            return jsonify(cancel_result), 400

        return jsonify(cancel_result)

    except Exception as e:
        app_logger.error(f"❌ Order cancellation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel order',
            'message': str(e)
        }), 500


@app.route('/api/products/check-availability', methods=['POST'])
def check_product_availability():
    """🔍 Check product availability and stock"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400

        # Check availability
        availability = order_management.check_product_availability(
            product_id=product_id,
            requested_quantity=quantity
        )

        return jsonify(availability)

    except Exception as e:
        app_logger.error(f"❌ Product availability error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to check product availability',
            'message': str(e)
        }), 500


@app.route('/api/support/recommendations', methods=['POST'])
def get_support_recommendations():
    """🎯 Get intelligent customer support recommendations"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for personalized support recommendations',
                'message': 'Please log in to get personalized support assistance'
            }), 401

        # Extract request parameters
        support_query = data.get('support_query', '')
        scenario = data.get('scenario', 'general_browsing')
        customer_mood = data.get('customer_mood', 'neutral')
        conversation_history = data.get('conversation_history', [])
        current_products = data.get('current_products', [])
        cart_items = data.get('cart_items', [])
        budget_range = data.get('budget_range')
        urgency_level = data.get('urgency_level', 'medium')
        preferred_categories = data.get('preferred_categories', [])

        if not support_query:
            return jsonify({
                'success': False,
                'error': 'Support query is required',
                'message': 'Please provide your support question or request'
            }), 400

        # Use enhanced support engine if available
        if ENHANCED_SUPPORT_AVAILABLE and support_recommendation_engine:
            try:
                # Convert scenario string to enum
                scenario_enum = None
                try:
                    scenario_enum = SupportScenario(scenario)
                except ValueError:
                    scenario_enum = SupportScenario.GENERAL_BROWSING

                # Create support request
                support_request = SupportRecommendationRequest(
                    customer_id=customer_id,
                    support_query=support_query,
                    scenario=scenario_enum,
                    customer_mood=customer_mood,
                    conversation_history=conversation_history,
                    current_products=current_products,
                    cart_items=cart_items,
                    budget_range=tuple(budget_range) if budget_range and len(budget_range) == 2 else None,
                    urgency_level=urgency_level,
                    preferred_categories=preferred_categories,
                    session_context=dict(session)
                )

                # Get enhanced recommendations
                support_response = support_recommendation_engine.get_support_recommendations(support_request)

                return jsonify({
                    'success': True,
                    'support_recommendations': {
                        'recommendations': support_response.recommendations,
                        'primary_message': support_response.primary_message,
                        'secondary_message': support_response.secondary_message,
                        'call_to_action': support_response.call_to_action,
                        'confidence_score': support_response.confidence_score,
                        'recommendation_reasoning': support_response.recommendation_reasoning,
                        'total_recommendations': support_response.total_recommendations,
                        'estimated_satisfaction_impact': support_response.estimated_satisfaction_impact,
                        'next_best_actions': support_response.next_best_actions
                    },
                    'scenario': scenario,
                    'customer_mood': customer_mood,
                    'enhanced_support': True,
                    'generated_at': datetime.now().isoformat()
                })

            except Exception as e:
                app_logger.error(f"❌ Enhanced support recommendations error: {e}")
                # Fallback to basic recommendations
                pass

        # Fallback to basic recommendations using existing engine
        try:
            basic_recommendations = recommendation_engine.get_comprehensive_recommendations(
                customer_id=customer_id, limit=15)

            return jsonify({
                'success': True,
                'support_recommendations': {
                    'recommendations': basic_recommendations,
                    'primary_message': "I'd be happy to help you find exactly what you need.",
                    'secondary_message': f"Here are some personalized recommendations based on your preferences.",
                    'call_to_action': "Which of these products interests you most?",
                    'confidence_score': 0.7,
                    'recommendation_reasoning': ["Based on your purchase history", "Popular among similar customers"],
                    'total_recommendations': sum(len(recs) for recs in basic_recommendations.values()),
                    'estimated_satisfaction_impact': "medium",
                    'next_best_actions': ["Ask about specific products", "Add items to cart", "Get more details"]
                },
                'scenario': scenario,
                'customer_mood': customer_mood,
                'enhanced_support': False,
                'generated_at': datetime.now().isoformat()
            })

        except Exception as e:
            app_logger.error(f"❌ Basic support recommendations error: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate support recommendations',
                'message': 'Unable to provide recommendations at this time. Please try again.'
            }), 500

    except Exception as e:
        app_logger.error(f"❌ Support recommendations endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Support recommendations service unavailable',
            'message': str(e)
        }), 500


@app.route('/api/support/context-analysis', methods=['POST'])
def analyze_support_context():
    """🧠 Analyze customer support context for intelligent assistance"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        support_query = data.get('support_query', '')
        conversation_history = data.get('conversation_history', [])

        if not support_query:
            return jsonify({
                'success': False,
                'error': 'Support query is required for context analysis'
            }), 400

        # Analyze context using enhanced DB querying
        try:
            context_analysis = db_querying.analyze_customer_support_context(support_query, customer_id)

            if hasattr(context_analysis, '__dict__'):
                context_data = {
                    'support_query': context_analysis.support_query,
                    'support_category': context_analysis.support_category,
                    'customer_mood': context_analysis.customer_mood,
                    'conversation_stage': context_analysis.conversation_stage,
                    'mentioned_products': context_analysis.mentioned_products,
                    'problem_category': context_analysis.problem_category,
                    'resolution_priority': context_analysis.resolution_priority
                }
            else:
                context_data = context_analysis

            # Get suggested scenarios based on context
            suggested_scenarios = []
            if context_data.get('support_category') == 'product_issue':
                suggested_scenarios = ['troubleshooting', 'satisfaction_recovery', 'return_exchange']
            elif context_data.get('support_category') == 'order_problem':
                suggested_scenarios = ['order_assistance', 'satisfaction_recovery']
            elif context_data.get('customer_mood') == 'frustrated':
                suggested_scenarios = ['satisfaction_recovery', 'troubleshooting']
            elif context_data.get('customer_mood') == 'curious':
                suggested_scenarios = ['product_inquiry', 'product_comparison', 'general_browsing']
            else:
                suggested_scenarios = ['general_browsing', 'product_inquiry']

            return jsonify({
                'success': True,
                'context_analysis': context_data,
                'suggested_scenarios': suggested_scenarios,
                'recommended_approach': {
                    'urgency_level': 'high' if context_data.get('resolution_priority') == 'high' else 'medium',
                    'response_tone': 'empathetic' if context_data.get('customer_mood') == 'frustrated' else 'helpful',
                    'focus_areas': context_data.get('mentioned_products', []) + [context_data.get('problem_category', 'general')]
                },
                'generated_at': datetime.now().isoformat()
            })

        except Exception as e:
            app_logger.error(f"❌ Context analysis error: {e}")

            # Fallback basic analysis
            basic_analysis = {
                'support_query': support_query,
                'support_category': 'general_inquiry',
                'customer_mood': 'neutral',
                'conversation_stage': 'initial',
                'mentioned_products': [],
                'problem_category': 'general',
                'resolution_priority': 'medium'
            }

            return jsonify({
                'success': True,
                'context_analysis': basic_analysis,
                'suggested_scenarios': ['general_browsing'],
                'recommended_approach': {
                    'urgency_level': 'medium',
                    'response_tone': 'helpful',
                    'focus_areas': ['general']
                },
                'fallback_used': True,
                'generated_at': datetime.now().isoformat()
            })

    except Exception as e:
        app_logger.error(f"❌ Support context analysis endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Context analysis service unavailable',
            'message': str(e)
        }), 500


@app.route('/api/support/cross-sell', methods=['POST'])
def get_cross_sell_recommendations():
    """🛒 Get cross-sell recommendations for customer support"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for cross-sell recommendations'
            }), 401

        current_product_id = data.get('current_product_id')
        cart_items = data.get('cart_items', [])
        limit = data.get('limit', 8)

        # Get cross-sell recommendations
        cross_sell_recs = recommendation_engine.get_cross_sell_recommendations(
            customer_id=customer_id,
            current_product_id=current_product_id,
            cart_items=cart_items,
            limit=limit
        )

        # Convert to JSON-serializable format
        recommendations_data = []
        for rec in cross_sell_recs:
            recommendations_data.append({
                'product_id': rec.product_id,
                'product_name': rec.product_name,
                'category': rec.category,
                'brand': rec.brand,
                'price': rec.price,
                'price_formatted': rec.price_formatted,
                'description': rec.description,
                'stock_quantity': rec.stock_quantity,
                'stock_status': rec.stock_status,
                'recommendation_score': rec.recommendation_score,
                'recommendation_reason': rec.recommendation_reason,
                'recommendation_type': rec.recommendation_type.value
            })

        return jsonify({
            'success': True,
            'cross_sell_recommendations': recommendations_data,
            'total_recommendations': len(recommendations_data),
            'customer_id': customer_id,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        app_logger.error(f"❌ Cross-sell recommendations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate cross-sell recommendations',
            'message': str(e)
        }), 500


@app.route('/api/support/upsell', methods=['POST'])
def get_upsell_recommendations():
    """⬆️ Get upsell recommendations for customer support"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for upsell recommendations'
            }), 401

        current_product_id = data.get('current_product_id')
        current_price = data.get('current_price')
        limit = data.get('limit', 6)

        # Get upsell recommendations
        upsell_recs = recommendation_engine.get_upsell_recommendations(
            customer_id=customer_id,
            current_product_id=current_product_id,
            current_price=current_price,
            limit=limit
        )

        # Convert to JSON-serializable format
        recommendations_data = []
        for rec in upsell_recs:
            recommendations_data.append({
                'product_id': rec.product_id,
                'product_name': rec.product_name,
                'category': rec.category,
                'brand': rec.brand,
                'price': rec.price,
                'price_formatted': rec.price_formatted,
                'description': rec.description,
                'stock_quantity': rec.stock_quantity,
                'stock_status': rec.stock_status,
                'recommendation_score': rec.recommendation_score,
                'recommendation_reason': rec.recommendation_reason,
                'recommendation_type': rec.recommendation_type.value
            })

        return jsonify({
            'success': True,
            'upsell_recommendations': recommendations_data,
            'total_recommendations': len(recommendations_data),
            'customer_id': customer_id,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        app_logger.error(f"❌ Upsell recommendations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate upsell recommendations',
            'message': str(e)
        }), 500


@app.route('/api/support/cart-recovery', methods=['POST'])
def get_cart_recovery_recommendations():
    """🛒 Get cart abandonment recovery recommendations"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required for cart recovery recommendations'
            }), 401

        abandoned_items = data.get('abandoned_items', [])
        limit = data.get('limit', 8)

        # Get cart recovery recommendations
        recovery_recs = recommendation_engine.get_abandoned_cart_recommendations(
            customer_id=customer_id,
            abandoned_items=abandoned_items,
            limit=limit
        )

        # Convert to JSON-serializable format
        recommendations_data = []
        for rec in recovery_recs:
            recommendations_data.append({
                'product_id': rec.product_id,
                'product_name': rec.product_name,
                'category': rec.category,
                'brand': rec.brand,
                'price': rec.price,
                'price_formatted': rec.price_formatted,
                'description': rec.description,
                'stock_quantity': rec.stock_quantity,
                'stock_status': rec.stock_status,
                'recommendation_score': rec.recommendation_score,
                'recommendation_reason': rec.recommendation_reason,
                'recommendation_type': rec.recommendation_type.value
            })

        return jsonify({
            'success': True,
            'cart_recovery_recommendations': recommendations_data,
            'total_recommendations': len(recommendations_data),
            'customer_id': customer_id,
            'generated_at': datetime.now().isoformat()
        })

    except Exception as e:
        app_logger.error(f"❌ Cart recovery recommendations error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate cart recovery recommendations',
            'message': str(e)
        }), 500


@app.route('/api/orders/create', methods=['POST'])
def create_order_from_chat():
    """🛒 Create order from chatbot interaction with enhanced validation"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to place an order',
                'action_required': 'login'
            }), 401

        # Extract order data
        product_query = data.get('product_query', '')
        quantity = data.get('quantity', 1)
        delivery_state = data.get('delivery_state')
        payment_method = data.get('payment_method', 'Pay on Delivery')

        # Validate required fields
        if not product_query:
            return jsonify({
                'success': False,
                'error': 'Product information required',
                'message': 'Please specify what product you want to order'
            }), 400

        # Get customer info for state default
        customer = customer_repo.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found',
                'message': 'Unable to find your customer profile'
            }), 404

        # Use customer's state as default if not provided
        if not delivery_state:
            delivery_state = customer['state']

        # 🔍 Product search and matching (simplified for demo)
        # In a real implementation, this would search your product database
        mock_products = [
            {'product_id': 1, 'name': 'Samsung Galaxy A54', 'price': 285000, 'category': 'Electronics'},
            {'product_id': 2, 'name': 'iPhone 14', 'price': 850000, 'category': 'Electronics'},
            {'product_id': 3, 'name': 'HP Laptop', 'price': 450000, 'category': 'Computing'},
            {'product_id': 4, 'name': 'Nike Air Max', 'price': 65000, 'category': 'Fashion'},
            {'product_id': 5, 'name': 'Ankara Dress', 'price': 25000, 'category': 'Fashion'}
        ]

        # Simple product matching
        matched_product = None
        for product in mock_products:
            if any(word in product['name'].lower() for word in product_query.lower().split()):
                matched_product = product
                break

        if not matched_product:
            # Return product suggestions
            return jsonify({
                'success': False,
                'error': 'Product not found',
                'message': f"I couldn't find '{product_query}' in our catalog. Here are some suggestions:",
                'suggestions': mock_products[:3],
                'action_required': 'product_selection'
            }), 404

        # Calculate order totals
        items = [{
            'product_id': matched_product['product_id'],
            'quantity': quantity
        }]

        # Use existing order calculation logic
        order_calc = order_management.calculate_order_totals(
            items=items,
            customer_id=customer_id,
            delivery_state=delivery_state
        )

        if not order_calc['success']:
            return jsonify({
                'success': False,
                'error': 'Order calculation failed',
                'message': order_calc.get('error', 'Unable to calculate order total')
            }), 400

        # Apply tier discounts
        tier_discounts = {
            'Bronze': 0.0,
            'Silver': 0.05,
            'Gold': 0.10,
            'Platinum': 0.15
        }

        discount_rate = tier_discounts.get(customer['account_tier'], 0.0)
        subtotal = order_calc['subtotal']
        discount_amount = subtotal * discount_rate

        # Free delivery for Gold and Platinum
        delivery_fee = order_calc['delivery_fee']
        if customer['account_tier'] in ['Gold', 'Platinum']:
            delivery_fee = 0

        final_total = subtotal - discount_amount + delivery_fee

        # Prepare order summary for confirmation
        order_summary = {
            'product': matched_product,
            'quantity': quantity,
            'subtotal': subtotal,
            'discount_rate': discount_rate * 100,  # Convert to percentage
            'discount_amount': discount_amount,
            'delivery_fee': delivery_fee,
            'total_amount': final_total,
            'payment_method': payment_method,
            'delivery_state': delivery_state,
            'customer_tier': customer['account_tier'],
            'estimated_delivery_days': order_calc.get('delivery_days', 3)
        }

        return jsonify({
            'success': True,
            'order_summary': order_summary,
            'customer_info': {
                'name': customer['name'],
                'email': customer['email'],
                'state': customer['state'],
                'tier': customer['account_tier']
            },
            'message': f"Order ready for confirmation! Total: {format_currency(final_total)}",
            'action_required': 'confirmation'
        })

    except Exception as e:
        app_logger.error(f"❌ Order creation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Order creation failed',
            'message': str(e)
        }), 500

@app.route('/api/orders/confirm', methods=['POST'])
def confirm_order():
    """✅ Confirm and place the order"""
    try:
        data = request.get_json()
        customer_id = session.get('customer_id') if session.get('user_authenticated') else None

        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401

        # Extract confirmed order data
        order_data = data.get('order_data', {})
        delivery_address = data.get('delivery_address', {})

        # Get customer info
        customer = customer_repo.get_customer_by_id(customer_id)

        # Prepare delivery address
        if not delivery_address:
            delivery_address = {
                'state': customer['state'],
                'lga': customer.get('lga', 'Municipal'),
                'full_address': customer.get('address', f"{customer['state']}, Nigeria")
            }

        # Create the order using existing order management
        items = [{
            'product_id': order_data['product']['product_id'],
            'quantity': order_data['quantity']
        }]

        order_result = order_management.create_order(
            customer_id=customer_id,
            items=items,
            delivery_address=delivery_address,
            payment_method=order_data['payment_method']
        )

        if not order_result['success']:
            return jsonify(order_result), 400

        # Update order in database with correct total
        order_id = order_result['database_order_id']
        final_total = order_data['total_amount']

        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                UPDATE orders
                SET total_amount = %s, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = %s
            """, (final_total, order_id))

        # 📧 Send order confirmation email
        if email_service:
            try:
                # Prepare order data for email
                order_email_data = {
                    'customer_name': customer['name'],
                    'customer_email': customer['email'],
                    'order_id': order_result['order_id'],
                    'items': [{
                        'name': order_data['product']['name'],
                        'quantity': order_data['quantity'],
                        'unit_price': order_data['product']['price'],
                        'subtotal': order_data['subtotal']
                    }],
                    'subtotal': order_data['subtotal'],
                    'discount_amount': order_data.get('discount_amount', 0),
                    'discount_percentage': order_data.get('discount_rate', 0),
                    'delivery_fee': order_data.get('delivery_fee', 0),
                    'total_amount': final_total,
                    'account_tier': customer['account_tier'],
                    'delivery_state': delivery_address.get('state', customer['state']),
                    'delivery_lga': delivery_address.get('lga', customer.get('lga', '')),
                    'delivery_address': delivery_address.get('full_address', customer.get('address', '')),
                    'payment_method': order_data['payment_method'],
                    'order_status': 'Pending'
                }

                email_sent = email_service.send_order_confirmation_email(order_email_data)
                if email_sent:
                    app_logger.info(f"✅ Order confirmation email sent to {customer['email']} for order {order_result['order_id']}")
                else:
                    app_logger.warning(f"⚠️ Failed to send order confirmation email to {customer['email']}")
            except Exception as email_error:
                app_logger.error(f"❌ Order confirmation email error for {customer['email']}: {email_error}")

        return jsonify({
            'success': True,
            'order_id': order_result['order_id'],
            'message': f"🎉 Order {order_result['order_id']} confirmed! You'll receive SMS/email confirmation shortly.",
            'order_details': {
                'order_id': order_result['order_id'],
                'total_amount': final_total,
                'payment_method': order_data['payment_method'],
                'estimated_delivery': order_result['order_summary'].estimated_delivery.strftime('%B %d, %Y')
            }
        })

    except Exception as e:
        app_logger.error(f"❌ Order confirmation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Order confirmation failed',
            'message': str(e)
        }), 500


@app.route('/api/customer/profile', methods=['GET', 'PUT'])
def customer_profile_api():
    """🔐 Customer Profile API - Secure customer self-service for profile management"""
    try:
        # Check authentication
        if not session.get('user_authenticated'):
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to access your profile'
            }), 401

        customer_id = session.get('customer_id')
        if not customer_id:
            return jsonify({
                'success': False,
                'error': 'Customer ID not found',
                'message': 'Invalid session'
            }), 401

        # Database connection
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if request.method == 'GET':
            # Get customer profile information
            cursor.execute("""
                SELECT customer_id, name, email, phone, state, lga, address,
                       account_tier, created_at, user_role, account_status
                FROM customers
                WHERE customer_id = %s
            """, (customer_id,))

            profile = cursor.fetchone()
            cursor.close()
            conn.close()

            if not profile:
                return jsonify({
                    'success': False,
                    'error': 'Profile not found'
                }), 404

            # Convert to dict and format dates
            profile_data = dict(profile)
            if profile_data.get('created_at'):
                profile_data['member_since'] = profile_data['created_at'].strftime('%B %Y')
                profile_data['created_at'] = profile_data['created_at'].isoformat()

            # Get spending summary
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_amount), 0) as total_spent,
                    COUNT(CASE WHEN order_status IN ('Pending', 'Processing') THEN 1 END) as active_orders
                FROM orders
                WHERE customer_id = %s
            """, (customer_id,))

            spending_summary = cursor.fetchone()
            cursor.close()
            conn.close()

            if spending_summary:
                profile_data.update({
                    'total_orders': spending_summary['total_orders'],
                    'total_spent': float(spending_summary['total_spent']),
                    'total_spent_formatted': format_currency(float(spending_summary['total_spent'])),
                    'active_orders': spending_summary['active_orders']
                })

            return jsonify({
                'success': True,
                'profile': profile_data,
                'message': 'Profile loaded successfully'
            })

        elif request.method == 'PUT':
            # Update customer profile
            data = request.json

            # Define allowed fields that customers can update
            allowed_fields = {
                'name': str,
                'phone': str,
                'state': str,
                'lga': str,
                'address': str
            }

            # Validate and prepare updates
            updates = {}
            update_fields = []
            update_values = []

            for field, field_type in allowed_fields.items():
                if field in data:
                    value = data[field]
                    if isinstance(value, field_type) and value.strip():
                        updates[field] = value.strip()
                        update_fields.append(f"{field} = %s")
                        update_values.append(value.strip())

            if not updates:
                return jsonify({
                    'success': False,
                    'error': 'No valid fields to update',
                    'message': 'Please provide valid data to update'
                }), 400

            # Build update query
            update_query = f"""
                UPDATE customers
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s
                RETURNING customer_id, name, email, phone, state, lga, address, account_tier
            """
            update_values.append(customer_id)

            try:
                cursor.execute(update_query, update_values)
                updated_profile = cursor.fetchone()
                conn.commit()
                cursor.close()
                conn.close()

                if updated_profile:
                    app_logger.info(f"✅ Customer {customer_id} updated profile: {', '.join(updates.keys())}")

                    return jsonify({
                        'success': True,
                        'profile': dict(updated_profile),
                        'message': f'Profile updated successfully! Updated: {", ".join(updates.keys())}',
                        'updated_fields': list(updates.keys())
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Update failed',
                        'message': 'Could not update profile'
                    }), 400

            except Exception as e:
                conn.rollback()
                cursor.close()
                conn.close()
                error_logger.error(f"❌ Profile update error for customer {customer_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Update failed',
                    'message': 'An error occurred while updating your profile'
                }), 500

    except Exception as e:
        error_logger.error(f"❌ Customer profile API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': 'An error occurred while processing your request'
        }), 500


@app.route('/api/session/debug', methods=['GET'])
def debug_session():
    """Debug endpoint to check session state"""
    try:
        session_info = {
            'session_id': session.get('session_id'),
            'user_authenticated': session.get('user_authenticated', False),
            'customer_email': session.get('customer_email'),
            'customer_id': session.get('customer_id'),
            'current_conversation_id': session.get('current_conversation_id'),
            'session_permanent': session.permanent,
            'session_keys': list(session.keys()),
            'session_type': app.config.get('SESSION_TYPE'),
            'session_file_dir': app.config.get('SESSION_FILE_DIR'),
        }

        # Also check if session exists in database
        try:
            if session.get('session_id'):
                conversations = session_manager.get_user_conversations(session['session_id'])
                session_info['conversations_count'] = len(conversations)
                session_info['conversations'] = [{
                    'id': conv.conversation_id,
                    'title': conv.conversation_title,
                    'message_count': conv.message_count
                } for conv in conversations[:5]]  # Show first 5
            else:
                session_info['conversations_count'] = 0
                session_info['conversations'] = []
        except Exception as e:
            session_info['database_error'] = str(e)

        app_logger.info(f"🔍 Session debug info: {session_info}")

        return jsonify({
            'success': True,
            'session_info': session_info
        })

    except Exception as e:
        app_logger.error(f"❌ Session debug error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Initialize session
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
