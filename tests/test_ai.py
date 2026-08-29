import pytest
from app.services.ai_service import match_products_by_intent, process_ai_chat

def test_ai_relevance_induction_stove(app):
    """
    CRITICAL RELEVANCE TEST:
    Requesting 'induction stoves' MUST return induction stove products, NOT headphones or laptops!
    """
    with app.app_context():
        products, header, matched_cats = match_products_by_intent("Show me induction stoves")
        assert len(products) > 0
        assert any("Induction" in p.title for p in products)
        assert not any("Headphones" in p.title for p in products)

def test_ai_followup_cheapest(app):
    with app.app_context():
        # First query context
        context = [{'product_ids': [1, 2], 'matched_categories': ['Kitchen Appliances']}]
        products, header, cats = match_products_by_intent("Which one is cheaper?", context_history=context)
        assert len(products) > 0
        # Product 1 ($4999) is cheaper than Product 2 ($15000)
        assert products[0].id == 1

def test_ai_chat_api_endpoint(client):
    response = client.post('/api/ai/chat', json={'message': 'Show me induction stoves'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['products']) > 0

def test_ai_headphones_no_phones(app):
    """
    Requesting 'headphones for music' MUST return headphones with correct photos,
    and MUST NOT include mobile phones (e.g. iPhone) due to substring matching on 'phone'!
    """
    with app.app_context():
        products, header, matched_cats = match_products_by_intent("Show me headphones for music")
        assert len(products) > 0
        assert not any("iPhone" in p.name or "Galaxy" in p.name for p in products)
        assert any("Headphones" in p.name or "AirPods" in p.name or "headphone" in p.name.lower() for p in products)

