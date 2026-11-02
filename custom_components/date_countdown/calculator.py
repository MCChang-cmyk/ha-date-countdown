"""Calendar arithmetic independent of Home Assistant."""
from calendar import monthrange
from datetime import date, timedelta

def calculate(start: date, amount: int, unit: str, today: date):
    """Return due date, signed days remaining and bounded percentage."""
    if amount < 1 or unit not in ("days", "months", "years"):
        raise ValueError("Invalid lifetime")
    if unit == "days":
        due = start + timedelta(days=amount)
    else:
        months = amount * (12 if unit == "years" else 1)
        index = start.year * 12 + start.month - 1 + months
        year, month = divmod(index, 12)
        month += 1
        due = date(year, month, min(start.day, monthrange(year, month)[1]))
    remaining = (due - today).days
    total = (due - start).days
    return due, remaining, round(max(0, min(100, remaining / total * 100)), 1)
