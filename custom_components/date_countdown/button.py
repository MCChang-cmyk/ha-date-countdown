"""Record replacement today."""
from homeassistant.components.button import ButtonEntity
from homeassistant.util import dt as dt_util
from .entity import CountdownEntity

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ReplaceToday(entry)])

class ReplaceToday(CountdownEntity, ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, entry):
        super().__init__(entry, "replace_today")

    async def async_press(self):
        self.set_start_date(dt_util.now().date())
