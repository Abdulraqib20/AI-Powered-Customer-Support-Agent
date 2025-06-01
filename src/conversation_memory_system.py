#!/usr/bin/env python3
"""
🧠 World-Class Conversation Memory System
===============================================================================

Implements multiple memory types for superior conversation context management:
1. ConversationBufferMemory - Recent raw interactions
2. ConversationSummaryMemory - Summarized distant interactions
3. SemanticMemory - Vector-based contextual understanding
4. SessionStateMemory - Shopping cart and user state
5. EntityMemory - Product and order entity tracking

Based on LangChain memory patterns but optimized for e-commerce conversations.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib
import redis
from enum import Enum
from decimal import Decimal
from cachetools import TTLCache
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up cache configuration
CACHE_MAXSIZE = 500  # Maximum number of conversations in cache
CACHE_TTL = 1800  # Time to live for cache items (30 minutes)
MEMORY_TOKEN_LIMIT = 2000  # Token limit for conversation memory

# Global cache instance using TTLCache for automatic expiration
conversation_cache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)

def print_log(message, level='info'):
    """Logs a message with a specified log level and colors."""
    levels = {
        'info': '\033[94m',   # Blue
        'warning': '\033[93m', # Yellow
        'error': '\033[91m',   # Red
        'success': '\033[92m', # Green
        'reset': '\033[0m'     # Reset color
    }
    color = levels.get(level, levels['info'])
    print(f"{color}[MEMORY] {level.upper()}: {message}{levels['reset']}")

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects"""
    def default(self, obj):
        if hasattr(obj, 'quantize'):  # Check if it's a Decimal
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

def safe_json_dumps(obj, **kwargs):
    """Safe JSON dumps that handles Decimal and datetime objects"""
    return json.dumps(obj, cls=DecimalEncoder, **kwargs)

def safe_json_loads(json_str):
    """Safe JSON loads"""
    if not json_str:
        return None
    return json.loads(json_str)

class MemoryType(Enum):
    BUFFER = "buffer"
    SUMMARY = "summary"
    SEMANTIC = "semantic"
    SESSION = "session"
    ENTITY = "entity"

@dataclass
class ConversationTurn:
    """Single conversation turn (user input + AI response)"""
    timestamp: datetime
    user_input: str
    ai_response: str
    intent: str
    entities: Dict[str, Any]
    session_state: Dict[str, Any]
    turn_id: str
    confidence: float = 0.0

@dataclass
class SessionState:
    """Complete session state including shopping context"""
    session_id: str
    customer_id: Optional[int]
    cart_items: List[Dict[str, Any]]
    checkout_state: Dict[str, Any]
    current_intent: str
    last_product_mentioned: Optional[Dict[str, Any]]
    delivery_address: Optional[Dict[str, str]]
    payment_method: Optional[str]
    conversation_stage: str  # "browsing", "adding_to_cart", "checkout", "placing_order"
    created_at: datetime
    updated_at: datetime

