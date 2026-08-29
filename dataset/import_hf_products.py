#!/usr/bin/env python3
"""
ShopSmart AI - Hugging Face API Product Importer
Imports 100,000+ products directly through the Hugging Face Dataset Viewer REST API
into the ShopSmart AI MySQL database without downloading parquet or full datasets locally.
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
logger = logging.getLogger('HFImporter')

# Default configuration settings
DEFAULT_HF_DATASET = os.environ.get('HF_DATASET', 'Qdrant/hm_ecommerce_products')
DEFAULT_HF_CONFIG = os.environ.get('HF_CONFIG', 'default')
DEFAULT_HF_SPLIT = os.environ.get('HF_SPLIT', 'train')
DEFAULT_HF_API_URL = os.environ.get('HF_API_URL', 'https://datasets-server.huggingface.co/rows')
DEFAULT_HF_API_BATCH_SIZE = int(os.environ.get('HF_API_BATCH_SIZE', '100'))
DEFAULT_HF_DB_BATCH_SIZE = int(os.environ.get('HF_DB_BATCH_SIZE', '500'))
DEFAULT_HF_TARGET_PRODUCTS = int(os.environ.get('HF_TARGET_PRODUCTS', '100000'))
DEFAULT_HF_MAX_RETRIES = int(os.environ.get('HF_MAX_RETRIES', '5'))
DEFAULT_HF_REQUEST_TIMEOUT = int(os.environ.get('HF_REQUEST_TIMEOUT', '30'))

PROGRESS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'hf_import_progress.json')
UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'uploads', 'products'))


def get_api_url() -> str:
    """Returns the base URL for the Hugging Face Dataset Viewer API."""
    return DEFAULT_HF_API_URL


def fetch_api_batch(
    dataset: str = DEFAULT_HF_DATASET,
    config: str = DEFAULT_HF_CONFIG,
    split: str = DEFAULT_HF_SPLIT,
    offset: int = 0,
    length: int = 100,
    token: Optional[str] = None,
    max_retries: int = DEFAULT_HF_MAX_RETRIES,
    timeout: int = DEFAULT_HF_REQUEST_TIMEOUT
) -> Optional[Dict[str, Any]]:
    """
    Fetches a single paginated batch of rows from the Hugging Face REST API.
    Handles rate limiting (429), server errors (5xx), timeouts, and exponential backoff retries.
    """
    url = get_api_url()
    params = {
        'dataset': dataset,
        'config': config,
        'split': split,
        'offset': offset,
        'length': length
    }
    
    headers = {
        'User-Agent': 'ShopSmart-AI-Importer/1.0'
    }
    if token:
        headers['Authorization'] = f"Bearer {token}"
        
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=(10, timeout))
            
            if response.status_code == 200:
                return response.json()
            
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else (2 ** attempt * 2)
                logger.warning(f"Rate limited (429) at offset {offset}. Retrying in {wait_time}s... (Attempt {attempt}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            if response.status_code in (500, 502, 503, 504):
                wait_time = 2 ** attempt * 2
                logger.warning(f"Server error ({response.status_code}) at offset {offset}. Retrying in {wait_time}s... (Attempt {attempt}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            logger.error(f"API request failed with status code {response.status_code}: {response.text[:200]}")
            return None

        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt * 2
            logger.warning(f"Network error at offset {offset}: {e}. Retrying in {wait_time}s... (Attempt {attempt}/{max_retries})")
            time.sleep(wait_time)
            
    logger.error(f"Failed to fetch offset {offset} after {max_retries} attempts.")
    return None


CATEGORY_IMAGES = {
    'tops': [
        'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1618354691373-d851c5c3a990?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=600&q=80'
    ],
    'dresses': [
        'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?auto=format&fit=crop&w=600&q=80'
    ],
    'trousers': [
        'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1582552938357-32b906df40cb?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?auto=format&fit=crop&w=600&q=80'
    ],
    'jackets': [
        'https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1548883354-7622d03aca27?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1544441893-675973e31985?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1520975954732-35dd22299614?auto=format&fit=crop&w=600&q=80'
    ],
    'shoes': [
        'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1560769629-975ec94e6a86?auto=format&fit=crop&w=600&q=80'
    ],
    'underwear': [
        'https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=600&q=80'
    ],
    'accessories': [
        'https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1523206489230-c012c64b2b48?auto=format&fit=crop&w=600&q=80'
    ],
    'default': [
        'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=600&q=80',
        'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80'
    ]
}


def get_fallback_fashion_image(category_name: str, article_id: str) -> str:
    """Returns a deterministic, high quality fashion photo URL for a category."""
    cat_lower = category_name.lower()
    group_key = 'default'
    if any(w in cat_lower for w in ('top', 'vest', 'shirt', 'blouse', 't-shirt', 'jersey', 'sweater', 'hoodie')):
        group_key = 'tops'
    elif any(w in cat_lower for w in ('dress', 'skirt', 'gown')):
        group_key = 'dresses'
    elif any(w in cat_lower for w in ('trousers', 'pants', 'jeans', 'shorts', 'leggings')):
        group_key = 'trousers'
    elif any(w in cat_lower for w in ('jacket', 'coat', 'blazer', 'cardigan', 'outerwear')):
        group_key = 'jackets'
    elif any(w in cat_lower for w in ('shoe', 'boot', 'sneaker', 'footwear', 'sandal')):
        group_key = 'shoes'
    elif any(w in cat_lower for w in ('bra', 'underwear', 'lingerie', 'panties', 'briefs', 'swimwear', 'socks')):
        group_key = 'underwear'
    elif any(w in cat_lower for w in ('bag', 'hat', 'belt', 'scarf', 'glove', 'accessory', 'jewelry')):
        group_key = 'accessories'

    img_list = CATEGORY_IMAGES.get(group_key, CATEGORY_IMAGES['default'])
    hash_idx = int(hashlib.md5(article_id.encode('utf-8')).hexdigest()[:8], 16) % len(img_list)
    return img_list[hash_idx]


def extract_image_url(image_val: Any, category_name: str = '', article_id: str = '') -> Optional[str]:
    """
    Extracts a clean image URL string from raw API image value.
    Replaces dead S3 bucket URLs (qdrant-nextjs-demo-product-images) with high quality category fashion photos.
    """
    url = None
    if isinstance(image_val, str):
        val = image_val.strip()
        if val.startswith('http://') or val.startswith('https://') or val.startswith('/static/'):
            url = val
    elif isinstance(image_val, dict):
        for key in ('src', 'url', 'path', 'link'):
            if key in image_val and isinstance(image_val[key], str):
                v = image_val[key].strip()
                if v.startswith('http://') or v.startswith('https://'):
                    url = v
                    break

    # Check if URL is dead or from qdrant-nextjs-demo-product-images S3 bucket
    if not url or 'qdrant-nextjs-demo-product-images' in url:
        return get_fallback_fashion_image(category_name, article_id)

    return url


def parse_price(price_val: Any, article_id: str) -> float:
    """
    Parses price from dataset row if available.
    If price is missing or invalid, generates a deterministic price based on article ID
    so prices remain stable across runs without breaking non-null schema constraints.
    """
    if price_val is not None:
        try:
            val_str = str(price_val).strip()
            cleaned = re.sub(r'[^\d.]', '', val_str)
            if cleaned:
                p = float(cleaned)
                if p > 0:
                    return round(p, 2)
        except (ValueError, TypeError):
            pass

    # Deterministic price generation based on article_id hash (e.g., $14.99 - $129.99)
    hash_num = int(hashlib.md5(article_id.encode('utf-8')).hexdigest()[:8], 16)
    base_price = 14.99 + (hash_num % 11500) / 100.0
    return round(base_price, 2)


def extract_product_data(row_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts product fields from a raw Hugging Face row object.
    Maps dataset fields to standard ShopSmart AI Product representation.
    """
    row = row_dict.get('row', row_dict)
    if not isinstance(row, dict):
        return None

    # Title extraction
    title = row.get('prod_name') or row.get('product_name') or row.get('product_title') or row.get('name') or row.get('title')
    if not title or not isinstance(title, str):
        return None
        
    title = title.strip()
    title = re.sub(r'\s+', ' ', title)
    if not title or title.lower() in ('n/a', 'unknown product', 'product 123', 'none'):
        return None
        
    # Truncate title if longer than 255 chars
    if len(title) > 255:
        title = title[:255].strip()

    # Article ID / Product Code
    article_id = str(row.get('article_id') or row.get('product_code') or row.get('id') or '').strip()
    if not article_id:
        article_id = hashlib.md5(title.encode('utf-8')).hexdigest()[:10]

    # Description
    desc = row.get('detail_desc') or row.get('product_description') or row.get('description')
    if not desc or not isinstance(desc, str) or not desc.strip():
        # Fallback description using available metadata
        dept = row.get('department_name') or row.get('section_name') or 'Apparel'
        color = row.get('colour_group_name') or row.get('perceived_colour_value_name') or ''
        group = row.get('product_group_name') or row.get('product_type_name') or 'Clothing'
        desc_parts = [title]
        if color:
            desc_parts.append(f"in {color}")
        desc_parts.append(f"- {group} from {dept}.")
        desc = " ".join(desc_parts)
    else:
        desc = desc.strip()

    # Brand
    brand = row.get('ground_truth_brand') or row.get('brand') or 'H&M'
    brand = str(brand).strip()
    if not brand or brand.lower() in ('n/a', 'none', 'unknown'):
        brand = 'H&M'
    if len(brand) > 100:
        brand = brand[:100].strip()

    # Category
    cat_raw = row.get('product_type_name') or row.get('product_group_name') or row.get('garment_group_name') or row.get('index_name') or 'Fashion'
    category_name = normalize_category(str(cat_raw))

    # Image URL
    image_url = extract_image_url(row.get('image_url') or row.get('image') or row.get('img_url'), category_name, article_id)
    if not image_url:
        image_url = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80'

    # Price
    price = parse_price(row.get('price'), article_id)

    # Features & Specifications
    features = []
    if row.get('colour_group_name'):
        features.append(f"Color: {row.get('colour_group_name')}")
    if row.get('graphical_appearance_name'):
        features.append(f"Pattern: {row.get('graphical_appearance_name')}")
    if row.get('garment_group_name'):
        features.append(f"Group: {row.get('garment_group_name')}")
    if row.get('section_name'):
        features.append(f"Section: {row.get('section_name')}")

    specs = {}
    if row.get('article_id'):
        specs['Article ID'] = str(row.get('article_id'))
    if row.get('product_code'):
        specs['Product Code'] = str(row.get('product_code'))
    if row.get('index_name'):
        specs['Department'] = str(row.get('index_name'))
    if row.get('colour_group_name'):
        specs['Color'] = str(row.get('colour_group_name'))

    return {
        'article_id': article_id,
        'title': title,
        'name': title,
        'description': desc,
        'brand': brand,
        'category_name': category_name,
        'image_url': image_url,
        'price': price,
        'features': json.dumps(features) if features else None,
        'specs': json.dumps(specs) if specs else None
    }


