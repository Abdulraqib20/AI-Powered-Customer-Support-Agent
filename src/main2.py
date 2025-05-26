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
import logging
from logging.handlers import RotatingFileHandler

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
CUSTOMER_CHAT_MODEL = "llama3-70b-8192" # For handling customer conversations

# MODELS = {
#     "llama-3.3-70b-versatile",
#     "llama-3.1-8b-instant",
#     "llama3-70b-8192",
#     "gemini-2.5-flash-preview-04-17"
# }
# streamlit cache clear

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Import logging configuration
from config.logging_config import setup_logging

# Initialize loggers
app_logger, api_logger, error_logger = setup_logging()

#-----------------------------------------------------
# Usage Tracking
#-----------------------------------------------------
class APIUsageTracker:
    def __init__(self):
        self.usage_data = {
            "google_api": {
                "total_requests": 0,
                "total_tokens": 0,
                "requests_today": 0,
                "tokens_today": 0,
                "last_reset": datetime.now().date(),
                "request_history": []
            },
            "groq_api": {
                "total_requests": 0,
                "total_tokens": 0,
                "requests_today": 0,
                "tokens_today": 0,
                "last_reset": datetime.now().date(),
                "request_history": []
            }
        }

    def track_google_request(self, tokens_used=0, request_type="generation"):
        current_date = datetime.now().date()

        # Reset daily counters if new day
        if current_date != self.usage_data["google_api"]["last_reset"]:
            api_logger.info(f"🔄 Daily GOOGLE usage reset - Previous day: {self.usage_data['google_api']['requests_today']} requests, {self.usage_data['google_api']['tokens_today']} tokens")
            self.usage_data["google_api"]["requests_today"] = 0
            self.usage_data["google_api"]["tokens_today"] = 0
            self.usage_data["google_api"]["last_reset"] = current_date

        # Update counters
        self.usage_data["google_api"]["total_requests"] += 1
        self.usage_data["google_api"]["total_tokens"] += tokens_used
        self.usage_data["google_api"]["requests_today"] += 1
        self.usage_data["google_api"]["tokens_today"] += tokens_used

        # Log API usage
        api_logger.info(f"📊 GOOGLE API Call - Type: {request_type}, Tokens: {tokens_used}, Daily Total: {self.usage_data['google_api']['requests_today']} requests, {self.usage_data['google_api']['tokens_today']} tokens")

        # Add to history
        self.usage_data["google_api"]["request_history"].append({
            "timestamp": datetime.now(),
            "tokens": tokens_used,
            "type": request_type
        })

        # Keep only last 100 requests in history
        if len(self.usage_data["google_api"]["request_history"]) > 100:
            self.usage_data["google_api"]["request_history"] = \
                self.usage_data["google_api"]["request_history"][-100:]

        # Warning thresholds
        if self.usage_data["google_api"]["requests_today"] >= 80:
            app_logger.warning(f"⚠️ High GOOGLE API usage: {self.usage_data['google_api']['requests_today']} requests today")
        elif self.usage_data["google_api"]["tokens_today"] >= 40000:
            app_logger.warning(f"⚠️ High GOOGLE token usage: {self.usage_data['google_api']['tokens_today']} tokens today")

    def track_groq_request(self, tokens_used=0, request_type="customer_chat"):
        current_date = datetime.now().date()

        # Reset daily counters if new day
        if current_date != self.usage_data["groq_api"]["last_reset"]:
            api_logger.info(f"🔄 Daily GROQ usage reset - Previous day: {self.usage_data['groq_api']['requests_today']} requests, {self.usage_data['groq_api']['tokens_today']} tokens")
            self.usage_data["groq_api"]["requests_today"] = 0
            self.usage_data["groq_api"]["tokens_today"] = 0
            self.usage_data["groq_api"]["last_reset"] = current_date

        # Update counters
        self.usage_data["groq_api"]["total_requests"] += 1
        self.usage_data["groq_api"]["total_tokens"] += tokens_used
        self.usage_data["groq_api"]["requests_today"] += 1
        self.usage_data["groq_api"]["tokens_today"] += tokens_used

        # Log API usage
        api_logger.info(f"📊 GROQ API Call - Type: {request_type}, Tokens: {tokens_used}, Daily Total: {self.usage_data['groq_api']['requests_today']} requests, {self.usage_data['groq_api']['tokens_today']} tokens")

        # Add to history
        self.usage_data["groq_api"]["request_history"].append({
            "timestamp": datetime.now(),
            "tokens": tokens_used,
            "type": request_type
        })

        # Keep only last 100 requests in history
        if len(self.usage_data["groq_api"]["request_history"]) > 100:
            self.usage_data["groq_api"]["request_history"] = \
                self.usage_data["groq_api"]["request_history"][-100:]

        # Warning thresholds
        if self.usage_data["groq_api"]["requests_today"] >= 100:
            app_logger.warning(f"⚠️ High GROQ API usage: {self.usage_data['groq_api']['requests_today']} requests today")
        elif self.usage_data["groq_api"]["tokens_today"] >= 50000:
            app_logger.warning(f"⚠️ High GROQ token usage: {self.usage_data['groq_api']['tokens_today']} tokens today")

    def get_usage_stats(self):
        return self.usage_data

    def estimate_cost(self):
        # Gemini 2.0 Flash pricing (approximate)
        # Input: $0.075 per 1M tokens
        # Output: $0.30 per 1M tokens
        # Assuming 50/50 split for estimation
        tokens = self.usage_data["google_api"]["total_tokens"]
        estimated_cost = (tokens / 1000000) * 0.1875  # Average of input/output
        return estimated_cost



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
# Customer Support Agent
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
                    "max_tokens": 1000,
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
            # cloud
            # "vector_store": {
            #     "provider": "qdrant",
            #     "config": {
            #         "url": QDRANT_URL_CLOUD,
            #         "api_key": QDRANT_API_KEY,

            #     }
            # },
        }
        try:
            # Debug: Print config (without sensitive data)
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

    def handle_query(self, query, user_id=None):
        try:
            # Search for relevant memories
            relevant_memories = self.memory.search(query=query, user_id=user_id)

            # Build context from relevant memories
            context = "Relevant past information:\n"
            if relevant_memories and "results" in relevant_memories:
                for memory in relevant_memories["results"]:
                    if "memory" in memory:
                        context += f"- {memory['memory']}\n"

            # Use GROQ ONLY for customer chat - NO GEMINI TOKENS
            app_logger.info(f"💬 Processing customer query for user: {user_id} using GROQ model: {CUSTOMER_CHAT_MODEL}")

            full_prompt = f"""
            I need you to act as a customer support agent for raqibtech.com, a leading Nigerian e-commerce platform specializing in electronics and general merchandise.

            CUSTOMER'S HISTORY:
            {context}

            Customer ID: {user_id}

            CUSTOMER QUERY:
            {query}

            YOUR RESPONSE GUIDELINES:
            As a customer support agent for raqibtech.com (a leading Nigerian e-commerce platform):
            1. Be warm, professional and conversational - use "I" not "we"
            2. Address the customer by name when appropriate
            3. Reference specific details from their profile and order history
            4. Provide clear, actionable solutions
            5. Use Nigerian English where appropriate (not exaggerated)
            6. Acknowledge Nigerian-specific challenges (delivery logistics, payment issues)
            7. For order status, reference their specific order details
            8. For product questions, provide relevant information for the Nigerian market
            9. Keep responses concise but complete

            Your response should feel personalized to this specific customer and their situation in Nigeria.

            Your response:
            """

            # Track API usage
            start_time = time.time()

            groq_client = Groq(api_key=GROQ_API_KEY)
            response = groq_client.chat.completions.create(
                model=CUSTOMER_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a customer support AI agent for raqibtech.com, a leading Nigerian online electronics and general merchandise store. You should be familiar with Nigerian terminology, locations, and common shopping concerns. Always be helpful, professional, and considerate of Nigerian cultural context."},
                    {"role": "user", "content": full_prompt}
                ]
            )

                        # Track GROQ usage (NOT Google/Gemini)
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            usage_tracker.track_groq_request(tokens_used, "customer_chat")

            # Log usage with explicit GROQ model name
            elapsed_time = time.time() - start_time
            app_logger.info(f"💬 GROQ Customer chat response - Model: {CUSTOMER_CHAT_MODEL}, Tokens: {tokens_used}, Time: {elapsed_time:.2f}s, User: {user_id}")

            answer = response.choices[0].message.content

            # Add the query and answer to memory
            self.memory.add(query, user_id=user_id, metadata={"app_id": self.app_id, "role": "user"})
            self.memory.add(answer, user_id=user_id, metadata={"app_id": self.app_id, "role": "assistant"})

            return answer
        except Exception as e:
            error_logger.error(f"❌ Error in handle_query for user {user_id}: {e}", exc_info=True)
            st.error(f"An error occurred while handling the query: {e}")
            return "Sorry, I encountered an error. Please try again later."


    def get_memories(self, user_id=None):
        try:
            # Retrieve all memories for a user
            return self.memory.get_all(user_id=user_id)
        except Exception as e:
            st.error(f"Failed to retrieve memories: {e}")
            return None

    def clear_memories(self, user_id=None):
        try:
            if user_id in persistent_state["message_history"]:
                persistent_state["message_history"][user_id] = []
            return True
        except Exception as e:
            st.error(f"Failed to clear memories: {e}")
            return False

    def generate_synthetic_data(self, user_id: str) -> dict | None:
        try:
            app_logger.info(f"🔄 Starting synthetic data generation for user: {user_id}")
            today = datetime.now()
            order_date = (today - timedelta(days=10)).strftime("%B %d, %Y")
            expected_delivery = (today + timedelta(days=2)).strftime("%B %d, %Y")

            # Use Gemini instead of Groq
            model = genai.GenerativeModel(SYNTHETIC_DATA_MODEL)
            app_logger.info(f"📝 Using Gemini model: {SYNTHETIC_DATA_MODEL}")

            prompt = f"""Generate a detailed UNIQUE Nigerian customer profile for raqibtech.com customer ID {user_id}.
            Strict requirements:
            1. Create a COMPLETELY UNIQUE Nigerian full name that has NEVER been used before
            2. Ensure the name follows Nigerian naming conventions but is distinguishable from all previous customers
            3. The name must NOT match or resemble any existing names: {[data['customer_info']['name'] for data in persistent_state["all_customer_data"].values()]}

            Generate realistic profile with:
            - Name reflecting specific Nigerian ethnic groups (Yoruba/Igbo/Hausa/Edo/etc.)
            - Valid Nigerian address format with accurate city/state combinations
            - Nigerian phone number format (e.g., +234 or 080x)
            - Realistic order history with appropriate Nigerian products and pricing
            - Appropriate payment methods common in Nigeria

            Format as JSON with this structure:
            {{
                "customer_info": {{
                    "name": "Full Nigerian name",
                    "email": "Email address with common Nigerian domains like gmail.com or yahoo.com",
                    "shipping_address": "Specific Nigerian address with estate/area, street, city and state (e.g. '15 Adeniyi Jones Avenue, Ikeja, Lagos')",
                    "phone": "Nigerian mobile number format (e.g. '0803-123-4567' or '+234 813 456 7890')",
                    "state": "Actual Nigerian state",
                    "lga": "Corresponding Local Government Area"
                }},
                "current_order": {{
                    "order_id": "JMT-NG-{user_id[-6:]}",
                    "order_date": "{order_date}",
                    "expected_delivery": "{expected_delivery}",
                    "delivery_method": "One of: raqibtech Express, PickUp Station, Courier Service",
                    "payment_method": "One of: Pay on Delivery, Card Payment, Bank Transfer, RaqibTechPay",
                    "products": [
                        {{"name": "Realistic Nigerian product name", "price": "Price in Naira format with ₦ symbol", "quantity": X, "status": "Processing/Shipped/Delivered"}}
                    ],
                    "shipping_fee": "₦x,xxx",
                    "total": "₦xx,xxx"
                }},
                "order_history": [
                    {{"order_id": "JMT-NG-xxxxxx", "date": "YYYY-MM-DD", "items": X, "total": "₦xx,xxx", "status": "Delivered/Returned/Cancelled"}}
                ],
                "account": {{
                    "member_since": "Month YYYY",
                    "tier": "One of: Bronze, Silver, Gold, Platinum",
                    "points": "raqibtech reward points number"
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
    "last_reset": None,
        "request_history": []
    })

    # Google/Gemini metrics
    st.sidebar.markdown("**🔵 Google/Gemini (Synthetic Data)**")
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

display_usage_metrics()

# Initialize tabs for main content
tab1, tab2, tab3 = st.tabs(["💬 Chat Interface", "👥 Customer Profiles", "📊 Usage Analytics"])

# Handle tab switching
if "switch_to_tab" in st.session_state:
    if st.session_state["switch_to_tab"] == "chat":
        # Switch to the chat tab
        tab1_index = 0  # Index of the chat tab
        st.session_state["active_tab_index"] = tab1_index
        st.session_state.pop("switch_to_tab", None)

# Handle customer switching (needs to happen before customer_id input widget)
if "switch_to_customer" in st.session_state:
    # Store the customer ID to be set
    st.session_state["_customer_id"] = st.session_state["switch_to_customer"]
    st.session_state.pop("switch_to_customer", None)


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
                <div class='profile-item-label'>Status:</div>
                <div>{current_order.get('status', 'N/A')}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


with tab1:
    # Chat interface
    col_chat1, col_chat2 = st.columns([5, 1])

    with col_chat1:
        st.markdown("<div class='sidebar-header'>👤 Active Customer</div>", unsafe_allow_html=True)

    with col_chat2:
        if st.button("Clear Chat", key="clear_chat_btn", help="Clear the current chat conversation"):
            if "customer_id" in st.session_state and st.session_state.customer_id:
                if st.session_state.customer_id in persistent_state["message_history"]:
                    persistent_state["message_history"][st.session_state.customer_id] = []
                st.success("Chat cleared successfully!")
                st.rerun()

    # Customer ID
    # st.sidebar.markdown("<div class='sidebar-header'>👤 Customer Details</div>", unsafe_allow_html=True)
    # customer_id = st.sidebar.text_input("Enter Customer ID", value=st.session_state.get("customer_id", ""), key="customer_id")

    # Customer ID
    st.sidebar.markdown("<div class='sidebar-header'>👤 Customer Details</div>", unsafe_allow_html=True)
    default_value = st.session_state.get("_customer_id", st.session_state.get("customer_id", ""))
    if "_customer_id" in st.session_state:
        del st.session_state["_customer_id"]
    customer_id = st.sidebar.text_input("Enter Customer ID", value=default_value, key="customer_id")

    # Handle multiple customer IDs generation
    st.sidebar.markdown("<div class='sidebar-header'>🔄 Multiple Customer Details</div>", unsafe_allow_html=True)

    multiple_ids = st.sidebar.text_area("Generate multiple customer profiles (one ID per line)",
                                      placeholder="Enter customer IDs, one per line\nExample:\nCUST001\nCUST002\nCUST003")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Generate Profiles", key="gen_multi_data"):
            if multiple_ids:


                support_agent = CustomerSupportAIAgent(model_choice)

                ids_list = [id.strip() for id in multiple_ids.split("\n") if id.strip()]
                progress_bar = st.sidebar.progress(0)

                for i, cust_id in enumerate(ids_list):
                    with st.sidebar.status(f"Generating profile for {cust_id}..."):
                        customer_data = support_agent.generate_synthetic_data(cust_id)
                        if customer_data:
                            st.sidebar.success(f"Generated profile for {cust_id}")
                        else:
                            st.sidebar.error(f"Failed to generate profile for {cust_id}")

                    # Update progress
                    progress_bar.progress((i + 1) / len(ids_list))

                st.sidebar.success(f"Generated {len(ids_list)} customer profiles!")
                st.rerun()
            else:
                st.sidebar.error("Please enter at least one customer ID.")

    with col2:
        if st.button("Clear Memory", key="clear_mem_btn"):
            if "customer_id" in st.session_state and st.session_state.customer_id:


                support_agent = CustomerSupportAIAgent(model_choice)
                success = support_agent.clear_memories(st.session_state.customer_id)
                if success:
                    st.sidebar.success("Memory cleared successfully!")
                else:
                    st.sidebar.error("Failed to clear memory.")
            else:
                st.sidebar.error("Please select a customer ID first.")

    # Initialize the CustomerSupportAIAgent with groq model
    support_agent = CustomerSupportAIAgent(model_choice)

   # Handle customer ID selection
    if customer_id:
        st.session_state["selected_customer_id"] = customer_id
        # Initialize message history for this customer if it doesn't exist
        if customer_id not in persistent_state["message_history"]:
            persistent_state["message_history"][customer_id] = []

        # Display customer profile if available
        if customer_id in persistent_state["all_customer_data"]:
            customer_data = persistent_state["all_customer_data"][customer_id]

            with st.expander("📊 Customer Profile", expanded=False):
                render_customer_profile(customer_data)

        # if customer_id in persistent_state["all_customer_data"]:
        #     customer_data = persistent_state["all_customer_data"][customer_id]
        #     st.markdown("<div class='profile-card'>", unsafe_allow_html=True)
        #     st.markdown("<div class='profile-header'>📊 Customer Profile</div>", unsafe_allow_html=True)
        #     render_customer_profile(customer_data)
        #     st.markdown("</div>", unsafe_allow_html=True)


        else:
            # Generate data if it doesn't exist
            if st.button("Generate Customer Data", key="gen_single_data"):
                with st.spinner("Generating customer data..."):
                    customer_data = support_agent.generate_synthetic_data(customer_id)
                if customer_data:
                    st.success("Data generated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to generate data.")


    # Create a custom chat container
    st.markdown("<div class='chat-container' id='chat-container'>", unsafe_allow_html=True)

    # Display the chat history for the selected customer
    if "customer_id" in st.session_state and st.session_state.customer_id:
        customer_id = st.session_state.customer_id
        for message in persistent_state["message_history"].get(customer_id, []):
            if message["role"] == "user":
                st.markdown(
                    f"""
                    <div class='chat-message chat-message-user'>
                        <div class='avatar avatar-user'>👤</div>
                        <div class='message-content'>{message["content"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class='chat-message chat-message-assistant'>
                        <div class='avatar avatar-assistant'>🤖</div>
                        <div class='message-content'>{message["content"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Display thinking indicator if waiting for response
        if "waiting_response" in st.session_state and st.session_state.waiting_response:
            st.markdown(
                f"""
                <div class='chat-message chat-message-assistant'>
                    <div class='avatar avatar-assistant'>🤖</div>
                    <div class='message-content'><span class='thinking-indicator'>|</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    if "customer_id" in st.session_state and st.session_state.customer_id:
        customer_id = st.session_state.customer_id

        # Chat input
        query = st.chat_input("How can I assist you today?", key="chat_input")

        if query:
            # Add user message to chat history
            persistent_state["message_history"].setdefault(customer_id, []).append({"role": "user", "content": query})

            # Set waiting flag
            st.session_state.waiting_response = True
            st.rerun()
    else:
        st.info("Please enter a Customer ID in the sidebar to start chatting.")

    # Process any pending query
    if ("customer_id" in st.session_state and st.session_state.customer_id and
        "waiting_response" in st.session_state and st.session_state.waiting_response):
        customer_id = st.session_state.customer_id

        # Get the last user message
        messages = persistent_state["message_history"].get(customer_id, [])
        last_user_message = next((msg["content"] for msg in reversed(messages)
                                if msg["role"] == "user"), None)

        if last_user_message:
            # Generate response
            with st.spinner("Thinking..."):
                answer = support_agent.handle_query(last_user_message, user_id=customer_id)

            # Add assistant response to chat history
            persistent_state["message_history"].setdefault(customer_id, []).append({"role": "assistant", "content": answer})

            # Clear waiting flag
            st.session_state.waiting_response = False
            st.rerun()




with tab2:
    st.markdown("<div class='sub-header'>📊 All Customer Profiles</div>", unsafe_allow_html=True)

    if persistent_state["all_customer_data"]:
        # Display all customer profiles in a grid
        st.markdown("<div class='customer-profiles-grid'>", unsafe_allow_html=True)

        # Create columns for buttons
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("Refresh Profiles", key="refresh_profiles"):
                st.rerun()

        # Display all customer profiles
        for cust_id, cust_data in persistent_state["all_customer_data"].items():
            with st.expander(f"Customer: {cust_id} - {cust_data['customer_info']['name']}", expanded=False):
                render_customer_profile(cust_data)

                if st.button(f"Chat with {cust_data['customer_info']['name']}", key=f"select_{cust_id}"):
                    st.session_state["switch_to_customer"] = cust_id
                    st.session_state["switch_to_tab"] = "chat"
                    st.rerun()

        # for cust_id, cust_data in persistent_state["all_customer_data"].items():
        #     st.markdown(f"""
        #     <div class='profile-card'>
        #         <div class='profile-header'>
        #             <div class='profile-icon'>👤</div>
        #             <div class='profile-name'>Customer: {cust_id} - {cust_data['customer_info']['name']}</div>
        #         </div>
        #     """, unsafe_allow_html=True)
        #     render_customer_profile(cust_data)
        #     st.markdown("</div>", unsafe_allow_html=True)

        #     if st.button(f"Chat with {cust_data['customer_info']['name']}", key=f"select_{cust_id}"):
        #         st.session_state["switch_to_customer"] = cust_id
        #         st.session_state["switch_to_tab"] = "chat"
        #         st.rerun()



    else:
        st.info("No customer profiles available. Generate customer profiles from the sidebar first.")


with tab3:
    st.markdown("<div class='sub-header'>📊 Comprehensive Usage Analytics</div>", unsafe_allow_html=True)

    stats = usage_tracker.get_usage_stats()
    google_stats = stats["google_api"]

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Requests",
            value=google_stats["total_requests"],
            help="Total API requests made"
        )

    with col2:
        st.metric(
            label="Total Tokens",
            value=f"{google_stats['total_tokens']:,}",
            help="Total tokens consumed"
        )

    with col3:
        st.metric(
            label="Today's Requests",
            value=google_stats["requests_today"],
            help="API requests made today"
        )

    with col4:
        estimated_cost = usage_tracker.estimate_cost()
        st.metric(
            label="Estimated Cost",
            value=f"${estimated_cost:.4f}",
            help="Approximate cost in USD"
        )

    # Usage breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Usage Trends")
        if google_stats["request_history"]:
            # Create a simple chart of recent usage
            recent_requests = google_stats["request_history"][-20:]  # Last 20 requests
            timestamps = [req["timestamp"].strftime("%H:%M") for req in recent_requests]
            tokens = [req["tokens"] for req in recent_requests]

            chart_data = {
                "Time": timestamps,
                "Tokens": tokens
            }
            st.line_chart(chart_data, x="Time", y="Tokens")
        else:
            st.info("No usage data available yet.")

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
                "Tokens": req["tokens"]
            })

        st.dataframe(activity_data, use_container_width=True)
    else:
        st.info("No recent activity to display.")

    # Usage limits and warnings
    st.markdown("### ⚠️ Usage Monitoring")

    # Daily limits (you can adjust these)
    DAILY_REQUEST_LIMIT = 100
    DAILY_TOKEN_LIMIT = 50000

    request_percentage = (google_stats["requests_today"] / DAILY_REQUEST_LIMIT) * 100
    token_percentage = (google_stats["tokens_today"] / DAILY_TOKEN_LIMIT) * 100

    col1, col2 = st.columns(2)

    with col1:
        st.progress(min(request_percentage / 100, 1.0))
        st.write(f"Daily Requests: {google_stats['requests_today']}/{DAILY_REQUEST_LIMIT} ({request_percentage:.1f}%)")

        if request_percentage > 90:
            st.error("🚨 Approaching daily request limit!")
        elif request_percentage > 70:
            st.warning("⚠️ High request usage today")
        else:
            st.success("✅ Request usage is healthy")

    with col2:
        st.progress(min(token_percentage / 100, 1.0))
        st.write(f"Daily Tokens: {google_stats['tokens_today']:,}/{DAILY_TOKEN_LIMIT:,} ({token_percentage:.1f}%)")

        if token_percentage > 90:
            st.error("🚨 Approaching daily token limit!")
        elif token_percentage > 70:
            st.warning("⚠️ High token usage today")
        else:
            st.success("✅ Token usage is healthy")

    # Cost breakdown
    st.markdown("### 💰 Cost Analysis")

    # Estimate costs for different usage levels
    cost_data = {
        "Usage Level": ["Current", "10x Current", "100x Current"],
        "Requests": [google_stats["total_requests"], google_stats["total_requests"] * 10, google_stats["total_requests"] * 100],
        "Tokens": [google_stats["total_tokens"], google_stats["total_tokens"] * 10, google_stats["total_tokens"] * 100],
        "Estimated Cost": [f"${estimated_cost:.4f}", f"${estimated_cost * 10:.4f}", f"${estimated_cost * 100:.4f}"]
    }

    st.dataframe(cost_data, use_container_width=True)

    # Reset button
    if st.button("🔄 Reset Usage Statistics", type="secondary"):
        # Reset the usage tracker
        usage_tracker.usage_data["google_api"] = {
            "total_requests": 0,
            "total_tokens": 0,
            "requests_today": 0,
            "tokens_today": 0,
            "last_reset": datetime.now().date(),
            "request_history": []
        }
        st.success("Usage statistics have been reset!")
        st.rerun()


# Footer
st.sidebar.markdown("""
<div class="footer">
    <p>Built with ❤️ by raqibcodes for raqibtech.com</p>
</div>
""", unsafe_allow_html=True)
