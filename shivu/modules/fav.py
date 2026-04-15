# shivu/modules/fav.py

from html import escape
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)

from shivu import application, user_collection, collection


# ==============================================================
#                    TINY CAPS HELPER
# ==============================================================

TINY_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
)

def tiny(text: str) -> str:
    return escape(str(text)).translate(TINY_MAP)


# ==============================================================
#                         /fav COMMAND
# ==============================================================

async def fav_command(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = update.effective_user.id

    if not context.args:  
        return await message.reply_html(f"❌ <b>{tiny('please provide a character id.')}</b>")  

    try:  
        char_id = int(context.args[0])  
    except ValueError:  
        return await message.reply_html(f"❌ <b>{tiny('invalid character id.')}</b>")  

    user_doc = await user_collection.find_one({"id": user_id})  
    if not user_doc or not user_doc.get("characters"):  
        return await message.reply_html(f"❌ <b>{tiny('you have no characters.')}</b>")  

    # ownership check  
    if not any(str(c.get("id")) == str(char_id) for c in user_doc["characters"]):  
        return await message.reply_html(  
            f"❌ <b>{tiny('this character is not in your collection.')}</b>"  
        )  

    character = await collection.find_one({"id": str(char_id)})  
    if not character:  
        return await message.reply_html(f"❌ <b>{tiny('character not found.')}</b>")  

    keyboard = InlineKeyboardMarkup(  
        [[  
            InlineKeyboardButton("✅ ʏᴇꜱ", callback_data=f"fav_yes:{char_id}:{user_id}"),  
            InlineKeyboardButton("❎ ɴᴏ", callback_data="fav_no")  
        ]]  
    )  

    caption = (  
        f"⭐ <b>{tiny('add to favorites')}</b>\n\n"  
        f"👤 <b>{tiny('name')}:</b> {tiny(character.get('name', 'unknown'))}\n"  
        f"🏖️ <b>{tiny('anime')}:</b> {tiny(character.get('anime', 'unknown'))}\n"  
        f"🔮 <b>{tiny('rarity')}:</b> {tiny(character.get('rarity', 'unknown'))}\n"  
        f"🆔 <code>{char_id}</code>"  
    )  

    if character.get("vid_url"):  
        return await message.reply_video(  
            video=character["vid_url"],  
            caption=caption,  
            parse_mode="HTML",  
            reply_markup=keyboard  
        )  

    if character.get("img_url"):  
        return await message.reply_photo(  
            photo=character["img_url"],  
            caption=caption,  
            parse_mode="HTML",  
            reply_markup=keyboard  
        )  

    return await message.reply_html(f"❌ <b>{tiny('no media available.')}</b>")


# ==============================================================
#                     FAV YES CALLBACK
# ==============================================================

async def fav_yes_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, char_id, owner_id = query.data.split(":")
    char_id = int(char_id)
    owner_id = int(owner_id)

    if query.from_user.id != owner_id:
        return await query.answer(tiny("not your menu!"), show_alert=True)

    # Store favorite as string ID
    await user_collection.update_one(
        {"id": owner_id},
        {"$set": {"favorites": [str(char_id)]}},
        upsert=True
    )

    character = await collection.find_one({"id": str(char_id)})

    if not character:
        return await query.edit_message_caption(
            f"❌ <b>{tiny('character not found')}</b>",
            parse_mode="HTML"
        )

    await query.edit_message_caption(
        f"⭐ <b>{tiny(character.get('name', 'unknown'))}</b>\n"
        f"<b>{tiny('is now your favorite')}</b>",
        parse_mode="HTML"
    )


# ==============================================================
#                     FAV NO CALLBACK
# ==============================================================

async def fav_no_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer(tiny("cancelled ❎"))
    await query.message.delete()


# ==============================================================
#                        /unfav COMMAND
# ==============================================================

async def unfav_command(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = update.effective_user.id

    user_doc = await user_collection.find_one({"id": user_id})
    
    # Check if user has any favorites set
    if not user_doc or not user_doc.get("favorites"):
        return await message.reply_html(f"❌ <b>{tiny('you currently do not have a favorite character.')}</b>")

    fav_list = user_doc.get("favorites")
    if len(fav_list) == 0:
        return await message.reply_html(f"❌ <b>{tiny('you currently do not have a favorite character.')}</b>")

    # Assuming a single favorite based on previous logic
    char_id = fav_list[0]
    
    character = await collection.find_one({"id": str(char_id)})
    if not character:
        # If character no longer exists in DB, clean up the favorite anyway
        await user_collection.update_one({"id": user_id}, {"$set": {"favorites": []}})
        return await message.reply_html(f"❌ <b>{tiny('favorite character not found in database. cleared.')}</b>")

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ ʏᴇꜱ", callback_data=f"unfav_yes:{user_id}"),
            InlineKeyboardButton("❎ ɴᴏ", callback_data="unfav_no")
        ]]
    )

    caption = (
        f"💔 <b>{tiny('remove from favorites')}</b>\n\n"
        f"👤 <b>{tiny('name')}:</b> {tiny(character.get('name', 'unknown'))}\n"
        f"🏖️ <b>{tiny('anime')}:</b> {tiny(character.get('anime', 'unknown'))}\n"
        f"🆔 <code>{char_id}</code>\n\n"
        f"<b>{tiny('are you sure you want to remove this character from favorites?')}</b>"
    )

    if character.get("vid_url"):
        return await message.reply_video(
            video=character["vid_url"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    if character.get("img_url"):
        return await message.reply_photo(
            photo=character["img_url"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    return await message.reply_html(f"❌ <b>{tiny('no media available.')}</b>")


# ==============================================================
#                     UNFAV YES CALLBACK
# ==============================================================

async def unfav_yes_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, owner_id = query.data.split(":")
    owner_id = int(owner_id)

    if query.from_user.id != owner_id:
        return await query.answer(tiny("not your menu!"), show_alert=True)

    # Clear the favorites array
    await user_collection.update_one(
        {"id": owner_id},
        {"$set": {"favorites": []}}
    )

    await query.edit_message_caption(
        f"💔 <b>{tiny('character has been removed from your favorites.')}</b>",
        parse_mode="HTML"
    )


# ==============================================================
#                     UNFAV NO CALLBACK
# ==============================================================

async def unfav_no_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer(tiny("cancelled ❎"))
    await query.message.delete()


# ==============================================================
#                        HANDLERS
# ==============================================================

application.add_handler(CommandHandler("fav", fav_command))
application.add_handler(CallbackQueryHandler(fav_yes_callback, pattern=r"^fav_yes:"))
application.add_handler(CallbackQueryHandler(fav_no_callback, pattern=r"^fav_no$"))

application.add_handler(CommandHandler("unfav", unfav_command))
application.add_handler(CallbackQueryHandler(unfav_yes_callback, pattern=r"^unfav_yes:"))
application.add_handler(CallbackQueryHandler(unfav_no_callback, pattern=r"^unfav_no$"))
