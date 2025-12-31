import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Required for flash messages and session
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB limit
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders_v2.db' # Local SQLite DB (v2 with filename)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    material = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(255), nullable=True) # New column for image filename
    status = db.Column(db.String(20), default='Pending') # Pending, Processing, Completed, Cancelled
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.id}>'

# Product Model
class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    original_price = db.Column(db.String(50), nullable=True)
    discount_label = db.Column(db.String(50), nullable=True)
    desc = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    specs = db.Column(db.Text, nullable=True) # Stored as JSON string
    variants = db.Column(db.Text, nullable=True) # Stored as JSON string
    addons = db.Column(db.Text, nullable=True) # Stored as JSON string
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'original_price': self.original_price,
            'discount_label': self.discount_label,
            'desc': self.desc,
            'image': self.image,
            'specs': json.loads(self.specs) if self.specs else [],
            'variants': json.loads(self.variants) if self.variants else [],
            'addons': json.loads(self.addons) if self.addons else []
        }

# Create DB on startup
with app.app_context():
    db.create_all()
    
    # Check if products exist, if not seed from dictionary
    # Note: We need to access products_data here, but it's defined later in the file in the original code.
    # We should move products_data definition UP or handle this seeding after products_data is defined.
    # Strategy: We will move the seeding logic to the bottom of the file, before app.run, or move products_data up.
    # Let's check where products_data is. It's at line 188.
    # To avoid massive reordering, let's keep the db.create_all() here but add a separate seeding block at the end of the file.

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Admin Configuration
ADMIN_PASSWORD = "admin" # Default password, change this!

# Google Sheets Web App URL
GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxv-mle-uSkDbYFH5zJXwUNqd8y7yMZ5z1Vt7cug_q3_8iIZuq-aP_fuAx2zhV4f84K/exec'

# Product Data (unchanged)
# ... (rest of product data initialization if needed, but here we replace the top section)

# ... (Previous product data code - ensure this block replaces correctly from line 6 down)

# ... (Route: Home Page -> /products -> /product/<id> -> /process -> /terms -> /privacy -> /guidelines -> /materials -> /faq)

# Context Processor to inject data into all templates
@app.context_processor
def inject_navbar_products():
    try:
        # Fetch top 4 products for the navbar dropdown
        navbar_products = Product.query.order_by(Product.sort_order).limit(4).all()
        return dict(navbar_products=navbar_products)
    except Exception:
        return dict(navbar_products=[])

