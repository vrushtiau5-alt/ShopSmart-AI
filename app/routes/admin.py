import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.contact import ContactMessage
from app.models.cart import CartItem
from app.models.wishlist import WishlistItem
from app.models.ai_log import AILog
from app.utils.decorators import admin_required
from app.utils.helpers import slugify

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login')
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_products = Product.query.count()
    total_users = User.query.filter_by(role='USER').count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0.0
    total_wishlist = WishlistItem.query.count()
    total_cart = CartItem.query.count()
    total_contacts = ContactMessage.query.count()
    total_ai_queries = AILog.query.count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    # Chart 1: Category Product Distribution
    cat_stats = db.session.query(Category.name, func.count(Product.id)).outerjoin(Product).group_by(Category.id).all()
    cat_labels = [c[0] for c in cat_stats]
    cat_counts = [c[1] for c in cat_stats]

    # Chart 2: Order Status Distribution
    status_stats = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    status_labels = [s[0] for s in status_stats]
    status_counts = [s[1] for s in status_stats]

    return render_template(
        'admin/dashboard.html',
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_wishlist=total_wishlist,
        total_cart=total_cart,
        total_contacts=total_contacts,
        total_ai_queries=total_ai_queries,
        recent_orders=recent_orders,
        cat_labels=json.dumps(cat_labels),
        cat_counts=json.dumps(cat_counts),
        status_labels=json.dumps(status_labels),
        status_counts=json.dumps(status_counts)
    )

# --- PRODUCT MANAGEMENT ---

@admin_bp.route('/products')
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)

    query = Product.query
    if search:
        query = query.filter(
            db.or_(
                Product.title.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%")
            )
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)

    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=20, error_out=False)
    product_list = pagination.items
    categories = Category.query.all()

    return render_template(
        'admin/products.html',
        products=product_list,
        pagination=pagination,
        categories=categories,
        search=search,
        selected_category_id=category_id
    )

@admin_bp.route('/product/add', methods=['GET', 'POST'])
@admin_required
def product_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        brand = request.form.get('brand', '').strip()
        price = request.form.get('price', type=float)
        rating = request.form.get('rating', 4.5, type=float)
        stock = request.form.get('stock', 50, type=int)
        features = request.form.get('features', '').strip()
        specs = request.form.get('specs', '').strip()
        image_url = request.form.get('image_url', '').strip()
        is_featured = True if request.form.get('is_featured') else False

        if not title or not price or not category_id:
            flash('Title, Price, and Category are required.', 'danger')
            return render_template('admin/product_form.html', categories=Category.query.all(), action='Add')

        product = Product(
            title=title,
            description=description,
            category_id=category_id,
            brand=brand,
            price=price,
            rating=rating,
            stock=stock,
            features=features,
            specs=specs,
            image_url=image_url or 'https://via.placeholder.com/400x300?text=Product',
            is_featured=is_featured
        )
        db.session.add(product)
        db.session.commit()

        flash(f'Product "{title}" created successfully.', 'success')
        return redirect(url_for('admin.products'))

    categories = Category.query.all()
    return render_template('admin/product_form.html', categories=categories, action='Add')

