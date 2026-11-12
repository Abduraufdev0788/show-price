# BTC AI Tracker — Professional Telegram Bot & Market Analysis Worker

Professional, production-ready, AI-powered Bitcoin monitoring and portfolio management Telegram bot built with Python, PostgreSQL, SQLAlchemy 2.x, Alembic, Docker, and Google Gemini AI.

---

## 🚀 Imkoniyatlar (Features)

- **Real-vaqtdagi BTC Narxi:** Binance Public API orqali real-vaqtda BTC/USDT narxi, 24 soatlik tebranish, hajm va ekstremumlar.
- **Markazlashgan Monitoring:** 1 ta markaziy worker orqali narxlar olinadi (API limitlaridan oshib ketmaslik uchun har bir foydalanuvchiga alohida so'rov yuborilmaydi).
- **Shaxsiy Narx Harakati Signallari (Alerts):** Har bir foydalanuvchi uchun alohida narx o'zgarish chegarasi ($10, $25, $50, $100, $250, $500 yoki ixtiyoriy summa). Narx oshganda yoki tushganda avtomatik xabarnoma.
- **Google Gemini AI Bozor Tahlili:**
  - Texnik indikatorlar (RSI 14, EMA 20/50/200, MACD, Pivot Support/Resistance, Volatility) Python'da aniq hisoblanadi.
  - Rasmiy `google-genai` SDK orqali 1h, 4h va 24h bo'yicha ehtimoliy senariylar va darajalar taqdim etiladi.
  - Bepul tarif kvotalarini ehtiyotlash uchun avtomatik keshlash (60 daqiqa) va qo'lda so'rovlar uchun cooldown (10 daqiqa).
- **BTC Xaridini Ro'yxatga Olish (🟢 BTC SOTIB OLDIM):**
  - Xarid summasi, BTC narxi, birja komissiyasi.
  - Ochiq pozitsiya yaratish (`OPEN`) va avtomatik ravishda `🔴 BTC SOTDIM` tugmasini faollashtirish.
- **BTC Sotuvini Ro'yxatga Olish (🔴 BTC SOTDIM):**
  - To'liq yoki qisman sotuv (Partial Sales).
  - FIFO (First-In, First-Out) tamoyili bo'yicha tannarxni adolatli taqsimlash.
  - Pozitsiyani yopish (`CLOSED`) yoki qoldiq miqdorni yangilash.
- **Moliyaviy Dvigatel (P/L Engine):**
  - Barcha hisob-kitoblar qat'iy ravishda `Decimal` da bajariladi (`float` ishlatilmaydi).
  - Kutilayotgan (Unrealized) va Realizatsiya qilingan (Realized) foyda/zarar qat'iy ajratilgan.
- **Shaxsiy Portfolio va Statistika:**
  - `💼 PORTFOLIO`: Ochiq pozitsiyalar, o'rtacha xarid narxi, likvidatsiya qiymati, kutilayotgan P/L.
  - `📅 OYLIK STATISTIKA`: Bugun, hafta, oy, o'tgan oy, yil va butun davr kesimida g'alabali/mag'lubiyatli savdolar soni, sof foyda/zarar.
- **Multi-User Izolyatsiya:** Bir foydalanuvchi boshqa bir foydalanuvchining portfeli yoki tranzaksiyalarini ko'ra olmaydi yoki o'zgartira olmaydi.

---

## 🛠 Texnologiyalar Staki

- **Til & Muhit:** Python 3.12+
- **Telegram Bot:** `pyTelegramBotAPI` (`telebot`)
- **Baza & ORM:** PostgreSQL 16, SQLAlchemy 2.x, Alembic
- **Validatsiya:** Pydantic v2
- **Foniy Ishlar:** APScheduler
- **AI Integratsiya:** `google-genai` (Google Gemini)
- **Konteynerlashtirish:** Docker, Docker Compose
- **Testlash:** pytest, pytest-mock

---

## 📁 Loyiha Strukturasi

```text
btc_ai_tracker/
├── bot.py                     # Telegram Bot entrypoint
├── worker.py                  # Background Price Monitor & AI worker
├── config.py                  # Pydantic Settings konfiguratsiya
├── requirements.txt           # Python bog'liqliklar
├── Dockerfile                 # Docker obraz
├── docker-compose.yml         # Ko'p konteynerli Docker sozlamasi
├── alembic.ini                # Alembic konfiguratsiyasi
├── migrations/                # Database migratsiyalari
├── bot/
│   ├── loader.py              # TeleBot va StateMemoryStorage
│   ├── keyboards/             # Reply va Inline tugmalar
│   ├── handlers/              # Telegram buyruqlari va xabarlarni qayta ishlash
│   └── states/                # FSM foydalanuvchi holatlari
├── services/
│   ├── binance_service.py     # Binance Public API mijozi
│   ├── price_service.py       # Narx monitoringi va keshlash
│   ├── alert_service.py       # Narx signallarini yuborish
│   ├── purchase_service.py    # Xaridlarni qayd etish
│   ├── sale_service.py        # Sotuvlar va FIFO tannarx taqsimoti
│   ├── portfolio_service.py   # Portfel hisob-kitoblari
│   ├── statistics_service.py  # Vaqt kesimidagi moliyaviy hisobotlar
│   ├── technical_analysis.py  # RSI, EMA, MACD, Pivot indikatorlari
│   ├── gemini_service.py      # Google GenAI mijoz integratsiyasi
│   └── ai_forecast_service.py # AI tahlil koordinatori va keshlash
├── database/
│   ├── base.py                # DeclarativeBase va TimestampMixin
│   ├── connection.py          # SessionLocal va engine
│   ├── models/                # SQLAlchemy 2.0 ma'lumotlar modellari
│   └── repositories/          # Baza so'rovlari va izolyatsiya qilingan CRUD
├── scheduler/
│   ├── monitor.py             # APScheduler rejalashtiruvchisi
│   ├── jobs.py                # Narx va AI davriy topshiriqlari
│   └── locks.py               # Process lock (dublikat worker'lar oldini olish)
└── tests/                     # To'liq avtomatlashtirilgan testlar to'plami
```

---

## ⚙️ O'rnatish va Ishga Tushirish

### 1. Repozitoriyni klonlash va `.env` faylini sozlash

```bash
cp .env.example .env
nano .env
```

`.env` faylida quyidagi asosiy o'zgaruvchilarni to'ldiring:
- `TELEGRAM_BOT_TOKEN`: [@BotFather](https://t.me/BotFather) dan olingan bot tokeni.
- `ADMIN_TELEGRAM_IDS`: O'zingizning Telegram ID raqamingiz.
- `GEMINI_API_KEY`: [Google AI Studio](https://aistudio.google.com/) dan olingan API kalit.

---

### 2. Docker Compose orqali ishga tushirish (Tavsiya etiladi)

Tizimda Docker va Docker Compose o'rnatilgan bo'lsa:

```bash
# Konteynerlarni yig'ish va fonga tushirish
docker compose up -d --build

# Ishlayotgan konteynerlar holatini tekshirish
docker compose ps

# Loglarni real vaqtda kuzatish
docker compose logs -f

# Bot loglari
docker compose logs -f bot

# Worker loglari
docker compose logs -f worker
```

---

### 3. Docker boshqaruv buyruqlari

```bash
# Tizimni to'xtatish
docker compose down

# Baza migratsiyasini qo'lda ishga tushirish
docker compose exec bot alembic upgrade head

# PostgreSQL ma'lumotlarini zaxiralash (Backup)
docker compose exec -t db pg_dump -U btc_user btc_tracker_db > backup_$(date +%Y%m%d_%H%M%S).sql

# PostgreSQL ma'lumotlarini qayta tiklash (Restore)
cat backup_file.sql | docker compose exec -T db psql -U btc_user -d btc_tracker_db
```

---

### 4. Lokal ishlab chiquvchi muhitida ishga tushirish (Local Dev)

```bash
# Kutubxonalarni o'rnatish
pip install -r requirements.txt

# Baza migratsiyalarini qo'llash
alembic upgrade head

# Testlarni yurgizish
pytest -v

# Botni ishga tushirish
python bot.py

# Boshqa terminalda Worker'ni ishga tushirish
python worker.py
```

---

## 🧪 Avtomatlashtirilgan Testlar

Loyiha barcha asosiy talablar bo'yicha to'liq `pytest` test qoplamasiga ega:

```bash
pytest -v
```

Test qamrovi:
- ✅ **Multi-user isolation:** Foydalanuvchilar o'rtasida ma'lumotlar ajratilganligi.
- ✅ **Purchase & Sale lifecycle:** Xarid qilish, qisman sotish, FIFO, pozitsiyani yopish.
- ✅ **Decimal Math:** Moliyaviy aniqlik, komissiyalar, realized va unrealized P/L.
- ✅ **Alembic Migrations:** Jadvallarning to'g'ri yaratilishi va qaytarilishi (`upgrade/downgrade`).
- ✅ **Price Alerts:** Narx harakati chegaralari ($100 drop/rise) va dublikatlarning oldini olish.
- ✅ **AI Schemas & Indicators:** Pydantic sxemalari, RSI, EMA, MACD, Pivot Point hisoblash.

