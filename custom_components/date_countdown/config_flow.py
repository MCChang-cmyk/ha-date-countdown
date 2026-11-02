"""UI setup and options."""
from datetime import date
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util
from .calculator import calculate
from .const import DOMAIN

def schema(defaults, include_name=False):
    fields = {}
    if include_name:
        fields[vol.Required("name")] = selector.TextSelector()
    fields.update({
        vol.Required("start_date", default=defaults.get("start_date", dt_util.now().date().isoformat())): selector.DateSelector(),
        vol.Required("duration", default=defaults.get("duration", 6)): vol.All(vol.Coerce(int), vol.Range(min=1, max=36500)),
        vol.Required("unit", default=defaults.get("unit", "months")): selector.SelectSelector(
            selector.SelectSelectorConfig(options=["days", "months", "years"], translation_key="unit")),
    })
    return vol.Schema(fields)

def valid(data):
    try:
        calculate(date.fromisoformat(data["start_date"]), data["duration"], data["unit"], dt_util.now().date())
        return bool(data.get("name", "item").strip())
    except (ValueError, OverflowError):
        return False

class CountdownConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if valid(user_input):
                return self.async_create_entry(title=user_input["name"].strip(), data=user_input)
            errors["base"] = "invalid_settings"
        return self.async_show_form(step_id="user", data_schema=schema(user_input or {}, True), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CountdownOptionsFlow()

class CountdownOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if valid(user_input):
                return self.async_create_entry(title="", data=user_input)
            errors["base"] = "invalid_settings"
        defaults = {**self.config_entry.data, **self.config_entry.options, **(user_input or {})}
        return self.async_show_form(step_id="init", data_schema=schema(defaults), errors=errors)
