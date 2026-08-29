import hmac
import hashlib
import pytest
from app.models.product import Product
from app.models.cart import CartItem
from app.models.order import Order, OrderItem

def test_payment_create_order_server_side_calculation(client, app):
    """Verifies that payment amount is calculated strictly on the server and converted to paise."""
    # 1. Login user
    client.post('/login/user', data={'email': 'user@test.com', 'password': 'user123'})

    # 2. Add product to cart
    with app.app_context():
        product = Product.query.first()
        prod_id = product.id
        prod_price = product.price

    client.post('/cart/add', data={'product_id': prod_id, 'quantity': 2})

    # 3. Create payment order
    response = client.post('/payment/create-order', json={
        'address': '742 Evergreen Terrace',
        'city': 'Springfield',
        'zip_code': '97477',
        'payment_method': 'Google Pay'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'razorpay_order_id' in data
    assert 'amount' in data

    # Verify server-side total: subtotal = 2 * prod_price, tax = subtotal * 0.08, shipping = 15.0 if subtotal < 100 else 0
    subtotal = prod_price * 2
    tax = subtotal * 0.08
    shipping = 15.0 if subtotal < 100 else 0.0
    expected_total = round(subtotal + tax + shipping, 2)
    expected_paise = int(round(expected_total * 100))

    assert data['amount'] == expected_paise

    # Verify Order created in DB
    with app.app_context():
        order = Order.query.get(data['order_id'])
        assert order is not None
        assert order.payment_status == 'PENDING'
        assert order.total_amount == expected_total


def test_payment_verify_valid_signature(client, app):
    """Verifies HMAC signature check, marks order PAID, and clears user cart upon success."""
    client.post('/login/user', data={'email': 'user@test.com', 'password': 'user123'})

    with app.app_context():
        product = Product.query.first()
        prod_id = product.id

    client.post('/cart/add', data={'product_id': prod_id, 'quantity': 1})

    # Initiate payment order
    res_create = client.post('/payment/create-order', json={
        'address': '123 Tech Road',
        'city': 'Bangalore',
        'zip_code': '560001',
        'payment_method': 'Google Pay'
    })
    order_data = res_create.get_json()
    order_id = order_data['order_id']
    rzp_order_id = order_data['razorpay_order_id']

    # Generate valid test signature
    secret = app.config.get('RAZORPAY_KEY_SECRET', 'rzp_test_shopsmart_secret_key')
    payment_id = 'pay_test_99887766'
    valid_sig = hmac.new(
        secret.encode('utf-8'),
        f"{rzp_order_id}|{payment_id}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Verify payment
    res_verify = client.post('/payment/verify', json={
        'order_id': order_id,
        'razorpay_order_id': rzp_order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': valid_sig
    })

    assert res_verify.status_code == 200
    verify_data = res_verify.get_json()
    assert verify_data['success'] is True

    # Verify order state in DB & cart clearance
    with app.app_context():
        order = Order.query.get(order_id)
        assert order.payment_status == 'PAID'
        assert order.status == 'Processing'
        assert order.gateway_payment_id == payment_id
        assert order.paid_at is not None

        # Cart must be cleared
        cart_count = CartItem.query.filter_by(user_id=order.user_id).count()
        assert cart_count == 0


def test_payment_verify_invalid_signature_fails(client, app):
    """Verifies that invalid signature marks order FAILED and keeps user cart intact."""
    client.post('/login/user', data={'email': 'user@test.com', 'password': 'user123'})

    with app.app_context():
        product = Product.query.first()
        prod_id = product.id

    client.post('/cart/add', data={'product_id': prod_id, 'quantity': 1})

    res_create = client.post('/payment/create-order', json={
        'address': '456 Security Street',
        'city': 'Mumbai',
        'zip_code': '400001',
        'payment_method': 'Google Pay'
    })
    order_data = res_create.get_json()
    order_id = order_data['order_id']
    rzp_order_id = order_data['razorpay_order_id']

    # Send forged signature
    res_verify = client.post('/payment/verify', json={
        'order_id': order_id,
        'razorpay_order_id': rzp_order_id,
        'razorpay_payment_id': 'pay_fake_123',
        'razorpay_signature': 'invalid_forged_signature_hash'
    })

    assert res_verify.status_code == 400
    verify_data = res_verify.get_json()
    assert verify_data['success'] is False

    # Verify order status is FAILED and cart is NOT cleared
    with app.app_context():
        order = Order.query.get(order_id)
        assert order.payment_status == 'FAILED'

        cart_count = CartItem.query.filter_by(user_id=order.user_id).count()
        assert cart_count > 0
