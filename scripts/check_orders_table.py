#!/usr/bin/env python3
"""
🔍 Orders Table Structure Checker
"""

import psycopg2
import os

def check_orders_table():
    """Check the structure of the orders table"""

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

        print('🔍 Checking orders table structure...')
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        print(f'\n📋 orders table columns:')
        for col_name, data_type, max_length, nullable in columns:
            length_info = f"({max_length})" if max_length else ""
            print(f'   {col_name}: {data_type}{length_info} ({"NULL" if nullable == "YES" else "NOT NULL"})')

        # Check current data
        print(f'\n📊 Current data in orders:')
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_count = cursor.fetchone()[0]
        print(f'   Total records: {total_count}')

        if total_count > 0:
            cursor.execute("SELECT order_id, customer_id, order_status, payment_method, total_amount FROM orders LIMIT 5")
            sample_data = cursor.fetchall()
            print(f'\n📄 Sample data (first 5 rows):')
            for i, row in enumerate(sample_data, 1):
                print(f'   Row {i}: {row}')

        # Check order_id data type specifically
        cursor.execute("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'orders' AND column_name = 'order_id'
        """)
        order_id_type = cursor.fetchone()
        print(f'\n🎯 order_id column data type: {order_id_type[0] if order_id_type else "Not found"}')

        cursor.close()
        conn.close()

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_orders_table()
