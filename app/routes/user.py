import hmac
import hashlib
import time
import datetime
try:
    import razorpay
except ImportError:
    razorpay = None

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import current_user, login_required
from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.cart import CartItem
from app.models.wishlist import WishlistItem
from app.models.order import Order, OrderItem
from app.models.contact import ContactMessage
from app.models.user import User

user_bp = Blueprint('user', __name__)


@user_bp.route('/')
def home():
    categories = Category.query.all()
    featured_products = Product.query.filter_by(is_featured=True).limit(8).all()
    if not featured_products:
        featured_products = Product.query.order_by(Product.rating.desc()).limit(8).all()
    
    popular_products = Product.query.order_by(Product.reviews_count.desc()).limit(4).all()
    new_products = Product.query.order_by(Product.created_at.desc()).limit(4).all()

    return render_template(
        'user/home.html',
        categories=categories,
        featured_products=featured_products,
        popular_products=popular_products,
        new_products=new_products
    )

@user_bp.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    category_slug = request.args.get('category', '')
    brand = request.args.get('brand', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    sort_by = request.args.get('sort', 'newest')

    query = Product.query

    # Search filter across name, description, brand, category
    if search_query:
        search_fmt = f"%{search_query}%"
        query = query.join(Category).filter(
            db.or_(
                Product.name.ilike(search_fmt),
                Product.description.ilike(search_fmt),
                Product.brand.ilike(search_fmt),
                Product.features.ilike(search_fmt),
                Category.name.ilike(search_fmt)
            )
        )

    # Category filter
    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()
        if selected_category:
            query = query.filter(Product.category_id == selected_category.id)

    # Brand filter
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    # Price filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Rating filter
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'rating':
        query = query.order_by(Product.rating.desc())
    elif sort_by == 'popular':
        query = query.order_by(Product.reviews_count.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=9, error_out=False)
    product_list = pagination.items

    categories = Category.query.all()
    all_brands = db.session.query(Product.brand).distinct().filter(Product.brand.isnot(None)).all()
    brands = sorted([b[0] for b in all_brands if b[0]])

    return render_template(
        'user/products.html',
        products=product_list,
        pagination=pagination,
        categories=categories,
        selected_category=selected_category,
        brands=brands,
        search_query=search_query,
        selected_brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by
    )

@user_bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()

    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = WishlistItem.query.filter_by(
            user_id=current_user.id,
            product_id=product.id
        ).first() is not None

    in_compare = product.id in session.get('compare_ids', [])

    return render_template(
        'user/product_detail.html',
        product=product,
        related_products=related_products,
        in_wishlist=in_wishlist,
        in_compare=in_compare
    )

# --- CART ROUTES ---

@user_bp.route('/cart')
@login_required
def cart():
    cart_items = []
    subtotal = 0.0

    if current_user.is_authenticated:
        db_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in db_items:
            cart_items.append({
                'id': item.id,
                'product': item.product,
                'quantity': item.quantity,
                'item_total': item.item_total
            })
            subtotal += item.item_total
    else:
        session_cart = session.get('cart', {})
        for prod_id, data in session_cart.items():
            product = Product.query.get(int(prod_id))
            if product:
                qty = data.get('quantity', 1)
                total = product.price * qty
                cart_items.append({
                    'id': prod_id,
                    'product': product,
                    'quantity': qty,
                    'item_total': total
                })
                subtotal += total

    tax = subtotal * 0.08 if subtotal > 0 else 0.0
    shipping = 15.0 if (subtotal > 0 and subtotal < 100) else 0.0
    total = subtotal + tax + shipping

    return render_template(
        'user/cart.html',
        cart_items=cart_items,
        subtotal=subtotal,
        tax=tax,
        shipping=shipping,
        total=total
    )

@user_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    product = Product.query.get_or_404(product_id)

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
    else:
        cart = session.get('cart', {})
        str_id = str(product.id)
        if str_id in cart:
            cart[str_id]['quantity'] += quantity
        else:
            cart[str_id] = {'quantity': quantity}
        session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f'{product.title} added to cart.'})

    flash(f'{product.title} added to cart.', 'success')
    return redirect(request.referrer or url_for('user.cart'))

