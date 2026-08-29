import os
import time
import re
import json
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "7823545024:AAG7tyrhxhtwMTu2xKe47uzhK4SQHRkdmrc"
SUPER_ADMINS = [6289653515, 7393427319]

PUBLIC_CHANNELS = ["@jyoex", "@comchater", "@foraremy"]
BACKUP_CHANNEL_LINK = "https://t.me/+YwwAed_oQwU5YWY1"
ANNOUNCEMENT_CHANNEL_LINK = "https://t.me/+ObinPrPz_ktkODJl"
WORK_BOT_LINK = "https://t.me/talkwithhimbot"

PER_REFERRAL_REWARD = 1
DB_FILE = "bot_data.json"
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# 24/7 Web Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive 24/7")

    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def self_ping():
    time.sleep(10)
    port = int(os.environ.get("PORT", 8080))
    while True:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10)
        except Exception:
            pass
        time.sleep(120)

threading.Thread(target=self_ping, daemon=True).start()

def load_data():
    default_db = {
        "users": {},
        "admins": SUPER_ADMINS,
        "groups": [],
        "banned": [],
        "qr_file_id": None,
        "qr_locked": True,
        "settings": {
            "maintenance": False,
            "new_user_notify": True
        },
        "scheduler": {
            "enabled": False,
            "text": "gmailcrtorbot here we are best we are no 1 gmai provider genuine mails try us",
            "interval_min": 60,
            "target": "all"
        },
        "feedbacks": []
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
user_last_messages = {}

REDEEM_TICKETS = [
    {"code": "Freezgmail1", "chance": 30, "msg": "🎉 **CONGRATS!**\nYOU GOT A FREE 2 GMAIL CREATION TICKET!"},
    {"code": "nex&time2", "chance": 90, "msg": "😔 **SORRY NEXT TIME!**"},
    {"code": "Tryagain3", "chance": 80, "msg": "🔄 **SORRY TRY AGAIN!**"},
    {"code": "Badluck4", "chance": 60, "msg": "⚠️ **THIS TIME YOUR BAD LUCK!**"},
    {"code": "Notyourluck5", "chance": 70, "msg": "⌛ **TODAY IS NOT YOUR DAY!**"},
    {"code": "Bobmcredit6", "chance": 50, "msg": "🎉 **CONGRATS!**\nYOU GOT 5 FREE BOMBER CREDITS!"},
    {"code": "Get7c", "chance": 60, "msg": "🎉 **CONGRATS!**\nYOU GOT 7 FREE NUMBER DETAILS TICKETS!"},
    {"code": "Wors8tdy", "chance": 60, "msg": "🌧️ **SORRY TODAY IS YOUR WORST DAY!**"},
    {"code": "Nott9oday", "chance": 85, "msg": "💔 **NOT YOUR DAY DEAR USER!**"},
    {"code": "Loki5210", "chance": 79, "msg": "🍀 **OPPPS BETTER LUCK NEXT TIME!**"}
]

def auto_scheduler_loop():
    while True:
        try:
            sched = data.get("scheduler", {})
            if sched.get("enabled") and sched.get("text"):
                interval = sched.get("interval_min", 60) * 60
                time.sleep(interval)
                msg = sched.get("text")
                target = sched.get("target", "all")
                
                targets_list = []
                if target in ["groups", "all"]:
                    targets_list.extend(data.get("groups", []))
                if target in ["users", "all"]:
                    targets_list.extend([int(u) for u in data.get("users", {}).keys()])

                for chat_id in set(targets_list):
                    try:
                        bot.send_message(chat_id, msg)
                        time.sleep(0.05)
                    except Exception:
                        pass
            else:
                time.sleep(10)
        except Exception:
            time.sleep(10)

threading.Thread(target=auto_scheduler_loop, daemon=True).start()

MENU_BUTTONS = [
    "Join Announcement Channel",
    "24x7 consumer helpline",
    "Work with us",
    "Mail create",
    "Balance",
    "👥 Referrals",
    "⭐ Rating / Feedback",
    "⚙️ Help",
    "🛠️ Admin Panel",
    "🚫 Cancel",
    "❌ Cancel"
]

def is_admin(user_id):
    return user_id in data.get("admins", SUPER_ADMINS) or user_id in SUPER_ADMINS

def parse_time_input(input_text):
    text = input_text.lower().strip()
    match_hr = re.search(r'(\d+)\s*(hour|hr|h)', text)
    if match_hr:
        return int(match_hr.group(1)) * 60
    match_min = re.search(r'(\d+)\s*(minute|min|m)', text)
    if match_min:
        return int(match_min.group(1))
    if text.isdigit():
        return int(text)
    return None

def find_user_key(query):
    query_str = str(query).strip().lower()
    if query_str.startswith("@"):
        query_str = query_str[1:]
    for uid, udata in data.get("users", {}).items():
        if str(uid) == query_str:
            return uid
        stored_uname = str(udata.get("username", "")).lower().replace("@", "")
        if stored_uname and stored_uname == query_str:
            return uid
    return None

def format_user_card_by_id(user_id):
    str_id = str(user_id)
    if str_id not in data["users"]:
        return None
    user_info = data["users"][str_id]
    name = user_info.get("name", "User")
    uname = f"@{user_info.get('username')}" if user_info.get('username') else "None"
    return (
        f"👤 **USER PROFILE DETAILS**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** [{name}](tg://user?id={user_id})\n"
        f"🆔 **User ID:** [`{user_id}`](tg://user?id={user_id})\n"
        f"🔗 **Username:** {uname}\n"
        f"💵 **Current Balance:** `{user_info.get('balance', 0)} Credits`\n"
        f"👥 **Total Referrals:** `{user_info.get('total_referrals', 0)} Users`\n"
        f"📅 **Member Since:** `{user_info.get('joined_at', '2026')}`"
    )

def format_user_card(user_obj, user_id):
    name = user_obj.first_name if hasattr(user_obj, 'first_name') else "User"
    username = f"@{user_obj.username}" if getattr(user_obj, 'username', None) else "None"
    profile_link = f"[{name}](tg://user?id={user_id})"
    user_info = get_user(user_id, user_obj)
    
    return (
        f"👤 User: {profile_link}\n"
        f"🆔 User ID: [`{user_id}`](tg://user?id={user_id})\n"
        f"🔗 Username: {username}\n"
        f"👥 Referrals: `{user_info.get('total_referrals', 0)}`\n"
        f"💵 Balance: `{user_info.get('balance', 0)} Credits`"
    )

def get_user(user_id, user_obj=None):
    str_id = str(user_id)
    is_new = str_id not in data["users"]
    if is_new:
        data["users"][str_id] = {
            "name": user_obj.first_name if user_obj else "User",
            "username": user_obj.username if user_obj else None,
            "balance": 0,
            "referred_by": None,
            "referral_rewarded": False,
            "total_referrals": 0,
            "joined_at": time.strftime("%d-%m-%Y %H:%M"),
            "blocked": False
        }
        save_data(data)
    else:
        if user_obj:
            if user_obj.first_name:
                data["users"][str_id]["name"] = user_obj.first_name
            if user_obj.username:
                data["users"][str_id]["username"] = user_obj.username
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
    btn_balance = types.KeyboardButton("Balance")
    btn_referrals = types.KeyboardButton("👥 Referrals")
    btn_rating = types.KeyboardButton("⭐ Rating / Feedback")
    btn_help = types.KeyboardButton("⚙️ Help")
    
    markup.row(btn_announcement)
    markup.row(btn_helpline)
    markup.row(btn_work, btn_mail)
    markup.row(btn_balance, btn_referrals)
    
    if is_admin(user_id):
        btn_admin = types.KeyboardButton("🛠️ Admin Panel")
        markup.row(btn_rating, btn_help, btn_admin)
    else:
        markup.row(btn_rating, btn_help)
    return markup

def get_use_credit_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    b1 = types.InlineKeyboardButton("1mail creation (10 credit)", callback_data="use_cred_gmail")
    b2 = types.InlineKeyboardButton("BUY LUCK COUPON (10 CREDIT)", callback_data="use_cred_ticket")
    b3 = types.InlineKeyboardButton("number details 1 credit", callback_data="use_cred_numdet")
    b4 = types.InlineKeyboardButton("Redeem Free Outlook Mail (5 Credits)", callback_data="use_cred_outlook")
    markup.add(b1, b2, b3, b4)
    return markup

def get_admin_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    m_state = "🔴 ON" if data["settings"].get("maintenance") else "⚪ OFF"
    n_state = "🔔 ON" if data["settings"].get("new_user_notify") else "🔕 OFF"
    s_state = "🟢 ON" if data.get("scheduler", {}).get("enabled") else "⚪ OFF"
    qr_state = "🟢 LOCKED" if data.get("qr_locked", True) else "🔓 UNLOCKED"
    
    btn1 = types.InlineKeyboardButton("📨 Mailing / Broadcast", callback_data="adm_cmd_mail")
    btn2 = types.InlineKeyboardButton("📊 Statistics & Users", callback_data="adm_cmd_stats")
    btn3 = types.InlineKeyboardButton(f"🛠️ Maintenance ({m_state})", callback_data="adm_cmd_toggle_maint")
    btn4 = types.InlineKeyboardButton(f"👤 New User Notify ({n_state})", callback_data="adm_cmd_toggle_notify")
    btn5 = types.InlineKeyboardButton(f"🔒 QR Lock ({qr_state})", callback_data="adm_cmd_toggle_qrlock")
    btn6 = types.InlineKeyboardButton("🔄 Change QR Code", callback_data="adm_cmd_update_qr")
    btn7 = types.InlineKeyboardButton("👥 Manage Admins", callback_data="adm_cmd_manage_admins")
    btn8 = types.InlineKeyboardButton("💰 Manage User Credits", callback_data="adm_cmd_manage_credits")
    btn9 = types.InlineKeyboardButton(f"⏰ Auto Timer Msg ({s_state})", callback_data="adm_cmd_auto_timer")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7, btn8)
    markup.add(btn9)
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

