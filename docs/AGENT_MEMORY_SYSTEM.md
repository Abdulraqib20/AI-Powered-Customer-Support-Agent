# 🧠 Redis-based Agent Memory System

## Overview

The Agent Memory System provides intelligent, persistent memory capabilities for your customer support AI agents. It enables agents to remember user preferences, learn from conversations, and provide increasingly personalized experiences across both the Flask web app and WhatsApp channels.

## Architecture

The system implements a dual-memory architecture inspired by the [CoALA paper](https://arxiv.org/abs/2309.02427):

### 🔄 Short-term Memory
- **Technology**: LangGraph Redis checkpointer
- **Purpose**: Maintains conversation context within sessions
- **Scope**: Current conversation thread
- **Storage**: Redis with automatic expiration

### 🧠 Long-term Memory
- **Technology**: RedisVL with vector embeddings
- **Purpose**: Persistent learning and user preferences
- **Scope**: Cross-session, cross-channel
- **Storage**: Redis vector database with semantic search

## Memory Types

### 📚 Episodic Memory
- **Definition**: User-specific experiences and preferences
- **Examples**:
  - "User prefers Lagos delivery addresses"
  - "Customer likes Samsung smartphones"
  - "User typically pays with RaqibTechPay"
  - "Customer complained about slow delivery"

### 🌍 Semantic Memory
- **Definition**: General knowledge and domain facts
- **Examples**:
  - "Lagos has same-day delivery available"
  - "Electronics require careful packaging"
  - "Nigerian customers prefer cash on delivery"

## Key Features

### ✨ Intelligent Learning
- **Automatic Extraction**: Identifies preferences from natural conversation
- **Pattern Recognition**: Detects user interests, complaints, and behaviors
- **Confidence Scoring**: Assigns reliability scores to memories
- **Deduplication**: Prevents storing similar memories multiple times

### 🔄 Memory Consolidation
- **Background Processing**: Merges similar memories automatically
- **Optimized Storage**: Reduces redundancy while preserving information
- **Scheduled Consolidation**: Runs periodically for each user

### 🌐 Cross-Channel Consistency
- **Unified User Identity**: Links memories across Flask and WhatsApp
- **Shared Learning**: Insights from one channel benefit the other
- **Seamless Experience**: Users get consistent personalization everywhere

## Integration Points

### 🌐 Flask Web Application
**File**: `src/enhanced_db_querying.py`

```python
# Agent memory is automatically integrated during initialization
enhanced_db = EnhancedDatabaseQuerying()

# Memory context is retrieved for each query
agent_memory_context = self.agent_memory.get_memory_context_for_ai(
    query=user_query,
    user_id=user_id,
    thread_id=session_id,
    max_memories=3
)

# Insights are automatically stored after processing
self._schedule_agent_memory_storage(user_query, session_context, customer_id)
```

### 📱 WhatsApp Integration
**File**: `src/whatsapp_handler.py`

```python
# Agent memory is integrated in the WhatsApp handler
handler = WhatsAppBusinessHandler()

# Memory context enhances responses
agent_memory_context = self._get_agent_memory_context(
    message_content, customer_id, session_id, phone_number
)

# Insights are stored from WhatsApp conversations
self._store_agent_memory_insights(
    message_content, ai_response, customer_id, session_id, phone_number
)
```

## Memory Storage Patterns

### 🎯 Automatic Triggers

The system automatically stores memories when it detects:

#### User Preferences
- **Triggers**: "I like", "I prefer", "I want", "I need", "my favorite"
- **Example**: "I prefer delivery to my office" → Stored as episodic memory

#### Product Interests
- **Triggers**: "show me", "looking for", "interested in", "want to buy"
- **Example**: "Show me smartphones" → Stored as product interest

#### Delivery Preferences
- **Triggers**: "delivery", "shipping", "address", "location"
- **Example**: "Deliver to Lagos Island" → Stored as delivery preference

#### Payment Preferences
- **Triggers**: "payment", "pay", "card", "transfer", "RaqibTechPay"
- **Example**: "I pay with card" → Stored as payment preference

#### Issues and Complaints
- **Triggers**: "problem", "issue", "complaint", "not working", "error"
- **Example**: "My order was delayed" → Stored as customer issue

### 🎯 Manual Storage (Tool-based)

For LangGraph agents, memory can be managed via tools:

```python
from src.agent_memory_system import store_memory_tool, retrieve_memories_tool

# Store a memory
store_memory_tool.invoke({
    "content": "User prefers premium delivery options",
    "memory_type": MemoryType.EPISODIC,
    "metadata": {"confidence": 0.9}
})

# Retrieve relevant memories
retrieve_memories_tool.invoke({
    "query": "delivery preferences",
    "memory_type": [MemoryType.EPISODIC],
    "limit": 5
})
```

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional: Custom embedding model
AGENT_MEMORY_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Dependencies

Add to `requirements.txt`:
```
langgraph==0.2.50
langgraph-checkpoint==2.0.8
langgraph-checkpoint-redis==2.0.8
redisvl==0.3.8
sentence-transformers==3.0.1
ulid-py==1.1.0
```

## Usage Examples

### 🔍 Retrieving User Context

```python
from src.agent_memory_system import get_agent_memory_system

memory_system = get_agent_memory_system()

# Get personalized context for AI responses
context = memory_system.get_memory_context_for_ai(
    query="Where should I deliver this order?",
    user_id="customer@example.com",
    max_memories=3
)

# Example output:
# 🧠 RELEVANT USER MEMORIES:
#   • User prefers delivery to Lagos Island office
#   • Customer typically available for delivery after 5 PM
#   • User requested SMS notifications for deliveries
```

### 📝 Storing User Insights

```python
from src.agent_memory_system import MemoryType

# Store a user preference
success = memory_system.store_memory(
    content="Customer prefers Samsung phones over other brands",
    memory_type=MemoryType.EPISODIC,
    user_id="customer@example.com",
    confidence_score=0.8
)
```

### 📊 Memory Analytics

```python
# Get memory statistics for a user
stats = memory_system.get_memory_stats("customer@example.com")

# Example output:
# {
#     "user_id": "customer@example.com",
#     "episodic_memories": 15,
#     "semantic_memories": 3,
#     "total_memories": 18,
#     "last_updated": "2025-01-15T10:30:00"
# }
```

## Performance Considerations

### 🚀 Optimization Features

- **Vector Embeddings**: Enable semantic similarity search
- **Background Consolidation**: Prevents memory bloat
- **Confidence Scoring**: Prioritizes high-quality memories
- **Distance Thresholds**: Controls memory relevance
- **Automatic Deduplication**: Prevents redundant storage

### 📈 Scaling

- **Redis Clustering**: Supports horizontal scaling
- **Memory Limits**: Configurable per-user memory limits
- **TTL Settings**: Automatic cleanup of old memories
- **Batch Processing**: Efficient bulk memory operations

## Monitoring and Debugging

### 📊 Logging

The system provides comprehensive logging:

```python
# Memory operations are logged with appropriate levels
logger.info("🤖 Added agent memory context for user {user_id}")
logger.warning("⚠️ Failed to get agent memory context: {error}")
logger.error("❌ Error storing memory: {error}")
```

### 🔍 Memory Inspection

```python
# Retrieve all memories for debugging
all_memories = memory_system.retrieve_memories(
    query="",  # Empty query gets all
    user_id="customer@example.com",
    distance_threshold=1.0,  # Include all memories
    limit=100
)

# Inspect memory content
for memory in all_memories:
    print(f"[{memory.memory_type}] {memory.content}")
    print(f"  Created: {memory.created_at}")
    print(f"  Confidence: {memory.confidence_score}")
```

## Testing

### 🧪 Running Tests

```bash
# Run the integration test suite
python test_agent_memory_integration.py
```

### ✅ Test Coverage

The test suite validates:
- Basic memory storage and retrieval
- Flask app integration
- WhatsApp handler integration
- Cross-channel memory consistency
- LangGraph tool functionality

## Troubleshooting

### Common Issues

#### ❌ "RedisVL not available"
**Solution**: Install dependencies
```bash
pip install redisvl sentence-transformers
```

#### ❌ "Redis connection failed"
**Solution**: Start Redis server
```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:latest

# Or install Redis locally
redis-server
```

#### ❌ "Memory not persisting"
**Solution**: Check Redis configuration and ensure it's not running in-memory mode

#### ❌ "Slow memory retrieval"
**Solution**: Verify vector index is created properly and consider adjusting distance thresholds

### 🔧 Configuration Tuning

```python
# Adjust memory system parameters
memory_system = AgentMemorySystem(
    embedding_model="sentence-transformers/all-mpnet-base-v2",  # Higher quality embeddings
    distance_threshold=0.2,  # Stricter similarity matching
    consolidation_interval=300  # More frequent consolidation (5 minutes)
)
```

## Best Practices

### 💡 Memory Design

1. **Be Specific**: Store concrete, actionable preferences
   - ✅ "User prefers Lagos Island delivery"
   - ❌ "User likes stuff"

2. **Include Context**: Add relevant metadata
   - Include confidence scores
   - Add source information
   - Timestamp important events

3. **Balance Granularity**: Not too broad, not too narrow
   - ✅ "Customer prefers Samsung Galaxy series"
   - ❌ "Customer likes phones" (too broad)
   - ❌ "Customer likes Galaxy S23 256GB Blue" (too narrow)

### 🔄 Integration Patterns

1. **Pre-processing**: Get memory context before AI generation
2. **Post-processing**: Store insights after AI responses
3. **Cross-reference**: Use memories to validate AI suggestions
4. **Gradual Learning**: Build memories over multiple interactions

### 🎯 Personalization Strategy

1. **Start Simple**: Begin with basic preferences
2. **Build Gradually**: Layer complexity over time
3. **Validate Assumptions**: Confirm preferences with users
4. **Respect Privacy**: Store only relevant business information

## Future Enhancements

### 🔮 Roadmap

- **Multi-modal Memory**: Support for image and voice memories
- **Temporal Reasoning**: Time-aware memory retrieval
- **Collaborative Filtering**: Learn from similar users
- **Explainable AI**: Show users what the system remembers
- **Memory Export**: Allow users to download their memory data
- **Advanced Consolidation**: ML-powered memory merging

### 🚀 Extensibility

The system is designed for easy extension:

```python
# Custom memory types
class CustomMemoryType(str, Enum):
    FINANCIAL = "financial"
    BEHAVIORAL = "behavioral"

# Custom storage patterns
def store_financial_memory(transaction_data):
    # Custom logic for financial insights
    pass

# Custom retrieval strategies
def get_behavioral_insights(user_id):
    # Custom behavioral analysis
    pass
```

## Conclusion

The Redis-based Agent Memory System transforms your customer support from reactive to proactive, enabling truly personalized experiences that improve over time. By remembering user preferences and learning from every interaction, your agents become more helpful, efficient, and customer-focused.

The system's cross-channel architecture ensures consistent experiences whether customers interact via the Flask web app or WhatsApp, building stronger relationships and driving better business outcomes.

---

**Need Help?**
- Check the test suite: `python test_agent_memory_integration.py`
- Review the logs for detailed debugging information
- Ensure Redis is running and properly configured
- Verify all dependencies are installed correctly
