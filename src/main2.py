import streamlit as st
from mem0 import Memory
import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from groq import Groq
import google.generativeai as genai
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from config.appconfig import (
    QDRANT_URL_CLOUD,
    QDRANT_URL_LOCAL,
    QDRANT_API_KEY,
    GROQ_API_KEY,
    GOOGLE_API_KEY,
)

#-----------------------------------------------------
# Configs
#-----------------------------------------------------
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
SYNTHETIC_DATA_MODEL = "gemini-2.0-flash"   # For generating customer profiles
CUSTOMER_CHAT_MODEL = "llama-3.1-8b-instant" # For handling customer conversations

# MODELS = {
#     "llama-3.3-70b-versatile",
#     "llama-3.1-8b-instant",
#     "llama3-70b-8192",
#     "gemini-2.5-flash-preview-04-17",
#     "gemini-2.0-flash"
# }
# streamlit cache clear

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Import logging configuration
from config.logging_config import setup_logging

# Initialize loggers
app_logger, api_logger, error_logger = setup_logging()

#-----------------------------------------------------
# Usage Tracking with Enhanced Gemini 2.0 Flash Quotas
#-----------------------------------------------------
class APIUsageTracker:
    def __init__(self):
        # Official Gemini 2.0 Flash quotas from Google Cloud documentation
        self.gemini_quotas = {
            "requests_per_minute": 1000,  # Default quota for gemini-2.0-flash
            "tokens_per_minute": 4000000,  # 4M tokens per minute
            "requests_per_day": 50000,     # Estimated daily limit
            "concurrent_requests": 100,    # Max concurrent requests
            "max_output_tokens": 8192,     # Max output tokens per request
            "max_input_tokens": 2097152,   # ~2M input tokens per request
        }

        # Groq quotas for comparison
        self.groq_quotas = {
            "requests_per_minute": 30,     # Groq free tier
            "tokens_per_minute": 100000,   # 100K tokens per minute
            "requests_per_day": 14400,     # Estimated daily limit
        }

        self.usage_data = {
            "google_api": {
                "total_requests": 0,
                "total_tokens": 0,
                "requests_today": 0,
                "tokens_today": 0,
                "requests_this_minute": 0,
                "tokens_this_minute": 0,
                "last_reset": datetime.now().date(),
                "last_minute_reset": datetime.now().replace(second=0, microsecond=0),
                "request_history": [],
                "peak_rpm": 0,  # Peak requests per minute
                "peak_tpm": 0,  # Peak tokens per minute
            },
            "groq_api": {
                "total_requests": 0,
                "total_tokens": 0,
                "requests_today": 0,
                "tokens_today": 0,
                "requests_this_minute": 0,
                "tokens_this_minute": 0,
                "last_reset": datetime.now().date(),
                "last_minute_reset": datetime.now().replace(second=0, microsecond=0),
                "request_history": [],
                "peak_rpm": 0,
                "peak_tpm": 0,
            }
        }

    def _reset_minute_counters(self, api_type):
        """Reset per-minute counters if a new minute has started"""
        current_minute = datetime.now().replace(second=0, microsecond=0)
        if current_minute != self.usage_data[api_type]["last_minute_reset"]:
            # Update peak values before reset
            self.usage_data[api_type]["peak_rpm"] = max(
                self.usage_data[api_type]["peak_rpm"],
                self.usage_data[api_type]["requests_this_minute"]
            )
            self.usage_data[api_type]["peak_tpm"] = max(
                self.usage_data[api_type]["peak_tpm"],
                self.usage_data[api_type]["tokens_this_minute"]
            )

            # Reset minute counters
            self.usage_data[api_type]["requests_this_minute"] = 0
            self.usage_data[api_type]["tokens_this_minute"] = 0
            self.usage_data[api_type]["last_minute_reset"] = current_minute

    def track_google_request(self, tokens_used=0, request_type="generation"):
        current_date = datetime.now().date()

        # Reset daily counters if new day
        if current_date != self.usage_data["google_api"]["last_reset"]:
            api_logger.info(f"🔄 Daily GOOGLE usage reset - Previous day: {self.usage_data['google_api']['requests_today']} requests, {self.usage_data['google_api']['tokens_today']} tokens")
            self.usage_data["google_api"]["requests_today"] = 0
            self.usage_data["google_api"]["tokens_today"] = 0
            self.usage_data["google_api"]["last_reset"] = current_date

        # Reset minute counters if needed
        self._reset_minute_counters("google_api")

        # Update all counters
        self.usage_data["google_api"]["total_requests"] += 1
        self.usage_data["google_api"]["total_tokens"] += tokens_used
        self.usage_data["google_api"]["requests_today"] += 1
        self.usage_data["google_api"]["tokens_today"] += tokens_used
        self.usage_data["google_api"]["requests_this_minute"] += 1
        self.usage_data["google_api"]["tokens_this_minute"] += tokens_used

        # Log API usage with quota context
        rpm_percentage = (self.usage_data["google_api"]["requests_this_minute"] / self.gemini_quotas["requests_per_minute"]) * 100
        tpm_percentage = (self.usage_data["google_api"]["tokens_this_minute"] / self.gemini_quotas["tokens_per_minute"]) * 100

        api_logger.info(f"📊 GOOGLE API Call - Type: {request_type}, Tokens: {tokens_used}, "
                       f"RPM: {self.usage_data['google_api']['requests_this_minute']}/{self.gemini_quotas['requests_per_minute']} ({rpm_percentage:.1f}%), "
                       f"TPM: {self.usage_data['google_api']['tokens_this_minute']}/{self.gemini_quotas['tokens_per_minute']} ({tpm_percentage:.1f}%)")

        # Add to history
        self.usage_data["google_api"]["request_history"].append({
            "timestamp": datetime.now(),
            "tokens": tokens_used,
            "type": request_type,
            "rpm_at_time": self.usage_data["google_api"]["requests_this_minute"],
            "tpm_at_time": self.usage_data["google_api"]["tokens_this_minute"]
        })

        # Keep only last 100 requests in history
        if len(self.usage_data["google_api"]["request_history"]) > 100:
            self.usage_data["google_api"]["request_history"] = \
                self.usage_data["google_api"]["request_history"][-100:]

        # Enhanced warning thresholds based on official quotas
        if self.usage_data["google_api"]["requests_this_minute"] >= self.gemini_quotas["requests_per_minute"] * 0.9:
            app_logger.warning(f"🚨 CRITICAL: Approaching Gemini RPM limit! {self.usage_data['google_api']['requests_this_minute']}/{self.gemini_quotas['requests_per_minute']}")
        elif self.usage_data["google_api"]["tokens_this_minute"] >= self.gemini_quotas["tokens_per_minute"] * 0.9:
            app_logger.warning(f"🚨 CRITICAL: Approaching Gemini TPM limit! {self.usage_data['google_api']['tokens_this_minute']}/{self.gemini_quotas['tokens_per_minute']}")
        elif self.usage_data["google_api"]["requests_today"] >= self.gemini_quotas["requests_per_day"] * 0.8:
            app_logger.warning(f"⚠️ High daily usage: {self.usage_data['google_api']['requests_today']}/{self.gemini_quotas['requests_per_day']} requests")

    def track_groq_request(self, tokens_used=0, request_type="customer_chat"):
        current_date = datetime.now().date()

        # Reset daily counters if new day
        if current_date != self.usage_data["groq_api"]["last_reset"]:
            api_logger.info(f"🔄 Daily GROQ usage reset - Previous day: {self.usage_data['groq_api']['requests_today']} requests, {self.usage_data['groq_api']['tokens_today']} tokens")
            self.usage_data["groq_api"]["requests_today"] = 0
            self.usage_data["groq_api"]["tokens_today"] = 0
            self.usage_data["groq_api"]["last_reset"] = current_date

        # Reset minute counters if needed
        self._reset_minute_counters("groq_api")

        # Update all counters
        self.usage_data["groq_api"]["total_requests"] += 1
        self.usage_data["groq_api"]["total_tokens"] += tokens_used
        self.usage_data["groq_api"]["requests_today"] += 1
        self.usage_data["groq_api"]["tokens_today"] += tokens_used
        self.usage_data["groq_api"]["requests_this_minute"] += 1
        self.usage_data["groq_api"]["tokens_this_minute"] += tokens_used

        # Log API usage with quota context
        rpm_percentage = (self.usage_data["groq_api"]["requests_this_minute"] / self.groq_quotas["requests_per_minute"]) * 100
        tpm_percentage = (self.usage_data["groq_api"]["tokens_this_minute"] / self.groq_quotas["tokens_per_minute"]) * 100

        api_logger.info(f"📊 GROQ API Call - Type: {request_type}, Tokens: {tokens_used}, "
                       f"RPM: {self.usage_data['groq_api']['requests_this_minute']}/{self.groq_quotas['requests_per_minute']} ({rpm_percentage:.1f}%), "
                       f"TPM: {self.usage_data['groq_api']['tokens_this_minute']}/{self.groq_quotas['tokens_per_minute']} ({tpm_percentage:.1f}%)")

        # Add to history
        self.usage_data["groq_api"]["request_history"].append({
            "timestamp": datetime.now(),
            "tokens": tokens_used,
            "type": request_type,
            "rpm_at_time": self.usage_data["groq_api"]["requests_this_minute"],
            "tpm_at_time": self.usage_data["groq_api"]["tokens_this_minute"]
        })

        # Keep only last 100 requests in history
        if len(self.usage_data["groq_api"]["request_history"]) > 100:
            self.usage_data["groq_api"]["request_history"] = \
                self.usage_data["groq_api"]["request_history"][-100:]

        # Warning thresholds for Groq
        if self.usage_data["groq_api"]["requests_this_minute"] >= self.groq_quotas["requests_per_minute"] * 0.9:
            app_logger.warning(f"🚨 CRITICAL: Approaching Groq RPM limit! {self.usage_data['groq_api']['requests_this_minute']}/{self.groq_quotas['requests_per_minute']}")
        elif self.usage_data["groq_api"]["tokens_this_minute"] >= self.groq_quotas["tokens_per_minute"] * 0.9:
            app_logger.warning(f"🚨 CRITICAL: Approaching Groq TPM limit! {self.usage_data['groq_api']['tokens_this_minute']}/{self.groq_quotas['tokens_per_minute']}")

    def get_usage_stats(self):
        return self.usage_data

    def get_quota_info(self):
        """Get detailed quota information for both APIs"""
        return {
            "gemini": self.gemini_quotas,
            "groq": self.groq_quotas
        }

    def estimate_cost(self):
        # Updated Gemini 2.0 Flash pricing (from Google Cloud documentation)
        # Input: $0.075 per 1M tokens
        # Output: $0.30 per 1M tokens
        # Assuming 50/50 split for estimation
        tokens = self.usage_data["google_api"]["total_tokens"]
        estimated_cost = (tokens / 1000000) * 0.1875  # Average of input/output
        return estimated_cost

    def get_quota_status(self):
        """Get current quota utilization status"""
        google_stats = self.usage_data["google_api"]
        groq_stats = self.usage_data["groq_api"]

        return {
            "gemini": {
                "rpm_usage": (google_stats["requests_this_minute"] / self.gemini_quotas["requests_per_minute"]) * 100,
                "tpm_usage": (google_stats["tokens_this_minute"] / self.gemini_quotas["tokens_per_minute"]) * 100,
                "daily_usage": (google_stats["requests_today"] / self.gemini_quotas["requests_per_day"]) * 100,
                "status": self._get_status_level(google_stats["requests_this_minute"], self.gemini_quotas["requests_per_minute"])
            },
            "groq": {
                "rpm_usage": (groq_stats["requests_this_minute"] / self.groq_quotas["requests_per_minute"]) * 100,
                "tpm_usage": (groq_stats["tokens_this_minute"] / self.groq_quotas["tokens_per_minute"]) * 100,
                "daily_usage": (groq_stats["requests_today"] / self.groq_quotas["requests_per_day"]) * 100,
                "status": self._get_status_level(groq_stats["requests_this_minute"], self.groq_quotas["requests_per_minute"])
            }
        }

    def _get_status_level(self, current, limit):
        """Get status level based on usage percentage"""
        percentage = (current / limit) * 100
        if percentage >= 90:
            return "critical"
        elif percentage >= 70:
            return "warning"
        elif percentage >= 50:
            return "moderate"
        else:
            return "healthy"

