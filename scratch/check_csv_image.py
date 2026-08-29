import pandas as pd

df = pd.read_csv('dataset/amazon_products_full/amazon-products.csv')

vguard_row = df[df['title'].str.contains('V-Guard Envibe 12D4', na=False, case=False)]

print("Found rows in amazon-products.csv:")
for idx, row in vguard_row.iterrows():
    print("----------------------------------------")
    print(f"Title: {row.get('title')}")
    print(f"Image URL: {row.get('imgUrl')}")
    print(f"Product Link: {row.get('productURL') or row.get('link')}")
