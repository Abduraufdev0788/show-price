from decimal import Decimal
import pytest
from utils.calculations import (
    calculate_purchase_quantity,
    calculate_sale_metrics,
    calculate_unrealized_pl,
    quantize_btc,
    quantize_usd,
)


def test_calculate_purchase_with_fee_included():
    # $100 total investment, BTC price $50,000, 1% fee
    # Fee = $100 * 0.01 = $1.00
    # Net investment = $99.00
    # BTC qty = 99 / 50000 = 0.00198000
    btc_qty, fee = calculate_purchase_quantity(
        investment_amount=Decimal("100"),
        btc_price=Decimal("50000"),
        fee_percent=Decimal("1.0"),
        includes_fee=True
    )
    assert fee == Decimal("1.0000")
    assert btc_qty == Decimal("0.00198000")


def test_calculate_purchase_with_fee_excluded():
    # $100 investment, BTC price $50,000, 1% fee excluded
    # Net investment = $100 -> BTC qty = 0.00200000
    # Fee = $1.0000
    btc_qty, fee = calculate_purchase_quantity(
        investment_amount=Decimal("100"),
        btc_price=Decimal("50000"),
        fee_percent=Decimal("1.0"),
        includes_fee=False
    )
    assert btc_qty == Decimal("0.00200000")
    assert fee == Decimal("1.0000")


def test_calculate_sale_metrics_profit():
    # Sell 0.001 BTC at $80,000 (Gross = $80.00)
    # Fee 1% = $0.80 -> Net proceeds = $79.20
    # Cost basis = $70.00
    # Gross P/L = $80.00 - $70.00 = +$10.00
    # Net P/L = $79.20 - $70.00 = +$9.20
    gross, fee, net, gross_pl, net_pl = calculate_sale_metrics(
        btc_quantity_sold=Decimal("0.00100000"),
        sale_price=Decimal("80000"),
        selling_fee_percent=Decimal("1.0"),
        allocated_cost_basis=Decimal("70.0000")
    )
    assert gross == Decimal("80.0000")
    assert fee == Decimal("0.8000")
    assert net == Decimal("79.2000")
    assert gross_pl == Decimal("10.0000")
    assert net_pl == Decimal("9.2000")


def test_calculate_sale_metrics_loss():
    # Sell 0.001 BTC at $60,000 (Gross = $60.00)
    # Fee 1% = $0.60 -> Net proceeds = $59.40
    # Cost basis = $70.00
    # Net P/L = $59.40 - $70.00 = -$10.60
    gross, fee, net, gross_pl, net_pl = calculate_sale_metrics(
        btc_quantity_sold=Decimal("0.00100000"),
        sale_price=Decimal("60000"),
        selling_fee_percent=Decimal("1.0"),
        allocated_cost_basis=Decimal("70.0000")
    )
    assert gross == Decimal("60.0000")
    assert fee == Decimal("0.6000")
    assert net == Decimal("59.4000")
    assert net_pl == Decimal("-10.6000")


def test_calculate_unrealized_pl():
    # Open 0.002 BTC, cost basis $140.00, current price $75,000, 0.1% fee
    # Market value = 0.002 * 75,000 = $150.00
    # Est fee = 150 * 0.001 = $0.15
    # Net val = $149.85
    # Unrealized P/L = 149.85 - 140.00 = +$9.85
    mkt, fee, unrealized = calculate_unrealized_pl(
        btc_quantity=Decimal("0.00200000"),
        current_price=Decimal("75000"),
        cost_basis=Decimal("140.0000"),
        estimated_fee_percent=Decimal("0.1")
    )
    assert mkt == Decimal("150.0000")
    assert fee == Decimal("0.1500")
    assert unrealized == Decimal("9.8500")

