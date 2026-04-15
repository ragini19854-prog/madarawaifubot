import random
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection 

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        
        await context.bot.send_message(
            chat_id=GROUP_ID, 
            text=f"🆕 <b>New User Started The Bot!</b>\n👤 <b>User:</b> <a href='tg://user?id={user_id}'>{escape(first_name)}</a>", 
            parse_mode=ParseMode.HTML
        )
    else:
        if user_data.get('first_name') != first_name or user_data.get('username') != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    # --- PRIVATE CHAT START MESSAGE ---
    if update.effective_chat.type == "private":
        caption = (
            f"<b>✨ Welcome to the Character Catcher Bot! ✨</b>\n\n"
            f"I am a bot designed to drop random anime characters in your group! "
            f"Just add me to your group, and I'll start spawning characters for you to catch.\n\n"
            f"🎯 Use <code>/guess</code> to claim characters!\n"
            f"📚 Use <code>/harem</code> to view your amazing collection!\n"
            f"⚔️ Trade, gift, and compete in the global leaderboards!\n\n"
            f"<i>Add me to your group and start building your harem today! 🚀</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("💬 SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)

        await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=photo_url, 
            caption=caption, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.HTML
        )

    # --- GROUP CHAT START MESSAGE ---
    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("💬 SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=photo_url, 
            caption="<b>✨ I am alive and working perfectly! ✨</b>\n\nStart me in Private Chat for more information and commands.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = (
            "<b>📚 Help & Commands Menu:</b>\n\n"
            "🎮 <b>Core Commands:</b>\n"
            "• <code>/guess</code> - Catch a spawned character.\n"
            "• <code>/harem</code> - View your character collection.\n"
            "• <code>/fav</code> - Set your favorite character.\n\n"
            "♻️ <b>Economy & Trade:</b>\n"
            "• <code>/trade</code> - Trade characters with others.\n"
            "• <code>/gift</code> - Give a character to another user.\n\n"
            "🏆 <b>Leaderboards:</b>\n"
            "• <code>/top</code> - Top users globally.\n"
            "• <code>/topgroups</code> - Most active groups.\n"
            "• <code>/ctop</code> - Top users in the current chat.\n\n"
            "⚙️ <b>Settings:</b>\n"
            "• <code>/changetime</code> - Change spawn frequency."
        )
        help_keyboard = [[InlineKeyboardButton("⬅️ BACK", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)
        
        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id, 
            message_id=query.message.message_id, 
            caption=help_text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.HTML
        )

    elif query.data == 'back':
        caption = (
            f"<b>✨ Welcome to the Character Catcher Bot! ✨</b>\n\n"
            f"I am a bot designed to drop random anime characters in your group! "
            f"Just add me to your group, and I'll start spawning characters for you to catch.\n\n"
            f"🎯 Use <code>/guess</code> to claim characters!\n"
            f"📚 Use <code>/harem</code> to view your amazing collection!\n"
            f"⚔️ Trade, gift, and compete in the global leaderboards!\n\n"
            f"<i>Add me to your group and start building your harem today! 🚀</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("💬 SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📢 UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("❓ HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id, 
            message_id=query.message.message_id, 
            caption=caption, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.HTML
        )

# Handlers Registration
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
application.add_handler(CommandHandler('start', start, block=False))
