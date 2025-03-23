# AI-Powered Customer Support Agent

A Nigerian-based e-commerce customer support agent designed to deliver context-aware, intelligent assistance while keeping track of every conversation along the way. It works by generating synthetic customer profiles (current order, account information and contact information) for different customer IDs and then simulates individual customer conversations where the agent selects a specific customer profile and interacts as if they were that customer.

## Features
1️⃣ Meta's Llama 3.3 70-B model via Groq 

—Generates the profiles for different customer IDs
—Enables the agent to comprehend and respond to complex customer queries.
—Provides in-depth answers addressing order details, payment-related, product-related, account-related and service issues tailored to the Nigerian market.

2️⃣ mem0 (Mem0) 

—Serves as the memory layer for the system as it manages conversation history to ensure continuity in customer interactions.
—Helps the support agent recall previous details, making each conversation feel more personal and informed.

3️⃣ Qdrant Vector DB

—Enables efficient similarity searches, ensuring that responses are both timely and contextually accurate.
—Quickly retrieves relevant past interactions, making the convo better and more accurate.

4️⃣ Google's Embedding models

—Converts text into vector representations which improves matching of customer queries with right responses
—Enhances the agent's understanding of customer queries, leading to more accurate responses.

## 🛠️ Installation

```bash
git clone https://github.com/Abdulraqib20/AI-Powered-Customer-Support-Agent.git
cd AI-Powered-Customer-Support-Agent
pip install -r requirements.txt
```

## ⚙️ Configuration
Create .env file with:
QDRANT_URL_LOCAL="your-qdrant-local-host"
GROQ_API_KEY="groq-api-key"
GOOGLE_API_KEY="google-key"

## 📧 Support

Report issues at: https://github.com/Abdulraqib20/AI-Powered-Customer-Support-Agent/issues
