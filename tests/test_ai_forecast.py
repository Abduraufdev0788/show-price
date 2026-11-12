from decimal import Decimal
import pytest
from pydantic import ValidationError

from schemas.ai_analysis import AIHorizonForecast, AIAnalysisReport
from services.technical_analysis import TechnicalAnalysis


def test_ai_schema_validation_valid():
    data = {
        "current_price": Decimal("75000.00"),
        "timestamp": "BTCUSDT",
        "horizons": [
            {
                "forecast_horizon": "1h",
                "market_direction": "bullish",
                "lower_price": Decimal("74800.00"),
                "upper_price": Decimal("75500.00"),
                "confidence": "medium",
                "reasoning": ["RSI above 50", "EMA 20 upward slope"],
                "risks": ["Short-term pullback"]
            }
        ],
        "summary_uz": "Bozor ijobiy ko'rinishda."
    }
    report = AIAnalysisReport(**data)
    assert report.current_price == Decimal("75000.00")
    assert report.horizons[0].market_direction == "bullish"


def test_ai_schema_validation_invalid_bounds():
    # upper_price < lower_price must fail validation
    data = {
        "forecast_horizon": "4h",
        "market_direction": "bearish",
        "lower_price": Decimal("76000.00"),
        "upper_price": Decimal("74000.00"),  # Invalid: upper < lower
        "confidence": "high",
        "reasoning": ["Heavy selling volume"],
        "risks": ["Support bounce"]
    }
    with pytest.raises(ValidationError):
        AIHorizonForecast(**data)


def test_technical_analysis_indicators():
    # Generate 50 sample prices
    prices = [50000 + (i * 100) for i in range(50)]
    rsi = TechnicalAnalysis.calculate_rsi(prices, period=14)
    # Strictly upward trending prices should produce high RSI
    assert rsi > 70.0

    ema20 = TechnicalAnalysis.calculate_ema(prices, 20)
    assert ema20 > 50000

    macd = TechnicalAnalysis.calculate_macd(prices)
    assert "macd" in macd
    assert "signal" in macd
    assert "histogram" in macd

    sr = TechnicalAnalysis.calculate_support_resistance(prices, prices, prices)
    assert sr["pivot"] > 0
    assert sr["resistance1"] >= sr["pivot"]
    assert sr["support1"] <= sr["pivot"]

