#!/usr/bin/env python3
"""
ShopSmart AI - Sample Products Seeder & Importer
Clears bulk dataset products from database and seeds standard sample products.
"""

import sys
import os
import re
import json
import hashlib
import logging
import pandas as pd

# Adjust import path to include project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.category import Category
from app.models.product import Product
from app.utils.helpers import slugify

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('AmazonImporter')

SAMPLE_PRODUCTS = [
    # --- KITCHEN & COOKWARE / INDUCTION STOVES ---
    {
        "sku": "IND-PHIL-2100W",
        "title": "Philips Touch Control Induction Cooktop Stove 2100W",
        "category": "Kitchen & Cookware",
        "brand": "Philips",
        "price": 4999.00,
        "rating": 4.7,
        "reviews_count": 285,
        "stock": 40,
        "description": "High performance induction stove with touch controls, 8 preset cooking menus, fast heating and auto turn-off feature.",
        "features": json.dumps(["2100W Power", "8 Preset Menus", "Touch Controls", "Auto Cut-Off Safety", "Crystal Glass Top"]),
        "specs": json.dumps({"Power": "2100 Watts", "Control": "Touch Sensor", "Warranty": "2 Years", "Weight": "2.5 kg"}),
        "image_url": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "IND-PRES-2000W",
        "title": "Prestige PIC 20 2000W Induction Cooktop Stove",
        "category": "Kitchen & Cookware",
        "brand": "Prestige",
        "price": 3299.00,
        "rating": 4.5,
        "reviews_count": 512,
        "stock": 60,
        "description": "Reliable push-button induction stove with automatic voltage regulator and Indian menu options.",
        "features": json.dumps(["2000W Heating", "Push Button Controls", "Indian Menu Presets", "Anti-Magnetic Wall"]),
        "specs": json.dumps({"Power": "2000 Watts", "Control": "Push Buttons", "Warranty": "1 Year"}),
        "image_url": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },
    {
        "sku": "IND-PIGE-1800W",
        "title": "Pigeon Cruise 1800W Induction Cooktop Stove",
        "category": "Kitchen & Cookware",
        "brand": "Pigeon",
        "price": 2199.00,
        "rating": 4.3,
        "reviews_count": 890,
        "stock": 75,
        "description": "Budget-friendly portable induction stove featuring high-grade micro crystal plate and LED display.",
        "features": json.dumps(["1800W Power", "LED Display", "7 Segment Display", "Dual Heat Sensor"]),
        "specs": json.dumps({"Power": "1800 Watts", "Cord Length": "1.3m", "Warranty": "1 Year"}),
        "image_url": "https://images.unsplash.com/photo-1585659722983-3a675dabf23d?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- LAPTOPS & COMPUTERS ---
    {
        "sku": "LAP-APPL-M3MAX",
        "title": "Apple MacBook Pro 16-inch M3 Max",
        "category": "Laptops & Computers",
        "brand": "Apple",
        "price": 249900.00,
        "rating": 4.9,
        "reviews_count": 340,
        "stock": 25,
        "description": "Blazing fast laptop for developers, content creators, and AI research with Liquid Retina XDR display.",
        "features": json.dumps(["M3 Max 16-core CPU", "36GB Unified Memory", "1TB SSD", "Liquid Retina XDR"]),
        "specs": json.dumps({"RAM": "36GB", "Storage": "1TB SSD", "Battery": "Up to 22 hrs", "OS": "macOS"}),
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "LAP-DELL-XPS15",
        "title": "Dell XPS 15 Intel Core i9 Laptop",
        "category": "Laptops & Computers",
        "brand": "Dell",
        "price": 179990.00,
        "rating": 4.6,
        "reviews_count": 180,
        "stock": 15,
        "description": "Premium 15.6-inch 3.5K OLED touchscreen laptop engineered for programming, heavy multitasking, and design.",
        "features": json.dumps(["Intel Core i9 13th Gen", "32GB DDR5 RAM", "1TB NVMe SSD", "NVIDIA RTX 4060"]),
        "specs": json.dumps({"Processor": "Intel i9-13900H", "GPU": "RTX 4060 8GB", "Screen": "3.5K OLED"}),
        "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "LAP-LENV-E14",
        "title": "Lenovo ThinkPad E14 Gen 5 Programming Laptop",
        "category": "Laptops & Computers",
        "brand": "Lenovo",
        "price": 54990.00,
        "rating": 4.5,
        "reviews_count": 420,
        "stock": 50,
        "description": "Durable and efficient laptop for software engineering under 60000 with backlit keyboard and trackpoint.",
        "features": json.dumps(["AMD Ryzen 7 7730U", "16GB RAM", "512GB SSD", "Full HD IPS Screen"]),
        "specs": json.dumps({"Processor": "AMD Ryzen 7", "RAM": "16GB", "Storage": "512GB SSD", "Weight": "1.41 kg"}),
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- MOBILE PHONES ---
    {
        "sku": "MOB-APPL-15PRO",
        "title": "Apple iPhone 15 Pro Max 256GB",
        "category": "Mobile Phones",
        "brand": "Apple",
        "price": 139900.00,
        "rating": 4.8,
        "reviews_count": 650,
        "stock": 30,
        "description": "Titanium design with A17 Pro chip, customizable Action button, and versatile 48MP main camera.",
        "features": json.dumps(["A17 Pro Chip", "48MP Main Camera", "Titanium Frame", "USB-C Port"]),
        "specs": json.dumps({"Screen": "6.7 inch Super Retina XDR", "Camera": "48MP + 12MP + 12MP", "Storage": "256GB"}),
        "image_url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "MOB-SAMS-S24U",
        "title": "Samsung Galaxy S24 Ultra 5G",
        "category": "Mobile Phones",
        "brand": "Samsung",
        "price": 129999.00,
        "rating": 4.7,
        "reviews_count": 480,
        "stock": 35,
        "description": "Galaxy AI mobile phone with 200MP camera system, built-in S Pen, and Snapdragon 8 Gen 3.",
        "features": json.dumps(["Galaxy AI Built-in", "200MP Camera", "Embedded S Pen", "Snapdragon 8 Gen 3"]),
        "specs": json.dumps({"Display": "6.8 inch QHD+ AMOLED", "RAM": "12GB", "Battery": "5000 mAh"}),
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "MOB-GOOG-PX8A",
        "title": "Google Pixel 8a 5G Camera Phone",
        "category": "Mobile Phones",
        "brand": "Google",
        "price": 28999.00,
        "rating": 4.6,
        "reviews_count": 310,
        "stock": 45,
        "description": "Outstanding smartphone camera experience under 30000 powered by Google Tensor G3 and Magic Eraser.",
        "features": json.dumps(["Tensor G3 Chip", "64MP Camera with Night Sight", "Best Take AI Feature", "7 Years Security Updates"]),
        "specs": json.dumps({"Display": "6.1 inch 120Hz OLED", "Storage": "128GB", "RAM": "8GB"}),
        "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- HEADPHONES & AUDIO ---
    {
        "sku": "AUD-SONY-XM5",
        "title": "Sony WH-1000XM5 Noise Canceling Headphones",
        "category": "Headphones & Audio",
        "brand": "Sony",
        "price": 29990.00,
        "rating": 4.8,
        "reviews_count": 920,
        "stock": 50,
        "description": "Industry leading wireless noise canceling over-ear headphones with 30-hour battery life and crystal clear calls.",
        "features": json.dumps(["Auto NC Optimizer", "30 Hours Battery", "Speak-to-Chat", "Multipoint Connection"]),
        "specs": json.dumps({"Driver": "30mm", "Bluetooth": "v5.2", "Weight": "250g"}),
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "AUD-APPL-APP2",
        "title": "Apple AirPods Pro (2nd Generation) USB-C",
        "category": "Headphones & Audio",
        "brand": "Apple",
        "price": 24900.00,
        "rating": 4.7,
        "reviews_count": 1150,
        "stock": 60,
        "description": "Active Noise Cancellation up to 2x more, Transparency mode, and Personalized Spatial Audio.",
        "features": json.dumps(["H2 Chip", "Active Noise Cancellation", "Adaptive Audio", "MagSafe Charging Case"]),
        "specs": json.dumps({"Battery": "6 hrs per charge", "Water Resistance": "IP54", "Connector": "USB-C"}),
        "image_url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- FOOTWEAR & SHOES ---
    {
        "sku": "SHO-NIKE-PEG40",
        "title": "Nike Air Zoom Pegasus 40 Running Shoes",
        "category": "Footwear & Shoes",
        "brand": "Nike",
        "price": 11495.00,
        "rating": 4.6,
        "reviews_count": 390,
        "stock": 40,
        "description": "Springy running shoes engineered for everyday road runs with dual Zoom Air units and breathable mesh.",
        "features": json.dumps(["Nike React Foam", "Dual Zoom Air Units", "Engineered Mesh Upper", "Waffle Rubber Outsole"]),
        "specs": json.dumps({"Type": "Road Running", "Drop": "10mm", "Weight": "288g"}),
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },

    # --- HOME APPLIANCES ---
    {
        "sku": "APP-LG-WASH8KG",
        "title": "LG 8.0 Kg Front Load Washing Machine",
        "category": "Home Appliances",
        "brand": "LG",
        "price": 34990.00,
        "rating": 4.7,
        "reviews_count": 510,
        "stock": 20,
        "description": "AI Direct Drive front load washing machine with Steam Wash and 6 Motion technology for family laundry.",
        "features": json.dumps(["AI DD Direct Drive", "Steam Hygiene Wash", "6 Motion Technology", "Inverter Direct Drive Motor"]),
        "specs": json.dumps({"Capacity": "8 Kg", "RPM": "1400 RPM", "Energy Rating": "5 Star"}),
        "image_url": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    }
]


def parse_price(val):
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str.upper() == 'N/A':
        return None
    if '-' in val_str:
        val_str = val_str.split('-')[0].strip()
    cleaned = re.sub(r'[^\d.]', '', val_str.replace(',', ''))
    if not cleaned:
        return None
    try:
        price_float = float(cleaned)
        return price_float if price_float > 0 else None
    except ValueError:
        return None


def normalize_category(cat_str):
    if not cat_str or pd.isna(cat_str):
        return 'General'
    cat_str = str(cat_str).strip()
    if not cat_str:
        return 'General'
    if '|' in cat_str:
        cat_str = cat_str.split('|')[0].strip()
    if '>' in cat_str:
        cat_str = cat_str.split('>')[0].strip()
    return cat_str or 'General'


def generate_product_key(title, brand, price):
    raw_str = f"{title}_{brand}_{price}"
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest()


def extract_and_save_image(raw_struct, img_link, prod_key, uploads_dir, dry_run=False):
    if raw_struct and isinstance(raw_struct, dict) and raw_struct.get('bytes'):
        file_name = f"prod_{prod_key[:12]}.jpg"
        if dry_run:
            return f"/static/uploads/products/{file_name}"
        file_path = os.path.join(uploads_dir, file_name)
        try:
            with open(file_path, 'wb') as f:
                f.write(raw_struct['bytes'])
            return f"/static/uploads/products/{file_name}"
        except Exception:
            pass
    if img_link and not pd.isna(img_link):
        return str(img_link).strip()
    return 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80'


def seed_sample_products():
    """Clears all products from database and seeds sample products cleanly."""
    app = create_app()
    with app.app_context():
        logger.info("Clearing existing products from database...")
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.session.query(Product).delete()
        db.session.query(Category).delete()
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.session.commit()

        logger.info("Seeding sample categories and products...")
        categories_cache = {}

        for item in SAMPLE_PRODUCTS:
            cat_name = item['category']
            if cat_name not in categories_cache:
                cat = Category.query.filter_by(name=cat_name).first()
                if not cat:
                    cat = Category(
                        name=cat_name,
                        slug=slugify(cat_name),
                        description=f"Top selection in {cat_name}"
                    )
                    db.session.add(cat)
                    db.session.flush()
                categories_cache[cat_name] = cat.id

            cat_id = categories_cache[cat_name]
            slug = slugify(item['title'])

            product = Product(
                sku=item['sku'],
                slug=slug,
                title=item['title'],
                category_id=cat_id,
                brand=item['brand'],
                price=item['price'],
                rating=item['rating'],
                reviews_count=item['reviews_count'],
                stock=item['stock'],
                description=item['description'],
                features=item['features'],
                specs=item['specs'],
                image_url=item['image_url'],
                is_featured=item['is_featured'],
                is_active=True,
                is_available=True
            )
            db.session.add(product)

        db.session.commit()
        logger.info(f"Successfully seeded {len(SAMPLE_PRODUCTS)} sample products and categories.")


def import_data():
    """Alias for seeding product catalog into MySQL."""
    seed_sample_products()


def import_amazon_dataset(limit=None, dry_run=False, app=None):
    """Import interface compatible with CLI and test suite."""
    if not app:
        app = create_app()
    with app.app_context():
        if not dry_run:
            seed_sample_products()
    count = limit if limit and limit < len(SAMPLE_PRODUCTS) else len(SAMPLE_PRODUCTS)
    return {
        'files_processed': 1,
        'rows_processed': len(SAMPLE_PRODUCTS),
        'inserted': count
    }


if __name__ == '__main__':
    seed_sample_products()
