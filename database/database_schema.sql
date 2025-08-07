-- =====================================================================
-- AI-Powered Customer Support Agent Database Schema
-- Nigerian E-commerce Platform - PostgreSQL Database
-- Optimized for scalability and Nigerian market requirements
-- =====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================================
-- ENUM TYPES
-- =====================================================================

-- Account tier enumeration for customer loyalty levels
CREATE TYPE account_tier_enum AS ENUM ('Bronze', 'Silver', 'Gold', 'Platinum');

-- Order status enumeration for tracking order lifecycle
CREATE TYPE order_status_enum AS ENUM ('Pending', 'Processing', 'Delivered', 'Returned');

-- Payment method enumeration tailored for Nigerian market
CREATE TYPE payment_method_enum AS ENUM ('Pay on Delivery', 'Bank Transfer', 'Card', 'RaqibTechPay');

-- =====================================================================
-- CUSTOMERS TABLE
-- =====================================================================

-- Store Nigerian customer profiles with contact, location, and preferences
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- Full customer name (First + Last name)
    email VARCHAR(255) UNIQUE NOT NULL, -- Unique email address for customer identification
    phone VARCHAR(15) NOT NULL, -- Nigerian phone format (+234 or 080x format)
    state VARCHAR(50) NOT NULL, -- Nigerian state (Lagos, Abuja, Kano, Rivers, etc.)
    lga VARCHAR(50) NOT NULL, -- Local Government Area for precise location
    address TEXT NOT NULL, -- Full shipping address with street, area, city details
    account_tier account_tier_enum DEFAULT 'Bronze', -- Customer loyalty tier
    preferences JSONB, -- Customer preferences in flexible JSON format (language, categories, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Account creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Last profile update timestamp
);

-- Add comments for table and columns
COMMENT ON TABLE customers IS 'Customer profiles for Nigerian e-commerce platform with location and preference data';
COMMENT ON COLUMN customers.customer_id IS 'Auto-incrementing primary key for customer identification';
COMMENT ON COLUMN customers.name IS 'Full customer name following Nigerian naming conventions';
COMMENT ON COLUMN customers.email IS 'Unique email address for customer account and communications';
COMMENT ON COLUMN customers.phone IS 'Nigerian phone number in +234 or 080x format';
COMMENT ON COLUMN customers.state IS 'Nigerian state for geographic analytics and delivery optimization';
COMMENT ON COLUMN customers.lga IS 'Local Government Area for precise location targeting';
COMMENT ON COLUMN customers.address IS 'Complete shipping address for order delivery';
COMMENT ON COLUMN customers.account_tier IS 'Customer loyalty level affecting discounts and benefits';
COMMENT ON COLUMN customers.preferences IS 'Customer preferences in JSON format (language, product categories, notifications)';

-- =====================================================================
-- ORDERS TABLE WITH PARTITIONING
-- =====================================================================

-- Track orders with Nigerian payment methods and delivery status
CREATE TABLE orders (
    order_id SERIAL,
    customer_id INTEGER NOT NULL,
    order_status order_status_enum NOT NULL DEFAULT 'Pending', -- Current order status
    payment_method payment_method_enum NOT NULL, -- Payment method used for the order
    total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >= 0), -- Total amount in Nigerian Naira
    delivery_date DATE, -- Expected or actual delivery date
    product_category VARCHAR(50), -- Main product category for analytics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Order creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Last order update timestamp

    -- Composite primary key including partition column
    PRIMARY KEY (order_id, created_at),

    -- Foreign key to customers table
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
) PARTITION BY RANGE (created_at);

-- Add comments for orders table
COMMENT ON TABLE orders IS 'Order tracking with Nigerian payment methods, delivery status, and Naira pricing';
COMMENT ON COLUMN orders.order_id IS 'Order identifier (part of composite primary key with created_at)';
COMMENT ON COLUMN orders.customer_id IS 'Reference to customer who placed the order';
COMMENT ON COLUMN orders.order_status IS 'Current status of the order in fulfillment process';
COMMENT ON COLUMN orders.payment_method IS 'Payment method used, optimized for Nigerian market';
COMMENT ON COLUMN orders.total_amount IS 'Total order value in Nigerian Naira (₦)';
COMMENT ON COLUMN orders.delivery_date IS 'Expected or actual delivery date for logistics tracking';
COMMENT ON COLUMN orders.product_category IS 'Primary product category for business analytics';

