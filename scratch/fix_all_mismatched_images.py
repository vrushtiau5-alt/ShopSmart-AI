import os
import sys
import pandas as pd
import requests

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

print("Loading dataset/amazon_products_full/amazon-products.csv...")
df = pd.read_csv('dataset/amazon_products_full/amazon-products.csv')

# Drop rows with null name or image
df = df.dropna(subset=['name', 'image'])

print(f"Loaded {len(df)} rows from CSV.")

# Create name -> original image URL dictionary
# Standardize names for lookup
csv_map = {}
for idx, row in df.iterrows():
    name_clean = str(row['name']).strip()
    img_url = str(row['image']).strip()
    if name_clean and img_url and img_url.startswith(('http://', 'https://')):
        csv_map[name_clean] = img_url

print(f"Built mapping dictionary for {len(csv_map)} unique product names.")

upload_dir = 'app/static/uploads/products'
local_files = set(os.listdir(upload_dir)) if os.path.exists(upload_dir) else set()

with app.app_context():
    db_products = Product.query.filter(Product.id > 13).all()
    print(f"Checking {len(db_products)} catalog products in database...")

    updated_count = 0
    downloaded_count = 0
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for p in db_products:
        name_clean = str(p.name).strip()
        orig_img = csv_map.get(name_clean)
        
        if orig_img:
            # Check if current image_url is already matching or valid
            # If current image_url is a mismatched local fallback or dead link, restore original Amazon image URL!
            if p.image_url != orig_img:
                p.image_url = orig_img
                updated_count += 1

        if updated_count % 5000 == 0 and updated_count > 0:
            db.session.commit()
            print(f"Progress: Updated {updated_count} product image URLs...")

    db.session.commit()
    print(f"SUCCESS: Updated {updated_count} products with their EXACT original Amazon dataset images!")
