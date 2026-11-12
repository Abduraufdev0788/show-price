# AGENTS.md
# BTC AI Tracker — Complete Professional Development Specification

## 1. PROJECT OVERVIEW

Build a production-ready, AI-powered Bitcoin monitoring and portfolio management Telegram bot.

The application must allow multiple Telegram users to independently monitor BTC prices, receive price movement notifications, obtain AI-powered market analysis, record BTC purchases and sales, and calculate their actual realized profit or loss.

The bot must support:

- Real-time BTC price monitoring.
- Automatic price movement alerts.
- Gemini AI market analysis.
- AI-based price forecasts and scenarios.
- BTC purchase registration.
- BTC sale registration.
- Automatic profit/loss calculations.
- Monthly and yearly financial statistics.
- Personal portfolio management.
- Transaction history.
- Configurable commissions.
- Docker-based deployment.

IMPORTANT:

This is a tracking, analysis, and signal application.

Do not implement automatic cryptocurrency trading.

Never request Telegram Wallet passwords, private keys, or seed phrases.

---

# 2. TECHNOLOGY STACK

Use the following technologies:

### Backend
- Python 3.11+
- pyTelegramBotAPI (telebot)
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic
- python-dotenv

### External APIs
- Binance Public API for BTC/USDT prices.
- Google Gemini API for AI market analysis.
- Gemini free-tier model available through the official Google Gen AI SDK.

Use:
`google-genai`

Do not use deprecated Gemini SDK integrations.

### Background Processing
- APScheduler
- Centralized BTC price monitoring.
- Separate background worker process where appropriate.

### Infrastructure
- Docker
- Docker Compose
- PostgreSQL container
- Python bot container
- Python worker container

### Testing
- pytest
- pytest-mock

### Code Quality
- Type hints.
- Decimal financial calculations.
- Structured logging.
- Modular architecture.

STRICT RULE:

Use pyTelegramBotAPI (`telebot`) exclusively.

Do not use Aiogram or python-telegram-bot.

---

# 3. MULTI-USER ARCHITECTURE

This bot must support unlimited registered users subject to infrastructure capacity.

Every Telegram user must have completely independent:

- Settings.
- Portfolio.
- Purchases.
- Sales.
- Transactions.
- Price alerts.
- AI analysis preferences.
- Monthly statistics.
- Trading history.

When a user presses `/start`:

1. Check whether the Telegram user already exists.
2. If not, register the user.
3. Create default user settings.
4. Initialize personal portfolio.
5. Display the main menu.

Use Telegram user ID as the external user identifier.

Every database query involving user data must be scoped to the authenticated Telegram user.

Never allow one user to access another user's transactions or financial statistics.

Use database foreign keys and appropriate indexes.

---

# 4. BTC PRICE MONITORING

Primary exchange: Binance.

API:

`https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT`

Requirements:

- Retrieve current BTC/USDT price.
- Validate API responses.
- Handle connection errors.
- Implement retry mechanisms.
- Handle API rate limits.
- Store last valid price.
- Store price timestamps.
- Detect stale data.
- Never generate new signals from stale prices.

Use one centralized price monitoring service.

Do not make an independent Binance request for every user.

Default monitoring interval: 5 seconds, configurable according to API limits and deployment capacity.

The monitoring system must continue running independently of individual Telegram conversations.

---

# 5. PRICE MOVEMENT NOTIFICATIONS

Default threshold: $100.

Example:

Reference price: $74,500

- $74,450: No alert.
- $74,400: BTC DOWN $100.
- $74,300: BTC DOWN $100 from the previous alert reference.
- $74,400: BTC UP $100.

Rules:

1. Each user has an independent alert threshold.
2. Compare the latest valid price with the user's notification reference.
3. Send a notification when the threshold is reached.
4. Update the user's reference after the notification.
5. Avoid duplicate notifications.
6. Support both upward and downward movements.
7. Store notifications in the database.

Allow users to configure:

- $10
- $25
- $50
- $100
- $250
- $500
- Custom threshold.

Users can enable or disable notifications independently.

---

# 6. GEMINI AI INTEGRATION

This is one of the most important features.

Integrate Google Gemini using the official Google Gen AI SDK.

Environment configuration:

`GEMINI_API_KEY=`

The API key must never be exposed to Telegram users.

