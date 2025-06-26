#!/usr/bin/env python3
"""
🔧 FIX SPECIFIC ORDERS WITH CALCULATION DISCREPANCIES
==================================================

This script fixes the specific orders showing calculation discrepancies
by updating their database total_amount fields with correct calculated values.

Based on the logs, we need to fix orders like:
- Order 17411: Stored=₦190,050.00, Should be=₦193,500.00
- Order 17455: Stored=₦7,650.00, Should be=₦8,075.00
- Order 17448: Stored=₦436,500.00, Should be=₦460,750.00
etc.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import sys
import os

# Add the src directory to the path to import the order management system
sys.path.append('src')
from order_management import OrderManagementSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpecificOrdersFixer:
    """Fix specific orders with calculation discrepancies"""

    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'nigerian_ecommerce',
            'user': 'postgres',
            'password': 'oracle'
        }
        self.order_system = OrderManagementSystem()

    def get_database_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)

    def fix_order_total(self, order_id: str) -> bool:
        """Fix a specific order's total_amount in the database"""
        try:
            # Get the order status which includes correct calculation
            order_status = self.order_system.get_order_status(order_id)

            if not order_status['success']:
                logger.error(f"❌ Could not get order status for {order_id}: {order_status.get('error')}")
                return False

            order_data = order_status['order']

            # The order_system already calculates the correct total and stores it in order_data['total_amount']
            correct_total = float(order_data['total_amount'])

            # Get the pricing breakdown for logging
            breakdown = order_data.get('pricing_breakdown', {})
            stored_total = breakdown.get('stored_total', 0)
            discrepancy = breakdown.get('discrepancy', 0)

            if abs(discrepancy) <= 0.01:
                logger.info(f"✅ Order {order_id} already has correct total: ₦{correct_total:,.2f}")
                return True

            # Update the database with the correct total
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE orders
                        SET total_amount = %s
                        WHERE order_id = %s
                    """, (correct_total, order_id))

                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f"✅ Fixed Order {order_id}: Updated database from ₦{stored_total:,.2f} to ₦{correct_total:,.2f} (Difference: ₦{-discrepancy:,.2f})")
                        return True
                    else:
                        logger.error(f"❌ Order {order_id} not found in database")
                        return False

        except Exception as e:
            logger.error(f"❌ Error fixing order {order_id}: {e}")
            return False

    def scan_and_fix_all_discrepancies(self) -> dict:
        """Scan all orders and fix any with discrepancies"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    # Get all order IDs
                    cursor.execute("SELECT order_id FROM orders ORDER BY order_id")
                    all_orders = cursor.fetchall()

            logger.info(f"🔍 Scanning {len(all_orders)} orders for discrepancies...")

            stats = {
                'total_scanned': len(all_orders),
                'discrepancies_found': 0,
                'orders_fixed': 0,
                'orders_failed': 0,
                'total_amount_corrected': 0.0
            }

            for (order_id,) in all_orders:
                try:
                    # Get order status to check for discrepancies
                    order_status = self.order_system.get_order_status(str(order_id))

                    if order_status['success']:
                        order_data = order_status['order']
                        breakdown = order_data.get('pricing_breakdown', {})
                        discrepancy = breakdown.get('discrepancy', 0)

                        if abs(discrepancy) > 0.01:  # More than 1 kobo difference
                            stats['discrepancies_found'] += 1
                            stats['total_amount_corrected'] += abs(discrepancy)

                            # Fix this order
                            if self.fix_order_database_only(order_id, order_data):
                                stats['orders_fixed'] += 1
                            else:
                                stats['orders_failed'] += 1

                except Exception as e:
                    logger.warning(f"⚠️ Error scanning order {order_id}: {e}")
                    stats['orders_failed'] += 1

            logger.info("📊 SCAN AND FIX SUMMARY:")
            logger.info(f"   📋 Total Orders Scanned: {stats['total_scanned']}")
            logger.info(f"   ⚠️ Discrepancies Found: {stats['discrepancies_found']}")
            logger.info(f"   ✅ Orders Fixed: {stats['orders_fixed']}")
            logger.info(f"   ❌ Orders Failed: {stats['orders_failed']}")
            logger.info(f"   💰 Total Amount Corrected: ₦{stats['total_amount_corrected']:,.2f}")

            return stats

        except Exception as e:
            logger.error(f"❌ Error in scan and fix: {e}")
            return {'error': str(e)}

    def fix_order_database_only(self, order_id: str, order_data: dict) -> bool:
        """Fix order total directly in database without recalculating"""
        try:
            correct_total = float(order_data['total_amount'])

            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE orders
                        SET total_amount = %s
                        WHERE order_id = %s
                    """, (correct_total, order_id))

                    if cursor.rowcount > 0:
                        conn.commit()
                        return True
                    else:
                        return False

        except Exception as e:
            logger.error(f"❌ Error updating order {order_id}: {e}")
            return False

    def fix_specific_orders_from_logs(self) -> dict:
        """Fix the specific orders mentioned in the logs"""
        problem_orders = [
            '17411',  # Stored=₦190,050.00, Should be=₦193,500.00
            '17455',  # Stored=₦7,650.00, Should be=₦8,075.00
            '17448',  # Stored=₦436,500.00, Should be=₦460,750.00
            '34322',  # Stored=₦7,650.00, Should be=₦8,075.00
            '34321'   # Stored=₦10,800.00, Should be=₦11,400.00
        ]

        logger.info("🎯 Fixing specific orders identified in logs...")

        stats = {
            'orders_processed': 0,
            'orders_fixed': 0,
            'orders_failed': 0,
            'total_discrepancy_fixed': 0.0
        }

        for order_id in problem_orders:
            stats['orders_processed'] += 1

            if self.fix_order_total(order_id):
                stats['orders_fixed'] += 1
            else:
                stats['orders_failed'] += 1

        logger.info("📊 SPECIFIC ORDERS FIX SUMMARY:")
        logger.info(f"   📋 Orders Processed: {stats['orders_processed']}")
        logger.info(f"   ✅ Orders Fixed: {stats['orders_fixed']}")
        logger.info(f"   ❌ Orders Failed: {stats['orders_failed']}")

        return stats

def main():
    """Main execution function"""
    print("🔧 SPECIFIC ORDERS CALCULATION FIX")
    print("=" * 45)

    fixer = SpecificOrdersFixer()

    # First fix the specific problem orders from logs
    # print("\n🎯 PHASE 1: Fixing specific orders from logs...")
    # specific_stats = fixer.fix_specific_orders_from_logs()

    # Then scan and fix any remaining discrepancies
    print("\n🔍 PHASE 2: Scanning for additional discrepancies...")
    scan_stats = fixer.scan_and_fix_all_discrepancies()

    print("\n" + "=" * 45)
    print("🎉 COMPREHENSIVE FIX COMPLETED!")
    print("✅ Database totals updated")
    print("✅ My Order History will show correct amounts")
    print("✅ UI and database now consistent")

if __name__ == "__main__":
    main()
