from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from database.models.purchase import Purchase
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.sale_repo import SaleRepository
from services.price_service import price_service
from utils.calculations import calculate_unrealized_pl, quantize_btc, quantize_usd, to_decimal


class PortfolioService:
    @staticmethod
    def get_user_portfolio(session: Session, user_id: int) -> Dict[str, Any]:
        """Calculate complete live portfolio state for user."""
        open_purchases: List[Purchase] = PurchaseRepository.get_open_purchases(session, user_id)
        current_price = price_service.get_current_btc_price(session)

        total_open_btc = Decimal("0")
        total_open_cost_basis = Decimal("0")
        total_current_market_value = Decimal("0")
        total_unrealized_pl = Decimal("0")
        positions_detail = []

        for p in open_purchases:
            rem_btc = p.remaining_btc_quantity
            # Cost basis of remaining portion
            rem_cost = quantize_usd(p.investment_amount * (rem_btc / p.btc_quantity))
            mkt_val, est_fee, pos_unrealized_pl = calculate_unrealized_pl(
                btc_quantity=rem_btc,
                current_price=current_price,
                cost_basis=rem_cost,
                estimated_fee_percent=Decimal("0.1")
            )

            total_open_btc += rem_btc
            total_open_cost_basis += rem_cost
            total_current_market_value += mkt_val
            total_unrealized_pl += pos_unrealized_pl

            positions_detail.append({
                "purchase_id": p.id,
                "purchase_date": p.purchase_date,
                "purchase_price": p.purchase_price,
                "remaining_btc": rem_btc,
                "cost_basis": rem_cost,
                "market_value": mkt_val,
                "unrealized_pl": pos_unrealized_pl,
            })

        # Calculate average acquisition cost
        if total_open_btc > Decimal("0"):
            avg_buy_price = quantize_usd(total_open_cost_basis / total_open_btc)
        else:
            avg_buy_price = Decimal("0")

        # Get total realized P/L from all sales
        all_sales = SaleRepository.get_all_sales(session, user_id)
        total_realized_pl = sum((s.net_profit_loss for s in all_sales), Decimal("0"))
        total_selling_fees = sum((s.selling_fee for s in all_sales), Decimal("0"))

        return {
            "has_open_positions": len(open_purchases) > 0,
            "open_positions_count": len(open_purchases),
            "total_open_btc": quantize_btc(total_open_btc),
            "current_btc_price": current_price,
            "average_buy_price": avg_buy_price,
            "total_open_cost_basis": quantize_usd(total_open_cost_basis),
            "total_current_market_value": quantize_usd(total_current_market_value),
            "total_unrealized_pl": quantize_usd(total_unrealized_pl),
            "total_realized_pl": quantize_usd(total_realized_pl),
            "total_selling_fees": quantize_usd(total_selling_fees),
            "positions": positions_detail
        }


portfolio_service = PortfolioService()

