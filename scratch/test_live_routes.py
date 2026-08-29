import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

def test_live_routes_and_ai():
    app = create_app()
    client = app.test_client()

    print("========================================================")
    print(" TESTING LIVE ROUTES AGAINST MYSQL DATABASE")
    print("========================================================")

    with app.app_context():
        from app.models.product import Product
        first_prod = Product.query.first()
        prod_id = first_prod.id if first_prod else 1

    routes = [
        '/',
        '/products',
        f'/product/{prod_id}',
        '/register',
        '/register/user',
        '/register/admin',
        '/login',
        '/login/user',
        '/login/admin',
        '/forgot-password',
        '/verify-reset-otp',
        '/wishlist',
        '/cart',
        '/compare',
        '/planner',
        '/ai',
        '/about',
        '/contact',
        '/admin/dashboard',
        '/admin/products',
        '/admin/categories',
        '/admin/users',
        '/admin/orders',
        '/admin/contacts',
        '/admin/analytics',
        '/admin/reports'
    ]

    with client:
        # Log in as admin via /login/admin
        client.post('/login/admin', data={'email': 'admin@shopsmart.ai', 'password': 'admin123'}, follow_redirects=True)

        for route in routes:
            res = client.get(route)
            status = res.status_code
            print(f" -> GET {route:<24} Status: {status}")
            assert status in [200, 302], f"Route {route} returned unexpected status {status}"

    print("\n========================================================")
    print(" TESTING AI ASSISTANT RELEVANCE & FOLLOW-UP QUERIES")
    print("========================================================")

    ai_prompts = [
        "Show me induction stoves",
        "I need a laptop for programming under 60000",
        "Show me headphones",
        "I need a washing machine",
        "Which one is cheaper?",
        "Show me another option"
    ]

    with client:
        for prompt in ai_prompts:
            res = client.post('/api/ai/chat', json={'message': prompt})
            data = res.get_json()
            products = data.get('products', [])
            prod_titles = [p['title'] for p in products]
            print(f"\nPrompt: '{prompt}'")
            print(f" -> Response Header: {data.get('message')}")
            print(f" -> Products Returned ({len(products)}): {prod_titles}")

            # Specific relevance assertions
            if "induction stoves" in prompt.lower():
                assert any("Induction" in t or "Cooktop" in t or "Stove" in t for t in prod_titles), "Failed: Induction stove query did not return induction stoves!"
                assert not any("AirPods" in t or "MacBook" in t for t in prod_titles), "Failed: Induction stove query returned unrelated AirPods/Laptops!"
            elif "headphones" in prompt.lower():
                assert any("Headphones" in t or "AirPods" in t for t in prod_titles), "Failed: Headphones query did not return audio devices!"

    print("\n========================================================")
    print(" ALL ROUTE & AI RELEVANCE CHECKS PASSED PERFECTLY!")
    print("========================================================")

if __name__ == '__main__':
    test_live_routes_and_ai()
