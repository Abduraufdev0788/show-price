from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.purchase import Purchase


class PurchaseRepository:
    @staticmethod
    def create(
        session: Session,
        user_id: int,
        investment_amount: Decimal,
        investment_includes_fee: bool,
        purchase_price: Decimal,
        btc_quantity: Decimal,
        purchase_fee: Decimal,
        purchase_fee_percent: Optional[Decimal] = None,
        purchase_date: Optional[datetime] = None,
        note: Optional[str] = None
    ) -> Purchase:
        purchase = Purchase(
            user_id=user_id,
            investment_amount=investment_amount,
            investment_includes_fee=investment_includes_fee,
            purchase_price=purchase_price,
            btc_quantity=btc_quantity,
            remaining_btc_quantity=btc_quantity,
            purchase_fee=purchase_fee,
            purchase_fee_percent=purchase_fee_percent,
            status="OPEN",
            note=note
        )
        if purchase_date:
            purchase.purchase_date = purchase_date
        session.add(purchase)
        session.flush()
        return purchase

    @staticmethod
    def get_by_id(session: Session, user_id: int, purchase_id: int) -> Optional[Purchase]:
        stmt = select(Purchase).where(Purchase.id == purchase_id, Purchase.user_id == user_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_open_purchases(session: Session, user_id: int) -> List[Purchase]:
        """Get all open purchases for user ordered by purchase_date ASC for FIFO."""
        stmt = (
            select(Purchase)
            .where(
                Purchase.user_id == user_id,
                Purchase.status == "OPEN",
                Purchase.remaining_btc_quantity > Decimal("0")
            )
            .order_by(Purchase.purchase_date.asc())
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_purchases(session: Session, user_id: int) -> List[Purchase]:
        stmt = (
            select(Purchase)
            .where(Purchase.user_id == user_id)
            .order_by(Purchase.purchase_date.desc())
        )
        return list(session.execute(stmt).scalars().all())

