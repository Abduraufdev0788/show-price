from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from database.models.purchase import Purchase
from database.models.sale import Sale
from database.models.transaction import Transaction
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.sale_repo import SaleRepository
from database.repositories.transaction_repo import TransactionRepository
from utils.calculations import calculate_sale_metrics, quantize_btc, quantize_usd, to_decimal


class SaleService:
    @staticmethod
    def sell_from_position(
        session: Session,
        user_id: int,
        purchase_id: int,
        btc_quantity_sold: Decimal,
        sale_price: Decimal,
        selling_fee_percent: Decimal = Decimal("0"),
        flat_selling_fee: Decimal = Decimal("0"),
        sold_at: Optional[datetime] = None,
        note: Optional[str] = None
    ) -> Tuple[Sale, Purchase]:
        """Sell BTC from a specific purchase position."""
        purchase = PurchaseRepository.get_by_id(session, user_id=user_id, purchase_id=purchase_id)
        if not purchase:
            raise ValueError("Ko'rsatilgan xarid pozitsiyasi topilmadi.")

        sold_qty = quantize_btc(to_decimal(btc_quantity_sold))
        if sold_qty <= Decimal("0"):
            raise ValueError("Sotilayotgan BTC miqdori 0 dan katta bo'lishi kerak.")
        if sold_qty > purchase.remaining_btc_quantity:
            raise ValueError(
                f"Sotish uchun yetarli BTC yo'q. Mavjud: {purchase.remaining_btc_quantity} BTC, so'ralgan: {sold_qty} BTC"
            )

        price = quantize_usd(to_decimal(sale_price))

        # Calculate proportional acquisition cost
        # Total cost basis of original purchase = investment_amount
        proportion = sold_qty / purchase.btc_quantity
        allocated_cost = quantize_usd(purchase.investment_amount * proportion)

        gross, fee, net_proceeds, gross_pl, net_pl = calculate_sale_metrics(
            btc_quantity_sold=sold_qty,
            sale_price=price,
            selling_fee_percent=selling_fee_percent,
            flat_selling_fee=flat_selling_fee,
            allocated_cost_basis=allocated_cost
        )

        sale = SaleRepository.create(
            session=session,
            user_id=user_id,
            purchase_id=purchase.id,
            btc_quantity_sold=sold_qty,
            sale_price=price,
            gross_sale_amount=gross,
            selling_fee=fee,
            net_sale_proceeds=net_proceeds,
            allocated_cost_basis=allocated_cost,
            gross_profit_loss=gross_pl,
            net_profit_loss=net_pl,
            sold_at=sold_at or datetime.now(timezone.utc),
            note=note
        )

        # Update purchase remaining quantity & status
        purchase.remaining_btc_quantity = quantize_btc(purchase.remaining_btc_quantity - sold_qty)
        if purchase.remaining_btc_quantity <= Decimal("0"):
            purchase.remaining_btc_quantity = Decimal("0")
            purchase.status = "CLOSED"

        # Record transaction
        TransactionRepository.create(
            session=session,
            user_id=user_id,
            purchase_id=purchase.id,
            sale_id=sale.id,
            transaction_type="SELL",
            amount=net_proceeds,
            btc_quantity=sold_qty,
            price=price,
            fee=fee
        )

        session.flush()
        return sale, purchase

    @staticmethod
    def sell_fifo(
        session: Session,
        user_id: int,
        btc_quantity_sold: Decimal,
        sale_price: Decimal,
        selling_fee_percent: Decimal = Decimal("0"),
        flat_selling_fee: Decimal = Decimal("0"),
        sold_at: Optional[datetime] = None,
        note: Optional[str] = None
    ) -> List[Sale]:
        """Sell BTC using FIFO (First-In, First-Out) across open positions."""
        total_qty_to_sell = quantize_btc(to_decimal(btc_quantity_sold))
        open_purchases = PurchaseRepository.get_open_purchases(session, user_id=user_id)

        total_available = sum((p.remaining_btc_quantity for p in open_purchases), Decimal("0"))
        if total_qty_to_sell > total_available:
            raise ValueError(
                f"Sotish uchun portfelda yetarli BTC yo'q. Mavjud: {total_available} BTC, so'ralgan: {total_qty_to_sell} BTC"
            )

        remaining_to_sell = total_qty_to_sell
        sales_created = []

        for p in open_purchases:
            if remaining_to_sell <= Decimal("0"):
                break

            qty_from_this_purchase = min(p.remaining_btc_quantity, remaining_to_sell)
            sale, _ = SaleService.sell_from_position(
                session=session,
                user_id=user_id,
                purchase_id=p.id,
                btc_quantity_sold=qty_from_this_purchase,
                sale_price=sale_price,
                selling_fee_percent=selling_fee_percent,
                flat_selling_fee=flat_selling_fee,
                sold_at=sold_at,
                note=note
            )
            sales_created.append(sale)
            remaining_to_sell -= qty_from_this_purchase

        return sales_created


sale_service = SaleService()