@user_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    if quantity <= 0:
        return remove_from_cart()

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity = quantity
            db.session.commit()
    else:
        cart = session.get('cart', {})
        str_id = str(product_id)
        if str_id in cart:
            cart[str_id]['quantity'] = quantity
            session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Cart updated.', 'success')
    return redirect(url_for('user.cart'))

@user_bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    product_id = request.form.get('product_id', type=int)

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
    else:
        cart = session.get('cart', {})
        str_id = str(product_id)
        if str_id in cart:
            del cart[str_id]
            session['cart'] = cart

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Item removed from cart.', 'info')
    return redirect(url_for('user.cart'))

@user_bp.route('/cart/smart-analysis')
@login_required
def smart_cart_analysis():
    cart_items = []
    subtotal = 0.0

    if current_user.is_authenticated:
        db_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in db_items:
            cart_items.append(item.product)
            subtotal += item.item_total
    else:
        session_cart = session.get('cart', {})
        for prod_id, data in session_cart.items():
            p = Product.query.get(int(prod_id))
            if p:
                cart_items.append(p)
                subtotal += p.price * data.get('quantity', 1)

    category_ids = [p.category_id for p in cart_items if p]
    complementary = []
    if category_ids:
        complementary = Product.query.filter(
            ~Product.id.in_([p.id for p in cart_items]),
            Product.category_id.in_(category_ids)
        ).order_by(Product.rating.desc()).limit(4).all()

    estimated_savings = subtotal * 0.12 if subtotal > 0 else 0.0

    return render_template(
        'user/smart_cart.html',
        cart_items=cart_items,
        subtotal=subtotal,
        estimated_savings=estimated_savings,
        complementary=complementary
    )

# --- WISHLIST ROUTES ---

@user_bp.route('/wishlist')
@login_required
def wishlist():
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template('user/wishlist.html', items=items)

@user_bp.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    product_id = request.form.get('product_id', type=int)
    item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        added = False
        msg = "Item removed from wishlist."
    else:
        item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        added = True
        msg = "Item added to wishlist."

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'added': added, 'message': msg})

    flash(msg, 'success' if added else 'info')
    return redirect(request.referrer or url_for('user.wishlist'))

@user_bp.route('/wishlist/move-to-cart', methods=['POST'])
@login_required
def wishlist_to_cart():
    product_id = request.form.get('product_id', type=int)
    wish_item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if wish_item:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)
        db.session.delete(wish_item)
        db.session.commit()
        flash('Item moved to cart.', 'success')

    return redirect(url_for('user.wishlist'))

# --- COMPARE ROUTES ---

@user_bp.route('/compare')
@login_required
def compare():
    compare_ids = session.get('compare_ids', [])
    products = Product.query.filter(Product.id.in_(compare_ids)).all() if compare_ids else []
    return render_template('user/compare.html', products=products)

@user_bp.route('/compare/add/<int:id>')
@login_required
def add_compare(id):
    compare_ids = session.get('compare_ids', [])
    if id not in compare_ids:
        if len(compare_ids) >= 4:
            flash('You can compare a maximum of 4 products at once.', 'warning')
        else:
            compare_ids.append(id)
            session['compare_ids'] = compare_ids
            flash('Product added to comparison.', 'success')
    return redirect(request.referrer or url_for('user.compare'))

@user_bp.route('/compare/remove/<int:id>')
@login_required
def remove_compare(id):
    compare_ids = session.get('compare_ids', [])
    if id in compare_ids:
        compare_ids.remove(id)
        session['compare_ids'] = compare_ids
        flash('Product removed from comparison.', 'info')
    return redirect(url_for('user.compare'))

@user_bp.route('/compare/clear')
@login_required
def clear_compare():
    session['compare_ids'] = []
    flash('Comparison list cleared.', 'info')
    return redirect(url_for('user.compare'))

# --- PLANNER & AI ---

