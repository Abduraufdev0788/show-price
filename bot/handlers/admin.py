from telebot import TeleBot
from telebot.types import Message
from sqlalchemy import func, select

from config import settings
from database.connection import get_db
from database.models import User, Purchase, Sale, Transaction
from utils.formatters import format_usd
from utils.logger import logger


def register_admin_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["admin"])
    def handle_admin_command(message: Message) -> None:
        user_id = message.from_user.id
        if user_id not in settings.admin_ids and str(user_id) not in settings.ADMIN_TELEGRAM_IDS:
            bot.reply_to(message, "⛔️ Ushbu buyruq faqat bot administratorlari uchun ruxsat etilgan.")
            return

        try:
            with get_db() as session:
                users_count = session.execute(select(func.count(User.id))).scalar() or 0
                purchases_count = session.execute(select(func.count(Purchase.id))).scalar() or 0
                sales_count = session.execute(select(func.count(Sale.id))).scalar() or 0
                total_volume = session.execute(select(func.sum(Transaction.amount))).scalar() or 0

            msg = (
                "👑 <b>ADMINISTRATOR DASHBOARD</b>\n\n"
                f"👥 <b>Foydalanuvchilar:</b> {users_count} ta\n"
                f"📥 <b>Jami xaridlar:</b> {purchases_count} ta\n"
                f"📤 <b>Jami sotuvlar:</b> {sales_count} ta\n"
                f"💰 <b>Umumiy aylanma:</b> {format_usd(total_volume)}\n\n"
                f"⚡️ <b>Tizim holati:</b> ISHLAMOQDA ✅"
            )
            bot.send_message(chat_id=message.chat.id, text=msg)
        except Exception as e:
            logger.error(f"Error in admin handler: {e}")
            bot.send_message(chat_id=message.chat.id, text=f"Xatolik yuz berdi: {e}")

