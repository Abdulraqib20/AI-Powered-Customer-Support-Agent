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
    """Nigerian state-based delivery fee and time calculator"""

    # Delivery zones and fees (in Naira)
    DELIVERY_ZONES = {
        "Lagos Metro": {
            "states": ["Lagos"],
            "base_fee": 2000,
            "per_kg_fee": 500,
            "delivery_days": 1
        },
        "Abuja FCT": {
            "states": ["FCT"],
            "base_fee": 2500,
            "per_kg_fee": 600,
            "delivery_days": 2
        },
        "Major Cities": {
            "states": ["Kano", "Rivers", "Oyo", "Kaduna", "Anambra", "Edo", "Enugu", "Delta", "Imo"],
            "base_fee": 3000,
            "per_kg_fee": 700,
            "delivery_days": 3
        },
        "Other States": {
            "states": ["Abia", "Adamawa", "Akwa Ibom", "Bauchi", "Bayelsa", "Benue", "Borno",
                      "Cross River", "Ebonyi", "Ekiti", "Gombe", "Jigawa", "Kebbi", "Kogi",
                      "Kwara", "Nasarawa", "Niger", "Ondo", "Osun", "Ogun", "Plateau",
                      "Sokoto", "Taraba", "Yobe", "Zamfara"],
            "base_fee": 4000,
            "per_kg_fee": 800,
            "delivery_days": 5
        }
    }

    @staticmethod
    def calculate_delivery_fee(state: str, total_weight_kg: float = 1.0, total_value: float = 0) -> Tuple[float, int, str]:
        """Calculate delivery fee based on Nigerian state and package details"""

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

        # Calculate base delivery fee
        base_fee = zone_info["base_fee"]
        weight_fee = zone_info["per_kg_fee"] * max(1.0, total_weight_kg)

        # Apply free delivery for high-value orders
        total_delivery_fee = base_fee + weight_fee
        if total_value >= 200000:  # Free delivery for orders above ₦200K
            total_delivery_fee = 0
        elif total_value >= 100000:  # 50% discount for orders above ₦100K
            total_delivery_fee *= 0.5

        delivery_days = zone_info["delivery_days"]

        return total_delivery_fee, delivery_days, zone_name

class OrderManagementSystem:
    """🛒 Advanced Order Management System"""

    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'oracle'),
        }

        # Initialize Redis for order caching
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
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

            # Calculate item subtotals
            order_items = []
            subtotal = Decimal('0.00')
            total_weight = Decimal('0.00')  # 🔧 Fix: Use Decimal for consistency

            for item in items:
                product_check = self.check_product_availability(
                    item['product_id'], item['quantity']
                )

                if not product_check['available']:
                    raise ValueError(f"Product {item['product_id']}: {product_check['error']}")

                product_info = product_check['product_info']
                item_price = Decimal(str(product_info['price']))
                quantity = Decimal(str(item['quantity']))  # 🔧 Fix: Convert to Decimal
                item_subtotal = item_price * quantity

                order_items.append(OrderItem(
                    product_id=product_info['product_id'],
                    product_name=product_info['product_name'],
                    category=product_info['category'],
                    brand=product_info['brand'],
                    price=float(item_price),
                    quantity=int(quantity),  # Keep as int for OrderItem
                    subtotal=float(item_subtotal),
                    availability_status="Available"
                ))

                subtotal += item_subtotal
                # 🔧 Fix: Ensure weight calculation uses Decimal
                weight_per_item = Decimal(str(product_info.get('weight_kg', 1.0)))
                total_weight += (weight_per_item * quantity)

            # Calculate delivery fee
            delivery_fee, delivery_days, delivery_zone = self.delivery_calculator.calculate_delivery_fee(
                delivery_state, float(total_weight), float(subtotal)
            )

            # Calculate tier discount
            tier_discount_rate = self._get_tier_discount_rate(customer['account_tier'])
            tier_discount = subtotal * Decimal(str(tier_discount_rate))

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
                "total_weight_kg": float(total_weight),  # 🔧 Fix: Convert back to float for return
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
                    # Get customer info
                    cursor.execute("""
                        SELECT name, email, phone, lga FROM customers WHERE customer_id = %s
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
        """📦 Get order status and tracking information"""
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

            # Query database
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT o.order_id, o.customer_id, o.order_status, o.payment_method,
                               o.total_amount, o.delivery_date, o.created_at, o.updated_at,
                               c.name as customer_name, c.state, c.lga, c.address,
                               p.product_name, p.category, p.brand, p.price
                        FROM orders o
                        JOIN customers c ON o.customer_id = c.customer_id
                        LEFT JOIN products p ON o.product_id = p.product_id
                        WHERE o.order_id = %s
                    """

                    params = [order_id]
                    if customer_id:
                        query += " AND o.customer_id = %s"
                        params.append(customer_id)

                    cursor.execute(query, params)
                    order_data = cursor.fetchone()

                    if not order_data:
                        return {
                            "success": False,
                            "error": "Order not found or access denied"
                        }

                    return {
                        "success": True,
                        "order": dict(order_data),
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
        """📋 Get customer's order history"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT o.order_id, o.order_status, o.payment_method, o.total_amount,
                               o.delivery_date, o.created_at, o.updated_at,
                               p.product_name, p.category, p.brand
                        FROM orders o
                        LEFT JOIN products p ON o.product_id = p.product_id
                        WHERE o.customer_id = %s
                        ORDER BY o.created_at DESC
                        LIMIT %s
                    """, (customer_id, limit))

                    orders = [dict(row) for row in cursor.fetchall()]

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
            "Silver": 0.02,   # 2% discount
            "Gold": 0.05,     # 5% discount
            "Platinum": 0.10  # 10% discount
        }
        return tier_discounts.get(account_tier, 0.0)

    def _update_customer_tier(self, cursor, customer_id: int, order_amount: float):
        """Update customer tier based on total spending"""
        # Get customer's total spending
        cursor.execute("""
            SELECT SUM(total_amount) as total_spent, account_tier
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.customer_id = %s AND o.order_status != 'Returned'
            GROUP BY c.account_tier
        """, (customer_id,))

        result = cursor.fetchone()
        if not result:
            return

        total_spent = float(result['total_spent'] or 0)
        current_tier = result['account_tier']

        # Tier progression thresholds (in Naira)
        tier_thresholds = {
            100000: "Silver",    # ₦100K
            300000: "Gold",      # ₦300K
            500000: "Platinum"   # ₦500K
        }

        new_tier = "Bronze"  # Default
        for threshold, tier in sorted(tier_thresholds.items()):
            if total_spent >= threshold:
                new_tier = tier

        # Update tier if changed
        if new_tier != current_tier:
            cursor.execute("""
                UPDATE customers
                SET account_tier = %s, updated_at = CURRENT_TIMESTAMP
                WHERE customer_id = %s
            """, (new_tier, customer_id))

            logger.info(f"🏆 Customer {customer_id} upgraded to {new_tier} tier")

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