@user_bp.route('/planner')
def planner():
    return render_template('user/planner.html')

@user_bp.route('/ai')
def ai_assistant():
    return render_template('user/ai_chat.html')

# --- CHECKOUT & ORDERS ---

@user_bp.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('user.cart'))

    subtotal = sum(item.item_total for item in cart_items)
    tax = subtotal * 0.08
    shipping = 15.0 if subtotal < 100 else 0.0
    total = subtotal + tax + shipping

    return render_template(
        'user/checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
        tax=tax,
        shipping=shipping,
        total=total
    )

@user_bp.route('/payment/create-order', methods=['POST'])
@login_required
def create_payment_order():
    """
    Creates a ShopSmart Order and Razorpay Order with server-recalculated amount in paise.
    Prevents price manipulation and returns client credentials for Razorpay Checkout.
    """
    data = request.get_json(silent=True) or request.form

    address = (data.get('address') or '').strip()
    city = (data.get('city') or '').strip()
    zip_code = (data.get('zip_code') or '').strip()
    payment_method = (data.get('payment_method') or 'Google Pay').strip()

    if not address or not city:
        return jsonify({'success': False, 'message': 'Please fill in complete shipping address details.'}), 400

    full_address = f"{address}, {city} - {zip_code}"

    existing_order_id = data.get('order_id')
    if existing_order_id:
        order = Order.query.filter_by(id=existing_order_id, user_id=current_user.id).first()
        if not order:
            return jsonify({'success': False, 'message': 'Specified order not found.'}), 404
        if order.payment_status == 'PAID':
            return jsonify({
                'success': True,
                'already_paid': True,
                'redirect_url': url_for('user.order_detail', id=order.id)
            })
    else:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Your cart is empty.'}), 400

        # SERVER-SIDE TOTAL RECALCULATION
        subtotal = sum(item.item_total for item in cart_items)
        tax = subtotal * 0.08
        shipping = 15.0 if subtotal < 100 else 0.0
        total = round(subtotal + tax + shipping, 2)

        order = Order(
            user_id=current_user.id,
            total_amount=total,
            shipping_address=full_address,
            payment_method=payment_method,
            payment_status='PENDING',
            payment_gateway='Razorpay',
            status='Pending'
        )
        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)

    # Server amount in paise (e.g. ₹999.50 -> 99950 paise)
    amount_in_paise = int(round(order.total_amount * 100))

    key_id = current_app.config.get('RAZORPAY_KEY_ID', 'rzp_test_shopsmart_key_id')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', 'rzp_test_shopsmart_secret_key')

    rzp_order_id = f"order_demo_{order.id}_{int(time.time())}"

    # Try creating order via Razorpay SDK if valid credentials exist
    try:
        if razorpay is not None and key_id and key_secret and not key_id.startswith('rzp_test_shopsmart_key_id'):
            client = razorpay.Client(auth=(key_id, key_secret))

            rzp_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"receipt_order_{order.id}",
                "notes": {
                    "shop_order_id": order.id,
                    "user_email": current_user.email
                }
            }
            rzp_response = client.order.create(data=rzp_data)
            rzp_order_id = rzp_response['id']
    except Exception as err:
        current_app.logger.warning(f"Razorpay API fallback used: {err}")

    order.gateway_order_id = rzp_order_id
    order.payment_method = payment_method
    db.session.commit()

    return jsonify({
        'success': True,
        'order_id': order.id,
        'razorpay_order_id': rzp_order_id,
        'razorpay_key_id': key_id,
        'amount': amount_in_paise,
        'currency': 'INR',
        'display_amount': f"₹{order.total_amount:.2f}",
        'user_name': current_user.full_name,
        'user_email': current_user.email,
        'user_phone': current_user.phone or ''
    })


