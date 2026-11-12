from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple


def parse_and_validate_usd(text: str) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """Parse and validate USD input from user."""
    cleaned = text.strip().replace("$", "").replace(",", "")
    try:
        val = Decimal(cleaned)
        if val <= Decimal("0"):
            return False, None, "Summa 0 dan katta bo'lishi kerak."
        if val > Decimal("1000000000"):
            return False, None, "Kiritilgan summa juda katta."
        return True, val, None
    except InvalidOperation:
        return False, None, "Iltimos, to'g'ri son kiriting (masalan: 100 yoki 100.50)."


def parse_and_validate_btc(text: str) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """Parse and validate BTC quantity input from user."""
    cleaned = text.strip().lower().replace("btc", "").replace(",", "")
    try:
        val = Decimal(cleaned)
        if val <= Decimal("0"):
            return False, None, "BTC miqdori 0 dan katta bo'lishi kerak."
        if val > Decimal("21000000"):
            return False, None, "BTC miqdori 21,000,000 dan oshishi mumkin emas."
        return True, val, None
    except InvalidOperation:
        return False, None, "Iltimos, to'g'ri BTC miqdorini kiriting (masalan: 0.005 yoki 0.00125)."


def parse_and_validate_fee_percent(text: str) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """Parse and validate fee percent (e.g. 0.1 for 0.1%)."""
    cleaned = text.strip().replace("%", "").replace(",", "")
    try:
        val = Decimal(cleaned)
        if val < Decimal("0"):
            return False, None, "Komissiya foizi 0 dan kam bo'lishi mumkin emas."
        if val > Decimal("50"):
            return False, None, "Komissiya foizi 50% dan yuqori bo'lishi mumkin emas."
        return True, val, None
    except InvalidOperation:
        return False, None, "Iltimos, to'g'ri foiz kiriting (masalan: 0.1 yoki 0.25)."


def parse_and_validate_threshold(text: str) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """Parse and validate price alert threshold in USD."""
    cleaned = text.strip().replace("$", "").replace(",", "")
    try:
        val = Decimal(cleaned)
        if val < Decimal("1"):
            return False, None, "Narx o'zgarish chegarasi kamida $1 bo'lishi kerak."
        if val > Decimal("50000"):
            return False, None, "Chegara $50,000 dan oshishi mumkin emas."
        return True, val, None
    except InvalidOperation:
        return False, None, "Iltimos, to'g'ri summa kiriting (masalan: 100 yoki 250)."

