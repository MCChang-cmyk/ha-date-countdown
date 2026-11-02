"""Date Countdown integration."""
from homeassistant.const import Platform
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR, Platform.DATE, Platform.BUTTON, Platform.BINARY_SENSOR]

async def async_setup_entry(hass, entry):
    async def updated(hass, entry):
        async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}")
    def midnight(now):
        async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}")
    entry.async_on_unload(entry.add_update_listener(updated))
    entry.async_on_unload(async_track_time_change(hass, midnight, hour=0, minute=0, second=0))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
