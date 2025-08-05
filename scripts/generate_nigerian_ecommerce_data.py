#!/usr/bin/env python3
"""
🇳🇬 Nigerian E-commerce Data Generator
Generates authentic Nigerian e-commerce data for Flask app with:
- Fresh data generation for orders, customers, and products tables
- Data augmentation for existing records
- Nigerian ethnic and regional diversity
- Business growth stage timestamp distributions
- RBAC staff accounts integration
- Realistic tier progression and payment patterns
"""

import os
import sys
import json
import random
import re
import bcrypt
import psycopg2
import pandas as pd
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config.database_config import DATABASE_CONFIG
except ImportError:
    # Fallback database config
    from config.appconfig import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

    DATABASE_CONFIG = {
        'host': DB_HOST,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURATION CONSTANTS
# =====================================================================

# Business Growth Stages with Realistic Timestamp Distributions
BUSINESS_GROWTH_STAGES = {
    'early_stage': {
        'weight': 0.15,
        'start_date': datetime(2023, 1, 1),
        'end_date': datetime(2023, 6, 30),
        'customer_multiplier': 0.3,
        'order_frequency_multiplier': 0.5
    },
    'growth_stage': {
        'weight': 0.25,
        'start_date': datetime(2023, 7, 1),
        'end_date': datetime(2024, 3, 31),
        'customer_multiplier': 0.7,
        'order_frequency_multiplier': 0.8
    },
    'expansion_stage': {
        'weight': 0.35,
        'start_date': datetime(2024, 4, 1),
        'end_date': datetime(2024, 12, 31),
        'customer_multiplier': 1.0,
        'order_frequency_multiplier': 1.2
    },
    'current_stage': {
        'weight': 0.25,
        'start_date': datetime(2025, 1, 1),
        'end_date': datetime(2025, 6, 9),  # Up to June 09, 2025
        'customer_multiplier': 1.2,
        'order_frequency_multiplier': 1.5
    }
}

# Nigerian Network Prefixes - FIXED FOR DATABASE CONSTRAINT
# Constraint: ^(\+234|0)[7-9][0-1][0-9]{8}$
# This means: start with +234 or 0, then 7/8/9, then 0/1, then 8 digits
NETWORK_PREFIXES = {
    'MTN': ['0701', '0801', '0901'],  # MTN network prefixes matching constraint
    'Airtel': ['0702', '0802', '0902'],  # Airtel network prefixes matching constraint
    'Glo': ['0705', '0805', '0905'],  # Glo network prefixes matching constraint
    '9mobile': ['0709', '0809', '0909']  # 9mobile network prefixes matching constraint
}

# Product Categories
ALL_PRODUCT_CATEGORIES = [
    'Automotive', 'Beauty', 'Books', 'Computing', 'Electronics', 'Fashion', 'Food Items', 'Home & Kitchen'
]

# RBAC Staff Accounts
STAFF_ACCOUNTS = {
    'support_agents': [
        {'name': 'Adunni Support Agent', 'email': 'adunni.support@raqibtech.com', 'phone': '08035550001', 'state': 'Lagos', 'lga': 'Victoria Island', 'password': 'Support2024!', 'user_role': 'support_agent'},
        {'name': 'Kemi Support Agent', 'email': 'kemi.support@raqibtech.com', 'phone': '08035550002', 'state': 'Abuja', 'lga': 'Wuse', 'password': 'Support2024!', 'user_role': 'support_agent'}
    ],
    'admins': [
        {'name': 'Folake Admin', 'email': 'folake.admin@raqibtech.com', 'phone': '08035550003', 'state': 'Lagos', 'lga': 'Ikeja', 'password': 'Admin2024!', 'user_role': 'admin'},
        {'name': 'Chidi Admin', 'email': 'chidi.admin@raqibtech.com', 'phone': '08035550004', 'state': 'Anambra', 'lga': 'Awka', 'password': 'Admin2024!', 'user_role': 'admin'}
    ],
    'super_admins': [
        {'name': 'Raqib Super Admin', 'email': 'raqib@raqibtech.com', 'phone': '07025965922', 'state': 'Lagos', 'lga': 'Victoria Island', 'password': 'SuperAdmin2024!', 'user_role': 'super_admin'}
    ]
}

# Account Tier Logic
TIER_CRITERIA = {
    'Bronze': {'min_spent': 0, 'max_spent': 100000, 'min_orders': 0},
    'Silver': {'min_spent': 100000, 'max_spent': 500000, 'min_orders': 3},
    'Gold': {'min_spent': 500000, 'max_spent': 2000000, 'min_orders': 10},
    'Platinum': {'min_spent': 2000000, 'max_spent': float('inf'), 'min_orders': 20}
}

# Nigerian Food Products (from your existing system)
NIGERIAN_FOOD_PRODUCTS = [
    ('Golden Penny Semovita 1kg', 'Food Items', 'Golden Penny', 'Premium semolina for making swallow, rich in carbohydrates', 2500.00, 150, 1.0, '20 x 15 x 8'),
    ('Honeywell Wheat Flour 2kg', 'Food Items', 'Honeywell', 'High-quality wheat flour for baking bread, cakes, and pastries', 3200.00, 200, 2.0, '25 x 20 x 10'),
    ('Mama Gold Rice 50kg', 'Food Items', 'Mama Gold', 'Premium parboiled rice, stone-free, perfect for jollof rice', 85000.00, 50, 50.0, '80 x 50 x 15'),
    ('Cap Rice 25kg', 'Food Items', 'Cap Rice', 'Quality long grain rice, ideal for Nigerian households', 45000.00, 75, 25.0, '70 x 40 x 12'),
    ('Dangote Spaghetti 500g', 'Food Items', 'Dangote', 'Premium pasta made from durum wheat, perfect for spaghetti dishes', 1800.00, 300, 0.5, '30 x 8 x 3'),
    ('Titus Fish (Frozen) 1kg', 'Food Items', 'Ocean Fresh', 'Fresh frozen mackerel fish, rich in omega-3, perfect for stews', 8500.00, 100, 1.0, '25 x 15 x 8'),
    ('Chicken (Whole) 1.5kg', 'Food Items', 'CHI Farms', 'Fresh whole chicken, farm-raised, antibiotic-free', 12000.00, 80, 1.5, '30 x 20 x 15'),
    ('Beef (Fresh Cut) 1kg', 'Food Items', 'Premium Meat', 'Fresh beef cuts, perfect for pepper soup and stews', 15000.00, 60, 1.0, '25 x 20 x 8'),
    ('Dried Fish (Stockfish) 500g', 'Food Items', 'Niger Delta', 'Premium dried stockfish, essential for authentic Nigerian soups', 25000.00, 40, 0.5, '40 x 20 x 10'),
    ('Smoked Turkey 1kg', 'Food Items', 'Smoky Delights', 'Premium smoked turkey, adds rich flavor to soups and stews', 18000.00, 35, 1.0, '30 x 20 x 12'),
    ('Maggi Cubes (50 pieces)', 'Food Items', 'Maggi', 'Popular seasoning cubes for Nigerian cooking, chicken flavor', 2500.00, 500, 0.5, '15 x 10 x 8'),
    ('Curry Powder 100g', 'Food Items', 'Spice World', 'Aromatic curry powder blend, perfect for rice dishes', 1500.00, 200, 0.1, '10 x 8 x 5'),
    ('Thyme Leaves 50g', 'Food Items', 'Fresh Herbs', 'Dried thyme leaves for seasoning soups and stews', 800.00, 150, 0.05, '8 x 6 x 3'),
    ('Scotch Bonnet Pepper (Ata Rodo) 250g', 'Food Items', 'Farm Fresh', 'Hot peppers essential for Nigerian pepper soup and stews', 1200.00, 100, 0.25, '15 x 10 x 5'),
    ('Locust Beans (Iru) 200g', 'Food Items', 'Traditional', 'Fermented locust beans, traditional seasoning for soups', 3500.00, 80, 0.2, '12 x 8 x 6'),
    ('Devon Kings Vegetable Oil 5L', 'Food Items', 'Devon Kings', 'Pure vegetable cooking oil, perfect for frying and cooking', 12000.00, 120, 5.0, '25 x 20 x 30'),
    ('Red Palm Oil 1L', 'Food Items', 'Tropical Oil', 'Pure red palm oil, essential for authentic Nigerian dishes', 4500.00, 100, 1.0, '20 x 8 x 25'),
    ('Groundnut Oil 2L', 'Food Items', 'Golden Oil', 'Pure groundnut oil, ideal for deep frying and traditional cooking', 8000.00, 90, 2.0, '22 x 10 x 28'),
    ('Coconut Oil (Virgin) 500ml', 'Food Items', 'Pure Coconut', 'Extra virgin coconut oil for healthy cooking and hair care', 6500.00, 60, 0.5, '15 x 8 x 15'),
    ('Milo Chocolate Drink 500g', 'Food Items', 'Milo', 'Nutritious chocolate malt drink, rich in vitamins and minerals', 4500.00, 180, 0.5, '12 x 8 x 15'),
    ('Bournvita 500g', 'Food Items', 'Bournvita', 'Health food drink with essential nutrients for growing children', 4200.00, 160, 0.5, '12 x 8 x 15'),
    ('Lipton Tea Bags (100 pieces)', 'Food Items', 'Lipton', 'Premium black tea bags, perfect for Nigerian tea culture', 3500.00, 200, 0.3, '15 x 10 x 8'),
    ('Peak Milk Powder 900g', 'Food Items', 'Peak', 'Full cream milk powder, essential for tea, coffee, and cooking', 8500.00, 140, 0.9, '18 x 12 x 20'),
    ('Hollandia Yoghurt 1L', 'Food Items', 'Hollandia', 'Fresh strawberry yoghurt, probiotic and nutritious', 2500.00, 100, 1.0, '20 x 8 x 25'),
    ('Plantain Chips 250g', 'Food Items', 'Crispy Bites', 'Crunchy plantain chips, perfect snack for all ages', 1500.00, 250, 0.25, '20 x 15 x 8'),
    ('Chin Chin 500g', 'Food Items', 'Sweet Treats', 'Traditional Nigerian sweet snack, crunchy and delicious', 2000.00, 200, 0.5, '25 x 18 x 10'),
    ('Groundnut (Roasted) 500g', 'Food Items', 'Nutty Delights', 'Roasted groundnuts, protein-rich healthy snack', 1800.00, 180, 0.5, '20 x 15 x 8'),
    ('Kuli Kuli 200g', 'Food Items', 'Northern Treats', 'Traditional groundnut snack from Northern Nigeria', 1200.00, 150, 0.2, '15 x 10 x 5'),
    ('Coconut Candy 300g', 'Food Items', 'Island Sweets', 'Sweet coconut candy, traditional Nigerian confection', 2500.00, 120, 0.3, '18 x 12 x 8'),
    ('Yam Tuber (Medium) 2kg', 'Food Items', 'Farm Direct', 'Fresh yam tuber, perfect for pounded yam and yam porridge', 8000.00, 80, 2.0, '40 x 15 x 15'),
    ('Sweet Potato 1kg', 'Food Items', 'Organic Farms', 'Fresh sweet potatoes, rich in vitamins and fiber', 3500.00, 120, 1.0, '30 x 20 x 10'),
    ('Cassava Flour (Garri) 2kg', 'Food Items', 'Traditional Mills', 'Premium garri for eba, processed hygienically', 3000.00, 200, 2.0, '25 x 20 x 10'),
    ('Plantain (Bunch)', 'Food Items', 'Tropical Farms', 'Fresh ripe plantains, perfect for dodo and plantain porridge', 4500.00, 100, 3.0, '50 x 20 x 15'),
    ('Corned Beef 340g', 'Food Items', 'Geisha', 'Premium corned beef, protein-rich, perfect for sandwiches', 3500.00, 150, 0.34, '12 x 8 x 8'),
    ('Sardine in Tomato Sauce 125g', 'Food Items', 'Titus', 'Sardine fish in rich tomato sauce, omega-3 rich', 1800.00, 200, 0.125, '10 x 6 x 3'),
    ('Sweet Corn (Canned) 340g', 'Food Items', 'Green Valley', 'Sweet corn kernels in brine, ready to eat', 2200.00, 180, 0.34, '12 x 8 x 10'),
    ('Honey 500ml', 'Food Items', 'Pure Honey', 'Raw unprocessed honey, natural sweetener with health benefits', 8500.00, 80, 0.5, '15 x 8 x 20'),
    ('Non-stick Frying Pan 28cm', 'Home & Kitchen', 'Kitchen Master', 'Non-stick frying pan perfect for Nigerian cooking', 15000.00, 60, 1.2, '30 x 30 x 8'),
    ('Pressure Pot 5L', 'Home & Kitchen', 'Prestige', 'Pressure cooker for faster cooking of beans and tough meat', 35000.00, 40, 3.5, '25 x 25 x 20'),
    ('Mortar and Pestle (Traditional)', 'Home & Kitchen', 'Traditional', 'Granite mortar and pestle for grinding spices and pepper', 12000.00, 30, 8.0, '20 x 20 x 15'),
    ('Wooden Spoon Set (3 pieces)', 'Home & Kitchen', 'Kitchen Essentials', 'Traditional wooden spoons for stirring soups and stews', 3500.00, 100, 0.3, '35 x 8 x 3')
]

# Nigerian States and LGAs (representative sample)
NIGERIAN_STATES_LGA = {
    'Lagos': ['Ikeja', 'Victoria Island', 'Lekki', 'Surulere', 'Yaba', 'Ikoyi', 'Alimosho', 'Kosofe'],
    'Abuja': ['Wuse', 'Garki', 'Maitama', 'Asokoro', 'Utako', 'Gwarinpa', 'Kubwa', 'Nyanya'],
    'Kano': ['Municipal', 'Nassarawa', 'Fagge', 'Dala', 'Gwale', 'Tarauni', 'Ungogo', 'Kumbotso'],
    'Rivers': ['Port Harcourt', 'Obio-Akpor', 'Eleme', 'Ikwerre', 'Oyigbo', 'Okrika', 'Degema', 'Bonny'],
    'Oyo': ['Ibadan North', 'Ibadan South-West', 'Egbeda', 'Akinyele', 'Lagelu', 'Oluyole', 'Ona Ara', 'Ido'],
    'Kaduna': ['Kaduna North', 'Kaduna South', 'Chikun', 'Igabi', 'Ikara', 'Jaba', 'Jema\'a', 'Kachia'],
    'Anambra': ['Awka', 'Onitsha North', 'Onitsha South', 'Nnewi North', 'Nnewi South', 'Idemili North', 'Idemili South', 'Aguata'],
    'Delta': ['Warri North', 'Warri South', 'Udu', 'Uvwie', 'Sapele', 'Okpe', 'Oshimili North', 'Oshimili South'],
    'Enugu': ['Enugu North', 'Enugu South', 'Enugu East', 'Nkanu East', 'Nkanu West', 'Oji River', 'Ezeagu', 'Igbo Etiti'],
    'Edo': ['Oredo', 'Egor', 'Ikpoba-Okha', 'Orhionmwon', 'Uhunmwonde', 'Ovia North-East', 'Ovia South-West', 'Owan East'],
    'Kwara': ['Ilorin East', 'Ilorin West', 'Ilorin South', 'Asa', 'Baruten', 'Edu', 'Ekiti', 'Ifelodun'],
    'Imo': ['Owerri Municipal', 'Owerri North', 'Owerri West', 'Aboh Mbaise', 'Ahiazu Mbaise', 'Ehime Mbano', 'Ezinihitte', 'Ideato North'],
    'Abia': ['Umuahia North', 'Umuahia South', 'Aba North', 'Aba South', 'Arochukwu', 'Bende', 'Ikwuano', 'Isiala Ngwa North'],
    'Akwa Ibom': ['Uyo', 'Ikot Ekpene', 'Eket', 'Abak', 'Eastern Obolo', 'Enna', 'Essien Udim', 'Etim Ekpo'],
    'Cross River': ['Calabar Municipal', 'Calabar South', 'Akpabuyo', 'Bakassi', 'Bekwarra', 'Biase', 'Boki', 'Etung'],
    'Bayelsa': ['Yenagoa', 'Kolokuma/Opokuma', 'Nembe', 'Ogbia', 'Sagbama', 'Southern Ijaw', 'Ekeremor', 'Brass'],
    'Plateau': ['Jos North', 'Jos South', 'Jos East', 'Barkin Ladi', 'Bassa', 'Bokkos', 'Kanam', 'Kanke'],
    'Benue': ['Makurdi', 'Gboko', 'Katsina-Ala', 'Konshisha', 'Kwande', 'Logo', 'Obi', 'Ogbadibo'],
    'Niger': ['Minna', 'Suleja', 'Bida', 'Kontagora', 'Agaie', 'Agwara', 'Bida', 'Borgu'],
    'Sokoto': ['Sokoto North', 'Sokoto South', 'Binji', 'Bodinga', 'Dange Shuni', 'Gada', 'Goronyo', 'Gudu'],
    'Kebbi': ['Birnin Kebbi', 'Aleiro', 'Arewa Dandi', 'Argungu', 'Augie', 'Bagudo', 'Bunza', 'Dandi'],
    'Zamfara': ['Gusau', 'Anka', 'Bakura', 'Birnin Magaji/Kiyaw', 'Bukkuyum', 'Bungudu', 'Gummi', 'Kaura Namoda']
}

# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def generate_phone_number() -> str:
    """Generate realistic Nigerian phone number matching database constraint"""
    # Constraint: ^(\+234|0)[7-9][0-1][0-9]{8}$
    network = random.choice(list(NETWORK_PREFIXES.keys()))
    prefix = random.choice(NETWORK_PREFIXES[network])  # Already matches first 4 digits
    # Generate remaining 7 digits to complete the 11-digit number (4 prefix + 7 = 11)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix}{suffix}"

def validate_email_format(email: str) -> bool:
    """Validate email format against database constraint"""
    import re
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return bool(re.match(pattern, email))

def generate_safe_email(first_name: str, surname: str) -> str:
    """Generate email that passes database validation"""
    # Clean names - remove special characters and ensure valid format
    clean_first = re.sub(r'[^A-Za-z0-9]', '', first_name.lower())
    clean_surname = re.sub(r'[^A-Za-z0-9]', '', surname.lower())

    # Ensure minimum length
    if len(clean_first) < 2:
        clean_first = f"user{random.randint(100, 999)}"
    if len(clean_surname) < 2:
        clean_surname = f"lastname{random.randint(100, 999)}"

    # Generate with unique suffix
    suffix = random.randint(1000, 9999)
    domain = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])
    email = f"{clean_first}.{clean_surname}{suffix}@{domain}"

    # Validate and fix if needed
    if not validate_email_format(email):
        email = f"user{suffix}@{domain}"

    return email

