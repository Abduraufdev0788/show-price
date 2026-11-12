from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from database.models.purchase import Purchase
from database.models.transaction import Transaction
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.transaction_repo import TransactionRepository
from utils.calculations import calculate_purchase_quantity, quantize_btc, quantize_usd, to_decimal


class PurchaseService:
    @staticmethod
    def register_purchase(
        session: Session,
        user_id: int,
        investment_amount: Decimal,
        purchase_price: Decimal,
        btc_quantity: Optional[Decimal] = None,
        fee_percent: Optional[Decimal] = None,
        flat_fee: Decimal = Decimal("0"),
        investment_includes_fee: bool = True,
        purchase_date: Optional[datetime] = None,
        note: Optional[str] = None
    ) -> Tuple[Purchase, Transaction]:
        """Register a new BTC purchase with strict Decimal calculations and database consistency."""
        inv = quantize_usd(to_decimal(investment_amount))
        price = quantize_usd(to_decimal(purchase_price))

        if btc_quantity is not None and btc_quantity > Decimal("0"):
            qty = quantize_btc(to_decimal(btc_quantity))
            if fee_percent is not None:
                fee = quantize_usd(inv * (to_decimal(fee_percent) / Decimal("100")) + flat_fee)
            else:
                fee = quantize_usd(flat_fee)
        else:
            qty, fee = calculate_purchase_quantity(
                investment_amount=inv,
                btc_price=price,
                fee_percent=fee_percent,
                flat_fee=flat_fee,
                includes_fee=investment_includes_fee
            )

        purchase = PurchaseRepository.create(
            session=session,
            user_id=user_id,
            investment_amount=inv,
            investment_includes_fee=investment_includes_fee,
            purchase_price=price,
            btc_quantity=qty,
            purchase_fee=fee,
            purchase_fee_percent=fee_percent,
            purchase_date=purchase_date or datetime.now(timezone.utc),
            note=note
        )

        # Register in transactions table
        tx = TransactionRepository.create(
            session=session,
            user_id=user_id,
            purchase_id=purchase.id,
            transaction_type="BUY",
            amount=inv,
            btc_quantity=qty,
            price=price,
            fee=fee
        )

        session.flush()
        return purchase, tx


purchase_service = PurchaseService()
