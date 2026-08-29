import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    vguard = Product.query.filter(Product.name.ilike('%V-Guard Envibe 12D4%')).first()
    if vguard:
        print(f"ID: {vguard.id}")
        print(f"Name: {vguard.name}")
        print(f"Restored Original Amazon Image URL: {vguard.image_url}")
