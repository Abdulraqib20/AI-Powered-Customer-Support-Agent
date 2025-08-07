"""
🚀 Advanced Product Recommendation Engine for Nigerian E-commerce Platform
================================================================================

Multi-Algorithm Recommendation System:
1. Collaborative Filtering (Customer-based & Item-based)
2. Content-Based Filtering (Category, Brand, Price range)
3. Nigerian Market Intelligence (Regional preferences, Seasonal trends)
4. Customer Tier-Based Recommendations (Bronze → Platinum progression)
5. Real-time Inventory-Aware Recommendations
6. Emotional State-Aware Shopping (Happy = Premium, Budget-conscious = Deals)

Features:
- Nigerian brand preference analysis
- State-based geographic recommendations
- Account tier progression incentives
- Seasonal and cultural event awareness
- Multi-currency support (Naira formatting)
- Stock-aware recommendations (no out-of-stock suggestions)

Author: AI Assistant for Nigerian E-commerce Excellence
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from collections import defaultdict, Counter
import math
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import safe_int_env, safe_str_env

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """Types of recommendations we can generate"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    POPULAR_PRODUCTS = "popular_products"
    CATEGORY_BASED = "category_based"
    BRAND_BASED = "brand_based"
    PRICE_BASED = "price_based"
    REGIONAL_POPULAR = "regional_popular"
    TIER_PROGRESSION = "tier_progression"
    SEASONAL_TRENDING = "seasonal_trending"
    CROSS_SELL = "cross_sell"
    UP_SELL = "up_sell"
    SIMILAR_PRODUCTS = "similar_products"
    BOUGHT_TOGETHER = "bought_together"
    RECENTLY_VIEWED = "recently_viewed"
    ABANDONED_CART_RECOVERY = "abandoned_cart_recovery"
    CUSTOMER_SUPPORT_CONTEXTUAL = "customer_support_contextual"
    PRICE_DROP_ALERT = "price_drop_alert"
    BACK_IN_STOCK = "back_in_stock"
    BROWSING_CONTINUATION = "browsing_continuation"
    PROBLEM_SOLVING = "problem_solving"

@dataclass
class RecommendationResult:
    """Structured recommendation result"""
    product_id: int
    product_name: str
    category: str
    brand: str
    price: float
    price_formatted: str
    description: str
    stock_quantity: int
    stock_status: str
    recommendation_score: float
    recommendation_reason: str
    recommendation_type: RecommendationType
    customer_tier_discount: float = 0.0
    regional_popularity: int = 0

@dataclass
class CustomerProfile:
    """Enhanced customer profile for recommendations"""
    customer_id: int
    name: str
    account_tier: str
    state: str
    preferences: Dict[str, Any]
    order_history: List[Dict]
    favorite_categories: List[str]
    favorite_brands: List[str]
    average_order_value: float
    total_orders: int
    last_order_date: Optional[datetime]
    price_sensitivity: str  # "budget", "mid_range", "premium"

@dataclass
class CustomerSupportContext:
    """Context for customer support recommendations"""
    support_query: str
    support_category: str  # "product_issue", "order_problem", "general_inquiry"
    customer_mood: str  # "frustrated", "curious", "satisfied", "urgent"
    conversation_stage: str  # "initial", "diagnosis", "solution", "followup"
    mentioned_products: List[str]
    problem_category: str  # "quality", "delivery", "payment", "returns"
    resolution_priority: str  # "high", "medium", "low"

class NigerianMarketIntelligence:
    """Nigerian market-specific intelligence and trends"""

    # Nigerian seasonal shopping patterns
    SEASONAL_TRENDS = {
        "january": ["electronics", "fitness", "beauty"],  # New Year resolutions
        "february": ["fashion", "beauty", "books"],  # Valentine's, new academic year prep
        "march": ["fashion", "beauty", "automotive"],  # Wedding season starts
        "april": ["books", "computing", "electronics"],  # School resumption
        "may": ["fashion", "beauty", "electronics"],  # End of dry season shopping
        "june": ["fashion", "beauty", "automotive"],  # Mid-year, wedding peak
        "july": ["books", "electronics", "computing"],  # School shopping
        "august": ["books", "fashion", "electronics"],  # Back-to-school peak
        "september": ["fashion", "electronics", "automotive"],  # End of rainy season
        "october": ["fashion", "beauty", "electronics"],  # Independence celebration
        "november": ["electronics", "fashion", "beauty"],  # Pre-Christmas shopping
        "december": ["fashion", "beauty", "electronics", "books"]  # Christmas season
    }

    # State-based preferences (based on economic activities)
    STATE_PREFERENCES = {
        "Lagos": ["electronics", "fashion", "beauty", "computing"],  # Commercial hub
        "Abuja": ["electronics", "fashion", "automotive", "beauty"],  # Federal capital
        "Kano": ["fashion", "beauty", "books", "automotive"],  # Northern commercial center
        "Rivers": ["electronics", "automotive", "fashion", "beauty"],  # Oil industry
        "Oyo": ["books", "fashion", "beauty", "electronics"],  # Educational hub
        "Kaduna": ["automotive", "books", "electronics", "fashion"],  # Industrial center
    }

    # Nigerian brand loyalty patterns
    BRAND_LOYALTY = {
        "Samsung": 0.8,  # High loyalty
        "Tecno": 0.9,    # Very high loyalty (local favorite)
        "Infinix": 0.85, # High loyalty
        "Apple": 0.7,    # Premium brand loyalty
        "Nike": 0.75,    # Sports brand loyalty
        "MAC": 0.8,      # Beauty brand loyalty
    }

    @staticmethod
    def get_seasonal_boost(month: int) -> Dict[str, float]:
        """Get seasonal category boost factors"""
        month_names = ["", "january", "february", "march", "april", "may", "june",
                      "july", "august", "september", "october", "november", "december"]

        current_month = month_names[month].lower()
        trending_categories = NigerianMarketIntelligence.SEASONAL_TRENDS.get(current_month, [])

        boost_factors = {}
        for category in trending_categories:
            boost_factors[category.title()] = 1.3  # 30% boost for seasonal categories

        return boost_factors

    @staticmethod
    def get_regional_preferences(state: str) -> List[str]:
        """Get regional category preferences"""
        return NigerianMarketIntelligence.STATE_PREFERENCES.get(state,
            ["electronics", "fashion", "beauty", "computing"])  # Default preferences

