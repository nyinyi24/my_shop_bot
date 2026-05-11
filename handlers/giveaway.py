import telebot
from telebot import types
import datetime
from database import (
    get_all_gw_item_types, get_user_last_gw_claim, 
    add_gw_claim, get_available_gw_items_by_type, mark_gw_item_as_used
)

def init_giveaway_handlers(bot):
    
    def show_giveaway_options(user_id, bot):
        """Giveaway ပစ္စည်းစာရင်းကို ပြသခြင်း (Back ခလုတ် အမြဲပါဝင်စေရမည်)"""
        gw_types = get_all_gw_item_types()
        
        # Back to Home ခလုတ်ကို အရင်ပြင်ဆင်ပါ
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("🏠 Back to Home", callback_data='home')

        # ၁။ ပစ္စည်းမရှိလျှင် Back ခလုတ်တစ်ခုတည်းဖြင့် ပြန်လှည့်မည်
        if not gw_types:
            markup.add(back_btn)
            bot.send_message(user_id, "🎁 လက်ရှိတွင် Giveaway အစီအစဉ်မရှိသေးပါ။", reply_markup=markup)
            return

        # ၂။ ပစ္စည်းရှိလျှင် စာရင်းများပြပြီး အောက်ဆုံးတွင် Back ခလုတ်ထည့်မည်
        for gt in gw_types:
            markup.add(types.InlineKeyboardButton(f"🎁 {gt}", callback_data=f"claim_gw_{gt}"))
        
        markup.add(back_btn)
        bot.send_message(user_id, "🎁 *Available Giveaways:*\n\nကံစမ်းလိုသည့် အမျိုးအစားကို ရွေးချယ်ပါ-", 
                         reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data == 'giveaway')
    def giveaway_callback(call):
        user_id = call.from_user.id
        from handlers.start import check_subscription
        
        # Channel Join မ Join စစ်ဆေးခြင်း
        is_joined = check_subscription(user_id, bot)
        
        if not is_joined:
            # Join မထားလျှင် Error Alert ပြပြီး Join ရန် ခလုတ်ပြမည်
            bot.answer_callback_query(call.id, "❌ Verify fail! Channel ကို မ join ရသေးပါ၊၊", show_alert=True)
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 Join Our Channel", url="https://t.me/ENIpremiumstore")) # သင့် link
            markup.add(types.InlineKeyboardButton("✅ Verify & Continue", callback_data='giveaway'))
            markup.add(types.InlineKeyboardButton("🏠 Back to Home", callback_data='home'))

            # စာသားဟောင်းကို Update လုပ်ပြမည် (ထပ်ခါထပ်ခါ မပေါ်စေရန်)
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="🎁 Giveaway ရယူရန် ကျွန်ုပ်တို့၏ Channel ကို အရင် Join ပေးပါ၊၊",
                    reply_markup=markup
                )
            except:
                pass
            return

        # Join ပြီးသား User ဖြစ်လျှင် Giveaway Options ပြမည်
        bot.answer_callback_query(call.id, "✅ အတည်ပြုပြီးပါပြီ၊၊")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_giveaway_options(user_id, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('claim_gw_'))
    def claim_giveaway(call):
        user_id = call.from_user.id
        item_type = call.data.split('claim_gw_')[1]
        now = datetime.datetime.now()

    # ၁။ နောက်ဆုံးယူခဲ့သည့်အချိန်ကို စစ်ဆေးခြင်း (ရက်သတ္တပတ်အလိုက်)
    # database.py ထဲတွင် get_user_last_gw_claim ဆိုသည့် function ရှိရပါမည်
        last_claim_time = get_user_last_gw_claim(user_id) 

        if last_claim_time:
            # စာသားကို datetime object အဖြစ်ပြောင်းလဲခြင်း
            last_date = datetime.datetime.strptime(last_claim_time, "%Y-%m-%d %H:%M:%S")
            
            # ၇ ရက် (၁ ပတ်) မပြည့်သေးပါက ငြင်းပယ်မည်
            if now < last_date + datetime.timedelta(days=7):
                next_available = last_date + datetime.timedelta(days=7)
                wait_time = next_available - now
                days = wait_time.days
                hours = wait_time.seconds // 3600
                
                bot.answer_callback_query(
                    call.id, 
                    f"❌ သင်သည် ဤအပတ်အတွက် Giveaway ယူပြီးပါပြီ၊၊ \n\nနောက်ထပ် {days} ရက် {hours} နာရီ စောင့်ပေးပါဦးဗျာ၊၊", 
                    show_alert=True
                )
                return

    # ၂။ ပစ္စည်းရှိမရှိ စစ်ဆေးခြင်း
        item = get_available_gw_items_by_type(item_type)
        if item:
            # အောင်မြင်လျှင် ပစ္စည်းပေးမည်
            delivery_text = (
                "🎉 <b>Congratulations!</b>\n\n"
                f"📦 <b>{item_type}</b> ရရှိပါပြီ:\n\n"
                f"<code>{item[2]}</code>\n\n"
                "⚠️ ဤအချက်အလက်ကို သေချာစွာ သိမ်းဆည်းထားပါ၊၊ ၁ ပတ်လျှင် တစ်ကြိမ်သာ ယူခွင့်ရှိပါသည်၊၊"
            )
            
            bot.send_message(user_id, delivery_text, parse_mode='HTML')
            
            # Database status များ update လုပ်ခြင်း
            mark_gw_item_as_used(item[0])
            add_gw_claim(user_id, now.strftime("%Y-%m-%d %H:%M:%S"))
            
            bot.answer_callback_query(call.id, "✅ အောင်မြင်စွာ ရယူပြီးပါပြီ၊၊")
        else:
            bot.answer_callback_query(call.id, "😔 စိတ်မကောင်းပါဘူး၊ ပစ္စည်းကုန်သွားပါပြီ၊၊", show_alert=True)