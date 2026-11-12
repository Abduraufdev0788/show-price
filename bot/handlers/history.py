from telebot import TeleBot
from telebot.types import Message

from database.connection import get_db
from database.repositories.transaction_repo import TransactionRepository
from database.repositories.user_repo import UserRepository
from utils.formatters import format_btc, format_datetime, format_usd
from utils.logger import logger


def register_history_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "📜 TRANZAKSIYALAR TARIXI")
    def handle_transactions_history(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                txs = TransactionRepository.get_user_transactions(session, user_id=user.id, limit=15)
                user_tz = user.timezone

            if not txs:
                bot.send_message(
                    chat_id=chat_id,
                    text="📜 <b>Sizda hali tranzaksiyalar mavjud emas.</b>\n"
                         "BTC xaridini kiritish uchun <b>🟢 BTC SOTIB OLDIM</b> tugmasini bosing."
                )
                return

            lines = ["📜 <b>OXIRGI TRANZAKSIYALAR TARIXI:</b>\n"]
            for tx in txs:
                dt_str = format_datetime(tx.created_at, user_tz)
                if tx.transaction_type == "BUY":
                    icon = "🟢 XARID"
                    amt_str = f"-{format_usd(tx.amount)}"
                else:
                    icon = "🔴 SOTUV"
                    amt_str = f"+{format_usd(tx.amount)}"

                lines.append(
                    f"{icon} | <code>{format_btc(tx.btc_quantity)}</code> @ {format_usd(tx.price)}\n"
                    f"💵 Summa: {amt_str} | Komissiya: {format_usd(tx.fee)}\n"
                    f"⏱ <i>{dt_str}</i>\n"
                    f"──────────────"
                )

            bot.send_message(chat_id=chat_id, text="\n".join(lines))
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            bot.send_message(chat_id=chat_id, text=f"❌ Tarixni yuklashda xatolik: {e}")