Use a Gemini model that is currently available under Google's free-tier terms.

Do not hardcode a model name without checking current model availability.

Model name must be configurable through:

`GEMINI_MODEL=`

## 6.1. AI Market Analysis

Gemini should analyze BTC market information using real market data.

Provide the model with:

- Current BTC price.
- Recent price history.
- 1-hour price change.
- 4-hour price change.
- 24-hour price change.
- Trading volume.
- High and low prices.
- Relevant technical indicators.
- Available historical candles.
- Market trend information.

Calculate technical indicators in Python rather than asking Gemini to invent them.

Recommended indicators:

- RSI (14).
- EMA 20.
- EMA 50.
- EMA 200.
- MACD.
- Support and resistance levels.
- Volume changes.
- Volatility.

The AI must distinguish between actual market data and its own interpretation.

## 6.2. AI Price Forecast

The bot should answer questions such as:

- What is the possible BTC price in one hour?
- What could BTC cost in four hours?
- What is the possible 24-hour price range?
- Is the current trend bullish or bearish?
- What are the possible upward and downward scenarios?

Example output:

BTC AI ANALYSIS

Current price: $74,500

1-Hour Scenario:
- Possible range: $74,200–$74,800.
- Direction: Neutral.
- Confidence: Low.

4-Hour Scenario:
- Possible range: $73,900–$75,100.
- Direction: Slightly bullish.
- Confidence: Medium.

24-Hour Scenario:
- Possible range: $73,000–$76,000.
- Direction: Uncertain.
- Confidence: Low.

Market factors:
- RSI condition.
- EMA trend.
- Trading volume.
- Recent volatility.

Important:

These values are illustrative examples, not hardcoded predictions.

The AI must produce forecasts based on actual available data.

Never present speculative forecasts as guaranteed results.

Never invent exact probabilities or confidence levels without a defined methodology.

Use probabilistic scenarios only when supported by historical model evaluation or a calibrated forecasting method.

If data is insufficient, Gemini must explicitly say that a reliable forecast cannot be generated.

## 6.3. AI Forecast Output Format

Require structured JSON output from Gemini.

Example schema:

{
  "market_direction": "bullish",
  "forecast_horizon": "4h",
  "lower_price": 74200,
  "upper_price": 75100,
  "confidence": "medium",
  "reasoning": [
    "EMA trend",
    "RSI condition",
    "Volume changes"
  ],
  "risks": [
    "High volatility",
    "Unexpected market news"
  ]
}

Validate every AI response with Pydantic.

Reject invalid or incomplete responses.

Never execute AI-generated code or arbitrary instructions.

## 6.4. AI Forecast Limitations

- Gemini free-tier usage has rate limits.
- Do not call Gemini every five seconds.
- Use scheduled AI analysis.
- Cache the latest analysis.
- Allow manual analysis requests with cooldown.
- Handle quota exhaustion.
- Handle API failures.
- Display the analysis timestamp.
- Do not generate a fake forecast when Gemini is unavailable.

Recommended initial configuration:

- Automatic analysis: every 60 minutes.
- Manual analysis: configurable cooldown.
- Forecast horizons: 1h, 4h, 24h.

These settings must be configurable.

Do not promise that Gemini is always free. Respect current API quotas and pricing.

---

# 7. BUY BTC — PURCHASE REGISTRATION

Main menu button:

🟢 BTC SOTIB OLDIM

When the user clicks this button:

Start a purchase registration flow.

Collect:

1. Total amount paid in USD.
2. Actual BTC purchase price.
3. BTC quantity, if known.
4. Purchase commission.
5. Purchase date and time.
6. Optional notes.

If BTC quantity is provided, use the actual quantity.

Otherwise calculate it using the investment amount and fee structure.

Support both:

- Investment amount including fees.
- Investment amount excluding fees.

After collecting information, display a confirmation screen.

Example:

PURCHASE CONFIRMATION

Investment: $100
BTC price: $74,500
Purchase fee: $1
BTC quantity: calculated quantity

Buttons:

- ✅ Confirm Purchase
- ✏️ Edit
- ❌ Cancel

After confirmation:

1. Save the purchase in PostgreSQL.
2. Set position status to OPEN.
3. Display purchase details.
4. Show the current estimated profit/loss.
5. Display a new button:

🔴 BTC SOTDIM

