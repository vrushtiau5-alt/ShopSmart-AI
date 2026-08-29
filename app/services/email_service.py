import sys
from flask import url_for, current_app
from flask_mail import Message
from app import mail

def send_password_reset_email(user, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    subject = "ShopSmart AI - Password Reset Request"

    body = f"""Hello {user.full_name},

You requested a password reset for your ShopSmart AI account.

Please click the following link to reset your password:
{reset_url}

This link is valid for 30 minutes. If you did not request this, please ignore this email.

Best regards,
The ShopSmart AI Team
"""

    # Always log reset link to console for easy local testing
    print(f"\n========================================================", file=sys.stderr)
    print(f"[DEVELOPMENT PASSWORD RESET LOG]", file=sys.stderr)
    print(f"Target User: {user.email}", file=sys.stderr)
    print(f"Reset Link : {reset_url}", file=sys.stderr)
    print(f"========================================================\n", file=sys.stderr)

    try:
        if current_app.config.get('MAIL_SERVER') and current_app.config.get('MAIL_SERVER') != 'localhost':
            msg = Message(subject=subject, recipients=[user.email], body=body)
            mail.send(msg)
            return True, "Password reset email sent."
        else:
            return True, "Development mode: Reset link generated and logged to server console."
    except Exception as e:
        print(f"Failed to send email via SMTP: {e}", file=sys.stderr)
        return True, "Development mode: Reset link generated and logged to server console."
