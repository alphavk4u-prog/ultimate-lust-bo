import os
import sqlite3
import logging
from datetime import datetime, timedelta
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=== BOT STARTING - AUTO CHANNEL FETCH MODE ===")

token = os.getenv("TOKEN")
if not token:
    print("ERROR: No TOKEN!")
    exit(1)

CHANNEL_USERNAME = "@UltimateLustFiles"

# Database
db_path = 'users.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, daily_count INTEGER, last_reset TEXT, is_premium INTEGER DEFAULT 0, last_free_time TEXT)''')
conn.commit()

async def fetch_all_media_ids(context, channel_username):
    """Channel के all media message IDs auto fetch by pagination"""
    media_ids = []
    last_id = 0  # Start from latest
    while True:
        try:
            messages = await context.bot.get_chat_history(chat_id=channel_username, limit=100, from_message_id=last_id)
            if not messages:
                break
            for msg in messages:
                if msg.photo or msg.video:
                    media_ids.append(msg.message_id)
            last_id = messages[-1].message_id - 1  # Paginate backwards
            if len(messages) < 100:
                break
        except Exception as e:
            print(f"Error fetching history: {e}")
            break
    print(f"Fetched {len(media_ids)} media IDs from channel")
    return media_ids

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆓 Free Access", callback_data="free")],
        [InlineKeyboardButton("💎 Premium Unlimited", callback_data="premium")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to @UltimateLust_Bot 🔥😈\n\n"
        "Free: 5 clicks/day (2 random hot files from channel)\n"
        "Premium: Unlimited + private group 💦\n\n"
        "Choose:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    today = datetime.now().date().isoformat()
    now = datetime.now()

    c.execute("SELECT daily_count, last_reset, is_premium, last_free_time FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if row:
        count, last_reset, is_premium, last_free_time = row
        if last_reset != today:
            count = 0
            last_free_time = None
            c.execute("UPDATE users SET daily_count=?, last_reset=?, last_free_time=? WHERE user_id=?", (count, today, last_free_time, user_id))
            conn.commit()
    else:
        is_premium = 0
        count = 0
        last_free_time = None
        c.execute("INSERT INTO users (user_id, daily_count, last_reset, is_premium, last_free_time) VALUES (?, ?, ?, ?, ?)", 
                  (user_id, count, today, is_premium, last_free_time))
        conn.commit()

    c.execute("SELECT daily_count, is_premium, last_free_time FROM users WHERE user_id=?", (user_id,))
    count, is_premium, last_free_time = c.fetchone()

    # Auto fetch media IDs from channel
    media_ids = await fetch_all_media_ids(context, CHANNEL_USERNAME)
    if not media_ids:
        await query.edit_message_text("No files in channel! Add some hot content 🔥")
        return

    if query.data == "free":
        if is_premium == 1:
            selected = random.sample(media_ids, min(2, len(media_ids)))
            for msg_id in selected:
                await context.bot.forward_message(chat_id=user_id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            await query.edit_message_text("Premium unlocked! 🔥 Unlimited hot files 💦")
            return

        if count >= 5:
            if last_free_time:
                last_time = datetime.fromisoformat(last_free_time)
                time_diff = now - last_time
                if time_diff < timedelta(minutes=30):
                    minutes_left = 30 - int(time_diff.total_seconds() / 60)
                    await query.edit_message_text(f"Free limit over! ⏳ Wait {minutes_left} minutes\nGo premium 💎")
                    return

        count += 1
        c.execute("UPDATE users SET daily_count=?, last_free_time=? WHERE user_id=?", (count, now.isoformat(), user_id))
        conn.commit()

        selected = random.sample(media_ids, min(2, len(media_ids)))
        for msg_id in selected:
            await context.bot.forward_message(chat_id=user_id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)

        caption = f"Free #{count}/5 🔥\nTeasing you... premium for full access 💦"
        await query.edit_message_text(caption)

    elif query.data == "premium":
        response = (
            "🔥 Unlimited files + private group!\n\n"
            "💎 Plans:\n"
            "• ₹99 → 1 Month\n"
            "• ₹699 → Lifetime 🔥\n\n"
            "UPI: akashzyt@ybl (Vishal Kumar)\n\n"
            "Payment करो → screenshot @Anjali_Sharma4u को भेजो → private group link मिलेगा!"
        )
        await query.edit_message_text(response)

    elif query.data == "help":
        response = (
            "❓ Help\n\n"
            "• Free: 5 clicks/day (2 files)\n"
            "• After limit: 30 min wait\n"
            "• Premium: Unlimited\n\n"
            "Admin: @Anjali_Sharma4u"
        )
        await query.edit_message_text(response)

try:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot LIVE - Auto fetching all channel files 🔥😈")
    app.run_polling(drop_pending_updates=True)
except Exception as e:
    print(f"ERROR: {e}")
