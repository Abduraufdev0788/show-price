from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
from database.repositories.user_repo import UserRepository
from services.alert_service import alert_service


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


def test_price_alert_dispatch_and_thresholds(session, mocker):
    mock_bot = mocker.MagicMock()

    # Create user with $100 threshold
    user = UserRepository.get_or_create(session, telegram_id=9001)
    user.settings.price_threshold = Decimal("100.00")
    user.settings.last_notified_price = Decimal("74500.00")
    user.settings.notification_enabled = True

    # 1. Price moved to $74,550 (+$50) -> under $100 threshold -> NO alert
    sent = alert_service.check_and_dispatch_alerts(session, current_price=Decimal("74550.00"), bot_instance=mock_bot)
    assert sent == 0
    assert mock_bot.send_message.call_count == 0

    # 2. Price moved to $74,600 (+$100 from 74,500) -> threshold reached -> 1 alert sent!
    sent = alert_service.check_and_dispatch_alerts(session, current_price=Decimal("74600.00"), bot_instance=mock_bot)
    assert sent == 1
    assert mock_bot.send_message.call_count == 1
    # Check that user's reference price was updated to 74,600
    assert user.settings.last_notified_price == Decimal("74600.00")

    # 3. Same price $74,600 checked again -> NO duplicate alert
    sent = alert_service.check_and_dispatch_alerts(session, current_price=Decimal("74600.00"), bot_instance=mock_bot)
    assert sent == 0
    assert mock_bot.send_message.call_count == 1

    # 4. Price drops by $150 to $74,450 (below $74,600 by $150) -> DOWN alert sent!
    sent = alert_service.check_and_dispatch_alerts(session, current_price=Decimal("74450.00"), bot_instance=mock_bot)
    assert sent == 1
    assert mock_bot.send_message.call_count == 2
    assert user.settings.last_notified_price == Decimal("74450.00")

