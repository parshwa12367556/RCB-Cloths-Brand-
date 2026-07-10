# 🏆 ARENA Sports Luxury — RCB Cloths Brand

> **A luxury sports-fashion e-commerce platform** — Not just merchandise. A symbol of fearless fandom.

ARENA (formerly RCB Cloths Brand) is a full-featured, multi-role e-commerce web application built with Flask that transforms sports merchandise retail into a premium luxury experience. From cricket to Formula 1, esports to NBA — every sport, every league, one **Arena**.

---

## ✨ Features

### 👥 Multi-Role Authentication
| Role | Capabilities |
|------|-------------|
| **Admin** | Full control over products, orders, users, deliveries, returns, notifications, and analytics |
| **Customer** | Browse, purchase, review products; manage orders, returns, wallet, and membership |
| **Delivery Personnel** | View assigned orders, update delivery status, track earnings |

### 🛍️ E-Commerce Core
- **Product Management** — CRUD operations with images, categories, pricing, stock levels, and low-stock thresholds
- **Category System** — Organize products by sport/collection (Football, Cricket, IPL, NBA, Formula 1, Esports, etc.)
- **Shopping Cart** — Full cart with quantity management, jersey personalization (custom name + number)
- **Checkout System** — Address management, shipping, tax calculation, free delivery thresholds
- **Order Management** — Order lifecycle from `payment_pending` → `pending` → `shipped` → `out_for_delivery` → `delivered`
- **Order Tracking** — Public tracking page using unique tracking IDs (e.g., `TRK-12345678`)

### 💳 Payments & Wallet
- **Razorpay Integration** — Secure online payments with order creation, verification, and webhook support
- **Store Wallet** — Customers get refunds to their wallet; wallet balance can be used for purchases
- **Wallet Transaction Log** — Complete audit trail of all credits/debits
- **Cash on Delivery (COD)** — Traditional payment method support

### 💰 Premium Features
- **Membership Ecosystem ("The Bold Club")** — Tiered loyalty system:
  - 🟤 **Rookie Fan** (0–499 points)
  - 🥉 **Stadium Loyalist** (500–1,999 points)
  - 🥈 **Arena Champion** (2,000–4,999 points)
  - 🥇 **Dynasty Elite** (5,000+ points)
- **Loyalty Points** — Earn points with every successful order
- **Championship Rewards** — Exclusive perks based on membership tier

### 📦 Delivery Management
- **Delivery Person Portal** — Separate login for delivery staff
- **Route Management** — View active deliveries with Google Maps navigation
- **Status Updates** — Mark orders as `out_for_delivery`, `delivered`, or `failed`
- **Earnings Tracking** — ₹40 flat fee per successful delivery with earning history

### 🔄 Returns & Refunds
- **Return Request System** — Customers can request returns on delivered orders
- **Trust Algorithm** — Users with 3+ successful orders get **instant wallet refunds**
- **Razorpay Refunds** — Automated refunds to original payment method (with wallet fallback)
- **Return Lifecycle** — `pending` → `picked_up` → `refunded` / `rejected`

### ⭐ Reviews & Ratings
- **Product Reviews** — Verified purchase-based reviews with 1–5 star ratings
- **Average Rating Calculation** — Auto-computed on product models
- **Review Ownership** — One review per user per product

### 🔔 Notifications
- **In-App Notifications** — Order confirmations, low stock alerts, refund notifications
- **Read/Unread Tracking** — Unread count shown globally in navbar
- **Bulk Mark Read** — Mark all notifications as read at once

### 📊 Admin Dashboard (Command Center)
- **Real-Time Analytics** — Revenue, profit, orders, users, pending actions
- **Chart.js Visualizations** — Daily / weekly / monthly revenue and profit charts
- **Top Selling Products** — Trending drops with percentage bars
- **Order Management** — Status updates, delivery person assignment
- **Inventory Management** — Product CRUD with pagination, stock alerts
- **User Management** — View all customers and their activity
- **Returns Management** — Process pickups, trigger refunds
- **Broadcast System** — Send notifications to users
- **Support Tickets** — "Talk to a Human" feature generates priority support tickets

### 🎯 AI & Personalization
- **AI Jersey Recommendations** — Trending jersey picks generated dynamically
- **Recently Viewed** — Tracked via session data (4 most recent products)
- **Smart Recommendations** — Products in same category as recently viewed items
- **"ATHLUXE" AI Sports Stylist** — Mock outfit coordination engine