-- Create monthly partitions for orders table (current and future months)
-- 2024 partitions
CREATE TABLE orders_2024_01 PARTITION OF orders FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE orders_2024_02 PARTITION OF orders FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE orders_2024_03 PARTITION OF orders FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
CREATE TABLE orders_2024_04 PARTITION OF orders FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');
CREATE TABLE orders_2024_05 PARTITION OF orders FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');
CREATE TABLE orders_2024_06 PARTITION OF orders FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
CREATE TABLE orders_2024_07 PARTITION OF orders FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');
CREATE TABLE orders_2024_08 PARTITION OF orders FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
CREATE TABLE orders_2024_09 PARTITION OF orders FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');
CREATE TABLE orders_2024_10 PARTITION OF orders FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
CREATE TABLE orders_2024_11 PARTITION OF orders FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');
CREATE TABLE orders_2024_12 PARTITION OF orders FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- 2025 partitions (for future orders)
CREATE TABLE orders_2025_01 PARTITION OF orders FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE orders_2025_02 PARTITION OF orders FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE orders_2025_03 PARTITION OF orders FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE orders_2025_04 PARTITION OF orders FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE orders_2025_05 PARTITION OF orders FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE orders_2025_06 PARTITION OF orders FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE orders_2025_07 PARTITION OF orders FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');
CREATE TABLE orders_2025_08 PARTITION OF orders FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
CREATE TABLE orders_2025_09 PARTITION OF orders FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
CREATE TABLE orders_2025_10 PARTITION OF orders FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE orders_2025_11 PARTITION OF orders FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE orders_2025_12 PARTITION OF orders FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- =====================================================================
-- ANALYTICS TABLE
-- =====================================================================

-- Store aggregated metrics for business intelligence and reporting
CREATE TABLE analytics (
    analytics_id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL, -- Type of metric (revenue, customer_count, order_volume, etc.)
    metric_value JSONB NOT NULL, -- Metric data in flexible JSON format
    time_period VARCHAR(20) NOT NULL, -- Time period for the metric (daily, weekly, monthly, yearly)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Metric calculation timestamp
);

-- Add comments for analytics table
COMMENT ON TABLE analytics IS 'Aggregated business metrics and KPIs for dashboard and reporting';
COMMENT ON COLUMN analytics.analytics_id IS 'Auto-incrementing primary key for analytics records';
COMMENT ON COLUMN analytics.metric_type IS 'Type of business metric (revenue, customer_distribution, order_trends, etc.)';
COMMENT ON COLUMN analytics.metric_value IS 'Metric data and values in JSON format for flexibility';
COMMENT ON COLUMN analytics.time_period IS 'Time aggregation period (daily, weekly, monthly, quarterly, yearly)';
COMMENT ON COLUMN analytics.created_at IS 'Timestamp when the metric was calculated and stored';

-- =====================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================================

-- Customers table indexes
CREATE INDEX idx_customers_email ON customers(email); -- Fast email lookups for authentication
CREATE INDEX idx_customers_state ON customers(state); -- Geographic analytics and filtering
CREATE INDEX idx_customers_account_tier ON customers(account_tier); -- Customer segmentation queries
CREATE INDEX idx_customers_created_at ON customers(created_at); -- Customer acquisition analytics
CREATE INDEX idx_customers_phone ON customers(phone); -- Phone number lookups for support
CREATE INDEX idx_customers_lga ON customers(lga); -- Local Government Area analytics

-- Orders table indexes (applied to main table and inherited by partitions)
CREATE INDEX idx_orders_customer_id ON orders(customer_id); -- Customer order history queries
CREATE INDEX idx_orders_status ON orders(order_status); -- Order fulfillment tracking
CREATE INDEX idx_orders_payment_method ON orders(payment_method); -- Payment analytics
CREATE INDEX idx_orders_delivery_date ON orders(delivery_date); -- Delivery scheduling
CREATE INDEX idx_orders_product_category ON orders(product_category); -- Product performance analytics
CREATE INDEX idx_orders_total_amount ON orders(total_amount); -- Revenue analytics

-- Analytics table indexes
CREATE INDEX idx_analytics_metric_type ON analytics(metric_type); -- Metric type filtering
CREATE INDEX idx_analytics_time_period ON analytics(time_period); -- Time-based queries
CREATE INDEX idx_analytics_created_at ON analytics(created_at); -- Temporal analytics queries

-- Composite indexes for common query patterns
CREATE INDEX idx_orders_customer_status ON orders(customer_id, order_status); -- Customer order status queries
CREATE INDEX idx_customers_state_tier ON customers(state, account_tier); -- Geographic customer segmentation

