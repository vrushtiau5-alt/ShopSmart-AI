from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app.models.user import User

def generate_reset_token(user, expires_sec=1800):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.id}, salt='password-reset-salt')

def verify_reset_token(token, expires_sec=1800):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='password-reset-salt', max_age=expires_sec)
        user_id = data.get('user_id')
    except Exception:
        return None
    return User.query.get(user_id)
