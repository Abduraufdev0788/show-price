from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models.purchase import Purchase
    from database.models.sale import Sale
    from database.models.transaction import Transaction
    from database.models.price import PriceAlert
    from database.models.ai import UserAIAnalysis


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    purchases: Mapped[List["Purchase"]] = relationship(
        "Purchase",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sales: Mapped[List["Sale"]] = relationship(
        "Sale",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    alerts: Mapped[List["PriceAlert"]] = relationship(
        "PriceAlert",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    ai_requests: Mapped[List["UserAIAnalysis"]] = relationship(
        "UserAIAnalysis",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} username={self.username}>"


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    # Narx o'zgarishi chegarasi (standart $100)
    price_threshold: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("100.00"), nullable=False)
    # Monitoring oraliq vaqti (soniyalarda)
    monitoring_interval: Mapped[int] = mapped_column(default=5, nullable=False)
    # Standart komissiya foizlari (masalan 0.1% = 0.1000)
    buy_fee_percent: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.1000"), nullable=False)
    sell_fee_percent: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.1000"), nullable=False)
    withdrawal_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    exchange_name: Mapped[str] = mapped_column(String(64), default="Binance", nullable=False)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_analysis_interval: Mapped[int] = mapped_column(default=60, nullable=False)

    # Reference price for notifications
    last_notified_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 4), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id} threshold={self.price_threshold}>"