def calculate_account_tier(total_spent: float, order_count: int) -> str:
    """Calculate account tier based on spending and orders"""
    for tier in ['Platinum', 'Gold', 'Silver', 'Bronze']:
        criteria = TIER_CRITERIA[tier]
        if (total_spent >= criteria['min_spent'] and
            total_spent <= criteria['max_spent'] and
            order_count >= criteria['min_orders']):
            return tier
    return 'Bronze'

def select_random_timestamp(stage_name: str) -> datetime:
    """Select random timestamp within business growth stage"""
    stage = BUSINESS_GROWTH_STAGES[stage_name]
    start = stage['start_date']
    end = stage['end_date']
    time_diff = end - start
    random_seconds = random.randint(0, int(time_diff.total_seconds()))
    return start + timedelta(seconds=random_seconds)

def ensure_database_schema():
    """Ensure database has required schema and RBAC columns"""
    logger.info("🔧 Ensuring database schema is ready...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = True

        with conn.cursor() as cursor:
            # Create enums if they don't exist
            cursor.execute("""
                DO $$ BEGIN
                    CREATE TYPE user_role_enum AS ENUM ('customer', 'support_agent', 'admin', 'super_admin');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)

            cursor.execute("""
                DO $$ BEGIN
                    CREATE TYPE account_status_enum AS ENUM ('active', 'inactive', 'suspended', 'deactivated');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)

            # Add RBAC columns to customers table if they don't exist
            rbac_columns = [
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS user_role user_role_enum DEFAULT 'customer'",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT FALSE",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}'::jsonb",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS account_status account_status_enum DEFAULT 'active'",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
                "ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_login TIMESTAMP"
            ]

            for column_sql in rbac_columns:
                cursor.execute(column_sql)

            # Add product_id to orders table if it doesn't exist
            cursor.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS product_id INTEGER")

            # Create missing partitions for 2023 (needed for historical data)
            logger.info("📅 Creating missing partitions for 2023...")
            partitions_2023 = [
                "CREATE TABLE IF NOT EXISTS orders_2023_01 PARTITION OF orders FOR VALUES FROM ('2023-01-01') TO ('2023-02-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_02 PARTITION OF orders FOR VALUES FROM ('2023-02-01') TO ('2023-03-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_03 PARTITION OF orders FOR VALUES FROM ('2023-03-01') TO ('2023-04-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_04 PARTITION OF orders FOR VALUES FROM ('2023-04-01') TO ('2023-05-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_05 PARTITION OF orders FOR VALUES FROM ('2023-05-01') TO ('2023-06-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_06 PARTITION OF orders FOR VALUES FROM ('2023-06-01') TO ('2023-07-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_07 PARTITION OF orders FOR VALUES FROM ('2023-07-01') TO ('2023-08-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_08 PARTITION OF orders FOR VALUES FROM ('2023-08-01') TO ('2023-09-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_09 PARTITION OF orders FOR VALUES FROM ('2023-09-01') TO ('2023-10-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_10 PARTITION OF orders FOR VALUES FROM ('2023-10-01') TO ('2023-11-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_11 PARTITION OF orders FOR VALUES FROM ('2023-11-01') TO ('2023-12-01')",
                "CREATE TABLE IF NOT EXISTS orders_2023_12 PARTITION OF orders FOR VALUES FROM ('2023-12-01') TO ('2024-01-01')"
            ]

            for partition_sql in partitions_2023:
                cursor.execute(partition_sql)

            # Create trigger function for staff flags
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_staff_flags()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.is_staff := NEW.user_role IN ('support_agent', 'admin', 'super_admin');
                    NEW.is_admin := NEW.user_role IN ('admin', 'super_admin');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)

            # Create trigger
            cursor.execute("""
                DROP TRIGGER IF EXISTS trigger_update_staff_flags ON customers;
                CREATE TRIGGER trigger_update_staff_flags
                    BEFORE INSERT OR UPDATE OF user_role ON customers
                    FOR EACH ROW EXECUTE FUNCTION update_staff_flags();
            """)

        conn.close()
        logger.info("✅ Database schema verified and updated")
        return True

    except Exception as e:
        logger.error(f"❌ Schema setup failed: {e}")
        return False

