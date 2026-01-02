from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime
import random
import os

# Database (Railway पर persistent storage के लिए /data folder use करेंगे)
if not os.path.exists('/data'):
    os.makedirs('/data')
conn = sqlite3.connect('/data/users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, daily_count INTEGER, last_reset TEXT, is_premium INTEGER DEFAULT 0)''')
conn.commit()

# Content list – और जितने चाहो add कर लो
free_content = [
    "🔥 Hot tip: Imagination is the key to ultimate pleasure 😈",
    "💦 Feel the heat rising? More fantasies await in premium...",
    "😏 You're teasing me already? Good boy/girl, let's play 🔥",
    "🌙 Midnight desires? Let me whisper secrets in your ear...",
    "💋 Lips locked in passion – want the full story?",
    "🖤 Your body is my favorite playground...",
    "😈 Tell me your darkest fantasy... premium unlocks everything 💦"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆓 Free Access", callback_data="free")],
        [InlineKeyboardButton("💎 Premium Unlimited", callback_data="premium")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to @UltimateLustBot 🔥😈\n\nThe ultimate lust experience!\nFree: 5 hot messages/day\nPremium: Unlimited + exclusive fantasies 💦\n\nChoose:",
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
    else:
        is_premium = 0
        count = 0
        c.execute("INSERT INTO users (user_id, daily_count, last_reset, is_premium) VALUES (?, ?, ?, ?)", (user_id, count, today, is_premium))
    conn.commit()

    c.execute("SELECT daily_count, is_premium FROM users WHERE user_id=?", (user_id,))
    count, is_premium = c.fetchone()

    if query.data == "free":
        if is_premium == 1:
            await query.edit_message_text("Premium unlocked! 🔥 Here's unlimited heat:\n" + random.choice(free_content))
        elif count < 5:
            count += 1
            c.execute("UPDATE users SET daily_count=? WHERE user_id=?", (count, user_id))
            conn.commit()
            await query.edit_message_text(f"Free #{count}/5 🔥:\n{random.choice(free_content)}\n\nWant more? Go premium! 💎")
        else:
            await query.edit_message_text("Free limit over for today 😏\nUpgrade to premium for unlimited lust!")

    elif query.data == "premium":
        await query.edit_message_text(
            "🔥 Ready for unlimited fantasies?\n\n"
            "Pay via UPI/Paytm/Razorpay:\n"
            "[अपना payment link यहाँ डाल दो]\n\n"
            "Payment के बाद screenshot भेजो @yourusername को unlock के लिए!"
        )

app = Application.builder().token("YOUR_TOKEN_HERE").build()  # अपना BOT_TOKEN डालो
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
print("Bot started successfully!")
app.run_polling()
