import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    seed_products = Product.query.order_by(Product.id.asc()).limit(13).all()
    print("========================================")
    print("VERIFIED FEATURED / SEED PRODUCTS IMAGES")
    print("========================================")
    for p in seed_products:
        local_path = os.path.join('app', p.image_url.lstrip('/'))
        exists = os.path.exists(local_path)
        size = os.path.getsize(local_path) if exists else 0
        print(f"ID {p.id:2d} | '{p.name[:38]:38s}' | File: {p.image_url} | Exists: {exists} ({size} bytes)")
    print("========================================")
