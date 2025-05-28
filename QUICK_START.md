# 🚀 Quick Start Guide - AI Customer Support Agent

## 🌐 Access Your Application
Open your browser and navigate to: **http://localhost:5000**

## 🔧 Services Status
- **Redis**: Running on port 6379 (Docker)
- **Qdrant**: Running on port 6333 (Docker)
- **Flask App**: Running on port 5000

## 📱 Application Features

### 1. **Unified Support Tab**
- **AI Chat Interface**: Ask questions about customers, orders, analytics
- **Quick Actions**: Pre-built queries for common tasks
- **Example queries**:
  - "Show customers from Lagos"
  - "Show pending orders"
  - "Show revenue analytics"

### 2. **Customer Profiles Tab**
- **Search & Filter**: Find customers by name, state, or tier
- **Nigerian States**: All 36 states + FCT supported
- **Account Tiers**: Bronze, Silver, Gold, Platinum

### 3. **Usage Analytics Tab**
- **API Monitoring**: Track Groq API usage and quotas
- **Performance Metrics**: Response times and cache hit rates
- **Real-time Updates**: Refreshes every 30 seconds

### 4. **Support Dashboard Tab**
- **Business Intelligence**: Revenue by state, customer distribution
- **Order Analytics**: Status distribution, payment methods
- **KPIs**: Total revenue, average order value, top performing states

## 🛠️ Managing Services

### Start All Services (Recommended)
```powershell
.\start_services.ps1
```

### Manual Service Management
```powershell
# Start Redis
docker start redis-server

# Start Qdrant
docker start $(docker ps -aq --filter "ancestor=qdrant/qdrant")

# Start Flask App
python flask_app/run.py
```

### Stop Services
```powershell
# Stop Flask (Ctrl+C in terminal)
# Stop containers
docker stop redis-server
docker stop $(docker ps -aq --filter "ancestor=qdrant/qdrant")
```

## 🔑 Environment Variables
Make sure your `.env` file contains:
```
QDRANT_URL_CLOUD=http://localhost:6333
QDRANT_URL_LOCAL=http://localhost:6333
QDRANT_API_KEY=your-api-key
GROQ_API_KEY=your-groq-key
GOOGLE_API_KEY=your-google-key
```

## 🎯 Testing the AI Chat
Try these sample queries in the Unified Support tab:

1. **Customer Queries**:
   - "Show me customers from Lagos state"
   - "Find customers with Gold tier accounts"
   - "Show customers with payment issues"

2. **Order Queries**:
   - "Show pending orders"
   - "Display orders from this week"
   - "Show delivery status updates"

3. **Analytics Queries**:
   - "Show revenue by state"
   - "Display top performing states"
   - "Show order trends this month"

## 🚨 Troubleshooting

### If Redis is not working:
```powershell
docker run -d --name redis-server -p 6379:6379 redis:latest
```

### If Qdrant is not working:
```powershell
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### If Flask app won't start:
1. Check that Redis and Qdrant are running: `docker ps`
2. Verify your `.env` file has all required variables
3. Check the terminal for error messages

## 📊 Nigerian Market Features
- **Currency**: All amounts displayed in Nigerian Naira (₦)
- **States**: Complete list of 36 Nigerian states + FCT
- **Payment Methods**: Pay on Delivery, Bank Transfer, Card, RaqibTechPay
- **Cultural Context**: AI responses optimized for Nigerian e-commerce

## 🔄 Auto-Refresh Features
- Usage analytics update every 30 seconds
- Real-time API quota monitoring
- Live chat interface with typing indicators

## 📈 Production Deployment
For production use:
```powershell
# Use the production startup script
.\start_services.ps1

# Or use Gunicorn directly
gunicorn -c gunicorn.conf.py flask_app.app:app
```

---
**🎉 Enjoy your AI-Powered Customer Support Agent!**
