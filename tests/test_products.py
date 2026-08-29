def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'ShopSmart' in response.data

def test_products_catalog(client):
    response = client.get('/products')
    assert response.status_code == 200
    assert b'Philips Induction Stove' in response.data

def test_product_search(client):
    response = client.get('/products?search=induction')
    assert response.status_code == 200
    assert b'Philips Induction Stove' in response.data

def test_product_detail(client, app):
    response = client.get('/product/1')
    assert response.status_code == 200
    assert b'Philips Induction Stove' in response.data
