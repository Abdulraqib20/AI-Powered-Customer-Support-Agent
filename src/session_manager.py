"""
Session Manager for Customer Support Chat System
Handles user sessions, chat conversations, and message history
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from pathlib import Path
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import safe_int_env, safe_str_env

@dataclass
class ChatMessage:
    message_id: str
    sender_type: str  # 'user' or 'ai'
    message_content: str
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class ChatConversation:
    conversation_id: str
    session_id: str
    conversation_title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int = 0

@dataclass
class UserSession:
    session_id: str
    user_identifier: Optional[str]
    created_at: datetime
    last_active: datetime
    session_data: Dict[str, Any]

class SessionManager:
    def __init__(self):
        self.db_config = {
            'host': safe_str_env('DB_HOST', 'localhost'),
            'port': safe_int_env('DB_PORT', 5432),
            'database': safe_str_env('DB_NAME', 'nigerian_ecommerce'),
            'user': safe_str_env('DB_USER', 'postgres'),
            'password': safe_str_env('DB_PASSWORD', 'oracle')
        }

    def get_connection(self):
        """Get database connection with error handling"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.OperationalError as e:
            print(f"❌ Database connection failed: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected connection error: {e}")
            raise

    def create_session(self, user_identifier: Optional[str] = None) -> str:
        """Create a new user session with comprehensive error handling"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    session_id = str(uuid.uuid4())

                    # Check if session already exists (unlikely but possible)
                    cur.execute("SELECT session_id FROM user_sessions WHERE session_id = %s", (session_id,))
                    if cur.fetchone():
                        # Very unlikely, but generate a new one
                        session_id = str(uuid.uuid4())

                    try:
                        cur.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, session_data)
                            VALUES (%s, %s, %s)
                            RETURNING session_id
                        """, (session_id, user_identifier, json.dumps({})))

                        result = cur.fetchone()
                        if result:
                            conn.commit()
                            print(f"✅ Session created successfully: {result['session_id']}")
                            return result['session_id']
                        else:
                            raise Exception("Session creation returned no result")

                    except psycopg2.IntegrityError as ie:
                        conn.rollback()
                        print(f"❌ Session creation integrity error: {ie}")
                        # Generate new session_id and retry once
                        session_id = str(uuid.uuid4())
                        cur.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, session_data)
                            VALUES (%s, %s, %s)
                            RETURNING session_id
                        """, (session_id, user_identifier, json.dumps({})))
                        result = cur.fetchone()
                        if result:
                            conn.commit()
                            print(f"✅ Session created successfully on retry: {result['session_id']}")
                            return result['session_id']
                        else:
                            raise Exception("Session creation failed on retry")

        except psycopg2.DatabaseError as db_error:
            print(f"❌ Database error creating session: {db_error}")
            fallback_id = str(uuid.uuid4())
            print(f"⚠️ Using fallback session ID: {fallback_id}")
            return fallback_id
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            fallback_id = str(uuid.uuid4())
            print(f"⚠️ Using fallback session ID: {fallback_id}")
            return fallback_id

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT session_id, user_identifier, created_at, last_active, session_data
                        FROM user_sessions
                        WHERE session_id = %s
                    """, (session_id,))

                    row = cur.fetchone()
                    if row:
                        return UserSession(
                            session_id=row['session_id'],
                            user_identifier=row['user_identifier'],
                            created_at=row['created_at'],
                            last_active=row['last_active'],
                            session_data=row['session_data'] or {}
                        )
                    return None

        except Exception as e:
            print(f"❌ Error getting session: {e}")
            return None

    def update_session_activity(self, session_id: str):
        """Update last active timestamp for session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_sessions
                        SET last_active = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                    """, (session_id,))
                    conn.commit()

        except Exception as e:
            print(f"❌ Error updating session activity: {e}")

    def create_conversation(self, session_id: str, title: str = "New Chat") -> str:
        """Create a new conversation for a session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # First verify the session exists
                    cur.execute("SELECT session_id FROM user_sessions WHERE session_id = %s", (session_id,))
                    if not cur.fetchone():
                        print(f"❌ Session {session_id} does not exist, creating it first")
                        # Create the session first
                        cur.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, session_data)
                            VALUES (%s, %s, %s)
                        """, (session_id, None, json.dumps({})))
                        conn.commit()
                        print(f"✅ Created missing session: {session_id}")

                    conversation_id = str(uuid.uuid4())

                    cur.execute("""
                        INSERT INTO chat_conversations (conversation_id, session_id, conversation_title)
                        VALUES (%s, %s, %s)
                        RETURNING conversation_id
                    """, (conversation_id, session_id, title))

                    result = cur.fetchone()
                    conn.commit()
                    print(f"✅ Conversation created successfully: {result['conversation_id']}")
                    return result['conversation_id']

        except Exception as e:
            print(f"❌ Error creating conversation: {e}")
            fallback_id = str(uuid.uuid4())
            print(f"⚠️ Using fallback conversation ID: {fallback_id}")
            return fallback_id

    def get_user_conversations(self, session_id: str) -> List[ChatConversation]:
        """Get all conversations for a user session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT
                            c.conversation_id,
                            c.session_id,
                            c.conversation_title,
                            c.created_at,
                            c.updated_at,
                            c.is_active,
                            COUNT(m.message_id) as message_count
                        FROM chat_conversations c
                        LEFT JOIN chat_messages m ON c.conversation_id = m.conversation_id
                        WHERE c.session_id = %s
                        GROUP BY c.conversation_id, c.session_id, c.conversation_title,
                                c.created_at, c.updated_at, c.is_active
                        ORDER BY c.updated_at DESC
                    """, (session_id,))

                    conversations = []
                    for row in cur.fetchall():
                        conversations.append(ChatConversation(
                            conversation_id=row['conversation_id'],
                            session_id=row['session_id'],
                            conversation_title=row['conversation_title'],
                            created_at=row['created_at'],
                            updated_at=row['updated_at'],
                            is_active=row['is_active'],
                            message_count=row['message_count'] or 0
                        ))

                    return conversations

        except Exception as e:
            print(f"❌ Error getting conversations: {e}")
            return []

    def get_user_conversations_by_email(self, user_email: str) -> List[ChatConversation]:
        """Get all conversations for an authenticated user by their email across all sessions"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get conversations from all sessions that belong to this user
                    cur.execute("""
                        SELECT
                            c.conversation_id,
                            c.session_id,
                            c.conversation_title,
                            c.created_at,
                            c.updated_at,
                            c.is_active,
                            COUNT(m.message_id) as message_count
                        FROM chat_conversations c
                        LEFT JOIN chat_messages m ON c.conversation_id = m.conversation_id
                        INNER JOIN user_sessions us ON c.session_id = us.session_id
                        WHERE us.user_identifier = %s
                        GROUP BY c.conversation_id, c.session_id, c.conversation_title,
                                c.created_at, c.updated_at, c.is_active
                        ORDER BY c.updated_at DESC
                    """, (user_email,))

                    conversations = []
                    for row in cur.fetchall():
                        conversations.append(ChatConversation(
                            conversation_id=row['conversation_id'],
                            session_id=row['session_id'],
                            conversation_title=row['conversation_title'],
                            created_at=row['created_at'],
                            updated_at=row['updated_at'],
                            is_active=row['is_active'],
                            message_count=row['message_count'] or 0
                        ))

                    print(f"✅ Found {len(conversations)} conversations for user {user_email}")
                    return conversations

        except Exception as e:
            print(f"❌ Error getting conversations by email: {e}")
            return []

    def link_conversations_to_current_session(self, user_email: str, current_session_id: str):
        """Link existing conversations to the current session for authenticated users"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 🔧 FIX: Get all conversations for this user across all their sessions
                    cur.execute("""
                        SELECT c.conversation_id, c.session_id, c.updated_at,
                               COUNT(m.message_id) as message_count
                        FROM chat_conversations c
                        INNER JOIN user_sessions us ON c.session_id = us.session_id
                        LEFT JOIN chat_messages m ON c.conversation_id = m.conversation_id
                        WHERE us.user_identifier = %s
                        GROUP BY c.conversation_id, c.session_id, c.updated_at
                        ORDER BY c.updated_at DESC
                    """, (user_email,))

                    user_conversations = cur.fetchall()
                    print(f"🔍 Found {len(user_conversations)} existing conversations for {user_email}")

                    if user_conversations:
                        # Update only the most recent conversation to current session
                        # This ensures the user can continue their latest conversation seamlessly
                        most_recent_conv = user_conversations[0]
                        conv_id, old_session_id, updated_at, msg_count = most_recent_conv

                        if old_session_id != current_session_id:
                            cur.execute("""
                                UPDATE chat_conversations
                                SET session_id = %s
                                WHERE conversation_id = %s
                            """, (current_session_id, conv_id))

                            updated_count = cur.rowcount
                            conn.commit()

                            if updated_count > 0:
                                print(f"✅ Linked most recent conversation {conv_id[:8]}... ({msg_count} messages) to current session")
                            else:
                                print(f"⚠️ No conversations were updated for {user_email}")
                        else:
                            print(f"ℹ️ Most recent conversation already linked to current session")
                    else:
                        print(f"ℹ️ No existing conversations found for {user_email}")

        except Exception as e:
            print(f"❌ Error linking conversations: {e}")

    def add_message(self, conversation_id: str, sender_type: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a message to a conversation"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # First verify the conversation exists
                    cur.execute("SELECT conversation_id FROM chat_conversations WHERE conversation_id = %s", (conversation_id,))
                    if not cur.fetchone():
                        print(f"❌ Conversation {conversation_id} does not exist, cannot add message")
                        return str(uuid.uuid4())  # Return fallback ID

                    message_id = str(uuid.uuid4())

                    cur.execute("""
                        INSERT INTO chat_messages (message_id, conversation_id, sender_type, message_content, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING message_id
                    """, (message_id, conversation_id, sender_type, content, json.dumps(metadata or {})))

                    result = cur.fetchone()
                    if not result:
                        print(f"❌ Failed to insert message, using fallback ID")
                        fallback_id = str(uuid.uuid4())
                        print(f"⚠️ Using fallback message ID: {fallback_id}")
                        return fallback_id

                    # Update conversation timestamp
                    cur.execute("""
                        UPDATE chat_conversations
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE conversation_id = %s
                    """, (conversation_id,))

                    conn.commit()
                    print(f"✅ Message added successfully: {result['message_id']}")
                    return result['message_id']

        except Exception as e:
            print(f"❌ Error adding message: {e}")
            fallback_id = str(uuid.uuid4())
            print(f"⚠️ Using fallback message ID: {fallback_id}")
            return fallback_id

    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get messages for a conversation"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT message_id, sender_type, message_content, metadata, created_at
                        FROM chat_messages
                        WHERE conversation_id = %s
                        ORDER BY created_at ASC
                        LIMIT %s
                    """, (conversation_id, limit))

                    messages = []
                    for row in cur.fetchall():
                        messages.append(ChatMessage(
                            message_id=row['message_id'],
                            sender_type=row['sender_type'],
                            message_content=row['message_content'],
                            metadata=row['metadata'] or {},
                            created_at=row['created_at']
                        ))

                    return messages

        except Exception as e:
            print(f"❌ Error getting messages: {e}")
            return []

    def update_conversation_title(self, conversation_id: str, title: str):
        """Update conversation title"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chat_conversations
                        SET conversation_title = %s
                        WHERE conversation_id = %s
                    """, (title, conversation_id))
                    conn.commit()
                    print(f"✅ Conversation title updated: {title[:30]}...")

        except Exception as e:
            print(f"❌ Error updating conversation title: {e}")

    def generate_conversation_title(self, first_user_message: str) -> str:
        """Generate an intelligent conversation title from the first user message, similar to ChatGPT"""
        if not first_user_message:
            return "New Chat"

        # Clean and prepare the message
        message = first_user_message.strip()

        # If message is too short, use it as-is
        if len(message) <= 30:
            return message.capitalize()

        # For longer messages, try to extract the key intent
        lower_message = message.lower()

        # Common patterns for Nigerian e-commerce
        if any(word in lower_message for word in ['order', 'track', 'delivery', 'shipping']):
            if 'track' in lower_message or 'where' in lower_message:
                return "Track Order"
            elif 'history' in lower_message:
                return "Order History"
            else:
                return "Order Inquiry"

        elif any(word in lower_message for word in ['account', 'profile', 'update', 'change']):
            return "Account Settings"

        elif any(word in lower_message for word in ['payment', 'pay', 'card', 'bank']):
            return "Payment Inquiry"

        elif any(word in lower_message for word in ['product', 'search', 'find', 'show me']):
            return "Product Search"

        elif any(word in lower_message for word in ['help', 'support', 'problem', 'issue']):
            return "Customer Support"

        elif any(word in lower_message for word in ['price', 'cost', 'how much']):
            return "Pricing Inquiry"

        elif any(word in lower_message for word in ['cancel', 'refund', 'return']):
            return "Cancel/Return"

        # If no pattern matches, take first meaningful words (up to 4 words or 35 chars)
        words = message.split()
        if len(words) <= 4:
            return message.capitalize()

        # Take first 4 words or until we hit 35 characters
        title_words = []
        char_count = 0

        for word in words[:4]:
            if char_count + len(word) + 1 > 35:  # +1 for space
                break
            title_words.append(word)
            char_count += len(word) + 1

        title = " ".join(title_words)

        # Add ellipsis if we truncated
        if len(title_words) < len(words) and len(words) > 4:
            title += "..."

        return title.capitalize()

    def update_conversation_title_if_new(self, conversation_id: str, user_message: str):
        """Update conversation title only if it's still 'New Chat' (i.e., this is the first real message)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check current title
                    cur.execute("""
                        SELECT conversation_title,
                               (SELECT COUNT(*) FROM chat_messages WHERE conversation_id = %s AND sender_type = 'user') as user_message_count
                        FROM chat_conversations
                        WHERE conversation_id = %s
                    """, (conversation_id, conversation_id))

                    result = cur.fetchone()
                    if result and (result['conversation_title'] == 'New Chat' or result['user_message_count'] == 1):
                        # This is the first user message, generate a title
                        new_title = self.generate_conversation_title(user_message)
                        self.update_conversation_title(conversation_id, new_title)
                        print(f"🏷️ Auto-generated conversation title: '{new_title}' for conversation {conversation_id[:8]}...")

        except Exception as e:
            print(f"❌ Error updating conversation title if new: {e}")

    def get_session_context_for_ai(self, session_id: str) -> Dict[str, Any]:
        """Get session context for AI queries with customer validation"""
        try:
            session = self.get_session(session_id)
            if session and session.user_identifier:
                # Validate that the user_identifier (email) exists in customers table
                try:
                    from config.database_config import CustomerRepository, DatabaseManager
                    db_manager = DatabaseManager()
                    customer_repo = CustomerRepository(db_manager)
                    customer = customer_repo.get_customer_by_email(session.user_identifier)

                    if customer:
                        return {
                            'session_id': session_id,
                            'user_email': session.user_identifier,
                            'customer_id': customer['customer_id'],
                            'customer_name': customer['name'],
                            'user_authenticated': True,
                            'customer_verified': True
                        }
                    else:
                        # User email not found in customers table
                        return {
                            'session_id': session_id,
                            'user_email': session.user_identifier,
                            'user_authenticated': False,
                            'customer_verified': False,
                            'error': 'Customer not found in database'
                        }

                except Exception as db_error:
                    print(f"❌ Error validating customer: {db_error}")
                    return {
                        'session_id': session_id,
                        'user_email': session.user_identifier,
                        'user_authenticated': False,
                        'customer_verified': False,
                        'error': 'Database error during customer validation'
                    }

            return {
                'session_id': session_id,
                'user_email': None,
                'customer_id': None,
                'user_authenticated': False,
                'customer_verified': False
            }

        except Exception as e:
            print(f"❌ Error getting session context: {e}")
            return {
                'session_id': session_id,
                'user_email': None,
                'customer_id': None,
                'user_authenticated': False,
                'customer_verified': False,
                'error': str(e)
            }

    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old sessions and conversations"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cutoff_date = datetime.now() - timedelta(days=days_old)

                    cur.execute("""
                        DELETE FROM user_sessions
                        WHERE last_active < %s
                    """, (cutoff_date,))

                    conn.commit()
                    print(f"✅ Cleaned up sessions older than {days_old} days")

        except Exception as e:
            print(f"❌ Error cleaning up sessions: {e}")

# Global session manager instance
session_manager = SessionManager()
