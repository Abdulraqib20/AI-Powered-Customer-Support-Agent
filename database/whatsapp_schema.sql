-- WhatsApp Business API Integration Schema
-- Add WhatsApp-specific tables to existing Nigerian E-commerce database

-- Add WhatsApp number to customers table
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20) UNIQUE,
ADD COLUMN IF NOT EXISTS whatsapp_opt_in BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS whatsapp_verified BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS whatsapp_first_contact TIMESTAMP;

-- WhatsApp conversations table
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id),
    conversation_status VARCHAR(20) DEFAULT 'active', -- active, paused, completed
    last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id UUID REFERENCES user_sessions(session_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp messages table
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES whatsapp_conversations(conversation_id) ON DELETE CASCADE,
    whatsapp_message_id VARCHAR(100) UNIQUE, -- WhatsApp's message ID
    phone_number VARCHAR(20) NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id),
    message_type VARCHAR(20) NOT NULL, -- text, image, button, interactive, template
    direction VARCHAR(10) NOT NULL, -- inbound, outbound
    content TEXT,
    media_url TEXT, -- For images, videos, documents
    button_reply TEXT, -- For button interactions
    interactive_reply JSONB, -- For interactive message replies
    status VARCHAR(20) DEFAULT 'sent', -- sent, delivered, read, failed
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}' -- Additional WhatsApp-specific data
);

-- WhatsApp session state table (extends existing session management)
CREATE TABLE IF NOT EXISTS whatsapp_session_state (
    session_id UUID PRIMARY KEY REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    shopping_context JSONB DEFAULT '{}', -- Cart items, conversation stage
    last_product_mentioned JSONB DEFAULT '{}',
    delivery_address TEXT,
    payment_method VARCHAR(50),
    conversation_stage VARCHAR(50) DEFAULT 'browsing',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp templates table (for message templates)
CREATE TABLE IF NOT EXISTS whatsapp_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) NOT NULL UNIQUE,
    template_category VARCHAR(50) NOT NULL, -- marketing, utility, authentication
    language_code VARCHAR(10) DEFAULT 'en',
    header_text TEXT,
    body_text TEXT NOT NULL,
    footer_text TEXT,
    buttons JSONB DEFAULT '[]', -- Array of button objects
    variables JSONB DEFAULT '[]', -- Template variables
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp webhook events log
CREATE TABLE IF NOT EXISTS whatsapp_webhook_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- message, status, error
    phone_number VARCHAR(20),
    webhook_payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_phone ON whatsapp_conversations(phone_number);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_customer ON whatsapp_conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_session ON whatsapp_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_conversations_status ON whatsapp_conversations(conversation_status);

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_conversation ON whatsapp_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_phone ON whatsapp_messages(phone_number);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_customer ON whatsapp_messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_direction ON whatsapp_messages(direction);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_timestamp ON whatsapp_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_wa_id ON whatsapp_messages(whatsapp_message_id);

CREATE INDEX IF NOT EXISTS idx_whatsapp_session_phone ON whatsapp_session_state(phone_number);
CREATE INDEX IF NOT EXISTS idx_whatsapp_session_updated ON whatsapp_session_state(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_name ON whatsapp_templates(template_name);
CREATE INDEX IF NOT EXISTS idx_whatsapp_templates_category ON whatsapp_templates(template_category);

CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_type ON whatsapp_webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_processed ON whatsapp_webhook_events(processed);
CREATE INDEX IF NOT EXISTS idx_whatsapp_webhook_created ON whatsapp_webhook_events(created_at DESC);

-- Insert default WhatsApp message templates
INSERT INTO whatsapp_templates (template_name, template_category, body_text, variables) VALUES
('welcome_message', 'utility',
 'Welcome to raqibtech! 🎉\n\nI''m your AI shopping assistant. I can help you:\n• 🛍️ Browse and buy products\n• 📦 Track your orders\n• 💬 Get customer support\n• 🔍 Find specific items\n\nWhat would you like to do today?',
 '[]'),
('order_confirmation', 'utility',
 'Order Confirmed! ✅\n\n📦 Order ID: {{1}}\n💰 Total: {{2}}\n🚚 Delivery: {{3}} days to {{4}}\n💳 Payment: {{5}}\n\nTrack your order: https://raqibtech.com/orders/{{6}}',
 '["order_id", "total_amount", "delivery_days", "delivery_state", "payment_method", "tracking_id"]'),
('product_found', 'utility',
 'Found {{1}} - {{2}} 🔍\n\n📱 {{3}}\n📦 {{4}}\n⭐ Rating: {{5}}\n\nReply:\n1️⃣ Add to cart\n2️⃣ More details\n3️⃣ Similar products',
 '["product_name", "price_formatted", "description", "stock_status", "rating"]')
ON CONFLICT (template_name) DO NOTHING;

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_whatsapp_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_whatsapp_conversations_updated_at
    BEFORE UPDATE ON whatsapp_conversations
    FOR EACH ROW EXECUTE FUNCTION update_whatsapp_timestamp();

CREATE TRIGGER trigger_whatsapp_session_state_updated_at
    BEFORE UPDATE ON whatsapp_session_state
    FOR EACH ROW EXECUTE FUNCTION update_whatsapp_timestamp();
