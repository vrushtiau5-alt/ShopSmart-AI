import os
import io
import pytest
from PIL import Image
from dataset.import_amazon_products import (
    parse_price,
    normalize_category,
    generate_product_key,
    extract_and_save_image,
    import_amazon_dataset
)

def test_parse_price():
    assert parse_price('$14.47') == 14.47
    assert parse_price('$12.74') == 12.74
    assert parse_price('₹4999') == 4999.00
    assert parse_price('₹4,999.00') == 4999.00
    assert parse_price('4999') == 4999.00
    assert parse_price('$1,299.99') == 1299.99
    assert parse_price('$29.44 - $49.99') == 29.44
    assert parse_price(None) is None
    assert parse_price('') is None
    assert parse_price('N/A') is None
    assert parse_price('-50') is None

def test_normalize_category():
    assert normalize_category('Toys & Games | Arts & Crafts | Craft Kits') == 'Toys & Games'
    assert normalize_category(' Laptops & Computers > Accessories ') == 'Laptops & Computers'
    assert normalize_category('') == 'General'
    assert normalize_category(None) == 'General'

def test_generate_product_key():
    key1 = generate_product_key('Test Product Name', 'Test Brand', 99.99)
    key2 = generate_product_key('Test Product Name', 'Test Brand', 99.99)
    key3 = generate_product_key('Different Name', 'Test Brand', 99.99)
    assert key1 == key2
    assert key1 != key3

def test_extract_and_save_image(tmp_path):
    # Create valid dummy JPEG image bytes in memory
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    valid_bytes = buf.getvalue()

    raw_struct = {'bytes': valid_bytes}
    prod_key = 'testkey123456'
    uploads_dir = str(tmp_path)

    path = extract_and_save_image(raw_struct, None, prod_key, uploads_dir, dry_run=False)
    assert path is not None
    assert path.startswith('/static/uploads/products/')
    assert os.path.exists(os.path.join(uploads_dir, f"prod_{prod_key[:12]}.jpg"))

    # Test dry run mode does not write file
    dry_dir = str(tmp_path / 'dry')
    os.makedirs(dry_dir, exist_ok=True)
    path_dry = extract_and_save_image(raw_struct, None, 'drykey123456', dry_dir, dry_run=True)
    assert path_dry is not None
    assert not os.path.exists(os.path.join(dry_dir, "prod_drykey123456.jpg"))

    # Test fallback URL when raw bytes missing
    fallback_path = extract_and_save_image(None, 'https://example.com/image.jpg', 'fallbackkey', uploads_dir)
    assert fallback_path == 'https://example.com/image.jpg'

def test_import_amazon_dataset_dry_run(app):
    stats = import_amazon_dataset(limit=5, dry_run=True, app=app)
    assert stats['files_processed'] > 0
    assert stats['rows_processed'] > 0
    assert stats['inserted'] == 5
