import os
import sys
import requests

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

# Curated direct, high-quality image URLs matching each of the 13 seed products
ACCURATE_SEED_IMAGES = {
    1: "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=600&q=80",  # Philips Induction Cooktop
    2: "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=600&q=80",  # Prestige Induction Cooktop
    3: "https://images.unsplash.com/photo-1585659722983-3a675dabf23d?auto=format&fit=crop&w=600&q=80",  # Pigeon Induction Cooktop
    4: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",  # Apple MacBook Pro
    5: "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=600&q=80",  # Dell XPS Laptop
    6: "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=600&q=80",  # Lenovo ThinkPad Laptop
    7: "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80",  # Apple iPhone 15 Pro Max
    8: "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80",  # Samsung Galaxy S24 Ultra
    9: "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80",  # Google Pixel 8a Phone
    10: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80", # Sony WH-1000XM5 Headphones
    11: "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=600&q=80", # Apple AirPods Pro
    12: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80", # Nike Air Zoom Pegasus Running Shoes
    13: "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=600&q=80"  # LG Front Load Washing Machine
}

upload_dir = 'app/static/uploads/products'
os.makedirs(upload_dir, exist_ok=True)

with app.app_context():
    print("Downloading and saving accurate local images for Seed Products 1 to 13...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for pid, img_url in ACCURATE_SEED_IMAGES.items():
        product = db.session.get(Product, pid)
        if not product:
            continue
            
        local_filename = f"seed_product_{pid}.jpg"
        local_filepath = os.path.join(upload_dir, local_filename)
        
        try:
            resp = requests.get(img_url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(local_filepath, 'wb') as f:
                    f.write(resp.content)
                product.image_url = f"/static/uploads/products/{local_filename}"
                print(f"[OK] Product {pid} ('{product.name[:35]}') -> Saved {local_filename}")
            else:
                print(f"[WARN] Failed HTTP download for Product {pid}, status {resp.status_code}")
        except Exception as e:
            print(f"[ERROR] Error downloading for Product {pid}: {e}")

    db.session.commit()
    print("All seed product images updated and committed successfully!")
