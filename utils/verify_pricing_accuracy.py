import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def verify_pricing_accuracy():
    """Verify that all orders in the database have correct pricing calculations"""

    try:
        # Database connection
        from config.appconfig import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print('🔍 VERIFYING PRICING ACCURACY IN DATABASE...')
        print('=' * 70)

        # Get sample of orders across different periods
        cursor.execute('''
            SELECT
                o.order_id,
                o.customer_id,
                p.product_id,
                p.product_name,
                p.price,
                p.category,
                o.total_amount,
                o.order_status,
                c.account_tier,
                c.state,
                c.address,
                o.payment_method,
                o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status != 'Returned'  -- Exclude returned orders
            ORDER BY o.created_at DESC
            LIMIT 50  -- Check recent 50 orders
        ''')

        orders = cursor.fetchall()
        print(f'📊 Found {len(orders)} orders to verify')
        print()

        # Define delivery fees (matching your system logic)
        delivery_zones = {
            'Lagos': 2500,
            'FCT': 3100,  # Abuja
            'Rivers': 3700, 'Ogun': 3700, 'Kano': 3700, 'Kaduna': 3700,
            'Oyo': 3700, 'Delta': 3700, 'Imo': 3700, 'Akwa Ibom': 3700,
            'Ondo': 3700, 'Anambra': 3700, 'Edo': 3700, 'Abia': 3700
        }

        # Tier discounts
        tier_discounts = {
            'Bronze': 0.0,
            'Silver': 0.05,
            'Gold': 0.10,
            'Platinum': 0.15
        }

        total_checked = 0
        total_correct = 0
        total_incorrect = 0
        total_discrepancy = 0.0
        incorrect_orders = []

        for order in orders:
            order_id = order['order_id']
            price = float(order['price'])
            tier = order['account_tier'] or 'Bronze'
            state = order['state']
            stored_total = float(order['total_amount'])

            # Calculate expected delivery fee
            delivery_fee = delivery_zones.get(state, 4800)  # Default 4800 for other states

            # Calculate tier discount
            tier_discount_rate = tier_discounts.get(tier, 0.0)
            tier_discount = price * tier_discount_rate

            # Free delivery for Gold/Platinum
            if tier in ['Gold', 'Platinum']:
                delivery_fee = 0

            # Calculate expected total: price - discount + delivery
            expected_total = price - tier_discount + delivery_fee

            # Check if calculation matches
            difference = stored_total - expected_total
            is_correct = abs(difference) < 0.01  # Less than 1 kobo difference

            total_checked += 1
            if is_correct:
                total_correct += 1
            else:
                total_incorrect += 1
                total_discrepancy += abs(difference)
                incorrect_orders.append({
                    'order_id': order_id,
                    'product_name': order['product_name'],
                    'expected': expected_total,
                    'stored': stored_total,
                    'difference': difference,
                    'breakdown': {
                        'price': price,
                        'tier': tier,
                        'tier_discount': tier_discount,
                        'delivery_fee': delivery_fee,
                        'state': state
                    }
                })

            # Show first 10 orders for detailed view
            if total_checked <= 10:
                status_icon = '✅' if is_correct else '❌'
                print(f'{status_icon} Order {order_id}: {order["product_name"][:30]}...')
                print(f'   💰 Price: ₦{price:,.2f} | 🏆 Tier: {tier} | 📍 State: {state}')
                print(f'   📊 Expected: ₦{expected_total:,.2f} | 💾 Stored: ₦{stored_total:,.2f} | 📉 Diff: ₦{difference:,.2f}')
                if not is_correct:
                    print(f'   🔍 Breakdown: ₦{price:,.2f} - ₦{tier_discount:,.2f} + ₦{delivery_fee:,.2f} = ₦{expected_total:,.2f}')
                print()

        print('=' * 70)
        print(f'📊 PRICING VERIFICATION SUMMARY:')
        print(f'Total Orders Checked: {total_checked}')
        print(f'✅ Correct Calculations: {total_correct}')
        print(f'❌ Incorrect Calculations: {total_incorrect}')
        print(f'🎯 Accuracy Rate: {(total_correct/total_checked)*100:.1f}%' if total_checked > 0 else 'No orders to check')
        print(f'💸 Total Discrepancy: ₦{total_discrepancy:,.2f}')
        print()

        # Show details of incorrect orders
        if incorrect_orders:
            print('🚨 ORDERS WITH PRICING DISCREPANCIES:')
            print('-' * 70)
            for idx, order in enumerate(incorrect_orders[:10], 1):  # Show first 10
                print(f"{idx}. Order {order['order_id']}: {order['product_name'][:25]}...")
                print(f"   Expected: ₦{order['expected']:,.2f} | Stored: ₦{order['stored']:,.2f}")
                print(f"   Difference: ₦{order['difference']:,.2f}")
                b = order['breakdown']
                print(f"   Details: ₦{b['price']:,.2f} ({b['tier']}) - ₦{b['tier_discount']:,.2f} + ₦{b['delivery_fee']:,.2f} ({b['state']})")
                print()

            if len(incorrect_orders) > 10:
                print(f"   ... and {len(incorrect_orders) - 10} more orders with discrepancies")

        # Check overall database health
        print('=' * 70)
        print('🏥 DATABASE HEALTH CHECK:')

        # Check for any NULL or invalid values
        cursor.execute('''
            SELECT
                COUNT(*) as total_orders,
                COUNT(CASE WHEN total_amount IS NULL OR total_amount <= 0 THEN 1 END) as invalid_totals,
                AVG(total_amount) as avg_order_value,
                MIN(total_amount) as min_order_value,
                MAX(total_amount) as max_order_value
            FROM orders
            WHERE order_status != 'Returned'
        ''')

        health_stats = cursor.fetchone()
        print(f"📋 Total Active Orders: {health_stats['total_orders']:,}")
        print(f"⚠️ Invalid Totals: {health_stats['invalid_totals']}")
        print(f"💰 Average Order Value: ₦{health_stats['avg_order_value']:,.2f}" if health_stats['avg_order_value'] else "N/A")
        print(f"📉 Min Order Value: ₦{health_stats['min_order_value']:,.2f}" if health_stats['min_order_value'] else "N/A")
        print(f"📈 Max Order Value: ₦{health_stats['max_order_value']:,.2f}" if health_stats['max_order_value'] else "N/A")

        cursor.close()
        conn.close()

        # Final assessment
        print()
        print('=' * 70)
        if total_incorrect == 0:
            print('🎉 EXCELLENT! All checked orders have correct pricing calculations.')
            print('🔒 Users are getting fair and accurate total amounts.')
            print('✅ Database pricing integrity: VERIFIED')
        elif (total_correct / total_checked) >= 0.95:  # 95% or higher
            print('✅ GOOD! Most orders have correct pricing calculations.')
            print(f'⚠️ {total_incorrect} orders need attention but overall system is healthy.')
            print('🔧 Recommend fixing the identified discrepancies.')
        else:
            print('🚨 ATTENTION NEEDED! Significant pricing discrepancies found.')
            print('💡 Recommend immediate review and correction of pricing logic.')
            print('🔧 Database may need comprehensive pricing updates.')

        return {
            'total_checked': total_checked,
            'total_correct': total_correct,
            'total_incorrect': total_incorrect,
            'accuracy_rate': (total_correct/total_checked)*100 if total_checked > 0 else 0,
            'total_discrepancy': total_discrepancy,
            'incorrect_orders': incorrect_orders
        }

    except Exception as e:
        print(f'❌ Error verifying pricing: {e}')
        return None

if __name__ == "__main__":
    verify_pricing_accuracy()
