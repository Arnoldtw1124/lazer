from flask import Flask, render_template, request

app = Flask(__name__)

# Route: Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Route: Booking Page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        # TODO: Handle booking submission logic
        return "Booking Received!" # Mock response
    return render_template('booking.html')

# Route: File Preview (Mock)
@app.route('/preview')
def preview():
    return render_template('preview.html')


if __name__ == '__main__':
    app.run(debug=True)
