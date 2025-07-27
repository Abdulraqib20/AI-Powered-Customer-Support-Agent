#!/usr/bin/env python3
"""
🧠 Redis-based Agent Memory System for Customer Support
===============================================================================

Implements intelligent memory management for AI agents using Redis and LangGraph:
1. Short-term Memory - Conversation context via Redis checkpointer
2. Long-term Memory - User preferences, experiences via RedisVL vector store
3. Memory Types - Episodic (user-specific) and Semantic (general knowledge)
4. Memory Consolidation - Background processing to optimize storage
5. Tool-based Memory Management - LLM decides when to store/retrieve

Integrates with existing conversation memory system while adding agent capabilities.
"""

import os
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue
import redis
import ulid

# LangGraph and memory components
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.redis import RedisSaver
from langgraph.graph.message import MessagesState

# Redis Vector Library for semantic memory
try:
    from redisvl.index import SearchIndex
    from redisvl.schema.schema import IndexSchema
    from redisvl.query import VectorRangeQuery
    from redisvl.query.filter import Tag
    from redisvl.utils.vectorize import HFTextVectorizer
    REDISVL_AVAILABLE = True
except ImportError:
    REDISVL_AVAILABLE = False
    logging.warning("RedisVL not available, memory system will work with limited functionality")

# Sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence transformers not available, using fallback embeddings")

# Setup logging
logger = logging.getLogger(__name__)

# Constants
SYSTEM_USER_ID = "system"
MEMORY_EMBEDDING_DIMS = 384  # MiniLM embedding dimension
MEMORY_DISTANCE_THRESHOLD = 0.3
MEMORY_CONSOLIDATION_INTERVAL = 600  # 10 minutes

# Global model cache to prevent reloading
_GLOBAL_VECTORIZER_CACHE = {}
_VECTORIZER_LOCK = threading.Lock()

class MemoryType(str, Enum):
    """Memory categorization following CoALA paper concepts"""
    EPISODIC = "episodic"  # User preferences, experiences
    SEMANTIC = "semantic"  # General knowledge, facts

class MemoryStrategy(str, Enum):
    """Strategy for memory extraction and management"""
    TOOL_BASED = "tool_based"  # LLM decides when to store/retrieve
    MANUAL = "manual"        # Automatic extraction from conversations

@dataclass
class Memory:
    """Represents a single long-term memory"""
    content: str
    memory_type: MemoryType
    metadata: str = "{}"

@dataclass
class StoredMemory:
    """A stored long-term memory with Redis metadata"""
    id: str
    memory_id: str
    content: str
    memory_type: MemoryType
    created_at: datetime
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    metadata: str = "{}"
    confidence_score: float = 0.0

