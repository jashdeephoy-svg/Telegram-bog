import os
import time
import json
import threading
import requests
import telebot
from telebot import types
from datetime import datetime

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8950259719:AAGW4Bf5vXmFBO6VaVSGedl1LgjHoLO5U-k"
CHECK_INTERVAL_SECONDS = 25
DB_FILE = "dual_tracker_db.json"

# Visual Media Links
MONITORING_GIF = "https://media.giphy.com/media/3o7TKTDnUxE0g2fSE8/giphy.gif"
UNBANNED_GIF = "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif"
BANNED_GIF = "https://media.giphy.com/media/l2YWg3f6m0tI7Ff2w/giphy.gif"
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Auto-set command suggestions for Telegram UI popup
try:
    bot.set_my_commands([
        types.BotCommand("ub", "Monitor an account for recovery / unban"),
        types.BotCommand("b", "Monitor an account for ban"),
        types.BotCommand("status", "Show active monitored accounts"),
        types.BotCommand("help", "Show help and bot usage")
    ])
except Exception as e:
    print(f"Command registration notice: {e}")

# ----------------- DATABASE HELPERS -----------------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"unban_monitors": {}, "ban_monitors": {}}
    return {"unban_monitors": {}, "ban_monitors": {}}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Database Error: {e}")

db = load_db()

# ----------------- TIME & DATE HELPERS -----------------
def get_current_time_str():
    return datetime.now().strftime("%I:%M:%S %p")

