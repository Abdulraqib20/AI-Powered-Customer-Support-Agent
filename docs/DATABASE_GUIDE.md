# 📊 Database Structure Guide for Nigerian E-commerce Customer Support Agent

## 🏗️ **Database Overview**

Your PostgreSQL database (`nigerian_ecommercce`) contains 3 main tables designed specifically for Nigerian e-commerce operations:

### 1. **CUSTOMERS Table** 👥

```sql
customers (
    customer_id SERIAL PRIMARY KEY,           -- Auto-incrementing unique ID
    name VARCHAR(100) NOT NULL,               -- Customer full name
    email VARCHAR(255) UNIQUE NOT NULL,       -- Email (must be unique)
    phone VARCHAR(15) NOT NULL,               -- Nigerian phone number
    state VARCHAR(50) NOT NULL,               -- Nigerian state (Lagos, Kano, etc.)
    lga VARCHAR(50) NOT NULL,                 -- Local Government Area
    address TEXT,                             -- Full address
    account_tier ENUM NOT NULL,               -- 'Bronze', 'Silver', 'Gold', 'Platinum'
    preferences JSONB,                        -- Customer preferences as JSON
    created_at TIMESTAMP DEFAULT NOW(),       -- When customer was created
    updated_at TIMESTAMP DEFAULT NOW()        -- Last update time
)
```

**Key Features:**

- **Phone Validation**: Must match Nigerian format `^(\+234|0)[7-9][0-1][0-9]{8}$`
- **State/LGA**: Nigerian geographic data for localized support
- **Account Tiers**: Loyalty levels affecting service priority
- **Preferences**: JSON data for language, categories, notifications

### 2. **ORDERS Table** 📦

```sql
orders (
    order_id SERIAL PRIMARY KEY,             -- Auto-incrementing unique ID
    customer_id INTEGER REFERENCES customers, -- Links to customer who made order
    order_status ENUM NOT NULL,              -- 'Pending', 'Processing', 'Delivered', 'Returned'
    payment_method ENUM NOT NULL,            -- 'Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay'
    total_amount NUMERIC(10,2),              -- Order value in Naira (₦)
    delivery_date DATE,                      -- Expected/actual delivery date
    product_category VARCHAR(50),            -- Electronics, Fashion, Food Items, etc.
    created_at TIMESTAMP DEFAULT NOW(),      -- When order was placed
    updated_at TIMESTAMP DEFAULT NOW()       -- Last update time
)
```

**Key Features:**

- **Partitioned by Month**: Tables like `orders_2024_01`, `orders_2025_01` for performance
- **Nigerian Payment Methods**: Includes local options like "Pay on Delivery"
- **Delivery Constraints**: Cannot deliver in the past
- **Amount in Naira**: Uses NUMERIC for precise currency handling

### 3. **ANALYTICS Table** 📈

```sql
analytics (
    analytics_id SERIAL PRIMARY KEY,         -- Auto-incrementing unique ID
    metric_type VARCHAR(50),                 -- Type of metric (revenue_by_state, etc.)
    metric_value JSONB,                      -- Metric data as JSON
    time_period VARCHAR(20),                 -- 'monthly', 'weekly', 'current'
    created_at TIMESTAMP DEFAULT NOW()       -- When metric was recorded
)
```

**Key Features:**

- **Flexible JSON Storage**: Stores complex analytics data
- **Time-based Metrics**: Track performance over different periods
- **Business Intelligence**: Revenue, customer distribution, trends

## 🔗 **Table Relationships**

```
CUSTOMERS (1) ←→ (Many) ORDERS
    └── customer_id is the foreign key linking them

ANALYTICS (Independent)
    └── Stores aggregated data from other tables
```

## 📝 **How to Populate Tables in the Future**

### **Adding New Customers**

```python
# Using the repository pattern
from config.database_config import get_repositories

repositories = get_repositories()

# Add a single customer
new_customer = {
    'name': 'Kemi Adebayo',
    'email': 'kemi.adebayo@gmail.com',
    'phone': '+2348012345678',  # Must match Nigerian format
    'state': 'Lagos',
    'lga': 'Victoria Island',
    'address': '10 Ahmadu Bello Way, Victoria Island, Lagos',
    'account_tier': 'Gold',
    'preferences': {
        'language': 'English',
        'preferred_categories': ['Fashion', 'Beauty'],
        'notifications': {'email': True, 'sms': False},
        'delivery_preference': 'Express Delivery'
    }
}

customer_id = repositories['customers'].create(new_customer)
```