-- Text search indexes for customer support
CREATE INDEX idx_customers_name_gin ON customers USING gin(name gin_trgm_ops); -- Fuzzy name search
CREATE INDEX idx_customers_address_gin ON customers USING gin(address gin_trgm_ops); -- Address search

-- =====================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =====================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- CUSTOMER DISTRIBUTION VIEW
-- =====================================================================

-- Aggregate customers by state and tier for geographic analytics
CREATE VIEW customer_distribution_view AS
SELECT
    state,
    account_tier,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(AVG(EXTRACT(DAYS FROM (CURRENT_DATE - created_at::DATE))), 0) as avg_days_since_registration,
    MIN(created_at) as first_customer_date,
    MAX(created_at) as latest_customer_date
FROM customers
GROUP BY state, account_tier
ORDER BY state,
    CASE account_tier
        WHEN 'Platinum' THEN 1
        WHEN 'Gold' THEN 2
        WHEN 'Silver' THEN 3
        WHEN 'Bronze' THEN 4
    END;

-- Add comment for the view
COMMENT ON VIEW customer_distribution_view IS 'Geographic and tier-based customer distribution analytics for business intelligence';

-- =====================================================================
-- ADDITIONAL VIEWS FOR ANALYTICS
-- =====================================================================

-- Order summary view for quick analytics
CREATE VIEW order_summary_view AS
SELECT
    DATE_TRUNC('month', created_at) as month,
    order_status,
    payment_method,
    COUNT(*) as order_count,
    SUM(total_amount) as total_revenue,
    ROUND(AVG(total_amount), 2) as avg_order_value,
    MIN(total_amount) as min_order_value,
    MAX(total_amount) as max_order_value
FROM orders
GROUP BY DATE_TRUNC('month', created_at), order_status, payment_method
ORDER BY month DESC, order_status, payment_method;

COMMENT ON VIEW order_summary_view IS 'Monthly order and revenue analytics by status and payment method';

-- Customer lifetime value view
CREATE VIEW customer_lifetime_value_view AS
SELECT
    c.customer_id,
    c.name,
    c.state,
    c.account_tier,
    COUNT(o.order_id) as total_orders,
    COALESCE(SUM(o.total_amount), 0) as lifetime_value,
    COALESCE(ROUND(AVG(o.total_amount), 2), 0) as avg_order_value,
    MIN(o.created_at) as first_order_date,
    MAX(o.created_at) as last_order_date,
    CASE
        WHEN MAX(o.created_at) < CURRENT_DATE - INTERVAL '90 days' THEN 'Inactive'
        WHEN MAX(o.created_at) < CURRENT_DATE - INTERVAL '30 days' THEN 'At Risk'
        ELSE 'Active'
    END as customer_status
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.state, c.account_tier
ORDER BY lifetime_value DESC;

COMMENT ON VIEW customer_lifetime_value_view IS 'Customer lifetime value analysis with activity status for retention strategies';

-- =====================================================================
-- SAMPLE DATA INSERTS
-- =====================================================================

-- Sample customer data representing Nigerian market diversity
INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences) VALUES
('Adebayo Okonkwo', 'adebayo.okonkwo@gmail.com', '+234 813 456 7890', 'Lagos', 'Ikeja', '15 Adeniyi Jones Avenue, Ikeja, Lagos State', 'Gold',
 '{"language": "English", "preferred_categories": ["Electronics", "Fashion"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Home Delivery"}'),

('Fatima Abdullahi', 'fatima.abdullahi@yahoo.com', '0803-123-4567', 'Kano', 'Municipal', '23 Bompai Road, Nasarawa GRA, Kano State', 'Silver',
 '{"language": "Hausa", "preferred_categories": ["Home & Kitchen", "Beauty"], "notifications": {"email": true, "sms": false}, "delivery_preference": "Pickup Station"}'),

('Chioma Okechukwu', 'chioma.okechukwu@gmail.com', '+234 901 234 5678', 'Anambra', 'Awka South', '7 Zik Avenue, Awka, Anambra State', 'Platinum',
 '{"language": "Igbo", "preferred_categories": ["Electronics", "Food Items"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Express Delivery"}');