class ProductRecommendationEngine:
    """🎯 Advanced Product Recommendation Engine"""

    def __init__(self):
        self.db_config = {
            'host': safe_str_env('DB_HOST', 'localhost'),
            'port': safe_int_env('DB_PORT', 5432),
            'database': safe_str_env('DB_NAME', 'nigerian_ecommerce'),
            'user': safe_str_env('DB_USER', 'postgres'),
            'password': safe_str_env('DB_PASSWORD', 'oracle'),
        }

        # Initialize Redis for caching recommendations
        try:
            # Safe Redis port parsing - handle secret names and invalid values
            redis_port_str = os.getenv('REDIS_PORT', '6379')
            try:
                # If it's a secret name (contains 'latest' or 'secret'), use default
                if 'latest' in redis_port_str or 'secret' in redis_port_str:
                    redis_port = 6379
                    logger.warning(f"⚠️ Redis port appears to be a secret name, using default: {redis_port}")
                else:
                    redis_port = int(redis_port_str)
            except (ValueError, TypeError):
                redis_port = 6379
                logger.warning(f"⚠️ Invalid Redis port '{redis_port_str}', using default: {redis_port}")

            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=redis_port,
                db=1,  # Use different db for recommendations
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis recommendation cache initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable for recommendations: {e}")
            self.redis_client = None

        self.market_intelligence = NigerianMarketIntelligence()

        # Cache for browsing behavior
        self.browsing_cache = {}

    def get_database_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise Exception(f"Database connection failed: {e}")

    def get_customer_profile(self, customer_id: int) -> CustomerProfile:
        """🔍 Build comprehensive customer profile for recommendations"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get customer basic info
                    cursor.execute("""
                        SELECT customer_id, name, account_tier, state, preferences
                        FROM customers
                        WHERE customer_id = %s
                    """, (customer_id,))

                    customer_data = cursor.fetchone()
                    if not customer_data:
                        raise ValueError(f"Customer {customer_id} not found")

                    # Get order history with product details
                    cursor.execute("""
                        SELECT o.order_id, o.total_amount, o.created_at, o.product_category,
                               p.product_name, p.category, p.brand, p.price
                        FROM orders o
                        LEFT JOIN products p ON o.product_id = p.product_id
                        WHERE o.customer_id = %s
                        ORDER BY o.created_at DESC
                        LIMIT 50
                    """, (customer_id,))

                    order_history = [dict(row) for row in cursor.fetchall()]

                    # Analyze customer preferences from order history
                    categories = [order.get('category') or order.get('product_category', '')
                                for order in order_history if order.get('category') or order.get('product_category')]
                    brands = [order.get('brand', '') for order in order_history if order.get('brand')]
                    amounts = [float(order['total_amount']) for order in order_history if order['total_amount']]

                    favorite_categories = [cat for cat, count in Counter(categories).most_common(3)]
                    favorite_brands = [brand for brand, count in Counter(brands).most_common(3)]

                    # Calculate price sensitivity
                    avg_order_value = sum(amounts) / len(amounts) if amounts else 0
                    if avg_order_value < 50000:  # Below 50K Naira
                        price_sensitivity = "budget"
                    elif avg_order_value < 200000:  # 50K - 200K Naira
                        price_sensitivity = "mid_range"
                    else:  # Above 200K Naira
                        price_sensitivity = "premium"

                    return CustomerProfile(
                        customer_id=customer_data['customer_id'],
                        name=customer_data['name'],
                        account_tier=customer_data['account_tier'],
                        state=customer_data['state'],
                        preferences=customer_data['preferences'] or {},
                        order_history=order_history,
                        favorite_categories=favorite_categories,
                        favorite_brands=favorite_brands,
                        average_order_value=avg_order_value,
                        total_orders=len(order_history),
                        last_order_date=order_history[0]['created_at'] if order_history else None,
                        price_sensitivity=price_sensitivity
                    )

        except Exception as e:
            logger.error(f"❌ Error building customer profile: {e}")
            raise

    def get_popular_products(self, limit: int = 20, category: str = None,
                           state: str = None) -> List[RecommendationResult]:
        """📈 Get popular products with regional and category filtering"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Build dynamic query
                    base_query = """
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               COUNT(o.order_id) as order_count,
                               AVG(o.total_amount) as avg_order_value
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        WHERE p.in_stock = true AND p.stock_quantity > 0
                    """

                    params = []

                    if category:
                        base_query += " AND (p.category ILIKE %s OR p.product_name ILIKE %s)"
                        params.extend([f"%{category}%", f"%{category}%"])

                    if state:
                        # Add regional filtering through customer location
                        base_query += """
                            AND EXISTS (
                                SELECT 1 FROM orders o2
                                JOIN customers c ON o2.customer_id = c.customer_id
                                WHERE o2.product_id = p.product_id AND c.state = %s
                            )
                        """
                        params.append(state)

                    base_query += """
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        ORDER BY order_count DESC, p.price ASC
                        LIMIT %s
                    """
                    params.append(limit)

                    cursor.execute(base_query, params)
                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['order_count'] or 0),
                            recommendation_reason=f"Popular choice • {product['order_count'] or 0} orders",
                            recommendation_type=RecommendationType.POPULAR_PRODUCTS,
                            regional_popularity=product['order_count'] or 0
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting popular products: {e}")
            return []

    def get_collaborative_recommendations(self, customer_profile: CustomerProfile,
                                        limit: int = 10) -> List[RecommendationResult]:
        """🤝 Collaborative Filtering: Customers who bought X also bought Y"""
        try:
            if not customer_profile.order_history:
                return []

            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get products bought by similar customers
                    customer_product_ids = [order.get('product_id') for order in customer_profile.order_history
                                          if order.get('product_id')]

                    if not customer_product_ids:
                        return []

                    # Find customers who bought similar products
                    cursor.execute("""
                        WITH similar_customers AS (
                            SELECT o.customer_id, COUNT(*) as shared_products
                            FROM orders o
                            WHERE o.product_id = ANY(%s)
                            AND o.customer_id != %s
                            GROUP BY o.customer_id
                            HAVING COUNT(*) >= 1
                            ORDER BY shared_products DESC
                            LIMIT 20
                        ),
                        recommended_products AS (
                            SELECT p.product_id, p.product_name, p.category, p.brand,
                                   p.price, p.description, p.stock_quantity, p.in_stock,
                                   COUNT(o.order_id) as recommendation_score,
                                   sc.shared_products
                            FROM similar_customers sc
                            JOIN orders o ON sc.customer_id = o.customer_id
                            JOIN products p ON o.product_id = p.product_id
                            WHERE p.product_id != ALL(%s)  -- Exclude already purchased
                            AND p.in_stock = true AND p.stock_quantity > 0
                            GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                     p.price, p.description, p.stock_quantity, p.in_stock, sc.shared_products
                            ORDER BY recommendation_score DESC, sc.shared_products DESC
                            LIMIT %s
                        )
                        SELECT * FROM recommended_products
                    """, (customer_product_ids, customer_profile.customer_id,
                          customer_product_ids, limit))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['recommendation_score']),
                            recommendation_reason=f"Customers with similar taste also bought this",
                            recommendation_type=RecommendationType.COLLABORATIVE_FILTERING
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error in collaborative filtering: {e}")
            return []

    def get_content_based_recommendations(self, customer_profile: CustomerProfile,
                                        limit: int = 10) -> List[RecommendationResult]:
        """📊 Content-Based Filtering: Based on customer's favorite categories and brands"""
        try:
            if not customer_profile.favorite_categories and not customer_profile.favorite_brands:
                return []

            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get customer's purchased product IDs to exclude
                    purchased_ids = [order.get('product_id') for order in customer_profile.order_history
                                   if order.get('product_id')]

                    # Build query based on favorite categories and brands
                    query_conditions = []
                    params = []

                    if customer_profile.favorite_categories:
                        placeholders = ','.join(['%s'] * len(customer_profile.favorite_categories))
                        query_conditions.append(f"p.category IN ({placeholders})")
                        params.extend(customer_profile.favorite_categories)

                    if customer_profile.favorite_brands:
                        placeholders = ','.join(['%s'] * len(customer_profile.favorite_brands))
                        query_conditions.append(f"p.brand IN ({placeholders})")
                        params.extend(customer_profile.favorite_brands)

                    # Price range based on customer's price sensitivity
                    if customer_profile.price_sensitivity == "budget":
                        query_conditions.append("p.price <= 100000")  # Under 100K
                    elif customer_profile.price_sensitivity == "mid_range":
                        query_conditions.append("p.price BETWEEN 50000 AND 300000")  # 50K-300K
                    # Premium customers - no price restriction

                    where_clause = " OR ".join(query_conditions) if query_conditions else "1=1"

                    exclude_clause = ""
                    if purchased_ids:
                        exclude_placeholders = ','.join(['%s'] * len(purchased_ids))
                        exclude_clause = f"AND p.product_id NOT IN ({exclude_placeholders})"
                        params.extend(purchased_ids)

                    cursor.execute(f"""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               CASE
                                   WHEN p.category = ANY(%s) THEN 2.0
                                   WHEN p.brand = ANY(%s) THEN 1.5
                                   ELSE 1.0
                               END as content_score,
                               COUNT(o.order_id) as popularity_score
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        WHERE ({where_clause})
                        AND p.in_stock = true AND p.stock_quantity > 0
                        {exclude_clause}
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        ORDER BY content_score DESC, popularity_score DESC, p.price ASC
                        LIMIT %s
                    """, (customer_profile.favorite_categories, customer_profile.favorite_brands) +
                         tuple(params) + (limit,))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        # Determine recommendation reason
                        reason = "Matches your preferences"
                        if product['category'] in customer_profile.favorite_categories:
                            reason = f"You love {product['category']} products"
                        elif product['brand'] in customer_profile.favorite_brands:
                            reason = f"You're a {product['brand']} fan"

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['content_score']) * (1 + float(product['popularity_score']) * 0.1),
                            recommendation_reason=reason,
                            recommendation_type=RecommendationType.CONTENT_BASED
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error in content-based filtering: {e}")
            return []

    def get_tier_progression_recommendations(self, customer_profile: CustomerProfile,
                                           limit: int = 5) -> List[RecommendationResult]:
        """🏆 Account Tier Progression: Encourage customers to upgrade tiers"""
        try:
            tier_targets = {
                "Bronze": {"target_amount": 100000, "message": "Spend ₦100K+ to reach Silver tier"},
                "Silver": {"target_amount": 500000, "message": "Spend ₦500K+ to reach Gold tier"},
                "Gold": {"target_amount": 2000000, "message": "Spend ₦2M+ to reach Platinum tier"},
                "Platinum": {"target_amount": 2000000, "message": "Maintain Platinum status with continued premium purchases"}
            }

            current_tier = customer_profile.account_tier
            tier_info = tier_targets.get(current_tier, tier_targets["Bronze"])

            # Get premium products that help tier progression
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock
                        FROM products p
                        WHERE p.price >= %s
                        AND p.in_stock = true AND p.stock_quantity > 0
                        AND p.category IN ('Electronics', 'Computing', 'Automotive')  -- High-value categories
                        ORDER BY p.price DESC
                        LIMIT %s
                    """, (tier_info["target_amount"] * 0.1, limit))  # 10% of tier target

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        # Calculate tier progression discount
                        tier_discount = 0.05 if current_tier in ["Gold", "Platinum"] else 0.02

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['price']) / 10000,  # Higher price = higher score
                            recommendation_reason=f"{tier_info['message']} • Premium quality",
                            recommendation_type=RecommendationType.TIER_PROGRESSION,
                            customer_tier_discount=tier_discount
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error in tier progression recommendations: {e}")
            return []

    def get_seasonal_recommendations(self, customer_profile: CustomerProfile,
                                   limit: int = 8) -> List[RecommendationResult]:
        """🌟 Seasonal Trending: Nigerian seasonal shopping patterns"""
        try:
            current_month = datetime.now().month
            seasonal_boost = self.market_intelligence.get_seasonal_boost(current_month)

            if not seasonal_boost:
                return []

            trending_categories = list(seasonal_boost.keys())

            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    placeholders = ','.join(['%s'] * len(trending_categories))

                    cursor.execute(f"""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               COUNT(o.order_id) as recent_orders
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                            AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
                        WHERE p.category IN ({placeholders})
                        AND p.in_stock = true AND p.stock_quantity > 0
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        ORDER BY recent_orders DESC, p.price ASC
                        LIMIT %s
                    """, tuple(trending_categories) + (limit,))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        # Apply seasonal boost to score
                        category_boost = seasonal_boost.get(product['category'], 1.0)
                        score = float(product['recent_orders']) * category_boost

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=score,
                            recommendation_reason=f"Trending this season • Perfect for {datetime.now().strftime('%B')}",
                            recommendation_type=RecommendationType.SEASONAL_TRENDING
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error in seasonal recommendations: {e}")
            return []

    def get_comprehensive_recommendations(self, customer_id: int,
                                        limit: int = 20) -> Dict[str, List[RecommendationResult]]:
        """🎯 Get comprehensive recommendations using all algorithms"""
        try:
            # Build customer profile
            customer_profile = self.get_customer_profile(customer_id)

            # Get different types of recommendations
            recommendations = {
                "for_you": [],
                "popular": [],
                "trending": [],
                "upgrade_tier": [],
                "regional_favorites": []
            }

            # Collaborative filtering (personalized)
            collab_recs = self.get_collaborative_recommendations(customer_profile, limit=5)
            content_recs = self.get_content_based_recommendations(customer_profile, limit=5)
            recommendations["for_you"] = collab_recs + content_recs

            # Popular products
            recommendations["popular"] = self.get_popular_products(limit=6)

            # Seasonal trending
            recommendations["trending"] = self.get_seasonal_recommendations(customer_profile, limit=6)

            # Tier progression
            recommendations["upgrade_tier"] = self.get_tier_progression_recommendations(customer_profile, limit=4)

            # Regional favorites
            recommendations["regional_favorites"] = self.get_popular_products(
                limit=6, state=customer_profile.state)

            # Sort all recommendations by score
            for category in recommendations:
                recommendations[category] = sorted(
                    recommendations[category],
                    key=lambda x: x.recommendation_score,
                    reverse=True
                )

            logger.info(f"✅ Generated comprehensive recommendations for customer {customer_id}")
            return recommendations

        except Exception as e:
            logger.error(f"❌ Error generating comprehensive recommendations: {e}")
            return {
                "for_you": [],
                "popular": [],
                "trending": [],
                "upgrade_tier": [],
                "regional_favorites": []
            }

    def search_products(self, query: str, customer_id: int = None,
                       category: str = None, max_price: float = None,
                       limit: int = 20) -> List[RecommendationResult]:
        """🔍 Smart Product Search with personalization"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Build search query
                    search_conditions = ["p.in_stock = true", "p.stock_quantity > 0"]
                    params = []

                    # Text search
                    if query:
                        search_conditions.append("""
                            (p.product_name ILIKE %s OR p.description ILIKE %s
                             OR p.brand ILIKE %s OR p.category ILIKE %s)
                        """)
                        search_term = f"%{query}%"
                        params.extend([search_term, search_term, search_term, search_term])

                    # Category filter with flexible matching
                    if category:
                        search_conditions.append("(p.category ILIKE %s OR p.product_name ILIKE %s)")
                        params.extend([f"%{category}%", f"%{category}%"])

                    # Price filter
                    if max_price:
                        search_conditions.append("p.price <= %s")
                        params.append(max_price)

                    where_clause = " AND ".join(search_conditions)

                    # Get customer profile for personalization
                    relevance_score = "1.0"
                    if customer_id:
                        try:
                            customer_profile = self.get_customer_profile(customer_id)
                            # Boost score for favorite categories and brands
                            favorite_categories = "', '".join(customer_profile.favorite_categories)
                            favorite_brands = "', '".join(customer_profile.favorite_brands)

                            relevance_score = f"""
                                CASE
                                    WHEN p.category IN ('{favorite_categories}') THEN 3.0
                                    WHEN p.brand IN ('{favorite_brands}') THEN 2.0
                                    ELSE 1.0
                                END
                            """
                        except:
                            pass  # Use default relevance if profile fails

                    cursor.execute(f"""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               COUNT(o.order_id) as popularity,
                               ({relevance_score}) as relevance_score
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        WHERE {where_clause}
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        ORDER BY relevance_score DESC, popularity DESC, p.price ASC
                        LIMIT %s
                    """, params + [limit])

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['relevance_score']) * (1 + float(product['popularity']) * 0.1),
                            recommendation_reason="Matches your search",
                            recommendation_type=RecommendationType.CONTENT_BASED
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error in product search: {e}")
            return []

    def _get_stock_status(self, stock_quantity: int) -> str:
        """Get human-readable stock status"""
        if stock_quantity == 0:
            return "Out of Stock"
        elif stock_quantity <= 5:
            return "Low Stock"
        elif stock_quantity <= 20:
            return "Limited Stock"
        else:
            return "In Stock"

    def _format_naira(self, amount: float) -> str:
        """Format amount in Nigerian Naira - only use K for amounts ≥ 100,000"""
        if amount >= 1_000_000:
            return f"₦{amount/1_000_000:.1f}M"
        elif amount >= 100_000:  # 🔧 CRITICAL FIX: Only use K for amounts ≥ 100,000
            return f"₦{amount/1_000:.0f}K"
        else:
            return f"₦{amount:,.0f}"  # Show full amount for values less than 100,000

    def track_customer_browsing(self, customer_id: int, product_id: int, action: str = "view"):
        """🔍 Track customer browsing behavior for better recommendations"""
        try:
            timestamp = datetime.now()
            browsing_key = f"browsing_{customer_id}"

            if browsing_key not in self.browsing_cache:
                self.browsing_cache[browsing_key] = []

            self.browsing_cache[browsing_key].append({
                'product_id': product_id,
                'action': action,
                'timestamp': timestamp
            })

            # Keep only last 50 browsing actions
            self.browsing_cache[browsing_key] = self.browsing_cache[browsing_key][-50:]

            # Store in Redis if available
            if self.redis_client:
                self.redis_client.lpush(f"browsing:{customer_id}",
                                      f"{product_id}:{action}:{timestamp.isoformat()}")
                self.redis_client.ltrim(f"browsing:{customer_id}", 0, 49)

        except Exception as e:
            logger.error(f"❌ Error tracking browsing behavior: {e}")

    def get_customer_support_recommendations(self, customer_id: int, support_context: CustomerSupportContext,
                                           limit: int = 10) -> List[RecommendationResult]:
        """🎯 Context-aware recommendations for customer support scenarios"""
        try:
            customer_profile = self.get_customer_profile(customer_id)
            recommendations = []

            # Problem-solving recommendations based on support context
            if support_context.support_category == "product_issue":
                # Recommend alternative products or upgrades
                recommendations.extend(self._get_problem_solving_recommendations(
                    customer_profile, support_context, limit // 2))

            elif support_context.support_category == "order_problem":
                # Recommend similar products or replacement options
                recommendations.extend(self._get_order_replacement_recommendations(
                    customer_profile, support_context, limit // 2))

            elif support_context.support_category == "general_inquiry":
                # Recommend based on inquiry context
                recommendations.extend(self._get_inquiry_based_recommendations(
                    customer_profile, support_context, limit // 2))

            # Add mood-based recommendations
            if support_context.customer_mood == "frustrated":
                # Offer premium alternatives or satisfaction guarantees
                recommendations.extend(self._get_satisfaction_recovery_recommendations(
                    customer_profile, support_context, limit // 2))
            elif support_context.customer_mood == "curious":
                # Educational or exploratory products
                recommendations.extend(self._get_educational_recommendations(
                    customer_profile, support_context, limit // 2))

            # Sort by relevance and remove duplicates
            seen_products = set()
            unique_recommendations = []
            for rec in sorted(recommendations, key=lambda x: x.recommendation_score, reverse=True):
                if rec.product_id not in seen_products:
                    seen_products.add(rec.product_id)
                    unique_recommendations.append(rec)

            return unique_recommendations[:limit]

        except Exception as e:
            logger.error(f"❌ Error getting customer support recommendations: {e}")
            return []

    def get_cross_sell_recommendations(self, customer_id: int, current_product_id: int = None,
                                     cart_items: List[Dict] = None, limit: int = 8) -> List[RecommendationResult]:
        """🛒 Cross-sell recommendations for complementary products"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    # Get products frequently bought together
                    product_ids = []
                    if current_product_id:
                        product_ids.append(current_product_id)
                    if cart_items:
                        product_ids.extend([item.get('product_id') for item in cart_items if item.get('product_id')])

                    if not product_ids:
                        return []

                    # Find products frequently bought with current products
                    placeholders = ','.join(['%s'] * len(product_ids))
                    cursor.execute(f"""
                        WITH target_orders AS (
                            SELECT DISTINCT order_id, customer_id
                            FROM orders
                            WHERE product_id IN ({placeholders})
                        ),
                        complementary_products AS (
                            SELECT p.product_id, p.product_name, p.category, p.brand,
                                   p.price, p.description, p.stock_quantity, p.in_stock,
                                   COUNT(DISTINCT o.order_id) as co_purchase_frequency,
                                   AVG(o.total_amount) as avg_order_value
                            FROM target_orders to_orders
                            JOIN orders o ON to_orders.order_id = o.order_id
                            JOIN products p ON o.product_id = p.product_id
                            WHERE p.product_id NOT IN ({placeholders})
                            AND p.in_stock = true AND p.stock_quantity > 0
                            GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                     p.price, p.description, p.stock_quantity, p.in_stock
                            HAVING COUNT(DISTINCT o.order_id) >= 2
                            ORDER BY co_purchase_frequency DESC, avg_order_value DESC
                            LIMIT %s
                        )
                        SELECT * FROM complementary_products
                    """, tuple(product_ids + product_ids + [limit]))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['co_purchase_frequency']) * 1.5,
                            recommendation_reason=f"Frequently bought together • {product['co_purchase_frequency']} co-purchases",
                            recommendation_type=RecommendationType.CROSS_SELL
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting cross-sell recommendations: {e}")
            return []

    def get_upsell_recommendations(self, customer_id: int, current_product_id: int = None,
                                 current_price: float = None, limit: int = 6) -> List[RecommendationResult]:
        """⬆️ Upsell recommendations for higher-value products"""
        try:
            customer_profile = self.get_customer_profile(customer_id)

            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    # Get current product info if not provided
                    if current_product_id and not current_price:
                        cursor.execute("SELECT price, category FROM products WHERE product_id = %s",
                                     (current_product_id,))
                        product_info = cursor.fetchone()
                        if product_info:
                            current_price = float(product_info['price'])
                            category = product_info['category']
                        else:
                            return []

                    if not current_price:
                        current_price = customer_profile.average_order_value or 100000  # Default 100K

                    # Find higher-value products in same/related categories
                    min_upsell_price = current_price * 1.2  # At least 20% higher
                    max_upsell_price = current_price * 3.0   # Not more than 3x

                    # Adjust based on customer tier and price sensitivity
                    if customer_profile.price_sensitivity == "premium":
                        max_upsell_price = current_price * 5.0
                    elif customer_profile.price_sensitivity == "budget":
                        max_upsell_price = current_price * 1.5

                    cursor.execute("""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               COUNT(o.order_id) as popularity,
                               AVG(CASE WHEN c.account_tier = %s THEN 1 ELSE 0 END) as tier_preference
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        LEFT JOIN customers c ON o.customer_id = c.customer_id
                        WHERE p.price BETWEEN %s AND %s
                        AND p.in_stock = true AND p.stock_quantity > 0
                        AND (%s IS NULL OR p.product_id != %s)
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        ORDER BY tier_preference DESC, popularity DESC, p.price ASC
                        LIMIT %s
                    """, (customer_profile.account_tier, min_upsell_price, max_upsell_price,
                          current_product_id, current_product_id, limit))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        # Calculate value proposition
                        price_increase = ((float(product['price']) - current_price) / current_price) * 100

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['popularity']) * (1 + float(product['tier_preference'])),
                            recommendation_reason=f"Premium upgrade • {price_increase:.0f}% better value",
                            recommendation_type=RecommendationType.UP_SELL
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting upsell recommendations: {e}")
            return []

    def get_abandoned_cart_recommendations(self, customer_id: int,
                                         abandoned_items: List[Dict] = None,
                                         limit: int = 8) -> List[RecommendationResult]:
        """🛒 Cart abandonment recovery recommendations"""
        try:
            customer_profile = self.get_customer_profile(customer_id)
            recommendations = []

            if abandoned_items:
                # Recommendations based on abandoned items
                for item in abandoned_items[:3]:  # Focus on top 3 abandoned items
                    product_id = item.get('product_id')

                    # Get similar but discounted products
                    similar_recs = self.get_similar_products_recommendations(
                        customer_id, product_id, price_filter="lower", limit=2)
                    recommendations.extend(similar_recs)

                    # Get cross-sell for abandoned items
                    cross_sell_recs = self.get_cross_sell_recommendations(
                        customer_id, product_id, limit=2)
                    recommendations.extend(cross_sell_recs)

            # Add general appeal recommendations
            popular_recs = self.get_popular_products(limit=4, state=customer_profile.state)
            recommendations.extend(popular_recs)

            # Sort by relevance and mark as cart recovery
            for rec in recommendations:
                rec.recommendation_type = RecommendationType.ABANDONED_CART_RECOVERY
                rec.recommendation_reason = f"Complete your purchase • {rec.recommendation_reason}"

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"❌ Error getting cart abandonment recommendations: {e}")
            return []

    def get_similar_products_recommendations(self, customer_id: int, product_id: int,
                                           price_filter: str = "any", limit: int = 8) -> List[RecommendationResult]:
        """🔄 Similar products recommendations"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    # Get current product info
                    cursor.execute("""
                        SELECT category, brand, price FROM products WHERE product_id = %s
                    """, (product_id,))

                    current_product = cursor.fetchone()
                    if not current_product:
                        return []

                    # Build price filter condition
                    price_condition = ""
                    price_params = []

                    if price_filter == "lower":
                        price_condition = "AND p.price < %s"
                        price_params.append(float(current_product['price']) * 0.9)  # 10% lower
                    elif price_filter == "higher":
                        price_condition = "AND p.price > %s"
                        price_params.append(float(current_product['price']) * 1.1)  # 10% higher
                    elif price_filter == "similar":
                        price_condition = "AND p.price BETWEEN %s AND %s"
                        base_price = float(current_product['price'])
                        price_params.extend([base_price * 0.8, base_price * 1.2])  # ±20%

                    cursor.execute(f"""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               COUNT(o.order_id) as popularity,
                               CASE
                                   WHEN p.category = %s AND p.brand = %s THEN 3.0
                                   WHEN p.category = %s THEN 2.0
                                   WHEN p.brand = %s THEN 1.5
                                   ELSE 1.0
                               END as similarity_score
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        WHERE p.product_id != %s
                        AND p.in_stock = true AND p.stock_quantity > 0
                        {price_condition}
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        ORDER BY similarity_score DESC, popularity DESC
                        LIMIT %s
                    """, (current_product['category'], current_product['brand'],
                          current_product['category'], current_product['brand'],
                          product_id) + tuple(price_params) + (limit,))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        # Determine recommendation reason
                        if product['category'] == current_product['category'] and product['brand'] == current_product['brand']:
                            reason = f"Same brand and category"
                        elif product['category'] == current_product['category']:
                            reason = f"Similar {product['category']} product"
                        elif product['brand'] == current_product['brand']:
                            reason = f"Same {product['brand']} brand"
                        else:
                            reason = "Similar features"

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['similarity_score']) * (1 + float(product['popularity']) * 0.1),
                            recommendation_reason=reason,
                            recommendation_type=RecommendationType.SIMILAR_PRODUCTS
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting similar products recommendations: {e}")
            return []

    def _get_problem_solving_recommendations(self, customer_profile: CustomerProfile,
                                           support_context: CustomerSupportContext,
                                           limit: int) -> List[RecommendationResult]:
        """🔧 Problem-solving recommendations for product issues"""
        try:
            recommendations = []

            # If customer mentioned specific products, recommend alternatives
            if support_context.mentioned_products:
                for product_name in support_context.mentioned_products[:2]:
                    # Find products with similar names
                    similar_recs = self._find_products_by_name_similarity(product_name, limit=2)
                    for rec in similar_recs:
                        rec.recommendation_reason = f"Alternative to resolve {support_context.problem_category} issue"
                        rec.recommendation_type = RecommendationType.PROBLEM_SOLVING
                    recommendations.extend(similar_recs)

            # Recommend highly-rated products in customer's favorite categories
            if customer_profile.favorite_categories and len(recommendations) < limit:
                reliable_products = self._get_highly_rated_products(
                    customer_profile.favorite_categories[0], limit - len(recommendations))
                for rec in reliable_products:
                    rec.recommendation_reason = f"Highly reliable {rec.category} option"
                    rec.recommendation_type = RecommendationType.PROBLEM_SOLVING
                recommendations.extend(reliable_products)

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"❌ Error getting problem-solving recommendations: {e}")
            return []

    def _get_satisfaction_recovery_recommendations(self, customer_profile: CustomerProfile,
                                                 support_context: CustomerSupportContext,
                                                 limit: int) -> List[RecommendationResult]:
        """😊 Satisfaction recovery recommendations for frustrated customers"""
        try:
            # Get premium products with good reviews to rebuild confidence
            tier_recs = self.get_tier_progression_recommendations(customer_profile, limit)

            for rec in tier_recs:
                rec.recommendation_reason = "Premium quality to ensure satisfaction"
                rec.recommendation_type = RecommendationType.CUSTOMER_SUPPORT_CONTEXTUAL

            return tier_recs

        except Exception as e:
            logger.error(f"❌ Error getting satisfaction recovery recommendations: {e}")
            return []

    def _find_products_by_name_similarity(self, product_name: str, limit: int = 5) -> List[RecommendationResult]:
        """🔍 Find products with similar names"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    # Use fuzzy matching with ILIKE
                    search_terms = product_name.split()
                    where_conditions = []
                    params = []

                    for term in search_terms:
                        where_conditions.append("p.product_name ILIKE %s")
                        params.append(f"%{term}%")

                    where_clause = " OR ".join(where_conditions)

                    cursor.execute(f"""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock
                        FROM products p
                        WHERE ({where_clause})
                        AND p.in_stock = true AND p.stock_quantity > 0
                        ORDER BY p.product_name
                        LIMIT %s
                    """, params + [limit])

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=1.0,
                            recommendation_reason="Similar product alternative",
                            recommendation_type=RecommendationType.SIMILAR_PRODUCTS
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error finding similar products: {e}")
            return []

    def _get_highly_rated_products(self, category: str, limit: int) -> List[RecommendationResult]:
        """⭐ Get highly-rated products in a category"""
        try:
            with self.get_database_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                    cursor.execute("""
                        SELECT p.product_id, p.product_name, p.category, p.brand,
                               p.price, p.description, p.stock_quantity, p.in_stock,
                               COUNT(o.order_id) as order_count
                        FROM products p
                        LEFT JOIN orders o ON p.product_id = o.product_id
                        WHERE (p.category ILIKE %s OR p.product_name ILIKE %s)
                        AND p.in_stock = true AND p.stock_quantity > 0
                        GROUP BY p.product_id, p.product_name, p.category, p.brand,
                                 p.price, p.description, p.stock_quantity, p.in_stock
                        HAVING COUNT(o.order_id) >= 3  -- At least 3 orders (indicates reliability)
                        ORDER BY order_count DESC
                        LIMIT %s
                    """, (f"%{category}%", f"%{category}%", limit))

                    products = cursor.fetchall()

                    recommendations = []
                    for product in products:
                        stock_status = self._get_stock_status(product['stock_quantity'])

                        recommendations.append(RecommendationResult(
                            product_id=product['product_id'],
                            product_name=product['product_name'],
                            category=product['category'],
                            brand=product['brand'],
                            price=float(product['price']),
                            price_formatted=self._format_naira(product['price']),
                            description=product['description'] or "",
                            stock_quantity=product['stock_quantity'],
                            stock_status=stock_status,
                            recommendation_score=float(product['order_count']),
                            recommendation_reason=f"Highly rated • {product['order_count']} satisfied customers",
                            recommendation_type=RecommendationType.CONTENT_BASED
                        ))

                    return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting highly-rated products: {e}")
            return []

    def _get_order_replacement_recommendations(self, customer_profile: CustomerProfile,
                                             support_context: CustomerSupportContext,
                                             limit: int) -> List[RecommendationResult]:
        """📦 Order replacement recommendations"""
        # For order problems, recommend similar products or direct replacements
        return self.get_content_based_recommendations(customer_profile, limit)

    def _get_inquiry_based_recommendations(self, customer_profile: CustomerProfile,
                                         support_context: CustomerSupportContext,
                                         limit: int) -> List[RecommendationResult]:
        """❓ Inquiry-based recommendations"""
        # For general inquiries, provide personalized recommendations
        return self.get_content_based_recommendations(customer_profile, limit)

    def _get_educational_recommendations(self, customer_profile: CustomerProfile,
                                       support_context: CustomerSupportContext,
                                       limit: int) -> List[RecommendationResult]:
        """📚 Educational recommendations for curious customers"""
        # Recommend diverse products to satisfy curiosity
        popular_recs = self.get_popular_products(limit)
        for rec in popular_recs:
            rec.recommendation_reason = f"Discover new products • {rec.recommendation_reason}"
        return popular_recs
