from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.transaction import Transaction


class TransactionRepository:
    @staticmethod
    def create(
        session: Session,
        user_id: int,
        transaction_type: str,
        amount: Decimal,
        btc_quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        purchase_id: Optional[int] = None,
        sale_id: Optional[int] = None
    ) -> Transaction:
        tx = Transaction(
            user_id=user_id,
            purchase_id=purchase_id,
            sale_id=sale_id,
            transaction_type=transaction_type,
            amount=amount,
            btc_quantity=btc_quantity,
            price=price,
            fee=fee
        )
        session.add(tx)
        session.flush()
        return tx

    @staticmethod
    def get_user_transactions(session: Session, user_id: int, limit: int = 20) -> List[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(session.execute(stmt).scalars().all())

