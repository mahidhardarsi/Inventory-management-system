from flask import Flask, render_template
from inventory_db import init_db

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/add_items')
def add_items():
    return render_template('add_items.html')

@app.route('/sell_items')
def sell_items():
    return render_template('sell_items.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/new_products')
def new_products():
    return render_template('new_products.html')

@app.route('/returns')
def returns():
    return render_template('returns.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 