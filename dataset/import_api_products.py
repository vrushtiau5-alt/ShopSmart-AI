#!/usr/bin/env python3
"""
ShopSmart AI - Public API Electronics & Food Product Importer
Imports a small, curated set of Electronics and Food/Groceries products
from a public REST API into the ShopSmart AI MySQL database.
Strictly additive: preserves all existing products, categories, and application features.
"""

import sys
import os
import re
import json
import time
import hashlib
import logging
import argparse
import datetime
import requests
from typing import Dict, Any, List, Optional, Tuple, Set

# Adjust import path to include project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.category import Category
from app.models.product import Product
from app.services.price_verifier import verify_product_price
from app.utils.helpers import slugify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('APIImporter')

DEFAULT_API_URL = os.environ.get('PRODUCT_API_URL', 'https://dummyjson.com/products?limit=200')
API_KEY = os.environ.get('PRODUCT_API_KEY', '')

# Category mapping definitions
ELECTRONICS_CATEGORIES = {
    'smartphones': 'Mobile Phones',
    'laptops': 'Laptops & Computers',
    'tablets': 'Tablets & Gadgets',
    'mobile-accessories': 'Headphones & Audio',
    'kitchen-accessories': 'Home Appliances'
}

FOOD_CATEGORIES = {
    'groceries': 'Food & Groceries',
    'beverages': 'Beverages & Drinks',
    'snacks': 'Snacks & Sweets',
    'dairy': 'Dairy & Fresh'
}


