import os
import sys
from app import create_app
from app.utils.seed import seed_database_builtin

app = create_app()


def seed_database():
    print("Initializing database tables, default accounts, and product catalog...")
    with app.app_context():
        try:
            return seed_database_builtin()
        except Exception as err:
            print(f"Warning: Primary DB initialization exception: {err}")
            _sqlite_uri = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'shopsmart.db')}"
            app.config['SQLALCHEMY_DATABASE_URI'] = _sqlite_uri
            from app import db
            db.engine.dispose()
            db.init_app(app)
            return seed_database_builtin()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == 'seed':
            success = seed_database()
            sys.exit(0 if success else 1)

    # Automatically initialize database and sample data on startup
    try:
        with app.app_context():
            seed_database_builtin()
    except Exception as err:
        print(f"Warning: Startup database initialization fallback engaged ({err})")
        _sqlite_uri = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'shopsmart.db')}"
        app.config['SQLALCHEMY_DATABASE_URI'] = _sqlite_uri
        from app import db
        with app.app_context():
            db.engine.dispose()
            db.init_app(app)
            seed_database_builtin()

    debug_enabled = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')

    port_number = int(os.environ.get('PORT', 5000))

    print("\n========================================================")
    print(" Starting ShopSmart AI Web Application")
    print(f" Server Port   : {port_number}")
    print(f" Debugger Mode : {'ON' if debug_enabled else 'OFF'}")
    print("========================================================\n")

    app.run(
        host='0.0.0.0',
        port=port_number,
        debug=debug_enabled
    )