from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from bot.keyboards.purchase import get_cancel_inline_keyboard
from bot.keyboards.settings import get_alert_settings_keyboard
from bot.states.settings_states import SettingsStates
from database.connection import get_db
from database.repositories.user_repo import UserRepository
from utils.formatters import format_usd
from utils.validators import parse_and_validate_threshold
from utils.logger import logger


def register_alert_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "🔔 SIGNAL SOZLAMALARI")
    @bot.callback_query_handler(func=lambda c: c.data == "goto_alert_settings")
    def handle_alert_settings_menu(event) -> None:
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        user_id = event.from_user.id
        if isinstance(event, CallbackQuery):
            bot.answer_callback_query(event.id)

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            settings = user.settings

            status_str = "YOQILGAN ✅" if settings.notification_enabled else "O'CHIRILGAN ❌"
            msg = (
                f"🔔 <b>NARX O'ZGARISH SIGNALLARI SOZLAMALARI</b>\n\n"
                f"Siz belgilagan chegara miqdorida BTC narxi ko'tarilsa yoki tushsa, "
                f"bot sizga darhol Telegram xabarnoma yuboradi.\n\n"
                f"⚙️ <b>Joriy chegara:</b> {format_usd(settings.price_threshold)}\n"
                f"🔔 <b>Bildirishnomalar holati:</b> {status_str}\n\n"
                f"O'zgartirish uchun quyidagi tugmalardan birini tanlang:"
            )

            if isinstance(event, Message):
                bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_alert_settings_keyboard(settings))
            else:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=event.message.message_id,
                    text=msg,
                    reply_markup=get_alert_settings_keyboard(settings)
                )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_thresh_"))
    def handle_threshold_change(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        action = call.data.replace("set_thresh_", "")

        if action == "custom":
            bot.answer_callback_query(call.id)
            bot.set_state(user_id, SettingsStates.custom_threshold, chat_id)
            bot.send_message(
                chat_id=chat_id,
                text="✏️ O'zingiz xohlagan narx chegarasini USD da kiriting (masalan: 75 yoki 150):",
                reply_markup=get_cancel_inline_keyboard()
            )
            return

        # Preset selected
        thresh_val = Decimal(action)
        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            user.settings.price_threshold = thresh_val
            settings = user.settings

        bot.answer_callback_query(call.id, f"Chegara ${action} ga o'rnatildi!")
        msg = (
            f"🔔 <b>NARX SIGNALLARI SOZLAMALARI</b>\n\n"
            f"✅ Chegara muvaffaqiyatli saqlandi: <b>${action}</b>\n\n"
            f"Bildirishnomalar holati: {'YOQILGAN ✅' if settings.notification_enabled else 'O\'CHIRILGAN ❌'}"
        )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=msg,
            reply_markup=get_alert_settings_keyboard(settings)
        )

    @bot.message_handler(state=SettingsStates.custom_threshold)
    def handle_custom_threshold_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, thresh, err = parse_and_validate_threshold(message.text)
        if not valid or thresh is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            user.settings.price_threshold = thresh
            settings = user.settings

        bot.delete_state(user_id, chat_id)
        msg = (
            f"🔔 <b>NARX SIGNALLARI SOZLAMALARI</b>\n\n"
            f"✅ Chegara muvaffaqiyatli saqlandi: <b>{format_usd(thresh)}</b>"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_alert_settings_keyboard(settings))

    @bot.callback_query_handler(func=lambda c: c.data == "toggle_notifications")
    def handle_toggle_notifications(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            user.settings.notification_enabled = not user.settings.notification_enabled
            settings = user.settings

        state_text = "yoqildi" if settings.notification_enabled else "o'chirildi"
        bot.answer_callback_query(call.id, f"Bildirishnomalar {state_text}!")

        msg = (
            f"🔔 <b>NARX SIGNALLARI SOZLAMALARI</b>\n\n"
            f"⚙️ <b>Joriy chegara:</b> {format_usd(settings.price_threshold)}\n"
            f"🔔 <b>Bildirishnomalar holati:</b> {'YOQILGAN ✅' if settings.notification_enabled else 'O\'CHIRILGAN ❌'}"
        )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=msg,
            reply_markup=get_alert_settings_keyboard(settings)
        )

