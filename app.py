import requests
from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Required for flash messages

# Google Sheets Web App URL
GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbzJ_HU_bBSTJhpAnNzUQ-IYK227w9KP9UcVWIqZLMUZooNUMSpe7pA0lcwOFedsmr-a/exec'

# Product Data
products_data = {
    'keychain': {
        'id': 'keychain',
        'name': '客製化鑰匙圈',
        'price': 'NT$ 150 起',
        'desc': '個人專屬雷雕鑰匙圈，可刻印名字或簡單圖案。適合送禮或自用。選用進口高級板材，邊緣光滑不刮手。',
        'specs': ['尺寸：5cm x 3cm', '厚度：3mm', '材質：壓克力 / 木質', '包含：金屬鑰匙扣環'],
        'image': 'keychain.jpg' 
    },
    'coaster': {
        'id': 'coaster',
        'name': '原木杯墊',
        'price': 'NT$ 250 起',
        'desc': '天然原木材質，質感溫潤。可刻印公司 Logo 或紀念文字。每一片木紋都是獨一無二的藝術品。',
        'specs': ['直徑：9cm', '厚度：8mm', '材質：山毛櫸 / 胡桃木', '表面：環保防水漆處理'],
        'image': 'coaster.jpg'
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
    }
}

# Route: Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Route: Products List
@app.route('/products')
def products():
    return render_template('products.html', products=products_data)

# Route: Product Detail
@app.route('/product/<product_id>')
def product_detail(product_id):
    product = products_data.get(product_id)
    if not product:
        return redirect(url_for('products'))
    return render_template('product_detail.html', product=product)

# Route: Production Process
@app.route('/process')
def process():
    return render_template('process.html')

# Route: Booking Page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        # Extract data from form
        data = {
            'name': request.form.get('name'),
            'material': request.form.get('product'), # Map 'product' to 'material' column in Sheets
            'contact': request.form.get('contact'),
            'notes': request.form.get('notes')
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
        
    return render_template('booking.html')




if __name__ == '__main__':
    app.run(debug=True)