# Initialize usage tracker
@st.cache_resource
def get_usage_tracker():
    return APIUsageTracker()

usage_tracker = get_usage_tracker()

#--------------------------------------
# Streamlit App Initialization
#--------------------------------------
# Set page configuration
st.set_page_config(
    page_title="AI Customer Support Agent",
    page_icon="🗨️",
    layout="centered",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
        padding: 0.68rem;
        background: linear-gradient(135deg, #6C5CE7, #00B894);
        color: #F8F9FA;
        # box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        border-radius: 10px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    .sidebar-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1rem;
    }

    .card {
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
    }

    .metric-card {
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        padding: 1rem;
    }

    .chat-message {
        display: flex;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        align-items: flex-start;
    }

    .chat-message-user {
        border-left: 3px solid #9D86FF;
        background-color: rgba(157, 134, 255, 0.05);
    }

    .chat-message-assistant {
        border-left: 3px solid #FF4B4B;
        background-color: rgba(255, 75, 75, 0.05);
    }

    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }

    .source-card {
        padding: 0.5rem;
        border-radius: 5px;
        margin-top: 0.5rem;
    }

    .expander-header {
        font-weight: 600;
    }
    .stButton>button {
        background-color: #6C5CE7;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #574B90;
    }


    # .chat-container {
    #     display: flex;
    #     flex-direction: column;
    #     height: 65vh;
    #     overflow-y: auto;
    #     padding: 1rem;
    #     border-radius: 10px;
    #     margin-bottom: 1rem;
    #     border: 1px solid rgba(49, 51, 63, 0.2);
    # }

    .footer {
        margin-top: 2rem;
        padding-top: 1rem;
        text-align: center;
        font-size: 0.85rem;
    }

    .profile-card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(49, 51, 63, 0.2);
    }

    .profile-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }

    .profile-icon {
        font-size: 1.8rem;
        margin-right: 0.8rem;
    }

    .profile-name {
        font-size: 1.2rem;
        font-weight: 600;
    }

    .profile-section {
        margin-bottom: 1rem;
    }

    .profile-section-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding-bottom: 0.2rem;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
    }

    .profile-item {
        display: flex;
        margin-bottom: 0.3rem;
    }

    .profile-item-label {
        font-weight: 500;
        min-width: 120px;
    }

    .profile-order {
        padding: 0.8rem;
        border-radius: 5px;
        margin-bottom: 0.8rem;
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(49, 51, 63, 0.2);
    }

    .action-button {
        margin-right: 0.5rem;
    }

    .thinking-indicator {
        font-family: monospace;
        animation: blink 1s infinite;
    }

    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }

    .customer-profiles-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }

    .profile-card-compact {
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(49, 51, 63, 0.2);
        background-color: rgba(255, 255, 255, 0.05);
        height: 100%;
    }

    .profile-card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease;
        border-left: 4px solid #6C5CE7;
    }

    .profile-card-compact {
        padding: 1.25rem;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
        border: 1px solid #eee;
    }

    .profile-card-compact:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }

    # .customer-profiles-grid {
    #     display: grid;
    #     grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    #     gap: 1.5rem;
    #     margin-top: 1rem;
    # }
</style>
""", unsafe_allow_html=True)


st.markdown("<div class='main-header'>🤖 AI-Powered Customer Support Agent</div>", unsafe_allow_html=True)
st.markdown("""
<div class='card'>
    <p style='text-align: center;'>Chat with our intelligent support assistant who remembers your past interactions.</p>
