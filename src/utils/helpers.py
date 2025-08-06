from functools import wraps
from time import time
from pyrogram.types import Message, InputMediaPhoto
from pyrogram.errors import UserIsBlocked, PeerIdInvalid, ChatWriteForbidden

# Cache DM availability for 10 minutes
dm_cache = {}

async def can_send_dm(client, user_id):
    """Check if bot can message a user with caching"""
    if user_id in dm_cache and dm_cache[user_id]['expiry'] > time():
        return dm_cache[user_id]['result']

    try:
        msg = await client.send_message(user_id, "⌛", disable_notification=True)
        await msg.delete()
        result = True
        dm_cache[user_id] = {'result': True, 'expiry': time() + 600}
    except (UserIsBlocked, PeerIdInvalid, ChatWriteForbidden):
        result = False
    except Exception:
        result = False

    return result

def format_player_list(players):
    """Format player list with numbering"""
    if not players:
        return "No players yet"
    return "\n".join(f"{i+1}. {p['name']}" for i, p in enumerate(players))

def game_required(active=True):
    """Decorator factory to check game status"""
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update):
            user_id = update.from_user.id
            message = update if isinstance(update, Message) else update.message

            game = game_manager.get_game_by_player(user_id)
            if not game:
                await message.reply("❌ You're not in any active game!")
                return

            if active and not game.started:
                await message.reply("⌛ Game hasn't started yet!")
                return
            elif not active and game.started:
                await message.reply("🚫 Game has already started!")
                return

            return await func(client, update, game)
        return wrapper
    return decorator

async def cleanup_game_messages(client, game):
    """Comprehensive game cleanup without media"""
    caption = "🎉 Game Over! Thanks for playing."

    for player in game.players:
        try:
            await client.send_message(player['id'], caption)
        except Exception:
            pass

def rate_limit(seconds=2):
    """Prevent command spamming"""
    def decorator(func):
        last_called = {}

        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            user_id = message.from_user.id
            now = time()

            if user_id in last_called and (now - last_called[user_id]) < seconds:
                await message.reply(f"⚠️ Please wait {seconds} seconds between commands")
                return

            last_called[user_id] = now
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator

async def is_admin(client, chat_id, user_id):
    """Check if user has admin privileges"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ('administrator', 'creator')
    except Exception:
        return False