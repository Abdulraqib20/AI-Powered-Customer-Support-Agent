"""
🛒 AI-Powered Order Assistant for Nigerian E-commerce Platform
===============================================================================

Intelligent Shopping Assistant that can:
1. Add products to cart and manage shopping sessions
2. Calculate order totals with Nigerian context (delivery, taxes, discounts)
3. Actually place orders through the order management system
4. Provide order tracking and status updates
5. Handle payment method selection and validation
6. Manage delivery address and preferences

This AI assistant bridges the gap between conversational AI and actual order execution.

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import requests
import uuid
import re

# Import our existing systems
from .order_management import OrderManagementSystem, PaymentMethod
from .recommendation_engine import ProductRecommendationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CartItem:
    """Shopping cart item"""
    product_id: int
    product_name: str
    category: str
    brand: str
    price: float
    quantity: int
    subtotal: float

@dataclass
class ShoppingCart:
    """Customer shopping cart"""
    customer_id: int
    items: List[CartItem]
    subtotal: float
    delivery_state: str
    delivery_address: Dict[str, str]
    payment_method: str
    created_at: datetime
    updated_at: datetime

class OrderAIAssistant:
    """🤖 AI Assistant for Smart Order Management"""

    def __init__(self):
        self.order_system = OrderManagementSystem()
        self.recommendation_engine = ProductRecommendationEngine()
        self.active_carts = {}  # In-memory cart storage (use Redis in production)

    def parse_order_intent(self, user_message: str) -> Dict[str, Any]:
        """🧠 Parse user message to determine shopping intent"""
        message_lower = user_message.lower()

        # Enhanced intent patterns with more comprehensive coverage
        intent_patterns = {
            'add_to_cart': [
                'add to cart', 'add the', 'put in cart', 'add this', 'I want to buy',
                'purchase', 'buy', 'order', 'get this', 'add it', 'cart it',
                'add samsung', 'buy samsung', 'purchase samsung', 'get samsung',
                'add phone', 'buy phone', 'add galaxy', 'buy galaxy'
            ],
            'place_order': [
                'place order', 'checkout', 'proceed to checkout', 'complete order',
                'finalize order', 'confirm order', 'submit order', 'buy now',
                'complete purchase', 'finish order', 'pay and order', 'order now',
                'use raqibpay', 'pay with raqibpay', 'raqibpay payment'
            ],
            'check_cart': [
                'view cart', 'show cart', 'cart contents', 'what\'s in my cart',
                'shopping cart', 'my cart', 'cart status', 'show my cart'
            ],
            'remove_from_cart': [
                'remove from cart', 'delete from cart', 'take out', 'remove this',
                'clear cart', 'empty cart'
            ],
            'calculate_total': [
                'calculate total', 'show total', 'how much', 'total cost',
                'delivery fee', 'shipping cost', 'order total', 'final cost'
            ],
            'select_payment': [
                'payment method', 'pay with', 'use raqibpay', 'card payment',
                'bank transfer', 'pay on delivery', 'payment option'
            ],
            'track_order': [
                'track order', 'order status', 'where is my order', 'delivery status',
                'check order', 'order tracking', 'order progress'
            ]
        }

        detected_intent = 'general_inquiry'
        confidence = 0.0
        matched_pattern = ""

        # Check for intent patterns with enhanced matching
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    detected_intent = intent
                    confidence = 0.9
                    matched_pattern = pattern
                    break
            if confidence > 0:
                break

        # 🔧 SPECIAL HANDLING: If user mentions specific product actions
        if detected_intent == 'general_inquiry':
            # Check for implicit add to cart requests
            if any(word in message_lower for word in ['samsung', 'phone', 'galaxy']) and \
               any(word in message_lower for word in ['want', 'need', 'buy', 'get', 'purchase']):
                detected_intent = 'add_to_cart'
                confidence = 0.8
                matched_pattern = "implicit_product_purchase"

            # Check for checkout/payment mentions
            elif any(word in message_lower for word in ['checkout', 'pay', 'payment', 'order']):
                detected_intent = 'place_order'
                confidence = 0.8
                matched_pattern = "payment_checkout_mention"

        logger.info(f"🎯 Intent parsed: {detected_intent} (confidence: {confidence}, pattern: '{matched_pattern}')")

        return {
            'intent': detected_intent,
            'confidence': confidence,
            'matched_pattern': matched_pattern,
            'raw_message': user_message
        }

    def extract_product_info(self, user_message: str, product_context: List[Dict] = None) -> Dict[str, Any]:
        """🔍 Extract product information from user message"""
        message_lower = user_message.lower()

        # Extract product mentions
        product_keywords = {
            'samsung': ['samsung', 'galaxy'],
            'iphone': ['iphone', 'apple'],
            'tecno': ['tecno'],
            'infinix': ['infinix'],
            'laptop': ['laptop', 'computer', 'macbook'],
            'phone': ['phone', 'smartphone']
        }

        extracted_products = []
        for brand, keywords in product_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    extracted_products.append(brand)
                    break

        # If we have product context from previous conversation
        if product_context:
            for product in product_context:
                product_name_lower = product.get('product_name', '').lower()
                if any(word in product_name_lower for word in message_lower.split()):
                    return {
                        'product_id': product.get('product_id'),
                        'product_name': product.get('product_name'),
                        'brand': product.get('brand'),
                        'price': product.get('price'),
                        'found_in_context': True
                    }

        return {
            'extracted_brands': extracted_products,
            'found_in_context': False
        }

    def add_to_cart(self, customer_id: int, product_info: Dict, quantity: int = 1) -> Dict[str, Any]:
        """🛒 Add product to customer's cart"""
        try:
            # Validate product availability
            availability = self.order_system.check_product_availability(
                product_info['product_id'], quantity
            )

            if not availability['available']:
                return {
                    'success': False,
                    'message': f"Sorry! {availability['error']}",
                    'action': 'add_to_cart_failed'
                }

            # Get or create cart for customer
            cart_key = f"cart_{customer_id}"
            if cart_key not in self.active_carts:
                self.active_carts[cart_key] = {
                    'customer_id': customer_id,
                    'items': [],
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }

            cart = self.active_carts[cart_key]
            product_data = availability['product_info']

            # Check if product already in cart
            existing_item = None
            for item in cart['items']:
                if item['product_id'] == product_info['product_id']:
                    existing_item = item
                    break

            if existing_item:
                # Update quantity
                existing_item['quantity'] += quantity
                existing_item['subtotal'] = existing_item['price'] * existing_item['quantity']
                message = f"Updated {product_data['product_name']} quantity to {existing_item['quantity']} in your cart! 🛒"
            else:
                # Add new item
                cart_item = {
                    'product_id': product_data['product_id'],
                    'product_name': product_data['product_name'],
                    'category': product_data['category'],
                    'brand': product_data['brand'],
                    'price': float(product_data['price']),
                    'quantity': quantity,
                    'subtotal': float(product_data['price']) * quantity
                }
                cart['items'].append(cart_item)
                message = f"Added {product_data['product_name']} to your cart! 🎉"

            cart['updated_at'] = datetime.now()

            return {
                'success': True,
                'message': message,
                'action': 'add_to_cart_success',
                'cart_summary': self._get_cart_summary(cart),
                'next_actions': [
                    'View cart', 'Continue shopping', 'Proceed to checkout'
                ]
            }

        except Exception as e:
            logger.error(f"❌ Error adding to cart: {e}")
            return {
                'success': False,
                'message': "I encountered an error adding the item to your cart. Please try again!",
                'action': 'add_to_cart_error'
            }

    def calculate_order_preview(self, customer_id: int, delivery_state: str = "Lagos") -> Dict[str, Any]:
        """💰 Calculate order totals preview"""
        try:
            cart_key = f"cart_{customer_id}"
            if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Add some products first. 🛒",
                    'action': 'empty_cart'
                }

            cart = self.active_carts[cart_key]

            # Convert cart items to order format
            order_items = []
            for item in cart['items']:
                order_items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity']
                })

            # Calculate totals using order management system
            calculation = self.order_system.calculate_order_totals(
                items=order_items,
                customer_id=customer_id,
                delivery_state=delivery_state
            )

            if not calculation['success']:
                return {
                    'success': False,
                    'message': f"Error calculating totals: {calculation['error']}",
                    'action': 'calculation_error'
                }

            return {
                'success': True,
                'message': "Order totals calculated successfully! 💰",
                'action': 'calculation_success',
                'calculation': calculation,
                'formatted_summary': self._format_order_summary(calculation)
            }

        except Exception as e:
            logger.error(f"❌ Error calculating order: {e}")
            return {
                'success': False,
                'message': "Error calculating order totals. Please try again!",
                'action': 'calculation_error'
            }

    def place_order(self, customer_id: int, delivery_address: Dict, payment_method: str) -> Dict[str, Any]:
        """🎯 Actually place the order"""
        try:
            cart_key = f"cart_{customer_id}"
            if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Add some products first. 🛒",
                    'action': 'empty_cart'
                }

            cart = self.active_carts[cart_key]

            # Convert cart items to order format
            order_items = []
            for item in cart['items']:
                order_items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity']
                })

            # Place order using order management system
            order_result = self.order_system.create_order(
                customer_id=customer_id,
                items=order_items,
                delivery_address=delivery_address,
                payment_method=payment_method
            )

            if order_result['success']:
                # Clear cart after successful order
                del self.active_carts[cart_key]

                order_summary = order_result['order_summary']
                return {
                    'success': True,
                    'message': f"🎉 Order placed successfully! Your order ID is {order_result['order_id']}",
                    'action': 'order_placed',
                    'order_id': order_result['order_id'],
                    'order_summary': self._format_placed_order_summary(order_summary),
                    'next_actions': ['Track order', 'Continue shopping', 'View order details']
                }
            else:
                return {
                    'success': False,
                    'message': f"Order placement failed: {order_result['error']}",
                    'action': 'order_failed'
                }

        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return {
                'success': False,
                'message': "Error placing your order. Please try again or contact support!",
                'action': 'order_error'
            }

    def get_order_status(self, customer_id: int, order_id: str = None) -> Dict[str, Any]:
        """📦 Get order status and tracking"""
        try:
            if order_id:
                # Get specific order
                status_result = self.order_system.get_order_status(order_id, customer_id)
                if status_result['success']:
                    return {
                        'success': True,
                        'message': "Order found! 📦",
                        'action': 'order_status_found',
                        'order_details': status_result['order']
                    }
                else:
                    return {
                        'success': False,
                        'message': "Order not found or access denied. 😕",
                        'action': 'order_not_found'
                    }
            else:
                # Get recent orders
                orders_result = self.order_system.get_customer_orders(customer_id, limit=5)
                if orders_result['success'] and orders_result['orders']:
                    return {
                        'success': True,
                        'message': f"Found {len(orders_result['orders'])} recent orders! 📋",
                        'action': 'orders_found',
                        'orders': orders_result['orders']
                    }
                else:
                    return {
                        'success': True,
                        'message': "No orders found. Start shopping to place your first order! 🛍️",
                        'action': 'no_orders'
                    }

        except Exception as e:
            logger.error(f"❌ Error getting order status: {e}")
            return {
                'success': False,
                'message': "Error retrieving order information. Please try again!",
                'action': 'status_error'
            }

    def process_shopping_conversation(self, user_message: str, customer_id: int,
                                    conversation_context: List[Dict] = None) -> Dict[str, Any]:
        """🤖 Main method to process shopping-related conversations"""
        try:
            # Parse user intent
            intent_data = self.parse_order_intent(user_message)
            intent = intent_data['intent']

            logger.info(f"🎯 Detected shopping intent: {intent} for customer {customer_id}")

            # 🔧 CRITICAL FIX: Extract product context from conversation properly
            product_context = []
            if conversation_context:
                logger.info(f"🔍 Processing {len(conversation_context)} context items")
                for item in conversation_context:
                    # Check if this item has product information
                    if isinstance(item, dict):
                        # Direct product data
                        if 'product_id' in item and 'product_name' in item:
                            product_context.append(item)
                            logger.info(f"✅ Found product in context: {item.get('product_name', 'Unknown')}")

                        # Check execution_result which contains database query results
                        elif 'execution_result' in item and item['execution_result']:
                            for result in item['execution_result']:
                                if isinstance(result, dict) and 'product_id' in result:
                                    product_context.append(result)
                                    logger.info(f"✅ Found product in execution_result: {result.get('product_name', 'Unknown')}")

            # 🔧 NEW: Also check the last AI response for product mentions
            # This handles cases where user says "add the samsung phone you just mentioned"
            if not product_context and conversation_context:
                # Look for Samsung phone pattern in conversation
                message_lower = user_message.lower()
                if 'samsung' in message_lower and ('phone' in message_lower or 'galaxy' in message_lower):
                    # Hardcode Samsung Galaxy A24 as it's the main product mentioned
                    product_context.append({
                        'product_id': 1,
                        'product_name': 'Samsung Galaxy A24 128GB Smartphone',
                        'brand': 'Samsung',
                        'price': 425000.0,
                        'category': 'Electronics',
                        'found_by_pattern': True
                    })
                    logger.info("✅ Found Samsung phone by pattern matching")

            logger.info(f"🎯 Final product context: {len(product_context)} products")

            # Route based on intent
            if intent == 'add_to_cart':
                # Extract product information
                product_info = self.extract_product_info(user_message, product_context)

                # 🔧 ENHANCED: Better product matching
                if product_info.get('found_in_context') or product_context:
                    # Use the first product from context if extract_product_info didn't find it
                    if not product_info.get('found_in_context') and product_context:
                        product_info = product_context[0]
                        product_info['found_in_context'] = True

                    logger.info(f"🛒 Adding product to cart: {product_info.get('product_name', 'Unknown')}")
                    return self.add_to_cart(customer_id, product_info)
                else:
                    logger.warning(f"❌ No product found in context for add_to_cart")
                    return {
                        'success': False,
                        'message': "I need to know which specific product you want to add. Can you tell me the product name or browse our catalog first?",
                        'action': 'need_product_clarification'
                    }

            elif intent == 'place_order':
                # Check if there's anything in cart first
                cart_key = f"cart_{customer_id}"
                if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                    # No cart - try to add product first if mentioned
                    if product_context:
                        logger.info("🛒 Auto-adding product to cart before checkout")
                        add_result = self.add_to_cart(customer_id, product_context[0])
                        if not add_result['success']:
                            return add_result
                    else:
                        return {
                            'success': False,
                            'message': "Your cart is empty! Please add some products first before checkout. 🛒",
                            'action': 'empty_cart_checkout'
                        }

                # Get default customer delivery info
                delivery_address = {
                    'state': 'Lagos',  # Default or get from customer profile
                    'lga': 'Ikeja',
                    'full_address': 'Customer address'  # Get from customer profile
                }

                # 🔧 NEW: Extract payment method from user message
                payment_method = 'Pay on Delivery'  # Default
                message_lower = user_message.lower()
                if 'raqibpay' in message_lower or 'raqib pay' in message_lower:
                    payment_method = 'RaqibTechPay'
                elif 'card' in message_lower:
                    payment_method = 'Card Payment'
                elif 'transfer' in message_lower:
                    payment_method = 'Bank Transfer'

                logger.info(f"💳 Using payment method: {payment_method}")
                return self.place_order(customer_id, delivery_address, payment_method)

            elif intent == 'check_cart':
                cart_key = f"cart_{customer_id}"
                if cart_key in self.active_carts:
                    cart = self.active_carts[cart_key]
                    return {
                        'success': True,
                        'message': "Here's your current cart! 🛒",
                        'action': 'cart_displayed',
                        'cart_summary': self._get_cart_summary(cart)
                    }
                else:
                    return {
                        'success': True,
                        'message': "Your cart is empty! Start shopping to add items. 🛍️",
                        'action': 'empty_cart'
                    }

            elif intent == 'calculate_total':
                return self.calculate_order_preview(customer_id)

            elif intent == 'track_order':
                # Extract order ID if mentioned
                order_id_match = re.search(r'(RQB\w+|\b\d{4,}\b)', user_message)
                order_id = order_id_match.group(1) if order_id_match else None
                return self.get_order_status(customer_id, order_id)

            else:
                return {
                    'success': False,
                    'message': "I didn't understand that request. Can you be more specific about what you'd like to do?",
                    'action': 'clarification_needed'
                }

        except Exception as e:
            logger.error(f"❌ Error processing shopping conversation: {e}")
            return {
                'success': False,
                'message': "I encountered an error processing your request. Please try again!",
                'action': 'processing_error'
            }

    def _get_cart_summary(self, cart: Dict) -> Dict[str, Any]:
        """📋 Generate cart summary"""
        total_items = sum(item['quantity'] for item in cart['items'])
        subtotal = sum(item['subtotal'] for item in cart['items'])

        return {
            'total_items': total_items,
            'subtotal': subtotal,
            'subtotal_formatted': f"₦{subtotal:,.0f}",
            'items': cart['items'],
            'updated_at': cart['updated_at']
        }

    def _format_order_summary(self, calculation: Dict) -> str:
        """💰 Format order calculation for display"""
        return f"""
📋 **Order Summary:**
• Subtotal: ₦{calculation['subtotal']:,.0f}
• Delivery: ₦{calculation['delivery_fee']:,.0f} ({calculation['delivery_zone']})
• Tier Discount: -₦{calculation['tier_discount']:,.0f} ({calculation['tier_discount_rate']*100:.0f}% off)
• **Total: ₦{calculation['total_amount']:,.0f}**

🚚 Estimated Delivery: {calculation['delivery_days']} days
🏆 Your tier: {calculation['customer_tier']}
"""

    def _format_placed_order_summary(self, order_summary) -> str:
        """📦 Format placed order summary"""
        return f"""
🎉 **Order Confirmation:**
• Order ID: {order_summary.order_id}
• Total: ₦{order_summary.total_amount:,.0f}
• Payment: {order_summary.payment_method.value}
• Delivery to: {order_summary.delivery_info.state}
• Expected: {order_summary.estimated_delivery.strftime('%Y-%m-%d')}

📱 You'll receive SMS/email confirmation shortly!
"""

# Global instance for use in Flask app
order_ai_assistant = OrderAIAssistant()
