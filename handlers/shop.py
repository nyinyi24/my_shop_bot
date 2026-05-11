import telebot
from telebot import types
from database import get_all_items, get_item_by_id

def init_shop_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'shop')
    def shop_callback(call):
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        show_shop_catalog(call.from_user.id, bot)

    # handlers/shop.py

def show_shop_catalog(user_id, bot):
    items = get_all_items()
    markup = types.InlineKeyboardMarkup(row_width=1) # ခလုတ်တွေကို တစ်တန်းချင်းစီပြရန်

    if not items:
        markup.add(types.InlineKeyboardButton("⬅️ Back to Home", callback_data='home'))
        bot.send_message(user_id, "🛍️ လက်ရှိတွင် ရောင်းချရန် ပစ္စည်းမရှိသေးပါ။", reply_markup=markup)
        return

    # ပစ္စည်းတစ်ခုချင်းစီအတွက် ခလုတ်များ
    # handlers/shop.py ထဲက show_shop_catalog function ထဲမှာ ပြင်ရန်
    for item in items:
        # item[0] သည် item_id ဖြစ်ရပါမည်
        item_id = item[0]
        btn_text = f"{item[1]} - {item[3]} MMK"
        # callback_data မှာ နာမည်အစား ID ကို သုံးမယ်
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{item_id}"))
    
    # --- ဒီနေရာမှာ Back to Home ခလုတ်ကို ထည့်ပေးရပါမယ် ---
    markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
    
    bot.send_message(user_id, "🛍️ *Our Products:*\n\nဝယ်ယူလိုသည့် ပစ္စည်းကို ရွေးချယ်ပါ-", 
                     reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('item_detail_'))
    def show_item_detail(call):
        item_id = int(call.data.split('_')[2])
        item = get_item_by_id(item_id)
        if not item:
            bot.answer_callback_query(call.id, "ပစ္စည်းရှာမတွေ့ပါ။")
            return

        markup = types.InlineKeyboardMarkup()
        # အရေအတွက် ရွေးချယ်ရန် ခလုတ်များ
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
