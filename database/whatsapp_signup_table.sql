-- WhatsApp Signup Progress Table
-- Tracks the progress of WhatsApp users during the signup/registration process

CREATE TABLE IF NOT EXISTS whatsapp_signup_progress (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    progress_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one signup process per phone number
    CONSTRAINT whatsapp_signup_phone_unique UNIQUE (phone_number)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_signup_phone ON whatsapp_signup_progress(phone_number);
CREATE INDEX IF NOT EXISTS idx_whatsapp_signup_session ON whatsapp_signup_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_signup_created ON whatsapp_signup_progress(created_at);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_whatsapp_signup_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_whatsapp_signup_updated_at
    BEFORE UPDATE ON whatsapp_signup_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_whatsapp_signup_timestamp();

-- Cleanup old signup progress (older than 24 hours)
CREATE OR REPLACE FUNCTION cleanup_old_whatsapp_signup_progress()
RETURNS void AS $$
BEGIN
    DELETE FROM whatsapp_signup_progress
    WHERE created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Comment for documentation
COMMENT ON TABLE whatsapp_signup_progress IS 'Tracks WhatsApp user signup progress and temporary data during registration process';
COMMENT ON COLUMN whatsapp_signup_progress.progress_data IS 'JSON data containing signup step progress (email, verification status, etc.)';
