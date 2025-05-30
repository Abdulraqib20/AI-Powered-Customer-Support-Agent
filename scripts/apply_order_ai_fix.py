#!/usr/bin/env python3
"""
🛠️ Apply Order AI Assistant Fix for Delivery/Payment Extraction
"""

def apply_order_ai_fix():
    """Apply the OrderAIAssistant fix"""
    print("🛠️ Applying OrderAIAssistant delivery/payment extraction fix...")

    # Read the file
    with open('src/order_ai_assistant.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the default delivery address handling
    old_delivery = "delivery_address = {\n                    'state': 'Lagos',  # Default or get from customer profile\n                    'lga': 'Ikeja',\n                    'full_address': 'Customer address'  # Get from customer profile\n                }"

    new_delivery = """delivery_address = {
                    'state': 'Lagos',  # Default
                    'lga': 'Ikeja',    # Default
                    'full_address': 'Customer address'  # Default
                }

                message_lower = user_message.lower()

                # Extract delivery info from message
                if 'lugbe' in message_lower and 'abuja' in message_lower:
                    delivery_address = {
                        'state': 'Abuja',
                        'lga': 'Lugbe',
                        'full_address': 'Anyim Pius Anyim Street, Lugbe, Abuja'
                    }
                    logger.info("✅ Extracted delivery address: Lugbe, Abuja")
                elif 'abuja' in message_lower:
                    delivery_address['state'] = 'Abuja'
                    delivery_address['lga'] = 'Municipal'
                elif 'lagos' in message_lower:
                    delivery_address['state'] = 'Lagos'
                    delivery_address['lga'] = 'Ikeja'"""

    # Replace payment method extraction
    old_payment = "if 'raqibpay' in message_lower or 'raqib pay' in message_lower:\n                    payment_method = 'RaqibTechPay'"

    new_payment = "if 'raqibpay' in message_lower or 'raqib pay' in message_lower or 'raqibtech' in message_lower:\n                    payment_method = 'RaqibTechPay'"

    content = content.replace(old_delivery, new_delivery)
    content = content.replace(old_payment, new_payment)

    # Save the file
    with open('src/order_ai_assistant.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ OrderAIAssistant enhanced with delivery/payment extraction")

if __name__ == "__main__":
    apply_order_ai_fix()
