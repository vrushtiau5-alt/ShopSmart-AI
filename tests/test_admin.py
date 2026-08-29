def test_non_admin_forbidden(client):
    """Normal customer trying to access admin page gets 403 Forbidden."""
    client.post('/login/user', data={'email': 'user@test.com', 'password': 'user123'})
    response = client.get('/admin/dashboard')
    assert response.status_code == 403
    assert b'403' in response.data or b'Access Forbidden' in response.data

def test_admin_dashboard_success(client):
    client.post('/login/admin', data={'email': 'admin@test.com', 'password': 'admin123'})
    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Executive Dashboard Overview' in response.data

def test_admin_add_product(client, app):
    client.post('/login/admin', data={'email': 'admin@test.com', 'password': 'admin123'})
    response = client.post('/admin/product/add', data={
        'title': 'New Microwave Oven',
        'category_id': 1,
        'brand': 'LG',
        'price': 8999.00,
        'stock': 10,
        'description': 'Smart microwave oven'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'New Microwave Oven' in response.data
