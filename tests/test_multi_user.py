from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.user_repo import UserRepository
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.sale_repo import SaleRepository
from services.portfolio_service import portfolio_service
from services.purchase_service import purchase_service
from services.sale_service import sale_service
from services.statistics_service import statistics_service


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


def test_complete_multi_user_isolation(session, mocker):
    # Mock price service to return static $70,000 for portfolio tests
    mocker.patch("services.portfolio_service.price_service.get_current_btc_price", return_value=Decimal("70000.00"))

    # User 1 and User 2
    user1 = UserRepository.get_or_create(session, telegram_id=101, username="alice", first_name="Alice")
    user2 = UserRepository.get_or_create(session, telegram_id=102, username="bob", first_name="Bob")

    # User 1 purchases 0.01 BTC at $60,000 ($600)
    p1, tx1 = purchase_service.register_purchase(
        session=session,
        user_id=user1.id,
        investment_amount=Decimal("600"),
        purchase_price=Decimal("60000"),
        btc_quantity=Decimal("0.01"),
        fee_percent=Decimal("0.1"),
        investment_includes_fee=True
    )

    # User 2 purchases 0.05 BTC at $50,000 ($2500)
    p2, tx2 = purchase_service.register_purchase(
        session=session,
        user_id=user2.id,
        investment_amount=Decimal("2500"),
        purchase_price=Decimal("50000"),
        btc_quantity=Decimal("0.05"),
        fee_percent=Decimal("0.1"),
        investment_includes_fee=True
    )

    # Check portfolio isolation
    port1 = portfolio_service.get_user_portfolio(session, user1.id)
    port2 = portfolio_service.get_user_portfolio(session, user2.id)

    assert port1["total_open_btc"] == Decimal("0.01000000")
    assert port1["total_open_cost_basis"] == Decimal("600.0000")

    assert port2["total_open_btc"] == Decimal("0.05000000")
    assert port2["total_open_cost_basis"] == Decimal("2500.0000")

    # User 1 sells their position
    sale1, _ = sale_service.sell_from_position(
        session=session,
        user_id=user1.id,
        purchase_id=p1.id,
        btc_quantity_sold=Decimal("0.01"),
        sale_price=Decimal("70000"),
        selling_fee_percent=Decimal("0.1")
    )

    # User 1 stats should show 1 completed trade, User 2 stats should show 0 completed trades
    stats1 = statistics_service.get_all_time_statistics(session, user1.id)
    stats2 = statistics_service.get_all_time_statistics(session, user2.id)

    assert stats1["completed_trades"] == 1
    assert stats1["net_realized_pl"] > Decimal("0")
    assert stats2["completed_trades"] == 0
    assert stats2["net_realized_pl"] == Decimal("0.0000")

    # User 2 attempts to sell User 1's purchase - MUST FAIL with ValueError
    with pytest.raises(ValueError, match="topilmadi"):
        sale_service.sell_from_position(
            session=session,
            user_id=user2.id,
            purchase_id=p1.id,
            btc_quantity_sold=Decimal("0.01"),
            sale_price=Decimal("70000")
        )

