from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.user_repo import UserRepository
from services.purchase_service import purchase_service
from services.sale_service import sale_service


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_partial_and_complete_sale(session):
    user = UserRepository.get_or_create(session, telegram_id=6001)

    # Buy 0.01 BTC for $500 ($50,000 / BTC)
    purchase, _ = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("500.00"),
        purchase_price=Decimal("50000.00"),
        btc_quantity=Decimal("0.01000000"),
        fee_percent=Decimal("0")
    )

    # 1. Partial sale: sell 0.004 BTC at $60,000
    # Cost basis = 500 * (0.004 / 0.01) = $200.00
    # Gross sale = 0.004 * 60,000 = $240.00
    # Net P/L = $240 - $200 = +$40.00
    sale1, updated_p = sale_service.sell_from_position(
        session=session,
        user_id=user.id,
        purchase_id=purchase.id,
        btc_quantity_sold=Decimal("0.00400000"),
        sale_price=Decimal("60000.00"),
        selling_fee_percent=Decimal("0")
    )

    assert sale1.net_profit_loss == Decimal("40.0000")
    assert updated_p.remaining_btc_quantity == Decimal("0.00600000")
    assert updated_p.status == "OPEN"

    # 2. Attempt to sell more than remaining (0.007 BTC) -> ValueError
    with pytest.raises(ValueError, match="yetarli BTC yo'q"):
        sale_service.sell_from_position(
            session=session,
            user_id=user.id,
            purchase_id=purchase.id,
            btc_quantity_sold=Decimal("0.00700000"),
            sale_price=Decimal("60000.00")
        )

    # 3. Complete remaining sale: sell 0.006 BTC at $70,000
    # Cost basis = 500 * (0.006 / 0.01) = $300.00
    # Gross sale = 0.006 * 70,000 = $420.00
    # Net P/L = $420 - $300 = +$120.00
    sale2, updated_p2 = sale_service.sell_from_position(
        session=session,
        user_id=user.id,
        purchase_id=purchase.id,
        btc_quantity_sold=Decimal("0.00600000"),
        sale_price=Decimal("70000.00"),
        selling_fee_percent=Decimal("0")
    )

    assert sale2.net_profit_loss == Decimal("120.0000")
    assert updated_p2.remaining_btc_quantity == Decimal("0.00000000")
    assert updated_p2.status == "CLOSED"


def test_fifo_sale_across_multiple_purchases(session):
    user = UserRepository.get_or_create(session, telegram_id=6002)

    # Purchase 1: 0.01 BTC at $50,000 ($500)
    p1, _ = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("500"),
        purchase_price=Decimal("50000"),
        btc_quantity=Decimal("0.01"),
        fee_percent=Decimal("0")
    )
    # Purchase 2: 0.02 BTC at $60,000 ($1200)
    p2, _ = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("1200"),
        purchase_price=Decimal("60000"),
        btc_quantity=Decimal("0.02"),
        fee_percent=Decimal("0")
    )

    # Sell 0.015 BTC using FIFO at $70,000
    # Should take all 0.01 from p1 (closing p1)
    # And 0.005 from p2 (leaving 0.015 in p2, p2 stays OPEN)
    sales = sale_service.sell_fifo(
        session=session,
        user_id=user.id,
        btc_quantity_sold=Decimal("0.01500000"),
        sale_price=Decimal("70000.00")
    )

    assert len(sales) == 2
    assert p1.status == "CLOSED"
    assert p1.remaining_btc_quantity == Decimal("0")
    assert p2.status == "OPEN"
    assert p2.remaining_btc_quantity == Decimal("0.01500000")

