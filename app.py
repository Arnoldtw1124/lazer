import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from functools import wraps

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
csrf = CSRFProtect(app) # Initialize CSRF Protection

app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key') # Use env var or default
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB limit
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders_v2.db' # Local SQLite DB (v2 with filename)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Security & Utils
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'ai', 'cdr', 'svg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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

# SiteConfig Model for Dynamic Settings
class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

# Create DB on startup
with app.app_context():
    db.create_all()
    # Ensure default marquee text exists
    if not SiteConfig.query.filter_by(key='marquee_text').first():
        default_marquee = SiteConfig(key='marquee_text', value='Cyberpunk 2077 Style Laser Engraving Service // 客製化雷雕服務 // 歡迎預約')
        db.session.add(default_marquee)
        db.session.commit()

# Context Processor to inject marquee text into all templates
@app.context_processor
def inject_site_config():
    marquee_config = SiteConfig.query.filter_by(key='marquee_text').first()
    marquee_text = marquee_config.value if marquee_config else 'Welcome to LaserCraft'
    
    # Existing navbar product logic
    navbar_products = Product.query.order_by(Product.sort_order).limit(4).all()
    
    return dict(marquee_text=marquee_text, navbar_products=navbar_products)

# ... (Previous code)

# Route: Admin Marketing (Marquee Settings)
@app.route('/admin/marketing', methods=['GET', 'POST'])
@login_required
def admin_marketing():
    
    if request.method == 'POST':
        marquee_text = request.form.get('marquee_text')
        config = SiteConfig.query.filter_by(key='marquee_text').first()
        if config:
            config.value = marquee_text
        else:
            new_config = SiteConfig(key='marquee_text', value=marquee_text)
            db.session.add(new_config)
        
        try:
            db.session.commit()
            flash('跑馬燈內容已更新！', 'admin_success')
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {e}', 'admin_error')
            
    # Get current value
    config = SiteConfig.query.filter_by(key='marquee_text').first()
    current_marquee = config.value if config else ''
    
    return render_template('admin_marketing.html', current_marquee=current_marquee)

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
@login_required
def admin_dashboard():
    
    # Get all orders ordered by date (newest first)
    try:
        orders = Order.query.order_by(Order.date.desc()).all()
    except Exception as e:
        print(f"Error fetching orders: {e}")
        orders = []
    
    # Stats for V2 Dashboard
    try:
        product_count = Product.query.count()
        # Calculate pending orders safely in Python
        pending_count = len([o for o in orders if o.status == 'Pending'])
        
        # Calculate Weekly Growth
        now = datetime.now()
        cutoff_7d = now - timedelta(days=7)
        cutoff_14d = now - timedelta(days=14)
        
        # Filter orders locally since we have them (assumes valid o.date)
        this_week_count = sum(1 for o in orders if o.date and o.date >= cutoff_7d)
        last_week_count = sum(1 for o in orders if o.date and o.date >= cutoff_14d and o.date < cutoff_7d)
        
        if last_week_count > 0:
            growth_rate = ((this_week_count - last_week_count) / last_week_count) * 100
        else:
            growth_rate = 100.0 if this_week_count > 0 else 0.0

    except Exception as e:
        print(f"Error fetching stats: {e}")
        product_count = 0
        pending_count = 0
        growth_rate = 0.0
        
    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('admin_dashboard.html', orders=orders, product_count=product_count, pending_count=pending_count, growth_rate=growth_rate, now_time=now_time)

# Route: Admin Data Center (Page)
@app.route('/admin/data')
@login_required
def admin_data():
    return render_template('admin_data.html')

# Route: Admin Stats API (JSON)
@app.route('/admin/api/stats')
@login_required
def admin_stats_api():
    
    # 1. Status Distribution
    orders = Order.query.all()
    status_counts = {'Pending': 0, 'Processing': 0, 'Completed': 0, 'Cancelled': 0}
    for o in orders:
        s = o.status if o.status else 'Pending'
        if s in status_counts:
            status_counts[s] += 1
        else:
            status_counts['Pending'] += 1 # Default fallback
            
    # 2. Orders Last 7 Days
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    daily_orders = {date: 0 for date in dates}
    
    for o in orders:
        if o.date:
            o_date = o.date.date().strftime('%Y-%m-%d')
            if o_date in daily_orders:
                daily_orders[o_date] += 1
                
    # 3. Top Products
    product_sales = {}
    for o in orders:
        # Simple string matching for now (e.g. "keychain - Variant")
        p_name = o.material.split(' - ')[0] if o.material else 'Unknown'
        product_sales[p_name] = product_sales.get(p_name, 0) + 1
        
    # Sort top 5
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "status_distribution": status_counts,
        "daily_orders": {"labels": list(daily_orders.keys()), "data": list(daily_orders.values())},
        "top_products": {"labels": [p[0] for p in top_products], "data": [p[1] for p in top_products]}
    }

