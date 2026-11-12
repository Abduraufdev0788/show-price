from decimal import Decimal
from typing import Any, Dict, List
import numpy as np


class TechnicalAnalysis:
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index (RSI)."""
        if len(prices) < period + 1:
            return 50.0  # Neutral default

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(float(rsi), 2)

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average (EMA)."""
        if not prices:
            return 0.0
        if len(prices) < period:
            return float(np.mean(prices))

        multiplier = 2.0 / (period + 1)
        ema = float(np.mean(prices[:period]))
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        return round(ema, 2)

    @staticmethod
    def calculate_macd(prices: List[float]) -> Dict[str, float]:
        """Calculate MACD (12, 26, 9)."""
        if len(prices) < 35:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

        ema12 = TechnicalAnalysis.calculate_ema(prices, 12)
        ema26 = TechnicalAnalysis.calculate_ema(prices, 26)
        macd_line = round(ema12 - ema26, 2)

        # Estimate signal line
        macd_series = []
        for i in range(26, len(prices) + 1):
            subset = prices[:i]
            e12 = TechnicalAnalysis.calculate_ema(subset, 12)
            e26 = TechnicalAnalysis.calculate_ema(subset, 26)
            macd_series.append(e12 - e26)

        signal_line = TechnicalAnalysis.calculate_ema(macd_series, 9) if len(macd_series) >= 9 else macd_line
        histogram = round(macd_line - signal_line, 2)

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }

    @staticmethod
    def calculate_support_resistance(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, float]:
        """Calculate Classic Pivot Point Support and Resistance levels."""
        if not closes:
            return {"pivot": 0.0, "support1": 0.0, "resistance1": 0.0, "support2": 0.0, "resistance2": 0.0}

        high = max(highs[-24:]) if len(highs) >= 24 else max(highs)
        low = min(lows[-24:]) if len(lows) >= 24 else min(lows)
        close = closes[-1]

        pivot = (high + low + close) / 3.0
        r1 = (2.0 * pivot) - low
        s1 = (2.0 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        return {
            "pivot": round(pivot, 2),
            "resistance1": round(r1, 2),
            "support1": round(s1, 2),
            "resistance2": round(r2, 2),
            "support2": round(s2, 2),
        }

    @staticmethod
    def calculate_volatility(closes: List[float]) -> float:
        """Calculate annualized percentage volatility over recent closes."""
        if len(closes) < 2:
            return 0.0
        returns = np.diff(closes) / closes[:-1]
        std_dev = float(np.std(returns))
        # Return percentage standard deviation
        return round(std_dev * 100, 2)

    @classmethod
    def analyze_klines(cls, klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce full technical indicators summary from klines list."""
        if not klines:
            return {}

        closes = [float(k["close"]) for k in klines]
        highs = [float(k["high"]) for k in klines]
        lows = [float(k["low"]) for k in klines]
        volumes = [float(k["volume"]) for k in klines]

        rsi = cls.calculate_rsi(closes, 14)
        ema20 = cls.calculate_ema(closes, 20)
        ema50 = cls.calculate_ema(closes, 50)
        ema200 = cls.calculate_ema(closes, 200)
        macd = cls.calculate_macd(closes)
        levels = cls.calculate_support_resistance(highs, lows, closes)
        volatility = cls.calculate_volatility(closes)

        # Volume change: last candle volume vs 20-period average
        avg_vol = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
        vol_change_pct = round(((volumes[-1] - avg_vol) / avg_vol * 100.0), 2) if avg_vol > 0 else 0.0

        return {
            "rsi_14": rsi,
            "ema_20": ema20,
            "ema_50": ema50,
            "ema_200": ema200,
            "macd": macd,
            "support_resistance": levels,
            "volatility_pct": volatility,
            "volume_change_pct": vol_change_pct,
            "latest_close": closes[-1]
        }

