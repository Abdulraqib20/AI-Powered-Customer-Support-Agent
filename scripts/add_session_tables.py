#!/usr/bin/env python3
"""
Add Session Management Tables to Database
"""

import psycopg2
import os

def add_session_tables():
    """Add session management tables to the database"""

    try:
        # Connect to PostgreSQL using environment variables
        from config.appconfig import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        print('🗄️ Connected to database')
        cur = conn.cursor()

        # Create the new session tables
        session_sql = '''
        -- Chat Sessions and Conversation History
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_identifier VARCHAR(255), -- Email or username (optional)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_data JSONB DEFAULT '{}', -- Store any additional session info
            UNIQUE(user_identifier)
        );

        CREATE TABLE IF NOT EXISTS chat_conversations (
            conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES user_sessions(session_id) ON DELETE CASCADE,
            conversation_title VARCHAR(255) DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT true
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID REFERENCES chat_conversations(conversation_id) ON DELETE CASCADE,
            sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('user', 'ai')),
            message_content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}', -- Store query_type, execution_time, etc.
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_user_sessions_last_active ON user_sessions(last_active);
        CREATE INDEX IF NOT EXISTS idx_chat_conversations_session_id ON chat_conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_conversations_updated_at ON chat_conversations(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
        '''

        cur.execute(session_sql)
        conn.commit()

        print('✅ Session tables created successfully')
        print('📊 Tables: user_sessions, chat_conversations, chat_messages')
        print('🔧 Indexes created for performance')

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f'❌ Error creating session tables: {e}')
        print('💡 Make sure PostgreSQL is running and credentials are correct')
        print('🔧 Set environment variables: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD')
        return False

if __name__ == '__main__':
    print('🚀 Adding session management tables to database...')
    success = add_session_tables()

    if success:
        print('✅ Session management setup complete!')
        print('🎉 You can now run the Flask app with session support!')
    else:
        print('❌ Setup failed!')
        exit(1)
