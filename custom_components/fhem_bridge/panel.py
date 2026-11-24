"""HA device configuration panel and its authenticated commands."""

import asyncio
from hashlib import sha256
import json
import logging
from pathlib import Path

import voluptuous as vol
import yaml

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import area_registry as ar, label_registry as lr

from .client import BridgeError
from .const import DOMAIN, PANEL_PATH
from .config_flow import DeviceOptions, TECHNICAL_TYPES
from .diagnostics import diagnostics
from .device_config import CONF_LOGS, PERMISSIONS, device_subentries, settings, update_permissions
from .groups import member_index
from .publications import (
    command_feedback, command_modes, device_class, needed_readings, rule_matches, shareable_class, template_assignment,
)

from .thermostat import read_week, schedule_family, write_week
from .publication_schema import ITEM_SCHEMA, SENSOR_CLASSES, SENSOR_STATE_CLASSES
from .template_library import MAX_FILE_SIZE, matched_rule, model_of, template_role, template_role_id

_LOGGER = logging.getLogger(__name__)

INPUTS = vol.All([vol.Any(None, str, int, float)], vol.Length(max=256))

COMMAND_FIELDS = {
    vol.Required("kind"): vol.In(("set", "get")),
    vol.Required("command"): str,
    vol.Optional("arguments", default=list): [vol.Any(str, int, float)],
    vol.Optional("inputs"): INPUTS,
}


def resolve_device(hass, device_id, source=None, bridge_identifier=None):
    """Resolve a HA registry ID to a loaded bridge and FHEM identifier."""
    device = dr.async_get(hass).async_get(device_id)
    if device is not None:
        owner = getattr(device, "config_entry_id", None)
        for entry_id in (owner,) if owner else device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is None or entry.domain != DOMAIN or getattr(entry, "runtime_data", None) is None:
                continue
            prefix = f"{entry.unique_id}/"
            for domain, identifier in device.identifiers:
                if domain == DOMAIN and identifier.startswith(prefix):
                    runtime = entry.runtime_data
                    target = identifier.removeprefix(prefix)
                    return resolve_source(runtime, target, source)
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            continue
        if (target := runtime.device_aliases.get(device_id)) in runtime.active:
            return resolve_source(runtime, target, source)
        prefix = f"{entry.unique_id}/"
        if bridge_identifier and bridge_identifier.startswith(prefix):
            target = bridge_identifier.removeprefix(prefix)
            if runtime.group_sources(target):
                return resolve_source(runtime, target, source)
    raise HomeAssistantError("Select a device from the FHEM Bridge integration")


def resolve_source(runtime, target, source):
    sources = runtime.group_sources(runtime.device_key(target))
    if source is None:
        source = target if target in sources else next(iter(sources), None)
    if source not in sources:
        raise HomeAssistantError("The selected FHEM channel is not available on this device")
    return runtime, source


