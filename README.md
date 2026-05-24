# 🏪 ENI Premium Store Telegram Bot

An automated Telegram e-commerce bot designed for ENI Premium Store to sell digital subscriptions and services seamlessly using both Auto-Delivery and Manual Delivery workflows.

---

## 🚀 Features

### 1. 🤖 Dual-Delivery Channels
* **Auto-Delivery Workflow:** When the admin clicks `✅ Approve` on a payment receipt, the bot automatically pulls available account credentials (Mail:Pass) from the database stock and instantly delivers them to the buyer.
* **Manual Delivery Workflow:** If an item goes out of stock, the bot instantly alerts the admin chat, prompting the admin to type out the account credentials directly or use the `/send` command to complete the order.

### 2. ✍️ In-Bot Review & Feedback System
* Once a product is delivered (via either Auto or Manual methods), a **`✍️ Review / Feedback ပေးရန်`** inline button is automatically attached to the delivery message.
* Buyers can click the button and type their review directly inside the bot without being redirected elsewhere.
* The bot automatically forwards the review to the public **[ENI Reviews Channel](https://t.me/ENIreviews)**. For privacy, the buyer's name is masked (Anonymous, e.g., `N***`).
* Simultaneously, a detailed notification with the buyer's actual name and Telegram ID is sent to the Admin Chat for internal tracking.

---

## 📂 Project Structure

```text
my_shop_bot/
├── env/                    # Virtual Environment
├── handlers/               # Split bot logic modules
│   ├── __init__.py
│   ├── giveaway.py         # Giveaway management system
│   ├── payment.py          # Auto/Manual Delivery & In-Bot Review core logic 🌟
│   ├── shop.py             # Product catalog and display logic
│   └── start.py            # Welcome menu and homepage navigation
├── config.py               # Bot tokens, Admin IDs, and configurations
├── database.py             # SQLite Queries (Orders, Stock, and User tracking)
├── main.py                 # Core main loop and manual /send command handler 🌟
├── requirements.txt         # Required Python dependencies
├── setup_stock.py          # Script to pre-load stock into the database
└── shop.db                 # SQLite database storage file
