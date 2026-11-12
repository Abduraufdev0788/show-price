from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_portfolio_keyboard(has_open: bool = True) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    if has_open:
        markup.add(
            InlineKeyboardButton("🔴 BTC Sotish", callback_data="start_sale_flow"),
            InlineKeyboardButton("🟢 BTC Sotib olish", callback_data="start_buy_flow")
        )
    else:
        markup.add(
            InlineKeyboardButton("🟢 Birinchi BTC xaridini kiritish", callback_data="start_buy_flow")
        )
    markup.add(InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_portfolio"))
    return markup

