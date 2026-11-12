from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List
from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    forecast_horizon: Mapped[str] = mapped_column(String(16), nullable=False)  # '1h', '4h', '24h'
    lower_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    upper_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    market_direction: Mapped[str] = mapped_column(String(32), nullable=False)  # 'bullish', 'bearish', 'neutral'
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)  # 'low', 'medium', 'high'
    reasoning: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    risks: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    technical_indicators: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False
    )

    # Relationships
    user_requests: Mapped[List["UserAIAnalysis"]] = relationship(
        "UserAIAnalysis",
        back_populates="ai_analysis",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIAnalysis id={self.id} horizon={self.forecast_horizon} dir={self.market_direction}>"


class UserAIAnalysis(Base):
    __tablename__ = "user_ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    ai_analysis_id: Mapped[int] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ai_requests")
    ai_analysis: Mapped["AIAnalysis"] = relationship("AIAnalysis", back_populates="user_requests")

    def __repr__(self) -> str:
        return f"<UserAIAnalysis user_id={self.user_id} analysis_id={self.ai_analysis_id}>"

