#!/usr/bin/env python3
"""
Add Test Customer for Login Testing
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from config.database_config import DatabaseManager, CustomerRepository

def add_test_customer():
    """Add a test customer to the database"""

    print("🧪 Adding test customer for login testing...")

    try:
        # Initialize database
        db_manager = DatabaseManager()
        customer_repo = CustomerRepository(db_manager)

        # Test customer data
        test_customer = {
            'name': 'Abdul Raqib Shakir',
            'email': 'abdulraqibshakir03@gmail.com',
            'phone': '08012345678',  # Shorter phone format
            'state': 'Lagos',
            'lga': 'Ikeja',
            'address': '123 Technology Avenue, Ikeja, Lagos State',
            'account_tier': 'Gold',
            'preferences': {
                'newsletter': True,
                'sms_notifications': True,
                'preferred_payment': 'Card',
                'preferred_delivery_time': 'Evening'
            }
        }

        # Check if customer already exists
        existing_customer = customer_repo.get_customer_by_email(test_customer['email'])
        if existing_customer:
            print(f"✅ Customer already exists: {existing_customer['name']} (ID: {existing_customer['customer_id']})")
            return existing_customer['customer_id']

        # Create customer
        customer_id = customer_repo.create_customer(test_customer)
        print(f"✅ Test customer created successfully!")
        print(f"📋 Customer ID: {customer_id}")
        print(f"👤 Name: {test_customer['name']}")
        print(f"📧 Email: {test_customer['email']}")
        print(f"📱 Phone: {test_customer['phone']}")
        print(f"🏠 Location: {test_customer['lga']}, {test_customer['state']}")
        print(f"⭐ Account Tier: {test_customer['account_tier']}")

        return customer_id

    except Exception as e:
        print(f"❌ Error adding test customer: {e}")
        return None

def add_test_order(customer_id):
    """Add a test order for the customer"""

    try:
        from config.database_config import OrderRepository
        from datetime import datetime, timedelta

        db_manager = DatabaseManager()
        order_repo = OrderRepository(db_manager)

        # Test order data
        test_order = {
            'customer_id': customer_id,
            'order_status': 'Processing',
            'payment_method': 'Card',
            'total_amount': 85000.00,  # ₦85,000
            'delivery_date': (datetime.now() + timedelta(days=3)).date(),
            'product_category': 'Electronics'
        }

        order_id = order_repo.create_order(test_order)
        print(f"✅ Test order created: Order #{order_id}")
        print(f"💰 Amount: ₦{test_order['total_amount']:,.2f}")
        print(f"🚚 Expected Delivery: {test_order['delivery_date']}")

        return order_id

    except Exception as e:
        print(f"❌ Error adding test order: {e}")
        return None

if __name__ == "__main__":
    customer_id = add_test_customer()

    if customer_id:
        print("\n🛍️ Adding test order...")
        add_test_order(customer_id)

        print("\n🎉 Test setup complete!")
        print("\n📝 You can now test login with:")
        print("Email: abdulraqibshakir03@gmail.com")
        print("This customer has orders and can access personal data.")
    else:
        print("❌ Failed to set up test customer")
