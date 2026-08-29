import os
import sys
from app import create_app
from app.utils.seed import seed_database_builtin

app = create_app()


def seed_database():
    print("Initializing database tables, default accounts, and product catalog...")
    with app.app_context():
        return seed_database_builtin()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == 'seed':
            success = seed_database()
            sys.exit(0 if success else 1)

    # Automatically initialize database and sample data on startup
    with app.app_context():
        seed_database_builtin()

    debug_enabled = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')

    print("\n========================================================")
    print(" Starting ShopSmart AI Web Application")
    print(" Customer URL  : http://127.0.0.1:5000/")
    print(" Admin URL     : http://127.0.0.1:5000/admin/login")
    print(f" Debugger Mode : {'ON' if debug_enabled else 'OFF'}")
    print("========================================================\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_enabled
    )