class WorldClassMemorySystem:
    """🧠 World-class conversation memory management system"""

    def __init__(self):
        self.redis_client = self._init_redis()
        self.memory_types = {
            MemoryType.BUFFER: BufferMemory(self.redis_client),
            MemoryType.SUMMARY: SummaryMemory(self.redis_client),
            MemoryType.SEMANTIC: SemanticMemory(self.redis_client),
            MemoryType.SESSION: SessionMemory(self.redis_client),
            MemoryType.ENTITY: EntityMemory(self.redis_client)
        }
        logger.info("🧠 World-Class Memory System initialized successfully")

    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection for memory storage"""
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            client.ping()
            logger.info("✅ Redis memory store connected successfully")
            return client
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using in-memory fallback: {e}")
            return None

    def store_conversation_turn(self, session_id: str, user_input: str,
                              ai_response: str, intent: str, entities: Dict[str, Any],
                              session_state: Dict[str, Any]) -> str:
        """🔄 Store a complete conversation turn across all memory types"""

        turn_id = self._generate_turn_id(session_id, user_input)
        timestamp = datetime.now()

        # Create conversation turn
        turn = ConversationTurn(
            timestamp=timestamp,
            user_input=user_input,
            ai_response=ai_response,
            intent=intent,
            entities=entities,
            session_state=session_state,
            turn_id=turn_id
        )

        # Store in all memory types
        for memory_type, memory_system in self.memory_types.items():
            try:
                memory_system.store_turn(session_id, turn)
                logger.debug(f"✅ Stored turn in {memory_type.value} memory")
            except Exception as e:
                logger.error(f"❌ Failed to store in {memory_type.value} memory: {e}")

        logger.info(f"🔄 Conversation turn stored: {turn_id}")
        return turn_id

    def get_conversation_context(self, session_id: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """🎯 Get comprehensive conversation context for AI response generation"""

        context = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'buffer_memory': {},
            'summary_memory': {},
            'semantic_memory': {},
            'session_state': {},
            'entity_memory': {},
            'total_tokens': 0
        }

        try:
            # Get buffer memory (recent raw conversations)
            buffer_context = self.memory_types[MemoryType.BUFFER].get_context(session_id, max_turns=5)
            context['buffer_memory'] = buffer_context

            # Get summary memory (summarized distant conversations)
            summary_context = self.memory_types[MemoryType.SUMMARY].get_context(session_id)
            context['summary_memory'] = summary_context

            # Get session state (cart, checkout status, etc.)
            session_context = self.memory_types[MemoryType.SESSION].get_context(session_id)
            context['session_state'] = session_context

            # Get entity memory (products, orders mentioned)
            entity_context = self.memory_types[MemoryType.ENTITY].get_context(session_id)
            context['entity_memory'] = entity_context

            # Calculate rough token count
            context_str = json.dumps(context)
            context['total_tokens'] = len(context_str.split()) * 1.3  # Rough token estimation

            logger.info(f"🎯 Retrieved conversation context for {session_id}: ~{context['total_tokens']} tokens")
            return context

        except Exception as e:
            logger.error(f"❌ Error retrieving conversation context: {e}")
            return context

    def update_session_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """📝 Update session state with new information"""
        try:
            return self.memory_types[MemoryType.SESSION].update_state(session_id, updates)
        except Exception as e:
            logger.error(f"❌ Error updating session state: {e}")
            return False

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """📋 Get current session state"""
        try:
            return self.memory_types[MemoryType.SESSION].get_session_state(session_id)
        except Exception as e:
            logger.error(f"❌ Error getting session state: {e}")
            return None

    def clear_session(self, session_id: str) -> bool:
        """🗑️ Clear all memory for a session"""
        success = True
        for memory_type, memory_system in self.memory_types.items():
            try:
                memory_system.clear_session(session_id)
                logger.debug(f"✅ Cleared {memory_type.value} memory for {session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to clear {memory_type.value} memory: {e}")
                success = False

        logger.info(f"🗑️ Session {session_id} memory cleared: {'success' if success else 'partial'}")
        return success

    def clear_session_context(self, session_id: str) -> bool:
        """🧹 Clear session context - alias for clear_session for compatibility"""
        return self.clear_session(session_id)

    def _generate_turn_id(self, session_id: str, user_input: str) -> str:
        """Generate unique turn ID"""
        timestamp = datetime.now().isoformat()
        raw_id = f"{session_id}:{timestamp}:{user_input[:50]}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:12]

    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get conversation history with caching for better performance"""
        start_time = time.time()

        # Check if conversation history is in cache first
        cache_key = f"history_{session_id}_{limit}"
        cached_history = conversation_cache.get(cache_key)

        if cached_history:
            print_log(f"Retrieved conversation history from cache for {session_id} in {time.time() - start_time:.3f}s", 'success')
            return cached_history

        print_log(f"Retrieving conversation history from storage for {session_id}...")

        try:
            history = self.memory_types[MemoryType.BUFFER].get_context(session_id, max_turns=limit*2)['recent_turns']

            # Limit the history to the requested number of turns
            limited_history = history[-limit*2:] if limit else history  # *2 for user+AI pairs

            # Cache the conversation history
            conversation_cache[cache_key] = limited_history

            print_log(f"Conversation history loaded and cached in {time.time() - start_time:.3f}s", 'success')
            return limited_history

        except Exception as e:
            print_log(f"Error getting conversation history: {e}", 'error')
            return []

    def update_conversation_cache(self, session_id: str, user_message: str, ai_response: str):
        """Update conversation cache efficiently"""
        try:
            # Update all relevant cache entries
            for cache_key in list(conversation_cache.keys()):
                if cache_key.startswith(f"history_{session_id}_"):
                    # Remove cached entries for this session to force refresh
                    del conversation_cache[cache_key]

            print_log(f"Conversation cache updated for session {session_id}")

        except Exception as e:
            print_log(f"Error updating conversation cache: {e}", 'error')

    def clear_conversation_cache(self, session_id: Optional[str] = None):
        """Clear conversation cache for specific session or all sessions"""
        try:
            if session_id:
                # Clear cache entries for specific session
                keys_to_remove = [k for k in conversation_cache.keys() if session_id in k]
                for key in keys_to_remove:
                    del conversation_cache[key]
                print_log(f"Cache cleared for session {session_id}")
            else:
                conversation_cache.clear()
                print_log("All conversation caches cleared")
        except Exception as e:
            print_log(f"Error clearing conversation cache: {e}", 'error')

