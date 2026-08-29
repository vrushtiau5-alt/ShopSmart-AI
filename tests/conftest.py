import pytest
from app import create_app, db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        
        # Seed test categories & products
        cat1 = Category(name='Kitchen Appliances', slug='kitchen-appliances', description='Cookware and appliances')
        cat2 = Category(name='Headphones & Audio', slug='headphones-audio', description='Audio devices')
        db.session.add_all([cat1, cat2])
        db.session.flush()

        prod1 = Product(
            sku='TEST-IND-01',
            slug='philips-induction-stove-cooktop-2100w',
            name='Philips Induction Stove Cooktop 2100W',
            description='Touch control induction stove',
            category_id=cat1.id,
            brand='Philips',
            price=4999.00,
            rating=4.7,
            reviews_count=100,
            stock_quantity=20,
            is_featured=True,
            is_available=True,
            is_active=True
        )
        prod2 = Product(
            sku='TEST-AUD-01',
            slug='sony-wireless-headphones',
            name='Sony Wireless Headphones',
            description='Noise canceling audio headphones',
            category_id=cat2.id,
            brand='Sony',
            price=15000.00,
            rating=4.8,
            reviews_count=200,
            stock_quantity=15,
            is_available=True,
            is_active=True
        )
        db.session.add_all([prod1, prod2])

        # Seed test user & admin using full_name
        user = User(full_name='Test Customer', email='user@test.com', role='USER', is_active=True)
        user.set_password('user123')

        admin = User(full_name='Test Admin', email='admin@test.com', role='ADMIN', is_active=True)
        admin.set_password('admin123')

        db.session.add_all([user, admin])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