def get_rating_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=5)
    stars = [types.InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate_{i}") for i in range(1, 6)]
    markup.add(*stars)
    return markup

def send_delayed_give_hit(target_id):
    time.sleep(5)
    user_states[target_id] = "AWAITING_CREDENTIALS"
    cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
    try:
        bot.send_message(target_id, "𝗚𝗜𝗩𝗘 𝗛𝗜𝗧 𝗢𝗥 𝗠𝗔𝗜𝗟 𝗔𝗡𝗗 𝙔𝙊𝙐𝙍 𝗣𝗔𝗦𝗦", reply_markup=cancel_kb)
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

@bot.my_chat_member_handler()
def on_user_block_or_unblock(message):
    new_status = message.new_chat_member.status
    user_id = message.from_user.id
    name = message.from_user.first_name or "User"
    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    profile_link = f"[{name}](tg://user?id={user_id})"
    user_info = data.get("users", {}).get(str(user_id), {})
    
    if new_status in ['kicked', 'left']:
        user_info["blocked"] = True
        save_data(data)
        alert = (
            f"🚫 **User Left / Blocked Bot Alert:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User: {profile_link}\n"
            f"🆔 User ID: [`{user_id}`](tg://user?id={user_id})\n"
            f"🔗 Username: {username}\n"
            f"💵 Balance: `{user_info.get('balance', 0)} Credits`\n"
            f"👥 Referrals: `{user_info.get('total_referrals', 0)}`\n"
            f"📅 Left At: `{time.strftime('%d-%m-%Y %H:%M')}`"
        )
        for adm in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(adm, alert, parse_mode="Markdown")
            except Exception:
                pass
    elif new_status == 'member':
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["blocked"] = False
            save_data(data)

@bot.message_handler(content_types=['new_chat_members'])
def on_bot_joined_group(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            chat_id = message.chat.id
            if chat_id not in data.get("groups", []):
                data.setdefault("groups", []).append(chat_id)
                save_data(data)
            bot.send_message(chat_id, "gmailcrtorbot here we are best we are no 1 gmai provider genuine mails try us")

@bot.message_handler(commands=['start', 'admin'])
def start_handler(message):
    user_id = message.from_user.id
    if user_id in data.get("banned", []):
        bot.send_message(user_id, "⛔ You are banned from using this bot.")
        return

    if data.get("settings", {}).get("maintenance", False) and not is_admin(user_id):
        bot.send_message(user_id, "🛠️ **Bot is under maintenance for upgrades!**\nPlease wait, we will be back online soon.")
        return

    str_id = str(user_id)
    is_existing = str_id in data.get("users", {})
    was_blocked = is_existing and data["users"][str_id].get("blocked", False)
    
    user = get_user(user_id, message.from_user)
    user_states.pop(user_id, None)

    # Notify admin only for New User or Restart (after unblock/left)
    if data.get("settings", {}).get("new_user_notify", True) and user_id not in SUPER_ADMINS:
        if not is_existing or was_blocked:
            name = message.from_user.first_name or "User"
            username = f"@{message.from_user.username}" if message.from_user.username else "None"
            profile_link = f"[{name}](tg://user?id={user_id})"
            status_text = "🔄 **Restart User Alert:**" if was_blocked else "🆕 **New User Alert:**"
            alert_msg = (
                f"{status_text}\n"
                f"👤 Name: {profile_link}\n"
                f"🆔 User ID: [`{user_id}`](tg://user?id={user_id})\n"
                f"🔗 Username: {username}\n"
                f"📅 Date: `{time.strftime('%d-%m-%Y %H:%M')}`"
            )
            for adm in data.get("admins", SUPER_ADMINS):
                try:
                    bot.send_message(adm, alert_msg, parse_mode="Markdown")
                except Exception:
                    pass

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
    user = get_user(user_id, call.from_user)

    if call.data == "check_joined":
        if is_subscribed(user_id):
            if user.get("referred_by") and not user.get("referral_rewarded"):
                ref_user = get_user(user["referred_by"])
                ref_user["balance"] += PER_REFERRAL_REWARD
                ref_user["total_referrals"] += 1
                user["referral_rewarded"] = True
                save_data(data)
                try:
                    bot.send_message(int(user["referred_by"]), f"🎉 New user joined via your link! +{PER_REFERRAL_REWARD} Credit added.")
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

    if call.data == "open_use_credit_menu":
        bot.send_message(user_id, "👇 **Use Credit Points Menu:**", reply_markup=get_use_credit_menu_keyboard(), parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    # Use Credit Points Redeem Actions (Admin Free Unlimited Access)
    if call.data == "use_cred_gmail":
        admin_mode = is_admin(user_id)
        if not admin_mode and user["balance"] < 10:
            bot.answer_callback_query(call.id, "❌ You need at least 10 Credits!", show_alert=True)
            return
        if not admin_mode:
            user["balance"] -= 10
            save_data(data)
        
        user_card = format_user_card(call.from_user, user_id)
        for adm in data.get("admins", SUPER_ADMINS):
            try:
                tag = "👑 ADMIN TEST REQUEST" if admin_mode else "🎁 CREDIT USER"
                bot.send_message(adm, f"{tag} - Free Gmail Request:\n{user_card}", reply_markup=get_admin_action_keyboard(user_id), parse_mode="Markdown")
            except Exception:
                pass
                
        bot.send_message(user_id, "Your request has been sent to the moderator. Please hold for 10 minutes.")
        bot.answer_callback_query(call.id, "Request Submitted ✅")
        return

    elif call.data == "use_cred_outlook":
        admin_mode = is_admin(user_id)
        if not admin_mode and user["balance"] < 5:
            bot.answer_callback_query(call.id, "❌ You need at least 5 Credits!", show_alert=True)
            return
        if not admin_mode:
            user["balance"] -= 5
            save_data(data)
        
        user_card = format_user_card(call.from_user, user_id)
        for adm in data.get("admins", SUPER_ADMINS):
            try:
                tag = "👑 ADMIN TEST REQUEST" if admin_mode else "🎁 CREDIT USER"
                bot.send_message(adm, f"{tag} - Outlook Mail Request:\n{user_card}", reply_markup=get_admin_action_keyboard(user_id), parse_mode="Markdown")
            except Exception:
                pass
                
        bot.send_message(user_id, "Your request has been sent to the moderator. Please hold for 10 minutes.")
        bot.answer_callback_query(call.id, "Request Submitted ✅")
        return

    elif call.data == "use_cred_numdet":
        admin_mode = is_admin(user_id)
        if not admin_mode and user["balance"] < 1:
            bot.answer_callback_query(call.id, "❌ You need at least 1 Credit!", show_alert=True)
            return
        if not admin_mode:
            user["balance"] -= 1
            save_data(data)
        user_states[user_id] = "AWAITING_NUMBER_INPUT"
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
        bot.send_message(user_id, "🔍 Please enter the number (must start with +91, format: +91XXXXXXXXXX):", reply_markup=cancel_kb)
        bot.answer_callback_query(call.id, "Enter Phone Number")
        return

    elif call.data == "use_cred_ticket":
        admin_mode = is_admin(user_id)
        if not admin_mode and user["balance"] < 10:
            bot.answer_callback_query(call.id, "❌ 10 Credits required for Lucky Redeem Ticket!", show_alert=True)
            return
        if not admin_mode:
            user["balance"] -= 10
            save_data(data)
        
        weights = [t["chance"] for t in REDEEM_TICKETS]
        selected_ticket = random.choices(REDEEM_TICKETS, weights=weights, k=1)[0]
        
        user_card = format_user_card(call.from_user, user_id)
        for adm in data.get("admins", SUPER_ADMINS):
            try:
                tag = "👑 ADMIN TEST LUCK" if admin_mode else "🎟️ CREDIT USER"
                bot.send_message(adm, f"{tag} - Lucky Ticket Win:\n{user_card}\nTicket: `{selected_ticket['code']}`", reply_markup=get_admin_action_keyboard(user_id), parse_mode="Markdown")
            except Exception:
                pass

        bal_str = "Unlimited (Admin Test)" if admin_mode else f"{user['balance']} Credits"
        result_msg = (
            f"🎟️ **LUCKY REDEEM TICKET RESULT** 🎟️\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ Ticket: `{selected_ticket['code']}`\n\n"
            f"{selected_ticket['msg']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Remaining Balance: `{bal_str}`"
        )
        bot.send_message(user_id, result_msg, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "Ticket Drawn! 🎰")
        return

    if call.data.startswith("rate_"):
        rating = call.data.split("_")[1]
        user_states[user_id] = {"mode": "WAITING_FEEDBACK_TEXT", "rating": rating}
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
        bot.send_message(user_id, f"⭐ You selected **{rating} Stars**! Please write your short review/feedback now:", reply_markup=cancel_kb, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return

    if call.data == "user_reply_to_admin":
        user_states[user_id] = "AWAITING_ADMIN_REPLY_INPUT"
        cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
        bot.send_message(user_id, "✍️ Type your reply for the admin:", reply_markup=cancel_kb)
        return

    # Admin Control Handlers
    if is_admin(user_id):
        if call.data == "adm_cmd_stats":
            total_users = len(data.get("users", {}))
            total_admins = len(data.get("admins", SUPER_ADMINS))
            stats_text = (
                f"📊 **DETAILED BOT STATISTICS**\n━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 Total Registered Users: `{total_users}`\n"
                f"👑 Total Active Admins: `{total_admins}`\n"
                f"👥 Active Groups Connected: `{len(data.get('groups', []))}`\n"
                f"🚫 Banned Users Count: `{len(data.get('banned', []))}`\n"
                f"⭐ Total Reviews Received: `{len(data.get('feedbacks', []))}`\n"
                f"🔒 QR System Status: `{'LOCKED' if data.get('qr_locked', True) else 'UNLOCKED'}`\n"
                f"⚙️ Maintenance Mode: `{'ON' if data['settings'].get('maintenance') else 'OFF'}`\n"
                f"🔔 New User Notify: `{'ON' if data['settings'].get('new_user_notify') else 'OFF'}`\n"
                f"⏰ Auto Timer Status: `{'ON' if data.get('scheduler', {}).get('enabled') else 'OFF'}`\n"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👥 View Users List", callback_data="adm_view_users_list"))
            bot.send_message(user_id, stats_text, reply_markup=markup, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data == "adm_view_users_list":
            users = data.get("users", {})
            if not users:
                bot.send_message(user_id, "No users registered yet.")
                bot.answer_callback_query(call.id)
                return
            lines = ["📋 **REGISTERED USERS LIST:**\n━━━━━━━━━━━━━━━━━━━━"]
            for idx, (uid, uinfo) in enumerate(users.items(), 1):
                name = uinfo.get("name", "User")
                uname = f"@{uinfo.get('username')}" if uinfo.get('username') else "No Username"
                bal = uinfo.get("balance", 0)
                lines.append(f"{idx}. [{name}](tg://user?id={uid}) (`{uid}`) | {uname}\n   💵 Balance: `{bal} Credits`")
                if len(lines) >= 30:
                    break
            bot.send_message(user_id, "\n".join(lines), parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_toggle_qrlock":
            data["qr_locked"] = not data.get("qr_locked", True)
            save_data(data)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_inline())
            bot.answer_callback_query(call.id, f"QR is now {'LOCKED 🔒' if data['qr_locked'] else 'UNLOCKED 🔓'}")

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

        elif call.data == "adm_cmd_auto_timer":
            user_states[user_id] = "TIMER_SET_TEXT"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            bot.send_message(user_id, "✍️ **Step 1:** Send the **Custom Message Text** you want the bot to broadcast automatically:", reply_markup=cancel_kb, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data.startswith("set_timer_target_"):
            target_type = call.data.split("set_timer_target_")[1]
            data.setdefault("scheduler", {})["target"] = target_type
            save_data(data)
            bot.send_message(user_id, f"✅ Target set to `{target_type.upper()}`! Auto-timer is broadcasting.")
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_mail":
            user_states[user_id] = "ADMIN_BROADCAST"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            bot.send_message(user_id, "📨 **Send the Broadcast Message or Photo** you want to send to ALL users:", reply_markup=cancel_kb)
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_manage_admins":
            users = data.get("users", {})
            if not users:
                bot.send_message(user_id, "No users in database to manage.")
                bot.answer_callback_query(call.id)
                return
            markup = types.InlineKeyboardMarkup(row_width=1)
            for uid, uinfo in list(users.items())[:35]:
                name = uinfo.get("name", "User")
                is_adm = int(uid) in data.get("admins", SUPER_ADMINS)
                status_icon = "👑 Admin"
                if not is_adm:
                    status_icon = "👤 Member"
                markup.add(types.InlineKeyboardButton(f"{name} ({uid}) - {status_icon}", callback_data=f"adm_toggle_promote_{uid}"))
            bot.send_message(user_id, "👥 **Select a member to Promote or Demote:**", reply_markup=markup, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data.startswith("adm_toggle_promote_"):
            target_uid = int(call.data.split("adm_toggle_promote_")[1])
            if target_uid in SUPER_ADMINS:
                bot.answer_callback_query(call.id, "Cannot modify Super Admin!", show_alert=True)
                return
            if target_uid in data.get("admins", []):
                data["admins"].remove(target_uid)
                save_data(data)
                bot.answer_callback_query(call.id, "Demoted successfully ❌")
                try:
                    bot.send_message(target_uid, "You are demoted from the admin.")
                except Exception:
                    pass
            else:
                data.setdefault("admins", []).append(target_uid)
                save_data(data)
                bot.answer_callback_query(call.id, "Promoted successfully ✅")
                try:
                    bot.send_message(target_uid, "Congrats now you are the moderator of our bot.")
                except Exception:
                    pass
            return

        elif call.data == "adm_cmd_manage_credits":
            user_states[user_id] = "ADMIN_MANAGE_CREDITS_ID"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            bot.send_message(user_id, "💰 Enter the **User ID or Username** (e.g. `123456789` or `@username`):", reply_markup=cancel_kb, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif call.data == "adm_cmd_update_qr":
            user_states[user_id] = "ADMIN_SET_QR"
            cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_kb.add(types.KeyboardButton("🚫 Cancel"))
            bot.send_message(user_id, "🖼️ Please send the **new QR Code Photo** right now (This will update and lock your QR):", reply_markup=cancel_kb)
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
            bot.send_message(user_id, f"✍️ Type the **Reply / Details** for User [`{target_id}`](tg://user?id={target_id}) (User will get Reply button):", parse_mode="Markdown")

        elif call.data.startswith("adm_not_"):
            target_id = int(call.data.split("adm_not_")[1])
            user_states[user_id] = {"mode": "ADMIN_NOTIFYING", "target": target_id}
            bot.send_message(user_id, f"📢 Type the **Notification Alert** for User [`{target_id}`](tg://user?id={target_id}) (No Reply button):", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo'])
def handle_all_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text or ""

    if message.chat.type in ['group', 'supergroup']:
        if chat_id not in data.get("groups", []):
            data.setdefault("groups", []).append(chat_id)
            save_data(data)
        return

    # Auto-delete older user action messages if exceeding limit (Keep chat clean)
    user_last_messages.setdefault(user_id, [])
    user_last_messages[user_id].append(message.message_id)
    if len(user_last_messages[user_id]) > 4:
        old_msg_id = user_last_messages[user_id].pop(0)
        try:
            bot.delete_message(chat_id, old_msg_id)
        except Exception:
            pass

    if data.get("settings", {}).get("maintenance", False) and not is_admin(user_id):
        bot.send_message(user_id, "🛠️ **Bot is under maintenance for upgrades!**\nPlease wait, we will be back online soon.")
        return

    if user_id in data.get("banned", []):
        bot.send_message(user_id, "⛔ You are banned from using this bot.")
        return

    # Cancel handling (Universal check)
    if text in ["🚫 Cancel", "❌ Cancel"]:
        user_states.pop(user_id, None)
        bot.send_message(user_id, "❌ Action Cancelled.", reply_markup=get_bottom_menu_keyboard(user_id))
        return

    # Admin Control Multi-step Handlers
    if is_admin(user_id) and user_id in user_states:
        state_data = user_states[user_id]

        if state_data == "ADMIN_MANAGE_CREDITS_ID":
            found_key = find_user_key(text)
            if found_key:
                user_states[user_id] = {"mode": "ADMIN_MANAGE_CREDITS_VAL", "target": found_key}
                card = format_user_card_by_id(found_key)
                bot.send_message(user_id, f"{card}\n\n🎁 **Enter Credits to Gift / Set:** (e.g. `5`, `+10`, `-2`)", parse_mode="Markdown")
            else:
                bot.send_message(user_id, "❌ User not found in database. Make sure user has started the bot! Try again or Cancel:")
            return

        elif isinstance(state_data, dict) and state_data.get("mode") == "ADMIN_MANAGE_CREDITS_VAL":
            target_usr = state_data["target"]
            user_states.pop(user_id, None)
            try:
                added_amount = 0
                if text.startswith("+"):
                    added_amount = int(text[1:])
                    data["users"][target_usr]["balance"] += added_amount
                elif text.startswith("-"):
                    added_amount = -int(text[1:])
                    data["users"][target_usr]["balance"] += added_amount
                elif text.isdigit():
                    new_val = int(text)
                    added_amount = new_val - data["users"][target_usr]["balance"]
                    data["users"][target_usr]["balance"] = new_val
                else:
                    bot.send_message(user_id, "❌ Invalid format. Operation cancelled.", reply_markup=get_bottom_menu_keyboard(user_id))
                    return
                save_data(data)
                
                # Notify User
                try:
                    bot.send_message(int(target_usr), f"🎉 **Congratulations!**\nAdmin has gifted you **+{added_amount} Credits**!\nNew Balance: `{data['users'][target_usr]['balance']} Credits`", parse_mode="Markdown")
                except Exception:
                    pass

                bot.send_message(user_id, f"✅ Successfully updated balance for user `{target_usr}`. New Balance: `{data['users'][target_usr]['balance']} Credits`", parse_mode="Markdown", reply_markup=get_bottom_menu_keyboard(user_id))
            except Exception as e:
                bot.send_message(user_id, f"❌ Error: {e}", reply_markup=get_bottom_menu_keyboard(user_id))
            return

        elif state_data == "TIMER_SET_TEXT":
            user_states[user_id] = {"mode": "TIMER_SET_INTERVAL", "text": text}
            bot.send_message(user_id, "⏱️ **Step 2:** How much gap between each message? (e.g. `10 minutes`, `1 hour`, `120 mins` or `60`):", parse_mode="Markdown")
            return

        elif isinstance(state_data, dict) and state_data.get("mode") == "TIMER_SET_INTERVAL":
            parsed_mins = parse_time_input(text)
            if parsed_mins and parsed_mins > 0:
                msg_text = state_data["text"]
                data.setdefault("scheduler", {})
                data["scheduler"]["interval_min"] = parsed_mins
                data["scheduler"]["text"] = msg_text
                data["scheduler"]["enabled"] = True
                save_data(data)
                user_states.pop(user_id, None)
                
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("🌐 All", callback_data="set_timer_target_all"),
                    types.InlineKeyboardButton("👥 Groups Only", callback_data="set_timer_target_groups"),
                    types.InlineKeyboardButton("👤 Users Only", callback_data="set_timer_target_users")
                )
                bot.send_message(user_id, f"✅ **Auto Timer Activated!**\n⏱ Interval: Every `{parsed_mins}` minutes\n📝 Text:\n{msg_text}\n\n👇 **Select Broadcast Target:**", reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(user_id, "⚠️ Invalid format! Please type like `10 minutes`, `1 hour`, or numbers like `30`:")
            return

        elif state_data == "ADMIN_SET_QR":
            if message.content_type == 'photo':
                data["qr_file_id"] = message.photo[-1].file_id
                data["qr_locked"] = True
                save_data(data)
                user_states.pop(user_id, None)
                bot.send_message(user_id, "✅ **New QR Code updated and Locked permanently!**", reply_markup=get_bottom_menu_keyboard(user_id))
            else:
                bot.send_message(user_id, "⚠️ Please send a valid photo.")
            return

        elif state_data == "ADMIN_ADD_ADMIN":
            found_key = find_user_key(text)
            user_states.pop(user_id, None)
            if found_key:
                new_adm = int(found_key)
                if new_adm not in data["admins"]:
                    data["admins"].append(new_adm)
                    save_data(data)
                    bot.send_message(user_id, f"✅ User [`{new_adm}`](tg://user?id={new_adm}) added to Admins list!", reply_markup=get_bottom_menu_keyboard(user_id), parse_mode="Markdown")
                else:
                    bot.send_message(user_id, "⚠️ User is already an admin.", reply_markup=get_bottom_menu_keyboard(user_id))
            else:
                bot.send_message(user_id, "❌ User not found in database.", reply_markup=get_bottom_menu_keyboard(user_id))
            return

        elif state_data == "ADMIN_BROADCAST":
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

        elif isinstance(state_data, dict) and state_data.get("mode") in ["ADMIN_REPLYING", "ADMIN_NOTIFYING"]:
            target = state_data["target"]
            mode = state_data["mode"]
            user_states.pop(user_id, None)

            if mode == "ADMIN_REPLYING":
                try:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Reply to Admin", callback_data="user_reply_to_admin"))
                    msg_body = f"💬 **Admin message #msg**\n─────────────────\n{text}"
                    bot.send_message(target, msg_body, reply_markup=markup, parse_mode="Markdown")
                    bot.send_message(user_id, f"✔ Message successfully sent to user ([`{target}`](tg://user?id={target})) with Reply option!", parse_mode="Markdown")
                except Exception as e:
                    bot.send_message(user_id, f"❌ Failed to send: {e}")
                return

            elif mode == "ADMIN_NOTIFYING":
                try:
                    bot.send_message(target, f"🔔 **Notification Alert:**\n\n{text}", parse_mode="Markdown")
                    bot.send_message(user_id, f"✔ Alert successfully sent to user ([`{target}`](tg://user?id={target})) without Reply button!", parse_mode="Markdown")
                except Exception as e:
                    bot.send_message(user_id, f"❌ Failed to send: {e}")
                return

    # Feedback Handler
    if user_id in user_states and isinstance(user_states[user_id], dict) and user_states[user_id].get("mode") == "WAITING_FEEDBACK_TEXT":
        rating = user_states[user_id]["rating"]
        user_states.pop(user_id, None)
        
        feed_entry = {"user_id": user_id, "rating": rating, "text": text, "date": time.strftime("%d-%m-%Y %H:%M")}
        data.setdefault("feedbacks", []).append(feed_entry)
        save_data(data)
        
        user_card = format_user_card(message.from_user, user_id)
        admin_feedback_msg = (
            f"⭐ **New Rating & Feedback Received!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{user_card}\n"
            f"⭐ Rating: `{rating} / 5 Stars`\n"
            f"📝 Review: {text}"
        )
        for adm in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(adm, admin_feedback_msg, parse_mode="Markdown")
            except Exception:
                pass
                
        bot.send_message(user_id, "❤️ **Thank you for your valuable feedback!**", reply_markup=get_bottom_menu_keyboard(user_id), parse_mode="Markdown")
        return

    # Direct Reply To Admin (No length restrictions)
    if user_id in user_states and user_states[user_id] == "AWAITING_ADMIN_REPLY_INPUT":
        user_states.pop(user_id, None)
        user_card = format_user_card(message.from_user, user_id)
        report_card = (
            f"💬 **User Reply to Admin:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{user_card}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📩 **Message:**\n{text}"
        )
        for admin in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(admin, report_card, reply_markup=get_admin_action_keyboard(user_id), parse_mode="Markdown")
            except Exception:
                pass
        bot.send_message(user_id, "✔ **Your reply has been sent to Admin!**", reply_markup=get_bottom_menu_keyboard(user_id), parse_mode="Markdown")
        return

    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            WELCOME_TEXT,
            reply_markup=get_force_join_keyboard(),
            parse_mode="Markdown"
        )
        return

    state = user_states.get(user_id)

    # Number Details Input Validation for Credit Service
    if state == "AWAITING_NUMBER_INPUT":
        user_states.pop(user_id, None)
        if not text.startswith("+91") or len(text) < 13:
            bot.send_message(
                user_id,
                "❌ Send Number must start with\n         +91\n📞 Format: +91XXXXXXXXXX",
                reply_markup=get_bottom_menu_keyboard(user_id)
            )
            return
        
        user_card = format_user_card(message.from_user, user_id)
        for admin in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(
                    admin,
                    f"🔍 **CREDIT USER - Number Details Query:**\n{user_card}\n\n📱 **Target Number:**\n`{text}`",
                    reply_markup=get_admin_action_keyboard(user_id),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        bot.send_message(user_id, "Your request has been sent to the moderator. Please hold for 10 minutes.", reply_markup=get_bottom_menu_keyboard(user_id))
        return

    # Consumer Helpline State (Only applies here)
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
        user_card = format_user_card(message.from_user, user_id)
        
        report_card = (
            f"📩 **24x7 Consumer Support**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{user_card}\n"
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

    if state == "AWAITING_PAYMENT_SS":
        user_states.pop(user_id, None)
        user_card = format_user_card(message.from_user, user_id)

        admin_caption = (
            f"💳 **New Payment Order Submission:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{user_card}"
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

    if state == "AWAITING_CREDENTIALS":
        user_states.pop(user_id, None)
        processing_timers[user_id] = time.time()
        user_card = format_user_card(message.from_user, user_id)

        for admin in data.get("admins", SUPER_ADMINS):
            try:
                bot.send_message(
                    admin,
                    f"🔐 **User Credentials Received:**\n{user_card}\n\n📝 **Credentials:**\n`{text}`",
                    reply_markup=get_admin_action_keyboard(user_id),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        bot.send_message(user_id, "𝙂𝙢𝙖𝙞𝙡 𝙞𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙥𝙡𝙨 𝙬𝙖𝙞𝙩✋🥺", reply_markup=get_bottom_menu_keyboard(user_id))
        return

    if user_id in processing_timers and not is_admin(user_id):
        if time.time() - processing_timers[user_id] < 1200:
            if text not in MENU_BUTTONS:
                bot.send_message(user_id, "W8 a minute 𝙂𝙢𝙖𝙞𝙡 𝙞𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙥𝙡𝙨 𝙬𝙖𝙞𝙩✋🥺")
                return
        else:
            processing_timers.pop(user_id, None)

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

    elif text == "Balance":
        user_info = get_user(user_id, message.from_user)
        name = message.from_user.first_name or "User"
        profile_link = f"[{name}](tg://user?id={user_id})"
        username = f"@{message.from_user.username}" if message.from_user.username else "None"
        
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(types.InlineKeyboardButton("Use credit 💳", callback_data="open_use_credit_menu"))

        balance_card = (
            f"👤 **USER ACCOUNT & BALANCE DETAILS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Name:** {profile_link}\n"
            f"🆔 **User ID:** [`{user_id}`](tg://user?id={user_id})\n"
            f"🔗 **Username:** {username}\n"
            f"💵 **Current Balance:** `{user_info.get('balance', 0)} Credits`\n"
            f"👥 **Total Referrals:** `{user_info.get('total_referrals', 0)} Users`\n"
            f"📅 **Member Since:** `{user_info.get('joined_at', '2026')}`"
        )
        bot.send_message(user_id, balance_card, reply_markup=inline_kb, parse_mode="Markdown")

    elif text == "👥 Referrals":
        user_info = get_user(user_id, message.from_user)
        try:
            bot_username = bot.get_me().username
            ref_link = f"https://t.me/{bot_username}?start={user_id}"
            bot.send_message(
                user_id,
                f"👥 **Refer & Earn Program:**\n\n"
                f"Share your referral link with friends and earn **+{PER_REFERRAL_REWARD} Credit** for every joined user!\n\n"
                f"🔗 **Your Link:**\n`{ref_link}`\n\n"
                f"📊 Total Referrals: `{user_info.get('total_referrals', 0)}`",
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(user_id, "⚠️ Error generating referral link. Please try again later.")

    elif text == "⭐ Rating / Feedback":
        bot.send_message(user_id, "🌟 **How was your experience with us?**\nPlease choose a rating below:", reply_markup=get_rating_keyboard())

    elif text == "⚙️ Help":
        help_markup = types.InlineKeyboardMarkup()
        help_markup.add(types.InlineKeyboardButton("📢 Official Announcement Channel", url=ANNOUNCEMENT_CHANNEL_LINK))
        
        help_text = (
            "⚙️ **Help & Information:**\n\n"
            "• **Mail create:** Request fresh and premium Gmail accounts.\n"
            "• **Referrals:** Invite friends to earn free credits.\n"
            "• **24x7 consumer helpline:** Send direct report to support team.\n"
            "• **Rating / Feedback:** Rate your order experience."
        )
        bot.send_message(user_id, help_text, reply_markup=help_markup, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            time.sleep(3)
