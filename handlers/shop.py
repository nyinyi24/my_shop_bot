import telebot
from telebot import types
from database import get_all_items, get_item_by_id, get_shop_status
from datetime import datetime
from config import ADMIN_ID
import pytz

def is_shop_open():
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz)
    current_hour = now.hour
    # မနက် ၉ နာရီ မှ ည ၉ နာရီ အထိ ဖွင့်မည်
    return 9 <= current_hour < 21

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
            return 

        # ၂။ Admin က Manual ပိတ်ထားခြင်း စစ်ခြင်း
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

        # ၃။ အချိန်ဇယားအရ ပိတ်ချိန် စစ်ခြင်း
        if not is_shop_open():
            time_closed_text = (
                "🌙 <b>Shop is Currently Closed</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ယခုအချိန်သည် Admin အနားယူချိန် ဖြစ်ပါသဖြင့် ဆိုင်ခေတ္တ ပိတ်ထားပါသည်၊၊\n\n"
                "🕒 <b>ဆိုင်ဖွင့်ချိန်:</b> 09:00 AM - 09:00 PM\n\n"
                "မနက် ၉ နာရီ ကျမှ ပြန်လည် ဝယ်ယူနိုင်ပါမည်။ ကျေးဇူးတင်ပါတယ်ဗျ၊၊ 😊"
            )
            bot.answer_callback_query(call.id, "ဆိုင်ပိတ်ချိန်ဖြစ်ပါသည်", show_alert=True)
            bot.edit_message_text(time_closed_text, call.message.chat.id, call.message.message_id, parse_mode='HTML')
            return

        # ၄။ အပေါ်က အခြေအနေများ ကင်းရှင်းမှ Catalog ပြမည်
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        show_shop_catalog(call.from_user.id, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('item_detail_'))
    def show_item_detail(call):
        item_id = int(call.data.split('_')[2])
        item = get_item_by_id(item_id)
        if not item:
            bot.answer_callback_query(call.id, "ပစ္စည်းရှာမတွေ့ပါ။")
            return

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("1 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_1"),
            types.InlineKeyboardButton("2 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_2")
        )
        markup.add(types.InlineKeyboardButton("3 ခု ဝယ်မည်", callback_data=f"buy_{item_id}_3"))
        markup.add(types.InlineKeyboardButton("⬅️ Back to Shop", callback_data='shop'))

        text = (
            f"📦 *{item[1]}*\n\n"
            f"📝 Details: {item[2]}\n"
            f"💰 Price: {item[3]} MMK\n"
            f"📦 Stock: {item[4]}\n\n"
            f"ဝယ်ယူမည့် အရေအတွက်ကို ရွေးချယ်ပါ-"
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=markup,
            parse_mode='Markdown'
        )

def show_shop_catalog(user_id, bot):
    items = get_all_items()
    markup = types.InlineKeyboardMarkup(row_width=1)

    if not items:
        markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
        bot.send_message(user_id, "🛍️ လက်ရှိတွင် ရောင်းချရန် ပစ္စည်းမရှိသေးပါ။", reply_markup=markup)
        return

    for item in items:
        item_id = item[0]
        btn_text = f"{item[1]} - {item[3]} MMK"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{item_id}"))

    markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
    bot.send_message(
        user_id,
        "🛍️ *Our Products:*\n\nဝယ်ယူလိုသည့် ပစ္စည်းကို ရွေးချယ်ပါ-",
        reply_markup=markup,
        parse_mode='Markdown'
    )