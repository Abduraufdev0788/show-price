from telebot.handler_backends import State, StatesGroup


class SettingsStates(StatesGroup):
    custom_threshold = State()  # Foydalanuvchi kiritadigan erkin chegara (masalan $150)
    buy_fee = State()           # Standart xarid komissiyasi foizi
    sell_fee = State()          # Standart sotuv komissiyasi foizi

