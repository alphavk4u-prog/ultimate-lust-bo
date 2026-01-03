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

# Private Channel Username (files यहाँ से आएंगे)
CHANNEL_USERNAME = "@UltimateLustFiles"  # तुम्हारा channel

# Free में भेजने वाले Message IDs (channel posts के IDs)
# Example में कुछ dummy IDs हैं – real IDs तुम डालो (नीचे बताया कैसे लो)
FREE_MESSAGE_IDS = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]  # यहाँ अपने real IDs डालो

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
        "The ultimate lust experience!\n"
        "Free: 5 clicks/day (2 random hot files)\n"
        "Premium: Unlimited + private group access 💦\n\n"
        "Choose your path:",
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

    if query.data == "free":
        if is_premium == 1:
            # Premium: Unlimited 2 files
            selected_ids = random.sample(FREE_MESSAGE_IDS, min(2, len(FREE_MESSAGE_IDS)))
            for msg_id in selected_ids:
                await context.bot.forward_message(chat_id=user_id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)
            await query.edit_message_text("Premium unlocked! 🔥 Unlimited hot files just for you 😈💦")
            return

        # Free limit logic
        if count >= 5:
            if last_free_time:
                last_time = datetime.fromisoformat(last_free_time)
                time_diff = now - last_time
                if time_diff < timedelta(minutes=30):
                    minutes_left = 30 - int(time_diff.total_seconds() / 60)
                    await query.edit_message_text(f"Free limit over! ⏳ Wait {minutes_left} minutes more...\nGo premium for instant unlimited 💎")
                    return
                else:
                    count = 0
                    c.execute("UPDATE users SET daily_count=? WHERE user_id=?", (count, user_id))
                    conn.commit()

        count += 1
        c.execute("UPDATE users SET daily_count=?, last_free_time=? WHERE user_id=?", (count, now.isoformat(), user_id))
        conn.commit()

        # Send 2 random files from channel
        selected_ids = random.sample(FREE_MESSAGE_IDS, min(2, len(FREE_MESSAGE_IDS)))
        for msg_id in selected_ids:
            await context.bot.forward_message(chat_id=user_id, from_chat_id=CHANNEL_USERNAME, message_id=msg_id)

        caption = f"Free #{count}/5 🔥\nEnjoy the tease... premium for full satisfaction 💦"
        await query.edit_message_text(caption)

    elif query.data == "premium":
        response = (
            "🔥 Ready for unlimited everything?\n\n"
            "💎 Premium Plans:\n"
            "• ₹99 → 1 Month Unlimited\n"
            "• ₹699 → Lifetime Unlimited 🔥\n\n"
            "📲 Pay via UPI:\n"
            "UPI ID: akashzyt@ybl\n"
            "Name: Vishal Kumar\n\n"
            "Payment करो → screenshot भेजो @Anjali_Sharma4u को\n"
            "मैं confirm करके private group link + unlimited unlock कर दूँगा 😈💦"
        )
        await query.edit_message_text(response)

    elif query.data == "help":
        response = (
            "❓ Help & Support\n\n"
            "• Free: 5 clicks/day (2 hot files per click)\n"
            "• After 5 clicks: 30 minute wait\n"
            "• Premium: Unlimited files + private group access\n\n"
            "Admin: @Anjali_Sharma4u\n"
            "Payment/issue? Message admin directly 😊\n\n"
            "Enjoy the lust! 🔥"
        )
        await query.edit_message_text(response)

# Bot run
try:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot started successfully! Channel files ready 🔥😈")
    app.run_polling(drop_pending_updates=True)
except Exception as e:
    print(f"FATAL ERROR: {e}")
    logging.error("Bot crashed", exc_info=True)
