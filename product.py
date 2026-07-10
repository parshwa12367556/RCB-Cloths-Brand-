from flask import Blueprint, render_template, request, redirect, url_for, session

product_bp = Blueprint('product_bp', __name__)

from models import Product, Category

@product_bp.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    search = request.args.get('q')
    price = request.args.get('price')
    sort = request.args.get('sort')
    
    query = Product.query
    
    if category:
        # Use case-insensitive matching to prevent issues with trailing spaces or casing
        query = query.filter(Product.category.ilike(category))
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
        
    # Apply price filtering based on the dropdown selected in the UI
    if price:
        if price == 'under_200':
            query = query.filter(Product.price < 200)
        elif price == '200_500':
            query = query.filter(Product.price >= 200, Product.price <= 500)
        elif price == '500_1000':
            query = query.filter(Product.price > 500, Product.price <= 1000)
        elif price == 'above_1000':
            query = query.filter(Product.price > 1000)
            
    # Apply Sorting
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'oldest':
        query = query.order_by(Product.created_at.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    # Paginate: 12 products per page
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    
    categories = Category.query.all()
    
    return render_template('shop/product.html', pagination=pagination, categories=categories)

@product_bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    
    # Point 8: Personalized Experience - Track Recently Viewed
    if 'recently_viewed' not in session:
        session['recently_viewed'] = []
    
    rv = list(session.get('recently_viewed', []))
    if id in rv:
        rv.remove(id)
    rv.insert(0, id)
    session['recently_viewed'] = rv[:4] # Keep the 4 most recent views
    session.modified = True
    
    return render_template('shop/product_detail.html', product=product)

@product_bp.route('/category/<category_name>')
def category_page(category_name):
    # Redirect directly to the product page with the category filter active
    return redirect(url_for('product_bp.products', category=category_name))

@product_bp.route('/siraj-pace-pack')
def siraj_pace_pack():
    # Fetching products that fit the high-performance or Siraj branding
    products = Product.query.filter(Product.category.ilike('Jerseys') | Product.name.ilike('%Siraj%')).limit(6).all()
    return render_template('shop/siraj_pace_pack.html', products=products)