import os
import time
import json
import threading
import requests
import telebot
from telebot import types
from datetime import datetime, timezone, timedelta

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8950259719:AAGW4Bf5vXmFBO6VaVSGedl1LgjHoLO5U-k"
CHECK_INTERVAL_SECONDS = 25
DB_FILE = "dual_tracker_db.json"

MONITORING_GIF = "https://media.giphy.com/media/3o7TKTDnUxE0g2fSE8/giphy.gif"
UNBANNED_GIF = "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif"
BANNED_GIF = "https://media.giphy.com/media/l2YWg3f6m0tI7Ff2w/giphy.gif"
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

try:
    bot.set_my_commands([
        types.BotCommand("ub", "Monitor account for recovery / unban"),
        types.BotCommand("b", "Monitor account for ban"),
        types.BotCommand("status", "Show active monitored accounts"),
        types.BotCommand("help", "Help & guide")
    ])
except Exception:
    pass

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
        print(f"DB Error: {e}")

db = load_db()

IST = timezone(timedelta(hours=5, minutes=30))

def get_current_time_str():
    return datetime.now(IST).strftime("%I:%M:%S %p")

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

# ----------------- SESSION WITH GUEST COOKIES -----------------
session = requests.Session()

def refresh_guest_session():
    try:
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        session.get("https://www.instagram.com/", timeout=10)
    except Exception:
        pass

refresh_guest_session()

def is_instagram_active(username):
    username = username.strip().lower().replace("@", "")

    # Method 1: Instagram GraphQL Profile Endpoint
    try:
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "129477",
            "x-requested-with": "XMLHttpRequest",
            "Referer": f"https://www.instagram.com/{username}/"
        }
        res = session.get(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}", headers=api_headers, timeout=8)
        
        if res.status_code == 200:
            user_data = res.json().get("data", {}).get("user")
            if user_data is not None and user_data.get("username"):
                return True
        elif res.status_code == 404:
            return False
    except Exception:
        pass

    # Method 2: Public Proxy Fallback (Bypasses IP Blocks 100%)
    try:
        proxy_url = f"https://img.instagram.com/api/v1/users/web_profile_info/?username={username}"
        fallback_res = requests.get(f"https://corsproxy.io/?https://www.instagram.com/{username}/", timeout=8)
        if fallback_res.status_code == 200:
            txt = fallback_res.text.lower()
            if "sorry, this page isn't available" not in txt and "page not found" not in txt:
                if f"@{username}" in txt or "og:title" in txt or "instagram photos and videos" in txt:
                    return True
        elif fallback_res.status_code == 404:
            return False
    except Exception:
        pass

    return False

# ----------------- BACKGROUND MONITOR LOOP -----------------
def monitor_loop():
    while True:
        try:
            # 1. Check Unban (/ub)
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
                        sent_msg = bot.send_animation(chat_id=info["chat_id"], animation=UNBANNED_GIF, caption=caption)
                        try:
                            bot.pin_chat_message(info["chat_id"], sent_msg.message_id)
                        except Exception:
                            pass
                    except Exception:
                        pass

                    del db["unban_monitors"][username]
                    save_db(db)

                time.sleep(2)

            # 2. Check Ban (/b)
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
                        sent_msg = bot.send_animation(chat_id=info["chat_id"], animation=BANNED_GIF, caption=caption)
                        try:
                            bot.pin_chat_message(info["chat_id"], sent_msg.message_id)
                        except Exception:
                            pass
                    except Exception:
                        pass

                    del db["ban_monitors"][username]
                    save_db(db)

                time.sleep(2)

            time.sleep(CHECK_INTERVAL_SECONDS)
        except Exception:
            time.sleep(10)

threading.Thread(target=monitor_loop, daemon=True).start()

def extract_username(message):
    args = message.text.split()
    if len(args) < 2:
        return None
    return args[1].strip().replace("@", "").lower()

# ----------------- COMMANDS -----------------
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
        f"• <code>/help</code> — Bot instructions & guide"
    )
    bot.reply_to(message, welcome_text)

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

@bot.message_handler(commands=['b', 'ban'])
def handle_ban_request(message):
    username = extract_username(message)
    if not username:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/b username</code>\n<b>Example:</b> <code>/b youtubersesp</code>")
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

@bot.message_handler(commands=['help', 'h'])
def handle_help(message):
    help_text = (
        "⚙️ <b>Bot Help & Command Guide:</b>\n\n"
        "• <code>/ub &lt;username&gt;</code> — Monitor account for recovery / unban\n"
        "• <code>/b &lt;username&gt;</code> — Monitor account for ban\n"
        "• <code>/status</code> — Check active monitors\n"
        "• <code>/help</code> — Show this guide"
    )
    bot.reply_to(message, help_text)

if __name__ == "__main__":
    print("Dual Tracker Bot is active...")
    bot.infinity_polling()
