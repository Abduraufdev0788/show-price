from datetime import datetime, time
import calendar
from typing import Optional, Tuple
import pytz


def get_user_timezone(tz_name: str = "Asia/Tashkent") -> pytz.BaseTzInfo:
    try:
        return pytz.timezone(tz_name)
    except Exception:
        return pytz.timezone("Asia/Tashkent")


def now_utc() -> datetime:
    return datetime.now(pytz.utc)


def now_user(tz_name: str = "Asia/Tashkent") -> datetime:
    tz = get_user_timezone(tz_name)
    return datetime.now(tz)


def get_day_boundaries(tz_name: str = "Asia/Tashkent") -> Tuple[datetime, datetime]:
    tz = get_user_timezone(tz_name)
    local_now = datetime.now(tz)
    start_local = tz.localize(datetime.combine(local_now.date(), time.min))
    end_local = tz.localize(datetime.combine(local_now.date(), time.max))
    return start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc)


def get_week_boundaries(tz_name: str = "Asia/Tashkent") -> Tuple[datetime, datetime]:
    tz = get_user_timezone(tz_name)
    local_now = datetime.now(tz)
    start_of_week = local_now.date() - pytz.datetime.timedelta(days=local_now.weekday())
    end_of_week = start_of_week + pytz.datetime.timedelta(days=6)
    start_local = tz.localize(datetime.combine(start_of_week, time.min))
    end_local = tz.localize(datetime.combine(end_of_week, time.max))
    return start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc)


def get_month_boundaries(
    tz_name: str = "Asia/Tashkent",
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Tuple[datetime, datetime]:
    tz = get_user_timezone(tz_name)
    local_now = datetime.now(tz)
    target_year = year or local_now.year
    target_month = month or local_now.month

    _, last_day = calendar.monthrange(target_year, target_month)
    start_local = tz.localize(datetime(target_year, target_month, 1, 0, 0, 0))
    end_local = tz.localize(datetime(target_year, target_month, last_day, 23, 59, 59, 999999))
    return start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc)


def get_prev_month_boundaries(tz_name: str = "Asia/Tashkent") -> Tuple[datetime, datetime]:
    tz = get_user_timezone(tz_name)
    local_now = datetime.now(tz)
    if local_now.month == 1:
        prev_month = 12
        prev_year = local_now.year - 1
    else:
        prev_month = local_now.month - 1
        prev_year = local_now.year

    return get_month_boundaries(tz_name, prev_year, prev_month)


def get_year_boundaries(
    tz_name: str = "Asia/Tashkent",
    year: Optional[int] = None
) -> Tuple[datetime, datetime]:
    tz = get_user_timezone(tz_name)
    local_now = datetime.now(tz)
    target_year = year or local_now.year

    start_local = tz.localize(datetime(target_year, 1, 1, 0, 0, 0))
    end_local = tz.localize(datetime(target_year, 12, 31, 23, 59, 59, 999999))
    return start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc)

