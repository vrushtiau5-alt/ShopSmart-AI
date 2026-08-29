import pandas as pd

df = pd.read_csv('dataset/amazon_products_full/amazon-products.csv', nrows=5)
print("Columns in amazon-products.csv:")
print(list(df.columns))

# Search for V-Guard in title or any string column
df_full = pd.read_csv('dataset/amazon_products_full/amazon-products.csv', usecols=['title', 'imgUrl', 'productURL'] if 'title' in df.columns else None)
title_col = [c for c in df_full.columns if 'title' in c.lower() or 'name' in c.lower()][0]
img_col = [c for c in df_full.columns if 'img' in c.lower() or 'image' in c.lower()][0]

vguard_row = df_full[df_full[title_col].astype(str).str.contains('V-Guard', na=False, case=False)]
print(f"Found {len(vguard_row)} rows matching V-Guard:")
for idx, row in vguard_row.head(5).iterrows():
    print("----------------------------------------")
    print(f"Title: {row[title_col]}")
    print(f"ImgURL: {row[img_col]}")
