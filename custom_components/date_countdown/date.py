"""Editable replacement date."""
from datetime import date
from homeassistant.components.date import DateEntity
from .entity import CountdownEntity

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ReplacementDate(entry)] if {**entry.data, **entry.options}["mode"] == "lifetime" else [])

class ReplacementDate(CountdownEntity, DateEntity):
    _attr_icon = "mdi:calendar-edit"

    def __init__(self, entry):
        super().__init__(entry, "start_date")

    @property
    def native_value(self):
        return date.fromisoformat(self.settings["start_date"])

    async def async_set_value(self, value):
        self.set_start_date(value)
