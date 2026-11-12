from datetime import datetime, timedelta, timezone
from decimal import Decimal
import time
from typing import Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database.models.ai import AIAnalysis, UserAIAnalysis
from services.binance_service import binance_service
from services.gemini_service import gemini_service
from services.technical_analysis import TechnicalAnalysis
from schemas.ai_analysis import AIAnalysisReport
from utils.formatters import format_datetime, format_usd
from utils.logger import logger


class AIForecastService:
    def __init__(self):
        self._cached_report: Optional[AIAnalysisReport] = None
        self._cached_indicators: Optional[Dict] = None
        self._cached_time: Optional[datetime] = None
        self._user_last_request: Dict[int, float] = {}

    def get_or_generate_forecast(
        self,
        session: Session,
        user_id: int,
        user_tz: str = "Asia/Tashkent",
        force_refresh: bool = False
    ) -> Tuple[str, bool]:
        """
        Get latest AI forecast report.
        If cache is fresh (< 60 minutes) and not forced, returns cached report.
        Enforces user cooldown for force_refresh.
        Returns: (formatted_message, is_cached)
        """
        now_ts = time.time()
        now_dt = datetime.now(timezone.utc)

        # Check cooldown for manual request
        if force_refresh:
            last_req = self._user_last_request.get(user_id, 0)
            cooldown_sec = settings.AI_MANUAL_COOLDOWN_MINUTES * 60
            if (now_ts - last_req) < cooldown_sec:
                remaining_min = int((cooldown_sec - (now_ts - last_req)) / 60) + 1
                return (
                    f"⏳ <b>AI tahlil cheklovi (Cooldown):</b>\n\n"
                    f"Siz yaqinda yangi tahlil so'ragansiz. Bepul API kvotasini tejash uchun "
                    f"yana <b>{remaining_min} daqiqa</b>dan so'ng yangi tahlil so'rashingiz mumkin.\n\n"
                    f"Quyida so'nggi tayyor tahlil ko'rsatilmoqda:\n\n"
                    + self._format_cached_report(user_tz),
                    True
                )

        # Check in-memory cache
        cache_validity = timedelta(minutes=settings.AI_ANALYSIS_INTERVAL_MINUTES)
        if (
            not force_refresh
            and self._cached_report is not None
            and self._cached_time is not None
            and (now_dt - self._cached_time) < cache_validity
        ):
            return self._format_cached_report(user_tz), True

        # Check DB cache
        stmt = (
            select(AIAnalysis)
            .where(AIAnalysis.expires_at > now_dt)
            .order_by(AIAnalysis.analyzed_at.desc())
            .limit(1)
        )
        db_analysis = session.execute(stmt).scalar_one_or_none()
        if not force_refresh and db_analysis:
            return self._format_db_analysis(db_analysis, user_tz), True

        # Generate fresh analysis using Binance real data + Gemini
        if not gemini_service.is_available():
            return self._generate_technical_only_report(session, user_tz), False

        try:
            current_price = float(binance_service.get_current_price("BTCUSDT"))
            ticker_24h = binance_service.get_24hr_ticker("BTCUSDT")
            klines = binance_service.get_klines("BTCUSDT", interval="1h", limit=100)
            indicators = TechnicalAnalysis.analyze_klines(klines)

            report = gemini_service.generate_market_analysis(
                current_price=current_price,
                ticker_24h=ticker_24h,
                indicators=indicators
            )

            # Update cache
            self._cached_report = report
            self._cached_indicators = indicators
            self._cached_time = now_dt
            self._user_last_request[user_id] = now_ts

            # Save in DB
            expires_at = now_dt + timedelta(minutes=settings.AI_ANALYSIS_INTERVAL_MINUTES)
            for h in report.horizons:
                ai_row = AIAnalysis(
                    market_price=Decimal(str(current_price)),
                    model_name=settings.GEMINI_MODEL,
                    forecast_horizon=h.forecast_horizon,
                    lower_price=h.lower_price,
                    upper_price=h.upper_price,
                    market_direction=h.market_direction,
                    confidence=h.confidence,
                    reasoning=h.reasoning,
                    risks=h.risks,
                    technical_indicators=indicators,
                    analyzed_at=now_dt,
                    expires_at=expires_at
                )
                session.add(ai_row)
                session.flush()

                if user_id > 0:
                    user_req = UserAIAnalysis(
                        user_id=user_id,
                        ai_analysis_id=ai_row.id,
                        requested_at=now_dt
                    )
                    session.add(user_req)

            session.commit()
            return self._format_cached_report(user_tz), False

        except Exception as e:
            logger.error(f"Failed to generate fresh AI forecast: {e}")
            if self._cached_report is not None:
                return "⚠️ <i>Gemini so'rovi cheklandi, so'nggi saqlangan tahlil:</i>\n\n" + self._format_cached_report(user_tz), True
            return self._generate_technical_only_report(session, user_tz), False

    def _format_cached_report(self, user_tz: str) -> str:
        report = self._cached_report
        ind = self._cached_indicators or {}
        time_str = format_datetime(self._cached_time or datetime.now(timezone.utc), user_tz)

        curr = Decimal(str(report.current_price))
        h1 = next((h for h in report.horizons if h.forecast_horizon == "1h"), None)
        h4 = next((h for h in report.horizons if h.forecast_horizon == "4h"), None)
        h24 = next((h for h in report.horizons if h.forecast_horizon == "24h"), None)

        dir_icons = {"bullish": "🟢 O'sish (Buqa)", "bearish": "🔴 Tushish (Ayiq)", "neutral": "⚪️ Neytral"}
        conf_icons = {"low": "Past", "medium": "O'rtacha", "high": "Yuqori"}

        lines = [
            f"🤖 <b>BTC 1 SOATLIK AI PROGNOZ & BOZOR TAHLILI</b>",
            f"⏱ <i>Vaqt: {time_str}</i>",
            f"💵 <b>Hozirgi narx:</b> <code>{format_usd(curr)}</code>\n"
        ]

        if h1:
            max_rise = max(Decimal("0"), h1.upper_price - curr)
            max_drop = max(Decimal("0"), curr - h1.lower_price)
            lines.extend([
                f"⏳ <b>KEYINGI 1 SOAT ICHIDAGI KUTILMA:</b>",
                f"• 🎯 <b>Kutilayotgan oraliq:</b> <b>{format_usd(h1.lower_price)} — {format_usd(h1.upper_price)}</b>",
                f"• 📈 <b>Ko'tarilish ehtimoli:</b> +{format_usd(max_rise)} gacha ({format_usd(h1.upper_price)})",
                f"• 📉 <b>Tushish ehtimoli:</b> -{format_usd(max_drop)} gacha ({format_usd(h1.lower_price)})",
                f"• 🧭 <b>Yo'nalish:</b> {dir_icons.get(h1.market_direction, h1.market_direction)}",
                f"• 🛡 <b>Ishonchlilik:</b> {conf_icons.get(h1.confidence, h1.confidence)}\n"
            ])

        if report.human_explanation_uz:
            lines.extend([
                f"💬 <b>Odam tilida tushuntirish:</b>",
                f"{report.human_explanation_uz}\n"
            ])
        elif report.summary_uz:
            lines.extend([
                f"💬 <b>AI Xulosasi:</b>",
                f"{report.summary_uz}\n"
            ])

        lines.extend([
            f"📊 <b>Texnik ko'rsatkichlar:</b>",
            f"• RSI (14): <code>{ind.get('rsi_14', 'N/A')}</code>",
            f"• EMA 20: <code>${ind.get('ema_20', 'N/A')}</code> | EMA 50: <code>${ind.get('ema_50', 'N/A')}</code>",
            f"• Volatillik: <code>{ind.get('volatility_pct', 'N/A')}%</code>\n"
        ])

        if h4 or h24:
            lines.append("🔭 <b>Uzoqroq muddatli ko'rinish:</b>")
            if h4:
                lines.append(f"• <b>4 soatlik:</b> {format_usd(h4.lower_price)} — {format_usd(h4.upper_price)} ({dir_icons.get(h4.market_direction, h4.market_direction)})")
            if h24:
                lines.append(f"• <b>24 soatlik:</b> {format_usd(h24.lower_price)} — {format_usd(h24.upper_price)} ({dir_icons.get(h24.market_direction, h24.market_direction)})")

        lines.append("\n⚠️ <i>Eslatma: Bu moliyaviy maslahat emas, bozor indikatorlari asosidagi ehtimoliy prognozdir.</i>")
        return "\n".join(lines)

    def _format_db_analysis(self, db_analysis: AIAnalysis, user_tz: str) -> str:
        time_str = format_datetime(db_analysis.analyzed_at, user_tz)
        ind = db_analysis.technical_indicators or {}
        curr = db_analysis.market_price
        max_rise = max(Decimal("0"), db_analysis.upper_price - curr)
        max_drop = max(Decimal("0"), curr - db_analysis.lower_price)

        return (
            f"🤖 <b>BTC 1 SOATLIK AI PROGNOZ (Keshdan)</b>\n"
            f"⏱ <i>Vaqt: {time_str}</i>\n"
            f"💵 <b>Bozor narxi:</b> {format_usd(curr)}\n\n"
            f"⏳ <b>Prognoz ({db_analysis.forecast_horizon}):</b>\n"
            f"• Kutilayotgan oraliq: <b>{format_usd(db_analysis.lower_price)} — {format_usd(db_analysis.upper_price)}</b>\n"
            f"• Ko'tarilsa: +{format_usd(max_rise)} | Tushsa: -{format_usd(max_drop)}\n"
            f"• Yo'nalish: <b>{db_analysis.market_direction.upper()}</b> ({db_analysis.confidence} ishonch)\n\n"
            f"Omillar: <i>{', '.join(db_analysis.reasoning)}</i>\n\n"
            f"⚠️ <i>Eslatma: Moliyaviy maslahat emas.</i>"
        )

    def _generate_technical_only_report(self, session: Session, user_tz: str) -> str:
        """Fallback when Gemini API is unavailable."""
        try:
            current_price = binance_service.get_current_price("BTCUSDT")
            klines = binance_service.get_klines("BTCUSDT", interval="1h", limit=100)
            ind = TechnicalAnalysis.analyze_klines(klines)
            sr = ind.get("support_resistance", {})
            time_str = format_datetime(datetime.now(timezone.utc), user_tz)

            return (
                f"📈 <b>BTC BOZOR TEXNIK TAHLILI</b>\n"
                f"⏱ <i>Vaqt: {time_str}</i>\n"
                f"💵 <b>Joriy BTC narxi:</b> {format_usd(current_price)}\n\n"
                f"📊 <b>Hisoblangan Texnik Indikatorlar:</b>\n"
                f"• RSI (14): <code>{ind.get('rsi_14')}</code>\n"
                f"• EMA 20: <code>${ind.get('ema_20')}</code> | EMA 50: <code>${ind.get('ema_50')}</code>\n"
                f"• Volatillik: <code>{ind.get('volatility_pct')}%</code>\n\n"
                f"📍 <b>Kutilayotgan Darajalar:</b>\n"
                f"• Yuqori qarshilik: <code>${sr.get('resistance1')}</code>\n"
                f"• Pastki qo'llab-quvvatlash: <code>${sr.get('support1')}</code>\n\n"
                f"⚠️ <i>Eslatma: AI servisi qayta ulanmoqda.</i>"
            )
        except Exception as e:
            logger.error(f"Error in technical fallback: {e}")
            return "⚠️ Bozor ma'lumotlarini yuklashda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."


ai_forecast_service = AIForecastService()
