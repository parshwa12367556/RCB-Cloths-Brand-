from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
import random
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import SignatureExpired, BadSignature
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import razorpay
from io import BytesIO
from xhtml2pdf import pisa

customer_bp = Blueprint('customer', __name__)

from extensions import db
from models import User, Cart, Order, OrderItem, Product, Notification, Feedback, ReturnRequest, DeliveryPerson, Review, WalletTransaction


@customer_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('index'))
        
    # Check if a delivery person is already logged in
    if 'dp_id' in session:
        return redirect(url_for('delivery.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'customer')
        
        if role == 'admin':
            user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
            if user and user.is_admin and user.check_password(password):
                login_user(user)
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
            flash('Invalid admin credentials!', 'danger')
            
        elif role == 'delivery':
            dp = DeliveryPerson.query.filter((DeliveryPerson.email == username) | (DeliveryPerson.phone == username)).first()
            if dp and dp.check_password(password):
                session['dp_id'] = dp.id
                flash(f'Welcome to the Delivery Portal, {dp.name}!', 'success')
                return redirect(url_for('delivery.dashboard'))
            flash('Invalid delivery personnel credentials!', 'danger')
            
        else: # customer
            user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
            if user and not user.is_admin and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            flash('Invalid customer credentials!', 'danger')
    
    return render_template('auth/login.html')

@customer_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        if not username or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('customer.register'))
            
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('customer.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('customer.register'))
    
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('customer.register'))
        
        user = User(username=username, email=email, phone=phone, address=address)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('customer.login'))
    
    return render_template('auth/register.html')

def send_reset_email(user, token):
    sender_email = current_app.config.get('MAIL_USERNAME')
    sender_password = current_app.config.get('MAIL_PASSWORD')
    
    reset_url = url_for('customer.reset_password', token=token, _external=True)
    
    msg = MIMEMultipart()
    msg['Subject'] = 'ARENA Sports Luxury - Password Reset Request'
    msg['From'] = sender_email
    msg['To'] = user.email
    
    body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email and no changes will be made.
