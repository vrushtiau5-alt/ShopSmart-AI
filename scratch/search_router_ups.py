import pandas as pd

df = pd.read_csv('dataset/amazon_products_full/amazon-products.csv')

match = df[df['name'].astype(str).str.contains('Router UPS|12D4|Envibe', na=False, case=False)]
print(f"Found {len(match)} rows in CSV:")
for idx, row in match.iterrows():
    print("----------------------------------------")
    print(f"Index: {idx}")
    print(f"Name: {row['name']}")
    print(f"Image: {row['image']}")
    print(f"Link: {row['link']}")
