-- RBAC Migration Script - Clean Version
-- Extends existing customer table with role-based access control

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

-- Add RBAC columns to existing customers table
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS user_role user_role_enum DEFAULT 'customer',
ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS account_status account_status_enum DEFAULT 'active',
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NULL;

-- Function to automatically set staff/admin flags based on role
CREATE OR REPLACE FUNCTION update_staff_flags()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_staff := NEW.user_role IN ('support_agent', 'admin', 'super_admin');
    NEW.is_admin := NEW.user_role IN ('admin', 'super_admin');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic flag updates
DROP TRIGGER IF EXISTS trigger_update_staff_flags ON customers;
CREATE TRIGGER trigger_update_staff_flags
    BEFORE INSERT OR UPDATE OF user_role ON customers
    FOR EACH ROW EXECUTE FUNCTION update_staff_flags();

-- Add indexes for RBAC queries
CREATE INDEX IF NOT EXISTS idx_customers_user_role ON customers(user_role);
CREATE INDEX IF NOT EXISTS idx_customers_is_staff ON customers(is_staff);
CREATE INDEX IF NOT EXISTS idx_customers_account_status ON customers(account_status);

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

-- Complete message
DO $$
BEGIN
    RAISE NOTICE 'RBAC Migration Complete Successfully!';
    RAISE NOTICE 'Extended customers table with RBAC columns';
    RAISE NOTICE 'RBAC system ready for integration';
END $$;
