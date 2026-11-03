"""Authenticated management API; never expose history as entity attributes."""
import asyncio

from homeassistant.components import websocket_api
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import callback
from homeassistant.util import dt as dt_util
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .manager import SIGNAL, edit, history, settings, summary, ensure_data
from .schema import vol


def _entry(hass, entry_id):
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ValueError("找不到這個項目")
    ensure_data(hass, entry)
    return entry


def _items(hass):
    result = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        ensure_data(hass, entry)
        result.append(summary(entry))
    return result


@websocket_api.websocket_command({
    "type": "date_countdown/manage",
    vol.Required("operation"): vol.In(["list", "get", "create", "update", "history", "delete"]),
    vol.Optional("entry_id"): str,
    vol.Optional("revision"): int,
    vol.Optional("data", default={}): dict,
})
@websocket_api.require_admin
@websocket_api.async_response
async def manage(hass, connection, msg):
    """Serialize create/delete and reject stale edits from another browser."""
    async with hass.data[DOMAIN]["lock"]:
        operation = msg["operation"]
        try:
            if operation == "list":
                result = {"today": dt_util.now().date().isoformat(),
                          "items": _items(hass)}
            elif operation == "create":
                flow = await hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_USER}, data=msg["data"])
                if flow["type"] != "create_entry":
                    raise ValueError("請檢查名稱、日期與期限")
                result = summary(flow["result"])
            else:
                entry = _entry(hass, msg.get("entry_id"))
                data = settings(entry)
                if operation == "get":
                    result = {**summary(entry), "history": data["history"]}
                else:
                    if msg.get("revision") != data["revision"]:
                        connection.send_error(msg["id"], "stale_revision", "資料已在其他地方更新，請重新開啟後再試")
                        return
                    if operation == "update":
                        edit(hass, entry, msg["data"])
                    elif operation == "history":
                        payload = msg["data"]
                        if set(payload) - {"action", "day", "note", "record_id"}:
                            raise ValueError("未知的紀錄欄位")
                        history(hass, entry, **payload)
                    elif operation == "delete":
                        removed = await hass.config_entries.async_remove(entry.entry_id)
                        if not removed:
                            raise ValueError("項目尚未刪除，請稍後重試")
                    result = True if operation == "delete" else summary(entry)
        except (ValueError, OverflowError, KeyError, TypeError) as err:
            connection.send_error(msg["id"], "invalid_input", str(err))
            return
        connection.send_result(msg["id"], result)


@websocket_api.websocket_command({"type": "date_countdown/subscribe"})
@websocket_api.require_admin
@callback
def subscribe(hass, connection, msg):
    @callback
    def changed():
        connection.send_event(msg["id"], {})
    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL, changed)
    connection.send_result(msg["id"])


@callback
def async_register_commands(hass):
    hass.data.setdefault(DOMAIN, {})["lock"] = asyncio.Lock()
    websocket_api.async_register_command(hass, manage)
    websocket_api.async_register_command(hass, subscribe)