def format_time_taken(seconds_elapsed):
    days = int(seconds_elapsed // 86400)
    hours = int((seconds_elapsed % 86400) // 3600)
    minutes = int((seconds_elapsed % 3600) // 60)
    seconds = int(seconds_elapsed % 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"

# ----------------- ACCURATE INSTAGRAM CHECKER -----------------
def is_instagram_active(username):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    # Method 1: Web Request Check
    try:
        url = f"https://www.instagram.com/{username}/"
        res = requests.get(url, headers=headers, timeout=8, allow_redirects=False)
        
        # 404 means definitely unavailable / banned
        if res.status_code == 404:
            return False
            
        # 301/302 redirect usually means account is not found / routed to login
        if res.status_code in [301, 302]:
            loc = res.headers.get("Location", "")
            if "accounts/login" in loc or loc == "/" or f"/{username}/" not in loc:
                return False
                
        if res.status_code == 200:
            text = res.text.lower()
            if "sorry, this page isn't available" in text:
                return False
            if "link you followed may be broken" in text:
                return False
            if "user not found" in text:
                return False
            return True
    except Exception:
        pass

    # Method 2: API Fallback Check
    try:
        api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "x-ig-app-id": "936619743392459"
        }
        api_res = requests.get(api_url, headers=api_headers, timeout=8)
        if api_res.status_code == 404:
            return False
        if api_res.status_code == 200:
            data = api_res.json()
            if data.get("data", {}).get("user") is not None:
                return True
            return False
    except Exception:
        pass

    return False

# ----------------- BACKGROUND MONITORING THREAD -----------------
def monitor_loop():
    while True:
        try:
            # 1. Unban / Recovery Targets
            unban_list = list(db.get("unban_monitors", {}).items())
            for username, info in unban_list:
                if is_instagram_active(username):
                    elapsed = time.time() - info.get("start_time", time.time())
                    time_str = format_time_taken(elapsed)
                    req_time = info.get("requested_time", "N/A")
                    unban_time = get_current_time_str()
                    user_mention = f'<a href="tg://user?id={info["user_id"]}">{info.get("user_name", "User")}</a>'

                    caption = (
                        f"📸 <b>Instagram Account Unbanned</b>\n\n"
                        f"<b>@{username}</b>\n"
                        f"⏱ <b>Time Taken:</b> {time_str}\n"
                        f"🕒 <b>Requested at:</b> {req_time}\n"
                        f"✅ <b>Recovered at:</b> {unban_time}\n"
                        f"👤 <b>Requested by:</b> {user_mention}"
                    )

                    try:
                        sent_msg = bot.send_animation(
                            chat_id=info["chat_id"],
                            animation=UNBANNED_GIF,
                            caption=caption
                        )
                        try:
                            bot.pin_chat_message(info["chat_id"], sent_msg.message_id)
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"Error sending unban notification: {e}")

                    del db["unban_monitors"][username]
                    save_db(db)

                time.sleep(2)

            # 2. Ban Targets
            ban_list = list(db.get("ban_monitors", {}).items())
            for username, info in ban_list:
                if not is_instagram_active(username):
                    elapsed = time.time() - info.get("start_time", time.time())
                    time_str = format_time_taken(elapsed)
                    req_time = info.get("requested_time", "N/A")
                    ban_time = get_current_time_str()
                    user_mention = f'<a href="tg://user?id={info["user_id"]}">{info.get("user_name", "User")}</a>'

                    caption = (
                        f"🚫 <b>Instagram Account Banned</b>\n\n"
                        f"<b>@{username}</b>\n"
                        f"⏱ <b>Time Taken:</b> {time_str}\n"
                        f"🕒 <b>Requested at:</b> {req_time}\n"
                        f"❌ <b>Banned at:</b> {ban_time}\n"
                        f"👤 <b>Requested by:</b> {user_mention}"
                    )

                    try:
                        sent_msg = bot.send_animation(
                            chat_id=info["chat_id"],
                            animation=BANNED_GIF,
                            caption=caption
                        )
                        try:
                            bot.pin_chat_message(info["chat_id"], sent_msg.message_id)
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"Error sending ban notification: {e}")

                    del db["ban_monitors"][username]
                    save_db(db)

                time.sleep(2)

            time.sleep(CHECK_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(10)

threading.Thread(target=monitor_loop, daemon=True).start()

# ----------------- HELPER FUNCTIONS -----------------
def extract_username(message):
    args = message.text.split()
    if len(args) < 2:
        return None
    # Extract only clean first argument
    return args[1].strip().replace("@", "").lower()

# ----------------- START HANDLER (DM ONLY) -----------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"
    user_mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'

    welcome_text = (
        f"👋 <b>Welcome {user_mention}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User Name:</b> {user_name}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Available Commands:</b>\n"
        f"• <code>/ub &lt;username&gt;</code> — Monitor account for recovery / unban\n"
        f"• <code>/b &lt;username&gt;</code> — Monitor account for ban\n"
        f"• <code>/status</code> — View active monitored accounts\n"
        f"• <code>/help</code> — Bot instructions & guide\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>Add this bot to your group and give admin access to receive instant alerts!</i>"
    )
    bot.reply_to(message, welcome_text)

# ----------------- COMMAND: /ub (UNBAN MONITOR) -----------------
@bot.message_handler(commands=['ub', 'unban', 'm'])
def handle_unban_request(message):
    username = extract_username(message)
    if not username:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/ub username</code>\n<b>Example:</b> <code>/ub hers_vivek</code>")
        return

    if username in db.get("unban_monitors", {}):
        bot.reply_to(message, f"ℹ️ <b>@{username}</b> is already in the unban monitoring list.")
        return

    if is_instagram_active(username):
        bot.reply_to(message, f"⚠️ <b>Request Denied:</b> <b>@{username}</b> is already <b>Active / Unbanned</b> on Instagram.")
        return

    req_time = get_current_time_str()
    user_mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name or "User"}</a>'

    db.setdefault("unban_monitors", {})[username] = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "user_name": message.from_user.first_name or "User",
        "start_time": time.time(),
        "requested_time": req_time
    }
    save_db(db)

    caption = (
        f"🕒 <b>Instagram Account Monitoring (Recovery)</b>\n\n"
        f"<b>@{username}</b> added successfully.\n"
        f"You'll be notified as soon as the account is active.\n\n"
        f"🕒 <b>Requested at:</b> {req_time}\n"
        f"👤 <b>Requested by:</b> {user_mention}"
    )

    try:
        bot.send_animation(chat_id=message.chat.id, animation=MONITORING_GIF, caption=caption, reply_to_message_id=message.message_id)
    except Exception:
        bot.send_message(chat_id=message.chat.id, text=caption, reply_to_message_id=message.message_id)

