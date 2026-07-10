from flask import Flask, render_template, session
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import webbrowser
from threading import Timer
from dotenv import load_dotenv
from flask_migrate import Migrate

from extensions import db, login_manager
from sqlalchemy import text
from models import User, Product, Category, Cart, Order, DeliveryPerson, Review

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Secure Credentials (loaded from .env)
app.config['RAZORPAY_KEY_ID'] = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_YOUR_KEY_ID')
app.config['RAZORPAY_KEY_SECRET'] = os.environ.get('RAZORPAY_KEY_SECRET', 'YOUR_KEY_SECRET')
app.config['RAZORPAY_WEBHOOK_SECRET'] = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'your_custom_webhook_secret_123')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_app_password')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)
login_manager.init_app(app)
login_manager.login_view = 'customer.login'
login_manager.login_message_category = 'info'

# Allowed extensions for image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Context processor for cart count
@app.context_processor
def cart_count_processor():
    # This needs to be imported here to avoid circular dependency at startup
    from flask_login import current_user as login_user
    from models import Notification
    
    cart_count = 0
    unread_count = 0
    wallet = 0.0
    
    if login_user.is_authenticated:
        cart_count = Cart.query.filter_by(user_id=login_user.id).count()
        unread_count = Notification.query.filter_by(user_id=login_user.id, is_read=False).count()
        wallet = login_user.wallet_balance

    return dict(
        cart_count=cart_count, 
        unread_notifications_count=unread_count, 
        current_wallet=wallet, 
        active_campaign='gold-edition',
        is_match_live=True
    )

# Main route
@app.route('/')
def index():
    products = Product.query.limit(8).all()
    categories = Category.query.all()

    # Point 8: Personalized Experience
    recently_viewed = []
    recommended = []
    
    if 'recently_viewed' in session:
        rv_ids = session['recently_viewed']
        for pid in rv_ids:
            p = db.session.get(Product, pid)
            if p:
                recently_viewed.append(p)
                
    if recently_viewed:
        # Simple recommendation: Products in the same category as the most recently viewed item
        top_cat = recently_viewed[0].category
        recommended = Product.query.filter(
            Product.category == top_cat,
            Product.id.not_in([p.id for p in recently_viewed])
        ).limit(4).all()

    # Point 18: Premium AI Features - AI Jersey Recommendation
    # Simulate an AI engine by selecting high-end jerseys or trending ones
    try:
        ai_jerseys = Product.query.filter(Product.category.ilike('Jerseys')).order_by(db.func.random()).limit(3).all()
    except Exception:
        ai_jerseys = []

    # ATHLUXE: AI Sports Stylist - Mocking outfit logic
    athluxe_outfits = Product.query.order_by(db.func.random()).limit(4).all()

    return render_template('shop/index.html', 
                         products=products, 
                         categories=categories,
                         recently_viewed=recently_viewed,
                         recommended=recommended,
                         ai_jerseys=ai_jerseys,
                         athluxe_outfits=athluxe_outfits)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('layout/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('layout/500.html'), 500

# Import and register blueprints
from admin import admin_bp
from customer import customer_bp
from product import product_bp
from delivery import delivery_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(customer_bp)
app.register_blueprint(product_bp)
app.register_blueprint(delivery_bp, url_prefix='/delivery')

def cleanup_abandoned_orders():
    """Background task to delete 'payment_pending' orders older than 24 hours."""
    with app.app_context():
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        abandoned_orders = Order.query.filter(Order.status == 'payment_pending', Order.created_at < cutoff_time).all()
        
        if abandoned_orders:
            count = len(abandoned_orders)
            for order in abandoned_orders:
                db.session.delete(order)
            db.session.commit()
            print(f"Cleanup Task: Deleted {count} abandoned 'payment_pending' order(s).")

def open_browser():
    """Utility to open Google Chrome specifically, falling back to default if needed."""
    url = 'http://127.0.0.1:5018/'
    # List of common aliases for Chrome across different Operating Systems
    chrome_aliases = ['google-chrome', 'chrome', 'google-chrome-stable', 'chromium']
    
    for alias in chrome_aliases:
        try:
            webbrowser.get(alias).open_new(url)
            return
        except webbrowser.Error:
            continue

    # Fallback to the system default browser if Chrome is not specifically registered
    webbrowser.open_new(url)

if __name__ == '__main__':
    # Initialize and start the background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_abandoned_orders, trigger="interval", hours=1)
    scheduler.start()

    with app.app_context():
        db.create_all()
        
        # Fallback Programmatic Migrations for Development (SQLite)
        # This ensures new columns exist even if CLI migrations are skipped
        for cmd in [
            'ALTER TABLE products ADD COLUMN low_stock_threshold INTEGER DEFAULT 5',
            'ALTER TABLE products ADD COLUMN is_authentic BOOLEAN DEFAULT 1',
            'ALTER TABLE products ADD COLUMN release_date DATETIME',
            'ALTER TABLE products ADD COLUMN is_exclusive BOOLEAN DEFAULT 0',
            'ALTER TABLE products ADD COLUMN updated_at DATETIME',
            'ALTER TABLE users ADD COLUMN wallet_balance FLOAT DEFAULT 0.0',
            'ALTER TABLE users ADD COLUMN loyalty_points INTEGER DEFAULT 0',
            'ALTER TABLE users ADD COLUMN successful_orders_count INTEGER DEFAULT 0',
            'ALTER TABLE orders ADD COLUMN razorpay_order_id VARCHAR(100)',
            'ALTER TABLE orders ADD COLUMN razorpay_payment_id VARCHAR(100)',
            'ALTER TABLE cart ADD COLUMN custom_name VARCHAR(50)',
            'ALTER TABLE cart ADD COLUMN custom_number INTEGER',
            'ALTER TABLE order_items ADD COLUMN custom_name VARCHAR(50)',
            'ALTER TABLE order_items ADD COLUMN custom_number INTEGER',
            'ALTER TABLE feedback ADD COLUMN is_resolved BOOLEAN DEFAULT 0'
        ]:
            try:
                db.session.execute(text(cmd))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com')
            db.session.add(admin)
            
            # Ensure admin privileges and reset password to default just in case
            admin.is_admin = True
            admin.set_password('admin123')
        
        # Add some categories
        categories = ['Football', 'Cricket', 'IPL', 'NBA', 'Kabaddi', 
                     'Formula 1', 'Esports', 'Retro Collections', 'Streetwear']
        for cat in categories:
            if not Category.query.filter_by(name=cat).first():
                db.session.add(Category(name=cat))
        
        db.session.commit()

    # We use a Timer to wait 1 second for the server to initialize before opening the browser.
    # The check for WERKZEUG_RUN_MAIN ensures the browser doesn't open twice 
    # when the Flask reloader restarts the app.
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(1, open_browser).start()

    app.run(debug=True, port=5018, host='127.0.0.1')
   