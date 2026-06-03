import telebot
from telebot import types
import datetime
import re
import sqlite3
from config import ADMIN_ID, SUPPORT_URL
from database import get_shop_status
from database import (
    get_item_by_id, update_order_status, create_order, 
    get_order_details, update_order_delivery, 
    pull_account_from_stock_by_name, get_user_orders, get_public_order_id
)

# ယာယီ အော်ဒါမှတ်တမ်းများကို သိမ်းရန်
pending_orders = {}


# =====================================================================
# 🌟 (၁) MANUAL DELIVERY FUNCTION (🚨 အပြင်ဘက်သို့ လုံးဝ ဆွဲထုတ်လိုက်ပါပြီ)
# =====================================================================
def process_manual_delivery(message, bot, target_user_id, item_name, order_id, original_caption, admin_msg_id):
    if str(message.from_user.id) != str(ADMIN_ID): return
    
    account_data = message.text.strip()
    
    # Database အား အောင်မြင်ကြောင်း အခြေအနေပြောင်းလဲခြင်း
    update_order_status(order_id, "Success")
    update_order_delivery(order_id, account_data)
    
    # Admin Chat ရှိ Message အား အခြေအနေ ပြောင်းလဲခြင်း
    try:
        bot.edit_message_caption(original_caption + "\n\n✅ *Status: Manual-Delivered*", 
                                 message.chat.id, admin_msg_id, parse_mode='Markdown')
    except Exception as e:
        print(f"Error editing admin caption: {e}")

    # ဝယ်သူထံသွားမည့် Message တွင် Review Button တွဲထည့်ခြင်း
    review_markup = types.InlineKeyboardMarkup()
    review_markup.add(
        types.InlineKeyboardButton("✍️ Review / Feedback ပေးရန်", callback_data="give_review")
    )

    delivery_msg = (
        "🎉 *သင်ဝယ်ယူထားသော ပစ္စည်းရောက်ရှိပါပြီ!*\n\n"
        f"📦 *Item:* {item_name}\n"
        f"📧 *Account Info:* \n`{account_data}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *အရေးကြီးသတိပေးချက်:*\n"
        "ယခုအော်ဒါသည် Manual စနစ်ဖြင့် ပို့ဆောင်ပေးထားခြင်း ဖြစ်သောကြောင့် "
        "ဝယ်ယူပြီးသည့် အချက်အလက်များကို *မိမိဘာသာ သီးသန့်သိမ်းဆည်းထားပါရန်* မေတ္တာရပ်ခံအပ်ပါသည်၊၊\n\n"
        "🙏 စနစ်ပိုင်းလိုအပ်ချက်ကြောင့် My Orders ထဲတွင် ဤအချက်အလက်များကို "
        "ပြန်လည်ကြည့်ရှု၍ မရနိုင်ခြင်းအတွက် အနူးအညွတ် တောင်းပန်အပ်ပါသည်၊၊\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "အဆင်မပြေမှုရှိပါက Admin @independence_N ကို ဆက်သွယ်ပါ၊၊"
    )
    
    # ဝယ်သူထံသို့ ပစ္စည်းပို့ဆောင်ခြင်း
    bot.send_message(target_user_id, delivery_msg, reply_markup=review_markup, parse_mode='Markdown')
    # Admin ထံသို့ အကြောင်းကြားစာ ပြန်ပြခြင်း
    bot.send_message(message.chat.id, f"✅ User <code>{target_user_id}</code> ထံ ပစ္စည်းကို Manual စနစ်ဖြင့် ပို့ဆောင်ပြီးပါပြီဗျာ၊၊", parse_mode='HTML')


