from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User
    from database.models.purchase import Purchase
    from database.models.sale import Sale


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    purchase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("purchases.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    sale_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    transaction_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'BUY', 'SELL'
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    btc_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(16, 4), default=Decimal("0.0000"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    purchase: Mapped[Optional["Purchase"]] = relationship("Purchase", back_populates="transactions")
    sale: Mapped[Optional["Sale"]] = relationship("Sale", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} type={self.transaction_type} amount={self.amount}>"

