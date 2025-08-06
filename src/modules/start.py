import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import MessageNotModified
from src import app
from src.database import add_user, add_chat, remove_chat


@app.on_message(filters.command("start") & ~filters.bot)
async def start(client: Client, m: Message):
    bot_name = app.name

    if m.chat.type == ChatType.PRIVATE:
        user_id = m.from_user.id
        await add_user(user_id, m.from_user.username or None)

        await m.reply_text(
            f"""<b>Hey {m.from_user.mention} 💫</b>

Welcome to <b>{bot_name}</b> — your ultimate companion for group card games! 🃏  

Experience the thrill of <b>Chitti Card Game</b> where strategy meets speed! The goal is simple: <b>collect all matching emoji cards</b> before your opponents do.

Ready to test your skills? Let the games begin! 🎮""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Start New Game", url=f"https://t.me/{app.username}?startgroup=true")],
                [
                    InlineKeyboardButton("📚 Game Rules", callback_data="game_rules"),
                    InlineKeyboardButton("👥 Support Group", url="https://t.me/DebugAngels")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=m.id
        )

    elif m.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        chat_id = m.chat.id
        await add_chat(chat_id, m.chat.title)

        await m.reply_text(
            f"Hey {m.from_user.mention}, I'm here to bring excitement to your group! 🎉",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 How to Play", callback_data="game_rules")],
                [InlineKeyboardButton("🎮 Create Game", callback_data="create_game_info")]
            ]),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=m.id
        )


@app.on_callback_query(filters.regex("^game_rules$"))
async def game_rules(client: Client, callback_query):
    await callback_query.answer()

    rules_text = """<b>🎮 Game Rules</b>

<b>🎯 Objective:</b>
Collect all cards of the same type (emoji) to win the round!

<b>⚙️ Setup:</b>
• 4-8 players required to start
• Each player receives N cards (N = number of players)
• Cards are distributed randomly from 8 different emoji types

<b>🎮 How to Play:</b>

<b>1. Starting the Game:</b>
• Host creates game with <code>/game</code>
• Players join using <code>/join</code>
• Host starts with <code>/begin</code>

<b>2. Gameplay:</b>
• Players take turns in random order
• On your turn, select ONE card to pass to the next player
• You'll receive cards from other players
• Goal: Collect all cards of ONE emoji type

<b>3. Winning:</b>
• When you have all matching cards, use <code>/lock</code>
• First to complete a matching set wins that round!
• Game continues until only one player remains

<b>🎲 Strategy Tips:</b>
• Keep track of which cards you've seen
• Try to collect the emoji type you have most of
• Sometimes it's better to pass cards others need!

<i>📝 Found a bug? Use <b>/feedback</b> to report it!</i>"""

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_start")]
    ])

    try:
        await callback_query.message.edit_text(
            rules_text,
            reply_markup=back_button,
            parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass


@app.on_callback_query(filters.regex("^create_game_info$"))
async def create_game_info(client: Client, callback_query):
    await callback_query.answer()

    info_text = """<b>🎮 Creating a Game</b>

<b>Quick Start Guide:</b>

<b>1. Create Game:</b>
Type <code>/game</code> in this group to create a new game session.

<b>2. Players Join:</b>
Other members use <code>/join</code> to participate.
• Minimum: 4 players
• Maximum: 8 players

<b>3. Start Playing:</b>
Game creator uses <code>/begin</code> to start the match.

<b>4. Game Flow:</b>
• Each player gets cards in their DM
• Take turns passing cards to each other
• First to collect matching cards wins!

<b>⚠️ Important:</b>
• All players must start the bot first
• Game happens via private messages
• You can only play in one group at a time

Ready to create some fun? Use <code>/game</code> now! 🚀"""

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
    ])

    try:
        await callback_query.message.edit_text(
            info_text,
            reply_markup=back_button,
            parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass


@app.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start(client: Client, callback_query):
    await callback_query.answer()
    user = callback_query.from_user
    bot_name = app.name

    if callback_query.message.chat.type == ChatType.PRIVATE:
        text = f"""<b>Hey {user.mention} 💫</b>

Welcome to <b>{bot_name}</b> — your ultimate companion for group card games! 🃏  

Experience the thrill of <b>Chitti Card Game</b> where strategy meets speed! The goal is simple: <b>collect all matching emoji cards</b> before your opponents do.

Ready to test your skills? Let the games begin! 🎮"""

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Start New Game", url=f"https://t.me/{app.username}?startgroup=true")],
            [
                InlineKeyboardButton("📚 Game Rules", callback_data="game_rules"),
                InlineKeyboardButton("👥 Support Group", url="https://t.me/DebugAngels")
            ]
        ])
    else:
        text = f"Hey {user.mention}, I'm here to bring excitement to your group! 🎉"
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 How to Play", callback_data="game_rules")],
            [InlineKeyboardButton("🎮 Create Game", callback_data="create_game_info")]
        ])

    try:
        await callback_query.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass


@app.on_chat_member_updated()
async def chat_updates(client: Client, m: ChatMemberUpdated):
    bot_id = (await client.get_me()).id

    if m.new_chat_member and m.new_chat_member.user and m.new_chat_member.user.id == bot_id:
        chat_id = m.chat.id
        await add_chat(chat_id, m.chat.title)

    elif m.old_chat_member and m.old_chat_member.user and m.old_chat_member.user.id == bot_id and not m.new_chat_member:
        chat_id = m.chat.id
        await remove_chat(chat_id)


@app.on_message(filters.command("help"))
async def help_command(client: Client, m: Message):
    if m.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await m.reply_text(
            "Need help? Click below to get detailed information about commands and gameplay!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Game Rules", callback_data="game_rules")]
            ]),
            reply_to_message_id=m.id
        )
    else:
        help_text = """<b>🎮 Game Commands:</b>
• <code>/game</code> – Create a new game (groups only)
• <code>/join</code> – Join the active game
• <code>/begin</code> – Start the game (host only)
• <code>/lock</code> – Declare win (when you have a matching set)
• <code>/stop</code> – End game (host/admin or 3+ votes)

<b>💬 Other Commands:</b>
• <code>/start</code> – Start the bot & see the main menu
• <code>/help</code> – Show this help message
• <code>/feedback</code> – Send feedback to the developers

<b>📚 Quick Guide:</b>
1. Go to a group and type <code>/game</code>
2. Wait for 4–8 players to <code>/join</code>
3. Host uses <code>/begin</code> to start
4. Play via DM, pass cards strategically
5. First to collect all matching cards wins!

<b>🎯 Objective:</b>
Collect all cards of the same emoji type before others do!

Need more details? Use the buttons below 👇"""
        
        await m.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📚 Detailed Rules", callback_data="game_rules"),
                    InlineKeyboardButton("🎮 Start New Game", url=f"https://t.me/{client.me.username}?startgroup=true")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=m.id
        )