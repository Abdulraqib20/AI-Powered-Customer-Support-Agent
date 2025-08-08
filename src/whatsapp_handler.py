"""
WhatsApp Business API Handler for RaqibTech Customer Support Agent
Integrates WhatsApp conversations with existing AI system, session management, and order processing
"""

import os
import json
import requests
import logging
import re
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import hmac
from dotenv import load_dotenv
from src.order_image_generator import generate_order_image, cleanup_order_image
import redis
import time
import sys
from pathlib import Path
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import safe_int_env, safe_str_env

load_dotenv(override=True)

# Import existing system components
from .order_ai_assistant import OrderAIAssistant
from .session_manager import SessionManager
from .conversation_memory_system import WorldClassMemorySystem
from .whatsapp_rate_limiter import rate_limiter, WhatsAppRateLimiter

logger = logging.getLogger(__name__)

@dataclass
class WhatsAppMessage:
    """WhatsApp message data structure"""
    message_id: str
    from_number: str
    content: str
    message_type: str
    timestamp: datetime
    raw_data: Dict

    def __init__(self, message_data: Dict):
        """Initialize from WhatsApp webhook data"""
        try:
            self.message_id = message_data.get('id', '')
            self.from_number = message_data.get('from', '')
            self.raw_data = message_data  # Store the raw data

            # Handle different message types
            if 'text' in message_data:
                self.content = message_data['text'].get('body', '')
                self.message_type = 'text'
            elif 'button' in message_data:
                self.content = message_data['button'].get('text', '')
                self.message_type = 'button'
            elif 'interactive' in message_data:
                # Handle interactive messages (buttons, lists)
                interactive = message_data['interactive']
                if 'button_reply' in interactive:
                    self.content = interactive['button_reply'].get('title', '')
                elif 'list_reply' in interactive:
                    self.content = interactive['list_reply'].get('title', '')
                else:
                    self.content = 'Interactive message'
                self.message_type = 'interactive'
            else:
                self.content = 'Unsupported message type'
                self.message_type = 'unknown'

            # Parse timestamp
            timestamp_str = message_data.get('timestamp', str(int(time.time())))
            self.timestamp = datetime.fromtimestamp(int(timestamp_str))

        except Exception as e:
            logger.error(f"❌ Error parsing WhatsApp message: {e}")
            # Set defaults
            self.message_id = str(uuid.uuid4())
            self.from_number = 'unknown'
            self.content = 'Error parsing message'
            self.message_type = 'error'
            self.timestamp = datetime.now()
            self.raw_data = message_data if message_data else {}

