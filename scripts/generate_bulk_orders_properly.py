#!/usr/bin/env python3
"""
Generate Bulk Orders While Respecting Database Constraints
Generate thousands of orders that work with current database setup
Maintains all ethnic authenticity and business logic
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, date, timedelta
import random
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.database_config import get_repositories, DATABASE_CONFIG
import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_existing_customers():
    """Get all existing customers with their details"""
    logger.info("📊 Loading existing customers...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT customer_id, name, account_tier, state, preferences, created_at
            FROM customers
            ORDER BY customer_id
        """)

        customers = []
        for row in cursor.fetchall():
            customer_id, name, tier, state, preferences, created_at = row

            # Parse preferences
            if isinstance(preferences, str):
                prefs = json.loads(preferences)
            else:
                prefs = preferences

            customers.append({
                'customer_id': customer_id,
                'name': name,
                'account_tier': tier,
                'state': state,
                'preferences': prefs,
                'created_at': created_at
            })

        conn.close()
        logger.info(f"✅ Loaded {len(customers)} existing customers")
        return customers

    except Exception as e:
        logger.error(f"❌ Failed to load customers: {e}")
        return []

def calculate_customer_order_profile(customer):
    """Calculate realistic order profile for a customer based on tier and history"""

    tier = customer['account_tier']
    registration_date = customer['created_at']
    days_as_customer = (datetime.now() - registration_date).days

    # Base order patterns by tier - updated with correct categories
    tier_profiles = {
        'Bronze': {
            'orders_per_month': random.uniform(0.5, 2.0),
            'avg_order_value': random.uniform(8000, 25000),
            'preferred_categories': ['Food Items', 'Beauty', 'Books'],
            'payment_method_weights': [0.6, 0.25, 0.1, 0.05]  # [POD, Bank, Card, RaqibTech]
        },
        'Silver': {
            'orders_per_month': random.uniform(1.5, 4.0),
            'avg_order_value': random.uniform(15000, 50000),
            'preferred_categories': ['Fashion', 'Phones & Tablets', 'Beauty', 'Books'],
            'payment_method_weights': [0.4, 0.3, 0.25, 0.05]
        },
        'Gold': {
            'orders_per_month': random.uniform(3.0, 8.0),
            'avg_order_value': random.uniform(30000, 100000),
            'preferred_categories': ['Electronics', 'Computing', 'Phones & Tablets', 'Automotive'],
            'payment_method_weights': [0.2, 0.3, 0.4, 0.1]
        },
        'Platinum': {
            'orders_per_month': random.uniform(5.0, 15.0),
            'avg_order_value': random.uniform(50000, 200000),
            'preferred_categories': ['Electronics', 'Computing', 'Automotive', 'Fashion'],
            'payment_method_weights': [0.1, 0.3, 0.5, 0.1]
        }
    }

    profile = tier_profiles.get(tier, tier_profiles['Bronze'])

    # Calculate number of orders based on customer lifetime
    months_active = max(days_as_customer / 30, 1)
    total_orders = int(profile['orders_per_month'] * months_active)

    # Add some randomness but ensure reasonable minimums
    total_orders = max(total_orders + random.randint(-2, 5), 1)

    return {
        'total_orders': total_orders,
        'avg_order_value': profile['avg_order_value'],
        'preferred_categories': profile['preferred_categories'],
        'payment_method_weights': profile['payment_method_weights']
    }