### 🎨 Premium UI/UX
- **Cinematic Motion System** — Staggered fade reveals, parallax scrolling, floating gradients
- **Luxury Brand Storytelling** — "THE BOLD LEGACY" narrative section
- **Premium Typography** — Oversized headings, dramatic spacing, luxury alignment
- **Limited Edition Drops** — Countdown timer for exclusive product launches
- **Interactive Hero Section** — Mouse-follow glow, layered parallax, animated lion watermark
- **Athlete Showcase** — Featured athlete profiles with quotes
- **Seasonal Campaign System** — Dynamic theming (IPL, Gold Edition, etc.)
- **Product Badges** — Championship, Limited Edition, Exclusive indicators
- **Smooth Skeleton Loaders** — Gradient shimmer cards during async loading
- **Mobile Luxury Experience** — Thumb-friendly interactions, sticky bottom cart, swipe galleries
- **Advanced Product Showcase** — 360° rotation, fabric zoom, lifestyle model shots

### 📧 Email Integration
- **Order Confirmations** — HTML email receipts with order summary
- **Password Reset** — Secure email-based password reset with expiring tokens (1 hour)
- **SMTP Configuration** — Gmail SMTP support

### ⚙️ Background Tasks
- **Abandoned Order Cleanup** — APScheduler deletes `payment_pending` orders older than 24 hours (runs every hour)
- **Low Stock Alerts** — Automatic admin notifications when stock drops below threshold

### 📄 PDF Invoices
- **Printable Invoices** — Generate downloadable PDF invoices for completed orders using xhtml2pdf

