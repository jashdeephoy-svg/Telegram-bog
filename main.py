import os
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8141174859:AAGOzJQrQAxyNU49D2NQd1tL3bstorSyAJA")
ADMINS = [6289653515, 7393427319]

QR_IMAGE_URL = "https://via.placeholder.com/400x400.png?text=Scan+QR+to+Pay"
ANNOUNCEMENT_LINK = "https://t.me/+ObinPrPz_ktkODJl"
# ------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# Render 24/7 Keep-Alive Web Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# UTF-8 Data Storage
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}}
    return {"users": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Data save error: {e}")

db = load_data()

def get_user_data(uid):
    s_uid = str(uid)
    if s_uid not in db["users"]:
        db["users"][s_uid] = {
            "referrals": 0,
            "credits": 0,
            "referred_by": None,
            "state": None,
            "lock_time": 0
        }
        save_data(db)
    return db["users"][s_uid]

def notify_admins(text, reply_markup=None, photo_id=None):
    for admin_id in ADMINS:
        try:
            if photo_id:
                bot.send_photo(admin_id, photo_id, caption=text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                bot.send_message(admin_id, text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception as e:
            print(f"Failed to alert admin {admin_id}: {e}")

PUBLIC_CHANNELS = ["@Jyoex", "@foraremy", "@comchater"]

def is_user_member(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def check_all_channels(user_id):
    for ch in PUBLIC_CHANNELS:
        if not is_user_member(ch, user_id):
            return False
    return True

def get_force_join_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("JYOEX", url="https://t.me/Jyoex"),
        types.InlineKeyboardButton("SELL HUB", url="https://t.me/foraremy"),
        types.InlineKeyboardButton("Comchater", url="https://t.me/comchater"),
        types.InlineKeyboardButton("Market place", url="https://t.me/+_SvgfCFJeMdiMjNl"),
        types.InlineKeyboardButton("backup", url="https://t.me/+lZWeY9LOneU0ZDk1"),
        types.InlineKeyboardButton("✅ Check Joined", callback_data="check_joined")
    )
    return markup

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("Join Announcement Channel"))
    markup.row(types.KeyboardButton("Consumer helpline 📞"))
    markup.row(types.KeyboardButton("Work with us"), types.KeyboardButton("Mail create"))
    return markup

WELCOME_TEXT = (
    "🚀 <b>WELCOME TO THE GMAIL PORTAL</b> 🚀\n"
    "─────────────────────────\n"
    "⚡ <b>Looking for Premium & Fresh Gmail Accounts?</b>\n"
    "You are at the right place! We provide high quality accounts with full trust.\n\n"
    "💎 <b>Why Choose Us?</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🛡️ 100% Trusted & Genuine Service\n"
    "🚫 Zero Panel Use (No cheap bots/scripts)\n"
    "📱 100% Created via Real Devices\n"
    "📦 Bulk Orders Accepted\n"
    "💰 Best Prices & Fast Support\n\n"
    "─────────────────────────\n"
    "👇 Please select an option from the menu below:"
)

HELP_TEXT = (
    "If you face any issues regarding our bot or mail services, please reach out to our Customer Support. "
    "Our moderators will review your query and reply to you as soon as possible!\n\n"
    "📞 <b>Support Contact:</b> @Jyoex"
)

# /start Handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    user = get_user_data(uid)
    user["state"] = None
    save_data(db)

    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = args[1]
        if ref_id != str(uid) and not user.get("referred_by"):
            user["referred_by"] = ref_id
            ref_user = get_user_data(ref_id)
            ref_user["referrals"] += 1
            if ref_user["referrals"] % 10 == 0:
                ref_user["credits"] += 1
                try:
                    bot.send_message(
                        int(ref_id), 
                        "🎉 <b>Congratulations!</b>\nYou referred 10 users. You got <b>1 Free Mail Credit</b>!", 
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            save_data(db)

    if check_all_channels(uid):
        bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu(), parse_mode="HTML")
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Please join all our channels below to use this bot:</b>",
            reply_markup=get_force_join_markup(),
            parse_mode="HTML"
        )

# /help Handler
@bot.message_handler(commands=['help'])
def send_help_cmd(message):
    bot.send_message(message.chat.id, HELP_TEXT, parse_mode="HTML")

# Admin Reply Command
@bot.message_handler(commands=['reply'])
def admin_reply_cmd(message):
    if message.from_user.id not in ADMINS:
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(message, "⚠️ Usage: `/reply <USER_ID> <MESSAGE>`", parse_mode="Markdown")
        return
    target_id = args[1]
    reply_text = args[2]
    try:
        bot.send_message(int(target_id), f"📩 <b>Support Reply:</b>\n\n{reply_text}", parse_mode="HTML")
        bot.send_message(
            int(target_id),
            "🌟 <b>Give us vouch for creating your mail!</b>\nPlease send your feedback here.",
            parse_mode="HTML"
        )
        bot.reply_to(message, "✅ Reply sent successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error sending reply: {e}")

# Callback Query Handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    user = get_user_data(uid)

    if call.data == "check_joined":
        if check_all_channels(uid):
            bot.answer_callback_query(call.id, "Verification Successful!")
            bot.send_message(call.message.chat.id, WELCOME_TEXT, reply_markup=get_main_menu(), parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ You have not joined all channels yet!", show_alert=True)

    elif call.data == "start_report":
        user["state"] = "AWAITING_REPORT"
        save_data(db)
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "If you have any issues, questions, or suggestions regarding Gmail Creator Bot, please let us know through a text message. Our support team will do its best to assist you."
        )

    elif call.data in ["choose_gmail", "choose_outlook"]:
        domain = "Gmail" if call.data == "choose_gmail" else "Outlook"
        price = "40" if domain == "Gmail" else "20"
        user["state"] = f"AWAITING_PAYMENT_{domain.upper()}"
        save_data(db)
        bot.answer_callback_query(call.id)

        caption = (
            f"✅ <b>Selected:</b> {domain}\n"
            f"<b>per mail {price} inr after payment your mail will be created</b>\n\n"
            "<b>SEND PAYMENT SS AND WITH CLEAR SHOWING TRANSACTION ID AND NAME 😇</b>"
        )
        markup = None
        if domain == "Gmail" and user.get("credits", 0) > 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"🎁 Use Credit Point (Credits: {user['credits']})", callback_data="use_credit"))

        try:
            bot.send_photo(call.message.chat.id, QR_IMAGE_URL, caption=caption, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, caption, reply_markup=markup, parse_mode="HTML")

    elif call.data == "use_credit":
        if user.get("credits", 0) > 0:
            user["credits"] -= 1
            user["state"] = "AWAITING_PASS"
            save_data(db)
            bot.answer_callback_query(call.id)

            notify_admins(
                f"🎁 <b>Credit User Request!</b>\nUser ID: <code>{uid}</code>\nRemaining Credits: {user['credits']}\nReply with: <code>/reply {uid} &lt;details&gt;</code>",
                types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("✅ Approve Credit", callback_data=f"app_credit_{uid}")
                )
            )
            bot.send_message(
                call.message.chat.id,
                "Your credit request has been submitted to admin!\n\n<b>GIVE HIT OR MAIL AND YOUR PASS</b>",
                parse_mode="HTML"
            )
        else:
            bot.answer_callback_query(call.id, "❌ You have 0 credits available!", show_alert=True)

    elif call.data.startswith("app_credit_"):
        target_uid = int(call.data.split("_")[2])
        bot.answer_callback_query(call.id, "Credit Approved!")
        bot.send_message(
            target_uid,
            "Your credit are reached us\nGmail in processing pls wait✋🥺"
        )

    elif call.data.startswith("pay_app_"):
        target_uid = int(call.data.split("_")[2])
        target_user = get_user_data(target_uid)
        target_user["state"] = "AWAITING_PASS"
        save_data(db)
        bot.answer_callback_query(call.id, "Payment Approved!")

        bot.send_message(
            target_uid,
            "Your funds have safely reached me. Mail in processing\n\n<b>GIVE HIT OR MAIL AND YOUR PASS</b>",
            parse_mode="HTML"
        )

    elif call.data.startswith("pay_dec_"):
        target_uid = int(call.data.split("_")[2])
        target_user = get_user_data(target_uid)
        target_user["state"] = None
        save_data(db)
        bot.answer_callback_query(call.id, "Payment Declined!")

        bot.send_message(
            target_uid,
            "Your funds are not reached us you send invalid transaction id ss"
        )

