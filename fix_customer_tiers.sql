-- Fix Customer Tier Progression Issues
-- This script updates customer tiers based on their actual spending

-- First, let's see the current state
SELECT
    'BEFORE UPDATE' as phase,
    account_tier,
    COUNT(*) as customer_count,
    ROUND(AVG(total_spent), 0) as avg_spending
FROM (
    SELECT
        c.customer_id,
        c.account_tier,
        COALESCE(SUM(o.total_amount), 0) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status != 'Returned' OR o.order_status IS NULL
    GROUP BY c.customer_id, c.account_tier
) customer_spending
GROUP BY account_tier
ORDER BY CASE account_tier
    WHEN 'Platinum' THEN 1
    WHEN 'Gold' THEN 2
    WHEN 'Silver' THEN 3
    WHEN 'Bronze' THEN 4
END;

-- Update all customer tiers based on their actual spending
UPDATE customers
SET account_tier = CASE
    WHEN customer_spending.total_spent >= 2000000 THEN 'Platinum'
    WHEN customer_spending.total_spent >= 500000 THEN 'Gold'
    WHEN customer_spending.total_spent >= 100000 THEN 'Silver'
    ELSE 'Bronze'
END,
updated_at = CURRENT_TIMESTAMP
FROM (
    SELECT
        c.customer_id,
        COALESCE(SUM(o.total_amount), 0) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status != 'Returned' OR o.order_status IS NULL
    GROUP BY c.customer_id
) customer_spending
WHERE customers.customer_id = customer_spending.customer_id
AND customers.account_tier != CASE
    WHEN customer_spending.total_spent >= 2000000 THEN 'Platinum'
    WHEN customer_spending.total_spent >= 500000 THEN 'Gold'
    WHEN customer_spending.total_spent >= 100000 THEN 'Silver'
    ELSE 'Bronze'
END;

-- Show updated results
SELECT
    'AFTER UPDATE' as phase,
    account_tier,
    COUNT(*) as customer_count,
    ROUND(AVG(total_spent), 0) as avg_spending,
    MIN(total_spent) as min_spending,
    MAX(total_spent) as max_spending
FROM (
    SELECT
        c.customer_id,
        c.account_tier,
        COALESCE(SUM(o.total_amount), 0) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status != 'Returned' OR o.order_status IS NULL
    GROUP BY c.customer_id, c.account_tier
) customer_spending
GROUP BY account_tier
ORDER BY CASE account_tier
    WHEN 'Platinum' THEN 1
    WHEN 'Gold' THEN 2
    WHEN 'Silver' THEN 3
    WHEN 'Bronze' THEN 4
END;

-- Check specific customer 1503
SELECT
    c.customer_id,
    c.name,
    c.account_tier,
    COALESCE(SUM(o.total_amount), 0) as total_spent,
    COUNT(o.order_id) as order_count,
    CASE
        WHEN COALESCE(SUM(o.total_amount), 0) >= 2000000 THEN 'Platinum'
        WHEN COALESCE(SUM(o.total_amount), 0) >= 500000 THEN 'Gold'
        WHEN COALESCE(SUM(o.total_amount), 0) >= 100000 THEN 'Silver'
        ELSE 'Bronze'
    END as should_be_tier
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE c.customer_id = 1503
AND (o.order_status != 'Returned' OR o.order_status IS NULL)
GROUP BY c.customer_id, c.name, c.account_tier;