IMPORTANT:

After a successful purchase, the user must see the sale button for that open position.

Do not mark a position as sold automatically.

---

# 8. SELL BTC — SALE REGISTRATION

When the user has an open BTC position, show:

🔴 BTC SOTDIM

When clicked, start the sale registration process.

Collect:

1. Actual BTC selling price.
2. BTC quantity sold.
3. Selling commission.
4. Actual received amount, if available.
5. Sale date and time.
6. Optional notes.

Support partial sales.

Example:

Purchase:
- Investment: $100
- BTC quantity: 0.001 BTC
- Purchase price: $74,500

Sale:
- Selling quantity: 0.001 BTC
- Selling price: $75,500
- Selling fee: 1%

Calculate:

Gross sale value:

0.001 × 75,500 = $75.50

Selling commission:

$75.50 × 1% = $0.755

Net sale proceeds:

$75.50 - $0.755 = $74.745

IMPORTANT:

The example is illustrative. Real purchase quantity and cost basis must be used for accurate P/L.

## 8.1. Sale Confirmation

Display:

SALE CONFIRMATION

BTC quantity sold: ...
Purchase cost basis: ...
Sale price: ...
Gross sale value: ...
Selling commission: ...
Purchase commission allocation: ...
Net profit/loss: ...

Buttons:

- ✅ Confirm Sale
- ✏️ Edit
- ❌ Cancel

After confirmation:

1. Save the sale transaction.
2. Calculate realized profit/loss.
3. Update the open position quantity.
4. Change status to CLOSED if all BTC has been sold.
5. Keep the position OPEN if there is a remaining quantity.
6. Update user financial statistics.
7. Display the final sale report.

The bot must then display:

🟢 BTC SOTIB OLDIM

This allows the user to register another purchase.

---

# 9. PROFIT AND LOSS ENGINE

Build a dedicated financial calculation service.

Never use float for money.

Use Decimal for all financial calculations.

Distinguish between:

### Unrealized Profit/Loss

The profit or loss that would result if an open position were sold at the current estimated selling price.

### Realized Profit/Loss

The actual profit or loss recorded after a confirmed sale.

Formula:

Net Realized P/L = Net Sale Proceeds - Allocated Acquisition Cost

Net Sale Proceeds:

Gross Sale Value - Selling Fees - Other Sale Expenses

Allocated Acquisition Cost:

Allocated Purchase Cost Including Purchase Fees

Support FIFO cost-basis accounting for partial sales as the default method.

Keep the accounting method configurable for future expansion.

Avoid counting the same purchase or sale twice.

Use database transactions when confirming sales.

All financial records must remain historically consistent.

---

# 10. PERSONAL FINANCIAL DASHBOARD

Create a personal statistics section.

Main menu button:

📊 STATISTIKA

Display:

- Total money invested.
- Total amount sold.
- Total BTC purchased.
- Current open BTC quantity.
- Current portfolio market value.
- Estimated unrealized profit/loss.
- Realized profit/loss.
- Total commissions paid.
- Number of purchases.
- Number of sales.
- Number of profitable trades.
- Number of losing trades.

Separate realized and unrealized P/L.

Never combine them without clearly labeling the figures.

## 10.1. Monthly Statistics

Create:

📅 BU OY

Calculate based on the current calendar month in the user's configured timezone.

Display:

- Number of completed sales.
- Total invested in purchases during the month.
- Total sales proceeds during the month.
- Realized gross profit/loss.
- Purchase fees.
- Selling fees.
- Other transaction expenses.
- Net realized profit/loss.
- Profitable trade count.
- Losing trade count.

Example:

MONTHLY REPORT — NOVEMBER

Completed trades: 8

Gross realized P/L: +$35.00

Purchase commissions: -$2.00

Selling commissions: -$2.50

Other fees: -$0.50

NET REALIZED PROFIT: +$30.00

Winning trades: 5
Losing trades: 3

This is illustrative output only.

Important:

A purchase alone must not be counted as realized profit or loss.

Unrealized profits from open positions must be displayed separately.

## 10.2. Additional Reports

Allow users to view:

- Today's statistics.
- This week's statistics.
- This month's statistics.
- Previous month's statistics.
- Yearly statistics.
- All-time statistics.

Implement accurate date boundaries and timezone-aware calculations.

---

