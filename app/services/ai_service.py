import re
import json
from flask import session, current_app
from app.models.product import Product
from app.models.category import Category
from app import db

# Category Synonyms and Entity Mappings
CATEGORY_MAP = {
    'induction': ['Kitchen & Cookware', 'Kitchen Appliances', 'Appliances'],
    'stove': ['Kitchen & Cookware', 'Kitchen Appliances', 'Appliances'],
    'cooktop': ['Kitchen & Cookware', 'Kitchen Appliances', 'Appliances'],
    'laptop': ['Laptops & Computers', 'Computers'],
    'macbook': ['Laptops & Computers', 'Computers'],
    'computer': ['Laptops & Computers', 'Computers'],
    'phone': ['Mobile Phones', 'Mobiles'],
    'mobile': ['Mobile Phones', 'Mobiles'],
    'smartphone': ['Mobile Phones', 'Mobiles'],
    'headphone': ['Headphones & Audio', 'Audio'],
    'earphone': ['Headphones & Audio', 'Audio'],
    'airpods': ['Headphones & Audio', 'Audio'],
    'headset': ['Headphones & Audio', 'Audio'],
    'shoe': ['Footwear & Shoes', 'Shoes'],
    'sneaker': ['Footwear & Shoes', 'Shoes'],
    'running': ['Footwear & Shoes', 'Shoes'],
    'boot': ['Footwear & Shoes', 'Shoes'],
    'watch': ['Watches & Wearables', 'Accessories'],
    'washing machine': ['Home Appliances', 'Appliances'],
    'refrigerator': ['Home Appliances', 'Appliances'],
    'fridge': ['Home Appliances', 'Appliances'],
    'tv': ['Television & Video'],
    'television': ['Television & Video']
}

