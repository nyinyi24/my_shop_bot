import telebot
from telebot import types
from datetime import datetime
import pytz
from config import ADMIN_ID, DATABASE_NAME
from database import get_all_items, get_item_by_id, get_shop_status

def is_shop_open():
    """ဆိုင်ဖွင့်ချိန် (09:00 AM - 09:00 PM) ဟုတ်မဟုတ် စစ်ဆေးခြင်း"""
    try:
        tz = pytz.timezone('Asia/Yangon')
        now = datetime.now(tz)
        current_hour = now.hour
        if 9 <= current_hour < 21:
            return True
        return False
    except:
        # pytz error တက်ပါက ပုံမှန်အတိုင်း ဖွင့်ပေးထားမည်
        return True

def show_shop_catalog(user_id, bot, message_id=None):
    """ပစ္စည်းစာရင်း (Catalog) ကို ပြသခြင်း"""
    items = get_all_items()
    markup = types.InlineKeyboardMarkup(row_width=1)

    if not items:
        markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
        text = "🛍️ လက်ရှိတွင် ရောင်းချရန် ပစ္စည်းမရှိသေးပါ။"
    else:
        for item in items:
            item_id = item[0]
            name = item[1]
            price = item[3]
            stock = item[4]
            btn_text = f"{name} - {price} MMK ({stock} left)"
            # detail ကြည့်ရန် callback_data ကို item_detail_ ဟု ပေးမည်
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"item_detail_{item_id}"))
        
        markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
        text = "🛍️ <b>Our Products:</b>\n\nဝယ်ယူလိုသည့် ပစ္စည်းကို ရွေးချယ်ပါ-"

    if message_id:
        bot.edit_message_text(text, user_id, message_id, reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')

def init_shop_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'shop')
    def shop_callback(call):
        user_id = call.from_user.id
        status = get_shop_status()

        # ၁။ Maintenance Mode စစ်ခြင်း
        if status == 'maintenance' and str(user_id) != str(ADMIN_ID):
            bot.answer_callback_query(call.id, "🛠 Bot ကို ပြုပြင်နေပါသည်၊၊", show_alert=True)
            return

        # ၂။ Admin က Manual ပိတ်ထားခြင်း စစ်ခြင်း
        if status == 'close' and str(user_id) != str(ADMIN_ID):
            admin_closed_text = (
                "🛑 <b>Shop is Closed Today</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ယနေ့ ဆိုင်ပိတ်ထားပါတယ်ခင်ဗျာ၊၊\n\n"
                "နောက်ရက်မှ ပြန်လည် အားပေးပါရန် ဖိတ်ခေါ်အပ်ပါတယ်၊၊ 🙏"
            )
            bot.answer_callback_query(call.id, "ယနေ့ ဆိုင်ပိတ်ပါသည်", show_alert=True)
            bot.edit_message_text(admin_closed_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            return

        # ၃။ အချိန်ဇယားအရ ဆိုင်ပိတ်ချိန် စစ်ခြင်း
        if not is_shop_open() and str(user_id) != str(ADMIN_ID):
            time_closed_text = (
                "🌙 <b>Shop is Currently Closed</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ယခုအချိန်သည် Admin အနားယူချိန် ဖြစ်ပါသဖြင့် ဆိုင်ခေတ္တ ပိတ်ထားပါသည်၊၊\n\n"
                "🕒 <b>ဆိုင်ဖွင့်ချိန်:</b> 09:00 AM - 09:00 PM\n\n"
                "မနက် ၉ နာရီ ကျမှ ပြန်လည် ဝယ်ယူနိုင်ပါမည်။ 😊"
            )
            bot.answer_callback_query(call.id, "ဆိုင်ပိတ်ချိန်ဖြစ်ပါသည်", show_alert=True)
            bot.edit_message_text(time_closed_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            return

        # ၄။ Catalog ပြခြင်း
        bot.answer_callback_query(call.id)
        show_shop_catalog(user_id, bot, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('item_detail_'))
    def show_item_detail(call):
        try:
            item_id = int(call.data.split('_')[2])
            item = get_item_by_id(item_id)
            if not item:
                bot.answer_callback_query(call.id, "❌ ပစ္စည်းရှာမတွေ့ပါ။", show_alert=True)
                return

            markup = types.InlineKeyboardMarkup(row_width=2)
            # ဝယ်ယူမည့် အရေအတွက် ခလုတ်များ
            markup.add(
                types.InlineKeyboardButton("1 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_1"),
                types.InlineKeyboardButton("2 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_2"),
                types.InlineKeyboardButton("3 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_3")
            )
            markup.add(types.InlineKeyboardButton("⬅️ Back to Shop", callback_data='shop'))

            text = (
                f"📦 <b>{item[1]}</b>\n\n"
                f"📝 <b>Details:</b> {item[2]}\n"
                f"💰 <b>Price:</b> {item[3]} MMK\n"
                f"📦 <b>Stock:</b> {item[4]}\n\n"
                f"ဝယ်ယူမည့် အရေအတွက်ကို ရွေးချယ်ပါ-"
            )

            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        except Exception as e:
            print(f"Error in show_item_detail: {e}")
            bot.answer_callback_query(call.id, "Error occurred!")