# Message & Photo Handler
@bot.message_handler(content_types=['text', 'photo'])
def handle_all_messages(message):
    uid = message.from_user.id
    user = get_user_data(uid)

    if not check_all_channels(uid):
        bot.send_message(
            message.chat.id, 
            "⚠️ <b>Please join all our channels first:</b>", 
            reply_markup=get_force_join_markup(),
            parse_mode="HTML"
        )
        return

    # 5 Minutes Lock Check
    current_time = time.time()
    if user.get("lock_time", 0) > current_time:
        bot.send_message(message.chat.id, "Wait 5 minutes we are creating your mail with your custom pass")
        return

    state = user.get("state")
    text = message.text if message.text else ""

    # 1. Report Validation (15 to 150 words)
    if state == "AWAITING_REPORT":
        words = text.strip().split()
        if len(words) < 15 or len(words) > 150:
            bot.send_message(message.chat.id, "⚠️ type your report minimun 15 words")
            return

        user["state"] = None
        save_data(db)
        bot.send_message(message.chat.id, "Your report successfully accepted.\nsoon our moderator replied you")

        admin_msg = (
            f"🚨 <b>New Consumer Report:</b>\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"📝 Message: {text}\n\n"
            f"👉 Reply using: <code>/reply {uid} &lt;Your message&gt;</code>"
        )
        notify_admins(admin_msg)
        return

    # 2. Receiving Payment Screenshot
    if state in ["AWAITING_PAYMENT_GMAIL", "AWAITING_PAYMENT_OUTLOOK"]:
        if message.photo:
            photo_id = message.photo[-1].file_id
            domain = "Gmail" if "GMAIL" in state else "Outlook"
            user["state"] = None
            save_data(db)

            bot.send_message(
                message.chat.id,
                "apki payment appeal mode tak pahucha di gayi hai jab wo approved karenge tab apki mail create hogi wait some time"
            )

            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"pay_app_{uid}"),
                types.InlineKeyboardButton("❌ Decline", callback_data=f"pay_dec_{uid}")
            )
            notify_admins(
                f"💳 <b>New Payment Verification:</b>\n👤 User ID: <code>{uid}</code>\n📧 Domain: {domain}\nText: {message.caption or 'None'}",
                reply_markup=admin_markup,
                photo_id=photo_id
            )
            return
        else:
            bot.send_message(message.chat.id, "⚠️ Please send a clear payment screenshot photo.")
            return

    # 3. Receiving Mail and Custom Password
    if state == "AWAITING_PASS":
        user["state"] = None
        user["lock_time"] = time.time() + 300
        save_data(db)

        bot.send_message(message.chat.id, "Gmail in processing pls wait✋🥺")

        notify_admins(
            f"🔑 <b>Mail & Pass Request:</b>\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"📝 User Provided: {text}\n\n"
            f"👉 Deliver via: <code>/reply {uid} &lt;Account Details&gt;</code>"
        )
        return

    # 4. Main Menu Actions
    if text == "Join Announcement Channel":
        bot.send_message(message.chat.id, f"📢 <b>Announcement Channel:</b>\n{ANNOUNCEMENT_LINK}", parse_mode="HTML")

    elif text == "Consumer helpline 📞":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("24x7 consumer support", callback_data="start_report"))
        bot.send_message(message.chat.id, "📞 <b>Customer Support Menu:</b>\nClick the button below to submit your issue:", reply_markup=markup, parse_mode="HTML")

    elif text == "Work with us":
        bot.send_message(
            message.chat.id,
            "DM us on @talkwithhimbot We’ll explain the work in detail, and you can earn good money with us."
        )

    elif text == "Mail create":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Gmail", callback_data="choose_gmail"),
            types.InlineKeyboardButton("Outlook", callback_data="choose_outlook")
        )
        bot.send_message(message.chat.id, "choose your domain to create mail", reply_markup=markup)

    else:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>Invalid Option</b>\n\n"
            "I couldn't understand that command. Please use the menu buttons below or type /help for assistance.\n\n"
            "👉 Tap /start to view the Main Menu.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Bot is successfully running 24/7...")
    bot.infinity_polling()