def extract_price_constraint(user_text):
    text = user_text.lower()
    patterns = [
        r'(?:under|below|less than|within|max|budget)\s*(?:rs\.?|\$|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:budget|or less|max)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                clean_num = match.group(1).replace(',', '')
                return float(clean_num)
            except ValueError:
                pass
    return None

def extract_target_keywords(user_text):
    stopwords = {'i', 'need', 'a', 'an', 'the', 'for', 'under', 'below', 'show', 'me', 'want', 'buy', 'looking', 'good', 'best', 'cheap', 'with'}
    tokens = re.findall(r'\b[a-zA-Z0-9]+\b', user_text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]

def match_products_by_intent(user_text, context_history=None):
    """
    Intelligent product retrieval based on entity matching, category mapping,
    price filtering, and relevance scoring.
    """
    text = user_text.lower().strip()
    max_price = extract_price_constraint(text)
    keywords = extract_target_keywords(text)

    # 1. Handle Follow-up Context queries
    if context_history and len(context_history) > 0:
        last_item = context_history[-1]
        previous_product_ids = last_item.get('product_ids', [])
        matched_cats = last_item.get('matched_categories', [])

        if any(w in text for w in ['cheaper', 'cheapest', 'lowest price', 'low price']):
            if previous_product_ids:
                products = Product.query.filter(
                    Product.id.in_(previous_product_ids),
                    Product.is_active == True
                ).order_by(Product.price.asc()).all()
                return products, "Here are the previous options sorted by price (cheapest first):", matched_cats

        if any(w in text for w in ['highest rated', 'best rated', 'top rated']):
            if previous_product_ids:
                products = Product.query.filter(
                    Product.id.in_(previous_product_ids),
                    Product.is_active == True
                ).order_by(Product.rating.desc()).all()
                return products, "Here are the previous options sorted by highest rating:", matched_cats

        if any(w in text for w in ['another', 'more', 'other', 'else']):
            query = Product.query.filter(Product.is_active == True)
            if previous_product_ids:
                query = query.filter(~Product.id.in_(previous_product_ids))
            if matched_cats:
                categories = Category.query.filter(Category.name.in_(matched_cats)).all()
                cat_ids = [c.id for c in categories]
                if cat_ids:
                    query = query.filter(Product.category_id.in_(cat_ids))
            if max_price:
                query = query.filter(Product.price <= max_price)
            products = query.order_by(Product.rating.desc()).limit(4).all()
            if products:
                return products, "Here are additional relevant options matching your criteria:", matched_cats

    # 2. Category & Intent Identification
    target_category_names = set()
    entity_tokens = set()
    for word, cats in CATEGORY_MAP.items():
        if re.search(r'\b' + re.escape(word) + r's?\b', text, re.IGNORECASE):
            target_category_names.update(cats)
            entity_tokens.add(word)

    # If no explicit CATEGORY_MAP entities matched, check dynamic DB categories
    if not entity_tokens:
        for kw in keywords:
            found_db_cats = Category.query.filter(Category.name.ilike(f"%{kw}%")).all()
            for cat_obj in found_db_cats:
                target_category_names.add(cat_obj.name)
                entity_tokens.add(kw)

    matched_categories = list(target_category_names)
    matched_category_ids = []
    if target_category_names:
        found_cats = Category.query.filter(
            db.or_(*[Category.name.ilike(f"%{cat}%") for cat in target_category_names])
        ).all()
        matched_category_ids = [c.id for c in found_cats]

    # 3. DB Query Construction
    query = Product.query.filter(Product.is_active == True)

    if matched_category_ids:
        unique_cat_ids = list(set(matched_category_ids))
        query = query.filter(Product.category_id.in_(unique_cat_ids))

    if max_price:
        query = query.filter(Product.price <= max_price)

    candidate_products = query.all()

    # Fallback if category yielded 0 products or candidates are empty
    if not candidate_products and keywords:
        fallback_query = Product.query.filter(Product.is_active == True)
        if max_price:
            fallback_query = fallback_query.filter(Product.price <= max_price)
        
        or_filters = []
        for kw in keywords:
            or_filters.append(Product.name.ilike(f"%{kw}%"))
            or_filters.append(Product.description.ilike(f"%{kw}%"))
            or_filters.append(Product.brand.ilike(f"%{kw}%"))
        
        if or_filters:
            fallback_query = fallback_query.filter(db.or_(*or_filters))
        candidate_products = fallback_query.all()

    # 4. Strict Keyword & Entity Relevance Scoring
    scored_products = []
    for p in candidate_products:
        score = 0
        p_name_lower = (p.name or '').lower()
        p_cat_name = (p.category.name or '') if p.category else ''
        p_cat_lower = p_cat_name.lower()
        p_brand_lower = (p.brand or '').lower()
        p_desc_lower = (p.description or '').lower()
        p_text = f"{p_name_lower} {p_desc_lower} {p_brand_lower} {p_cat_lower}"
        
        # Entity matching: enforce strict match when entity_tokens are identified
        if entity_tokens:
            matches_entity = any(e in p_text for e in entity_tokens)
            if not matches_entity:
                continue  # Exclude unrelated products!
            
            if any(e in p_name_lower for e in entity_tokens):
                score += 30
            elif any(e in p_cat_lower for e in entity_tokens):
                score += 20
            else:
                score += 10

        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r's?\b', p_name_lower):
                score += 15
            elif kw in p_name_lower:
                score += 10
            elif kw in p_text:
                score += 3
        
        if p.category and any(cat.lower() in p_cat_lower for cat in target_category_names):
            score += 10

        if p.image_url and 'placeholder' not in p.image_url:
            score += 5
            
        scored_products.append((score, p))

    scored_products.sort(key=lambda x: x[0], reverse=True)
    top_products = [p for score, p in scored_products[:4]]

    # Clean display header for categories
    if target_category_names:
        display_cats = [c for c in list(target_category_names) if c.lower() not in ['mobiles', 'audio', 'appliances']]
        if not display_cats:
            display_cats = list(target_category_names)
        cat_str = ", ".join(display_cats[:2])
        header = f"Here are the top matches for {cat_str}:"
    elif keywords:
        header = f"Here are the top options matching '{' '.join(keywords)}':"
    else:
        header = "Here are recommended products matching your request:"

    return top_products, header, matched_categories

def process_ai_chat(user_text, context_history=None):
    """
    Main entry point for AI chatbot.
    """
    api_key = current_app.config.get('AI_API_KEY')
    provider = current_app.config.get('AI_PROVIDER', 'gemini')

    # Local intent & product retrieval
    products, message, matched_cats = match_products_by_intent(user_text, context_history)

    # Product Cards Formatting
    product_cards = []
    for p in products:
        reason = f"Rated {p.rating}/5 by {p.reviews_count} buyers. Great fit for your request."
        if p.price:
            reason = f"Excellent value at ₹{p.price:.2f}. " + reason
        product_cards.append({
            'id': p.id,
            'title': p.name,
            'brand': p.brand,
            'price': p.price,
            'rating': p.rating,
            'reviews_count': p.reviews_count,
            'image_url': p.image_url,
            'category_name': p.category.name if p.category else '',
            'reason': reason
        })

    # External AI API enhancement if API key present
    if api_key and len(api_key) > 5:
        try:
            if provider == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"User asked: '{user_text}'. We retrieved products: {[p.name for p in products]}. Provide a 2-sentence friendly summary introducing these products."
                response = model.generate_content(prompt)
                if response and response.text:
                    message = response.text.strip()
        except Exception:
            pass

    return {
        'message': message,
        'products': product_cards,
        'matched_categories': matched_cats,
        'product_ids': [p.id for p in products]
    }