class BufferMemory:
    """🔄 Stores recent raw conversation turns"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.fallback_storage = {}

    def store_turn(self, session_id: str, turn: ConversationTurn):
        """Store conversation turn in buffer"""
        try:
            key = f"buffer:{session_id}"
            turn_data = {
                'turn_id': turn.turn_id,
                'timestamp': turn.timestamp.isoformat(),
                'user_input': turn.user_input,
                'ai_response': turn.ai_response,
                'intent': turn.intent,
                'entities': turn.entities
            }

            if self.redis:
                # Store as list with expiration
                self.redis.lpush(key, safe_json_dumps(turn_data))
                self.redis.ltrim(key, 0, 9)  # Keep only last 10 turns
                self.redis.expire(key, 3600)  # Expire in 1 hour
            else:
                # Fallback to in-memory storage
                if session_id not in self.fallback_storage:
                    self.fallback_storage[session_id] = []
                self.fallback_storage[session_id].insert(0, turn_data)
                self.fallback_storage[session_id] = self.fallback_storage[session_id][:10]
        except Exception as e:
            logger.error(f"❌ Failed to store in buffer memory: {e}")

    def get_context(self, session_id: str, max_turns: int = 5) -> Dict[str, Any]:
        """Get recent conversation context"""
        key = f"buffer:{session_id}"

        try:
            if self.redis:
                turns_data = self.redis.lrange(key, 0, max_turns - 1)
                turns = [safe_json_loads(turn) for turn in turns_data if turn]
            else:
                turns = self.fallback_storage.get(session_id, [])[:max_turns]

            return {
                'recent_turns': turns,
                'turn_count': len(turns),
                'last_user_input': turns[0]['user_input'] if turns else None,
                'last_ai_response': turns[0]['ai_response'] if turns else None,
                'recent_intents': [turn['intent'] for turn in turns]
            }
        except Exception as e:
            logger.error(f"❌ Error getting buffer context: {e}")
            return {'recent_turns': [], 'turn_count': 0}

    def clear_session(self, session_id: str):
        """Clear buffer memory for session"""
        if self.redis:
            self.redis.delete(f"buffer:{session_id}")
        else:
            self.fallback_storage.pop(session_id, None)

class SessionMemory:
    """📋 Manages session state including shopping cart and checkout state"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.fallback_storage = {}

    def store_turn(self, session_id: str, turn: ConversationTurn):
        """Update session state based on conversation turn"""
        # Extract session updates from turn
        updates = {
            'last_intent': turn.intent,
            'last_interaction': turn.timestamp.isoformat(),
            'updated_at': turn.timestamp.isoformat()
        }

        # Extract shopping-related updates
        if 'product_info' in turn.entities:
            updates['last_product_mentioned'] = turn.entities['product_info']

        if turn.intent in ['add_to_cart', 'cart_action']:
            updates['conversation_stage'] = 'adding_to_cart'
        elif turn.intent in ['checkout', 'place_order']:
            updates['conversation_stage'] = 'checkout'
        elif turn.intent == 'set_delivery_address':
            updates['conversation_stage'] = 'checkout'
            if 'delivery_address' in turn.entities:
                updates['delivery_address'] = turn.entities['delivery_address']
        elif turn.intent == 'payment_method_selection':
            updates['conversation_stage'] = 'checkout'
            if 'payment_method' in turn.entities:
                updates['payment_method'] = turn.entities['payment_method']

        self.update_state(session_id, updates)

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get current session context"""
        session_state = self.get_session_state(session_id)
        if not session_state:
            return {'session_exists': False}

        return {
            'session_exists': True,
            'customer_id': session_state.customer_id,
            'cart_items': session_state.cart_items,
            'cart_item_count': len(session_state.cart_items),
            'checkout_state': session_state.checkout_state,
            'current_intent': session_state.current_intent,
            'last_product_mentioned': session_state.last_product_mentioned,
            'delivery_address': session_state.delivery_address,
            'payment_method': session_state.payment_method,
            'conversation_stage': session_state.conversation_stage,
            'session_duration': (datetime.now() - session_state.created_at).total_seconds()
        }

    def update_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session state"""
        try:
            # Get current state or create new
            current_state = self.get_session_state(session_id)
            if not current_state:
                current_state = SessionState(
                    session_id=session_id,
                    customer_id=updates.get('customer_id'),
                    cart_items=[],
                    checkout_state={},
                    current_intent='general',
                    last_product_mentioned=None,
                    delivery_address=None,
                    payment_method=None,
                    conversation_stage='browsing',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

            # Apply updates
            for key, value in updates.items():
                if hasattr(current_state, key):
                    setattr(current_state, key, value)

            current_state.updated_at = datetime.now()

            # Store updated state
            key = f"session:{session_id}"
            state_data = asdict(current_state)

            # Convert datetime objects to strings and handle Decimal objects
            for k, v in state_data.items():
                if isinstance(v, datetime):
                    state_data[k] = v.isoformat()
                elif isinstance(v, Decimal):
                    state_data[k] = float(v)

            if self.redis:
                self.redis.setex(key, 7200, safe_json_dumps(state_data))  # 2 hour expiration
            else:
                self.fallback_storage[session_id] = state_data

            return True

        except Exception as e:
            logger.error(f"❌ Error updating session state: {e}")
            return False

    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get session state object"""
        try:
            key = f"session:{session_id}"

            if self.redis:
                state_data = self.redis.get(key)
                if not state_data:
                    return None
                state_data = safe_json_loads(state_data)
            else:
                state_data = self.fallback_storage.get(session_id)
                if not state_data:
                    return None

            # Convert string dates back to datetime
            for date_field in ['created_at', 'updated_at']:
                if date_field in state_data and isinstance(state_data[date_field], str):
                    state_data[date_field] = datetime.fromisoformat(state_data[date_field])

            return SessionState(**state_data)

        except Exception as e:
            logger.error(f"❌ Error getting session state: {e}")
            return None

    def clear_session(self, session_id: str):
        """Clear session memory"""
        if self.redis:
            self.redis.delete(f"session:{session_id}")
        else:
            self.fallback_storage.pop(session_id, None)

class SummaryMemory:
    """📄 Summarizes and stores distant conversation history"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.fallback_storage = {}

    def store_turn(self, session_id: str, turn: ConversationTurn):
        """Store turn and trigger summarization if needed"""
        try:
            # For now, just store key information
            # In production, would implement LLM-based summarization
            key = f"summary:{session_id}"

            summary_data = {
                'last_updated': turn.timestamp.isoformat(),
                'total_interactions': self._increment_interaction_count(session_id),
                'key_topics': self._extract_key_topics(turn),
                'important_entities': self._extract_important_entities(turn)
            }

            if self.redis:
                self.redis.setex(key, 86400, safe_json_dumps(summary_data))  # 24 hour expiration
            else:
                self.fallback_storage[session_id] = summary_data
        except Exception as e:
            logger.error(f"❌ Failed to store in summary memory: {e}")

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation summary"""
        key = f"summary:{session_id}"

        try:
            if self.redis:
                summary_data = self.redis.get(key)
                if summary_data:
                    return safe_json_loads(summary_data)
            else:
                return self.fallback_storage.get(session_id, {})

            return {'summary_available': False}

        except Exception as e:
            logger.error(f"❌ Error getting summary context: {e}")
            return {'summary_available': False}

    def _increment_interaction_count(self, session_id: str) -> int:
        """Increment and return interaction count"""
        count_key = f"summary_count:{session_id}"
        if self.redis:
            return self.redis.incr(count_key)
        else:
            current_count = self.fallback_storage.get(f"{session_id}_count", 0)
            self.fallback_storage[f"{session_id}_count"] = current_count + 1
            return current_count + 1

    def _extract_key_topics(self, turn: ConversationTurn) -> List[str]:
        """Extract key topics from conversation turn"""
        topics = []

        if 'product' in turn.user_input.lower():
            topics.append('product_inquiry')
        if any(word in turn.user_input.lower() for word in ['cart', 'add', 'buy']):
            topics.append('shopping')
        if any(word in turn.user_input.lower() for word in ['checkout', 'order', 'purchase']):
            topics.append('ordering')
        if any(word in turn.user_input.lower() for word in ['delivery', 'address', 'shipping']):
            topics.append('delivery')
        if any(word in turn.user_input.lower() for word in ['payment', 'pay', 'card']):
            topics.append('payment')

        return topics

    def _extract_important_entities(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Extract important entities"""
        entities = {}

        if 'product_info' in turn.entities:
            entities['last_product'] = turn.entities['product_info']
        if 'delivery_address' in turn.entities:
            entities['delivery_address'] = turn.entities['delivery_address']
        if 'payment_method' in turn.entities:
            entities['payment_method'] = turn.entities['payment_method']

        return entities

    def clear_session(self, session_id: str):
        """Clear summary memory"""
        if self.redis:
            self.redis.delete(f"summary:{session_id}")
            self.redis.delete(f"summary_count:{session_id}")
        else:
            self.fallback_storage.pop(session_id, None)
            self.fallback_storage.pop(f"{session_id}_count", None)

class SemanticMemory:
    """🔍 Vector-based semantic understanding of conversations"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.fallback_storage = {}

    def store_turn(self, session_id: str, turn: ConversationTurn):
        """Store semantic representation of turn"""
        try:
            # For now, store keyword-based semantic info
            # In production, would use vector embeddings
            semantic_data = {
                'intent': turn.intent,
                'keywords': self._extract_keywords(turn.user_input),
                'semantic_context': self._analyze_semantic_context(turn),
                'timestamp': turn.timestamp.isoformat()
            }

            key = f"semantic:{session_id}:{turn.turn_id}"

            if self.redis:
                self.redis.setex(key, 3600, safe_json_dumps(semantic_data))
            else:
                self.fallback_storage[f"{session_id}:{turn.turn_id}"] = semantic_data
        except Exception as e:
            logger.error(f"❌ Failed to store in semantic memory: {e}")

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get semantic context"""
        # For now, return basic semantic info
        return {
            'semantic_analysis': 'basic_keywords',
            'context_available': True
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords"""
        import re

        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter for important words
        important_words = [
            word for word in words
            if len(word) > 3 and word not in ['this', 'that', 'with', 'from', 'they', 'have', 'been']
        ]

        return important_words[:10]  # Top 10 keywords

    def _analyze_semantic_context(self, turn: ConversationTurn) -> Dict[str, Any]:
        """Analyze semantic context of conversation"""
        return {
            'intent_confidence': turn.confidence,
            'entity_types': list(turn.entities.keys()),
            'interaction_type': self._classify_interaction_type(turn.user_input)
        }

    def _classify_interaction_type(self, text: str) -> str:
        """Classify type of interaction"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['add', 'cart', 'buy']):
            return 'purchase_intent'
        elif any(word in text_lower for word in ['checkout', 'order', 'place']):
            return 'transaction_intent'
        elif any(word in text_lower for word in ['price', 'cost', 'how much']):
            return 'inquiry_intent'
        elif any(word in text_lower for word in ['help', 'support', 'problem']):
            return 'support_intent'
        else:
            return 'general_intent'

    def clear_session(self, session_id: str):
        """Clear semantic memory"""
        if self.redis:
            # Delete all semantic keys for session
            pattern = f"semantic:{session_id}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        else:
            # Clear fallback storage
            keys_to_remove = [k for k in self.fallback_storage.keys() if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del self.fallback_storage[key]

class EntityMemory:
    """🏷️ Tracks entities mentioned in conversations (products, orders, etc.)"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.fallback_storage = {}

    def store_turn(self, session_id: str, turn: ConversationTurn):
        """Store entities from conversation turn"""
        try:
            for entity_type, entity_data in turn.entities.items():
                if entity_type in ['product_info', 'delivery_address', 'payment_method', 'order_info']:
                    self._store_entity(session_id, entity_type, entity_data, turn.timestamp)
        except Exception as e:
            logger.error(f"❌ Failed to store in entity memory: {e}")

    def _store_entity(self, session_id: str, entity_type: str, entity_data: Any, timestamp: datetime):
        """Store individual entity"""
        try:
            key = f"entity:{session_id}:{entity_type}"

            entity_record = {
                'data': entity_data,
                'timestamp': timestamp.isoformat(),
                'type': entity_type
            }

            if self.redis:
                self.redis.setex(key, 7200, safe_json_dumps(entity_record))  # 2 hour expiration
            else:
                self.fallback_storage[key] = entity_record
        except Exception as e:
            logger.error(f"❌ Failed to store entity {entity_type}: {e}")

    def _get_entity(self, session_id: str, entity_type: str) -> Optional[Any]:
        """Get entity data"""
        key = f"entity:{session_id}:{entity_type}"

        try:
            if self.redis:
                entity_record = self.redis.get(key)
                if entity_record:
                    return safe_json_loads(entity_record)['data']
            else:
                entity_record = self.fallback_storage.get(key)
                if entity_record:
                    return entity_record['data']

            return None

        except Exception as e:
            logger.error(f"❌ Error getting entity {entity_type}: {e}")
            return None

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get entity context"""
        try:
            entities = {}
            entity_types = ['product_info', 'delivery_address', 'payment_method', 'order_info']

            for entity_type in entity_types:
                entity_data = self._get_entity(session_id, entity_type)
                if entity_data:
                    entities[entity_type] = entity_data

            return {
                'entities': entities,
                'entity_count': len(entities)
            }

        except Exception as e:
            logger.error(f"❌ Error getting entity context: {e}")
            return {'entities': {}, 'entity_count': 0}

    def clear_session(self, session_id: str):
        """Clear entity memory"""
        if self.redis:
            pattern = f"entity:{session_id}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        else:
            keys_to_remove = [k for k in self.fallback_storage.keys() if k.startswith(f"entity:{session_id}:")]
            for key in keys_to_remove:
                del self.fallback_storage[key]

# Global instance
world_class_memory = WorldClassMemorySystem()
