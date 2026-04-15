import re
from cachetools import TTLCache
from shivu import user_collection, collection

# ======================================================
# CACHES
# ======================================================
all_characters_cache = TTLCache(maxsize=10000, ttl=300)   # 5 minutes
user_collection_cache = TTLCache(maxsize=10000, ttl=30)   # 30 seconds


# ======================================================
# GET USER COLLECTION
# ======================================================
async def get_user_collection(user_id: str):
    user_id = str(user_id)

    if user_id in user_collection_cache:
        return user_collection_cache[user_id]

    user = await user_collection.find_one({"id": int(user_id)})
    if user:
        user_collection_cache[user_id] = user

    return user


# ======================================================
# SEARCH CHARACTERS (GLOBAL)
# ======================================================
async def search_characters(query: str, force_refresh: bool = False):

    key = f"search_{query.lower()}"

    if not force_refresh and key in all_characters_cache:
        return all_characters_cache[key]

    regex = re.compile(query, re.IGNORECASE)

    characters = await collection.find({
        "$or": [
            {"name": regex},
            {"anime": regex},
            {"aliases": regex}
        ]
    }).to_list(length=None)

    all_characters_cache[key] = characters
    return characters


# ======================================================
# GET ALL CHARACTERS
# ======================================================
async def get_all_characters(force_refresh: bool = False):

    if not force_refresh and "all" in all_characters_cache:
        return all_characters_cache["all"]

    characters = await collection.find({}).to_list(length=None)
    all_characters_cache["all"] = characters

    return characters


# ======================================================
# FORCE REFRESH (ADMIN)
# ======================================================
async def refresh_character_caches():
    all_characters_cache.clear()
    user_collection_cache.clear()
