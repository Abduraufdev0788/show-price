from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.price_repo import PriceRepository
from services.price_service import PriceService


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


def test_price_service_caching(mocker):
    service = PriceService()
    mock_binance = mocker.patch("services.price_service.binance_service.get_current_price", return_value=Decimal("75000.00"))

    # First call: calls binance
    p1 = service.get_current_btc_price()
    assert p1 == Decimal("75000.00")
    assert mock_binance.call_count == 1

    # Second call within TTL: returns cache without calling binance again
    p2 = service.get_current_btc_price()
    assert p2 == Decimal("75000.00")
    assert mock_binance.call_count == 1


def test_price_service_db_fallback(session, mocker):
    service = PriceService()
    # Save a price in DB
    PriceRepository.save_price(session, price=Decimal("74000.00"), symbol="BTCUSDT")

    # Simulate Binance API error
    mocker.patch("services.price_service.binance_service.get_current_price", side_effect=RuntimeError("Binance unreachable"))

    # Call with DB session should fallback to DB price
    price = service.get_current_btc_price(session=session)
    assert price == Decimal("74000.00")