-- Sample order data with Nigerian pricing and payment methods
INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at) VALUES
(1, 'Delivered', 'RaqibTechPay', 185000.00, '2024-11-20', 'Electronics', '2024-11-15 10:30:00'),
(1, 'Processing', 'Card', 42500.00, '2024-12-28', 'Fashion', '2024-12-25 14:15:00'),
(2, 'Delivered', 'Pay on Delivery', 12500.00, '2024-11-18', 'Food Items', '2024-11-15 09:45:00'),
(2, 'Pending', 'Bank Transfer', 75000.00, '2024-12-30', 'Home & Kitchen', '2024-12-26 16:20:00'),
(3, 'Delivered', 'Card', 420000.00, '2024-10-05', 'Electronics', '2024-09-28 11:00:00'),
(3, 'Processing', 'RaqibTechPay', 95000.00, '2024-12-29', 'Beauty', '2024-12-26 13:30:00');

-- Sample analytics data for business intelligence
INSERT INTO analytics (metric_type, metric_value, time_period) VALUES
('revenue_by_state',
 '{"Lagos": 227500, "Kano": 87500, "Anambra": 515000, "total": 830000, "currency": "NGN"}',
 'monthly'),

('customer_distribution',
 '{"Bronze": 45, "Silver": 78, "Gold": 32, "Platinum": 15, "total": 170}',
 'current'),

('payment_method_usage',
 '{"Pay on Delivery": 35, "Bank Transfer": 20, "Card": 25, "RaqibTechPay": 20, "unit": "percentage"}',
 'monthly'),

('order_trends',
 '{"total_orders": 1250, "avg_order_value": 48750, "growth_rate": 12.5, "currency": "NGN"}',
 'monthly');

-- =====================================================================
-- PERFORMANCE MONITORING QUERIES
-- =====================================================================

-- View to monitor partition performance
CREATE VIEW partition_info_view AS
SELECT
    schemaname,
    tablename as partition_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    (SELECT COUNT(*) FROM orders WHERE created_at >=
        (SELECT substring(tablename from 'orders_(\d{4}_\d{2})')::text)::date
     AND created_at <
        (SELECT substring(tablename from 'orders_(\d{4}_\d{2})')::text)::date + INTERVAL '1 month'
    ) as row_count
FROM pg_tables
WHERE tablename LIKE 'orders______%'
ORDER BY tablename;

COMMENT ON VIEW partition_info_view IS 'Monitor orders table partition sizes and row counts for maintenance';

-- =====================================================================
-- DATABASE MAINTENANCE FUNCTIONS
-- =====================================================================

-- Function to create new monthly partitions automatically
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + INTERVAL '1 month';

    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);

    RAISE NOTICE 'Created partition % for period % to %', partition_name, start_date, end_date;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_monthly_partition IS 'Automatically create new monthly partitions for orders table';

-- =====================================================================
-- SECURITY AND ACCESS CONTROL
-- =====================================================================

-- Create roles for different access levels
-- Commented out as role creation requires superuser privileges
/*
CREATE ROLE customer_support_read;
CREATE ROLE customer_support_write;
CREATE ROLE analytics_read;
CREATE ROLE admin_full;

-- Grant appropriate permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO customer_support_read;
GRANT SELECT, INSERT, UPDATE ON customers, orders TO customer_support_write;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_read;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_full;
*/

-- =====================================================================
-- SCHEMA VALIDATION AND CONSTRAINTS
-- =====================================================================

-- Ensure total_amount is always positive
ALTER TABLE orders ADD CONSTRAINT check_positive_amount CHECK (total_amount > 0);

-- Ensure email format is valid (basic check)
ALTER TABLE customers ADD CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Ensure Nigerian phone number format
ALTER TABLE customers ADD CONSTRAINT check_nigerian_phone CHECK (
    phone ~* '^(\+234|0)[7-9][0-1][0-9]{8}$'
);

-- Ensure delivery date is not in the past for new orders
ALTER TABLE orders ADD CONSTRAINT check_future_delivery CHECK (
    delivery_date IS NULL OR delivery_date >= CURRENT_DATE
);

-- =====================================================================
-- COMPLETION MESSAGE
-- =====================================================================

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Nigerian E-commerce Database Schema Created Successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: customers, orders (partitioned), analytics';
    RAISE NOTICE 'Views created: customer_distribution_view, order_summary_view, customer_lifetime_value_view';
    RAISE NOTICE 'Indexes created: 15+ performance-optimized indexes';
    RAISE NOTICE 'Sample data inserted: 3 customers, 6 orders, 4 analytics records';
    RAISE NOTICE 'Monthly partitions: 2024-2025 (24 partitions)';
    RAISE NOTICE 'Ready for production use in Nigerian e-commerce environment!';
    RAISE NOTICE '========================================';
END $$;
