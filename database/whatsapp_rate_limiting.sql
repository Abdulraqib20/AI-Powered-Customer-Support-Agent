-- WhatsApp Rate Limiting System
-- Prevents abuse and manages backend resource usage

-- Rate limiting configuration table
CREATE TABLE IF NOT EXISTS whatsapp_rate_limits (
    limit_id SERIAL PRIMARY KEY,
    user_tier VARCHAR(20) NOT NULL UNIQUE, -- 'anonymous', 'authenticated', 'premium', 'vip'
    conversations_per_day INTEGER NOT NULL DEFAULT 5,
    messages_per_hour INTEGER NOT NULL DEFAULT 20,
    burst_allowance INTEGER NOT NULL DEFAULT 30,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User rate limiting tracking table
CREATE TABLE IF NOT EXISTS whatsapp_user_rate_tracking (
    tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id),
    user_tier VARCHAR(20) DEFAULT 'anonymous',

    -- Daily conversation tracking
    conversations_today INTEGER DEFAULT 0,
    daily_reset_date DATE DEFAULT CURRENT_DATE,

    -- Hourly message tracking
    messages_this_hour INTEGER DEFAULT 0,
    hourly_reset_time TIMESTAMP DEFAULT date_trunc('hour', CURRENT_TIMESTAMP),

    -- Burst tracking (rolling 10-minute window)
    burst_count INTEGER DEFAULT 0,
    burst_window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Rate limit violations
    total_violations INTEGER DEFAULT 0,
    last_violation_time TIMESTAMP,
    is_temporarily_blocked BOOLEAN DEFAULT FALSE,
    block_expires_at TIMESTAMP,

    -- Metadata
    first_tracked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_phone_tracking UNIQUE (phone_number)
);

-- Rate limiting events log (for monitoring and analysis)
CREATE TABLE IF NOT EXISTS whatsapp_rate_limit_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    customer_id INTEGER,
    event_type VARCHAR(30) NOT NULL, -- 'conversation_created', 'message_sent', 'limit_exceeded', 'block_applied'
    limit_type VARCHAR(20) NOT NULL, -- 'daily_conversation', 'hourly_message', 'burst'
    current_count INTEGER,
    limit_threshold INTEGER,
    user_tier VARCHAR(20),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default rate limiting tiers
INSERT INTO whatsapp_rate_limits (user_tier, conversations_per_day, messages_per_hour, burst_allowance, description) VALUES
('anonymous', 5, 20, 30, 'New/unverified WhatsApp users'),
('authenticated', 20, 60, 100, 'Email-verified customers'),
('premium', 50, 120, 200, 'Premium subscription customers'),
('vip', 999, 300, 500, 'VIP/Enterprise customers')
ON CONFLICT (user_tier) DO NOTHING;

-- Function to get user tier based on customer status
CREATE OR REPLACE FUNCTION get_user_tier_for_rate_limiting(p_customer_id INTEGER)
RETURNS VARCHAR(20) AS $$
DECLARE
    customer_record RECORD;
    tier VARCHAR(20) := 'anonymous';
BEGIN
    -- Get customer information including account tier
    SELECT c.account_tier, c.email
    FROM customers c
    WHERE c.customer_id = p_customer_id
    INTO customer_record;

    IF customer_record IS NULL THEN
        RETURN 'anonymous';
    END IF;

    -- Use existing account tier system
    IF customer_record.email IS NOT NULL THEN
        CASE customer_record.account_tier
            WHEN 'Bronze' THEN tier := 'bronze';
            WHEN 'Silver' THEN tier := 'silver';
            WHEN 'Gold' THEN tier := 'gold';
            WHEN 'Platinum' THEN tier := 'platinum';
            ELSE tier := 'bronze'; -- Default for customers
        END CASE;
    END IF;

    RETURN tier;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can start new conversation