### 🔒 Security
- **Password Hashing** — Werkzeug security (generate_password_hash / check_password_hash)
- **CSRF Protection** — Flask-Login integration
- **Payment Signature Verification** — Razorpay cryptographic verification
- **Webhook Signature Verification** — Secure Razorpay webhook handling
- **Role-Based Access Control** — Admin decorator, delivery person session checks
- **Rate Limiting** — Vague error messages to prevent user enumeration attacks

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | [Flask](https://flask.palletsprojects.com/) (Python 3.x) |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) |
| **Auth** | [Flask-Login](https://flask-login.readthedocs.io/) |
| **Migrations** | [Flask-Migrate](https://flask-migrate.readthedocs.io/) (Alembic) |
| **Database** | SQLite (development) — easily switchable to PostgreSQL/MySQL |
| **Payments** | [Razorpay](https://razorpay.com/) |
| **Scheduler** | [APScheduler](https://apscheduler.readthedocs.io/) |
| **PDF** | [xhtml2pdf](https://github.com/xhtml2pdf/xhtml2pdf) |
| **Templating** | Jinja2 |
| **Frontend** | Bootstrap 5, Font Awesome 6, Chart.js |
| **Custom CSS/JS** | Arena design system (`static/`) |
| **Email** | smtplib (Gmail SMTP) |

---

## 📁 Project Structure

```
├── app.py                  # Main Flask application entry point
├── models.py               # Database models (User, Product, Order, etc.)
├── extensions.py           # Flask extensions initialization (db, login_manager)
├── admin.py                # Admin panel blueprint
├── customer.py             # Customer-facing routes blueprint
├── product.py              # Product listing and detail routes
├── delivery.py             # Delivery personnel portal
├── requirement.txt         # Development notes & roadmap (not pip requirements)
├── scripts/
│   └── write_profile.py    # Utility script for profiles
├── instance/
│   └── grocery.db          # SQLite database file
├── static/
│   ├── admin/              # Admin panel CSS, JS, charts
│   ├── auth/               # Login/register CSS
│   ├── delivery/           # Delivery dashboard CSS
│   ├── layout/             # Base layout CSS (navbar, footer, error pages)
│   └── shop/               # Shop UI CSS (arena theme, index, cart, checkout, etc.)
└── templates/
    ├── admin/              # Admin templates (dashboard, products, orders, etc.)
    ├── auth/               # Authentication templates (login, register, password reset)
    ├── delivery/           # Delivery personnel dashboard
    ├── layout/             # Base templates, 404/500 error pages
    └── shop/               # Shop templates (index, products, cart, checkout, etc.)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- (Optional) A [Razorpay](https://razorpay.com/) merchant account for payment integration
- (Optional) A Gmail account with App Password for email features

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/RCB-Cloths-Brand.git
   cd RCB-Cloths-Brand
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-login flask-migrate apscheduler python-dotenv razorpay xhtml2pdf
   ```

4. **Create a `.env` file** in the project root (optional but recommended):
   ```env
   SECRET_KEY=your-secret-key-here
   RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
   RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET
   RAZORPAY_WEBHOOK_SECRET=your_custom_webhook_secret_123
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_gmail_app_password
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open the app**
   - The app automatically opens at `http://127.0.0.1:5018/`
   - **Default Admin Credentials**: Username: `admin`, Password: `admin123`

---

## 🔑 Default Accounts

| Role | Username | Password | Notes |
|------|----------|----------|-------|
| **Admin** | `admin` | `admin123` | Created automatically on first run |
| **Customer** | Register via `/register` | User-defined | |
| **Delivery** | Added via admin panel | Default: phone number | Login at `/login` with role "Delivery" |

---

## 🧭 Key Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage (arena landing) |
| `/products` | Product listing with filters, search, sorting, pagination |
| `/product/<id>` | Product detail with reviews |
| `/cart` | Shopping cart |
| `/checkout` | Checkout page |
| `/login` | Multi-role login (Customer / Admin / Delivery) |
| `/register` | Customer registration |
| `/profile` | User profile with order history & wallet |
| `/track` | Public order tracking |
| `/membership` | The Bold Club membership tiers |
| `/admin/dashboard` | Admin command center |
| `/admin/products` | Manage inventory |
| `/admin/orders` | Manage orders |
| `/admin/returns` | Process returns |
| `/delivery/dashboard` | Delivery personnel portal |

---

## 🏛️ Database Models

| Model | Key Fields |
|-------|-----------|
| **User** | username, email, password_hash, wallet_balance, loyalty_points, membership_tier (computed) |
| **Product** | name, description, price, stock, image, category, low_stock_threshold, is_authentic, is_exclusive |
| **Category** | name, description |
| **Cart** | user_id, product_id, quantity, custom_name, custom_number |
| **Order** | user_id, total_amount, status, tracking_id, payment_method, razorpay_order_id, razorpay_payment_id, delivery_person_id |
| **OrderItem** | order_id, product_id, quantity, price, custom_name, custom_number |
| **DeliveryPerson** | name, phone, email, vehicle_number, status, password_hash |
| **Notification** | user_id, title, message, is_read |
| **Feedback** | user_id, rating, order_number, message, contact_requested, is_resolved |
| **ReturnRequest** | order_id, user_id, reason, status, refund_amount |
| **Review** | product_id, user_id, rating (1-5), comment |
| **WalletTransaction** | user_id, amount, transaction_type, description |

---

## 📈 Business Logic Highlights

### Revenue & Profit Calculation
- **Total Value**: `subtotal + 10% tax + ₹5 delivery fee` (free delivery for orders > ₹50)
- **Estimated Profit**: `total_value × 15% - ₹40` (delivery person payout)
- Only counts for `delivered` orders

### Delivery Person Earnings
- **Flat fee**: ₹40 per successful delivery
- Total earnings calculated on the dashboard

### Membership Tiers
- Points awarded per order; tiers unlock exclusive content and perks
- Computed dynamically via the `User.membership_tier` property

### Trust Algorithm (Returns)
- Users with ≥ 3 successful orders get **instant wallet refunds** on return pickup
- New users must wait for warehouse inspection

---

## 🧪 Development Notes

### Database Migrations
The app runs **fallback programmatic migrations** on startup via raw SQL `ALTER TABLE` commands wrapped in try/except blocks. This is safe for development but for production, use Flask-Migrate:
```bash
flask db init
flask db migrate -m "Migration message"
flask db upgrade
```

### Background Scheduler
- APScheduler runs automatically when `app.py` starts
- Cleans up abandoned `payment_pending` orders every hour
- Orders older than 24 hours with status `payment_pending` are deleted

### Auto Open Browser
The app uses a 1-second timer to automatically open Chrome (or default browser) at startup. This is suppressed when the Flask reloader restarts.

---

## 🎯 Roadmap & Future Enhancements

From the project planning notes (`requirement.txt`):

1. ✅ **Product Pagination** — Implemented via SQLAlchemy `.paginate()` (12 per page)
2. ✅ **Delivery Dashboard** — Full delivery portal with login
3. ✅ **Abandoned Order Cleanup** — APScheduler background task
4. ✅ **Product Reviews & Ratings** — Review model with rating system
5. ✅ **Razorpay Refunds** — Automated refunds via API
6. ✅ **Professional Migrations** — Flask-Migrate integrated
7. 🔜 **Email Order Confirmations** — Partially implemented (in code, requires SMTP config)
8. 🔜 **Luxury Brand Story Section** — Concept designed, needing implementation
9. 🔜 **Cinematic Motion System** — Parallax, staggered reveals, floating blobs
10. 🔜 **Premium Loading Experience** — SVG lion animation, skeleton loaders
11. 🔜 **360° Product Rotation** — Three.js or custom JS viewer
12. 🔜 **Seasonal Campaign System** — CSS variable theming engine

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

This project is for educational and demonstration purposes.

---

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) and the amazing Python ecosystem
- Payments powered by [Razorpay](https://razorpay.com/)
- Icons by [Font Awesome](https://fontawesome.com/)
- Charts by [Chart.js](https://www.chartjs.org/)
- UI framework by [Bootstrap](https://getbootstrap.com/)

---

> **"Wear the Game. Enter the Arena."** 🏟️🔥