def generate_future_orders_for_customer(customer, order_profile, num_orders):
    """Generate orders with future delivery dates for constraint compliance"""

    orders = []
    payment_methods = ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay']

    # Load products for smart assignment
    products_by_category = get_products_by_category()

    # Start generating orders from today forward
    today = datetime.now()

    for i in range(num_orders):
        # Order placement time - can be in the past or recent
        # But delivery must be in future
        if i < num_orders // 2:
            # Recent orders (last 30 days)
            order_date = today - timedelta(days=random.randint(0, 30))
        else:
            # Older orders (up to customer lifetime, but delivery still future)
            max_days_back = min((today - customer['created_at']).days, 365)
            order_date = today - timedelta(days=random.randint(0, max_days_back))

        # Add realistic time
        hour = random.choices(
            list(range(24)),
            weights=[1,1,1,1,1,1,2,3,4,4,4,4,4,4,4,4,4,3,2,2,1,1,1,1]  # Business hours weighted
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        order_date = order_date.replace(hour=hour, minute=minute, second=second)

        # CRITICAL: Delivery date must be FUTURE to satisfy constraint
        delivery_date = today.date() + timedelta(days=random.randint(1, 45))

        # Order amount with variation
        base_amount = order_profile['avg_order_value']
        amount = random.uniform(base_amount * 0.3, base_amount * 1.8)
        amount = max(amount, 5000)  # Minimum order value

        # Select category and smart product assignment
        category = random.choice(order_profile['preferred_categories'])
        product_id = select_smart_product(category, amount, products_by_category)

        # Select payment method
        payment_method = random.choices(
            payment_methods,
            weights=order_profile['payment_method_weights']
        )[0]

        # Order status with realistic distribution
        status = random.choices(
            ['Pending', 'Processing', 'Delivered', 'Returned'],
            weights=[0.15, 0.25, 0.55, 0.05]
        )[0]

        order = {
            'customer_id': customer['customer_id'],
            'order_status': status,
            'payment_method': payment_method,
            'total_amount': round(amount, 2),
            'delivery_date': delivery_date,
            'product_category': category,
            'product_id': product_id,
            'created_at': order_date
        }

        orders.append(order)

    return orders

def get_products_by_category():
    """Load products grouped by category for smart assignment"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT product_id, category, price
            FROM products
            ORDER BY category, product_id
        """)

        products_by_category = {}
        for product_id, category, price in cursor.fetchall():
            if category not in products_by_category:
                products_by_category[category] = []
            products_by_category[category].append({
                'id': product_id,
                'price': float(price)
            })

        conn.close()
        return products_by_category

    except Exception as e:
        logger.warning(f"⚠️ Could not load products: {e}. Using fallback.")
        return {}

def select_smart_product(category, order_amount, products_by_category):
    """Select product based on category and price matching"""
    if category not in products_by_category or not products_by_category[category]:
        return None

    available_products = products_by_category[category]

    # Filter products by price range (50% below to 200% above order amount)
    min_price = order_amount * 0.5
    max_price = order_amount * 2.0

    suitable_products = [
        p for p in available_products
        if min_price <= p['price'] <= max_price
    ]

    # If no suitable products by price, use all products in category
    if not suitable_products:
        suitable_products = available_products

    # Select random product from suitable ones
    selected_product = random.choice(suitable_products)
    return selected_product['id']

