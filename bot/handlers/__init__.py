from telebot import TeleBot

from bot.handlers.start import register_start_handlers
from bot.handlers.price import register_price_handlers
from bot.handlers.purchase import register_purchase_handlers
from bot.handlers.sale import register_sale_handlers
from bot.handlers.portfolio import register_portfolio_handlers
from bot.handlers.statistics import register_statistics_handlers
from bot.handlers.ai_analysis import register_ai_handlers
from bot.handlers.alerts import register_alert_handlers
from bot.handlers.settings import register_settings_handlers
from bot.handlers.history import register_history_handlers
from bot.handlers.admin import register_admin_handlers


def register_all_handlers(bot: TeleBot) -> None:
    # 1. Base commands
    register_start_handlers(bot)
    register_admin_handlers(bot)

    # 2. Main functional flows
    register_price_handlers(bot)
    register_purchase_handlers(bot)
    register_sale_handlers(bot)
    register_portfolio_handlers(bot)
    register_statistics_handlers(bot)
    register_ai_handlers(bot)
    register_alert_handlers(bot)
    register_settings_handlers(bot)
    register_history_handlers(bot)

