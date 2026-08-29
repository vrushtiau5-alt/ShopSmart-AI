#!/usr/bin/env python3
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    cols = [c['name'] for c in inspector.get_columns('orders')]
    print('Current orders columns:', cols)
    with db.engine.connect() as conn:
        if 'payment_status' not in cols:
            conn.execute(text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(30) DEFAULT 'PENDING' NOT NULL;"))
            print("Added payment_status column.")
        if 'payment_gateway' not in cols:
            conn.execute(text("ALTER TABLE orders ADD COLUMN payment_gateway VARCHAR(50) DEFAULT 'Razorpay' NULL;"))
            print("Added payment_gateway column.")
        if 'gateway_order_id' not in cols:
            conn.execute(text("ALTER TABLE orders ADD COLUMN gateway_order_id VARCHAR(100) NULL;"))
            print("Added gateway_order_id column.")
        if 'gateway_payment_id' not in cols:
            conn.execute(text("ALTER TABLE orders ADD COLUMN gateway_payment_id VARCHAR(100) NULL;"))
            print("Added gateway_payment_id column.")
        if 'paid_at' not in cols:
            conn.execute(text("ALTER TABLE orders ADD COLUMN paid_at DATETIME NULL;"))
            print("Added paid_at column.")
        conn.commit()
    print('Updated orders columns successfully!')
