import streamlit as st
from mem0 import Memory
import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from groq import Groq

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
GEMINI_MODEL_NAME = "gemini/gemini-2.0-flash"
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
# GROQ_MODEL_NAME = "mixtral-8x7b-32768"

#--------------------------------------
# Streamlit App Initialization
#--------------------------------------
# Set page configuration
st.set_page_config(
    page_title="AI Customer Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(""" 
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
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
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 65vh;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid rgba(49, 51, 63, 0.2);
    }
    
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
</style>
""", unsafe_allow_html=True)


st.markdown("<div class='main-header'>🤖 AI-Powered Customer Support Agent with Memory</div>", unsafe_allow_html=True)
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
        # "vector_store": None,
    }

# Initialize persistent state
persistent_state = get_persistent_state()

class CustomerSupportAIAgent:
    def test_qdrant_connection():
        try:
            client = QdrantClient(
                url=QDRANT_URL_LOCAL,
                timeout=10
            )
            collections = client.get_collections()
            print("Connection successful! Collections:", collections)
            return True
        except Exception as e:
            print("Connection failed:", e)
            return False

    if test_qdrant_connection():
        print("Qdrant is ready!")
    else:
        print("Please start Qdrant first: docker run -p 6333:6333 qdrant/qdrant")
    
    def __init__(self, model_choice):
        # Initialize Mem0 with Qdrant as the vector store
        config = {
            "llm": {
                "provider": "groq",
                "config": {
                    "model": GROQ_MODEL_NAME,
                    "api_key": GROQ_API_KEY,
                    "temperature": 0.1,
                    "max_tokens": 1000,
                }
            },
            "embeddings": {
                "provider": "google",
                "model": GEMINI_EMBEDDING_MODEL,
                # "api_key": GOOGLE_API_KEY,
                "params": {
                    "api_key": GOOGLE_API_KEY,
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
            # "vector_store": {
            #     "provider": "qdrant",
            #     "config": {
            #         "url": QDRANT_URL_CLOUD,
            #         "api_key": QDRANT_API_KEY,
                    
            #     }
            # },
        }
        try:
            # st.write("Attempting to initialize memory with config:", config)
            self.memory = Memory.from_config(config)
        except Exception as e:
            st.error(f"Failed to initialize memory: {e}")
            import traceback
            st.error(traceback.format_exc())
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

            groq_client = Groq(api_key=GROQ_API_KEY)
            
            full_prompt = f"{context}\nCustomer: {query}\nSupport Agent:"
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a customer support AI agent for TechGadgets.com, an online electronics store."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            answer = response.choices[0].message.content

            # Add the query and answer to memory
            self.memory.add(query, user_id=user_id, metadata={"app_id": self.app_id, "role": "user"})
            self.memory.add(answer, user_id=user_id, metadata={"app_id": self.app_id, "role": "assistant"})

            return answer
        except Exception as e:
            st.error(f"An error occurred while handling the query: {e}")
            import traceback
            st.error(traceback.format_exc())
            return "Sorry, I encountered an error. Please try again later."
    
    
    def get_memories(self, user_id=None):
        try:
            # Retrieve all memories for a user
            return self.memory.get_all(user_id=user_id)
        except Exception as e:
            st.error(f"Failed to retrieve memories: {e}")
            return None

    def generate_synthetic_data(self, user_id: str) -> dict | None:
        try:
            today = datetime.now()
            order_date = (today - timedelta(days=10)).strftime("%B %d, %Y")
            expected_delivery = (today + timedelta(days=2)).strftime("%B %d, %Y")
            groq_client = Groq(api_key=GROQ_API_KEY)
            
            prompt = f"""Generate a detailed Nigerian customer profile for raqibtech customer ID {user_id}. 
            Format as JSON with this structure:
            {{
                "customer_info": {{
                    "name": "Akanbi Omotosho",
                    "email": "omotosho@gmail.com",
                    "shipping_address": "Victoria Island, Wuse 2, Mile One, Port Harcourt",
                    "phone": "0803-123-4567"
                }},
                "current_order": {{
                    "order_date": "{order_date}",
                    "expected_delivery": "{expected_delivery}",
                    "products": [
                        {{"name": "Smartphone", "price": ₦150,000}}
                    ]
                }},
                "order_history": [
                    {{"date": "2023-01-15", "total": ₦100,000}}
                ]
            }}
            Only respond with valid JSON, no markdown formatting."""
            
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a Nigerian e-commerce data generator. Use common Nigerian formats and pidgin where appropriate."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} 
            )
            
            # Handle markdown formatting and validate JSON
            raw_content = response.choices[0].message.content
            
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

            return customer_data
            
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON response from model: {e}\nRaw response: {raw_content}")
            return None
        except Exception as e:
            st.error(f"Failed to generate synthetic data: {e}")
            return None

st.sidebar.markdown("<div class='sidebar-header'>🔧 Settings</div>", unsafe_allow_html=True)
model_choice = "Groq" 

# Customer ID 
st.sidebar.markdown("<div class='sidebar-header'>👤 Customer Details</div>", unsafe_allow_html=True)
previous_customer_id = st.session_state.get("previous_customer_id", None)
customer_id = st.sidebar.text_input("Enter your Customer ID", key="customer_id_input")

if customer_id != previous_customer_id:
    st.session_state.messages = []
    st.session_state.previous_customer_id = customer_id
    st.session_state.customer_data = None

# Initialize the CustomerSupportAIAgent with groq model
support_agent = CustomerSupportAIAgent(model_choice)

# Sidebar buttons
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("Generate Data", key="gen_data"):
        if customer_id:
            with st.spinner("Generating customer data..."):
                st.session_state.customer_data = support_agent.generate_synthetic_data(customer_id)
            if st.session_state.customer_data:
                st.sidebar.success("Data generated successfully!")
            else:
                st.sidebar.error("Failed to generate data.")
        else:
            st.sidebar.error("Please enter a customer ID first.")

with col2:
    if st.button("View Memory", key="view_mem"):
        if customer_id:
            memories = support_agent.get_memories(user_id=customer_id)
            if memories and "results" in memories and len(memories["results"]) > 0:
                st.session_state.show_memories = True
            else:
                st.sidebar.info("No memory found for this customer.")
        else:
            st.sidebar.error("Please enter a customer ID first.")

# Customer profile tab
if st.sidebar.button("View Customer Profile", key="view_profile"):
    if hasattr(st.session_state, 'customer_data') and st.session_state.customer_data:
        st.sidebar.markdown("<div class='sidebar-header'>📊 Customer Profile</div>", unsafe_allow_html=True)
        st.sidebar.json(st.session_state.customer_data)
    else:
        st.sidebar.info("No customer data yet. Generate data first.")

# Main chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display memory tab if requested
if hasattr(st.session_state, 'show_memories') and st.session_state.show_memories:
    with st.expander("Memory History", expanded=True):
        memories = support_agent.get_memories(user_id=customer_id)
        if memories and "results" in memories:
            for i, memory in enumerate(memories["results"]):
                if "memory" in memory:
                    st.markdown(f"<div class='source-card'>Memory {i+1}: {memory['memory']}</div>", unsafe_allow_html=True)

# Create a custom chat container
st.markdown("<div class='chat-container' id='chat-container'>", unsafe_allow_html=True)

# Display the chat history
for message in st.session_state.messages:
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

st.markdown("</div>", unsafe_allow_html=True)

# Chat input
if customer_id:
    query = st.chat_input("How can I assist you today?", key="chat_input")
    
    if query:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        st.rerun()
else:
    st.info("Please enter your Customer ID in the sidebar to start chatting.")

# Process any pending query
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    # Last message is from user, generate response
    with st.spinner("Thinking..."):
        answer = support_agent.handle_query(st.session_state.messages[-1]["content"], user_id=customer_id)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# Auto-scroll to bottom of chat
st.markdown("""
<script>
    function scrollToBottom() {
        var chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    setTimeout(scrollToBottom, 500);
</script>
""", unsafe_allow_html=True)

# Footer
st.sidebar.markdown("""
<div class="footer">
    <p>Built with ❤️ by raqibcodes for TechGadgets.com</p>
</div>
""", unsafe_allow_html=True)