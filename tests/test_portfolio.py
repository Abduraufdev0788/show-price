from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.user_repo import UserRepository
from services.portfolio_service import portfolio_service
from services.purchase_service import purchase_service


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


def test_portfolio_metrics(session, mocker):
    mocker.patch("services.portfolio_service.price_service.get_current_btc_price", return_value=Decimal("80000.00"))

    user = UserRepository.get_or_create(session, telegram_id=7001)

    # 1. Buy 0.01 BTC at $50,000 ($500)
    purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("500.00"),
        purchase_price=Decimal("50000.00"),
        btc_quantity=Decimal("0.01000000"),
        fee_percent=Decimal("0")
    )
    # 2. Buy 0.01 BTC at $70,000 ($700)
    purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("700.00"),
        purchase_price=Decimal("70000.00"),
        btc_quantity=Decimal("0.01000000"),
        fee_percent=Decimal("0")
    )

    port = portfolio_service.get_user_portfolio(session, user_id=user.id)

    # Total open BTC = 0.02
    assert port["total_open_btc"] == Decimal("0.02000000")
    # Total cost basis = $1200
    assert port["total_open_cost_basis"] == Decimal("1200.0000")
    # Average buy price = 1200 / 0.02 = $60,000
    assert port["average_buy_price"] == Decimal("60000.0000")
    # Current market value at $80,000 = 0.02 * 80,000 = $1600.00
    assert port["total_current_market_value"] == Decimal("1600.0000")
    # Unrealized P/L (with 0.1% est fee: 1600 - 1.6 - 1200 = 398.40)
    assert port["total_unrealized_pl"] == Decimal("398.4000")

