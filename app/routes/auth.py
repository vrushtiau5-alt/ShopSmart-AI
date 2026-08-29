import random
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.tokens import generate_reset_token, verify_reset_token
from app.services.email_service import send_password_reset_email

auth_bp = Blueprint('auth', __name__)

# ==========================================
# REGISTRATION SELECTION & SPLIT ROUTES
# ==========================================

@auth_bp.route('/register', methods=['GET'])
def register():
    """Main registration account-type selection page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('user.home'))
    return render_template('auth/register_select.html')

@auth_bp.route('/register/user', methods=['GET', 'POST'])
def register_user():
    """Customer registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')

        full_name = f"{first_name} {last_name}".strip() if first_name else request.form.get('full_name', '').strip()

        if not full_name or not email or not password:
            flash('Full Name, Email, and Password are required.', 'danger')
            return render_template('auth/register_user.html')

        if not terms:
            flash('You must agree to the Terms and Conditions to register.', 'warning')
            return render_template('auth/register_user.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_user.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register_user.html')

        if username and User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'warning')
            return render_template('auth/register_user.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists.', 'warning')
            return render_template('auth/register_user.html')

        # PUBLIC CUSTOMER REGISTRATION ALWAYS SETS ROLE = 'USER'
        user = User(
            full_name=full_name,
            username=username if username else email.split('@')[0],
            email=email,
            phone=phone,
            role='USER',
            is_active=True,
            email_verified=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please login to continue.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_user.html')

@auth_bp.route('/register/admin', methods=['GET', 'POST'])
def register_admin():
    """Administrator registration route with invite code verification."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('user.home'))

    if request.method == 'POST':
        full_name = request.form.get('admin_name', '').strip() or request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        admin_code = request.form.get('admin_code', '').strip()

        expected_code = current_app.config.get('ADMIN_INVITE_CODE', 'change_this_secure_code')

        if not full_name or not email or not password or not admin_code:
            flash('All fields including Administrator Authorization Code are required.', 'danger')
            return render_template('auth/register_admin.html')

        # SERVER-SIDE ADMIN AUTHORIZATION CODE VALIDATION
        if admin_code != expected_code:
            flash('Invalid Administrator Authorization Code. Admin registration denied.', 'danger')
            return render_template('auth/register_admin.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register_admin.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register_admin.html')

        if username and User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'warning')
            return render_template('auth/register_admin.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists.', 'warning')
            return render_template('auth/register_admin.html')

        # ADMIN REGISTRATION SETS ROLE = 'ADMIN'
        admin_user = User(
            full_name=full_name,
            username=username if username else f"admin_{email.split('@')[0]}",
            email=email,
            phone=phone,
            role='ADMIN',
            is_active=True,
            email_verified=True
        )
        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        flash('Admin registration successful. Please login to continue.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_admin.html')

# ==========================================
# LOGIN SELECTION & SPLIT ROUTES
# ==========================================

@auth_bp.route('/login', methods=['GET'])
def login():
    """Main login account-type selection page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('user.home'))
    return render_template('auth/login_select.html')

@auth_bp.route('/login/user', methods=['GET', 'POST'])
def login_user_route():
    """Customer login route."""
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))

    if request.method == 'POST':
        login_input = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid email/username or password.', 'danger')
            return render_template('auth/login_user.html')

        if not user.is_active:
            flash('Your account has been suspended. Please contact customer support.', 'danger')
            return render_template('auth/login_user.html')

        # STRICT ROLE VERIFICATION FOR USER LOGIN
        if user.role != 'USER':
            flash('Access Denied: Please use Admin Login for administrator accounts.', 'danger')
            return render_template('auth/login_user.html')

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.full_name}!', 'success')

        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('user.home'))

    return render_template('auth/login_user.html')

@auth_bp.route('/login/admin', methods=['GET', 'POST'])
def login_admin_route():
    """Admin login route."""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        login_input = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid admin credentials.', 'danger')
            return render_template('auth/login_admin.html')

        if not user.is_active:
            flash('Admin account is suspended.', 'danger')
            return render_template('auth/login_admin.html')

        # STRICT ROLE VERIFICATION FOR ADMIN LOGIN
        if user.role != 'ADMIN':
            flash('Access Denied: You do not have administrator permissions.', 'danger')
            return render_template('auth/login_admin.html')

        login_user(user, remember=remember)
        flash(f'Administrator login successful. Welcome, {user.full_name}.', 'success')

        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))

    return render_template('auth/login_admin.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    logout_user()
    flash('You have been logged out successfully.', 'info')
    response = redirect(url_for('auth.login'))
    response.delete_cookie('remember_token')
    response.delete_cookie(current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token'))
    return response

# ==========================================
# FORGOT PASSWORD & OTP RESET FLOW
# ==========================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate 6-digit OTP and reset token
            otp = f"{random.randint(100000, 999999)}"
            expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
            token = generate_reset_token(user)

            user.forgot_password_otp = otp
            user.forgot_password_otp_expiry = expiry
            user.reset_token = token
            user.reset_token_expiry = expiry
            db.session.commit()

            # Development fallback logging
            print(f"\n========================================================")
            print(f" [DEV OTP LOG] Password Reset for {user.email}")
            print(f" OTP Code : {otp}")
            print(f" Token    : {token}")
            print(f"========================================================\n")

            send_password_reset_email(user, token)
            session['reset_email'] = email
            flash('Password reset instructions and OTP code have been generated.', 'info')
            return redirect(url_for('auth.verify_reset_otp'))

        flash('If an account with that email exists, reset instructions have been generated.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    email = session.get('reset_email', '')
    if request.method == 'POST':
        input_email = request.form.get('email', '').strip().lower() or email
        input_otp = request.form.get('otp', '').strip()

        user = User.query.filter_by(email=input_email).first()
        if not user or not user.forgot_password_otp or user.forgot_password_otp != input_otp:
            flash('Invalid OTP code. Please check and try again.', 'danger')
            return render_template('auth/verify_otp.html', email=email)

        if user.forgot_password_otp_expiry and user.forgot_password_otp_expiry < datetime.datetime.utcnow():
            flash('OTP code has expired. Please request a new password reset.', 'warning')
            return redirect(url_for('auth.forgot_password'))

        # Valid OTP: redirect to reset password page
        session['verified_reset_user_id'] = user.id
        return redirect(url_for('auth.reset_password'))

    return render_template('auth/verify_otp.html', email=email)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token=None):
    user = None
    if token:
        user = verify_reset_token(token)
    elif 'verified_reset_user_id' in session:
        user = User.query.get(session['verified_reset_user_id'])

    if not user:
        flash('Invalid or expired password reset request.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        user.forgot_password_otp = None
        user.forgot_password_otp_expiry = None
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        session.pop('verified_reset_user_id', None)
        session.pop('reset_email', None)

        flash('Password reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