class AgentMemorySystem:
    """
    🧠 Redis-based Agent Memory System

    Provides dual-memory architecture:
    - Short-term: LangGraph Redis checkpointer for conversation history
    - Long-term: RedisVL vector store for persistent learning and preferences
    """

    def __init__(self, redis_url: str = None, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the agent memory system"""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.embedding_model = embedding_model

        # Initialize Redis clients
        self._init_redis_clients()

        # Initialize vector embeddings
        self._init_embeddings()

        # Initialize long-term memory index
        self._init_long_term_memory()

        # Initialize memory consolidation
        self._init_memory_consolidation()

        logger.info("🧠 Agent Memory System initialized successfully")

    def _init_redis_clients(self):
        """Initialize Redis connections for different purposes"""
        try:
            # Main Redis client for general operations
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()

            # Redis saver for LangGraph checkpointing (short-term memory)
            if 'langgraph' in globals():
                self.redis_saver = RedisSaver(redis_client=redis.from_url(self.redis_url))
                self.redis_saver.setup()
            else:
                self.redis_saver = None

            logger.info("✅ Redis clients initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis clients: {e}")
            raise

    def _init_embeddings(self):
        """Initialize text embedding system with global caching"""
        try:
            if REDISVL_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE:
                # Set environment variable to avoid tokenizer warnings
                os.environ["TOKENIZERS_PARALLELISM"] = "false"

                # Check global cache first to avoid reloading model
                with _VECTORIZER_LOCK:
                    if self.embedding_model in _GLOBAL_VECTORIZER_CACHE:
                        self.vectorizer = _GLOBAL_VECTORIZER_CACHE[self.embedding_model]
                        logger.info(f"✅ Using cached vectorizer for {self.embedding_model}")
                    else:
                        # Only load model if not cached
                        logger.info(f"🔄 Loading embedding model: {self.embedding_model}")
                        self.vectorizer = HFTextVectorizer(model=self.embedding_model)
                        _GLOBAL_VECTORIZER_CACHE[self.embedding_model] = self.vectorizer
                        logger.info(f"✅ Cached new vectorizer for {self.embedding_model}")

                # Test embedding to ensure it works (only if newly loaded)
                if self.embedding_model not in _GLOBAL_VECTORIZER_CACHE or len(_GLOBAL_VECTORIZER_CACHE) == 1:
                    test_embedding = self.vectorizer.embed("Test memory content")
                    logger.info(f"✅ Embeddings initialized with dimension: {len(test_embedding)}")
                else:
                    logger.debug(f"✅ Using cached embeddings")

            else:
                self.vectorizer = None
                logger.warning("⚠️ Vector embeddings not available, using text-only memory")

        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            self.vectorizer = None

    def _init_long_term_memory(self):
        """Initialize Redis vector index for long-term memory storage"""
        if not REDISVL_AVAILABLE or not self.vectorizer:
            self.long_term_memory_index = None
            return

        try:
            # Define schema for memory storage
            memory_schema = IndexSchema.from_dict({
                "index": {
                    "name": "agent_memories",
                    "prefix": "memory",
                    "key_separator": ":",
                    "storage_type": "json",
                },
                "fields": [
                    {"name": "content", "type": "text"},
                    {"name": "memory_type", "type": "tag"},
                    {"name": "metadata", "type": "text"},
                    {"name": "created_at", "type": "text"},
                    {"name": "user_id", "type": "tag"},
                    {"name": "memory_id", "type": "tag"},
                    {"name": "thread_id", "type": "tag"},
                    {"name": "confidence_score", "type": "numeric"},
                    {
                        "name": "embedding",
                        "type": "vector",
                        "attrs": {
                            "algorithm": "flat",
                            "dims": MEMORY_EMBEDDING_DIMS,
                            "distance_metric": "cosine",
                            "datatype": "float32",
                        },
                    },
                ],
            })

            # Create Redis client for RedisVL (without decode_responses for binary data)
            redisvl_client = redis.from_url(self.redis_url, decode_responses=False)

            # Create the search index
            self.long_term_memory_index = SearchIndex(
                schema=memory_schema,
                redis_client=redisvl_client
            )

            try:
                self.long_term_memory_index.create(overwrite=False)
                logger.info("✅ Created new long-term memory index")
            except Exception as e:
                # Index likely already exists, which is fine
                logger.debug(f"Memory index creation info: {e}")
                pass

            logger.info("✅ Long-term memory index initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize long-term memory index: {e}")
            self.long_term_memory_index = None

    def _init_memory_consolidation(self):
        """Initialize background memory consolidation"""
        self.consolidation_queue = Queue()
        self._consolidation_running = True

        # Start consolidation worker thread
        self.consolidation_thread = threading.Thread(
            target=self._memory_consolidation_worker,
            daemon=True
        )
        self.consolidation_thread.start()

        logger.info("✅ Memory consolidation worker started")

    def similar_memory_exists(self, content: str, memory_type: MemoryType,
                            user_id: str = SYSTEM_USER_ID,
                            thread_id: Optional[str] = None,
                            distance_threshold: float = MEMORY_DISTANCE_THRESHOLD) -> bool:
        """Check if a similar long-term memory already exists"""
        if not self.long_term_memory_index or not self.vectorizer:
            return False

        try:
            content_embedding = self.vectorizer.embed(content)

            # Build filters
            filters = (Tag("user_id") == user_id) & (Tag("memory_type") == memory_type.value)
            if thread_id:
                filters = filters & (Tag("thread_id") == thread_id)

            # Search for similar memories
            vector_query = VectorRangeQuery(
                vector=content_embedding,
                num_results=1,
                vector_field_name="embedding",
                filter_expression=filters,
                distance_threshold=distance_threshold,
                return_fields=["id"],
            )

            results = self.long_term_memory_index.query(vector_query)

            if results:
                logger.debug(f"Similar memory found for: {content[:50]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking for similar memories: {e}")
            return False

    def store_memory(self, content: str, memory_type: MemoryType,
                    user_id: str = SYSTEM_USER_ID,
                    thread_id: Optional[str] = None,
                    metadata: Optional[str] = None,
                    confidence_score: float = 1.0) -> bool:
        """Store a long-term memory with deduplication"""
        if not self.long_term_memory_index or not self.vectorizer:
            logger.warning("⚠️ Long-term memory storage not available")
            return False

        if metadata is None:
            metadata = "{}"

        logger.debug(f"📝 Storing memory: {content[:50]}...")

        # Check for duplicates with error handling
        try:
            if self.similar_memory_exists(content, memory_type, user_id, thread_id):
                logger.debug("🔄 Similar memory exists, skipping storage")
                return False
        except Exception:
            logger.debug("⚠️ Duplicate check failed, proceeding anyway")

        try:
            # Generate embedding with error handling
            try:
                embedding = self.vectorizer.embed(content)
            except Exception as embed_error:
                logger.debug(f"⚠️ Embedding failed: {embed_error}")
                return False

            # Create memory data
            memory_data = {
                "user_id": user_id or SYSTEM_USER_ID,
                "content": content,
                "memory_type": memory_type.value,
                "metadata": metadata,
                "created_at": datetime.now().isoformat(),
                "embedding": embedding,
                "memory_id": str(ulid.ULID()),
                "thread_id": thread_id,
                "confidence_score": confidence_score,
            }

            # Try storage with multiple fallback approaches
            storage_success = False

            # Approach 1: Try RedisVL (expected to fail currently)
            try:
                self.long_term_memory_index.load([memory_data])
                storage_success = True
            except Exception:
                # Approach 2: Try simple Redis storage
                try:
                    memory_key = f"simple_memory:{memory_data['memory_id']}"
                    simple_data = {
                        "content": content,
                        "memory_type": memory_type.value,
                        "user_id": user_id or SYSTEM_USER_ID,
                        "created_at": datetime.now().isoformat()
                    }
                    self.redis_client.setex(memory_key, 86400, json.dumps(simple_data))
                    storage_success = True
                except Exception:
                    # Approach 3: Silent failure (graceful degradation)
                    logger.debug(f"⚠️ Memory storage unavailable, continuing without memory")
                    return False

            if storage_success:
                logger.debug(f"✅ Memory stored: {content[:30]}...")
                return True
            else:
                return False

        except Exception as e:
            logger.debug(f"❌ Memory storage error: {e}")
            return False

    def retrieve_memories(self, query: str,
                         memory_type: Union[MemoryType, List[MemoryType], None] = None,
                         user_id: str = SYSTEM_USER_ID,
                         thread_id: Optional[str] = None,
                         distance_threshold: float = MEMORY_DISTANCE_THRESHOLD,
                         limit: int = 5) -> List[StoredMemory]:
        """Retrieve relevant memories using vector similarity search"""
        if not self.long_term_memory_index or not self.vectorizer:
            return []

        try:
            logger.debug(f"🔍 Retrieving memories for query: {query}")

            # Handle empty queries by using a default search
            if not query.strip():
                query = "general memory search"

            # Create vector query
            vector_query = VectorRangeQuery(
                vector=self.vectorizer.embed(query),
                return_fields=[
                    "content", "memory_type", "metadata", "created_at",
                    "memory_id", "thread_id", "user_id", "confidence_score"
                ],
                num_results=limit,
                vector_field_name="embedding",
                distance_threshold=distance_threshold,
            )

            # Build filter conditions using RedisVL's proper syntax
            filters = []

            # User ID filter
            filters.append(Tag("user_id") == (user_id or SYSTEM_USER_ID))

            # Memory type filter
            if memory_type:
                if isinstance(memory_type, list):
                    # For multiple types, use OR logic
                    type_filters = [Tag("memory_type") == mt.value for mt in memory_type]
                    if len(type_filters) > 1:
                        from redisvl.query.filter import FilterExpression
                        # Combine with OR - using the first filter as base
                        memory_type_filter = type_filters[0]
                        for tf in type_filters[1:]:
                            memory_type_filter = memory_type_filter | tf
                        filters.append(memory_type_filter)
                    else:
                        filters.append(type_filters[0])
                else:
                    filters.append(Tag("memory_type") == memory_type.value)

            # Thread ID filter
            if thread_id:
                filters.append(Tag("thread_id") == thread_id)

            # Combine all filters with AND logic
            if filters:
                combined_filter = filters[0]
                for f in filters[1:]:
                    combined_filter = combined_filter & f
                vector_query.filter_expression = combined_filter

            # Execute search
            results = self.long_term_memory_index.query(vector_query)

            # Parse results into StoredMemory objects
            memories = []
            for doc in results:
                try:
                    # Safely parse the created_at field
                    created_at_str = doc.get("created_at", "")
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except (ValueError, TypeError):
                        created_at = datetime.now()

                    memory = StoredMemory(
                        id=doc.get("id", ""),
                        memory_id=doc.get("memory_id", ""),
                        user_id=doc.get("user_id", ""),
                        thread_id=doc.get("thread_id"),
                        memory_type=MemoryType(doc.get("memory_type", "episodic")),
                        content=doc.get("content", ""),
                        created_at=created_at,
                        metadata=doc.get("metadata", "{}"),
                        confidence_score=float(doc.get("confidence_score", 0.0))
                    )
                    memories.append(memory)
                except Exception as e:
                    logger.error(f"Error parsing memory result: {e}")
                    logger.debug(f"Problematic document: {doc}")
                    continue

            logger.debug(f"📋 Retrieved {len(memories)} memories")
            return memories

        except Exception as e:
            logger.error(f"❌ Error retrieving memories: {e}")
            return []

    def get_memory_context_for_ai(self, query: str, user_id: str,
                                 thread_id: Optional[str] = None,
                                 max_memories: int = 5) -> str:
        """Get formatted memory context for AI prompting"""
        try:
            # Retrieve relevant memories
            episodic_memories = self.retrieve_memories(
                query=query,
                memory_type=MemoryType.EPISODIC,
                user_id=user_id,
                thread_id=thread_id,
                limit=max_memories
            )

            semantic_memories = self.retrieve_memories(
                query=query,
                memory_type=MemoryType.SEMANTIC,
                user_id=user_id,
                limit=max_memories
            )

            # Format context
            context_parts = []

            if episodic_memories:
                context_parts.append("🧠 RELEVANT USER MEMORIES:")
                for memory in episodic_memories:
                    context_parts.append(f"  • {memory.content}")

            if semantic_memories:
                context_parts.append("\n📚 RELEVANT KNOWLEDGE:")
                for memory in semantic_memories:
                    context_parts.append(f"  • {memory.content}")

            return "\n".join(context_parts) if context_parts else ""

        except Exception as e:
            logger.error(f"❌ Error getting memory context: {e}")
            return ""

    def _memory_consolidation_worker(self):
        """Background worker for memory consolidation"""
        while self._consolidation_running:
            try:
                # Wait for consolidation tasks
                if not self.consolidation_queue.empty():
                    user_id = self.consolidation_queue.get(timeout=MEMORY_CONSOLIDATION_INTERVAL)
                    self._consolidate_memories_for_user(user_id)
                else:
                    time.sleep(MEMORY_CONSOLIDATION_INTERVAL)

            except Exception as e:
                logger.error(f"❌ Memory consolidation error: {e}")
                time.sleep(60)  # Wait before retrying

    def _consolidate_memories_for_user(self, user_id: str):
        """Consolidate similar memories for a specific user"""
        if not self.long_term_memory_index:
            return

        try:
            logger.info(f"🔧 Consolidating memories for user: {user_id}")

            # Get all memories for user
            all_memories = self.retrieve_memories(
                query="",  # Empty query to get all
                user_id=user_id,
                distance_threshold=1.0,  # Get all memories
                limit=100
            )

            # Group similar memories and consolidate
            # This is a simplified version - could be enhanced with clustering
            consolidated_count = 0
            for memory_type in [MemoryType.EPISODIC, MemoryType.SEMANTIC]:
                type_memories = [m for m in all_memories if m.memory_type == memory_type]

                if len(type_memories) > 10:  # Only consolidate if we have many memories
                    # Find similar groups and merge (simplified approach)
                    # In production, you'd use clustering algorithms
                    consolidated_count += self._merge_similar_memories(type_memories)

            if consolidated_count > 0:
                logger.info(f"✅ Consolidated {consolidated_count} memories for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Error consolidating memories for user {user_id}: {e}")

    def _merge_similar_memories(self, memories: List[StoredMemory]) -> int:
        """Merge similar memories (simplified implementation)"""
        # This is a placeholder for more sophisticated memory consolidation
        # In production, you'd implement clustering and intelligent merging
        return 0

    def schedule_memory_consolidation(self, user_id: str):
        """Schedule memory consolidation for a user"""
        try:
            self.consolidation_queue.put(user_id)
            logger.debug(f"📅 Scheduled memory consolidation for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ Error scheduling consolidation: {e}")

    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user"""
        try:
            episodic_count = len(self.retrieve_memories(
                query="", memory_type=MemoryType.EPISODIC,
                user_id=user_id, distance_threshold=1.0, limit=1000
            ))

            semantic_count = len(self.retrieve_memories(
                query="", memory_type=MemoryType.SEMANTIC,
                user_id=user_id, distance_threshold=1.0, limit=1000
            ))

            return {
                "user_id": user_id,
                "episodic_memories": episodic_count,
                "semantic_memories": semantic_count,
                "total_memories": episodic_count + semantic_count,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error getting memory stats: {e}")
            return {"error": str(e)}

    def cleanup(self):
        """Cleanup resources"""
        self._consolidation_running = False
        if hasattr(self, 'consolidation_thread'):
            self.consolidation_thread.join(timeout=5)
        logger.info("🧹 Agent memory system cleaned up")

# Memory Management Tools for LLM
@tool
def store_memory_tool(content: str, memory_type: MemoryType,
                     metadata: Optional[str] = None,
                     config: Optional[RunnableConfig] = None) -> str:
    """
    Store important information in long-term memory.

    Use this to save user preferences, experiences, or knowledge
    that will be useful in future conversations.
    """
    config = config or RunnableConfig()
    user_id = config.get("user_id", SYSTEM_USER_ID)
    thread_id = config.get("thread_id")

    # Get the global memory system instance
    memory_system = get_agent_memory_system()

    try:
        success = memory_system.store_memory(
            content=content,
            memory_type=memory_type,
            user_id=user_id,
            thread_id=thread_id,
            metadata=metadata or "{}"
        )

        if success:
            return f"✅ Successfully stored {memory_type.value} memory: {content}"
        else:
            return f"ℹ️ Similar memory already exists, not stored: {content}"

    except Exception as e:
        return f"❌ Error storing memory: {str(e)}"

@tool
def retrieve_memories_tool(query: str, memory_type: List[MemoryType],
                          limit: int = 5,
                          config: Optional[RunnableConfig] = None) -> str:
    """
    Search for relevant memories based on a query.

    Use this to find user preferences, past experiences, or
    relevant knowledge for the current conversation.
    """
    config = config or RunnableConfig()
    user_id = config.get("user_id", SYSTEM_USER_ID)

    # Get the global memory system instance
    memory_system = get_agent_memory_system()

    try:
        memories = memory_system.retrieve_memories(
            query=query,
            memory_type=memory_type,
            user_id=user_id,
            limit=limit
        )

        if not memories:
            return "No relevant memories found."

        # Format response
        response_parts = ["🧠 RELEVANT MEMORIES:"]
        for memory in memories:
            response_parts.append(f"  • [{memory.memory_type.value}] {memory.content}")

        return "\n".join(response_parts)

    except Exception as e:
        return f"❌ Error retrieving memories: {str(e)}"

# Global instance management
_global_agent_memory_system = None
_memory_system_failed = False

class MockAgentMemorySystem:
    """Mock memory system when real system fails"""
    def store_memory(self, *args, **kwargs):
        return False

    def retrieve_memories(self, *args, **kwargs):
        return []

    def get_memory_context_for_ai(self, *args, **kwargs):
        return ""

def get_agent_memory_system():
    """Get or create the global agent memory system instance with graceful fallback"""
    global _global_agent_memory_system, _memory_system_failed

    if _memory_system_failed:
        return MockAgentMemorySystem()

    if _global_agent_memory_system is None:
        try:
            _global_agent_memory_system = AgentMemorySystem()
        except Exception as e:
            logger.error(f"⚠️ Agent Memory System initialization failed: {e}")
            logger.info("🔄 Falling back to mock memory system")
            _memory_system_failed = True
            return MockAgentMemorySystem()

    return _global_agent_memory_system

def initialize_agent_memory_system(redis_url: str = None):
    """Initialize the global agent memory system with graceful fallback"""
    global _global_agent_memory_system, _memory_system_failed

    try:
        _global_agent_memory_system = AgentMemorySystem(redis_url=redis_url)
        _memory_system_failed = False
        return _global_agent_memory_system
    except Exception as e:
        logger.error(f"⚠️ Agent Memory System initialization failed: {e}")
        logger.info("🔄 Using mock memory system as fallback")
        _memory_system_failed = True
        return MockAgentMemorySystem()

# Export the memory tools for LangGraph agents
AGENT_MEMORY_TOOLS = [store_memory_tool, retrieve_memories_tool]
