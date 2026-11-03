"""Validated item data and history operations, independent of Home Assistant."""
from copy import deepcopy
from datetime import date
from uuid import uuid4

from .calculator import calculate

CONFIG_FIELDS = {"name", "mode", "group", "start_date", "due_date",
                 "duration", "unit", "reminder_days"}


def _day(value):
    if not isinstance(value, str):
        raise ValueError("日期格式錯誤")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("日期請使用 YYYY-MM-DD 格式")
    return parsed


def _integer(value, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError("請輸入有效的整數")
    return value


def validate_config(raw, today):
    """Validate every write, including writes outside a selector form."""
    data = {k: v for k, v in raw.items() if k in CONFIG_FIELDS}
    for key, limit in (("name", 100), ("group", 100)):
        value = data.get(key, "")
        if not isinstance(value, str) or len(value.strip()) > limit:
            raise ValueError("名稱或分組過長")
        data[key] = value.strip()
    if not data["name"]:
        raise ValueError("請填寫名稱")
    data.setdefault("mode", "lifetime")
    if data["mode"] not in ("lifetime", "fixed"):
        raise ValueError("未知的倒數類型")
    data["reminder_days"] = _integer(data.get("reminder_days", 14), 0, 36500)
    if data["mode"] == "lifetime":
        start = _day(data["start_date"])
        if start > today:
            raise ValueError("更換日期不能晚於今天；未來期限請使用固定到期日")
        data["duration"] = _integer(data.get("duration"), 1, 36500)
        if data.get("unit") not in ("days", "months", "years"):
            raise ValueError("請選擇天、月或年")
        calculate(start, data["duration"], data["unit"], today)
        data.pop("due_date", None)
    else:
        _day(data["due_date"])
        # Tracking begins when the item is created, not each time its due date changes.
        data.setdefault("start_date", today.isoformat())
        _day(data["start_date"])
        data.pop("duration", None)
        data.pop("unit", None)
    return data


def event(kind, day, now, note="", **extra):
    if not isinstance(note, str) or len(note) > 2000:
        raise ValueError("備註最多 2000 字")
    _day(day)
    return {"id": uuid4().hex, "kind": kind, "date": day, "note": note,
            "created_at": now, **extra}


def initialize(raw, today, now):
    """Idempotently seed one baseline; retain legacy future dates on migration."""
    raw = deepcopy(raw)
    raw.setdefault("mode", "lifetime")
    raw.setdefault("group", "")
    raw.setdefault("reminder_days", 14)
    raw.setdefault("revision", 0)
    if "history" not in raw:
        kind = "replacement" if raw["mode"] == "lifetime" else "created"
        day = raw["start_date"] if kind == "replacement" else today.isoformat()
        raw["history"] = [event(kind, day, now, due_date=raw.get("due_date"),
                                note="初始紀錄")]
    return raw


def current_start(data):
    records = [r for r in data["history"] if r["kind"] == "replacement"]
    if not records:
        raise ValueError("至少需保留一筆更換紀錄")
    return max(records, key=lambda r: (r["date"], r["created_at"], r["id"]))["date"]


def values(data, today):
    if data.get("mode", "lifetime") == "lifetime":
        return calculate(_day(data["start_date"]), data["duration"], data["unit"], today)
    due = _day(data["due_date"])
    remaining = (due - today).days
    total = (due - _day(data["start_date"])).days
    percentage = round(max(0, min(100, remaining / total * 100)), 1) if total > 0 else 0
    return due, remaining, percentage


def edit_item(existing, patch, today, now):
    if patch.get("mode", existing["mode"]) != existing["mode"]:
        raise ValueError("無法變更既有項目的類型，請新增另一個項目")
    if set(patch) - CONFIG_FIELDS:
        raise ValueError("未知的設定欄位")
    config = validate_config({**existing, **patch}, today)
    result = {**deepcopy(existing), **config}
    if existing["mode"] == "lifetime" and config["start_date"] != existing["start_date"]:
        latest = max((r for r in result["history"] if r["kind"] == "replacement"),
                     key=lambda r: (r["date"], r["created_at"], r["id"]))
        latest.update(date=config["start_date"], updated_at=now)
        result["start_date"] = current_start(result)
    if existing["mode"] == "fixed":
        result["start_date"] = existing["start_date"]
        if config["due_date"] != existing["due_date"]:
            result["history"].append(event("due_changed", today.isoformat(), now,
                previous_due_date=existing["due_date"], due_date=config["due_date"]))
    result["revision"] = existing["revision"] + 1
    return result


def change_history(existing, action, today, now, day=None, note="", record_id=None):
    if existing["mode"] != "lifetime":
        raise ValueError("固定到期日項目沒有更換紀錄")
    result = deepcopy(existing)
    if action in ("add", "edit"):
        if _day(day) > today:
            raise ValueError("更換日期不能晚於今天")
        record = event("replacement", day, now, note)
    if action == "add":
        result["history"].append(record)
    elif action in ("edit", "delete"):
        target = next((r for r in result["history"]
                       if r["id"] == record_id and r["kind"] == "replacement"), None)
        if target is None:
            raise ValueError("找不到這筆更換紀錄")
        if action == "edit":
            target.update(date=day, note=note, updated_at=now)
        else:
            result["history"].remove(target)
    else:
        raise ValueError("未知的紀錄操作")
    result["start_date"] = current_start(result)
    # Verify a changed date still yields a representable calendar due date.
    values(result, today)
    result["revision"] = existing["revision"] + 1
    return result
