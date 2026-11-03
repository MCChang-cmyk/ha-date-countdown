"""Real Home Assistant lifecycle tests (no mock entity platforms)."""
from pathlib import Path

import pytest
import pytest_asyncio

from homeassistant.core import HomeAssistant
from homeassistant import loader, auth
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import SOURCE_USER, ConfigEntries
from homeassistant.setup import async_setup_component

ROOT = Path(__file__).resolve().parents[1]


@pytest_asyncio.fixture
async def hass(tmp_path):
    (tmp_path / "custom_components").symlink_to(ROOT / "custom_components", target_is_directory=True)
    instance = HomeAssistant(str(tmp_path))
    instance.config.skip_pip = True
    loader.async_setup(instance)
    instance.config_entries = ConfigEntries(instance, {})
    await async_load_base_functionality(instance)
    instance.auth = await auth.auth_manager_from_config(instance, [], [])
    await instance.config.async_set_time_zone("Asia/Taipei")
    assert await async_setup_component(instance, "http", {"http": {
        "server_host": "127.0.0.1", "server_port": 18329}})
    assert await async_setup_component(instance, "date_countdown", {})
    yield instance
    await instance.async_stop(force=True)


async def create(hass, **patch):
    data = {"name":"測試濾心","start_date":"2026-09-02","duration":6,
            "unit":"months",**patch}
    flow = await hass.config_entries.flow.async_init(
        "date_countdown", context={"source":SOURCE_USER}, data=data)
    assert flow["type"] == "create_entry", flow
    await hass.async_block_till_done()
    return flow["result"]


async def test_full_ha_install_options_reload(hass):
    from custom_components.date_countdown.manager import settings, history, edit
    from homeassistant.helpers import entity_registry as er
    entry = await create(hass)
    registry=er.async_get(hass)
    entities=er.async_entries_for_config_entry(registry,entry.entry_id)
    assert len(entities)==6
    original={e.unique_id:e.entity_id for e in entities}
    date_entity=next(e.entity_id for e in entities if e.domain=="date")
    button_entity=next(e.entity_id for e in entities if e.domain=="button")
    await hass.services.async_call("date","set_value",
        {"entity_id":date_entity,"date":"2026-10-01"},blocking=True)
    await hass.async_block_till_done()
    assert settings(entry)["start_date"]=="2026-10-01"
    assert len(settings(entry)["history"])==1
    await hass.services.async_call("button","press",{"entity_id":button_entity},blocking=True)
    await hass.async_block_till_done()
    assert len(settings(entry)["history"])==2
    edit(hass,entry,{"name":"新版名稱","duration":12})
    await hass.async_block_till_done()
    assert entry.title=="新版名稱"
    sensor=next(e.entity_id for e in entities if e.unique_id.endswith("_days_remaining"))
    assert "history" not in hass.states.get(sensor).attributes
    assert hass.states.get(sensor).attributes["countdown_id"]==entry.entry_id
    history(hass,entry,"delete",record_id=settings(entry)["history"][-1]["id"])
    await hass.async_block_till_done()
    assert settings(entry)["start_date"]=="2026-10-01"
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(settings(entry)["history"])==1
    assert original=={e.unique_id:e.entity_id for e in er.async_entries_for_config_entry(registry,entry.entry_id)}
    options = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(options["flow_id"], user_input={
        "name":"改名","group":"淨水器","start_date":"2026-10-01",
        "duration":24,"unit":"months","reminder_days":30})
    assert result["type"]=="create_entry",result
    await hass.async_block_till_done()
    assert settings(entry)["duration"]==24
    assert len(settings(entry)["history"])==1


async def test_fixed_entry_platforms(hass):
    from homeassistant.helpers import entity_registry as er
    from custom_components.date_countdown.manager import settings, edit
    entry=await create(hass,mode="fixed",name="食品",due_date="2027-11-03")
    entities=er.async_entries_for_config_entry(er.async_get(hass),entry.entry_id)
    assert len(entities)==4
    assert not any(e.domain in ("button","date") for e in entities)
    edit(hass,entry,{"due_date":"2027-12-03"})
    await hass.async_block_till_done()
    assert settings(entry)["history"][-1]["kind"]=="due_changed"
    assert await hass.config_entries.async_remove(entry.entry_id)
    assert not er.async_entries_for_config_entry(er.async_get(hass),entry.entry_id)


