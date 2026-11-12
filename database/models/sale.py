from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User
    from database.models.purchase import Purchase
    from database.models.transaction import Transaction


class Sale(Base):
    __tablename__ = "sales"

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
    btc_quantity_sold: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    gross_sale_amount: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    selling_fee: Mapped[Decimal] = mapped_column(Numeric(16, 4), default=Decimal("0.0000"), nullable=False)
    net_sale_proceeds: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    allocated_cost_basis: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    gross_profit_loss: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    net_profit_loss: Mapped[Decimal] = mapped_column(Numeric(16, 4), nullable=False)
    sold_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sales")
    purchase: Mapped[Optional["Purchase"]] = relationship("Purchase", back_populates="sales")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="sale")

    def __repr__(self) -> str:
        return f"<Sale id={self.id} user_id={self.user_id} qty={self.btc_quantity_sold} net_pl={self.net_profit_loss}>"

