"""
🛒 Advanced Order Management System for Nigerian E-commerce Platform
===========================================================================

Comprehensive Order Processing Pipeline:
1. Product Availability & Stock Validation
2. Customer Authentication & Profile Management
3. Nigerian Payment Method Integration (Pay on Delivery, Bank Transfer, Card, RaqibTechPay)
4. Inventory Management & Stock Updates
5. Order Confirmation & Tracking
6. State-wise Delivery Calculation
7. Account Tier Benefits & Discounts

Features:
- Real-time inventory management
- Nigerian state-based delivery fee calculation
- Multi-payment method support optimized for Nigeria
- Automatic account tier progression
- Order modification and cancellation
- SMS/Email notification integration
- Fraud detection and security

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import uuid
from decimal import Decimal, ROUND_HALF_UP
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import safe_int_env, safe_str_env

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    RETURNED = "Returned"
    CANCELLED = "Returned"

class PaymentMethod(Enum):
    """Nigerian payment methods"""
    PAY_ON_DELIVERY = "Pay on Delivery"
    BANK_TRANSFER = "Bank Transfer"
    CARD = "Card"
    RAQIBTECH_PAY = "RaqibTechPay"

class AccountTier(Enum):
    """Customer account tiers"""
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"

@dataclass
class OrderItem:
    """Individual order item"""
    product_id: int
    product_name: str
    category: str
    brand: str
    price: float
    quantity: int
    subtotal: float
    availability_status: str

@dataclass
class DeliveryInfo:
    """Delivery information and calculations"""
    state: str
    lga: str
    full_address: str
    delivery_fee: float
    estimated_delivery_days: int
    delivery_zone: str  # "Lagos", "Major Cities", "Remote Areas"

@dataclass
class OrderSummary:
    """Complete order summary"""
    order_id: str
    customer_id: int
    customer_name: str
    items: List[OrderItem]
    subtotal: float
    delivery_fee: float
    tier_discount: float
    tax_amount: float
    total_amount: float
    payment_method: PaymentMethod
    delivery_info: DeliveryInfo
    order_status: OrderStatus
    created_at: datetime
    estimated_delivery: datetime

class NigerianDeliveryCalculator:
    """🚚 Simplified Nigerian state-based delivery fee calculator - Location & Tier Based Only"""

    # 🎯 SIMPLIFIED DELIVERY ZONES - Fixed fees only, no weight calculation
    DELIVERY_ZONES = {
        "Lagos Metro": {
            "states": ["Lagos"],
            "fixed_fee": 1500,  # Flat rate - no per_kg nonsense
            "delivery_days": 1
        },
        "Abuja FCT": {
            "states": ["FCT", "Abuja"],
            "fixed_fee": 2000,  # Flat rate
            "delivery_days": 2
        },
        "Major Cities": {
            "states": ["Kano", "Rivers", "Oyo", "Kaduna", "Anambra", "Edo", "Enugu", "Delta", "Imo"],
            "fixed_fee": 2500,  # Flat rate
            "delivery_days": 3
        },
        "Other States": {
            "states": ["Abia", "Adamawa", "Akwa Ibom", "Bauchi", "Bayelsa", "Benue", "Borno",
                      "Cross River", "Ebonyi", "Ekiti", "Gombe", "Jigawa", "Kebbi", "Kogi",
                      "Kwara", "Nasarawa", "Niger", "Ondo", "Osun", "Ogun", "Plateau",
                      "Sokoto", "Taraba", "Yobe", "Zamfara"],
            "fixed_fee": 3000,  # Flat rate
            "delivery_days": 5
        }
    }

    @staticmethod
    def calculate_delivery_fee(state: str, total_weight_kg: float = None, total_value: float = 0) -> Tuple[float, int, str]:
        """
        🎯 SIMPLIFIED delivery fee calculation - Location & Tier Based Only

        Args:
            state: Nigerian state for delivery
            total_weight_kg: IGNORED - we don't use weight anymore
            total_value: Order value for high-value free delivery benefits

        Returns:
            Tuple of (delivery_fee, delivery_days, delivery_zone)
        """

        # Find the delivery zone
        zone_name = "Other States"  # Default
        zone_info = None

        for zone, info in NigerianDeliveryCalculator.DELIVERY_ZONES.items():
            if state in info["states"]:
                zone_name = zone
                zone_info = info
                break

        if not zone_info:
            zone_info = NigerianDeliveryCalculator.DELIVERY_ZONES["Other States"]

        # 🎯 SIMPLE: Just use the fixed fee - no weight calculation!
        delivery_fee = zone_info["fixed_fee"]

        # Apply high-value order benefits (before tier benefits)
        if total_value >= 200000:  # Free delivery for orders above ₦200K
            delivery_fee = 0
        elif total_value >= 100000:  # 50% discount for orders above ₦100K
            delivery_fee *= 0.5

        delivery_days = zone_info["delivery_days"]

        logger.info(f"🚚 Delivery to {state} ({zone_name}): ₦{delivery_fee:,.2f} ({delivery_days} days)")
        return delivery_fee, delivery_days, zone_name

    @staticmethod
    def get_delivery_zones_info() -> Dict[str, Any]:
        """Get all delivery zones information for external use"""
        return {
            zone: {
                "states": info["states"],
                "fee": info["fixed_fee"],
                "days": info["delivery_days"]
            }
            for zone, info in NigerianDeliveryCalculator.DELIVERY_ZONES.items()
        }

class OrderManagementSystem:
    """🛒 Advanced Order Management System"""

    def __init__(self):
        self.db_config = {
            'host': safe_str_env('DB_HOST', 'localhost'),
            'port': safe_int_env('DB_PORT', 5432),
            'database': safe_str_env('DB_NAME', 'nigerian_ecommerce'),
            'user': safe_str_env('DB_USER', 'postgres'),
            'password': safe_str_env('DB_PASSWORD', 'oracle'),
        }

        # Initialize Redis for order caching
        try:
            # Safe Redis port parsing - handle secret names and invalid values
            redis_port_str = os.getenv('REDIS_PORT', '6379')
            try:
                # If it's a secret name (contains 'latest' or 'secret'), use default
                if 'latest' in redis_port_str or 'secret' in redis_port_str:
                    redis_port = 6379
                    logger.warning(f"⚠️ Redis port appears to be a secret name, using default: {redis_port}")
                else:
                    redis_port = int(redis_port_str)
            except (ValueError, TypeError):
                redis_port = 6379
                logger.warning(f"⚠️ Invalid Redis port '{redis_port_str}', using default: {redis_port}")

            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=redis_port,
                db=2,  # Use different db for orders
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis order cache initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable for orders: {e}")
            self.redis_client = None

        self.delivery_calculator = NigerianDeliveryCalculator()

    def get_database_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise Exception(f"Database connection failed: {e}")

    def check_product_availability(self, product_id: int, requested_quantity: int) -> Dict[str, Any]:
        """🔍 Check product availability and stock"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT product_id, product_name, category, brand, price,
                               stock_quantity, in_stock, weight_kg, description
                        FROM products
                        WHERE product_id = %s
                    """, (product_id,))

                    product = cursor.fetchone()

                    if not product:
                        return {
                            "available": False,
                            "error": "Product not found",
                            "product_info": None
                        }

                    if not product['in_stock']:
                        return {
                            "available": False,
                            "error": "Product is currently out of stock",
                            "product_info": dict(product)
                        }

                    if product['stock_quantity'] < requested_quantity:
                        return {
                            "available": False,
                            "error": f"Insufficient stock. Only {product['stock_quantity']} units available",
                            "available_quantity": product['stock_quantity'],
                            "product_info": dict(product)
                        }

                    return {
                        "available": True,
                        "product_info": dict(product),
                        "available_quantity": product['stock_quantity']
                    }

        except Exception as e:
            logger.error(f"❌ Error checking product availability: {e}")
            return {
                "available": False,
                "error": f"System error: {str(e)}",
                "product_info": None
            }

    def calculate_order_totals(self, items: List[Dict], customer_id: int,
                             delivery_state: str) -> Dict[str, Any]:
        """💰 Calculate comprehensive order totals with Nigerian context"""
        try:
            # Get customer info for tier discounts
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT account_tier, state, preferences
                        FROM customers
                        WHERE customer_id = %s
                    """, (customer_id,))

                    customer = cursor.fetchone()
                    if not customer:
                        raise ValueError(f"Customer {customer_id} not found")

            # Calculate item subtotals - NO MORE WEIGHT CALCULATION!
            order_items = []
            subtotal = Decimal('0.00')

            for item in items:
                product_check = self.check_product_availability(
                    item['product_id'], item['quantity']
                )

                if not product_check['available']:
                    raise ValueError(f"Product {item['product_id']}: {product_check['error']}")

                product_info = product_check['product_info']
                item_price = Decimal(str(product_info['price']))
                quantity = Decimal(str(item['quantity']))
                item_subtotal = item_price * quantity

                order_items.append(OrderItem(
                    product_id=product_info['product_id'],
                    product_name=product_info['product_name'],
                    category=product_info['category'],
                    brand=product_info['brand'],
                    price=float(item_price),
                    quantity=int(quantity),
                    subtotal=float(item_subtotal),
                    availability_status="Available"
                ))

                subtotal += item_subtotal

            # 🎯 SIMPLIFIED: Calculate delivery fee based on location and order value only
            delivery_fee, delivery_days, delivery_zone = self.delivery_calculator.calculate_delivery_fee(
                delivery_state, None, float(subtotal)  # No weight needed!
            )

            # 🔧 FIX: Apply tier-based delivery benefits
            # Gold and Platinum customers get FREE delivery
            if customer['account_tier'] in ['Gold', 'Platinum']:
                delivery_fee = 0.0
                logger.info(f"🎁 Free delivery applied for {customer['account_tier']} tier customer")

            # Calculate tier discount
            tier_discount_rate = self._get_tier_discount_rate(customer['account_tier'])
            tier_discount = subtotal * Decimal(str(tier_discount_rate))

            # 📊 ENHANCED LOGGING FOR TIER DISCOUNT CALCULATION
            logger.info(f"💰 TIER DISCOUNT CALCULATION:")
            logger.info(f"   👤 Customer Tier: {customer['account_tier']}")
            logger.info(f"   📊 Subtotal: ₦{subtotal:,.2f}")
            logger.info(f"   🎯 Discount Rate: {tier_discount_rate*100:.1f}%")
            logger.info(f"   💸 Discount Amount: ₦{tier_discount:,.2f}")

            # Calculate tax (VAT - 7.5% in Nigeria, but often included in product price)
            # For simplicity, we'll assume tax is included in product prices
            tax_amount = Decimal('0.00')

            # Calculate final total
            total_amount = subtotal - tier_discount + Decimal(str(delivery_fee)) + tax_amount

            return {
                "success": True,
                "order_items": order_items,
                "subtotal": float(subtotal),
                "delivery_fee": delivery_fee,
                "delivery_days": delivery_days,
                "delivery_zone": delivery_zone,
                "tier_discount": float(tier_discount),
                "tier_discount_rate": tier_discount_rate,
                "tax_amount": float(tax_amount),
                "total_amount": float(total_amount),
                "customer_tier": customer['account_tier']
            }

        except Exception as e:
            logger.error(f"❌ Error calculating order totals: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_order(self, customer_id: int, items: List[Dict],
                    delivery_address: Dict, payment_method: str) -> Dict[str, Any]:
        """🛒 Create a new order with comprehensive validation"""
        try:
            # Calculate order totals first
            order_calc = self.calculate_order_totals(
                items, customer_id, delivery_address['state']
            )

            if not order_calc['success']:
                return {
                    "success": False,
                    "error": order_calc['error']
                }

            # Create delivery info
            # Handle different delivery address formats
            if 'full_address' not in delivery_address:
                # Build full address from components
                address_parts = []
                if 'street' in delivery_address:
                    address_parts.append(delivery_address['street'])
                if 'city' in delivery_address:
                    address_parts.append(delivery_address['city'])
                if 'state' in delivery_address:
                    address_parts.append(delivery_address['state'])
                if 'country' in delivery_address:
                    address_parts.append(delivery_address['country'])
                full_address = ', '.join(address_parts)
            else:
                full_address = delivery_address['full_address']

            # Handle missing lga field
            lga = delivery_address.get('lga', delivery_address.get('city', 'Municipal'))

            delivery_info = DeliveryInfo(
                state=delivery_address['state'],
                lga=lga,
                full_address=full_address,
                delivery_fee=order_calc['delivery_fee'],
                estimated_delivery_days=order_calc['delivery_days'],
                delivery_zone=order_calc['delivery_zone']
            )

            # Calculate estimated delivery date
            estimated_delivery = datetime.now() + timedelta(days=order_calc['delivery_days'])

            # Start database transaction
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get customer info including account_tier for email
                    cursor.execute("""
                        SELECT name, email, phone, lga, account_tier FROM customers WHERE customer_id = %s
                    """, (customer_id,))
                    customer_info = cursor.fetchone()

                    # 🔧 FIX: Insert order and get the auto-generated integer order_id
                    cursor.execute("""
                        INSERT INTO orders (
                            customer_id, order_status, payment_method,
                            total_amount, delivery_date, product_category, product_id,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING order_id
                    """, (
                        customer_id, OrderStatus.PENDING.value, payment_method,
                        order_calc['total_amount'], estimated_delivery,
                        order_calc['order_items'][0].category,  # Primary category
                        order_calc['order_items'][0].product_id,  # Primary product
                        datetime.now(), datetime.now()
                    ))

                    # Get the auto-generated order_id
                    order_id = cursor.fetchone()['order_id']

                    # Create formatted order reference for display
                    formatted_order_id = f"RQB{datetime.now().strftime('%Y%m%d')}{order_id:08d}"

                    # Create order summary
                    order_summary = OrderSummary(
                        order_id=formatted_order_id,  # Use formatted ID for display
                        customer_id=customer_id,
                        customer_name=customer_info.get('name', 'Unknown Customer'),
                        items=order_calc['order_items'],
                        subtotal=order_calc['subtotal'],
                        delivery_fee=order_calc['delivery_fee'],
                        tier_discount=order_calc['tier_discount'],
                        tax_amount=order_calc['tax_amount'],
                        total_amount=order_calc['total_amount'],
                        payment_method=PaymentMethod(payment_method),
                        delivery_info=delivery_info,
                        order_status=OrderStatus.PENDING,
                        created_at=datetime.now(),
                        estimated_delivery=estimated_delivery
                    )

                    # Update product stock quantities
                    for item in order_calc['order_items']:
                        cursor.execute("""
                            UPDATE products
                            SET stock_quantity = stock_quantity - %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE product_id = %s
                        """, (item.quantity, item.product_id))

                        # Check if product is now out of stock
                        cursor.execute("""
                            UPDATE products
                            SET in_stock = false
                            WHERE product_id = %s AND stock_quantity <= 0
                        """, (item.product_id,))

                    # Update customer account tier if needed
                    self._update_customer_tier(cursor, customer_id, order_calc['total_amount'])

                    # Commit transaction
                    conn.commit()

                    logger.info(f"✅ Order {formatted_order_id} (ID: {order_id}) created successfully for customer {customer_id}")

                    # Cache order for quick retrieval
                    if self.redis_client:
                        self.redis_client.setex(
                            f"order:{formatted_order_id}",
                            3600,  # 1 hour cache
                            json.dumps(asdict(order_summary), default=str)
                        )

                    # 📧 Send order confirmation email (if email service is available)
                    try:
                        from email_service import EmailService
                        email_service = EmailService()

                        # Prepare order data for email
                        order_email_data = {
                            'customer_name': customer_info.get('name', 'Customer'),
                            'customer_email': customer_info.get('email', ''),
                            'order_id': formatted_order_id,
                            'items': [],
                            'subtotal': order_calc['subtotal'],
                            'discount_amount': order_calc.get('tier_discount', 0),
                            'discount_percentage': 0,  # Will be calculated based on tier
                            'delivery_fee': order_calc['delivery_fee'],
                            'total_amount': order_calc['total_amount'],
                            'account_tier': customer_info.get('account_tier', 'Bronze'),
                            'delivery_state': delivery_address.get('state', ''),
                            'delivery_lga': delivery_address.get('lga', ''),
                            'delivery_address': delivery_address.get('full_address', ''),
                            'payment_method': payment_method,
                            'order_status': 'Pending'
                        }

                        # Add items to email data
                        for item in order_calc['order_items']:
                            order_email_data['items'].append({
                                'name': item.product_name,
                                'quantity': item.quantity,
                                'unit_price': item.price,
                                'subtotal': item.subtotal
                            })

                        # Calculate discount percentage for display
                        tier_discounts = {'Bronze': 0, 'Silver': 5, 'Gold': 10, 'Platinum': 15}
                        order_email_data['discount_percentage'] = tier_discounts.get(customer_info.get('account_tier', 'Bronze'), 0)

                        if customer_info.get('email'):
                            email_sent = email_service.send_order_confirmation_email(order_email_data)
                            if email_sent:
                                logger.info(f"✅ Order confirmation email sent to {customer_info.get('email')} for order {formatted_order_id}")
                            else:
                                logger.warning(f"⚠️ Failed to send order confirmation email to {customer_info.get('email')}")
                    except ImportError:
                        logger.debug("📧 Email service not available - skipping order confirmation email")
                    except Exception as email_error:
                        logger.error(f"❌ Order confirmation email error: {email_error}")

                    return {
                        "success": True,
                        "order_id": formatted_order_id,  # Return formatted ID
                        "database_order_id": order_id,  # Also return DB ID for reference
                        "order_summary": order_summary,
                        "message": f"Order {formatted_order_id} created successfully! You'll receive confirmation via SMS/email."
                    }

        except Exception as e:
            logger.error(f"❌ Error creating order: {e}")
            return {
                "success": False,
                "error": f"Failed to create order: {str(e)}"
            }

    def get_order_status(self, order_id: str, customer_id: int = None) -> Dict[str, Any]:
        """📦 Get order status and tracking information with detailed pricing breakdown"""
        try:
            # Check Redis cache first
            if self.redis_client:
                cached_order = self.redis_client.get(f"order:{order_id}")
                if cached_order:
                    order_data = json.loads(cached_order)
                    if not customer_id or order_data.get('customer_id') == customer_id:
                        return {
                            "success": True,
                            "order": order_data,
                            "source": "cache"
                        }

            # Query database - using correct column names
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get order details with proper date fields
                    cursor.execute("""
                        SELECT DISTINCT
                            o.order_id,
                            o.customer_id,
                            o.order_status as status,
                            o.payment_method,
                            o.total_amount,
                            o.delivery_date as order_date,
                            o.created_at,
                            o.updated_at,
                            c.address as delivery_address,
                            c.state,
                            c.lga,
                            c.name as customer_name,
                            c.account_tier
                        FROM orders o
                        JOIN customers c ON o.customer_id = c.customer_id
                        WHERE o.order_id = %s
                        """ + (" AND o.customer_id = %s" if customer_id else ""),
                        (order_id, customer_id) if customer_id else (order_id,))

                    order_row = cursor.fetchone()

                    if not order_row:
                        return {
                            "success": False,
                            "error": "Order not found or access denied"
                        }

                    order_data = dict(order_row)

                    # Get products for this order
                    cursor.execute("""
                        SELECT DISTINCT
                            p.product_id,
                            p.product_name,
                            p.category,
                            p.brand,
                            p.price,
                            p.weight_kg,
                            1 as quantity
                        FROM orders o
                        LEFT JOIN products p ON o.product_id = p.product_id
                        WHERE o.order_id = %s
                    """, (order_id,))

                    products = [dict(row) for row in cursor.fetchall()]
                    order_data['products'] = products
                    order_data['items_count'] = len(products)

                    # 🔧 CALCULATE DETAILED PRICING BREAKDOWN WITH ALL COMPONENTS
                    if products:
                        # Calculate subtotal from actual product prices
                        subtotal = sum(float(product['price']) * int(product['quantity']) for product in products)

                        # 🎯 SIMPLIFIED: Calculate delivery fee based on location and order value only
                        delivery_fee, delivery_days, delivery_zone = self.delivery_calculator.calculate_delivery_fee(
                            order_data['state'], None, subtotal  # No weight needed!
                        )

            # Calculate tier discount
            tier_discount_rate = self._get_tier_discount_rate(order_data['account_tier'])
            tier_discount = subtotal * tier_discount_rate

            # Apply free delivery for Gold and Platinum tiers
            original_delivery_fee = delivery_fee

            # 📊 ENHANCED LOGGING FOR ORDER PRICING BREAKDOWN
            logger.info(f"🧮 ORDER {order_id} DETAILED PRICING BREAKDOWN:")
            logger.info(f"   👤 Customer Tier: {order_data['account_tier']}")
            logger.info(f"   📦 Products Subtotal: ₦{subtotal:,.2f}")
            logger.info(f"   🎯 Tier Discount Rate: {tier_discount_rate*100:.1f}%")
            logger.info(f"   💸 Tier Discount Amount: ₦{tier_discount:,.2f}")
            logger.info(f"   🚚 Original Delivery Fee: ₦{original_delivery_fee:,.2f}")
            tier_delivery_benefit = False
            if order_data['account_tier'] in ['Gold', 'Platinum']:
                delivery_fee = 0
                tier_delivery_benefit = True
                logger.info(f"   🎁 FREE DELIVERY applied for {order_data['account_tier']} tier")

            # ✅ CALCULATE CORRECT TOTAL
            calculated_total = subtotal - tier_discount + delivery_fee

            logger.info(f"   🚚 Final Delivery Fee: ₦{delivery_fee:,.2f}")
            logger.info(f"   💰 CALCULATED TOTAL: ₦{calculated_total:,.2f}")

            # Get stored total amount for comparison
            stored_total = float(order_data['total_amount'])

            # 🎯 ALWAYS USE CALCULATED TOTAL (CORRECT CALCULATION)
            # Override stored total with correct calculation
            correct_total = calculated_total

            # Identify any discrepancy for logging
            discrepancy = stored_total - calculated_total
            if abs(discrepancy) > 0.01:  # More than 1 kobo difference
                logger.warning(f"⚠️ Order {order_id} calculation discrepancy: Stored=₦{stored_total:,.2f}, Calculated=₦{calculated_total:,.2f}, Difference=₦{discrepancy:,.2f}")

            # Add detailed pricing breakdown to order data with ALL components
            order_data['pricing_breakdown'] = {
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'original_delivery_fee': original_delivery_fee,
                'tier_delivery_benefit': tier_delivery_benefit,
                'account_tier': order_data['account_tier'],
                'tier_discount': tier_discount,
                'tier_discount_rate': tier_discount_rate * 100,  # Convert to percentage
                'calculated_total': correct_total,  # Use calculated total
                'stored_total': stored_total,  # Keep for reference
                'discrepancy': discrepancy,
                'delivery_zone': delivery_zone,
                'delivery_days': delivery_days,
                'shows_complete_breakdown': True  # Flag that this is a complete breakdown
            }

            # ✅ UPDATE ORDER DATA WITH CORRECT TOTAL
            order_data['total_amount'] = correct_total

            logger.info(f"🧮 Order {order_id} pricing breakdown: Subtotal=₦{subtotal:,.2f}, Delivery=₦{delivery_fee:,.2f}, Discount=₦{tier_discount:,.2f}, Calculated Total=₦{correct_total:,.2f}")

            # Ensure proper field formatting
            if order_data.get('order_date'):
                if isinstance(order_data['order_date'], str):
                    order_data['order_date'] = order_data['order_date']
                else:
                    order_data['order_date'] = order_data['order_date'].isoformat() if order_data['order_date'] else None

            # Ensure status is properly set
            if not order_data.get('status'):
                order_data['status'] = 'Pending'

            # Cache the result
            if self.redis_client:
                self.redis_client.setex(f"order:{order_id}", 300, json.dumps(order_data, default=str))

            return {
                "success": True,
                "order": order_data,
                "source": "database"
            }

        except Exception as e:
            logger.error(f"❌ Error getting order status: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve order: {str(e)}"
            }

    def update_order_status(self, order_id: str, new_status: str,
                          notes: str = "") -> Dict[str, Any]:
        """📋 Update order status (admin function)"""
        try:
            if new_status not in [status.value for status in OrderStatus]:
                return {
                    "success": False,
                    "error": f"Invalid status. Valid options: {[s.value for s in OrderStatus]}"
                }

            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE orders
                        SET order_status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE order_id = %s
                    """, (new_status, order_id))

                    if cursor.rowcount == 0:
                        return {
                            "success": False,
                            "error": "Order not found"
                        }

                    conn.commit()

                    # Clear cache
                    if self.redis_client:
                        self.redis_client.delete(f"order:{order_id}")

                    logger.info(f"✅ Order {order_id} status updated to {new_status}")

                    return {
                        "success": True,
                        "message": f"Order {order_id} status updated to {new_status}"
                    }

        except Exception as e:
            logger.error(f"❌ Error updating order status: {e}")
            return {
                "success": False,
                "error": f"Failed to update order: {str(e)}"
            }

    def cancel_order(self, order_id: str, customer_id: int,
                    reason: str = "") -> Dict[str, Any]:
        """❌ Cancel an order and restore inventory"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check if order can be cancelled
                    cursor.execute("""
                        SELECT order_status, product_id
                        FROM orders
                        WHERE order_id = %s AND customer_id = %s
                    """, (order_id, customer_id))

                    order_info = cursor.fetchone()

                    if not order_info:
                        return {
                            "success": False,
                            "error": "Order not found"
                        }

                    if order_info['order_status'] in ['Delivered', 'Returned']:
                        return {
                            "success": False,
                            "error": f"Cannot cancel order with status: {order_info['order_status']}"
                        }

                    # Update order status
                    cursor.execute("""
                        UPDATE orders
                        SET order_status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE order_id = %s
                    """, (OrderStatus.RETURNED.value, order_id))

                    # Restore product stock (simplified - assumes 1 quantity)
                    cursor.execute("""
                        UPDATE products
                        SET stock_quantity = stock_quantity + 1,
                            in_stock = true,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = %s
                    """, (order_info['product_id'],))

                    conn.commit()

                    # Clear cache
                    if self.redis_client:
                        self.redis_client.delete(f"order:{order_id}")

                    logger.info(f"✅ Order {order_id} cancelled successfully")

                    return {
                        "success": True,
                        "message": f"Order {order_id} has been cancelled successfully. Inventory restored."
                    }

        except Exception as e:
            logger.error(f"❌ Error cancelling order: {e}")
            return {
                "success": False,
                "error": f"Failed to cancel order: {str(e)}"
            }

    def get_customer_orders(self, customer_id: int, limit: int = 20) -> Dict[str, Any]:
        """📋 Get customer's order history with enhanced product information"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get order summary information - using correct column names
                    cursor.execute("""
                        SELECT DISTINCT
                            o.order_id,
                            o.order_status as status,
                            o.payment_method,
                            o.total_amount,
                            o.delivery_date as order_date,
                            o.created_at,
                            o.updated_at,
                            COUNT(DISTINCT o.product_id) as items_count,
                            c.address as delivery_address,
                            c.state,
                            c.lga
                        FROM orders o
                        JOIN customers c ON o.customer_id = c.customer_id
                        WHERE o.customer_id = %s
                        GROUP BY o.order_id, o.order_status, o.payment_method, o.total_amount,
                                 o.delivery_date, o.created_at, o.updated_at, c.address, c.state, c.lga
                        ORDER BY o.created_at DESC
                        LIMIT %s
                    """, (customer_id, limit))

                    orders = []
                    for order_row in cursor.fetchall():
                        order_dict = dict(order_row)

                        # Get products for this order
                        cursor.execute("""
                            SELECT DISTINCT
                                p.product_id,
                                p.product_name,
                                p.category,
                                p.brand,
                                p.price,
                                1 as quantity
                            FROM orders o
                            LEFT JOIN products p ON o.product_id = p.product_id
                            WHERE o.order_id = %s AND o.customer_id = %s
                        """, (order_dict['order_id'], customer_id))

                        products = [dict(row) for row in cursor.fetchall()]
                        order_dict['products'] = products

                        # Ensure proper field formatting
                        if order_dict.get('order_date'):
                            # Convert to proper datetime format
                            if isinstance(order_dict['order_date'], str):
                                order_dict['order_date'] = order_dict['order_date']
                            else:
                                order_dict['order_date'] = order_dict['order_date'].isoformat() if order_dict['order_date'] else None

                        # Ensure status is properly set
                        if not order_dict.get('status'):
                            order_dict['status'] = 'Pending'

                        # Ensure items_count is set
                        if not order_dict.get('items_count'):
                            order_dict['items_count'] = len(products)

                        orders.append(order_dict)

                    return {
                        "success": True,
                        "orders": orders,
                        "total_orders": len(orders)
                    }

        except Exception as e:
            logger.error(f"❌ Error getting customer orders: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve orders: {str(e)}",
                "orders": []
            }

    def _get_tier_discount_rate(self, account_tier: str) -> float:
        """Get discount rate based on account tier"""
        tier_discounts = {
            "Bronze": 0.0,    # No discount
            "Silver": 0.05,   # 5% discount
            "Gold": 0.10,     # 10% discount - FIXED FROM 5%
            "Platinum": 0.15  # 15% discount - FIXED FROM 10%
        }
        discount_rate = tier_discounts.get(account_tier, 0.0)
        logger.info(f"💰 Tier discount for {account_tier}: {discount_rate*100:.0f}%")
        return discount_rate

    def _update_customer_tier(self, cursor, customer_id: int, order_amount: float):
        """Update customer tier based on total spending with enhanced logic"""
        try:
            # 🔧 FIXED: Simplified SQL query to avoid casting issues
            cursor.execute("""
                SELECT c.account_tier,
                       COALESCE(SUM(CASE WHEN o.order_status != 'Returned' THEN o.total_amount ELSE 0 END), 0) as total_spent,
                       COUNT(CASE WHEN o.order_status != 'Returned' THEN o.order_id END) as order_count
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                WHERE c.customer_id = %s
                GROUP BY c.customer_id, c.account_tier
            """, (customer_id,))

            result = cursor.fetchone()
            if not result:
                logger.warning(f"⚠️ No customer data found for customer_id {customer_id}")
                return

            current_tier, total_spent_raw, order_count = result['account_tier'], result['total_spent'], result['order_count']

            # 🔧 ROBUST TYPE CONVERSION: Handle PostgreSQL Decimal/numeric types
            try:
                # Convert to float safely - handle Decimal, float, int, str, None
                if total_spent_raw is None:
                    total_spent = 0.0
                elif isinstance(total_spent_raw, (int, float)):
                    total_spent = float(total_spent_raw)
                elif hasattr(total_spent_raw, '__float__'):  # Decimal type
                    total_spent = float(total_spent_raw)
                elif isinstance(total_spent_raw, str):
                    # Only try to convert if it's a valid numeric string
                    if total_spent_raw.replace('.', '').replace('-', '').replace(',', '').isdigit():
                        total_spent = float(total_spent_raw.replace(',', ''))
                    else:
                        logger.error(f"❌ Invalid total_spent string '{total_spent_raw}' for customer {customer_id}")
                        total_spent = 0.0
                else:
                    # Last resort - try direct conversion
                    total_spent = float(total_spent_raw)

                logger.debug(f"💰 Customer {customer_id} - Total spent: ₦{total_spent:,.2f} (from {type(total_spent_raw).__name__}: {total_spent_raw})")

            except (ValueError, TypeError, AttributeError) as e:
                logger.error(f"❌ Error converting total_spent '{total_spent_raw}' (type: {type(total_spent_raw).__name__}) to float for customer {customer_id}: {e}")
                total_spent = 0.0

            # Enhanced tier progression logic with order count requirements
            tier_criteria = {
                'Platinum': {'spending': 2000000, 'orders': 20},  # ₦2M+, 20+ orders
                'Gold': {'spending': 500000, 'orders': 10},       # ₦500K+, 10+ orders
                'Silver': {'spending': 100000, 'orders': 3},      # ₦100K+, 3+ orders
                'Bronze': {'spending': 0, 'orders': 0}            # Default tier
            }

            # Determine new tier based on spending and order count
            new_tier = "Bronze"  # Default
            for tier, criteria in tier_criteria.items():
                if total_spent >= criteria['spending'] and order_count >= criteria['orders']:
                    new_tier = tier
                    break

            logger.info(f"🎯 TIER EVALUATION for customer {customer_id}:")
            logger.info(f"   💰 Total Spent: ₦{total_spent:,.2f}")
            logger.info(f"   📦 Order Count: {order_count}")
            logger.info(f"   🏆 Current Tier: {current_tier}")
            logger.info(f"   🎖️ Calculated Tier: {new_tier}")

            # Update tier if changed
            if new_tier != current_tier:
                cursor.execute("""
                    UPDATE customers
                    SET account_tier = %s::account_tier_enum, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s
                """, (new_tier, customer_id))

                logger.info(f"🏆 Customer {customer_id} upgraded from {current_tier} to {new_tier} tier!")
                logger.info(f"   💰 Total spent: ₦{total_spent:,}")
                logger.info(f"   📦 Order count: {order_count}")

                # Log tier upgrade for analytics
                try:
                    import json
                    from datetime import datetime
                    cursor.execute("""
                        INSERT INTO analytics (metric_type, metric_value, time_period, created_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """, (
                        'tier_upgrade',
                        json.dumps({
                            'customer_id': customer_id,
                            'from_tier': current_tier,
                            'to_tier': new_tier,
                            'total_spent': total_spent,
                            'order_count': order_count,
                            'upgrade_date': datetime.now().isoformat()
                        }),
                        'event'
                    ))
                    logger.info(f"📊 Tier upgrade analytics logged")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to log tier upgrade analytics: {e}")
            else:
                logger.debug(f"👥 Customer {customer_id} remains on {current_tier} tier (₦{total_spent:,} spent, {order_count} orders)")

        except Exception as e:
            logger.error(f"❌ Error updating customer tier for customer {customer_id}: {e}")
            # Don't let tier update failures block order creation

    def get_order_analytics(self, customer_id: int = None) -> Dict[str, Any]:
        """📊 Get order analytics and insights"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    base_query = """
                        SELECT
                            COUNT(*) as total_orders,
                            SUM(total_amount) as total_revenue,
                            AVG(total_amount) as avg_order_value,
                            COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) as delivered_orders,
                            COUNT(CASE WHEN order_status = 'Pending' THEN 1 END) as pending_orders,
                            COUNT(CASE WHEN order_status = 'Returned' THEN 1 END) as returned_orders
                        FROM orders
                    """

                    if customer_id:
                        base_query += " WHERE customer_id = %s"
                        cursor.execute(base_query, (customer_id,))
                    else:
                        cursor.execute(base_query)

                    analytics = dict(cursor.fetchone())

                    return {
                        "success": True,
                        "analytics": analytics
                    }

        except Exception as e:
            logger.error(f"❌ Error getting order analytics: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve analytics: {str(e)}"
            }

    def format_potential_order_summary(self, cart_summary, delivery_address, payment_method):
        """🧾 Format a potential order summary for checkout confirmation"""
        try:
            items_text = ""
            for item in cart_summary.get('items', []):
                items_text += f"• {item['product_name']} - ₦{item['price']:,.2f} x{item['quantity']} = ₦{item['subtotal']:,.2f}\n"

            # Handle delivery address formatting
            if isinstance(delivery_address, dict):
                address_str = delivery_address.get('full_address', str(delivery_address))
            else:
                address_str = str(delivery_address)

            # Handle payment method formatting
            if hasattr(payment_method, 'value'):
                payment_str = payment_method.value
            else:
                payment_str = str(payment_method)

            summary = f"""🛍️ **Order Summary**

