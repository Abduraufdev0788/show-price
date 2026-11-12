from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.binance_service import binance_service
from services.price_service import price_service
from utils.formatters import format_datetime, format_usd
from utils.logger import logger


def get_price_inline_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_btc_price"),
        InlineKeyboardButton("📈 AI Tahlil", callback_data="open_ai_analysis")
    )
    return markup


def build_price_message() -> str:
    current_price = price_service.get_current_btc_price()
    try:
        t24 = binance_service.get_24hr_ticker("BTCUSDT")
        pct = t24.get("price_change_percent", Decimal("0"))
        sign = "+" if pct >= 0 else ""
        arrow = "🟢 ↗️" if pct >= 0 else "🔴 ↘️"
        h24 = format_usd(t24.get("high_price", Decimal("0")))
        l24 = format_usd(t24.get("low_price", Decimal("0")))
        vol = f"{t24.get('volume', Decimal('0')):,.2f} BTC"
        change_text = f"{arrow} <b>24s o'zgarish:</b> {sign}{pct:.2f}%\n"
    except Exception:
        change_text = ""
        h24 = "N/A"
        l24 = "N/A"
        vol = "N/A"

    msg = (
        f"📊 <b>BITCOIN (BTC/USDT) BOZOR NARXI</b>\n\n"
        f"💵 <b>Joriy narx:</b> <code>{format_usd(current_price)}</code>\n"
        f"{change_text}"
        f"🔺 <b>24s Yuqori:</b> {h24}\n"
        f"🔻 <b>24s Quyi:</b> {l24}\n"
        f"📦 <b>24s Savdo hajmi:</b> {vol}\n"
        f"🏛 <b>Birja:</b> Binance\n"
    )
    return msg


def register_price_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "📊 BTC NARXI")
    def handle_btc_price_menu(message: Message) -> None:
        try:
            text = build_price_message()
            bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=get_price_inline_keyboard()
            )
        except Exception as e:
            logger.error(f"Error handling BTC price: {e}")
            bot.send_message(
                chat_id=message.chat.id,
                text="⚠️ Narxni olishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
            )

    @bot.callback_query_handler(func=lambda call: call.data == "refresh_btc_price")
    def handle_refresh_price(call: CallbackQuery) -> None:
        try:
            text = build_price_message()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_price_inline_keyboard()
            )
            bot.answer_callback_query(call.id, "Narx yangilandi!")
        except Exception as e:
            logger.warning(f"Error refreshing price: {e}")
            bot.answer_callback_query(call.id, "Narx o'zgarmadi yoki xatolik yuz berdi.")

