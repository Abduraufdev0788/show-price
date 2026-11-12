from telebot.handler_backends import State, StatesGroup


class PurchaseStates(StatesGroup):
    amount = State()      # Investitsiya summasi (USD)
    price = State()       # Xarid qilingan BTC narxi
    fee = State()         # Komissiya (USD yoki %)
    confirm = State()     # Tasdiqlash