async def test_legacy_migration(hass):
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers import entity_registry as er
    from custom_components.date_countdown.manager import settings
    entry = ConfigEntry(version=1,minor_version=1,domain="date_countdown",
        title="舊濾心",data={"name":"舊濾心","start_date":"2026-09-02","duration":24,"unit":"months"},
        options={"start_date":"2026-10-02"},source=SOURCE_USER,unique_id=None,
        discovery_keys={},subentries_data=[])
    await hass.config_entries.async_add(entry)
    await hass.async_block_till_done()
    assert entry.version==2
    assert settings(entry)["start_date"]=="2026-10-02"
    assert settings(entry)["history"][0]["date"]=="2026-10-02"
    assert len(er.async_entries_for_config_entry(er.async_get(hass),entry.entry_id))==6


async def test_websocket_crud_history_conflicts_and_permissions(hass):
    import aiohttp
    from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_USER
    users=[]
    for group in [GROUP_ID_ADMIN,GROUP_ID_USER]:
        user=await hass.auth.async_create_user("test",group_ids=[group])
        refresh=await hass.auth.async_create_refresh_token(user, client_id="http://localhost/")
        users.append(hass.auth.async_create_access_token(refresh))
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://127.0.0.1:18329/api/websocket") as ws:
            assert (await ws.receive_json())["type"]=="auth_required"
            await ws.send_json({"type":"auth","access_token":users[0]})
            assert (await ws.receive_json())["type"]=="auth_ok"
            counter=0
            async def call(operation,**extra):
                nonlocal counter
                counter+=1
                await ws.send_json({"id":counter,"type":"date_countdown/manage","operation":operation,**extra})
                return await ws.receive_json()
            response=await call("create",data={"name":"API 濾心","mode":"lifetime",
                "start_date":"2026-09-02","duration":6,"unit":"months"})
            assert response["success"],response
            item=response["result"]
            assert item["history_count"]==1
            response=await call("history",entry_id=item["id"],revision=item["revision"],
                data={"action":"add","day":"2026-10-01","note":"補登"})
            assert response["success"],response
            response=await call("update",entry_id=item["id"],revision=item["revision"],data={"name":"stale"})
            assert response["error"]["code"]=="stale_revision"
            response=await call("get",entry_id=item["id"])
            assert len(response["result"]["history"])==2
            revision=response["result"]["revision"]
            response=await call("delete",entry_id=item["id"],revision=revision)
            assert response["success"]
            response=await call("list")
            assert response["result"]["items"]==[]
        async with session.ws_connect("http://127.0.0.1:18329/api/websocket") as ws:
            await ws.receive_json()
            await ws.send_json({"type":"auth","access_token":users[1]})
            assert (await ws.receive_json())["type"]=="auth_ok"
            await ws.send_json({"id":1,"type":"date_countdown/manage","operation":"list"})
            response=await ws.receive_json()
            assert response["success"] is False
            assert response["error"]["code"]=="unauthorized"


async def test_data_survives_new_ha_instance(hass,tmp_path):
    """Stop HA, reload its storage in a second instance and restore entities."""
    from custom_components.date_countdown.manager import settings,history,edit
    from homeassistant.helpers import entity_registry as er
    entry=await create(hass)
    history(hass,entry,"add",day="2026-10-01",note="重啟前的更換紀錄")
    edit(hass,entry,{"duration":12,"group":"淨水器"})
    await hass.async_block_till_done()
    expected=settings(entry)
    entity_ids={e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass),entry.entry_id)}
    await hass.async_start()
    await hass.async_stop(force=True)

    second=HomeAssistant(str(tmp_path))
    second.config.skip_pip=True
    loader.async_setup(second)
    second.config_entries=ConfigEntries(second,{})
    await async_load_base_functionality(second)
    second.auth=await auth.auth_manager_from_config(second,[],[])
    await second.config.async_set_time_zone("Asia/Taipei")
    try:
        assert await async_setup_component(second,"http",{"http":{"server_host":"127.0.0.1","server_port":18329}})
        assert await async_setup_component(second,"date_countdown",{})
        restored=second.config_entries.async_get_entry(entry.entry_id)
        assert restored is not None
        assert restored.state.value == "loaded"
        await second.async_block_till_done()
        assert settings(restored)==expected
        assert entity_ids=={e.entity_id for e in er.async_entries_for_config_entry(er.async_get(second),restored.entry_id)}
        assert all(second.states.get(entity_id) for entity_id in entity_ids)
    finally:
        await second.async_stop(force=True)
