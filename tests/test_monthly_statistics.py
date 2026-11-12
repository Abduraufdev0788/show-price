from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.user_repo import UserRepository
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


def test_monthly_statistics_calculation(session):
    user = UserRepository.get_or_create(session, telegram_id=8001)

    # Trade 1: Profitable trade
    p1, _ = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("100.00"),
        purchase_price=Decimal("50000.00"),
        btc_quantity=Decimal("0.00200000"),
        fee_percent=Decimal("1.0")  # $1 fee
    )
    sale_service.sell_from_position(
        session=session,
        user_id=user.id,
        purchase_id=p1.id,
        btc_quantity_sold=Decimal("0.00200000"),
        sale_price=Decimal("60000.00"),  # $120 gross
        selling_fee_percent=Decimal("1.0")  # $1.20 fee -> Net $118.80
    )
    # Net P/L trade 1 = $118.80 - $100.00 = +$18.80

    # Trade 2: Losing trade
    p2, _ = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("100.00"),
        purchase_price=Decimal("50000.00"),
        btc_quantity=Decimal("0.00200000"),
        fee_percent=Decimal("0")
    )
    sale_service.sell_from_position(
        session=session,
        user_id=user.id,
        purchase_id=p2.id,
        btc_quantity_sold=Decimal("0.00200000"),
        sale_price=Decimal("40000.00"),  # $80 gross
        selling_fee_percent=Decimal("0")
    )
    # Net P/L trade 2 = $80.00 - $100.00 = -$20.00

    stats = statistics_service.get_month_statistics(session, user_id=user.id, user_tz="Asia/Tashkent")

    assert stats["completed_trades"] == 2
    assert stats["winning_trades"] == 1
    assert stats["losing_trades"] == 1
    # Total net P/L = +18.80 - 20.00 = -1.20
    assert stats["net_realized_pl"] == Decimal("-1.2000")

