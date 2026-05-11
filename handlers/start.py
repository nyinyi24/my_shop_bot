import telebot
from telebot import types
import datetime
from config import YOUR_CHANNEL_ID, SUPPORT_URL
from database import add_user, get_user

def check_subscription(user_id, bot):
    """User က Channel ကို Join ထားခြင်း ရှိ/မရှိ စစ်ဆေးခြင်း"""
    try:
        status = bot.get_chat_member(YOUR_CHANNEL_ID, user_id).status
        return status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def show_home_menu(user_id, first_name, bot):
    """ပင်မ Menu နှင့် Welcome Message ကို ပြသခြင်း"""
    # Markdown Error မတက်အောင် underscore ရှေ့မှာ \ ခံထားပါသည်
    welcome_text = (
        f"👋 မင်္ဂလာပါ *{first_name}* ရေ...\n\n"
        f"🏰 *ENI Premium Store* မှ နွေးထွေးစွာ ကြိုဆိုပါတယ်ဗျာ။\n\n"
        f"🤖 *ကျွန်ုပ်တို့၏ Bot သည်:*\n"
        f"🔹 Premium Account များကို သက်သာသော ဈေးနှုန်းဖြင့် ဝယ်ယူနိုင်ခြင်း\n"
        f"🔹 လစဉ် Giveaway အစီအစဉ်များတွင် ပါဝင်ကံစမ်းနိုင်ခြင်း\n"
        f"🔹 လုံခြုံစိတ်ချရသော ငွေပေးချေမှုစနစ်များဖြင့် ဝန်ဆောင်မှုပေးနေပါသည်၊၊\n\n"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛍️ Shop", callback_data='shop'),
        types.InlineKeyboardButton("🎁 Giveaway", callback_data='giveaway'),
        types.InlineKeyboardButton("🛒 My Orders", callback_data='my_orders'),
        types.InlineKeyboardButton("🎧 Support", url="https://t.me/independence_N")
    )
    
    try:
        bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='Markdown')
    except:
        # Error တက်ပါက parse_mode မပါဘဲ ပို့မည်
        bot.send_message(user_id, welcome_text, reply_markup=markup)

def send_help(message, bot):
    """Help စာသားကို ပြသခြင်း"""
    help_text = (
        "❓ *အကူအညီလိုအပ်ပါသလား?*\n\n"
        "• ပစ္စည်းများကြည့်ရှုရန် /start သို့မဟုတ် *Shop* ကိုနှိပ်ပါ။\n"
        "• ပင်မစာမျက်နှာသို့ပြန်သွားရန် /home ကိုနှိပ်ပါ။\n"
        "• ဝယ်ယူထားသည်များကိုကြည့်ရန် *My Orders* ကိုနှိပ်ပါ။\n\n"
        "🎧 အခက်အခဲရှိပါက Admin @independence\_N သို့ တိုက်ရိုက်ဆက်သွယ်နိုင်ပါသည်၊၊"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Chat with Admin", url="https://t.me/independence_N"))
    
    try:
        bot.send_message(message.chat.id, help_text, reply_markup=markup, parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id, help_text, reply_markup=markup)

def init_start_handlers(bot):
    """Handler အားလုံးကို Register လုပ်ခြင်း"""
    
    @bot.message_handler(commands=["start"])
    def start_handler(message):
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        if not get_user(user_id):
            add_user(user_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        show_home_menu(user_id, first_name, bot)

    @bot.message_handler(commands=["home"])
    def home_handler(message):
        show_home_menu(message.from_user.id, message.from_user.first_name, bot)

    @bot.message_handler(commands=["help"])
    def help_handler(message):
        send_help(message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == 'verify_subscription')
    def verify_subscription_callback(call):
        user_id = call.from_user.id
        if check_subscription(user_id, bot):
            bot.answer_callback_query(call.id, "✅ အောင်မြင်ပါသည်၊၊")
            show_home_menu(user_id, call.from_user.first_name, bot)
        else:
            bot.answer_callback_query(call.id, "❌ Verify fail! Channel ကို အရင် Join ပေးပါ၊၊", show_alert=True)