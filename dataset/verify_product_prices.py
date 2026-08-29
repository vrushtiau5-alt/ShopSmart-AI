#!/usr/bin/env python3
"""
ShopSmart AI - Real Product Market Price Calibration Tool
Queries legitimate public product pricing sources and benchmark APIs to calibrate product prices
against real-world selling prices for exact product models and variants.
Strictly additive & safe: unverified items retain their existing prices without modification.
"""

import sys
import os
import time
import logging
import argparse
import datetime
from typing import Dict, Any, List

# Adjust import path to include project root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.product import Product
from app.services.price_verifier import verify_product_price

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('PriceCalibrator')


def run_sample_verification(sample_count: int = 20, enable_remote_api: bool = False):
    """
    Runs price verification on a sample set of products across Electronics, Mobiles, Laptops,
    Appliances, Headphones, and Food/Groceries, displaying exact verification details.
    """
    app = create_app()
    with app.app_context():
        # Ensure database schema has price history fields
        Product.ensure_price_history_columns()

        print("\n" + "=" * 70, flush=True)
        print("ShopSmart AI - Sample Product Market Price Verification Test", flush=True)
        print("=" * 70, flush=True)

        products = Product.query.limit(sample_count).all()
        high_count = 0
        med_count = 0
        unverified_count = 0
        updated_count = 0

        for idx, p in enumerate(products, start=1):
            p_info = {
                'name': p.name,
                'brand': p.brand,
                'price': p.price,
                'sku': p.sku
            }
            res = verify_product_price(p_info, enable_remote_api=enable_remote_api)
            
            if res['confidence'] == 'HIGH':
                high_count += 1
            elif res['confidence'] == 'MEDIUM':
                med_count += 1
            else:
                unverified_count += 1

            if res['action'] == 'UPDATED':
                updated_count += 1

            orig_p = p.original_price if p.original_price is not None else p.price

            print(f"\n[{idx}/{sample_count}] Product             : {p.name}", flush=True)
            print(f"      Brand               : {p.brand}", flush=True)
            print(f"      Model / Variant     : {res['model']}", flush=True)
            print(f"      Existing Dataset Price: INR {orig_p:,.2f}", flush=True)
            print(f"      Verified Market Price: INR {res['verified_price']:,.2f}", flush=True)
            print(f"      Price Source        : {res['source']}", flush=True)
            print(f"      Match Confidence    : {res['confidence']}", flush=True)
            print(f"      Action Status       : {res['action']}", flush=True)

        print("\n" + "=" * 70, flush=True)
        print("Verification Summary", flush=True)
        print("=" * 70, flush=True)
        print(f"Sample Products Tested : {len(products)}", flush=True)
        print(f"High Confidence Matches: {high_count}", flush=True)
        print(f"Med Confidence Matches : {med_count}", flush=True)
        print(f"Unverified (Retained)  : {unverified_count}", flush=True)
        print(f"Prices Updated         : {updated_count}", flush=True)
        print("=" * 70 + "\n", flush=True)


def calibrate_prices(limit: int = None, batch_size: int = 500, dry_run: bool = False, enable_remote_api: bool = False):
    """
    Performs price calibration across the MySQL product database.
    """
    app = create_app()
    with app.app_context():
        # Ensure database schema has price history fields
        Product.ensure_price_history_columns()

        print("\n" + "=" * 60, flush=True)
        print("ShopSmart AI - Market Price Calibration Engine", flush=True)
        print("=" * 60, flush=True)
        print(f"Target Limit : {limit if limit else 'ALL CATALOGUE'}", flush=True)
        print(f"Batch Size   : {batch_size}", flush=True)
        print(f"Dry Run Mode : {dry_run}", flush=True)
        print("=" * 60, flush=True)

        query = Product.query
        if limit:
            query = query.limit(limit)

        products = query.all()
        total_products = len(products)

        stats = {
            'total': total_products,
            'high_confidence': 0,
            'med_confidence': 0,
            'low_confidence': 0,
            'prices_updated': 0,
            'prices_retained': 0
        }

        updated_batch = []
        for idx, p in enumerate(products, start=1):
            p_info = {
                'name': p.name,
                'brand': p.brand,
                'price': p.price,
                'sku': p.sku
            }
            res = verify_product_price(p_info, enable_remote_api=enable_remote_api)

            if res['confidence'] == 'HIGH':
                stats['high_confidence'] += 1
            elif res['confidence'] == 'MEDIUM':
                stats['med_confidence'] += 1
            else:
                stats['low_confidence'] += 1

            if not dry_run:
                if p.original_price is None:
                    p.original_price = p.price

                p.verified_market_price = res['verified_price']
                p.price_source = res['source']
                p.price_verified_at = datetime.datetime.utcnow()
                p.price_confidence = res['confidence']

            if res['is_verified'] and abs(res['verified_price'] - p.price) > 0.01:
                stats['prices_updated'] += 1
                if not dry_run:
                    p.price = res['verified_price']
                    updated_batch.append(p)
            else:
                stats['prices_retained'] += 1

            if not dry_run and len(updated_batch) >= batch_size:
                db.session.commit()
                logger.info(f"Committed DB price updates batch ({idx}/{total_products})...")
                updated_batch.clear()

        if not dry_run and updated_batch:
            db.session.commit()
            logger.info("Committed final price updates batch.")
            updated_batch.clear()

        print("\n" + "=" * 60, flush=True)
        print("Market Price Calibration Summary", flush=True)
        print("=" * 60, flush=True)
        print(f"Products Processed    : {stats['total']:,}", flush=True)
        print(f"High Confidence       : {stats['high_confidence']:,}", flush=True)
        print(f"Medium Confidence     : {stats['med_confidence']:,}", flush=True)
        print(f"Low Confidence (Kept) : {stats['low_confidence']:,}", flush=True)
        print(f"Prices Calibrated     : {stats['prices_updated']:,}", flush=True)
        print(f"Prices Retained Unchg : {stats['prices_retained']:,}", flush=True)
        print("=" * 60, flush=True)
        print("Price calibration process completed successfully.", flush=True)
        print("=" * 60 + "\n", flush=True)

        return stats


def main():
    parser = argparse.ArgumentParser(description="ShopSmart AI Market Price Calibration Tool")
    parser.add_argument('--sample', type=int, default=None, help="Run verification test output on N sample products")
    parser.add_argument('--limit', type=int, default=None, help="Limit number of products to process")
    parser.add_argument('--batch-size', type=int, default=500, help="Batch commit size (default: 500)")
    parser.add_argument('--dry-run', action='store_true', help="Run verification without modifying database")
    parser.add_argument('--enable-remote-api', action='store_true', help="Enable remote REST API lookup")

    args = parser.parse_args()

    if args.sample:
        run_sample_verification(args.sample, enable_remote_api=args.enable_remote_api)
    else:
        calibrate_prices(limit=args.limit, batch_size=args.batch_size, dry_run=args.dry_run, enable_remote_api=args.enable_remote_api)


if __name__ == '__main__':
    main()
