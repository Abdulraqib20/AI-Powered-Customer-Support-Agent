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
import logging

# Get logger for session manager
logger = logging.getLogger('customer_support_app')

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
        """Get database connection with error handling"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected connection error: {e}")
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
                            # Only log session creation if debug level is enabled to avoid duplicates
                            logger.debug(f"✅ Session created successfully: {result['session_id']}")
                            return result['session_id']
                        else:
                            raise Exception("Session creation returned no result")

                    except psycopg2.IntegrityError as ie:
                        conn.rollback()
                        logger.warning(f"❌ Session creation integrity error: {ie}")
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
                            logger.debug(f"✅ Session created successfully on retry: {result['session_id']}")
                            return result['session_id']
                        else:
                            raise Exception("Session creation failed on retry")

        except psycopg2.DatabaseError as db_error:
            logger.error(f"❌ Database error creating session: {db_error}")
            fallback_id = str(uuid.uuid4())
            logger.warning(f"⚠️ Using fallback session ID: {fallback_id}")
            return fallback_id
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}")
            fallback_id = str(uuid.uuid4())
            logger.warning(f"⚠️ Using fallback session ID: {fallback_id}")
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
            logger.error(f"❌ Error getting session: {e}")
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
            logger.error(f"❌ Error updating session activity: {e}")

    def create_conversation(self, session_id: str, title: str = "New Chat") -> str:
        """Create a new conversation for a session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # First verify the session exists
                    cur.execute("SELECT session_id FROM user_sessions WHERE session_id = %s", (session_id,))
                    if not cur.fetchone():
                        logger.warning(f"❌ Session {session_id} does not exist, creating it first")
                        # Create the session first
                        cur.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, session_data)
                            VALUES (%s, %s, %s)
                        """, (session_id, None, json.dumps({})))
                        conn.commit()
                        logger.debug(f"✅ Created missing session: {session_id}")

                    conversation_id = str(uuid.uuid4())

                    cur.execute("""
                        INSERT INTO chat_conversations (conversation_id, session_id, conversation_title)
                        VALUES (%s, %s, %s)
                        RETURNING conversation_id
                    """, (conversation_id, session_id, title))

                    result = cur.fetchone()
                    conn.commit()
                    logger.debug(f"✅ Conversation created successfully: {result['conversation_id']}")
                    return result['conversation_id']

        except Exception as e:
            logger.error(f"❌ Error creating conversation: {e}")
            fallback_id = str(uuid.uuid4())
            logger.warning(f"⚠️ Using fallback conversation ID: {fallback_id}")
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
            logger.error(f"❌ Error getting conversations: {e}")
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

                    logger.debug(f"✅ Found {len(conversations)} conversations for user {user_email}")
                    return conversations

        except Exception as e:
            logger.error(f"❌ Error getting conversations by email: {e}")
            return []

    def link_conversations_to_current_session(self, user_email: str, current_session_id: str):
        """Link the most recent conversation of a user to their current session"""
        try:
            # Get all conversations for this user
            user_conversations = self.get_user_conversations_by_email(user_email)

            if not user_conversations:
                logger.debug(f"ℹ️ No existing conversations found for {user_email}")
                return

            logger.debug(f"🔍 Found {len(user_conversations)} existing conversations for {user_email}")

            # Get the most recent conversation
            most_recent_conv = user_conversations[0]

            # Check if it's already linked to the current session
            if most_recent_conv.session_id == current_session_id:
                logger.debug(f"ℹ️ Most recent conversation already linked to current session")
                return

            # Link the most recent conversation to the current session
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chat_conversations
                        SET session_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE conversation_id = %s
                    """, (current_session_id, most_recent_conv.conversation_id))

                    if cur.rowcount > 0:
                        conn.commit()
                        conv_id = most_recent_conv.conversation_id
                        msg_count = most_recent_conv.message_count
                        logger.debug(f"✅ Linked most recent conversation {conv_id[:8]}... ({msg_count} messages) to current session")
                    else:
                        logger.warning(f"⚠️ No conversations were updated for {user_email}")

        except Exception as e:
            logger.error(f"❌ Error linking conversations: {e}")

    def add_message(self, conversation_id: str, sender_type: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a message to a conversation"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Verify conversation exists
                    cur.execute("SELECT conversation_id FROM chat_conversations WHERE conversation_id = %s", (conversation_id,))
                    if not cur.fetchone():
                        logger.warning(f"❌ Conversation {conversation_id} does not exist, cannot add message")
                        # Return a fallback message ID
                        return str(uuid.uuid4())

                    message_id = str(uuid.uuid4())

                    try:
                        cur.execute("""
                            INSERT INTO chat_messages (message_id, conversation_id, sender_type, message_content, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING message_id
                        """, (message_id, conversation_id, sender_type, content, json.dumps(metadata or {})))

                        result = cur.fetchone()
                        if not result:
                            logger.warning(f"❌ Failed to insert message, using fallback ID")
                            fallback_id = str(uuid.uuid4())
                            logger.warning(f"⚠️ Using fallback message ID: {fallback_id}")
                            return fallback_id

                        # Update conversation timestamp
                        cur.execute("""
                            UPDATE chat_conversations
                            SET updated_at = CURRENT_TIMESTAMP
                            WHERE conversation_id = %s
                        """, (conversation_id,))

                        conn.commit()
                        logger.debug(f"✅ Message added successfully: {result['message_id']}")
                        return result['message_id']

                    except Exception as insert_error:
                        logger.error(f"❌ Error adding message: {insert_error}")
                        fallback_id = str(uuid.uuid4())
                        logger.warning(f"⚠️ Using fallback message ID: {fallback_id}")
                        return fallback_id

        except Exception as e:
            logger.error(f"❌ Error adding message: {e}")
            fallback_id = str(uuid.uuid4())
            logger.warning(f"⚠️ Using fallback message ID: {fallback_id}")
            return fallback_id

    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get messages from a conversation"""
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
            logger.error(f"❌ Error getting messages: {e}")
            return []

    def update_conversation_title(self, conversation_id: str, title: str):
        """Update conversation title"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chat_conversations
                        SET conversation_title = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE conversation_id = %s
                    """, (title, conversation_id))
                    conn.commit()
                    logger.debug(f"✅ Conversation title updated: {title[:30]}...")

        except Exception as e:
            logger.error(f"❌ Error updating conversation title: {e}")

    def generate_conversation_title(self, first_user_message: str) -> str:
        """Generate a conversation title based on the first user message"""
        try:
            # Simple title generation - take first 50 characters or first sentence
            if not first_user_message:
                return "New Chat"

            # Clean the message
            cleaned_message = first_user_message.strip()

            # If it's a question, use it as is (up to 50 chars)
            if cleaned_message.endswith('?'):
                return cleaned_message[:50] + ('...' if len(cleaned_message) > 50 else '')

            # If it contains a period, take the first sentence
            if '.' in cleaned_message:
                first_sentence = cleaned_message.split('.')[0]
                return first_sentence[:50] + ('...' if len(first_sentence) > 50 else '')

            # Otherwise, take first 50 characters
            return cleaned_message[:50] + ('...' if len(cleaned_message) > 50 else '')

        except Exception as e:
            logger.error(f"❌ Error generating conversation title: {e}")
            return "New Chat"

    def update_conversation_title_if_new(self, conversation_id: str, user_message: str):
        """Update conversation title if it's still 'New Chat' based on first user message"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if conversation title is still 'New Chat'
                    cur.execute("""
                        SELECT conversation_title
                        FROM chat_conversations
                        WHERE conversation_id = %s AND conversation_title = 'New Chat'
                    """, (conversation_id,))

                    if cur.fetchone():
                        # Generate new title based on user message
                        new_title = self.generate_conversation_title(user_message)

                        # Update the title
                        cur.execute("""
                            UPDATE chat_conversations
                            SET conversation_title = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE conversation_id = %s
                        """, (new_title, conversation_id))

                        conn.commit()
                        logger.debug(f"🏷️ Auto-generated conversation title: '{new_title}' for conversation {conversation_id[:8]}...")

        except Exception as e:
            logger.error(f"❌ Error updating conversation title if new: {e}")

    def get_session_context_for_ai(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session context for AI processing"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get session info
                    cur.execute("""
                        SELECT session_id, user_identifier, created_at, last_active, session_data
                        FROM user_sessions
                        WHERE session_id = %s
                    """, (session_id,))

                    session_row = cur.fetchone()
                    if not session_row:
                        return {}

                    # If user is authenticated, get customer info
                    customer_info = None
                    if session_row['user_identifier']:
                        try:
                            cur.execute("""
                                SELECT customer_id, name, email, phone, address, tier, total_spent, join_date
                                FROM customers
                                WHERE email = %s
                            """, (session_row['user_identifier'],))
                            customer_row = cur.fetchone()
                            if customer_row:
                                customer_info = dict(customer_row)
                        except psycopg2.DatabaseError as db_error:
                            logger.error(f"❌ Error validating customer: {db_error}")

                    return {
                        'session_id': session_row['session_id'],
                        'user_identifier': session_row['user_identifier'],
                        'created_at': session_row['created_at'].isoformat(),
                        'last_active': session_row['last_active'].isoformat(),
                        'session_data': session_row['session_data'],
                        'customer_info': customer_info,
                        'is_authenticated': bool(session_row['user_identifier'])
                    }

        except Exception as e:
            logger.error(f"❌ Error getting session context: {e}")
            return {}

    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old sessions and their associated data"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Delete old sessions and cascade to conversations and messages
                    cur.execute("""
                        DELETE FROM user_sessions
                        WHERE created_at < NOW() - INTERVAL '%s days'
                    """, (days_old,))

                    deleted_count = cur.rowcount
                    conn.commit()

                    logger.info(f"✅ Cleaned up {deleted_count} sessions older than {days_old} days")

        except Exception as e:
            logger.error(f"❌ Error cleaning up sessions: {e}")

# Global session manager instance
session_manager = SessionManager()