# =====================================================================
# DATA GENERATION FUNCTIONS
# =====================================================================

def generate_nigerian_customer(stage_name: str) -> Dict:
    """Generate ethnically authentic Nigerian customer"""
    # Nigerian ethnic groups and naming patterns
    ethnic_groups = {
        'Yoruba': {
            'states': ['Lagos', 'Oyo', 'Osun', 'Ogun', 'Ondo', 'Ekiti'],
            'first_names_male': ['Adebayo', 'Olumide', 'Babatunde', 'Kehinde', 'Taiwo', 'Folarin', 'Adedayo'],
            'first_names_female': ['Adunni', 'Folake', 'Bukola', 'Funmi', 'Yemi', 'Tope', 'Kemi'],
            'surnames': ['Okonkwo', 'Adebayo', 'Ogundimu', 'Adekunle', 'Ogundipe', 'Falana', 'Adeyemi']
        },
        'Igbo': {
            'states': ['Anambra', 'Imo', 'Abia', 'Enugu', 'Ebonyi'],
            'first_names_male': ['Chidi', 'Emeka', 'Ikenna', 'Obinna', 'Kelechi', 'Chigozie', 'Nnamdi'],
            'first_names_female': ['Chioma', 'Adanna', 'Ngozi', 'Ifeoma', 'Chinwe', 'Amaka', 'Obioma'],
            'surnames': ['Okechukwu', 'Okafor', 'Eze', 'Nwankwo', 'Obiora', 'Nwosu', 'Onwudiwe']
        },
        'Hausa': {
            'states': ['Kano', 'Kaduna', 'Sokoto', 'Kebbi', 'Zamfara'],
            'first_names_male': ['Musa', 'Ibrahim', 'Umar', 'Yusuf', 'Ahmad', 'Abdullahi', 'Mohammed'],
            'first_names_female': ['Fatima', 'Aisha', 'Zainab', 'Halima', 'Hauwa', 'Mariam', 'Safiya'],
            'surnames': ['Ibrahim', 'Abdullahi', 'Mohammed', 'Usman', 'Bello', 'Aliyu', 'Garba']
        },
        'Niger_Delta': {
            'states': ['Rivers', 'Bayelsa', 'Delta', 'Cross River', 'Akwa Ibom'],
            'first_names_male': ['Edet', 'Bassey', 'Godwin', 'Samuel', 'David', 'Emmanuel', 'Victor'],
            'first_names_female': ['Grace', 'Joy', 'Peace', 'Faith', 'Love', 'Mercy', 'Hope'],
            'surnames': ['Edem', 'Bassey', 'Okon', 'Udoh', 'Akpan', 'Williams', 'Johnson']
        },
        'Middle_Belt': {
            'states': ['Plateau', 'Benue', 'Niger', 'Kwara'],
            'first_names_male': ['Daniel', 'Joseph', 'Paul', 'Peter', 'John', 'James', 'Michael'],
            'first_names_female': ['Mary', 'Elizabeth', 'Sarah', 'Ruth', 'Esther', 'Hannah', 'Rebecca'],
            'surnames': ['Danjuma', 'Yakubu', 'Gyang', 'Musa', 'Adamu', 'Joshua', 'Emmanuel']
        }
    }

    # Select ethnic group and corresponding data
    ethnicity = random.choice(list(ethnic_groups.keys()))
    ethnic_data = ethnic_groups[ethnicity]

    # Generate name
    gender = random.choice(['male', 'female'])
    if gender == 'male':
        first_name = random.choice(ethnic_data['first_names_male'])
    else:
        first_name = random.choice(ethnic_data['first_names_female'])

    surname = random.choice(ethnic_data['surnames'])
    full_name = f"{first_name} {surname}"

    # Select state and LGA
    state = random.choice(ethnic_data['states'])
    lga = random.choice(NIGERIAN_STATES_LGA.get(state, ['Central']))

    # Generate contact info with database-safe email and phone
    email = generate_safe_email(first_name, surname)
    phone = generate_phone_number()

    # Generate address
    street_number = random.randint(1, 999)
    street_names = ['Adeniji Street', 'Lagos Road', 'Ibrahim Way', 'Market Street', 'Unity Road', 'Independence Avenue']
    address = f"{street_number} {random.choice(street_names)}, {lga}, {state} State"

    # Generate customer activity based on stage
    stage = BUSINESS_GROWTH_STAGES[stage_name]
    registration_date = select_random_timestamp(stage_name)

    # Calculate customer profile
    days_as_customer = (datetime.now() - registration_date).days
    days_as_customer = max(days_as_customer, 1)

    # Order patterns based on ethnicity and stage - TIER-AWARE GENERATION
    base_monthly_orders = random.uniform(0.5, 3.0) * stage['order_frequency_multiplier']

    # Pre-determine tier-appropriate behavior
    months_active = max(days_as_customer / 30, 0.5)

    # Different order patterns by intended tier (creating realistic data distribution)
    tier_probability = random.random()
    if tier_probability < 0.45:  # 45% Bronze customers (low activity)
        order_multiplier = random.uniform(0.3, 0.8)
        spend_multiplier = random.uniform(0.2, 0.6)
        target_tier = 'Bronze'
    elif tier_probability < 0.75:  # 30% Silver customers (moderate activity)
        order_multiplier = random.uniform(0.8, 1.5)
        spend_multiplier = random.uniform(0.6, 1.2)
        target_tier = 'Silver'
    elif tier_probability < 0.92:  # 17% Gold customers (high activity)
        order_multiplier = random.uniform(1.5, 2.5)
        spend_multiplier = random.uniform(1.2, 2.0)
        target_tier = 'Gold'
    else:  # 8% Platinum customers (very high activity)
        order_multiplier = random.uniform(2.5, 4.0)
        spend_multiplier = random.uniform(2.0, 3.5)
        target_tier = 'Platinum'

    # Calculate order count based on tier
    order_count = max(int(months_active * base_monthly_orders * order_multiplier), 1)

    # Spending patterns adjusted for tier
    base_monthly_spend = random.uniform(8000, 50000) * stage['customer_multiplier'] * spend_multiplier
    total_spent = months_active * base_monthly_spend
    total_spent = max(total_spent, 3000)

    # Ensure spending aligns with target tier
    if target_tier == 'Bronze':
        total_spent = min(total_spent, random.uniform(50000, 98000))
    elif target_tier == 'Silver':
        total_spent = max(total_spent, random.uniform(100000, 120000))
        total_spent = min(total_spent, random.uniform(400000, 498000))
    elif target_tier == 'Gold':
        total_spent = max(total_spent, random.uniform(500000, 600000))
        total_spent = min(total_spent, random.uniform(1500000, 1980000))
    else:  # Platinum
        total_spent = max(total_spent, random.uniform(2000000, 2500000))

    # Calculate tier (should match target tier now)
    account_tier = calculate_account_tier(total_spent, order_count)

    # Generate preferences
    category_preferences = {
        'Yoruba': ['Electronics', 'Fashion', 'Beauty'],
        'Igbo': ['Electronics', 'Computing', 'Automotive'],
        'Hausa': ['Fashion', 'Food Items', 'Beauty'],
        'Niger_Delta': ['Electronics', 'Automotive', 'Fashion'],
        'Middle_Belt': ['Books', 'Electronics', 'Food Items']
    }

    preferences = {
        'language': 'English',
        'preferred_categories': category_preferences.get(ethnicity, ['Electronics', 'Fashion']),
        'notifications': {'email': True, 'sms': random.choice([True, False])},
        'delivery_preference': random.choice(['Home Delivery', 'Pickup Station']),
        'ethnicity': ethnicity
    }

    return {
        'name': full_name,
        'email': email,
        'phone': phone,
        'state': state,
        'lga': lga,
        'address': address,
        'account_tier': account_tier,
        'preferences': json.dumps(preferences),
        'created_at': registration_date,
        'user_role': 'customer',
        'is_staff': False,
        'is_admin': False,
        'permissions': json.dumps({'can_view_own_orders': True, 'can_edit_own_profile': True}),
        'account_status': 'active',
        'password_hash': None,
        'last_login': None,
        # Additional metadata for order generation
        'ethnicity': ethnicity,
        'days_as_customer': days_as_customer,
        'order_count': order_count,
        'total_spent': total_spent
    }

