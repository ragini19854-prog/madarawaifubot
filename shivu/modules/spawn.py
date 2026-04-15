import random
import asyncio
import time
import logging
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from shivu import application, collection
from shivu import db, user_collection

# Database setup
active_col = db["active_characters"]

last_characters = {}
first_correct_guesses = {}
user_guess_progress = {}

# Dictionary to remember last rarity
last_spawned_rarity = {}

# LOCK to prevent overlapping spawns in active groups (Fixes race condition)
spawn_locks = {}

# --- HELPER: AUTO DELETE ---
async def delete_message(context: CallbackContext, chat_id: int, message_id: int):
    await asyncio.sleep(300)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except Exception:
        pass

# --- RARITY CONFIGURATION ---
RARITY_CONFIG = {
    "⛩ Normal":        {"weight": 300, "enabled": True},
    "🏮 Standard":      {"weight": 250, "enabled": True},
    "🍀 Regular":       {"weight": 200, "enabled": True},
    "🔮 Mystic":        {"weight": 200, "enabled": True},
    "🎐 Eternal":       {"weight": 150, "enabled": True},
    "👑 Royal":         {"weight": 150, "enabled": True},
    "🔥 Infernal":      {"weight": 150, "enabled": True},
    "🎊 Astral":        {"weight": 90,  "enabled": True},
    "🏮 Classic":       {"weight": 70,  "enabled": True},
    "🎭 Mythic":        {"weight": 50,  "enabled": True},
    "🧧 Continental":   {"weight": 20,  "enabled": True},
    "🎈 Chunbiyo":      {"weight": 20,  "enabled": False},
}


# ==============================
#        SPAWN CHARACTER
# ==============================
async def spawn_character(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    # If a spawn is already processing for this group, block the new one
    if spawn_locks.get(chat_id):
        return
    spawn_locks[chat_id] = True

    try:
        prev_rarity = last_spawned_rarity.get(chat_id)

        # Step 1: Get all enabled rarities
        enabled_rarities = [r for r, cfg in RARITY_CONFIG.items() if cfg.get("enabled")]

        # Step 2: Remove previous rarity STRICTLY
        if prev_rarity in enabled_rarities:
            enabled_rarities.remove(prev_rarity)

        # Step 3: Safety fallback (agar galti se sab disable ho gaye aur 1 bacha)
        if not enabled_rarities:
            enabled_rarities = [r for r, cfg in RARITY_CONFIG.items() if cfg.get("enabled")]

        if not enabled_rarities:
            return

        selected_character = None
        
        # Keep trying until we find a rarity that actually has characters in the DB
        while enabled_rarities:
            # Step 4: Prepare weights for CURRENTLY enabled rarities
            weights = [RARITY_CONFIG[r]["weight"] for r in enabled_rarities]
            
            # Step 5: Pick rarity
            chosen_rarity = random.choices(enabled_rarities, weights=weights, k=1)[0]
            
            # Optimized DB Fetch: Get exactly 1 random character
            pipeline = [
                {"$match": {"rarity": chosen_rarity}},
                {"$sample": {"size": 1}}
            ]
            characters = await collection.aggregate(pipeline).to_list(length=1)
            
            if characters:
                selected_character = characters[0]
                # EXTREMELY IMPORTANT: Update immediately when found
                last_spawned_rarity[chat_id] = chosen_rarity 
                
                # Bonus Debug Tip: Print to console
                logging.info(f"Chat {chat_id} | Prev: {prev_rarity} -> New: {chosen_rarity}")
                break
            else:
                # Agar us rarity ka DB empty hai, usko list se nikalo aur wapas try karo
                enabled_rarities.remove(chosen_rarity)

        if not selected_character:
            logging.warning("no database found!")
            return

        selected = selected_character
        
        last_characters[chat_id] = selected
        last_characters[chat_id]["timestamp"] = time.time()
        last_characters[chat_id]["ranaway"] = False

        if chat_id in first_correct_guesses:
            del first_correct_guesses[chat_id]

        rarity_text = str(selected['rarity'])

        # Simple Hardcoded Spawn Message
        caption = (
            f"✨ <b>A {rarity_text} Character Appears!</b> ✨\n\n"
            f"🔍 Use <b>/guess</b> to claim this mysterious character!\n"
            f"💫 Hurry, before someone else snatches them!"
        )

        # --- UPDATED MEDIA SENDING LOGIC ---
        if selected.get("vid_url"):
            video_url = selected["vid_url"]
            try:
                # send_animation forces auto-play and fixes the static thumbnail issue
                msg = await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=video_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logging.warning(f"Animation failed for {video_url}, falling back to video: {e}")
                # Fallback to normal send_video just in case
                msg = await context.bot.send_video(
                    chat_id=chat_id,
                    video=video_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
        else:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=selected["img_url"],
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        # -----------------------------------

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
        # VERY IMPORTANT: Release the lock
        spawn_locks[chat_id] = False
          
