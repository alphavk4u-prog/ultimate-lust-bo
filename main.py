import os
import sqlite3
import logging
from datetime import datetime, timedelta
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=== BOT STARTING ===")

# Token
token = os.getenv("TOKEN")
if not token:
    print("ERROR: No TOKEN found!")
    exit(1)

# Private Channel
CHANNEL_USERNAME = "@UltimateLustFiles"  # तुम्हारा channel

# Database
db_path = 'users.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, daily_count INTEGER, last_reset TEXT, is_premium INTEGER DEFAULT 0, last_free_time TEXT)''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆓 Free Access", callback_data="free")],
        [InlineKeyboardButton("💎 Premium Unlimited", callback_data="premium")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to @UltimateLust_Bot 🔥😈\n\n"
        "Free: 5 random hot files/day from channel\n"
        "Premium: Unlimited + private group 💦\n\n"
        "Choose:",
        reply_markup=reply_markup
    )

async def get_channel_files(context, limit=50):
    """Channel के latest 'limit' posts से media वाले messages collect करो"""
    messages = await context.bot.get_chat_history(chat_id=CHANNEL_USERNAME, limit=limit)
    media_messages = []
    for msg in messages:
        if msg.photo or msg.video:
            media_messages.append(msg.message_id)
    return media_messages

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

    if query.data == "free":
        if is_premium == 1:
            # Premium: Unlimited 5 files
            media_ids = await get_channel_files(context, limit=100)
            if media_ids:
                selected = random.sample(media_ids, min(5, len(media_ids)))
                for msg_id in selected:
                    await context.bot.forward_message(chat_id=user_id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            await query.edit_message_text("Premium unlocked! 🔥 5 hot files for you 😈💦")
            return

        # Free logic
        if count >= 1:  # सिर्फ 1 click per day free में (5 files one time)
            if last_free_time:
                last_time = datetime.fromisoformat(last_free_time)
                time_diff = now - last_time
                if time_diff < timedelta(hours=24):
                    hours_left = 24 - int(time_diff.total_seconds() / 3600)
                    await query.edit_message_text(f"Free limit over for today! ⏳ Wait {hours_left} hours\nGo premium for unlimited 💎")
                    return

        # Free user को 5 random files one time
        media_ids = await get_channel_files(context, limit=100)
        if media_ids:
            selected = random.sample(media_ids, min(5, len(media_ids)))
            for msg_id in selected:
                await context.bot.forward_message(chat_id=user_id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
        else:
            await query.edit_message_text("No files in channel yet! Add some hot content 🔥")

        c.execute("UPDATE users SET daily_count=1, last_free_time=? WHERE user_id=?", (now.isoformat(), user_id))
        conn.commit()

        await query.edit_message_text("Free 5 hot files sent! 🔥\nCome back tomorrow or go premium for unlimited 💦")

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
            "• Free: 5 random files once per day\n"
            "• Premium: Unlimited anytime\n\n"
            "Admin: @Anjali_Sharma4u\n"
            "Issue? Message admin!"
        )
        await query.edit_message_text(response)

# Bot run
try:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot started! Auto picking from channel 🔥")
    app.run_polling(drop_pending_updates=True)
except Exception as e:
    print(f"ERROR: {e}")
