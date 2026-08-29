import pytest
from app.models.user import User
from app.utils.tokens import generate_reset_token, verify_reset_token

def test_register_selection_page_renders(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Choose your account type' in response.data

def test_customer_registration_success(client, app):
    response = client.post('/register/user', data={
        'first_name': 'New',
        'last_name': 'Customer',
        'username': 'newcust',
        'email': 'newcust@test.com',
        'phone': '1234567890',
        'password': 'password123',
        'confirm_password': 'password123',
        'terms': '1'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful. Please login to continue.' in response.data

    with app.app_context():
        user = User.query.filter_by(email='newcust@test.com').first()
        assert user is not None
        assert user.role == 'USER'

def test_admin_registration_with_invalid_code_fails(client, app):
    response = client.post('/register/admin', data={
        'admin_name': 'Fake Admin',
        'username': 'fakeadmin',
        'email': 'fakeadmin@test.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'admin_code': 'wrong_code'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid Administrator Authorization Code' in response.data

    with app.app_context():
        user = User.query.filter_by(email='fakeadmin@test.com').first()
        assert user is None

def test_admin_registration_with_valid_code_success(client, app):
    response = client.post('/register/admin', data={
        'admin_name': 'Valid Admin',
        'username': 'validadmin',
        'email': 'validadmin@test.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'admin_code': 'change_this_secure_code'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Admin registration successful. Please login to continue.' in response.data

    with app.app_context():
        user = User.query.filter_by(email='validadmin@test.com').first()
        assert user is not None
        assert user.role == 'ADMIN'

def test_login_selection_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Account Login' in response.data

def test_customer_login_success(client):
    response = client.post('/login/user', data={
        'email': 'user@test.com',
        'password': 'user123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back' in response.data

def test_user_cannot_login_at_admin_portal(client):
    """SECURITY TEST: Normal user attempting Admin login is rejected."""
    response = client.post('/login/admin', data={
        'email': 'user@test.com',
        'password': 'user123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Access Denied: You do not have administrator permissions' in response.data

def test_admin_login_success(client):
    response = client.post('/login/admin', data={
        'email': 'admin@test.com',
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Administrator login successful' in response.data

def test_forgot_password_and_token(client, app):
    with app.app_context():
        user = User.query.filter_by(email='user@test.com').first()
        token = generate_reset_token(user)
        verified = verify_reset_token(token)
        assert verified.id == user.id

    response = client.get(f'/reset-password/{token}')
    assert response.status_code == 200
