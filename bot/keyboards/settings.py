from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models.user import UserSettings


def get_alert_settings_keyboard(settings: UserSettings) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=3)

    # Threshold presets
    presets = [10, 25, 50, 100, 250, 500]
    preset_buttons = []
    current_thresh = int(settings.price_threshold)
    for p in presets:
        mark = "✅ " if current_thresh == p else ""
        preset_buttons.append(
            InlineKeyboardButton(f"{mark}${p}", callback_data=f"set_thresh_{p}")
        )
    markup.add(*preset_buttons[:3])
    markup.add(*preset_buttons[3:])

    # Custom threshold button
    markup.add(InlineKeyboardButton("✏️ Boshqa chegara kiritish", callback_data="set_thresh_custom"))

    # Notification toggle
    notif_text = "🔔 Bildirishnomalar: YONIQ ✅" if settings.notification_enabled else "🔕 Bildirishnomalar: O'CHIQ ❌"
    markup.add(InlineKeyboardButton(notif_text, callback_data="toggle_notifications"))

    return markup


def get_general_settings_keyboard(settings: UserSettings) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)

    ai_text = "🤖 AI Tahlil: YONIQ ✅" if settings.ai_enabled else "🤖 AI Tahlil: O'CHIQ ❌"
    markup.add(
        InlineKeyboardButton(ai_text, callback_data="toggle_ai"),
        InlineKeyboardButton(f"⚙️ Xarid komissiyasi: {settings.buy_fee_percent}%", callback_data="change_buy_fee"),
        InlineKeyboardButton(f"⚙️ Sotuv komissiyasi: {settings.sell_fee_percent}%", callback_data="change_sell_fee"),
        InlineKeyboardButton("🔔 Signal sozlamalariga o'tish", callback_data="goto_alert_settings")
    )
    return markup

