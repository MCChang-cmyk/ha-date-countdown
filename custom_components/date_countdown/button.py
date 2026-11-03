"""Record replacement today."""
from homeassistant.components.button import ButtonEntity
from homeassistant.util import dt as dt_util
from .entity import CountdownEntity
from .manager import history

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ReplaceToday(entry)] if {**entry.data, **entry.options}["mode"] == "lifetime" else [])

class ReplaceToday(CountdownEntity, ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, entry):
        super().__init__(entry, "replace_today")

    async def async_press(self):
        history(self.hass, self.entry, "add", day=dt_util.now().date().isoformat())
