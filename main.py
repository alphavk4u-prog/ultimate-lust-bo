import os
import sqlite3
import logging
from datetime import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("=== BOT STARTING ===")
print("Loading libraries... Done")

token = os.getenv("TOKEN")
if not token:
    print("ERROR: No TOKEN found!")
    exit(1)
print(f"Token loaded: {token[:10]}...{token[-5:]}")

# Database path change – Render में /tmp folder use करो (write permission है)
db_path = '/tmp/users.db'  # /data की जगह /tmp use करो
conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, daily_count INTEGER, last_reset TEXT, is_premium INTEGER DEFAULT 0)''')
conn.commit()
print("Database ready at /tmp/users.db")

free_content = [
    "🔥 Hot tip: Imagination is the key to ultimate pleasure 😈",
    "💦 Feel the heat rising? More fantasies await in premium...",
    "😏 You're teasing me already? Good boy/girl, let's play 🔥",
    "🌙 Midnight desires? Let me whisper secrets in your ear...",
    "💋 Lips locked in passion – want the full story?",
    "🖤 Your body is my favorite playground...",
    "😈 Tell me your darkest fantasy... premium unlocks everything 💦",
    "🔥 Ready to lose control? Only premium can handle that heat..."
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆓 Free Access", callback_data="free")],
        [InlineKeyboardButton("💎 Premium Unlimited", callback_data="premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to @UltimateLust_Bot 🔥😈\n\n"
        "The ultimate lust experience!\n"
        "Free: 5 hot messages/day\n"
        "Premium: Unlimited + exclusive fantasies 💦\n\n"
        "Choose your path:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    today = datetime.now().date().isoformat()

    c.execute("SELECT daily_count, last_reset, is_premium FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if row:
        count, last_reset, is_premium = row
        if last_reset != today:
            count = 0
            c.execute("UPDATE users SET daily_count=?, last_reset=? WHERE user_id=?", (count, today, user_id))
            conn.commit()
    else:
        is_premium = 0
        count = 0
        c.execute("INSERT INTO users (user_id, daily_count, last_reset, is_premium) VALUES (?, ?, ?, ?)", 
                  (user_id, count, today, is_premium))
        conn.commit()

    c.execute("SELECT daily_count, is_premium FROM users WHERE user_id=?", (user_id,))
    count, is_premium = c.fetchone()

    if query.data == "free":
        if is_premium == 1:
            response = "Premium unlocked! 🔥 Here's unlimited heat:\n" + random.choice(free_content)
        elif count < 5:
            count += 1
            c.execute("UPDATE users SET daily_count=? WHERE user_id=?", (count, user_id))
            conn.commit()
            response = f"Free #{count}/5 🔥:\n{random.choice(free_content)}\n\nWant more? Go premium! 💎"
        else:
            response = "Free limit over for today 😏\nUpgrade to premium for unlimited lust!"
        await query.edit_message_text(response)

    elif query.data == "premium":
        response = (
            "🔥 Ready for unlimited fantasies?\n\n"
            "Pay via UPI/Paytm/Razorpay:\n"
            "[अपना payment link यहाँ डाल दो]\n\n"
            "Payment के बाद screenshot भेजो @yourusername को unlock के लिए!"
        )
        await query.edit_message_text(response)

app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot handlers added")
print("Bot starting polling...")
print("Bot started successfully! @UltimateLust_Bot is LIVE 🔥😈")

app.run_polling(drop_pending_updates=True)
