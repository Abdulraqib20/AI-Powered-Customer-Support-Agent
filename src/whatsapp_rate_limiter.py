"""
WhatsApp Rate Limiting Manager
Prevents abuse and manages backend resource usage for WhatsApp conversations
"""

import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    CONVERSATION = "conversation"
    MESSAGE = "message"
    BURST = "burst"

class RateLimitResult(Enum):
    ALLOWED = "allowed"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    HOURLY_LIMIT_EXCEEDED = "hourly_limit_exceeded"
    BURST_LIMIT_EXCEEDED = "burst_limit_exceeded"
    TEMPORARILY_BLOCKED = "temporarily_blocked"

@dataclass
class RateLimitResponse:
    allowed: bool
    result: RateLimitResult
    message: str
    current_count: Optional[int] = None
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_time: Optional[datetime] = None
    user_tier: Optional[str] = None
    block_expires_at: Optional[datetime] = None

class WhatsAppRateLimiter:
    """
    Manages rate limiting for WhatsApp conversations and messages
    """

    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle')
        }

    def get_database_connection(self):
        """Get database connection with error handling"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def check_conversation_limit(self, phone_number: str, customer_id: Optional[int] = None) -> RateLimitResponse:
        """
        Check if user can start a new conversation

        Args:
            phone_number: WhatsApp phone number
            customer_id: Customer ID if user is authenticated

        Returns:
            RateLimitResponse with allow/deny decision and details
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Call the database function to check conversation limits
                    cursor.execute("""
                        SELECT can_start_conversation(%s, %s) as result
                    """, (phone_number, customer_id))

                    result = cursor.fetchone()
                    if not result:
                        return self._create_error_response("Database error checking conversation limit")

                    response_data = result['result']

                    if response_data['allowed']:
                        return RateLimitResponse(
                            allowed=True,
                            result=RateLimitResult.ALLOWED,
                            message="Conversation allowed",
                            remaining=response_data.get('remaining_conversations'),
                            user_tier=response_data.get('user_tier'),
                            limit=response_data.get('limit')
                        )
                    else:
                        return self._parse_limit_response(response_data, RateLimitType.CONVERSATION)

        except Exception as e:
            logger.error(f"❌ Error checking conversation limit for {phone_number}: {e}")
            return self._create_error_response("System error checking rate limit")

    def check_message_limit(self, phone_number: str, customer_id: Optional[int] = None) -> RateLimitResponse:
        """
        Check if user can send a message within an existing conversation

        Args:
            phone_number: WhatsApp phone number
            customer_id: Customer ID if user is authenticated

        Returns:
            RateLimitResponse with allow/deny decision and details
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Call the database function to check message limits
                    cursor.execute("""
                        SELECT can_send_message(%s, %s) as result
                    """, (phone_number, customer_id))

                    result = cursor.fetchone()
                    if not result:
                        return self._create_error_response("Database error checking message limit")

                    response_data = result['result']

                    if response_data['allowed']:
                        return RateLimitResponse(
                            allowed=True,
                            result=RateLimitResult.ALLOWED,
                            message="Message allowed",
                            remaining=response_data.get('remaining_messages_hour'),
                            user_tier=response_data.get('user_tier')
                        )
                    else:
                        return self._parse_limit_response(response_data, RateLimitType.MESSAGE)

        except Exception as e:
            logger.error(f"❌ Error checking message limit for {phone_number}: {e}")
            return self._create_error_response("System error checking rate limit")

    def _parse_limit_response(self, response_data: Dict, limit_type: RateLimitType) -> RateLimitResponse:
        """Parse database response into RateLimitResponse object"""
        reason = response_data.get('reason', 'unknown')
        message = response_data.get('message', 'Rate limit exceeded')

        # Map database reasons to enum values
        result_map = {
            'daily_limit_exceeded': RateLimitResult.DAILY_LIMIT_EXCEEDED,
            'hourly_limit_exceeded': RateLimitResult.HOURLY_LIMIT_EXCEEDED,
            'burst_limit_exceeded': RateLimitResult.BURST_LIMIT_EXCEEDED,
            'temporarily_blocked': RateLimitResult.TEMPORARILY_BLOCKED
        }

        result = result_map.get(reason, RateLimitResult.DAILY_LIMIT_EXCEEDED)

        # Parse reset time if available
        reset_time = None
        if 'reset_time' in response_data:
            try:
                reset_time = datetime.fromisoformat(str(response_data['reset_time']).replace('Z', '+00:00'))
            except:
                pass

        # Parse block expiry if available
        block_expires_at = None
        if 'block_expires_at' in response_data:
            try:
                block_expires_at = datetime.fromisoformat(str(response_data['block_expires_at']).replace('Z', '+00:00'))
            except:
                pass

        return RateLimitResponse(
            allowed=False,
            result=result,
            message=message,
            current_count=response_data.get('current_count'),
            limit=response_data.get('limit'),
            reset_time=reset_time,
            user_tier=response_data.get('user_tier'),
            block_expires_at=block_expires_at
        )

    def _create_error_response(self, error_message: str) -> RateLimitResponse:
        """Create error response for system failures"""
        return RateLimitResponse(
            allowed=False,
            result=RateLimitResult.TEMPORARILY_BLOCKED,
            message=f"System temporarily unavailable: {error_message}"
        )

    def get_user_rate_status(self, phone_number: str) -> Dict:
        """
        Get current rate limiting status for a user

        Args:
            phone_number: WhatsApp phone number

        Returns:
            Dictionary with current usage and limits
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT
                            t.phone_number,
                            t.user_tier,
                            t.conversations_today,
                            l.conversations_per_day,
                            t.messages_this_hour,
                            l.messages_per_hour,
                            t.burst_count,
                            l.burst_allowance,
                            t.total_violations,
                            t.is_temporarily_blocked,
                            t.block_expires_at,
                            t.last_activity
                        FROM whatsapp_user_rate_tracking t
                        JOIN whatsapp_rate_limits l ON t.user_tier = l.user_tier
                        WHERE t.phone_number = %s
                    """, (phone_number,))

                    result = cursor.fetchone()
                    if not result:
                        return {
                            'phone_number': phone_number,
                            'user_tier': 'anonymous',
                            'conversations_today': 0,
                            'conversations_limit': 5,
                            'messages_this_hour': 0,
                            'messages_limit': 20,
                            'violations': 0,
                            'is_blocked': False
                        }

                    return {
                        'phone_number': result['phone_number'],
                        'user_tier': result['user_tier'],
                        'conversations_today': result['conversations_today'],
                        'conversations_limit': result['conversations_per_day'],
                        'conversations_remaining': max(0, result['conversations_per_day'] - result['conversations_today']),
                        'messages_this_hour': result['messages_this_hour'],
                        'messages_limit': result['messages_per_hour'],
                        'messages_remaining': max(0, result['messages_per_hour'] - result['messages_this_hour']),
                        'burst_count': result['burst_count'],
                        'burst_limit': result['burst_allowance'],
                        'violations': result['total_violations'],
                        'is_blocked': result['is_temporarily_blocked'],
                        'block_expires_at': result['block_expires_at'].isoformat() if result['block_expires_at'] else None,
                        'last_activity': result['last_activity'].isoformat() if result['last_activity'] else None
                    }

        except Exception as e:
            logger.error(f"❌ Error getting rate status for {phone_number}: {e}")
            return {'error': str(e)}

    def apply_temporary_block(self, phone_number: str, duration_hours: int = 24) -> bool:
        """
        Apply temporary block to a user for violations

        Args:
            phone_number: WhatsApp phone number
            duration_hours: Block duration in hours

        Returns:
            True if block was applied successfully
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT apply_temporary_block(%s, %s) as success
                    """, (phone_number, duration_hours))

                    result = cursor.fetchone()
                    conn.commit()

                    success = result['success'] if result else False
                    if success:
                        logger.warning(f"🚫 Applied {duration_hours}h block to {phone_number}")

                    return success

        except Exception as e:
            logger.error(f"❌ Error applying block to {phone_number}: {e}")
            return False

    def update_rate_limits(self, user_tier: str, conversations_per_day: int = None,
                          messages_per_hour: int = None, burst_allowance: int = None) -> bool:
        """
        Update rate limits for a user tier

        Args:
            user_tier: User tier to update
            conversations_per_day: New daily conversation limit
            messages_per_hour: New hourly message limit
            burst_allowance: New burst allowance

        Returns:
            True if update was successful
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    # Build update query dynamically
                    updates = []
                    params = []

                    if conversations_per_day is not None:
                        updates.append("conversations_per_day = %s")
                        params.append(conversations_per_day)

                    if messages_per_hour is not None:
                        updates.append("messages_per_hour = %s")
                        params.append(messages_per_hour)

                    if burst_allowance is not None:
                        updates.append("burst_allowance = %s")
                        params.append(burst_allowance)

                    if not updates:
                        return False

                    params.append(user_tier)

                    cursor.execute(f"""
                        UPDATE whatsapp_rate_limits
                        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                        WHERE user_tier = %s
                    """, params)

                    conn.commit()

                    if cursor.rowcount > 0:
                        logger.info(f"✅ Updated rate limits for tier '{user_tier}'")
                        return True
                    else:
                        logger.warning(f"⚠️ No rate limit tier found for '{user_tier}'")
                        return False

        except Exception as e:
            logger.error(f"❌ Error updating rate limits for {user_tier}: {e}")
            return False

    def get_rate_limit_stats(self, days: int = 7) -> Dict:
        """
        Get rate limiting statistics for monitoring

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get violation statistics
                    cursor.execute("""
                        SELECT
                            event_type,
                            limit_type,
                            user_tier,
                            COUNT(*) as count,
                            COUNT(DISTINCT phone_number) as unique_users
                        FROM whatsapp_rate_limit_events
                        WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                        GROUP BY event_type, limit_type, user_tier
                        ORDER BY count DESC
                    """, (days,))

                    events = cursor.fetchall()

                    # Get current blocked users
                    cursor.execute("""
                        SELECT COUNT(*) as blocked_count
                        FROM whatsapp_user_rate_tracking
                        WHERE is_temporarily_blocked = TRUE
                        AND block_expires_at > CURRENT_TIMESTAMP
                    """)

                    blocked_result = cursor.fetchone()
                    blocked_count = blocked_result['blocked_count'] if blocked_result else 0

                    # Get tier distribution
                    cursor.execute("""
                        SELECT
                            user_tier,
                            COUNT(*) as user_count,
                            AVG(conversations_today) as avg_conversations,
                            AVG(messages_this_hour) as avg_messages
                        FROM whatsapp_user_rate_tracking
                        WHERE last_activity >= CURRENT_DATE - INTERVAL '%s days'
                        GROUP BY user_tier
                    """, (days,))

                    tier_stats = cursor.fetchall()

                    return {
                        'period_days': days,
                        'events': [dict(event) for event in events],
                        'currently_blocked': blocked_count,
                        'tier_statistics': [dict(stat) for stat in tier_stats],
                        'generated_at': datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"❌ Error getting rate limit stats: {e}")
            return {'error': str(e)}

    def format_rate_limit_message(self, response: RateLimitResponse) -> str:
        """
        Format user-friendly rate limit message for WhatsApp

        Args:
            response: RateLimitResponse object

        Returns:
            Formatted message string
        """
        if response.allowed:
            if response.remaining is not None and response.remaining <= 3:
                return f"⚠️ Limit warning: {response.remaining} {response.result.value}s remaining today."
            return ""

        # Create user-friendly messages based on limit type
        messages = {
            RateLimitResult.DAILY_LIMIT_EXCEEDED: (
                f"🚫 Daily conversation limit reached ({response.limit} conversations).\n"
                f"Resets tomorrow at midnight. Try again then! 🌙"
            ),
            RateLimitResult.HOURLY_LIMIT_EXCEEDED: (
                f"⏰ Hourly message limit reached ({response.limit} messages/hour).\n"
                f"Please wait {self._format_reset_time(response.reset_time)} to continue."
            ),
            RateLimitResult.BURST_LIMIT_EXCEEDED: (
                f"🚀 Slow down! Too many messages too quickly.\n"
                f"Please wait a few minutes before sending more messages."
            ),
            RateLimitResult.TEMPORARILY_BLOCKED: (
                f"🚫 Account temporarily blocked due to repeated violations.\n"
                f"Block expires: {self._format_reset_time(response.block_expires_at)}"
            )
        }

        base_message = messages.get(response.result, response.message)

        # Add tier upgrade suggestion for anonymous users
        if response.user_tier == 'anonymous':
            base_message += "\n\n💡 Tip: Create an account to get higher limits!"

        return base_message

    def _format_reset_time(self, reset_time: Optional[datetime]) -> str:
        """Format reset time for user display"""
        if not reset_time:
            return "soon"

        now = datetime.now(reset_time.tzinfo) if reset_time.tzinfo else datetime.now()
        diff = reset_time - now

        if diff.total_seconds() < 0:
            return "now"
        elif diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"in {minutes} minute{'s' if minutes != 1 else ''}"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(diff.total_seconds() / 3600)
            return f"in {hours} hour{'s' if hours != 1 else ''}"
        else:
            return reset_time.strftime("%I:%M %p on %B %d")


# Global instance for easy importing
rate_limiter = WhatsAppRateLimiter()
