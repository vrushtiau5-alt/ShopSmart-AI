import os
import sys
import random
from collections import defaultdict

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    upload_dir = 'app/static/uploads/products'
    local_files = []
    if os.path.exists(upload_dir):
        with os.scandir(upload_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    local_files.append(entry.name)

    local_files_set = set(local_files)
    print(f"Total local image files available: {len(local_files)}")

    products = Product.query.all()
    
    cat_to_images = defaultdict(list)
    missing_count = 0
    valid_count = 0

    for p in products:
        filename = os.path.basename(p.image_url) if p.image_url else ''
        if filename and filename in local_files_set and p.image_url.startswith('/static/uploads/products/'):
            valid_count += 1
            cat_to_images[p.category_id].append(p.image_url)
        else:
            missing_count += 1

    print(f"Products currently with valid local image: {valid_count}")
    print(f"Products needing image assignment: {missing_count}")
    print(f"Categories with valid images: {len(cat_to_images)}")

    # All valid local images list as fallback pool
    all_valid_urls = [url for urls in cat_to_images.values() for url in urls]
    if not all_valid_urls:
        all_valid_urls = [f"/static/uploads/products/{fn}" for fn in local_files]

    # Map missing products to category-matched or pooled local images
    updated = 0
    for p in products:
        filename = os.path.basename(p.image_url) if p.image_url else ''
        if not (filename and filename in local_files_set and p.image_url.startswith('/static/uploads/products/')):
            cat_imgs = cat_to_images.get(p.category_id)
            if cat_imgs:
                # Pick deterministic image based on product ID to avoid re-shuffling on every run
                chosen_url = cat_imgs[p.id % len(cat_imgs)]
            else:
                chosen_url = all_valid_urls[p.id % len(all_valid_urls)]
            
            p.image_url = chosen_url
            updated += 1

    db.session.commit()
    print(f"Successfully updated {updated} products to use valid local image URLs!")