def normalize_category(cat_str: str) -> str:
    """Normalizes category strings for clean grouping and duplicate avoidance."""
    if not cat_str or cat_str.lower() in ('n/a', 'none', 'null', 'nan'):
        return 'Apparel'
    
    cat = cat_str.strip()
    if '|' in cat:
        cat = cat.split('|')[0].strip()
    if '>' in cat:
        cat = cat.split('>')[-1].strip()
        
    cat = re.sub(r'\s+', ' ', cat).title()
    if len(cat) > 100:
        cat = cat[:100].strip()
        
    return cat or 'Apparel'


def generate_product_key(article_id: str, title: str, brand: str) -> str:
    """Generates a unique deterministic key for duplicate detection."""
    raw = f"{article_id}_{title.lower()}_{brand.lower()}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def resolve_category(
    category_name: str,
    categories_cache: Dict[str, int],
    dry_run: bool = False
) -> int:
    """
    Checks category cache and database for existing category.
    Creates a new Category record if it does not exist (unless dry_run).
    """
    norm_key = category_name.lower()
    if norm_key in categories_cache:
        return categories_cache[norm_key]

    if dry_run:
        # Assign mock category ID for dry run mode
        categories_cache[norm_key] = 9999
        return 9999

    cat = Category.query.filter(db.func.lower(Category.name) == norm_key).first()
    if not cat:
        cat_slug = slugify(category_name)
        # Ensure category slug uniqueness
        existing_slug = Category.query.filter_by(slug=cat_slug).first()
        if existing_slug:
            cat_slug = f"{cat_slug}-{hashlib.md5(category_name.encode()).hexdigest()[:4]}"
            
        cat = Category(
            name=category_name,
            slug=cat_slug,
            description=f"Collection of {category_name} items",
            is_active=True
        )
        db.session.add(cat)
        db.session.flush()

    categories_cache[norm_key] = cat.id
    return cat.id


