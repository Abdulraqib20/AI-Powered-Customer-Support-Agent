#!/usr/bin/env python3
"""
🧹 User Sessions Cleanup Script
Fixes duplicate key violations and cross-user contamination
"""

import psycopg2
import os
from datetime import datetime

def cleanup_user_sessions():
    """Clean up user_sessions table to fix authentication issues"""

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'nigerian_ecommerce'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'oracle')
        )

        cursor = conn.cursor()

        print('🔍 Checking user_sessions table for issues...')

        # Check total records
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        total_count = cursor.fetchone()[0]
        print(f'📊 Total sessions: {total_count}')

        # Find sessions with NULL user_identifier (anonymous sessions)
        cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE user_identifier IS NULL")
        null_count = cursor.fetchone()[0]
        print(f'👤 Anonymous sessions: {null_count}')

        # Find actual user sessions
        cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE user_identifier IS NOT NULL")
        user_count = cursor.fetchone()[0]
        print(f'🔐 User sessions: {user_count}')

        # Check for duplicates by user_identifier (excluding NULL)
        cursor.execute("""
            SELECT user_identifier, COUNT(*) as count
            FROM user_sessions
            WHERE user_identifier IS NOT NULL
            GROUP BY user_identifier
            HAVING COUNT(*) > 1
        """)

        duplicates = cursor.fetchall()
        if duplicates:
            print(f'\n❌ Found {len(duplicates)} users with duplicate sessions:')
            for user_id, count in duplicates:
                print(f'   {user_id}: {count} sessions')

            # Delete all duplicate entries except the most recent one
            print('\n🗑️ Cleaning up duplicate user sessions...')
            cursor.execute("""
                DELETE FROM user_sessions
                WHERE ctid NOT IN (
                    SELECT DISTINCT ON (user_identifier) ctid
                    FROM user_sessions
                    WHERE user_identifier IS NOT NULL
                    ORDER BY user_identifier, last_active DESC
                )
                AND user_identifier IS NOT NULL
            """)
            deleted_count = cursor.rowcount
            print(f'✅ Deleted {deleted_count} duplicate user sessions')
        else:
            print('\n✅ No duplicate user sessions found')

        # Clean up old anonymous sessions (keep only recent ones)
        print('\n🧹 Cleaning up old anonymous sessions...')
        cursor.execute("""
            DELETE FROM user_sessions
            WHERE user_identifier IS NULL
            AND last_active < NOW() - INTERVAL '24 hours'
        """)
        deleted_anonymous = cursor.rowcount
        print(f'✅ Deleted {deleted_anonymous} old anonymous sessions')

        # Check for the specific problematic user
        cursor.execute("""
            SELECT session_id, user_identifier, created_at, last_active, session_data
            FROM user_sessions
            WHERE user_identifier = 'chineduobi.@yahoo.com'
        """)

        entries = cursor.fetchall()
        if entries:
            print(f'\n📋 Found {len(entries)} entries for chineduobi.@yahoo.com:')
            for entry in entries:
                print(f'   Session: {entry[0]}, Created: {entry[2]}, Last Active: {entry[3]}')

            # Clean up this specific user to allow fresh login
            cursor.execute("DELETE FROM user_sessions WHERE user_identifier = 'chineduobi.@yahoo.com'")
            print(f'🗑️ Deleted all sessions for chineduobi.@yahoo.com to allow fresh login')

        # Show final counts
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        final_total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE user_identifier IS NOT NULL")
        final_users = cursor.fetchone()[0]

        print(f'\n📊 Final counts:')
        print(f'   Total sessions: {final_total}')
        print(f'   User sessions: {final_users}')
        print(f'   Anonymous sessions: {final_total - final_users}')

        conn.commit()
        cursor.close()
        conn.close()
        print('\n✅ Database cleanup completed successfully!')

    except Exception as e:
        print(f'❌ Cleanup error: {e}')

if __name__ == '__main__':
    cleanup_user_sessions()
