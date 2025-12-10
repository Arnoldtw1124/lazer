import requests
from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Required for flash messages

# Google Sheets Web App URL
GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxHCpaqrvjipuFS2pVNq867X7h8XjGdN7be7mvzJT4fywH_tZnRQTKbnm2k9Xj-4l7j/exec'

# Route: Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Route: Booking Page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        # Extract data from form
        data = {
            'name': request.form.get('name'),
            'material': request.form.get('material'),
            'date': request.form.get('date'),
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