# 11. PORTFOLIO MANAGEMENT

Main menu:

💼 PORTFOLIO

Display:

- Open positions.
- Closed positions.
- Total BTC quantity.
- Average acquisition cost.
- Current BTC price.
- Estimated net liquidation value.
- Unrealized P/L.
- Realized P/L.

For every open position show:

- Purchase date.
- Purchase price.
- BTC quantity remaining.
- Original investment.
- Allocated acquisition cost.
- Current estimated value.
- Estimated selling fee.
- Net estimated P/L.

Each position must have its own purchase and sale controls.

Support multiple simultaneous open positions.

---

# 12. MAIN TELEGRAM INTERFACE

Use professional Uzbek-language messages.

Main menu:

📊 BTC NARXI
🟢 BTC SOTIB OLDIM
💼 PORTFOLIO
📈 AI TAHLIL
💰 FOYDA / ZARAR
📅 OYLIK STATISTIKA
📜 TRANZAKSIYALAR TARIXI
🔔 SIGNAL SOZLAMALARI
⚙️ SOZLAMALAR

Use inline keyboards wherever appropriate.

Every registration flow must include:

- Cancel button.
- Back button.
- Input validation.
- Confirmation.
- Clear error messages.

After purchase:

Display the corresponding sale button.

After full sale:

Display the purchase button again.

For partial sales:

Keep the remaining position open and retain its sale button.

Use a proper per-user conversation state system.

Never use global conversation variables shared across users.

---

# 13. DATABASE DESIGN

Use PostgreSQL and SQLAlchemy 2.x.

Create the following models.

### User

- id
- telegram_id (unique)
- username
- first_name
- timezone
- is_active
- created_at
- updated_at

### UserSettings

- id
- user_id (FK)
- price_threshold
- monitoring_interval
- buy_fee_percent
- sell_fee_percent
- withdrawal_fee
- exchange_name
- notification_enabled
- ai_enabled
- ai_analysis_interval
- created_at
- updated_at

### Purchase

- id
- user_id (FK)
- investment_amount
- investment_includes_fee
- purchase_price
- btc_quantity
- remaining_btc_quantity
- purchase_fee
- purchase_fee_percent
- purchase_date
- status
- note
- created_at

### Sale

- id
- user_id (FK)
- purchase_id (FK)
- btc_quantity_sold
- sale_price
- gross_sale_amount
- selling_fee
- net_sale_proceeds
- allocated_cost_basis
- gross_profit_loss
- net_profit_loss
- sold_at
- note
- created_at

### Transaction

- id
- user_id (FK)
- purchase_id (FK, nullable)
- sale_id (FK, nullable)
- transaction_type
- amount
- btc_quantity
- price
- fee
- created_at

### PriceHistory

- id
- exchange
- symbol
- price
- volume
- recorded_at

### PriceAlert

- id
- user_id (FK)
- previous_price
- current_price
- difference
- direction
- created_at

### PriceMonitorState

- id
- exchange
- symbol
- reference_price
- last_price
- updated_at

### AIAnalysis

- id
- market_price
- model_name
- forecast_horizon
- lower_price
- upper_price
- market_direction
- confidence
- reasoning
- risks
- analyzed_at
- expires_at

### UserAIAnalysis

- id
- user_id (FK)
- ai_analysis_id (FK)
- requested_at

Use NUMERIC database fields for monetary and BTC values.

Add proper indexes, constraints, unique constraints, and relationships.

Do not store user financial data inside shared global records.

AI market analysis may be shared when generated from the same market data, but individual user portfolios and recommendations must remain isolated.

---

# 14. DOCKER AND DOCKER COMPOSE

Docker is mandatory.

The project must run using:

`docker compose up -d --build`

Create:

- Dockerfile
- docker-compose.yml
- .dockerignore
- .env.example

Required containers:

### 1. bot

Runs Telegram polling and handles user interactions.

### 2. worker

Runs BTC price monitoring, notifications, and scheduled AI analysis.

### 3. db

Runs PostgreSQL.

Use persistent Docker volumes for database storage.

Requirements:

- Restart policies.
- Health checks.
- Environment configuration.
- Internal Docker networking.
- Secure database credentials.
- Proper service dependencies.
- Database readiness checks.
- Graceful shutdown.
- Persistent logs where appropriate.

