"""Pure helpers for report data. No third-party imports, so they are easy to test."""
from datetime import date, datetime, timedelta, timezone

MANILA = timezone(timedelta(hours=8))
MAX_RANGE_DAYS = 366


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Dates must look like 2026-10-04.")


def validate_range(start: str, end: str) -> tuple[date, date]:
    s, e = parse_date(start), parse_date(end)
    if e < s:
        raise ValueError("The end date must not be earlier than the start date.")
    if (e - s).days + 1 > MAX_RANGE_DAYS:
        raise ValueError(f"Choose a range of {MAX_RANGE_DAYS} days or less.")
    return s, e


def fill_days(rows: list[dict], start: date, end: date) -> list[dict]:
    """One row per day from start to end. Days with no camera data show zeros."""
    by_day = {str(r["day"]): r for r in rows}
    out, d = [], start
    while d <= end:
        r = by_day.get(d.isoformat())
        out.append({
            "day": d.isoformat(),
            "peak_inside": int((r or {}).get("peak_inside") or 0),
            "total_in": int((r or {}).get("total_in") or 0),
            "total_out": int((r or {}).get("total_out") or 0),
            "has_data": r is not None,
        })
        d += timedelta(days=1)
    return out


def summarize(days: list[dict]) -> dict:
    with_data = [d for d in days if d["has_data"]]
    busiest = max(with_data, key=lambda d: d["peak_inside"]) if with_data else None
    return {
        "days_in_range": len(days),
        "days_with_data": len(with_data),
        "total_in": sum(d["total_in"] for d in days),
        "total_out": sum(d["total_out"] for d in days),
        "peak_inside": busiest["peak_inside"] if busiest else 0,
        "busiest_day": busiest["day"] if busiest else None,
    }


def manila_bounds(start: date, end: date) -> tuple[str, str]:
    """ISO timestamps that cover whole Manila days, for filtering alerts."""
    lo = datetime(start.year, start.month, start.day, tzinfo=MANILA)
    hi = datetime(end.year, end.month, end.day, tzinfo=MANILA) + timedelta(days=1)
    return lo.isoformat(), hi.isoformat()


USERNAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789._-")


def valid_username(u: str) -> bool:
    return 3 <= len(u) <= 30 and set(u) <= USERNAME_CHARS
