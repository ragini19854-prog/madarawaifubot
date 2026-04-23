import time
import datetime
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from shivu import application

START_TIME = time.time()


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()

    msg = await update.message.reply_text("🏓 Pinging...")

    end = time.time()
    ping_ms = round((end - start) * 1000, 2)

    # uptime
    uptime_sec = int(time.time() - START_TIME)
    uptime = str(datetime.timedelta(seconds=uptime_sec))

    # dynamic values
    user_name = update.effective_user.first_name
    bot_name = context.bot.first_name
    chat_name = update.effective_chat.title or "Private Chat"

    await msg.edit_text(
        f"""
╭━〔 {bot_name} 〕━⬣
┃ 🏓 **PING STATUS**
┃ ⚡ Speed: `{ping_ms} ms`
┃ 🕒 Uptime: `{uptime}`
┃ 👤 User: **{user_name}**
╰━━━━━━━━━━━━━━━⬣

❝ ❤️ Powered By: **madara** ❞  
❝ 💬 Chat: **{chat_name}** ❞
"""
    )


application.add_handler(CommandHandler("ping", ping))