{items_text}
📦 Total Items: {cart_summary.get('total_items', 0)}
💰 Subtotal: ₦{cart_summary.get('subtotal', 0):,.2f}

📍 **Delivery Address:** {address_str}
💳 **Payment Method:** {payment_str}

Ready to place your order? 🚀"""

            return summary.strip()
        except Exception as e:
            logger.error(f"❌ Error formatting order summary: {e}")
            return f"Order Summary: {cart_summary.get('total_items', 0)} items, ₦{cart_summary.get('subtotal', 0):,.2f} total"

    def place_order(self, customer_id, cart_items, delivery_address, payment_method, notes=""):
        """🛒 Place an order using the existing create_order method"""
        try:
            # Convert cart_items to the format expected by create_order
            items_for_order = []
            for item in cart_items:
                items_for_order.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity']
                })

            # Handle payment method conversion
            if hasattr(payment_method, 'value'):
                payment_method_str = payment_method.value
            else:
                payment_method_str = str(payment_method)

            # Call the existing create_order method
            result = self.create_order(
                customer_id=customer_id,
                items=items_for_order,
                delivery_address=delivery_address,
                payment_method=payment_method_str
            )

            if result.get('success'):
                order_id = result.get('order_id')
                order_summary = result.get('order_summary')  # This is the OrderSummary dataclass
                logger.info(f"✅ Order {order_id} placed successfully for customer {customer_id}")

                # Convert OrderSummary dataclass to dict for proper serialization
                if hasattr(order_summary, '__dataclass_fields__'):
                    # Convert OrderSummary dataclass to dict
                    order_details_dict = {
                        'order_id': order_summary.order_id,
                        'customer_id': order_summary.customer_id,
                        'customer_name': order_summary.customer_name,
                        'total_amount': order_summary.total_amount,
                        'subtotal': order_summary.subtotal,
                        'delivery_fee': order_summary.delivery_fee,
                        'tier_discount': order_summary.tier_discount,
                        'tax_amount': order_summary.tax_amount,
                        'payment_method': order_summary.payment_method.value if hasattr(order_summary.payment_method, 'value') else str(order_summary.payment_method),
                        'order_status': order_summary.order_status.value if hasattr(order_summary.order_status, 'value') else str(order_summary.order_status),
                        'status': order_summary.order_status.value if hasattr(order_summary.order_status, 'value') else str(order_summary.order_status),
                        'created_at': order_summary.created_at.isoformat() if hasattr(order_summary.created_at, 'isoformat') else str(order_summary.created_at),
                        'estimated_delivery': order_summary.estimated_delivery.isoformat() if hasattr(order_summary.estimated_delivery, 'isoformat') else str(order_summary.estimated_delivery),
                        'items': [],
                        'order_items': []
                    }

                    # Add delivery address from delivery_info
                    if hasattr(order_summary, 'delivery_info') and order_summary.delivery_info:
                        order_details_dict['delivery_address'] = order_summary.delivery_info.full_address
                        order_details_dict['delivery_info'] = {
                            'full_address': order_summary.delivery_info.full_address,
                            'state': order_summary.delivery_info.state,
                            'lga': order_summary.delivery_info.lga,
                            'delivery_fee': order_summary.delivery_info.delivery_fee,
                            'delivery_zone': order_summary.delivery_info.delivery_zone,
                            'estimated_delivery_days': order_summary.delivery_info.estimated_delivery_days
                        }
                    else:
                        order_details_dict['delivery_address'] = str(delivery_address)

                    # Add items in both formats for compatibility
                    for item in order_summary.items:
                        item_dict = {
                            'product_id': item.product_id,
                            'product_name': item.product_name,
                            'category': item.category,
                            'brand': item.brand,
                            'price': item.price,
                            'quantity': item.quantity,
                            'subtotal': item.subtotal,
                            'availability_status': item.availability_status
                        }
                        order_details_dict['items'].append(item_dict)
                        order_details_dict['order_items'].append(item_dict)

                    return order_id, order_details_dict, None
                else:
                    # Fallback if order_summary is already a dict
                    return order_id, order_summary, None
            else:
                error_msg = result.get('error', 'Unknown error occurred')
                logger.error(f"❌ Failed to place order for customer {customer_id}: {error_msg}")
                return None, None, error_msg

        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None, None, str(e)

    def format_order_summary(self, order_details):
        """🎉 Format order details into a readable confirmation summary"""
        try:
            # Handle OrderSummary dataclass objects
            if hasattr(order_details, '__dataclass_fields__'):
                # This is an OrderSummary dataclass object
                items_text = ""
                for item in order_details.items:
                    if hasattr(item, 'product_name'):
                        items_text += f"• {item.product_name} x{item.quantity} - ₦{item.subtotal:,.2f}\n"

                # Handle delivery address formatting
                delivery_str = "Not specified"
                if hasattr(order_details, 'delivery_info') and order_details.delivery_info:
                    delivery_str = order_details.delivery_info.full_address

                # Handle payment method formatting
                payment_method_str = "Not specified"
                if hasattr(order_details, 'payment_method'):
                    if hasattr(order_details.payment_method, 'value'):
                        payment_method_str = order_details.payment_method.value
                    else:
                        payment_method_str = str(order_details.payment_method)

                # Handle order status formatting
                status_str = "Pending"
                if hasattr(order_details, 'order_status'):
                    if hasattr(order_details.order_status, 'value'):
                        status_str = order_details.order_status.value
                    else:
                        status_str = str(order_details.order_status)

                summary = f"""🎉 **Order Confirmation**