def generate_customer_orders(customer: Dict, products_by_category: Dict) -> List[Dict]:
    """Generate realistic orders for a customer"""
    orders = []

    remaining_budget = customer['total_spent']
    num_orders = customer['order_count']

    preferences = json.loads(customer['preferences'])
    preferred_categories = preferences.get('preferred_categories', ['Electronics', 'Fashion'])

    # Payment method preferences by tier and ethnicity
    tier = customer['account_tier']
    ethnicity = customer['ethnicity']

    if tier in ['Gold', 'Platinum'] and ethnicity in ['Yoruba', 'Igbo']:
        payment_weights = [0.1, 0.2, 0.5, 0.2]  # POD, Bank, Card, RaqibTech
    elif ethnicity == 'Hausa':
        payment_weights = [0.6, 0.3, 0.08, 0.02]
    else:
        payment_weights = [0.4, 0.3, 0.25, 0.05]

    payment_methods = ['Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay']

    # Generate orders with realistic spacing
    for i in range(num_orders):
        # Calculate order date (spread throughout customer lifetime)
        days_ago = random.randint(1, customer['days_as_customer'])
        order_date = datetime.now() - timedelta(days=days_ago)

        # Calculate order amount
        if i == num_orders - 1:  # Last order gets remaining budget
            order_amount = max(remaining_budget, 2000)
        else:
            order_amount = remaining_budget / (num_orders - i) * random.uniform(0.5, 1.5)
            order_amount = max(order_amount, 2000)

        remaining_budget -= order_amount
        remaining_budget = max(remaining_budget, 0)

        # Select category and product
        category = random.choice(preferred_categories)
        if category not in products_by_category or not products_by_category[category]:
            category = random.choice(list(products_by_category.keys()))

        # Select product within price range
        suitable_products = [p for p in products_by_category[category]
                           if p['price'] <= order_amount * 1.2]

        if not suitable_products:
            suitable_products = products_by_category[category]

        product = random.choice(suitable_products)

        # Determine order status based on date
        days_since_order = (datetime.now() - order_date).days

        if days_since_order > 10:
            status = random.choices(['Delivered', 'Returned'], weights=[0.92, 0.08])[0]
            if status == 'Delivered':
                delivery_date = order_date.date() + timedelta(days=random.randint(1, 7))
            else:
                delivery_date = order_date.date() + timedelta(days=random.randint(1, 5))
        elif days_since_order > 3:
            status = random.choices(['Delivered', 'Processing'], weights=[0.8, 0.2])[0]
            if status == 'Delivered':
                delivery_date = order_date.date() + timedelta(days=random.randint(1, 3))
            else:
                delivery_date = datetime.now().date() + timedelta(days=random.randint(1, 5))
        else:
            status = random.choices(['Processing', 'Pending'], weights=[0.7, 0.3])[0]
            delivery_date = datetime.now().date() + timedelta(days=random.randint(1, 7))

        # Don't use 'Pending' if delivery_date exceeds current date
        if status == 'Pending' and delivery_date > date(2025, 6, 9):
            status = 'Processing'
            delivery_date = date(2025, 6, 9)

        payment_method = random.choices(payment_methods, weights=payment_weights)[0]

        # Ensure order amount is always positive (database constraint requirement)
        final_amount = max(round(order_amount, 2), 1.0)  # Minimum ₦1.00

        orders.append({
            'customer_id': None,  # Will be set when customer is inserted
            'order_status': status,
            'payment_method': payment_method,
            'total_amount': final_amount,
            'delivery_date': delivery_date,
            'product_category': category,
            'product_id': product['product_id'],
            'created_at': order_date
        })

    return orders