</div>
""", unsafe_allow_html=True)

#--------------------------------------
# Session persistence
#--------------------------------------
@st.cache_resource
def get_persistent_state():
    """Return a persistent state object that will retain data across sessions."""
    return {
        "all_customer_data": {},
        "message_history": {},
        "active_customers": []
    }

# Initialize persistent state
persistent_state = get_persistent_state()


#--------------------------------------
# Enhanced Customer Support Agent - Unified System
#--------------------------------------
class CustomerSupportAIAgent:
    def test_qdrant_connection():
        try:
            client = QdrantClient(
                url=QDRANT_URL_LOCAL,
                timeout=10
            )
            collections = client.get_collections()
            app_logger.info(f"🔗 Qdrant connection successful! Collections: {collections}")
            return True
        except Exception as e:
            error_logger.error(f"❌ Qdrant connection failed: {e}")
            return False

    if test_qdrant_connection():
        app_logger.info("✅ Qdrant is ready!")
    else:
        app_logger.error("❌ Please start Qdrant first: docker run -p 6333:6333 qdrant/qdrant")

    def __init__(self, model_choice):
        # Initialize Mem0 with Qdrant as the vector store
        config = {
            "llm": {
                "provider": "litellm",
                "config": {
                    "model": "gemini/gemini-2.0-flash",
                    "temperature": 0.2,
                    "max_tokens": 1500,
                }
            },
            "embeddings": {
                "provider": "google",
                "model": GEMINI_EMBEDDING_MODEL,
                "api_key": GOOGLE_API_KEY,
                "params": {
                    "task_type": "RETRIEVAL_DOCUMENT"
                }
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333,
                }
            },
        }
        try:
            debug_config = config.copy()
            debug_config["llm"]["config"]["api_key"] = "***HIDDEN***"
            debug_config["embeddings"]["api_key"] = "***HIDDEN***"
            app_logger.info(f"🔧 Initializing Mem0 with config: {debug_config}")

            self.memory = Memory.from_config(config)
            app_logger.info("✅ Memory initialized successfully")
        except Exception as e:
            error_logger.error(f"❌ Memory initialization failed: {e}", exc_info=True)
            st.error(f"Failed to initialize memory: {e}")
            st.stop()

        self.model_choice = model_choice
        self.app_id = "customer-support"

    def get_all_customer_data(self):
        """Get all customer data from persistent state"""
        return persistent_state["all_customer_data"]

    def search_customers_by_criteria(self, criteria):
        """Search customers based on various criteria"""
        all_customers = self.get_all_customer_data()
        results = []

        criteria_lower = criteria.lower()

        for customer_id, customer_data in all_customers.items():
            customer_info = customer_data.get("customer_info", {})
            current_order = customer_data.get("current_order", {})
            order_history = customer_data.get("order_history", [])
            account = customer_data.get("account", {})

            # Search in various fields
            searchable_text = f"""
            {customer_info.get('name', '')} {customer_info.get('email', '')}
            {customer_info.get('phone', '')} {customer_info.get('state', '')}
            {current_order.get('order_id', '')} {current_order.get('delivery_method', '')}
            {current_order.get('payment_method', '')} {account.get('tier', '')}
            """.lower()

            # Check products in current order
            for product in current_order.get('products', []):
                searchable_text += f" {product.get('name', '')} {product.get('status', '')}"

            # Check order history
            for order in order_history:
                searchable_text += f" {order.get('order_id', '')} {order.get('items', '')} {order.get('status', '')}"

            if criteria_lower in searchable_text:
                results.append({
                    'customer_id': customer_id,
                    'customer_data': customer_data,
                    'relevance_score': searchable_text.count(criteria_lower)
                })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results

    def get_customer_analytics(self):
        """Generate analytics across all customers"""
        all_customers = self.get_all_customer_data()

        if not all_customers:
            return None

        analytics = {
            'total_customers': len(all_customers),
            'states_distribution': {},
            'tier_distribution': {},
            'payment_methods': {},
            'delivery_methods': {},
            'order_statuses': {},
            'pending_orders': [],
            'high_value_customers': [],
            'recent_orders': [],
            'total_revenue': 0
        }

        for customer_id, customer_data in all_customers.items():
            customer_info = customer_data.get("customer_info", {})
            current_order = customer_data.get("current_order", {})
            account = customer_data.get("account", {})

            # State distribution
            state = customer_info.get('state', 'Unknown')
            analytics['states_distribution'][state] = analytics['states_distribution'].get(state, 0) + 1

            # Tier distribution
            tier = account.get('tier', 'Unknown')
            analytics['tier_distribution'][tier] = analytics['tier_distribution'].get(tier, 0) + 1

            # Payment and delivery methods
            payment_method = current_order.get('payment_method', 'Unknown')
            delivery_method = current_order.get('delivery_method', 'Unknown')
            analytics['payment_methods'][payment_method] = analytics['payment_methods'].get(payment_method, 0) + 1
            analytics['delivery_methods'][delivery_method] = analytics['delivery_methods'].get(delivery_method, 0) + 1

            # Order status analysis
            for product in current_order.get('products', []):
                status = product.get('status', 'Unknown')
                analytics['order_statuses'][status] = analytics['order_statuses'].get(status, 0) + 1

                if status.lower() in ['processing', 'pending', 'shipped']:
                    analytics['pending_orders'].append({
                        'customer_id': customer_id,
                        'customer_name': customer_info.get('name', 'Unknown'),
                        'order_id': current_order.get('order_id', 'Unknown'),
                        'product': product.get('name', 'Unknown'),
                        'status': status
                    })

            # Revenue calculation (extract numeric value from total)
            total_str = current_order.get('total', '₦0')
            try:
                # Remove currency symbol and commas, then convert to float
                total_numeric = float(total_str.replace('₦', '').replace(',', ''))
                analytics['total_revenue'] += total_numeric

                # High value customers (orders > ₦100,000)
                if total_numeric > 100000:
                    analytics['high_value_customers'].append({
                        'customer_id': customer_id,
                        'customer_name': customer_info.get('name', 'Unknown'),
                        'order_value': total_str,
                        'tier': tier
                    })
            except:
                pass

            # Recent orders
            order_date = current_order.get('order_date', '')
            if order_date:
                analytics['recent_orders'].append({
                    'customer_id': customer_id,
                    'customer_name': customer_info.get('name', 'Unknown'),
                    'order_id': current_order.get('order_id', 'Unknown'),
                    'order_date': order_date,
                    'total': current_order.get('total', 'Unknown')
                })

        # Sort recent orders by date (most recent first)
        analytics['recent_orders'].sort(key=lambda x: x['order_date'], reverse=True)
        analytics['recent_orders'] = analytics['recent_orders'][:10]  # Top 10 recent

        return analytics

    def handle_unified_query(self, query):
        """Handle queries across all customer data with intelligent context awareness"""
        try:
            app_logger.info(f"💬 Processing unified support query: {query}")

            # Get all customer data for context
            all_customers = self.get_all_customer_data()
            analytics = self.get_customer_analytics()

            # Build comprehensive context
            context_parts = []

            # Add customer count and basic stats
            if analytics:
                context_parts.append(f"""
SYSTEM OVERVIEW:
- Total Customers: {analytics['total_customers']}
- Total Revenue: ₦{analytics['total_revenue']:,.2f}
- Pending Orders: {len(analytics['pending_orders'])}
- High Value Customers: {len(analytics['high_value_customers'])}
""")

            # Search for relevant customers based on query
            relevant_customers = self.search_customers_by_criteria(query)[:5]  # Top 5 most relevant

            if relevant_customers:
                context_parts.append("RELEVANT CUSTOMER DATA:")
                for result in relevant_customers:
                    customer_id = result['customer_id']
                    customer_data = result['customer_data']
                    customer_info = customer_data.get("customer_info", {})
                    current_order = customer_data.get("current_order", {})

                    context_parts.append(f"""
Customer ID: {customer_id}
Name: {customer_info.get('name', 'Unknown')}
Email: {customer_info.get('email', 'Unknown')}
State: {customer_info.get('state', 'Unknown')}
Current Order: {current_order.get('order_id', 'None')} - {current_order.get('total', 'Unknown')}
Order Status: {', '.join([p.get('status', 'Unknown') for p in current_order.get('products', [])])}
""")

            # Add analytics context if relevant
            if analytics and any(keyword in query.lower() for keyword in ['analytics', 'report', 'summary', 'overview', 'statistics']):
                context_parts.append(f"""
ANALYTICS SUMMARY:
- States: {', '.join([f"{k}: {v}" for k, v in list(analytics['states_distribution'].items())[:5]])}
- Tiers: {', '.join([f"{k}: {v}" for k, v in analytics['tier_distribution'].items()])}
- Payment Methods: {', '.join([f"{k}: {v}" for k, v in analytics['payment_methods'].items()])}
""")

            # Combine all context
            full_context = "\n".join(context_parts)

            # Create the prompt for the AI
            full_prompt = f"""You are a professional customer support agent for raqibtech.com, a Nigerian e-commerce platform.

AVAILABLE CUSTOMER DATA:
{full_context}

CUSTOMER SUPPORT QUERY: {query}

RESPONSE GUIDELINES:
1. Act as a knowledgeable support agent with access to all customer information
2. Provide specific, actionable responses based on the available data
3. If the query is about a specific customer/order, reference the exact details
4. For general queries, provide insights across all customers
5. Use Nigerian context and currency (₦) appropriately
6. Be professional, helpful, and concise
7. If you need to look up specific information not provided, mention what additional details would be helpful
8. For analytics queries, provide clear summaries and insights
9. Always maintain customer privacy - don't expose sensitive information unnecessarily

