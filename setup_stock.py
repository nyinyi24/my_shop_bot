import sqlite3
from config import DATABASE_NAME

def add_stock():
    # သင့် folder ထဲက shop.db ဆီကို ချိတ်ဆက်ပါမယ်
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # --- ဒီနေရာမှာ ရောင်းချမယ့် အကောင့်တွေကို ထည့်ပါ ---
    # ပုံစံ: ('ပစ္စည်းအမည်', 'Mail:Password သို့မဟုတ် Account Info')
    accounts = [
        ('Netflix Premium', 'user1@gmail.com:pass111'),
        ('Netflix Premium', 'user2@gmail.com:pass222'),
        ('Netflix Premium', 'user3@gmail.com:pass333'),
        ('Spotify Family', 'spotify_vip@gmail.com:music789'),
        ('YouTube Premium', 'yt_premium@gmail.com:video555')
    ]

    # Database ထဲသို့ ထည့်သွင်းခြင်း
    cursor.executemany("INSERT INTO item_stocks (item_name, account_info) VALUES (?, ?)", accounts)
    
    conn.commit()
    conn.close()
    print(f"✅ အကောင့် Stock ({len(accounts)}) ခုကို Database ထဲ ထည့်သွင်းပြီးပါပြီ၊၊")

if __name__ == "__main__":
    add_stock()
