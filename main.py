import telebot
import sqlite3
from config import DATABASE_NAME, API_TOKEN, ADMIN_ID
from database import init_db, set_shop_status
from handlers.start import init_start_handlers, show_home_menu
from handlers.shop import init_shop_handlers
from handlers.giveaway import init_giveaway_handlers

# 🚨 ပြင်ဆင်ချက်: payment.py ထဲက init_all_handlers ကို လှမ်းယူပါတယ်
from handlers.payment import init_all_handlers

# ၁။ Bot Initialize လုပ်ခြင်း
bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')

# ၂။ Database Initialize လုပ်ခြင်း
init_db()

# ၃။ Handler များ Register လုပ်ခြင်း
init_start_handlers(bot)
init_shop_handlers(bot)
init_giveaway_handlers(bot)

# 🌟 ပြင်ဆင်ချက်: Payment, Review, Admin Buttons အားလုံး တစ်ခါတည်း အလုပ်လုပ်စေရန် နှိုးလိုက်ခြင်း
init_all_handlers(bot)

# ---------------------------------------------------------
# Universal Callback Handlers
# (start.py ထဲမှ home handler ကို ဖယ်ရှားပြီး ဒီနေရာတွင်တစ်ခုတည်းသာ ထားရမည်)
# ---------------------------------------------------------

@bot.callback_query_handler(func=lambda call: call.data == 'home')
def universal_back_home(call):
    try:
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_home_menu(call.from_user.id, call.from_user.first_name, bot)
    except Exception:
        show_home_menu(call.from_user.id, call.from_user.first_name, bot)

# ---------------------------------------------------------
# Admin Commands
# ---------------------------------------------------------

@bot.message_handler(commands=['send'])
def handle_send_command(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    try:
        msg_parts = message.text.split(maxsplit=2)
        if len(msg_parts) < 3:
            bot.reply_to(message, "⚠️ <b>အသုံးပြုပုံ:</b>\n<code>/send [user_id] [account_info]</code>")
            return

        target_id = msg_parts[1]
        info      = msg_parts[2]

        delivery_text = (
            "🎉 <b>သင်ဝယ်ယူထားသော ပစ္စည်းရောက်ရှိပါပြီ!</b>\n\n"
            f"📧 <b>Account Info:</b>\n<code>{info}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>အရေးကြီးသတိပေးချက်:</b>\n"
            "ယခုအော်ဒါသည် Manual ပို့ဆောင်ပေးထားခြင်းဖြစ်၍ ဤအချက်အလက်များကို "
            "<b>မိမိဘာသာ သေချာစွာ သိမ်းဆည်းထားပါရန်</b> မေတ္တာရပ်ခံအပ်ပါသည်၊၊\n\n"
            "🙏 စနစ်ပိုင်းလိုအပ်ချက်ကြောင့် My Orders ထဲတွင် ဤအချက်အလက်များကို "
            "ပြန်လည်ကြည့်ရှု၍ မရနိုင်ခြင်းအတွက် အနူးအညွတ် တောင်းပန်အပ်ပါသည်၊၊\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "အဆင်မပြေမှုရှိပါက Admin @independence_N ကို ဆက်သွယ်ပါ၊၊"
        )
        
        # 🌟 Review Button ဆောက်ခြင်း
        from telebot import types 
        review_markup = types.InlineKeyboardMarkup()
        review_markup.add(
            types.InlineKeyboardButton("✍️ Review / Feedback ပေးရန်", callback_data="give_review")
        )

        # ဝယ်သူထံသို့ စာပို့ရာတွင် reply_markup=review_markup ကို တွဲထည့်ပေးခြင်း
        bot.send_message(target_id, delivery_text, reply_markup=review_markup, parse_mode='HTML')
        
        # Admin Chat ထဲသို့ အကြောင်းကြားစာ ပြန်ပြခြင်း
        bot.reply_to(message, f"✅ User <code>{target_id}</code> ထံ ပစ္စည်းပို့ဆောင်ပြီး Review Button တွဲပေးလိုက်ပါပြီ၊၊", parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"❌ ပို့ဆောင်မှု မအောင်မြင်ပါ- {e}")


@bot.message_handler(commands=['open', 'close', 'maintenance'])
def change_status(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    status = message.text[1:]  # /open → open

    # database.py ၏ set_shop_status() ကို သုံးခြင်းဖြင့်
    # row မရှိသော်လည်း INSERT OR REPLACE ဖြင့် အမြဲ အလုပ်လုပ်မည်
    set_shop_status(status)

    status_msg = {
        'open':        "✅ ဆိုင်ကို ပြန်ဖွင့်လိုက်ပါပြီ၊၊",
        'close':       "🛑 ဆိုင်ကို ပိတ်လိုက်ပါပြီ၊၊",
        'maintenance': "🛠 Bot ကို Maintenance Mode ပြောင်းလိုက်ပါပြီ၊၊"
    }
    bot.reply_to(message, status_msg.get(status, "Status updated!"))


@bot.message_handler(commands=['announcement'])
def broadcast(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    text_to_send = message.text.replace('/announcement', '').strip()
    if not text_to_send:
        bot.reply_to(message, "💡 သုံးနည်း: /announcement [စာသား]")
        return

    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM orders")
        users = cursor.fetchall()

    count = 0
    for user in users:
        try:
            bot.send_message(user[0], f"📢 <b>ANNOUNCEMENT</b>\n\n{text_to_send}", parse_mode='HTML')
            count += 1
        except Exception:
            continue

    bot.reply_to(message, f"✅ User {count} ယောက်ဆီ ပို့ဆောင်ပြီးပါပြီ၊၊")


def set_bot_commands(bot):
    user_commands = [
        telebot.types.BotCommand("start", "Bot ကိုစတင်ရန်"),
        telebot.types.BotCommand("help",  "အကူအညီရယူရန်"),
        telebot.types.BotCommand("home",  "ပင်မစာမျက်နှာသို့သွားရန်")
    ]
    bot.set_my_commands(user_commands, scope=telebot.types.BotCommandScopeAllPrivateChats())

    admin_commands = user_commands + [
        telebot.types.BotCommand("open",         "ဆိုင်ဖွင့်မည်"),
        telebot.types.BotCommand("close",        "ဆိုင်ပိတ်မည်"),
        telebot.types.BotCommand("maintenance",  "Maintenance Mode"),
        telebot.types.BotCommand("announcement", "Announcement ပို့မည်"),
        telebot.types.BotCommand("send",         "ပစ္စည်း ပို့ဆောင်မည်")
    ]
    bot.set_my_commands(
        admin_commands,
        scope=telebot.types.BotCommandScopeChat(chat_id=ADMIN_ID)
    )


set_bot_commands(bot)

# ၄။ Bot စတင်ခြင်း
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)