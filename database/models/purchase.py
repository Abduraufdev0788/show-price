from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User
    from database.models.sale import Sale
    from database.models.transaction import Transaction


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    investment_amount: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    investment_includes_fee: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    btc_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    remaining_btc_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    purchase_fee: Mapped[Decimal] = mapped_column(Numeric(16, 4), default=Decimal("0.0000"), nullable=False)
    purchase_fee_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    purchase_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True, nullable=False)  # 'OPEN', 'CLOSED'
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="purchases")
    sales: Mapped[List["Sale"]] = relationship("Sale", back_populates="purchase")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="purchase")

    def __repr__(self) -> str:
        return f"<Purchase id={self.id} user_id={self.user_id} qty={self.btc_quantity} status={self.status}>"

