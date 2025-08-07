# 🇳🇬 Nigerian E-commerce Data Generator

## Overview

The **Nigerian E-commerce Data Generator** is a comprehensive Python script designed to generate authentic Nigerian e-commerce data for your Flask application. It creates realistic customer profiles, orders, and product data that reflects Nigeria's ethnic diversity, regional preferences, and e-commerce patterns.

## Features

### ✅ **Fresh Data Generation**
- Generate new customers across all six Nigerian geopolitical zones
- Ethnically authentic names from Yoruba, Igbo, Hausa, Niger Delta, and Middle Belt cultures
- Realistic phone numbers using actual Nigerian network prefixes (MTN, Airtel, Glo, 9mobile)
- Business growth stage timestamps (early, growth, expansion, current)
- Account tier progression based on spending and order patterns

### ✅ **Data Augmentation**
- Add new orders to existing customers
- Maintain consistency with customer preferences and tier status
- Recent order patterns with realistic status distributions

### ✅ **RBAC Staff Accounts**
- Support agents, admins, and super admin accounts
- Proper role-based permissions and authentication
- Staff account integration with existing system

### ✅ **Nigerian Food Products**
- 40+ authentic Nigerian food products and kitchen items
- From Maggi cubes and palm oil to traditional items like garri and stockfish
- Realistic pricing in Nigerian Naira

### ✅ **Business Intelligence**
- Realistic account tier distributions (Bronze: 45%, Silver: 30%, Gold: 20%, Platinum: 5%)
- Payment method preferences by region and tier
- Seasonal and cultural shopping patterns

## Installation & Setup

### Prerequisites

```bash
# Install required Python packages
pip install psycopg2 bcrypt pandas
```

### Database Configuration

Ensure your `config/database_config.py` has the correct PostgreSQL connection details:

```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'raqibtech_db',
    'user': 'postgres',
    'password': 'your_password'
}
```

## Usage

### Command Line Interface

The script supports three main modes:

#### 1. Fresh Data Generation (Default)
Generate completely new data from scratch:

```bash
# Generate 1000 customers with orders (default)
python scripts/generate_nigerian_ecommerce_data.py

# Generate 2000 customers
python scripts/generate_nigerian_ecommerce_data.py --mode fresh --customers 2000

# Generate 500 customers
python scripts/generate_nigerian_ecommerce_data.py --customers 500
```

#### 2. Data Augmentation
Add new orders to existing customers:

```bash
# Add 2 new orders per existing customer (default)
python scripts/generate_nigerian_ecommerce_data.py --mode augment

# Add 5 new orders per customer
python scripts/generate_nigerian_ecommerce_data.py --mode augment --orders 5
```

#### 3. Clean & Regenerate
Clean all existing data and generate fresh data:

```bash
# Clean everything and generate 1500 new customers
python scripts/generate_nigerian_ecommerce_data.py --mode clean --customers 1500
```

### Python API Usage

You can also import and use the functions directly:

```python
from scripts.generate_nigerian_ecommerce_data import (
    generate_fresh_data,
    augment_existing_data,
    clean_and_regenerate
)

# Generate 500 customers
success = generate_fresh_data(num_customers=500)

# Add 3 orders per existing customer
success = augment_existing_data(additional_orders_per_customer=3)

# Clean and regenerate with 2000 customers
success = clean_and_regenerate(num_customers=2000)
```

## Generated Data Structure

### Customer Profiles

Each customer includes:

- **Ethnically authentic names** (Yoruba, Igbo, Hausa, Niger Delta, Middle Belt)
- **Realistic contact info** (Nigerian phone numbers, regional email patterns)
- **Geographic data** (State, LGA, full address)
- **Account tier** (Bronze, Silver, Gold, Platinum) based on spending
- **Cultural preferences** (language, preferred categories, delivery options)
- **RBAC fields** (user_role, permissions, account_status)

### Order Patterns

Orders are generated with:

- **Realistic timestamps** distributed across business growth stages
- **Status logic** (no "Pending" orders with past delivery dates)
- **Payment methods** based on tier and regional preferences
- **Product selection** matching customer preferences
- **Spending patterns** aligned with account tiers

### Staff Accounts

Automatically creates RBAC staff accounts:

- **Support Agents**: Adunni and Kemi (password: Support2024!)
- **Admins**: Folake and Chidi (password: Admin2024!)
- **Super Admin**: Raqib (password: SuperAdmin2024!)

### Nigerian Food Products

Inserts 40+ authentic Nigerian products including:

- **Staples**: Rice, garri, semovita, wheat flour
- **Proteins**: Fish, chicken, beef, turkey, stockfish
- **Seasonings**: Maggi cubes, curry, thyme, locust beans
- **Oils**: Palm oil, vegetable oil, groundnut oil, coconut oil
- **Beverages**: Milo, Bournvita, tea, milk, yoghurt
- **Snacks**: Plantain chips, chin chin, groundnuts, kuli kuli
- **Kitchen Items**: Frying pans, pressure pots, mortar and pestle

## Business Growth Stages

The script generates data across four realistic business growth stages:

