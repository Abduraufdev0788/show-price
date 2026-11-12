from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from bot.keyboards.statistics import get_statistics_keyboard
from database.connection import get_db
from database.repositories.user_repo import UserRepository
from services.statistics_service import statistics_service
from utils.formatters import format_usd
from utils.logger import logger


def format_statistics_report(data: dict) -> str:
    period_title = data["period_label"]
    net_pl = data["net_realized_pl"]
    gross_pl = data["gross_realized_pl"]

    pl_icon = "🟢 +" if net_pl >= Decimal("0") else "🔴 -"
    pl_str = f"{pl_icon}{format_usd(abs(net_pl))}"

    gross_sign = "+" if gross_pl >= Decimal("0") else "-"
    gross_str = f"{gross_sign}{format_usd(abs(gross_pl))}"

    total_fees = data["total_purchase_fees"] + data["selling_commissions"]

    msg = (
        f"📊 <b>MOLIYAVIY HISOBOT — {period_title}</b>\n\n"
        f"🔄 <b>Yopilgan savdolar (Sotuvlar):</b> {data['completed_trades']} ta\n"
        f"📥 <b>Yangi xaridlar soni:</b> {data['purchases_count']} ta\n"
        f"💵 <b>Xaridlarga kiritilgan summa:</b> {format_usd(data['total_invested'])}\n"
        f"💸 <b>Sotuvlardan tushgan sof tushum:</b> {format_usd(data['total_sales_proceeds'])}\n\n"
        f"🏷 <b>Xarid komissiyalari:</b> -{format_usd(data['total_purchase_fees'])}\n"
        f"🏷 <b>Sotuv komissiyalari:</b> -{format_usd(data['selling_commissions'])}\n"
        f"🧾 <b>Jami to'langan komissiyalar:</b> -{format_usd(total_fees)}\n\n"
        f"📈 <b>Yalpi foyda/zarar (Gross):</b> {gross_str}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>SOF REALIZATSIYA QILINGAN P/L:</b>\n"
        f"👉 <b>{pl_str}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎯 <b>Yutuqli savdolar:</b> {data['winning_trades']} ta 🟢\n"
        f"🔻 <b>Zararli savdolar:</b> {data['losing_trades']} ta 🔴\n"
        f"⚖️ <b>Nol (Breakeven):</b> {data['breakeven_trades']} ta ⚪️\n\n"
        f"<i>Eslatma: Bu yerda faqat sotuv bilan yakunlangan (realized) savdolar aks etadi. Ochiq pozitsiyalar qiymati alohida 'Portfolio' bo'limida ko'rsatiladi.</i>"
    )
    return msg


def register_statistics_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text in ["📅 OYLIK STATISTIKA", "💰 FOYDA / ZARAR"])
    @bot.callback_query_handler(func=lambda c: c.data == "view_profit_loss")
    def handle_statistics_menu(event) -> None:
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        user_id = event.from_user.id
        if isinstance(event, CallbackQuery):
            bot.answer_callback_query(event.id)

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                data = statistics_service.get_month_statistics(session, user_id=user.id, user_tz=user.timezone)

            bot.send_message(
                chat_id=chat_id,
                text=format_statistics_report(data),
                reply_markup=get_statistics_keyboard()
            )
        except Exception as e:
            logger.error(f"Error showing statistics: {e}")
            bot.send_message(chat_id=chat_id, text=f"❌ Statistikani hisoblashda xatolik: {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("stats_"))
    def handle_period_stats_switch(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        period = call.data.replace("stats_", "")

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                tz = user.timezone

                if period == "today":
                    data = statistics_service.get_today_statistics(session, user.id, tz)
                elif period == "week":
                    data = statistics_service.get_week_statistics(session, user.id, tz)
                elif period == "month":
                    data = statistics_service.get_month_statistics(session, user.id, tz)
                elif period == "prev_month":
                    data = statistics_service.get_prev_month_statistics(session, user.id, tz)
                elif period == "year":
                    data = statistics_service.get_year_statistics(session, user.id, tz)
                elif period == "all_time":
                    data = statistics_service.get_all_time_statistics(session, user.id)
                else:
                    data = statistics_service.get_month_statistics(session, user.id, tz)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=format_statistics_report(data),
                reply_markup=get_statistics_keyboard()
            )
            bot.answer_callback_query(call.id, f"{data['period_label']} yuklandi!")
        except Exception as e:
            logger.error(f"Error switching stats period: {e}")
            bot.answer_callback_query(call.id, "Hisoblashda xatolik yuz berdi.")