def load_products_by_category() -> Dict:
    """Load products grouped by category"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT product_id, product_name, category, price FROM products ORDER BY category")
            products = cursor.fetchall()

        conn.close()

        products_by_category = {}
        for product_id, name, category, price in products:
            if category not in products_by_category:
                products_by_category[category] = []
            products_by_category[category].append({
                'product_id': product_id,
                'name': name,
                'price': float(price)
            })

        return products_by_category

    except Exception as e:
        logger.error(f"❌ Failed to load products: {e}")
        return {}

def insert_nigerian_food_products():
    """Insert Nigerian food products into database - REPLACED WITH COMPREHENSIVE PRODUCTS"""
    return insert_comprehensive_products()

def create_comprehensive_product_catalog():
    """Create comprehensive product catalog for all categories"""

    # Nigerian food products (existing)
    food_products = NIGERIAN_FOOD_PRODUCTS

    # Electronics products
    electronics_products = [
        ('Samsung Galaxy A54 5G', 'Electronics', 'Samsung', 'Android smartphone with 5G connectivity, 128GB storage', 450000.00, 50, 0.2, '15 x 7 x 1'),
        ('iPhone 14 128GB', 'Electronics', 'Apple', 'Latest iPhone with advanced camera system', 1200000.00, 30, 0.17, '14 x 7 x 1'),
        ('Sony 55" 4K Smart TV', 'Electronics', 'Sony', '4K Ultra HD Android TV with smart features', 1100000.00, 15, 18.5, '123 x 71 x 8'),
        ('LG 43" LED TV', 'Electronics', 'LG', 'Full HD LED television with built-in apps', 380000.00, 40, 12.0, '97 x 57 x 8'),
        ('JBL Bluetooth Speaker', 'Electronics', 'JBL', 'Portable wireless speaker with deep bass', 45000.00, 80, 0.6, '18 x 10 x 8'),
        ('Canon EOS 2000D Camera', 'Electronics', 'Canon', 'DSLR camera perfect for photography enthusiasts', 320000.00, 12, 1.2, '13 x 10 x 8'),
        ('Samsung 65" QLED TV', 'Electronics', 'Samsung', 'Premium QLED TV with quantum dot technology', 1450000.00, 8, 22.0, '145 x 83 x 8'),
        ('Xiaomi Redmi Note 12', 'Electronics', 'Xiaomi', 'Budget-friendly smartphone with great features', 185000.00, 70, 0.18, '16 x 7 x 1'),
        ('PlayStation 5 Console', 'Electronics', 'Sony', 'Next-gen gaming console with 4K gaming', 850000.00, 15, 4.5, '39 x 26 x 10'),
        ('Bluetooth Headphones', 'Electronics', 'Beats', 'Wireless over-ear headphones with noise cancellation', 175000.00, 45, 0.3, '20 x 18 x 8')
    ]

    # Computing products
    computing_products = [
        ('HP Pavilion Laptop', 'Computing', 'HP', 'Intel Core i5, 8GB RAM, 512GB SSD laptop', 850000.00, 25, 2.1, '36 x 25 x 2'),
        ('Dell Inspiron Desktop', 'Computing', 'Dell', 'Desktop computer for home and office use', 650000.00, 20, 8.5, '35 x 17 x 35'),
        ('Apple iPad 10th Gen', 'Computing', 'Apple', 'Versatile tablet for work and entertainment', 720000.00, 25, 0.48, '25 x 17 x 1'),
        ('MacBook Air M2', 'Computing', 'Apple', 'Lightweight laptop with M2 chip', 1850000.00, 10, 1.24, '30 x 21 x 1'),
        ('Gaming PC Setup', 'Computing', 'Custom Build', 'High-performance gaming computer with RTX graphics', 1200000.00, 12, 15.0, '45 x 20 x 40'),
        ('Microsoft Surface Pro', 'Computing', 'Microsoft', '2-in-1 tablet laptop for professionals', 980000.00, 18, 0.77, '29 x 21 x 1'),
        ('Wireless Keyboard & Mouse', 'Computing', 'Logitech', 'Ergonomic wireless keyboard and mouse combo', 35000.00, 60, 0.8, '45 x 20 x 5'),
        ('External Hard Drive 2TB', 'Computing', 'Seagate', 'Portable external storage for backup', 85000.00, 40, 0.23, '12 x 8 x 2'),
        ('USB-C Hub', 'Computing', 'Anker', 'Multi-port USB-C hub with HDMI and USB ports', 28000.00, 80, 0.15, '12 x 5 x 2'),
        ('Webcam HD 1080p', 'Computing', 'Logitech', 'High-definition webcam for video calls', 45000.00, 55, 0.25, '10 x 6 x 6')
    ]

    # Fashion products
    fashion_products = [
        ('Adidas Originals Sneakers', 'Fashion', 'Adidas', 'Classic three-stripe sneakers for everyday wear', 65000.00, 100, 0.8, '35 x 22 x 12'),
        ('Nike Air Force 1', 'Fashion', 'Nike', 'Iconic basketball shoes in white colorway', 85000.00, 80, 0.9, '35 x 22 x 12'),
        ('Ankara Print Dress', 'Fashion', 'African Prints', 'Beautiful traditional Nigerian Ankara dress', 25000.00, 60, 0.3, '50 x 30 x 2'),
        ('Gucci Polo Shirt', 'Fashion', 'Gucci', 'Premium cotton polo shirt with logo', 180000.00, 20, 0.2, '25 x 20 x 2'),
        ('Levi\'s 501 Jeans', 'Fashion', 'Levi\'s', 'Classic straight-leg denim jeans', 45000.00, 120, 0.6, '30 x 25 x 3'),
        ('Traditional Agbada', 'Fashion', 'Nigerian Tailors', 'Elegant traditional Nigerian men\'s wear', 95000.00, 15, 0.8, '60 x 40 x 5'),
        ('Corporate Blazer', 'Fashion', 'Business Attire', 'Professional blazer for office wear', 55000.00, 40, 0.5, '50 x 35 x 3'),
        ('Gele Headtie', 'Fashion', 'Textile Co', 'Traditional Nigerian headwrap for women', 15000.00, 200, 0.1, '120 x 25 x 1'),
        ('Italian Leather Shoes', 'Fashion', 'Premium Leather', 'Handcrafted leather dress shoes', 125000.00, 30, 1.2, '32 x 22 x 12'),
        ('African Print Handbag', 'Fashion', 'Lagos Bags', 'Stylish handbag with African print design', 35000.00, 70, 0.4, '30 x 25 x 15')
    ]

    # Beauty products
    beauty_products = [
        ('Shea Butter Body Cream', 'Beauty', 'Ori Naturals', 'Pure Nigerian shea butter moisturizer', 8500.00, 150, 0.25, '15 x 8 x 8'),
        ('Black Soap Face Wash', 'Beauty', 'Dudu Osun', 'Traditional African black soap cleanser', 3500.00, 200, 0.15, '10 x 6 x 3'),
        ('Coconut Oil Hair Treatment', 'Beauty', 'Tropical Care', 'Virgin coconut oil for hair and skin', 12000.00, 100, 0.5, '15 x 8 x 15'),
        ('Foundation Makeup', 'Beauty', 'Fenty Beauty', 'Full coverage foundation for all skin tones', 28000.00, 80, 0.05, '8 x 3 x 12'),
        ('Lipstick Set', 'Beauty', 'MAC Cosmetics', 'Set of 3 premium lipsticks in bold colors', 45000.00, 60, 0.1, '12 x 8 x 3'),
        ('Perfume - Oud Blend', 'Beauty', 'Arabian Scents', 'Luxury oud perfume with floral notes', 85000.00, 40, 0.1, '12 x 5 x 5'),
        ('Hair Relaxer Kit', 'Beauty', 'Dark & Lovely', 'Complete hair relaxing system', 15000.00, 90, 0.4, '20 x 15 x 8'),
        ('Face Mask - Honey Oat', 'Beauty', 'Glow Naturals', 'Nourishing face mask with natural ingredients', 6500.00, 120, 0.08, '10 x 10 x 2'),
        ('Body Lotion - Cocoa Butter', 'Beauty', 'Palmer\'s', 'Moisturizing lotion with cocoa butter', 9500.00, 130, 0.35, '20 x 8 x 8'),
        ('Nail Polish Set', 'Beauty', 'Essie', 'Collection of 5 trendy nail polish colors', 18000.00, 70, 0.2, '15 x 10 x 8')
    ]

    # Automotive products
    automotive_products = [
        ('Car Engine Oil 5L', 'Automotive', 'Mobil 1', 'Synthetic motor oil for optimal engine performance', 25000.00, 60, 4.5, '25 x 18 x 18'),
        ('Car Battery 12V', 'Automotive', 'Exide', 'Reliable car battery with 2-year warranty', 65000.00, 30, 18.0, '24 x 17 x 19'),
        ('Michelin Tire 195/65R15', 'Automotive', 'Michelin', 'Premium tire with excellent grip and durability', 85000.00, 40, 8.5, '62 x 62 x 19'),
        ('Car Air Freshener', 'Automotive', 'Little Trees', 'Long-lasting car air freshener in various scents', 2500.00, 200, 0.05, '10 x 7 x 1'),
        ('Brake Pads Set', 'Automotive', 'Bosch', 'High-quality brake pads for safe driving', 35000.00, 50, 2.0, '20 x 15 x 8'),
        ('Car Phone Holder', 'Automotive', 'iOttie', 'Dashboard phone mount for hands-free driving', 8500.00, 100, 0.3, '15 x 10 x 8'),
        ('Jump Starter Kit', 'Automotive', 'Anker', 'Portable car jump starter with USB charging', 45000.00, 25, 1.5, '25 x 15 x 8'),
        ('Car Floor Mats', 'Automotive', 'WeatherTech', 'All-weather floor protection mats', 28000.00, 60, 3.0, '60 x 40 x 3'),
        ('Dash Cam HD', 'Automotive', 'Nextbase', 'High-definition dashboard camera for security', 75000.00, 35, 0.2, '12 x 8 x 5'),
        ('Car Tool Kit', 'Automotive', 'Craftsman', 'Essential tools for basic car maintenance', 38000.00, 40, 2.5, '35 x 25 x 10')
    ]

    # Books
    books_products = [
        ('Things Fall Apart', 'Books', 'Chinua Achebe', 'Classic Nigerian novel about colonial impact', 8500.00, 100, 0.3, '20 x 13 x 2'),
        ('Purple Hibiscus', 'Books', 'Chimamanda Adichie', 'Award-winning novel by Nigerian author', 9500.00, 80, 0.35, '20 x 13 x 2'),
        ('The Beautiful Ones Are Not Yet Born', 'Books', 'Ayi Kwei Armah', 'African literature masterpiece', 7500.00, 60, 0.28, '19 x 12 x 2'),
        ('Python Programming for Beginners', 'Books', 'Tech Books Nigeria', 'Learn Python programming from basics', 15000.00, 50, 0.6, '23 x 18 x 3'),
        ('Business Strategy in Nigeria', 'Books', 'Lagos Business Press', 'Guide to successful business in Nigeria', 12000.00, 40, 0.5, '22 x 15 x 2'),
        ('Yoruba Language Dictionary', 'Books', 'University Press', 'Comprehensive Yoruba-English dictionary', 18000.00, 30, 0.8, '25 x 18 x 4'),
        ('Islamic Studies Textbook', 'Books', 'Islamic Publications', 'Complete guide to Islamic teachings', 13000.00, 45, 0.7, '24 x 17 x 3'),
        ('Nigerian History', 'Books', 'Educational Publishers', 'Comprehensive history of Nigeria', 16000.00, 35, 0.9, '25 x 18 x 4'),
        ('Cooking with Nigerian Spices', 'Books', 'Culinary Arts Press', 'Traditional and modern Nigerian recipes', 11000.00, 70, 0.4, '21 x 15 x 2'),
        ('Financial Literacy Guide', 'Books', 'Money Matters Nigeria', 'Personal finance management in Nigeria', 14000.00, 55, 0.45, '22 x 16 x 2')
    ]

    return food_products + electronics_products + computing_products + fashion_products + beauty_products + automotive_products + books_products

def insert_comprehensive_products():
    """Insert comprehensive product catalog for all categories"""
    logger.info("🛍️ Inserting comprehensive product catalog...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        with conn.cursor() as cursor:
            # Clear existing products to avoid duplicates
            cursor.execute("DELETE FROM products")

            # Get comprehensive product catalog
            all_products = create_comprehensive_product_catalog()

            # Insert all products
            inserted_count = 0
            for product_data in all_products:
                try:
                    cursor.execute("""
                        INSERT INTO products (product_name, category, brand, description, price, stock_quantity, weight_kg, dimensions_cm)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, product_data)
                    inserted_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Failed to insert product {product_data[0]}: {e}")

            conn.commit()

            # Report categories inserted
            cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY category")
            category_counts = cursor.fetchall()

            logger.info(f"✅ Successfully inserted {inserted_count} products across {len(category_counts)} categories:")
            for category, count in category_counts:
                logger.info(f"   📦 {category}: {count} products")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to insert products: {e}")
        return False