| Stage | Weight | Time Period | Customer Behavior |
|-------|--------|-------------|-------------------|
| **Early Stage** | 15% | Jan 2023 - Jun 2023 | Lower activity, basic tiers |
| **Growth Stage** | 25% | Jul 2023 - Mar 2024 | Moderate growth, mixed tiers |
| **Expansion Stage** | 35% | Apr 2024 - Dec 2024 | Peak activity, higher tiers |
| **Current Stage** | 25% | Jan 2025 - Jun 2025 | Latest customers, all tiers |

## Account Tier Logic

Tier progression follows realistic Nigerian e-commerce patterns:

| Tier | Spending Range | Min Orders | Typical Customers |
|------|----------------|------------|-------------------|
| **Bronze** | ₦0 - ₦100K | 0+ | New/occasional customers |
| **Silver** | ₦100K - ₦500K | 3+ | Regular customers |
| **Gold** | ₦500K - ₦2M | 10+ | Loyal customers |
| **Platinum** | ₦2M+ | 20+ | VIP customers |

## Regional & Cultural Patterns

### Ethnic Group Preferences

- **Yoruba** (Lagos, Oyo, Osun): Electronics, Fashion, Beauty
- **Igbo** (Anambra, Imo, Abia): Electronics, Computing, Automotive
- **Hausa** (Kano, Kaduna, Sokoto): Fashion, Food Items, Beauty
- **Niger Delta** (Rivers, Bayelsa, Delta): Electronics, Automotive, Fashion
- **Middle Belt** (Plateau, Benue, Niger): Books, Electronics, Food Items

### Payment Method Preferences

- **Gold/Platinum + Urban**: Card (50%), RaqibTechPay (20%), Bank Transfer (20%), POD (10%)
- **Hausa Regions**: Pay on Delivery (60%), Bank Transfer (30%), Card (8%), RaqibTechPay (2%)
- **General**: Pay on Delivery (40%), Bank Transfer (30%), Card (25%), RaqibTechPay (5%)

## Database Impact

### Tables Modified

1. **customers** - Adds RBAC columns and customer data
2. **orders** - Adds order history with product relationships
3. **products** - Adds Nigerian food products
4. **analytics** - May add business metrics

### Schema Changes

The script automatically adds RBAC columns to the customers table:

```sql
ALTER TABLE customers ADD COLUMN IF NOT EXISTS user_role user_role_enum DEFAULT 'customer';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS account_status account_status_enum DEFAULT 'active';
ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
```

## Performance Considerations

- **1000 customers**: ~2-3 minutes generation time
- **5000 customers**: ~10-15 minutes generation time
- **Database size**: ~1MB per 1000 customers with orders
- **Memory usage**: ~100MB for 1000 customers

## Verification & Testing

After running the script, verify the data:

```sql
-- Check customer distribution
SELECT account_tier, COUNT(*) FROM customers WHERE user_role = 'customer' GROUP BY account_tier;

-- Check ethnic distribution
SELECT preferences->'ethnicity', COUNT(*) FROM customers GROUP BY preferences->'ethnicity';

-- Check order status distribution
SELECT order_status, COUNT(*) FROM orders GROUP BY order_status;

-- Check staff accounts
SELECT name, user_role, is_staff FROM customers WHERE is_staff = true;
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure PostgreSQL user has CREATE/INSERT permissions
2. **Missing Dependencies**: Install psycopg2, bcrypt, pandas
3. **Schema Conflicts**: Run with `--mode clean` to reset completely
4. **Memory Issues**: Reduce customer count for large datasets

### Debug Mode

Add debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Existing Systems

The generated data is fully compatible with:

- ✅ Flask app authentication system
- ✅ Order management workflows
- ✅ Customer support AI queries
- ✅ Business analytics dashboards
- ✅ Account tier progression logic
- ✅ Delivery fee calculations
- ✅ Payment processing

## Best Practices

1. **Start Small**: Test with 100-500 customers first
2. **Backup Database**: Always backup before major data generation
3. **Monitor Performance**: Watch database size and query performance
4. **Clean Staging**: Use clean mode for staging environments
5. **Incremental Growth**: Use augment mode for realistic growth simulation

## Example Output

```
🇳🇬 Nigerian E-commerce Data Generator
==================================================
🇳🇬 Generating fresh Nigerian e-commerce data...
   👥 Target customers: 1000
   📦 Target orders per customer: ~3
🔧 Ensuring database schema is ready...
✅ Database schema verified and updated
🍽️ Inserting Nigerian food products...
✅ Successfully inserted 40 Nigerian food products
👨‍💼 Inserting RBAC staff accounts...
✅ Successfully inserted 5 staff accounts
   🏢 early_stage: 150 customers
   🏢 growth_stage: 250 customers
   🏢 expansion_stage: 350 customers
   🏢 current_stage: 250 customers
✅ Fresh data generation complete!
   👥 Customers inserted: 1000
   📦 Orders inserted: 2847
🎉 Data generation completed successfully!
📊 DATABASE SUMMARY:
   👥 Regular customers: 1000
   👨‍💼 Staff accounts: 5
   📦 Total orders: 2847
   🍽️ Nigerian food products: 40
🏆 TIER DISTRIBUTION:
   Bronze: 445 (44.5%)
   Silver: 312 (31.2%)
   Gold: 187 (18.7%)
   Platinum: 56 (5.6%)
```

---

**Created by**: RaqibTech Development Team
**Last Updated**: June 2025
**Version**: 1.0.0