@app.errorhandler(500)
def internal_error(error):
    return f"""
    <html><body>
        <h1>500 Internal Server Error</h1>
        <p>The server encountered an error:</p>
        <pre>{error}</pre>
        <p>Please report this to the developer.</p>
        <p><a href="/admin">Return to Admin</a> | <a href="/">Return to Home</a></p>
    </body></html>
    """, 500

# Route: Update Order Status
@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_status(order_id):
        
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash(f'訂單 #{order.id} 狀態已更新為 {new_status}', 'admin_success')
    
    # Check for redirect target
    redirect_target = request.form.get('redirect_to')
    if redirect_target == 'admin_orders':
        return redirect(url_for('admin_orders'))
    
    return redirect(url_for('admin_dashboard'))

# Route: Admin Orders Management
@app.route('/admin/orders')
@login_required
def admin_orders():
    
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '').strip()
    
    query = Order.query
    
    # Apply Status Filter
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
        
    # Apply Search
    if search_query:
        # Search by ID or Name or Contact
        if search_query.isdigit():
            query = query.filter(Order.id == int(search_query))
        else:
            # Case-insensitive search using func.lower()
            from sqlalchemy import func
            search_query_lower = search_query.lower()
            query = query.filter(
                (func.lower(Order.name).contains(search_query_lower)) | 
                (func.lower(Order.contact).contains(search_query_lower))
            )
            
    # Order by date desc
    orders = query.order_by(Order.date.desc()).all()
    
    return render_template('admin_orders.html', orders=orders, current_status=status_filter, search_query=search_query)

