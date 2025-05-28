-- =====================================================================
-- Fix script for missing database objects and data
-- =====================================================================

-- Fix the customer_distribution_view with correct PostgreSQL syntax
DROP VIEW IF EXISTS customer_distribution_view;

CREATE VIEW customer_distribution_view AS
SELECT
    state,
    account_tier,
    COUNT(*) as customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(AVG(CURRENT_DATE - created_at::DATE), 0) as avg_days_since_registration,
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

-- Insert sample customer data if not exists (with correct phone number lengths)
INSERT INTO customers (name, email, phone, state, lga, address, account_tier, preferences)
SELECT * FROM (VALUES
    ('Adebayo Okonkwo', 'adebayo.okonkwo@gmail.com', '+234813456789', 'Lagos', 'Ikeja', '15 Adeniyi Jones Avenue, Ikeja, Lagos State', 'Gold'::account_tier_enum,
     '{"language": "English", "preferred_categories": ["Electronics", "Fashion"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Home Delivery"}'::jsonb),

    ('Fatima Abdullahi', 'fatima.abdullahi@yahoo.com', '08031234567', 'Kano', 'Municipal', '23 Bompai Road, Nasarawa GRA, Kano State', 'Silver'::account_tier_enum,
     '{"language": "Hausa", "preferred_categories": ["Home & Kitchen", "Beauty"], "notifications": {"email": true, "sms": false}, "delivery_preference": "Pickup Station"}'::jsonb),

    ('Chioma Okechukwu', 'chioma.okechukwu@gmail.com', '+234901234567', 'Anambra', 'Awka South', '7 Zik Avenue, Awka, Anambra State', 'Platinum'::account_tier_enum,
     '{"language": "Igbo", "preferred_categories": ["Electronics", "Food Items"], "notifications": {"email": true, "sms": true}, "delivery_preference": "Express Delivery"}'::jsonb)
) AS new_customers(name, email, phone, state, lga, address, account_tier, preferences)
WHERE NOT EXISTS (
    SELECT 1 FROM customers WHERE email = new_customers.email
);

-- Insert sample order data if customers exist
INSERT INTO orders (customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at)
SELECT * FROM (VALUES
    (1, 'Delivered'::order_status_enum, 'RaqibTechPay'::payment_method_enum, 185000.00, '2024-11-20'::date, 'Electronics', '2024-11-15 10:30:00'::timestamp),
    (1, 'Processing'::order_status_enum, 'Card'::payment_method_enum, 42500.00, '2024-12-28'::date, 'Fashion', '2024-12-25 14:15:00'::timestamp),
    (2, 'Delivered'::order_status_enum, 'Pay on Delivery'::payment_method_enum, 12500.00, '2024-11-18'::date, 'Food Items', '2024-11-15 09:45:00'::timestamp),
    (2, 'Pending'::order_status_enum, 'Bank Transfer'::payment_method_enum, 75000.00, '2024-12-30'::date, 'Home & Kitchen', '2024-12-26 16:20:00'::timestamp),
    (3, 'Delivered'::order_status_enum, 'Card'::payment_method_enum, 420000.00, '2024-10-05'::date, 'Electronics', '2024-09-28 11:00:00'::timestamp),
    (3, 'Processing'::order_status_enum, 'RaqibTechPay'::payment_method_enum, 95000.00, '2024-12-29'::date, 'Beauty', '2024-12-26 13:30:00'::timestamp)
) AS new_orders(customer_id, order_status, payment_method, total_amount, delivery_date, product_category, created_at)
WHERE EXISTS (SELECT 1 FROM customers WHERE customer_id = new_orders.customer_id);

-- Insert sample analytics data if not exists
INSERT INTO analytics (metric_type, metric_value, time_period)
SELECT * FROM (VALUES
    ('revenue_by_state',
     '{"Lagos": 227500, "Kano": 87500, "Anambra": 515000, "total": 830000, "currency": "NGN"}'::jsonb,
     'monthly'),

    ('customer_distribution',
     '{"Bronze": 45, "Silver": 78, "Gold": 32, "Platinum": 15, "total": 170}'::jsonb,
     'current'),

    ('payment_method_usage',
     '{"Pay on Delivery": 35, "Bank Transfer": 20, "Card": 25, "RaqibTechPay": 20, "unit": "percentage"}'::jsonb,
     'monthly'),

    ('order_trends',
     '{"total_orders": 1250, "avg_order_value": 48750, "growth_rate": 12.5, "currency": "NGN"}'::jsonb,
     'monthly')
) AS new_analytics(metric_type, metric_value, time_period)
WHERE NOT EXISTS (
    SELECT 1 FROM analytics WHERE metric_type = new_analytics.metric_type AND time_period = new_analytics.time_period
);

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database Fix Applied Successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Fixed: customer_distribution_view with correct PostgreSQL syntax';
    RAISE NOTICE 'Added: Sample customer, order, and analytics data';
    RAISE NOTICE 'Ready for testing!';
    RAISE NOTICE '========================================';
END $$;
