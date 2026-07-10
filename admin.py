from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import razorpay
import functools
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

from extensions import db
from models import Product, Category, Order, User, DeliveryPerson, Notification, OrderItem, Feedback, ReturnRequest, Cart, WalletTransaction
from sqlalchemy import func

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/')
@login_required
@admin_required
def admin_home():
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # Calculate Earnings and Profit using true order values (ignoring wallet deductions for revenue stats)
    valid_orders = Order.query.filter(Order.status != 'cancelled').all()
    total_earnings_raw = sum(order.total_value for order in valid_orders)
    total_profit_raw = sum(order.estimated_profit for order in valid_orders)
    
    # Formatting for display
    total_earnings_fmt = f"₹{total_earnings_raw:,.2f}"
    total_profit_fmt = f"₹{total_profit_raw:,.2f}"
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(5).all()
    
    # Track pending human support requests
    pending_support = Feedback.query.filter_by(contact_requested=True).count()
    
    # Track pending return requests
    pending_returns = ReturnRequest.query.filter_by(status='pending').count()
    
    # Calculate Top Selling Products
    top_products_query = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem).group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(3).all()
    
    max_sold = top_products_query[0].total_sold if top_products_query else 1
    top_products = [
        {
            'name': p.name,
            'sold': p.total_sold,
            'percentage': (p.total_sold / max_sold) * 100 if max_sold > 0 else 0
        }
        for p in top_products_query
    ]
    
    # Calculate Earning History based on recent delivered orders
    earning_history_orders = Order.query.filter_by(status='delivered').order_by(Order.created_at.desc()).limit(10).all()
    earning_history = []
    for order in earning_history_orders:
        earning_history.append({
            'id': order.id,
            'date': order.created_at,
            'revenue': order.total_value,
            'profit': order.estimated_profit,
            'delivery_person': order.delivery_person.name if order.delivery_person else 'Unknown'
        })

    # Aggregate chart data by time period for the analytics graph
    all_delivered = Order.query.filter_by(status='delivered').order_by(Order.created_at.asc()).all()
    
    # Daily aggregation (last 14 days)
    daily_data = {}
    for order in all_delivered:
        day_key = order.created_at.strftime('%b %d')
        if day_key not in daily_data:
            daily_data[day_key] = {'revenue': 0, 'profit': 0, 'orders': 0}
        daily_data[day_key]['revenue'] += order.total_value
        daily_data[day_key]['profit'] += order.estimated_profit
        daily_data[day_key]['orders'] += 1
    daily_labels = list(daily_data.keys())[-14:]
    daily_revenue = [round(daily_data[k]['revenue'], 2) for k in daily_labels]
    daily_profit = [round(daily_data[k]['profit'], 2) for k in daily_labels]
    daily_orders = [daily_data[k]['orders'] for k in daily_labels]

    # Weekly aggregation (last 8 weeks)
    weekly_data = {}
    for order in all_delivered:
        # Get week start (Monday)
        week_start = order.created_at - timedelta(days=order.created_at.weekday())
        week_key = week_start.strftime('%b %d')
        if week_key not in weekly_data:
            weekly_data[week_key] = {'revenue': 0, 'profit': 0, 'orders': 0}
        weekly_data[week_key]['revenue'] += order.total_value
        weekly_data[week_key]['profit'] += order.estimated_profit
        weekly_data[week_key]['orders'] += 1
    weekly_labels = list(weekly_data.keys())[-8:]
    weekly_revenue = [round(weekly_data[k]['revenue'], 2) for k in weekly_labels]
    weekly_profit = [round(weekly_data[k]['profit'], 2) for k in weekly_labels]
    weekly_orders = [weekly_data[k]['orders'] for k in weekly_labels]

    # Monthly aggregation (last 6 months)
    monthly_data = {}
    for order in all_delivered:
        month_key = order.created_at.strftime('%b %Y')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'revenue': 0, 'profit': 0, 'orders': 0}
        monthly_data[month_key]['revenue'] += order.total_value
        monthly_data[month_key]['profit'] += order.estimated_profit
        monthly_data[month_key]['orders'] += 1
    monthly_labels = list(monthly_data.keys())[-6:]
    monthly_revenue = [round(monthly_data[k]['revenue'], 2) for k in monthly_labels]
    monthly_profit = [round(monthly_data[k]['profit'], 2) for k in monthly_labels]
    monthly_orders = [monthly_data[k]['orders'] for k in monthly_labels]
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         recent_users=recent_users,
                         top_products=top_products,
                         pending_support=pending_support,
                         pending_returns=pending_returns,
                         total_earnings=total_earnings_fmt,
                         total_profit=total_profit_fmt,
                         total_earnings_raw=total_earnings_raw,
                         total_profit_raw=total_profit_raw,
                         earning_history=earning_history,
                         chart_daily_labels=daily_labels,
                         chart_daily_revenue=daily_revenue,
                         chart_daily_profit=daily_profit,
                         chart_daily_orders=daily_orders,
                         chart_weekly_labels=weekly_labels,
                         chart_weekly_revenue=weekly_revenue,
                         chart_weekly_profit=weekly_profit,
                         chart_weekly_orders=weekly_orders,
                         chart_monthly_labels=monthly_labels,
                         chart_monthly_revenue=monthly_revenue,
                         chart_monthly_profit=monthly_profit,
                         chart_monthly_orders=monthly_orders)

