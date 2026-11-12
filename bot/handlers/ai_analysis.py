from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.connection import get_db
from database.repositories.user_repo import UserRepository
from services.ai_forecast_service import ai_forecast_service
from utils.logger import logger


def get_ai_inline_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔄 Yangi AI tahlil so'rash", callback_data="refresh_ai_analysis"),
        InlineKeyboardButton("📊 Narxni ko'rish", callback_data="refresh_btc_price")
    )
    return markup


def register_ai_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "📈 AI TAHLIL")
    @bot.callback_query_handler(func=lambda c: c.data == "open_ai_analysis")
    def handle_ai_analysis(event) -> None:
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        user_id = event.from_user.id
        if isinstance(event, CallbackQuery):
            bot.answer_callback_query(event.id)

        status_msg = bot.send_message(chat_id=chat_id, text="🔍 <i>Bozor tahlili va ko'rsatkichlar hisoblanmoqda...</i>")

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                user_tz = user.timezone
                report_text, is_cached = ai_forecast_service.get_or_generate_forecast(
                    session=session,
                    user_id=user.id,
                    user_tz=user_tz,
                    force_refresh=False
                )

            bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
            bot.send_message(
                chat_id=chat_id,
                text=report_text,
                reply_markup=get_ai_inline_keyboard()
            )
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"❌ AI tahlilini yuklashda xatolik yuz berdi: {e}"
            )

    @bot.callback_query_handler(func=lambda c: c.data == "refresh_ai_analysis")
    def handle_refresh_ai_analysis(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id, "Tahlil yangilanmoqda...")

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                user_tz = user.timezone
                report_text, is_cached = ai_forecast_service.get_or_generate_forecast(
                    session=session,
                    user_id=user.id,
                    user_tz=user_tz,
                    force_refresh=True
                )

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=report_text,
                reply_markup=get_ai_inline_keyboard()
            )
        except Exception as e:
            logger.error(f"Error refreshing AI analysis: {e}")
            bot.answer_callback_query(call.id, "Yangilashda xatolik yuz berdi.")

