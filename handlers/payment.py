import telebot
from telebot import types
import datetime
import re
import sqlite3
from config import ADMIN_ID, SUPPORT_URL
from database import get_item_by_id, update_order_status, create_order, get_order_details, update_order_delivery, pull_account_from_stock_by_name, get_user_orders

# ယာယီ အော်ဒါမှတ်တမ်းများကို သိမ်းရန်
pending_orders = {}

def init_payment_handlers(bot):
    
    # ၁။ ဝယ်ယူမည့် ခလုတ်ကို နှိပ်ခြင်း (ID system သုံးထားသည်)
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

        # ၁။ Screenshot အရ Index များကို ယူခြင်း
            item_name = item[1]         
            short_detail = item[2]      
            raw_price_str = str(item[3]).replace(',', '') 
            product_info = item[6] if len(item) > 6 and item[6] else "အသေးစိတ် အချက်အလက် မရှိသေးပါ၊၊"

        # ၂။ ဈေးနှုန်းတွက်ချက်ခြင်း
            price_per_item = int(float(raw_price_str))
            total_price = price_per_item * quantity
            
            # ၃။ ကော်မာ ထည့်ပြီး Format လုပ်ခြင်း
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
            f"🔢 <b>အရေအတွက်:</b> {quantity} ခု\n"
            f"💵 <b>တစ်ခုဈေး:</b> <code>{formatted_price}</code> MMK\n"
            f"💰 <b>စုစုပေါင်း:</b> <code>{formatted_total}</code> MMK\n\n"
            
            f"📝 <b>Product Details:</b>\n"
            f"{product_info}\n\n"
            
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👇 <b>ငွေပေးချေမည့် နည်းလမ်းကို ရွေးချယ်ပါ:</b>"
        )
        
        # ၂။ parse_mode ကို 'HTML' ဟု ပြောင်းပါ
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

        except Exception as e:
            print(f"Buy Button Error: {e}")
            bot.answer_callback_query(call.id, "❌ အမှားအယွင်းတစ်ခု ဖြစ်ပွားခဲ့ပါသည်၊၊")

    # ၂။ ငွေပေးချေမှု နည်းလမ်း ရွေးချယ်ခြင်း
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
    def handle_payment_method(call):
        parts = call.data.split('_')
        method, item_id, qty = parts[1], int(parts[2]), int(parts[3])
        user_id = call.from_user.id
        item = get_item_by_id(item_id)
        total_amount = item[3] * qty
        formatted_total = f"{int(total_amount):,}" # ဒီမှာ သုံးပါ
        
        if not item: return

        # အော်ဒါအသစ် ဆောက်ခြင်း
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_id = create_order(user_id, item[1], qty, method.upper(), "Pending", timestamp)
        
        # ယာယီ သိမ်းဆည်းခြင်း
        pending_orders[user_id] = {
            "order_id": order_id, 
            "item_name": item[1], 
            "qty": qty, 
            "total": item[3]*qty, 
            "method": method.upper()
        }

        text = (
            f"✅ *{method.upper()}* ကို ရွေးချယ်ထားပါတယ်၊၊\n\n"
            f"💰 ကျသင့်ငွေ: {formatted_total} MMK\n"
            f"🆔 Order ID: `#{order_id}`\n\n"
            f"📍 *ငွေလွှဲရန်:* `09975374020` (NNML)\n\n"
            f"ငွေလွှဲပြီးပါက ပြေစာ Screenshot ကို ပို့ပေးပါ၊၊"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎧 Support", url=SUPPORT_URL), 
                   types.InlineKeyboardButton("❌ Cancel", callback_data='home'))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    # ၃။ Screenshot လက်ခံခြင်း
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

        admin_text = (
            f"🔔 *New Order Alert!*\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📦 Item: {order_data['item_name']}\n"
            f"💰 Amount: {order_data['total']:,} MMK\n"
            f"💳 Method: {order_data['method']}\n"
            f"🆔 Order ID: {order_data['order_id']}"
        )
        # Admin ထံ ပို့ခြင်း
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_text, reply_markup=markup, parse_mode='Markdown')
        success_text = (
            "✅ Screenshot ပေးပို့မှု အောင်မြင်ပါသည်၊၊\n\n"
            "ကျွန်ုပ်တို့၏ Admin မှ သင်၏ ငွေလွှဲပြေစာကို စစ်ဆေးနေပါပြီ၊၊ "
            "စစ်ဆေးပြီးပါက အကောင့်အချက်အလက်များကို ဤနေရာသို့ အလိုအလျောက် ပို့ဆောင်ပေးသွားမည် ဖြစ်ပါသည်၊၊\n\n"
            "⏳ ခေတ္တစောင့်ဆိုင်းပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်၊၊"
            )
        bot.send_message(user_id, success_text)
        del pending_orders[user_id]

    # ၄။ Admin ၏ ဆုံးဖြတ်ချက် (Approve/Reject)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def admin_action(call):
        # ၁။ ခလုတ်နှိပ်လိုက်တာနဲ့ ချက်ချင်း တုံ့ပြန်မှုပေးပါ (ဒါဆိုရင် နှိပ်ရတာ မြန်သွားပါမယ်)
        bot.answer_callback_query(call.id, "ခေတ္တစောင့်ဆိုင်းပါ...")

        parts = call.data.split('_')
        action, order_id = parts[1], int(parts[2])
        caption = call.message.caption
        
        try:
            # Regex သုံးပြီး User ID နဲ့ Item Name ကို ဆွဲထုတ်ခြင်း
            target_user_id = int(re.search(r'User ID:.*?(\d+)', caption).group(1))
            item_name = re.search(r'Item: (.*)', caption).group(1).strip()
        except Exception as e:
            print(f"Admin Action Error (Data parsing): {e}")
            return

        if action == "approve":
            # Database ထဲက အော်ဒါအသေးစိတ်ကို ယူခြင်း
            order = get_order_details(order_id)
            if not order:
                bot.send_message(call.message.chat.id, "❌ အော်ဒါအချက်အလက် ရှာမတွေ့ပါ၊၊")
                return

            # Stock ထဲမှ အကောင့်ကို နှိုက်ယူခြင်း
            account_data = pull_account_from_stock_by_name(item_name)
            
            if account_data:
                # Database status များကို Update လုပ်ခြင်း
                update_order_status(order_id, "Success")
                update_order_delivery(order_id, account_data)
                
                # Admin Message တွင် status ပြောင်းလဲခြင်း
                bot.edit_message_caption(caption + "\n\n✅ *Status: Auto-Delivered*", 
                                         call.message.chat.id, call.message.message_id, parse_mode='Markdown')
                
                # ၂။ User ဆီကို ပို့မည့် စာသားအသစ် (ဒီစာသားကို သေချာ ပြန်စစ်ပေးပါ)
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
                    "အဆင်မပြေမှုရှိပါက Admin @independence\_N ကို ဆက်သွယ်ပါ၊၊"
                )
                
                # User ထံ စာပို့ခြင်း
                bot.send_message(target_user_id, delivery_msg, parse_mode='Markdown')
                print(f"✅ Order #{order_id} delivered to {target_user_id}")
                
            else:
                # Stock ကုန်နေလျှင် Admin ကို အကြောင်းကြားခြင်း
                bot.send_message(call.message.chat.id, 
                                f"⚠️ {item_name} အတွက် အကောင့်ကုန်နေသဖြင့် Manual ပို့ပေးရန် လိုအပ်ပါသည်၊၊\n\n"
                                f"ပုံစံ- `/send {target_user_id} [Mail:Pass]`")
        
        elif action == "reject":
            update_order_status(order_id, "Rejected")
            bot.edit_message_caption(caption + "\n\n❌ *Status: Rejected*", 
                                     call.message.chat.id, call.message.message_id)
            
            reject_msg = (
                    f"❌ သင်၏ Order ID: #{order_id} ကို ငြင်းပယ်လိုက်ပါတယ်၊၊\n\n"
                    "အဆင်မပြေမှု တစ်စုံတစ်ရာ ရှိပါက Menu မှတစ်ဆင့် Home Page သို့သွားပြီး "
                    "Support ခလုတ်ကိုနှိပ်၍ Admin ကို တိုက်ရိုက်ဆက်သွယ် မေးမြန်းနိုင်ပါတယ်ဗျာ၊၊"
                )
            bot.send_message(target_user_id, reject_msg)
            bot.answer_callback_query(call.id, "❌ Order ကို ငြင်းပယ်လိုက်ပါပြီ")
    # ၅။ My Orders ပြသခြင်း
    @bot.callback_query_handler(func=lambda call: call.data == 'my_orders')
    def my_orders(call):
        orders = get_user_orders(call.from_user.id)
        markup = types.InlineKeyboardMarkup(row_width=1)

        if not orders:
            markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
            bot.edit_message_text("🛒 *ဝယ်ယူထားသည့် မှတ်တမ်းမရှိသေးပါ၊၊*", 
                                call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
            return

        text = "🛒 *သင်ဝယ်ယူထားသည့် အော်ဒါများ:*\n\nအသေးစိတ်ကြည့်ရန် အော်ဒါကို နှိပ်ပါ-"
        for o in orders:
            # o[0]=id, o[2]=item_name, o[6]=timestamp
            btn_text = f"📦 {o[2]} ({o[6].split()[0]})"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_order_{o[0]}"))
        
        markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    # ၆။ အော်ဒါအသေးစိတ် ကြည့်ရှုခြင်း (Mail:Pass ပြန်ကြည့်ရန်)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_order_'))
    def view_order_detail(call):
        try:
            order_id = int(call.data.split('_')[2])
            order = get_order_details(order_id)
            
            if order:
                # Table column index အလိုက် (o[7] သည် delivered_data ဖြစ်ရမည်)
                acc_info = order[7] if len(order) > 7 and order[7] else "အချက်အလက်မရှိပါ (Manual ပို့ထားသော အော်ဒါဖြစ်နိုင်သည်)"
                
                detail_text = (
                    f"📄 *Order Detail* (ID: #{order[0]})\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📦 *Item:* {order[2]}\n"
                    f"📅 *Date:* {order[6]}\n"
                    f"💰 *Status:* {order[5]}\n\n"
                    f"📧 *Account Info:* \n`{acc_info}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"⚠️ အကယ်၍ အကောင့်ဝင်မရပါက Admin ကို ဆက်သွယ်ပါ၊၊"
                )
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⬅️ Back to List", callback_data='my_orders'))
                bot.edit_message_text(detail_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            print(f"View Order Error: {e}")