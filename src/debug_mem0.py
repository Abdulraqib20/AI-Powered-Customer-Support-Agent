import os
import sys
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from mem0 import Memory
from config.appconfig import GROQ_API_KEY, GOOGLE_API_KEY
import warnings;warnings.filterwarnings("ignore")

# # Test 1: Check if API keys are loaded correctly
# print("=== API Keys Check ===")
# print(f"GROQ_API_KEY: {GROQ_API_KEY[:10]}...{GROQ_API_KEY[-10:]}")
# print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-10:]}")

# # Test 2: Test Groq directly
# print("\n=== Direct Groq Test ===")
# from groq import Groq
# try:
#     groq_client = Groq(api_key=GROQ_API_KEY)
#     response = groq_client.chat.completions.create(
#         model="llama-3.3-70b-versatile",
#         messages=[{"role": "user", "content": "Hello"}]
#     )
#     print("✅ Direct Groq test: SUCCESS")
# except Exception as e:
#     print(f"❌ Direct Groq test: FAILED - {e}")

# # Test 3: Test Mem0 configuration step by step
# print("\n=== Mem0 Configuration Test ===")

# # Simple config first
# simple_config = {
#     "llm": {
#         "provider": "groq",
#         "config": {
#             "model": "llama-3.3-70b-versatile",
#             "api_key": GROQ_API_KEY,
#             "temperature": 0.2,
#             "max_tokens": 1000,
#         }
#     }
# }

# try:
#     print("Testing simple Mem0 config (LLM only)...")
#     memory_simple = Memory.from_config(simple_config)
#     print("✅ Simple Mem0 config: SUCCESS")
# except Exception as e:
#     print(f"❌ Simple Mem0 config: FAILED - {e}")

# # Full config
# full_config = {
#     "llm": {
#         "provider": "groq",
#         "config": {
#             "model": "llama-3.3-70b-versatile",
#             "api_key": GROQ_API_KEY,
#             "temperature": 0.2,
#             "max_tokens": 1000,
#         }
#     },
#     "embeddings": {
#         "provider": "google",
#         "model": "models/text-embedding-004",
#         "params": {
#             "api_key": GOOGLE_API_KEY,
#             "task_type": "RETRIEVAL_DOCUMENT"
#         }
#     },
#     "vector_store": {
#         "provider": "qdrant",
#         "config": {
#             "host": "localhost",
#             "port": 6333,
#         }
#     }
# }

# try:
#     print("Testing full Mem0 config...")
#     memory_full = Memory.from_config(full_config)
#     print("✅ Full Mem0 config: SUCCESS")

#     # Test memory operations
#     print("Testing memory add...")
#     memory_full.add("Test message", user_id="test_user")
#     print("✅ Memory add: SUCCESS")

#     print("Testing memory search...")
#     results = memory_full.search("Test", user_id="test_user")
#     print("✅ Memory search: SUCCESS")

# except Exception as e:
#     print(f"❌ Full Mem0 config: FAILED - {e}")
#     import traceback
#     traceback.print_exc()

config = {
    "llm": {
        "provider": "groq",
        "config": {
            "model": "llama-3.1-8b-instant",
            "api_key": GROQ_API_KEY,
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    },
    "embeddings": {
        "provider": "google",
        "model": "models/text-embedding-004",
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
}

m = Memory.from_config(config)
messages = [
    {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
    {"role": "assistant", "content": "How about a thriller movies? They can be quite engaging."},
    {"role": "user", "content": "I’m not a big fan of thriller movies but I love sci-fi movies."},
    {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
]
m.add(messages, user_id="alice", metadata={"category": "movies"})
