import random
import asyncio
import time
import traceback
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, GROUP_ID
from shivu import pm_users as collection 


START_TIME = time.time()


def get_uptime():
    uptime = int(time.time() - START_TIME)
    h, r = divmod(uptime, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"


# ------------------ ANIMATION ------------------ #
async def startup_animation(update: Update):
    msg = await update.message.reply_text("⚡ Initializing...")
    for text in ["⚡ Loading modules...", "💫 Connecting DB...", "🚀 Starting bot..."]:
        await asyncio.sleep(0.6)
        await msg.edit_text(text)
    await asyncio.sleep(0.5)
    await msg.delete()


# ------------------ START ------------------ #
async def start(update: Update, context: CallbackContext):

    try:
        start_time = time.time()

        user = update.effective_user
        chat = update.effective_chat

        user_id = user.id
        first_name = user.first_name
        username = user.username

        bot_name = context.bot.first_name
        chat_name = chat.title if chat.title else "Private Chat"

        # SAVE USER
        try:
            user_data = await collection.find_one({"_id": user_id})
            if not user_data:
                await collection.insert_one({
                    "_id": user_id,
                    "first_name": first_name,
                    "username": username
                })
        except:
            pass

        # PRIVATE
        if chat.type == "private":

            await startup_animation(update)

            ping = round((time.time() - start_time) * 1000, 2)
            uptime = get_uptime()

            caption = f"""
<blockquote>
🌸 <b>Hello {escape(first_name)}!</b>

🤖 <b>{bot_name}</b> is ready!

━━━━━━━━━━━━━━━
⚡ <b>Ping:</b> {ping} ms
🕒 <b>Uptime:</b> {uptime}
👤 <b>You:</b> {escape(first_name)}
━━━━━━━━━━━━━━━

💖 Catch • Trade • Collect Anime Characters!
</blockquote>
"""

            keyboard = [
                [InlineKeyboardButton("➕ Add Me", url=f"http://t.me/{BOT_USERNAME}?startgroup=true")],
                [
                    InlineKeyboardButton("👑 ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/YOUR_MADARA_BRO"),
                    InlineKeyboardButton("📚 Help", callback_data="help")
                ],
                [
                    InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}"),
                    InlineKeyboardButton("Updates", url=f"https://t.me/{UPDATE_CHAT}")
                ]
            ]

        # GROUP
        else:
            caption = f"""
🌟 <b>{bot_name}</b> is active in <b>{chat_name}</b>

━━━━━━━━━━━━━━━
💫 Spawn anime characters
🎮 Games • Leaderboards
🚀 Use /help to explore
━━━━━━━━━━━━━━━
"""

            keyboard = [
                [
                    InlineKeyboardButton("📚 Help", callback_data="help"),
                    InlineKeyboardButton("📊 Stats", callback_data="stats")
                ]
            ]

        photo_url = random.choice(PHOTO_URL)

        await context.bot.send_photo(
            chat_id=chat.id,
            photo=photo_url,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    except Exception:
        print(traceback.format_exc())


# ------------------ BUTTON ------------------ #
async def button(update: Update, context: CallbackContext):

    query = update.callback_query
    await query.answer()

    try:
        # HELP MENU
        if query.data == "help":

            text = """<b>📚 Help Menu</b>

These are the available commands for you
"""

            keyboard = [
                [
                    InlineKeyboardButton("🎮 Guess", callback_data="guess"),
                    InlineKeyboardButton("📚 Harem", callback_data="harem")
                ],
                [
                    InlineKeyboardButton("💖 Fav", callback_data="fav"),
                    InlineKeyboardButton("🔁 Trade", callback_data="trade")
                ],
                [
                    InlineKeyboardButton("🎁 Gift", callback_data="gift"),
                    InlineKeyboardButton("🏆 Leaderboard", callback_data="top")
                ],
                [
                    InlineKeyboardButton("⬅ Back", callback_data="home")
                ]
            ]

        # STATS
        elif query.data == "stats":

            uptime = get_uptime()

            text = f"""
<b>📊 Bot Stats</b>

⚡ Uptime: {uptime}
🤖 Bot: {context.bot.first_name}
"""

            keyboard = [[InlineKeyboardButton("⬅ Back", callback_data="home")]]

        # HOME
        elif query.data == "home":

            text = """
🌸 <b>Welcome Back!</b>

Use buttons below to explore 💖
"""

            keyboard = [
                [
                    InlineKeyboardButton("📊 Stats", callback_data="stats"),
                    InlineKeyboardButton("📚 Help", callback_data="help")
                ]
            ]

        # COMMAND BUTTON RESPONSES
        elif query.data == "guess":
            return await query.answer("Use /guess")

        elif query.data == "harem":
            return await query.answer("Use /harem")

        elif query.data == "fav":
            return await query.answer("Use /fav")

        elif query.data == "trade":
            return await query.answer("Use /trade")

        elif query.data == "gift":
            return await query.answer("Use /gift")

        elif query.data == "top":
            return await query.answer("Use /top")

        # EDIT MESSAGE
        await query.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    except Exception:
        print(traceback.format_exc())


# ------------------ HANDLERS ------------------ #
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
