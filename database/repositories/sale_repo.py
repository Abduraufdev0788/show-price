from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.sale import Sale


class SaleRepository:
    @staticmethod
    def create(
        session: Session,
        user_id: int,
        purchase_id: Optional[int],
        btc_quantity_sold: Decimal,
        sale_price: Decimal,
        gross_sale_amount: Decimal,
        selling_fee: Decimal,
        net_sale_proceeds: Decimal,
        allocated_cost_basis: Decimal,
        gross_profit_loss: Decimal,
        net_profit_loss: Decimal,
        sold_at: Optional[datetime] = None,
        note: Optional[str] = None
    ) -> Sale:
        sale = Sale(
            user_id=user_id,
            purchase_id=purchase_id,
            btc_quantity_sold=btc_quantity_sold,
            sale_price=sale_price,
            gross_sale_amount=gross_sale_amount,
            selling_fee=selling_fee,
            net_sale_proceeds=net_sale_proceeds,
            allocated_cost_basis=allocated_cost_basis,
            gross_profit_loss=gross_profit_loss,
            net_profit_loss=net_profit_loss,
            note=note
        )
        if sold_at:
            sale.sold_at = sold_at
        session.add(sale)
        session.flush()
        return sale

    @staticmethod
    def get_by_id(session: Session, user_id: int, sale_id: int) -> Optional[Sale]:
        stmt = select(Sale).where(Sale.id == sale_id, Sale.user_id == user_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_sales_in_range(
        session: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Sale]:
        stmt = select(Sale).where(Sale.user_id == user_id)
        if start_date:
            stmt = stmt.where(Sale.sold_at >= start_date)
        if end_date:
            stmt = stmt.where(Sale.sold_at <= end_date)
        stmt = stmt.order_by(Sale.sold_at.desc())
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_all_sales(session: Session, user_id: int) -> List[Sale]:
        stmt = select(Sale).where(Sale.user_id == user_id).order_by(Sale.sold_at.desc())
        return list(session.execute(stmt).scalars().all())