Respond as a helpful customer support agent:"""

            # Track API usage
            start_time = time.time()

            groq_client = Groq(api_key=GROQ_API_KEY)
            response = groq_client.chat.completions.create(
                model=CUSTOMER_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional customer support agent for raqibtech.com with access to comprehensive customer data. Provide helpful, accurate responses based on available information."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )

            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            usage_tracker.track_groq_request(tokens_used, "unified_support_query")
            elapsed_time = time.time() - start_time
            app_logger.info(f"💬 Unified support query processed - Tokens: {tokens_used}, Time: {elapsed_time:.2f}s")

            answer = response.choices[0].message.content

            # Store the interaction in memory for future reference
            self.memory.add(
                f"Query: {query}\nResponse: {answer}",
                user_id="support_agent",
                metadata={"app_id": self.app_id, "type": "unified_query"}
            )

            return answer, relevant_customers, analytics

        except Exception as e:
            error_logger.error(f"❌ Error in unified query handling: {e}", exc_info=True)
            return f"Sorry, I encountered an error while processing your query: {e}", [], None

    def get_customer_by_id(self, customer_id):
        """Get specific customer data by ID"""
        return persistent_state["all_customer_data"].get(customer_id)

    def get_orders_by_status(self, status):
        """Get all orders with a specific status"""
        all_customers = self.get_all_customer_data()
        orders = []

        for customer_id, customer_data in all_customers.items():
            current_order = customer_data.get("current_order", {})
            customer_info = customer_data.get("customer_info", {})

            for product in current_order.get('products', []):
                if product.get('status', '').lower() == status.lower():
                    orders.append({
                        'customer_id': customer_id,
                        'customer_name': customer_info.get('name', 'Unknown'),
                        'order_id': current_order.get('order_id', 'Unknown'),
                        'product': product.get('name', 'Unknown'),
                        'status': product.get('status', 'Unknown'),
                        'order_date': current_order.get('order_date', 'Unknown')
                    })

        return orders

    def generate_synthetic_data(self, user_id: str) -> dict | None:
        """Generate synthetic customer data (unchanged from original)"""
        try:
            app_logger.info(f"🔄 Starting synthetic data generation for user: {user_id}")
            today = datetime.now()
            order_date = (today - timedelta(days=10)).strftime("%B %d, %Y")
            expected_delivery = (today + timedelta(days=2)).strftime("%B %d, %Y")

            model = genai.GenerativeModel(SYNTHETIC_DATA_MODEL)
            app_logger.info(f"📝 Using Gemini model: {SYNTHETIC_DATA_MODEL}")

            prompt = f"""Generate a detailed UNIQUE Nigerian customer profile for raqibtech.com customer ID {user_id}.

            STRICT REQUIREMENTS:
            1. Create a COMPLETELY UNIQUE Nigerian full name that has NEVER been used before
            2. Ensure the name follows Nigerian naming conventions but is distinguishable from all previous customers
            3. The name must NOT match or resemble any existing names: {[data['customer_info']['name'] for data in persistent_state["all_customer_data"].values()]}

            Generate realistic profile with DETAILED ORDER INFORMATION:
            - Full Nigerian name (First + Last name from Yoruba/Igbo/Hausa/Edo/etc.)
            - Valid Nigerian address with specific street, area, city, and state
            - Nigerian phone number format (+234 or 080x format)
            - DETAILED order history with SPECIFIC REALISTIC PRODUCTS
            - Consistent pricing in Nigerian Naira
            - Appropriate payment methods common in Nigeria

            PRODUCT CATEGORIES TO USE (pick realistic items):
            Electronics: Samsung Galaxy phones, iPhone, HP laptops, Dell computers, LG TVs, Sony headphones
            Home & Kitchen: Rice cookers, blenders, microwaves, refrigerators, gas cookers
            Food Items: Indomie noodles, Golden Penny semovita, Peak milk, Maggi cubes, vegetable oil
            Fashion: Ankara fabrics, shoes, bags, watches, jewelry
            Beauty: skincare products, hair products, makeup, perfumes

            Format as JSON with this EXACT structure:
            {{
                "customer_info": {{
                    "name": "Full Nigerian name (e.g., 'Adebayo Okonkwo' or 'Fatima Abdullahi')",
                    "email": "realistic email with gmail.com or yahoo.com",
                    "shipping_address": "Specific address like '15 Adeniyi Jones Avenue, Ikeja, Lagos' or '23 Uselu-Lagos Road, Benin City, Edo'",
                    "phone": "Nigerian format like '+234 813 456 7890' or '0803-123-4567'",
                    "state": "Actual Nigerian state (Lagos, Abuja, Kano, Rivers, etc.)",
                    "lga": "Corresponding Local Government Area"
                }},
                "current_order": {{
                    "order_id": "JMT-NG-{user_id[-6:]}",
                    "order_date": "{order_date}",
                    "expected_delivery": "{expected_delivery}",
                    "delivery_method": "raqibtech Express OR PickUp Station OR Courier Service",
                    "payment_method": "Pay on Delivery OR Card Payment OR Bank Transfer OR RaqibTechPay",
                    "products": [
                        {{"name": "Specific product name with brand", "price": "₦XX,XXX", "quantity": 1, "status": "Processing"}},
                        {{"name": "Another specific product", "price": "₦XX,XXX", "quantity": 2, "status": "Processing"}}
                    ],
                    "shipping_fee": "₦2,500",
                    "total": "₦XX,XXX"
                }},
                "order_history": [
                    {{"order_id": "JMT-NG-{user_id[-6:].replace(user_id[-1], '1')}", "date": "2024-11-15", "items": "Samsung Galaxy A15, Phone case", "total": "₦185,000", "status": "Delivered"}},
                    {{"order_id": "JMT-NG-{user_id[-6:].replace(user_id[-1], '2')}", "date": "2024-09-22", "items": "HP Laptop 15-inch, Laptop bag", "total": "₦420,000", "status": "Delivered"}},
                    {{"order_id": "JMT-NG-{user_id[-6:].replace(user_id[-1], '3')}", "date": "2024-07-10", "items": "Indomie Noodles (carton), Peak Milk", "total": "₦12,500", "status": "Delivered"}}
                ],
                "account": {{
                    "member_since": "March 2024 OR June 2023 OR January 2024",
                    "tier": "Bronze OR Silver OR Gold OR Platinum",
                    "points": "realistic points number (500-5000)"
                }}
            }}

            RESPOND ONLY WITH VALID JSON. NO EXPLANATIONS OR MARKDOWN."""

            # Track API usage
            start_time = time.time()

            # Generate with Gemini
            full_prompt = f"""You are a Nigerian e-commerce data generator. Use authentic Nigerian formats, locations, and naming conventions.

            {prompt}"""

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    response_mime_type="application/json"
                )
            )

            # Track usage
            tokens_used = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            usage_tracker.track_google_request(tokens_used, "synthetic_data_generation")

            # Log usage
            elapsed_time = time.time() - start_time
            app_logger.info(f"🔍 Synthetic data generated - Tokens: {tokens_used}, Time: {elapsed_time:.2f}s, User: {user_id}")

            # Handle response
            raw_content = response.text

            # Remove markdown code blocks if present
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:-3]  # Remove ```json and trailing ```

            customer_data = json.loads(raw_content)

            # Add generated data to memory
            self.memory.add(
                json.dumps(customer_data),
                user_id=user_id,
                metadata={"app_id": self.app_id, "role": "system"}
            )

            # Store in persistent state
            persistent_state["all_customer_data"][user_id] = customer_data

            # Add to active customers if not already there
            if user_id not in persistent_state["active_customers"]:
                persistent_state["active_customers"].append(user_id)

            return customer_data

        except json.JSONDecodeError as e:
            error_logger.error(f"❌ JSON decode error for user {user_id}: {e}", exc_info=True)
            st.error(f"Invalid JSON response from model: {e}")
            return None
        except Exception as e:
            error_logger.error(f"❌ Failed to generate synthetic data for user {user_id}: {e}", exc_info=True)
            st.error(f"Failed to generate synthetic data: {e}")
            return None

# Initialize sidebar
st.sidebar.markdown("<div class='sidebar-header'>🔧 Settings</div>", unsafe_allow_html=True)
model_choice = "Groq"

# Add usage metrics in sidebar
st.sidebar.markdown("<div class='sidebar-header'>📊 API Usage Metrics</div>", unsafe_allow_html=True)

def display_usage_metrics():
    stats = usage_tracker.get_usage_stats()
    google_stats = stats["google_api"]
    groq_stats = stats.get("groq_api", {
    "total_requests": 0,
    "total_tokens": 0,
    "requests_today": 0,
    "tokens_today": 0,
    "requests_this_minute": 0,
    "tokens_this_minute": 0,
    "last_reset": None,
    "last_minute_reset": None,
    "request_history": [],
    "peak_rpm": 0,
    "peak_tpm": 0,
    })

    # Google/Gemini metrics
    st.sidebar.markdown("**🔵 Google/Gemini (Customer Data)**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric(
            label="Google Requests",
            value=google_stats["requests_today"],
            delta=f"Total: {google_stats['total_requests']}"
        )
    with col2:
        st.metric(
            label="Google Tokens",
            value=f"{google_stats['tokens_today']:,}",
            delta=f"Total: {google_stats['total_tokens']:,}"
        )

    # Groq metrics
    st.sidebar.markdown("**🟠 Groq (Customer Chat)**")
    col3, col4 = st.sidebar.columns(2)
    with col3:
        st.metric(
            label="Groq Requests",
            value=groq_stats["requests_today"],
            delta=f"Total: {groq_stats['total_requests']}"
        )
    with col4:
        st.metric(
            label="Groq Tokens",
            value=f"{groq_stats['tokens_today']:,}",
            delta=f"Total: {groq_stats['total_tokens']:,}"
        )

    # Cost estimation
    estimated_cost = usage_tracker.estimate_cost()
    st.sidebar.metric(
        label="Estimated Cost (USD)",
        value=f"${estimated_cost:.4f}",
        help="Approximate cost based on Gemini 2.0 Flash pricing"
    )

    # Usage warning
    if google_stats["requests_today"] > 50:
        st.sidebar.warning("⚠️ High API usage today!")
    elif google_stats["requests_today"] > 20:
        st.sidebar.info("ℹ️ Moderate API usage")
    else:
        st.sidebar.success("✅ Low API usage")

    # Recent activity
    if google_stats["request_history"]:
        with st.sidebar.expander("📈 Recent Activity", expanded=False):
            recent_requests = google_stats["request_history"][-5:]  # Last 5 requests
            for req in reversed(recent_requests):
                timestamp = req["timestamp"].strftime("%H:%M:%S")
                st.write(f"🕐 {timestamp} - {req['tokens']} tokens ({req['type']})")

    # Quota status
    quota_status = usage_tracker.get_quota_status()
    st.sidebar.markdown("**🔵 Quota Status**")
    col5, col6 = st.sidebar.columns(2)
    with col5:
        st.metric(
            label="Gemini RPM Usage",
            value=f"{quota_status['gemini']['rpm_usage']:.1f}%",
            help="Percentage of current requests per minute"
        )
    with col6:
        st.metric(
            label="Gemini TPM Usage",
            value=f"{quota_status['gemini']['tpm_usage']:.1f}%",
            help="Percentage of current tokens per minute"
        )

    col7, col8 = st.sidebar.columns(2)
    with col7:
        st.metric(
            label="Gemini Daily Usage",
            value=f"{quota_status['gemini']['daily_usage']:.1f}%",
            help="Percentage of current requests per day"
        )
    with col8:
        st.metric(
            label="Gemini Status",
            value=quota_status['gemini']['status'],
            help="Usage level for Gemini"
        )

    col9, col10 = st.sidebar.columns(2)
    with col9:
        st.metric(
            label="Groq RPM Usage",
            value=f"{quota_status['groq']['rpm_usage']:.1f}%",
            help="Percentage of current requests per minute"
        )
    with col10:
        st.metric(
            label="Groq TPM Usage",
            value=f"{quota_status['groq']['tpm_usage']:.1f}%",
            help="Percentage of current tokens per minute"
        )

    col11, col12 = st.sidebar.columns(2)
    with col11:
        st.metric(
            label="Groq Daily Usage",
            value=f"{quota_status['groq']['daily_usage']:.1f}%",
            help="Percentage of current requests per day"
        )
    with col12:
        st.metric(
            label="Groq Status",
            value=quota_status['groq']['status'],
            help="Usage level for Groq"
        )

display_usage_metrics()

# Initialize tabs for main content
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Unified Support", "👥 Customer Profiles", "📊 Usage Analytics", "📈 Support Dashboard"])

# Function to render customer profile in a friendly format
def render_customer_profile(data):
    customer_info = data["customer_info"]
    current_order = data["current_order"]
    order_history = data["order_history"]
    account = data["account"]

    st.markdown("<div class='profile-card'>", unsafe_allow_html=True)

    # Customer basic info
    st.markdown(f"""
        <div class='profile-header'>
            <div class='profile-icon'>👤</div>
            <div class='profile-name'>{customer_info['name']}</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
        st.markdown("<div class='profile-section-title'>Contact Information</div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class='profile-item'>
                <div class='profile-item-label'>Email:</div>
                <div>{customer_info['email']}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Phone:</div>
                <div>{customer_info['phone']}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Address:</div>
                <div>{customer_info['shipping_address']}</div>
            </div>
        """, unsafe_allow_html=True)

        if "state" in customer_info:
            st.markdown(f"""
                <div class='profile-item'>
                    <div class='profile-item-label'>State:</div>
                    <div>{customer_info['state']}</div>
                </div>
            """, unsafe_allow_html=True)

        if "lga" in customer_info:
            st.markdown(f"""
                <div class='profile-item'>
                    <div class='profile-item-label'>LGA:</div>
                    <div>{customer_info['lga']}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
        st.markdown("<div class='profile-section-title'>Account Information</div>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class='profile-item'>
                <div class='profile-item-label'>Member Since:</div>
                <div>{account['member_since']}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Tier:</div>
                <div>{account['tier']}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Points:</div>
                <div>{account['points']}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Current order
    st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
    st.markdown("<div class='profile-section-title'>Current Order</div>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class='profile-order'>
            <div class='profile-item'>
                <div class='profile-item-label'>Order ID:</div>
                <div>{current_order.get('order_id', 'N/A')}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Order Date:</div>
                <div>{current_order.get('order_date', 'N/A')}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Expected Delivery:</div>
                <div>{current_order.get('expected_delivery', 'N/A')}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Delivery Method:</div>
                <div>{current_order.get('delivery_method', 'N/A')}</div>
            </div>
            <div class='profile-item'>
                <div class='profile-item-label'>Payment Method:</div>
                <div>{current_order.get('payment_method', 'N/A')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Display products if available
    if current_order.get('products'):
        st.markdown("<div class='profile-section-title'>Order Items</div>", unsafe_allow_html=True)
        for i, product in enumerate(current_order['products']):
            st.markdown(f"""
                <div class='profile-order'>
                    <div class='profile-item'>
                        <div class='profile-item-label'>Product {i+1}:</div>
                        <div>{product.get('name', 'Unknown Product')}</div>
                    </div>
                    <div class='profile-item'>
                        <div class='profile-item-label'>Price:</div>
                        <div>{product.get('price', 'N/A')}</div>
                    </div>
                    <div class='profile-item'>
                        <div class='profile-item-label'>Quantity:</div>
                        <div>{product.get('quantity', 'N/A')}</div>
                    </div>
                    <div class='profile-item'>
                        <div class='profile-item-label'>Status:</div>
                        <div>{product.get('status', 'N/A')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Order totals
    if current_order.get('shipping_fee') or current_order.get('total'):
        st.markdown("<div class='profile-section-title'>Order Summary</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='profile-order'>
                <div class='profile-item'>
                    <div class='profile-item-label'>Shipping Fee:</div>
                    <div>{current_order.get('shipping_fee', 'N/A')}</div>
                </div>
                <div class='profile-item'>
                    <div class='profile-item-label'><strong>Total Amount:</strong></div>
                    <div><strong>{current_order.get('total', 'N/A')}</strong></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Initialize the CustomerSupportAIAgent
support_agent = CustomerSupportAIAgent(model_choice)

with tab1:
    st.markdown("<div class='sub-header'>🎯 Unified Customer Support Agent</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='card'>
        <p style='text-align: center;'>Ask me anything about customers, orders, or support operations. I have access to all customer data and can help with:</p>
        <ul>
            <li>🔍 Finding specific customers or orders</li>
            <li>📊 Generating reports and analytics</li>
            <li>⚠️ Identifying issues and trends</li>
            <li>📋 Managing support workflows</li>
            <li>💰 Revenue and business insights</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Quick action buttons
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Customer Overview", key="overview_btn"):
            st.session_state["quick_query"] = "Give me an overview of all customers and their current status"

    with col2:
        if st.button("⚠️ Pending Orders", key="pending_btn"):
            st.session_state["quick_query"] = "Show me all pending orders that need attention"

    with col3:
        if st.button("💰 High Value Customers", key="high_value_btn"):
            st.session_state["quick_query"] = "Who are our high-value customers and what are they ordering?"

    with col4:
        if st.button("📈 Today's Summary", key="summary_btn"):
            st.session_state["quick_query"] = "Give me a summary of today's customer activity and any issues"

    # Initialize unified chat history
    if "unified_chat_history" not in st.session_state:
        st.session_state["unified_chat_history"] = []

    # Clear chat button
    col_clear1, col_clear2 = st.columns([6, 1])
    with col_clear2:
        if st.button("🗑️ Clear Chat", key="clear_unified_chat"):
            st.session_state["unified_chat_history"] = []
            st.success("Chat cleared!")
            st.rerun()

    # Display chat history
    st.markdown("### 💬 Support Conversation")

    # Create chat container
    chat_container = st.container()

    with chat_container:
        for message in st.session_state["unified_chat_history"]:
            if message["role"] == "user":
                st.markdown(
                    f"""
                    <div class='chat-message chat-message-user'>
                        <div class='avatar'>👤</div>
                        <div class='message-content'>{message["content"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class='chat-message chat-message-assistant'>
                        <div class='avatar'>🤖</div>
                        <div class='message-content'>{message["content"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Display relevant customers if available
                if "relevant_customers" in message and message["relevant_customers"]:
                    with st.expander(f"📋 Relevant Customers ({len(message['relevant_customers'])})", expanded=False):
                        for result in message["relevant_customers"][:3]:  # Show top 3
                            customer_data = result["customer_data"]
                            customer_info = customer_data["customer_info"]
                            current_order = customer_data["current_order"]

                            st.markdown(f"""
                            **{customer_info['name']}** (ID: {result['customer_id']})
                            - 📧 {customer_info['email']}
                            - 📍 {customer_info['state']}
                            - 🛒 Order: {current_order.get('order_id', 'N/A')} - {current_order.get('total', 'N/A')}
                            """)

    # Handle quick queries
    if "quick_query" in st.session_state:
        query = st.session_state["quick_query"]
        del st.session_state["quick_query"]

        # Add user message
        st.session_state["unified_chat_history"].append({"role": "user", "content": query})

        # Process query
        with st.spinner("🤖 Processing your request..."):
            try:
                answer, relevant_customers, analytics = support_agent.handle_unified_query(query)

                # Add assistant response with metadata
                st.session_state["unified_chat_history"].append({
                    "role": "assistant",
                    "content": answer,
                    "relevant_customers": relevant_customers,
                    "analytics": analytics
                })

            except Exception as e:
                st.session_state["unified_chat_history"].append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {e}"
                })

        st.rerun()

    # Chat input
    query = st.chat_input("Ask me anything about customers, orders, or support operations...", key="unified_chat_input")

    if query:
        # Add user message
        st.session_state["unified_chat_history"].append({"role": "user", "content": query})

        # Process query
        with st.spinner("🤖 Processing your request..."):
            try:
                answer, relevant_customers, analytics = support_agent.handle_unified_query(query)

                # Add assistant response with metadata
                st.session_state["unified_chat_history"].append({
                    "role": "assistant",
                    "content": answer,
                    "relevant_customers": relevant_customers,
                    "analytics": analytics
                })

            except Exception as e:
                st.session_state["unified_chat_history"].append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {e}"
                })

        st.rerun()

    # Sample queries section
    if not st.session_state["unified_chat_history"]:
        st.markdown("### 💡 Sample Queries")
        st.markdown("""
        Try asking me questions like:
        - "Show me all customers from Lagos"
        - "Which orders are still processing?"
        - "Who are our platinum tier customers?"
        - "Find customer with order ID JMT-NG-123456"
        - "What's our total revenue this month?"
        - "Show me customers with payment issues"
        - "Which products are most popular?"
        """)

    # Customer data generation section
    st.markdown("### 🔄 Customer Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Generate Single Customer**")
        single_id = st.text_input("Customer ID", placeholder="e.g., CUST001", key="single_customer_id")
        if st.button("Generate Customer", key="gen_single_customer"):
            if single_id:
                with st.spinner(f"Generating customer profile for {single_id}..."):
                    customer_data = support_agent.generate_synthetic_data(single_id)
                if customer_data:
                    st.success(f"✅ Generated profile for {single_id}")
                    st.rerun()
                else:
                    st.error("❌ Failed to generate customer profile")
            else:
                st.error("Please enter a Customer ID")

    with col2:
        st.markdown("**Generate Multiple Customers**")
        multiple_ids = st.text_area("Customer IDs (one per line)", placeholder="CUST001\nCUST002\nCUST003", key="multiple_customer_ids")
        if st.button("Generate Multiple", key="gen_multiple_customers"):
            if multiple_ids:
                ids_list = [id.strip() for id in multiple_ids.split("\n") if id.strip()]
                progress_bar = st.progress(0)

                for i, cust_id in enumerate(ids_list):
                    with st.status(f"Generating {cust_id}..."):
                        customer_data = support_agent.generate_synthetic_data(cust_id)
                        if customer_data:
                            st.write(f"✅ {cust_id}")
                        else:
                            st.write(f"❌ {cust_id}")

                    progress_bar.progress((i + 1) / len(ids_list))

                st.success(f"Generated {len(ids_list)} customer profiles!")
                st.rerun()
            else:
                st.error("Please enter at least one Customer ID")


with tab2:
    st.markdown("<div class='sub-header'>📊 All Customer Profiles</div>", unsafe_allow_html=True)

    if persistent_state["all_customer_data"]:
        # Summary statistics
        total_customers = len(persistent_state["all_customer_data"])
        st.markdown(f"### 📈 Overview: {total_customers} Customer{'s' if total_customers != 1 else ''}")

        # Quick stats
        col1, col2, col3, col4 = st.columns(4)

        # Calculate quick stats
        states = set()
        tiers = {}
        total_revenue = 0

        for customer_data in persistent_state["all_customer_data"].values():
            customer_info = customer_data.get("customer_info", {})
            current_order = customer_data.get("current_order", {})
            account = customer_data.get("account", {})

            # Collect states
            if customer_info.get('state'):
                states.add(customer_info['state'])

            # Count tiers
            tier = account.get('tier', 'Unknown')
            tiers[tier] = tiers.get(tier, 0) + 1

            # Calculate revenue
            total_str = current_order.get('total', '₦0')
            try:
                total_numeric = float(total_str.replace('₦', '').replace(',', ''))
                total_revenue += total_numeric
            except:
                pass

        with col1:
            st.metric("Total Customers", total_customers)

        with col2:
            st.metric("States Covered", len(states))

        with col3:
            st.metric("Total Revenue", f"₦{total_revenue:,.0f}")

        with col4:
            premium_customers = tiers.get('Gold', 0) + tiers.get('Platinum', 0)
            st.metric("Premium Customers", premium_customers)

        # Search and filter
        st.markdown("### 🔍 Search & Filter")
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("Search customers", placeholder="Name, email, state, order ID...")

        with col2:
            state_filter = st.selectbox("Filter by State", ["All States"] + sorted(list(states)))

        with col3:
            tier_filter = st.selectbox("Filter by Tier", ["All Tiers"] + sorted(list(tiers.keys())))

        # Filter customers based on search criteria
        filtered_customers = {}

        for cust_id, cust_data in persistent_state["all_customer_data"].items():
            customer_info = cust_data.get("customer_info", {})
            current_order = cust_data.get("current_order", {})
            account = cust_data.get("account", {})

            # Apply filters
            if state_filter != "All States" and customer_info.get('state') != state_filter:
                continue

            if tier_filter != "All Tiers" and account.get('tier') != tier_filter:
                continue

            # Apply search
            if search_term:
                searchable_text = f"""
                {customer_info.get('name', '')} {customer_info.get('email', '')}
                {customer_info.get('state', '')} {current_order.get('order_id', '')}
                """.lower()

                if search_term.lower() not in searchable_text:
                    continue

            filtered_customers[cust_id] = cust_data

        # Display filtered results
        if filtered_customers:
            st.markdown(f"### 👥 Customer Profiles ({len(filtered_customers)} found)")

            # Create columns for buttons
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("Refresh Profiles", key="refresh_profiles"):
                    st.rerun()

            with col2:
                if st.button("Export Data", key="export_profiles"):
                    st.success("Customer data exported successfully!")

            # Display all customer profiles
            for cust_id, cust_data in filtered_customers.items():
                with st.expander(f"👤 {cust_data['customer_info']['name']} (ID: {cust_id})", expanded=False):
                    render_customer_profile(cust_data)

                    # Quick info summary
                    customer_info = cust_data.get("customer_info", {})
                    current_order = cust_data.get("current_order", {})
                    account = cust_data.get("account", {})

                    st.markdown("---")
                    st.markdown("**Quick Actions:**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button(f"📋 View Details", key=f"details_{cust_id}"):
                            st.info(f"Detailed view for {customer_info['name']} would open here")

                    with col2:
                        if st.button(f"📧 Send Email", key=f"email_{cust_id}"):
                            st.success(f"Email template opened for {customer_info['name']}")

                    with col3:
                        if st.button(f"📞 Call Customer", key=f"call_{cust_id}"):
                            st.success(f"Call initiated to {customer_info['phone']}")
        else:
            st.info("No customers match your search criteria. Try adjusting your filters.")

    else:
        st.info("No customer profiles available. Generate customer profiles from the Unified Support tab first.")

        # Quick generation option
        st.markdown("### 🚀 Quick Start")
        if st.button("Generate Sample Customers", key="generate_sample_customers"):
            sample_ids = ["SAMPLE001", "SAMPLE002", "SAMPLE003"]
            progress_bar = st.progress(0)

            support_agent = CustomerSupportAIAgent(model_choice)

            for i, sample_id in enumerate(sample_ids):
                with st.status(f"Generating {sample_id}..."):
                    customer_data = support_agent.generate_synthetic_data(sample_id)
                    if customer_data:
                        st.write(f"✅ {sample_id}")
                    else:
                        st.write(f"❌ {sample_id}")

                progress_bar.progress((i + 1) / len(sample_ids))

            st.success("Sample customers generated!")
            st.rerun()


with tab3:
    st.markdown("<div class='sub-header'>📊 Comprehensive Usage Analytics</div>", unsafe_allow_html=True)

    stats = usage_tracker.get_usage_stats()
    quota_info = usage_tracker.get_quota_info()
    quota_status = usage_tracker.get_quota_status()
    google_stats = stats["google_api"]
    groq_stats = stats["groq_api"]

    # Real-time quota monitoring section
    st.markdown("### 🚨 Real-Time Quota Monitoring")
    st.markdown("*Based on official Google Cloud Vertex AI quotas*")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔵 Gemini 2.0 Flash Quotas")

        # RPM Progress
        rpm_percentage = quota_status['gemini']['rpm_usage']
        st.markdown(f"**Requests Per Minute: {google_stats['requests_this_minute']}/{quota_info['gemini']['requests_per_minute']}**")
        progress_color = "🟢" if rpm_percentage < 50 else "🟡" if rpm_percentage < 80 else "🔴"
        st.progress(min(rpm_percentage / 100, 1.0))
        st.write(f"{progress_color} {rpm_percentage:.1f}% of RPM quota used")

        # TPM Progress
        tpm_percentage = quota_status['gemini']['tpm_usage']
        st.markdown(f"**Tokens Per Minute: {google_stats['tokens_this_minute']:,}/{quota_info['gemini']['tokens_per_minute']:,}**")
        progress_color = "🟢" if tpm_percentage < 50 else "🟡" if tpm_percentage < 80 else "🔴"
        st.progress(min(tpm_percentage / 100, 1.0))
        st.write(f"{progress_color} {tpm_percentage:.1f}% of TPM quota used")

        # Daily Progress
        daily_percentage = quota_status['gemini']['daily_usage']
        st.markdown(f"**Daily Requests: {google_stats['requests_today']}/{quota_info['gemini']['requests_per_day']}**")
        progress_color = "🟢" if daily_percentage < 50 else "🟡" if daily_percentage < 80 else "🔴"
        st.progress(min(daily_percentage / 100, 1.0))
        st.write(f"{progress_color} {daily_percentage:.1f}% of daily quota used")

    with col2:
        st.markdown("#### 🟠 Groq API Quotas")

        # RPM Progress
        rpm_percentage = quota_status['groq']['rpm_usage']
        st.markdown(f"**Requests Per Minute: {groq_stats['requests_this_minute']}/{quota_info['groq']['requests_per_minute']}**")
        progress_color = "🟢" if rpm_percentage < 50 else "🟡" if rpm_percentage < 80 else "🔴"
        st.progress(min(rpm_percentage / 100, 1.0))
        st.write(f"{progress_color} {rpm_percentage:.1f}% of RPM quota used")

        # TPM Progress
        tpm_percentage = quota_status['groq']['tpm_usage']
        st.markdown(f"**Tokens Per Minute: {groq_stats['tokens_this_minute']:,}/{quota_info['groq']['tokens_per_minute']:,}**")
        progress_color = "🟢" if tpm_percentage < 50 else "🟡" if tpm_percentage < 80 else "🔴"
        st.progress(min(tpm_percentage / 100, 1.0))
        st.write(f"{progress_color} {tpm_percentage:.1f}% of TPM quota used")

        # Daily Progress
        daily_percentage = quota_status['groq']['daily_usage']
        st.markdown(f"**Daily Requests: {groq_stats['requests_today']}/{quota_info['groq']['requests_per_day']}**")
        progress_color = "🟢" if daily_percentage < 50 else "🟡" if daily_percentage < 80 else "🔴"
        st.progress(min(daily_percentage / 100, 1.0))
        st.write(f"{progress_color} {daily_percentage:.1f}% of daily quota used")

    # Overview metrics
    st.markdown("### 📈 Usage Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Requests (Gemini)",
            value=google_stats["total_requests"],
            delta=f"Today: {google_stats['requests_today']}",
            help="Total API requests made to Gemini"
        )

    with col2:
        st.metric(
            label="Total Tokens (Gemini)",
            value=f"{google_stats['total_tokens']:,}",
            delta=f"Today: {google_stats['tokens_today']:,}",
            help="Total tokens consumed by Gemini"
        )

    with col3:
        st.metric(
            label="Peak RPM (Gemini)",
            value=google_stats["peak_rpm"],
            help="Highest requests per minute recorded"
        )

    with col4:
        estimated_cost = usage_tracker.estimate_cost()
        st.metric(
            label="Estimated Cost",
            value=f"${estimated_cost:.4f}",
            help="Approximate cost in USD based on Gemini 2.0 Flash pricing"
        )

    # Detailed quota information
    st.markdown("### 📋 Official API Quotas & Limits")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔵 Gemini 2.0 Flash (Official Limits)")
        gemini_quota_data = {
            "Metric": [
                "Requests per minute",
                "Tokens per minute",
                "Requests per day (est.)",
                "Max concurrent requests",
                "Max output tokens",
                "Max input tokens"
            ],
            "Limit": [
                f"{quota_info['gemini']['requests_per_minute']:,}",
                f"{quota_info['gemini']['tokens_per_minute']:,}",
                f"{quota_info['gemini']['requests_per_day']:,}",
                f"{quota_info['gemini']['concurrent_requests']:,}",
                f"{quota_info['gemini']['max_output_tokens']:,}",
                f"{quota_info['gemini']['max_input_tokens']:,}"
            ],
            "Current Usage": [
                f"{google_stats['requests_this_minute']} ({quota_status['gemini']['rpm_usage']:.1f}%)",
                f"{google_stats['tokens_this_minute']:,} ({quota_status['gemini']['tpm_usage']:.1f}%)",
                f"{google_stats['requests_today']} ({quota_status['gemini']['daily_usage']:.1f}%)",
                "N/A",
                "N/A",
                "N/A"
            ]
        }
        st.dataframe(gemini_quota_data, use_container_width=True)

    with col2:
        st.markdown("#### 🟠 Groq API (Free Tier Limits)")
        groq_quota_data = {
            "Metric": [
                "Requests per minute",
                "Tokens per minute",
                "Requests per day (est.)"
            ],
            "Limit": [
                f"{quota_info['groq']['requests_per_minute']:,}",
                f"{quota_info['groq']['tokens_per_minute']:,}",
                f"{quota_info['groq']['requests_per_day']:,}"
            ],
            "Current Usage": [
                f"{groq_stats['requests_this_minute']} ({quota_status['groq']['rpm_usage']:.1f}%)",
                f"{groq_stats['tokens_this_minute']:,} ({quota_status['groq']['tpm_usage']:.1f}%)",
                f"{groq_stats['requests_today']} ({quota_status['groq']['daily_usage']:.1f}%)"
            ]
        }
        st.dataframe(groq_quota_data, use_container_width=True)

    # Usage breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Usage Trends (Gemini)")
        if google_stats["request_history"]:
            # Create a simple chart of recent usage
            recent_requests = google_stats["request_history"][-20:]  # Last 20 requests
            timestamps = [req["timestamp"].strftime("%H:%M") for req in recent_requests]
            tokens = [req["tokens"] for req in recent_requests]
            rpm_data = [req.get("rpm_at_time", 0) for req in recent_requests]

            chart_data = {
                "Time": timestamps,
                "Tokens": tokens,
                "RPM": rpm_data
            }
            st.line_chart(chart_data, x="Time", y=["Tokens", "RPM"])
        else:
            st.info("No Gemini usage data available yet.")

    with col2:
        st.markdown("### 🔍 Request Types")
        if google_stats["request_history"]:
            # Count request types
            type_counts = {}
            for req in google_stats["request_history"]:
                req_type = req["type"]
                type_counts[req_type] = type_counts.get(req_type, 0) + 1

            st.bar_chart(type_counts)
        else:
            st.info("No request type data available yet.")

    # Recent activity table
    st.markdown("### 📋 Recent Activity")
    if google_stats["request_history"]:
        recent_requests = google_stats["request_history"][-10:]  # Last 10 requests

        activity_data = []
        for req in reversed(recent_requests):
            activity_data.append({
                "Timestamp": req["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "Type": req["type"],
                "Tokens": req["tokens"],
                "RPM at Time": req.get("rpm_at_time", 0),
                "TPM at Time": req.get("tpm_at_time", 0)
            })

        st.dataframe(activity_data, use_container_width=True)
    else:
        st.info("No recent activity to display.")

    # Cost breakdown with enhanced pricing info
    st.markdown("### 💰 Cost Analysis")
    st.markdown("*Based on official Gemini 2.0 Flash pricing: Input $0.075/1M tokens, Output $0.30/1M tokens*")

    # Estimate costs for different usage levels
    cost_data = {
        "Usage Level": ["Current", "10x Current", "100x Current", "1000x Current"],
        "Requests": [
            google_stats["total_requests"],
            google_stats["total_requests"] * 10,
            google_stats["total_requests"] * 100,
            google_stats["total_requests"] * 1000
        ],
        "Tokens": [
            google_stats["total_tokens"],
            google_stats["total_tokens"] * 10,
            google_stats["total_tokens"] * 100,
            google_stats["total_tokens"] * 1000
        ],
        "Estimated Cost": [
            f"${estimated_cost:.4f}",
            f"${estimated_cost * 10:.4f}",
            f"${estimated_cost * 100:.2f}",
            f"${estimated_cost * 1000:.2f}"
        ]
    }

    st.dataframe(cost_data, use_container_width=True)

    # Quota recommendations
    st.markdown("### 💡 Quota Recommendations")

    if quota_status['gemini']['rpm_usage'] > 80:
        st.error("🚨 **CRITICAL**: You're approaching Gemini RPM limits! Consider implementing request queuing or rate limiting.")
    elif quota_status['gemini']['rpm_usage'] > 60:
        st.warning("⚠️ **WARNING**: High Gemini RPM usage. Monitor closely and consider optimizing request patterns.")
    elif quota_status['gemini']['daily_usage'] > 70:
        st.warning("⚠️ **WARNING**: High daily usage. You may hit daily limits if usage continues at this rate.")
    else:
        st.success("✅ **HEALTHY**: Your usage is within safe limits. Current patterns are sustainable.")

    # Additional insights
    if google_stats["peak_rpm"] > 0:
        efficiency = (google_stats["total_tokens"] / max(google_stats["total_requests"], 1))
        st.info(f"📊 **Usage Insights**: Average tokens per request: {efficiency:.1f} | Peak RPM: {google_stats['peak_rpm']} | Peak TPM: {google_stats['peak_tpm']}")

    # Reset button
    if st.button("🔄 Reset Usage Statistics", type="secondary"):
        # Reset the usage tracker
        usage_tracker.usage_data["google_api"] = {
            "total_requests": 0,
            "total_tokens": 0,
            "requests_today": 0,
            "tokens_today": 0,
            "requests_this_minute": 0,
            "tokens_this_minute": 0,
            "last_reset": datetime.now().date(),
            "last_minute_reset": datetime.now().replace(second=0, microsecond=0),
            "request_history": [],
            "peak_rpm": 0,
            "peak_tpm": 0,
        }
        usage_tracker.usage_data["groq_api"] = {
            "total_requests": 0,
            "total_tokens": 0,
            "requests_today": 0,
            "tokens_today": 0,
            "requests_this_minute": 0,
            "tokens_this_minute": 0,
            "last_reset": datetime.now().date(),
            "last_minute_reset": datetime.now().replace(second=0, microsecond=0),
            "request_history": [],
            "peak_rpm": 0,
            "peak_tpm": 0,
        }
        st.success("Usage statistics have been reset!")
        st.rerun()


with tab4:
    st.markdown("<div class='sub-header'>📈 Support Dashboard</div>", unsafe_allow_html=True)

    # Get analytics data
    analytics = support_agent.get_customer_analytics()

    if analytics:
        # Key metrics overview
        st.markdown("### 📊 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total Customers",
                value=analytics['total_customers'],
                help="Total number of customers in the system"
            )

        with col2:
            st.metric(
                label="Pending Orders",
                value=len(analytics['pending_orders']),
                help="Orders that need attention"
            )

        with col3:
            st.metric(
                label="High Value Customers",
                value=len(analytics['high_value_customers']),
                help="Customers with orders > ₦100,000"
            )

        with col4:
            st.metric(
                label="Total Revenue",
                value=f"₦{analytics['total_revenue']:,.0f}",
                help="Total revenue from all current orders"
            )

        # Distribution charts
        st.markdown("### 📈 Customer Distribution")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🗺️ Customers by State")
            if analytics['states_distribution']:
                st.bar_chart(analytics['states_distribution'])
            else:
                st.info("No state distribution data available")

        with col2:
            st.markdown("#### 🏆 Customers by Tier")
            if analytics['tier_distribution']:
                st.bar_chart(analytics['tier_distribution'])
            else:
                st.info("No tier distribution data available")

        # Payment and delivery insights
        st.markdown("### 💳 Payment & Delivery Insights")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💰 Payment Methods")
            if analytics['payment_methods']:
                st.bar_chart(analytics['payment_methods'])
            else:
                st.info("No payment method data available")

        with col2:
            st.markdown("#### 🚚 Delivery Methods")
            if analytics['delivery_methods']:
                st.bar_chart(analytics['delivery_methods'])
            else:
                st.info("No delivery method data available")

        # Order status overview
        st.markdown("### 📦 Order Status Overview")
        if analytics['order_statuses']:
            st.bar_chart(analytics['order_statuses'])
        else:
            st.info("No order status data available")

        # Pending orders table
        st.markdown("### ⚠️ Orders Requiring Attention")
        if analytics['pending_orders']:
            pending_df = []
            for order in analytics['pending_orders']:
                pending_df.append({
                    "Customer": order['customer_name'],
                    "Customer ID": order['customer_id'],
                    "Order ID": order['order_id'],
                    "Product": order['product'],
                    "Status": order['status']
                })

            st.dataframe(pending_df, use_container_width=True)

            # Quick actions for pending orders
            st.markdown("#### 🚀 Quick Actions")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📧 Send Status Updates", key="send_updates"):
                    st.success("Status update emails would be sent to customers with pending orders")

            with col2:
                if st.button("📞 Priority Follow-up", key="priority_followup"):
                    st.success("Priority follow-up list generated for support team")

            with col3:
                if st.button("📋 Export Report", key="export_report"):
                    st.success("Pending orders report exported successfully")
        else:
            st.success("🎉 No pending orders requiring attention!")

        # High value customers
        st.markdown("### 💎 High Value Customers")
        if analytics['high_value_customers']:
            hv_df = []
            for customer in analytics['high_value_customers']:
                hv_df.append({
                    "Customer": customer['customer_name'],
                    "Customer ID": customer['customer_id'],
                    "Order Value": customer['order_value'],
                    "Tier": customer['tier']
                })

            st.dataframe(hv_df, use_container_width=True)
        else:
            st.info("No high-value customers (orders > ₦100,000) found")

        # Recent orders
        st.markdown("### 🕒 Recent Orders")
        if analytics['recent_orders']:
            recent_df = []
            for order in analytics['recent_orders']:
                recent_df.append({
                    "Customer": order['customer_name'],
                    "Customer ID": order['customer_id'],
                    "Order ID": order['order_id'],
                    "Order Date": order['order_date'],
                    "Total": order['total']
                })

            st.dataframe(recent_df, use_container_width=True)
        else:
            st.info("No recent orders found")

        # Support insights
        st.markdown("### 🔍 Support Insights")

        # Calculate some insights
        avg_order_value = analytics['total_revenue'] / max(analytics['total_customers'], 1)
        pending_percentage = (len(analytics['pending_orders']) / max(analytics['total_customers'], 1)) * 100

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Average Order Value",
                value=f"₦{avg_order_value:,.0f}",
                help="Average order value across all customers"
            )

        with col2:
            st.metric(
                label="Pending Order Rate",
                value=f"{pending_percentage:.1f}%",
                help="Percentage of customers with pending orders"
            )

        with col3:
            # Most popular state
            if analytics['states_distribution']:
                popular_state = max(analytics['states_distribution'], key=analytics['states_distribution'].get)
                st.metric(
                    label="Top State",
                    value=popular_state,
                    delta=f"{analytics['states_distribution'][popular_state]} customers",
                    help="State with most customers"
                )

        # Recommendations
        st.markdown("### 💡 Recommendations")

        recommendations = []

        if len(analytics['pending_orders']) > analytics['total_customers'] * 0.3:
            recommendations.append("🚨 **High pending order rate**: Consider reviewing fulfillment processes")

        if len(analytics['high_value_customers']) < analytics['total_customers'] * 0.1:
            recommendations.append("💰 **Low high-value customer ratio**: Consider upselling strategies")

        if analytics['states_distribution'] and len(analytics['states_distribution']) < 5:
            recommendations.append("🗺️ **Limited geographic reach**: Consider expanding to more states")

        if not recommendations:
            recommendations.append("✅ **All metrics look healthy**: Continue current operations")

        for rec in recommendations:
            st.markdown(f"- {rec}")

        # Refresh button
        if st.button("🔄 Refresh Dashboard", key="refresh_dashboard"):
            st.rerun()

    else:
        st.info("No customer data available. Generate some customer profiles first to see the dashboard.")

        # Quick generation for demo
        st.markdown("### 🚀 Quick Demo Setup")
        if st.button("Generate Demo Data", key="generate_demo_data"):
            demo_ids = ["DEMO001", "DEMO002", "DEMO003", "DEMO004", "DEMO005"]
            progress_bar = st.progress(0)

            for i, demo_id in enumerate(demo_ids):
                with st.status(f"Generating {demo_id}..."):
                    customer_data = support_agent.generate_synthetic_data(demo_id)
                    if customer_data:
                        st.write(f"✅ {demo_id}")
                    else:
                        st.write(f"❌ {demo_id}")

                progress_bar.progress((i + 1) / len(demo_ids))

            st.success("Demo data generated! Refresh the dashboard to see analytics.")
            st.rerun()


# Footer
st.sidebar.markdown("""
<div class="footer">
    <p>Built with ❤️ by raqibcodes for raqibtech.com</p>
</div>
""", unsafe_allow_html=True)
