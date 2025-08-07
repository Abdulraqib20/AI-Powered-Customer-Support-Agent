#!/usr/bin/env python3
"""
Ethnically Authentic Bulk Data Generation for Nigerian E-commerce
Generate thousands of realistic Nigerian e-commerce records with proper ethnic-geographical mapping
Based on Nigeria's three major ethnic groups (Hausa, Yoruba, Igbo) and six geopolitical zones
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, date, timedelta
import random
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database_config import get_repositories, DATABASE_CONFIG
import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NIGERIA'S GEOPOLITICAL ZONES AND ETHNIC DISTRIBUTION
# Based on authentic Nigerian demographics and geographical patterns

GEOPOLITICAL_ZONES = {
    'North_West': {
        'states': ['Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Sokoto', 'Zamfara'],
        'dominant_ethnicity': 'Hausa',
        'secondary_ethnicity': 'Fulani',
        'religion': 'Islam',
        'economic_pattern': 'agriculture_trading'
    },
    'North_East': {
        'states': ['Adamawa', 'Bauchi', 'Borno', 'Gombe', 'Taraba', 'Yobe'],
        'dominant_ethnicity': 'Hausa',
        'secondary_ethnicity': 'Kanuri',
        'religion': 'Islam',
        'economic_pattern': 'agriculture_livestock'
    },
    'North_Central': {
        'states': ['Benue', 'Kogi', 'Kwara', 'Nasarawa', 'Niger', 'Plateau', 'Abuja'],
        'dominant_ethnicity': 'Middle_Belt',  # Mixed ethnicities
        'secondary_ethnicity': 'Hausa',
        'religion': 'Mixed',
        'economic_pattern': 'agriculture_civil_service'
    },
    'South_West': {
        'states': ['Ekiti', 'Lagos', 'Ogun', 'Ondo', 'Osun', 'Oyo'],
        'dominant_ethnicity': 'Yoruba',
        'secondary_ethnicity': 'Yoruba',
        'religion': 'Christianity_Islam',
        'economic_pattern': 'commerce_industry'
    },
    'South_East': {
        'states': ['Abia', 'Anambra', 'Ebonyi', 'Enugu', 'Imo'],
        'dominant_ethnicity': 'Igbo',
        'secondary_ethnicity': 'Igbo',
        'religion': 'Christianity',
        'economic_pattern': 'commerce_manufacturing'
    },
    'South_South': {
        'states': ['Akwa Ibom', 'Bayelsa', 'Cross River', 'Delta', 'Edo', 'Rivers'],
        'dominant_ethnicity': 'Niger_Delta',  # Ijaw, Efik, Ibibio, etc.
        'secondary_ethnicity': 'Edo',
        'religion': 'Christianity',
        'economic_pattern': 'oil_gas_fishing'
    }
}

# AUTHENTIC NIGERIAN NAMES BY ETHNIC GROUP AND GENDER
NIGERIAN_NAMES = {
    'Hausa': {
        'male_first': ['Abubakar', 'Ahmed', 'Aliyu', 'Aminu', 'Bashir', 'Garba', 'Hassan', 'Ibrahim', 'Ismail', 'Kabir', 'Mahmud', 'Muhammad', 'Musa', 'Sani', 'Umar', 'Usman', 'Yusuf', 'Zakariya'],
        'female_first': ['Aisha', 'Amina', 'Asma\'u', 'Fatima', 'Hafsat', 'Hajara', 'Halima', 'Hauwa', 'Khadija', 'Maryam', 'Nasira', 'Rahma', 'Safiya', 'Salamatu', 'Zainab', 'Zulaihat'],
        'surnames': ['Abdullahi', 'Ahmad', 'Bello', 'Dantata', 'Gidado', 'Hassan', 'Ibrahim', 'Jibril', 'Kano', 'Mohammed', 'Mustapha', 'Sani', 'Tanko', 'Usman', 'Yusuf']
    },
    'Yoruba': {
        'male_first': ['Adebayo', 'Adeniyi', 'Adeolu', 'Adewale', 'Akeem', 'Babatunde', 'Bamidele', 'Biodun', 'Bolaji', 'Femi', 'Kayode', 'Kunle', 'Olumide', 'Segun', 'Tunde', 'Wale', 'Yemi'],
        'female_first': ['Adunni', 'Aishat', 'Bisola', 'Bukola', 'Folake', 'Funmi', 'Kehinde', 'Kemi', 'Nike', 'Olumide', 'Ronke', 'Sade', 'Taiwo', 'Tope', 'Yetunde'],
        'surnames': ['Adebayo', 'Adeleke', 'Adeyemi', 'Akindele', 'Akinyemi', 'Babangida', 'Falana', 'Obasanjo', 'Ogundipe', 'Okonkwo', 'Olusegun', 'Oyebola', 'Tinubu']
    },
    'Igbo': {
        'male_first': ['Chidi', 'Chijioke', 'Chikwado', 'Chinedu', 'Chukwudi', 'Emeka', 'Ikechukwu', 'Kelechi', 'Nnamdi', 'Obiora', 'Obinna', 'Okechukwu', 'Oluchukwu', 'Onyeka', 'Ugochukwu'],
        'female_first': ['Adaeze', 'Amaka', 'Chiamaka', 'Chioma', 'Ebere', 'Ifeoma', 'Ngozi', 'Nkechi', 'Nmesoma', 'Obiageli', 'Ogechi', 'Uchechi', 'Ugochi'],
        'surnames': ['Achebe', 'Azikiwe', 'Chukwu', 'Eze', 'Ikpeazu', 'Nnamani', 'Nwankwo', 'Obi', 'Ogbonna', 'Okwu', 'Okonkwo', 'Onwudiwe', 'Uzor']
    },
    'Niger_Delta': {
        'male_first': ['Ebitimi', 'Timipre', 'Preye', 'Dokubo', 'Tonye', 'Tariye', 'Ere', 'Daniel', 'Victor', 'Emmanuel', 'Michael', 'Peter', 'John', 'Joseph'],
        'female_first': ['Ebiere', 'Tonbra', 'Kemeari', 'Diepreye', 'Bolouere', 'Blessing', 'Faith', 'Grace', 'Joy', 'Peace', 'Mercy', 'Patience'],
        'surnames': ['Alamieyeseigha', 'Dickson', 'Sylva', 'Jonathan', 'Okowa', 'Wike', 'Peterside', 'Abe', 'Amaechi', 'Odili']
    },
    'Middle_Belt': {
        'male_first': ['Danjuma', 'Yakubu', 'Samuel', 'Gyang', 'Pam', 'Dogara', 'Timothy', 'Joshua', 'David', 'James', 'Paul', 'Abraham'],
        'female_first': ['Laraba', 'Comfort', 'Rebecca', 'Lydia', 'Ruth', 'Esther', 'Deborah', 'Sarah', 'Mary', 'Hannah'],
        'surnames': ['Danjuma', 'Gowon', 'Dogara', 'Orka', 'Akume', 'Suswam', 'Yar\'Adua', 'Kwankwaso', 'Shekarau']
    }
}

# LGAs BY STATE (Major ones for authenticity)
LGAS_BY_STATE = {
    # North West (Hausa/Fulani)
    'Kano': ['Municipal', 'Fagge', 'Dala', 'Gwale', 'Tarauni', 'Nasarawa', 'Ungogo'],
    'Kaduna': ['Kaduna North', 'Kaduna South', 'Chikun', 'Igabi', 'Ikara', 'Kafanchan'],
    'Sokoto': ['Sokoto North', 'Sokoto South', 'Wamako', 'Kware', 'Tangaza'],
    'Katsina': ['Katsina', 'Daura', 'Funtua', 'Malumfashi', 'Dutsin-Ma'],

    # South West (Yoruba)
    'Lagos': ['Lagos Island', 'Lagos Mainland', 'Surulere', 'Ikeja', 'Alimosho', 'Ikorodu', 'Epe'],
    'Oyo': ['Ibadan North', 'Ibadan South West', 'Ogbomoso North', 'Oyo East', 'Iseyin'],
    'Ogun': ['Abeokuta North', 'Abeokuta South', 'Ijebu Ode', 'Sagamu', 'Ilaro'],
    'Osun': ['Osogbo', 'Ile Ife East', 'Iwo', 'Ede North', 'Ejigbo'],

    # South East (Igbo)
    'Anambra': ['Awka North', 'Awka South', 'Onitsha North', 'Onitsha South', 'Nnewi North'],
    'Imo': ['Owerri Municipal', 'Owerri North', 'Owerri West', 'Orlu', 'Okigwe'],
    'Enugu': ['Enugu North', 'Enugu South', 'Enugu East', 'Nsukka', 'Udi'],
    'Abia': ['Umuahia North', 'Umuahia South', 'Aba North', 'Aba South', 'Arochukwu'],

    # South South (Niger Delta)
    'Rivers': ['Port Harcourt', 'Obio-Akpor', 'Okrika', 'Eleme', 'Ikwerre'],
    'Delta': ['Warri North', 'Warri South', 'Sapele', 'Ughelli North', 'Isoko South'],
    'Akwa Ibom': ['Uyo', 'Ikot Ekpene', 'Eket', 'Oron', 'Abak'],
    'Cross River': ['Calabar Municipal', 'Calabar South', 'Ikom', 'Ogoja', 'Obudu'],

    # North Central (Mixed)
    'Abuja': ['Municipal Area Council', 'Gwagwalada', 'Kuje', 'Abaji', 'Kwali', 'Bwari'],
    'Niger': ['Minna', 'Bida', 'Kontagora', 'Suleja', 'New Bussa'],
    'Plateau': ['Jos North', 'Jos South', 'Mangu', 'Pankshin', 'Bokkos'],
    'Benue': ['Makurdi', 'Gboko', 'Otukpo', 'Katsina-Ala', 'Vandeikya']
}

def get_zone_for_state(state):
    """Get the geopolitical zone for a given state"""
    for zone, data in GEOPOLITICAL_ZONES.items():
        if state in data['states']:
            return zone
    return 'North_Central'  # Default fallback

def generate_ethnically_authentic_customer():
    """Generate a customer with ethnically authentic name-state-ethnicity matching"""

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

    # Customer registration date (1 day to 3 years ago)
    days_ago = random.randint(1, 1095)
    registration_date = datetime.now() - timedelta(days=days_ago)

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
        'zone': zone
    }

    return customer

def generate_cultural_preferences(ethnicity, religion):
    """Generate culturally appropriate preferences"""

    # Base categories
    all_categories = ['Electronics', 'Fashion', 'Food Items', 'Home & Kitchen', 'Beauty',
                     'Books', 'Sports', 'Automotive', 'Baby Products', 'Health',
                     'Phones & Tablets', 'Computing']

    # Cultural preferences
    if ethnicity == 'Hausa':
        preferred_categories = random.sample(['Fashion', 'Food Items', 'Electronics', 'Books', 'Home & Kitchen'],
                                           random.randint(2, 4))
        languages = ['Hausa', 'English', 'Arabic']
    elif ethnicity == 'Yoruba':
        preferred_categories = random.sample(['Electronics', 'Fashion', 'Beauty', 'Phones & Tablets', 'Computing'],
                                           random.randint(3, 5))
        languages = ['Yoruba', 'English']
    elif ethnicity == 'Igbo':
        preferred_categories = random.sample(['Electronics', 'Computing', 'Automotive', 'Phones & Tablets', 'Fashion'],
                                           random.randint(3, 5))
        languages = ['Igbo', 'English']
    else:  # Niger Delta or Middle Belt
        preferred_categories = random.sample(all_categories, random.randint(2, 4))
        languages = ['English']

    # Delivery preferences
    delivery_prefs = ['Home Delivery', 'Pickup Station', 'Express Delivery', 'Office Delivery']

    return {
        'language': random.choice(languages),
        'preferred_categories': preferred_categories,
        'notifications': {
            'email': random.choice([True, False]),
            'sms': random.choice([True, False])
        },
        'delivery_preference': random.choice(delivery_prefs),
        'cultural_background': ethnicity
    }

def generate_realistic_phone():
    """Generate realistic Nigerian phone numbers"""
    prefixes = ['+234', '0']
    # Valid network codes for major networks
    valid_networks = ['70', '71', '80', '81', '90', '91']

    prefix = random.choice(prefixes)
    network = random.choice(valid_networks)
    remaining = ''.join([str(random.randint(0, 9)) for _ in range(8)])

    if prefix == '+234':
        return f"+234{network}{remaining}"
    else:
        return f"0{network}{remaining}"

def generate_realistic_email(name):
    """Generate realistic email addresses"""
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'yahoo.co.uk']
    separators = ['.', '_', '']
    numbers = ['', str(random.randint(1, 999)), str(random.randint(2000, 2024))]

    clean_name = name.lower().replace(' ', '').replace('\'', '')
    domain = random.choice(domains)
    separator = random.choice(separators)
    number = random.choice(numbers)

    return f"{clean_name}{separator}{number}@{domain}"

# BUSINESS LOGIC FOR ACCOUNT TIERS (Same as before)
TIER_CRITERIA = {
    'Bronze': {
        'min_total_spent': 0,
        'max_total_spent': 100000,
        'min_orders': 0,
        'max_orders': 5,
        'description': 'New customers or low-value customers'
    },
    'Silver': {
        'min_total_spent': 100000,
        'max_total_spent': 500000,
        'min_orders': 3,
        'max_orders': float('inf'),  # No upper limit on orders
        'description': 'Regular customers with moderate spending'
    },
    'Gold': {
        'min_total_spent': 500000,
        'max_total_spent': 2000000,
        'min_orders': 10,
        'max_orders': float('inf'),  # No upper limit on orders
        'description': 'High-value customers with frequent orders'
    },
    'Platinum': {
        'min_total_spent': 2000000,
        'max_total_spent': float('inf'),
        'min_orders': 20,
        'max_orders': float('inf'),
        'description': 'VIP customers with highest value and loyalty'
    }
}

def calculate_account_tier(total_spent, order_count, days_as_customer):
    """Calculate account tier based on business criteria"""
    # Apply time-based bonuses for long-term customers
    if days_as_customer > 365:
        total_spent *= 1.1
    if days_as_customer > 730:
        total_spent *= 1.2

    # Determine tier based on spending and order frequency
    for tier in ['Platinum', 'Gold', 'Silver', 'Bronze']:
        criteria = TIER_CRITERIA[tier]
        if (total_spent >= criteria['min_total_spent'] and
            total_spent <= criteria['max_total_spent'] and
            order_count >= criteria['min_orders'] and
            order_count <= criteria['max_orders']):
            return tier

    return 'Bronze'

def generate_orders_for_customer(customer):
    """Generate realistic orders for a customer"""
    orders = []
    remaining_budget = customer['total_spent']
    num_orders = customer['order_count']

    # Product categories based on customer's zone and ethnicity
    preferences = json.loads(customer['preferences'])
    preferred_categories = preferences.get('preferred_categories', ['Electronics', 'Fashion'])

    # Payment methods based on region and tier
    zone = customer['zone']
    tier = customer['account_tier']

    if zone in ['South_West', 'South_East'] and tier in ['Gold', 'Platinum']:
        payment_methods = random.choices(
            ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'],
            weights=[0.1, 0.2, 0.5, 0.2]
        )
    elif zone in ['North_West', 'North_East']:
        payment_methods = random.choices(
            ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'],
            weights=[0.5, 0.3, 0.15, 0.05]
        )
    else:
        payment_methods = random.choices(
            ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'],
            weights=[0.3, 0.3, 0.3, 0.1]
        )

    for i in range(num_orders):
        # Order date between registration and now
        days_since_reg = random.randint(0, customer['days_as_customer'])
        order_date = customer['created_at'] + timedelta(days=days_since_reg)

        # Future delivery date
        delivery_date = datetime.now() + timedelta(days=random.randint(1, 30))

        # Order amount
        if i == num_orders - 1:
            amount = max(remaining_budget, 5000)
        else:
            avg_per_order = remaining_budget / (num_orders - i)
            amount = random.uniform(avg_per_order * 0.3, avg_per_order * 1.7)
            amount = max(amount, 5000)
            amount = min(amount, remaining_budget * 0.8)

        remaining_budget -= amount

        order = {
            'customer_id': None,
            'order_status': random.choices(
                ['Pending', 'Processing', 'Delivered', 'Returned'],
                weights=[0.1, 0.2, 0.65, 0.05]
            )[0],
            'payment_method': payment_methods[0],
            'total_amount': round(amount, 2),
            'delivery_date': delivery_date.date(),
            'product_category': random.choice(preferred_categories),
            'created_at': order_date
        }
        orders.append(order)

    return orders

def generate_ethnically_authentic_bulk_data(num_customers=1000):
    """Generate bulk data with ethnic authenticity"""
    logger.info(f"🌍 Generating {num_customers} customers with ethnic-geographical authenticity...")
    logger.info("📍 Mapping: Hausa (North), Yoruba (SW), Igbo (SE), Niger Delta (SS)")

    customers_data = []
    all_orders_data = []

    # Track ethnic distribution
    ethnic_count = {}
    zone_count = {}

    for i in range(num_customers):
        if i % 100 == 0:
            logger.info(f"   📊 Generated {i}/{num_customers} customers...")

        customer = generate_ethnically_authentic_customer()
        customers_data.append(customer)

        # Track distribution
        ethnicity = customer['ethnicity']
        zone = customer['zone']
        ethnic_count[ethnicity] = ethnic_count.get(ethnicity, 0) + 1
        zone_count[zone] = zone_count.get(zone, 0) + 1

        # Generate orders
        orders = generate_orders_for_customer(customer)
        all_orders_data.extend(orders)

    # Log distributions
    logger.info("🏛️ Ethnic Distribution:")
    for ethnicity, count in ethnic_count.items():
        percentage = (count / num_customers) * 100
        logger.info(f"   {ethnicity}: {count} ({percentage:.1f}%)")

    logger.info("🗺️ Geopolitical Zone Distribution:")
    for zone, count in zone_count.items():
        percentage = (count / num_customers) * 100
        logger.info(f"   {zone}: {count} ({percentage:.1f}%)")

    customers_df = pd.DataFrame(customers_data)
    orders_df = pd.DataFrame(all_orders_data)

    return customers_df, orders_df

def insert_ethnically_authentic_data(customers_df, orders_df):
    """Insert ethnically authentic data into PostgreSQL"""
    logger.info("💾 Inserting ethnically authentic data into PostgreSQL...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        with conn.cursor() as cursor:
            # Insert customers
            logger.info(f"👥 Inserting {len(customers_df)} ethnically authentic customers...")

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
                    if "duplicate key" not in str(e).lower():
                        logger.warning(f"⚠️ Customer insert warning: {e}")
                    conn.rollback()

            conn.commit()
            logger.info(f"✅ Successfully inserted {successful_customers} ethnically authentic customers")

            # Insert orders
            logger.info(f"📦 Inserting {len(orders_df)} culturally appropriate orders...")

            successful_orders = 0
            for idx, order in orders_df.iterrows():
                try:
                    available_customers = list(customer_id_mapping.values())
                    if not available_customers:
                        break

                    customer_id = random.choice(available_customers)

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

            # Show final statistics
            cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]

            logger.info(f"✅ Database now contains:")
            logger.info(f"   👥 {customer_count} ethnically authentic customers")
            logger.info(f"   📦 {order_count} culturally appropriate orders")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Database insertion failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting Ethnically Authentic Nigerian E-commerce Data Generation")
    logger.info("🌍 Ensuring cultural authenticity: Names ↔ States ↔ Ethnic Groups")
    logger.info("📍 Geopolitical Zones: North (Hausa), SW (Yoruba), SE (Igbo), SS (Niger Delta)")

    NUM_CUSTOMERS = 1000

    try:
        # Generate ethnically authentic data
        customers_df, orders_df = generate_ethnically_authentic_bulk_data(NUM_CUSTOMERS)

        # Insert into database
        if insert_ethnically_authentic_data(customers_df, orders_df):
            logger.info("🎉 Ethnically Authentic Data Generation Complete!")
            logger.info("✅ Cultural authenticity maintained throughout!")
            logger.info("  Your Nigerian e-commerce database is now culturally accurate!")
        else:
            logger.error("❌ Data generation failed!")

    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")

if __name__ == "__main__":
    main()
