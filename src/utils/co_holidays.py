"""
Utility for checking whether a given date is a public holiday in Colombia.
Uses the 'holidays' package, which includes movable holidays.
"""

from datetime import date, datetime

from holidays import Colombia as co_holidays

# TODO: load start year, end year from the params config
HOLIDAYS = co_holidays(years=range(2020, 2030))


def is_holiday(dt: date | datetime) -> bool:
    if isinstance(dt, datetime):
        dt = dt.date()
    return dt in HOLIDAYS
