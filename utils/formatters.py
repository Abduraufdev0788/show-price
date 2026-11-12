from decimal import Decimal
from datetime import datetime
import pytz


def format_usd(amount: Decimal, include_sign: bool = False) -> str:
    """Format USD currency amount, e.g. $74,500.00 or +$12.50."""
    sign = ""
    if include_sign:
        if amount > 0:
            sign = "+"
        elif amount < 0:
            sign = "-"
        val = abs(amount)
    else:
        if amount < 0:
            sign = "-"
        val = abs(amount)

    formatted = f"{val:,.2f}"
    return f"{sign}${formatted}"


def format_btc(amount: Decimal) -> str:
    """Format BTC quantity to 8 decimal places or trimmed."""
    formatted = f"{amount:.8f}".rstrip("0").rstrip(".")
    if not formatted or formatted == "-0":
        formatted = "0"
    return f"{formatted} BTC"


def format_percent(percent: Decimal, include_sign: bool = False) -> str:
    """Format percentage, e.g. +2.45% or 0.10%."""
    sign = "+" if (include_sign and percent > 0) else ""
    return f"{sign}{percent:.2f}%"


def format_datetime(dt: datetime, user_tz: str = "Asia/Tashkent") -> str:
    """Format datetime localized to user timezone."""
    try:
        tz = pytz.timezone(user_tz)
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        local_dt = dt.astimezone(tz)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

