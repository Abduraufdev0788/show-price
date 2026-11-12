from telebot.handler_backends import State, StatesGroup


class SaleStates(StatesGroup):
    select_purchase = State()  # Pozitsiyani tanlash
    quantity = State()         # Sotilayotgan BTC miqdori
    price = State()            # Sotuv narxi (USD)
    fee = State()              # Sotuv komissiyasi
    confirm = State()          # Tasdiqlash

