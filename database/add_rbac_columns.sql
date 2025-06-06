-- =====================================================================
-- RBAC Extension for Existing Customer Table
-- Adds role-based access control to raqibtech.com customer support system
-- =====================================================================

-- 1. Create role enumeration type
CREATE TYPE user_role_enum AS ENUM ('customer', 'support_agent', 'admin', 'super_admin');

-- 2. Add RBAC columns to existing customers table
ALTER TABLE customers
ADD COLUMN user_role user_role_enum DEFAULT 'customer',
ADD COLUMN is_staff BOOLEAN DEFAULT FALSE,
ADD COLUMN is_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN permissions JSONB DEFAULT '[]',
ADD COLUMN last_login TIMESTAMP,
ADD COLUMN account_status VARCHAR(20) DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended'));

-- 3. Add comments for new columns
COMMENT ON COLUMN customers.user_role IS 'User role for RBAC: customer, support_agent, admin, super_admin';
COMMENT ON COLUMN customers.is_staff IS 'Quick check if user is staff (support_agent or above)';
COMMENT ON COLUMN customers.is_admin IS 'Quick check if user is admin (admin or super_admin)';
COMMENT ON COLUMN customers.permissions IS 'Additional granular permissions as JSON array';
COMMENT ON COLUMN customers.last_login IS 'Last login timestamp for security tracking';
COMMENT ON COLUMN customers.account_status IS 'Account status: active, inactive, or suspended';

-- 4. Create indexes for performance
CREATE INDEX idx_customers_user_role ON customers(user_role);
CREATE INDEX idx_customers_is_staff ON customers(is_staff);
CREATE INDEX idx_customers_is_admin ON customers(is_admin);
CREATE INDEX idx_customers_account_status ON customers(account_status);

-- 5. Create function to automatically set staff/admin flags
CREATE OR REPLACE FUNCTION update_staff_admin_flags()
RETURNS TRIGGER AS $$
BEGIN
    -- Update is_staff flag
    NEW.is_staff = CASE
        WHEN NEW.user_role IN ('support_agent', 'admin', 'super_admin') THEN TRUE
        ELSE FALSE
    END;

    -- Update is_admin flag
    NEW.is_admin = CASE
        WHEN NEW.user_role IN ('admin', 'super_admin') THEN TRUE
        ELSE FALSE
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. Create trigger to automatically maintain flags
CREATE TRIGGER trigger_update_staff_admin_flags
    BEFORE INSERT OR UPDATE OF user_role ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_staff_admin_flags();

-- 7. Insert sample staff and admin users
INSERT INTO customers (name, email, phone, state, lga, address, account_tier, user_role, preferences) VALUES

-- Support Agents
('Kemi Adebayo', 'kemi.adebayo@raqibtech.com', '+2348023456789', 'Lagos', 'Victoria Island', 'RaqibTech HQ, Victoria Island, Lagos', 'Gold', 'support_agent',
 '{"role": "support_agent", "department": "customer_support", "languages": ["English", "Yoruba"], "shift": "day"}'),

('Musa Ibrahim', 'musa.ibrahim@raqibtech.com', '+2347034567890', 'Abuja', 'Garki', 'RaqibTech Abuja Office, Garki, FCT', 'Silver', 'support_agent',
 '{"role": "support_agent", "department": "customer_support", "languages": ["English", "Hausa"], "shift": "night"}'),

-- Administrators
('Sarah Okafor', 'sarah.okafor@raqibtech.com', '+2348145678901', 'Lagos', 'Ikeja', 'RaqibTech HQ, Management Floor, Ikeja, Lagos', 'Platinum', 'admin',
 '{"role": "admin", "department": "management", "access_level": "business_analytics", "languages": ["English"]}'),

('Ahmed Bello', 'ahmed.bello@raqibtech.com', '+2349056789012', 'Kano', 'Municipal', 'RaqibTech Kano Office, Kano State', 'Platinum', 'admin',
 '{"role": "admin", "department": "operations", "access_level": "full_analytics", "languages": ["English", "Hausa"]}'),

-- Super Admin
('Dr. Raqib Omotosho', 'raqib@raqibtech.com', '+2347025965922', 'Lagos', 'Lekki', 'RaqibTech CEO Office, Lekki Phase 1, Lagos', 'Platinum', 'super_admin',
 '{"role": "super_admin", "department": "executive", "access_level": "full_system", "languages": ["English", "Yoruba"]}')

ON CONFLICT (email) DO NOTHING;

-- 8. Update existing customers to have explicit customer role
UPDATE customers
SET user_role = 'customer',
    account_status = 'active'
WHERE user_role IS NULL OR user_role = 'customer';

-- 9. Create view for user authentication
CREATE OR REPLACE VIEW user_authentication_view AS
SELECT
    customer_id,
    name,
    email,
    phone,
    user_role,
    is_staff,
    is_admin,
    account_status,
    permissions,
    last_login,
    CASE
        WHEN user_role = 'customer' THEN 'Customer'
        WHEN user_role = 'support_agent' THEN 'Support Agent'
        WHEN user_role = 'admin' THEN 'Administrator'
        WHEN user_role = 'super_admin' THEN 'Super Administrator'
    END as role_display_name,
    CASE
        WHEN user_role = 'customer' THEN 'Own data only'
        WHEN user_role = 'support_agent' THEN 'Cross-customer support'
        WHEN user_role = 'admin' THEN 'Business analytics'
        WHEN user_role = 'super_admin' THEN 'Full system access'
    END as access_description
FROM customers
WHERE account_status = 'active';

COMMENT ON VIEW user_authentication_view IS 'User authentication and role information for RBAC system';

-- 10. Function to authenticate user and return role info
CREATE OR REPLACE FUNCTION authenticate_user(user_email VARCHAR)
RETURNS TABLE(
    customer_id INTEGER,
    name VARCHAR,
    email VARCHAR,
    user_role user_role_enum,
    is_staff BOOLEAN,
    is_admin BOOLEAN,
    permissions JSONB,
    access_description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.customer_id,
        u.name,
        u.email,
        u.user_role,
        u.is_staff,
        u.is_admin,
        u.permissions,
        u.access_description
    FROM user_authentication_view u
    WHERE u.email = user_email
    AND u.account_status = 'active';

    -- Update last login
    UPDATE customers
    SET last_login = CURRENT_TIMESTAMP
    WHERE customers.email = user_email;
END;
$$ LANGUAGE plpgsql;

-- 11. Sample authentication examples
COMMENT ON FUNCTION authenticate_user IS 'Authenticate user by email and return role information for session context';

-- 12. Display current role distribution
SELECT
    user_role,
    COUNT(*) as user_count,
    STRING_AGG(name, ', ') as users
FROM customers
GROUP BY user_role
ORDER BY
    CASE user_role
        WHEN 'super_admin' THEN 1
        WHEN 'admin' THEN 2
        WHEN 'support_agent' THEN 3
        WHEN 'customer' THEN 4
    END;
