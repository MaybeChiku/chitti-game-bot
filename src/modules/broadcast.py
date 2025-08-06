import asyncio

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from src import app
from src.database import get_chats
from config import OWNER_ID

@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_(_, message: Message):
    """Broadcasts a single message to all chats and users."""

    reply = message.reply_to_message
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else None

    if not reply and not text:
        return await message.reply_text("❖ Reply to a message or provide text to broadcast.")

    progress_msg = await message.reply_text("❖ Broadcasting message, please wait...")

    sent, users, failed = 0, 0, 0
    data = await get_chats()
    recipients = data["chats"] + data["users"]

    for chat_id in recipients:
        try:
            if reply:
                await reply.copy(chat_id)
            else:
                await app.send_message(chat_id, text=text)

            if chat_id < 0:
                sent += 1
            else:
                users += 1

            await asyncio.sleep(0.2)

        except FloodWait as fw:
            await asyncio.sleep(fw.value + 1)
        except:
            failed += 1
            continue

    await progress_msg.edit_text(
        f"Broadcasted message to {sent} chats and {users} from the bot."
    )