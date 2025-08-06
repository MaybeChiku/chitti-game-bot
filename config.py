from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API credentials
API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
BOT_TOKEN = getenv("BOT_TOKEN")

# Bot owner information
OWNER_ID = int(getenv("OWNER_ID"))

# MongoDB database URL
MONGO_URL = getenv("MONGO_URL")

# Logger channel or group ID
LOGGER_ID = int(getenv("LOGGER_ID"))

# Game card items
CARD_ITEMS = ["🍎", "🍉", "🍒", "🍓", "🍊", "🍋", "🍍", "🥝"]