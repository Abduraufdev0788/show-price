from decimal import Decimal
from typing import List
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models.purchase import Purchase
from utils.formatters import format_btc, format_usd, format_datetime


def get_open_positions_keyboard(purchases: List[Purchase], user_tz: str = "Asia/Tashkent") -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)

    for p in purchases:
        date_str = format_datetime(p.purchase_date, user_tz).split()[0]
        btn_text = f"📦 #{p.id} | {format_btc(p.remaining_btc_quantity)} @ {format_usd(p.purchase_price)} ({date_str})"
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"sel_pos_{p.id}"))

    markup.add(InlineKeyboardButton("⚡️ FIFO (Eng dastlabkisidan sotish)", callback_data="sel_pos_fifo"))
    markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action"))
    return markup


def get_sale_qty_options_keyboard(remaining_btc: Decimal) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("100% (Hammasi)", callback_data="sale_pct_100"),
        InlineKeyboardButton("50%", callback_data="sale_pct_50"),
        InlineKeyboardButton("25%", callback_data="sale_pct_25")
    )
    markup.add(InlineKeyboardButton("✏️ Boshqa miqdor kiritish", callback_data="sale_qty_custom"))
    markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action"))
    return markup


def get_sale_fee_keyboard(default_fee_pct: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(f"✅ Standart ({default_fee_pct}%)", callback_data="sale_fee_default"),
        InlineKeyboardButton("0️⃣ Komissiyasiz (0%)", callback_data="sale_fee_zero"),
        InlineKeyboardButton("✏️ Boshqa foiz kiritish", callback_data="sale_fee_custom"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
    )
    return markup


def get_sale_confirm_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Sotuvni tasdiqlash", callback_data="confirm_sale"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data="edit_sale"),
    )
    markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action"))
    return markup


def get_post_sale_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🟢 Yangi BTC xaridini kiritish", callback_data="start_buy_flow"),
        InlineKeyboardButton("💼 Portfolioni ko'rish", callback_data="view_portfolio"),
        InlineKeyboardButton("💰 Foyda / Zarar hisoboti", callback_data="view_profit_loss")
    )
    return markup

