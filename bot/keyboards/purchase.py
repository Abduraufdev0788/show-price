from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_cancel_inline_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action"))
    return markup


def get_purchase_fee_keyboard(default_fee_pct: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"✅ Standart ({default_fee_pct}%) ichida", callback_data="fee_default"),
        InlineKeyboardButton("0️⃣ Komissiyasiz (0%)", callback_data="fee_zero"),
        InlineKeyboardButton("✏️ Boshqa komissiya kiritish", callback_data="fee_custom"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )
    return markup


def get_purchase_confirm_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Xaridni tasdiqlash", callback_data="confirm_purchase"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data="edit_purchase"),
    )
    markup.add(
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )
    return markup


def get_post_purchase_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔴 BTC SOTDIM (Sotuvni ro'yxatga olish)", callback_data="start_sale_flow"),
        InlineKeyboardButton("💼 Portfolioni ko'rish", callback_data="view_portfolio")
    )
    return markup

