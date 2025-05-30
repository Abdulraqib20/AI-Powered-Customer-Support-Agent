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
try:
    from .order_management import OrderManagementSystem, PaymentMethod
    from .recommendation_engine import ProductRecommendationEngine
except ImportError:
    # Fallback for when imported directly
    try:
        from order_management import OrderManagementSystem, PaymentMethod
        from recommendation_engine import ProductRecommendationEngine
    except ImportError:
        # Create mock classes if imports fail
        class OrderManagementSystem:
            def check_product_availability(self, product_id, quantity):
                return {'available': True, 'product_info': {'product_name': 'Mock Product'}}
            def create_order(self, *args, **kwargs):
                return {'success': True, 'order_id': 'MOCK123', 'database_order_id': 123}

        class ProductRecommendationEngine:
            def __init__(self):
                pass

        class PaymentMethod:
            PAY_ON_DELIVERY = "Pay on Delivery"
            RAQIB_TECH_PAY = "RaqibTechPay"

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
                'purchase', 'buy', 'get this', 'add it', 'cart it',
                'add samsung', 'buy samsung', 'purchase samsung', 'get samsung',
                'add phone', 'buy phone', 'add galaxy', 'buy galaxy'
            ],
            'place_order': [
                'place order', 'checkout', 'proceed to checkout', 'complete order',
                'finalize order', 'confirm order', 'submit order', 'buy now',
                'complete purchase', 'finish order', 'pay and order', 'order now',
                'use raqibpay', 'pay with raqibpay', 'raqibpay payment',
                'confirm', 'place', 'order', 'proceed', 'complete'
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

            # 🆕 ENHANCED LOGGING FOR ORDER PLACEMENT
            logger.info(f"🎯 PLACING ORDER for customer {customer_id}")
            logger.info(f"📦 Cart items: {len(self.active_carts[cart_key]['items'])}")
            logger.info(f"🚚 Delivery: {delivery_address}")
            logger.info(f"💳 Payment: {payment_method}")

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

            # 🆕 ENHANCED LOGGING FOR ORDER PLACEMENT
            logger.info(f"🎯 PLACING ORDER for customer {customer_id}")
            logger.info(f"📦 Cart items: {len(self.active_carts[cart_key]['items'])}")
            logger.info(f"🚚 Delivery: {delivery_address}")
            logger.info(f"💳 Payment: {payment_method}")

            cart = self.active_carts[cart_key]

            # Convert cart items to order format
            order_items = []
            for item in cart['items']:
                order_items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity']
                })

            # Place order using order management system
            logger.info("📞 Calling OrderManagementSystem.create_order()...")
            order_result = self.order_system.create_order(
                customer_id=customer_id,
                items=order_items,
                delivery_address=delivery_address,
                payment_method=payment_method
            )

            logger.info(f"📋 Order creation result: {order_result.get('success', False)}")
            if not order_result['success']:
                logger.error(f"❌ Order creation failed: {order_result.get('error', 'Unknown error')}")

            if order_result['success']:
                # Clear cart after successful order
                del self.active_carts[cart_key]

                logger.info(f"✅ ORDER SUCCESSFULLY PLACED! Order ID: {order_result['order_id']}")
                logger.info(f"💾 Database order ID: {order_result.get('database_order_id', 'N/A')}")

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
        """🎯 Process shopping conversation with intelligent context awareness"""
        try:
            # Parse user intent
            intent_data = self.parse_order_intent(user_message)
            intent = intent_data['intent']

            logger.info(f"🛒 Processing shopping intent: {intent} for customer {customer_id}")

            # Handle different shopping intents
            if intent == 'add_to_cart':
                # Extract product information
                product_info = self.extract_product_info(user_message, conversation_context)

                # 🔧 ENHANCED: Better product matching
                if product_info.get('found_in_context') or conversation_context:
                    # Use the first product from context if extract_product_info didn't find it
                    if not product_info.get('found_in_context') and conversation_context:
                        product_info = conversation_context[0]
                        product_info['found_in_context'] = True

                    logger.info(f"🛒 Adding product to cart: {product_info.get('product_name', 'Unknown')}")
                    add_result = self.add_to_cart(customer_id, product_info)

                    # 🆕 PROGRESSIVE CHECKOUT: After adding to cart, start checkout flow
                    if add_result['success']:
                        checkout_result = self.progressive_checkout(customer_id, "start checkout", conversation_context)

                        # Combine the add to cart success with checkout initiation
                        add_result['message'] += f"\n\n{checkout_result['message']}"
                        add_result['checkout_step'] = checkout_result.get('checkout_step', 'delivery_address')

                    return add_result
                else:
                    logger.warning(f"❌ No product found in context for add_to_cart")
                    return {
                        'success': False,
                        'message': "I need to know which specific product you want to add. Can you tell me the product name or browse our catalog first?",
                        'action': 'need_product_clarification'
                    }

            elif intent == 'place_order':
                # Check if we have delivery and payment info
                delivery_address = self.extract_delivery_address(user_message)
                payment_method = self.extract_payment_method(user_message)

                if delivery_address and payment_method:
                    # Direct order placement with all info provided
                    return self.place_order(customer_id, delivery_address, payment_method)
                else:
                    # Start progressive checkout
                    return self.progressive_checkout(customer_id, user_message, conversation_context)

            elif intent == 'check_cart':
                return self.get_cart_contents(customer_id)

            elif intent == 'calculate_total':
                return self.calculate_order_preview(customer_id)

            elif intent == 'track_order':
                return self.get_order_status(customer_id)

            elif any(keyword in user_message.lower() for keyword in ['delivery', 'address', 'payment', 'confirm', 'lugbe', 'abuja', 'lagos', 'raqibpay']):
                # Handle checkout flow responses
                checkout_key = f"checkout_{customer_id}"
                if checkout_key in self.active_carts:
                    return self.progressive_checkout(customer_id, user_message, conversation_context)
                else:
                    # No active checkout, but user mentioned checkout-related terms
                    return {
                        'success': False,
                        'message': "I don't see an active checkout session. Please add items to your cart first! 🛒",
                        'action': 'no_active_checkout'
                    }

            else:
                return {
                    'success': False,
                    'message': "I didn't understand that request. Can you be more specific about what you'd like to do?",
                    'action': 'clarification_needed'
                }

        except Exception as e:
            logger.error(f"❌ Error in shopping conversation: {e}")
            return {
                'success': False,
                'message': "Something went wrong. Please try again!",
                'action': 'error'
            }

    def progressive_checkout(self, customer_id: int, user_message: str,
                           conversation_context: List[Dict] = None) -> Dict[str, Any]:
        """🎯 Progressive checkout - collect details step by step"""
        try:
            cart_key = f"cart_{customer_id}"

            # Check if cart exists
            if cart_key not in self.active_carts or not self.active_carts[cart_key]['items']:
                return {
                    'success': False,
                    'message': "Your cart is empty! Please add some products first. 🛒",
                    'action': 'empty_cart'
                }

            cart = self.active_carts[cart_key]
            message_lower = user_message.lower()

            # Initialize checkout session if not exists
            checkout_key = f"checkout_{customer_id}"
            if checkout_key not in self.active_carts:
                self.active_carts[checkout_key] = {
                    'step': 'delivery_address',
                    'delivery_address': None,
                    'payment_method': None,
                    'confirmed': False
                }

            checkout_session = self.active_carts[checkout_key]

            # Step 1: Collect delivery address
            if checkout_session['step'] == 'delivery_address':
                # Check if delivery address provided in message
                if any(location in message_lower for location in ['lugbe', 'abuja', 'lagos', 'address']):
                    if 'lugbe' in message_lower and 'abuja' in message_lower:
                        checkout_session['delivery_address'] = {
                            'state': 'Abuja',
                            'lga': 'Lugbe',
                            'full_address': 'Anyim Pius Anyim Street, Lugbe, Abuja'
                        }
                    elif 'abuja' in message_lower:
                        checkout_session['delivery_address'] = {
                            'state': 'Abuja',
                            'lga': 'Municipal',
                            'full_address': 'Abuja, Nigeria'
                        }
                    elif 'lagos' in message_lower:
                        checkout_session['delivery_address'] = {
                            'state': 'Lagos',
                            'lga': 'Ikeja',
                            'full_address': 'Lagos, Nigeria'
                        }

                    if checkout_session['delivery_address']:
                        checkout_session['step'] = 'payment_method'
                        logger.info(f"✅ Delivery address collected: {checkout_session['delivery_address']}")

                        return {
                            'success': True,
                            'message': f"✅ Delivery address confirmed: {checkout_session['delivery_address']['full_address']}\n\n💳 Now, please choose your payment method:\n• RaqibTechPay\n• Pay on Delivery\n• Card Payment\n• Bank Transfer\n\nJust say something like 'I want to use RaqibTechPay'",
                            'action': 'delivery_confirmed_payment_needed',
                            'checkout_step': 'payment_method'
                        }

                # Ask for delivery address
                return {
                    'success': True,
                    'message': f"🚚 Great! You have {len(cart['items'])} item(s) in your cart.\n\nTo proceed with checkout, please provide your delivery address.\n\nFor example: 'My delivery address is Lugbe, Abuja' or 'Deliver to Lagos'",
                    'action': 'delivery_address_needed',
                    'checkout_step': 'delivery_address'
                }

            # Step 2: Collect payment method
            elif checkout_session['step'] == 'payment_method':
                payment_method = 'Pay on Delivery'  # Default

                if 'raqibpay' in message_lower or 'raqibtech' in message_lower:
                    payment_method = 'RaqibTechPay'
                elif 'card' in message_lower:
                    payment_method = 'Card'
                elif 'transfer' in message_lower:
                    payment_method = 'Bank Transfer'
                elif 'delivery' in message_lower:
                    payment_method = 'Pay on Delivery'

                checkout_session['payment_method'] = payment_method
                checkout_session['step'] = 'confirmation'
                logger.info(f"✅ Payment method collected: {payment_method}")

                # Calculate totals for confirmation
                cart_summary = self._get_cart_summary(cart)

                return {
                    'success': True,
                    'message': f"✅ Payment method confirmed: {payment_method}\n\n📋 **Order Summary:**\n• Items: {cart_summary['total_items']}\n• Subtotal: {cart_summary['subtotal_formatted']}\n• Delivery: {checkout_session['delivery_address']['full_address']}\n• Payment: {payment_method}\n\n🎯 Ready to place your order? Say 'confirm order' or 'place order' to complete!",
                    'action': 'payment_confirmed_ready_to_order',
                    'checkout_step': 'confirmation'
                }

            # Step 3: Final confirmation and order placement
            elif checkout_session['step'] == 'confirmation':
                if any(keyword in message_lower for keyword in ['confirm', 'place order', 'yes', 'proceed']):
                    # Place the actual order
                    order_result = self.place_order(
                        customer_id,
                        checkout_session['delivery_address'],
                        checkout_session['payment_method']
                    )

                    # Clear checkout session
                    if checkout_key in self.active_carts:
                        del self.active_carts[checkout_key]

                    return order_result
                else:
                    return {
                        'success': True,
                        'message': "Please confirm your order by saying 'confirm order' or 'place order', or you can modify details by saying 'change delivery address' or 'change payment method'.",
                        'action': 'awaiting_confirmation'
                    }

            return {
                'success': False,
                'message': "Something went wrong with checkout. Please try again.",
                'action': 'checkout_error'
            }

        except Exception as e:
            logger.error(f"❌ Error in progressive checkout: {e}")
            return {
                'success': False,
                'message': "Checkout error. Please try again!",
                'action': 'checkout_error'
            }

    def extract_delivery_address(self, user_message: str) -> Dict[str, str]:
        """🚚 Extract delivery address from user message"""
        message_lower = user_message.lower()

        if 'lugbe' in message_lower and 'abuja' in message_lower:
            return {
                'state': 'Abuja',
                'lga': 'Lugbe',
                'full_address': 'Anyim Pius Anyim Street, Lugbe, Abuja'
            }
        elif 'abuja' in message_lower:
            return {
                'state': 'Abuja',
                'lga': 'Municipal',
                'full_address': 'Abuja, Nigeria'
            }
        elif 'lagos' in message_lower:
            return {
                'state': 'Lagos',
                'lga': 'Ikeja',
                'full_address': 'Lagos, Nigeria'
            }

        return None

    def extract_payment_method(self, user_message: str) -> str:
        """💳 Extract payment method from user message"""
        message_lower = user_message.lower()

        if 'raqibpay' in message_lower or 'raqibtech' in message_lower:
            return 'RaqibTechPay'
        elif 'card' in message_lower:
            return 'Card'
        elif 'transfer' in message_lower:
            return 'Bank Transfer'
        elif 'delivery' in message_lower:
            return 'Pay on Delivery'

        return None

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