# ----------------- COMMAND: /b (BAN MONITOR) -----------------
@bot.message_handler(commands=['b', 'ban'])
def handle_ban_request(message):
    username = extract_username(message)
    if not username:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/b username</code>\n<b>Example:</b> <code>/b hers_vivek</code>")
        return

    if username in db.get("ban_monitors", {}):
        bot.reply_to(message, f"ℹ️ <b>@{username}</b> is already in the ban monitoring list.")
        return

    if not is_instagram_active(username):
        bot.reply_to(message, f"⚠️ <b>Request Denied:</b> <b>@{username}</b> is already <b>Banned / Unavailable</b> on Instagram.")
        return

    req_time = get_current_time_str()
    user_mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name or "User"}</a>'

    db.setdefault("ban_monitors", {})[username] = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "user_name": message.from_user.first_name or "User",
        "start_time": time.time(),
        "requested_time": req_time
    }
    save_db(db)

    caption = (
        f"🎯 <b>Instagram Account Monitoring (Ban)</b>\n\n"
        f"<b>@{username}</b> added successfully.\n"
        f"You'll be notified as soon as the account is banned.\n\n"
        f"🕒 <b>Requested at:</b> {req_time}\n"
        f"👤 <b>Requested by:</b> {user_mention}"
    )

    try:
        bot.send_animation(chat_id=message.chat.id, animation=MONITORING_GIF, caption=caption, reply_to_message_id=message.message_id)
    except Exception:
        bot.send_message(chat_id=message.chat.id, text=caption, reply_to_message_id=message.message_id)

# ----------------- COMMAND: /status -----------------
@bot.message_handler(commands=['status', 's'])
def handle_status(message):
    unbans = db.get("unban_monitors", {})
    bans = db.get("ban_monitors", {})

    if not unbans and not bans:
        bot.reply_to(message, "📭 No accounts are currently being monitored.")
        return

    lines = ["📊 <b>Active Instagram Monitors:</b>\n━━━━━━━━━━━━━━━━━━━━"]
    
    if unbans:
        lines.append("\n🟢 <b>Awaiting Recovery / Unban:</b>")
        for u, d in unbans.items():
            t = format_time_taken(time.time() - d["start_time"])
            lines.append(f"• <b>@{u}</b> (Elapsed: <code>{t}</code>) — by {d.get('user_name')}")

    if bans:
        lines.append("\n🔴 <b>Awaiting Ban:</b>")
        for u, d in bans.items():
            t = format_time_taken(time.time() - d["start_time"])
            lines.append(f"• <b>@{u}</b> (Elapsed: <code>{t}</code>) — by {d.get('user_name')}")

    bot.reply_to(message, "\n".join(lines))

# ----------------- COMMAND: /help -----------------
@bot.message_handler(commands=['help', 'h'])
def handle_help(message):
    help_text = (
        "⚙️ <b>Bot Help & Command Guide:</b>\n\n"
        "• <code>/ub &lt;username&gt;</code> — Set an unban monitor. The bot alerts when the account comes back online.\n"
        "• <code>/b &lt;username&gt;</code> — Set a ban monitor. The bot alerts when the account gets banned.\n"
        "• <code>/status</code> — Check all ongoing active monitors.\n"
        "• <code>/help</code> — Show this help message."
    )
    bot.reply_to(message, help_text)

if __name__ == "__main__":
    print("Instagram Status Monitor Bot is online...")
    bot.infinity_polling()