'''
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_order_confirmation_email(user, order):
    sender_email = current_app.config.get('MAIL_USERNAME')
    sender_password = current_app.config.get('MAIL_PASSWORD')
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'ARENA Sports Luxury - Order Confirmation #{order.tracking_id}'
    msg['From'] = sender_email
    msg['To'] = user.email
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #D90429;">Thank you for your order, {user.username}!</h2>
        <p>Your order <strong>#{order.tracking_id}</strong> has been successfully placed.</p>
        <h3 style="border-bottom: 2px solid #D90429; padding-bottom: 5px;">Order Summary</h3>
        <ul>
    """
    for item in order.items:
        html_content += f"<li>{item.product.name} (x{item.quantity}) - ₹{item.price * item.quantity:.2f}</li>"
        
    html_content += f"""
        </ul>
        <p><strong>Total Paid:</strong> ₹{order.total_amount:.2f}</p>
        <p>We will notify you once your order is shipped.</p>
        <p>Best Regards,<br><strong>ARENA Sports Luxury Team</strong></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")

@customer_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            send_reset_email(user, token)
        
        # We use a vague success message to prevent user enumeration attacks
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('customer.login'))
        
    return render_template('auth/forget_password.html')

@customer_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Token expires after 3600 seconds (1 hour)
        email = s.loads(token, salt='password-reset-salt', max_age=3600) 
    except (SignatureExpired, BadSignature):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('customer.forgot_password'))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or password != confirm_password:
            flash('Passwords do not match or are empty!', 'danger')
            return redirect(url_for('customer.reset_password', token=token))
            
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('customer.login'))
        
    return render_template('auth/reset_password.html', token=token)

@customer_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    # Clear delivery person session if it exists
    session.pop('dp_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@customer_bp.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    # Fetch the last 10 wallet transactions for the user
    wallet_history = WalletTransaction.query.filter_by(user_id=current_user.id).order_by(WalletTransaction.created_at.desc()).limit(10).all()
    return render_template('shop/profile.html', orders=orders, wallet_history=wallet_history)

@customer_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    new_username = request.form.get('username')
    new_email = request.form.get('email')

    # Check for unique constraints
    if new_username != current_user.username:
        if User.query.filter_by(username=new_username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('customer.profile'))
    if new_email != current_user.email:
        if User.query.filter_by(email=new_email).first():
            flash('Email already in use.', 'danger')
            return redirect(url_for('customer.profile'))

    current_user.username = new_username
    current_user.email = new_email
    current_user.phone = request.form.get('phone')
    current_user.address = request.form.get('address')
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('customer.profile'))

@customer_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_pwd = request.form.get('current_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('confirm_password')
    
    if not current_user.check_password(current_pwd):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('customer.profile'))
        
    if new_pwd != confirm_pwd:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('customer.profile'))
        
    current_user.set_password(new_pwd)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('customer.profile'))

@customer_bp.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    custom_name = request.form.get('custom_name')
    custom_number = request.form.get('custom_number')

    # Check if product already in cart
    # We only group items if they have the SAME customization
    cart_item = Cart.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id,
        custom_name=custom_name,
        custom_number=custom_number
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity, custom_name=custom_name, custom_number=custom_number)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('customer.cart'))

@customer_bp.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # Calculate Free Delivery Progress
    FREE_DELIVERY_THRESHOLD = 50.0
    amount_needed = max(0, FREE_DELIVERY_THRESHOLD - total)
    progress_percentage = min(100, (total / FREE_DELIVERY_THRESHOLD) * 100)
    
    return render_template('shop/cart.html', cart_items=cart_items, total=total, amount_needed=amount_needed, progress_percentage=progress_percentage)

@customer_bp.route('/update-cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = Cart.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    quantity = int(request.form.get('quantity', 0))
    if quantity > 0:
        cart_item.quantity = quantity
        db.session.commit()
    else:
        db.session.delete(cart_item)
        db.session.commit()
    
    flash('Cart updated successfully!', 'success')
    return redirect(url_for('customer.cart'))

@customer_bp.route('/remove-from-cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = Cart.query.get_or_404(item_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart!', 'success')
    return redirect(url_for('customer.cart'))

@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('product_bp.products'))
    
    # Define constants for fees and taxes
    TAX_RATE = 0.10
    
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    DELIVERY_FEE = 0.00 if subtotal > 50 else 5.00
    tax_amount = subtotal * TAX_RATE
    final_total = subtotal + tax_amount + DELIVERY_FEE
    
    if request.method == 'POST':
        # Generate a unique Tracking ID
        tracking_id = f"TRK-{random.randint(10000000, 99999999)}"

        amount_to_pay = final_total
        if current_user.wallet_balance > 0:
            if current_user.wallet_balance >= amount_to_pay:
                amount_to_pay = 0
            else:
                amount_to_pay -= current_user.wallet_balance

        # Get payment method
        payment_method = request.form.get('payment', 'cod')

        # Create order
        order = Order(
            user_id=current_user.id,
            total_amount=amount_to_pay, # Only charge what wasn't covered by wallet
            shipping_address=request.form.get('address'),
            phone=request.form.get('phone'),
            status='payment_pending',
            tracking_id=tracking_id,
            payment_method=payment_method
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                custom_name=cart_item.custom_name,
                custom_number=cart_item.custom_number
            )
            db.session.add(order_item)
            
            # Low Stock Alert Check
            if cart_item.product.stock <= cart_item.product.low_stock_threshold:
                admin_users = User.query.filter_by(is_admin=True).all()
                for admin in admin_users:
                    alert = Notification(
                        user_id=admin.id,
                        title="⚠️ Low Stock Alert",
                        message=f"Product '{cart_item.product.name}' has only {cart_item.product.stock} items left."
                    )
                    db.session.add(alert)
        
        # Clear cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        
        # Increase trust score for successful order
        current_user.successful_orders_count += 1

        db.session.commit()
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title='Order Placed',
            message=f'Your order #{order.id} has been placed successfully!'
        )
        db.session.add(notification)
        db.session.commit()
        
        # Send Confirmation Email
        send_order_confirmation_email(current_user, order)
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('customer.order_confirmation', order_id=order.id))
    
    return render_template('shop/checkout_premium.html', 
                           cart_items=cart_items, 
                           subtotal=subtotal,
                           tax=tax_amount,
                           delivery_fee=DELIVERY_FEE,
                           total=final_total)

@customer_bp.route('/orders')
@login_required
def orders():
    # The profile page handles displaying the order history for the user
    return redirect(url_for('customer.profile'))

@customer_bp.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))
    return render_template('shop/order_confirmation.html', order=order)

def fulfill_order(order):
    """Helper to handle post-payment order fulfillment logic."""
    # Atomic update to prevent double-fulfillment (e.g., race conditions 
    # between webhook and redirect, or page refreshes).
    rows_updated = Order.query.filter_by(id=order.id, status='payment_pending').update({'status': 'pending'})

    if rows_updated == 0:
        # Order has already been processed or is not in a payable state
        return

    # Sync the local order object with the database state for subsequent logic
    db.session.refresh(order)
    
    # Deduct Wallet (Calculated by the difference between order actual value and the razorpay amount paid)
    subtotal = sum(item.price * item.quantity for item in order.items)
    actual_total = subtotal + (subtotal * 0.10) + (0.00 if subtotal > 50 else 5.00)
    wallet_used = actual_total - order.total_amount
    
    user = User.query.get(order.user_id)
    if wallet_used > 0 and user.wallet_balance >= wallet_used:
        user.wallet_balance -= wallet_used
        # Log wallet usage for online payment
        db.session.add(WalletTransaction(
            user_id=user.id,
            amount=-wallet_used,
            transaction_type='purchase',
            description=f'Used for Order #{order.tracking_id}'
        ))
    elif wallet_used > 0:
        user.wallet_balance = 0
        
    for item in order.items:
        # Double check stock before final deduction
        if item.product.stock >= item.quantity:
            item.product.stock -= item.quantity
        else:
            # In a real system, you would trigger a support ticket here
            # for an "Over-sold" error.
            item.product.stock = 0
        
        # Trigger Low Stock Alert
        if item.product.stock <= item.product.low_stock_threshold:
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                db.session.add(Notification(
                    user_id=admin.id,
                    title="⚠️ Low Stock Alert",
                    message=f"Product '{item.product.name}' is low ({item.product.stock} left)."
                ))
        Cart.query.filter_by(user_id=order.user_id).delete()
    user.successful_orders_count += 1
    
    # Create notification
    notification = Notification(
        user_id=user.id,
        title='Order Placed',
        message=f'Your order #{order.id} has been placed successfully!'
    )
    db.session.add(notification)
    
    db.session.commit()
    send_order_confirmation_email(user, order)
    
    # Optional: Log for debug
    current_app.logger.info(f"Order {order.id} fulfilled successfully.")


@customer_bp.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('customer.orders'))
        
    if order.status in ['pending', 'payment_pending']:
        # Calculate the actual total value of the order
        subtotal = sum(item.price * item.quantity for item in order.items)
        actual_total = subtotal + (subtotal * 0.10) + (0.00 if subtotal > 50 else 5.00)
        wallet_used = actual_total - order.total_amount
        
        wallet_refund = 0
        online_refund = 0
        
        if order.status == 'payment_pending':
            wallet_refund = wallet_used
        elif order.status == 'pending' and order.payment_method == 'online':
            online_refund = order.total_amount # Gateway amount
            wallet_refund = wallet_used
        elif order.status == 'pending' and order.payment_method == 'cod':
            wallet_refund = wallet_used
            
        if wallet_refund > 0:
            current_user.wallet_balance += wallet_refund
            wallet_log = WalletTransaction(
                user_id=current_user.id,
                amount=wallet_refund,
                transaction_type='cancellation',
                description=f'Refund for cancelled Order #{order.id}'
            )
            db.session.add(wallet_log)
            
        refund_message = f'₹{wallet_refund:.2f} has been refunded to your Store Wallet.'
            
        # Initiate Razorpay Refund
        if online_refund > 0 and order.razorpay_payment_id:
            try:
                razorpay_client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
                razorpay_client.payment.refund(order.razorpay_payment_id, {
                    "amount": int(online_refund * 100) # Amount in paise
                })
                refund_message = f'₹{online_refund:.2f} refunded to your bank account'
                if wallet_refund > 0:
                    refund_message += f' and ₹{wallet_refund:.2f} to your Store Wallet.'
            except Exception as e:
                print(f"Razorpay Refund Error: {e}")
                # Fallback to wallet if gateway fails
                current_user.wallet_balance += online_refund
                refund_message = f'Refund of ₹{(online_refund + wallet_refund):.2f} added to your Store Wallet (Gateway delay).'
            
        # Restore stock
        for item in order.items:
            item.product.stock += item.quantity
            
        order.status = 'cancelled'
        
        notification = Notification(
            user_id=current_user.id,
            title='Order Cancelled',
            message=f'Your order #{order.id} has been cancelled. {refund_message}'
        )
        db.session.add(notification)
        db.session.commit()
        flash(f'Order cancelled successfully! {refund_message}', 'success')
    else:
        flash('This order cannot be cancelled.', 'danger')
        
    return redirect(url_for('customer.orders'))

@customer_bp.route('/order/return/<int:order_id>', methods=['POST'])
@login_required
def return_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('customer.orders'))
        
    if order.status == 'delivered':
        reason = request.form.get('reason')
        if not reason:
            flash('Please provide a reason for the return.', 'danger')
            return redirect(url_for('customer.orders'))
            
        if ReturnRequest.query.filter_by(order_id=order.id).first():
            flash('A return request for this order already exists.', 'warning')
            return redirect(url_for('customer.orders'))
            
        # Calculate refund amount
        subtotal = sum(item.price * item.quantity for item in order.items)
        actual_total = subtotal + (subtotal * 0.10) + (0.00 if subtotal > 50 else 5.00)
        
        return_req = ReturnRequest(
            order_id=order.id,
            user_id=current_user.id,
            reason=reason,
            refund_amount=actual_total
        )
        db.session.add(return_req)
        
        order.status = 'return_requested'
        
        notification = Notification(
            user_id=current_user.id,
            title='Return Requested',
            message=f'Your return request for order #{order.id} has been received and is pending approval.'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Return request submitted successfully.', 'success')
    else:
        flash('Only delivered orders can be returned.', 'danger')
        
    return redirect(url_for('customer.orders'))

@customer_bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('shop/shop_notifaction.html', notifications=notifications)

@customer_bp.route('/mark-notification-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('customer.notifications'))

@customer_bp.route('/mark-all-notifications-read')
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('customer.notifications'))

@customer_bp.route('/about')
def about():
    return render_template('shop/about.html')

@customer_bp.route('/membership')
def membership():
    # In a real app, you'd pass user tier data here
    return render_template('shop/membership.html')

@customer_bp.route('/contact')
def contact():
    return render_template('shop/contact.html')

@customer_bp.route('/track', methods=['GET', 'POST'])
def track_order():
    tracking_id = request.args.get('id') or request.form.get('tracking_id')
    order = None
    
    if tracking_id:
        order = Order.query.filter_by(tracking_id=tracking_id).first()
        if not order:
            flash('Invalid Tracking ID. Please check and try again.', 'danger')
            
    return render_template('shop/track.html', order=order, search_id=tracking_id)

@customer_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        rating = int(request.form.get('rating', 0))
        order_number = request.form.get('order_number')
        liked_most = request.form.get('liked_most')
        message = request.form.get('message')
        suggestions = request.form.get('suggestions')
        contact_requested = 'contact_requested' in request.form
        
        feedback_entry = Feedback(
            user_id=current_user.id,
            rating=rating,
            order_number=order_number,
            liked_most=liked_most,
            message=message,
            suggestions=suggestions,
            contact_requested=contact_requested
        )
        db.session.add(feedback_entry)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('customer.thank_you'))
    return render_template('shop/feedback.html')

@customer_bp.route('/talk-to-human', methods=['POST'])
@login_required
def talk_to_human():
    order_number = request.form.get('order_number', 'General Inquiry')
    
    # Auto-generate a high-priority support ticket
    support_request = Feedback(
        user_id=current_user.id,
        rating=0, # 0 indicates a support ticket rather than a standard review
        order_number=order_number,
        message="🚨 URGENT: Customer clicked 'Talk to a Human'. Requires immediate assistance.",
        suggestions="System auto-generated: User requested a callback/human intervention.",
        contact_requested=True
    )
    db.session.add(support_request)
    db.session.commit()
    
    flash('Support request received! A human agent will reach out to you shortly.', 'success')
    
    # Redirect back to the page they came from, or profile as a fallback
    return redirect(request.referrer or url_for('customer.profile'))

@customer_bp.route('/thank-you')
def thank_you():
    return render_template('shop/thankyou.html')

@customer_bp.route('/payment/create', methods=['POST'])
@login_required
def create_payment():
    # Initialize securely using Flask configuration
    razorpay_client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
    
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
        
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    DELIVERY_FEE = 0.00 if subtotal > 50 else 5.00
    tax_amount = subtotal * 0.10
    final_total = subtotal + tax_amount + DELIVERY_FEE
    
    amount_to_pay = final_total
    if current_user.wallet_balance > 0:
        if current_user.wallet_balance >= amount_to_pay:
            amount_to_pay = 0
        else:
            amount_to_pay -= current_user.wallet_balance
            
    if amount_to_pay <= 0:
        return jsonify({'error': 'Total is covered by wallet. Please use COD or Wallet checkout.'}), 400
        
    # Razorpay requires the amount in paise (multiply by 100)
    amount_in_paise = int(amount_to_pay * 100)
    data = { "amount": amount_in_paise, "currency": "INR", "receipt": f"arena_receipt_{current_user.id}" }
    
    # Generate the Order ID on Razorpay's servers
    payment = razorpay_client.order.create(data=data)
    
    # CREATE THE PENDING ORDER IN OUR DB
    tracking_id = f"TRK-{random.randint(10000000, 99999999)}"
    order = Order(
        user_id=current_user.id,
        total_amount=amount_to_pay,
        shipping_address=request.form.get('address'),
        phone=request.form.get('phone'),
        status='payment_pending', # Marked specifically as awaiting payment
        tracking_id=tracking_id,
        payment_method='online',
        razorpay_order_id=payment['id']
    )
    db.session.add(order)
    db.session.flush()
    
    for item in cart_items:
        db.session.add(OrderItem(
            order_id=order.id, 
            product_id=item.product_id, 
            quantity=item.quantity, 
            price=item.product.price,
            custom_name=item.custom_name,
            custom_number=item.custom_number
        ))
        
    db.session.commit()
    return jsonify(payment)

@customer_bp.route('/verify_payment', methods=['POST'])
@login_required
def verify_payment():
    # Initialize securely using Flask configuration
    razorpay_client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
    
    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')
    
    try:
        # Verify the signature to ensure the payment is authentic
        razorpay_client.utility.verify_payment_signature({
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        flash('Payment verification failed! If money was deducted, it will be refunded.', 'danger')
        return redirect(url_for('customer.checkout'))
        
    order = Order.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not order:
        flash('Order not found!', 'danger')
        return redirect(url_for('customer.checkout'))
        
    # Fulfill the order if it's currently awaiting payment
    if order.status == 'payment_pending':
        order.razorpay_payment_id = razorpay_payment_id
        fulfill_order(order)
    
    flash('Payment successful and order placed!', 'success')
    return redirect(url_for('customer.order_confirmation', order_id=order.id))

@customer_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
    webhook_signature = request.headers.get('X-Razorpay-Signature')
    
    # Initialize Razorpay Client
    razorpay_client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
    
    try:
        # Verify the webhook signature to ensure it's genuinely from Razorpay
        razorpay_client.utility.verify_webhook_signature(
            request.get_data(as_text=True),
            webhook_signature,
            webhook_secret
        )
    except razorpay.errors.SignatureVerificationError:
        return jsonify({'status': 'invalid signature'}), 400
        
    payload = request.json
    
    # Handle the successful payment event
    if payload.get('event') == 'order.paid':
        payment_entity = payload['payload']['payment']['entity']
        razorpay_order_id = payment_entity['order_id']
        razorpay_payment_id = payment_entity['id']
        
        order = Order.query.filter_by(razorpay_order_id=razorpay_order_id).first()
        if order:
            order.razorpay_payment_id = razorpay_payment_id
            fulfill_order(order)
            print(f"Webhook processed: Order {order.id} fulfillment triggered.")
            
    return jsonify({'status': 'ok'}), 200

@customer_bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def submit_review(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Verify user actually bought the product and it was delivered
    has_purchased = OrderItem.query.join(Order).filter(
        Order.user_id == current_user.id,
        Order.status == 'delivered',
        OrderItem.product_id == product_id
    ).first()
    
    if not has_purchased:
        flash('You can only review products you have purchased and received.', 'danger')
        return redirect(url_for('product_bp.product_detail', id=product_id))
        
    existing_review = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_review:
        flash('You have already reviewed this product.', 'warning')
        return redirect(url_for('product_bp.product_detail', id=product_id))
        
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '')
    
    review = Review(user_id=current_user.id, product_id=product_id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    
    flash('Thank you for your review!', 'success')
    return redirect(url_for('product_bp.product_detail', id=product_id))

@customer_bp.route('/order/invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
        
    html = render_template('shop/invoice.html', order=order)
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=pdf)
    
    if pisa_status.err:
        flash('Error generating PDF invoice.', 'danger')
        return redirect(url_for('customer.orders'))
        
    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ARENA_Invoice_ORD{order.id}.pdf'
    return response