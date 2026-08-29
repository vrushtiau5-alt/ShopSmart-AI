import re

def format_currency(value):
    if value is None:
        return "₹0.00"
    return f"₹{float(value):,.2f}"

def slugify(text):
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')
