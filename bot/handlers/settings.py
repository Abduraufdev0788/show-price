from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from bot.keyboards.purchase import get_cancel_inline_keyboard
from bot.keyboards.settings import get_general_settings_keyboard
from bot.states.settings_states import SettingsStates
from database.connection import get_db
from database.repositories.user_repo import UserRepository
from utils.validators import parse_and_validate_fee_percent
from utils.logger import logger


def register_settings_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "⚙️ SOZLAMALAR")
    def handle_settings_menu(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            settings = user.settings

        msg = (
            f"⚙️ <b>UMUMIY SOZLAMALAR</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {user.first_name or user.username or user.telegram_id}\n"
            f"🌐 <b>Vaqt mintaqasi:</b> {user.timezone}\n"
            f"📥 <b>Standart xarid komissiyasi:</b> {settings.buy_fee_percent}%\n"
            f"📤 <b>Standart sotuv komissiyasi:</b> {settings.sell_fee_percent}%\n"
            f"🤖 <b>AI Tahlil:</b> {'YOQILGAN ✅' if settings.ai_enabled else 'O\'CHIRILGAN ❌'}\n\n"
            f"O'zgartirish uchun kerakli tugmani bosing:"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_general_settings_keyboard(settings))

    @bot.callback_query_handler(func=lambda c: c.data == "toggle_ai")
    def handle_toggle_ai(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            user.settings.ai_enabled = not user.settings.ai_enabled
            settings = user.settings

        status = "yoqildi" if settings.ai_enabled else "o'chirildi"
        bot.answer_callback_query(call.id, f"AI tahlil {status}!")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_general_settings_keyboard(settings)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "change_buy_fee")
    def handle_change_buy_fee(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)
        bot.set_state(user_id, SettingsStates.buy_fee, chat_id)
        bot.send_message(
            chat_id=chat_id,
            text="Yangi standart xarid komissiyasi foizini kiriting (masalan: 0.1 yoki 0.25):",
            reply_markup=get_cancel_inline_keyboard()
        )

    @bot.message_handler(state=SettingsStates.buy_fee)
    def handle_buy_fee_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, fee, err = parse_and_validate_fee_percent(message.text)
        if not valid or fee is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            user.settings.buy_fee_percent = fee
            settings = user.settings

        bot.delete_state(user_id, chat_id)
        bot.send_message(
            chat_id=chat_id,
            text=f"✅ Xarid komissiyasi {fee}% ga o'zgartirildi.",
            reply_markup=get_general_settings_keyboard(settings)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "change_sell_fee")
    def handle_change_sell_fee(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)
        bot.set_state(user_id, SettingsStates.sell_fee, chat_id)
        bot.send_message(
            chat_id=chat_id,
            text="Yangi standart sotuv komissiyasi foizini kiriting (masalan: 0.1 yoki 0.2):",
            reply_markup=get_cancel_inline_keyboard()
        )

    @bot.message_handler(state=SettingsStates.sell_fee)
    def handle_sell_fee_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, fee, err = parse_and_validate_fee_percent(message.text)
        if not valid or fee is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            user.settings.sell_fee_percent = fee
            settings = user.settings

        bot.delete_state(user_id, chat_id)
        bot.send_message(
            chat_id=chat_id,
            text=f"✅ Sotuv komissiyasi {fee}% ga o'zgartirildi.",
            reply_markup=get_general_settings_keyboard(settings)
        )

