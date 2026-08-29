import sys
import os
import json
import pandas as pd
from app.utils.helpers import slugify

def prepare_products(cleaned_file, output_file=None):
    """
    Prepares cleaned Amazon products for bulk MySQL database insertion.
    Maps categories, generates SKUs, formats JSON specs and features.
    """
    if not os.path.exists(cleaned_file):
        print(f"Cleaned dataset file '{cleaned_file}' not found.")
        return None

    print(f"Preparing products from cleaned file: {cleaned_file}...")
    df = pd.read_csv(cleaned_file)

    prepared_records = []
    for idx, row in df.iterrows():
        title = str(row.get('title', 'Product')).strip()
        category = str(row.get('category', 'General')).strip()
        brand = str(row.get('brand', 'Generic')).strip()
        if not brand or brand == 'nan': brand = 'Generic'

        price = float(row.get('price', 999.0))
        rating = float(row.get('rating', 4.5))
        reviews_count = int(row.get('reviews_count', 12)) if not pd.isna(row.get('reviews_count')) else 12

        sku = f"AZ-{slugify(brand)[:10].upper()}-{idx+1000}"
        slug = f"{slugify(title)[:60]}-{idx+1000}"

        image_url = str(row.get('image_url', '')).strip()
        if not image_url or image_url == 'nan':
            image_url = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80'

        desc = str(row.get('description', '')).strip()
        if not desc or desc == 'nan':
            desc = f"Premium {title} from {brand}. Engineered for quality performance."

        features = json.dumps(["High Quality Build", "Official Brand Warranty", "Top Rated Selection"])
        specs = json.dumps({"Brand": brand, "Rating": f"{rating}/5.0", "Condition": "New"})

        prepared_records.append({
            'sku': sku,
            'slug': slug,
            'title': title,
            'category': category,
            'brand': brand,
            'price': price,
            'rating': rating,
            'reviews_count': reviews_count,
            'description': desc,
            'features': features,
            'specs': specs,
            'image_url': image_url,
            'stock': 50,
            'is_available': True,
            'is_active': True,
            'is_featured': (rating >= 4.7)
        })

    prep_df = pd.DataFrame(prepared_records)

    if not output_file:
        output_file = os.path.join(os.path.dirname(cleaned_file), 'prepared_amazon_products.csv')

    prep_df.to_csv(output_file, index=False)
    print(f"Successfully prepared {len(prep_df)} products. Saved to: {output_file}")
    return output_file

if __name__ == '__main__':
    if len(sys.argv) > 1:
        prepare_products(sys.argv[1])
    else:
        print("Usage: python dataset/prepare_amazon_products.py <path_to_cleaned_dataset>")
