"""Shared entity behavior."""
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util
from .model import values
from .manager import edit, settings
from .const import DOMAIN

class CountdownEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry, key):
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name=entry.title,
            manufacturer="Date Countdown", model="Date Countdown",
        )

    @property
    def settings(self):
        return settings(self.entry)

    @property
    def values(self):
        return values(self.settings, dt_util.now().date())

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, f"{DOMAIN}_{self.entry.entry_id}", self.async_write_ha_state))

    def set_start_date(self, value):
        edit(self.hass, self.entry, {"start_date": value.isoformat()})
