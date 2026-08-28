import os
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
# आपका नया अपडेटेड टोकन
BOT_TOKEN = "7823545024:AAG7tyrhxhtwMTu2xKe47uzhK4SQHRkdmrc"
ADMINS = [6289653515, 7393427319]

# चैनल्स और हेल्प लिंक्स
ANNOUNCEMENT_CHANNEL_LINK = "https://t.me/+Ob81sV9D5vsyMjhl"
CONSUMER_HELPLINE_USER = "https://t.me/Jyoex"
WORK_WITH_US_LINK = "https://t.me/Jyoex"
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

user_states = {}

# 2x2 Clean Grid Layout Buttons
def get_portal_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton("📢 Join Announcement", url=ANNOUNCEMENT_CHANNEL_LINK)
    btn2 = types.InlineKeyboardButton("📞 Consumer Helpline", url=CONSUMER_HELPLINE_USER)
    btn3 = types.InlineKeyboardButton("💼 Work with Us", url=WORK_WITH_US_LINK)
    btn4 = types.InlineKeyboardButton("✉️ Mail Create", callback_data="btn_mail_create")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    return markup

WELCOME_TEXT = (
    "🚀 **WELCOME TO THE GMAIL PORTAL** 🚀\n"
    "─────────────────────────\n"
    "⚡ **Looking for Premium & Fresh Gmail Accounts?**\n"
    "You are at the right place! We provide high quality accounts with full trust.\n\n"
    "💎 **Why Choose Us?**\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🛡️ 100% Trusted & Genuine Service\n"
    "🚫 Zero Panel Use (No cheap bots/scripts)\n"
    "📱 100% Created via Real Devices\n"
    "📦 Bulk Orders Accepted\n"
    "💰 Best Prices & Fast Support\n\n"
    "─────────────────────────\n"
    "👇 **Please select an option from the menu below:**"
)

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)

    bot.send_message(
        user_id,
        WELCOME_TEXT,
        reply_markup=get_portal_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id

    if call.data == "btn_mail_create":
        user_states[user_id] = "AWAITING_MAIL_DETAILS"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_action"))
        bot.send_message(
            user_id,
            "✍️ **Mail Creation Request:**\n\nकृपया अपनी ज़रूरत (Quantity, Custom Name, etc.) लिखकर भेजें। एडमिन आपसे जल्द संपर्क करेंगे।",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif call.data == "cancel_action":
        user_states.pop(user_id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(
            user_id,
            WELCOME_TEXT,
            reply_markup=get_portal_keyboard(),
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_messages(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state == "AWAITING_MAIL_DETAILS" and message.text:
        user_states.pop(user_id, None)
        for admin in ADMINS:
            try:
                bot.send_message(
                    admin,
                    f"📩 **New Mail Creation Order/Request:**\n"
                    f"👤 User: @{message.from_user.username or 'No Username'}\n"
                    f"🆔 User ID: `{user_id}`\n\n"
                    f"📝 Request:\n{message.text}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        bot.send_message(
            user_id,
            "✅ आपकी रिक्वेस्ट सफलतापूर्वक एडमिन तक पहुँच गई है! हम जल्द ही संपर्क करेंगे।",
            reply_markup=get_portal_keyboard(),
            parse_mode="Markdown"
        )

# Auto Polling
if __name__ == "__main__":
    print("Gmail Portal Bot started with new token...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)
