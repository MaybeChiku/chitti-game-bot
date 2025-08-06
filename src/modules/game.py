from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src import app
from src.utils import (
    game_manager,
    can_send_dm,
    format_player_list,
    cleanup_game_messages
)

async def disable_expired_buttons(client, game):
    """Disable all buttons from the ended game"""
    for message_id, chat_id in game.active_button_messages:
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="🎮 Game session ended. Buttons disabled.",
                reply_markup=None
            )
        except Exception:
            pass
    game.clear_button_messages()

async def handle_blocked_player(client, game, player_id):
    player = next((p for p in game.players if p['id'] == player_id), None)
    if not player:
        return

    card, next_player_id = game.get_random_card(player_id)
    next_player = next((p for p in game.players if p['id'] == next_player_id), None)
    if not card or not next_player:
        return

    # Get user objects for mentions
    try:
        blocked_user = await client.get_users(player_id)
        next_user = await client.get_users(next_player_id)

        await client.send_message(
            game.chat_id,
            f"⚠️ {blocked_user.mention} couldn't be reached. Auto-passed card to {next_user.mention}"
        )
    except Exception:
        await client.send_message(
            game.chat_id,
            f"⚠️ {player['name']} couldn't be reached. Auto-passed card to {next_player['name']}"
        )

    current_player = game.get_current_player()
    if current_player:
        buttons = game.get_card_buttons(current_player['id'])
        if buttons:
            try:
                msg = await client.send_message(
                    current_player['id'],
                    f"You received {card} from {player['name']}. Choose a card to pass:",
                    reply_markup=buttons
                )
                game.add_button_message(msg.id, msg.chat.id)
            except:
                await handle_blocked_player(client, game, current_player['id'])

@app.on_message(filters.command("game"))
async def new_game(client, message):
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply("Please use this command in a group chat.")

    if game_manager.get_game(message.chat.id):
        return await message.reply("⚠️ A game is already in progress!")

    # Check if user is already in another group's game
    existing_chat = game_manager.get_player_active_chat(message.from_user.id)
    if existing_chat and existing_chat != message.chat.id:
        return await message.reply("⚠️ You're already playing in another group! Finish that game first.")

    game = game_manager.create_game(host_id=message.from_user.id, chat_id=message.chat.id)
    if not game:
        return await message.reply("⚠️ You're already playing in another group! Finish that game first.")

    await message.reply(
        f"🎮 New game created by {message.from_user.mention}! (Game ID: {game.game_hash})\n"
        "Players can join with /join\n"
        "Game requires 4–8 players.\n"
        "Host can use /begin to start."
    )

@app.on_message(filters.command("join"))
async def join_game(client, message):
    game = game_manager.get_game(message.chat.id)
    if not game:
        return await message.reply("⚠️ No game found in this group.")
    if game.started:
        return await message.reply("Game already started!")
    if len(game.players) >= 8:
        return await message.reply("⚠️ Game is full! (Max 8 players)")

    success, msg = game_manager.add_player(message.chat.id, message.from_user.id, message.from_user.first_name)
    if success:
        player_list = format_player_list(game.players)
        await message.reply(
            f"🎮 {message.from_user.mention} joined!\n👥 Players: {len(game.players)}/8 joined (need minimum 4)"
        )
    else:
        await message.reply(f"⚠️ {msg}")

@app.on_message(filters.command("begin"))
async def begin_game(client, message):
    game = game_manager.get_game(message.chat.id)
    if not game:
        return await message.reply("⚠️ No game found in this group.")
    if message.from_user.id != game.host:
        return await message.reply("🔒 Only the host can start the game.")
    if game.started:
        return await message.reply("⚠️ Game already running.")
    if len(game.players) < 4:
        return await message.reply("👥 Need at least 4 players to start!")

    # Get user objects for mentions in unavailable players list
    unavailable_users = []
    for p in game.players:
        if not await can_send_dm(client, p['id']):
            try:
                user = await client.get_users(p['id'])
                unavailable_users.append(user.mention)
            except:
                unavailable_users.append(p['name'])

    if unavailable_users:
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Bot", url=f"https://t.me/{client.me.username}?start=start")]
        ])
        return await message.reply(
            "⚠️ The following players need to start the bot:\n\n" +
            "\n".join(f"• {n}" for n in unavailable_users),
            reply_markup=btn
        )

    game.start_game()
    await message.reply(f"🎮 Game started! Check your DMs for your cards.")

    first_player = game.get_current_player()
    if first_player:
        # Get user object for mention
        try:
            first_user = await client.get_users(first_player['id'])
            await client.send_message(
                game.chat_id,
                f"🎮 {first_user.mention}'s turn! Choose a card to pass."
            )
        except:
            await client.send_message(
                game.chat_id,
                f"🎮 {first_player['name']}'s turn! Choose a card to pass."
            )

        buttons = game.get_card_buttons(first_player['id'])
        if buttons:
            try:
                msg = await client.send_message(
                    first_player['id'],
                    f"🎮You're first! Select a card to pass",
                    reply_markup=buttons
                )
                game.add_button_message(msg.id, msg.chat.id)
            except:
                await handle_blocked_player(client, game, first_player['id'])

    # Inform others of their upcoming turns with mentions
    for p in game.players:
        if p['id'] != first_player['id']:
            before_names = []
            for pl in game.players:
                if (pl['id'] in game.turn_order[:game.turn_order.index(p['id'])] and 
                    pl['id'] not in game.locked_players):
                    try:
                        user = await client.get_users(pl['id'])
                        before_names.append(user.mention)
                    except:
                        before_names.append(pl['name'])

            if before_names:
                await client.send_message(p['id'], f"⏳ Your turn comes after: {', '.join(before_names)}")

