# PostgreSQL Database Setup for Nigerian E-commerce Customer Support Agent

This document provides instructions for setting up and migrating to PostgreSQL database for your AI-Powered Customer Support Agent.

## 🎯 Overview

The database schema is designed specifically for Nigerian e-commerce operations, featuring:

- **Customer profiles** with Nigerian states, LGAs, and payment preferences
- **Orders system** with local payment methods (Pay on Delivery, Bank Transfer, Card, RaqibTechPay)
- **Analytics** for business intelligence and performance tracking
- **Scalable design** with partitioning and optimized indexes

## 📋 Prerequisites

### 1. PostgreSQL Installation

**Windows:**
```bash
# Download from https://www.postgresql.org/download/windows/
# Or using chocolatey:
choco install postgresql

# Or using winget:
winget install PostgreSQL.PostgreSQL
```

**macOS:**
```bash
# Using Homebrew
brew install postgresql

# Start PostgreSQL service
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Python Dependencies

Install PostgreSQL dependencies (already in requirements.txt):
```bash
pip install psycopg2-binary SQLAlchemy
```

## 🚀 Quick Setup

### 1. Run the Setup Script

```bash
# Complete setup (recommended)
python setup_database.py

# Skip PostgreSQL installation check
python setup_database.py --skip-postgres-check

# Only test connection
python setup_database.py --test-only
```

### 2. Configure Database Connection

Update `.env` file with your PostgreSQL credentials:
```bash
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nigerian_ecommerce
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_SSLMODE=prefer
```

### 3. Test the Setup

```bash
python setup_database.py --test-only
```

## 📊 Database Schema

### Tables

#### 1. **customers** - Customer Profiles
```sql
- customer_id (SERIAL PRIMARY KEY)
- name (VARCHAR(100)) - Full Nigerian name
- email (VARCHAR(255) UNIQUE) - Customer email
- phone (VARCHAR(15)) - Nigerian phone format
- state (VARCHAR(50)) - Nigerian state
- lga (VARCHAR(50)) - Local Government Area
- address (TEXT) - Full shipping address
- account_tier (ENUM) - Bronze, Silver, Gold, Platinum
- preferences (JSONB) - Customer preferences
- created_at, updated_at (TIMESTAMP)
```

#### 2. **orders** - Order Management (Partitioned by Month)
```sql
- order_id (SERIAL)
- customer_id (INTEGER) - References customers
- order_status (ENUM) - Pending, Processing, Delivered, Returned
- payment_method (ENUM) - Pay on Delivery, Bank Transfer, Card, RaqibTechPay
- total_amount (NUMERIC(10,2)) - Amount in Nigerian Naira
- delivery_date (DATE)
- product_category (VARCHAR(50))
- created_at, updated_at (TIMESTAMP)
```

#### 3. **analytics** - Business Intelligence
```sql
- analytics_id (SERIAL PRIMARY KEY)
- metric_type (VARCHAR(50)) - Type of metric
- metric_value (JSONB) - Flexible metric data
- time_period (VARCHAR(20)) - Time aggregation period
- created_at (TIMESTAMP)
```

### Views

- **customer_distribution_view** - Customer analytics by state and tier
- **order_summary_view** - Monthly order and revenue analytics
- **customer_lifetime_value_view** - Customer value analysis

### Indexes

Performance-optimized indexes for:
- Email and phone lookups
- Geographic queries (state, LGA)
- Order status and payment method filtering
- Customer segmentation
- Text search capabilities

## 🔄 Data Migration

### From Synthetic Data to PostgreSQL

Use the migration utility in your application:

```python
from config.database_config import get_repositories, migrate_synthetic_data_to_db

# Get existing synthetic data (from your current system)
synthetic_data = {
    "customer_info": {
        "name": "Adebayo Okonkwo",
        "email": "adebayo@example.com",
        "phone": "+234 813 456 7890",
        "state": "Lagos",
        "lga": "Ikeja",
        "shipping_address": "15 Adeniyi Jones Avenue, Ikeja, Lagos"
    },
    "account": {
        "tier": "Gold",
        "member_since": "March 2024",
        "points": 1500
    },
    "current_order": {
        "payment_method": "RaqibTechPay",
        "total": "₦185,000",
        "expected_delivery": "December 30, 2024"
    },
    "order_history": [
        {
            "date": "2024-11-15",
            "total": "₦185,000",
            "status": "Delivered"
        }
    ]
}

