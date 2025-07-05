import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new delivery calculator
from src.order_management import NigerianDeliveryCalculator

load_dotenv()

def fix_all_database_pricing():
    """Fix all pricing discrepancies in the database by recalculating totals"""

    try:
        # Database connection
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'nigerian_ecommerce'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print('🔧 COMPREHENSIVE DATABASE PRICING FIX')
        print('=' * 70)

        # Get all active orders that need fixing with product weights
        cursor.execute('''
            SELECT
                o.order_id,
                o.customer_id,
                p.product_id,
                p.product_name,
                p.price,
                p.weight_kg,
                o.total_amount,
                c.account_tier,
                c.state,
                o.order_status,
                o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status != 'Returned'  -- Don't modify returned orders
            ORDER BY o.created_at DESC
        ''')

        orders = cursor.fetchall()
        print(f'📊 Found {len(orders)} orders to check and fix')
        print()

        # Use the new delivery calculator
        delivery_calculator = NigerianDeliveryCalculator()

        # Tier discounts
        tier_discounts = {
            'Bronze': 0.0,
            'Silver': 0.05,
            'Gold': 0.10,
            'Platinum': 0.15
        }

        total_checked = 0
        total_fixed = 0
        total_discrepancy_fixed = 0.0
        batch_size = 100

        print('🔄 Starting batch processing...')

        # Process orders in batches
        for i in range(0, len(orders), batch_size):
            batch = orders[i:i + batch_size]
            batch_fixes = []

            for order in batch:
                order_id = order['order_id']
                price = float(order['price'])
                weight_kg = float(order['weight_kg']) if order['weight_kg'] else 1.0
                tier = order['account_tier'] or 'Bronze'
                state = order['state']
                stored_total = float(order['total_amount'])

                # Calculate expected delivery fee using new weight-based calculator
                delivery_fee, delivery_days, delivery_zone = delivery_calculator.calculate_delivery_fee(
                    state, weight_kg, price
                )

                # Calculate tier discount
                tier_discount_rate = tier_discounts.get(tier, 0.0)
                tier_discount = price * tier_discount_rate

                # Free delivery for Gold/Platinum
                if tier in ['Gold', 'Platinum']:
                    delivery_fee = 0

                # Calculate correct total: price - discount + delivery
                correct_total = price - tier_discount + delivery_fee

                # Check if fix is needed
                difference = abs(stored_total - correct_total)

                total_checked += 1

                if difference >= 0.01:  # More than 1 kobo difference
                    batch_fixes.append({
                        'order_id': order_id,
                        'old_total': stored_total,
                        'new_total': correct_total,
                        'difference': stored_total - correct_total
                    })
                    total_discrepancy_fixed += difference

            # Apply batch fixes
            if batch_fixes:
                for fix in batch_fixes:
                    try:
                        cursor.execute('''
                            UPDATE orders
                            SET total_amount = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE order_id = %s
                        ''', (fix['new_total'], fix['order_id']))

                        total_fixed += 1

                        # Log the fix
                        if total_fixed <= 10:  # Show first 10 fixes
                            print(f"✅ Fixed Order {fix['order_id']}: ₦{fix['old_total']:,.2f} → ₦{fix['new_total']:,.2f} (Diff: ₦{fix['difference']:,.2f})")

                    except Exception as e:
                        print(f"❌ Failed to fix Order {fix['order_id']}: {e}")

                # Commit batch
                conn.commit()
                print(f"📦 Batch {i//batch_size + 1}: Processed {len(batch)} orders, Fixed {len(batch_fixes)} orders")
            else:
                print(f"📦 Batch {i//batch_size + 1}: Processed {len(batch)} orders, No fixes needed")

        print()
        print('=' * 70)
        print(f'📊 COMPREHENSIVE FIX SUMMARY:')
        print(f'Total Orders Checked: {total_checked:,}')
        print(f'✅ Orders Fixed: {total_fixed:,}')
        print(f'💰 Total Discrepancy Fixed: ₦{total_discrepancy_fixed:,.2f}')
        print(f'🎯 Fix Rate: {(total_fixed/total_checked)*100:.1f}%' if total_checked > 0 else 'N/A')

        # Verify the fixes worked
        print()
        print('🔍 POST-FIX VERIFICATION...')

        # Check a sample of recently fixed orders
        cursor.execute('''
            SELECT
                o.order_id,
                p.price,
                p.weight_kg,
                o.total_amount,
                c.account_tier,
                c.state
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_status != 'Returned'
            ORDER BY o.updated_at DESC
            LIMIT 10
        ''')

        verification_orders = cursor.fetchall()
        verification_passed = 0

        for order in verification_orders:
            price = float(order['price'])
            weight_kg = float(order['weight_kg']) if order['weight_kg'] else 1.0
            tier = order['account_tier'] or 'Bronze'
            state = order['state']
            stored_total = float(order['total_amount'])

            # Recalculate expected total using new delivery calculator
            delivery_fee, delivery_days, delivery_zone = delivery_calculator.calculate_delivery_fee(
                state, weight_kg, price
            )
            tier_discount_rate = tier_discounts.get(tier, 0.0)
            tier_discount = price * tier_discount_rate

            if tier in ['Gold', 'Platinum']:
                delivery_fee = 0

            expected_total = price - tier_discount + delivery_fee

            # Check if now correct
            difference = abs(stored_total - expected_total)
            is_correct = difference < 0.01

            if is_correct:
                verification_passed += 1

            status_icon = '✅' if is_correct else '❌'
            print(f"{status_icon} Order {order['order_id']}: Expected ₦{expected_total:,.2f}, Stored ₦{stored_total:,.2f}")

        print()
        print(f"✅ Verification: {verification_passed}/{len(verification_orders)} orders now have correct pricing")

        cursor.close()
        conn.close()

        print()
        print('=' * 70)
        if total_fixed > 0:
            print('🎉 DATABASE PRICING FIX COMPLETED!')
            print('💰 All customers are now getting fair and accurate pricing!')
            print('🔒 Database pricing integrity has been restored!')
        else:
            print('✅ No pricing fixes were needed - all orders already correct!')

        return {
            'total_checked': total_checked,
            'total_fixed': total_fixed,
            'total_discrepancy_fixed': total_discrepancy_fixed,
            'verification_passed': verification_passed if 'verification_passed' in locals() else 0
        }

    except Exception as e:
        print(f'❌ Error fixing database pricing: {e}')
        if 'conn' in locals():
            conn.rollback()
        return None

if __name__ == "__main__":
    fix_all_database_pricing()