@admin_bp.route('/products')
@login_required
@admin_required
def manage_products():
    page = request.args.get('page', 1, type=int)
    # Paginate admin products (10 per page) to ensure fast loading
    pagination = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/manage_product.html', pagination=pagination)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Product name is required!', 'danger')
            return redirect(url_for('admin.add_product'))
            
        try:
            price = float(request.form.get('price', 0))
        except (ValueError, TypeError):
            price = 0.0
            
        try:
            stock = int(request.form.get('stock', 0))
        except (ValueError, TypeError):
            stock = 0
            
        try:
            threshold = int(request.form.get('low_stock_threshold', 5))
        except (ValueError, TypeError):
            threshold = 5

        category = request.form.get('category')
        
        try:
            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                low_stock_threshold=threshold
            )
            
            # Handle image upload or URL safely
            image_url = request.form.get('image_url')
            if 'image' in request.files and request.files['image'].filename:
                file = request.files['image']
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    product.image = filename
                else:
                    flash('Invalid image format! Please use PNG, JPG, JPEG, or GIF.', 'danger')
                    return redirect(url_for('admin.add_product'))
            elif image_url:
                product.image = image_url
            
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.manage_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the product: {str(e)}', 'danger')
            return redirect(url_for('admin.add_product'))
    
    return render_template('admin/add_product.html', categories=categories)

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        if not product.name:
            flash('Product name is required!', 'danger')
            return redirect(url_for('admin.edit_product', id=id))
            
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        
        try:
            product.price = float(request.form.get('price', 0))
        except (ValueError, TypeError):
            product.price = 0.0
            
        try:
            product.stock = int(request.form.get('stock', 0))
        except (ValueError, TypeError):
            product.stock = 0
            
        try:
            product.low_stock_threshold = int(request.form.get('low_stock_threshold', 5))
        except (ValueError, TypeError):
            pass
            
        # Trigger Low Stock Alert on manual edit
        if product.stock <= product.low_stock_threshold:
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                alert = Notification(
                    user_id=admin.id,
                    title="⚠️ Stock Alert (Manual Edit)",
                    message=f"Product '{product.name}' updated. Stock is now {product.stock}."
                )
                db.session.add(alert)

        try:
            image_url = request.form.get('image_url')
            # Handle image upload or URL safely
            if 'image' in request.files and request.files['image'].filename:
                file = request.files['image']
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    product.image = filename
                else:
                    flash('Invalid image format! Please use PNG, JPG, JPEG, or GIF.', 'danger')
                    return redirect(url_for('admin.edit_product', id=id))
            elif image_url:
                product.image = image_url
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.manage_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the product: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_product', id=id))
    
    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin_bp.route('/products/delete/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    if OrderItem.query.filter_by(product_id=id).first():
        flash('Cannot delete product because it is part of an existing order.', 'danger')
        return redirect(url_for('admin.manage_products'))
        
    Cart.query.filter_by(product_id=id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.manage_products'))

@admin_bp.route('/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.query.all()
    return render_template('admin/prod_category.html', categories=categories)

@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if Category.query.filter_by(name=name).first():
        flash('Category already exists!', 'danger')
    else:
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/categories/delete/<int:id>')
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    if Product.query.filter_by(category=category.name).first():
        flash('Cannot delete category because it contains products.', 'danger')
        return redirect(url_for('admin.manage_categories'))
        
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    delivery_persons = DeliveryPerson.query.all()
    return render_template('admin/order_list.html', pagination=pagination, delivery_persons=delivery_persons)

@admin_bp.route('/orders/update-status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    
    order.status = status
    db.session.commit()
    flash(f'Order status updated to {status}!', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/orders/assign-delivery/<int:id>', methods=['POST'])
@login_required
@admin_required
def assign_delivery_person(id):
    order = Order.query.get_or_404(id)
    dp_id = request.form.get('delivery_person_id')
    if dp_id:
        order.delivery_person_id = int(dp_id)
        db.session.commit()
        flash('Delivery person assigned successfully!', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/returns')
@login_required
@admin_required
def manage_returns():
    """Dedicated page for managing all return requests."""
    page = request.args.get('page', 1, type=int)
    
    # Filter by status if provided
    status_filter = request.args.get('status')
    query = ReturnRequest.query.order_by(ReturnRequest.created_at.desc())
    
    if status_filter:
        query = query.filter(ReturnRequest.status == status_filter)
    
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    
    # Counts for each status
    status_counts = {
        'pending': ReturnRequest.query.filter_by(status='pending').count(),
        'picked_up': ReturnRequest.query.filter_by(status='picked_up').count(),
        'refunded': ReturnRequest.query.filter_by(status='refunded').count(),
        'rejected': ReturnRequest.query.filter_by(status='rejected').count(),
    }
    
    return render_template('admin/return_requests.html',
                           pagination=pagination,
                           status_counts=status_counts,
                           active_filter=status_filter)

@admin_bp.route('/returns/confirm-pickup/<int:return_id>', methods=['POST'])
@login_required
@admin_required
def confirm_return_pickup(return_id):
    # This simulates a delivery driver scanning the return package at the customer's door
    return_req = ReturnRequest.query.get_or_404(return_id)
    user = return_req.user
    
    # Mark as picked up
    return_req.status = 'picked_up'
    
    # THE TRUST ALGORITHM:
    # If the user has >= 3 successful past orders, they get an INSTANT wallet refund
    if user.successful_orders_count >= 3:
        user.wallet_balance += return_req.refund_amount
        return_req.status = 'refunded'
        
        db.session.add(WalletTransaction(
            user_id=user.id,
            amount=return_req.refund_amount,
            transaction_type='refund',
            description=f'Instant refund for return of Order #{return_req.order_id}'
        ))
        
        # Notify user of the instant refund
        notification = Notification(
            user_id=user.id,
            title='Instant Refund Issued! 💸',
            message=f'We picked up your return and instantly credited ₹{return_req.refund_amount} to your Store Wallet!'
        )
        db.session.add(notification)
        flash(f'Instant refund of ₹{return_req.refund_amount} issued to {user.username}!', 'success')
    else:
        flash('Item marked as picked up. Refund will be processed after warehouse inspection.', 'info')
        
    db.session.commit()
    return redirect(url_for('admin.manage_returns'))

@admin_bp.route('/returns/process-refund/<int:return_id>', methods=['POST'])
@login_required
@admin_required
def process_return_refund(return_id):
    return_req = ReturnRequest.query.get_or_404(return_id)
    if return_req.status != 'picked_up':
        flash('Return must be picked up before processing the refund.', 'danger')
        return redirect(url_for('admin.orders'))
        
    order = return_req.order
    user = return_req.user
    refund_method = "Store Wallet"

    # Check if we should refund via Razorpay or Wallet
    if order.payment_method == 'online' and order.razorpay_payment_id:
        try:
            razorpay_client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
            # Razorpay expects amount in paise
            razorpay_client.payment.refund(order.razorpay_payment_id, {
                "amount": int(return_req.refund_amount * 100)
            })
            refund_method = "Original Payment Method (Bank/UPI)"
        except Exception as e:
            print(f"Razorpay Refund Error: {e}")
            # Fallback to wallet if API fails
            user.wallet_balance += return_req.refund_amount
    else:
        user.wallet_balance += return_req.refund_amount

    return_req.status = 'refunded'
    
    db.session.add(WalletTransaction(
        user_id=user.id,
        amount=return_req.refund_amount,
        transaction_type='refund',
        description=f'Refund for return of Order #{return_req.order_id}'
    ))
    
    notification = Notification(
        user_id=user.id,
        title='Return Refund Processed 💸',
        message=f'Your refund of ₹{return_req.refund_amount} for Order #{return_req.order_id} has been processed via {refund_method}.'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Refund of ₹{return_req.refund_amount} processed for {user.username}.', 'success')
    return redirect(url_for('admin.manage_returns'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/customer_list.html', users=users)

@admin_bp.route('/delivery-persons')
@login_required
@admin_required
def delivery_persons():
    delivery_persons = DeliveryPerson.query.all()
    # Updated to match the exact spelling of your HTML file
    return render_template('admin/develivery_person.html', delivery_persons=delivery_persons)

@admin_bp.route('/delivery-persons/<int:id>')
@login_required
@admin_required
def dp_detailed(id):
    dp = DeliveryPerson.query.get_or_404(id)
    
    # Pre-calculate statistics and filter orders
    all_orders = dp.orders
    
    active_statuses = ['pending', 'shipped', 'out_for_delivery', 'processing']
    
    active_orders = [o for o in all_orders if o.status in active_statuses]
    completed_orders = [o for o in all_orders if o.status == 'delivered']
    
    # Calculate lifetime earnings for this specific delivery person
    FLAT_FEE_PER_DELIVERY = 40.0
    total_earnings = len(completed_orders) * FLAT_FEE_PER_DELIVERY
    
    stats = {
        'total': len(all_orders),
        'in_progress': len(active_orders),
        'completed': len(completed_orders),
        'total_earnings': total_earnings
    }
    return render_template('admin/dp_detailed.html', 
                           dp=dp, 
                           stats=stats,
                           active_orders=active_orders,
                           completed_orders=completed_orders)

@admin_bp.route('/delivery-persons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_delivery_person():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        vehicle_number = request.form.get('vehicle_number')
        
        dp = DeliveryPerson(
            name=name,
            phone=phone,
            email=email,
            vehicle_number=vehicle_number
        )
        dp.set_password(phone or '123456') # Default password is their phone number
        db.session.add(dp)
        db.session.commit()
        flash('Delivery person added successfully!', 'success')
        return redirect(url_for('admin.delivery_persons'))
        
    return render_template('admin/add_delivery_person.html')

@admin_bp.route('/delivery-persons/reset-password/<int:id>', methods=['POST'])
@login_required
@admin_required
def reset_dp_password(id):
    dp = DeliveryPerson.query.get_or_404(id)
    # Generate a simple, temporary password (e.g., phone number)
    new_password = dp.phone or f"password{dp.id}"
    dp.set_password(new_password)
    db.session.commit()
    flash(f"Password for {dp.name} has been reset to '{new_password}'.", 'success')
    return redirect(url_for('admin.dp_detailed', id=id))

@admin_bp.route('/delivery-persons/delete/<int:id>')
@login_required
@admin_required
def delete_delivery_person(id):
    dp = DeliveryPerson.query.get_or_404(id)
    db.session.delete(dp)
    db.session.commit()
    flash('Delivery person deleted successfully!', 'success')
    return redirect(url_for('admin.delivery_persons'))

@admin_bp.route('/send-notification', methods=['GET', 'POST'])
@login_required
@admin_required
def send_notification():
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        user_id = request.form.get('user_id')
        
        notification = Notification(
            user_id=user_id if user_id else None,
            title=title,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Notification sent successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(10).all()
    return render_template('admin/notification.html', users=users, recent_notifications=recent_notifications)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # Handle Profile Form Submission
        if 'username' in request.form and 'email' in request.form:
            if request.form.get('username'):
                current_user.username = request.form.get('username')
            if request.form.get('email'):
                current_user.email = request.form.get('email')
            current_user.phone = request.form.get('phone')
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
        # Handle Security (Password) Form Submission
        elif 'new_password' in request.form:
            current_pwd = request.form.get('current_password')
            new_pwd = request.form.get('new_password')
            confirm_pwd = request.form.get('confirm_password')
            
            if not current_user.check_password(current_pwd):
                flash('Incorrect current password.', 'danger')
            elif new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_pwd)
                db.session.commit()
                flash('Password changed successfully!', 'success')
    
    return render_template('admin/setting.html')

@admin_bp.route('/feedback')
@login_required
@admin_required
def feedback():
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin/feedback_list.html', feedbacks=feedbacks)

@admin_bp.route('/feedback/resolve/<int:id>')
@login_required
@admin_required
def resolve_feedback(id):
    item = Feedback.query.get_or_404(id)
    item.is_resolved = True
    db.session.commit()
    flash('Support ticket marked as resolved.', 'success')
    return redirect(url_for('admin.feedback'))