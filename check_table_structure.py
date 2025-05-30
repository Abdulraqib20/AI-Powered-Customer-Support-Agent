#!/usr/bin/env python3
"""
🔍 Database Table Structure Checker
"""

import psycopg2
import os

def check_table_structure():
    """Check the structure of the user_sessions table"""

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

        print('🔍 Checking user_sessions table structure...')
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_sessions'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        print(f'\n📋 user_sessions table columns:')
        for col_name, data_type, nullable in columns:
            print(f'   {col_name}: {data_type} ({"NULL" if nullable == "YES" else "NOT NULL"})')

        # Check current data
        print(f'\n📊 Current data in user_sessions:')
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        total_count = cursor.fetchone()[0]
        print(f'   Total records: {total_count}')

        if total_count > 0:
            cursor.execute("SELECT * FROM user_sessions LIMIT 3")
            sample_data = cursor.fetchall()
            print(f'\n📄 Sample data (first 3 rows):')
            for i, row in enumerate(sample_data, 1):
                print(f'   Row {i}: {row}')

        # Check for duplicates by user_identifier
        cursor.execute("""
            SELECT user_identifier, COUNT(*) as count
            FROM user_sessions
            GROUP BY user_identifier
            HAVING COUNT(*) > 1
        """)

        duplicates = cursor.fetchall()
        if duplicates:
            print(f'\n❌ Found {len(duplicates)} duplicate user_identifiers:')
            for user_id, count in duplicates:
                print(f'   {user_id}: {count} entries')
        else:
            print(f'\n✅ No duplicate user_identifiers found')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_table_structure()
