import json
import logging
from app import db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.utils.helpers import slugify

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('BuiltinSeeder')

SAMPLE_PRODUCTS = [
    # --- KITCHEN & COOKWARE ---
    {
        "sku": "IND-PHIL-2100W",
        "title": "Philips Touch Control Induction Cooktop Stove 2100W",
        "category": "Kitchen & Cookware",
        "brand": "Philips",
        "price": 4999.00,
        "rating": 4.7,
        "reviews_count": 285,
        "stock": 40,
        "description": "High performance induction stove with touch controls, 8 preset cooking menus, fast heating and auto turn-off feature.",
        "features": json.dumps(["2100W Power", "8 Preset Menus", "Touch Controls", "Auto Cut-Off Safety", "Crystal Glass Top"]),
        "specs": json.dumps({"Power": "2100 Watts", "Control": "Touch Sensor", "Warranty": "2 Years", "Weight": "2.5 kg"}),
        "image_url": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "IND-PRES-2000W",
        "title": "Prestige PIC 20 2000W Induction Cooktop Stove",
        "category": "Kitchen & Cookware",
        "brand": "Prestige",
        "price": 3299.00,
        "rating": 4.5,
        "reviews_count": 512,
        "stock": 60,
        "description": "Reliable push-button induction stove with automatic voltage regulator and Indian menu options.",
        "features": json.dumps(["2000W Heating", "Push Button Controls", "Indian Menu Presets", "Anti-Magnetic Wall"]),
        "specs": json.dumps({"Power": "2000 Watts", "Control": "Push Buttons", "Warranty": "1 Year"}),
        "image_url": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },
    {
        "sku": "IND-PIGE-1800W",
        "title": "Pigeon Cruise 1800W Induction Cooktop Stove",
        "category": "Kitchen & Cookware",
        "brand": "Pigeon",
        "price": 2199.00,
        "rating": 4.3,
        "reviews_count": 890,
        "stock": 75,
        "description": "Budget-friendly portable induction stove featuring high-grade micro crystal plate and LED display.",
        "features": json.dumps(["1800W Power", "LED Display", "7 Segment Display", "Dual Heat Sensor"]),
        "specs": json.dumps({"Power": "1800 Watts", "Cord Length": "1.3m", "Warranty": "1 Year"}),
        "image_url": "https://images.unsplash.com/photo-1585659722983-3a675dabf23d?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- LAPTOPS & COMPUTERS ---
    {
        "sku": "LAP-APPL-M3MAX",
        "title": "Apple MacBook Pro 16-inch M3 Max",
        "category": "Laptops & Computers",
        "brand": "Apple",
        "price": 249900.00,
        "rating": 4.9,
        "reviews_count": 340,
        "stock": 25,
        "description": "Blazing fast laptop for developers, content creators, and AI research with Liquid Retina XDR display.",
        "features": json.dumps(["M3 Max 16-core CPU", "36GB Unified Memory", "1TB SSD", "Liquid Retina XDR"]),
        "specs": json.dumps({"RAM": "36GB", "Storage": "1TB SSD", "Battery": "Up to 22 hrs", "OS": "macOS"}),
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "LAP-DELL-XPS15",
        "title": "Dell XPS 15 Intel Core i9 Laptop",
        "category": "Laptops & Computers",
        "brand": "Dell",
        "price": 179990.00,
        "rating": 4.6,
        "reviews_count": 180,
        "stock": 15,
        "description": "Premium 15.6-inch 3.5K OLED touchscreen laptop engineered for programming, heavy multitasking, and design.",
        "features": json.dumps(["Intel Core i9 13th Gen", "32GB DDR5 RAM", "1TB NVMe SSD", "NVIDIA RTX 4060"]),
        "specs": json.dumps({"Processor": "Intel i9-13900H", "GPU": "RTX 4060 8GB", "Screen": "3.5K OLED"}),
        "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "LAP-LENV-E14",
        "title": "Lenovo ThinkPad E14 Gen 5 Programming Laptop",
        "category": "Laptops & Computers",
        "brand": "Lenovo",
        "price": 54990.00,
        "rating": 4.5,
        "reviews_count": 420,
        "stock": 50,
        "description": "Durable and efficient laptop for software engineering under 60000 with backlit keyboard and trackpoint.",
        "features": json.dumps(["AMD Ryzen 7 7730U", "16GB RAM", "512GB SSD", "Full HD IPS Screen"]),
        "specs": json.dumps({"Processor": "AMD Ryzen 7", "RAM": "16GB", "Storage": "512GB SSD", "Weight": "1.41 kg"}),
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- MOBILE PHONES ---
    {
        "sku": "MOB-APPL-15PRO",
        "title": "Apple iPhone 15 Pro Max 256GB",
        "category": "Mobile Phones",
        "brand": "Apple",
        "price": 139900.00,
        "rating": 4.8,
        "reviews_count": 650,
        "stock": 30,
        "description": "Titanium design with A17 Pro chip, customizable Action button, and versatile 48MP main camera.",
        "features": json.dumps(["A17 Pro Chip", "48MP Main Camera", "Titanium Frame", "USB-C Port"]),
        "specs": json.dumps({"Screen": "6.7 inch Super Retina XDR", "Camera": "48MP + 12MP + 12MP", "Storage": "256GB"}),
        "image_url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "MOB-SAMS-S24U",
        "title": "Samsung Galaxy S24 Ultra 5G",
        "category": "Mobile Phones",
        "brand": "Samsung",
        "price": 129999.00,
        "rating": 4.7,
        "reviews_count": 480,
        "stock": 35,
        "description": "Galaxy AI mobile phone with 200MP camera system, built-in S Pen, and Snapdragon 8 Gen 3.",
        "features": json.dumps(["Galaxy AI Built-in", "200MP Camera", "Embedded S Pen", "Snapdragon 8 Gen 3"]),
        "specs": json.dumps({"Display": "6.8 inch QHD+ AMOLED", "RAM": "12GB", "Battery": "5000 mAh"}),
        "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "MOB-GOOG-PX8A",
        "title": "Google Pixel 8a 5G Camera Phone",
        "category": "Mobile Phones",
        "brand": "Google",
        "price": 28999.00,
        "rating": 4.6,
        "reviews_count": 310,
        "stock": 45,
        "description": "Outstanding smartphone camera experience under 30000 powered by Google Tensor G3 and Magic Eraser.",
        "features": json.dumps(["Tensor G3 Chip", "64MP Camera with Night Sight", "Best Take AI Feature", "7 Years Security Updates"]),
        "specs": json.dumps({"Display": "6.1 inch 120Hz OLED", "Storage": "128GB", "RAM": "8GB"}),
        "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- HEADPHONES & AUDIO ---
    {
        "sku": "AUD-SONY-XM5",
        "title": "Sony WH-1000XM5 Noise Canceling Headphones",
        "category": "Headphones & Audio",
        "brand": "Sony",
        "price": 29990.00,
        "rating": 4.8,
        "reviews_count": 920,
        "stock": 50,
        "description": "Industry leading wireless noise canceling over-ear headphones with 30-hour battery life and crystal clear calls.",
        "features": json.dumps(["Auto NC Optimizer", "30 Hours Battery", "Speak-to-Chat", "Multipoint Connection"]),
        "specs": json.dumps({"Driver": "30mm", "Bluetooth": "v5.2", "Weight": "250g"}),
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },
    {
        "sku": "AUD-APPL-APP2",
        "title": "Apple AirPods Pro (2nd Generation) USB-C",
        "category": "Headphones & Audio",
        "brand": "Apple",
        "price": 24900.00,
        "rating": 4.7,
        "reviews_count": 1150,
        "stock": 60,
        "description": "Active Noise Cancellation up to 2x more, Transparency mode, and Personalized Spatial Audio.",
        "features": json.dumps(["H2 Chip", "Active Noise Cancellation", "Adaptive Audio", "MagSafe Charging Case"]),
        "specs": json.dumps({"Battery": "6 hrs per charge", "Water Resistance": "IP54", "Connector": "USB-C"}),
        "image_url": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=600&q=80",
        "is_featured": False
    },

    # --- FOOTWEAR & SHOES ---
    {
        "sku": "SHO-NIKE-PEG40",
        "title": "Nike Air Zoom Pegasus 40 Running Shoes",
        "category": "Footwear & Shoes",
        "brand": "Nike",
        "price": 11495.00,
        "rating": 4.6,
        "reviews_count": 390,
        "stock": 40,
        "description": "Springy running shoes engineered for everyday road runs with dual Zoom Air units and breathable mesh.",
        "features": json.dumps(["Nike React Foam", "Dual Zoom Air Units", "Engineered Mesh Upper", "Waffle Rubber Outsole"]),
        "specs": json.dumps({"Type": "Road Running", "Drop": "10mm", "Weight": "288g"}),
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    },

    # --- HOME APPLIANCES ---
    {
        "sku": "APP-LG-WASH8KG",
        "title": "LG 8.0 Kg Front Load Washing Machine",
        "category": "Home Appliances",
        "brand": "LG",
        "price": 34990.00,
        "rating": 4.7,
        "reviews_count": 510,
        "stock": 20,
        "description": "AI Direct Drive front load washing machine with Steam Wash and 6 Motion technology for family laundry.",
        "features": json.dumps(["AI DD Direct Drive", "Steam Hygiene Wash", "6 Motion Technology", "Inverter Direct Drive Motor"]),
        "specs": json.dumps({"Capacity": "8 Kg", "RPM": "1400 RPM", "Energy Rating": "5 Star"}),
        "image_url": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=600&q=80",
        "is_featured": True
    }
]


def seed_database_builtin():
    """Initializes tables, default Admin & Customer users, and built-in product catalog."""
    logger.info("Ensuring all database tables exist...")
    db.create_all()

    # 1. Create Default Admins if missing
    admin = User.query.filter_by(email='admin@shopsmart.ai').first()
    if not admin:
        admin = User(
            full_name='System Admin',
            username='admin_shopsmart',
            email='admin@shopsmart.ai',
            role='ADMIN',
            is_active=True,
            email_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        logger.info("Created Default Admin: admin@shopsmart.ai (password: admin123)")
    else:
        logger.info("Default Admin (admin@shopsmart.ai) verified.")

    # Primary Admin User
    user_admin = User.query.filter_by(email='uk563644@gmail.com').first()
    if not user_admin:
        user_admin = User(
            full_name='Admin',
            username='admin_uk563644',
            email='uk563644@gmail.com',
            role='ADMIN',
            is_active=True,
            email_verified=True
        )
        user_admin.set_password('admin123')
        db.session.add(user_admin)
        logger.info("Created Primary Admin: uk563644@gmail.com (password: admin123)")
    else:
        user_admin.role = 'ADMIN'
        user_admin.is_active = True
        user_admin.set_password('admin123')
        logger.info("Primary Admin (uk563644@gmail.com) verified.")

    # 2. Create Default Customer if missing
    customer = User.query.filter_by(email='customer@shopsmart.ai').first()
    if not customer:
        customer = User(
            full_name='Jane Customer',
            username='customer_shopsmart',
            email='customer@shopsmart.ai',
            role='USER',
            is_active=True,
            email_verified=True
        )
        customer.set_password('user123')
        db.session.add(customer)
        logger.info("Created Default Customer: customer@shopsmart.ai (password: user123)")
    else:
        customer.set_password('user123')
        logger.info("Default Customer (customer@shopsmart.ai) verified.")

    db.session.commit()

    # 3. Seed catalog if empty or under 5 products
    current_product_count = Product.query.count()
    if current_product_count < 5:
        logger.info("Seeding built-in product catalog...")
        categories_cache = {}

        for item in SAMPLE_PRODUCTS:
            cat_name = item['category']
            if cat_name not in categories_cache:
                cat = Category.query.filter_by(name=cat_name).first()
                if not cat:
                    cat = Category(
                        name=cat_name,
                        slug=slugify(cat_name),
                        description=f"Top selection in {cat_name}"
                    )
                    db.session.add(cat)
                    db.session.flush()
                categories_cache[cat_name] = cat.id

            cat_id = categories_cache[cat_name]

            # Check if SKU exists
            prod = Product.query.filter_by(sku=item['sku']).first()
            if not prod:
                prod = Product(
                    sku=item['sku'],
                    slug=slugify(item['title']),
                    title=item['title'],
                    category_id=cat_id,
                    brand=item['brand'],
                    price=item['price'],
                    rating=item['rating'],
                    reviews_count=item['reviews_count'],
                    stock=item['stock'],
                    description=item['description'],
                    features=item['features'],
                    specs=item['specs'],
                    image_url=item['image_url'],
                    is_featured=item['is_featured'],
                    is_active=True,
                    is_available=True
                )
                db.session.add(prod)

        db.session.commit()
        logger.info(f"Successfully seeded product catalog ({Product.query.count()} products total).")
    else:
        logger.info(f"Product catalog already initialized ({current_product_count} products in database).")

    return True