# =====================================================================
# 🌟 (၂) PAYMENT HANDLERS
# =====================================================================
def init_payment_handlers(bot):
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def handle_buy_button(call):
        try:
            parts = call.data.split('_')
            item_id = int(parts[1])
            quantity = int(parts[2]) if len(parts) > 2 else 1
        
            item = get_item_by_id(item_id)
            if not item: 
                bot.answer_callback_query(call.id, "❌ ပစ္စည်း ရှာမတွေ့ပါ၊၊", show_alert=True)
                return

            item_name = item[1]         
            short_detail = item[2]      
            raw_price_str = str(item[3]).replace(',', '') 
            item_stock = item[4]
            product_info = item[5] if len(item) > 5 and item[5] else "Product details မရှိသေးပါ။"
            product_info = item[6] if len(item) > 6 and item[6] else "အသေးစိတ် အချက်အလက် မရှိသေးပါ၊၊"

            product_info = item[5] if len(item) > 5 and item[5] else product_info

            if item_stock <= 0:
                bot.answer_callback_query(call.id, "❌ စိတ်မရှိပါနဲ့ဗျာ၊ ဒီပစ္စည်းက Stock ပြတ်သွားပါပြီ၊၊", show_alert=True)
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⬅️ Back to Shop", callback_data="shop"))
                bot.edit_message_text(
                    f"⚠️ <b>{item_name}</b> က လက်ရှိမှာ Stock ပြတ်လပ်နေပါသည်၊၊\nAdmin ဘက်မှ Stock ပြန်ဖြည့်ပေးရန် ခေတ္တစောင့်ဆိုင်းပေးပါဦး၊၊",
                    call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML'
                )
                return

            if item_stock < quantity:
                bot.answer_callback_query(call.id, f"❌ လက်ကျန် {item_stock} ခုပဲ ရှိပါတော့တယ်ဗျာ၊၊", show_alert=True)
                return

            price_per_item = int(float(raw_price_str))
            total_price = price_per_item * quantity
            formatted_price = f"{price_per_item:,}"
            formatted_total = f"{total_price:,}"

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("KPay", callback_data=f"pay_kpay_{item_id}_{quantity}"),
                types.InlineKeyboardButton("Wave", callback_data=f"pay_wave_{item_id}_{quantity}"),
                types.InlineKeyboardButton("AYA Pay", callback_data=f"pay_aya_{item_id}_{quantity}")
            )
            markup.add(types.InlineKeyboardButton("⬅️ Back to Shop", callback_data="shop"))

            text = (
                f"💳 <b>Payment Confirmation</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 <b>ပစ္စည်း:</b> {item_name}\n"
                f"ℹ️ <b>အမျိုးအစား:</b> {short_detail}\n"
                f"📊 <b>လက်ကျန်:</b> {item_stock} ခု\n" 
                f"🔢 <b>ဝယ်ယူမည့် အရေအတွက်:</b> {quantity} ခု\n"
                f"💵 <b>တစ်ခုဈေး:</b> <code>{formatted_price}</code> MMK\n"
                f"💰 <b>စုစုပေါင်း:</b> <code>{formatted_total}</code> MMK\n\n"
                f"📝 <b>Product Details:</b>\n{product_info}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👇 <b>ငွေပေးချေမည့် နည်းလမ်းကို ရွေးချယ်ပါ:</b>"
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        except Exception as e:
            print(f"Buy Button Error: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
    def handle_payment_method(call):
        parts = call.data.split('_')
        method, item_id, qty = parts[1], int(parts[2]), int(parts[3])
        user_id = call.from_user.id
        item = get_item_by_id(item_id)
        if not item: return
        
        total_amount = item[3] * qty
        formatted_total = f"{int(total_amount):,}"
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_id = create_order(user_id, item[1], qty, method.upper(), "Pending", timestamp)
        order_code = get_public_order_id(get_order_details(order_id))
        
        pending_orders[user_id] = {
            "order_id": order_id,
            "order_code": order_code,
            "item_name": item[1], 
            "qty": qty, 
            "total": item[3]*qty, 
            "method": method.upper()
        }
        order_id = order_code

        text = (
            f"✅ *{method.upper()}* ကို ရွေးချယ်ထားပါတယ်၊၊\n\n"
            f"💰 ကျသင့်ငွေ: {formatted_total} MMK\n"
            f"🆔 Order ID: `{order_id}`\n\n"
            f"📍 *ငွေလွှဲရန်:* `09975374020` (NNML)\n\n"
            f"ငွေလွှဲပြီးပါက ပြေစာ Screenshot ကို ပို့ပေးပါ၊၊"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎧 Support", url=SUPPORT_URL), 
                   types.InlineKeyboardButton("❌ Cancel", callback_data='home'))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    @bot.message_handler(content_types=["photo"])
    def handle_screenshot(message):
        user_id = message.from_user.id
        if user_id not in pending_orders: return

        order_data = pending_orders[user_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{order_data['order_id']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{order_data['order_id']}")
        )

        order_data["order_id"] = order_data["order_code"]

        from handlers.shop import is_shop_open
        alert_title = "🔔 *New Order Alert!*" if is_shop_open() else "🌙 *New Pre-Order Alert (ညဘက်မှာယူမှု)!*"

        admin_text = (
            f"{alert_title}\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📦 Item: {order_data['item_name']}\n"
            f"💰 Amount: {order_data['total']:,} MMK\n"
            f"💳 Method: {order_data['method']}\n"
            f"🆔 Order ID: {order_data['order_id']}"
        )
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_text, reply_markup=markup, parse_mode='Markdown')
        
        if is_shop_open():
            success_text = (
                "✅ <b>Screenshot ပေးပို့မှု အောင်မြင်ပါသည်၊၊</b>\n\n"
                "ကျွန်ုပ်တို့၏ Admin မှ သင်၏ ငွေလွှဲပြေစာကို စစ်ဆေးနေပါပြီ၊၊ "
                "စစ်ဆေးပြီးပါက အကောင့်အချက်အလက်များကို ဤနေရာသို့ အလိုအလျောက် ပို့ဆောင်ပေးသွားမည် ဖြစ်ပါသည်၊၊\n\n"
                "⏳ ခေတ္တစောင့်ဆိုင်းပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်၊၊"
            )
        else:
            success_text = (
                "📝 <b>Pre-Order မှာယူမှု အောင်မြင်ပါသည်ဗျာ၊၊</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ငွေလွှဲပြေစာ Screenshot ပေးပို့မှု အောင်မြင်ပါသည်၊၊ ယခုအော်ဒါသည် ဆိုင်ပိတ်ချိန်အတွင်း "
                "မှာယူထားခြင်းဖြစ်သဖြင့် မနက်ဖြန် ဆိုင်ပြန်ဖွင့်ချိန် (မနက် ၉ နာရီ) ကျမှသာ Admin ဘက်က စစ်ဆေးပြီး "
                "<b>ပစ္စည်းကို အမြန်ဆုံး လှမ်းပို့ပေးသွားမှာ ဖြစ်ပါတယ်ပါတယ်ခင်ဗျာ၊၊</b>\n\n"
                "🙏 အနားယူချိန်စနစ်ကြောင့် ခေတ္တစောင့်ဆိုင်းရခြင်းအတွက် အနူးအညွတ် တောင်းပန်အပ်ပါသည်၊၊ "
                "ဝယ်ယူအားပေးမှုကို အထူးပင် ကျေးဇူးတင်ရှိပါသည်ဗျာ၊၊ 😊"
            )
        bot.send_message(user_id, success_text, parse_mode='HTML')
        del pending_orders[user_id]


# =====================================================================
# 🌟 (၃) REVIEW SYSTEM HANDLERS
# =====================================================================
def init_review_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'give_review')
    def ask_for_review_callback(call):
        bot.answer_callback_query(call.id)
        review_text = (
            "✍️ <b>Feedback & Review ပေးရန်</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "ENI Premium Store ကို အားပေးရတာ အဆင်ပြေရဲ့လားခင်ဗျာ၊၊ "
            "ဝန်ဆောင်မှုအပေါ် သဘောကျကျေနပ်မှု ရှိတယ်ဆိုရင် အောက်တွင် Review စာသားလေး (သို့မဟုတ်) "
            "အကြံပြုချက်လေးများကို ရိုက်ပြီး ပို့ပေးပါဦးဗျာ၊၊\n\n"
            "<i>(သင်ပို့လိုက်သော စာသားကို ကျွန်ုပ်တို့၏ Feedback Channel တွင် လူကြီးမင်း၏ နာမည်ကို ဖျောက်၍ အလိုအလျောက် တင်ပေးသွားမည် ဖြစ်ပါသည်)</i>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ မပေးတော့ပါ", callback_data='home'))
        msg = bot.edit_message_text(review_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        bot.register_next_step_handler(msg, process_user_review, bot)

    def process_user_review(message, bot):
        user_id = message.from_user.id
        user_name = message.from_user.first_name if message.from_user.first_name else "Customer"
        review_content = message.text.strip()
        
        if review_content.startswith('/'):
            bot.reply_to(message, "❌ Review ပေးခြင်းကို ဖျက်သိမ်းလိုက်ပါပြီ၊၊")
            return

        FEEDBACK_CHANNEL_ID = -1003923790039  
        channel_msg = (
            "🌟 <b>Review From Customer</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✍️ <i>\"{review_content}\"</i>\n\n"
            f"👤 <b>Buyer:</b> {user_name[0]}*** (Verified Buyer)\n"
            f"🏪 <b>Shop:</b> @ENIpremiumstore_bot\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        admin_msg = (
            "🔔 <b>Review အသစ်တစ်ခု ရောက်ရှိပါသည်!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>User:</b> {user_name} (ID: <code>{user_id}</code>)\n"
            f"📝 <b>Review:</b> {review_content}"
        )

        try: bot.send_message(FEEDBACK_CHANNEL_ID, channel_msg, parse_mode='HTML')
        except: pass
        try: bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
        except: pass

        thank_you_text = (
                "❤️ <b>ကျေးဇူးအများကြီး တင်ပါတယ်ဗျာ!</b>\n\n"
                "လူကြီးမင်းပေးခဲ့တဲ့ Review ဟာ ENI Premium Store ရဲ့ ဝန်ဆောင်မှုတွေကို "
                "ပိုမိုကောင်းမွန်လာအောင် ပြင်ဆင်ရာမှာ အများကြီး အထောက်အကူပြုပါတယ်ခင်ဗျာ၊၊ 🙏😊\n\n"
                "📣 အခြားသူများ၏ Review & Feedback များကိုလည်း <a href='https://t.me/ENIreviews'>ENI Reviews Channel</a> တွင် ဝင်ရောက်ကြည့်ရှုနိုင်ပါသည်ဗျာ၊၊"
            )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
        bot.send_message(user_id, thank_you_text, reply_markup=markup, parse_mode='HTML')


# =====================================================================
# 🌟 (၄) ADMIN ACTION HANDLERS
# =====================================================================
def init_admin_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def admin_action(call):
        bot.answer_callback_query(call.id, "ခေတ္တစောင့်ဆိုင်းပါ...")
        parts = call.data.split('_')
        action, order_id = parts[1], int(parts[2])
        caption = call.message.caption
        
        try:
            target_user_id = int(re.search(r'User ID:.*?(\d+)', caption).group(1))
            item_name = re.search(r'Item: (.*)', caption).group(1).strip()
        except Exception as e:
            print(f"Data parsing error: {e}")
            return

        if action == "approve":
            order = get_order_details(order_id)
            if not order:
                bot.send_message(call.message.chat.id, "❌ အော်ဒါအချက်အလက် ရှာမတွေ့ပါ၊၊")
                return

            account_data = pull_account_from_stock_by_name(item_name)
            if account_data:
                update_order_status(order_id, "Success")
                update_order_delivery(order_id, account_data)
                bot.edit_message_caption(caption + "\n\n✅ *Status: Auto-Delivered*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
                
                delivery_msg = (
                    "🎉 *သင်ဝယ်ယူထားသော ပစ္စည်းရောက်ရှိပါပြီ!*\n\n"
                    f"📦 *Item:* {item_name}\n"
                    f"📧 *Account Info:* \n`{account_data}`\n\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "⚠️ *အရေးကြီးသတိပေးချက်:*\n"
                    "ဝယ်ယူပြီးသည့် အချက်အလက်များကို *မိမိဘာသာ သီးသန့်သိမ်းဆည်းထားပါရန်* မေတ္တာရပ်ခံအပ်ပါသည်၊၊\n\n"
                    "🙏 စနစ်ပိုင်းလိုအပ်ချက်ကြောင့် My Orders ထဲတွင် ဤအချက်အလက်များကို "
                    "ပြန်လည်ကြည့်ရှု၍ မရနိုင်ခြင်းအတွက် အနူးအညွတ် တောင်းပန်အပ်ပါသည်၊၊\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "အဆင်မပြေမှုရှိပါက Admin @independence_N ကို ဆက်သွယ်ပါ၊၊"
                )
                review_markup = types.InlineKeyboardMarkup()
                review_markup.add(types.InlineKeyboardButton("✍️ Review / Feedback ပေးရန်", callback_data="give_review"))
                bot.send_message(target_user_id, delivery_msg, reply_markup=review_markup, parse_mode='Markdown')
            else:
                msg = bot.send_message(
                    call.message.chat.id,
                    f"⚠️ <b>{item_name}</b> အတွက် အကောင့်ကုန်နေသဖြင့် Manual ပို့ပေးရန် လိုအပ်ပါသည်၊၊\n\n"
                    f"<b>ဝယ်ယူသူထံ ပို့ပေးမည့် Account Info ကို အောက်တွင် တိုက်ရိုက်ရိုက်ပြီး ပို့ပေးပါဗျာ-</b>",
                    parse_mode='HTML'
                )
                # 🚨 ဤနေရာတွင် function အပြင်ထုတ်ထားသော process_manual_delivery ကို စနစ်တကျ လှမ်းခေါ်ထားပါသည်
                bot.register_next_step_handler(msg, process_manual_delivery, bot, target_user_id, item_name, order_id, caption, call.message.message_id)
                
        elif action == "reject":
            internal_order_id = order_id
            order_id = get_public_order_id(get_order_details(internal_order_id))
            update_order_status(internal_order_id, "Rejected")
            bot.edit_message_caption(caption + "\n\n❌ *Status: Rejected*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            reject_msg = f"❌ သင်၏ Order ID: {order_id} ကို ငြင်းပယ်လိုက်ပါတယ်၊၊"
            bot.send_message(target_user_id, reject_msg)


# =====================================================================
# 🌟 (၅) USER ORDER HISTORY HANDLERS
# =====================================================================
def init_order_history_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'my_orders')
    def my_orders(call):
        if get_shop_status() == 'maintenance' and str(call.from_user.id) != str(ADMIN_ID):
            return
        orders = get_user_orders(call.from_user.id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        if not orders:
            markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
            bot.edit_message_text("🛒 *ဝယ်ယူထားသည့် မှတ်တမ်းမရှိသေးပါ၊၊*", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
            return
        for o in orders:
            btn_text = f"📦 {o[2]} ({o[6].split()[0]})"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_order_{o[0]}"))
        markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
        bot.edit_message_text("🛒 *သင်ဝယ်ယူထားသည့် အော်ဒါများ:*", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_order_'))
    def view_order_detail(call):
        try:
            order_id = int(call.data.split('_')[2])
            order = get_order_details(order_id)
            if order:
                order = list(order)
                order[0] = get_public_order_id(order)
                acc_info = order[7] if len(order) > 7 and order[7] else "အချက်အလက်မရှိပါ"
                detail_text = f"📄 *Order Detail* (ID: {order[0]})\n📦 *Item:* {order[2]}\n📧 *Account Info:* \n`{acc_info}`"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⬅️ Back to List", callback_data='my_orders'))
                bot.edit_message_text(detail_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        except Exception as e: print(e)


# =====================================================================
# 🚀 ALL HANDLERS INITIALIZER (ပင်မ စုစည်းမှု စနစ်)
# =====================================================================
def init_all_handlers(bot):
    init_payment_handlers(bot)
    init_review_handlers(bot)
    init_admin_handlers(bot)
    init_order_history_handlers(bot)
