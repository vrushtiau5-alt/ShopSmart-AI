# ShopSmart AI - Intelligent E-Commerce Web Application

ShopSmart AI is a complete, production-grade e-commerce web platform built with Python, Flask, SQLAlchemy, MySQL, Bootstrap 5, and an AI Shopping Assistant powered by natural language intent extraction and multi-turn context memory.

---

## Technical Stack

- **Backend**: Python 3.13, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Mail, Werkzeug
- **Database**: MySQL (PyMySQL ORM)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Font Awesome 6
- **AI Engine**: Google Gemini API / OpenAI API integration with intelligent local fallback intent & category matching engine
- **Testing**: Pytest, Pytest-Flask

---

## Project Structure

```
ShopSmart-AI/
│
├── app.py                      # Flask app entry point
├── run.py                      # Main launcher script (python run.py) & CLI seed tools
├── config.py                   # Environment configuration & database connection builder
├── requirements.txt            # Python dependencies
├── .env                        # Active environment configuration
├── .env.example                # Template environment variables
├── README.md                   # Setup documentation
│
├── app/
│   ├── __init__.py             # Application factory, extensions setup & error handlers
│   ├── models/                 # Database models (User, Product, Category, Cart, Wishlist, Order, Contact, AILog)
│   ├── routes/                 # Blueprint routes (auth, user, admin, api)
│   ├── services/               # Core services (ai_service, email_service)
│   ├── utils/                  # Decorators (@admin_required), tokens, helpers
│   ├── templates/              # Jinja2 templates (user, admin, auth, components, errors)
│   └── static/                 # Static assets (css, js, images)
│
├── dataset/                    # Amazon dataset pipeline
│   ├── clean_dataset.py
│   ├── prepare_amazon_products.py
│   └── import_amazon_products.py
│
└── tests/                      # Automated test suite (pytest)
```

---

## Database Setup (MySQL)

1. Open your MySQL client (MySQL Command Line Client or MySQL Workbench).
2. Create the database:
   ```sql
   CREATE DATABASE ai_shopping_assistant;
   ```
3. Configure your MySQL credentials in `.env`:
   ```ini
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=ai_shopping_assistant
   ```

*Note: In accordance with project configuration, if MySQL is unreachable, the application will not silently switch to SQLite in production mode; it will cleanly present database setup instructions.*

---

## Installation & Data Seeding

1. **Install Dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Seed Initial Database & Default Accounts**:
   ```bash
   python run.py seed
   ```
   *This command creates the database tables, seeds default customer and admin accounts, and populates products across all core categories (including Induction Stoves, Laptops, Mobile Phones, Headphones, and Footwear).*

3. **(Optional) Import Custom Amazon Parquet / CSV Dataset**:
   ```bash
   python run.py import-data path/to/dataset.csv
   ```

---

## Running the Application

Execute the launch command:

```bash
python run.py
```

Access the application in your browser:

- **Customer Interface**: `http://127.0.0.1:5000/`
- **Admin Interface**: `http://127.0.0.1:5000/admin/login`

---

## Default Development Accounts

### Administrator Account
- **URL**: `http://127.0.0.1:5000/admin/login`
- **Role**: `ADMIN`
- **Email**: `admin@shopsmart.ai`
- **Password**: `admin123`

### Customer Account
- **URL**: `http://127.0.0.1:5000/login`
- **Role**: `USER`
- **Email**: `customer@shopsmart.ai`
- **Password**: `user123`

---

## Key Features

1. **Dual Separated Interfaces**:
   - **Customer Interface**: Home hero, product catalog with multi-filter & sorting, product details, AJAX cart, wishlist, product comparison, natural language Shopping Planner, AI Chatbot assistant, order checkout & status tracking, profile management, contact form.
   - **Admin Interface**: Executive dashboard, Metric cards & Chart.js graphs, Product CRUD, Category CRUD (with FK protection), User activation/suspension, Order status updates, Contact message management, AI analytics, and Sales reports.

2. **AI Shopping Assistant**:
   - Intent & entity extraction ("Show me induction stoves" returns induction cooktops, NOT airpods or laptops).
   - Multi-turn conversation context memory ("Which one is cheaper?").
   - Single-request guard locking in JS to prevent duplicate AJAX calls or messages.

3. **Security**:
   - Password hashing via Werkzeug (`generate_password_hash` / `check_password_hash`).
   - Dual-role database verification (`USER` vs `ADMIN`).
   - Non-admin access to `/admin` returns HTTP 403 Forbidden.
   - Time-limited, single-use password reset tokens via email or console logging fallback.

---

## Running Tests

Execute the Pytest suite:

```bash
pytest
```
