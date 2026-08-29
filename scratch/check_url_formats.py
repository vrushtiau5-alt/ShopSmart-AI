import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    # Fetch sample image_urls
    urls = [u[0] for u in db.session.query(Product.image_url).filter(Product.image_url.isnot(None)).limit(100).all()]
    
    # Check prefixes
    prefixes = db.session.query(
        db.func.substr(Product.image_url, 1, 30),
        db.func.count(Product.id)
    ).group_by(db.func.substr(Product.image_url, 1, 30)).all()

    print("Distinct URL Prefixes in DB:")
    for pref, count in prefixes:
        print(f"  {count} products -> prefix: '{pref}'")
