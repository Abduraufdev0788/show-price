from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.purchase import Purchase
from database.models.sale import Sale
from database.repositories.sale_repo import SaleRepository
from utils.calculations import quantize_usd
from utils.timezone import (
    get_day_boundaries,
    get_week_boundaries,
    get_month_boundaries,
    get_prev_month_boundaries,
    get_year_boundaries,
)


class StatisticsService:
    @staticmethod
    def get_period_statistics(
        session: Session,
        user_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        period_label: str
    ) -> Dict[str, Any]:
        """Calculate realized financial statistics strictly scoped to user and time window."""
        sales = SaleRepository.get_sales_in_range(session, user_id, start_date, end_date)

        # Get purchases in this period for investment volume calculation
        stmt_p = select(Purchase).where(Purchase.user_id == user_id)
        if start_date:
            stmt_p = stmt_p.where(Purchase.purchase_date >= start_date)
        if end_date:
            stmt_p = stmt_p.where(Purchase.purchase_date <= end_date)
        purchases = list(session.execute(stmt_p).scalars().all())

        total_invested = sum((p.investment_amount for p in purchases), Decimal("0"))
        total_purchase_fees = sum((p.purchase_fee for p in purchases), Decimal("0"))

        total_sales_proceeds = sum((s.net_sale_proceeds for s in sales), Decimal("0"))
        gross_realized_pl = sum((s.gross_profit_loss for s in sales), Decimal("0"))
        selling_commissions = sum((s.selling_fee for s in sales), Decimal("0"))
        net_realized_pl = sum((s.net_profit_loss for s in sales), Decimal("0"))

        winning_trades = sum(1 for s in sales if s.net_profit_loss > Decimal("0"))
        losing_trades = sum(1 for s in sales if s.net_profit_loss < Decimal("0"))
        breakeven_trades = sum(1 for s in sales if s.net_profit_loss == Decimal("0"))

        return {
            "period_label": period_label,
            "completed_trades": len(sales),
            "purchases_count": len(purchases),
            "total_invested": quantize_usd(total_invested),
            "total_purchase_fees": quantize_usd(total_purchase_fees),
            "total_sales_proceeds": quantize_usd(total_sales_proceeds),
            "gross_realized_pl": quantize_usd(gross_realized_pl),
            "selling_commissions": quantize_usd(selling_commissions),
            "net_realized_pl": quantize_usd(net_realized_pl),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "breakeven_trades": breakeven_trades
        }

    @staticmethod
    def get_today_statistics(session: Session, user_id: int, user_tz: str) -> Dict[str, Any]:
        start, end = get_day_boundaries(user_tz)
        return StatisticsService.get_period_statistics(session, user_id, start, end, "BUGUN")

    @staticmethod
    def get_week_statistics(session: Session, user_id: int, user_tz: str) -> Dict[str, Any]:
        start, end = get_week_boundaries(user_tz)
        return StatisticsService.get_period_statistics(session, user_id, start, end, "USHBU HAFTA")

    @staticmethod
    def get_month_statistics(session: Session, user_id: int, user_tz: str) -> Dict[str, Any]:
        start, end = get_month_boundaries(user_tz)
        return StatisticsService.get_period_statistics(session, user_id, start, end, "BU OY")

    @staticmethod
    def get_prev_month_statistics(session: Session, user_id: int, user_tz: str) -> Dict[str, Any]:
        start, end = get_prev_month_boundaries(user_tz)
        return StatisticsService.get_period_statistics(session, user_id, start, end, "O'TGAN OY")

    @staticmethod
    def get_year_statistics(session: Session, user_id: int, user_tz: str) -> Dict[str, Any]:
        start, end = get_year_boundaries(user_tz)
        return StatisticsService.get_period_statistics(session, user_id, start, end, "BU YIL")

    @staticmethod
    def get_all_time_statistics(session: Session, user_id: int) -> Dict[str, Any]:
        return StatisticsService.get_period_statistics(session, user_id, None, None, "BUTUN DAVR")


statistics_service = StatisticsService()

