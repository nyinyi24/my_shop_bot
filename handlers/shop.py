import telebot
from config import DATABASE_NAME
from telebot import types
from database import get_all_items, get_item_by_id
from datetime import datetime
from config import ADMIN_ID
from database import get_shop_status
import pytz

def is_shop_open():
    # မြန်မာနိုင်ငံ၏ အချိန်ဇုန်ကို သတ်မှတ်ပါ
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz)
    current_hour = now.hour # ၂၄ နာရီ format (0-23)

    # မနက် ၉ နာရီ (9) မှ ည ၉ နာရီ (21) အထိ ဖွင့်မည်
    if 9 <= current_hour < 21:
        return True
    return False

def init_shop_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'shop')
    def shop_callback(call):
        status = get_shop_status()

        # ၁။ Maintenance Mode စစ်ခြင်း
        if status == 'maintenance' and str(call.from_user.id) != str(ADMIN_ID):
            bot.answer_callback_query(call.id, "🛠 Bot ကို ပြုပြင်နေပါသည်၊၊", show_alert=True)
            bot.edit_message_text(
                "🛠 <b>Bot is Under Maintenance</b>\n\nခေတ္တပြုပြင်နေပါသဖြင့် မည်သည့် Feature ကိုမျှ အသုံးပြု၍ မရနိုင်သေးပါ၊၊",
                call.message.chat.id, call.message.message_id, parse_mode='HTML'
            )
            return  # အရင်က ဒီ return က အပြင်မှာ ရောက်နေလို့ အောက်ကို ဆက်မသွားတာပါ!

        # ၂။ Admin က Manual ပိတ်ထားခြင်း (/close) စစ်ခြင်း
        if status == 'close':
            admin_closed_text = (
                "🛑 <b>Shop is Closed Today</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ယနေ့ ဆိုင်ပိတ်ထားပါတယ်ခင်ဗျာ၊၊\n\n"
                "နောက်ရက်မှ ပြန်လည် အားပေးပါရန် ဖိတ်ခေါ်အပ်ပါတယ်၊၊ ကျေးဇူးတင်ပါတယ်ဗျ၊၊ 🙏"
            )
            bot.answer_callback_query(call.id, "ယနေ့ ဆိုင်ပိတ်ပါသည်", show_alert=True)
            bot.edit_message_text(admin_closed_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            return

        # ၃။ ညဘက် ဆိုင်ပိတ်ချိန်စနစ် (အိုင်ဒီယာသစ် Pre-Order စနစ်)
        if not is_shop_open():
            time_closed_text = (
                "🌙 <b>Shop is Currently Closed (Pre-Order Available)</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ယခုအချိန်သည် Admin အနားယူချိန် ဖြစ်ပါသဖြင့် ပုံမှန် Auto-Delivery စနစ်ကို ခေတ္တပိတ်ထားပါသည်၊၊\n\n"
                "🕒 <b>ဆိုင်ဖွင့်ချိန်:</b> 09:00 AM - 09:00 PM\n\n"
                "💡 <b>ဒါပေမဲ့ စိတ်မပူပါနဲ့ခင်ဗျာ!</b>\n"
                "သင်အခုပဲ <b>Pre-Order (ကြိုတင်မှာယူခြင်း)</b> စနစ်ဖြင့် ငွေပေးချေပြီး အော်ဒါတင်ထားနိုင်ပါတယ်၊၊ "
                "မနက်ဖြန် ဆိုင်ဖွင့်တာနဲ့ Admin ဘက်က အကောင့်များကို ဦးစားပေးစနစ်ဖြင့် ချက်ချင်း ပို့ဆောင်ပေးသွားမှာ ဖြစ်ပါသည်ဗျာ၊၊ 🙏\n\n"
                "👇 ကြိုတင်မှာယူလိုပါက အောက်ကခလုတ်ကို နှိပ်ပြီး ဆက်သွားနိုင်ပါတယ်-"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📝 Pre-Order တင်ရန် ဆက်သွားမည်", callback_data="force_open_catalog"))
            markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
            
            bot.answer_callback_query(call.id, "ဆိုင်ပိတ်ချိန်ဖြစ်သော်လည်း Pre-Order တင်နိုင်ပါသည်", show_alert=True)
            bot.edit_message_text(time_closed_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
            return

        # ၄။ ပုံမှန်ဖွင့်ချိန်ဆိုလျှင် တိုက်ရိုက် Catalog ပြခြင်း
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        show_shop_catalog(call.from_user.id, bot)

    # ညဘက်အတင်းဖွင့်ခိုင်းသည့် Callback Handler
    @bot.callback_query_handler(func=lambda call: call.data == 'force_open_catalog')
    def force_catalog_callback(call):
        bot.answer_callback_query(call.id)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        show_shop_catalog(call.from_user.id, bot)

    # Item Detail ကြည့်ရှုသည့် Callback Handler
    @bot.callback_query_handler(func=lambda call: call.data.startswith('item_detail_'))
    def show_item_detail(call):
        item_id = int(call.data.split('_')[2])
        item = get_item_by_id(item_id)
        if not item:
            bot.answer_callback_query(call.id, "ပစ္စည်းရှာမတွေ့ပါ။")
            return

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("1 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_1"),
                   types.InlineKeyboardButton("2 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_2"))
        markup.add(types.InlineKeyboardButton("3 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_3"))
        markup.add(types.InlineKeyboardButton("⬅️ Back to Shop", callback_data='shop'))

        text = f"📦 *{item[1]}*\n\n" \
               f"📝 Details: {item[2]}\n" \
               f"💰 Price: {item[3]} MMK\n" \
               f"📦 Stock: {item[4]}\n\n" \
               f"ဝယ်ယူမည့် အရေအတွက်ကို ရွေးချယ်ပါ-"

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')


def show_shop_catalog(user_id, bot):
    items = get_all_items()
    markup = types.InlineKeyboardMarkup(row_width=1)

    if not items:
        markup.add(types.InlineKeyboardButton("⬅️ Back to Home", callback_data='home'))
        bot.send_message(user_id, "🛍️ လက်ရှိတွင် ရောင်းချရန် ပစ္စည်းမရှိသေးပါ။", reply_markup=markup)
        return

    for item in items:
        item_id = item[0]
        btn_text = f"{item[1]} - {item[3]} MMK"
        # တိုက်ရိုက် buy_ သို့မဟုတ် item_detail_ ပြောင်းလဲနိုင်သည် (လက်ရှိ buy_ သို့ တိုက်ရိုက်လွှဲထားသည်)
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{item_id}"))
    
    markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
    bot.send_message(user_id, "🛍️ *Our Products:*\n\nဝယ်ယူလိုသည့် ပစ္စည်းကို ရွေးချယ်ပါ-", 
                     reply_markup=markup, parse_mode='Markdown')