### **Adding New Orders**

```python
# Add an order for an existing customer
from datetime import date, timedelta

new_order = {
    'customer_id': 1,  # Must exist in customers table
    'order_status': 'Pending',
    'payment_method': 'Pay on Delivery',
    'total_amount': 75000.00,  # In Naira
    'delivery_date': date.today() + timedelta(days=7),  # Future date
    'product_category': 'Electronics'
}

order_id = repositories['orders'].create(new_order)
```

### **Adding Analytics Data**

```python
# Record new analytics
analytics_data = {
    'metric_type': 'daily_revenue',
    'metric_value': {
        'total': 500000,
        'currency': 'NGN',
        'orders_count': 25,
        'avg_order_value': 20000
    },
    'time_period': 'daily'
}

repositories['analytics'].create(analytics_data)
```

## 🛠️ **Direct SQL Examples**

### **Insert Customer (SQL)**

```sql
INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences)
VALUES (
    'Amina Yusuf',
    'amina.yusuf@yahoo.com',
    '08087654321',  -- Valid Nigerian number
    'Kano',
    'Municipal',
    '45 Murtala Mohammed Way, Kano',
    'Silver',
    '{"language": "Hausa", "preferred_categories": ["Home & Kitchen"]}'::jsonb
);
```

### **Insert Order (SQL)**

```sql
INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category)
VALUES (
    1,  -- Existing customer ID
    'Processing',
    'Bank Transfer',
    150000.00,
    '2025-06-15',  -- Future date
    'Electronics'
);
```

### **Query Customer Orders (SQL)**

```sql
-- Get all orders for a customer with their details
SELECT
    c.name,
    c.state,
    o.order_status,
    o.total_amount,
    o.delivery_date,
    o.product_category
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE c.customer_id = 1
ORDER BY o.created_at DESC;
```

## 📊 **Important Views for Data Analysis**

### **Customer Distribution View**

```sql
SELECT * FROM customer_distribution_view;
-- Shows customers by state and account tier with percentages
```

### **Order Summary View**

```sql
SELECT * FROM order_summary_view;
-- Shows order statistics by status and payment method
```

### **Customer Lifetime Value View**

```sql
SELECT * FROM customer_lifetime_value_view;
-- Shows total value and order count per customer
```

## ⚠️ **Important Constraints to Remember**

### **Phone Number Validation**

- Must start with `+234` or `0`
- Network code: 7, 8, or 9
- Second digit: 0 or 1
- Total: exactly 11 digits (local) or 14 digits (international)

**Valid Examples:**

- `08012345678` ✅
- `+2348012345678` ✅
- `09087654321` ✅
- `+2347098765432` ✅

**Invalid Examples:**

- `+234901234567` ❌ (90 doesn't match [7-9][0-1])
- `08123456789` ❌ (12 doesn't match [7-9][0-1])

### **Delivery Date Constraint**

- Orders cannot have delivery dates in the past
- Use `date.today() + timedelta(days=X)` for future dates

### **Account Tiers**

- Must be one of: `'Bronze'`, `'Silver'`, `'Gold'`, `'Platinum'`

### **Payment Methods**

- Must be one of: `'Pay on Delivery'`, `'Bank Transfer'`, `'Card'`, `'RaqibTechPay'`

## 🔄 **Data Population Strategies**

### **For Development/Testing**

1. Use the existing scripts:
   - `add_remaining_customers.py` - Add more sample customers
   - `add_orders.py` - Add sample orders

### **For Production**

1. **API Integration**: Connect your Streamlit app to create customers/orders through user interactions
2. **Bulk Import**: Use CSV files with PostgreSQL COPY command
3. **Scheduled Analytics**: Create cron jobs to update analytics daily/weekly

### **Bulk Insert Example**

```python
# Add multiple customers at once
customers_data = [
    ('John Doe', 'john@example.com', '08012345678', 'Lagos', 'Ikeja', ...),
    ('Jane Smith', 'jane@example.com', '09087654321', 'Abuja', 'Municipal', ...),
    # ... more customers
]

# Use executemany for efficiency
cursor.executemany("""
    INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", customers_data)
```

## 🚀 **Integration with Your AI Agent**

Your customer support agent can now:

1. **Query real customer data** instead of generating synthetic data
2. **Update order statuses** in real-time
3. **Analyze customer patterns** using the views
4. **Provide personalized support** based on customer tier and preferences
5. **Track business metrics** through the analytics table

The database is production-ready and optimized for the Nigerian e-commerce market!
