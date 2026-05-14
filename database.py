import sqlite3

DATABASE_NAME = 'shop.db'

def init_db():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        # Users Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, join_date TEXT, role TEXT DEFAULT 'user')''')
        
        # Items Table (ပစ္စည်းအမည်နှင့် ဈေးနှုန်းပြရန်)
        cursor.execute('''CREATE TABLE IF NOT EXISTS items 
            (item_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, details TEXT, price REAL, stock INTEGER, type TEXT)''')
        
        # Item Stocks Table (ရောင်းမည့် Mail:Pass များ သိမ်းရန်)
        cursor.execute('''CREATE TABLE IF NOT EXISTS item_stocks 
            (stock_id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, account_info TEXT, is_sold BOOLEAN DEFAULT FALSE)''')
        
        # Orders Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
            (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_name TEXT, quantity INTEGER, payment_method TEXT, status TEXT, timestamp TEXT)''')
        
        # user Orders detail Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
            (order_id INTEGER PRIMARY KEY AUTOINCREMENT, 
             user_id INTEGER, 
             item_name TEXT, 
             quantity INTEGER, 
             payment_method TEXT, 
             status TEXT, 
             timestamp TEXT,
             delivered_data TEXT)''')
        conn.commit()

        # Giveaway Tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS gw_items 
            (gw_item_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, content TEXT, is_used BOOLEAN DEFAULT FALSE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS gw_claims 
            (claim_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, claim_date TEXT)''')

        conn.commit()

def get_item_by_id(item_id):
    """ID နဲ့ ပစ္စည်းအချက်အလက်ကို ယူရန်"""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM items WHERE item_id = ?", (item_id,))
        res = cursor.fetchone()
        return res[0] if res else None

def pull_account_from_stock_by_name(item_name):
    """နာမည်နဲ့ အကောင့်ကို stock ထဲက နှိုက်ယူရန် (အရှေ့က code ကို နည်းနည်း ပြန်ပြင်ထားသည်)"""
    import sqlite3
    with sqlite3.connect(DATABASE_NAME, check_same_thread=False, timeout=10) as conn:
        cursor = conn.cursor()
        # TRIM သုံးပြီး အသေအချာ ရှာမယ်
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

def add_user(user_id, join_date):
    try:
        # with သုံးခြင်းဖြင့် အလုပ်ပြီးတာနဲ့ connection ကို အလိုအလျောက် ပိတ်ပေးမှာပါ
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

def get_all_items():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        return cursor.fetchall()

def get_item_by_id(item_id):
    import sqlite3
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        # item_id Column နာမည် မှန်မမှန် ပြန်စစ်ပေးပါ (အချို့နေရာမှာ id ဟု သုံးတတ်သည်)
        cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
        item = cursor.fetchone()
        return item

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

def get_all_gw_item_types():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM gw_items")
        return [row[0] for row in cursor.fetchall()]

def get_user_last_gw_claim(user_id):
    """User နောက်ဆုံး Giveaway ယူခဲ့သည့် အချိန်ကို ယူရန် (Weekly Logic အတွက်)"""
    import sqlite3
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            # gw_claims table ထဲမှာ user_id အလိုက် နောက်ဆုံးယူခဲ့တဲ့ အချိန် (claim_date) ကို ယူမယ်
            # အချိန်အလိုက် စီပြီး (ORDER BY) အပေါ်ဆုံးက တစ်ခု (LIMIT 1) ကိုပဲ ယူမှာပါ
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

def get_order_details(order_id):
    """အော်ဒါ ID တစ်ခုချင်းစီရဲ့ အချက်အလက်အားလုံး (delivered_data အပါအဝင်) ကို ယူရန်"""
    import sqlite3
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error getting order details: {e}")
        return None
    
def reduce_gw_stock(item_id):
    import sqlite3
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        # Stock ကို တစ်ခုလျှော့မယ်
        cursor.execute("UPDATE gw_items SET stock = stock - 1 WHERE gw_item_id = ?", (item_id,))
        
        # အကယ်၍ Stock က 0 ဖြစ်သွားရင် is_used ကို 1 ပြောင်းပေးမယ် (Safety အတွက်ပါ)
        cursor.execute("UPDATE gw_items SET is_used = 1 WHERE gw_item_id = ? AND stock <= 0", (item_id,))
        conn.commit()

def get_shop_status():
    import sqlite3
    try:
        # DATABASE_NAME ကို config ကနေ import လုပ်ထားဖို့ လိုပါမယ်
        from config import DATABASE_NAME
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'shop_status'")
            result = cursor.fetchone()
            return result[0] if result else 'open'
    except:
        return 'open'