@dataclass
class WhatsAppConfig:
    """WhatsApp Business API configuration"""
    verify_token: str
    access_token: str
    phone_number_id: str
    db_config: Dict[str, str]

    def __init__(self):
        from config.appconfig import (
            WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_BUSINESS_ACCOUNT_ID,
            WHATSAPP_WEBHOOK_VERIFY_TOKEN, WHATSAPP_API_BASE_URL, DEVELOPER_WHATSAPP_NUMBER
        )

        self.access_token = WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID
        self.business_account_id = WHATSAPP_BUSINESS_ACCOUNT_ID
        self.webhook_verify_token = WHATSAPP_WEBHOOK_VERIFY_TOKEN
        self.api_base_url = WHATSAPP_API_BASE_URL
        self.developer_number = DEVELOPER_WHATSAPP_NUMBER
        self.verify_token = WHATSAPP_WEBHOOK_VERIFY_TOKEN  # Use the same token
        # Database configuration
        self.db_config = {
            'host': safe_str_env('DB_HOST', 'localhost'),
            'port': safe_int_env('DB_PORT', 5432),
            'database': safe_str_env('DB_NAME', 'nigerian_ecommerce'),
            'user': safe_str_env('DB_USER', 'postgres'),
            'password': safe_str_env('DB_PASSWORD', 'oracle'),
        }

    def is_configured(self) -> bool:
        """Check if all required configuration is available"""
        return bool(self.access_token and self.phone_number_id)

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

            # Initialize processed messages cache for deduplication
            self.processed_messages = set()
            self.processed_messages_ttl = {}  # message_id -> expiry_time

            logger.info("✅ WhatsApp handler initialized with existing AI system")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI components: {e}")
            raise

        # 🤖 Initialize Agent Memory System for persistent learning
        try:
            from .agent_memory_system import get_agent_memory_system
            self.agent_memory = get_agent_memory_system()
            logger.info("🤖 WhatsApp Agent Memory System integrated successfully")
        except Exception as e:
            logger.warning(f"⚠️ WhatsApp Agent Memory System integration failed: {e}")
            self.agent_memory = None

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
        expected_token = self.config.verify_token

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

            # Check if there are any actual messages to process before doing anything
            has_messages = False
            total_messages = 0

            for entry in entries:
                changes = entry.get('changes', [])
                for change in changes:
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        messages = value.get('messages', [])
                        total_messages += len(messages)
                        if messages:
                            has_messages = True

            # If no messages, just process status updates without creating sessions
            if not has_messages:
                logger.info(f"📱 Webhook received with {total_messages} messages - processing status updates only")
                for entry in entries:
                    changes = entry.get('changes', [])
                    for change in changes:
                        if change.get('field') == 'messages':
                            value = change.get('value', {})
                            # Process message status updates only
                            statuses = value.get('statuses', [])
                            for status in statuses:
                                self._process_message_status(status)

                return {
                    'success': True,
                    'processed_messages': 0,
                    'responses': [],
                    'status_updates_processed': True
                }

            # Process actual messages
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

            # Check for duplicate message processing
            if self._is_message_processed(message.message_id):
                logger.info(f"🔄 Skipping duplicate message: {message.message_id}")
                return None

            # Mark message as being processed
            self._mark_message_processed(message.message_id)

            logger.info(f"📱 Processing WhatsApp message from {message.from_number}: {message.content[:50]}...")

            # Get or create customer and session
            customer_id = self._get_or_create_customer(message.from_number)
            session_id = self._get_or_create_session(message.from_number, customer_id)

                        # ✅ RATE LIMITING CHECK - Check if user can send messages
            rate_check = rate_limiter.check_message_limit(message.from_number, customer_id)
            if not rate_check.allowed:
                logger.warning(f"🚫 Rate limit exceeded for {message.from_number}: {rate_check.result.value}")

                # Send rate limit message to user
                rate_limit_message = rate_limiter.format_rate_limit_message(rate_check)

                # Use the proper WhatsApp sending method
                try:
                    self._send_whatsapp_message(message.from_number, rate_limit_message)
                    logger.info(f"📤 Sent rate limit message to {message.from_number}")
                except Exception as e:
                    logger.error(f"❌ Failed to send rate limit message: {e}")

                # Still store the incoming message for audit purposes
                self._store_message(message, session_id, customer_id, 'inbound')

                # Log the rate limit event
                self._log_rate_limit_event(message.from_number, customer_id, rate_check)

                return {
                    'success': False,
                    'message': 'Rate limit exceeded',
                    'rate_limited': True,
                    'rate_limit_type': rate_check.result.value,
                    'phone_number': message.from_number,
                    'user_tier': rate_check.user_tier,
                    'reset_time': rate_check.reset_time.isoformat() if rate_check.reset_time else None
                }

            # Store incoming message
            self._store_message(message, session_id, customer_id, 'inbound')

            # Initialize variables to avoid scope issues
            sent_message = None
            cleaned_response = None
            ai_response = None

            # Check for authentication commands first
            auth_response = self._process_authentication_commands(message.content, message.from_number, customer_id, session_id)

            if auth_response:
                # Handle authentication command
                logger.info(f"🔐 Processing authentication command from {message.from_number}")
                response_message = auth_response.get('response', 'Authentication command processed.')
                sent_message = self._send_whatsapp_message(message.from_number, response_message, auth_response)
                cleaned_response = response_message
                ai_response = auth_response
            else:
                # Process message with AI assistant
                ai_response = self._process_with_ai(message.content, customer_id, session_id, message.from_number)

                # DEBUG: Log the full AI response structure
                logger.info(f"🔍 DEBUG: Full AI response structure: {ai_response}")
                logger.info(f"🔍 DEBUG: AI response keys: {list(ai_response.keys()) if ai_response else 'None'}")

                # Send response back to WhatsApp
                if ai_response and ai_response.get('success'):
                    # Handle both shopping responses ('message') and general responses ('response')
                    response_message = ai_response.get('message') or ai_response.get('response', 'I understand. How can I help you?')
                    logger.info(f"🔍 DEBUG: Extracted response_message: '{response_message}'")

                    # For shopping responses, format them properly for WhatsApp
                    if ai_response.get('action') in ['add_to_cart_success', 'cart_displayed', 'checkout_ready', 'product_found']:
                        response_message = self._format_shopping_response(ai_response)
                        logger.info(f"🔍 DEBUG: Formatted shopping response: '{response_message}'")

                    # Clean up AI response formatting tokens and duplicates
                    # BUT exempt order confirmations from aggressive cleaning to preserve full details
                    if ai_response.get('action') == 'order_placed':
                        # For order confirmations, only do light cleaning (remove AI tokens but keep all content)
                        cleaned_response = self._light_clean_ai_response(response_message)
                        logger.info(f"🔍 DEBUG: Light cleaned order confirmation: '{cleaned_response}'")

                        # Generate and send order confirmation image
                        image_sent = self._send_order_confirmation_image(message.from_number, ai_response, customer_id)
                        if image_sent:
                            logger.info(f"📸 Order confirmation image sent successfully")
                        else:
                            logger.warning(f"⚠️ Failed to send order confirmation image, fallback to text only")
                    else:
                        cleaned_response = self._clean_ai_response(response_message)
                        logger.info(f"🔍 DEBUG: Cleaned response_message: '{cleaned_response}'")

                    sent_message = self._send_whatsapp_message(message.from_number, cleaned_response, ai_response)
                else:
                    # Handle failed AI response
                    if ai_response and not ai_response.get('success'):
                        fallback_message = ai_response.get('message', 'I apologize, but I encountered an issue processing your request.')
                        cleaned_response = self._clean_ai_response(fallback_message)
                        sent_message = self._send_whatsapp_message(message.from_number, cleaned_response, ai_response)

            # Store outbound message if one was sent
            if sent_message and cleaned_response:
                self._store_outbound_message(message.from_number, cleaned_response, session_id, customer_id, sent_message.get('id'))

            return {
                'customer_id': customer_id,
                'session_id': session_id,
                'ai_response': ai_response,
                'sent_message_id': sent_message.get('id') if sent_message else None
            }

        except Exception as e:
            logger.error(f"❌ Error processing incoming message: {e}")
            return None

    def _process_with_ai(self, message_content: str, customer_id: int, session_id: str, phone_number: str) -> Dict[str, Any]:
        """Process message with existing AI system enhanced with agent memory"""
        try:
            # Short-circuit trivial greetings to avoid unnecessary DB flow and internal fallback messages
            def _is_greeting(text: str) -> bool:
                if not text:
                    return False
                cleaned = ''.join(ch for ch in text.lower().strip() if ch.isalnum() or ch.isspace())
                cleaned = ' '.join(cleaned.split())
                greeting_phrases = {
                    'hi', 'hello', 'hey', 'yo', 'sup',
                    'good morning', 'good afternoon', 'good evening',
                    'morning', 'afternoon', 'evening',
                    'whats up', 'what up', 'hiya'
                }
                if cleaned in greeting_phrases:
                    return True
                # Extremely short non-informational messages (1-2 tokens) are treated as greetings
                tokens = cleaned.split()
                return len(tokens) <= 2 and any(t in greeting_phrases for t in ('hi', 'hello', 'hey', 'yo'))

            if _is_greeting(message_content):
                friendly_greeting = (
                    "Hello! 😊 Welcome to raqibtech.com. I'm here to help with products, orders, or account questions. "
                    "What would you like to do today?"
                )
                return {
                    'success': True,
                    'response': friendly_greeting,
                    'action': 'general_conversation',
                    'channel': 'whatsapp',
                    'phone_number': phone_number
                }

            # 🤖 Get agent memory context for personalization
            agent_memory_context = self._get_agent_memory_context(message_content, customer_id, session_id, phone_number)

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

            # Get authentication status and user details for proper context
            is_authenticated = self._is_user_authenticated(customer_id)
            user_info = self._get_authenticated_user_info(customer_id) if is_authenticated else {}

            # Set correct user_id for conversation history lookup
            user_id = user_info.get('email', phone_number) if is_authenticated else 'anonymous'

            general_response = enhanced_db.process_enhanced_query(
                user_query=message_content,
                session_context={
                    'customer_id': customer_id,
                    'session_id': session_id,
                    'channel': 'whatsapp',
                    'phone_number': phone_number,
                    'user_authenticated': is_authenticated,
                    'user_id': user_id,
                    'customer_name': user_info.get('name'),
                    'customer_email': user_info.get('email'),
                    'user_role': 'customer',  # ✅ Fixed: Always 'customer' for regular users
                    'account_tier': user_info.get('tier')
                }
            )

            # Sanitize any internal fallback messages from DB layer before responding to user
            if isinstance(general_response, dict):
                resp_text = general_response.get('response')
                if isinstance(resp_text, str) and 'Invalid query structure detected' in resp_text:
                    general_response['response'] = (
                        "Hello! 😊 I'm here to help. Tell me what you'd like to do — for example, "
                        "'show latest phones', 'view my orders', or 'help with delivery fees'."
                    )

            general_response['channel'] = 'whatsapp'
            general_response['phone_number'] = phone_number

            # 🤖 Store insights in agent memory after processing
            self._store_agent_memory_insights(message_content, general_response, customer_id, session_id, phone_number)

            return general_response

        except Exception as e:
            logger.error(f"❌ Error processing with AI: {e}")

            # 🤖 Store error insights in agent memory
            self._store_agent_memory_insights(message_content, {'error': str(e)}, customer_id, session_id, phone_number)

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

    def _send_order_confirmation_image(self, to_number: str, ai_response: Dict, customer_id: int = None) -> bool:
        """Generate and send order confirmation image via WhatsApp"""
        try:
            # Extract order data from AI response with customer_id for database lookup
            order_data = self._extract_order_data_for_image(ai_response, customer_id)

            # Generate image using the sophisticated emoji generator
            from .order_image_generator import generate_order_image, cleanup_order_image
            image_path = generate_order_image(order_data)
            if not image_path:
                logger.error("❌ Failed to generate order confirmation image")
                return False

            # Send image via WhatsApp
            success = self._send_whatsapp_image(to_number, image_path, "🎉 Order Confirmation - raqibtech.com")

            # Clean up temporary image file
            cleanup_order_image(image_path)

            return success

        except Exception as e:
            logger.error(f"❌ Error sending order confirmation image: {e}")
            return False

    def _extract_order_data_for_image(self, ai_response: Dict, customer_id: int = None) -> Dict[str, Any]:
        """Extract order data from AI response for image generation with database customer lookup"""
        try:
            # Get order ID from AI response
            order_id = ai_response.get('order_id', 'N/A')

            # The order_summary is a formatted string, we need to parse key information from it
            order_summary_text = ai_response.get('order_summary', '')

            # Get real customer info including tier from database
            customer_name = 'Valued Customer'  # Default fallback
            customer_tier = 'Bronze'  # Default tier
            if customer_id:
                try:
                    user_info = self._get_authenticated_user_info(customer_id)
                    if user_info:
                        # Extract both name and tier from authenticated user info
                        if user_info.get('name'):
                            customer_name = user_info['name']
                        if user_info.get('tier'):  # 🎯 FIXED: Extract tier from user_info
                            customer_tier = user_info['tier']
                        logger.info(f"✅ Retrieved customer info from auth: {customer_name} ({customer_tier} tier)")
                    else:
                        # Fallback: try to get customer info from customers table
                        with self.get_database_connection() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT name, account_tier FROM customers WHERE customer_id = %s", (customer_id,))
                                result = cursor.fetchone()
                                if result:
                                    if result[0]:
                                        customer_name = result[0]
                                    if result[1]:
                                        customer_tier = result[1]
                                logger.info(f"✅ Retrieved customer info from DB fallback: {customer_name} ({customer_tier} tier)")
                except Exception as e:
                    logger.warning(f"⚠️ Could not retrieve customer info from database: {e}")

            # 🔧 CRITICAL FIX: Fetch actual order details from database instead of parsing text
            order_data = None
            if order_id and hasattr(self, 'ai_system') and hasattr(self.ai_system, 'order_system'):
                try:
                    # Get actual order details from order management system
                    order_details = self.ai_system.order_system.get_order_details(order_id)
                    if order_details and order_details.get('success'):
                        order_data = order_details
                        # Ensure customer info is set
                        order_data['customer_name'] = customer_name
                        order_data['customer_tier'] = customer_tier
                        order_data['account_tier'] = customer_tier

                        # 🔧 CRITICAL FIX: Ensure discount info is properly set from database
                        if order_data.get('pricing_breakdown') and order_data['pricing_breakdown'].get('tier_discount'):
                            order_data['tier_discount'] = order_data['pricing_breakdown']['tier_discount']
                            order_data['discount_amount'] = order_data['pricing_breakdown']['tier_discount']
                            logger.info(f"💰 Set discount from database: ₦{order_data['tier_discount']:,.2f}")

                        logger.info(f"✅ Retrieved order details from database for {order_id}")
                    else:
                        logger.warning(f"⚠️ Could not fetch order details for {order_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Error fetching order details for {order_id}: {e}")

            # Fallback: Parse basic info from the formatted text if database fetch failed
            if not order_data:
                order_data = {
                    'order_id': order_id,
                    'total_amount': 0,
                    'subtotal': 0,
                    'delivery_fee': self._calculate_delivery_fee(customer_id),  # 🎯 Dynamic delivery fee
                    'tier_discount': 0,  # 🎯 NEW: Include tier discount
                    'discount_amount': 0,  # Alternative field name
                    'account_tier': customer_tier,  # 🎯 NEW: Include customer tier
                    'customer_tier': customer_tier,  # Alternative field name
                    'payment_method': 'Not specified',
                    'delivery_address': 'Not specified',
                    'status': 'Pending',  # Default status for placed orders
                    'customer_name': customer_name,  # Use real customer name from database
                    'items': []
                }

            # 🔧 ENHANCED FIX: Only parse text if we don't have order data from database
            if not order_data.get('success') and isinstance(order_summary_text, str):
                # Extract total amount using regex
                total_match = re.search(r'Total:\s*₦([\d,]+\.?\d*)', order_summary_text)
                if total_match:
                    total_str = total_match.group(1).replace(',', '')
                    try:
                        order_data['total_amount'] = float(total_str)
                    except ValueError:
                        order_data['total_amount'] = 0

                # Extract payment method
                payment_match = re.search(r'Payment:\s*([^\n]+)', order_summary_text)
                if payment_match:
                    order_data['payment_method'] = payment_match.group(1).strip()

                # Extract delivery address
                delivery_match = re.search(r'Delivery:\s*([^\n]+)', order_summary_text)
                if delivery_match:
                    order_data['delivery_address'] = delivery_match.group(1).strip()

                # Extract items using regex - pattern: "• Product Name x{quantity} - ₦{price}"
                item_pattern = r'•\s*([^x\n]+?)\s*x(\d+)\s*-\s*₦([\d,]+\.?\d*)'
                items = re.findall(item_pattern, order_summary_text)

                total_items_value = 0
                for item_match in items:
                    product_name = item_match[0].strip()
                    quantity = int(item_match[1])
                    subtotal_str = item_match[2].replace(',', '')
                    try:
                        subtotal = float(subtotal_str)
                        price = subtotal / quantity if quantity > 0 else 0
                        total_items_value += subtotal

                        order_data['items'].append({
                            'product_name': product_name,
                            'quantity': quantity,
                            'price': price,
                            'subtotal': subtotal
                        })
                    except ValueError:
                        # Skip invalid items
                        continue

                # Calculate subtotal and tier discount based on order structure
                order_data['subtotal'] = total_items_value

                                # 🔧 CRITICAL FIX: Use pricing breakdown from order system if available
                if order_data.get('pricing_breakdown') and order_data['pricing_breakdown'].get('tier_discount'):
                    # Use the already-calculated correct discount from order system
                    tier_discount = order_data['pricing_breakdown']['tier_discount']
                    order_data['tier_discount'] = tier_discount
                    order_data['discount_amount'] = tier_discount
                    logger.info(f"💰 Using order system discount: ₦{tier_discount:,.2f} for {customer_tier} customer")
                elif not order_data.get('tier_discount') and order_data['total_amount'] > 0 and total_items_value > 0:
                    # Only calculate if no discount was provided and no pricing breakdown
                    subtotal_plus_delivery = total_items_value + order_data['delivery_fee']

                    # Be conservative - only if there's a clear discount pattern
                    if subtotal_plus_delivery > order_data['total_amount'] and (subtotal_plus_delivery - order_data['total_amount']) <= (total_items_value * 0.2):  # Max 20% discount
                        tier_discount = subtotal_plus_delivery - order_data['total_amount']
                        order_data['tier_discount'] = tier_discount
                        order_data['discount_amount'] = tier_discount
                        logger.info(f"💰 Calculated tier discount: ₦{tier_discount:,.2f} for {customer_tier} customer")
                    else:
                        # No clear discount pattern, assume no discount
                        order_data['tier_discount'] = 0
                        order_data['discount_amount'] = 0

            # Ensure we have at least one item for display
            if not order_data['items']:
                order_data['items'] = [{
                    'product_name': 'Order Item',
                    'quantity': 1,
                    'price': max(0, order_data['total_amount'] - order_data['delivery_fee']),
                    'subtotal': max(0, order_data['total_amount'] - order_data['delivery_fee'])
                }]
                order_data['subtotal'] = max(0, order_data['total_amount'] - order_data['delivery_fee'])

            logger.info(f"✅ Extracted order data for image: Order {order_id}, Customer: {customer_name} ({customer_tier}), Total: ₦{order_data['total_amount']:,.2f}, Discount: ₦{order_data['tier_discount']:,.2f}")
            return order_data

        except Exception as e:
            logger.error(f"❌ Error extracting order data for image: {e}")
            import traceback
            traceback.print_exc()

            # Return fallback data with real customer name if available
            fallback_customer_name = 'Valued Customer'
            fallback_customer_tier = 'Bronze'
            if customer_id:
                try:
                    user_info = self._get_authenticated_user_info(customer_id)
                    if user_info and user_info.get('name'):
                        fallback_customer_name = user_info['name']
                except:
                    pass

            return {
                'order_id': ai_response.get('order_id', 'N/A'),
                'total_amount': 0,
                'subtotal': 0,
                'delivery_fee': self._calculate_delivery_fee(customer_id),  # 🎯 Dynamic delivery fee
                'tier_discount': 0,  # 🎯 NEW: Include tier discount
                'discount_amount': 0,  # Alternative field name
                'account_tier': fallback_customer_tier,  # 🎯 NEW: Include customer tier
                'customer_tier': fallback_customer_tier,  # Alternative field name
                'payment_method': 'Not specified',
                'delivery_address': 'Not specified',
                'status': 'Pending',
                'customer_name': fallback_customer_name,
                'items': [{'product_name': 'Order Item', 'quantity': 1, 'price': 0, 'subtotal': 0}]
            }

    def _send_whatsapp_image(self, to_number: str, image_path: str, caption: str = "") -> bool:
        """Send image via WhatsApp Business API"""
        try:
            if not self.config.is_configured():
                logger.warning("⚠️ WhatsApp not configured, simulating image send")
                return True  # Simulate success

            # First, upload the image to WhatsApp
            media_id = self._upload_whatsapp_media(image_path)
            if not media_id:
                logger.error("❌ Failed to upload image to WhatsApp")
                return False

            # Send the image message
            url = f"{self.config.api_base_url}/{self.config.phone_number_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.config.access_token}',
                'Content-Type': 'application/json'
            }

            # Remove + prefix from phone number
            clean_number = to_number.replace('+', '') if to_number else to_number

            data = {
                'messaging_product': 'whatsapp',
                'to': clean_number,
                'type': 'image',
                'image': {
                    'id': media_id
                }
            }

            if caption:
                data['image']['caption'] = caption

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                logger.info(f"✅ WhatsApp image sent to {clean_number}")
                return True
            else:
                logger.error(f"❌ Failed to send WhatsApp image: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp image: {e}")
            return False

    def _upload_whatsapp_media(self, file_path: str) -> Optional[str]:
        """Upload media file to WhatsApp and return media ID"""
        try:
            if not self.config.is_configured():
                return "simulated_media_id"  # Simulate for testing

            url = f"{self.config.api_base_url}/{self.config.phone_number_id}/media"
            headers = {
                'Authorization': f'Bearer {self.config.access_token}'
            }

            # Prepare multipart form data with proper file type
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'image/png'),
                    'messaging_product': (None, 'whatsapp'),
                    'type': (None, 'image/png')
                }

                response = requests.post(url, headers=headers, files=files)

            if response.status_code == 200:
                result = response.json()
                media_id = result.get('id')
                logger.info(f"✅ Media uploaded successfully, ID: {media_id}")
                return media_id
            else:
                logger.error(f"❌ Failed to upload media: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error uploading media: {e}")
            return None

    def format_message_for_whatsapp(self, message: str, ai_response: Dict = None) -> str:
        """Public method to format AI response message for WhatsApp"""
        return self._format_message_for_whatsapp(message, ai_response)

    def _light_clean_ai_response(self, message: str) -> str:
        """Light cleaning for order confirmations - only remove AI tokens, preserve all content"""
        if not message:
            return message

        # Remove AI model formatting tokens and artifacts ONLY
        patterns_to_remove = [
            r'assistant<\|header_end\|>',
            r'<\|header_start\|>',
            r'<\|header_end\|>',
            r'<\|.*?\|>',  # Any other special tokens
            r'Yourassistant',
            r'assistant\s*$',  # "assistant" at end of line
            r'assistant\s*assistant',  # Duplicate "assistant"
            r'^\s*assistant\s*',  # "assistant" at start of line
        ]

        import re
        cleaned = message
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        # Only clean up excessive consecutive newlines (preserve formatting structure)
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Max 2 consecutive newlines
        cleaned = cleaned.strip()

        return cleaned if cleaned else "I understand. How can I help you?"

    def _clean_ai_response(self, message: str) -> str:
        """Clean up AI response formatting tokens and duplicates"""
        if not message:
            return message

        # Remove AI model formatting tokens and artifacts
        patterns_to_remove = [
            r'assistant<\|header_end\|>',
            r'<\|header_start\|>',
            r'<\|header_end\|>',
            r'<\|.*?\|>',  # Any other special tokens
            r'Yourassistant',
            r'assistant\s*$',  # "assistant" at end of line
            r'assistant\s*assistant',  # Duplicate "assistant"
            r'^\s*assistant\s*',  # "assistant" at start of line
        ]

        import re
        cleaned = message
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        # Clean up excessive newlines and duplicate content
        lines = cleaned.split('\n')
        unique_lines = []
        seen_lines = set()

        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(stripped)
            elif not stripped:  # Keep empty lines for formatting
                unique_lines.append(line)

        # Join lines and clean up excessive whitespace
        cleaned = '\n'.join(unique_lines)
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Max 2 consecutive newlines
        cleaned = cleaned.strip()

        return cleaned if cleaned else "I understand. How can I help you?"

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

    def _format_nigerian_phone(self, phone_number: str) -> str:
        """Format phone number to comply with database constraint"""
        # Remove any existing + or 0 prefix
        cleaned = phone_number.lstrip('+0')

        # If starts with 234, add + prefix for international format
        if cleaned.startswith('234'):
            return f"+{cleaned}"

        # If it's a 10-digit local number, add +234 prefix
        if len(cleaned) == 10 and cleaned[0] in '789':
            return f"+234{cleaned}"

        # Return original if format is unclear
        return phone_number

    def _get_or_create_customer(self, phone_number: str) -> int:
        """Get existing customer or create new one for WhatsApp number"""
        try:
            # Format phone number for database constraint compliance
            formatted_phone = self._format_nigerian_phone(phone_number)

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
                        formatted_phone,  # phone - use formatted version for DB constraint
                        'Lagos',  # state
                        'Lagos Island',  # lga
                        'WhatsApp Customer Address (To be updated)',  # address
                        phone_number,  # whatsapp_number - keep original for WhatsApp API
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
        """Get or create session for WhatsApp conversation with race condition protection"""
        try:
            user_identifier = f"whatsapp:{phone_number}"

            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check for existing authenticated session first (email-based)
                    cursor.execute("""
                        SELECT us.session_id, us.user_identifier
                        FROM user_sessions us
                        JOIN customers c ON c.email = us.user_identifier
                        WHERE c.whatsapp_number = %s AND c.customer_id = %s
                        ORDER BY us.last_active DESC LIMIT 1
                    """, (phone_number, customer_id))

                    authenticated_session = cursor.fetchone()
                    if authenticated_session:
                        logger.info(f"✅ Using existing authenticated session: {authenticated_session['session_id']} ({authenticated_session['user_identifier']})")
                        return authenticated_session['session_id']

                    # Use INSERT ... ON CONFLICT to handle race conditions atomically
                    session_id = str(uuid.uuid4())
                    session_data = json.dumps({
                        'channel': 'whatsapp',
                        'phone_number': phone_number,
                        'customer_id': customer_id,
                        'created_via': 'whatsapp_business_api'
                    })

                    cursor.execute("""
                        INSERT INTO user_sessions (session_id, user_identifier, session_data)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_identifier) DO UPDATE SET
                            last_active = CURRENT_TIMESTAMP
                        RETURNING session_id,
                                  CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as action
                    """, (session_id, user_identifier, session_data))

                    result = cursor.fetchone()
                    conn.commit()

                    if result['action'] == 'inserted':
                        logger.info(f"✅ Created new WhatsApp session: {result['session_id']}")
                    else:
                        logger.info(f"✅ Using existing WhatsApp session: {result['session_id']}")

                    return result['session_id']

        except Exception as e:
            logger.error(f"❌ Error handling WhatsApp session: {e}")
            logger.error(f"❌ Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")

            # Fallback: try to get existing session one more time
            try:
                user_identifier = f"whatsapp:{phone_number}"
                with self.get_database_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("""
                            SELECT session_id FROM user_sessions
                            WHERE user_identifier = %s
                            ORDER BY created_at DESC LIMIT 1
                        """, (user_identifier,))
                        existing = cursor.fetchone()
                        if existing:
                            logger.info(f"✅ Fallback: Using existing session {existing['session_id']}")
                            return existing['session_id']
            except Exception as fallback_e:
                logger.error(f"❌ Fallback session retrieval also failed: {fallback_e}")

            # Try creating a simple session without ON CONFLICT as last resort
            try:
                user_identifier = f"whatsapp:{phone_number}"
                session_id = str(uuid.uuid4())
                session_data = json.dumps({
                    'channel': 'whatsapp',
                    'phone_number': phone_number,
                    'customer_id': customer_id,
                    'created_via': 'whatsapp_business_api_fallback'
                })

                with self.get_database_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        # Simple insert without ON CONFLICT
                        cursor.execute("""
                            INSERT INTO user_sessions (session_id, user_identifier, session_data)
                            VALUES (%s, %s, %s)
                            RETURNING session_id
                        """, (session_id, user_identifier, session_data))

                        result = cursor.fetchone()
                        conn.commit()

                        if result:
                            logger.info(f"✅ Created fallback session: {result['session_id']}")
                            return result['session_id']

            except Exception as final_e:
                logger.error(f"❌ Final fallback session creation failed: {final_e}")

            # Last resort fallback - return UUID but warn it's not in DB
            fallback_id = str(uuid.uuid4())
            logger.warning(f"⚠️ Using in-memory fallback session ID (NOT STORED IN DB): {fallback_id}")
            return fallback_id

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
                        message.timestamp.isoformat() if message.timestamp else datetime.now().isoformat(),
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

    def _log_rate_limit_event(self, phone_number: str, customer_id: int, rate_check):
        """Log rate limit violation for monitoring"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO whatsapp_rate_limit_events (
                            phone_number, customer_id, event_type, limit_type, details
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (
                        phone_number,
                        customer_id,
                        'limit_exceeded_blocked',  # Indicates user was blocked from sending
                        rate_check.result.value,
                        json.dumps({
                            'user_tier': rate_check.user_tier,
                            'current_count': rate_check.current_count,
                            'limit': rate_check.limit,
                            'reset_time': rate_check.reset_time.isoformat() if rate_check.reset_time else None,
                            'message_content_preview': 'Message blocked due to rate limit'
                        })
                    ))
                    conn.commit()
                    logger.info(f"📊 Logged rate limit event for {phone_number}")

        except Exception as e:
            logger.error(f"❌ Error logging rate limit event: {e}")

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

    def _process_authentication_commands(self, message_content: str, phone_number: str, customer_id: int, session_id: str) -> Optional[Dict]:
        """Handle WhatsApp authentication commands (signup, login, account linking)"""
        content_lower = message_content.lower().strip()

        # Check for SPECIFIC authentication commands first (order matters!)
        if content_lower.startswith('verify email:'):
            # Handle email verification step
            email = content_lower.replace('verify email:', '').strip()
            return self._handle_email_verification(email, phone_number, customer_id, session_id)

        elif content_lower.startswith('complete signup:'):
            # Handle complete signup with user details
            signup_data = content_lower.replace('complete signup:', '').strip()
            return self._handle_complete_signup(signup_data, phone_number, customer_id, session_id)

        elif content_lower.startswith('login email:'):
            # Handle login with email - MUST come before general 'login' check
            email = content_lower.replace('login email:', '').strip()
            return self._handle_email_login(email, phone_number, customer_id, session_id)

        # Check for GENERAL authentication commands (less specific)
        elif any(keyword in content_lower for keyword in ['signup', 'register', 'create account', 'sign up']):
            return self._handle_signup_command(phone_number, customer_id, session_id)

        elif any(keyword in content_lower for keyword in ['login', 'sign in', 'signin']):
            return self._handle_login_command(phone_number, customer_id, session_id)

        elif any(keyword in content_lower for keyword in ['logout', 'sign out', 'signout', 'log out']):
            return self._handle_logout_command(phone_number, customer_id, session_id)

        elif any(keyword in content_lower for keyword in ['link account', 'connect account', 'upgrade account']):
            return self._handle_account_linking(phone_number, customer_id, session_id)

        return None

    def _handle_signup_command(self, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle WhatsApp signup command"""
        try:
            # Check if user is already authenticated
            if self._is_user_authenticated(customer_id):
                return {
                    'success': True,
                    'response': "✅ You're already registered! Your account is fully activated with access to all features.\n\n🔍 Try asking: 'show my orders' or 'update my profile'",
                    'query_type': 'authentication',
                    'channel': 'whatsapp'
                }

            signup_instructions = """
🆕 **Create Your RaqibTech Account**

To upgrade from guest to full customer access, please provide:

**Step 1:** Send your email address like this:
`verify email: your-email@example.com`

**Step 2:** Once verified, complete your profile:
`complete signup: Abdulraqib Omotosho | Lagos | Ikeja | Street 123 Victoria Island`

**Benefits of Full Account:**
✅ Order history & tracking
✅ Personalized recommendations
✅ Account tiers (Bronze→Gold→Platinum)
✅ Faster checkout
✅ Exclusive offers

*Already have an account? Type: `login`*
            """

            return {
                'success': True,
                'response': signup_instructions,
                'query_type': 'authentication_signup',
                'channel': 'whatsapp'
            }

        except Exception as e:
            logger.error(f"❌ Error in WhatsApp signup command: {e}")
            return {
                'success': True,
                'response': "Sorry, there was an issue starting the signup process. Please try again or contact support.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _handle_login_command(self, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle WhatsApp login command"""
        try:
            # Check if user is already authenticated
            if self._is_user_authenticated(customer_id):
                user_info = self._get_authenticated_user_info(customer_id)
                return {
                    'success': True,
                    'response': f"✅ Already logged in as **{user_info['name']}**!\n\n🔍 Try: 'show my orders' or 'my account details'",
                    'query_type': 'authentication',
                    'channel': 'whatsapp'
                }

            login_instructions = """
🔑 **Login to Your RaqibTech Account**

**Option 1:** Login with email
`login email: your-email@example.com`

**Option 2:** Link your WhatsApp to existing account
`link account`

**New to RaqibTech?**
Type: `signup` to create your account

*We'll verify your email and automatically log you in!*
            """

            return {
                'success': True,
                'response': login_instructions,
                'query_type': 'authentication_login',
                'channel': 'whatsapp'
            }

        except Exception as e:
            logger.error(f"❌ Error in WhatsApp login command: {e}")
            return {
                'success': True,
                'response': "Sorry, there was an issue with the login process. Please try again or contact support.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _handle_email_verification(self, email: str, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle email verification step"""
        try:
            import re

            # Validate email format
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email):
                return {
                    'success': True,
                    'response': "❌ Invalid email format. Please try again:\n`verify email: your-email@example.com`",
                    'query_type': 'authentication_error',
                    'channel': 'whatsapp'
                }

            # Check if email already exists
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("SELECT customer_id, name FROM customers WHERE email = %s", (email.lower(),))
                    existing_customer = cursor.fetchone()

                    if existing_customer:
                        # Email exists - suggest login instead
                        return {
                            'success': True,
                            'response': f"📧 This email is already registered!\n\n🔑 To login, type:\n`login email: {email}`\n\n🔗 Or to link this WhatsApp to your existing account:\n`link account`",
                            'query_type': 'authentication_existing_email',
                            'channel': 'whatsapp'
                        }

            # Store email for signup process
            self._store_signup_progress(phone_number, session_id, {'email': email.lower(), 'step': 'email_verified'})

            return {
                'success': True,
                'response': f"✅ Email **{email}** verified!\n\n📝 Now complete your profile:\n`complete signup: Full Name | State | LGA | Your Address`\n\n*Example:*\n`complete signup: Abdulraqib Omotosho | Lagos | Ikeja | St. 123 Victoria Island `",
                'query_type': 'authentication_email_verified',
                'channel': 'whatsapp'
            }

        except Exception as e:
            logger.error(f"❌ Error in email verification: {e}")
            return {
                'success': True,
                'response': "Sorry, there was an issue verifying your email. Please try again.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _handle_complete_signup(self, signup_data: str, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle complete signup with user details"""
        try:
            # Get stored email from signup progress
            progress = self._get_signup_progress(phone_number, session_id)
            if not progress or progress.get('step') != 'email_verified':
                return {
                    'success': True,
                    'response': "❌ Please start with email verification first:\n`verify email: your-email@example.com`",
                    'query_type': 'authentication_error',
                    'channel': 'whatsapp'
                }

            # Parse signup data: "Full Name | State | LGA | Address"
            parts = [part.strip() for part in signup_data.split('|')]
            if len(parts) != 4:
                return {
                    'success': True,
                    'response': "❌ Invalid format. Please use:\n`complete signup: Full Name | State | LGA | Your Address`\n\n*Example:*\n`complete signup: Abdulraqib Omotosho | Lagos | Ikeja | St. 123 Victoria Island `",
                    'query_type': 'authentication_error',
                    'channel': 'whatsapp'
                }

            full_name, state, lga, address = parts
            email = progress['email']
            formatted_phone = self._format_nigerian_phone(phone_number)

            # Validate Nigerian phone format
            import re
            nigerian_phone_regex = r'^(\+234|0)[7-9][0-1]\d{8}$'
            if not re.match(nigerian_phone_regex, formatted_phone):
                return {
                    'success': True,
                    'response': f"❌ Phone number format issue. Contact support with your number: {phone_number}",
                    'query_type': 'authentication_error',
                    'channel': 'whatsapp'
                }

            # Create full customer account (upgrade from guest)
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Update existing WhatsApp guest account to full account
                    cursor.execute("""
                        UPDATE customers
                        SET name = %s, email = %s, phone = %s, state = %s, lga = %s,
                            address = %s, account_tier = %s, user_role = %s,
                            preferences = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s
                        RETURNING customer_id, name, email
                    """, (
                        full_name, email, formatted_phone, state, lga, address,
                        'Bronze', 'customer',  # Upgrade from guest to customer
                        json.dumps({
                            'language': 'English',
                            'notifications': True,
                            'newsletter': True,
                            'whatsapp_verified': True
                        }),
                        customer_id
                    ))

                    updated_customer = cursor.fetchone()
                    if not updated_customer:
                        raise Exception("Failed to upgrade customer account")

                    # Update session to authenticated status
                    cursor.execute("""
                        UPDATE user_sessions
                        SET user_identifier = %s,
                            session_data = %s,
                            last_active = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                    """, (
                        email,
                        json.dumps({
                            'channel': 'whatsapp',
                            'phone_number': phone_number,
                            'customer_id': customer_id,
                            'authenticated': True,
                            'upgrade_time': datetime.now().isoformat(),
                            'email': email,
                            'name': full_name
                        }),
                        session_id
                    ))

                    conn.commit()

                    # Clear signup progress
                    self._clear_signup_progress(phone_number, session_id)

                    logger.info(f"✅ WhatsApp user upgraded: {phone_number} -> {email} (Customer ID: {customer_id})")

                    return {
                        'success': True,
                        'response': f"🎉 **Welcome to RaqibTech, {full_name}!**\n\n✅ Your account is now fully activated!\n📧 Email: {email}\n🏆 Account Tier: Bronze\n\n**New Features Unlocked:**\n• Order history & tracking\n• Personalized recommendations\n• Faster checkout\n• Account tier benefits\n\n🛒 Try: 'show my orders' or 'recommend products'",
                        'query_type': 'authentication_success',
                        'channel': 'whatsapp',
                        'customer_id': customer_id,
                        'authenticated': True
                    }

        except Exception as e:
            logger.error(f"❌ Error completing WhatsApp signup: {e}")
            return {
                'success': True,
                'response': "❌ Signup failed. Please try again or contact support.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _handle_email_login(self, email: str, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle login with email address"""
        try:
            import re

            # Validate email format
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email):
                return {
                    'success': True,
                    'response': "❌ Invalid email format. Please try again:\n`login email: your-email@example.com`",
                    'query_type': 'authentication_error',
                    'channel': 'whatsapp'
                }

            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Find customer by email
                    cursor.execute("""
                        SELECT customer_id, name, email, user_role, account_status, whatsapp_number
                        FROM customers
                        WHERE email = %s
                    """, (email.lower(),))

                    customer = cursor.fetchone()
                    if not customer:
                        return {
                            'success': True,
                            'response': f"❌ No account found with email: {email}\n\n🆕 Create account: `signup`\n🔗 Link WhatsApp: `link account`",
                            'query_type': 'authentication_error',
                            'channel': 'whatsapp'
                        }

                    # Check account status
                    if customer['account_status'] != 'active':
                        return {
                            'success': True,
                            'response': f"❌ Account is {customer['account_status']}. Please contact support.",
                            'query_type': 'authentication_error',
                            'channel': 'whatsapp'
                        }

                    # Link WhatsApp to existing account or login existing WhatsApp user
                    existing_customer_id = customer['customer_id']

                    if customer_id != existing_customer_id:
                        # Different customer - need to link WhatsApp to email account
                        # First, transfer any existing WhatsApp messages to the email account
                        cursor.execute("""
                            UPDATE whatsapp_messages
                            SET customer_id = %s
                            WHERE customer_id = %s
                        """, (existing_customer_id, customer_id))

                        # Update any sessions to point to the email account
                        cursor.execute("""
                            UPDATE user_sessions
                            SET session_data = jsonb_set(session_data, '{customer_id}', %s::text::jsonb)
                            WHERE session_id = %s
                        """, (existing_customer_id, session_id))

                        # Delete the temporary WhatsApp guest account
                        cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))

                        # Then update the email account with the WhatsApp number
                        cursor.execute("""
                            UPDATE customers
                            SET whatsapp_number = %s, whatsapp_verified = true, whatsapp_opt_in = true,
                                whatsapp_first_contact = CURRENT_TIMESTAMP
                            WHERE customer_id = %s
                        """, (phone_number, existing_customer_id))

                        customer_id = existing_customer_id  # Use the email account's customer_id

                    # Handle existing email sessions - merge WhatsApp session with email session
                    cursor.execute("""
                        SELECT session_id FROM user_sessions
                        WHERE user_identifier = %s
                    """, (email,))
                    existing_email_session = cursor.fetchone()

                    if existing_email_session:
                        # Update existing email session to include WhatsApp data
                        cursor.execute("""
                            UPDATE user_sessions
                            SET session_data = jsonb_set(
                                session_data,
                                '{whatsapp_linked}',
                                %s::jsonb
                            ),
                            last_active = CURRENT_TIMESTAMP
                            WHERE user_identifier = %s
                        """, (
                            json.dumps({
                                'phone_number': phone_number,
                                'linked_time': datetime.now().isoformat(),
                                'whatsapp_session_id': session_id
                            }),
                            email
                        ))

                        # Delete the temporary WhatsApp session
                        cursor.execute("DELETE FROM user_sessions WHERE session_id = %s", (session_id,))
                        session_id = existing_email_session['session_id']
                    else:
                        # Update current session with authentication
                        cursor.execute("""
                            UPDATE user_sessions
                            SET user_identifier = %s,
                                session_data = %s,
                                last_active = CURRENT_TIMESTAMP
                            WHERE session_id = %s
                        """, (
                            email,
                            json.dumps({
                                'channel': 'whatsapp',
                                'phone_number': phone_number,
                                'customer_id': customer_id,
                                'authenticated': True,
                                'login_time': datetime.now().isoformat(),
                                'email': email,
                                'name': customer['name']
                            }),
                            session_id
                        ))

                    conn.commit()

                    logger.info(f"✅ WhatsApp login successful: {phone_number} -> {email} (Customer ID: {customer_id})")

                    return {
                        'success': True,
                        'response': f"🔑 **Welcome back, {customer['name']}!**\n\n✅ Successfully logged in via WhatsApp\n📧 Email: {email}\n\n🛒 Try: 'show my orders' or 'my account'",
                        'query_type': 'authentication_success',
                        'channel': 'whatsapp',
                        'customer_id': customer_id,
                        'authenticated': True
                    }

        except Exception as e:
            logger.error(f"❌ Error in WhatsApp email login: {e}")
            return {
                'success': True,
                'response': "❌ Login failed. Please try again or contact support.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _handle_account_linking(self, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle account linking between WhatsApp and email accounts"""
        try:
            instructions = """
🔗 **Link Your WhatsApp to Email Account**

If you already have a RaqibTech account with email, you can link it to this WhatsApp number.

**Step 1:** Login with your email:
`login email: your-registered-email@example.com`

**Don't have an email account?**
`signup` - Create a new account

*This will give you access to your order history, preferences, and account benefits!*
            """

            return {
                'success': True,
                'response': instructions,
                'query_type': 'authentication_linking',
                'channel': 'whatsapp'
            }

        except Exception as e:
            logger.error(f"❌ Error in account linking: {e}")
            return {
                'success': True,
                'response': "Sorry, there was an issue with account linking. Please try again.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _handle_logout_command(self, phone_number: str, customer_id: int, session_id: str) -> Dict:
        """Handle WhatsApp logout command - properly clear authentication state"""
        try:
            # Check if user is currently authenticated
            if not self._is_user_authenticated(customer_id):
                return {
                    'success': True,
                    'response': "ℹ️ You're not currently logged in. You're browsing as a guest.\n\n🔑 To login, type: `login`\n🆕 To create account, type: `signup`",
                    'query_type': 'authentication_info',
                    'channel': 'whatsapp'
                }

            # Get user info for personalized goodbye message
            user_info = self._get_authenticated_user_info(customer_id)
            user_name = user_info.get('name', 'there')

            # Perform logout operations
            logout_successful = self._perform_logout(phone_number, customer_id, session_id)

            if logout_successful:
                return {
                    'success': True,
                    'response': f"👋 **Goodbye, {user_name}!**\n\n✅ You've been successfully logged out from WhatsApp\n🔒 Your session has been cleared for security\n\n🔑 To login again, type: `login`\n🆕 New to RaqibTech? Type: `signup`\n\n*Thanks for using RaqibTech! Have a great day!* ✨",
                    'query_type': 'authentication_logout',
                    'channel': 'whatsapp'
                }
            else:
                return {
                    'success': True,
                    'response': "❌ Logout failed. Please try again or contact support.",
                    'query_type': 'authentication_error',
                    'channel': 'whatsapp'
                }

        except Exception as e:
            logger.error(f"❌ Error in logout command: {e}")
            return {
                'success': True,
                'response': "❌ There was an issue logging out. Please try again.",
                'query_type': 'authentication_error',
                'channel': 'whatsapp'
            }

    def _perform_logout(self, phone_number: str, customer_id: int, session_id: str) -> bool:
        """Perform actual logout operations - clear session data while preserving customer account"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    # Step 1: Get current customer info for logging
                    cursor.execute("""
                        SELECT email, name, whatsapp_number FROM customers
                        WHERE customer_id = %s
                    """, (customer_id,))

                    customer = cursor.fetchone()
                    if not customer:
                        return False

                    # Step 2: Clear all sessions for this user (comprehensive approach)
                    # Method 1: Clear by direct identifiers
                    cursor.execute("""
                        DELETE FROM user_sessions
                        WHERE session_id = %s OR user_identifier = %s OR user_identifier = %s
                    """, (session_id, customer['email'], f"whatsapp:{phone_number}"))

                    sessions_cleared_1 = cursor.rowcount

                    # Method 2: Clear any remaining sessions linked to this customer
                    # This ensures complete logout by clearing sessions found via customer relationships
                    cursor.execute("""
                        DELETE FROM user_sessions
                        WHERE session_id IN (
                            SELECT DISTINCT us.session_id
                            FROM user_sessions us
                            JOIN customers c ON (c.email = us.user_identifier OR c.whatsapp_number = %s)
                            WHERE c.customer_id = %s
                        )
                    """, (phone_number, customer_id))

                    sessions_cleared_2 = cursor.rowcount
                    total_sessions = sessions_cleared_1 + sessions_cleared_2

                    logger.info(f"🗑️ Session cleanup: {sessions_cleared_1} direct + {sessions_cleared_2} linked = {total_sessions} total sessions cleared")

                    # Step 3: Clear any signup progress data
                    cursor.execute("""
                        DELETE FROM whatsapp_signup_progress
                        WHERE phone_number = %s
                    """, (phone_number,))

                    conn.commit()

                    logger.info(f"✅ Logout successful for {phone_number} -> {customer['email']} (Customer ID: {customer_id}). Customer account preserved.")

                    # Step 4: Clear Redis cache if available
                    try:
                        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                        # Clear conversation history
                        redis_client.delete(f"conversation:{customer['email']}")
                        redis_client.delete(f"conversation:{session_id}")
                        # Clear signup progress
                        redis_client.delete(f"whatsapp_signup:{phone_number}")
                        logger.info(f"✅ Cleared Redis cache for logged out user")
                    except:
                        logger.info("ℹ️ Redis cache clearing skipped (Redis not available)")

                    return True

        except Exception as e:
            logger.error(f"❌ Error performing logout: {e}")
            return False

    def _is_user_authenticated(self, customer_id: int) -> bool:
        """Check if WhatsApp user is authenticated (has valid customer account AND active session)"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Step 1: Check if customer has valid account
                    cursor.execute("""
                        SELECT user_role, email FROM customers
                        WHERE customer_id = %s
                    """, (customer_id,))

                    customer = cursor.fetchone()
                    if not customer:
                        return False

                    # Check if customer has valid account (not guest)
                    has_valid_account = (customer['user_role'] == 'customer' and
                                       not customer['email'].startswith('whatsapp'))

                    if not has_valid_account:
                        return False

                    # Step 2: Check if they have an active authenticated session
                    cursor.execute("""
                        SELECT session_id FROM user_sessions
                        WHERE user_identifier = %s
                    """, (customer['email'],))

                    active_session = cursor.fetchone()

                    # User is authenticated only if they have both valid account AND active session
                    is_authenticated = active_session is not None

                    logger.info(f"🔐 Authentication check for customer {customer_id}: "
                              f"valid_account={has_valid_account}, active_session={is_authenticated}, "
                              f"email={customer['email']}")

                    return is_authenticated

        except Exception as e:
            logger.error(f"❌ Error checking authentication status: {e}")
            return False

    def _get_authenticated_user_info(self, customer_id: int) -> Dict:
        """Get authenticated user information"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT name, email, account_tier FROM customers
                        WHERE customer_id = %s
                    """, (customer_id,))

                    customer = cursor.fetchone()
                    if customer:
                        return {
                            'name': customer['name'],
                            'email': customer['email'],
                            'tier': customer['account_tier']
                        }
            return {}
        except Exception as e:
            logger.error(f"❌ Error getting user info: {e}")
            return {}

    def _store_signup_progress(self, phone_number: str, session_id: str, progress_data: Dict):
        """Store signup progress in Redis or database"""
        try:
            # Store in Redis if available, otherwise in database
            key = f"whatsapp_signup:{phone_number}"
            progress_data['timestamp'] = datetime.now().isoformat()

            # Try Redis first
            try:
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                redis_client.setex(key, 3600, json.dumps(progress_data))  # 1 hour expiry
                logger.info(f"✅ Stored signup progress in Redis for {phone_number}")
            except:
                # Fallback to database storage
                with self.get_database_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO whatsapp_signup_progress (phone_number, session_id, progress_data, created_at)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (phone_number)
                            DO UPDATE SET progress_data = %s, updated_at = CURRENT_TIMESTAMP
                        """, (phone_number, session_id, json.dumps(progress_data), json.dumps(progress_data)))
                        conn.commit()

        except Exception as e:
            logger.error(f"❌ Error storing signup progress: {e}")

    def _get_signup_progress(self, phone_number: str, session_id: str) -> Optional[Dict]:
        """Get signup progress from Redis or database"""
        try:
            key = f"whatsapp_signup:{phone_number}"

            # Try Redis first
            try:
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                progress_json = redis_client.get(key)
                if progress_json:
                    return json.loads(progress_json)
            except:
                pass

            # Fallback to database
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT progress_data FROM whatsapp_signup_progress
                        WHERE phone_number = %s
                        ORDER BY updated_at DESC LIMIT 1
                    """, (phone_number,))

                    result = cursor.fetchone()
                    if result:
                        return json.loads(result['progress_data'])

            return None

        except Exception as e:
            logger.error(f"❌ Error getting signup progress: {e}")
            return None

    def _clear_signup_progress(self, phone_number: str, session_id: str):
        """Clear signup progress after successful completion"""
        try:
            key = f"whatsapp_signup:{phone_number}"

            # Clear from Redis
            try:
                redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                redis_client.delete(key)
            except:
                pass

            # Clear from database
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM whatsapp_signup_progress WHERE phone_number = %s", (phone_number,))
                    conn.commit()

        except Exception as e:
            logger.error(f"❌ Error clearing signup progress: {e}")

    def _format_shopping_response(self, ai_response: Dict) -> str:
        """Format shopping responses for WhatsApp display"""
        action = ai_response.get('action', '')
        base_message = ai_response.get('message', '')

        if action == 'add_to_cart_success':
            # Format add to cart success with cart summary
            cart_summary = ai_response.get('cart_summary', {})
            product_added = ai_response.get('product_added', {})

            formatted_message = f"🛒 *{base_message}*\n\n"

            # Add product details
            if product_added:
                formatted_message += f"📦 *{product_added['product_name']}*\n"
                formatted_message += f"💰 Price: {product_added.get('currency', 'NGN')} {product_added['price']:,.0f}\n\n"

            # Add cart summary
            if cart_summary and cart_summary.get('items'):
                formatted_message += "*🛒 Your Cart:*\n"
                for item in cart_summary['items']:
                    formatted_message += f"• {item['product_name']} (₦{item['price']:,.0f}) x{item['quantity']}\n"

                formatted_message += f"\n*Total: {cart_summary.get('subtotal_formatted', '₦0.00')}*\n\n"
                formatted_message += "💬 Type *'checkout'* to complete your order\n"
                formatted_message += "🛍️ Type *'show cart'* to view full cart"

            return formatted_message

        elif action == 'cart_displayed':
            # Format cart display
            cart_summary = ai_response.get('cart_summary', {})
            formatted_message = f"🛒 *Your Shopping Cart*\n\n"

            if cart_summary and cart_summary.get('items'):
                for item in cart_summary['items']:
                    formatted_message += f"📦 *{item['product_name']}*\n"
                    formatted_message += f"   ₦{item['price']:,.0f} x {item['quantity']} = ₦{item['subtotal']:,.0f}\n\n"

                formatted_message += f"*💰 Total: {cart_summary.get('subtotal_formatted', '₦0.00')}*\n\n"
                formatted_message += "💳 Type *'checkout'* to complete order\n"
                formatted_message += "➕ Type *'add [product]'* to add more items"
            else:
                formatted_message += "Your cart is empty 🛒\n\n"
                formatted_message += "🛍️ Browse our products by typing what you're looking for!"

            return formatted_message

        elif action == 'checkout_ready':
            # Format checkout confirmation
            formatted_message = f"💳 *{base_message}*\n\n"

            # Add order summary if available
            cart_summary = ai_response.get('cart_summary', {})
            if cart_summary and cart_summary.get('items'):
                formatted_message += "*📋 Order Summary:*\n"
                for item in cart_summary['items']:
                    formatted_message += f"• {item['product_name']} x{item['quantity']}\n"

                formatted_message += f"\n*💰 Total: {cart_summary.get('subtotal_formatted', '₦0.00')}*\n\n"
                formatted_message += "✅ Type *'confirm order'* to place your order\n"
                formatted_message += "✏️ Type *'edit cart'* to make changes"

            return formatted_message

        elif action == 'product_found':
            # Format product details
            product = ai_response.get('product_details', {})
            formatted_message = f"🔍 *{base_message}*\n\n"

            if product:
                formatted_message += f"📦 *{product['product_name']}*\n"
                formatted_message += f"🏷️ Brand: {product.get('brand', 'N/A')}\n"
                formatted_message += f"💰 Price: ₦{product['price']:,.0f}\n"
                formatted_message += f"📊 Stock: {product.get('stock_quantity', 0)} available\n\n"

                if product.get('description'):
                    formatted_message += f"📝 {product['description']}\n\n"

                formatted_message += f"🛒 Type *'add to cart'* to add this item\n"
                formatted_message += f"🔍 Type *'similar products'* for alternatives"

            return formatted_message

        # Default formatting for other actions
        return base_message

    def _calculate_delivery_fee(self, customer_id: int = None, order_value: float = 0, state: str = None) -> float:
        """🚚 Calculate delivery fee using the simplified delivery calculator"""
        try:
            # Import here to avoid circular imports
            from src.order_management import NigerianDeliveryCalculator

            # If state not provided, try to get from customer
            if not state and customer_id:
                try:
                    with self.get_database_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT state FROM customers WHERE customer_id = %s", (customer_id,))
                            result = cursor.fetchone()
                            if result and result[0]:
                                state = result[0]
                except Exception as e:
                    logger.warning(f"⚠️ Could not retrieve customer state: {e}")

            # Default to Lagos if no state found
            if not state:
                state = "Lagos"
                logger.debug(f"Using default state 'Lagos' for delivery calculation")

            # Use the simplified delivery calculator
            delivery_fee, delivery_days, delivery_zone = NigerianDeliveryCalculator.calculate_delivery_fee(
                state, None, order_value  # No weight calculation!
            )

            logger.info(f"🚚 Calculated delivery fee: ₦{delivery_fee:,.2f} for {state} (order value: ₦{order_value:,.2f})")
            return delivery_fee

        except Exception as e:
            logger.error(f"❌ Error calculating delivery fee: {e}")
            # Fallback to Lagos rate
            return 1500.0

    def _get_agent_memory_context(self, message_content: str, customer_id: int, session_id: str, phone_number: str) -> str:
        """🤖 Get agent memory context for personalizing WhatsApp responses"""
        if not self.agent_memory:
            return ""

        try:
            # Get authenticated user info for proper user_id
            is_authenticated = self._is_user_authenticated(customer_id)
            user_info = self._get_authenticated_user_info(customer_id) if is_authenticated else {}
            user_id = user_info.get('email', phone_number) if is_authenticated else f'whatsapp_{phone_number}'

            # Get memory context from agent memory system
            agent_memory_context = self.agent_memory.get_memory_context_for_ai(
                query=message_content,
                user_id=user_id,
                thread_id=session_id,
                max_memories=3
            )

            if agent_memory_context:
                logger.info(f"🤖 Retrieved agent memory context for WhatsApp user {user_id}")
                return agent_memory_context

            return ""

        except Exception as e:
            logger.warning(f"⚠️ Failed to get agent memory context for WhatsApp: {e}")
            return ""

    def _store_agent_memory_insights(self, message_content: str, ai_response: Dict[str, Any],
                                   customer_id: int, session_id: str, phone_number: str):
        """🤖 Store insights from WhatsApp conversation in agent memory"""
        if not self.agent_memory:
            return

        try:
            # Get authenticated user info for proper user_id
            is_authenticated = self._is_user_authenticated(customer_id)
            user_info = self._get_authenticated_user_info(customer_id) if is_authenticated else {}
            user_id = user_info.get('email', phone_number) if is_authenticated else f'whatsapp_{phone_number}'

            # Extract insights to store based on message patterns and AI response
            insights_to_store = []
            message_lower = message_content.lower()

            # Store meaningful user preferences only (not simple requests)
            strong_preference_patterns = [
                'i prefer', 'my favorite', 'i always', 'i usually', 'i love', 'i hate'
            ]
            if (any(pattern in message_lower for pattern in strong_preference_patterns) and
                len(message_content.strip()) > 10):  # Avoid storing very short messages
                insights_to_store.append({
                    'content': f"WhatsApp user preference: {message_content}",
                    'type': 'episodic',
                    'confidence': 0.9
                })

            # Store purchase interests (balanced approach)
            purchase_intent_patterns = [
                'want to buy', 'planning to order', 'interested in buying', 'need to purchase',
                'i need', 'i want', 'looking for', 'searching for'
            ]
            # Only store substantial queries to avoid noise
            if (any(pattern in message_lower for pattern in purchase_intent_patterns) and
                len(message_content.strip()) > 8):  # At least 8 characters
                insights_to_store.append({
                    'content': f"WhatsApp product interest: {message_content}",
                    'type': 'episodic',
                    'confidence': 0.7
                })

            # Store delivery preferences
            if any(word in message_lower for word in ['delivery', 'shipping', 'address', 'location', 'deliver to']):
                insights_to_store.append({
                    'content': f"WhatsApp delivery inquiry: {message_content}",
                    'type': 'episodic',
                    'confidence': 0.8
                })

            # Store payment preferences
            if any(word in message_lower for word in ['payment', 'pay', 'card', 'transfer', 'raqibtechpay', 'cash']):
                insights_to_store.append({
                    'content': f"WhatsApp payment inquiry: {message_content}",
                    'type': 'episodic',
                    'confidence': 0.8
                })

            # Store successful order completion
            if ai_response.get('action') == 'order_placed':
                insights_to_store.append({
                    'content': f"User successfully placed order via WhatsApp. Products: {ai_response.get('order_summary', {}).get('items', [])}",
                    'type': 'episodic',
                    'confidence': 0.9
                })

            # Store product searches and interests
            if ai_response.get('action') in ['product_found', 'products_displayed']:
                insights_to_store.append({
                    'content': f"User searched for products via WhatsApp: {message_content}",
                    'type': 'episodic',
                    'confidence': 0.7
                })

            # Store any issues or complaints
            if any(word in message_lower for word in ['problem', 'issue', 'complaint', 'not working', 'error', 'wrong']):
                insights_to_store.append({
                    'content': f"WhatsApp user reported issue: {message_content}",
                    'type': 'episodic',
                    'confidence': 0.8
                })

            # Store the insights in agent memory
            from .agent_memory_system import MemoryType
            for insight in insights_to_store:
                memory_type = MemoryType.EPISODIC if insight['type'] == 'episodic' else MemoryType.SEMANTIC

                success = self.agent_memory.store_memory(
                    content=insight['content'],
                    memory_type=memory_type,
                    user_id=user_id,
                    thread_id=session_id,
                    confidence_score=insight['confidence']
                )

                if success:
                    logger.info(f"📝 Stored WhatsApp agent memory for {user_id}: {insight['content'][:50]}...")

            # Schedule memory consolidation if we stored insights
            if insights_to_store:
                self.agent_memory.schedule_memory_consolidation(user_id)

        except Exception as e:
            logger.error(f"❌ Error storing WhatsApp agent memory insights: {e}")

    def _is_message_processed(self, message_id: str) -> bool:
        """Check if message has already been processed (deduplication)"""
        # Clean up expired entries first
        current_time = time.time()
        expired_ids = [mid for mid, expiry in self.processed_messages_ttl.items() if expiry < current_time]
        for mid in expired_ids:
            self.processed_messages.discard(mid)
            del self.processed_messages_ttl[mid]

        return message_id in self.processed_messages

    def _mark_message_processed(self, message_id: str):
        """Mark message as processed with TTL (1 hour)"""
        self.processed_messages.add(message_id)
        self.processed_messages_ttl[message_id] = time.time() + 3600  # 1 hour TTL

# Singleton instance
whatsapp_handler = None

def get_whatsapp_handler() -> WhatsAppBusinessHandler:
    """Get singleton WhatsApp handler instance"""
    global whatsapp_handler
    if whatsapp_handler is None:
        whatsapp_handler = WhatsAppBusinessHandler()
    return whatsapp_handler
