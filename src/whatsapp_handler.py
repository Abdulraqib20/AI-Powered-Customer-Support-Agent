"""
WhatsApp Business API Handler for RaqibTech Customer Support Agent
Integrates WhatsApp conversations with existing AI system, session management, and order processing
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import hashlib
import hmac

# Import existing system components
from .order_ai_assistant import OrderAIAssistant
from .session_manager import SessionManager
from .conversation_memory_system import WorldClassMemorySystem

logger = logging.getLogger(__name__)

class WhatsAppConfig:
    """WhatsApp Business API configuration"""

    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        self.api_base_url = os.getenv('WHATSAPP_API_BASE_URL', 'https://graph.facebook.com/v23.0')
        self.developer_number = os.getenv('DEVELOPER_WHATSAPP_NUMBER', '+2347025965922')

        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

    def is_configured(self) -> bool:
        """Check if WhatsApp is properly configured"""
        required_vars = [
            self.access_token,
            self.phone_number_id,
            self.webhook_verify_token
        ]
        return all(var is not None for var in required_vars)

class WhatsAppMessage:
    """WhatsApp message data structure"""

    def __init__(self, message_data: Dict):
        self.message_id = message_data.get('id')
        self.from_number = message_data.get('from')
        self.timestamp = message_data.get('timestamp')
        self.message_type = message_data.get('type', 'text')

        # Extract content based on message type
        if self.message_type == 'text':
            self.content = message_data.get('text', {}).get('body', '')
        elif self.message_type == 'image':
            self.content = message_data.get('image', {}).get('caption', '')
            self.media_url = message_data.get('image', {}).get('id')
        elif self.message_type == 'button':
            self.content = message_data.get('button', {}).get('text', '')
            self.button_reply = message_data.get('button', {}).get('payload', '')
        elif self.message_type == 'interactive':
            interactive = message_data.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                self.content = interactive.get('button_reply', {}).get('title', '')
                self.button_reply = interactive.get('button_reply', {}).get('id', '')
            elif interactive.get('type') == 'list_reply':
                self.content = interactive.get('list_reply', {}).get('title', '')
                self.button_reply = interactive.get('list_reply', {}).get('id', '')
        else:
            self.content = str(message_data)

        self.raw_data = message_data

class WhatsAppBusinessHandler:
    """Main WhatsApp Business API handler"""

    def __init__(self):
        self.config = WhatsAppConfig()
        if not self.config.is_configured():
            logger.warning("⚠️ WhatsApp Business API not fully configured. Some features may be limited.")

        # Initialize existing system components
        try:
            self.memory_system = WorldClassMemorySystem()
            self.ai_assistant = OrderAIAssistant(self.memory_system)
            self.session_manager = SessionManager()
            logger.info("✅ WhatsApp handler initialized with existing AI system")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI components: {e}")
            raise

    def get_database_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.config.db_config)
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook"""
        # Use configured token (already has fallback in __init__)
        expected_token = self.config.webhook_verify_token

        if mode == "subscribe" and token == expected_token:
            logger.info("✅ WhatsApp webhook verified successfully")
            return challenge
        else:
            logger.warning(f"❌ WhatsApp webhook verification failed - expected: {expected_token}, got: {token}")
            return None

    def process_webhook_data(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process incoming WhatsApp webhook data"""
        try:
            # Log webhook event
            self._log_webhook_event(webhook_data)

            # Extract messages from webhook data
            entries = webhook_data.get('entry', [])
            responses = []

            for entry in entries:
                changes = entry.get('changes', [])
                for change in changes:
                    if change.get('field') == 'messages':
                        value = change.get('value', {})

                        # Process incoming messages
                        messages = value.get('messages', [])
                        for message_data in messages:
                            response = self._process_incoming_message(message_data)
                            if response:
                                responses.append(response)

                        # Process message status updates
                        statuses = value.get('statuses', [])
                        for status in statuses:
                            self._process_message_status(status)

            return {
                'success': True,
                'processed_messages': len(responses),
                'responses': responses
            }

        except Exception as e:
            logger.error(f"❌ Error processing webhook data: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _process_incoming_message(self, message_data: Dict) -> Optional[Dict]:
        """Process a single incoming WhatsApp message"""
        try:
            message = WhatsAppMessage(message_data)
            logger.info(f"📱 Processing WhatsApp message from {message.from_number}: {message.content[:50]}...")

            # Get or create customer and session
            customer_id = self._get_or_create_customer(message.from_number)
            session_id = self._get_or_create_session(message.from_number, customer_id)

            # Store incoming message
            self._store_message(message, session_id, customer_id, 'inbound')

            # Process message with AI assistant
            ai_response = self._process_with_ai(message.content, customer_id, session_id, message.from_number)

            # Send response back to WhatsApp
            if ai_response and ai_response.get('success'):
                response_message = ai_response.get('message', 'I understand. How can I help you?')
                sent_message = self._send_whatsapp_message(message.from_number, response_message, ai_response)

                if sent_message:
                    # Store outbound message
                    self._store_outbound_message(message.from_number, response_message, session_id, customer_id, sent_message.get('id'))

                return {
                    'customer_id': customer_id,
                    'session_id': session_id,
                    'ai_response': ai_response,
                    'sent_message_id': sent_message.get('id') if sent_message else None
                }

            return None

        except Exception as e:
            logger.error(f"❌ Error processing incoming message: {e}")
            return None

    def _process_with_ai(self, message_content: str, customer_id: int, session_id: str, phone_number: str) -> Dict[str, Any]:
        """Process message with existing AI system"""
        try:
            # Try shopping conversation first (for orders, cart management, etc.)
            shopping_response = self.ai_assistant.process_shopping_conversation(
                user_message=message_content,
                customer_id=customer_id,
                session_id=session_id
            )

            # If shopping conversation was successful, return it
            if shopping_response.get('success') or shopping_response.get('action') != 'general_shopping_prompt':
                shopping_response['channel'] = 'whatsapp'
                shopping_response['phone_number'] = phone_number
                return shopping_response

            # Fall back to general enhanced query processing
            from .enhanced_db_querying import EnhancedDatabaseQuerying
            enhanced_db = EnhancedDatabaseQuerying()

            general_response = enhanced_db.process_enhanced_query(
                user_query=message_content,
                session_context={
                    'customer_id': customer_id,
                    'session_id': session_id,
                    'channel': 'whatsapp',
                    'phone_number': phone_number
                }
            )

            general_response['channel'] = 'whatsapp'
            general_response['phone_number'] = phone_number
            return general_response

        except Exception as e:
            logger.error(f"❌ Error processing with AI: {e}")
            return {
                'success': False,
                'message': "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                'error': str(e),
                'channel': 'whatsapp',
                'phone_number': phone_number
            }

    def _send_whatsapp_message(self, to_number: str, message: str, ai_response: Dict = None) -> Optional[Dict]:
        """Send message via WhatsApp Business API"""
        try:
            if not self.config.is_configured():
                logger.warning("⚠️ WhatsApp not configured, simulating message send")
                return {'id': f'sim_{uuid.uuid4()}', 'status': 'simulated'}

            url = f"{self.config.api_base_url}/{self.config.phone_number_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.config.access_token}',
                'Content-Type': 'application/json'
            }

            # Format message for WhatsApp
            formatted_message = self._format_message_for_whatsapp(message, ai_response)

            # Remove + prefix from phone number (WhatsApp API format requirement)
            clean_number = to_number.replace('+', '') if to_number else to_number

            data = {
                'messaging_product': 'whatsapp',
                'to': clean_number,
                'type': 'text',
                'text': {
                    'body': formatted_message
                }
            }

            # Add interactive elements for shopping responses
            if ai_response and ai_response.get('action') in ['cart_displayed', 'product_found', 'checkout_ready']:
                interactive_data = self._create_interactive_message(ai_response)
                if interactive_data:
                    data.update(interactive_data)

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ WhatsApp message sent to {clean_number} (original: {to_number})")
                return result.get('messages', [{}])[0]
            else:
                logger.error(f"❌ Failed to send WhatsApp message to {clean_number}: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return None

    def format_message_for_whatsapp(self, message: str, ai_response: Dict = None) -> str:
        """Public method to format AI response message for WhatsApp"""
        return self._format_message_for_whatsapp(message, ai_response)

    def _format_message_for_whatsapp(self, message: str, ai_response: Dict = None) -> str:
        """Format AI response message for WhatsApp"""
        # Remove excessive formatting that doesn't work well in WhatsApp
        formatted = message.replace('**', '*').replace('###', '').replace('####', '')

        # Add WhatsApp-specific formatting
        if ai_response:
            action = ai_response.get('action', '')

            if action == 'order_placed':
                # Add celebration emojis for successful orders
                formatted = f"🎉 {formatted}"
            elif action == 'add_to_cart_success':
                # Add cart emoji for cart additions
                formatted = f"🛒 {formatted}"
            elif action == 'product_found':
                # Add search emoji for product results
                formatted = f"🔍 {formatted}"
            elif 'error' in action or 'failed' in action:
                # Add warning emoji for errors
                formatted = f"⚠️ {formatted}"

        # Ensure message isn't too long for WhatsApp (4096 character limit)
        if len(formatted) > 4000:
            formatted = formatted[:3950] + "...\n\nFor more details, visit: https://raqibtech.com"

        return formatted

    def _create_interactive_message(self, ai_response: Dict) -> Optional[Dict]:
        """Create interactive WhatsApp message based on AI response"""
        action = ai_response.get('action', '')

        if action == 'product_found':
            return {
                'type': 'interactive',
                'interactive': {
                    'type': 'button',
                    'body': {'text': ai_response.get('message', '')},
                    'action': {
                        'buttons': [
                            {'type': 'reply', 'reply': {'id': 'add_to_cart', 'title': '🛒 Add to Cart'}},
                            {'type': 'reply', 'reply': {'id': 'more_details', 'title': '📄 More Details'}},
                            {'type': 'reply', 'reply': {'id': 'similar_products', 'title': '🔍 Similar Items'}}
                        ]
                    }
                }
            }
        elif action == 'cart_displayed':
            return {
                'type': 'interactive',
                'interactive': {
                    'type': 'button',
                    'body': {'text': ai_response.get('message', '')},
                    'action': {
                        'buttons': [
                            {'type': 'reply', 'reply': {'id': 'checkout', 'title': '💳 Checkout'}},
                            {'type': 'reply', 'reply': {'id': 'continue_shopping', 'title': '🛍️ Continue Shopping'}},
                            {'type': 'reply', 'reply': {'id': 'clear_cart', 'title': '🗑️ Clear Cart'}}
                        ]
                    }
                }
            }
        elif action == 'checkout_ready':
            return {
                'type': 'interactive',
                'interactive': {
                    'type': 'button',
                    'body': {'text': ai_response.get('message', '')},
                    'action': {
                        'buttons': [
                            {'type': 'reply', 'reply': {'id': 'place_order', 'title': '✅ Place Order'}},
                            {'type': 'reply', 'reply': {'id': 'edit_order', 'title': '✏️ Edit Order'}},
                            {'type': 'reply', 'reply': {'id': 'cancel', 'title': '❌ Cancel'}}
                        ]
                    }
                }
            }

        return None

    def _get_or_create_customer(self, phone_number: str) -> int:
        """Get existing customer or create new one for WhatsApp number"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check if customer exists with this WhatsApp number
                    cursor.execute("""
                        SELECT customer_id FROM customers
                        WHERE whatsapp_number = %s AND whatsapp_verified = true
                    """, (phone_number,))

                    existing = cursor.fetchone()
                    if existing:
                        return existing['customer_id']

                    # Create new WhatsApp customer
                    cursor.execute("""
                        INSERT INTO customers (
                            name, email, phone, state, lga, address,
                            whatsapp_number, whatsapp_opt_in, whatsapp_verified, whatsapp_first_contact
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                        ) RETURNING customer_id
                    """, (
                        f"WhatsApp User {phone_number[-4:]}",  # name
                        f"whatsapp{phone_number[-10:]}@raqibtech.com",  # email
                        phone_number,  # phone
                        'Lagos',  # state
                        'Lagos Island',  # lga
                        'WhatsApp Customer Address (To be updated)',  # address
                        phone_number,  # whatsapp_number
                        True,  # whatsapp_opt_in
                        True  # whatsapp_verified
                    ))

                    result = cursor.fetchone()
                    conn.commit()

                    customer_id = result['customer_id']
                    logger.info(f"✅ Created new WhatsApp customer: {customer_id} for {phone_number}")
                    return customer_id

        except Exception as e:
            logger.error(f"❌ Error creating WhatsApp customer: {e}")
            # Return a default customer ID for graceful degradation
            return 1  # Assuming customer ID 1 exists as fallback

    def _get_or_create_session(self, phone_number: str, customer_id: int) -> str:
        """Get or create session for WhatsApp conversation"""
        try:
            # Create proper UUID session ID for WhatsApp
            session_id = str(uuid.uuid4())

            # Use existing session manager to create/get session
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Create or get session
                    cursor.execute("""
                        SELECT session_id FROM user_sessions
                        WHERE user_identifier = %s
                        ORDER BY created_at DESC LIMIT 1
                    """, (phone_number,))

                    existing = cursor.fetchone()
                    if existing:
                        return existing['session_id']

                    # Create new session with proper UUID
                    cursor.execute("""
                        INSERT INTO user_sessions (session_id, user_identifier, session_data)
                        VALUES (%s, %s, %s)
                    """, (session_id, f"whatsapp:{phone_number}", json.dumps({
                        'channel': 'whatsapp',
                        'phone_number': phone_number,
                        'customer_id': customer_id,
                        'created_via': 'whatsapp_business_api'
                    })))
                    conn.commit()
                    logger.info(f"✅ Created WhatsApp session: {session_id}")

                    return session_id

        except Exception as e:
            logger.error(f"❌ Error creating WhatsApp session: {e}")
            return str(uuid.uuid4())  # Always return proper UUID

    def _store_message(self, message: WhatsAppMessage, session_id: str, customer_id: int, direction: str):
        """Store WhatsApp message in database"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if message already exists (prevent duplicates)
                    cursor.execute("""
                        SELECT whatsapp_message_id FROM whatsapp_messages
                        WHERE whatsapp_message_id = %s
                    """, (message.message_id,))

                    if cursor.fetchone():
                        logger.info(f"📱 Message {message.message_id} already exists, skipping duplicate")
                        return

                    # Insert new message
                    cursor.execute("""
                        INSERT INTO whatsapp_messages (
                            whatsapp_message_id, phone_number, customer_id,
                            message_type, direction, content, button_reply,
                            timestamp, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        message.message_id,
                        message.from_number,
                        customer_id,
                        message.message_type,
                        direction,
                        message.content,
                        getattr(message, 'button_reply', None),
                        datetime.fromtimestamp(int(message.timestamp)) if message.timestamp else datetime.now(),
                        json.dumps({
                            'session_id': session_id,
                            'raw_message': message.raw_data
                        })
                    ))
                    conn.commit()
                    logger.info(f"✅ Stored WhatsApp message: {message.message_id}")

        except Exception as e:
            logger.error(f"❌ Error storing WhatsApp message: {e}")

    def _store_outbound_message(self, to_number: str, content: str, session_id: str, customer_id: int, message_id: str):
        """Store outbound WhatsApp message"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_messages (
                            whatsapp_message_id, phone_number, customer_id,
                            message_type, direction, content, timestamp, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        message_id,
                        to_number,
                        customer_id,
                        'text',
                        'outbound',
                        content,
                        datetime.now(),
                        json.dumps({'session_id': session_id})
                    ))
                    conn.commit()

        except Exception as e:
            logger.error(f"❌ Error storing outbound WhatsApp message: {e}")

    def _process_message_status(self, status_data: Dict):
        """Process WhatsApp message status updates"""
        try:
            message_id = status_data.get('id')
            status = status_data.get('status')  # sent, delivered, read, failed

            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE whatsapp_messages
                        SET status = %s
                        WHERE whatsapp_message_id = %s
                    """, (status, message_id))
                    conn.commit()

        except Exception as e:
            logger.error(f"❌ Error processing message status: {e}")

    def _log_webhook_event(self, webhook_data: Dict):
        """Log webhook event for debugging and monitoring"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_webhook_events (
                            event_type, webhook_payload, processed
                        ) VALUES (%s, %s, %s)
                    """, (
                        'message',  # Default type
                        json.dumps(webhook_data),
                        True
                    ))
                    conn.commit()

        except Exception as e:
            logger.error(f"❌ Error logging webhook event: {e}")

    def send_order_confirmation(self, customer_id: int, order_details: Dict) -> bool:
        """Send order confirmation via WhatsApp"""
        try:
            # Get customer's WhatsApp number
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT whatsapp_number FROM customers
                        WHERE customer_id = %s AND whatsapp_opt_in = true
                    """, (customer_id,))

                    customer = cursor.fetchone()
                    if not customer or not customer['whatsapp_number']:
                        return False

                    # Format order confirmation message
                    message = self._format_order_confirmation(order_details)

                    # Send message
                    sent = self._send_whatsapp_message(customer['whatsapp_number'], message)
                    return sent is not None

        except Exception as e:
            logger.error(f"❌ Error sending order confirmation: {e}")
            return False

    def _format_order_confirmation(self, order_details: Dict) -> str:
        """Format order confirmation message"""
        order_id = order_details.get('order_id', 'N/A')
        total = order_details.get('total_amount', 0)
        delivery_state = order_details.get('delivery_state', 'Lagos')
        payment_method = order_details.get('payment_method', 'Pay on Delivery')

        return f"""✅ Order Confirmed!

📦 Order ID: {order_id}
💰 Total: ₦{total:,.2f}
🚚 Delivery: 2-3 days to {delivery_state}
💳 Payment: {payment_method}

Track your order: https://raqibtech.com/orders/{order_id}

Thank you for choosing RaqibTech! 🎉"""

# Singleton instance
whatsapp_handler = None

def get_whatsapp_handler() -> WhatsAppBusinessHandler:
    """Get singleton WhatsApp handler instance"""
    global whatsapp_handler
    if whatsapp_handler is None:
        whatsapp_handler = WhatsAppBusinessHandler()
    return whatsapp_handler
