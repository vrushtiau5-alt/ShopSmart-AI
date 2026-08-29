#!/usr/bin/env python3
"""
Fix ShopSmart AI Product Images
Restores valid image URLs for all 48,203 products in the MySQL database.
- Featured seed products (first 13 products) use seed_product_1.jpg .. seed_product_13.jpg
- All other products are assigned valid, existing JPEG files from app/static/uploads/products/
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models.product import Product


def fix_product_images():
    start_time = time.time()
    app = create_app()

    uploads_dir = os.path.join(app.root_path, 'static', 'uploads', 'products')
    if not os.path.exists(uploads_dir):
        print(f"Uploads directory not found: {uploads_dir}")
        return

    # List all valid non-seed JPEG files in uploads directory
    all_files = sorted([
        f for f in os.listdir(uploads_dir)
        if f.endswith('.jpg') and not f.startswith('seed_product_')
    ])
    num_files = len(all_files)
    print(f"Discovered {num_files} valid product image JPEG files in {uploads_dir}")

    with app.app_context():
        products = Product.query.order_by(Product.id.asc()).all()
        total_prods = len(products)
        print(f"Found {total_prods} products in database to update.")

        updated_count = 0
        seed_count = 0
        local_file_count = 0

        update_tuples = []

        for idx, p in enumerate(products):
            if idx < 13:
                # Seed products 1 to 13 map to seed_product_1.jpg to seed_product_13.jpg
                seed_fn = f"seed_product_{idx + 1}.jpg"
                seed_fp = os.path.join(uploads_dir, seed_fn)
                if os.path.exists(seed_fp):
                    img_url = f"/static/uploads/products/{seed_fn}"
                    seed_count += 1
                else:
                    assigned_file = all_files[idx % num_files]
                    img_url = f"/static/uploads/products/{assigned_file}"
                    local_file_count += 1
            else:
                # Deterministically assign an image file from all_files pool based on index
                assigned_file = all_files[(idx - 13) % num_files]
                img_url = f"/static/uploads/products/{assigned_file}"
                local_file_count += 1

            update_tuples.append((p.id, img_url))
            updated_count += 1

        # Execute high-speed bulk update in chunks of 500
        for i in range(0, len(update_tuples), 500):
            chunk = update_tuples[i:i + 500]
            case_clauses = []
            params = {}

            for c_idx, (p_id, img_url) in enumerate(chunk):
                param_id = f"id_{c_idx}"
                param_url = f"url_{c_idx}"
                case_clauses.append(f"WHEN id = :{param_id} THEN :{param_url}")
                params[param_id] = p_id
                params[param_url] = img_url

            ids_clause = ", ".join(f":id_{c_idx}" for c_idx in range(len(chunk)))
            case_sql = " ".join(case_clauses)
            sql = f"UPDATE products SET image_url = CASE {case_sql} END WHERE id IN ({ids_clause})"

            db.session.execute(db.text(sql), params)
            db.session.commit()

        print("\n========================================================")
        print(" Product Image Restoration Completed Successfully")
        print("========================================================")
        print(f" Total Products Updated : {updated_count}")
        print(f" Featured Seed Images   : {seed_count}")
        print(f" Local Image File Links : {local_file_count}")
        print(f" Elapsed Time           : {time.time() - start_time:.2f} seconds")
        print("========================================================\n")


if __name__ == '__main__':
    fix_product_images()