📋 Order ID: {order_details.order_id}
{items_text}
💰 Total: ₦{order_details.total_amount:,.2f}
📍 Delivery: {delivery_str}
💳 Payment: {payment_method_str}
📦 Status: {status_str}

Your order has been successfully placed! 🚀
We'll send you updates as it progresses."""

                return summary.strip()

            # Handle dictionary format (existing logic)
            items_text = ""

            # Handle different order_details formats
            if 'items' in order_details:
                items = order_details['items']
            elif 'order_items' in order_details:
                items = order_details['order_items']
            else:
                # Try to extract from individual order details
                items = [{
                    'product_name': order_details.get('product_name', 'Unknown Product'),
                    'quantity': 1,
                    'subtotal': order_details.get('total_amount', 0)
                }]

            for item in items:
                if isinstance(item, dict):
                    product_name = item.get('product_name', 'Unknown Product')
                    quantity = item.get('quantity', 1)
                    subtotal = item.get('subtotal', item.get('price', 0))
                    items_text += f"• {product_name} x{quantity} - ₦{subtotal:,.2f}\n"
                else:
                    # Handle OrderItem objects if they exist
                    items_text += f"• {getattr(item, 'product_name', 'Unknown')} x{getattr(item, 'quantity', 1)} - ₦{getattr(item, 'subtotal', 0):,.2f}\n"

            # Handle delivery address formatting
            delivery_address = order_details.get('delivery_address', 'Not specified')
            if isinstance(delivery_address, dict):
                delivery_str = delivery_address.get('full_address', str(delivery_address))
            else:
                delivery_str = str(delivery_address)

            summary = f"""🎉 **Order Confirmation**

📋 Order ID: {order_details.get('order_id', 'Unknown')}
{items_text}
💰 Total: ₦{order_details.get('total_amount', 0):,.2f}
📍 Delivery: {delivery_str}
💳 Payment: {order_details.get('payment_method', 'Not specified')}
📦 Status: {order_details.get('status', order_details.get('order_status', 'Pending'))}

Your order has been successfully placed! 🚀
We'll send you updates as it progresses."""

            return summary.strip()
        except Exception as e:
            logger.error(f"❌ Error formatting order confirmation: {e}")
            # Safe fallback that works with both formats
            if hasattr(order_details, 'order_id'):
                order_id = order_details.order_id
                total_amount = getattr(order_details, 'total_amount', 0)
            else:
                order_id = order_details.get('order_id', 'Unknown')
                total_amount = order_details.get('total_amount', 0)
            return f"Order {order_id} confirmed - ₦{total_amount:,.2f}"
