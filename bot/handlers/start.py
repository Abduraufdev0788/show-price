from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from database.connection import get_db
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.user_repo import UserRepository
from bot.keyboards.main_menu import get_main_menu_keyboard
from utils.logger import logger


def register_start_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def handle_start(message: Message) -> None:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(
                    session=session,
                    telegram_id=user_id,
                    username=username,
                    first_name=first_name
                )
                open_purchases = PurchaseRepository.get_open_purchases(session, user_id=user.id)
                has_open = len(open_purchases) > 0

            greeting = f"Assalomu alaykum, <b>{first_name or 'Hurmatli foydalanuvchi'}</b>!\n\n"
            text = (
                f"{greeting}"
                f"🤖 <b>BTC AI Tracker</b> botiga xush kelibsiz!\n\n"
                f"Bu bot orqali siz:\n"
                f"• Real vaqtdagi BTC/USDT narxlarini kuzatishingiz;\n"
                f"• Narx belgilangan chegaraga yetganda tezkor signallar olishingiz;\n"
                f"• Google Gemini AI orqali bozor tahlili va prognozlarni ko'rishingiz;\n"
                f"• Shaxsiy BTC xarid va sotuvlaringizni ro'yxatga olib, haqiqiy foyda/zararni (P/L) aniq hisoblashingiz mumkin.\n\n"
                f"Quyidagi menyudan kerakli bo'limni tanlang 👇"
            )

            bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=get_main_menu_keyboard(has_open_positions=has_open)
            )
        except Exception as e:
            logger.error(f"Error in /start handler: {e}")
            bot.send_message(
                chat_id=message.chat.id,
                text="Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring."
            )

    @bot.message_handler(commands=["help"])
    def handle_help(message: Message) -> None:
        text = (
            f"📖 <b>BTC AI Tracker — Qo'llanma</b>\n\n"
            f"<b>Asosiy bo'limlar:</b>\n"
            f"📊 <b>BTC NARXI</b> — Binance birjasidagi eng so'nggi real narx.\n"
            f"🟢 <b>BTC SOTIB OLDIM</b> — Yangi BTC xaridini ro'yxatga olish.\n"
            f"🔴 <b>BTC SOTDIM</b> — Mavjud BTC'ni to'liq yoki qisman sotish.\n"
            f"💼 <b>PORTFOLIO</b> — Sizning barcha ochiq pozitsiyalaringiz va kutilayotgan foyda.\n"
            f"📈 <b>AI TAHLIL</b> — Google Gemini va texnik indikatorlar tahlili.\n"
            f"💰 <b>FOYDA / ZARAR</b> — Savdolardan olingan sof foyda yoki zarar.\n"
            f"📅 <b>OYLIK STATISTIKA</b> — Oylar kesimidagi batafsil moliyaviy hisobot.\n"
            f"🔔 <b>SIGNAL SOZLAMALARI</b> — Narx o'zgarishi chegarasini sozlash ($10..$500).\n"
            f"⚙️ <b>SOZLAMALAR</b> — Komissiyalar va bildirishnomalar sozlamalari."
        )
        bot.send_message(chat_id=message.chat.id, text=text)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_action")
    def handle_cancel_action(call: CallbackQuery) -> None:
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.answer_callback_query(call.id, "Amal bekor qilindi.")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Amal bekor qilindi. Bosh menyudasiz."
        )

