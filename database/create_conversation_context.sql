-- Create conversation_context table for enhanced querying system
CREATE TABLE IF NOT EXISTS conversation_context (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    query_type VARCHAR(50) NOT NULL,
    entities JSONB DEFAULT '{}'::jsonb,
    sql_query TEXT,
    execution_result JSONB DEFAULT '{}'::jsonb,
    response_text TEXT,
    user_query TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_context_user_id ON conversation_context(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_session_id ON conversation_context(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_timestamp ON conversation_context(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_context_query_type ON conversation_context(query_type);
