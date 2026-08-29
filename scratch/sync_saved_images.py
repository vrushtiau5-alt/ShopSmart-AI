#!/usr/bin/env python3
import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models.product import Product
from app.models.category import Category

CATEGORY_FALLBACKS = {
    "electronics": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
    "apparel": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80",
    "home": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=600&q=80",
    "toys": "https://images.unsplash.com/photo-1566576721346-d4a3b4eaeb55?auto=format&fit=crop&w=600&q=80",
    "general": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80"
}


def sync_images():
    start = time.time()
    app = create_app()

    with app.app_context():
        uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'products')
        saved_files = set(os.listdir(uploads_dir))
        print(f"Discovered {len(saved_files)} saved JPEG files in static uploads.")

        prods = db.session.query(Product.id, Product.category_id).all()
        categories = dict(db.session.query(Category.id, Category.name).all())

        print(f"Linking images for {len(prods)} products in database...")

        matched_count = 0
        fallback_count = 0

        update_items = []
        for p_id, cat_id in prods:
            fname = f"prod_{p_id}.jpg"
            if fname in saved_files:
                update_items.append((p_id, f"/static/uploads/products/{fname}"))
                matched_count += 1
            else:
                cat_name = (categories.get(cat_id) or "").lower()
                pool_key = "general"
                if any(k in cat_name for k in ["electron", "computer", "phone", "audio"]):
                    pool_key = "electronics"
                elif any(k in cat_name for k in ["apparel", "clothing", "shoe", "fashion"]):
                    pool_key = "apparel"
                elif any(k in cat_name for k in ["home", "garden", "kitchen", "decor"]):
                    pool_key = "home"
                elif any(k in cat_name for k in ["toy", "game", "baby"]):
                    pool_key = "toys"

                fallback_url = CATEGORY_FALLBACKS[pool_key]
                update_items.append((p_id, fallback_url))
                fallback_count += 1

        # Bulk SQL update
        for i in range(0, len(update_items), 500):
            chunk = update_items[i:i+500]
            case_clauses = []
            params = {}

            for idx, (p_id, img_url) in enumerate(chunk):
                param_id = f"id_{idx}"
                param_url = f"url_{idx}"
                case_clauses.append(f"WHEN id = :{param_id} THEN :{param_url}")
                params[param_id] = p_id
                params[param_url] = img_url

            ids_clause = ", ".join(f":{param_id}" for param_id in [f"id_{idx}" for idx in range(len(chunk))])
            case_sql = " ".join(case_clauses)
            sql = f"UPDATE products SET image_url = CASE {case_sql} END WHERE id IN ({ids_clause})"

            db.session.execute(db.text(sql), params)
            db.session.commit()

        print(f"SUCCESS: Linked {matched_count} real product photos to MySQL database!")
        print(f"Fallback images set: {fallback_count}")
        print(f"Total time elapsed: {time.time() - start:.2f} seconds.")


if __name__ == '__main__':
    sync_images()
