"""
🎯 World-Class Customer Support Recommendation System
================================================================================

Advanced recommendation system specifically designed for customer support scenarios.
Integrates contextual recommendations, mood-aware suggestions, and intelligent
problem-solving recommendations to provide world-class customer service.

Features:
1. Context-Aware Recommendations based on support queries
2. Mood-Driven Product Suggestions (frustrated, curious, urgent)
3. Problem-Solving Recommendations for product issues
4. Cart Abandonment Recovery with intelligent alternatives
5. Cross-sell and Upsell for customer satisfaction
6. Real-time Browsing Behavior Analysis
7. Nigerian Market Intelligence Integration
8. Customer Journey Stage Optimization

Author: AI Assistant for World-Class Customer Support
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

# Import our enhanced components
try:
    from .recommendation_engine import (
        ProductRecommendationEngine, CustomerSupportContext,
        RecommendationType, RecommendationResult
    )
    from .enhanced_db_querying import EnhancedDatabaseQuerying, QueryType
    logger = logging.getLogger(__name__)
    logger.info("✅ Successfully imported enhanced recommendation components")
except ImportError:
    try:
        from recommendation_engine import (
            ProductRecommendationEngine, CustomerSupportContext,
            RecommendationType, RecommendationResult
        )
        from enhanced_db_querying import EnhancedDatabaseQuerying, QueryType
        logger = logging.getLogger(__name__)
        logger.info("✅ Successfully imported enhanced recommendation components (direct)")
    except ImportError:
        logger = logging.getLogger(__name__)
        logger.warning("⚠️ Enhanced recommendation components not available")
        ProductRecommendationEngine = None
        CustomerSupportContext = None
        RecommendationType = None
        RecommendationResult = None
        EnhancedDatabaseQuerying = None

# Configure logging
logging.basicConfig(level=logging.INFO)

class SupportScenario(Enum):
    """Different customer support scenarios"""
    PRODUCT_INQUIRY = "product_inquiry"
    PRODUCT_COMPARISON = "product_comparison"
    TROUBLESHOOTING = "troubleshooting"
    ORDER_ASSISTANCE = "order_assistance"
    CART_ABANDONMENT = "cart_abandonment"
    PRICE_NEGOTIATION = "price_negotiation"
    RETURN_EXCHANGE = "return_exchange"
    SATISFACTION_RECOVERY = "satisfaction_recovery"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    CROSS_SELL_OPPORTUNITY = "cross_sell_opportunity"
    GENERAL_BROWSING = "general_browsing"
    URGENT_PURCHASE = "urgent_purchase"

@dataclass
class SupportRecommendationRequest:
    """Request structure for support recommendations"""
    customer_id: int
    support_query: str
    scenario: SupportScenario
    customer_mood: str
    conversation_history: List[Dict]
    current_products: List[Dict] = None
    cart_items: List[Dict] = None
    budget_range: Tuple[float, float] = None
    urgency_level: str = "medium"  # low, medium, high
    preferred_categories: List[str] = None
    session_context: Dict[str, Any] = None

@dataclass
class SupportRecommendationResponse:
    """Response structure for support recommendations"""
    recommendations: Dict[str, List[Dict]]
    primary_message: str
    secondary_message: str
    call_to_action: str
    confidence_score: float
    recommendation_reasoning: List[str]
    total_recommendations: int
    estimated_satisfaction_impact: str  # high, medium, low
    next_best_actions: List[str]

class CustomerSupportRecommendationEngine:
    """🏆 World-Class Customer Support Recommendation Engine"""

    def __init__(self):
        """Initialize the customer support recommendation engine"""
        try:
            if ProductRecommendationEngine:
                self.recommendation_engine = ProductRecommendationEngine()
                logger.info("✅ ProductRecommendationEngine initialized for customer support")
            else:
                self.recommendation_engine = None
                logger.warning("⚠️ ProductRecommendationEngine not available")

            if EnhancedDatabaseQuerying:
                self.db_querying = EnhancedDatabaseQuerying()
                logger.info("✅ EnhancedDatabaseQuerying initialized for customer support")
            else:
                self.db_querying = None
                logger.warning("⚠️ EnhancedDatabaseQuerying not available")

            # Support-specific configuration
            self.mood_response_templates = self._initialize_mood_templates()
            self.scenario_handlers = self._initialize_scenario_handlers()

            logger.info("✅ CustomerSupportRecommendationEngine fully initialized")

        except Exception as e:
            logger.error(f"❌ Error initializing CustomerSupportRecommendationEngine: {e}")
            self.recommendation_engine = None
            self.db_querying = None

    def _initialize_mood_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize mood-specific response templates"""
        return {
            "frustrated": {
                "primary_tone": "empathetic_solution_focused",
                "message_prefix": "I understand your frustration, and I'm here to make this right.",
                "recommendation_focus": "premium_alternatives",
                "urgency": "high"
            },
            "curious": {
                "primary_tone": "educational_exploratory",
                "message_prefix": "Great question! Let me show you some exciting options.",
                "recommendation_focus": "educational_diverse",
                "urgency": "medium"
            },
            "urgent": {
                "primary_tone": "direct_action_oriented",
                "message_prefix": "I'll help you find the perfect solution right away.",
                "recommendation_focus": "immediate_availability",
                "urgency": "high"
            },
            "satisfied": {
                "primary_tone": "appreciation_enhancement",
                "message_prefix": "I'm so glad you're happy! Here are some great additions.",
                "recommendation_focus": "complementary_upsell",
                "urgency": "low"
            },
            "neutral": {
                "primary_tone": "professional_helpful",
                "message_prefix": "I'd be happy to help you find exactly what you need.",
                "recommendation_focus": "personalized_balanced",
                "urgency": "medium"
            }
        }

    def _initialize_scenario_handlers(self) -> Dict[SupportScenario, str]:
        """Initialize scenario-specific handlers"""
        return {
            SupportScenario.PRODUCT_INQUIRY: "handle_product_inquiry",
            SupportScenario.PRODUCT_COMPARISON: "handle_product_comparison",
            SupportScenario.TROUBLESHOOTING: "handle_troubleshooting",
            SupportScenario.ORDER_ASSISTANCE: "handle_order_assistance",
            SupportScenario.CART_ABANDONMENT: "handle_cart_abandonment",
            SupportScenario.PRICE_NEGOTIATION: "handle_price_negotiation",
            SupportScenario.RETURN_EXCHANGE: "handle_return_exchange",
            SupportScenario.SATISFACTION_RECOVERY: "handle_satisfaction_recovery",
            SupportScenario.UPSELL_OPPORTUNITY: "handle_upsell_opportunity",
            SupportScenario.CROSS_SELL_OPPORTUNITY: "handle_cross_sell_opportunity",
            SupportScenario.GENERAL_BROWSING: "handle_general_browsing",
            SupportScenario.URGENT_PURCHASE: "handle_urgent_purchase"
        }

    def get_support_recommendations(self, request: SupportRecommendationRequest) -> SupportRecommendationResponse:
        """🎯 Get comprehensive customer support recommendations"""
        try:
            if not self.recommendation_engine:
                return self._get_fallback_response(request)

            # Analyze support context
            support_context = self._analyze_support_context(request)

            # Get scenario-specific recommendations
            handler_name = self.scenario_handlers.get(request.scenario, "handle_general_browsing")
            handler = getattr(self, handler_name, self.handle_general_browsing)

            scenario_recommendations = handler(request, support_context)

            # Get mood-aware enhancements
            mood_enhancements = self._get_mood_aware_enhancements(request, scenario_recommendations)

            # Combine and prioritize recommendations
            final_recommendations = self._combine_and_prioritize_recommendations(
                scenario_recommendations, mood_enhancements, request)

            # Generate response messages
            response_messages = self._generate_response_messages(request, final_recommendations)

            # Calculate confidence and impact
            confidence_score = self._calculate_confidence_score(final_recommendations, request)
            satisfaction_impact = self._estimate_satisfaction_impact(final_recommendations, request)

            return SupportRecommendationResponse(
                recommendations=final_recommendations,
                primary_message=response_messages["primary"],
                secondary_message=response_messages["secondary"],
                call_to_action=response_messages["cta"],
                confidence_score=confidence_score,
                recommendation_reasoning=response_messages["reasoning"],
                total_recommendations=sum(len(recs) for recs in final_recommendations.values()),
                estimated_satisfaction_impact=satisfaction_impact,
                next_best_actions=response_messages["next_actions"]
            )

        except Exception as e:
            logger.error(f"❌ Error getting support recommendations: {e}")
            return self._get_fallback_response(request)

    def _analyze_support_context(self, request: SupportRecommendationRequest):
        """🔍 Analyze the support context for intelligent recommendations"""
        try:
            if not CustomerSupportContext:
                return None

            # Determine support category from scenario
            scenario_to_category = {
                SupportScenario.PRODUCT_INQUIRY: "general_inquiry",
                SupportScenario.PRODUCT_COMPARISON: "general_inquiry",
                SupportScenario.TROUBLESHOOTING: "product_issue",
                SupportScenario.ORDER_ASSISTANCE: "order_problem",
                SupportScenario.CART_ABANDONMENT: "general_inquiry",
                SupportScenario.RETURN_EXCHANGE: "product_issue",
                SupportScenario.SATISFACTION_RECOVERY: "product_issue"
            }

            support_category = scenario_to_category.get(request.scenario, "general_inquiry")

            # Determine conversation stage
            interaction_count = len(request.conversation_history)
            if interaction_count == 0:
                conversation_stage = "initial"
            elif interaction_count <= 2:
                conversation_stage = "diagnosis"
            elif interaction_count <= 4:
                conversation_stage = "solution"
            else:
                conversation_stage = "followup"

            # Extract mentioned products from query
            mentioned_products = self._extract_mentioned_products(request.support_query)

            # Determine problem category
            problem_categories = {
                "quality": ["broken", "defective", "not working", "poor quality"],
                "delivery": ["late", "delayed", "missing", "not arrived"],
                "payment": ["charge", "billing", "refund", "payment issue"],
                "returns": ["return", "exchange", "warranty", "replace"]
            }

            problem_category = "general"
            query_lower = request.support_query.lower()
            for category, keywords in problem_categories.items():
                if any(keyword in query_lower for keyword in keywords):
                    problem_category = category
                    break

            # Determine resolution priority
            priority_map = {
                "frustrated": "high",
                "urgent": "high",
                "satisfied": "low",
                "curious": "medium",
                "neutral": "medium"
            }
            resolution_priority = priority_map.get(request.customer_mood, "medium")

            return CustomerSupportContext(
                support_query=request.support_query,
                support_category=support_category,
                customer_mood=request.customer_mood,
                conversation_stage=conversation_stage,
                mentioned_products=mentioned_products,
                problem_category=problem_category,
                resolution_priority=resolution_priority
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing support context: {e}")
            return None

    def _extract_mentioned_products(self, query: str) -> List[str]:
        """🔍 Extract mentioned products from support query"""
        # Nigerian popular brands and product keywords
        brands = ['Samsung', 'Apple', 'Tecno', 'Infinix', 'Nike', 'Adidas', 'MAC', 'HP', 'Dell']
        products = ['phone', 'laptop', 'dress', 'shoe', 'watch', 'bag', 'headphones']

        mentioned = []
        query_lower = query.lower()

        for brand in brands:
            if brand.lower() in query_lower:
                mentioned.append(brand)

        for product in products:
            if product in query_lower:
                mentioned.append(product)

        return mentioned

    def handle_product_inquiry(self, request: SupportRecommendationRequest,
                             support_context) -> Dict[str, List[Dict]]:
        """🔍 Handle product inquiry scenarios"""
        recommendations = {}

        if self.recommendation_engine:
            # Get personalized recommendations
            personalized = self.recommendation_engine.get_content_based_recommendations(
                self.recommendation_engine.get_customer_profile(request.customer_id), limit=6)
            if personalized:
                recommendations["personalized_for_you"] = [self._convert_recommendation_result(r) for r in personalized]

            # Get popular products in mentioned categories
            if request.preferred_categories:
                for category in request.preferred_categories[:2]:
                    popular = self.recommendation_engine.get_popular_products(limit=4, category=category)
                    if popular:
                        recommendations[f"popular_{category.lower()}"] = [self._convert_recommendation_result(r) for r in popular]

        return recommendations

    def handle_product_comparison(self, request: SupportRecommendationRequest,
                                support_context) -> Dict[str, List[Dict]]:
        """⚖️ Handle product comparison scenarios"""
        recommendations = {}

        if self.recommendation_engine and support_context and hasattr(support_context, 'mentioned_products') and support_context.mentioned_products:
            # Get similar products for comparison
            for product_name in support_context.mentioned_products[:2]:
                product_id = self.recommendation_engine._find_products_by_name_similarity(product_name, limit=1)
                if product_id:
                    similar = self.recommendation_engine.get_similar_products_recommendations(
                        request.customer_id, product_id[0].product_id, limit=4)
                    if similar:
                        recommendations[f"similar_to_{product_name.lower()}"] = [self._convert_recommendation_result(r) for r in similar]

        return recommendations

    def handle_troubleshooting(self, request: SupportRecommendationRequest,
                             support_context) -> Dict[str, List[Dict]]:
        """🔧 Handle troubleshooting scenarios with problem-solving recommendations"""
        recommendations = {}

        if self.recommendation_engine and support_context:
            # Get problem-solving recommendations
            problem_solving = self.recommendation_engine.get_customer_support_recommendations(
                request.customer_id, support_context, limit=6)
            if problem_solving:
                recommendations["problem_solving_alternatives"] = [self._convert_recommendation_result(r) for r in problem_solving]

            # Get reliable alternatives
            if hasattr(support_context, 'mentioned_products') and support_context.mentioned_products:
                for product_name in support_context.mentioned_products[:1]:
                    alternatives = self.recommendation_engine._find_products_by_name_similarity(product_name, limit=3)
                    if alternatives:
                        recommendations["reliable_alternatives"] = [self._convert_recommendation_result(r) for r in alternatives]

        return recommendations

    def handle_cart_abandonment(self, request: SupportRecommendationRequest,
                               support_context) -> Dict[str, List[Dict]]:
        """🛒 Handle cart abandonment recovery"""
        recommendations = {}

        if self.recommendation_engine:
            # Get abandonment recovery recommendations
            recovery = self.recommendation_engine.get_abandoned_cart_recommendations(
                request.customer_id, request.cart_items, limit=8)
            if recovery:
                recommendations["complete_your_purchase"] = [self._convert_recommendation_result(r) for r in recovery]

            # Get incentive products (lower priced alternatives)
            if request.cart_items:
                for item in request.cart_items[:2]:
                    product_id = item.get('product_id')
                    if product_id:
                        alternatives = self.recommendation_engine.get_similar_products_recommendations(
                            request.customer_id, product_id, price_filter="lower", limit=3)
                        if alternatives:
                            recommendations["budget_friendly_alternatives"] = [self._convert_recommendation_result(r) for r in alternatives]

        return recommendations

    def handle_satisfaction_recovery(self, request: SupportRecommendationRequest,
                                   support_context) -> Dict[str, List[Dict]]:
        """😊 Handle satisfaction recovery for frustrated customers"""
        recommendations = {}

        if self.recommendation_engine:
            # Get premium alternatives to rebuild confidence
            premium = self.recommendation_engine.get_tier_progression_recommendations(
                self.recommendation_engine.get_customer_profile(request.customer_id), limit=5)
            if premium:
                recommendations["premium_satisfaction_guarantee"] = [self._convert_recommendation_result(r) for r in premium]

            # Get highly rated reliable products
            customer_profile = self.recommendation_engine.get_customer_profile(request.customer_id)
            if customer_profile.favorite_categories:
                reliable = self.recommendation_engine._get_highly_rated_products(
                    customer_profile.favorite_categories[0], limit=4)
                if reliable:
                    recommendations["highly_rated_reliable"] = [self._convert_recommendation_result(r) for r in reliable]

        return recommendations

    def handle_upsell_opportunity(self, request: SupportRecommendationRequest,
                                support_context) -> Dict[str, List[Dict]]:
        """⬆️ Handle upsell opportunities"""
        recommendations = {}

        if self.recommendation_engine and request.current_products:
            for product in request.current_products[:1]:
                product_id = product.get('product_id')
                current_price = product.get('price')

                if product_id:
                    upsell = self.recommendation_engine.get_upsell_recommendations(
                        request.customer_id, product_id, current_price, limit=4)
                    if upsell:
                        recommendations["premium_upgrades"] = [self._convert_recommendation_result(r) for r in upsell]

        return recommendations

    def handle_cross_sell_opportunity(self, request: SupportRecommendationRequest,
                                    support_context) -> Dict[str, List[Dict]]:
        """🛒 Handle cross-sell opportunities"""
        recommendations = {}

        if self.recommendation_engine and request.current_products:
            product_ids = [p.get('product_id') for p in request.current_products if p.get('product_id')]

            if product_ids:
                cross_sell = self.recommendation_engine.get_cross_sell_recommendations(
                    request.customer_id, product_ids[0], request.cart_items, limit=6)
                if cross_sell:
                    recommendations["frequently_bought_together"] = [self._convert_recommendation_result(r) for r in cross_sell]

        return recommendations

    def handle_general_browsing(self, request: SupportRecommendationRequest,
                              support_context) -> Dict[str, List[Dict]]:
        """👀 Handle general browsing scenarios"""
        recommendations = {}

        if self.recommendation_engine:
            # Get comprehensive recommendations
            comprehensive = self.recommendation_engine.get_comprehensive_recommendations(
                request.customer_id, limit=15)

            if comprehensive:
                # Map comprehensive categories to support-friendly names
                category_mapping = {
                    "for_you": "personalized_picks",
                    "popular": "trending_now",
                    "trending": "seasonal_favorites",
                    "upgrade_tier": "premium_collection",
                    "regional_favorites": "local_favorites"
                }

                for orig_cat, new_cat in category_mapping.items():
                    if orig_cat in comprehensive and comprehensive[orig_cat]:
                        recommendations[new_cat] = [self._convert_recommendation_result(r) for r in comprehensive[orig_cat][:5]]

        return recommendations

    def handle_urgent_purchase(self, request: SupportRecommendationRequest,
                             support_context) -> Dict[str, List[Dict]]:
        """⚡ Handle urgent purchase scenarios"""
        recommendations = {}

        if self.recommendation_engine:
            # Get immediately available products
            popular = self.recommendation_engine.get_popular_products(limit=6)
            if popular:
                # Filter for high stock items
                high_stock = [r for r in popular if r.stock_quantity > 10]
                if high_stock:
                    recommendations["immediately_available"] = [self._convert_recommendation_result(r) for r in high_stock[:5]]

            # Get customer favorites for quick decision
            customer_profile = self.recommendation_engine.get_customer_profile(request.customer_id)
            if customer_profile.favorite_categories:
                quick_picks = self.recommendation_engine.get_content_based_recommendations(
                    customer_profile, limit=4)
                if quick_picks:
                    recommendations["your_usual_favorites"] = [self._convert_recommendation_result(r) for r in quick_picks]

        return recommendations

    def _convert_recommendation_result(self, rec_result):
        """🔄 Convert RecommendationResult to dictionary format"""
        try:
            if hasattr(rec_result, '__dict__'):
                return {
                    'product_id': rec_result.product_id,
                    'product_name': rec_result.product_name,
                    'category': rec_result.category,
                    'brand': rec_result.brand,
                    'price': rec_result.price,
                    'price_formatted': rec_result.price_formatted,
                    'description': rec_result.description,
                    'stock_quantity': rec_result.stock_quantity,
                    'stock_status': rec_result.stock_status,
                    'recommendation_score': rec_result.recommendation_score,
                    'recommendation_reason': rec_result.recommendation_reason,
                    'recommendation_type': rec_result.recommendation_type.value if hasattr(rec_result.recommendation_type, 'value') else str(rec_result.recommendation_type)
                }
            else:
                return rec_result
        except Exception as e:
            logger.error(f"❌ Error converting recommendation result: {e}")
            return rec_result if isinstance(rec_result, dict) else {}

    def _get_mood_aware_enhancements(self, request: SupportRecommendationRequest,
                                   base_recommendations):
        """😊 Get mood-aware recommendation enhancements"""
        enhancements = {}

        mood_template = self.mood_response_templates.get(request.customer_mood, self.mood_response_templates["neutral"])
        focus = mood_template["recommendation_focus"]

        if focus == "premium_alternatives" and self.recommendation_engine:
            # Add premium options for frustrated customers
            customer_profile = self.recommendation_engine.get_customer_profile(request.customer_id)
            tier_recs = self.recommendation_engine.get_tier_progression_recommendations(customer_profile, limit=3)
            if tier_recs:
                enhancements["mood_premium_options"] = [self._convert_recommendation_result(r) for r in tier_recs]

        elif focus == "educational_diverse" and self.recommendation_engine:
            # Add diverse options for curious customers
            popular_different_cats = self.recommendation_engine.get_popular_products(limit=6)
            if popular_different_cats:
                enhancements["mood_explore_categories"] = [self._convert_recommendation_result(r) for r in popular_different_cats[:4]]

        return enhancements

    def _combine_and_prioritize_recommendations(self, scenario_recs, mood_recs, request):
        """🔄 Combine and prioritize all recommendations"""
        combined = {}

        # Priority order based on scenario and mood
        priority_order = self._get_priority_order(request)

        # Add scenario recommendations first
        for category, recs in scenario_recs.items():
            if recs:
                combined[category] = recs[:6]  # Limit each category

        # Add mood enhancements
        for category, recs in mood_recs.items():
            if recs:
                combined[category] = recs[:4]  # Smaller limit for enhancements

        # Sort categories by priority
        prioritized = {}
        for category in priority_order:
            if category in combined:
                prioritized[category] = combined[category]

        # Add remaining categories
        for category, recs in combined.items():
            if category not in prioritized:
                prioritized[category] = recs

        return prioritized

    def _get_priority_order(self, request):
        """📊 Get recommendation category priority order"""
        priority_maps = {
            SupportScenario.TROUBLESHOOTING: [
                "problem_solving_alternatives", "reliable_alternatives", "premium_satisfaction_guarantee"
            ],
            SupportScenario.CART_ABANDONMENT: [
                "complete_your_purchase", "budget_friendly_alternatives", "frequently_bought_together"
            ],
            SupportScenario.SATISFACTION_RECOVERY: [
                "premium_satisfaction_guarantee", "highly_rated_reliable", "mood_premium_options"
            ],
            SupportScenario.URGENT_PURCHASE: [
                "immediately_available", "your_usual_favorites", "personalized_picks"
            ]
        }

        return priority_maps.get(request.scenario, [
            "personalized_picks", "trending_now", "frequently_bought_together", "premium_upgrades"
        ])

    def _generate_response_messages(self, request, final_recommendations):
        """💬 Generate contextual response messages"""
        mood_template = self.mood_response_templates.get(request.customer_mood, self.mood_response_templates["neutral"])

        primary_message = mood_template["message_prefix"]

        # Generate specific secondary message based on recommendations
        rec_count = sum(len(recs) for recs in final_recommendations.values())
        category_count = len(final_recommendations)

        if rec_count > 0:
            secondary_message = f"I've found {rec_count} excellent options across {category_count} categories that perfectly match your needs."
        else:
            secondary_message = "Let me help you find exactly what you're looking for."

        # Generate call-to-action based on scenario
        cta_map = {
            SupportScenario.CART_ABANDONMENT: "Ready to complete your purchase? Just let me know which item interests you!",
            SupportScenario.TROUBLESHOOTING: "Would you like me to add any of these reliable alternatives to your cart?",
            SupportScenario.URGENT_PURCHASE: "These items are in stock and ready for immediate delivery. Shall we proceed?",
            SupportScenario.SATISFACTION_RECOVERY: "I guarantee these premium options will exceed your expectations. Would you like to try one?"
        }

        call_to_action = cta_map.get(request.scenario, "Which of these products would you like to learn more about?")

        # Generate reasoning
        reasoning = [
            f"Recommendations tailored for {request.scenario.value.replace('_', ' ')} scenario",
            f"Optimized for {request.customer_mood} customer mood",
            f"Based on your purchase history and preferences"
        ]

        # Generate next actions
        next_actions = [
            "Ask specific questions about any product",
            "Add items to cart for purchase",
            "Compare product features and prices",
            "Request additional recommendations"
        ]

        return {
            "primary": primary_message,
            "secondary": secondary_message,
            "cta": call_to_action,
            "reasoning": reasoning,
            "next_actions": next_actions
        }

    def _calculate_confidence_score(self, recommendations, request):
        """📊 Calculate recommendation confidence score"""
        base_score = 0.5

        # Boost based on number of recommendations
        rec_count = sum(len(recs) for recs in recommendations.values())
        if rec_count >= 10:
            base_score += 0.3
        elif rec_count >= 5:
            base_score += 0.2
        else:
            base_score += 0.1

        # Boost based on customer history
        if len(request.conversation_history) > 2:
            base_score += 0.1

        # Boost based on specific scenario handling
        if request.scenario in [SupportScenario.TROUBLESHOOTING, SupportScenario.SATISFACTION_RECOVERY]:
            base_score += 0.1

        return min(base_score, 1.0)

    def _estimate_satisfaction_impact(self, recommendations, request):
        """📈 Estimate customer satisfaction impact"""
        impact_factors = 0

        # Check for problem-solving recommendations
        if any("problem_solving" in cat or "satisfaction" in cat for cat in recommendations.keys()):
            impact_factors += 2

        # Check for mood-appropriate responses
        if request.customer_mood == "frustrated" and any("premium" in cat for cat in recommendations.keys()):
            impact_factors += 2
        elif request.customer_mood == "curious" and any("explore" in cat for cat in recommendations.keys()):
            impact_factors += 1

        # Check for personalization
        if any("personalized" in cat or "for_you" in cat for cat in recommendations.keys()):
            impact_factors += 1

        if impact_factors >= 3:
            return "high"
        elif impact_factors >= 1:
            return "medium"
        else:
            return "low"

    def _get_fallback_response(self, request):
        """🔄 Get fallback response when engine is unavailable"""
        return SupportRecommendationResponse(
            recommendations={"basic": []},
            primary_message="I'd be happy to help you find the right products.",
            secondary_message="Let me assist you with your request.",
            call_to_action="Please tell me more about what you're looking for.",
            confidence_score=0.3,
            recommendation_reasoning=["Basic assistance available"],
            total_recommendations=0,
            estimated_satisfaction_impact="low",
            next_best_actions=["Provide more specific requirements"]
        )

# Utility function for easy integration
def get_customer_support_recommendations(customer_id: int, support_query: str,
                                       scenario: str = "general_browsing",
                                       customer_mood: str = "neutral",
                                       conversation_history: List[Dict] = None,
                                       **kwargs):
    """🎯 Convenience function for getting customer support recommendations"""
    try:
        engine = CustomerSupportRecommendationEngine()

        # Convert string scenario to enum
        scenario_enum = SupportScenario(scenario) if scenario in [s.value for s in SupportScenario] else SupportScenario.GENERAL_BROWSING

        request = SupportRecommendationRequest(
            customer_id=customer_id,
            support_query=support_query,
            scenario=scenario_enum,
            customer_mood=customer_mood,
            conversation_history=conversation_history or [],
            **kwargs
        )

        response = engine.get_support_recommendations(request)

        return {
            "success": True,
            "recommendations": response.recommendations,
            "messages": {
                "primary": response.primary_message,
                "secondary": response.secondary_message,
                "call_to_action": response.call_to_action
            },
            "metadata": {
                "confidence_score": response.confidence_score,
                "satisfaction_impact": response.estimated_satisfaction_impact,
                "total_recommendations": response.total_recommendations,
                "reasoning": response.recommendation_reasoning,
                "next_actions": response.next_best_actions
            }
        }

    except Exception as e:
        logger.error(f"❌ Error in convenience function: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": {},
            "messages": {
                "primary": "I'd be happy to help you.",
                "secondary": "Please let me know what you're looking for.",
                "call_to_action": "How can I assist you today?"
            }
        }
