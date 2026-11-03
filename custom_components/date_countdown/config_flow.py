"""Native HA configuration, also used when creating an item from the panel."""
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .schema import vol
from .manager import clock, settings
from .model import initialize, validate_config, edit_item


def schema(defaults, mode):
    fields = {
        vol.Required("name", default=defaults.get("name", "")): selector.TextSelector(),
        vol.Optional("group", default=defaults.get("group", "")): selector.TextSelector(),
    }
    if mode == "lifetime":
        fields.update({
            vol.Required("start_date", default=defaults.get("start_date", dt_util.now().date().isoformat())): selector.DateSelector(),
            vol.Required("duration", default=defaults.get("duration", 6)): vol.All(vol.Coerce(int), vol.Range(min=1, max=36500)),
            vol.Required("unit", default=defaults.get("unit", "months")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["days", "months", "years"], translation_key="unit")),
        })
    else:
        fields[vol.Required("due_date", default=defaults.get("due_date", dt_util.now().date().isoformat()))] = selector.DateSelector()
    fields[vol.Required("reminder_days", default=defaults.get("reminder_days", 14))] = vol.All(vol.Coerce(int), vol.Range(min=0, max=36500))
    return vol.Schema(fields)


class CountdownConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return await self._form(user_input.get("mode", "lifetime"), user_input)
        return self.async_show_menu(step_id="user", menu_options=["lifetime", "fixed"])

    async def async_step_lifetime(self, user_input=None):
        return await self._form("lifetime", user_input)

    async def async_step_fixed(self, user_input=None):
        return await self._form("fixed", user_input)

    async def _form(self, mode, user_input):
        errors = {}
        if user_input is not None:
            try:
                today, now = clock()
                data = initialize(validate_config({**user_input, "mode": mode}, today), today, now)
            except (ValueError, OverflowError, KeyError, TypeError):
                errors["base"] = "invalid_settings"
            else:
                return self.async_create_entry(title=data["name"], data=data)
        return self.async_show_form(step_id=mode, data_schema=schema(user_input or {}, mode), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CountdownOptionsFlow()


class CountdownOptionsFlow(config_entries.OptionsFlow):
    def __init__(self):
        self._revision = None

    async def async_step_init(self, user_input=None):
        current = settings(self.config_entry)
        if self._revision is None:
            self._revision = current["revision"]
        errors = {}
        if user_input is not None:
            if self._revision != current["revision"]:
                return self.async_abort(reason="stale_revision")
            try:
                today, now = clock()
                data = edit_item(current, user_input, today, now)
            except (ValueError, OverflowError, KeyError, TypeError):
                errors["base"] = "invalid_settings"
            else:
                self.hass.config_entries.async_update_entry(self.config_entry, title=data["name"])
                return self.async_create_entry(title="", data=data)
        return self.async_show_form(step_id="init",
            data_schema=schema({**current, **(user_input or {})}, current["mode"]), errors=errors)
