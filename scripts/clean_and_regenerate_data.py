#!/usr/bin/env python3
"""
Clean and Regenerate Ethnically Authentic Data
Clean existing database and populate with fresh, authentic Nigerian e-commerce data
with realistic timestamp distribution
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

def clean_database():
    """Clean existing data while preserving schema"""
    logger.info("🧹 Cleaning existing database data...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = True

        with conn.cursor() as cursor:
            # Clear data in proper order (respecting foreign keys)
            cursor.execute("TRUNCATE TABLE analytics CASCADE")
            cursor.execute("TRUNCATE TABLE orders CASCADE")
            cursor.execute("TRUNCATE TABLE customers CASCADE")

            # Reset sequences
            cursor.execute("ALTER SEQUENCE customers_customer_id_seq RESTART WITH 1")
            cursor.execute("ALTER SEQUENCE orders_order_id_seq RESTART WITH 1")
            cursor.execute("ALTER SEQUENCE analytics_analytics_id_seq RESTART WITH 1")

            logger.info("✅ Database cleaned successfully")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Database cleaning failed: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def generate_realistic_timestamps():
    """Generate realistic timestamp distributions"""

    # Define business periods for more authentic data
    now = datetime.now()

    # Business growth periods (more recent = more activity)
    periods = {
        'early_stage': {
            'start': now - timedelta(days=1095),  # 3 years ago
            'end': now - timedelta(days=730),     # 2 years ago
            'weight': 0.15,
            'daily_orders': (5, 20)
        },
        'growth_stage': {
            'start': now - timedelta(days=730),   # 2 years ago
            'end': now - timedelta(days=365),     # 1 year ago
            'weight': 0.25,
            'daily_orders': (20, 50)
        },
        'expansion_stage': {
            'start': now - timedelta(days=365),   # 1 year ago
            'end': now - timedelta(days=90),      # 3 months ago
            'weight': 0.35,
            'daily_orders': (50, 100)
        },
        'current_stage': {
            'start': now - timedelta(days=90),    # 3 months ago
            'end': now,
            'weight': 0.25,
            'daily_orders': (80, 150)
        }
    }

    return periods

def generate_ethnically_authentic_customer_with_realistic_time():
    """Generate customer with realistic registration time"""
    # Import the functions we need from the original script
    import sys
    import os

    # Add the scripts directory to path to import the ethnic generation functions
    scripts_dir = Path(__file__).parent
    sys.path.append(str(scripts_dir))

    # Import all the ethnic data generation components
    from generate_bulk_data_ethnically_authentic import (
        GEOPOLITICAL_ZONES, NIGERIAN_NAMES, LGAS_BY_STATE,
        get_zone_for_state, generate_cultural_preferences,
        generate_realistic_phone, generate_realistic_email,
        TIER_CRITERIA, calculate_account_tier
    )

    periods = generate_realistic_timestamps()

    # Select period based on weights
    period_names = list(periods.keys())
    weights = [periods[p]['weight'] for p in period_names]
    selected_period = random.choices(period_names, weights=weights)[0]

    period_info = periods[selected_period]

    # Generate customer using the same logic as the original function
    # First select a geopolitical zone (weighted by population/economic activity)
    zone_weights = {
        'North_West': 0.25,    # Largest population
        'South_West': 0.22,    # Economic powerhouse
        'South_East': 0.18,    # High commercial activity
        'North_Central': 0.15, # Federal capital + middle belt
        'South_South': 0.12,   # Oil region
        'North_East': 0.08     # Security challenges affect e-commerce
    }

    zone = random.choices(list(zone_weights.keys()), weights=list(zone_weights.values()))[0]
    zone_info = GEOPOLITICAL_ZONES[zone]

    # Select state from the zone
    state = random.choice(zone_info['states'])

    # Determine ethnicity based on zone
    if zone in ['North_West', 'North_East']:
        ethnicity = random.choices(['Hausa', 'Fulani'], weights=[0.8, 0.2])[0]
        if ethnicity == 'Fulani':
            ethnicity = 'Hausa'  # Use Hausa names for Fulani as they're closely related
    elif zone == 'South_West':
        ethnicity = 'Yoruba'
    elif zone == 'South_East':
        ethnicity = 'Igbo'
    elif zone == 'South_South':
        ethnicity = random.choices(['Niger_Delta', 'Edo'], weights=[0.7, 0.3])[0]
        if ethnicity == 'Edo':
            ethnicity = 'Niger_Delta'  # Use Niger Delta names for broader South-South
    else:  # North_Central
        ethnicity = random.choices(['Middle_Belt', 'Hausa', 'Yoruba'], weights=[0.5, 0.3, 0.2])[0]

    # Generate gender
    gender = random.choice(['male', 'female'])

    # Generate ethnically appropriate name
    names = NIGERIAN_NAMES[ethnicity]
    first_name = random.choice(names[f'{gender}_first'])
    surname = random.choice(names['surnames'])
    full_name = f"{first_name} {surname}"

    # Select LGA based on state
    lgas = LGAS_BY_STATE.get(state, ['Central', 'Municipal', 'Urban'])
    lga = random.choice(lgas)

    # Generate realistic address
    street_types = ['Street', 'Avenue', 'Road', 'Close', 'Crescent', 'Lane']
    address = f"{random.randint(1, 150)} {random.choice(['Ahmadu', 'Ibrahim', 'Murtala', 'Tafawa Balewa', 'Independence', 'Unity', 'Peace', 'Progress', 'New Market'])} {random.choice(street_types)}, {lga}, {state}"

    # Override registration date with realistic timestamp
    period_duration = (period_info['end'] - period_info['start']).days
    random_days = random.randint(0, period_duration)
    registration_date = period_info['start'] + timedelta(days=random_days)

    # Add realistic hour (business hours weighted)
    business_hours = list(range(8, 18)) * 3 + list(range(18, 22)) * 2 + list(range(6, 8)) + list(range(22, 24))
    hour = random.choice(business_hours)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    registration_date = registration_date.replace(hour=hour, minute=minute, second=second)

    # Economic behavior based on zone
    zone_economic_multiplier = {
        'South_West': 1.4,     # Lagos economic hub
        'South_South': 1.3,    # Oil money
        'South_East': 1.2,     # Commercial activity
        'North_Central': 1.1,  # Civil service + Abuja
        'North_West': 0.9,     # Agricultural economy
        'North_East': 0.8      # Economic challenges
    }

    multiplier = zone_economic_multiplier[zone]
    if state in ['Lagos', 'Abuja']:
        multiplier *= 1.3  # Major cities premium

    # Generate order history and spending
    base_orders = random.randint(1, 20)
    order_count = int(base_orders * multiplier)

    # Base spending based on zone economics
    base_spending = random.uniform(25000, 600000)
    total_spent = base_spending * multiplier

    # Calculate days as customer from registration date
    days_ago = (datetime.now() - registration_date).days

    # Calculate tier based on business logic
    account_tier = calculate_account_tier(total_spent, order_count, days_ago)

    # Generate preferences based on ethnicity and religion
    preferences = generate_cultural_preferences(ethnicity, zone_info['religion'])

    customer = {
        'name': full_name,
        'email': generate_realistic_email(full_name),
        'phone': generate_realistic_phone(),
        'state': state,
        'lga': lga,
        'address': address,
        'account_tier': account_tier,
        'preferences': json.dumps(preferences),
        'created_at': registration_date,
        'total_spent': total_spent,
        'order_count': order_count,
        'days_as_customer': days_ago,
        'ethnicity': ethnicity,
        'zone': zone,
        'period': selected_period
    }

    return customer

def generate_realistic_orders_with_timestamps(customer):
    """Generate orders with realistic timestamps distributed over customer's lifetime"""
    orders = []

    customer_lifetime = customer['days_as_customer']
    num_orders = customer['order_count']
    remaining_budget = customer['total_spent']

    # Product categories based on customer's preferences
    preferences = json.loads(customer['preferences'])
    preferred_categories = preferences.get('preferred_categories', ['Electronics', 'Fashion'])

    # Payment methods based on region and tier
    zone = customer['zone']
    tier = customer['account_tier']

    if zone in ['South_West', 'South_East'] and tier in ['Gold', 'Platinum']:
        payment_weights = [0.1, 0.2, 0.5, 0.2]
    elif zone in ['North_West', 'North_East']:
        payment_weights = [0.5, 0.3, 0.15, 0.05]
    else:
        payment_weights = [0.3, 0.3, 0.3, 0.1]

    payment_methods = ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay']

    # Generate order timestamps with realistic distribution
    order_dates = []

    if customer_lifetime > 0 and num_orders > 0:
        # Create realistic order frequency (higher frequency for recent customers)
        if customer_lifetime <= 30:  # New customers
            # Orders clustered in recent days
            order_dates = [
                customer['created_at'] + timedelta(days=random.randint(0, min(customer_lifetime, 30)))
                for _ in range(num_orders)
            ]
        elif customer_lifetime <= 180:  # 6 month customers
            # More frequent recent orders
            early_orders = num_orders // 3
            recent_orders = num_orders - early_orders

            order_dates = (
                [customer['created_at'] + timedelta(days=random.randint(0, customer_lifetime // 2))
                 for _ in range(early_orders)] +
                [customer['created_at'] + timedelta(days=random.randint(customer_lifetime // 2, customer_lifetime))
                 for _ in range(recent_orders)]
            )
        else:  # Long-term customers
            # Distributed throughout lifetime with seasonal patterns
            for i in range(num_orders):
                # Simulate seasonal shopping (more orders during festive periods)
                day_offset = random.randint(0, customer_lifetime)
                order_date = customer['created_at'] + timedelta(days=day_offset)

                # Add festive season boost (December, April-May)
                month = order_date.month
                if month in [12, 4, 5]:  # Christmas, Easter, Eid periods
                    if random.random() < 0.3:  # 30% chance to cluster orders
                        day_offset = random.randint(max(0, customer_lifetime - 60), customer_lifetime)
                        order_date = customer['created_at'] + timedelta(days=day_offset)

                order_dates.append(order_date)
    else:
        # Fallback for edge cases
        order_dates = [customer['created_at'] for _ in range(num_orders)]

    # Sort orders chronologically
    order_dates.sort()

    # Generate orders with realistic timestamps
    for i, order_date in enumerate(order_dates):
        # Add realistic time of day
        business_hours = list(range(9, 17)) * 4 + list(range(17, 21)) * 2 + list(range(7, 9)) + list(range(21, 23))
        hour = random.choice(business_hours)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        order_date = order_date.replace(hour=hour, minute=minute, second=second)

        # Future delivery date (1-30 days from order)
        delivery_date = order_date.date() + timedelta(days=random.randint(1, 30))

        # Order amount distribution
        if i == num_orders - 1:
            amount = max(remaining_budget, 5000)
        else:
            avg_per_order = remaining_budget / (num_orders - i)
            amount = random.uniform(avg_per_order * 0.4, avg_per_order * 1.6)
            amount = max(amount, 5000)
            amount = min(amount, remaining_budget * 0.9)

        remaining_budget -= amount

        # Select payment method
        payment_method = random.choices(payment_methods, weights=payment_weights)[0]

        order = {
            'customer_id': None,  # Will be set during insertion
            'order_status': random.choices(
                ['Pending', 'Processing', 'Delivered', 'Returned'],
                weights=[0.1, 0.2, 0.65, 0.05]
            )[0],
            'payment_method': payment_method,
            'total_amount': round(amount, 2),
            'delivery_date': delivery_date,
            'product_category': random.choice(preferred_categories),
            'created_at': order_date
        }
        orders.append(order)

    return orders

def generate_analytics_data():
    """Generate realistic analytics data"""

    analytics_data = []

    # Revenue analytics by period
    periods = generate_realistic_timestamps()
    for period_name, period_info in periods.items():
        analytics_data.append({
            'metric_type': 'revenue_by_period',
            'metric_value': json.dumps({
                'period': period_name,
                'revenue': random.randint(500000, 5000000),
                'orders': random.randint(100, 1000),
                'currency': 'NGN'
            }),
            'time_period': period_name,
            'created_at': datetime.now()
        })

    # Geographic analytics
    for zone in ['North_West', 'North_East', 'North_Central', 'South_West', 'South_East', 'South_South']:
        analytics_data.append({
            'metric_type': 'revenue_by_zone',
            'metric_value': json.dumps({
                'zone': zone,
                'revenue': random.randint(200000, 2000000),
                'customers': random.randint(50, 500),
                'currency': 'NGN'
            }),
            'time_period': 'overall',
            'created_at': datetime.now()
        })

    return analytics_data

def insert_clean_authentic_data(customers_df, orders_df, analytics_data):
    """Insert clean, ethnically authentic data with realistic timestamps"""
    logger.info("💾 Inserting clean, ethnically authentic data...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        with conn.cursor() as cursor:
            # Insert customers
            logger.info(f"👥 Inserting {len(customers_df)} customers with realistic timestamps...")

            customer_id_mapping = {}
            successful_customers = 0

            for idx, customer in customers_df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::account_tier_enum, %s::jsonb, %s)
                        RETURNING customer_id
                    """, (
                        customer['name'],
                        customer['email'],
                        customer['phone'],
                        customer['state'],
                        customer['lga'],
                        customer['address'],
                        customer['account_tier'],
                        customer['preferences'],
                        customer['created_at']
                    ))

                    customer_id = cursor.fetchone()[0]
                    customer_id_mapping[idx] = customer_id
                    successful_customers += 1

                    if successful_customers % 100 == 0:
                        conn.commit()
                        logger.info(f"   ✅ Committed {successful_customers} customers...")

                except Exception as e:
                    logger.warning(f"⚠️ Customer insert warning: {e}")
                    conn.rollback()

            conn.commit()
            logger.info(f"✅ Successfully inserted {successful_customers} customers")

            # Insert orders with proper customer relationships
            logger.info(f"📦 Inserting orders with realistic timestamps...")

            successful_orders = 0
            orders_by_customer = {}

            # Group orders by customer index
            for idx, order in orders_df.iterrows():
                customer_idx = order.get('customer_idx', idx % len(customer_id_mapping))
                if customer_idx not in orders_by_customer:
                    orders_by_customer[customer_idx] = []
                orders_by_customer[customer_idx].append(order)

            # Insert orders for each customer
            for customer_idx, customer_orders in orders_by_customer.items():
                if customer_idx in customer_id_mapping:
                    customer_id = customer_id_mapping[customer_idx]

                    for order in customer_orders:
                        try:
                            cursor.execute("""
                                INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at)
                                VALUES (%s, %s::order_status_enum, %s::payment_method_enum, %s, %s, %s, %s)
                            """, (
                                customer_id,
                                order['order_status'],
                                order['payment_method'],
                                order['total_amount'],
                                order['delivery_date'],
                                order['product_category'],
                                order['created_at']
                            ))

                            successful_orders += 1

                            if successful_orders % 500 == 0:
                                conn.commit()
                                logger.info(f"   ✅ Committed {successful_orders} orders...")

                        except Exception as e:
                            logger.warning(f"⚠️ Order insert warning: {e}")
                            conn.rollback()

            conn.commit()
            logger.info(f"✅ Successfully inserted {successful_orders} orders")

            # Insert analytics
            logger.info("📊 Inserting analytics data...")
            successful_analytics = 0

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
                    logger.warning(f"⚠️ Analytics insert warning: {e}")
                    conn.rollback()

            conn.commit()
            logger.info(f"✅ Successfully inserted {successful_analytics} analytics records")

            # Show final statistics
            cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM analytics")
            analytics_count = cursor.fetchone()[0]

            logger.info(f"✅ Clean database now contains:")
            logger.info(f"   👥 {customer_count} ethnically authentic customers")
            logger.info(f"   📦 {order_count} orders with realistic timestamps")
            logger.info(f"   📊 {analytics_count} analytics records")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Data insertion failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function to clean and regenerate authentic data"""
    logger.info("🚀 Starting Clean Database Regeneration")
    logger.info("🌍 Ethnic authenticity + Realistic timestamps")

    NUM_CUSTOMERS = 1500  # Slightly larger dataset

    try:
        # Step 1: Clean existing data
        if not clean_database():
            logger.error("❌ Failed to clean database")
            return

        # Step 2: Generate ethnically authentic customers with realistic timestamps
        logger.info(f"🌍 Generating {NUM_CUSTOMERS} customers with realistic registration times...")

        customers_data = []
        all_orders_data = []

        for i in range(NUM_CUSTOMERS):
            if i % 100 == 0:
                logger.info(f"   📊 Generated {i}/{NUM_CUSTOMERS} customers...")

            customer = generate_ethnically_authentic_customer_with_realistic_time()
            customers_data.append(customer)

            # Generate orders for this customer
            orders = generate_realistic_orders_with_timestamps(customer)

            # Add customer index to orders for proper relationship
            for order in orders:
                order['customer_idx'] = i

            all_orders_data.extend(orders)

        # Step 3: Generate analytics data
        analytics_data = generate_analytics_data()

        # Step 4: Convert to DataFrames
        customers_df = pd.DataFrame(customers_data)
        orders_df = pd.DataFrame(all_orders_data)

        logger.info(f"📊 Generated:")
        logger.info(f"   👥 {len(customers_df)} customers")
        logger.info(f"   📦 {len(orders_df)} orders")
        logger.info(f"   📈 {len(analytics_data)} analytics records")

        # Step 5: Insert clean data
        if insert_clean_authentic_data(customers_df, orders_df, analytics_data):
            logger.info("🎉 Clean Regeneration Complete!")
            logger.info("✅ Database now has:")
            logger.info("   🌍 Ethnically authentic customers")
            logger.info("   ⏰ Realistic timestamp distribution")
            logger.info("   🏆 Intelligent business tier logic")
            logger.info("     Ready for AI hackathon!")
        else:
            logger.error("❌ Data insertion failed!")

    except Exception as e:
        logger.error(f"❌ Regeneration failed: {e}")

if __name__ == "__main__":
    main()