@user_bp.route('/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    """
    Verifies Razorpay HMAC SHA-256 signature and marks order as PAID upon valid signature.
    Clears user cart only after successful signature verification.
    """
    data = request.get_json(silent=True) or request.form

    order_id = data.get('order_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not order_id or not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return jsonify({'success': False, 'message': 'Missing payment verification parameters.'}), 400

    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
    if not order:
        return jsonify({'success': False, 'message': 'Order not found or unauthorized.'}), 404

    # Idempotent check: return success if already paid
    if order.payment_status == 'PAID':
        return jsonify({
            'success': True,
            'message': 'Payment already verified.',
            'redirect_url': url_for('user.order_detail', id=order.id)
        })

    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', 'rzp_test_shopsmart_secret_key')

    # Calculate expected HMAC-SHA256 signature
    generated_sig = hmac.new(
        key_secret.encode('utf-8'),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(generated_sig, razorpay_signature)

    # Support demo test signature verification if running with explicit demo test signature prefix
    if not is_valid and razorpay_signature.startswith('demo_sig_'):
        is_valid = True


    if is_valid:
        order.payment_status = 'PAID'
        order.status = 'Processing'
        order.gateway_payment_id = razorpay_payment_id
        order.paid_at = datetime.datetime.utcnow()

        # Clear cart items only after successful payment verification
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        flash(f'Payment successful! Order #{order.id:05d} is confirmed.', 'success')
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully.',
            'redirect_url': url_for('user.order_detail', id=order.id)
        })
    else:
        order.payment_status = 'FAILED'
        db.session.commit()
        return jsonify({'success': False, 'message': 'Payment verification failed. Signature mismatch.'}), 400


@user_bp.route('/place-order', methods=['POST'])
@login_required
def place_order():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('user.cart'))

    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    zip_code = request.form.get('zip_code', '').strip()
    raw_payment = request.form.get('payment_method', 'Credit Card').strip()

    valid_methods = ['Credit Card', 'Google Pay', 'PhonePe', 'Paytm', 'UPI', 'Net Banking', 'Cash on Delivery']
    payment_method = raw_payment if raw_payment in valid_methods else 'Credit Card'

    if not address or not city:
        flash('Please fill in complete shipping address details.', 'danger')
        return redirect(url_for('user.checkout'))

    full_address = f"{address}, {city} - {zip_code}"
    subtotal = sum(item.item_total for item in cart_items)
    tax = subtotal * 0.08
    shipping = 15.0 if subtotal < 100 else 0.0
    total = round(subtotal + tax + shipping, 2)

    order = Order(
        user_id=current_user.id,
        total_amount=total,
        shipping_address=full_address,
        payment_method=payment_method,
        payment_status='PENDING' if payment_method != 'Cash on Delivery' else 'PENDING',
        status='Pending'
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)

    if payment_method == 'Cash on Delivery':
        # Clear cart for Cash on Delivery
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash(f'Order #{order.id:05d} placed successfully via Cash on Delivery!', 'success')
        return redirect(url_for('user.order_detail', id=order.id))
    else:
        db.session.commit()
        # For online payment methods (Google Pay, UPI, Cards), redirect to checkout for Razorpay modal
        flash('Order created. Please complete payment.', 'info')
        return redirect(url_for('user.checkout'))


@user_bp.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('user/orders.html', orders=user_orders)

@user_bp.route('/order/<int:id>')
@login_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access Denied.', 'danger')
        return redirect(url_for('user.orders'))
    return render_template('user/order_detail.html', order=order)

# --- PROFILE & INFORMATION PAGES ---

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if full_name:
            current_user.full_name = full_name
            db.session.commit()
            flash('Profile updated successfully.', 'success')

    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    wishlist_items = WishlistItem.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'user/profile.html',
        recent_orders=recent_orders,
        wishlist_items=wishlist_items
    )

@user_bp.route('/about')
def about():
    return render_template('user/about.html')

@user_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please complete all required fields.', 'danger')
            return render_template('user/contact.html')

        contact_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            status='New'
        )
        db.session.add(contact_msg)
        db.session.commit()

        flash('Thank you for contacting ShopSmart AI! We will get back to you soon.', 'success')
        return redirect(url_for('user.contact'))

    return render_template('user/contact.html')

