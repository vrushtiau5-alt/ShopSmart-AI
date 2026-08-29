import sys
import os
import re
import pandas as pd

def clean_amazon_dataset(input_file, output_file=None):
    """
    Cleans raw Amazon product dataset in CSV/Parquet format.
    Normalizes columns, cleans text, validates prices/ratings, and removes duplicates.
    """
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return None

    print(f"Loading raw dataset: {input_file}...")
    if input_file.endswith('.parquet'):
        df = pd.read_parquet(input_file)
    else:
        df = pd.read_csv(input_file)

    print(f"Raw record count: {len(df)}")

    # Column Mapping Standardisation
    col_mapping = {
        'title': 'title', 'name': 'title', 'product_name': 'title',
        'category': 'category', 'main_category': 'category',
        'brand': 'brand',
        'price': 'price', 'discount_price': 'price', 'actual_price': 'price',
        'rating': 'rating', 'stars': 'rating',
        'ratings_count': 'reviews_count', 'reviews_count': 'reviews_count', 'num_ratings': 'reviews_count',
        'description': 'description', 'about_product': 'description',
        'img_link': 'image_url', 'image_url': 'image_url', 'image': 'image_url'
    }

    df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

    # Ensure required columns exist
    for required in ['title', 'category', 'brand', 'price', 'rating', 'description', 'image_url']:
        if required not in df.columns:
            df[required] = ''

    # Clean Price Column
    def clean_price(val):
        if pd.isna(val): return 999.0
        val_str = str(val).replace('₹', '').replace('$', '').replace(',', '').strip()
        try:
            res = float(re.search(r'\d+(?:\.\d+)?', val_str).group())
            return res if res > 0 else 999.0
        except Exception:
            return 999.0

    df['price'] = df['price'].apply(clean_price)

    # Clean Rating Column
    def clean_rating(val):
        if pd.isna(val): return 4.5
        try:
            r = float(re.search(r'\d+(?:\.\d+)?', str(val)).group())
            return min(max(r, 1.0), 5.0)
        except Exception:
            return 4.5

    df['rating'] = df['rating'].apply(clean_rating)

    # Remove empty or invalid titles
    df['title'] = df['title'].astype(str).str.strip()
    df = df[df['title'].str.len() > 3]

    # Deduplicate by title
    df.drop_duplicates(subset=['title'], keep='first', inplace=True)

    print(f"Cleaned record count: {len(df)}")

    if not output_file:
        output_file = os.path.join(os.path.dirname(input_file), 'cleaned_amazon_products.csv')

    df.to_csv(output_file, index=False)
    print(f"Saved cleaned dataset to: {output_file}")
    return output_file

if __name__ == '__main__':
    if len(sys.argv) > 1:
        clean_amazon_dataset(sys.argv[1])
    else:
        print("Usage: python dataset/clean_dataset.py <path_to_raw_dataset>")
