import datetime
import json
import uuid
from sqlalchemy.ext.hybrid import hybrid_property
from app import db
from app.utils.helpers import slugify

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    price = db.Column(db.Float, nullable=False, index=True)
    rating = db.Column(db.Float, default=4.5)
    reviews_count = db.Column(db.Integer, default=12)
    description = db.Column(db.Text, nullable=True)
    specifications = db.Column(db.JSON, nullable=True)
    features = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    stock_quantity = db.Column(db.Integer, default=50, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Price History & Real-World Calibration Audit Fields
    original_price = db.Column(db.Float, nullable=True)
    verified_market_price = db.Column(db.Float, nullable=True)
    price_source = db.Column(db.String(100), nullable=True)
    price_verified_at = db.Column(db.DateTime, nullable=True)
    price_confidence = db.Column(db.String(20), nullable=True)

    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    def __init__(self, **kwargs):
        # Auto-fill title if passed
        if 'title' in kwargs and 'name' not in kwargs:
            kwargs['name'] = kwargs.pop('title')
        
        prod_name = kwargs.get('name', 'Product')
        if 'slug' not in kwargs or not kwargs['slug']:
            kwargs['slug'] = f"{slugify(prod_name)}-{uuid.uuid4().hex[:6]}"
        if 'sku' not in kwargs or not kwargs['sku']:
            kwargs['sku'] = f"SKU-{slugify(prod_name)[:20].upper()}-{uuid.uuid4().hex[:6].upper()}"
            
        super().__init__(**kwargs)

    @hybrid_property
    def title(self):
        return self.name

    @title.setter
    def title(self, value):
        self.name = value
        if value and not self.slug:
            self.slug = slugify(value)

    @hybrid_property
    def stock(self):
        return self.stock_quantity

    @stock.setter
    def stock(self, value):
        self.stock_quantity = value

    @property
    def specs(self):
        if not self.specifications:
            return ""
        if isinstance(self.specifications, str):
            return self.specifications
        try:
            return json.dumps(self.specifications)
        except Exception:
            return str(self.specifications)

    @specs.setter
    def specs(self, value):
        if not value:
            self.specifications = {}
            return
        if isinstance(value, dict):
            self.specifications = value
            return
        try:
            self.specifications = json.loads(value)
        except Exception:
            res = {}
            for line in str(value).split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    res[k.strip()] = v.strip()
            self.specifications = res

    def get_features_list(self):
        if not self.features:
            return []
        try:
            return json.loads(self.features)
        except Exception:
            return [f.strip() for f in self.features.split('\n') if f.strip()]

    def get_specs_dict(self):
        if not self.specifications:
            return {}
        if isinstance(self.specifications, dict):
            return self.specifications
        try:
            return json.loads(self.specifications)
        except Exception:
            return {}

    def to_dict(self):
        img = self.image_url
        if not img or not isinstance(img, str) or not (img.startswith('http://') or img.startswith('https://') or img.startswith('/static/')):
            img = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80'

        return {
            'id': self.id,
            'sku': self.sku,
            'slug': self.slug,
            'title': self.title,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'brand': self.brand or 'Generic',
            'price': self.price,
            'original_price': self.original_price if self.original_price is not None else self.price,
            'verified_market_price': self.verified_market_price if self.verified_market_price is not None else self.price,
            'price_source': self.price_source or 'Imported Dataset',
            'price_verified_at': self.price_verified_at.isoformat() if self.price_verified_at else None,
            'price_confidence': self.price_confidence or 'UNVERIFIED',
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'stock': self.stock_quantity,
            'stock_quantity': self.stock_quantity,
            'features': self.get_features_list(),
            'specs': self.get_specs_dict(),
            'image_url': img,
            'is_available': self.is_available,
            'is_active': self.is_active,
            'is_featured': self.is_featured
        }

    @classmethod
    def ensure_price_history_columns(cls):
        """Ensures price history tracking columns exist in MySQL database without altering existing data."""
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('products')]
            
            queries = []
            if 'original_price' not in columns:
                queries.append("ALTER TABLE products ADD COLUMN original_price DOUBLE NULL")
            if 'verified_market_price' not in columns:
                queries.append("ALTER TABLE products ADD COLUMN verified_market_price DOUBLE NULL")
            if 'price_source' not in columns:
                queries.append("ALTER TABLE products ADD COLUMN price_source VARCHAR(100) NULL")
            if 'price_verified_at' not in columns:
                queries.append("ALTER TABLE products ADD COLUMN price_verified_at DATETIME NULL")
            if 'price_confidence' not in columns:
                queries.append("ALTER TABLE products ADD COLUMN price_confidence VARCHAR(20) NULL")
            
            for q in queries:
                db.session.execute(text(q))
            if queries:
                db.session.commit()
        except Exception:
            db.session.rollback()

    def __repr__(self):
        return f'<Product {self.name} (₹{self.price})>'
