-- Fix WhatsApp database schema issues
-- Run this on your PostgreSQL database

-- 1. Add unique constraint to whatsapp_sessions table
ALTER TABLE whatsapp_sessions
ADD CONSTRAINT whatsapp_sessions_user_identifier_unique
UNIQUE (user_identifier);

-- 2. Create the missing rate limiting function
CREATE OR REPLACE FUNCTION can_send_message(phone_number TEXT, max_messages INTEGER DEFAULT 10)
RETURNS BOOLEAN AS $$
DECLARE
    message_count INTEGER;
    last_message_time TIMESTAMP;
    time_window INTERVAL := INTERVAL '1 hour';
BEGIN
    -- Get message count in the last hour
    SELECT COUNT(*), MAX(created_at)
    INTO message_count, last_message_time
    FROM whatsapp_messages
    WHERE from_number = phone_number
    AND created_at > NOW() - time_window;

    -- Check if rate limit exceeded
    IF message_count >= max_messages THEN
        -- Check if enough time has passed since last message
        IF last_message_time IS NULL OR NOW() - last_message_time > time_window THEN
            RETURN TRUE; -- Reset after time window
        ELSE
            RETURN FALSE; -- Still rate limited
        END IF;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 3. Create index for better performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_from_number_created_at
ON whatsapp_messages(from_number, created_at);

-- 4. Ensure whatsapp_customers table has proper constraints
ALTER TABLE whatsapp_customers
ADD CONSTRAINT IF NOT EXISTS whatsapp_customers_phone_number_unique
UNIQUE (phone_number);

-- 5. Add any missing columns to whatsapp_sessions
ALTER TABLE whatsapp_sessions
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT NOW();

-- 6. Update existing sessions to have last_activity
UPDATE whatsapp_sessions
SET last_activity = created_at
WHERE last_activity IS NULL;

-- 7. Create function to update last activity
CREATE OR REPLACE FUNCTION update_whatsapp_session_activity(session_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE whatsapp_sessions
    SET last_activity = NOW()
    WHERE session_id = update_whatsapp_session_activity.session_id;
END;
$$ LANGUAGE plpgsql;