Only one worker instance should own a given scheduled monitoring job unless distributed locking is implemented.

Do not run duplicate schedulers accidentally.

Use Alembic migrations rather than relying on automatic table creation in production.

Provide commands for:

- Building containers.
- Starting containers.
- Stopping containers.
- Viewing logs.
- Running migrations.
- Restarting the bot.
- Backing up PostgreSQL.
- Restoring PostgreSQL.

---

# 15. PROJECT STRUCTURE

Create a clean modular architecture.

```text
btc_ai_tracker/
│
├── bot.py
├── worker.py
├── config.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
│
├── bot/
│   ├── __init__.py
│   ├── loader.py
│   ├── keyboards/
│   │   ├── main_menu.py
│   │   ├── purchase.py
│   │   ├── sale.py
│   │   ├── portfolio.py
│   │   ├── statistics.py
│   │   └── settings.py
│   │
│   ├── handlers/
│   │   ├── start.py
│   │   ├── price.py
│   │   ├── purchase.py
│   │   ├── sale.py
│   │   ├── portfolio.py
│   │   ├── statistics.py
│   │   ├── ai_analysis.py
│   │   ├── alerts.py
│   │   ├── settings.py
│   │   ├── history.py
│   │   └── admin.py
│   │
│   └── states/
│       ├── purchase_states.py
│       ├── sale_states.py
│       └── settings_states.py
│
├── services/
│   ├── price_service.py
│   ├── binance_service.py
│   ├── gemini_service.py
│   ├── technical_analysis.py
│   ├── ai_forecast_service.py
│   ├── portfolio_service.py
│   ├── purchase_service.py
│   ├── sale_service.py
│   ├── profit_loss_service.py
│   ├── fee_service.py
│   ├── statistics_service.py
│   └── alert_service.py
│
├── database/
│   ├── connection.py
│   ├── base.py
│   ├── models/
│   └── repositories/
│
├── scheduler/
│   ├── monitor.py
│   ├── jobs.py
│   └── locks.py
│
├── schemas/
│   ├── ai_analysis.py
│   ├── purchase.py
│   └── sale.py
│
├── utils/
│   ├── calculations.py
│   ├── formatters.py
│   ├── validators.py
│   ├── logger.py
│   └── timezone.py
│
├── migrations/
│
└── tests/
    ├── test_users.py
    ├── test_price_service.py
    ├── test_ai_forecast.py
    ├── test_purchase.py
    ├── test_sale.py
    ├── test_profit_loss.py
    ├── test_monthly_statistics.py
    ├── test_portfolio.py
    ├── test_multi_user.py
    └── test_alerts.py
```

The AI coding agent may improve the structure when technically justified.

Do not create unnecessary modules or duplicate business logic.

---

# 16. SECURITY AND RELIABILITY

Implement:

- Telegram user authorization.
- User-specific database queries.
- Admin authorization.
- Environment-based secrets.
- API timeout handling.
- Retry and backoff.
- Input validation.
- SQLAlchemy transaction management.
- Duplicate transaction prevention.
- Safe logging without secrets.
- Rate limiting.
- AI API quota handling.

Never expose Gemini API keys.

Never expose database passwords.

Never request wallet recovery phrases.

Never execute financial transactions automatically.

---

# 17. TESTING REQUIREMENTS

Write automated tests for:

### User isolation

- Two users register independently.
- User A cannot see User B's portfolio.
- User A cannot modify User B's purchases.
- User A cannot access User B's monthly reports.

### Purchase and sale

- Register a purchase.
- Register a sale.
- Register multiple purchases.
- Register partial sales.
- Close a position after a complete sale.
- Prevent selling more BTC than the remaining quantity.
- Cancel a purchase or sale before confirmation.

### Financial calculations

- Purchase commission.
- Selling commission.
- Gross profit/loss.
- Net profit/loss.
- Break-even price.
- Partial sale cost basis.
- FIFO calculations.
- Monthly realized P/L.
- Yearly realized P/L.
- Unrealized P/L.
- Rounding and precision.

### AI

- Gemini successful response.
- Invalid JSON response.
- Missing forecast fields.
- API quota exceeded.
- Timeout.
- Insufficient market data.
- Cached analysis.
- AI cooldown.

### Price monitoring

