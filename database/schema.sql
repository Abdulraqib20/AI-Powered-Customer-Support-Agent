-- Chat Sessions and Conversation History
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_identifier VARCHAR(255), -- Email or username (optional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_data JSONB DEFAULT '{}', -- Store any additional session info
    UNIQUE(user_identifier)
);

CREATE TABLE chat_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    conversation_title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(conversation_id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('user', 'ai')),
    message_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Store query_type, execution_time, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation Context Storage for Enhanced Querying System
CREATE TABLE conversation_context (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL, -- 'customer_123' or 'anonymous'
    session_id VARCHAR(100), -- Session identifier
    query_type VARCHAR(50) NOT NULL, -- order_analytics, product_info, etc.
    entities JSONB DEFAULT '{}', -- Extracted entities from conversation
    sql_query TEXT, -- Generated SQL query
    execution_result JSONB DEFAULT '{}', -- Query results
    response_text TEXT, -- Generated AI response
    user_query TEXT NOT NULL, -- Original user query
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_user_sessions_last_active ON user_sessions(last_active);
CREATE INDEX idx_chat_conversations_session_id ON chat_conversations(session_id);
CREATE INDEX idx_chat_conversations_updated_at ON chat_conversations(updated_at DESC);
CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);

-- Conversation context indexes
CREATE INDEX idx_conversation_context_user_id ON conversation_context(user_id);
CREATE INDEX idx_conversation_context_session_id ON conversation_context(session_id);
CREATE INDEX idx_conversation_context_timestamp ON conversation_context(timestamp DESC);
CREATE INDEX idx_conversation_context_query_type ON conversation_context(query_type);
