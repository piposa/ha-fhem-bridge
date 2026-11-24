"""Native HA subentries for imported FHEM devices and their channel permissions."""

from collections import defaultdict
from types import MappingProxyType

from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import (
    CONF_DEVICES, CONF_DEVICE_GROUPS, CONF_WRITABLE, CONF_QUERY,
    CONF_EDIT_ATTRIBUTES, CONF_TECHNICAL, DOMAIN,
)
from .groups import member_index

SUBENTRY_TYPE = "device"
MIGRATED = "device_subentries"
CONF_LOGS = "subscribe_logs"
PERMISSIONS = (CONF_WRITABLE, CONF_QUERY, CONF_EDIT_ATTRIBUTES, CONF_TECHNICAL)


def device_subentries(entry):
    return [sub for sub in entry.subentries.values() if sub.subentry_type == SUBENTRY_TYPE]


def settings(entry):
    """Subentries own membership and permissions after the one-time migration."""
    result = dict(entry.options)
    if not entry.options.get(MIGRATED):
        return result
    selected = set()
    groups = {}
    permissions = {name: set() for name in (*PERMISSIONS, CONF_LOGS)}
    for sub in device_subentries(entry):
        members = set(sub.data["members"])
        if group := sub.data.get("group"):
            groups[sub.data["key"]] = dict(group)
        selected.update(members)
        for name in permissions:
            permissions[name].update(set(sub.data.get(name, ())) & members)
    # Confirmed groups can be prepared before any of their channels are imported.
    groups.update({key: group for key, group in result.get(CONF_DEVICE_GROUPS, {}).items()
                   if key not in groups and group.get("manual") and not selected.intersection(group["members"])})
    return {**result, CONF_DEVICES: sorted(selected), CONF_DEVICE_GROUPS: groups,
            **{key: sorted(values) for key, values in permissions.items()}}


def save_devices(hass, entry, options, catalog):
    """Move surviving entities before removing obsolete group subentries."""
    sources = set(options.get(CONF_DEVICES, ()))
    groups = options.get(CONF_DEVICE_GROUPS, {})
    index = member_index(groups, sources)
    memberships = defaultdict(list)
    for source in sorted(sources):
        memberships[index.get(source, source)].append(source)
    existing = {sub.data["key"]: sub for sub in device_subentries(entry)}
    subentries = {key: sub for key, sub in entry.subentries.items() if sub.subentry_type != SUBENTRY_TYPE}
    identifiers = {}
    for key, members in memberships.items():
        old = existing.get(key)
        primary = groups.get(key, {}).get("primary", members[0])
        profile = catalog.get(primary, catalog.get(members[0], {}))
        attrs = profile.get("attributes", {})
        name = attrs.get("alias") or profile.get("alias") or profile.get("name") or (old.title if old else "FHEM")
        data = {**(dict(old.data) if old else {}), "key": key, "members": members, "group": groups.get(key),
                "names": {source: catalog.get(source, {}).get("name") or
                          (old.data.get("names", {}).get(source) if old else None) or source for source in members},
                **{permission: sorted(sources & set(options.get(permission, ())) & set(members))
                   for permission in (*PERMISSIONS, CONF_LOGS)}}
        sub = ConfigSubentry(data=MappingProxyType(data), subentry_type=SUBENTRY_TYPE,
                             title=old.title if old else name, unique_id=key,
                             **({"subentry_id": old.subentry_id} if old else {}))
        subentries[sub.subentry_id] = sub
        identifiers[key] = sub.subentry_id

    # Register the new owners first, keeping the old owners until entities have moved.
    for sub_id, sub in subentries.items():
        if sub_id in entry.subentries:
            hass.config_entries.async_update_subentry(entry, entry.subentries[sub_id], data=dict(sub.data))
        else:
            hass.config_entries.async_add_subentry(entry, sub)
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    prefix = f"{entry.unique_id}/"
    for entity in er.async_entries_for_config_entry(entities, entry.entry_id):
        if not entity.unique_id.startswith(prefix):
            continue
        source = entity.unique_id.removeprefix(prefix).split("/", 1)[0]
        owner = identifiers.get(index.get(source, source))
        if owner and entity.config_subentry_id != owner:
            entities.async_update_entity(entity.entity_id, config_subentry_id=owner)
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        keys = [identifier.removeprefix(prefix) for domain, identifier in device.identifiers
                if domain == DOMAIN and identifier.startswith(prefix)]
        owner = next((identifiers[index.get(key, key)] for key in keys if index.get(key, key) in identifiers), None)
        if owner and device.config_subentry_id != owner:
            devices.async_update_device(device.id, new_config_subentry_id=owner)
    for sub_id in list(entry.subentries):
        if sub_id not in subentries:
            hass.config_entries.async_remove_subentry(entry, sub_id)
    hass.config_entries.async_update_entry(entry, options={**options, MIGRATED: True})


def add_entities(runtime, callback, entities):
    """Assign native and published entities to the same per-device subentry."""
    grouped = defaultdict(list)
    owners = {sub.data["key"]: sub.subentry_id for sub in device_subentries(runtime.entry)}
    for entity in entities:
        grouped[owners.get(runtime.device_key(entity.device))].append(entity)
    for owner, batch in grouped.items():
        callback(batch, config_subentry_id=owner)


def update_permissions(hass, entry, subentry, values, logs_supported, assignment=None):
    """Validate the whole edit before committing channel rights."""
    from homeassistant.exceptions import HomeAssistantError

    data = {**subentry.data, **(assignment or {})}
    members = set(data["members"])
    if any(set(values.get(key, ())) - members for key in PERMISSIONS):
        raise HomeAssistantError("Choose channels from this device")
    if values.get(CONF_LOGS) and not logs_supported:
        raise HomeAssistantError("Update 98_HABridge.pm before enabling FHEM log subscriptions")
    data = {**data, **{key: sorted(set(values.get(key, ()))) for key in PERMISSIONS},
            CONF_LOGS: sorted(members) if values.get(CONF_LOGS) else []}
    hass.config_entries.async_update_subentry(entry, subentry, data=data)
