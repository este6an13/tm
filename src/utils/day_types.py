from datetime import date
from typing import Final, Literal

from src.utils.co_holidays import is_holiday

type DayType = Literal["WD", "SA", "SU", "HO"]

WD: Final = "WD"  # weekday
SA: Final = "SA"  # saturday
SH: Final = "SU"  # sunday / holiday

DAY_TYPES = [WD, SA, SH]


def get_day_type(dt: date) -> DayType:
    if is_holiday(dt) or dt.weekday() == 6:
        return SH
    elif dt.weekday() == 5:
        return SA
    else:
        return WD
