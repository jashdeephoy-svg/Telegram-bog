import os
import time
import json
import threading
import requests
import telebot
from telebot import types

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8950259719:AAGW4Bf5vXmFBO6VaVSGedl1LgjHoLO5U-k"
CHECK_INTERVAL_SECONDS = 30  # Har 30 second me Instagram check karega
DB_FILE = "dual_tracker_db.json"

# Visual GIFs (Aap apne hisaab se URL change kar sakte hain)
MONITORING_GIF = "https://media.giphy.com/media/3o7TKTDnUxE0g2fSE8/giphy.gif"
UNBANNED_GIF = "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif"
BANNED_GIF = "https://media.giphy.com/media/l2YWg3f6m0tI7Ff2w/giphy.gif"
# --------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

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

# ----------------- TIME FORMATTER -----------------
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

# ----------------- INSTAGRAM LIVE CHECKER -----------------
def is_instagram_active(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 404:
            return False
        if response.status_code == 200:
            if "Sorry, this page isn't available." in response.text or "The link you followed may be broken" in response.text:
                return False
            return True
        return False
    except Exception:
        return False

# ----------------- BACKGROUND MONITORING THREAD -----------------
def monitor_loop():
    while True:
        try:
            # 1. Unban / Recovery Monitoring (/ub)
            unban_list = list(db.get("unban_monitors", {}).items())
            for username, info in unban_list:
                if is_instagram_active(username):
                    elapsed = time.time() - info.get("start_time", time.time())
                    time_str = format_time_taken(elapsed)
                    user_mention = f'<a href="tg://user?id={info["user_id"]}">{info.get("user_name", "User")}</a>'

                    caption = (
                        f"📸 <b>Instagram Account Unbanned</b>\n\n"
                        f"<b>@{username}</b>\n"
                        f"⏱ <b>Time Taken:</b> {time_str}\n"
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
                        print(f"Error sending unban alert: {e}")

                    del db["unban_monitors"][username]
                    save_db(db)

                time.sleep(2)

            # 2. Ban Monitoring (/b)
            ban_list = list(db.get("ban_monitors", {}).items())
            for username, info in ban_list:
                if not is_instagram_active(username):
                    elapsed = time.time() - info.get("start_time", time.time())
                    time_str = format_time_taken(elapsed)
                    user_mention = f'<a href="tg://user?id={info["user_id"]}">{info.get("user_name", "User")}</a>'

                    caption = (
                        f"🚫 <b>Instagram Account Banned</b>\n\n"
                        f"<b>@{username}</b>\n"
                        f"⏱ <b>Time Taken:</b> {time_str}\n"
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
                        print(f"Error sending ban alert: {e}")

                    del db["ban_monitors"][username]
                    save_db(db)

                time.sleep(2)

            time.sleep(CHECK_INTERVAL_SECONDS)
        except Exception as e:
            print(f"Background Loop Error: {e}")
            time.sleep(10)

threading.Thread(target=monitor_loop, daemon=True).start()

# ----------------- HELPER FUNCTIONS -----------------
def extract_username(message):
    args = message.text.split()
    if len(args) < 2:
        return None
    return args[1].strip().replace("@", "").lower()

# ----------------- COMMAND: /ub (UNBAN MONITOR) -----------------
@bot.message_handler(commands=['ub', 'unban', 'm'])
def handle_unban_request(message):
    username = extract_username(message)
    if not username:
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/ub username</code>\nExample: <code>/ub fvowl</code>")
        return

    if username in db.get("unban_monitors", {}):
        bot.reply_to(message, f"ℹ️ <b>@{username}</b> pehle se Unban monitoring list me active hai.")
        return

    # Check if already active
    if is_instagram_active(username):
        bot.reply_to(message, f"⚠️ <b>Request Denied:</b> <b>@{username}</b> account pehle se hi <b>Active / Unbanned</b> hai!")
        return

    user_mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name or "User"}</a>'
    
    db.setdefault("unban_monitors", {})[username] = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "user_name": message.from_user.first_name or "User",
        "start_time": time.time(),
        "date_added": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_db(db)

    caption = (
        f"🕒 <b>Instagram Account Monitoring (Unban)</b>\n\n"
        f"<b>@{username}</b> added successfully.\n"
        f"You'll be notified as soon as the account is active.\n\n"
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
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/b username</code>\nExample: <code>/b fvowl</code>")
        return

    if username in db.get("ban_monitors", {}):
        bot.reply_to(message, f"ℹ️ <b>@{username}</b> pehle se Ban monitoring list me active hai.")
        return

    # Check if already banned
    if not is_instagram_active(username):
        bot.reply_to(message, f"⚠️ <b>Request Denied:</b> <b>@{username}</b> account pehle se hi <b>Banned / Unavailable</b> hai!")
        return

    user_mention = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name or "User"}</a>'
    
    db.setdefault("ban_monitors", {})[username] = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "user_name": message.from_user.first_name or "User",
        "start_time": time.time(),
        "date_added": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_db(db)

    caption = (
        f"🎯 <b>Instagram Account Monitoring (Ban)</b>\n\n"
        f"<b>@{username}</b> added successfully.\n"
        f"You'll be notified as soon as the account gets banned.\n\n"
        f"👤 <b>Requested by:</b> {user_mention}"
    )

    try:
        bot.send_animation(chat_id=message.chat.id, animation=MONITORING_GIF, caption=caption, reply_to_message_id=message.message_id)
    except Exception:
        bot.send_message(chat_id=message.chat.id, text=caption, reply_to_message_id=message.message_id)

# ----------------- COMMAND: /status -----------------
@bot.message_handler(commands=['status', 'list'])
def handle_status_command(message):
    unbans = db.get("unban_monitors", {})
    bans = db.get("ban_monitors", {})

    if not unbans and not bans:
        bot.reply_to(message, "📭 Abhi koi account monitoring list me active nahi hai.")
        return

    lines = ["📊 <b>CURRENT ACTIVE MONITORS:</b>\n━━━━━━━━━━━━━━━━━━━━"]
    
    if unbans:
        lines.append("\n🟢 <b>Waiting for Unban / Recovery:</b>")
        for u, d in unbans.items():
            t = format_time_taken(time.time() - d["start_time"])
            lines.append(f"• <b>@{u}</b> (Elapsed: <code>{t}</code>) — by {d.get('user_name')}")

    if bans:
        lines.append("\n🔴 <b>Waiting for Ban:</b>")
        for u, d in bans.items():
            t = format_time_taken(time.time() - d["start_time"])
            lines.append(f"• <b>@{u}</b> (Elapsed: <code>{t}</code>) — by {d.get('user_name')}")

    bot.reply_to(message, "\n".join(lines))

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
