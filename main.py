import os
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8141174859:AAGOzJQrQAxyNU49D2NQd1tL3bstorSyAJA"
ADMINS = [6289653515, 7393427319]
CHANNELS = ["@foraremy", "@comchater", "@Jyoex"]

# आपकी QR इमेज की Telegram File ID
QR_IMAGE_URL = "AgACAgUAAxkBAAEuGY5qkTYwvExkrLrJSIRYuk242MblQAACVxNrG4QQiVSTN65L1CiLrAEAAwIAA20AAz0E"
ANNOUNCEMENT_LINK = "https://t.me/+Ob81sV9D5vsyMjhl"

PER_REFERRAL_CREDITS = 2
SUBMISSION_COOLDOWN = 300  # 5 मिनट (300 सेकंड)
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
            "credits": 0,
            "referred_by": None,
            "referral_rewarded": False,
            "is_paid": False,
            "reports_submitted": 0,
            "last_submission": 0
        }
        save_data(data)
    return data["users"][str_id]

def is_subscribed(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

# Force Join Buttons Layout
def get_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📢 Join Channel 1 (@foraremy)", url="https://t.me/foraremy")
    btn2 = types.InlineKeyboardButton("📢 Join Channel 2 (@comchater)", url="https://t.me/comchater")
    btn3 = types.InlineKeyboardButton("📢 Join Channel 3 (@Jyoex)", url="https://t.me/Jyoex")
    verify_btn = types.InlineKeyboardButton("✅ Check Joined (सत्यापित करें)", callback_data="check_joined")
    
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    markup.row(verify_btn)
    return markup

# Clean Main Menu Inline Layout
def get_main_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_report = types.InlineKeyboardButton("📝 Submit Report", callback_data="btn_report")
    btn_profile = types.InlineKeyboardButton("👤 Status / Profile", callback_data="btn_profile")
    btn_help = types.InlineKeyboardButton("📞 Help & Support", callback_data="btn_support")
    btn_refer = types.InlineKeyboardButton("🔗 Refer & Earn", callback_data="btn_refer")
    btn_vip = types.InlineKeyboardButton("💎 VIP Access", callback_data="btn_buy")
    
    markup.row(btn_report)
    markup.row(btn_profile, btn_help)
    markup.row(btn_refer, btn_vip)
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    user = get_user(user_id)

    # Referral Tracking
    args = message.text.split()
    if len(args) > 1 and user["referred_by"] is None:
        ref_id = args[1]
        if ref_id != str(user_id) and ref_id in data["users"]:
            user["referred_by"] = ref_id
            save_data(data)

    if not is_subscribed(user_id):
        text = (
            "⚠️ **बॉट का उपयोग करने के लिए चैनल्स जॉइन करना अनिवार्य है:**\n\n"
            "1️⃣ @foraremy\n"
            "2️⃣ @comchater\n"
            "3️⃣ @Jyoex\n\n"
            "तीनों चैनल्स जॉइन करने के बाद नीचे **Check Joined** बटन पर टैप करें।"
        )
        bot.send_message(user_id, text, reply_markup=get_join_keyboard(), parse_mode="Markdown")
        return

    text = (
        "🤖 **Report & Appeal Bot**\n\n"
        "Submit your issue or request directly to admins.\n"
        "Choose an option below:"
    )
    bot.send_message(user_id, text, reply_markup=get_main_inline_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    user = get_user(user_id)

    if call.data == "check_joined":
        if is_subscribed(user_id):
            if user.get("referred_by") and not user.get("referral_rewarded"):
                ref_user = get_user(user["referred_by"])
                ref_user["credits"] += PER_REFERRAL_CREDITS
                user["referral_rewarded"] = True
                save_data(data)
                try:
                    bot.send_message(int(user["referred_by"]), f"🎉 आपके रेफरल लिंक से नया मेंबर जुड़ा! +{PER_REFERRAL_CREDITS} क्रेडिट्स मिले।")
                except Exception:
                    pass

            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            
            text = (
                "🤖 **Report & Appeal Bot**\n\n"
                "Submit your issue or request directly to admins.\n"
                "Choose an option below:"
            )
            bot.send_message(user_id, text, reply_markup=get_main_inline_keyboard(), parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ कृपया पहले सभी 3 चैनल्स जॉइन करें!", show_alert=True)
        return

    if not is_subscribed(user_id):
        bot.answer_callback_query(call.id, "⚠️ पहले सभी चैनल्स जॉइन करें!", show_alert=True)
        return

    if call.data == "btn_profile":
        text = (
            f"👤 **Your Status / Profile:**\n\n"
            f"🆔 User ID: `{user_id}`\n"
            f"💰 Credits: `{user['credits']}`\n"
            f"📊 Submitted Reports: `{user['reports_submitted']}`\n"
            f"👑 VIP Status: `{'Active' if user['is_paid'] else 'Inactive'}`"
        )
        bot.send_message(user_id, text, parse_mode="Markdown")

    elif call.data == "btn_refer":
        try:
            bot_username = bot.get_me().username
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            bot.send_message(
                user_id,
                f"🔗 **Your Referral Link:**\n`{ref_link}`\n\n🎁 Per Refer Reward: +{PER_REFERRAL_CREDITS} Credits",
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(user_id, f"🎁 Share link with friends to earn +{PER_REFERRAL_CREDITS} Credits!")

    elif call.data == "btn_support":
        bot.send_message(user_id, "📞 **Support Helpline:**\nContact: @Jyoex", parse_mode="Markdown")

    elif call.data == "btn_buy":
        user_states[user_id] = "AWAITING_PAYMENT_SS"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
        bot.send_photo(
            user_id,
            QR_IMAGE_URL,
            caption="💳 **VIP Access Plan** (₹99)\n\n1️⃣ Scan QR & Pay\n2️⃣ Send Screenshot here to verify.",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "btn_report":
        current_time = time.time()
        last_sub = user.get("last_submission", 0)
        if current_time - last_sub < SUBMISSION_COOLDOWN:
            remaining = int(SUBMISSION_COOLDOWN - (current_time - last_sub))
            mins, secs = divmod(remaining, 60)
            bot.answer_callback_query(call.id, f"⏳ Cooldown active! Wait {mins}m {secs}s.", show_alert=True)
            return

        user_states[user_id] = "AWAITING_REPORT"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
        bot.send_message(user_id, "✍️ **Type your appeal / report:**\n(Must be 15 to 150 words)", reply_markup=markup, parse_mode="Markdown")

    elif call.data == "cancel_action":
        user_states.pop(user_id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(user_id, "❌ Action cancelled.", reply_markup=get_main_inline_keyboard())

    elif call.data.startswith("app_pay_"):
        if user_id in ADMINS:
            target_id = call.data.split("_pay_")[1]
            get_user(target_id)["is_paid"] = True
            save_data(data)
            try:
                bot.edit_message_caption("✅ Approved by Admin", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(int(target_id), f"🎉 VIP Approved!\n🔗 Channel Link: {ANNOUNCEMENT_LINK}")
            except Exception:
                pass

    elif call.data.startswith("dec_pay_"):
        if user_id in ADMINS:
            target_id = call.data.split("_pay_")[1]
            try:
                bot.edit_message_caption("❌ Declined by Admin", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.send_message(int(target_id), "❌ VIP Payment Declined.")
            except Exception:
                pass

@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo'])
def handle_inputs(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state == "AWAITING_PAYMENT_SS" and message.content_type == 'photo':
        photo_id = message.photo[-1].file_id
        user_states.pop(user_id, None)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"app_pay_{user_id}"),
            types.InlineKeyboardButton("❌ Decline", callback_data=f"dec_pay_{user_id}")
        )
        for admin in ADMINS:
            try:
                bot.send_photo(admin, photo_id, caption=f"🔔 New Payment SS!\nUser ID: `{user_id}`", reply_markup=markup, parse_mode="Markdown")
            except Exception:
                pass
        bot.send_message(user_id, "✅ Screenshot received! Admin will verify soon.")

    elif state == "AWAITING_REPORT" and message.text:
        words = message.text.split()
        if len(words) < 15 or len(words) > 150:
            bot.send_message(user_id, f"⚠️ Report must be 15 to 150 words (currently {len(words)} words).")
            return

        user_states.pop(user_id, None)
        user = get_user(user_id)
        user["last_submission"] = time.time()
        user["reports_submitted"] += 1
        save_data(data)

        for admin in ADMINS:
            try:
                bot.send_message(admin, f"📩 **New Report Submitted:**\nUser ID: `{user_id}`\n\n{message.text}", parse_mode="Markdown")
            except Exception:
                pass

        bot.send_message(user_id, "✅ Report submitted successfully! (Next submission allowed after 5 min).", reply_markup=get_main_inline_keyboard())

# Auto-restarting Polling Loop
if __name__ == "__main__":
    print("Bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)
