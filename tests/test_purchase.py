from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.user_repo import UserRepository
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


def test_register_purchase_valid(session):
    user = UserRepository.get_or_create(session, telegram_id=5001, username="trader1")

    # Purchase $1000 with BTC price $50,000 and 0.1% fee
    # Fee = $1.00, Net = $999.00 -> btc = 999 / 50000 = 0.01998000
    purchase, tx = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("1000.00"),
        purchase_price=Decimal("50000.00"),
        fee_percent=Decimal("0.1"),
        investment_includes_fee=True
    )

    assert purchase.id is not None
    assert purchase.status == "OPEN"
    assert purchase.investment_amount == Decimal("1000.0000")
    assert purchase.purchase_fee == Decimal("1.0000")
    assert purchase.btc_quantity == Decimal("0.01998000")
    assert purchase.remaining_btc_quantity == Decimal("0.01998000")

    assert tx.transaction_type == "BUY"
    assert tx.amount == Decimal("1000.0000")
    assert tx.btc_quantity == Decimal("0.01998000")


def test_register_purchase_with_explicit_quantity(session):
    user = UserRepository.get_or_create(session, telegram_id=5002)

    purchase, tx = purchase_service.register_purchase(
        session=session,
        user_id=user.id,
        investment_amount=Decimal("2000.00"),
        purchase_price=Decimal("80000.00"),
        btc_quantity=Decimal("0.02500000"),
        fee_percent=Decimal("0.1")
    )

    assert purchase.btc_quantity == Decimal("0.02500000")
    assert purchase.remaining_btc_quantity == Decimal("0.02500000")
    assert purchase.purchase_fee == Decimal("2.0000")

