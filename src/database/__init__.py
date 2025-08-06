from motor.motor_asyncio import AsyncIOMotorClient
import config 

# Asynchronous Database Connection
ChatBot = AsyncIOMotorClient(config.MONGO_URL)
# Database
db = ChatBot["CricketBot"]

# Collections
usersdb = db["users"] # Users Collection
chatsdb = db["chats"] # Chats Collection
games_collection = db["games"] # Game Collection

# Importing other modules
from .chats import *