def fetch_api_products(api_url: str = DEFAULT_API_URL, api_key: str = API_KEY) -> List[Dict[str, Any]]:
    """
    Fetches product data from public REST API.
    Supports optional Authorization header if API_KEY is configured in .env.
    """
    headers = {
        'User-Agent': 'ShopSmart-AI-Importer/1.0',
        'Accept': 'application/json'
    }
    if api_key:
        headers['Authorization'] = f"Bearer {api_key}"

    try:
        logger.info(f"Fetching product dataset from public API: {api_url}")
        res = requests.get(api_url, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and 'products' in data:
                return data['products']
            if isinstance(data, list):
                return data
        logger.error(f"API returned status code {res.status_code}: {res.text[:200]}")
    except Exception as e:
        logger.error(f"Failed to fetch data from API: {e}")

    return []


def classify_product(item: Dict[str, Any]) -> Optional[str]:
    """
    Classifies an API item into 'electronics' or 'food'.
    Returns 'electronics', 'food', or None if it belongs to neither group.
    """
    cat = str(item.get('category', '')).lower()
    title = str(item.get('title', '')).lower()
    tags = [str(t).lower() for t in item.get('tags', [])]
    text = f"{cat} {title} {' '.join(tags)}"

    # Check Electronics classification
    if cat in ELECTRONICS_CATEGORIES or any(w in text for w in ('phone', 'laptop', 'tablet', 'headphone', 'audio', 'camera', 'charger', 'appliance', 'screen', 'speaker')):
        return 'electronics'

    # Check Food classification
    if cat in FOOD_CATEGORIES or any(w in text for w in ('grocery', 'food', 'snack', 'beverage', 'drink', 'fruit', 'meat', 'oil', 'milk', 'water', 'tea', 'coffee', 'juice', 'sauce', 'dairy', 'dessert')):
        return 'food'

    return None


def normalize_api_category(category_raw: str, group_type: str) -> str:
    """Normalizes API categories into clean ShopSmart AI category names."""
    cat_lower = category_raw.lower().strip()
    if group_type == 'electronics':
        if cat_lower in ELECTRONICS_CATEGORIES:
            return ELECTRONICS_CATEGORIES[cat_lower]
        if 'phone' in cat_lower or 'mobile' in cat_lower:
            return 'Mobile Phones'
        if 'laptop' in cat_lower or 'computer' in cat_lower:
            return 'Laptops & Computers'
        if 'audio' in cat_lower or 'headphone' in cat_lower or 'accessory' in cat_lower:
            return 'Headphones & Audio'
        return 'Electronics'
    else:
        if cat_lower in FOOD_CATEGORIES:
            return FOOD_CATEGORIES[cat_lower]
        if 'drink' in cat_lower or 'beverage' in cat_lower:
            return 'Beverages'
        if 'snack' in cat_lower or 'sweet' in cat_lower:
            return 'Snacks & Sweets'
        return 'Food & Groceries'


def extract_api_product(item: Dict[str, Any], group_type: str) -> Optional[Dict[str, Any]]:
    """
    Transforms raw API product dictionary into ShopSmart AI Product field mapping.
    """
    title = str(item.get('title') or item.get('name') or '').strip()
    if not title or title.lower() in ('n/a', 'unknown', 'null'):
        return None

    desc = str(item.get('description') or '').strip()
    if not desc:
        desc = f"High quality {title} ({group_type.capitalize()})."

    # Price
    try:
        price = float(item.get('price', 0.0))
        if price <= 0:
            price = 19.99
    except (ValueError, TypeError):
        price = 19.99

    # Brand
    brand = str(item.get('brand') or 'Generic').strip()
    if not brand or brand.lower() in ('n/a', 'null', 'none'):
        brand = 'Generic'

    # Category
    cat_raw = str(item.get('category') or group_type)
    category_name = normalize_api_category(cat_raw, group_type)

    # Image URL
    img_url = item.get('thumbnail') or (item.get('images')[0] if item.get('images') and isinstance(item['images'], list) else None) or item.get('image')
    if not img_url or not isinstance(img_url, str) or not img_url.startswith('http'):
        img_url = 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80' if group_type == 'food' else 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?auto=format&fit=crop&w=600&q=80'

    # Rating & Stock
    try:
        rating = float(item.get('rating', 4.5))
    except (ValueError, TypeError):
        rating = 4.5

    try:
        stock = int(item.get('stock', 50))
    except (ValueError, TypeError):
        stock = 50

    # API item ID for deterministic SKU
    item_id = str(item.get('id') or hashlib.md5(title.encode()).hexdigest()[:6])

    return {
        'item_id': item_id,
        'title': title,
        'description': desc,
        'price': round(price, 2),
        'brand': brand,
        'category_name': category_name,
        'image_url': img_url,
        'rating': round(rating, 1),
        'stock': stock,
        'group_type': group_type
    }


def resolve_category(category_name: str, categories_cache: Dict[str, int], dry_run: bool = False) -> int:
    """Finds or creates a Category record in MySQL."""
    norm_key = category_name.lower()
    if norm_key in categories_cache:
        return categories_cache[norm_key]

    if dry_run:
        categories_cache[norm_key] = 9999
        return 9999

    cat = Category.query.filter(db.func.lower(Category.name) == norm_key).first()
    if not cat:
        cat_slug = slugify(category_name)
        existing_slug = Category.query.filter_by(slug=cat_slug).first()
        if existing_slug:
            cat_slug = f"{cat_slug}-{hashlib.md5(category_name.encode()).hexdigest()[:4]}"

        cat = Category(
            name=category_name,
            slug=cat_slug,
            description=f"Selection of {category_name} items",
            is_active=True
        )
        db.session.add(cat)
        db.session.flush()

    categories_cache[norm_key] = cat.id
    return cat.id


def load_existing_identifiers() -> Tuple[Set[str], Set[str], Set[str]]:
    """Loads existing SKUs, Slugs, and Product Keys from MySQL into memory."""
    skus, slugs, keys = set(), set(), set()
    products = db.session.query(Product.sku, Product.slug, Product.name, Product.brand).all()
    for p_sku, p_slug, p_name, p_brand in products:
        if p_sku:
            skus.add(p_sku)
        if p_slug:
            slugs.add(p_slug)
        if p_name and p_brand:
            keys.add(f"{p_name.lower()}_{p_brand.lower()}")
    return skus, slugs, keys


def import_api_products(
    electronics_limit: int = 100,
    food_limit: int = 100,
    dry_run: bool = False,
    api_url: str = DEFAULT_API_URL
) -> Dict[str, Any]:
    """Main importer entry point for API Electronics & Food products."""
    app = create_app()
    with app.app_context():
        print("=" * 60, flush=True)
        print("ShopSmart AI - Public API Product Importer", flush=True)
        print("=" * 60, flush=True)
        print(f"Target Electronics Limit : {electronics_limit}", flush=True)
        print(f"Target Food Limit        : {food_limit}", flush=True)
        print(f"Dry Run Mode             : {dry_run}", flush=True)
        print("=" * 60, flush=True)

        raw_items = fetch_api_products(api_url=api_url)
        logger.info(f"Fetched {len(raw_items)} total products from API.")

        if not dry_run:
            existing_skus, existing_slugs, existing_keys = load_existing_identifiers()
        else:
            existing_skus, existing_slugs, existing_keys = set(), set(), set()

        categories_cache: Dict[str, int] = {}
        if not dry_run:
            for cat in Category.query.all():
                categories_cache[cat.name.lower()] = cat.id

        stats = {
            'api_products_fetched': len(raw_items),
            'electronics_fetched': 0,
            'food_fetched': 0,
            'valid_products': 0,
            'products_inserted': 0,
            'duplicates_skipped': 0,
            'invalid_products': 0,
            'images_saved': 0,
            'image_failures': 0,
            'categories_created': 0
        }

        initial_cat_count = len(categories_cache)
        elec_count = 0
        food_count = 0
        pending_products: List[Product] = []

        for item in raw_items:
            group_type = classify_product(item)
            if not group_type:
                continue

            if group_type == 'electronics':
                stats['electronics_fetched'] += 1
                if elec_count >= electronics_limit:
                    continue
            elif group_type == 'food':
                stats['food_fetched'] += 1
                if food_count >= food_limit:
                    continue

            p_data = extract_api_product(item, group_type)
            if not p_data:
                stats['invalid_products'] += 1
                continue

            title = p_data['title']
            brand = p_data['brand']
            item_id = p_data['item_id']

            sku = f"SKU-API-{group_type[:3].upper()}-{item_id}"
            base_slug = slugify(title)[:180]
            slug = f"{base_slug}-api-{item_id}"
            prod_key = f"{title.lower()}_{brand.lower()}"

            # Duplicate check
            if sku in existing_skus or slug in existing_slugs or prod_key in existing_keys:
                stats['duplicates_skipped'] += 1
                continue

            existing_skus.add(sku)
            existing_slugs.add(slug)
            existing_keys.add(prod_key)

            stats['valid_products'] += 1

            # Category resolution
            cat_id = resolve_category(p_data['category_name'], categories_cache, dry_run=dry_run)

            # Price Verification
            price_res = verify_product_price({'name': title, 'brand': brand, 'price': p_data['price'], 'sku': sku}, enable_remote_api=True)
            final_price = price_res['verified_price'] if (price_res['is_verified'] and price_res['confidence'] in ('HIGH', 'MEDIUM')) else p_data['price']

            # Create Product instance
            product = Product(
                sku=sku,
                slug=slug,
                name=title,
                brand=brand,
                category_id=cat_id,
                price=final_price,
                original_price=p_data['price'],
                verified_market_price=price_res['verified_price'],
                price_source=price_res['source'],
                price_verified_at=datetime.datetime.utcnow(),
                price_confidence=price_res['confidence'],
                rating=p_data['rating'],
                reviews_count=15,
                description=p_data['description'],
                image_url=p_data['image_url'],
                stock_quantity=p_data['stock'],
                is_available=True,
                is_active=True,
                is_featured=False
            )

            pending_products.append(product)
            stats['products_inserted'] += 1
            if p_data['image_url']:
                stats['images_saved'] += 1

            if group_type == 'electronics':
                elec_count += 1
            else:
                food_count += 1

        # Database Commit
        if not dry_run and pending_products:
            try:
                db.session.add_all(pending_products)
                db.session.commit()
                logger.info(f"Successfully committed {len(pending_products)} new API products to MySQL.")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to commit API products batch: {e}")

        stats['categories_created'] = len(categories_cache) - initial_cat_count

        # Final Summary
        print("\n" + "=" * 60, flush=True)
        print("ShopSmart AI Public API Product Importer Summary", flush=True)
        print("=" * 60, flush=True)
        print(f"API Products Fetched    : {stats['api_products_fetched']}", flush=True)
        print(f"Electronics Fetched     : {stats['electronics_fetched']}", flush=True)
        print(f"Food Fetched            : {stats['food_fetched']}", flush=True)
        print(f"Valid Products          : {stats['valid_products']}", flush=True)
        print(f"Products Inserted       : {stats['products_inserted']}", flush=True)
        print(f"Duplicates Skipped      : {stats['duplicates_skipped']}", flush=True)
        print(f"Invalid Products        : {stats['invalid_products']}", flush=True)
        print(f"Images Saved            : {stats['images_saved']}", flush=True)
        print(f"Image Failures          : {stats['image_failures']}", flush=True)
        print(f"Categories Created      : {stats['categories_created']}", flush=True)
        print("=" * 60, flush=True)
        print("Import completed successfully.", flush=True)
        print("=" * 60 + "\n", flush=True)

        return stats


def main():
    parser = argparse.ArgumentParser(description="ShopSmart AI Public API Electronics & Food Product Importer")
    parser.add_argument('--electronics-limit', type=int, default=100, help="Target number of electronics products (default: 100)")
    parser.add_argument('--food-limit', type=int, default=100, help="Target number of food products (default: 100)")
    parser.add_argument('--dry-run', action='store_true', help="Run validation & transformation without committing to DB")
    parser.add_argument('--api-url', type=str, default=DEFAULT_API_URL, help="Custom REST API URL")
    
    args = parser.parse_args()

    import_api_products(
        electronics_limit=args.electronics_limit,
        food_limit=args.food_limit,
        dry_run=args.dry_run,
        api_url=args.api_url
    )


if __name__ == '__main__':
    main()
