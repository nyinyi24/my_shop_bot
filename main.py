import telebot
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

# ၄။ Bot ကို စတင်ခြင်း
if __name__ == "__main__":
    print("🤖 Bot is running with HTML mode...")
    # infinity_polling သည် error တက်သော်လည်း bot မရပ်သွားအောင် ကာကွယ်ပေးသည်
    bot.infinity_polling(timeout=10, long_polling_timeout=5)