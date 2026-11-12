import telebot
from telebot.storage import StateMemoryStorage
from telebot import custom_filters

from config import settings
from utils.logger import logger

# Initialize in-memory state storage (isolated by user_id and chat_id)
state_storage = StateMemoryStorage()

# Initialize TeleBot
bot = telebot.TeleBot(
    token=settings.TELEGRAM_BOT_TOKEN or "DUMMY_TOKEN_FOR_INITIALIZATION",
    state_storage=state_storage,
    parse_mode="HTML"
)

# Register custom filters for state handling
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())

