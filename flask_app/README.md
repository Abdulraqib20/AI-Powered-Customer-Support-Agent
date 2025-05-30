#   Nigerian E-commerce Customer Support Agent - Flask Web Application

A comprehensive AI-powered customer support web application designed specifically for Nigerian e-commerce platforms. This Flask application replaces the Streamlit prototype with a production-ready, scalable solution featuring real-time AI chat, customer management, analytics, and Nigerian market-specific optimizations.

## 🌟 Features

### 🤖 AI-Powered Support
- **Groq LLaMA 3.1 8B Integration**: Fast, context-aware conversational AI
- **Mem0 Memory Management**: Persistent conversation context across sessions
- **Qdrant Vector Database**: Semantic search for relevant customer data
- **Google Text-Embedding-004**: Advanced text embeddings for context understanding

### 🎯 Nigerian Market Focus
- **Naira Currency Formatting**: Proper ₦ formatting and calculations
- **Nigerian States Support**: Complete list of 36 states + FCT
- **Local Payment Methods**: Pay on Delivery, Bank Transfer, Card, RaqibTechPay
- **Cultural Awareness**: Nigerian English, local naming conventions
- **Lagos-Abuja-Kano Optimization**: Focus on major commercial centers

### 📊 Comprehensive Dashboard
1. **Unified Support Tab**: AI chat interface with quick actions
2. **Customer Profiles Tab**: Search, filter, and manage customer data
3. **Usage Analytics Tab**: API usage monitoring and performance metrics
4. **Support Dashboard Tab**: Business intelligence and revenue analytics

### 🚀 Performance & Scalability
- **Sub-second Response Times**: Optimized API calls and caching
- **99.9% Uptime Target**: Robust error handling and failover
- **1,000+ Concurrent Users**: Gunicorn multi-threading support
- **Redis Caching**: Intelligent response caching and session management

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11+ (recommended 3.12)
- **PostgreSQL**: 12+ with existing Nigerian e-commerce database
- **Redis**: 6+ for caching and session management
- **Node.js**: 16+ (optional, for advanced frontend tooling)

### AI Service Accounts
- **Groq API Key**: For LLaMA 3.1 8B model access
- **Google AI API Key**: For Text-Embedding-004 model
- **Qdrant Cloud Account**: For vector database hosting
- **Mem0 Account**: For conversation memory management

## 🛠️ Installation & Setup

### 1. Clone and Navigate
```bash
cd flask_app/
```

### 2. Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(Flask|groq|redis|psycopg2)"
```

### 4. Environment Configuration
```bash
# Copy environment template
cp ../.env_example .env

# Edit .env file with your credentials
```

**Required Environment Variables:**
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nigerian_ecommerce
DB_USER=postgres
DB_PASSWORD=your_password

# AI Service APIs
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_ai_key
QDRANT_URL_CLOUD=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 5. Database Setup
```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Verify database connection
python -c "from config.database_config import test_database_connection; test_database_connection()"
```

### 6. Redis Setup
```bash
# Install and start Redis
# Ubuntu/Debian:
sudo apt install redis-server
sudo systemctl start redis-server

# macOS:
brew install redis
brew services start redis

# Windows: Download from https://redis.io/download

# Test Redis connection
redis-cli ping  # Should return "PONG"
```

### 7. AI Services Verification
```bash
# Test AI integrations
python -c "
from flask_app.app import groq_client, qdrant_client
print('✅ Groq client initialized:', bool(groq_client))
print('✅ Qdrant client initialized:', bool(qdrant_client))
"
```

## 🚀 Running the Application

### Development Mode
```bash
# Standard Flask development server
python app.py

# Or using Flask CLI
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000 --debug
```

### Production Mode
```bash
# Using Gunicorn (recommended for production)
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet app:app

# Or with custom configuration
gunicorn --config gunicorn.conf.py app:app
```

### Docker Deployment (Optional)
```bash
# Build Docker image
docker build -t nigerian-support-agent .

# Run with Docker Compose
docker-compose up -d
```

## 🎯 Usage Guide

### 1. Accessing the Application
- **Local Development**: http://localhost:5000
- **Production**: https://your-domain.com

### 2. Dashboard Navigation
1. **Unified Support**: Start here for AI-powered customer assistance
2. **Customer Profiles**: Manage and search customer database
3. **Usage Analytics**: Monitor API usage and performance
4. **Support Dashboard**: View business metrics and KPIs

### 3. AI Chat Examples
```
🗣️ Example Queries:
"Show customers from Lagos with pending orders"
"What's the total revenue from Abuja this month?"
"Find customers with payment issues"
"Show top-performing states by order volume"
"Help resolve delivery issues for customer ID 12345"
```

### 4. Quick Actions
- **Payment Resolution**: Automated payment issue detection and resolution
- **Delivery Tracking**: Real-time order status updates
- **Customer Insights**: AI-powered customer behavior analysis
- **Revenue Analytics**: Nigerian state-wise performance metrics

## 🔧 Configuration

### Database Configuration
```python
# Located in: config/database_config.py
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
}
```

### AI Configuration
```python
# Groq API Settings
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_MAX_TOKENS = 1024
GROQ_TEMPERATURE = 0.7

