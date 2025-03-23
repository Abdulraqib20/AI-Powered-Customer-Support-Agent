# ðŸš€ AI-Powered-Customer-Support-Agent

This application is a Nigerian-based e-commerce customer support agent designed to deliver context-aware, intelligent assistance while keeping track of every conversation along the way.

## âœ¨ Features
1ï¸âƒ£ Meta's Llama 3.3 70-B model via Groq 

â€”Generates the profiles for different customer IDs
â€”Enables the agent to comprehend and respond to complex customer queries.
â€”Provides in-depth answers addressing order details, payment-related, product-related, account-related and service issues tailored to the Nigerian market.

2ï¸âƒ£ mem0 (Mem0) 

â€”Serves as the memory layer for the system as it manages conversation history to ensure continuity in customer interactions.
â€”Helps the support agent recall previous details, making each conversation feel more personal and informed.

3ï¸âƒ£ Qdrant Vector DB

â€”Enables efficient similarity searches, ensuring that responses are both timely and contextually accurate.
â€”Quickly retrieves relevant past interactions, making the convo better and more accurate.

4ï¸âƒ£ Google's Embedding models

â€”Converts text into vector representations which improves matching of customer queries with right responses
â€”Enhances the agent's understanding of customer queries, leading to more accurate responses.

## ðŸ› ï¸ Installation
`ash
git clone https://github.com/Abdulraqib20/AI-Powered-Customer-Support-Agent.git
cd AI-Powered-Customer-Support-Agent
pip install -r requirements.txt
`

## âš™ï¸ Configuration
Create .env file with:
QDRANT_URL_LOCAL="your-qdrant-local-host"
GROQ_API_KEY="groq-api-key"
GOOGLE_API_KEY="google-key"

## ðŸ“§ Support
Report issues at: https://github.com/Abdulraqib20/AI-Powered-Customer-Support-Agent/issues
