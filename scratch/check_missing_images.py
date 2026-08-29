import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    upload_dir = 'app/static/uploads/products'
    local_files = set()
    if os.path.exists(upload_dir):
        with os.scandir(upload_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    local_files.add(entry.name)

    print(f"Total local image files: {len(local_files)}")

    products = db.session.query(Product.id, Product.name, Product.image_url, Product.category_id).all()
    
    missing_products = []
    valid_products = []
    
    for p in products:
        filename = os.path.basename(p.image_url) if p.image_url else ''
        if filename and filename in local_files:
            valid_products.append(p)
        else:
            missing_products.append(p)

    print(f"Products with valid local image: {len(valid_products)}")
    print(f"Products missing local image: {len(missing_products)}")

    print("\nSample missing products:")
    for p in missing_products[:15]:
        print(f"ID: {p.id} | Name: {p.name[:40]} | image_url: {p.image_url}")
