import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.product import Product

app = create_app()

with app.app_context():
    print("Querying total products...")
    total_products = Product.query.count()
    
    print("Querying image URLs...")
    products_with_url = db.session.query(Product.image_url).filter(Product.image_url.isnot(None), Product.image_url != '').all()
    with_image_url = len(products_with_url)
    without_image_url = total_products - with_image_url

    print("Scanning uploads directory...")
    upload_dir = 'app/static/uploads/products'
    local_files = set()
    total_bytes = 0
    if os.path.exists(upload_dir):
        with os.scandir(upload_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    local_files.add(entry.name)
                    total_bytes += entry.stat().st_size

    print("Verifying image references...")
    valid_image_refs = 0
    missing_image_refs = 0
    url_formats = set()
    sample_urls = []

    for i, (url,) in enumerate(products_with_url):
        if i < 15:
            sample_urls.append(url)
            
        filename = os.path.basename(url)
        
        if url.startswith('/static/'):
            url_formats.add("starts with /static/")
        elif url.startswith('static/'):
            url_formats.add("starts with static/")
        elif url.startswith('uploads/'):
            url_formats.add("starts with uploads/")
        elif url.startswith('http://') or url.startswith('https://'):
            url_formats.add("http(s) external URL")
        else:
            url_formats.add("filename or relative path")

        if filename in local_files:
            valid_image_refs += 1
        else:
            missing_image_refs += 1

    print("========================================")
    print("ShopSmart AI Image Diagnostic Report")
    print("========================================")
    print(f"Total Products: {total_products}")
    print(f"Products With Image URL: {with_image_url}")
    print(f"Products Without Image URL: {without_image_url}")
    print(f"Local Image Files: {len(local_files)}")
    print(f"Storage size: {total_bytes / (1024**3):.2f} GB ({total_bytes} bytes)")
    print(f"Valid Image References: {valid_image_refs}")
    print(f"Missing Image Files: {missing_image_refs}")
    print("----------------------------------------")
    print("Sample image_url formats from DB:")
    for s in sample_urls:
        print(f"  - {s}")
    print("URL Formats found:", list(url_formats))
    print("========================================")
