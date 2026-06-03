# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # .env ဖိုင်ကို ဖတ်မည်

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_TOKEN       = os.environ.get('BOT_TOKEN', '')
ADMIN_ID        = int(os.environ.get('ADMIN_ID', '0'))
YOUR_CHANNEL_ID = int(os.environ.get('CHANNEL_ID', '0'))
SUPPORT_URL     = os.environ.get('SUPPORT_URL', 'https://t.me/independence_N')
DATABASE_NAME   = os.path.join(BASE_DIR, 'shop.db')
