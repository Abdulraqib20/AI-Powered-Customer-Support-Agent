-- =====================================================================
-- RBAC MIGRATION SCRIPT - SEAMLESS INTEGRATION
-- =====================================================================
-- This script extends the existing customer table with RBAC columns
-- without disrupting current data or workflow
-- =====================================================================

-- Add user role enum
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM (
        'guest', 'customer', 'support_agent', 'admin', 'super_admin'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add account status enum
DO $$ BEGIN
    CREATE TYPE account_status_enum AS ENUM (
        'active', 'suspended', 'deactivated', 'pending_verification'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =====================================================================
-- EXTEND EXISTING CUSTOMERS TABLE (NON-DISRUPTIVE)
-- =====================================================================

-- Add RBAC columns to existing customers table
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS user_role user_role_enum DEFAULT 'customer',
ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS account_status account_status_enum DEFAULT 'active',
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NULL; -- For staff accounts

-- Add comments for new columns
COMMENT ON COLUMN customers.user_role IS 'User role for RBAC system (customer, support_agent, admin, super_admin)';
COMMENT ON COLUMN customers.is_staff IS 'Quick flag to identify staff members';
COMMENT ON COLUMN customers.is_admin IS 'Quick flag to identify admin users';
COMMENT ON COLUMN customers.permissions IS 'Additional permissions in JSON format';
COMMENT ON COLUMN customers.last_login IS 'Last login timestamp for activity tracking';
COMMENT ON COLUMN customers.account_status IS 'Account status (active, suspended, deactivated)';
COMMENT ON COLUMN customers.password_hash IS 'Password hash for staff accounts (customers use external auth)';

-- =====================================================================
-- AUTOMATIC TRIGGERS FOR STAFF FLAGS
-- =====================================================================

-- Function to automatically set staff/admin flags based on role
CREATE OR REPLACE FUNCTION update_staff_flags()
RETURNS TRIGGER AS $$
BEGIN
    -- Set staff flag
    NEW.is_staff := NEW.user_role IN ('support_agent', 'admin', 'super_admin');

    -- Set admin flag
    NEW.is_admin := NEW.user_role IN ('admin', 'super_admin');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic flag updates
DROP TRIGGER IF EXISTS trigger_update_staff_flags ON customers;
CREATE TRIGGER trigger_update_staff_flags
    BEFORE INSERT OR UPDATE OF user_role ON customers
    FOR EACH ROW EXECUTE FUNCTION update_staff_flags();

-- =====================================================================
-- RBAC INDEXES FOR PERFORMANCE
-- =====================================================================

-- Add indexes for RBAC queries (if they don't exist)
CREATE INDEX IF NOT EXISTS idx_customers_user_role ON customers(user_role);
CREATE INDEX IF NOT EXISTS idx_customers_is_staff ON customers(is_staff);
CREATE INDEX IF NOT EXISTS idx_customers_is_admin ON customers(is_admin);
CREATE INDEX IF NOT EXISTS idx_customers_account_status ON customers(account_status);
CREATE INDEX IF NOT EXISTS idx_customers_last_login ON customers(last_login);

-- =====================================================================
-- SAMPLE STAFF ACCOUNTS (EXTENDS YOUR EXISTING DATA)
-- =====================================================================

-- Insert sample staff accounts (only if they don't exist)
INSERT INTO customers (name, email, phone, state, lga, address, account_tier, user_role, preferences, account_status, password_hash)
VALUES
-- Support Agents
('Kemi Adebayo', 'kemi.adebayo@raqibtech.com', '+2348012345678', 'Lagos', 'Ikeja', 'RaqibTech Support Center, Computer Village, Ikeja, Lagos', 'Gold', 'support_agent',
 '{"role": "support_agent", "department": "customer_service", "languages": ["English", "Yoruba"], "shift": "day"}', 'active',
 '$2b$12$LQv3c1yqBWVHxkd0LQ1u2.VQgZ3i/EFO/y5v5/7hN8lOjvzXnGIB.'), -- password: support123

('Musa Ibrahim', 'musa.ibrahim@raqibtech.com', '+2348023456789', 'Kano', 'Kano Municipal', 'RaqibTech Support Center, Sabon Gari, Kano', 'Gold', 'support_agent',
 '{"role": "support_agent", "department": "customer_service", "languages": ["English", "Hausa"], "shift": "night"}', 'active',
 '$2b$12$LQv3c1yqBWVHxkd0LQ1u2.VQgZ3i/EFO/y5v5/7hN8lOjvzXnGIB.'), -- password: support123

-- Admins
('Sarah Okafor', 'sarah.okafor@raqibtech.com', '+2348034567890', 'Abuja', 'Abuja Municipal', 'RaqibTech HQ, Central Business District, Abuja', 'Platinum', 'admin',
 '{"role": "admin", "department": "operations", "access_level": "business_analytics", "languages": ["English"]}', 'active',
 '$2b$12$8vU2rX1wZqCj5bK9mN3eP.4dF8g2hI6jK7lM9nO1pQ2rS3tU5vW6x'), -- password: admin123

('Ahmed Bello', 'ahmed.bello@raqibtech.com', '+2348045678901', 'Kaduna', 'Kaduna North', 'RaqibTech Admin Office, Kaduna North, Kaduna', 'Platinum', 'admin',
 '{"role": "admin", "department": "analytics", "access_level": "full_reports", "languages": ["English", "Hausa"]}', 'active',
 '$2b$12$8vU2rX1wZqCj5bK9mN3eP.4dF8g2hI6jK7lM9nO1pQ2rS3tU5vW6x'), -- password: admin123

-- Super Admin
('Dr. Raqib Omotosho', 'raqib@raqibtech.com', '+2347025965922', 'Lagos', 'Lekki', 'RaqibTech CEO Office, Lekki Phase 1, Lagos', 'Platinum', 'super_admin',
 '{"role": "super_admin", "department": "executive", "access_level": "full_system", "languages": ["English", "Yoruba"]}', 'active',
 '$2b$12$9wV3sY2xAqDk6cL0nO4fQ.5eG9h3iJ7kL8mN0oP2qR3sT4uV6wX7y') -- password: superadmin123

ON CONFLICT (email) DO UPDATE SET
    user_role = EXCLUDED.user_role,
    preferences = EXCLUDED.preferences,
    account_status = EXCLUDED.account_status,
    password_hash = EXCLUDED.password_hash;

-- =====================================================================
-- RBAC AUTHENTICATION VIEW
-- =====================================================================

-- Create view for authentication (staff accounts only)
CREATE OR REPLACE VIEW staff_authentication_view AS
SELECT
    customer_id,
    name,
    email,
    user_role,
    is_staff,
    is_admin,
    permissions,
    account_status,
    password_hash,
    last_login,
    created_at
FROM customers
WHERE user_role IN ('support_agent', 'admin', 'super_admin')
  AND account_status = 'active';

-- =====================================================================
-- AUTHENTICATION FUNCTION
-- =====================================================================

-- Function to authenticate staff users
CREATE OR REPLACE FUNCTION authenticate_staff_user(
    p_email VARCHAR(255),
    p_password_hash VARCHAR(255)
)
RETURNS TABLE (
    customer_id INTEGER,
    name VARCHAR(100),
    email VARCHAR(255),
    user_role user_role_enum,
    is_staff BOOLEAN,
    is_admin BOOLEAN,
    permissions JSONB,
    account_status account_status_enum
) AS $$
BEGIN
    -- Update last login
    UPDATE customers
    SET last_login = CURRENT_TIMESTAMP
    WHERE email = p_email AND password_hash = p_password_hash;

    -- Return user info
    RETURN QUERY
    SELECT
        c.customer_id,
        c.name,
        c.email,
        c.user_role,
        c.is_staff,
        c.is_admin,
        c.permissions,
        c.account_status
    FROM customers c
    WHERE c.email = p_email
      AND c.password_hash = p_password_hash
      AND c.account_status = 'active'
      AND c.user_role IN ('support_agent', 'admin', 'super_admin');
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- RBAC PERMISSION CHECKING FUNCTION
-- =====================================================================

-- Function to check if user has specific permission
CREATE OR REPLACE FUNCTION user_has_permission(
    p_customer_id INTEGER,
    p_permission VARCHAR(50)
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role_val user_role_enum;
BEGIN
    SELECT user_role INTO user_role_val
    FROM customers WHERE customer_id = p_customer_id;

    CASE user_role_val
        WHEN 'super_admin' THEN RETURN TRUE;
        WHEN 'admin' THEN
            RETURN p_permission IN ('read_own_data', 'read_all_customer_data', 'view_business_analytics',
                                   'generate_reports', 'view_platform_stats', 'manage_customer_accounts');
        WHEN 'support_agent' THEN
            RETURN p_permission IN ('read_own_data', 'read_all_customer_data', 'manage_customer_accounts');
        WHEN 'customer' THEN
            RETURN p_permission IN ('read_own_data');
        ELSE
            RETURN FALSE;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- MIGRATION COMPLETE MESSAGE
-- =====================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ RBAC Migration Complete!';
    RAISE NOTICE '📊 Extended customers table with RBAC columns';
    RAISE NOTICE '👥 Added sample staff accounts';
    RAISE NOTICE '🔐 Created authentication functions';
    RAISE NOTICE '🛡️ RBAC system ready for integration';
END $$;