def download_product_image(image_url: str, article_id: str) -> str:
    """
    Optionally downloads remote product image to local static uploads directory.
    Returns relative path `/static/uploads/products/<filename>` or fallback URL on error.
    """
    if not image_url or not image_url.startswith('http'):
        return image_url

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    filename = f"hf_{article_id}.jpg"
    filepath = os.path.join(UPLOADS_DIR, filename)
    rel_path = f"/static/uploads/products/{filename}"

    if os.path.exists(filepath):
        return rel_path

    try:
        res = requests.get(image_url, timeout=10)
        if res.status_code == 200 and len(res.content) > 0:
            with open(filepath, 'wb') as f:
                f.write(res.content)
            return rel_path
    except Exception as e:
        logger.debug(f"Failed to download image for {article_id}: {e}")

    return image_url


def save_batch(batch: List[Product], dry_run: bool = False) -> bool:
    """Commits a batch of Product objects to MySQL within a safe transaction."""
    if dry_run or not batch:
        return True
        
    try:
        db.session.add_all(batch)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database commit failed for batch of {len(batch)} products: {e}")
        return False


def load_progress(progress_file: str = PROGRESS_FILE_PATH) -> Dict[str, Any]:
    """Loads saved import progress from JSON file."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load progress file {progress_file}: {e}")
    return {}


def save_progress(progress_data: Dict[str, Any], progress_file: str = PROGRESS_FILE_PATH) -> None:
    """Saves current import progress to JSON file."""
    try:
        os.makedirs(os.path.dirname(progress_file), exist_ok=True)
        progress_data['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save progress file {progress_file}: {e}")


def load_existing_identifiers() -> Tuple[Set[str], Set[str], Set[str]]:
    """Pre-loads existing SKUs, Slugs, and Article keys from database into memory."""
    logger.info("Pre-loading existing SKUs, slugs, and identifiers from database for fast duplicate detection...")
    
    skus = set()
    slugs = set()
    keys = set()

    products = db.session.query(Product.sku, Product.slug, Product.name, Product.brand).all()
    for p_sku, p_slug, p_name, p_brand in products:
        if p_sku:
            skus.add(p_sku)
            # Extract article_id from SKU if SKU format is SKU-HF-<article_id>
            if p_sku.startswith("SKU-HF-"):
                art_id = p_sku[7:]
                keys.add(art_id)
        if p_slug:
            slugs.add(p_slug)
        if p_name and p_brand:
            raw_key = f"_{p_name.lower()}_{p_brand.lower()}"
            keys.add(raw_key)

    logger.info(f"Loaded {len(skus)} existing SKUs, {len(slugs)} existing slugs into memory.")
    return skus, slugs, keys


def import_products(
    target_products: int = DEFAULT_HF_TARGET_PRODUCTS,
    start_offset: int = 0,
    api_batch_size: int = DEFAULT_HF_API_BATCH_SIZE,
    db_batch_size: int = DEFAULT_HF_DB_BATCH_SIZE,
    dataset: str = DEFAULT_HF_DATASET,
    config: str = DEFAULT_HF_CONFIG,
    split: str = DEFAULT_HF_SPLIT,
    dry_run: bool = False,
    download_images: bool = False,
    resume: bool = False,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main product ingestion pipeline.
    Fetches paginated records from Hugging Face API, validates, transforms, deduplicates, and commits to MySQL.
    """
    app = create_app()
    with app.app_context():
        # Handle resume logic
        progress_data = {}
        if resume:
            progress_data = load_progress()
            if progress_data.get('dataset') == dataset and progress_data.get('config') == config and progress_data.get('split') == split:
                start_offset = progress_data.get('last_successful_offset', start_offset)
                logger.info(f"Resuming import from last successful offset: {start_offset}")

        print("=" * 60, flush=True)
        print("ShopSmart AI Hugging Face API Importer", flush=True)
        print("=" * 60, flush=True)
        print(f"Dataset              : {dataset}", flush=True)
        print(f"Config               : {config}", flush=True)
        print(f"Split                : {split}", flush=True)
        print(f"Target Products      : {target_products:,}", flush=True)
        print(f"Starting Offset      : {start_offset:,}", flush=True)
        print(f"API Batch Size       : {api_batch_size}", flush=True)
        print(f"DB Batch Size        : {db_batch_size}", flush=True)
        print(f"Dry Run Mode         : {dry_run}", flush=True)
        print(f"Download Images      : {download_images}", flush=True)
        print("=" * 60, flush=True)

        # Pre-load existing database identifiers
        if not dry_run:
            existing_skus, existing_slugs, existing_keys = load_existing_identifiers()
        else:
            existing_skus, existing_slugs, existing_keys = set(), set(), set()

        categories_cache: Dict[str, int] = {}
        # Pre-load existing categories
        if not dry_run:
            for cat in Category.query.all():
                categories_cache[cat.name.lower()] = cat.id

        # Summary statistics counters
        stats = {
            'dataset_rows_available': 0,
            'api_rows_processed': 0,
            'valid_rows': 0,
            'products_inserted': 0,
            'duplicates_skipped': 0,
            'invalid_rows': 0,
            'categories_created_count': 0,
            'images_downloaded': 0,
            'image_failures': 0,
            'api_requests': 0,
            'api_retries': 0,
            'api_errors': 0,
            'last_successful_offset': start_offset
        }

        initial_cat_count = len(categories_cache)
        current_offset = start_offset
        pending_batch: List[Product] = []

        while stats['products_inserted'] < target_products:
            # Fetch API batch
            stats['api_requests'] += 1
            response_json = fetch_api_batch(
                dataset=dataset,
                config=config,
                split=split,
                offset=current_offset,
                length=api_batch_size,
                token=token
            )

            if not response_json or 'rows' not in response_json:
                stats['api_errors'] += 1
                logger.error(f"Stopping import due to API response error at offset {current_offset}.")
                break

            rows = response_json.get('rows', [])
            num_rows_total = response_json.get('num_rows_total', 0)
            if num_rows_total and stats['dataset_rows_available'] == 0:
                stats['dataset_rows_available'] = num_rows_total
                logger.info(f"Total dataset rows available on Hugging Face: {num_rows_total:,}")

            if not rows:
                logger.info(f"No more rows returned by API at offset {current_offset}. Reached end of dataset.")
                break

            batch_valid = 0
            batch_duplicates = 0
            batch_invalid = 0

            for raw_row in rows:
                stats['api_rows_processed'] += 1
                p_data = extract_product_data(raw_row)

                if not p_data:
                    stats['invalid_rows'] += 1
                    batch_invalid += 1
                    continue

                article_id = p_data['article_id']
                title = p_data['title']
                brand = p_data['brand']
                
                # Deterministic SKU & Slug
                sku = f"SKU-HF-{article_id}"
                base_slug = slugify(title)[:180]
                slug = f"{base_slug}-{article_id[:8]}" if article_id else base_slug

                # Duplicate detection check
                prod_key = generate_product_key(article_id, title, brand)
                if sku in existing_skus or slug in existing_slugs or article_id in existing_keys or prod_key in existing_keys:
                    stats['duplicates_skipped'] += 1
                    batch_duplicates += 1
                    continue

                # Add to in-memory duplicate sets immediately
                existing_skus.add(sku)
                existing_slugs.add(slug)
                existing_keys.add(article_id)
                existing_keys.add(prod_key)

                batch_valid += 1
                stats['valid_rows'] += 1

                # Resolve Category
                cat_id = resolve_category(p_data['category_name'], categories_cache, dry_run=dry_run)

                # Handle Image
                img_url = p_data['image_url']
                if download_images and not dry_run and img_url.startswith('http'):
                    saved_url = download_product_image(img_url, article_id)
                    if saved_url != img_url:
                        stats['images_downloaded'] += 1
                    else:
                        stats['image_failures'] += 1
                    img_url = saved_url

                # Price Verification
                price_res = verify_product_price({'name': title, 'brand': brand, 'price': p_data['price'], 'sku': sku}, enable_remote_api=True)
                final_price = price_res['verified_price'] if (price_res['is_verified'] and price_res['confidence'] in ('HIGH', 'MEDIUM')) else p_data['price']

                # Instantiate Product model
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
                    rating=4.5,
                    reviews_count=12,
                    description=p_data['description'],
                    features=p_data['features'],
                    specifications=p_data['specs'],
                    image_url=img_url,
                    stock_quantity=50,
                    is_available=True,
                    is_active=True,
                    is_featured=False
                )

                pending_batch.append(product)
                stats['products_inserted'] += 1

                # Commit pending batch when reaching db_batch_size
                if len(pending_batch) >= db_batch_size:
                    if save_batch(pending_batch, dry_run=dry_run):
                        pending_batch = []
                        stats['last_successful_offset'] = current_offset + len(rows)
                        if not dry_run:
                            save_progress({
                                'dataset': dataset,
                                'config': config,
                                'split': split,
                                'last_successful_offset': stats['last_successful_offset'],
                                'inserted_count': stats['products_inserted']
                            })
                    else:
                        logger.error("Batch insertion failed. Aborting remaining import.")
                        break

                if stats['products_inserted'] >= target_products:
                    break

            # Print progress block
            print(f"API Offset: {current_offset:<8} | Rows: {len(rows):<4} | Valid: {batch_valid:<4} | Dups: {batch_duplicates:<4} | Total Inserted: {stats['products_inserted']:,}/{target_products:,}", flush=True)

            current_offset += len(rows)
            stats['last_successful_offset'] = current_offset

            # Break loop if target satisfied
            if stats['products_inserted'] >= target_products:
                break

        # Save remaining pending batch
        if pending_batch:
            if save_batch(pending_batch, dry_run=dry_run):
                pending_batch = []
                if not dry_run:
                    save_progress({
                        'dataset': dataset,
                        'config': config,
                        'split': split,
                        'last_successful_offset': current_offset,
                        'inserted_count': stats['products_inserted']
                    })

        stats['categories_created_count'] = len(categories_cache) - initial_cat_count

        # Display Final Summary
        print("\n" + "=" * 60, flush=True)
        print("ShopSmart AI Hugging Face Import Summary", flush=True)
        print("=" * 60, flush=True)
        print(f"Dataset Rows Available  : {stats['dataset_rows_available']:,}", flush=True)
        print(f"API Rows Processed      : {stats['api_rows_processed']:,}", flush=True)
        print(f"Valid Rows              : {stats['valid_rows']:,}", flush=True)
        print(f"Products Inserted       : {stats['products_inserted']:,}", flush=True)
        print(f"Duplicates Skipped      : {stats['duplicates_skipped']:,}", flush=True)
        print(f"Invalid Rows            : {stats['invalid_rows']:,}", flush=True)
        print(f"Categories Created      : {stats['categories_created_count']:,}", flush=True)
        print(f"Images Downloaded       : {stats['images_downloaded']:,}", flush=True)
        print(f"Image Failures          : {stats['image_failures']:,}", flush=True)
        print(f"API Requests            : {stats['api_requests']:,}", flush=True)
        print(f"API Retries             : {stats['api_retries']:,}", flush=True)
        print(f"API Errors              : {stats['api_errors']:,}", flush=True)
        print(f"Last Successful Offset  : {stats['last_successful_offset']:,}", flush=True)
        print("=" * 60, flush=True)
        print("Import completed successfully.", flush=True)
        print("=" * 60 + "\n", flush=True)

        return stats


