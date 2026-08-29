from functools import wraps
from flask import render_template, abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return render_template('errors/401.html'), 401
        if current_user.role != 'ADMIN':
            return render_template('errors/403.html'), 403
        return f(*args, **kwargs)
    return decorated_function