# Google AI Settings
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSIONS = 768

# Qdrant Settings
COLLECTION_NAME = "nigerian_customer_data"
VECTOR_SIZE = 768
```

### Caching Configuration
```python
# Redis Cache Settings
CACHE_TIMEOUT = 1800  # 30 minutes
EMBEDDING_CACHE_TIMEOUT = 3600  # 1 hour
API_RESPONSE_CACHE_TIMEOUT = 1800  # 30 minutes
```

## 📊 API Documentation

### Customer Management
```http
GET /api/customers?search=name&state=Lagos&tier=Gold
POST /api/customers
```

### Order Management
```http
GET /api/orders?status=Pending&customer_id=123
POST /api/orders
```

### Analytics
```http
GET /api/analytics?type=summary
GET /api/analytics?type=usage
```

### AI Chat
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Show customers from Lagos",
  "user_id": "session_123"
}
```

## 🔍 Monitoring & Logging

### Log Locations
```
config/logs/
├── app.log          # Application logs
├── api.log          # API request logs
├── error.log        # Error logs
└── config.log       # Configuration logs
```

### Metrics Monitoring
- **Response Times**: Average API response times
- **Error Rates**: 4xx/5xx error tracking
- **API Usage**: Groq/Google AI quota monitoring
- **Database Performance**: Query execution times
- **Cache Hit Rates**: Redis cache effectiveness

### Health Checks
```bash
# Application health
curl http://localhost:5000/api/health

# Database connectivity
python -c "from config.database_config import test_database_connection; test_database_connection()"

# Redis connectivity
redis-cli ping
```

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify database exists
psql -h localhost -U postgres -l | grep nigerian_ecommerce

# Test connection
python -c "import psycopg2; psycopg2.connect(host='localhost', database='nigerian_ecommerce', user='postgres')"
```

**2. Redis Connection Issues**
```bash
# Check Redis status
redis-cli ping

# Restart Redis
sudo systemctl restart redis-server
```

**3. AI API Errors**
```bash
# Verify API keys
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Groq Key:', bool(os.getenv('GROQ_API_KEY')))
print('Google Key:', bool(os.getenv('GOOGLE_API_KEY')))
"
```

**4. Performance Issues**
- Monitor Groq API quota: 30 requests/minute, 100K tokens/minute
- Check Redis memory usage: `redis-cli info memory`
- Database query optimization: Enable PostgreSQL query logging

### Error Codes
- **500**: Internal server error (check error.log)
- **503**: Service unavailable (AI APIs down)
- **429**: Rate limit exceeded (API quotas)
- **400**: Bad request (invalid parameters)

## 🔒 Security Considerations

### Production Security
1. **Environment Variables**: Never commit .env files
2. **API Key Rotation**: Regularly rotate AI service keys
3. **Database Security**: Use connection pooling and prepared statements
4. **HTTPS**: Always use SSL in production
5. **CORS**: Configure appropriate CORS policies
6. **Rate Limiting**: Implement API rate limiting
7. **Input Validation**: Sanitize all user inputs

### Nigerian Data Privacy
- Comply with Nigeria Data Protection Regulation (NDPR)
- Implement data retention policies
- Ensure customer data encryption
- Provide data export/deletion capabilities

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/nigerian-enhancement`
3. Make changes with Nigerian market focus
4. Test thoroughly with sample Nigerian data
5. Submit pull request with detailed description

### Code Standards
- **Python**: Follow PEP 8, use Black formatter
- **JavaScript**: Use ESLint with Nigerian locale considerations
- **CSS**: BEM methodology with Nigerian color schemes
- **Comments**: Document Nigerian-specific business logic

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🌍 Nigerian Market Compliance

This application is designed to comply with:
- Nigerian Data Protection Regulation (NDPR)
- Central Bank of Nigeria (CBN) payment guidelines
- Nigerian Communications Commission (NCC) data requirements
- Lagos State e-commerce regulations

## 📞 Support

For technical support or Nigerian market-specific questions:
- **GitHub Issues**: [Create an issue](https://github.com/your-repo/issues)
- **Email**: support@nigeriancommerce.com
- **Documentation**: [Full API Documentation](https://docs.nigeriancommerce.com)

---

**Built with ❤️ for the Nigerian E-commerce Market  **

*Empowering Nigerian businesses with AI-powered customer support solutions that understand local context, culture, and commerce patterns.*
