"""
🚚 Unified Delivery Service for Nigerian E-commerce Platform
===========================================================================

Simplified, consistent delivery fee calculation service that can be used across:
- Flask web application
- WhatsApp AI agent
- Any other integrations

Features:
- Location-based fixed fees (no weight complexity)
- Tier-based benefits (Gold/Platinum get free delivery)
- High-value order benefits (free/discounted delivery)
- Consistent pricing across all channels

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import logging
from typing import Dict, Any, Tuple, Optional
from src.order_management import NigerianDeliveryCalculator

# Configure logging
logger = logging.getLogger(__name__)

class DeliveryService:
    """🚚 Unified delivery fee calculation service"""

    @staticmethod
    def calculate_delivery_fee(
        state: str,
        order_value: float = 0,
        customer_tier: str = None,
        customer_id: int = None
    ) -> Dict[str, Any]:
        """
        🎯 Calculate delivery fee with full context and tier benefits

        Args:
            state: Nigerian state for delivery
            order_value: Total order value for high-value benefits
            customer_tier: Customer tier for tier-based benefits
            customer_id: Customer ID for database lookup (optional)

        Returns:
            Dict with delivery_fee, delivery_days, delivery_zone, benefits_applied, etc.
        """
        try:
            # Use the simplified delivery calculator
            base_delivery_fee, delivery_days, delivery_zone = NigerianDeliveryCalculator.calculate_delivery_fee(
                state, None, order_value  # No weight calculation!
            )

            final_delivery_fee = base_delivery_fee
            benefits_applied = []

            # Apply tier-based benefits AFTER base calculation
            if customer_tier in ['Gold', 'Platinum']:
                final_delivery_fee = 0.0
                benefits_applied.append(f"{customer_tier} tier - Free delivery")
                logger.info(f"🎁 Free delivery applied for {customer_tier} tier customer")

            # Determine if high-value benefits were already applied in base calculation
            if base_delivery_fee == 0 and order_value >= 200000:
                benefits_applied.append("High-value order (₦200K+) - Free delivery")
            elif base_delivery_fee < NigerianDeliveryCalculator.DELIVERY_ZONES.get(
                delivery_zone, {"fixed_fee": 3000}
            ).get("fixed_fee", 3000) and order_value >= 100000:
                benefits_applied.append("High-value order (₦100K+) - 50% discount")

            result = {
                'success': True,
                'delivery_fee': final_delivery_fee,
                'original_delivery_fee': base_delivery_fee,
                'delivery_days': delivery_days,
                'delivery_zone': delivery_zone,
                'state': state,
                'order_value': order_value,
                'customer_tier': customer_tier,
                'benefits_applied': benefits_applied,
                'calculation_method': 'location_and_tier_based',
                'message': f'Delivery to {state}: ₦{final_delivery_fee:,.2f} ({delivery_days} days)'
            }

            if benefits_applied:
                result['benefits_message'] = ' | '.join(benefits_applied)
                logger.info(f"🎁 Delivery benefits applied: {', '.join(benefits_applied)}")

            logger.info(f"🚚 Delivery calculation: {state} → ₦{final_delivery_fee:,.2f} ({delivery_days} days) | Zone: {delivery_zone}")
            return result

        except Exception as e:
            logger.error(f"❌ Error in delivery service calculation: {e}")
            return {
                'success': False,
                'error': str(e),
                'delivery_fee': 1500.0,  # Fallback to Lagos rate
                'delivery_days': 3,
                'delivery_zone': 'Fallback',
                'state': state,
                'message': f'Fallback delivery rate applied: ₦1,500'
            }

    @staticmethod
    def get_delivery_zones() -> Dict[str, Any]:
        """Get all delivery zones and their rates"""
        try:
            return NigerianDeliveryCalculator.get_delivery_zones_info()
        except Exception as e:
            logger.error(f"❌ Error getting delivery zones: {e}")
            return {}

    @staticmethod
    def get_state_delivery_info(state: str) -> Dict[str, Any]:
        """Get delivery information for a specific state"""
        try:
            # Find which zone the state belongs to
            for zone_name, zone_info in NigerianDeliveryCalculator.DELIVERY_ZONES.items():
                if state in zone_info["states"]:
                    return {
                        'state': state,
                        'zone': zone_name,
                        'fixed_fee': zone_info["fixed_fee"],
                        'delivery_days': zone_info["delivery_days"],
                        'states_in_zone': zone_info["states"]
                    }

            # Default to "Other States" if not found
            other_states_info = NigerianDeliveryCalculator.DELIVERY_ZONES["Other States"]
            return {
                'state': state,
                'zone': 'Other States',
                'fixed_fee': other_states_info["fixed_fee"],
                'delivery_days': other_states_info["delivery_days"],
                'states_in_zone': other_states_info["states"]
            }

        except Exception as e:
            logger.error(f"❌ Error getting state delivery info: {e}")
            return {
                'state': state,
                'zone': 'Error',
                'fixed_fee': 1500.0,
                'delivery_days': 3,
                'error': str(e)
            }

    @staticmethod
    def format_delivery_summary(delivery_result: Dict[str, Any]) -> str:
        """Format delivery calculation result into a readable summary"""
        try:
            if not delivery_result.get('success', False):
                return f"Delivery calculation failed: {delivery_result.get('error', 'Unknown error')}"

            summary = f"🚚 Delivery to {delivery_result['state']}: ₦{delivery_result['delivery_fee']:,.2f}"
            summary += f" ({delivery_result['delivery_days']} days)"

            if delivery_result.get('benefits_applied'):
                summary += f"\n🎁 Benefits: {delivery_result['benefits_message']}"

            return summary

        except Exception as e:
            logger.error(f"❌ Error formatting delivery summary: {e}")
            return "Delivery information unavailable"

# Create singleton instance for easy importing
delivery_service = DeliveryService()

# Export the main calculation function for backward compatibility
def calculate_delivery_fee(state: str, order_value: float = 0, customer_tier: str = None) -> Dict[str, Any]:
    """Backward compatible delivery fee calculation"""
    return delivery_service.calculate_delivery_fee(state, order_value, customer_tier)
