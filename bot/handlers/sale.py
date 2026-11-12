from decimal import Decimal
from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.loader import bot
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.sale import (
    get_open_positions_keyboard,
    get_sale_qty_options_keyboard,
    get_sale_fee_keyboard,
    get_sale_confirm_keyboard,
    get_post_sale_keyboard,
)
from bot.keyboards.purchase import get_cancel_inline_keyboard
from bot.states.sale_states import SaleStates
from database.connection import get_db
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.user_repo import UserRepository
from services.price_service import price_service
from services.sale_service import sale_service
from utils.calculations import calculate_sale_metrics, quantize_btc, quantize_usd, to_decimal
from utils.formatters import format_btc, format_usd
from utils.validators import parse_and_validate_btc, parse_and_validate_fee_percent, parse_and_validate_usd
from utils.logger import logger


def register_sale_handlers(bot: TeleBot) -> None:
    @bot.message_handler(func=lambda m: m.text == "🔴 BTC SOTDIM")
    @bot.callback_query_handler(func=lambda call: call.data == "start_sale_flow")
    def start_sale_flow(event) -> None:
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        user_id = event.from_user.id

        if isinstance(event, CallbackQuery):
            bot.answer_callback_query(event.id)

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            open_purchases = PurchaseRepository.get_open_purchases(session, user_id=user.id)

            if not open_purchases:
                bot.send_message(
                    chat_id=chat_id,
                    text="ℹ️ Sizda hozirda ochiq BTC pozitsiyalari yo'q. Avval xaridni ro'yxatga oling:",
                    reply_markup=get_main_menu_keyboard(has_open_positions=False)
                )
                return

            user_tz = user.timezone

        bot.set_state(user_id, SaleStates.select_purchase, chat_id)
        bot.reset_data(user_id, chat_id)

        msg = (
            "🔴 <b>BTC SOTUVINI RO'YXATGA OLISH</b>\n\n"
            "Qaysi xarid pozitsiyasidan sotmoqchisiz?\n"
            "Quyidagi ro'yxatdan tanlang:"
        )
        bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=get_open_positions_keyboard(open_purchases, user_tz)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("sel_pos_"), state=SaleStates.select_purchase)
    def handle_position_selected(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)

        target = call.data.replace("sel_pos_", "")

        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            if target == "fifo":
                open_purchases = PurchaseRepository.get_open_purchases(session, user.id)
                if not open_purchases:
                    bot.send_message(chat_id=chat_id, text="Ochiq pozitsiyalar yo'q.")
                    return
                pos = open_purchases[0]
            else:
                pos = PurchaseRepository.get_by_id(session, user_id=user.id, purchase_id=int(target))
                if not pos:
                    bot.send_message(chat_id=chat_id, text="Pozitsiya topilmadi.")
                    return

            total_rem_btc = pos.remaining_btc_quantity
            purchase_id = pos.id
            purchase_price = pos.purchase_price
            cost_basis = pos.investment_amount * (pos.remaining_btc_quantity / pos.btc_quantity)

        bot.set_state(user_id, SaleStates.quantity, chat_id)
        with bot.retrieve_data(user_id, chat_id) as data:
            data["purchase_id"] = purchase_id
            data["max_btc"] = str(total_rem_btc)
            data["purchase_price"] = str(purchase_price)
            data["cost_basis"] = str(cost_basis)

        msg = (
            f"📦 <b>Pozitsiya #{purchase_id} tanlandi:</b>\n"
            f"🪙 Mavjud BTC: <code>{format_btc(total_rem_btc)}</code>\n"
            f"📈 Xarid narxi: {format_usd(purchase_price)}\n\n"
            f"Qancha miqdorda BTC sotmoqchisiz? Quyidagi foizlardan birini tanlang yoki miqdorni yozing:"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_sale_qty_options_keyboard(total_rem_btc))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("sale_pct_") or c.data == "sale_qty_custom", state=SaleStates.quantity)
    def handle_sale_qty_choice(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)

        if call.data == "sale_qty_custom":
            bot.send_message(
                chat_id=chat_id,
                text="Sotiladigan aniq BTC miqdorini kiriting (masalan: 0.005 yoki 0.00125):",
                reply_markup=get_cancel_inline_keyboard()
            )
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            max_btc = Decimal(data["max_btc"])
            if call.data == "sale_pct_100":
                qty = max_btc
            elif call.data == "sale_pct_50":
                qty = quantize_btc(max_btc * Decimal("0.5"))
            elif call.data == "sale_pct_25":
                qty = quantize_btc(max_btc * Decimal("0.25"))
            else:
                qty = max_btc

            data["sale_qty"] = str(qty)

        _ask_sale_price(chat_id, user_id)

    @bot.message_handler(state=SaleStates.quantity)
    def handle_custom_sale_qty_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, qty, err = parse_and_validate_btc(message.text)
        if not valid or qty is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            max_btc = Decimal(data["max_btc"])
            if qty > max_btc:
                bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Miqdor mavjud BTC ({format_btc(max_btc)}) dan oshib ketdi. Qayta kiriting:",
                    reply_markup=get_cancel_inline_keyboard()
                )
                return
            data["sale_qty"] = str(qty)

        _ask_sale_price(chat_id, user_id)

    def _ask_sale_price(chat_id: int, user_id: int) -> None:
        try:
            curr_price = price_service.get_current_btc_price()
        except Exception:
            curr_price = Decimal("75000.00")

        bot.set_state(user_id, SaleStates.price, chat_id)
        with bot.retrieve_data(user_id, chat_id) as data:
            data["default_price"] = str(curr_price)
            qty = Decimal(data["sale_qty"])

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(f"⚡️ Joriy narxda: {format_usd(curr_price)}", callback_data="sale_price_current"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")
        )

        msg = (
            f"🪙 <b>Sotilayotgan miqdor:</b> {format_btc(qty)}\n\n"
            f"BTC qaysi narxda sotilganini kiriting yoki joriy narxni tanlang:\n"
            f"<i>(Masalan: 75500 yoki 76200.00)</i>"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data == "sale_price_current", state=SaleStates.price)
    def handle_sale_price_current(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)

        with bot.retrieve_data(user_id, chat_id) as data:
            data["sale_price"] = data["default_price"]

        _ask_sale_fee(chat_id, user_id)

    @bot.message_handler(state=SaleStates.price)
    def handle_sale_price_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, price, err = parse_and_validate_usd(message.text)
        if not valid or price is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nSotuv narxini qayta kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            data["sale_price"] = str(price)

        _ask_sale_fee(chat_id, user_id)

    def _ask_sale_fee(chat_id: int, user_id: int) -> None:
        bot.set_state(user_id, SaleStates.fee, chat_id)
        with get_db() as session:
            user = UserRepository.get_or_create(session, telegram_id=user_id)
            default_fee = str(user.settings.sell_fee_percent if user.settings else "0.1")

        with bot.retrieve_data(user_id, chat_id) as data:
            data["default_fee_pct"] = default_fee

        msg = (
            "🏦 <b>Sotuv komissiyasi:</b>\n\n"
            f"Sotuv uchun komissiya foizini tanlang (Standart: {default_fee}%):"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_sale_fee_keyboard(default_fee))

    @bot.callback_query_handler(func=lambda c: c.data in ["sale_fee_default", "sale_fee_zero", "sale_fee_custom"], state=SaleStates.fee)
    def handle_sale_fee_selection(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)

        if call.data == "sale_fee_custom":
            msg = "Iltimos, sotuv komissiyasi foizini kiriting (masalan: 0.1 yoki 0.2):"
            bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            if call.data == "sale_fee_default":
                data["fee_percent"] = data["default_fee_pct"]
            else:
                data["fee_percent"] = "0.0"

        _show_sale_confirmation(chat_id, user_id)

    @bot.message_handler(state=SaleStates.fee)
    def handle_custom_sale_fee_input(message: Message) -> None:
        user_id = message.from_user.id
        chat_id = message.chat.id

        valid, fee_pct, err = parse_and_validate_fee_percent(message.text)
        if not valid or fee_pct is None:
            bot.send_message(chat_id=chat_id, text=f"❌ {err}\nQaytadan kiriting:", reply_markup=get_cancel_inline_keyboard())
            return

        with bot.retrieve_data(user_id, chat_id) as data:
            data["fee_percent"] = str(fee_pct)

        _show_sale_confirmation(chat_id, user_id)

    def _show_sale_confirmation(chat_id: int, user_id: int) -> None:
        bot.set_state(user_id, SaleStates.confirm, chat_id)
        with bot.retrieve_data(user_id, chat_id) as data:
            purchase_id = int(data["purchase_id"])
            qty = Decimal(data["sale_qty"])
            price = Decimal(data["sale_price"])
            fee_pct = Decimal(data["fee_percent"])

        with get_db() as session:
            pos = PurchaseRepository.get_by_id(session, user_id=UserRepository.get_or_create(session, user_id).id, purchase_id=purchase_id)
            allocated_cost = quantize_usd(pos.investment_amount * (qty / pos.btc_quantity))

        gross, fee, net_proceeds, gross_pl, net_pl = calculate_sale_metrics(
            btc_quantity_sold=qty,
            sale_price=price,
            selling_fee_percent=fee_pct,
            allocated_cost_basis=allocated_cost
        )

        with bot.retrieve_data(user_id, chat_id) as data:
            data["gross"] = str(gross)
            data["fee"] = str(fee)
            data["net_proceeds"] = str(net_proceeds)
            data["allocated_cost"] = str(allocated_cost)
            data["net_pl"] = str(net_pl)

        pl_sign = "🟢 +" if net_pl >= Decimal("0") else "🔴 -"
        pl_formatted = f"{pl_sign}{format_usd(abs(net_pl))}"

        msg = (
            "📋 <b>SOTUVNI TASDIQLASH (SALE CONFIRMATION)</b>\n\n"
            f"🪙 <b>Sotilayotgan BTC:</b> {format_btc(qty)}\n"
            f"📈 <b>Sotuv narxi:</b> {format_usd(price)}\n"
            f"💰 <b>Xarid qiymati (Cost Basis):</b> {format_usd(allocated_cost)}\n"
            f"💵 <b>Yalpi tushum (Gross):</b> {format_usd(gross)}\n"
            f"🏷 <b>Sotuv komissiyasi:</b> {format_usd(fee)}\n"
            f"💸 <b>Qoladigan sof summa:</b> {format_usd(net_proceeds)}\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"📊 <b>REALIZATSIYA QILINGAN SOF FOYDA/ZARAR:</b>\n"
            f"👉 <b>{pl_formatted}</b>\n\n"
            f"Sotuvni tasdiqlaysizmi?"
        )
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_sale_confirm_keyboard())

    @bot.callback_query_handler(func=lambda c: c.data == "edit_sale", state=SaleStates.confirm)
    def handle_edit_sale(call: CallbackQuery) -> None:
        bot.answer_callback_query(call.id)
        start_sale_flow(call)

    @bot.callback_query_handler(func=lambda c: c.data == "confirm_sale", state=SaleStates.confirm)
    def handle_confirm_sale(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id, "Sotuv rasmiylashtirilmoqda...")

        with bot.retrieve_data(user_id, chat_id) as data:
            purchase_id = int(data["purchase_id"])
            qty = Decimal(data["sale_qty"])
            price = Decimal(data["sale_price"])
            fee_pct = Decimal(data["fee_percent"])
            net_pl = Decimal(data["net_pl"])
            net_proceeds = Decimal(data["net_proceeds"])

        try:
            with get_db() as session:
                user = UserRepository.get_or_create(session, telegram_id=user_id)
                sale, purchase = sale_service.sell_from_position(
                    session=session,
                    user_id=user.id,
                    purchase_id=purchase_id,
                    btc_quantity_sold=qty,
                    sale_price=price,
                    selling_fee_percent=fee_pct
                )
                rem_qty = purchase.remaining_btc_quantity
                pos_status = purchase.status
                open_purchases = PurchaseRepository.get_open_purchases(session, user_id=user.id)
                has_open = len(open_purchases) > 0

            bot.delete_state(user_id, chat_id)

            pl_icon = "🟢" if net_pl >= Decimal("0") else "🔴"
            pl_text = f"+{format_usd(net_pl)}" if net_pl >= Decimal("0") else f"-{format_usd(abs(net_pl))}"

            report_msg = (
                f"✅ <b>SOTUV MUVAFFAQIYATLI AMALGA OSHIRILDI!</b>\n\n"
                f"🪙 <b>Sotilgan:</b> {format_btc(qty)}\n"
                f"📈 <b>Sotuv narxi:</b> {format_usd(price)}\n"
                f"💸 <b>Sof tushum:</b> {format_usd(net_proceeds)}\n"
                f"{pl_icon} <b>Realizatsiya qilingan P/L:</b> <b>{pl_text}</b>\n\n"
                f"📦 <b>Pozitsiya #{purchase_id} holati:</b>\n"
                f"• Qolgan BTC: {format_btc(rem_qty)}\n"
                f"• Holat: {pos_status}\n"
            )

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=report_msg,
                reply_markup=get_post_sale_keyboard()
            )

            bot.send_message(
                chat_id=chat_id,
                text="Asosiy menyu:",
                reply_markup=get_main_menu_keyboard(has_open_positions=has_open)
            )

        except Exception as e:
            logger.error(f"Error executing sale: {e}")
            bot.send_message(chat_id=chat_id, text=f"❌ Sotuvda xatolik yuz berdi: {e}")

