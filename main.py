import logging
from telebot import TeleBot, types

# बॉट सेटिंग्स
BOT_TOKEN = "7823545024:AAG7tyrhxhtwMTu2xKe47uzhK4SQHRkdmrc"
CHANNELS = ["@foraremy", "@comchater", "@Jyoex"]  # तीनों चैनल्स
REFERRAL_POINTS = 10                               # 1 रेफरल = 10 पॉइंट्स
CUSTOM_DEFAULT_MSG = "⚠️ कृपया नीचे दिए गए बटन्स का उपयोग करें! गलत कमांड मान्य नहीं हैं।"

bot = TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# डेटाबेस
users_db = {}
# Format: {user_id: {"points": 0, "referred_by": None, "referrals": 0, "bonus_credited": False}}

def check_all_subscriptions(user_id):
    """चेक करता है कि यूज़र ने तीनों चैनल्स जॉइन किए हैं या नहीं"""
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            # अगर बॉट चैनल में एडमिन नहीं है तो एरर से बचने के लिए
            logging.error(f"Error checking {ch}: {e}")
            return False
    return True

def get_main_keyboard():
    """मेन मेन्यू कीबोर्ड"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_balance = types.KeyboardButton("💰 My Points")
    btn_referral = types.KeyboardButton("🔗 Referral Link")
    btn_help = types.KeyboardButton("ℹ️ Help")
    markup.add(btn_balance, btn_referral, btn_help)
    return markup

def get_force_sub_keyboard():
    """तीनों चैनल्स के लिए जॉइन बटन्स"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for index, ch in enumerate(CHANNELS, start=1):
        clean_name = ch.replace('@', '')
        markup.add(types.InlineKeyboardButton(f"📢 Join Channel {index} ({ch})", url=f"https://t.me/{clean_name}"))
    markup.add(types.InlineKeyboardButton("✅ Check Joined (सत्यापित करें)", callback_data="check_sub"))
    return markup

# --- /start कमांड ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()

    # नया यूज़र रजिस्टर करना
    if user_id not in users_db:
        referred_by = None
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != user_id and ref_id in users_db:
                referred_by = ref_id
        
        users_db[user_id] = {
            "points": 0,
            "referred_by": referred_by,
            "referrals": 0,
            "bonus_credited": False
        }

    # Force Subscribe चेक
    if not check_all_subscriptions(user_id):
        bot.send_message(
            chat_id=user_id,
            text=f"👋 नमस्ते {message.from_user.first_name}!\n\nबॉट का उपयोग करने के लिए आपको हमारे **तीनों चैनल्स** को जॉइन करना अनिवार्य है:\n\n1. @foraremy\n2. @comchater\n3. @Jyoex\n\nतीनों जॉइन करने के बाद नीचे **Check Joined** दबाएं।",
            reply_markup=get_force_sub_keyboard(),
            parse_mode="Markdown"
        )
        return

    # रेफरल बोनस क्रेडिट
    credit_referral_bonus(user_id)

    bot.send_message(
        chat_id=user_id,
        text="🎉 आपका स्वागत है! नीचे दिए गए मेन्यू से विकल्प चुनें:",
        reply_markup=get_main_keyboard()
    )

def credit_referral_bonus(user_id):
    """रेफर करने वाले को बोनस पॉइंट्स देना"""
    user_data = users_db.get(user_id, {})
    ref_by = user_data.get("referred_by")
    if ref_by and not user_data.get("bonus_credited", False):
        if ref_by in users_db:
            users_db[ref_by]["points"] += REFERRAL_POINTS
            users_db[ref_by]["referrals"] += 1
            user_data["bonus_credited"] = True
            try:
                bot.send_message(ref_by, f"🎉 आपके रेफरल लिंक से एक नया यूज़र जुड़ा! आपको +{REFERRAL_POINTS} पॉइंट्स मिले।")
            except Exception:
                pass

# --- Check Button Callback ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    user_id = call.from_user.id
    if check_all_subscriptions(user_id):
        bot.answer_callback_query(call.id, "✅ वेरिफिकेशन सफल! सभी चैनल्स जॉइन हो गए।")
        try:
            bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        except Exception:
            pass
        
        credit_referral_bonus(user_id)
        bot.send_message(user_id, "🎉 स्वागत है! अब आप बॉट का इस्तेमाल कर सकते हैं:", reply_markup=get_main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ आपने अभी तक तीनों चैनल्स जॉइन नहीं किए हैं!", show_alert=True)

# --- मेन्यू बटन्स और कस्टम मैसेज हैंडलर ---
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id

    # पहले चेक करें कि तीनों चैनल्स में है या नहीं
    if not check_all_subscriptions(user_id):
        bot.send_message(
            chat_id=user_id,
            text="⚠️ बॉट का उपयोग करने के लिए पहले हमारे तीनों चैनल्स जॉइन करें:",
            reply_markup=get_force_sub_keyboard()
        )
        return

    text = message.text

    if text == "💰 My Points":
        pts = users_db.get(user_id, {}).get("points", 0)
        refs = users_db.get(user_id, {}).get("referrals", 0)
        bot.send_message(user_id, f"📊 **आपका बैलेंस विवरण:**\n\n💰 पॉइंट्स: `{pts}`\n👥 कुल रेफरल्स: `{refs}`", parse_mode="Markdown")

    elif text == "🔗 Referral Link":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(
            user_id, 
            f"🔗 **आपका रेफरल लिंक:**\n`{ref_link}`\n\nअपने दोस्तों को शेयर करें। हर जॉइन पर आपको **{REFERRAL_POINTS} पॉइंट्स** मिलेंगे!",
            parse_mode="Markdown"
        )

    elif text == "ℹ️ Help":
        bot.send_message(user_id, "ℹ️ **बॉट नियम व सहायता:**\n\n1. अपने रेफरल लिंक से दोस्तों को जोड़ें और पॉइंट्स कमाएं।\n2. बॉट चलाने के लिए तीनों चैनल्स में बने रहना अनिवार्य है।")

    # अगर कोई कुछ भी उल्टा-सीधा टाइप करे तो यह कस्टम मैसेज जाएगा
    else:
        bot.reply_to(message, CUSTOM_DEFAULT_MSG)

print("Bot is running...")
bot.infinity_polling()
