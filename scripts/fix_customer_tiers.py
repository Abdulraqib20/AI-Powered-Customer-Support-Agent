#!/usr/bin/env python3
"""
Customer Tier Audit and Fix Script
==================================

This script identifies and fixes customers who have incorrect account tiers
based on their actual spending and order history.

Tier Criteria:
- Bronze: ₦0 to ₦99,999 total spent, 0+ orders
- Silver: ₦100,000+ total spent, 3+ orders
- Gold: ₦500,000+ total spent, 10+ orders
- Platinum: ₦2,000,000+ total spent, 20+ orders
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from decimal import Decimal
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'nigerian_ecommerce'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'oracle'),
}

# Tier criteria - matches the system criteria exactly
TIER_CRITERIA = {
    'Platinum': {'min_spending': 2000000, 'min_orders': 20},
    'Gold': {'min_spending': 500000, 'min_orders': 10},
    'Silver': {'min_spending': 100000, 'min_orders': 3},
    'Bronze': {'min_spending': 0, 'min_orders': 0}
}

def calculate_correct_tier(total_spent: float, order_count: int) -> str:
    """Calculate the correct tier based on spending and order count"""
    # Check tiers from highest to lowest
    for tier, criteria in TIER_CRITERIA.items():
        if total_spent >= criteria['min_spending'] and order_count >= criteria['min_orders']:
            return tier
    return 'Bronze'

def get_database_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise

def audit_customer_tiers() -> List[Dict]:
    """Audit all customers and identify those with incorrect tiers"""
    logger.info("🔍 Starting customer tier audit...")

    incorrect_customers = []

    with get_database_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get all customers with their spending and order data
            cursor.execute("""
                SELECT
                    c.customer_id,
                    c.name,
                    c.email,
                    c.account_tier as current_tier,
                    c.created_at,
                    COALESCE(SUM(CASE
                        WHEN o.order_status != 'Returned'
                        THEN CAST(o.total_amount AS DECIMAL(15,2))
                        ELSE 0
                    END), 0)::DECIMAL(15,2) as total_spent,
                    COUNT(CASE
                        WHEN o.order_status != 'Returned'
                        THEN o.order_id
                    END)::INTEGER as order_count
                FROM customers c
                LEFT JOIN orders o ON c.customer_id = o.customer_id
                WHERE c.user_role = 'customer'  -- Only check actual customers, not staff
                GROUP BY c.customer_id, c.name, c.email, c.account_tier, c.created_at
                ORDER BY c.customer_id
            """)

            customers = cursor.fetchall()
            logger.info(f"📊 Auditing {len(customers)} customers...")

            tier_counts = {'Bronze': 0, 'Silver': 0, 'Gold': 0, 'Platinum': 0}
            correct_count = 0

            for customer in customers:
                customer_id = customer['customer_id']
                current_tier = customer['current_tier']
                total_spent = float(customer['total_spent']) if customer['total_spent'] else 0.0
                order_count = int(customer['order_count']) if customer['order_count'] else 0

                # Calculate what tier they should have
                correct_tier = calculate_correct_tier(total_spent, order_count)

                # Count current tier distribution
                tier_counts[current_tier] = tier_counts.get(current_tier, 0) + 1

                if current_tier != correct_tier:
                    incorrect_customers.append({
                        'customer_id': customer_id,
                        'name': customer['name'],
                        'email': customer['email'],
                        'current_tier': current_tier,
                        'correct_tier': correct_tier,
                        'total_spent': total_spent,
                        'order_count': order_count,
                        'member_since': customer['created_at'].strftime('%Y-%m-%d') if customer['created_at'] else 'Unknown'
                    })

                    logger.info(f"🔧 Customer {customer_id} ({customer['name'][:20]}...): "
                              f"{current_tier} → {correct_tier} "
                              f"(₦{total_spent:,.2f}, {order_count} orders)")
                else:
                    correct_count += 1

            logger.info(f"\n📈 AUDIT SUMMARY:")
            logger.info(f"✅ Correctly tiered customers: {correct_count}")
            logger.info(f"❌ Incorrectly tiered customers: {len(incorrect_customers)}")
            logger.info(f"\n🏆 Current tier distribution:")
            for tier, count in tier_counts.items():
                logger.info(f"   {tier}: {count} customers")

            return incorrect_customers

def fix_customer_tiers(incorrect_customers: List[Dict], dry_run: bool = True) -> int:
    """Fix customer tiers - either dry run or actual update"""
    if not incorrect_customers:
        logger.info("✅ No customers need tier corrections!")
        return 0

    action = "DRY RUN" if dry_run else "EXECUTING"
    logger.info(f"\n🔧 {action}: Fixing {len(incorrect_customers)} customer tiers...")

    if dry_run:
        logger.info("📋 Changes that would be made:")
        for customer in incorrect_customers:
            logger.info(f"   Customer {customer['customer_id']} ({customer['name'][:25]}...): "
                       f"{customer['current_tier']} → {customer['correct_tier']} "
                       f"(₦{customer['total_spent']:,.2f}, {customer['order_count']} orders)")
        return len(incorrect_customers)

    # Actual execution
    fixed_count = 0
    errors = []

    with get_database_connection() as conn:
        with conn.cursor() as cursor:
            for customer in incorrect_customers:
                try:
                    cursor.execute("""
                        UPDATE customers
                        SET account_tier = %s::account_tier_enum,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s
                    """, (customer['correct_tier'], customer['customer_id']))

                    # Log the tier upgrade for analytics
                    cursor.execute("""
                        INSERT INTO analytics (metric_type, metric_value, time_period, created_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """, (
                        'tier_correction',
                        f'{{"customer_id": {customer["customer_id"]}, "from_tier": "{customer["current_tier"]}", "to_tier": "{customer["correct_tier"]}", "total_spent": {customer["total_spent"]}, "order_count": {customer["order_count"]}, "correction_reason": "audit_fix"}}',
                        'event'
                    ))

                    fixed_count += 1
                    logger.info(f"✅ Fixed Customer {customer['customer_id']}: "
                              f"{customer['current_tier']} → {customer['correct_tier']}")

                except Exception as e:
                    error_msg = f"Customer {customer['customer_id']}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"❌ Failed to fix {error_msg}")

            if errors:
                logger.warning(f"⚠️ {len(errors)} errors occurred during tier corrections")
                conn.rollback()
                return 0
            else:
                conn.commit()
                logger.info(f"✅ Successfully fixed {fixed_count} customer tiers!")

    return fixed_count

def generate_tier_report(incorrect_customers: List[Dict]):
    """Generate a detailed tier correction report"""
    if not incorrect_customers:
        return

    logger.info(f"\n📊 DETAILED TIER CORRECTION REPORT")
    logger.info(f"=" * 80)

    # Group by correction type
    corrections = {
        'Bronze → Silver': [],
        'Bronze → Gold': [],
        'Bronze → Platinum': [],
        'Silver → Gold': [],
        'Silver → Platinum': [],
        'Gold → Platinum': [],
        'Other': []
    }

    for customer in incorrect_customers:
        correction_type = f"{customer['current_tier']} → {customer['correct_tier']}"
        if correction_type in corrections:
            corrections[correction_type].append(customer)
        else:
            corrections['Other'].append(customer)

    for correction_type, customers in corrections.items():
        if customers:
            logger.info(f"\n🔄 {correction_type}: {len(customers)} customers")
            for customer in customers[:5]:  # Show first 5 of each type
                logger.info(f"   • {customer['name'][:30]:30} | ₦{customer['total_spent']:>10,.2f} | {customer['order_count']:>3} orders")
            if len(customers) > 5:
                logger.info(f"   ... and {len(customers) - 5} more")

def main():
    """Main execution function"""
    try:
        logger.info("🚀 Starting Customer Tier Audit & Fix Script")
        logger.info("=" * 60)

        # Step 1: Audit all customer tiers
        incorrect_customers = audit_customer_tiers()

        if not incorrect_customers:
            logger.info("🎉 All customer tiers are correct! No fixes needed.")
            return

        # Step 2: Generate detailed report
        generate_tier_report(incorrect_customers)

        # Step 3: Show what would be fixed (dry run)
        logger.info(f"\n🔍 PREVIEW: What would be changed")
        fix_customer_tiers(incorrect_customers, dry_run=True)

        # Step 4: Ask for confirmation
        response = input(f"\n❓ Fix {len(incorrect_customers)} customer tiers? (y/N): ").strip().lower()

        if response in ['y', 'yes']:
            logger.info("✅ User confirmed - proceeding with tier corrections...")
            fixed_count = fix_customer_tiers(incorrect_customers, dry_run=False)

            if fixed_count > 0:
                logger.info(f"\n🎉 SUCCESS! Fixed {fixed_count} customer account tiers!")
                logger.info("💡 Customers will now receive appropriate discounts and benefits")

                # Verify the fixes
                logger.info("\n🔍 Verifying fixes...")
                remaining_incorrect = audit_customer_tiers()
                if not remaining_incorrect:
                    logger.info("✅ Verification passed! All customer tiers are now correct.")
                else:
                    logger.warning(f"⚠️ {len(remaining_incorrect)} customers still need fixing")
            else:
                logger.error("❌ No tiers were fixed due to errors")
        else:
            logger.info("❌ User cancelled - no changes made")

    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        raise

if __name__ == "__main__":
    main()
