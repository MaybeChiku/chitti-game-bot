from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
from typing import Dict, Set
from src import app
from src.utils import game_manager

# Track votes to end games
game_end_votes: Dict[int, Set[int]] = {}  # {chat_id: {user_ids}}

async def is_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        chat_member = await client.get_chat_member(chat_id, user_id)
        return chat_member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
    except Exception:
        return False

async def update_vote_message(client, chat_id: int, message_id: int):
    if chat_id not in game_end_votes:
        return

    current_votes = len(game_end_votes[chat_id])
    votes_needed = max(3 - current_votes, 0)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=f"🗳️ Vote to End ({current_votes}/3)",
            callback_data="vote_end_game"
        )]
    ])

    try:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=(
                f"🎮 End Game Voting\n\n"
                f"Current votes: {current_votes}/3\n"
                f"{votes_needed} more votes needed to end the game."
            ),
            reply_markup=keyboard
        )
    except Exception:
        pass

@app.on_message(filters.command("stop") & filters.group)
async def end_game_command(client, message):
    game = game_manager.get_game(message.chat.id)
    if not game:
        return await message.reply("Cannot end no active game found!")

    user_id = message.from_user.id

    # Case 1: User is the game host
    if user_id == game.host:
        game_manager.end_game(message.chat.id)
        if message.chat.id in game_end_votes:
            del game_end_votes[message.chat.id]
        return await message.reply("🎮 Game ended by host!")

    # Case 2: User is a group admin
    if await is_admin(client, message.chat.id, user_id):
        game_manager.end_game(message.chat.id)
        if message.chat.id in game_end_votes:
            del game_end_votes[message.chat.id]
        return await message.reply("🎮 Game ended by admin!")

    # Case 3: Regular user voting to end
    chat_id = message.chat.id

    # Initialize vote tracking if needed
    if chat_id not in game_end_votes:
        game_end_votes[chat_id] = set()

    # Create/update vote message
    current_votes = len(game_end_votes[chat_id])
    votes_needed = max(3 - current_votes, 0)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=f"🗳️ Vote to End ({current_votes}/3)",
            callback_data="vote_end_game"
        )]
    ])

    vote_msg = await message.reply(
        f"🎮 End Game Voting\n\n"
        f"Current votes: {current_votes}/3\n"
        f"{votes_needed} more votes needed to end the game.",
        reply_markup=keyboard
    )

    # Store message ID for updates
    if not hasattr(game, 'vote_message_id'):
        game.vote_message_id = vote_msg.id

@app.on_callback_query(filters.regex("^vote_end_game$"))
async def vote_end_game_callback(client, callback_query):
    game = game_manager.get_game(callback_query.message.chat.id)
    if not game:
        await callback_query.answer("No active game to end!", show_alert=False)
        return

    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    # Host and admins can't vote (they can directly end)
    if user_id == game.host or await is_admin(client, chat_id, user_id):
        await callback_query.answer("You can end the game directly with /stop", show_alert=False)
        return

    # Initialize vote tracking if needed
    if chat_id not in game_end_votes:
        game_end_votes[chat_id] = set()

    # Toggle vote
    if user_id in game_end_votes[chat_id]:
        game_end_votes[chat_id].remove(user_id)
        await callback_query.answer("Your vote has been removed!", show_alert=False)
    else:
        game_end_votes[chat_id].add(user_id)
        await callback_query.answer(" You voted to end the game!", show_alert=False)

    # Update vote message
    await update_vote_message(client, chat_id, callback_query.message.id)

    # Check if enough votes reached
    if len(game_end_votes.get(chat_id, set())) >= 3:
        game_manager.end_game(chat_id)
        if chat_id in game_end_votes:
            del game_end_votes[chat_id]

        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.id,
                text="🎮 Game ended by majority vote!"
            )
        except Exception:
            pass