def insert_staff_accounts():
    """Insert RBAC staff accounts"""
    logger.info("👨‍💼 Inserting RBAC staff accounts...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        with conn.cursor() as cursor:
            staff_inserted = 0

            for role_type, accounts in STAFF_ACCOUNTS.items():
                for staff in accounts:
                    try:
                        cursor.execute("""
                            INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences, created_at,
                                                 user_role, is_staff, is_admin, permissions, account_status, password_hash)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (email) DO UPDATE SET
                                user_role = EXCLUDED.user_role,
                                password_hash = EXCLUDED.password_hash,
                                account_status = EXCLUDED.account_status
                        """, (
                            staff['name'], staff['email'], staff['phone'], staff['state'], staff['lga'],
                            f"RaqibTech Office, {staff['lga']}, {staff['state']} State",
                            'Platinum',
                            json.dumps({
                                'language': 'English',
                                'preferred_categories': ['All Categories'],
                                'notifications': {'email': True, 'sms': True},
                                'delivery_preference': 'Office Delivery'
                            }),
                            datetime.now(),
                            staff['user_role'],
                            True,
                            staff['user_role'] in ['admin', 'super_admin'],
                            json.dumps({
                                'can_view_customers': True,
                                'can_edit_orders': staff['user_role'] != 'support_agent',
                                'can_access_analytics': True,
                                'can_manage_users': staff['user_role'] in ['admin', 'super_admin'],
                                'can_manage_system': staff['user_role'] == 'super_admin'
                            }),
                            'active',
                            hash_password(staff['password'])
                        ))
                        staff_inserted += 1

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to insert staff {staff['name']}: {e}")

            conn.commit()
            logger.info(f"✅ Successfully inserted {staff_inserted} staff accounts")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to insert staff accounts: {e}")
        return False

# =====================================================================
# MAIN EXECUTION FUNCTIONS
# =====================================================================

def generate_fresh_data(num_customers: int = 1000, num_orders_per_customer: int = 3):
    """Generate fresh Nigerian e-commerce data"""
    logger.info(f"🇳🇬 Generating fresh Nigerian e-commerce data...")
    logger.info(f"   👥 Target customers: {num_customers}")
    logger.info(f"   📦 Target orders per customer: ~{num_orders_per_customer}")

    try:
        # Ensure schema is ready
        if not ensure_database_schema():
            return False

        # Insert comprehensive products
        if not insert_comprehensive_products():
            return False

        # Insert staff accounts
        if not insert_staff_accounts():
            return False

        # Load products for order generation
        products_by_category = load_products_by_category()
        if not products_by_category:
            logger.error("❌ No products available for order generation")
            return False

        # Clear existing customer data for fresh generation (customer_id starts from 1)
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        with conn.cursor() as cursor:
            logger.info("🧹 Clearing existing customer and order data for fresh generation...")
            cursor.execute("DELETE FROM orders WHERE customer_id IN (SELECT customer_id FROM customers WHERE user_role = 'customer')")
            cursor.execute("DELETE FROM customers WHERE user_role = 'customer'")

            # Reset sequence to start after existing staff accounts
            cursor.execute("SELECT MAX(customer_id) FROM customers")
            max_existing_id = cursor.fetchone()[0] or 0
            next_id = max_existing_id + 1
            cursor.execute(f"ALTER SEQUENCE customers_customer_id_seq RESTART WITH {next_id}")
            conn.commit()
            logger.info(f"✅ Existing customer data cleared, customer_id will start from {next_id}")

        conn.close()

        # Generate customers across business growth stages
        all_customers = []

        for stage_name, stage_info in BUSINESS_GROWTH_STAGES.items():
            stage_customers = int(num_customers * stage_info['weight'])
            logger.info(f"   🏢 {stage_name}: {stage_customers} customers")

            for _ in range(stage_customers):
                customer = generate_nigerian_customer(stage_name)
                all_customers.append(customer)

        # Sort customers by registration date for chronological customer_id assignment
        all_customers.sort(key=lambda x: x['created_at'])
        logger.info(f"✅ Generated {len(all_customers)} customers, sorted chronologically")

        # Insert customers and orders into database
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False

        customers_inserted = 0
        orders_inserted = 0

        try:
            with conn.cursor() as cursor:
                # Process customers with their associated orders
                for customer_idx, customer in enumerate(all_customers):
                    try:
                        # Remove metadata fields before insert
                        customer_data = {k: v for k, v in customer.items()
                                       if k not in ['ethnicity', 'days_as_customer', 'order_count', 'total_spent']}

                        # PRE-INSERTION VALIDATION
                        # Validate email format
                        if not validate_email_format(customer_data['email']):
                            logger.error(f"❌ Invalid email format for {customer.get('name', 'Unknown')}: {customer_data['email']}")
                            customer_data['email'] = generate_safe_email(customer['name'].split()[0], customer['name'].split()[-1])
                            logger.info(f"✅ Generated new email: {customer_data['email']}")

                        # Validate phone format (Nigerian constraint)
                        phone_pattern = r'^(\+234|0)[7-9][0-1][0-9]{8}$'
                        if not re.match(phone_pattern, customer_data['phone']):
                            logger.error(f"❌ Invalid phone format for {customer.get('name', 'Unknown')}: {customer_data['phone']}")
                            customer_data['phone'] = generate_phone_number()
                            logger.info(f"✅ Generated new phone: {customer_data['phone']}")

                        # Check for existing email to avoid duplicates
                        cursor.execute("SELECT COUNT(*) FROM customers WHERE email = %s", (customer_data['email'],))
                        if cursor.fetchone()[0] > 0:
                            # Generate new unique email
                            base_email = customer_data['email'].split('@')[0]
                            domain = customer_data['email'].split('@')[1]
                            for attempt in range(10):  # Try up to 10 times
                                new_suffix = random.randint(10000, 99999)
                                new_email = f"{base_email}{new_suffix}@{domain}"
                                cursor.execute("SELECT COUNT(*) FROM customers WHERE email = %s", (new_email,))
                                if cursor.fetchone()[0] == 0:
                                    customer_data['email'] = new_email
                                    break

                        # Insert customer
                        cursor.execute("""
                            INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences, created_at,
                                                 user_role, is_staff, is_admin, permissions, account_status, password_hash, last_login)
                            VALUES (%(name)s, %(email)s, %(phone)s, %(state)s, %(lga)s, %(address)s, %(account_tier)s::account_tier_enum,
                                    %(preferences)s::jsonb, %(created_at)s, %(user_role)s::user_role_enum, %(is_staff)s, %(is_admin)s,
                                    %(permissions)s::jsonb, %(account_status)s::account_status_enum, %(password_hash)s, %(last_login)s)
                            RETURNING customer_id
                        """, customer_data)

                        customer_id = cursor.fetchone()[0]
                        customers_inserted += 1

                        # Get this customer's orders (generated earlier)
                        customer_orders = generate_customer_orders(customer, products_by_category)

                        # Insert customer's orders
                        for order in customer_orders:
                            order['customer_id'] = customer_id

                            cursor.execute("""
                                INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date,
                                                  product_category, product_id, created_at)
                                VALUES (%(customer_id)s, %(order_status)s::order_status_enum, %(payment_method)s::payment_method_enum,
                                       %(total_amount)s, %(delivery_date)s, %(product_category)s, %(product_id)s, %(created_at)s)
                            """, order)
                            orders_inserted += 1

                    except psycopg2.IntegrityError as ie:
                        # Specific constraint violations
                        error_msg = str(ie)
                        if 'check_email_format' in error_msg:
                            logger.error(f"❌ Email format constraint failed for {customer.get('name', 'Unknown')}: {customer_data.get('email', 'N/A')}")
                        elif 'check_nigerian_phone' in error_msg:
                            logger.error(f"❌ Phone format constraint failed for {customer.get('name', 'Unknown')}: {customer_data.get('phone', 'N/A')}")
                        elif 'customers_email_key' in error_msg:
                            logger.error(f"❌ Email uniqueness constraint failed for {customer.get('name', 'Unknown')}: {customer_data.get('email', 'N/A')}")
                        elif 'check_positive_amount' in error_msg:
                            logger.error(f"❌ Order amount constraint failed for {customer.get('name', 'Unknown')}")
                        else:
                            logger.error(f"❌ Database integrity error for {customer.get('name', 'Unknown')}: {ie}")

                        # For the first customer failure, rollback entire transaction to avoid "aborted transaction" state
                        if customer_idx == 0:
                            logger.error("❌ First customer failed, rolling back entire transaction")
                            conn.rollback()
                            return False
                        continue

                    except psycopg2.Error as db_error:
                        logger.error(f"❌ Database error for customer {customer.get('name', 'Unknown')}: {db_error}")
                        # For the first customer failure, rollback entire transaction
                        if customer_idx == 0:
                            logger.error("❌ First customer failed, rolling back entire transaction")
                            conn.rollback()
                            return False
                        continue

                    except Exception as e:
                        logger.error(f"❌ General error for customer {customer.get('name', 'Unknown')}: {e}")
                        # For the first customer failure, rollback entire transaction
                        if customer_idx == 0:
                            logger.error("❌ First customer failed, rolling back entire transaction")
                            conn.rollback()
                            return False
                        continue

            conn.commit()

        except Exception as e:
            logger.error(f"❌ Critical error during data insertion: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

        logger.info(f"✅ Fresh data generation complete!")
        logger.info(f"   👥 Customers inserted: {customers_inserted}")
        logger.info(f"   📦 Orders inserted: {orders_inserted}")

        return True

    except Exception as e:
        logger.error(f"❌ Fresh data generation failed: {e}")
        return False

def augment_existing_data(additional_orders_per_customer: int = 2):
    """Augment existing customer data with new orders"""
    logger.info(f"📈 Augmenting existing data with {additional_orders_per_customer} orders per customer...")

    try:
        # Load existing customers
        conn = psycopg2.connect(**DATABASE_CONFIG)

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT customer_id, name, state, account_tier, created_at, preferences
                FROM customers
                WHERE user_role = 'customer'
                ORDER BY customer_id
            """)

            existing_customers = cursor.fetchall()

        conn.close()

        if not existing_customers:
            logger.warning("⚠️ No existing customers found for augmentation")
            return False

        # Load products for order generation
        products_by_category = load_products_by_category()
        if not products_by_category:
            logger.error("❌ No products available for order generation")
            return False

        # Generate additional orders for existing customers
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = False
        orders_inserted = 0

        with conn.cursor() as cursor:
            for customer_id, name, state, tier, created_at, preferences in existing_customers:
                try:
                    # Calculate customer profile
                    days_as_customer = (datetime.now() - created_at).days
                    days_as_customer = max(days_as_customer, 1)

                    # Parse preferences
                    try:
                        prefs = json.loads(preferences) if preferences else {}
                    except:
                        prefs = {}

                    preferred_categories = prefs.get('preferred_categories', ['Electronics', 'Fashion'])

                    # Generate additional orders
                    for _ in range(additional_orders_per_customer):
                        # Recent order (within last 30 days)
                        days_ago = random.randint(1, 30)
                        order_date = datetime.now() - timedelta(days=days_ago)

                        # Order amount based on tier
                        tier_multipliers = {'Bronze': 1.0, 'Silver': 1.5, 'Gold': 2.0, 'Platinum': 3.0}
                        base_amount = random.uniform(5000, 50000) * tier_multipliers.get(tier, 1.0)

                        # Select category and product
                        category = random.choice(preferred_categories)
                        if category not in products_by_category:
                            category = random.choice(list(products_by_category.keys()))

                        # Select suitable product
                        suitable_products = [p for p in products_by_category[category]
                                           if p['price'] <= base_amount * 1.2]

                        if not suitable_products:
                            suitable_products = products_by_category[category]

                        product = random.choice(suitable_products)

                        # Determine order status
                        days_since_order = (datetime.now() - order_date).days
                        if days_since_order > 7:
                            status = random.choices(['Delivered', 'Returned'], weights=[0.9, 0.1])[0]
                            delivery_date = order_date.date() + timedelta(days=random.randint(1, 5))
                        else:
                            status = random.choices(['Processing', 'Delivered'], weights=[0.6, 0.4])[0]
                            delivery_date = datetime.now().date() + timedelta(days=random.randint(1, 7))

                        # Payment method based on tier
                        if tier in ['Gold', 'Platinum']:
                            payment_method = random.choices(['Card', 'RaqibTechPay', 'Bank Transfer'], weights=[0.5, 0.3, 0.2])[0]
                        else:
                            payment_method = random.choices(['Pay on Delivery', 'Bank Transfer', 'Card'], weights=[0.5, 0.3, 0.2])[0]

                        # Insert order
                        cursor.execute("""
                            INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date,
                                              product_category, product_id, created_at)
                            VALUES (%s, %s::order_status_enum, %s::payment_method_enum, %s, %s, %s, %s, %s)
                        """, (
                            customer_id, status, payment_method, round(base_amount, 2),
                            delivery_date, category, product['product_id'], order_date
                        ))
                        orders_inserted += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to add orders for customer {name}: {e}")

            conn.commit()

        conn.close()

        logger.info(f"✅ Data augmentation complete!")
        logger.info(f"   📦 Additional orders inserted: {orders_inserted}")

        return True

    except Exception as e:
        logger.error(f"❌ Data augmentation failed: {e}")
        return False

def clean_and_regenerate(num_customers: int = 1000):
    """Clean existing data and regenerate everything"""
    logger.info("🧹 Cleaning existing data and regenerating...")

    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = True

        with conn.cursor() as cursor:
            # Clean data in proper order
            logger.info("   Truncating orders...")
            cursor.execute("TRUNCATE TABLE orders RESTART IDENTITY CASCADE")

            logger.info("   Truncating customers...")
            cursor.execute("TRUNCATE TABLE customers RESTART IDENTITY CASCADE")

            logger.info("   Clearing all products...")
            cursor.execute("DELETE FROM products")

            # Reset sequences
            cursor.execute("ALTER SEQUENCE customers_customer_id_seq RESTART WITH 1")
            cursor.execute("ALTER SEQUENCE orders_order_id_seq RESTART WITH 1")

        conn.close()

        # Generate fresh data
        return generate_fresh_data(num_customers)

    except Exception as e:
        logger.error(f"❌ Clean and regenerate failed: {e}")
        return False

def main():
    """Main execution function"""
    logger.info("🇳🇬 Nigerian E-commerce Data Generator")
    logger.info("=" * 50)

    # Command line argument handling
    import argparse
    parser = argparse.ArgumentParser(description='Generate Nigerian e-commerce data')
    parser.add_argument('--mode', choices=['fresh', 'augment', 'clean'], default='fresh',
                       help='Data generation mode')
    parser.add_argument('--customers', type=int, default=1000,
                       help='Number of customers to generate (for fresh/clean modes)')
    parser.add_argument('--orders', type=int, default=2,
                       help='Additional orders per customer (for augment mode)')

    args = parser.parse_args()

    success = False

    if args.mode == 'fresh':
        success = generate_fresh_data(num_customers=args.customers)
    elif args.mode == 'augment':
        success = augment_existing_data(additional_orders_per_customer=args.orders)
    elif args.mode == 'clean':
        success = clean_and_regenerate(num_customers=args.customers)

    if success:
        logger.info("🎉 Data generation completed successfully!")

        # Display summary
        try:
            conn = psycopg2.connect(**DATABASE_CONFIG)
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM customers WHERE user_role = 'customer'")
                customer_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM customers WHERE is_staff = true")
                staff_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM orders")
                order_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM products")
                total_product_count = cursor.fetchone()[0]

                cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY category")
                category_counts = cursor.fetchall()

                cursor.execute("""
                    SELECT account_tier, COUNT(*)
                    FROM customers
                    WHERE user_role = 'customer'
                    GROUP BY account_tier
                    ORDER BY CASE account_tier
                        WHEN 'Platinum' THEN 1
                        WHEN 'Gold' THEN 2
                        WHEN 'Silver' THEN 3
                        WHEN 'Bronze' THEN 4
                    END
                """)
                tier_distribution = cursor.fetchall()

            conn.close()

            logger.info("📊 DATABASE SUMMARY:")
            logger.info(f"   👥 Regular customers: {customer_count}")
            logger.info(f"   👨‍💼 Staff accounts: {staff_count}")
            logger.info(f"   📦 Total orders: {order_count}")
            logger.info(f"   🛍️ Total products: {total_product_count}")
            logger.info("📦 PRODUCT CATEGORIES:")
            for category, count in category_counts:
                logger.info(f"   {category}: {count} products")
            logger.info("🏆 TIER DISTRIBUTION:")
            for tier, count in tier_distribution:
                percentage = (count / customer_count * 100) if customer_count > 0 else 0
                logger.info(f"   {tier}: {count} ({percentage:.1f}%)")

        except Exception as e:
            logger.warning(f"⚠️ Could not generate summary: {e}")

    else:
        logger.error("❌ Data generation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