# Route: Delete Order
@app.route('/admin/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
        
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash(f'訂單 #{order.id} 已刪除', 'admin_success')
    
    # Check for redirect target
    redirect_target = request.form.get('redirect_to')
    if redirect_target == 'admin_orders':
        return redirect(url_for('admin_orders'))
        
    return redirect(url_for('admin_dashboard'))

# Route: Customer Tracking Page


# --------------------------
# Admin Product Management
# --------------------------

# Route: Admin Product List
@app.route('/admin/products')
@login_required
def admin_products():
    products = Product.query.order_by(Product.sort_order).all()
    return render_template('admin_products.html', products=products)

# Route: Admin Add Product
@app.route('/admin/products/new', methods=['GET', 'POST'])
@login_required
def admin_product_new():
    
    if request.method == 'POST':
        try:
            # Handle Image Upload
            file = request.files.get('image')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = 'default_product.jpg' # Fallback

            # Process Variants Image Uploads
            raw_variants = request.form.get('variants')
            variants_list = json.loads(raw_variants) if raw_variants else []
            
            for i, variant in enumerate(variants_list):
                # Check for uploaded file with key 'variant_image_0', 'variant_image_1', etc.
                v_file = request.files.get(f'variant_image_{i}')
                if v_file and v_file.filename:
                    v_filename = secure_filename(v_file.filename)
                    v_file.save(os.path.join(app.config['UPLOAD_FOLDER'], v_filename))
                    variant['image'] = v_filename
                # Use existing image if no new file is uploaded (already in JSON from frontend)

            new_product = Product(
                id=request.form.get('id'),
                name=request.form.get('name'),
                price=request.form.get('price'),
                original_price=request.form.get('original_price'),
                discount_label=request.form.get('discount_label'),
                desc=request.form.get('desc'),
                image=filename,
                specs=request.form.get('specs'), # Now comes from serialized JSON string in hidden input
                variants=json.dumps(variants_list), # Processed list back to JSON string
                addons=request.form.get('addons'),
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
@login_required
def admin_product_edit(product_id):
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Handle Image Upload
            file = request.files.get('image')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image = filename # Update image only if new file uploaded

            # Process Variants Image Uploads
            raw_variants = request.form.get('variants')
            variants_list = json.loads(raw_variants) if raw_variants else []
            
            for i, variant in enumerate(variants_list):
                v_file = request.files.get(f'variant_image_{i}')
                if v_file and v_file.filename:
                    v_filename = secure_filename(v_file.filename)
                    v_file.save(os.path.join(app.config['UPLOAD_FOLDER'], v_filename))
                    variant['image'] = v_filename

            product.name = request.form.get('name')
            product.price = request.form.get('price')
            product.original_price = request.form.get('original_price')
            product.discount_label = request.form.get('discount_label')
            product.desc = request.form.get('desc')
            product.specs = request.form.get('specs')
            product.variants = json.dumps(variants_list) # Save processed list
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
@login_required
def admin_product_delete(product_id):
    
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
            if not allowed_file(file.filename):
                flash('不支援的檔案格式。請上傳圖片 (png, jpg) 或設計檔 (ai, pdf, cdr)。', 'error')
                return redirect(url_for('booking'))
                
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
        
        # 3. Send Email Notification (Local)
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.utils import formataddr

            # Email Config (Environment Variables)
            SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
            MAIL_USER = os.getenv('MAIL_USER')
            MAIL_PASS = os.getenv('MAIL_PASS')
            MAIL_RECEIVER = os.getenv('MAIL_RECEIVER')

            if not MAIL_USER or not MAIL_PASS:
                 print("Email credentials not set. Skipping notification.")
                 raise ValueError("Missing MAIL_USER or MAIL_PASS env vars")

            # Email Content
            subject = f'🔥 [新訂單] #{new_order.id} {new_order.name} - {new_order.material}'
            body = f"""
            <h1>LaserCraft 新訂單通知</h1>
            <p><strong>訂單編號：</strong> #{new_order.id}</p>
            <p><strong>顧客姓名：</strong> {new_order.name}</p>
            <p><strong>訂購商品：</strong> {new_order.material}</p>
            <p><strong>聯絡方式：</strong> {new_order.contact}</p>
            <p><strong>備註/需求：</strong><br>{new_order.notes}</p>
            <hr>
            <p>請至 <a href="http://localhost:5000/admin">後台管理系統</a> 查看詳情。</p>
            """

            msg = MIMEText(body, 'html', 'utf-8')
            msg['From'] = formataddr(('LaserCraft Bot', MAIL_USER))
            msg['To'] = MAIL_RECEIVER
            msg['Subject'] = subject

            # Send via Gmail
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(MAIL_USER, MAIL_PASS)
            server.send_message(msg)
            server.quit()
            print(f"Email notification sent to {MAIL_RECEIVER}")

        except Exception as e:
            print(f"Email Error: {e}") # Non-blocking error

        
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

# Route: Order Tracking
@app.route('/tracking', methods=['GET', 'POST'])
def tracking():
    result = None
    searched = False
    
    if request.method == 'POST':
        searched = True
        query = request.form.get('order_id', '').strip()
        
        if query:
            # Try to find by ID (if it's a number) or Name
            if query.isdigit():
                result = Order.query.filter_by(id=int(query)).first()
            
            if not result:
                # Basic search by name (case insensitive usually depends on DB collation, 
                # for SQLite it's case sensitive by default, we can use ilike equivalent or just exact match for now)
                result = Order.query.filter(Order.name.contains(query)).first()
                if not result:
                    result = Order.query.filter(Order.contact.contains(query)).first()

    return render_template('tracking.html', result=result, searched=searched)


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
    # 1. Recommended Products (Admin Controlled - sort_order)
    try:
        # Get products with highest sort_order
        rec_query = Product.query.order_by(Product.sort_order.desc()).limit(3).all()
        recommended_products = [p.to_dict() for p in rec_query]
    except Exception as e:
        print(f"Error fetching recommended: {e}")
        recommended_products = []

    # 2. Popular Products (Data Driven - Order Count)
    try:
        orders = Order.query.all()
        product_sales = {}
        for o in orders:
            # Parse Title from "ProductName - VariantName"
            if o.material:
                p_name = o.material.split(' - ')[0]
                product_sales[p_name] = product_sales.get(p_name, 0) + 1
        
        # Sort by sales count desc
        sorted_sales = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:3]
        top_names = [x[0] for x in sorted_sales]
        
        # Fetch product details for these names
        # Note: In a real app we'd join on ID, but here we match Name
        popular_products = []
        for name in top_names:
            p = Product.query.filter_by(name=name).first()
            if p:
                popular_products.append(p.to_dict())
                
        # Fallback if no orders yet: use newest 3
        if not popular_products:
             newest = Product.query.order_by(Product.id.desc()).limit(3).all()
             popular_products = [p.to_dict() for p in newest]

    except Exception as e:
        print(f"Error fetching popular: {e}")
        popular_products = []
    
    return render_template('index.html', recommended_products=recommended_products, popular_products=popular_products)

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
