from datetime import datetime, timezone
from decimal import Decimal
import time
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from database.repositories.price_repo import PriceRepository
from services.binance_service import binance_service
from utils.logger import logger


class PriceService:
    def __init__(self):
        self._cached_price: Optional[Decimal] = None
        self._cached_time: float = 0
        self.cache_ttl_seconds: float = 3.0  # Fast in-memory cache for user commands

    def get_current_btc_price(self, session: Optional[Session] = None) -> Decimal:
        """
        Get latest BTC price. Uses in-memory cache if fresh (< 3s),
        otherwise fetches from Binance or DB.
        """
        now = time.time()
        if self._cached_price is not None and (now - self._cached_time) < self.cache_ttl_seconds:
            return self._cached_price

        # Fetch directly from Binance
        try:
            price = binance_service.get_current_price("BTCUSDT")
            self._cached_price = price
            self._cached_time = now
            return price
        except Exception as e:
            logger.warning(f"Failed to fetch live price from Binance: {e}")

        # Fallback to DB latest recorded price
        if session:
            latest = PriceRepository.get_latest_price(session, "BTCUSDT")
            if latest:
                self._cached_price = latest.price
                self._cached_time = now
                return latest.price

        if self._cached_price is not None:
            return self._cached_price

        raise RuntimeError("BTC narxini aniqlab bo'lmadi. Binance va ma'lumotlar bazasi mavjud emas.")

    def fetch_and_record_price(self, session: Session) -> Tuple[Decimal, Optional[Decimal]]:
        """
        Used by the worker: fetches live price, saves to PriceHistory and PriceMonitorState.
        Returns: (current_price, previous_reference_price)
        """
        price = binance_service.get_current_price("BTCUSDT")
        self._cached_price = price
        self._cached_time = time.time()

        # Save to DB history
        PriceRepository.save_price(session, price=price, symbol="BTCUSDT", exchange="Binance")

        # Update monitor state
        state = PriceRepository.get_or_create_monitor_state(session, symbol="BTCUSDT", initial_price=price)
        prev_ref = state.reference_price
        state.last_price = price
        session.flush()

        return price, prev_ref


price_service = PriceService()

