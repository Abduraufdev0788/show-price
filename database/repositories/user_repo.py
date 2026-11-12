from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.user import User, UserSettings


class UserRepository:
    @staticmethod
    def get_or_create(
        session: Session,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> User:
        """Get existing user or create a new one with default settings."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = session.execute(stmt).scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                is_active=True
            )
            session.add(user)
            session.flush()

            # Create default settings
            default_settings = UserSettings(
                user_id=user.id,
                price_threshold=Decimal("100.00"),
                monitoring_interval=5,
                buy_fee_percent=Decimal("0.1000"),
                sell_fee_percent=Decimal("0.1000"),
                withdrawal_fee=Decimal("0.00"),
                exchange_name="Binance",
                notification_enabled=True,
                ai_enabled=True,
                ai_analysis_interval=60
            )
            session.add(default_settings)
            session.flush()
        else:
            # Update info if changed
            if username and user.username != username:
                user.username = username
            if first_name and user.first_name != first_name:
                user.first_name = first_name

        return user

    @staticmethod
    def get_by_telegram_id(session: Session, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_settings(session: Session, user_id: int) -> Optional[UserSettings]:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_users_with_alerts_enabled(session: Session) -> List[User]:
        """Retrieve all active users who have price notifications enabled."""
        stmt = (
            select(User)
            .join(UserSettings, User.id == UserSettings.user_id)
            .where(User.is_active.is_(True), UserSettings.notification_enabled.is_(True))
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_last_notified_price(session: Session, user_id: int, price: Decimal) -> None:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        settings = session.execute(stmt).scalar_one_or_none()
        if settings:
            settings.last_notified_price = price

