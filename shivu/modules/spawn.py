import random
import asyncio
import time
import logging
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters

from shivu import application, collection, db, user_collection

# ==============================
# DATABASE
# ==============================
active_col = db["active_characters"]
spawn_settings_col = db["spawn_settings"]

# ==============================
# GLOBALS
# ==============================
last_characters = {}
first_correct_guesses = {}
user_guess_progress = {}
last_spawned_rarity = {}
spawn_locks = {}

# message tracking
message_count = {}
last_spawn_time = {}

COOLDOWN = 60  # seconds


# ==============================
# AUTO DELETE
# ==============================
async def delete_message(context: CallbackContext, chat_id: int, message_id: int):
    await asyncio.sleep(300)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except:
        pass


# ==============================
# RARITY CONFIG
# ==============================
RARITY_CONFIG = {
    "⛩ Normal": {"weight": 300, "enabled": True},
    "🏮 Standard": {"weight": 250, "enabled": True},
    "🍀 Regular": {"weight": 200, "enabled": True},
    "🔮 Mystic": {"weight": 200, "enabled": True},
    "🎐 Eternal": {"weight": 150, "enabled": True},
    "👑 Royal": {"weight": 150, "enabled": True},
    "🔥 Infernal": {"weight": 150, "enabled": True},
    "🎊 Astral": {"weight": 90, "enabled": True},
    "🏮 Classic": {"weight": 70, "enabled": True},
    "🎭 Mythic": {"weight": 50, "enabled": True},
    "🧧 Continental": {"weight": 20, "enabled": True},
}


# ==============================
# SPAWN CHARACTER (UNCHANGED CORE)
# ==============================
async def spawn_character(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if spawn_locks.get(chat_id):
        return
    spawn_locks[chat_id] = True

    try:
        prev_rarity = last_spawned_rarity.get(chat_id)

        enabled_rarities = [r for r, cfg in RARITY_CONFIG.items() if cfg.get("enabled")]

        if prev_rarity in enabled_rarities:
            enabled_rarities.remove(prev_rarity)

        if not enabled_rarities:
            return

        selected_character = None

        while enabled_rarities:
            weights = [RARITY_CONFIG[r]["weight"] for r in enabled_rarities]
            chosen_rarity = random.choices(enabled_rarities, weights=weights, k=1)[0]

            pipeline = [
                {"$match": {"rarity": chosen_rarity}},
                {"$sample": {"size": 1}}
            ]

            characters = await collection.aggregate(pipeline).to_list(length=1)

            if characters:
                selected_character = characters[0]
                last_spawned_rarity[chat_id] = chosen_rarity
                break
            else:
                enabled_rarities.remove(chosen_rarity)

        if not selected_character:
            return

        selected = selected_character

        last_characters[chat_id] = selected
        last_characters[chat_id]["timestamp"] = time.time()
        last_characters[chat_id]["ranaway"] = False

        caption = (
            f"✨ <b>A {selected['rarity']} Character Appears!</b> ✨\n\n"
            f"🔍 Use <b>/guess</b> to claim this character!"
        )

        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=selected["img_url"],
            caption=caption,
            parse_mode=ParseMode.HTML
        )

        await active_col.update_one(
            {"chat_id": chat_id},
            {"$set": {
                "chat_id": chat_id,
                "message_id": msg.message_id,
                "id": selected["id"],
                "spawned_at": datetime.utcnow()
            }},
            upsert=True
        )

        asyncio.create_task(delete_message(context, chat_id, msg.message_id))

    except Exception as e:
        logging.error(f"Spawn Error: {e}")
    finally:
        spawn_locks[chat_id] = False


# ==============================
# MESSAGE TRACKER (AUTO SPAWN)
# ==============================
async def message_tracker(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if update.effective_chat.type == "private":
        return

    settings = await spawn_settings_col.find_one({"chat_id": chat_id})
    if not settings:
        return

    spawn_limit = settings.get("count", 50)

    now = time.time()
    last_time = last_spawn_time.get(chat_id, 0)

    if now - last_time < COOLDOWN:
        return

    message_count[chat_id] = message_count.get(chat_id, 0) + 1

    if message_count[chat_id] >= spawn_limit:
        message_count[chat_id] = 0
        last_spawn_time[chat_id] = now
        await spawn_character(update, context)


# ==============================
# SET SPAWN COMMAND
# ==============================
async def set_spawn(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if not context.args:
        return await update.message.reply_text("Usage: /setspawn 50")

    try:
        count = int(context.args[0])

        if count < 5:
            return await update.message.reply_text("Minimum is 5")

        await spawn_settings_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"count": count}},
            upsert=True
        )

        await update.message.reply_text(f"✅ Spawn every {count} messages")

    except:
        await update.message.reply_text("Invalid number")


# ==============================
# DISABLE SPAWN
# ==============================
async def disable_spawn(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    await spawn_settings_col.delete_one({"chat_id": chat_id})
    await update.message.reply_text("❌ Spawn disabled")


# ==============================
# HANDLERS
# ==============================
application.add_handler(CommandHandler("setspawn", set_spawn))
application.add_handler(CommandHandler("disablespawn", disable_spawn))

application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_tracker)
)
