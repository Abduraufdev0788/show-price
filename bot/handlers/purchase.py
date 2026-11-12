from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.loader import bot
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.purchase import (
    get_cancel_inline_keyboard,
    get_purchase_confirm_keyboard,
    get_purchase_fee_keyboard,
    get_post_purchase_keyboard,
)
from bot.states.purchase_states import PurchaseStates
from database.connection import get_db
from database.repositories.user_repo import UserRepository
from services.price_service import price_service
from services.purchase_service import purchase_service
from utils.calculations import calculate_purchase_quantity, quantize_btc, quantize_usd, to_decimal
from utils.formatters import format_btc, format_usd
from utils.validators import parse_and_validate_fee_percent, parse_and_validate_usd
from utils.logger import logger


def register_purchase_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "🟢 BTC SOTIB OLDIM")
    @bot.callback_query_handler(func=lambda call: call.data == "start_buy_flow")
    def start_purchase_flow(event) -> None:
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        user_id = event.from_user.id

        if isinstance(event, CallbackQuery):
            bot.answer_callback_query(event.id)

        # Clear any existing state and set to amount
        bot.set_state(user_id, PurchaseStates.amount, chat_id)
        bot.reset_data(user_id, chat_id)

        msg = (
            "🟢 <b>BTC XARIDINI RO'YXATGA OLISH</b>\n\n"
            "Qancha miqdorda (USD) Bitcoin sotib oldingiz?\n"
            "<i>(Masalan: 100 yoki 500.50)</i>"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_cancel_inline_keyboard())

    @bot.message_handler(state=PurchaseStates.amount)
    def handle_purchase_amount(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, amount, err = parse_and_validate_usd(message.text)
        if not valid or amount is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        # Fetch current BTC price to offer as convenient default
        try:
            curr_price = price_service.get_current_btc_price()
        except Exception:
            curr_price = Decimal("70000.00")

        bot.set_state(user_id, PurchaseStates.price, chat_id)
        with bot.retrieve_data(user_id, chat_id) as data:
            data["amount"] = str(amount)
            data["default_price"] = str(curr_price)

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(f"⚡️ Joriy narxda: {format_usd(curr_price)}", callback_data="buy_price_current"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
        )

        msg = (
            f"💵 <b>Kiritilgan summa:</b> {format_usd(amount)}\n\n"
            f"Endi BTC qaysi narxda sotib olinganini kiriting yoki joriy narxni tanlang:\n"
            f"<i>(Masalan: 74500 yoki 75200.50)</i>"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data == "buy_price_current", state=PurchaseStates.price)
    def handle_current_price_callback(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)

        with bot.retrieve_data(user_id, chat_id) as data:
            price = Decimal(data["default_price"])
            data["price"] = str(price)

        _ask_purchase_fee(chat_id, user_id)

    @bot.message_handler(state=PurchaseStates.price)
    def handle_purchase_price_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, price, err = parse_and_validate_usd(message.text)
        if not valid or price is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nBTC narxini qaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            data["price"] = str(price)

        _ask_purchase_fee(chat_id, user_id)

    def _ask_purchase_fee(chat_id: int, user_id: int) -> None:
        bot.set_state(user_id, PurchaseStates.fee, chat_id)
        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            default_fee = str(user.settings.buy_fee_percent if user.settings else "0.1")

        with bot.retrieve_data(user_id, chat_id) as data:
            data["default_fee_pct"] = default_fee

        msg = (
            "🏦 <b>Birja komissiyasi:</b>\n\n"
            f"Xarid uchun komissiya foizini tanlang (Standart: {default_fee}%):"
        )
        bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=get_purchase_fee_keyboard(default_fee)
        )

    @bot.callback_query_handler(func=lambda c: c.data in ["fee_default", "fee_zero", "fee_custom"], state=PurchaseStates.fee)
    def handle_fee_selection(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)

        if call.data == "fee_custom":
            msg = "Iltimos, komissiya foizini kiriting (masalan: 0.1 yoki 0.25):"
            bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            if call.data == "fee_default":
                data["fee_percent"] = data["default_fee_pct"]
            else:
                data["fee_percent"] = "0.0"

        _show_purchase_confirmation(chat_id, user_id)

    @bot.message_handler(state=PurchaseStates.fee)
    def handle_custom_fee_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, fee_pct, err = parse_and_validate_fee_percent(message.text)
        if not valid or fee_pct is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            data["fee_percent"] = str(fee_pct)

        _show_purchase_confirmation(chat_id, user_id)

    def _show_purchase_confirmation(chat_id: int, user_id: int) -> None:
        bot.set_state(user_id, PurchaseStates.confirm, chat_id)
        with bot.retrieve_data(user_id, chat_id) as data:
            inv = Decimal(data["amount"])
            price = Decimal(data["price"])
            fee_pct = Decimal(data["fee_percent"])

            qty, fee_usd = calculate_purchase_quantity(
                investment_amount=inv,
                btc_price=price,
                fee_percent=fee_pct,
                includes_fee=True
            )
            data["calculated_btc"] = str(qty)
            data["fee_usd"] = str(fee_usd)

        msg = (
            "📋 <b>XARIDNI TASDIQLASH (PURCHASE CONFIRMATION)</b>\n\n"
            f"💵 <b>Investitsiya summasi:</b> {format_usd(inv)}\n"
            f"📈 <b>BTC xarid narxi:</b> {format_usd(price)}\n"
            f"🏷 <b>Komissiya ({fee_pct}%):</b> {format_usd(fee_usd)}\n"
            f"🪙 <b>Olingan BTC miqdori:</b> <code>{format_btc(qty)}</code>\n\n"
            f"Ma'lumotlar to'g'rimi?"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_purchase_confirm_keyboard())

    @bot.callback_query_handler(func=lambda c: c.data == "edit_purchase", state=PurchaseStates.confirm)
    def handle_edit_purchase(call: CallbackQuery) -> None:
        bot.answer_callback_query(call.id)
        start_purchase_flow(call)

    @bot.callback_query_handler(func=lambda c: c.data == "confirm_purchase", state=PurchaseStates.confirm)
    def handle_confirm_purchase(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id, "Xarid saqlanmoqda...")

        with bot.retrieve_data(user_id, chat_id) as data:
            inv = Decimal(data["amount"])
            price = Decimal(data["price"])
            fee_pct = Decimal(data["fee_percent"])
            qty = Decimal(data["calculated_btc"])
            fee_usd = Decimal(data["fee_usd"])

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                purchase, tx = purchase_service.register_purchase(
                    session=session,
                    user_id=user.id,
                    investment_amount=inv,
                    purchase_price=price,
                    btc_quantity=qty,
                    fee_percent=fee_pct,
                    flat_fee=Decimal("0"),
                    investment_includes_fee=True
                )
                purchase_id = purchase.id

            bot.delete_state(user_id, chat_id)

            success_msg = (
                f"✅ <b>XARID MUVAFFAQIYATLI SAQLANDI!</b>\n\n"
                f"📦 <b>Pozitsiya ID:</b> #{purchase_id}\n"
                f"🪙 <b>Miqdor:</b> {format_btc(qty)}\n"
                f"💵 <b>Investitsiya:</b> {format_usd(inv)}\n"
                f"📈 <b>Xarid narxi:</b> {format_usd(price)}\n"
                f"🟢 <b>Status:</b> OCHIQ (OPEN)\n\n"
                f"Ushbu xaridni sotish vaqti kelganda pastdagi <b>🔴 BTC SOTDIM</b> tugmasidan foydalanishingiz mumkin."
            )

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=success_msg,
                reply_markup=get_post_purchase_keyboard()
            )

            # Send main menu with "🔴 BTC SOTDIM" button enabled!
            bot.send_message(
                chat_id=chat_id,
                text="Asosiy menyu yangilandi:",
                reply_markup=get_main_menu_keyboard(has_open_positions=True)
            )

        except Exception as e:
            logger.error(f"Error confirming purchase: {e}")
            bot.send_message(chat_id=chat_id, text=f"❌ Xaridni saqlashda xatolik yuz berdi: {e}")

