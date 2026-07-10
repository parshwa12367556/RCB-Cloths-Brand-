from flask import Blueprint, request, redirect, url_for, flash, session, render_template
import functools
from datetime import date

from extensions import db
from models import DeliveryPerson, Order, WalletTransaction

delivery_bp = Blueprint('delivery', __name__)

# ===== ROUTES =====
def dp_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'dp_id' not in session:
            flash('Please log in as delivery personnel.', 'warning')
            return redirect(url_for('customer.login'))
        return f(*args, **kwargs)
    return decorated_function

@delivery_bp.route('/dashboard')
@dp_required
def dashboard():
    dp_id = session['dp_id']
    dp = DeliveryPerson.query.get_or_404(dp_id)
    
    # Orders that need to be delivered
    active_statuses = ['shipped', 'out_for_delivery']
    active_orders = Order.query.filter(
        Order.delivery_person_id == dp_id,
        Order.status.in_(active_statuses)
    ).order_by(Order.created_at.asc()).all()
    
    # Orders that have been delivered
    completed_orders = Order.query.filter(
        Order.delivery_person_id == dp_id,
        Order.status == 'delivered'
    ).order_by(Order.created_at.desc()).limit(25).all()
    
    # Dashboard statistics - Delivery Earning Logic
    # The delivery person earns a flat fee of ₹40 for every successful delivery
    FLAT_FEE_PER_DELIVERY = 40.0
    
    total_completed = Order.query.filter(
        Order.delivery_person_id == dp_id,
        Order.status == 'delivered'
    ).count()
    
    total_earnings = total_completed * FLAT_FEE_PER_DELIVERY
    
    stats = {
        'active_count': len(active_orders),
        'completed_today': Order.query.filter(Order.delivery_person_id == dp_id, Order.status == 'delivered', db.func.date(Order.created_at) == date.today()).count(),
        'total_earnings': total_earnings
    }
    
    return render_template('delivery/dashboard.html', dp=dp, active_orders=active_orders, completed_orders=completed_orders, stats=stats)

@delivery_bp.route('/update-order/<int:order_id>', methods=['POST'])
@dp_required
def update_order(order_id):
    dp_id = session['dp_id']
    order = Order.query.get_or_404(order_id)
    
    if order.delivery_person_id != dp_id:
        flash('Unauthorized to update this order.', 'danger')
        return redirect(url_for('delivery.dashboard'))
        
    new_status = request.form.get('status')
    # Delivery personnel can mark as 'out for delivery', 'delivered', or 'cancelled' (Failed/Refused)
    valid_statuses = ['out_for_delivery', 'delivered', 'cancelled']
    
    if new_status in valid_statuses:
        # If delivery fails/customer refuses, restore stock & refund prepaid amount to wallet
        if new_status == 'cancelled' and order.status != 'cancelled':
            for item in order.items:
                item.product.stock += item.quantity
            if order.payment_method == 'online':
                order.user.wallet_balance += order.total_amount
                db.session.add(WalletTransaction(
                    user_id=order.user_id,
                    amount=order.total_amount,
                    transaction_type='refund',
                    description=f'Refund for Delivery Refusal/Failure (Order #{order.id})'
                ))
                
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status.replace("_", " ").title()}.', 'success')
    else:
        flash('Invalid status update.', 'danger')
        
    return redirect(url_for('delivery.dashboard'))