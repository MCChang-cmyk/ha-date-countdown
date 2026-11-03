"""Date Countdown: persistence, native entities and a central management panel."""
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, VERSION
from .manager import SIGNAL, ensure_data, update_device_name

PLATFORMS = [Platform.SENSOR, Platform.DATE, Platform.BUTTON, Platform.BINARY_SENSOR]


async def async_setup(hass, config):
    from .websocket import async_register_commands

    await hass.http.async_register_static_paths([
        StaticPathConfig("/date_countdown_static", str(Path(__file__).parent / "frontend"), False)
    ])
    module_url = f"/date_countdown_static/date-countdown.js?v={VERSION}"
    await panel_custom.async_register_panel(
        hass, frontend_url_path="date-countdown", webcomponent_name="date-countdown-panel",
        sidebar_title="日期倒數", sidebar_icon="mdi:calendar-clock",
        module_url=module_url, require_admin=True,
    )
    frontend.add_extra_js_url(hass, module_url)
    async_register_commands(hass)
    return True


async def async_setup_entry(hass, entry):
    ensure_data(hass, entry)

    async def updated(hass, entry):
        update_device_name(hass, entry)
        async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}")
        async_dispatcher_send(hass, SIGNAL)

    @callback
    def midnight(now):
        async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}")
        async_dispatcher_send(hass, SIGNAL)

    entry.async_on_unload(entry.add_update_listener(updated))
    entry.async_on_unload(async_track_time_change(hass, midnight, hour=0, minute=0, second=0))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_dispatcher_send(hass, SIGNAL)
    return True


async def async_unload_entry(hass, entry):
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    async_dispatcher_send(hass, SIGNAL)
    return result


async def async_migrate_entry(hass, entry):
    if entry.version > 2:
        return False
    if entry.version == 1:
        ensure_data(hass, entry)
        hass.config_entries.async_update_entry(entry, version=2)
    return True
