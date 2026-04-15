from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from shivu import application, user_collection


# =============================
#   TEMP STORAGE FOR CONFIRM
# =============================
pending_gifts = {}   # sender_id : { character, receiver_id, receiver_info }


# ==============================================================
#                /gift  (Start gifting)
# ==============================================================

async def gift_command(update: Update, context: CallbackContext):

    msg = update.message
    sender_id = msg.from_user.id

    # Must reply to someone
    if not msg.reply_to_message:
        return await msg.reply_html("<b>Reply to a user's message to gift a waifu/slave!</b>")

    receiver = msg.reply_to_message.from_user
    receiver_id = receiver.id

    # Cannot gift yourself
    if receiver_id == sender_id:
        return await msg.reply_html("<b>You cannot gift to yourself.</b>")

    # Must include character ID
    parts = msg.text.split()
    if len(parts) != 2:
        return await msg.reply_html("Usage:\n<code>/gift &lt;character_id&gt;</code>")

    character_id = parts[1]

    # Check sender data
    sender = await user_collection.find_one({"id": sender_id}) or {}

    characters = sender.get("characters", [])

    # Find the character
    character = next((c for c in characters if isinstance(c, dict) and c.get("id") == character_id), None)

    if not character:
        return await msg.reply_text("❌ You don't have this character.")

    # If already waiting for confirmation
    if sender_id in pending_gifts:
        return await msg.reply_html("<b>You already have a pending gift confirmation!</b>")

    # Save pending gift
    pending_gifts[sender_id] = {
        "character": character,
        "receiver_id": receiver_id,
        "receiver_username": receiver.username,
        "receiver_first_name": receiver.first_name
    }

    cap = (
        f"<b>Gift Confirmation</b>\n\n"
        f"Do you really want to gift this character to <b>{receiver.first_name}</b>?\n\n"
        f"🔹 <b>Name:</b> {character['name']}\n"
        f"🔹 <b>ID:</b> {character['id']}\n"
        f"🔹 <b>Rarity:</b> {character['rarity']}"
    )

    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="gift_yes")],
        [InlineKeyboardButton("❌ Cancel", callback_data="gift_no")]
    ])

    await msg.reply_html(cap, reply_markup=btns)


# ==============================================================
#                CALLBACK HANDLER
# ==============================================================
async def gift_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    sender_id = query.from_user.id

    if sender_id not in pending_gifts:
        return await query.answer("No pending gift found!", show_alert=True)

    data = query.data
    gift = pending_gifts[sender_id]
    receiver_id = gift["receiver_id"]
    character = gift["character"]

    if data == "gift_no":
        del pending_gifts[sender_id]
        return await query.edit_message_text("❌ Gifting canceled.")

    # ============================
    #          CONFIRM
    # ============================
    if data == "gift_yes":
        # --- FETCH USERS ---
        sender = await user_collection.find_one({"id": sender_id}) or {}
        receiver = await user_collection.find_one({"id": receiver_id})

        # --- REMOVE CHARACTER FROM SENDER ---
        sender_chars = sender.get("characters", [])
        sender_chars = [c for c in sender_chars if c.get("id") != character["id"]]

        await user_collection.update_one(
            {"id": sender_id},
            {"$set": {"characters": sender_chars}},
            upsert=True
        )

        # --- ADD CHARACTER TO RECEIVER ---
        if not receiver:
            # Create new receiver document if doesn't exist
            await user_collection.insert_one({
                "id": receiver_id,
                "first_name": gift["receiver_first_name"],
                "username": gift.get("receiver_username", ""),
                "characters": [character],
                "balance": 0
            })
        else:
            # Receiver exists, push character
            await user_collection.update_one(
                {"id": receiver_id},
                {"$push": {"characters": character}}
            )

        # --- CLEAR PENDING ---
        del pending_gifts[sender_id]

        await query.edit_message_text(
            f"🎁 Successfully gifted <b>{character['name']}</b> to <b>{gift['receiver_first_name']}</b>!",
            parse_mode="HTML"
        )



# ==============================================================
#                  REGISTER HANDLERS
# ==============================================================

application.add_handler(CommandHandler("gift", gift_command))
application.add_handler(CallbackQueryHandler(gift_callback, pattern="^(gift_yes|gift_no)$"))
