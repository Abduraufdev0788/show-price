from datetime import datetime
from decimal import Decimal
import time
from typing import Any, Dict, List, Optional
import requests

from config import settings
from utils.calculations import to_decimal, quantize_usd
from utils.logger import logger


BINANCE_ENDPOINTS = [
    "https://data-api.binance.vision",
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api3.binance.com",
]


class BinanceService:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 5):
        custom_url = (base_url or settings.BINANCE_API_URL).rstrip("/")
        # Put custom_url first, followed by alternates
        self.endpoints = [custom_url] + [ep for ep in BINANCE_ENDPOINTS if ep != custom_url]
        self.timeout = timeout
        self.last_valid_price: Optional[Decimal] = None
        self.last_valid_time: Optional[float] = None
        self.stale_threshold_seconds = 60

    def _request_with_failover(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Try request across available Binance endpoints with fast failover."""
        last_error = None
        for endpoint in self.endpoints:
            url = f"{endpoint}{path}"
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    logger.warning(f"Rate limit on {endpoint}. Trying next...")
                    continue
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        raise RuntimeError("Barcha Binance serverlari bilan aloqa o'rnatib bo'lmadi.")

    def get_current_price(self, symbol: str = "BTCUSDT") -> Decimal:
        """Fetch current ticker price with automatic endpoint failover."""
        try:
            data = self._request_with_failover("/api/v3/ticker/price", {"symbol": symbol})
            price = quantize_usd(to_decimal(data["price"]))
            self.last_valid_price = price
            self.last_valid_time = time.time()
            return price
        except Exception as e:
            logger.error(f"Error fetching current price from Binance endpoints: {e}")
            if self.last_valid_price is not None and self.last_valid_time is not None:
                if (time.time() - self.last_valid_time) <= self.stale_threshold_seconds:
                    return self.last_valid_price
            raise RuntimeError(f"Binance API bilan ulanishda xatolik: {e}")

    def get_24hr_ticker(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Fetch 24-hour statistics: price change, volume, high, low."""
        data = self._request_with_failover("/api/v3/ticker/24hr", {"symbol": symbol})
        return {
            "symbol": symbol,
            "last_price": quantize_usd(to_decimal(data["lastPrice"])),
            "price_change": quantize_usd(to_decimal(data["priceChange"])),
            "price_change_percent": to_decimal(data["priceChangePercent"]),
            "high_price": quantize_usd(to_decimal(data["highPrice"])),
            "low_price": quantize_usd(to_decimal(data["lowPrice"])),
            "volume": to_decimal(data["volume"]),
            "quote_volume": to_decimal(data["quoteVolume"]),
        }

    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch historical Kline/candlestick bars."""
        raw_klines = self._request_with_failover(
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit}
        )
        results = []
        for k in raw_klines:
            results.append({
                "open_time": datetime.fromtimestamp(k[0] / 1000),
                "open": to_decimal(k[1]),
                "high": to_decimal(k[2]),
                "low": to_decimal(k[3]),
                "close": to_decimal(k[4]),
                "volume": to_decimal(k[5]),
                "close_time": datetime.fromtimestamp(k[6] / 1000),
            })
        return results


binance_service = BinanceService()