async def async_setup_panel(hass):
    """Serve the bundled device panel without a separate frontend install."""
    panel_file = Path(__file__).with_name("device-panel.js")
    panel_bytes = await hass.async_add_executor_job(panel_file.read_bytes)
    digest = sha256(panel_bytes).hexdigest()[:16]
    url = f"/fhem_bridge_panel/{digest}.js"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(url, str(panel_file), True),
            StaticPathConfig("/fhem_bridge_panel/codemirror-5.65.13",
                             str(panel_file.with_name("codemirror")), True),
        ]
    )
    await panel_custom.async_register_panel(
        hass, PANEL_PATH, "fhem-bridge-device-panel", module_url=url, require_admin=True
    )
    frontend.add_extra_js_url(hass, url)
    websocket_api.async_register_command(hass, websocket_device)
    websocket_api.async_register_command(hass, websocket_config_status)
    websocket_api.async_register_command(hass, websocket_schedule)
    websocket_api.async_register_command(hass, websocket_device_options)
    websocket_api.async_register_command(hass, websocket_diagnostics)
    websocket_api.async_register_command(hass, websocket_publications)
    websocket_api.async_register_command(hass, websocket_templates)
    websocket_api.async_register_command(hass, websocket_command_scripts)
    websocket_api.async_register_command(hass, websocket_import)


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/import",
    vol.Required("entry_id"): str,
    vol.Required("op"): vol.In(("catalog", "areas", "commit", "devices", "group_preview", "group_commit")),
    vol.Optional("selected"): {str: vol.All([str], vol.Length(min=1))},
    vol.Optional("room_hints"): {str: [str]},
    vol.Optional("assignments"): {str: {vol.Required("area"): str, vol.Required("labels"): [str]}},
    vol.Optional("keys"): [str],
    vol.Optional("anchor"): str,
    vol.Optional("members"): [str],
    vol.Optional("import_channels", default=True): bool,
    vol.Optional("review"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_import(hass, connection, message):
    """Read the catalog, validate an import, or resolve newly registered HA devices."""
    entry = hass.config_entries.async_get_entry(message["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        raise HomeAssistantError("FHEM Bridge not found")
    runtime = getattr(entry, "runtime_data", None)
    operation = message["op"]
    if operation == "devices":
        registry = dr.async_get(hass)
        devices = {}
        keys = set(message.get("keys", ()))
        if runtime and runtime.connected and settings(entry) == runtime.loaded_settings:
            for sub in device_subentries(entry):
                key = sub.data["key"]
                if key not in keys:
                    continue
                identifier = runtime.identifier(key)
                device = registry.async_get_device_by_identifier((DOMAIN, identifier), entry.entry_id)
                if device:
                    devices[key] = {"id": device.id, "identifier": identifier}
        connection.send_result(message["id"], devices)
        return
    if runtime is None or not runtime.connected:
        raise HomeAssistantError("FHEM Bridge is offline")
    try:
        catalog = await runtime.inventory()
    except CONNECTION_ERRORS as err:
        raise HomeAssistantError("FHEM catalog is unavailable") from err
    flow = DeviceOptions()
    flow.hass, flow.handler, flow.runtime = hass, entry.entry_id, runtime
    flow.prepare_catalog(catalog)
    installed, _ = flow.saved_selection
    available = flow.catalog.keys() - installed
    groups = flow.import_groups(available)
    if operation == "catalog":
        connection.send_result(message["id"], {
            "definitions": [
                {"id": key, "name": item["name"], "alias": item.get("alias"), "type": item["type"],
                 "model": item.get("model"), "rooms": sorted(flow._rooms(item)), "installed": key in installed,
                 "technical": item["type"] in TECHNICAL_TYPES, "address": item.get("address")}
                for key, item in flow.catalog.items()
            ],
            "groups": groups,
            "saved_groups": list(flow.groups.values()),
        })
        return

    if operation in ("group_preview", "group_commit"):
        review = group_review(hass, flow, message)
        if operation == "group_preview":
            connection.send_result(message["id"], review)
            return
        if message.get("review") != review["review"]:
            connection.send_result(message["id"], {"error": "group_changed"})
            return
        if error := import_assignments(flow, review["rows"], message.get("assignments", {}), preserve=True):
            connection.send_result(message["id"], {"error": error})
            return
        if flow.write_selection() is None:
            connection.send_result(message["id"], {"error": "group_changed"})
            return
        connection.send_result(message["id"], {"target": review["target"]})
        return

    selected = message.get("selected", {})
    if not selected:
        raise HomeAssistantError("Select at least one FHEM device")
    used = set()
    for option, members in selected.items():
        group = groups.get(option)
        if group:
            expected = set(group["members"])
            if expected != set(members) or len(expected) != len(members):
                raise HomeAssistantError("The FHEM catalog changed. Refresh the selection.")
            key = option.removeprefix("group:")
            if any(other != key and expected & set(saved["members"]) for other, saved in flow.groups.items()):
                raise HomeAssistantError("An imported channel belongs to another group. Use manual grouping.")
            flow.groups[key] = group
        elif option in available and members == [option]:
            key, expected = option, {option}
        else:
            raise HomeAssistantError("The FHEM catalog changed. Refresh the selection.")
        if used & expected:
            raise HomeAssistantError("A FHEM channel was selected more than once")
        used.update(expected)
        flow.devices.update(expected)
        flow.area_room_hints[key] = set(message.get("room_hints", {}).get(option, ()))

    imported_groups = {key: members for key, members in flow._selected_groups().items()
                       if used.intersection(members)}
    _, _, _, rows = flow.area_fields(keys=imported_groups)
    imported = [{"key": key, "name": flow.catalog[flow.groups.get(key, {}).get("primary", members[0])]["name"]}
                for key, members in imported_groups.items()]
    if operation == "areas":
        connection.send_result(message["id"], {"rows": rows, "devices": imported})
        return
    if error := import_assignments(flow, rows, message.get("assignments", {})):
        connection.send_result(message["id"], {"error": error})
        return
    if flow.write_selection() is None:
        raise HomeAssistantError("The import selection changed. Refresh the selection.")
    connection.send_result(message["id"], {"devices": imported})


def import_assignments(flow, rows, assignments, *, preserve=False):
    keys = {row["key"] for row in rows}
    if keys != assignments.keys():
        return "invalid_assignment"
    _, errors, targets, _ = flow.area_fields({
        field: value for row in rows for field, value in (
            (row["area_field"], assignments[row["key"]]["area"]),
            (row["labels_field"], assignments[row["key"]]["labels"]),
        )
    }, keys=keys)
    if errors:
        return errors["base"]
    if not preserve:
        flow.import_areas.clear()
        flow.import_labels.clear()
    flow.import_areas.update({key: choice for key, (choice, _) in targets.items()})
    flow.import_labels.update({key: labels for key, (_, labels) in targets.items()})
    return None


def group_review(hass, flow, message):
    """Build the proposed group and its registry effects without saving anything."""
    anchor = message.get("anchor")
    members = set(message.get("members", ()))
    if anchor not in flow.catalog or anchor in members or not members <= flow.catalog.keys():
        raise HomeAssistantError("The FHEM catalog changed. Refresh the selection.")
    key = flow.group_key(anchor)
    current = flow.groups.get(key)
    if not members and not current:
        raise HomeAssistantError("Select at least one channel")
    importing = message.get("import_channels", True)
    affected = members | {anchor} | set((current or {}).get("members", ()))
    if not importing and affected.intersection(flow.devices | flow.missing):
        raise HomeAssistantError("The selection already contains imported channels")

    # Keep unavailable channels in a group being edited. An explicit dissolution clears it.
    if members and current:
        members.update(set(current["members"]) - flow.catalog.keys())
    old_index = member_index(flow.groups, flow.devices)
    flow.set_manual_group(anchor, members, import_channels=importing)
    flow.devices.intersection_update(flow.catalog)
    new_index = member_index(flow.groups, flow.devices)
    registry = dr.async_get(hass)
    entry = flow.config_entry

    def target(key):
        device = registry.async_get_device_by_identifier((DOMAIN, flow.runtime.identifier(key)), entry.entry_id)
        primary = flow.groups.get(key, {}).get("primary", key)
        item = flow.catalog.get(primary, {})
        name = (device.name_by_user or device.name if device else None) or item.get("alias") or item.get("name") or key
        return {"id": device.id if device else None, "name": name}

    prefix = flow.runtime.identifier("")
    moved = {}
    for entity in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id):
        if not entity.unique_id.startswith(prefix):
            continue
        source = entity.unique_id.removeprefix(prefix).split("/", 1)[0]
        if source in flow.devices and (destination := new_index.get(source, source)) != old_index.get(source, source):
            moved.setdefault(destination, []).append(entity.entity_id)
    changed_keys = {new_index.get(source, source) for source in flow.devices
                    if source in affected or new_index.get(source, source) != old_index.get(source, source)}
    flow.area_room_hints[key] = set(message.get("room_hints", {}).get(anchor, ()))
    _, _, _, rows = flow.area_fields(keys=changed_keys)
    result = {"target": target(key if members else anchor), "rows": rows,
              "new_imports": sorted(flow.devices - flow.saved_selection[0]),
              "moves": [{**target(dest), "entities": sorted(entities)} for dest, entities in sorted(moved.items())]}
    assignments = {}
    for source in sorted(members | {anchor}):
        old_key = old_index.get(source, source)
        old = registry.async_get_device_by_identifier((DOMAIN, flow.runtime.identifier(old_key)), entry.entry_id)
        if old is None or old.id in assignments:
            continue
        area = ar.async_get(hass).async_get_area(old.area_id) if old.area_id else None
        assignments[old.id] = {"name": old.name_by_user or old.name or flow.catalog.get(source, {}).get("name", source),
                               "area": area.name if area else None,
                               "labels": sorted(label.name for identifier in old.labels
                                                if (label := lr.async_get(hass).async_get_label(identifier)))}
    result["assignments"] = list(assignments.values()) if len(assignments) > 1 else []
    reviewed = (anchor, importing, result, sorted(members),
                {source: old_index.get(source, source) for source in sorted(affected)})
    result["review"] = sha256(json.dumps(reviewed, sort_keys=True).encode()).hexdigest()
    return result


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/command_scripts",
    vol.Required("device_id"): str,
    vol.Optional("source"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_command_scripts(hass, connection, message):
    """Find loaded HA scripts for every channel of the HA device."""
    runtime, source = resolve_device(hass, message["device_id"], message.get("source"))
    sources = set(runtime.group_sources(runtime.device_key(source)))
    component = hass.data.get("script")
    matches = []
    for script in component.entities if component else ():
        config = script.raw_config or {}
        sequence = config.get("sequence", [])
        if not isinstance(sequence, list):
            sequence = [sequence]
        commands = []
        for action in sequence:
            if not isinstance(action, dict) or action.get("action", action.get("service")) != "fhem_bridge.execute":
                continue
            data = action.get("data")
            if not isinstance(data, dict):
                continue
            kind, command = data.get("kind"), data.get("command")
            if kind not in ("set", "get") or not isinstance(command, str):
                continue
            target, channel = data.get("device_id"), data.get("source")
            if not isinstance(target, str) or (
                channel is not None and (not isinstance(channel, str) or channel not in sources)
            ):
                continue
            try:
                script_runtime, script_source = resolve_device(hass, target, channel)
            except HomeAssistantError:
                continue
            if script_runtime is not runtime or script_source not in sources:
                continue
            arguments = data.get("inputs", data.get("arguments", []))
            commands.append({
                "channel": runtime.profiles[script_source]["name"],
                "kind": kind,
                "command": command,
                "variable": isinstance(arguments, str),
                "arguments": arguments if isinstance(arguments, list) else [],
            })
        if commands:
            matches.append({
                "id": script.unique_id,
                "entity_id": script.entity_id,
                "name": script.name or script.entity_id,
                "commands": commands,
            })
    connection.send_result(message["id"], sorted(matches, key=lambda item: (item["name"].casefold(), item["entity_id"])))


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/device",
    vol.Required("device_id"): str,
    vol.Optional("source"): str,
    vol.Required("op"): vol.In(("describe", "set", "get", "attribute", "attribute_overview", "attribute_read", "attribute_update")),
    vol.Optional("refresh", default=False): bool,
    vol.Optional("command"): str,
    vol.Optional("arguments", default=list): [vol.Any(str, int, float)],
    vol.Optional("inputs"): INPUTS,
    vol.Optional("attribute"): str,
    vol.Optional("value"): str,
    vol.Optional("expected"): str,
    vol.Optional("remove", default=False): bool,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_device(hass, connection, message):
    """Serve device metadata or dispatch a device operation."""
    runtime, device = resolve_device(hass, message["device_id"], message.get("source"))
    op = message["op"]
    if op == "describe":
        result = {
            **await runtime.controls(device, message["refresh"]),
            "source": device,
            "bridge_entry_id": runtime.entry.entry_id,
            "schedule": schedule_family(runtime.profiles[device]),
            "sources": [
                {"id": item, "name": runtime.profiles[item]["name"],
                 "schedule": schedule_family(runtime.profiles[item])}
                for item in runtime.group_sources(runtime.device_key(device))
            ],
        }
    elif op == "attribute_overview":
        try:
            result = await runtime.attribute_overview(device)
        except (BridgeError, OSError, TimeoutError) as err:
            raise HomeAssistantError(str(err)) from err
    elif op in {"attribute_read", "attribute_update"}:
        name = message.get("attribute")
        if not name:
            raise HomeAssistantError("Select a FHEM attribute")
        if op == "attribute_read":
            result = await runtime.attributes(device, attribute=name)
        else:
            if not message.get("expected"):
                raise HomeAssistantError("Reload the attribute before editing it")
            result = await runtime.update_attribute(device, name, message["expected"],
                                                    message.get("value"), message["remove"])
    elif op == "attribute":
        if not message.get("attribute"):
            raise HomeAssistantError("Select a FHEM attribute")
        await runtime.edit_attribute(device, message["attribute"], message.get("value"), message["remove"])
        result = {"status": "accepted"}
    else:
        if not message.get("command"):
            raise HomeAssistantError("Select a FHEM command")
        result = await runtime.execute(
            device, op, message["command"], message["arguments"], inputs=message.get("inputs")
        )
    connection.send_result(message["id"], result)


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/config_status",
    vol.Required("entry_id"): str,
    vol.Optional("save", default=False): bool,
    vol.Optional("details", default=False): bool,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_config_status(hass, connection, message):
    entry = hass.config_entries.async_get_entry(message["entry_id"])
    runtime = getattr(entry, "runtime_data", None) if entry and entry.domain == DOMAIN else None
    if runtime is None or runtime.client is None:
        raise HomeAssistantError("FHEM Bridge is unavailable")
    try:
        status = await runtime.configuration_status(details=message["details"], save=message["save"])
    except (BridgeError, OSError, TimeoutError) as err:
        raise HomeAssistantError(str(err)) from err
    connection.send_result(message["id"], status)


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/thermostat",
    vol.Required("device_id"): str,
    vol.Optional("bridge_identifier"): str,
    vol.Optional("source"): str,
    vol.Required("op"): vol.In(("read", "write")),
    vol.Optional("revision"): str,
    vol.Optional("days"): dict,
    vol.Optional("temperatures"): vol.Any(None, list),
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_schedule(hass, connection, message):
    """Read or update a device-native schedule through the thermostat adapter."""
    runtime, device = resolve_device(
        hass, message["device_id"], message.get("source"), message.get("bridge_identifier")
    )
    if message["op"] == "read":
        result = await read_week(runtime, device)
    else:
        result = await write_week(
            runtime, device, message.get("revision"), message.get("days"), message.get("temperatures")
        )
    connection.send_result(message["id"], result)


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/device_options",
    vol.Required("device_id"): str,
    vol.Optional("source"): str,
    vol.Optional("values"): {
        **{vol.Optional(key): [str] for key in PERMISSIONS},
        vol.Optional(CONF_LOGS, default=False): bool,
    },
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_device_options(hass, connection, message):
    runtime, device = resolve_device(hass, message["device_id"], message.get("source"))
    key = runtime.device_key(device)
    subentry = next((sub for sub in device_subentries(runtime.entry) if sub.data["key"] == key), None)
    if subentry is None:
        raise HomeAssistantError("Reload FHEM Bridge to create the device configuration")
    if "values" in message:
        update_permissions(hass, runtime.entry, subentry, message["values"],
                           "device_logs" in runtime.client.capabilities)
    connection.send_result(message["id"], {
        "title": subentry.title,
        "members": [{"id": source, "name": runtime.profiles.get(source, {}).get("name", source)}
                    for source in subentry.data["members"]],
        "values": {key: list(subentry.data.get(key, ())) for key in (*PERMISSIONS, CONF_LOGS)},
        "logs_supported": "device_logs" in runtime.client.capabilities,
    })


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/diagnostics",
    vol.Required("device_id"): str,
    vol.Optional("source"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_diagnostics(hass, connection, message):
    runtime, source = resolve_device(hass, message["device_id"], message.get("source"))
    sources = runtime.groups.get(runtime.device_key(source), {}).get("members", [source])
    connection.send_result(message["id"], diagnostics(runtime.entry, sources))


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/publications",
    vol.Required("device_id"): str,
    vol.Optional("source"): str,
    vol.Required("op"): vol.In(("list", "preview", "preview_device", "commit")),
    vol.Optional("shared_id"): str,
    vol.Optional("template_choice"): {
        vol.Optional("key"): str, vol.Required("disabled"): bool,
        vol.Optional("layout"): ITEM_SCHEMA,
    },
    vol.Optional("scope", default="device"): vol.In(("device", "class", "type", "selected")),
    vol.Optional("assignment", default=False): bool,
    vol.Optional("disabled", default=False): bool,
    vol.Optional("role_id"): str,
    vol.Optional("copy_from"): str,
    vol.Optional("template_id"): str,
    vol.Optional("reset_keys", default=list): vol.All([str], vol.Length(max=500)),
    vol.Optional("template_name"): vol.All(str, str.strip, vol.Length(min=1, max=100)),
    vol.Optional("devices", default=list): vol.All([str], vol.Length(max=500)),
    vol.Optional("future", default=False): bool,
    vol.Optional("items", default=list): vol.All([ITEM_SCHEMA], vol.Length(max=500)),
    vol.Optional("rule_id"): str,
    vol.Optional("token"): str,
    vol.Optional("remove_rule", default=False): bool,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_publications(hass, connection, message):
    runtime, device = resolve_device(hass, message["device_id"], message.get("source"))
    publications = runtime.publications
    if message["op"] == "commit":
        if not message.get("token"):
            raise HomeAssistantError("Bitte zuerst die Vorschau öffnen.")
        entry_id = runtime.entry.entry_id
        _LOGGER.debug("Saving publication changes for bridge entry %s", entry_id)
        edited_template, sources = await publications.commit(message["token"], device, with_sources=True)
        if edited_template and not (
            publications.template_candidates(edited_template, publications.data["templates"], publications.data["rules"])
            or any(rule.get("template") == edited_template for rule in publications.data["rules"])
        ):
            connection.send_result(message["id"], {"reloaded": True, "edited_template": edited_template})
            return
        await asyncio.shield(hass.async_create_task(
            runtime.refresh_publications(sources), "Apply FHEM Bridge publications"
        ))
        result = {"reloaded": True, "edited_template": edited_template}
    elif device not in runtime.active:
        raise HomeAssistantError("FHEM-Gerät ist nicht verfügbar.")
    elif message["op"] == "preview_device":
        if message["scope"] == "type":
            raise HomeAssistantError("Wähle ein Gerät, ausgewählte Geräte oder eine Geräteklasse.")
        result = await publications.preview_device(
            device, message["items"], message.get("template_choice"), scope=message["scope"],
            future=message["future"], devices=message["devices"], shared_id=message.get("shared_id"),
        )
    elif message["op"] == "preview":
        result = await publications.preview(
            device, message["scope"], message["future"], message["items"], message.get("rule_id"), message["remove_rule"],
            assignment=message["assignment"], template_id=message.get("template_id"), devices=message["devices"],
            template_name=message.get("template_name"), reset_keys=message["reset_keys"],
            disabled=message["disabled"], template_role_id=message.get("role_id"), copy_from=message.get("copy_from"),
        )
    else:
        profile = runtime.profiles[device]
        rules = publications.data["rules"]
        controls = await runtime.controls(device)
        sections = {
            kind: [
                {**item, "modes": command_modes(kind, item["fields"], bool(profile["readings"]))}
                for item in controls["sections"][kind]
            ]
            for kind in ("set", "get")
        }
        selected = publications.resolved[device]["choices"]
        result = {
            **publications.resolved[device],
            "readings": publications.readings(device, profile, selected),
            "choices": selected,
            "sensor_classes": SENSOR_CLASSES,
            "sensor_state_classes": SENSOR_STATE_CLASSES,
            "rules": [{**rule, "applies": rule_matches(rule, device, profile),
                       "affected_ids": [target for target, other in runtime.profiles.items()
                                        if rule["scope"] != "device" and rule_matches(rule, target, other)],
                       "affected": [other["name"] for target, other in runtime.profiles.items()
                                    if rule["scope"] != "device" and rule_matches(rule, target, other)]}
                      for rule in rules if rule_matches({**rule, "future": True}, device, profile)],
            "class": device_class(profile),
            "shareable_class": shareable_class(profile),
            "class_count": sum(rule_matches(
                {"scope": "class", "match": device_class(profile), "future": True}, target, other
            ) for target, other in runtime.profiles.items()),
            "assignment": template_assignment(rules, device, profile),
            "templates": {
                key: {"name": doc["name"], "items": {
                    item["key"]: item for item in [*doc.get("items", []),
                        *template_role(doc, device, profile).get("items", [])]
                }, "role_id": template_role_id(doc, device, profile)}
                for key, doc in publications.data["templates"].items()
            },
            "bridge_entry_id": runtime.entry.entry_id,
            "group_templates": [
                {"name": runtime.profiles[source]["name"],
                 "role": publications.resolved[source].get("role"),
                 "template": publications.resolved[source].get("effective_template")}
                for source in runtime.group_sources(runtime.device_key(device))
                if source in publications.resolved
            ],
            "targets": {key: item["name"] for key, item in runtime.profiles.items()},
            "reference_devices": {
                key: runtime.identifier(runtime.device_key(key)) for key in runtime.profiles
            },
            "required": sorted(needed_readings(profile) | set(filter(None, map(
                command_feedback, publications.resolved[device]["commands"].values()
            )))),
            "sections": sections,
            "permissions": {key: bool(controls[key]) for key in ("writable", "query", "edit_attributes", "technical")},
            "blocked": {
                key: runtime.command_blocked(device, item["kind"], item["name"])
                for key, item in publications.resolved[device]["commands"].items()
            },
            "values": {name: runtime.values.get((device, name)) for name in profile["readings"]},
        }
    connection.send_result(message["id"], result)


@websocket_api.websocket_command({
    vol.Required("type"): "fhem_bridge/templates",
    vol.Required("entry_id"): str,
    vol.Required("op"): vol.In(("list", "document", "source", "edit", "reset", "delete", "create", "copy", "import", "commit")),
    vol.Optional("key"): str,
    vol.Optional("source"): str,
    vol.Optional("draft"): dict,
    vol.Optional("name"): vol.All(str, str.strip, vol.Length(min=1, max=100)),
    vol.Optional("content"): vol.All(str, vol.Length(max=MAX_FILE_SIZE)),
    vol.Optional("token"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_templates(hass, connection, message):
    entry = hass.config_entries.async_get_entry(message["entry_id"])
    runtime = getattr(entry, "runtime_data", None) if entry and entry.domain == DOMAIN else None
    if runtime is None:
        raise HomeAssistantError("FHEM Bridge ist nicht verfügbar.")
    publications = runtime.publications
    library = publications.library
    op, key = message["op"], message.get("key")
    if op == "list":
        result = {
            "templates": [{**{field: doc.get(field) for field in
                              ("key", "name", "description", "origin", "version", "base_version")},
                           "standard": library.defaults.get(id_, {}).get("version"),
                           "update_available": id_ in library.updates}
                          for id_, doc in library.documents.items()],
            "sensor_classes": SENSOR_CLASSES,
            "sensor_state_classes": SENSOR_STATE_CLASSES,
            "updated": len(library.updated),
            "errors": library.errors,
            "references": [
                {"id": source, "name": profile["name"], "type": profile["type"], "model": model_of(profile),
                 "channel": str(profile["attributes"].get("chanNo") or ""),
                 "compatible": [id_ for id_, doc in library.documents.items()
                                if matched_rule(doc, source, profile, automatic=False)],
                 "customizations": [item["name"] for rule in publications.data["rules"]
                                    if not rule.get("assignment") and rule_matches(rule, source, profile)
                                    for item in rule["items"].values()],
                 "device": runtime.identifier(runtime.device_key(source))}
                for source, profile in runtime.profiles.items() if source in runtime.active
            ],
        }
    elif op == "document":
        doc = library.documents.get(key)
        if not doc:
            raise HomeAssistantError("Die Vorlage ist nicht mehr verfügbar.")
        result = {"content": yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), "document": doc}
    elif op == "source":
        source = message.get("source")
        if source not in runtime.active:
            raise HomeAssistantError("Das Referenzgerät ist nicht verfügbar.")
        profile = runtime.profiles[source]
        resolved = publications.resolved[source]
        controls = await runtime.controls(source)
        result = {
            "readings": resolved["readings"], "items": resolved["choices"],
            "layout": resolved["layout"], "cover": resolved["cover"],
            "role": resolved.get("role"), "effective_template": resolved.get("effective_template"),
            "role_id": template_role_id(library.documents[key], source, profile) if key in library.documents else None,
            "sections": {kind: controls["sections"][kind] for kind in ("set", "get")},
            "rules": [{"id": rule["id"], "scope": rule["scope"], "items": rule["items"]}
                      for rule in publications.data["rules"]
                      if not rule.get("assignment") and rule_matches(rule, source, profile)],
        }
    elif op == "commit":
        token = message.get("token")
        if not token:
            raise HomeAssistantError("Bitte zuerst die Vorschau öffnen.")
        key, sources = await publications.commit(token, None, with_sources=True)
        await asyncio.shield(hass.async_create_task(
            runtime.refresh_publications(sources), "Apply FHEM Bridge templates"
        ))
        result = {"key": key, "reloaded": True}
    else:
        try:
            result = await publications.preview_library(op, key, message.get("content"), message.get("name"), message.get("draft") or {})
        except (ValueError, vol.Invalid, yaml.YAMLError) as err:
            raise HomeAssistantError(str(err)) from err
    connection.send_result(message["id"], result)
