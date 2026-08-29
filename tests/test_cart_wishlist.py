def login_user(client):
    client.post('/login/user', data={'email': 'user@test.com', 'password': 'user123'})

def test_add_to_cart_user(client):
    login_user(client)
    response = client.post('/cart/add', data={'product_id': 1, 'quantity': 2}, follow_redirects=True)
    assert response.status_code == 200
    
    cart_resp = client.get('/cart')
    assert cart_resp.status_code == 200
    assert b'Cart' in cart_resp.data

def test_compare_products(client):
    login_user(client)
    client.get('/compare/add/1')
    response = client.get('/compare')
    assert response.status_code == 200

def test_smart_cart_analysis(client):
    login_user(client)
    client.post('/cart/add', data={'product_id': 1, 'quantity': 1})
    response = client.get('/cart/smart-analysis')
    assert response.status_code == 200
    assert b'Smart Cart AI Analysis' in response.data
