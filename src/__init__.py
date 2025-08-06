import time
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient

import config

# MongoDB connection
db = AsyncIOMotorClient(config.MONGO_URL).Anonymous

# Uptime tracking
START_TIME = time.time()


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="CricketBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            max_concurrent_transmissions=7,
        )

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        me = await self.get_me()
        self.id = me.id
        self.name = me.first_name
        self.username = me.username
   

    async def stop(self, *args, **kwargs):
        await super().stop(*args, **kwargs)
  


app = Bot()