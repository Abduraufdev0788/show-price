import signal
import sys
import time

from bot.loader import bot
from bot.handlers import register_all_handlers
from config import settings
from database.connection import init_db
from utils.logger import logger


def signal_handler(sig, frame):
    logger.info("Bot stopping gracefully...")
    bot.stop_polling()
    sys.exit(0)


def main():
    logger.info("Starting BTC AI Tracker Telegram Bot...")

    # Ensure database tables exist (if not migrated via alembic)
    try:
        init_db()
        logger.info("Database connection verified.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    # Register all handlers
    register_all_handlers(bot)
    logger.info("All handlers registered successfully.")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN.startswith("your_"):
        logger.warning(
            "TELEGRAM_BOT_TOKEN is not set or using default placeholder. "
            "Please configure TELEGRAM_BOT_TOKEN in .env to run live polling."
        )
        return

    logger.info("Starting bot polling loop...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=20)
    except Exception as e:
        logger.error(f"Polling loop encountered an error: {e}")
        time.sleep(5)


if __name__ == "__main__":
    main()

