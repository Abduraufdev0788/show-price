from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_statistics_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📅 Bugun", callback_data="stats_today"),
        InlineKeyboardButton("📅 Bu hafta", callback_data="stats_week")
    )
    markup.add(
        InlineKeyboardButton("📅 Bu oy", callback_data="stats_month"),
        InlineKeyboardButton("📅 O'tgan oy", callback_data="stats_prev_month")
    )
    markup.add(
        InlineKeyboardButton("📅 Yillik", callback_data="stats_year"),
        InlineKeyboardButton("♾ Butun davr", callback_data="stats_all_time")
    )
    return markup

