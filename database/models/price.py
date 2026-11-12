from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    exchange: Mapped[str] = mapped_column(String(32), default="Binance", nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), default="BTCUSDT", index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<PriceHistory {self.symbol} {self.price} at {self.recorded_at}>"


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    previous_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # 'UP', 'DOWN'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<PriceAlert user_id={self.user_id} {self.direction} diff={self.difference}>"


class PriceMonitorState(Base):
    __tablename__ = "price_monitor_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(32), default="Binance", nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), default="BTCUSDT", unique=True, nullable=False)
    reference_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<PriceMonitorState {self.symbol} ref={self.reference_price} last={self.last_price}>"
