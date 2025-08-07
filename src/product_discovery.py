#!/usr/bin/env python3
"""
Dynamic Product Discovery System
Automatically learns what products are available in the database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Dict, List, Any
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.database_config import safe_int_env, safe_str_env

load_dotenv()
logger = logging.getLogger(__name__)

class ProductDiscoveryEngine:
    """Dynamically discovers and categorizes products from database"""

    def __init__(self):
        self.db_config = {
            'host': safe_str_env('DB_HOST', 'localhost'),
            'database': safe_str_env('DB_NAME', 'customer_support_agent'),
            'user': safe_str_env('DB_USER', 'postgres'),
            'password': safe_str_env('DB_PASSWORD', ''),
            'port': safe_int_env('DB_PORT', 5432)
        }
        self.product_map = {}
        self.category_map = {}
        self._discover_products()

    def _discover_products(self):
        """Scan database to discover all available products and create smart mappings"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get all products with their categories
            cursor.execute("""
                SELECT product_id, product_name, category, brand, price, stock_quantity, description
                FROM products
                WHERE in_stock = TRUE
                ORDER BY category, product_name
            """)

            products = cursor.fetchall()

            # Build smart mappings
            self._build_smart_mappings(products)

            cursor.close()
            conn.close()

            logger.info(f"✅ Discovered {len(products)} products across {len(self.category_map)} categories")

        except Exception as e:
            logger.error(f"❌ Error discovering products: {e}")

    def _build_smart_mappings(self, products: List[Dict]):
        """Build intelligent product and category mappings"""

        # Reset mappings
        self.product_map = {}
        self.category_map = {}

        # Category-based grouping
        for product in products:
            category = product['category']
            product_name = product['product_name'].lower()

            # Group by category
            if category not in self.category_map:
                self.category_map[category] = []
            self.category_map[category].append(dict(product))

            # Smart keyword mapping
            keywords = self._extract_keywords(product_name, product.get('description', ''))

            for keyword in keywords:
                if keyword not in self.product_map:
                    self.product_map[keyword] = []
                self.product_map[keyword].append({
                    'product': dict(product),
                    'relevance_score': self._calculate_relevance(keyword, product_name, category)
                })

        # Sort by relevance
        for keyword in self.product_map:
            self.product_map[keyword].sort(key=lambda x: x['relevance_score'], reverse=True)

    def _extract_keywords(self, product_name: str, description: str) -> List[str]:
        """Extract searchable keywords from product name and description"""
        keywords = set()

        # Product name keywords
        name_words = product_name.lower().split()
        keywords.update(name_words)

        # Add partial matches for phones
        if 'phone' in product_name.lower():
            keywords.add('phone')
            keywords.add('mobile')
            keywords.add('smartphone')

        # Add partial matches for laptops
        if any(word in product_name.lower() for word in ['laptop', 'computer', 'macbook']):
            keywords.add('laptop')
            keywords.add('computer')
            keywords.add('notebook')

        # Add brand-specific keywords
        brands = ['samsung', 'iphone', 'apple', 'google', 'pixel', 'oneplus', 'huawei', 'xiaomi']
        for brand in brands:
            if brand in product_name.lower():
                keywords.add(brand)
                if brand == 'iphone':
                    keywords.add('apple')
                    keywords.add('phone')
                    keywords.add('mobile')

        return list(keywords)

    def _calculate_relevance(self, keyword: str, product_name: str, category: str) -> float:
        """Calculate how relevant a product is for a keyword"""
        score = 0.0

        # Exact name match gets highest score
        if keyword == product_name.lower():
            score = 10.0
        # Keyword in product name
        elif keyword in product_name.lower():
            score = 8.0
        # Keyword matches category
        elif keyword in category.lower():
            score = 6.0
        else:
            score = 4.0

        return score

    def find_products_for_query(self, query: str, limit: int = 5) -> List[Dict]:
        """Find the most relevant products for a user query"""
        query_lower = query.lower()
        results = []

        # Extract potential keywords from query
        query_keywords = query_lower.split()

        # Find matches
        for keyword in query_keywords:
            if keyword in self.product_map:
                for product_info in self.product_map[keyword][:limit]:
                    product = product_info['product']
                    if not any(r['product_id'] == product['product_id'] for r in results):
                        results.append(product)

        return results[:limit]

    def get_category_summary(self) -> Dict[str, int]:
        """Get summary of available categories"""
        return {category: len(products) for category, products in self.category_map.items()}

    def get_smart_suggestions(self, intended_product: str) -> Dict[str, Any]:
        """Get smart suggestions for what customer might be looking for"""
        products = self.find_products_for_query(intended_product, limit=3)

        if not products or len(products) == 0:
            return {
                'found': False,
                'message': f"We don't currently have {intended_product} in stock.",
                'suggestions': []
            }

        # Find the best match
        best_match = products[0]
        alternatives = products[1:] if len(products) > 1 else []

        return {
            'found': True,
            'best_match': best_match,
            'alternatives': alternatives,
            'category_info': self.category_map.get(best_match['category'], [])
        }

# Global instance
_global_discovery_engine = None

def get_product_discovery_engine():
    """Get or create global product discovery engine"""
    global _global_discovery_engine
    if _global_discovery_engine is None:
        _global_discovery_engine = ProductDiscoveryEngine()
    return _global_discovery_engine
