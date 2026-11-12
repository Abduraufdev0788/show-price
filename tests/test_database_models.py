from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.models import User, UserSettings, Purchase, Sale, Transaction
from database.repositories.user_repo import UserRepository
from database.repositories.purchase_repo import PurchaseRepository
from database.repositories.sale_repo import SaleRepository


@pytest.fixture
def db_session():
    # Use SQLite in-memory for fast and isolated unit tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_user_registration_and_settings(db_session):
    # Register User 1
    user1 = UserRepository.get_or_create(db_session, telegram_id=11111, username="user_one", first_name="Ali")
    assert user1.id is not None
    assert user1.telegram_id == 11111
    assert user1.settings is not None
    assert user1.settings.price_threshold == Decimal("100.00")
    assert user1.settings.notification_enabled is True

    # Check idempotency
    same_user = UserRepository.get_or_create(db_session, telegram_id=11111)
    assert same_user.id == user1.id


def test_user_data_isolation(db_session):
    # Create two different users
    user_a = UserRepository.get_or_create(db_session, telegram_id=1001, username="user_a")
    user_b = UserRepository.get_or_create(db_session, telegram_id=1002, username="user_b")

    # User A purchases BTC
    p_a = PurchaseRepository.create(
        session=db_session,
        user_id=user_a.id,
        investment_amount=Decimal("500"),
        investment_includes_fee=True,
        purchase_price=Decimal("50000"),
        btc_quantity=Decimal("0.01"),
        purchase_fee=Decimal("0.50")
    )

    # User B purchases BTC
    p_b = PurchaseRepository.create(
        session=db_session,
        user_id=user_b.id,
        investment_amount=Decimal("1000"),
        investment_includes_fee=True,
        purchase_price=Decimal("50000"),
        btc_quantity=Decimal("0.02"),
        purchase_fee=Decimal("1.00")
    )

    # Verify User A cannot see User B's purchases
    user_a_purchases = PurchaseRepository.get_open_purchases(db_session, user_id=user_a.id)
    assert len(user_a_purchases) == 1
    assert user_a_purchases[0].id == p_a.id
    assert user_a_purchases[0].investment_amount == Decimal("500.0000")

    # Verify User B cannot see User A's purchases
    user_b_purchases = PurchaseRepository.get_open_purchases(db_session, user_id=user_b.id)
    assert len(user_b_purchases) == 1
    assert user_b_purchases[0].id == p_b.id
    assert user_b_purchases[0].investment_amount == Decimal("1000.0000")

    # User A trying to get User B's purchase by ID returns None
    hacked_purchase = PurchaseRepository.get_by_id(db_session, user_id=user_a.id, purchase_id=p_b.id)
    assert hacked_purchase is None

