import os
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "7823545024:AAG7tyrhxhtwMTu2xKe47uzhK4SQHRkdmrc"
ADMINS = [6289653515, 7393427319]

# फोर्स जॉइन के 3 पब्लिक चैनल्स
PUBLIC_CHANNELS = ["@jyoex", "@comchater", "@foraremy"]

# 4th बैकअप चैनल लिंक
BACKUP_CHANNEL_LINK = "https://t.me/+YwwAed_oQwU5YWY1"

# लिंक्स
ANNOUNCEMENT_CHANNEL_LINK = "https://t.me/+YwwAed_oQwU5YWY1"
CONSUMER_HELPLINE_USER = "https://t.me/Jyoex"
WORK_WITH_US_LINK = "https://t.me/Jyoex"

PER_REFERRAL_REWARD = 2  # Per refer bonus credits / balance
DB_FILE = "bot_data.json"
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# Web Server for Render 24/7 Keep-Alive
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is online 24/7")

    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# Data Handling
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}}

def save_data(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

data = load_data()
user_states = {}

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in data["users"]:
        data["users"][str_id] = {
            "balance": 0,
            "referred_by": None,
            "referral_rewarded": False,
            "total_referrals": 0
        }
        save_data(data)
    return data["users"][str_id]

def is_subscribed(user_id):
    for ch in PUBLIC_CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

# 1. फोर्स जॉइन इनलाइन कीबोर्ड
def get_force_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📢 Channel 1 (@jyoex)", url="https://t.me/jyoex")
    btn2 = types.InlineKeyboardButton("📢 Channel 2 (@comchater)", url="https://t.me/comchater")
    btn3 = types.InlineKeyboardButton("📢 Channel 3 (@foraremy)", url="https://t.me/foraremy")
    btn4 = types.InlineKeyboardButton("🛡️ Backup Channel", url=BACKUP_CHANNEL_LINK)
    verify_btn = types.InlineKeyboardButton("✅ Verify / Check Joined", callback_data="check_joined")
    
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(verify_btn)
    return markup

# 2. बॉट मेन्यू कीबोर्ड (Clean Layout with 3 New Buttons)
def get_bottom_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    btn_announcement = types.KeyboardButton("Join Announcement Channel")
    btn_helpline = types.KeyboardButton("Consumer helpline 📞")
    btn_work = types.KeyboardButton("Work with us")
    btn_mail = types.KeyboardButton("Mail create")
    
    # 3 New Buttons
    btn_balance = types.KeyboardButton("💰 My Balance")
    btn_referrals = types.KeyboardButton("👥 Referrals")
    btn_help = types.KeyboardButton("⚙️ Help")
    
    markup.row(btn_announcement)
    markup.row(btn_helpline)
    markup.row(btn_work, btn_mail)
    markup.row(btn_balance, btn_referrals)
    markup.row(btn_help)
    return markup

WELCOME_TEXT = (
    "🚀 **WELCOME TO GMAIL PORTAL** 🚀\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚡ **Looking for Premium & Fresh Gmail Accounts?**\n"
    "We provide 100% genuine, real-device created accounts with full trust.\n\n"
    "💎 **Features:**\n"
    "• 100% Real Device Creation\n"
    "• Zero Panel / No Cheap Bots\n"
    "• Bulk Orders Accepted\n"
    "• Fast Delivery & Support\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚠️ **Note:** बॉट को इस्तेमाल करने के लिए नीचे दिए गए सभी चैनल्स को जॉइन करना अनिवार्य है।"
)

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    user_states.pop(user_id, None)

    # Referral Tracking
    args = message.text.split()
    if len(args) > 1 and user["referred_by"] is None:
        ref_id = args[1]
        if ref_id != str(user_id) and ref_id in data["users"]:
            user["referred_by"] = ref_id
            save_data(data)

    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            WELCOME_TEXT,
            reply_markup=get_force_join_keyboard(),
            parse_mode="Markdown"
        )
        return

    bot.send_message(
        user_id,
        "✅ **Welcome! Select an option from the menu below:**",
        reply_markup=get_bottom_menu_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_user(user_id)

    if call.data == "check_joined":
        if is_subscribed(user_id):
            if user.get("referred_by") and not user.get("referral_rewarded"):
                ref_user = get_user(user["referred_by"])
                ref_user["balance"] += PER_REFERRAL_REWARD
                ref_user["total_referrals"] += 1
                user["referral_rewarded"] = True
                save_data(data)
                try:
                    bot.send_message(int(user["referred_by"]), f"🎉 आपके रेफरल लिंक से नया यूज़र जुड़ा! +{PER_REFERRAL_REWARD} बैलेंस मिला।")
                except Exception:
                    pass

            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            
            bot.send_message(
                user_id,
                "🎉 **Verification Successful!**\n\nWelcome to **Gmail Portal**. Choose an option below:",
                reply_markup=get_bottom_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Please join all channels first!", show_alert=True)

# नीचे वाले बटन्स के क्लिक हैंडलर
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_bottom_buttons(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    text = message.text

    # सुरक्षा जाँच
    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            "⚠️ **Access Denied!** Please join all channels to use the bot.",
            reply_markup=get_force_join_keyboard()
        )
        return

    # स्टेट चेक (Mail Create)
    state = user_states.get(user_id)
    if state == "AWAITING_MAIL_DETAILS":
        if text == "❌ Cancel":
            user_states.pop(user_id, None)
            bot.send_message(user_id, "❌ Action Cancelled.", reply_markup=get_bottom_menu_keyboard())
            return

        user_states.pop(user_id, None)
        for admin in ADMINS:
            try:
                bot.send_message(
                    admin,
                    f"📩 **New Mail Creation Order:**\n"
                    f"👤 User: @{message.from_user.username or 'No Username'}\n"
                    f"🆔 User ID: `{user_id}`\n\n"
                    f"📝 Details:\n{text}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        bot.send_message(
            user_id,
            "✅ आपकी रिक्वेस्ट एडमिन को भेज दी गई है! हम जल्द ही संपर्क करेंगे।",
            reply_markup=get_bottom_menu_keyboard()
        )
        return

    # Menu Actions
    if text == "Join Announcement Channel":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Open Announcement Channel", url=ANNOUNCEMENT_CHANNEL_LINK))
        bot.send_message(user_id, "👇 टैप करके Announcement Channel जॉइन करें:", reply_markup=markup)

    elif text == "Consumer helpline 📞":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Contact Support", url=CONSUMER_HELPLINE_USER))
        bot.send_message(user_id, "📞 किसी भी सहायता या प्रश्न के लिए सपोर्ट से संपर्क करें:", reply_markup=markup)

    elif text == "Work with us":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🤝 Contact for Work", url=WORK_WITH_US_LINK))
        bot.send_message(user_id, "💼 हमारे साथ काम करने या बल्क ऑर्डर्स के लिए संपर्क करें:", reply_markup=markup)

    elif text == "Mail create":
        user_states[user_id] = "AWAITING_MAIL_DETAILS"
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(
            user_id,
            "✍️ **Mail Creation Order:**\n\nकृपया अपनी ज़रूरत (जैसे कितनी मेल चाहिए, कोई खास नाम आदि) लिखकर भेजें:",
            reply_markup=cancel_kb,
            parse_mode="Markdown"
        )

    elif text == "💰 My Balance":
        bot.send_message(
            user_id,
            f"💰 **Your Account Balance:**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💵 Current Balance: `{user.get('balance', 0)} Credits`\n"
            f"👥 Total Referrals: `{user.get('total_referrals', 0)}`",
            parse_mode="Markdown"
        )

    elif text == "👥 Referrals":
        try:
            bot_username = bot.get_me().username
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            bot.send_message(
                user_id,
                f"👥 **Referral System:**\n\n"
                f"अपने दोस्तों को अपने लिंक से जोड़ें और हर सफल रेफरल पर **+{PER_REFERRAL_REWARD} Credits** कमाएं!\n\n"
                f"🔗 **Your Referral Link:**\n`{ref_link}`\n\n"
                f"📊 Total Referrals: `{user.get('total_referrals', 0)}`",
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(user_id, "⚠️ Error generating referral link. Please try again later.")

    elif text == "⚙️ Help":
        help_text = (
            "⚙️ **Help & Guide:**\n\n"
            "• **Mail create:** ताज़ा जीमेल अकाउंट्स ऑर्डर करने के लिए इसका उपयोग करें।\n"
            "• **Referrals:** अपने रेफरल लिंक से दोस्तों को जोड़कर बैलेंस बढ़ाएं।\n"
            "• **Consumer helpline 📞:** किसी भी तकनीकी समस्या के लिए एडमिन से संपर्क करें: @Jyoex\n\n"
            "Official Announcement: @comchater"
        )
        bot.send_message(user_id, help_text, parse_mode="Markdown")

# Auto Polling
if __name__ == "__main__":
    print("Gmail Portal Bot running...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)