@admin_bp.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def product_edit(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.title = request.form.get('title', '').strip()
        product.description = request.form.get('description', '').strip()
        product.category_id = request.form.get('category_id', type=int)
        product.brand = request.form.get('brand', '').strip()
        product.price = request.form.get('price', type=float)
        product.rating = request.form.get('rating', type=float)
        product.stock = request.form.get('stock', type=int)
        product.features = request.form.get('features', '').strip()
        product.specs = request.form.get('specs', '').strip()
        product.image_url = request.form.get('image_url', '').strip()
        product.is_featured = True if request.form.get('is_featured') else False

        db.session.commit()
        flash(f'Product "{product.title}" updated successfully.', 'success')
        return redirect(url_for('admin.products'))

    categories = Category.query.all()
    return render_template('admin/product_form.html', product=product, categories=categories, action='Edit')

@admin_bp.route('/product/delete/<int:id>', methods=['POST'])
@admin_required
def product_delete(id):
    product = Product.query.get_or_404(id)
    title = product.title
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{title}" deleted successfully.', 'info')
    return redirect(url_for('admin.products'))

# --- CATEGORY MANAGEMENT ---

@admin_bp.route('/categories')
@admin_required
def categories():
    cat_list = Category.query.all()
    return render_template('admin/categories.html', categories=cat_list)

@admin_bp.route('/category/add', methods=['POST'])
@admin_required
def category_add():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.categories'))

    slug = slugify(name)
    existing = Category.query.filter((Category.name == name) | (Category.slug == slug)).first()
    if existing:
        flash('Category already exists.', 'warning')
        return redirect(url_for('admin.categories'))

    category = Category(
        name=name,
        slug=slug,
        description=description,
        image_url=image_url
    )
    db.session.add(category)
    db.session.commit()

    flash(f'Category "{name}" added.', 'success')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/category/edit/<int:id>', methods=['POST'])
@admin_required
def category_edit(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    image_url = request.form.get('image_url', '').strip()

    if name:
        category.name = name
        category.slug = slugify(name)
        category.description = description
        category.image_url = image_url
        db.session.commit()
        flash('Category updated.', 'success')

    return redirect(url_for('admin.categories'))

@admin_bp.route('/category/delete/<int:id>', methods=['POST'])
@admin_required
def category_delete(id):
    category = Category.query.get_or_404(id)

    # Check foreign key relationships - prevent unsafe deletion
    product_count = Product.query.filter_by(category_id=category.id).count()
    if product_count > 0:
        flash(f'Cannot delete category "{category.name}" because it contains {product_count} product(s). Please reassign or delete the products first.', 'danger')
        return redirect(url_for('admin.categories'))

    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{name}" deleted.', 'info')
    return redirect(url_for('admin.categories'))

# --- USER MANAGEMENT ---

@admin_bp.route('/users')
@admin_required
def users():
    user_list = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=user_list)

@admin_bp.route('/user/toggle-status/<int:id>', methods=['POST'])
@admin_required
def user_toggle_status(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own admin account.', 'warning')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "suspended"
    flash(f'User {user.email} has been {status_str}.', 'success')
    return redirect(url_for('admin.users'))

# --- ORDER MANAGEMENT ---

@admin_bp.route('/orders')
@admin_required
def orders():
    status = request.args.get('status', '')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    order_list = query.order_by(Order.created_at.desc()).all()

    return render_template('admin/orders.html', orders=order_list, selected_status=status)

@admin_bp.route('/order/<int:id>')
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/order/<int:id>/status', methods=['POST'])
@admin_required
def order_update_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status', '').strip()
    valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to "{new_status}".', 'success')

    return redirect(url_for('admin.order_detail', id=order.id))

# --- CONTACT MANAGEMENT ---

@admin_bp.route('/contacts')
@admin_required
def contacts():
    msg_list = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contacts.html', messages=msg_list)

@admin_bp.route('/contact/<int:id>/status', methods=['POST'])
@admin_required
def contact_update_status(id):
    msg = ContactMessage.query.get_or_404(id)
    new_status = request.form.get('status', 'Resolved').strip()
    msg.status = new_status
    db.session.commit()
    flash(f'Contact message status set to "{new_status}".', 'success')
    return redirect(url_for('admin.contacts'))

# --- AI ANALYTICS & REPORTS ---

@admin_bp.route('/analytics')
@admin_required
def analytics():
    logs = AILog.query.order_by(AILog.timestamp.desc()).limit(100).all()
    total_logs = AILog.query.count()

    top_categories = db.session.query(AILog.category_matched, func.count(AILog.id)).filter(
        AILog.category_matched.isnot(None)
    ).group_by(AILog.category_matched).order_by(func.count(AILog.id).desc()).limit(5).all()

    top_intents = db.session.query(AILog.intent_extracted, func.count(AILog.id)).filter(
        AILog.intent_extracted.isnot(None)
    ).group_by(AILog.intent_extracted).order_by(func.count(AILog.id).desc()).limit(5).all()

    return render_template(
        'admin/analytics.html',
        logs=logs,
        total_logs=total_logs,
        top_categories=top_categories,
        top_intents=top_intents
    )

@admin_bp.route('/reports')
@admin_required
def reports():
    total_sales = db.session.query(func.sum(Order.total_amount)).filter(Order.status != 'Cancelled').scalar() or 0.0
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(status='Delivered').count()
    active_users = User.query.filter_by(role='USER', is_active=True).count()
    total_products = Product.query.count()

    top_products = db.session.query(
        Product.title, func.sum(OrderItem.quantity)
    ).join(OrderItem).group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    return render_template(
        'admin/reports.html',
        total_sales=total_sales,
        total_orders=total_orders,
        completed_orders=completed_orders,
        active_users=active_users,
        total_products=total_products,
        top_products=top_products
    )
