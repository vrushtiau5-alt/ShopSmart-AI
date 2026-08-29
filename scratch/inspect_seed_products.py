import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    products = Product.query.order_by(Product.id.asc()).limit(20).all()
    print("First 20 products in database:")
    for p in products:
        print(f"ID: {p.id:2d} | Name: {p.name[:50]:50s} | Brand: {p.brand:15s} | Image: {p.image_url}")
