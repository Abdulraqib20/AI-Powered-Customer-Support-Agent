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

## Potential Questions

### Order-Related Questions

"When will my order be delivered?"
"I haven't received my order yet. It's been 5 days since I ordered."
"Can I change my delivery address for order JMT-NG-123456?"
"Is it possible to cancel my current order?"
"I want to return one of the items I received yesterday."

### Payment-Related Questions

"I was charged twice for my last order. How can I get a refund?"
"Can I change my payment method from Pay on Delivery to card payment?"
"My bank shows the payment went through, but my order still says 'Payment Pending'"
"Do you accept Paystack transfers?"
"I'm having trouble completing payment with my GTBank card."

### Product-Related Questions

"Is the Samsung TV still in stock?"
"Does the HP laptop come with Windows installed?"
"What's the warranty period for phones on your platform?"
"Are the appliances compatible with Nigerian voltage?"
"Can I get the iPhone in blue color instead of black?"

### Account-Related Questions

"How can I upgrade to Gold tier membership?"
"I can't log into my account despite using the correct password."
"How do I redeem my raqibtech reward points?"
"I need to update my phone number in my profile."
"Can I create multiple delivery addresses in my account?"

### Nigeria-Specific Questions

"Do you deliver to Mararaba in Nasarawa State?"
"How long does delivery take to Port Harcourt during rainy season?"
"Can I pick up my order from your Lagos warehouse instead of waiting for delivery?"
"Do you have physical stores in Abuja where I can see the products?"
"Will I need to show my NIN for delivery verification?"

docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