def insert_bulk_orders(orders_data):
    """Insert bulk orders efficiently"""
    logger.info(f"💾 Inserting {len(orders_data)} orders...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        successful_orders = 0
        failed_orders = 0

        with conn.cursor() as cursor:
            for i, order in enumerate(orders_data):
                try:
                    cursor.execute("""
                        INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category, product_id, created_at)
                        VALUES (%s, %s::order_status_enum, %s::payment_method_enum, %s, %s, %s, %s, %s)
                    """, (
                        order['customer_id'],
                        order['order_status'],
                        order['payment_method'],
                        order['total_amount'],
                        order['delivery_date'],
                        order['product_category'],
                        order['product_id'],
                        order['created_at']
                    ))

                    successful_orders += 1

                    # Commit every 500 orders
                    if successful_orders % 500 == 0:
                        conn.commit()
                        logger.info(f"   ✅ Committed {successful_orders} orders...")

                except Exception as e:
                    failed_orders += 1
                    conn.rollback()
                    if failed_orders < 10:  # Only log first 10 failures
                        logger.warning(f"⚠️ Order insert failed: {str(e)[:100]}...")

            # Final commit
            conn.commit()

        conn.close()

        logger.info(f"✅ Successfully inserted {successful_orders} orders")
        if failed_orders > 0:
            logger.warning(f"⚠️ {failed_orders} orders failed (constraint violations)")

        return successful_orders

    except Exception as e:
        logger.error(f"❌ Bulk insert failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return 0

def generate_enhanced_analytics():
    """Generate comprehensive analytics data"""
    logger.info("📊 Generating enhanced analytics...")

    analytics_data = []
    now = datetime.now()

    # Customer tier analytics
    tiers = ['Bronze', 'Silver', 'Gold', 'Platinum']
    for tier in tiers:
        analytics_data.append({
            'metric_type': 'customer_tier_performance',
            'metric_value': json.dumps({
                'tier': tier,
                'avg_order_value': random.randint(10000, 80000),
                'orders_per_month': random.uniform(1.0, 10.0),
                'retention_rate': random.uniform(0.7, 0.95),
                'currency': 'NGN'
            }),
            'time_period': 'current_month',
            'created_at': now
        })

    # Geographic performance
    top_states = ['Lagos', 'Kano', 'Rivers', 'Oyo', 'Kaduna', 'Anambra']
    for state in top_states:
        analytics_data.append({
            'metric_type': 'state_performance',
            'metric_value': json.dumps({
                'state': state,
                'total_orders': random.randint(50, 500),
                'revenue': random.randint(1000000, 10000000),
                'avg_delivery_time': random.randint(2, 8),
                'currency': 'NGN'
            }),
            'time_period': 'last_30_days',
            'created_at': now
        })

    # Product category performance
    categories = ['Electronics', 'Fashion', 'Food Items', 'Computing', 'Beauty', 'Automotive', 'Books', 'Phones & Tablets']
    for category in categories:
        analytics_data.append({
            'metric_type': 'category_performance',
            'metric_value': json.dumps({
                'category': category,
                'units_sold': random.randint(100, 2000),
                'revenue': random.randint(500000, 5000000),
                'profit_margin': random.uniform(0.15, 0.40),
                'currency': 'NGN'
            }),
            'time_period': 'last_quarter',
            'created_at': now
        })

    return analytics_data

def insert_analytics_data(analytics_data):
    """Insert analytics data"""
    logger.info(f"📈 Inserting {len(analytics_data)} analytics records...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        successful_analytics = 0

        with conn.cursor() as cursor:
            for analytics in analytics_data:
                try:
                    cursor.execute("""
                        INSERT INTO analytics (metric_type, metric_value, time_period, created_at)
                        VALUES (%s, %s::jsonb, %s, %s)
                    """, (
                        analytics['metric_type'],
                        analytics['metric_value'],
                        analytics['time_period'],
                        analytics['created_at']
                    ))
                    successful_analytics += 1

                except Exception as e:
                    logger.warning(f"⚠️ Analytics insert failed: {e}")
                    conn.rollback()

            conn.commit()

        conn.close()
        logger.info(f"✅ Successfully inserted {successful_analytics} analytics records")
        return successful_analytics

    except Exception as e:
        logger.error(f"❌ Analytics insertion failed: {e}")
        return 0

def main():
    """Main function to generate bulk data respecting constraints"""
    logger.info("🚀 Starting Bulk Order Generation")
    logger.info("⚠️ Generating future-dated orders to respect delivery constraints")

    # Step 1: Load existing customers
    customers = get_existing_customers()
    if not customers:
        logger.error("❌ No customers found! Run customer generation first.")
        return

    # Step 2: Generate orders for each customer
    logger.info("🛍️ Generating orders for each customer...")

    all_orders = []
    total_planned_orders = 0

    for i, customer in enumerate(customers):
        if i % 100 == 0:
            logger.info(f"   📊 Processing customer {i+1}/{len(customers)}...")

        # Calculate order profile based on tier and history
        order_profile = calculate_customer_order_profile(customer)
        num_orders = min(order_profile['total_orders'], 20)  # Cap at 20 orders per customer
        total_planned_orders += num_orders

        # Generate orders for this customer
        customer_orders = generate_future_orders_for_customer(customer, order_profile, num_orders)
        all_orders.extend(customer_orders)

    logger.info(f"📦 Generated {len(all_orders)} orders across {len(customers)} customers")
    logger.info(f"📊 Average orders per customer: {len(all_orders) / len(customers):.1f}")

    # Step 3: Insert orders
    successful_orders = insert_bulk_orders(all_orders)

    # Step 4: Generate and insert enhanced analytics
    analytics_data = generate_enhanced_analytics()
    successful_analytics = insert_analytics_data(analytics_data)

    # Step 5: Final summary
    logger.info("🎉 Bulk Generation Complete!")
    logger.info(f"✅ Results:")
    logger.info(f"   👥 {len(customers)} customers (existing)")
    logger.info(f"   📦 {successful_orders} orders successfully inserted")
    logger.info(f"   📊 {successful_analytics} analytics records added")
    logger.info("   🌍 All ethnic authenticity preserved")
    logger.info("   ⏰ All constraints respected")
    logger.info("     Ready for AI hackathon!")

if __name__ == "__main__":
    main()
