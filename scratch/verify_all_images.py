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

    total = Product.query.count()
    products_with_url = db.session.query(Product.id, Product.image_url).all()
    
    valid_count = 0
    missing_count = 0
    
    for pid, url in products_with_url:
        filename = os.path.basename(url) if url else ''
        if filename and filename in local_files and url.startswith('/static/uploads/products/'):
            valid_count += 1
        else:
            missing_count += 1

    print("========================================")
    print("ALL PRODUCTS IMAGE MAP STATUS")
    print("========================================")
    print(f"Total Products: {total}")
    print(f"Products with Valid Local Image: {valid_count}")
    print(f"Products Missing Local Image: {missing_count}")
    print("========================================")
