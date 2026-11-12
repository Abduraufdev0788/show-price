from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

# Precision constants
BTC_PRECISION = Decimal("0.00000001")   # 8 decimal places
USD_PRECISION = Decimal("0.0001")       # 4 decimal places
PERCENT_PRECISION = Decimal("0.0001")   # 4 decimal places (e.g. 0.0010 = 0.1%)


def to_decimal(val: object) -> Decimal:
    """Safely convert any numeric value or string to Decimal."""
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def quantize_btc(amount: Decimal) -> Decimal:
    """Quantize to 8 decimal places (Satoshi precision)."""
    return amount.quantize(BTC_PRECISION, rounding=ROUND_HALF_UP)


def quantize_usd(amount: Decimal) -> Decimal:
    """Quantize to 4 decimal places for USD monetary precision."""
    return amount.quantize(USD_PRECISION, rounding=ROUND_HALF_UP)


def calculate_purchase_quantity(
    investment_amount: Decimal,
    btc_price: Decimal,
    fee_percent: Optional[Decimal] = None,
    flat_fee: Decimal = Decimal("0"),
    includes_fee: bool = True
) -> Tuple[Decimal, Decimal]:
    """
    Calculate BTC quantity and fee from investment amount and BTC price.
    
    If includes_fee is True:
        Total spent = investment_amount
        Fee is deducted from investment_amount before buying BTC
        net_investment = (investment_amount - flat_fee) / (1 + fee_percent/100) or fee deducted
        fee = investment_amount * (fee_percent / 100)
        net_investment = investment_amount - fee - flat_fee
        btc_qty = net_investment / btc_price
    If includes_fee is False:
        investment_amount is fully used to buy BTC
        btc_qty = investment_amount / btc_price
        fee = investment_amount * (fee_percent / 100) + flat_fee
        Total cost = investment_amount + fee
    
    Returns: (btc_quantity, purchase_fee)
    """
    investment = to_decimal(investment_amount)
    price = to_decimal(btc_price)
    fee_pct = to_decimal(fee_percent) if fee_percent is not None else Decimal("0")
    flat = to_decimal(flat_fee)

    if price <= Decimal("0"):
        raise ValueError("BTC price must be greater than zero")
    if investment <= Decimal("0"):
        raise ValueError("Investment amount must be greater than zero")

    if includes_fee:
        # fee is part of investment
        fee = quantize_usd(investment * (fee_pct / Decimal("100")) + flat)
        net_usd = investment - fee
        if net_usd <= Decimal("0"):
            raise ValueError("Fee is greater than or equal to investment amount")
        btc_qty = quantize_btc(net_usd / price)
    else:
        btc_qty = quantize_btc(investment / price)
        fee = quantize_usd(investment * (fee_pct / Decimal("100")) + flat)

    return btc_qty, fee


def calculate_sale_metrics(
    btc_quantity_sold: Decimal,
    sale_price: Decimal,
    selling_fee_percent: Decimal = Decimal("0"),
    flat_selling_fee: Decimal = Decimal("0"),
    allocated_cost_basis: Decimal = Decimal("0")
) -> Tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    """
    Calculate sale proceeds and profit/loss.
    
    Returns:
    (
        gross_sale_amount,
        selling_fee,
        net_sale_proceeds,
        gross_profit_loss,
        net_profit_loss
    )
    """
    qty = to_decimal(btc_quantity_sold)
    price = to_decimal(sale_price)
    fee_pct = to_decimal(selling_fee_percent)
    flat_fee = to_decimal(flat_selling_fee)
    cost_basis = to_decimal(allocated_cost_basis)

    gross_sale = quantize_usd(qty * price)
    selling_fee = quantize_usd(gross_sale * (fee_pct / Decimal("100")) + flat_fee)
    net_proceeds = gross_sale - selling_fee

    # Gross P/L = Gross Sale - Cost Basis
    gross_pl = gross_sale - cost_basis
    # Net P/L = Net Proceeds - Cost Basis
    net_pl = net_proceeds - cost_basis

    return (
        quantize_usd(gross_sale),
        quantize_usd(selling_fee),
        quantize_usd(net_proceeds),
        quantize_usd(gross_pl),
        quantize_usd(net_pl)
    )


def calculate_unrealized_pl(
    btc_quantity: Decimal,
    current_price: Decimal,
    cost_basis: Decimal,
    estimated_fee_percent: Decimal = Decimal("0")
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate estimated market value, estimated fee, and unrealized net profit/loss.
    
    Returns: (market_value, estimated_fee, unrealized_pnl)
    """
    qty = to_decimal(btc_quantity)
    price = to_decimal(current_price)
    cost = to_decimal(cost_basis)
    fee_pct = to_decimal(estimated_fee_percent)

    market_val = quantize_usd(qty * price)
    est_fee = quantize_usd(market_val * (fee_pct / Decimal("100")))
    net_val = market_val - est_fee
    unrealized_pnl = net_val - cost

    return quantize_usd(market_val), quantize_usd(est_fee), quantize_usd(unrealized_pnl)

