from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard(has_open_positions: bool = False) -> ReplyKeyboardMarkup:
    """Create the main menu reply keyboard."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # First row: Price & AI analysis
    btn_price = KeyboardButton("📊 BTC NARXI")
    btn_ai = KeyboardButton("📈 AI TAHLIL")
    keyboard.row(btn_price, btn_ai)

    # Second row: Buy / Sell buttons
    btn_buy = KeyboardButton("🟢 BTC SOTIB OLDIM")
    if has_open_positions:
        btn_sell = KeyboardButton("🔴 BTC SOTDIM")
        keyboard.row(btn_buy, btn_sell)
    else:
        keyboard.row(btn_buy)

    # Third row: Portfolio & Profit/Loss
    btn_portfolio = KeyboardButton("💼 PORTFOLIO")
    btn_pl = KeyboardButton("💰 FOYDA / ZARAR")
    keyboard.row(btn_portfolio, btn_pl)

    # Fourth row: Statistics & History
    btn_monthly = KeyboardButton("📅 OYLIK STATISTIKA")
    btn_history = KeyboardButton("📜 TRANZAKSIYALAR TARIXI")
    keyboard.row(btn_monthly, btn_history)

    # Fifth row: Settings
    btn_alerts = KeyboardButton("🔔 SIGNAL SOZLAMALARI")
    btn_settings = KeyboardButton("⚙️ SOZLAMALAR")
    keyboard.row(btn_alerts, btn_settings)

    return keyboard