- $100 price drop.
- $100 price rise.
- Multiple consecutive price movements.
- Duplicate alert prevention.
- API outage.
- Stale market data.

### Docker

- Database health check.
- Bot startup.
- Worker startup.
- Database persistence.
- Application restart.

All tests must pass before considering the project complete.

---

# 18. DEVELOPMENT WORKFLOW

The AI coding agent must implement the project in phases.

Do not generate the entire application in one huge code response.

Complete each phase, test it, and then continue.

### PHASE 1 — Project Foundation

- Create project structure.
- Configure dependencies.
- Configure Docker.
- Configure PostgreSQL.
- Configure SQLAlchemy.
- Configure Alembic.
- Create database models.

### PHASE 2 — Telegram Bot

- Initialize telebot.
- Implement registration.
- Create the main menu.
- Create per-user states.
- Implement navigation.

### PHASE 3 — BTC Price System

- Integrate Binance.
- Create centralized monitoring.
- Save price history.
- Implement movement detection.
- Implement Telegram alerts.

### PHASE 4 — Purchase System

- Implement purchase registration.
- Validate input.
- Calculate BTC quantity.
- Save purchases.
- Display purchase confirmation.
- Display sale button after purchase.

### PHASE 5 — Sale System

- Implement sale registration.
- Implement partial sales.
- Calculate commissions.
- Calculate realized P/L.
- Update remaining BTC.
- Save completed sales.
- Restore purchase button after full sale.

### PHASE 6 — Portfolio and Statistics

- Build portfolio.
- Calculate unrealized P/L.
- Calculate realized P/L.
- Implement daily statistics.
- Implement weekly statistics.
- Implement monthly statistics.
- Implement yearly statistics.
- Implement all-time statistics.

### PHASE 7 — Gemini AI

- Integrate Gemini API.
- Collect market data.
- Calculate technical indicators.
- Implement structured forecasts.
- Implement AI analysis history.
- Implement caching and cooldown.
- Handle free-tier limitations.

### PHASE 8 — Settings and Admin

- Implement alert thresholds.
- Implement commissions.
- Implement notification settings.
- Implement AI settings.
- Implement admin dashboard.

### PHASE 9 — Testing and Production

- Run all tests.
- Fix bugs.
- Verify financial calculations.
- Verify user isolation.
- Verify Docker deployment.
- Prepare README.
- Prepare Ubuntu deployment instructions.

---

# 19. FINAL ACCEPTANCE CRITERIA

The application is complete only when:

1. Users can start and independently use the bot.
2. BTC prices are retrieved from Binance.
3. Price changes trigger personalized notifications.
4. Users can register BTC purchases.
5. Users see a sale button after purchasing.
6. Users can register complete and partial sales.
7. All confirmed transactions are stored in PostgreSQL.
8. Net realized profit/loss is calculated correctly.
9. Unrealized profit/loss is displayed separately.
10. Monthly profit reports work correctly.
11. Yearly and all-time reports work correctly.
12. Gemini generates data-based market analysis.
13. AI forecasts clearly communicate uncertainty.
14. AI free-tier limitations are handled.
15. Multiple users have isolated financial records.
16. Docker Compose starts the complete application.
17. Database data persists after container restarts.
18. All financial and user-isolation tests pass.

---

# 20. FINAL INSTRUCTIONS TO THE AI CODING AGENT

Act as a senior Python backend engineer, database architect, AI integration engineer, and DevOps engineer.

Before writing code:

1. Inspect the existing repository.
2. Read this AGENTS.md completely.
3. Identify missing requirements.
4. Create a development roadmap.
5. Explain the architecture.
6. Implement the application phase by phase.

Do not:

- Use Aiogram.
- Use hardcoded BTC prices.
- Invent Gemini forecasts.
- Promise guaranteed trading profits.
- Use float for financial calculations.
- Mix realized and unrealized profit.
- Mix different users' portfolios.
- Store secrets in source code.
- Implement automatic trading.
- Create fake database records.
- Ignore Docker.
- Leave critical functions as TODO or pass.

Prioritize:

- Financial accuracy.
- Data isolation.
- Reliable price monitoring.
- Gemini API integration.
- Clean Telegram UX.
- Database integrity.
- Docker deployment.
- Maintainable architecture.

The final result must be a complete, tested, Dockerized BTC AI Tracker Telegram bot, not merely a prototype.