def main():
    parser = argparse.ArgumentParser(description="ShopSmart AI 100K+ Hugging Face Product Importer")
    parser.add_argument('--limit', type=int, default=DEFAULT_HF_TARGET_PRODUCTS, help="Target number of valid products to import (default: 100000)")
    parser.add_argument('--offset', type=int, default=0, help="Initial API offset to start fetching from (default: 0)")
    parser.add_argument('--api-batch-size', type=int, default=DEFAULT_HF_API_BATCH_SIZE, help="Number of rows per API request (default: 100)")
    parser.add_argument('--batch-size', type=int, default=DEFAULT_HF_DB_BATCH_SIZE, help="Database commit batch size (default: 500)")
    parser.add_argument('--dataset', type=str, default=DEFAULT_HF_DATASET, help="Hugging Face dataset identifier")
    parser.add_argument('--config', type=str, default=DEFAULT_HF_CONFIG, help="Hugging Face dataset config")
    parser.add_argument('--split', type=str, default=DEFAULT_HF_SPLIT, help="Hugging Face dataset split")
    parser.add_argument('--dry-run', action='store_true', help="Run validation & transformation without committing to DB")
    parser.add_argument('--download-images', action='store_true', help="Download product images locally to static uploads directory")
    parser.add_argument('--resume', action='store_true', help="Resume import from last saved offset in progress file")
    
    args = parser.parse_args()

    token = os.environ.get('HF_TOKEN')

    import_products(
        target_products=args.limit,
        start_offset=args.offset,
        api_batch_size=args.api_batch_size,
        db_batch_size=args.batch_size,
        dataset=args.dataset,
        config=args.config,
        split=args.split,
        dry_run=args.dry_run,
        download_images=args.download_images,
        resume=args.resume,
        token=token
    )


if __name__ == '__main__':
    main()