# Migrate to PostgreSQL
repositories = get_repositories()
customer_id = migrate_synthetic_data_to_db(synthetic_data, repositories)
print(f"Migrated customer with ID: {customer_id}")
```

## 🔧 Integration with Existing Application

### 1. Update your main2.py

Replace synthetic data generation with database operations:

```python
from config.database_config import get_repositories

# Initialize repositories
repositories = get_repositories()
customer_repo = repositories['customers']
order_repo = repositories['orders']
analytics_repo = repositories['analytics']

# Replace generate_synthetic_data method
def get_customer_data(self, customer_id: int):
    """Get real customer data from PostgreSQL"""
    customer = customer_repo.get_customer_by_id(customer_id)
    if customer:
        orders = order_repo.get_orders_by_customer(customer_id)
        return {
            'customer': customer,
            'orders': orders
        }
    return None

def search_customers(self, search_term: str):
    """Search customers in PostgreSQL"""
    return customer_repo.search_customers(search_term)
```

### 2. Update Analytics Functions

```python
def get_customer_analytics(self):
    """Get analytics from PostgreSQL views"""
    distribution = customer_repo.get_customer_distribution()
    lifetime_value = analytics_repo.get_customer_lifetime_value()
    order_summary = order_repo.get_order_summary()

    return {
        'distribution': distribution,
        'lifetime_value': lifetime_value,
        'order_summary': order_summary
    }
```

## 📈 Performance Optimization

### Partitioning

Orders table is automatically partitioned by month:
- Faster queries on recent orders
- Easier maintenance and archiving
- Automatic partition creation function included

### Indexing Strategy

- **B-tree indexes** for exact matches (email, customer_id)
- **GIN indexes** for text search (names, addresses)
- **Composite indexes** for common query patterns
- **Partial indexes** for frequently filtered data

### Query Optimization

Use the provided views for common analytics:
```sql
-- Customer distribution
SELECT * FROM customer_distribution_view;

-- Monthly revenue trends
SELECT * FROM order_summary_view WHERE month >= '2024-01-01';

-- Customer lifetime value
SELECT * FROM customer_lifetime_value_view ORDER BY lifetime_value DESC LIMIT 10;
```

## 🛠️ Maintenance

### Adding New Partitions

```python
from config.database_config import initialize_database

db = initialize_database()
with db.get_cursor() as cursor:
    cursor.execute("SELECT create_monthly_partition('orders', '2025-01-01'::date)")
```

### Backup and Restore

```bash
# Backup
pg_dump -h localhost -U postgres -d nigerian_ecommerce > backup.sql

# Restore
psql -h localhost -U postgres -d nigerian_ecommerce < backup.sql
```

### Monitor Performance

```sql
-- Check partition sizes
SELECT * FROM partition_info_view;

-- Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 🔐 Security

### Connection Security

- SSL/TLS encryption enabled by default
- Connection pooling for resource management
- Parameterized queries to prevent SQL injection

### Access Control

Recommended roles (uncomment in schema if needed):
- `customer_support_read` - Read-only access
- `customer_support_write` - CRUD operations
- `analytics_read` - Analytics and reporting
- `admin_full` - Full database access

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql

   # Test connection
   psql -h localhost -U postgres -d postgres
   ```

2. **Permission Denied**
   ```bash
   # Create user and database
   sudo -u postgres createuser --interactive
   sudo -u postgres createdb nigerian_ecommerce
   ```

3. **Schema Creation Failed**
   ```bash
   # Check logs
   tail -f /var/log/postgresql/postgresql-*.log

   # Manual schema creation
   psql -h localhost -U postgres -d nigerian_ecommerce -f database_schema.sql
   ```

### Performance Issues

1. **Slow Queries**
   ```sql
   -- Enable query logging
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();

   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 1;
   ```

2. **Lock Contention**
   ```sql
   -- Monitor locks
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

## 📞 Support

For database-related issues:

1. Check PostgreSQL logs
2. Verify connection parameters in `.env`
3. Test individual components with provided utilities
4. Review the schema comments for table/column purposes

## 🎉 Success Indicators

After successful setup, you should see:

- ✅ Database schema created with all tables, indexes, and views
- ✅ Sample data inserted (3 customers, 6 orders, 4 analytics records)
- ✅ 24 monthly partitions created (2024-2025)
- ✅ Connection pool initialized
- ✅ All repository classes working

Your Nigerian e-commerce customer support agent is now ready for production with a robust PostgreSQL backend!
