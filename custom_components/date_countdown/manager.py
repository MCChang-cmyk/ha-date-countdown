"""One persistence path for panel, options and entity writes."""
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .model import initialize, edit_item, change_history, values

SIGNAL = f"{DOMAIN}_changed"


def settings(entry):
    return {**entry.data, **entry.options}


def clock():
    now = dt_util.now()
    return now.date(), now.isoformat()


@callback
def ensure_data(hass, entry):
    today, now = clock()
    data = settings(entry)
    initialized = initialize(data, today, now)
    if initialized != data:
        hass.config_entries.async_update_entry(entry, options=initialized)


@callback
def update_device_name(hass, entry):
    registry = dr.async_get(hass)
    device = registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    if device and device.name != entry.title:
        registry.async_update_device(device.id, name=entry.title)


@callback
def save(hass, entry, data):
    hass.config_entries.async_update_entry(entry, options=data, title=data["name"])
    update_device_name(hass, entry)
    async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}")
    async_dispatcher_send(hass, SIGNAL)


@callback
def edit(hass, entry, patch):
    today, now = clock()
    save(hass, entry, edit_item(settings(entry), patch, today, now))


@callback
def history(hass, entry, action, **kwargs):
    today, now = clock()
    save(hass, entry, change_history(settings(entry), action, today, now, **kwargs))


def summary(entry):
    data = settings(entry)
    due, remaining, percentage = values(data, dt_util.now().date())
    return {"id": entry.entry_id, **{k: v for k, v in data.items() if k != "history"},
            "due_date": due.isoformat(), "days_remaining": remaining,
            "remaining_percentage": percentage, "history_count": len(data["history"]),
            "status": ("overdue" if remaining < 0 else "due" if remaining == 0
                       else "soon" if remaining <= data["reminder_days"] else "healthy")}
