import sqlite3

DATABASE_NAME = 'shop.db'

def init_db():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, join_date TEXT, role TEXT DEFAULT 'user')''')
        
        # 2. Items Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS items 
            (item_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, details TEXT, price REAL, stock INTEGER, type TEXT)''')
        
        # 3. Item Stocks Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS item_stocks 
            (stock_id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, account_info TEXT, is_sold BOOLEAN DEFAULT FALSE)''')
        
        # 4. Orders Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
            (order_id INTEGER PRIMARY KEY AUTOINCREMENT, 
             user_id INTEGER, 
             item_name TEXT, 
             quantity INTEGER, 
             payment_method TEXT, 
             status TEXT, 
             timestamp TEXT,
             delivered_data TEXT)''')
        
        # 5. Giveaway Tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS gw_items 
            (gw_item_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, content TEXT, stock INTEGER DEFAULT 0, is_used BOOLEAN DEFAULT FALSE)''')
            
        cursor.execute('''CREATE TABLE IF NOT EXISTS gw_claims 
            (claim_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, claim_date TEXT)''')

        # 6. Settings Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
            (key TEXT PRIMARY KEY, value TEXT)''')
        
        # Default settings
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_status', 'open')")

        conn.commit()

# --- Settings Functions ---

def get_shop_status():
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'shop_status'")
            result = cursor.fetchone()
            return result[0] if result else 'open'
    except:
        return 'open'

def set_shop_status(status):
    """ဆိုင်အခြေအနေ (open/close/maintenance) ကို ပြောင်းလဲရန်"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('shop_status', ?)", (status,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error setting shop status: {e}")
        return False

# --- Items Functions ---

def get_all_items():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        return cursor.fetchall()

def get_item_by_id(item_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
        return cursor.fetchone()

# --- Stocks Functions ---

def pull_account_from_stock_by_name(item_name):
    with sqlite3.connect(DATABASE_NAME, check_same_thread=False, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT stock_id, account_info FROM item_stocks 
            WHERE TRIM(item_name) = TRIM(?) COLLATE NOCASE 
            AND is_sold = 0 LIMIT 1
        """, (item_name,))
        res = cursor.fetchone()
        if res:
            stock_id, acc_info = res[0], res[1]
            cursor.execute("UPDATE item_stocks SET is_sold = 1 WHERE stock_id = ?", (stock_id,))
            cursor.execute("UPDATE items SET stock = stock - 1 WHERE name = ? COLLATE NOCASE", (item_name,))
            conn.commit()
            return acc_info
        return None

# --- User Functions ---

def add_user(user_id, join_date):
    try:
        with sqlite3.connect(DATABASE_NAME, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)", (user_id, join_date))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database Lock Error: {e}")

def get_user(user_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

# --- Orders Functions ---

def create_order(user_id, item_name, quantity, payment_method, status, timestamp):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (user_id, item_name, quantity, payment_method, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, item_name, quantity, payment_method, status, timestamp))
        conn.commit()
        return cursor.lastrowid

def update_order_status(order_id, status):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        conn.commit()

def update_order_delivery(order_id, account_info):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET delivered_data = ? WHERE order_id = ?", (account_info, order_id))
        conn.commit()

def get_user_orders(user_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE user_id = ? AND status = 'Success'", (user_id,))
        return cursor.fetchall()

def get_order_details(order_id):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error getting order details: {e}")
        return None

# --- Giveaway Functions ---

def get_all_gw_item_types():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM gw_items")
        return [row[0] for row in cursor.fetchall()]

def get_user_last_gw_claim(user_id):
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT claim_date FROM gw_claims WHERE user_id = ? ORDER BY claim_date DESC LIMIT 1", (user_id,))
            res = cursor.fetchone()
            return res[0] if res else None
    except Exception as e:
        print(f"Database Error (get_user_last_gw_claim): {e}")
        return None

def add_gw_claim(user_id, claim_date):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO gw_claims (user_id, claim_date) VALUES (?, ?)", (user_id, claim_date))
        conn.commit()

def get_available_gw_items_by_type(name):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gw_items WHERE name = ? AND is_used = FALSE LIMIT 1", (name,))
        return cursor.fetchone()

def mark_gw_item_as_used(gw_item_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE gw_items SET is_used = TRUE WHERE gw_item_id = ?", (gw_item_id,))
        conn.commit()

def reduce_gw_stock(item_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE gw_items SET stock = stock - 1 WHERE gw_item_id = ?", (item_id,))
        cursor.execute("UPDATE gw_items SET is_used = 1 WHERE gw_item_id = ? AND stock <= 0", (item_id,))
        conn.commit()