CREATE OR REPLACE FUNCTION can_start_conversation(p_phone_number VARCHAR(20), p_customer_id INTEGER DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    tracking_record RECORD;
    rate_limits RECORD;
    user_tier VARCHAR(20);
    result JSONB := '{"allowed": true}';
    current_date DATE := CURRENT_DATE;
BEGIN
    -- Determine user tier
    IF p_customer_id IS NOT NULL THEN
        user_tier := get_user_tier_for_rate_limiting(p_customer_id);
    ELSE
        user_tier := 'anonymous';
    END IF;

    -- Get rate limits for user tier
    SELECT * FROM whatsapp_rate_limits WHERE user_tier = user_tier INTO rate_limits;

    -- Get or create tracking record
    INSERT INTO whatsapp_user_rate_tracking (phone_number, customer_id, user_tier)
    VALUES (p_phone_number, p_customer_id, user_tier)
    ON CONFLICT (phone_number)
    DO UPDATE SET
        customer_id = COALESCE(EXCLUDED.customer_id, whatsapp_user_rate_tracking.customer_id),
        user_tier = EXCLUDED.user_tier,
        last_activity = CURRENT_TIMESTAMP
    RETURNING * INTO tracking_record;

    -- Check if user is temporarily blocked
    IF tracking_record.is_temporarily_blocked AND tracking_record.block_expires_at > CURRENT_TIMESTAMP THEN
        result := jsonb_build_object(
            'allowed', false,
            'reason', 'temporarily_blocked',
            'block_expires_at', tracking_record.block_expires_at,
            'message', 'Your account is temporarily blocked due to rate limit violations. Please try again later.'
        );
        RETURN result;
    END IF;

    -- Reset daily counter if needed
    IF tracking_record.daily_reset_date < current_date THEN
        UPDATE whatsapp_user_rate_tracking
        SET conversations_today = 0, daily_reset_date = current_date
        WHERE phone_number = p_phone_number;
        tracking_record.conversations_today := 0;
    END IF;

    -- Check daily conversation limit
    IF tracking_record.conversations_today >= rate_limits.conversations_per_day THEN
        result := jsonb_build_object(
            'allowed', false,
            'reason', 'daily_limit_exceeded',
            'current_count', tracking_record.conversations_today,
            'limit', rate_limits.conversations_per_day,
            'user_tier', user_tier,
            'reset_time', (current_date + INTERVAL '1 day')::timestamp,
            'message', format('Daily conversation limit (%s) reached. Limit resets at midnight.', rate_limits.conversations_per_day)
        );

        -- Log rate limit event
        INSERT INTO whatsapp_rate_limit_events (phone_number, customer_id, event_type, limit_type, current_count, limit_threshold, user_tier)
        VALUES (p_phone_number, p_customer_id, 'limit_exceeded', 'daily_conversation', tracking_record.conversations_today, rate_limits.conversations_per_day, user_tier);

        RETURN result;
    END IF;

    -- If all checks pass, increment conversation counter
    UPDATE whatsapp_user_rate_tracking
    SET conversations_today = conversations_today + 1,
        last_activity = CURRENT_TIMESTAMP
    WHERE phone_number = p_phone_number;

    -- Log successful conversation creation
    INSERT INTO whatsapp_rate_limit_events (phone_number, customer_id, event_type, limit_type, current_count, limit_threshold, user_tier)
    VALUES (p_phone_number, p_customer_id, 'conversation_created', 'daily_conversation', tracking_record.conversations_today + 1, rate_limits.conversations_per_day, user_tier);

    result := jsonb_build_object(
        'allowed', true,
        'remaining_conversations', rate_limits.conversations_per_day - (tracking_record.conversations_today + 1),
        'user_tier', user_tier,
        'limit', rate_limits.conversations_per_day
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can send message (within conversation)
CREATE OR REPLACE FUNCTION can_send_message(p_phone_number VARCHAR(20), p_customer_id INTEGER DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    tracking_record RECORD;
    rate_limits RECORD;
    user_tier VARCHAR(20);
    result JSONB := '{"allowed": true}';
    current_hour TIMESTAMP := date_trunc('hour', CURRENT_TIMESTAMP);
    burst_window_minutes INTEGER := 10;
    burst_window_start TIMESTAMP := CURRENT_TIMESTAMP - INTERVAL '10 minutes';
BEGIN
    -- Determine user tier
    IF p_customer_id IS NOT NULL THEN
        user_tier := get_user_tier_for_rate_limiting(p_customer_id);
    ELSE
        user_tier := 'anonymous';
    END IF;

    -- Get rate limits and tracking record
    SELECT * FROM whatsapp_rate_limits wrl WHERE wrl.user_tier = user_tier INTO rate_limits;
    SELECT * FROM whatsapp_user_rate_tracking WHERE phone_number = p_phone_number INTO tracking_record;

    IF tracking_record IS NULL THEN
        -- Create tracking record if it doesn't exist
        INSERT INTO whatsapp_user_rate_tracking (phone_number, customer_id, user_tier)
        VALUES (p_phone_number, p_customer_id, user_tier)
        RETURNING * INTO tracking_record;
    END IF;

    -- Check if user is temporarily blocked
    IF tracking_record.is_temporarily_blocked AND tracking_record.block_expires_at > CURRENT_TIMESTAMP THEN
        result := jsonb_build_object(
            'allowed', false,
            'reason', 'temporarily_blocked',
            'message', 'Account temporarily blocked. Please try again later.'
        );
        RETURN result;
    END IF;

    -- Reset hourly counter if needed
    IF tracking_record.hourly_reset_time < current_hour THEN
        UPDATE whatsapp_user_rate_tracking
        SET messages_this_hour = 0, hourly_reset_time = current_hour
        WHERE phone_number = p_phone_number;
        tracking_record.messages_this_hour := 0;
    END IF;

    -- Reset burst counter if needed (10-minute window)
    IF tracking_record.burst_window_start < burst_window_start THEN
        UPDATE whatsapp_user_rate_tracking
        SET burst_count = 0, burst_window_start = CURRENT_TIMESTAMP
        WHERE phone_number = p_phone_number;
        tracking_record.burst_count := 0;
    END IF;

    -- Check hourly message limit
    IF tracking_record.messages_this_hour >= rate_limits.messages_per_hour THEN
        result := jsonb_build_object(
            'allowed', false,
            'reason', 'hourly_limit_exceeded',
            'current_count', tracking_record.messages_this_hour,
            'limit', rate_limits.messages_per_hour,
            'reset_time', (current_hour + INTERVAL '1 hour'),
            'message', format('Hourly message limit (%s) reached. Resets at %s.',
                             rate_limits.messages_per_hour,
                             to_char(current_hour + INTERVAL '1 hour', 'HH24:MI'))
        );

        INSERT INTO whatsapp_rate_limit_events (phone_number, customer_id, event_type, limit_type, current_count, limit_threshold, user_tier)
        VALUES (p_phone_number, p_customer_id, 'limit_exceeded', 'hourly_message', tracking_record.messages_this_hour, rate_limits.messages_per_hour, user_tier);

        RETURN result;
    END IF;

    -- Check burst limit
    IF tracking_record.burst_count >= rate_limits.burst_allowance THEN
        result := jsonb_build_object(
            'allowed', false,
            'reason', 'burst_limit_exceeded',
            'current_count', tracking_record.burst_count,
            'limit', rate_limits.burst_allowance,
            'message', format('Burst limit (%s messages in 10 minutes) exceeded. Please slow down.', rate_limits.burst_allowance)
        );

        INSERT INTO whatsapp_rate_limit_events (phone_number, customer_id, event_type, limit_type, current_count, limit_threshold, user_tier)
        VALUES (p_phone_number, p_customer_id, 'limit_exceeded', 'burst', tracking_record.burst_count, rate_limits.burst_allowance, user_tier);

        RETURN result;
    END IF;

    -- If all checks pass, increment counters
    UPDATE whatsapp_user_rate_tracking
    SET messages_this_hour = messages_this_hour + 1,
        burst_count = burst_count + 1,
        last_activity = CURRENT_TIMESTAMP
    WHERE phone_number = p_phone_number;

    -- Log successful message
    INSERT INTO whatsapp_rate_limit_events (phone_number, customer_id, event_type, limit_type, current_count, limit_threshold, user_tier)
    VALUES (p_phone_number, p_customer_id, 'message_sent', 'hourly_message', tracking_record.messages_this_hour + 1, rate_limits.messages_per_hour, user_tier);

    result := jsonb_build_object(
        'allowed', true,
        'remaining_messages_hour', rate_limits.messages_per_hour - (tracking_record.messages_this_hour + 1),
        'remaining_burst', rate_limits.burst_allowance - (tracking_record.burst_count + 1),
        'user_tier', user_tier
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to temporarily block abusive users
CREATE OR REPLACE FUNCTION apply_temporary_block(p_phone_number VARCHAR(20), p_duration_hours INTEGER DEFAULT 24)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE whatsapp_user_rate_tracking
    SET is_temporarily_blocked = TRUE,
        block_expires_at = CURRENT_TIMESTAMP + (p_duration_hours || ' hours')::INTERVAL,
        total_violations = total_violations + 1,
        last_violation_time = CURRENT_TIMESTAMP
    WHERE phone_number = p_phone_number;

    -- Log the block event
    INSERT INTO whatsapp_rate_limit_events (phone_number, event_type, limit_type, details)
    VALUES (p_phone_number, 'block_applied', 'violation',
            jsonb_build_object('duration_hours', p_duration_hours, 'reason', 'repeated_violations'));

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rate_tracking_phone ON whatsapp_user_rate_tracking(phone_number);
CREATE INDEX IF NOT EXISTS idx_rate_tracking_customer ON whatsapp_user_rate_tracking(customer_id);
CREATE INDEX IF NOT EXISTS idx_rate_tracking_tier ON whatsapp_user_rate_tracking(user_tier);
CREATE INDEX IF NOT EXISTS idx_rate_tracking_blocked ON whatsapp_user_rate_tracking(is_temporarily_blocked, block_expires_at);
CREATE INDEX IF NOT EXISTS idx_rate_tracking_daily ON whatsapp_user_rate_tracking(daily_reset_date);
CREATE INDEX IF NOT EXISTS idx_rate_tracking_hourly ON whatsapp_user_rate_tracking(hourly_reset_time);

CREATE INDEX IF NOT EXISTS idx_rate_events_phone ON whatsapp_rate_limit_events(phone_number);
CREATE INDEX IF NOT EXISTS idx_rate_events_type ON whatsapp_rate_limit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_rate_events_created ON whatsapp_rate_limit_events(created_at DESC);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_rate_limit_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_rate_limits_updated_at
    BEFORE UPDATE ON whatsapp_rate_limits
    FOR EACH ROW EXECUTE FUNCTION update_rate_limit_timestamp();

-- Cleanup function for old rate limit events (keep 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_rate_limit_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM whatsapp_rate_limit_events
    WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- View for admin monitoring
CREATE OR REPLACE VIEW v_rate_limit_summary AS
SELECT
    t.phone_number,
    t.user_tier,
    t.conversations_today,
    l.conversations_per_day,
    t.messages_this_hour,
    l.messages_per_hour,
    t.burst_count,
    l.burst_allowance,
    t.total_violations,
    t.is_temporarily_blocked,
    t.block_expires_at,
    t.last_activity,
    c.name as customer_name,
    c.email as customer_email
FROM whatsapp_user_rate_tracking t
JOIN whatsapp_rate_limits l ON t.user_tier = l.user_tier
LEFT JOIN customers c ON t.customer_id = c.customer_id
ORDER BY t.last_activity DESC;

COMMENT ON TABLE whatsapp_rate_limits IS 'Rate limiting configuration for different user tiers';
COMMENT ON TABLE whatsapp_user_rate_tracking IS 'Tracks rate limiting counters and violations for each WhatsApp user';
COMMENT ON TABLE whatsapp_rate_limit_events IS 'Audit log of all rate limiting events for monitoring and analysis';
