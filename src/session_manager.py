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
from dataclasses import dataclass

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
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)

    def create_session(self, user_identifier: Optional[str] = None) -> str:
        """Create a new user session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    session_id = str(uuid.uuid4())

                    # First check if session already exists (unlikely but possible)
                    cur.execute("SELECT session_id FROM user_sessions WHERE session_id = %s", (session_id,))
                    if cur.fetchone():
                        # Very unlikely, but generate a new one
                        session_id = str(uuid.uuid4())

                    cur.execute("""
                        INSERT INTO user_sessions (session_id, user_identifier, session_data)
                        VALUES (%s, %s, %s)
                        RETURNING session_id
                    """, (session_id, user_identifier, json.dumps({})))

                    result = cur.fetchone()
                    conn.commit()
                    print(f"✅ Session created successfully: {result['session_id']}")
                    return result['session_id']

        except Exception as e:
            print(f"❌ Error creating session: {e}")
            # Return a fallback UUID but note it won't have database backing
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

        except Exception as e:
            print(f"❌ Error updating conversation title: {e}")

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