# Route: Admin Login
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('登入成功', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('密碼錯誤', 'error')
    return render_template('admin_login.html')

# Route: Admin Logout
@app.route('/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# Route: Admin Dashboard (Protected)
@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        # Get all orders ordered by date (newest first)
        orders = Order.query.order_by(Order.date.desc()).all()
        
        # Stats for V2 Dashboard
        try:
            product_count = Product.query.count()
            # Calculate pending orders safely in Python
            pending_count = len([o for o in orders if o.status == 'Pending'])
        except Exception as e:
            print(f"Error fetching stats: {e}")
            product_count = 0
            pending_count = 0
            
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return render_template('admin_dashboard.html', orders=orders, product_count=product_count, pending_count=pending_count, now_time=now_time)
        
    except Exception as e:
        # Emergency Debug Output
        return f"""
        <h1>DEBUG ERROR REPORT</h1>
        <p>Admin Dashboard crashed with error:</p>
        <pre>{str(e)}</pre>
        <p>Please screenshot this and send to developer.</p>
        """

# Route: Update Order Status
@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f'訂單 #{order.id} 狀態已更新為 {new_status}', 'admin_success')
    
    return redirect(url_for('admin_dashboard'))

# Route: Delete Order
@app.route('/admin/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
        
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash(f'訂單 #{order.id} 已刪除', 'admin_success')
    return redirect(url_for('admin_dashboard'))

# Route: Customer Tracking Page
@app.route('/tracking', methods=['GET', 'POST'])
def tracking():
    order = None
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            # Find the most recent order for this email
            order = Order.query.filter_by(contact=email).order_by(Order.date.desc()).first()
            if not order:
                flash('找不到相關訂單，請確認 Email 是否正確。', 'error')
    
    return render_template('tracking.html', order=order)

# --------------------------
# Admin Product Management
# --------------------------

# Route: Admin Product List
@app.route('/admin/products')
def admin_products():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    products = Product.query.order_by(Product.sort_order).all()
    return render_template('admin_products.html', products=products)

# Route: Admin Add Product
@app.route('/admin/products/new', methods=['GET', 'POST'])
def admin_product_new():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Handle Image Upload
            file = request.files.get('image')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = 'default_product.jpg' # Fallback

            new_product = Product(
                id=request.form.get('id'),
                name=request.form.get('name'),
                price=request.form.get('price'),
                original_price=request.form.get('original_price'),
                discount_label=request.form.get('discount_label'),
                desc=request.form.get('desc'),
                image=filename,
                specs=request.form.get('specs'), # Expecting JSON string from form
                variants=request.form.get('variants'), # Expecting JSON string from form
                addons=request.form.get('addons'), # Expecting JSON string from form
                sort_order=int(request.form.get('sort_order', 0))
            )
            db.session.add(new_product)
            db.session.commit()
            flash('商品新增成功！', 'admin_success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'新增失敗：{str(e)}', 'admin_error')
            
    return render_template('admin_product_form.html', product=None)

# Route: Admin Edit Product
@app.route('/admin/products/edit/<product_id>', methods=['GET', 'POST'])
def admin_product_edit(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Handle Image Upload
            file = request.files.get('image')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image = filename # Update image only if new file uploaded

            product.name = request.form.get('name')
            product.price = request.form.get('price')
            product.original_price = request.form.get('original_price')
            product.discount_label = request.form.get('discount_label')
            product.desc = request.form.get('desc')
            product.specs = request.form.get('specs')
            product.variants = request.form.get('variants')
            product.addons = request.form.get('addons')
            product.sort_order = int(request.form.get('sort_order', 0))
            
            db.session.commit()
            flash('商品更新成功！', 'admin_success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash(f'更新失敗：{str(e)}', 'admin_error')

    return render_template('admin_product_form.html', product=product)

# Route: Admin Delete Product
@app.route('/admin/products/delete/<product_id>', methods=['POST'])
def admin_product_delete(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'商品 {product.name} 已刪除', 'admin_success')
    return redirect(url_for('admin_products'))

# Route: Booking Page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    # Fetch all products from DB
    all_products = Product.query.all()
    products_map = {p.id: p.to_dict() for p in all_products}

    if request.method == 'POST':
        # Handle file upload
        file = request.files.get('file')
        filename = "無附檔"
        file_url = ""
        db_filename = None # For DB

        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Generate a local URL (or you could upload to a cloud service)
            # For this context, we'll store the filename to reference
            file_url = f" (附檔: {filename})"
            db_filename = filename
        
        # Extract data from form
        contact_info = request.form.get('email')
        
        product_name = request.form.get('product')
        variant_name = request.form.get('variant')
        
        # Combine product and variant
        full_product_name = f"{product_name} - {variant_name}" if variant_name else product_name
        
        notes_content = request.form.get('notes', '') + file_url

        # 1. Save to Local SQLite DB
        try:
            new_order = Order(
                name=request.form.get('name'),
                material=full_product_name,
                contact=contact_info,
                notes=notes_content,
                filename=db_filename # Check if None is allowed
            )
            db.session.add(new_order)
            db.session.commit()
        except Exception as e:
            print(f"Database Error: {e}") # Log error but continue to sheets

        # 2. Send to Google Sheets
        data = {
            'name': request.form.get('name'),
            'material': full_product_name, 
            'contact': contact_info,
            'notes': notes_content 
        }
        
        try:
            # Send data to Google Sheets
            response = requests.post(GOOGLE_SCRIPT_URL, json=data)
            
            if response.status_code == 200:
                flash('預約成功！我們將盡快與您聯繫。', 'success')
            else:
                flash('預約系統暫時忙碌中，請稍後再試。', 'error')
        except Exception as e:
            flash(f'發生錯誤：{str(e)}', 'error')
            
        return redirect(url_for('booking'))
        
    return render_template('booking.html', products=products_map)

# Product Data
products_data = {
    'keychain': {
        'id': 'keychain',
        'name': '皮革鑰匙圈',
        'price': 'NT$ 150 起',
        'desc': '質感皮革鑰匙圈，搭配精緻縫線與金屬扣環。可客製化刻印名字或紀念日期，展現個人獨特品味。',
        'specs': ['尺寸：10cm x 2cm', '材質：PU皮革 / 合金', '工藝：雷射雕刻'],
        'image': 'leather_keychain.jpg' 
    },
    'coaster': {
        'id': 'coaster',
        'name': '軟木杯墊',
        'price': 'NT$ 150 起',
        'desc': '天然軟木材質，厚實堅固且具備優異的隔熱防燙效果。獨特的溢水吸收特性，讓桌面時刻保持乾爽。提供多種形狀與功能款可供選擇。',
        'specs': [
            '特色：天然軟木 / 溢水吸收 / 隔熱防燙',
            '【凹槽款】直徑 100mm / 厚度 10mm',
            '【圓形款】直徑 98mm / 厚度 5mm',
            '【方形款】直徑 98mm / 厚度 5mm'
        ],
        'image': 'coaster_default.png',
        'variants': [
            {'name': '凹槽款', 'image': 'coaster_groove.png', 'spec_text': '【凹槽款】直徑 100mm / 厚度 10mm'},
            {'name': '圓形款', 'image': 'coaster_round.png', 'spec_text': '【圓形款】直徑 98mm / 厚度 5mm'},
            {'name': '方形款', 'image': 'coaster_square.png', 'spec_text': '【方形款】直徑 98mm / 厚度 5mm'}
        ]
    },
    'tag': {
        'id': 'tag',
        'name': '寵物名牌',
        'price': 'NT$ 200 起',
        'desc': '金屬或皮革材質，耐用且輕便。刻上毛孩名字與聯絡電話，防止走失。附贈防走失鈴鐺。',
        'specs': ['尺寸：3cm x 2cm', '材質：不鏽鋼 / 植鞣革', '工藝：深層雕刻 (不易磨損)'],
        'image': 'tag.jpg'
    },
    'stand': {
        'id': 'stand',
        'name': '壓克力立牌',
        'price': 'NT$ 450 起',
        'desc': '透明壓克力切割與雕刻，適合動漫角色、偶像應援或展示架。高透光度，邊緣鑽石拋光。',
        'specs': ['尺寸：可客製 (最大 20cm)', '厚度：5mm', '底座：包含可拆卸底座'],
        'image': 'stand.jpg'
    },
    'cardcheck': {
        'id': 'cardcheck',
        'name': '金屬名片/銘版',
        'price': 'NT$ 300 起',
        'desc': '陽極處理鋁合金或不鏽鋼，呈現極致工業風質感。適合高級商務人士或機械銘牌使用。',
        'specs': ['尺寸：8.5cm x 5.4cm (標準名片)', '材質：鋁合金 / 304不鏽鋼', '顏色：銀 / 黑 / 金'],
        'image': 'card.jpg'
    },
    'priceboard': {
        'id': 'priceboard',
        'name': '【展會專用】客製化雷雕價目牌',
        'price': 'NT$ 200',
        'original_price': 'NT$ 350', 
        'discount_label': '先行者優惠 (Early Access)',
        'desc': '同人展 (FF/CWT) 與市集攤位必備！告別軟爛紙張，用白橡木紋雷雕打造專業門面。防潑水、高對比、支援 QR Code 雕刻，不僅耐用更能吸引目光。',
        'specs': [
            '用途：同人展 (FF/CWT) / 創意市集 / 商業櫃台',
            '尺寸：30cm x 20cm',
            '厚度：2.85 mm (硬挺不彎曲)',
            '材質：防潑水白橡木紋植纖板',
            '特色：工業級耐用 / 高對比雷雕 / 支援 QR Code'
        ],
        'image': 'priceboard_mockup.png',
        'addons': [
            {'name': '加購畫架', 'price': '+NT$ 79', 'desc': '專用立架，穩固支撐 (搭配價)'}
        ]
    }
}

# Route: Home Page
@app.route('/')
def index():
    # Select Top 3 Popular Products
    popular_ids = ['coaster', 'keychain', 'stand'] 
    popular_products = []
    
    for pid in popular_ids:
        product = Product.query.get(pid)
        if product:
             popular_products.append(product.to_dict())
    
    return render_template('index.html', popular_products=popular_products)

# Route: Products List
@app.route('/products')
def products():
    products_list = Product.query.all()
    # Convert to dict for template compatibility if it uses .items(), or check template.
    # Assuming template iterates over dict values or we pass a list.
    # To be safe and compatible with potential {% for key, val in products.items() %} in template:
    products_map = {p.id: p.to_dict() for p in products_list}
    return render_template('products.html', products=products_map)

# Route: Product Detail
@app.route('/product/<product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product.to_dict())

# Route: Production Process
@app.route('/process')
def process():
    return render_template('process.html')

# Route: Terms of Service
@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Route: File Guidelines
@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

# Route: Material Library
@app.route('/materials')
def materials():
    return render_template('materials.html')

# Route: FAQ Page
@app.route('/faq')
def faq():
    return render_template('faq.html')






# Seed Database with Product Data
with app.app_context():
    if Product.query.count() == 0:
        print("Seeding products to database...")
        for pid, p_data in products_data.items():
            new_product = Product(
                id=pid,
                name=p_data['name'],
                price=p_data['price'],
                original_price=p_data.get('original_price'),
                discount_label=p_data.get('discount_label'),
                desc=p_data['desc'],
                image=p_data['image'],
                specs=json.dumps(p_data['specs']) if 'specs' in p_data else None,
                variants=json.dumps(p_data['variants']) if 'variants' in p_data else None,
                addons=json.dumps(p_data['addons']) if 'addons' in p_data else None,
                sort_order=0 # Default order
            )
            db.session.add(new_product)
        db.session.commit()
        print("Seeding complete.")

if __name__ == '__main__':
    app.run(debug=True)
