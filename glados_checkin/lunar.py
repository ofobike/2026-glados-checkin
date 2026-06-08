"""Lunar-calendar helpers used by countdown events.

Prefer the well-maintained ``lunar_python`` package when available, and keep a
small 1900-2100 fallback table so existing deployments do not break if the
extra package is missing.
"""

from datetime import date, timedelta
from typing import Final

try:
    from lunar_python import Lunar
except ImportError:  # pragma: no cover - exercised when optional dependency is absent
    Lunar = None


LUNAR_START_YEAR = 1900
LUNAR_END_YEAR = 2100
LUNAR_BASE_DATE = date(1900, 1, 31)

LUNAR_INFO = [
    0x04BD8, 0x04AE0, 0x0A570, 0x054D5, 0x0D260, 0x0D950, 0x16554, 0x056A0, 0x09AD0, 0x055D2,
    0x04AE0, 0x0A5B6, 0x0A4D0, 0x0D250, 0x1D255, 0x0B540, 0x0D6A0, 0x0ADA2, 0x095B0, 0x14977,
    0x04970, 0x0A4B0, 0x0B4B5, 0x06A50, 0x06D40, 0x1AB54, 0x02B60, 0x09570, 0x052F2, 0x04970,
    0x06566, 0x0D4A0, 0x0EA50, 0x06E95, 0x05AD0, 0x02B60, 0x186E3, 0x092E0, 0x1C8D7, 0x0C950,
    0x0D4A0, 0x1D8A6, 0x0B550, 0x056A0, 0x1A5B4, 0x025D0, 0x092D0, 0x0D2B2, 0x0A950, 0x0B557,
    0x06CA0, 0x0B550, 0x15355, 0x04DA0, 0x0A5B0, 0x14573, 0x052B0, 0x0A9A8, 0x0E950, 0x06AA0,
    0x0AEA6, 0x0AB50, 0x04B60, 0x0AAE4, 0x0A570, 0x05260, 0x0F263, 0x0D950, 0x05B57, 0x056A0,
    0x096D0, 0x04DD5, 0x04AD0, 0x0A4D0, 0x0D4D4, 0x0D250, 0x0D558, 0x0B540, 0x0B6A0, 0x195A6,
    0x095B0, 0x049B0, 0x0A974, 0x0A4B0, 0x0B27A, 0x06A50, 0x06D40, 0x0AF46, 0x0AB60, 0x09570,
    0x04AF5, 0x04970, 0x064B0, 0x074A3, 0x0EA50, 0x06B58, 0x055C0, 0x0AB60, 0x096D5, 0x092E0,
    0x0C960, 0x0D954, 0x0D4A0, 0x0DA50, 0x07552, 0x056A0, 0x0ABB7, 0x025D0, 0x092D0, 0x0CAB5,
    0x0A950, 0x0B4A0, 0x0BAA4, 0x0AD50, 0x055D9, 0x04BA0, 0x0A5B0, 0x15176, 0x052B0, 0x0A930,
    0x07954, 0x06AA0, 0x0AD50, 0x05B52, 0x04B60, 0x0A6E6, 0x0A4E0, 0x0D260, 0x0EA65, 0x0D530,
    0x05AA0, 0x076A3, 0x096D0, 0x04AFB, 0x04AD0, 0x0A4D0, 0x1D0B6, 0x0D250, 0x0D520, 0x0DD45,
    0x0B5A0, 0x056D0, 0x055B2, 0x049B0, 0x0A577, 0x0A4B0, 0x0AA50, 0x1B255, 0x06D20, 0x0ADA0,
    0x14B63, 0x09370, 0x049F8, 0x04970, 0x064B0, 0x168A6, 0x0EA50, 0x06B20, 0x1A6C4, 0x0AAE0,
    0x0A2E0, 0x0D2E3, 0x0C960, 0x0D557, 0x0D4A0, 0x0DA50, 0x05D55, 0x056A0, 0x0A6D0, 0x055D4,
    0x052D0, 0x0A9B8, 0x0A950, 0x0B4A0, 0x0B6A6, 0x0AD50, 0x055A0, 0x0ABA4, 0x0A5B0, 0x052B0,
    0x0B273, 0x06930, 0x07337, 0x06AA0, 0x0AD50, 0x14B55, 0x04B60, 0x0A570, 0x054E4, 0x0D160,
    0x0E968, 0x0D520, 0x0DAA0, 0x16AA6, 0x056D0, 0x04AE0, 0x0A9D4, 0x0A2D0, 0x0D150, 0x0F252,
    0x0D520,
]


class BirthdayCalculator:
    """Calculate the Gregorian date for a recurring lunar birthday."""

    def __init__(self, lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool = False):
        self.lunar_year: Final = lunar_year
        self.lunar_month: Final = lunar_month
        self.lunar_day: Final = lunar_day
        self.is_leap: Final = is_leap

    def get_solar_date(self, target_lunar_year: int) -> date:
        """Return the Gregorian date of this birthday in a target lunar year."""
        return lunar_to_solar(
            target_lunar_year,
            self.lunar_month,
            self.lunar_day,
            leap=self.is_leap,
        )

    def get_age(self, target_lunar_year: int) -> int:
        """Return the age reached in the target lunar year."""
        return max(0, target_lunar_year - self.lunar_year)


def _year_info(year):
    if not (LUNAR_START_YEAR <= year <= LUNAR_END_YEAR):
        raise ValueError(f"lunar year out of range: {year}")
    return LUNAR_INFO[year - LUNAR_START_YEAR]


def leap_month(year):
    """Return the leap lunar month number, or 0 if the year has none."""
    return _year_info(year) & 0xF


def leap_month_days(year):
    """Return days in the leap month, or 0 if the year has no leap month."""
    if not leap_month(year):
        return 0
    return 30 if (_year_info(year) & 0x10000) else 29


def lunar_month_days(year, month):
    """Return days in a normal lunar month."""
    if not 1 <= month <= 12:
        raise ValueError(f"lunar month out of range: {month}")
    return 30 if (_year_info(year) & (0x10000 >> month)) else 29


def lunar_year_days(year):
    """Return total days in a lunar year."""
    total = 348
    info = _year_info(year)
    for idx in range(12):
        if info & (0x8000 >> idx):
            total += 1
    return total + leap_month_days(year)


def lunar_to_solar(year, month, day, leap=False):
    """Convert a lunar date to a Gregorian date."""
    if Lunar is not None:
        lunar_month = -month if leap else month
        lunar = Lunar.fromYmd(year, lunar_month, day)
        solar = lunar.getSolar()
        return date(solar.getYear(), solar.getMonth(), solar.getDay())

    if day < 1:
        raise ValueError(f"lunar day out of range: {day}")

    max_day = leap_month_days(year) if leap else lunar_month_days(year, month)
    if leap and leap_month(year) != month:
        raise ValueError(f"lunar year {year} has no leap month {month}")
    if day > max_day:
        raise ValueError(f"lunar day out of range: {day}")

    offset = 0
    for y in range(LUNAR_START_YEAR, year):
        offset += lunar_year_days(y)

    for m in range(1, month):
        offset += lunar_month_days(year, m)
        if leap_month(year) == m:
            offset += leap_month_days(year)

    if leap:
        offset += lunar_month_days(year, month)

    offset += day - 1
    return LUNAR_BASE_DATE + timedelta(days=offset)
