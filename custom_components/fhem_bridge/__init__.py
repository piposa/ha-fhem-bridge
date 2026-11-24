"""Home Assistant integration for the FHEM Bridge."""

import asyncio
import logging
from time import monotonic

import voluptuous as vol

from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN, PLATFORMS
from .device_config import MIGRATED, save_devices, settings
from .panel import COMMAND_FIELDS, async_setup_panel, resolve_device
from .client import BridgeError
from .runtime import CONNECTION_ERRORS, Runtime


_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass, config):
    """Register admin actions for attributes and generic commands."""

    await async_setup_panel(hass)
    target = {vol.Required("device_id"): str, vol.Optional("source"): str}

    async def get_attributes(call):
        runtime, device = resolve_device(hass, call.data["device_id"], call.data.get("source"))
        return await runtime.attributes(device)

    async def set_attribute(call):
        runtime, device = resolve_device(hass, call.data["device_id"], call.data.get("source"))
        if runtime.enhanced:
            await runtime.edit_attribute(device, call.data["attribute"], call.data["value"])
        else:
            await runtime.write(device, "set_attribute", attribute=call.data["attribute"], value=call.data["value"])

    async def invoke(call):
        runtime, device = resolve_device(hass, call.data["device_id"], call.data.get("source"))
        await runtime.write(device, "invoke", action=call.data["action"], args=call.data["args"])

    async def execute(call):
        runtime, device = resolve_device(hass, call.data["device_id"], call.data.get("source"))
        reply = await runtime.execute(
            device, call.data["kind"], call.data["command"], call.data["arguments"], inputs=call.data.get("inputs")
        )
        if call.return_response:
            return {key: value for key, value in reply.items() if key not in {"id", "ok"}}

    async_register_admin_service(
        hass, DOMAIN, "execute", execute,
        vol.Schema({**target, **COMMAND_FIELDS}),
        SupportsResponse.OPTIONAL,
    )
    async_register_admin_service(
        hass, DOMAIN, "get_attributes", get_attributes,
        vol.Schema(target), SupportsResponse.ONLY,
    )
    async_register_admin_service(
        hass, DOMAIN, "set_attribute", set_attribute,
        vol.Schema({**target, vol.Required("attribute"): str, vol.Required("value"): str}),
    )
    async_register_admin_service(
        hass, DOMAIN, "invoke", invoke,
        vol.Schema({**target, vol.Required("action"): str, vol.Optional("args", default=dict): dict}),
    )
    return True


async def async_setup_entry(hass, entry):
    """Start a bridge and expose selected entities."""
    _LOGGER.debug("Setting up bridge entry %s", entry.entry_id)
    if entry.title == entry.unique_id:
        from .config_flow import bridge_title
        hass.config_entries.async_update_entry(entry, title=bridge_title(entry.data))
    setup_started = monotonic()
    runtime = Runtime(hass, entry)
    try:
        await runtime.start()
    except CONNECTION_ERRORS as err:
        reason = str(err) if isinstance(err, BridgeError) else type(err).__name__
        raise ConfigEntryNotReady(f"FHEM Bridge connection could not be established ({reason})") from err
    unsubscribe = None
    try:
        if not entry.options.get(MIGRATED):
            save_devices(hass, entry, dict(entry.options), runtime.profiles)
            runtime.loaded_settings = settings(entry)
        entry.runtime_data = runtime
        unsubscribe = runtime.listen_for_imported_devices()
        # Removing channels must also remove their obsolete registry entities.
        registry = er.async_get(hass)
        prefix = f"{entry.unique_id}/"
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
            if entity.unique_id.startswith(prefix):
                source = entity.unique_id.removeprefix(prefix).split("/", 1)[0]
                if source not in runtime.selected:
                    registry.async_remove(entity.entity_id)
        runtime.migrate_group_devices()
        runtime.publications.reconcile_registry()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        if unsubscribe is not None:
            unsubscribe()
        await runtime.stop()
        raise
    entry.async_on_unload(unsubscribe)

    reload_scheduled = False

    async def updated(hass, changed_entry):
        nonlocal reload_scheduled
        if runtime.config_status is not None:
            runtime.update_config_status(runtime.config_status)
        if reload_scheduled or settings(changed_entry) == runtime.loaded_settings:
            return
        if await runtime.apply_permissions():
            return
        reload_scheduled = True
        hass.config_entries.async_schedule_reload(changed_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(updated))
    runtime.supervise()
    await updated(hass, entry)
    elapsed = (monotonic() - setup_started) * 1000
    setup_log = logging.getLogger("custom_components.fhem_bridge.config_flow.diagnostics")
    (setup_log.warning if elapsed >= 3000 else setup_log.debug)(
        "Bridge %s setup completed in %.0f ms", entry.entry_id, elapsed)
    _LOGGER.debug("Bridge entry %s setup complete", entry.entry_id)
    return True


async def async_unload_entry(hass, entry):
    """Unload the entities and close the bridge connection."""
    entry_id = entry.entry_id
    phase = "entity platforms"
    _LOGGER.debug("Unloading bridge entry %s: removing entity platforms", entry_id)
    try:
        if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
            _LOGGER.error("Bridge entry %s could not unload all entity platforms", entry_id)
            return False
        phase = "TLS session"
        _LOGGER.debug("Unloading bridge entry %s: stopping TLS session", entry_id)
        await entry.runtime_data.stop()
    except asyncio.CancelledError:
        _LOGGER.warning("Unloading bridge entry %s was cancelled during %s", entry_id, phase)
        raise
    _LOGGER.debug("Bridge entry %s unload complete", entry_id)
    return True


async def async_remove_entry(hass, entry):
    """Remove only the configuration notification belonging to this bridge."""
    from homeassistant.components import persistent_notification

    persistent_notification.async_dismiss(hass, f"fhem_bridge_config_{entry.entry_id}")
