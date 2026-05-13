import telebot
import sqlite3
from config import DATABASE_NAME
from config import API_TOKEN, ADMIN_ID
from database import init_db
from handlers.start import init_start_handlers, show_home_menu
from handlers.shop import init_shop_handlers
from handlers.giveaway import init_giveaway_handlers
from handlers.payment import init_payment_handlers

# ၁။ Bot ကို Initialize လုပ်ခြင်း (HTML Mode ကို တစ်ခါတည်း သတ်မှတ်သည်)
bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')

# ၂။ Database Initialize လုပ်ခြင်း
init_db()

# ၃။ Handler များ Register လုပ်ခြင်း
init_start_handlers(bot)
init_shop_handlers(bot)
init_giveaway_handlers(bot)
init_payment_handlers(bot)

# ---------------------------------------------------------
# Universal Callback Handlers
# ---------------------------------------------------------

@bot.callback_query_handler(func=lambda call: call.data == 'home')
def universal_back_home(call):
    try:
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_home_menu(call.from_user.id, call.from_user.first_name, bot)
    except Exception as e:
        # Message ဖျက်မရလျှင်လည်း Menu အသစ် ပြပေးမည်
        show_home_menu(call.from_user.id, call.from_user.first_name, bot)

# ---------------------------------------------------------
# Admin Manual Send Command (HTML Version)
# ---------------------------------------------------------

@bot.message_handler(commands=['send'])
def handle_send_command(message):
    # Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    try:
        # command အပိုင်းအစများကို ခွဲထုတ်ခြင်း
        msg_parts = message.text.split(maxsplit=2)
        if len(msg_parts) < 3:
            bot.reply_to(message, "⚠️ <b>အသုံးပြုပုံ:</b>\n<code>/send [user_id] [account_info]</code>")
            return

        target_id = msg_parts[1]
        info = msg_parts[2]

        # HTML Tags သုံးပြီး စာသားကို ပိုမိုလှပအောင် ပြင်ဆင်ခြင်း
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
        
        # HTML ဖြင့် တိုက်ရိုက်ပို့ခြင်း (Underscore ပြဿနာ မရှိတော့ပါ)
        bot.send_message(target_id, delivery_text)
        bot.reply_to(message, f"✅ User <code>{target_id}</code> ထံ ပစ္စည်းပို့ဆောင်ပြီးပါပြီ၊၊")
        
    except Exception as e:
        bot.reply_to(message, f"❌ ပို့ဆောင်မှု မအောင်မြင်ပါ- {e}")

@bot.message_handler(commands=['open', 'close', 'maintenance'])
def change_status(message):
    if str(message.from_user.id) != str(ADMIN_ID): return

    status = message.text[1:] # /open ဆိုရင် open လို့ယူမယ်
    
    import sqlite3
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'shop_status'", (status,))
        conn.commit()
    
    status_msg = {
        'open': "✅ ဆိုင်ကို ပြန်ဖွင့်လိုက်ပါပြီ၊၊",
        'close': "🛑 ဆိုင်ကို ပိတ်လိုက်ပါပြီ၊၊",
        'maintenance': "🛠 Bot ကို Maintenance Mode ပြောင်းလိုက်ပါပြီ၊၊"
    }
    bot.reply_to(message, status_msg.get(status, "Status updated!"))

# Announcement ပို့သည့် Command
@bot.message_handler(commands=['announcement'])
def broadcast(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    
    text_to_send = message.text.replace('/announcement', '').strip()
    if not text_to_send:
        bot.reply_to(message, "💡 သုံးနည်း: /announcement [စာသား]")
        return

    # User အားလုံးဆီ ပို့ရန် (Database မှ user_id အားလုံးကို ဆွဲထုတ်ပါ)
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM orders") # ဝယ်ဖူးသူအားလုံးဆီ ပို့ခြင်း
        users = cursor.fetchall()

    count = 0
    for user in users:
        try:
            bot.send_message(user[0], f"📢 <b>ANNOUNCEMENT</b>\n\n{text_to_send}", parse_mode='HTML')
            count += 1
        except: continue
    
    bot.reply_to(message, f"✅ User {count} ယောက်ဆီ ပို့ဆောင်ပြီးပါပြီ၊၊")

def set_bot_commands(bot):
    # ၁။ User အားလုံးအတွက် ပြမည့် Command များ
    user_commands = [
        telebot.types.BotCommand("start", " Bot ကိုစတင်ရန"),
        telebot.types.BotCommand("help", "❓ အကူအညီရယူရန်"),
        telebot.types.BotCommand("home", "🏠 ပင်မစာမျက်နှာသိုသွားရန်")
    ]
    bot.set_my_commands(user_commands, scope=telebot.types.BotCommandScopeAllPrivateChats())

    # ၂။ Admin အတွက်သာ သီးသန့်ပြမည့် Command များ
    admin_commands = user_commands + [
        telebot.types.BotCommand("open", "✅ ဆိုင်ဖွင့်မည်"),
        telebot.types.BotCommand("close", "🛑 ဆိုင်ပိတ်မည်"),
        telebot.types.BotCommand("maintenance", "🛠 Maintenance Mode"),
        telebot.types.BotCommand("announcement", "📢 Announcement ပို့မည်"),
        telebot.types.BotCommand("send", "✉️ ပစ္စည်း ပို့ဆောင်မည်")
    ]
    
    # Admin ID အတွက်သာ scope သတ်မှတ်ခြင်း
    bot.set_my_commands(
        admin_commands, 
        scope=telebot.types.BotCommandScopeChat(chat_id=ADMIN_ID)
    )

# main ထဲမှာ bot စပွင့်တာနဲ့ ဒီ function ကို ခေါ်လိုက်ပါ
set_bot_commands(bot)

# ၄။ Bot ကို စတင်ခြင်း
if __name__ == "__main__":
    print("🤖 Bot is running with HTML mode...")
    # infinity_polling သည် error တက်သော်လည်း bot မရပ်သွားအောင် ကာကွယ်ပေးသည်
    bot.infinity_polling(timeout=10, long_polling_timeout=5)