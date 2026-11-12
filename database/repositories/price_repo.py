from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.price import PriceAlert, PriceHistory, PriceMonitorState


class PriceRepository:
    @staticmethod
    def save_price(
        session: Session,
        price: Decimal,
        symbol: str = "BTCUSDT",
        exchange: str = "Binance",
        volume: Optional[Decimal] = None
    ) -> PriceHistory:
        ph = PriceHistory(
            exchange=exchange,
            symbol=symbol,
            price=price,
            volume=volume
        )
        session.add(ph)
        session.flush()
        return ph

    @staticmethod
    def get_latest_price(session: Session, symbol: str = "BTCUSDT") -> Optional[PriceHistory]:
        stmt = (
            select(PriceHistory)
            .where(PriceHistory.symbol == symbol)
            .order_by(PriceHistory.recorded_at.desc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_or_create_monitor_state(
        session: Session,
        symbol: str = "BTCUSDT",
        initial_price: Decimal = Decimal("0")
    ) -> PriceMonitorState:
        stmt = select(PriceMonitorState).where(PriceMonitorState.symbol == symbol)
        state = session.execute(stmt).scalar_one_or_none()
        if state is None:
            state = PriceMonitorState(
                exchange="Binance",
                symbol=symbol,
                reference_price=initial_price,
                last_price=initial_price
            )
            session.add(state)
            session.flush()
        return state

    @staticmethod
    def update_monitor_state(
        session: Session,
        symbol: str,
        last_price: Decimal,
        reference_price: Optional[Decimal] = None
    ) -> None:
        stmt = select(PriceMonitorState).where(PriceMonitorState.symbol == symbol)
        state = session.execute(stmt).scalar_one_or_none()
        if state:
            state.last_price = last_price
            if reference_price is not None:
                state.reference_price = reference_price
            state.updated_at = datetime.utcnow()

    @staticmethod
    def save_alert(
        session: Session,
        user_id: int,
        previous_price: Decimal,
        current_price: Decimal,
        difference: Decimal,
        direction: str
    ) -> PriceAlert:
        alert = PriceAlert(
            user_id=user_id,
            previous_price=previous_price,
            current_price=current_price,
            difference=difference,
            direction=direction
        )
        session.add(alert)
        session.flush()
        return alert

