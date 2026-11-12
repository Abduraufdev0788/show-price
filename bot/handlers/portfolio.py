from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from bot.keyboards.portfolio import get_portfolio_keyboard
from database.connection import get_db
from database.repositories.user_repo import UserRepository
from services.portfolio_service import portfolio_service
from utils.formatters import format_btc, format_datetime, format_usd
from utils.logger import logger


def build_portfolio_message(user_id: int) -> str:
    with get_db() as session:
        user = UserRepository.get_or_create(session, telegram_id=user_id)
        p_data = portfolio_service.get_user_portfolio(session, user_id=user.id)
        user_tz = user.timezone

    unrealized_pl = p_data["total_unrealized_pl"]
    unrealized_icon = "🟢 +" if unrealized_pl >= Decimal("0") else "🔴 -"
    unrealized_str = f"{unrealized_icon}{format_usd(abs(unrealized_pl))}"

    realized_pl = p_data["total_realized_pl"]
    realized_icon = "🟢 +" if realized_pl >= Decimal("0") else "🔴 -"
    realized_str = f"{realized_icon}{format_usd(abs(realized_pl))}"

    lines = [
        "💼 <b>SIZNING SHAXSIY PORTFELINGIZ</b>\n",
        f"🪙 <b>Ochiq BTC miqdori:</b> <code>{format_btc(p_data['total_open_btc'])}</code>",
        f"💵 <b>Bozordagi joriy qiymati:</b> {format_usd(p_data['total_current_market_value'])}",
        f"📈 <b>O'rtacha xarid narxi:</b> {format_usd(p_data['average_buy_price'])}",
        f"📊 <b>Bozor narxi:</b> {format_usd(p_data['current_btc_price'])}",
        f"💰 <b>Kiritilgan tannarx:</b> {format_usd(p_data['total_open_cost_basis'])}\n",
        f"⏳ <b>Kutilayotgan (Unrealized) P/L:</b> <b>{unrealized_str}</b>",
        f"✅ <b>Realizatsiya qilingan (Realized) P/L:</b> <b>{realized_str}</b>",
        f"🏷 <b>Jami to'langan komissiyalar:</b> {format_usd(p_data['total_selling_fees'])}\n",
    ]

    if p_data["positions"]:
        lines.append("📋 <b>Ochiq pozitsiyalar:</b>")
        for pos in p_data["positions"]:
            dt_str = format_datetime(pos["purchase_date"], user_tz).split()[0]
            pos_pl = pos["unrealized_pl"]
            sign = "+" if pos_pl >= 0 else "-"
            lines.append(
                f"• #{pos['purchase_id']} | <code>{format_btc(pos['remaining_btc'])}</code> @ {format_usd(pos['purchase_price'])} "
                f"({dt_str}) -> {sign}{format_usd(abs(pos_pl))}"
            )
    else:
        lines.append("ℹ️ <i>Hozirda ochiq pozitsiyalar mavjud emas.</i>")

    return "\n".join(lines)


def register_portfolio_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "💼 PORTFOLIO")
    @bot.callback_query_handler(func=lambda c: c.data == "view_portfolio")
    def handle_portfolio(event) -> None:
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        user_id = event.from_user.id
        if isinstance(event, CallbackQuery):
            bot.answer_callback_query(event.id)

        try:
            msg = build_portfolio_message(user_id)
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                p_data = portfolio_service.get_user_portfolio(session, user_id=user.id)
                has_open = p_data["has_open_positions"]

            bot.send_message(
                chat_id=chat_id,
                text=msg,
                reply_markup=get_portfolio_keyboard(has_open=has_open)
            )
        except Exception as e:
            logger.error(f"Error displaying portfolio: {e}")
            bot.send_message(chat_id=chat_id, text=f"❌ Portfolioni ko'rsatishda xatolik: {e}")

    @bot.callback_query_handler(func=lambda c: c.data == "refresh_portfolio")
    def handle_refresh_portfolio(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        try:
            msg = build_portfolio_message(user_id)
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                p_data = portfolio_service.get_user_portfolio(session, user_id=user.id)
                has_open = p_data["has_open_positions"]

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=msg,
                reply_markup=get_portfolio_keyboard(has_open=has_open)
            )
            bot.answer_callback_query(call.id, "Portfel yangilandi!")
        except Exception as e:
            logger.warning(f"Error refreshing portfolio: {e}")
            bot.answer_callback_query(call.id, "Yangilashda xatolik yuz berdi.")

