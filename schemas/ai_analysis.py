from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class AIHorizonForecast(BaseModel):
    forecast_horizon: Literal["1h", "4h", "24h"] = Field(
        ...,
        description="Forecast horizon period"
    )
    market_direction: Literal["bullish", "bearish", "neutral"] = Field(
        ...,
        description="Expected trend direction"
    )
    lower_price: Decimal = Field(
        ...,
        description="Lower bound of expected price range in USD"
    )
    upper_price: Decimal = Field(
        ...,
        description="Upper bound of expected price range in USD"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        ...,
        description="Confidence level of forecast"
    )
    reasoning: List[str] = Field(
        default_factory=list,
        description="Key market factors and technical indicators supporting the forecast"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Identified market risks and uncertainties"
    )

    @field_validator("upper_price")
    @classmethod
    def validate_price_bounds(cls, v: Decimal, info) -> Decimal:
        lower = info.data.get("lower_price")
        if lower is not None and v < lower:
            raise ValueError("upper_price cannot be less than lower_price")
        return v


class AIAnalysisReport(BaseModel):
    current_price: Decimal
    timestamp: str
    horizons: List[AIHorizonForecast]
    summary_uz: str = Field(
        ...,
        description="Short technical summary in Uzbek"
    )
    human_explanation_uz: Optional[str] = Field(
        default=None,
        description="Conversational, human-friendly explanation of next 1 hour scenario in plain Uzbek"
    )
