import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect("inventory1.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS total_inventory (
        product_code TEXT PRIMARY KEY COLLATE NOCASE,
        product_name TEXT COLLATE NOCASE,
        available_stock INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_bought (
        in_bill_no INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        product_name TEXT COLLATE NOCASE,
        product_code TEXT COLLATE NOCASE,
        qty_bought INTEGER,
        Selling_Price REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_sell (
        out_bill_no INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        product_name TEXT COLLATE NOCASE,
        product_code TEXT COLLATE NOCASE,
        qty_sold INTEGER,
        price REAL,
        total_amount REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS returns (
    ret_no INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    product_name TEXT COLLATE NOCASE,
    product_code TEXT COLLATE NOCASE,
    qty_ret INTEGER,
    Selling_Price REAL,
    return_type TEXT DEFAULT 'sales_return' CHECK (return_type IN ('purchase_return', 'sales_return')),
    condition TEXT DEFAULT 'good' CHECK (condition IN ('good', 'damaged'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS new_products (
    product_code TEXT PRIMARY KEY COLLATE NOCASE,
    product_name TEXT NOT NULL COLLATE NOCASE,
    MRP REAL NOT NULL,
    Selling_Price REAL NOT NULL
    );""")

    conn.commit()
    conn.close()

def add_stock(code, name, qty, price):
    conn = sqlite3.connect("inventory1.db")
    cursor = conn.cursor()

    cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code = ?", (code,))
    result = cursor.fetchone()
    if result:
        new_stock = result[0] + qty
        cursor.execute("UPDATE total_inventory SET available_stock = ? WHERE product_code = ?", (new_stock, code))
    else:
        cursor.execute("INSERT INTO total_inventory (product_code, product_name, available_stock) VALUES (?, ?, ?)", (code, name, qty))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO inventory_bought (timestamp, product_name, product_code, qty_bought, Selling_Price) VALUES (?, ?, ?, ?, ?)",
                   (timestamp, name, code, qty, price))
    conn.commit()
    conn.close()

def sell_stock(code, name, qty, price):
    conn = sqlite3.connect("inventory1.db")
    cursor = conn.cursor()

    cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code = ?", (code,))
    result = cursor.fetchone()
    if not result or result[0] < qty:
        conn.close()
        return False

    new_stock = result[0] - qty
    cursor.execute("UPDATE total_inventory SET available_stock = ? WHERE product_code = ?", (new_stock, code))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_amount = qty * price
    cursor.execute("INSERT INTO inventory_sell (timestamp, product_name, product_code, qty_sold, price, total_amount) VALUES (?, ?, ?, ?, ?, ?)",
                   (timestamp, name, code, qty, price, total_amount))
    conn.commit()
    conn.close()
    return True

def fetch_sales_data(days=5):
    conn = sqlite3.connect("inventory1.db")
    cursor = conn.cursor()

    sales = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cursor.execute("SELECT SUM(total_amount) FROM inventory_sell WHERE DATE(timestamp) = ?", (date,))
        result = cursor.fetchone()
        sales.append(result[0] if result[0] else 0)
    conn.close()
    return sales[::-1]

def fetch_low_stock_data(threshold=10):
    """Fetch items with stock below or equal to the threshold."""
    conn = sqlite3.connect("inventory1.db")
    cursor = conn.cursor()
    cursor.execute("SELECT product_code, product_name, available_stock FROM total_inventory WHERE available_stock <= ?", (threshold,))
    items = cursor.fetchall()
    conn.close()
    return items
