import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    seed_products = Product.query.order_by(Product.id.asc()).limit(13).all()
    upload_dir = 'app/static/uploads/products'
    
    # Verify local file list
    local_files = set(os.listdir(upload_dir)) if os.path.exists(upload_dir) else set()

    for p in seed_products:
        print(f"========================================")
        print(f"Target Product ID {p.id}: '{p.name}'")
        
        # Search for products with similar name in DB (id > 13)
        keywords = p.name.split()[:2]  # first 2 words
        kw_pattern = f"%{keywords[0]}%"
        
        matches = Product.query.filter(
            Product.id > 13,
            Product.name.ilike(kw_pattern),
            Product.image_url.isnot(None),
            Product.image_url.startswith('/static/uploads/products/')
        ).limit(5).all()

        valid_matches = []
        for m in matches:
            fn = os.path.basename(m.image_url)
            if fn in local_files:
                valid_matches.append(m)
                
        print(f"Found {len(valid_matches)} matching DB products with local images:")
        for vm in valid_matches[:3]:
            print(f"   -> Match ID {vm.id}: '{vm.name[:45]}' | Image: {vm.image_url}")
