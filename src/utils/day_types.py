from datetime import date
from typing import Final, Literal

from src.utils.co_holidays import is_holiday

type DayType = Literal["WD", "SA", "SU", "HO"]

WD: Final = "WD"  # weekday
SA: Final = "SA"  # saturday
SU: Final = "SU"  # sunday
HO: Final = "HO"  # holiday

DAY_TYPES = [WD, SA, SU, HO]


def get_day_type(dt: date) -> DayType:
    if is_holiday(dt):
        return HO
    elif dt.weekday() == 5:
        return SA
    elif dt.weekday() == 6:
        return SU
    else:
        return WD