@app.on_callback_query(filters.regex(r"^pass_(\d+)_([a-f0-9]{8})$"))
async def handle_card_selection(client, callback_query):
    user_id = callback_query.from_user.id

    # Extract card index and game hash from callback data
    try:
        card_index = int(callback_query.matches[0].group(1))
        provided_hash = callback_query.matches[0].group(2)
    except (IndexError, ValueError):
        await callback_query.answer("❌ Invalid button data!", show_alert=True)
        return

    game = game_manager.get_game_by_player(user_id)

    if not game or not game.started:
        await callback_query.answer("⌛ Game session not found.", show_alert=False)
        return

    # Validate game hash
    if not game.is_valid_hash(provided_hash):
        await callback_query.answer("❌ This button is from an old game session!", show_alert=False)
        try:
            await callback_query.message.edit_text(
                "🚫 This button is from a previous game session and is no longer valid.",
                reply_markup=None
            )
        except:
            pass
        return

    try:
        card, next_player_id = game.pass_card(user_id, card_index)
    except ValueError as e:
        await callback_query.answer(str(e), show_alert=True)
        return

    next_player = next((p for p in game.players if p['id'] == next_player_id), None)
    if not next_player:
        return

    # Get next player mention
    try:
        next_user = await client.get_users(next_player_id)
        next_mention = next_user.mention
    except:
        next_mention = next_player['name']

    try:
        await callback_query.message.edit_text(
            f"🎮 You passed {card} to {next_mention}",
            reply_markup=None
        )
    except:
        pass

    # Continue game logic
    if len(game.locked_players) < len(game.players) - 1:
        current = game.get_current_player()
        if current:
            # Get current player mention
            try:
                current_user = await client.get_users(current['id'])
                current_mention = current_user.mention
            except:
                current_mention = current['name']

            await client.send_message(
                game.chat_id,
                f"🎮 {current_mention}'s turn! Choose a card to pass."
            )
            buttons = game.get_card_buttons(current['id'])
            if buttons:
                try:
                    msg = await client.send_message(
                        current['id'],
                        f"🎮 You received {card} from {callback_query.from_user.mention}. Choose a card to pass.",
                        reply_markup=buttons
                    )
                    game.add_button_message(msg.id, msg.chat.id)
                except:
                    await handle_blocked_player(client, game, current['id'])

    await callback_query.answer()

    if len(game.locked_players) >= len(game.players) - 1:
        await end_game(client, game)

@app.on_message(filters.command("lock") & filters.private)
async def lock_game(client, message):
    game = game_manager.get_game_by_player(message.from_user.id)
    if not game:
        return await message.reply("You're not in any active game!")

    if game.check_win(message.from_user.id):
        await message.reply(f"🎮 You completed your set and are now out!")
        await client.send_message(
            game.chat_id,
            f"🏆 {message.from_user.mention} has completed their set!"
        )

        if len(game.locked_players) >= len(game.players) - 1:
            await end_game(client, game)
        else:
            current = game.get_current_player()
            if current:
                buttons = game.get_card_buttons(current['id'])
                if buttons:
                    # Get current player mention
                    try:
                        current_user = await client.get_users(current['id'])
                        current_mention = current_user.mention
                    except:
                        current_mention = current['name']

                    await client.send_message(
                        game.chat_id,
                        f"🎮 {current_mention}'s turn now!"
                    )
                    try:
                        msg = await client.send_message(
                            current['id'],
                            f"🎮 Select a card to pass to the next player.",
                            reply_markup=buttons
                        )
                        game.add_button_message(msg.id, msg.chat.id)
                    except:
                        await handle_blocked_player(client, game, current['id'])
    else:
        await message.reply("You don't have matching cards yet!")

async def end_game(client, game):
    await disable_expired_buttons(client, game)
    await cleanup_game_messages(client, game)

    remaining = [p for p in game.players if p['id'] not in game.locked_players]
    if remaining:
        loser = remaining[0]

        # Get loser mention
        try:
            loser_user = await client.get_users(loser['id'])
            loser_mention = loser_user.mention
        except:
            loser_mention = loser['name']

        # Get winner mentions
        winner_mentions = []
        for p in game.players:
            if p['id'] in game.locked_players:
                try:
                    winner_user = await client.get_users(p['id'])
                    winner_mentions.append(f"• {winner_user.mention}")
                except:
                    winner_mentions.append(f"• {p['name']}")

        winners_text = "\n".join(winner_mentions)
        await client.send_message(
            game.chat_id,
            f"🎉 Game Over!\n🏆 Winners:\n{winners_text}\n\n{loser_mention} was the last without a set."
        )
    else:
        await client.send_message(game.chat_id, f"🎉 Game Over! Thanks for playing.")

    game_manager.end_game(game.chat_id)