import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)

app.secret_key = "super_secret_key"

# --- DATABASE CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="General")
    image = db.Column(db.String(255), nullable=False)
    desc = db.Column(db.Text, nullable=False)

# --- AUTO-GENERATE DATABASE & INSERT THE 15 ITEMS ---
with app.app_context():
    # Recreates database if it is deleted or malformed
    db.create_all() 
    
    # Only adds items if the database table is completely empty
    if not Product.query.first(): 
        print("Seeding database with 15 products...")
        items = [
            Product(name='Sonic-Blast Pro', category='Headphones', price=89.99, image='https://images.unsplash.com/photo-1505740420928-5e560c06d30e', desc='Wireless over-ear headphones with active noise cancellation and 40h battery.'),
            Product(name='Lunar Smartwatch', category='Watches', price=129.50, image='https://images.unsplash.com/photo-1523275335684-37898b6baf30', desc='Sleek titanium finish with heart rate monitoring and water resistance.'),
            Product(name='Click-Master X', category='Electronics', price=45.00, image='https://images.unsplash.com/photo-1527443224154-c4a3942d3acf', desc='Ergonomic mechanical gaming mouse with customizable RGB lighting.'),
            Product(name='ClearVoice Mic', category='Electronics', price=55.00, image='https://images.unsplash.com/photo-1590602847861-f357a9332bbc', desc='Professional USB condenser microphone for streaming and podcasting.'),
            Product(name='Pixel-View Tab', category='Tablets', price=349.00, image='https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0', desc='10-inch HD display perfect for reading, sketching, and entertainment.'),
            Product(name='Urban Nomad Pack', category='Bags', price=75.00, image='https://images.unsplash.com/photo-1553062407-98eeb64c6a62', desc='Weatherproof canvas backpack with a dedicated 15-inch laptop sleeve.'),
            Product(name='Venture Duffel', category='Bags', price=60.00, image='https://images.unsplash.com/photo-1547949003-9792a18a2601', desc='Spacious travel duffel made from eco-friendly recycled materials.'),
            Product(name='Classic Chrono', category='Watches', price=110.00, image='https://images.unsplash.com/photo-1524592094714-0f0654e20314', desc='Minimalist leather strap watch suitable for formal and casual wear.'),
            Product(name='Zenith Totebag', category='Bags', price=25.00, image='https://images.unsplash.com/photo-1544816155-12df9643f363', desc='Heavy-duty cotton tote bag for daily grocery runs or beach days.'),
            Product(name='Sleek Slim Wallet', category='Accessories', price=30.00, image='https://images.unsplash.com/photo-1627123424574-724758594e93', desc='RFID-blocking minimalist leather wallet that fits up to 8 cards.'),
            Product(name='Aura Desk Lamp', category='Home', price=35.00, image='https://images.unsplash.com/photo-1534073828943-f801091bb18c', desc='Minimalist LED desk lamp with adjustable brightness and USB port.'),
            Product(name='Echo Bluetooth', category='Speakers', price=65.00, image='https://images.unsplash.com/photo-1608156639585-b3a032ef9689', desc='Portable waterproof speaker with deep bass and 360-degree sound.'),
            Product(name='Nomad Flask', category='Accessories', price=22.00, image='https://images.unsplash.com/photo-1602143393494-1a2887a7406a', desc='Insulated stainless steel water bottle, keeps drinks cold for 24h.'),
            Product(name='Grip-Steady Stand', category='Electronics', price=18.00, image='https://images.unsplash.com/photo-1586105251261-72a7566408c1', desc='Universal aluminum phone stand for hands-free video calls.'),
            Product(name='Soft-Touch Case', category='Accessories', price=15.99, image='https://images.unsplash.com/photo-1601784551446-20c9e07cdbab', desc='Protective silicone case with a microfiber lining for latest phones.')
        ]
        db.session.bulk_save_objects(items)
        db.session.commit()
        print("Database Seeded Successfully!")

# --- AUTH HELPERS ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- USER ROUTES ---

@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()
    category_query = request.args.get('category', '').strip()
    query = Product.query
    if category_query:
        query = query.filter(Product.category == category_query)
    if search_query:
        query = query.filter(Product.name.icontains(search_query))
    
    products = query.all()
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    cart_count = len(session.get('cart', []))
    
    return render_template('index.html', products=products, categories=categories, 
                           active_category=category_query, search_query=search_query, 
                           cart_count=cart_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template('login.html')

# --- ADMIN ROUTES ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pw = request.form.get('password', '').strip()
        if email == "admin@store.com" and pw == "admin789":
            session['admin'] = email
            return redirect(url_for('admin_dashboard'))
        flash("Invalid Admin Credentials")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    search_query = request.args.get('search', '').strip()
    if search_query:
        all_products = Product.query.filter(Product.name.icontains(search_query)).all()
    else:
        all_products = Product.query.order_by(Product.category).all()
    return render_template('admin.html', products=all_products, search_query=search_query)

@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        new_product = Product(
            name=request.form.get('name'), 
            price=float(request.form.get('price')), 
            category=request.form.get('category'),
            image=request.form.get('image'), 
            desc=request.form.get('desc')
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!")
        return redirect(url_for('admin_dashboard'))
    return render_template('add_product.html')

@app.route('/admin/edit_product/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.image = request.form.get('image')
        product.desc = request.form.get('desc')
        db.session.commit()
        flash(f"Product updated successfully!")
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_product.html', product=product)

@app.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!')
    return redirect(url_for('admin_dashboard'))

# --- CART ROUTES ---

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session: session['cart'] = []
    cart = session['cart']
    cart.append(product_id)
    session['cart'] = cart
    flash("Item added to cart!")
    return redirect(url_for('home'))

@app.route('/cart')
def view_cart():
    cart_ids = session.get('cart', [])
    cart_items = Product.query.filter(Product.id.in_(cart_ids)).all()
    total = sum(item.price for item in cart_items)
    return render_template('cart.html', items=cart_items, total=total, cart_count=len(cart_ids))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_ids = session.get('cart', [])
    if not cart_ids: return redirect(url_for('home'))
    items = Product.query.filter(Product.id.in_(cart_ids)).all()
    total = sum(item.price for item in items)
    if request.method == 'POST':
        session.pop('cart', None)
        flash("Order placed successfully!")
        return redirect(url_for('home'))
    return render_template('checkout.html', items=items, total=total)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        if product_id in cart:
            cart.remove(product_id)
            session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('view_cart'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)