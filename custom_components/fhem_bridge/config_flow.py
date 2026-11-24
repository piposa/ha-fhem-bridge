"""Connection and device selection flows."""

import asyncio
import logging
from time import monotonic
from contextlib import asynccontextmanager
from html import escape
from urllib.parse import urlencode

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry, device_registry, label_registry, selector

from .device_config import CONF_LOGS, MIGRATED, PERMISSIONS, SUBENTRY_TYPE, device_subentries, save_devices, settings, update_permissions
from .client import BridgeError, probe_fingerprint
from .const import (
    CONF_DEVICE_ALIASES, CONF_DEVICE_GROUPS, CONF_DEVICES, CONF_EDIT_ATTRIBUTES,
    CONF_FINGERPRINT, CONF_IMPORT_AREAS, CONF_IMPORT_LABELS, CONF_QUERY, CONF_TECHNICAL, CONF_WRITABLE, DOMAIN, PANEL_PATH,
)
from .groups import automatic_groups, member_index, merge_manual
from .runtime import CONNECTION_ERRORS, make_client

_LOGGER = logging.getLogger(__name__)
_DIAGNOSTICS_LOGGER = logging.getLogger(__name__ + ".diagnostics")
CHECK_TIMEOUT = 12


def bridge_title(data):
    """Use a display name independently of credentials and stable server identity."""
    return data.get("name", "").strip() or f"FHEM · {data['host']}"


def certificate_schema(fingerprint):
    """Keep the pinned certificate visible as a copyable, read-only field."""
    return vol.Schema({
        vol.Required("fingerprint", default=fingerprint): selector.TextSelector(
            selector.TextSelectorConfig(read_only=True, multiline=True)),
        vol.Required("confirm", default=False): selector.BooleanSelector(),
    })


@asynccontextmanager
async def connection_phase(phase, data):
    """Bound and time a setup phase without logging credentials or input values."""
    start = monotonic()
    _DIAGNOSTICS_LOGGER.debug("Connection check phase=%s host=%s port=%s started", phase, data["host"], data["port"])
    try:
        async with asyncio.timeout(CHECK_TIMEOUT):
            yield
    except CONNECTION_ERRORS as err:
        reason = str(err) if isinstance(err, BridgeError) else type(err).__name__
        _LOGGER.warning("Connection check phase=%s host=%s port=%s failed after %.0f ms (%s)",
                        phase, data["host"], data["port"], (monotonic() - start) * 1000, reason)
        raise
    else:
        elapsed = (monotonic() - start) * 1000
        log = _DIAGNOSTICS_LOGGER.warning if elapsed >= 3000 else _DIAGNOSTICS_LOGGER.debug
        log("Connection check phase=%s host=%s port=%s completed in %.0f ms",
            phase, data["host"], data["port"], elapsed)


def connection_error(err):
    if isinstance(err, TimeoutError):
        return "connection_timeout"
    if isinstance(err, BridgeError) and str(err) in {
            "certificate_changed", "incompatible_protocol", "invalid_server_identity"}:
        return str(err)
    return "cannot_connect"


CONNECTION_CHECK_ERRORS = (*CONNECTION_ERRORS, HomeAssistantError)


@asynccontextmanager
async def connection_check(hass, entry):
    """Give the test connection exclusive use of FHEM's single client slot."""
    async with entry.setup_lock:
        was_loaded = entry.state is config_entries.ConfigEntryState.LOADED
        if was_loaded and not await hass.config_entries.async_unload(entry.entry_id, _lock=False):
            raise HomeAssistantError("The bridge could not be unloaded for the connection check")
        try:
            yield was_loaded
        finally:
            if was_loaded:
                hass.config_entries.async_schedule_reload(entry.entry_id)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Connect to a verified FHEM Bridge endpoint."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry):
        return {SUBENTRY_TYPE: DeviceConfigFlow}


    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if any(entry.data.get("host") == user_input["host"].strip() and
                   entry.data.get("port") == user_input["port"] for entry in self._async_current_entries()):
                return self.async_abort(reason="already_configured")
            try:
                async with connection_phase("certificate_probe", user_input):
                    fingerprint = await probe_fingerprint(user_input["host"].strip(), user_input["port"])
            except CONNECTION_ERRORS as err:
                errors["base"] = connection_error(err)
            else:
                self.connection = {**user_input, "host": user_input["host"].strip(), CONF_FINGERPRINT: fingerprint}
                return await self.async_step_confirm_certificate()
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Optional("name", default=""): str,
                    vol.Required("host"): str,
                    vol.Required("port", default=19091): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                    vol.Required("token"): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    ),
                }
            ),
        )

    async def async_step_confirm_certificate(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not user_input.get("confirm", False):
                return self.async_abort(reason="certificate_rejected")
            client = make_client(self.connection)
            try:
                async with connection_phase("authentication", self.connection):
                    server_id = await client.connect()
            except CONNECTION_ERRORS as err:
                errors["base"] = connection_error(err)
            else:
                await self.async_set_unique_id(server_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=bridge_title(self.connection), data=self.connection)
            finally:
                await client.close()
        return self.async_show_form(
            step_id="confirm_certificate",
            data_schema=certificate_schema(self.connection[CONF_FINGERPRINT]),
            description_placeholders={"fingerprint": self.connection[CONF_FINGERPRINT]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DeviceOptions()


TECHNICAL_TYPES = {
    "allowed", "at", "autocreate", "Dashboard", "DbLog", "DbRep", "DOIF",
    "eventTypes", "FHEMWEB", "FileLog", "FLOORPLAN", "FUIP", "HMCCURPCPROC",
    "HMinfo", "MQTT2_CLIENT", "notify", "readingsGroup", "SVG", "telnet",
    "watchdog", "weblink",
}


class DeviceOptions(config_entries.OptionsFlow):
    """Manage the bridge connection, device inventory and manual grouping."""

    async def async_step_init(self, user_input=None):
        self.runtime = getattr(self.config_entry, "runtime_data", None)
        library = self.runtime.publications.library if self.runtime else None
        url = "/" + PANEL_PATH + "?" + urlencode({"bridge": self.config_entry.entry_id})
        status = getattr(self.runtime, "config_status", None) if getattr(self.runtime, "connected", False) else None
        status_key = ("save_error" if status.get("save_error") else "dirty" if status.get("dirty") else "clean") if status else "unknown"
        return self.async_show_menu(step_id=f"init_{status_key}",
                                   menu_options=["add_devices", "group", "catalog", "connection"],
                                   description_placeholders={
                                       "fhem_bridge_import_entry": self.config_entry.entry_id,
                                       "config_url": "/" + PANEL_PATH + "?" + urlencode(
                                           {"bridge": self.config_entry.entry_id, "config": "1"}),
                                       "template_url": url,
                                       "template_updated": str(len(library.updated) if library else 0),
                                       "template_pending": str(len(library.updates) if library else 0),
                                       "template_errors": str(len(library.errors) if library else 0),
                                   })

    async def async_step_init_clean(self, user_input=None):
        return await self.async_step_init(user_input)

    async def async_step_init_dirty(self, user_input=None):
        return await self.async_step_init(user_input)

    async def async_step_init_save_error(self, user_input=None):
        return await self.async_step_init(user_input)

    async def async_step_init_unknown(self, user_input=None):
        return await self.async_step_init(user_input)

    async def async_step_catalog(self, user_input=None):
        if not await self.load_catalog():
            return await self.async_step_offline()
        return await self.async_step_selection()

    async def load_catalog(self):
        self.runtime = getattr(self.config_entry, "runtime_data", None)
        try:
            catalog = await self.runtime.inventory() if self.runtime and self.runtime.client else None
        except CONNECTION_ERRORS:
            catalog = None
        if catalog is None:
            return False
        self.prepare_catalog(catalog)
        return True

    def prepare_catalog(self, catalog):
        """Initialize a draft from the current HA selection and FHEM catalog."""
        self.catalog = {item["device"]: item for item in catalog}
        current = settings(self.config_entry)
        saved = set(current.get(CONF_DEVICES, ()))
        self.saved_selection = (saved, current.get(CONF_DEVICE_GROUPS, {}))
        self.devices = saved & self.catalog.keys()
        self.missing = saved - self.catalog.keys()
        self.groups = {key: dict(group) for key, group in self.saved_selection[1].items()}
        self.import_areas = {
            key: f"area:{area}" for key, area in self.config_entry.options.get(CONF_IMPORT_AREAS, {}).items()
        }
        labels = label_registry.async_get(self.hass)
        self.import_labels = {
            key: [label.name for identifier in identifiers if (label := labels.async_get_label(identifier))]
            for key, identifiers in self.config_entry.options.get(CONF_IMPORT_LABELS, {}).items()
        }
        self.area_room_hints = {}
        self.labels = {device: self._label(item) for device, item in self.catalog.items()}

    async def async_step_offline(self, user_input=None):
        return self.async_show_menu(step_id="offline", menu_options=["init", "connection"],
                                   description_placeholders=self.bridge_return())

    def bridge_return(self):
        return {"fhem_bridge_return_entry": self.config_entry.entry_id}

    async def async_step_selection(self, user_input=None):
        groups = self._selected_groups()
        rows = []
        for key, sources in groups.items():
            primary = self.groups.get(key, {}).get("primary", sources[0])
            label = escape(self.labels.get(primary, self.labels[sources[0]]))
            if len(sources) == 1:
                rows.append(f"<li><strong>{label}</strong></li>")
                continue
            channels = "".join(f"<li>{escape(self.catalog[source]['name'])}</li>" for source in sources)
            rows.append(f"<li><details><summary><strong>{label}</strong> · {len(sources)}</summary>"
                        f"<ul>{channels}</ul></details></li>")
        return self.async_show_menu(
            step_id="selection", menu_options=["init"],
            description_placeholders={
                **self.bridge_return(),
                "count": str(len(self.devices)), "devices": str(len(groups)),
                "missing": str(len(self.missing)), "rows": "<ul>" + "".join(rows) + "</ul>" if rows else "–",
            },
        )

    async def async_step_add_devices(self, user_input=None):
        """Recover if the frontend module has not attached to the menu yet."""
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(step_id="add_devices")

    async def async_step_connection(self, user_input=None):
        entry = self.config_entry
        errors = {}
        if user_input is not None:
            self.pending_connection = {
                **entry.data, **user_input, "host": user_input["host"].strip(), "token": user_input.get("token") or entry.data["token"],
            }
            if (bridge_title(self.pending_connection) != entry.title and
                    all(self.pending_connection[key] == entry.data[key] for key in ("host", "port", "token"))):
                self.hass.config_entries.async_update_entry(
                    entry, data=self.pending_connection, title=bridge_title(self.pending_connection))
                return self.async_abort(reason="connection_saved")
            try:
                async with connection_check(self.hass, entry):
                    async with connection_phase("certificate_probe", self.pending_connection):
                        fingerprint = await probe_fingerprint(self.pending_connection["host"], user_input["port"])
            except CONNECTION_CHECK_ERRORS:
                errors["base"] = "cannot_connect"
            else:
                self.pending_connection[CONF_FINGERPRINT] = fingerprint
                return await self.async_step_connection_certificate()
        return self.async_show_form(step_id="connection", errors=errors, description_placeholders=self.bridge_return(),
                                    data_schema=vol.Schema({
            vol.Required("name", default=entry.title): str,
            vol.Required("host", default=entry.data["host"]): str,
            vol.Required("port", default=entry.data["port"]): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Optional("token"): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }))

    async def async_step_connection_certificate(self, user_input=None):
        if user_input is not None:
            if not user_input.get("confirm", False):
                return self.async_abort(reason="certificate_rejected")
            entry = self.config_entry
            try:
                async with connection_check(self.hass, entry) as was_loaded:
                    client = make_client(self.pending_connection)
                    try:
                        async with connection_phase("authentication", self.pending_connection):
                            identifier = await client.connect()
                    finally:
                        await client.close()
                    if identifier != entry.unique_id:
                        return self.async_abort(reason="wrong_bridge")
                    self.hass.config_entries.async_update_entry(entry, data=self.pending_connection,
                                                                 title=bridge_title(self.pending_connection))
                    if not was_loaded:
                        self.hass.config_entries.async_schedule_reload(entry.entry_id)
            except CONNECTION_CHECK_ERRORS:
                return self.async_abort(reason="cannot_connect")
            return self.async_abort(reason="connection_saved")
        return self.async_show_form(
            step_id="connection_certificate",
            description_placeholders={**self.bridge_return(), "fingerprint": self.pending_connection[CONF_FINGERPRINT]},
            data_schema=certificate_schema(self.pending_connection[CONF_FINGERPRINT]),
        )

    def _selected_groups(self):
        index = member_index(self.groups, self.devices)
        grouped = {}
        for source in sorted(self.devices, key=lambda source: self.labels[source].casefold()):
            grouped.setdefault(index.get(source, source), []).append(source)
        return grouped

    def import_groups(self, candidates):
        """Return groups with at least one candidate channel."""
        available = automatic_groups(self.catalog)
        for key, group in self.groups.items():
            if group.get("manual"):
                members = set(group["members"]) & self.catalog.keys()
                primary = group["primary"]
                if primary in members:
                    merge_manual(available, primary, members - {primary}, group_key=key)
        sources = member_index(available, self.catalog)
        visible = {}
        for source in candidates:
            group_id = sources.get(source)
            if group_id is None:
                continue
            visible[f"group:{group_id}"] = available[group_id]
        return visible

    async def async_step_group(self, user_input=None):
        if user_input is None and not await self.load_catalog():
            return await self.async_step_offline()
        if user_input is not None and user_input.get("anchor") in self.catalog:
            self.group_anchor = user_input["anchor"]
            return await self.async_step_group_members()
        return self.async_show_form(step_id="group", data_schema=vol.Schema({
            vol.Required("anchor"): self._selector(self.labels, multiple=False),
        }))

    async def async_step_group_members(self, user_input=None):
        anchor = self.group_anchor
        current_key = self.group_key(anchor)
        current = set(self.groups.get(current_key, {}).get("members", ())) - {anchor}
        if user_input is not None:
            members = (set(user_input.get("members", ())) & self.catalog.keys()) - {anchor}
            self.set_manual_group(anchor, members)
            return await self.async_step_areas()
        return self.async_show_form(
            step_id="group_members", description_placeholders={"device": self.catalog[anchor]["name"]},
            data_schema=vol.Schema({
                vol.Optional("members", description={"suggested_value": sorted(current)}): self._selector(
                    {key: label for key, label in self.labels.items() if key != anchor},
                    mode=selector.SelectSelectorMode.LIST,
                ),
            }),
        )

    def group_key(self, anchor):
        return next((key for key, group in self.groups.items() if group["primary"] == anchor), anchor)

    def set_manual_group(self, anchor, members, *, import_channels=True):
        key = self.group_key(anchor)
        if members:
            merge_manual(self.groups, anchor, members, group_key=key)
            if import_channels:
                self.devices.update({anchor, *members})
        else:
            self.groups.pop(key, None)

    async def async_step_areas(self, user_input=None):
        fields, errors, targets, _ = self.area_fields(user_input)
        if fields and (user_input is None or errors):
            return self.async_show_form(step_id="areas", data_schema=vol.Schema(fields), errors=errors)
        self.import_areas = {key: choice for key, (choice, _) in targets.items()}
        self.import_labels = {key: labels for key, (_, labels) in targets.items()}
        return await self.async_step_write({})

    def area_fields(self, user_input=None, *, keys=None):
        areas = area_registry.async_get(self.hass)
        existing = sorted(areas.async_list_areas(), key=lambda area: area.name.casefold())
        registry = device_registry.async_get(self.hass)
        german = self.hass.config.language.startswith("de")
        fields = {}
        targets = {}
        errors = {}
        rows = []
        for key, sources in self._selected_groups().items():
            if keys is not None and key not in keys:
                continue
            if registry.async_get_device_by_identifier((DOMAIN, self.runtime.identifier(key)), self.config_entry.entry_id):
                continue
            rooms = set().union(*(self._rooms(self.catalog[source]) for source in sources))
            matches = {room: area for room in rooms if (area := areas.async_get_area_by_name(room))}
            preferred = {area.id for room, area in matches.items() if room in self.area_room_hints.get(key, ())}
            preferred = preferred or {area.id for area in matches.values()}
            choices = {f"area:{area.id}": area.name for area in existing if area.id in preferred}
            choices.update({f"area:{area.id}": area.name for area in existing})
            choices.update({
                f"room:{room}": f"{room} ({'neu' if german else 'new'})"
                for room in sorted(rooms - matches.keys(), key=str.casefold)
            })
            choices["none"] = "Kein Bereich" if german else "No area"
            proposed = f"area:{next(iter(preferred))}" if len(preferred) == 1 else "none"
            primary = self.groups.get(key, {}).get("primary", sources[0])
            device_name = self.catalog.get(primary, self.catalog[sources[0]])["name"]
            area_field = f"{device_name} · {'HA-Bereich' if german else 'HA area'}"
            labels_field = f"{device_name} · HA-Labels"
            chosen = (user_input or {}).get(area_field, self.import_areas.get(key, proposed))
            selected_labels = (user_input or {}).get(labels_field, self.import_labels.get(key, []))
            fields[vol.Required(area_field, default=chosen if chosen in choices else proposed)] = self._selector(
                choices, multiple=False,
            )
            label_choices = {room: room for room in sorted(rooms, key=str.casefold)}
            rows.append({"key": key, "name": device_name, "area_field": area_field, "labels_field": labels_field,
                         "areas": list(choices.items()), "labels": list(label_choices), "suggested": proposed})
            if label_choices:
                fields[vol.Optional(labels_field, default=[room for room in selected_labels if room in rooms])] = (
                    self._selector(label_choices)
                )
            if user_input is not None:
                if chosen not in choices or any(room not in rooms for room in selected_labels):
                    errors["base"] = "invalid_assignment"
                else:
                    kind, _, value = chosen.partition(":")
                    if (kind == "room" and value in selected_labels) or (
                        kind == "area" and any(room in matches and matches[room].id == value for room in selected_labels)
                    ):
                        errors["base"] = "duplicate_assignment"
                    targets[key] = chosen, selected_labels
        return fields, errors, targets, rows

    async def async_step_write(self, user_input=None):
        options = self.write_selection()
        if options is None:
            return self.async_abort(reason="selection_changed")
        return self.async_create_entry(title="", data=options)

    def write_selection(self):
        """Persist the common import and grouping draft."""
        current = settings(self.config_entry)
        if self.saved_selection != (set(current.get(CONF_DEVICES, ())), current.get(CONF_DEVICE_GROUPS, {})):
            return None
        permissions = {
            key: sorted((set(current.get(key, ())) & (self.devices | self.missing))
                        | (self.devices - self.saved_selection[0]))
            for key in (CONF_WRITABLE, CONF_QUERY, CONF_EDIT_ATTRIBUTES, CONF_TECHNICAL)
        }
        registry = device_registry.async_get(self.hass)
        aliases = dict(self.config_entry.options.get(CONF_DEVICE_ALIASES, {}))
        for source, group_id in member_index(self.groups, self.devices).items():
            if source == group_id:
                continue
            old = registry.async_get_device_by_identifier(
                (DOMAIN, self.runtime.identifier(source)), self.config_entry.entry_id
            )
            if old is not None:
                aliases[old.id] = source
        areas = area_registry.async_get(self.hass)
        labels = label_registry.async_get(self.hass)
        area_ids = dict(self.config_entry.options.get(CONF_IMPORT_AREAS, {}))
        label_ids = dict(self.config_entry.options.get(CONF_IMPORT_LABELS, {}))
        for key in self._selected_groups():
            if registry.async_get_device_by_identifier((DOMAIN, self.runtime.identifier(key)), self.config_entry.entry_id):
                continue
            if key not in self.import_areas:
                continue
            area_ids.pop(key, None)
            label_ids.pop(key, None)
            kind, _, value = self.import_areas[key].partition(":")
            if kind == "room":
                area_ids[key] = areas.async_get_or_create(value).id
            elif kind == "area" and areas.async_get_area(value):
                area_ids[key] = value
            if names := self.import_labels.get(key):
                label_ids[key] = [
                    (labels.async_get_label_by_name(name) or labels.async_create(name)).label_id for name in names
                ]
        selected_groups = self._selected_groups()
        options = {
            CONF_DEVICES: sorted(self.devices | self.missing), CONF_DEVICE_GROUPS: self.groups,
            CONF_DEVICE_ALIASES: aliases,
            CONF_IMPORT_AREAS: {key: ids for key, ids in area_ids.items() if key in selected_groups or key in self.missing},
            CONF_IMPORT_LABELS: {key: ids for key, ids in label_ids.items() if key in selected_groups or key in self.missing},
            **permissions,
        }
        options[CONF_LOGS] = sorted(set(current.get(CONF_LOGS, ())) & (self.devices | self.missing))
        save_devices(self.hass, self.config_entry, options, self.catalog)
        return {**options, MIGRATED: True}

    @staticmethod
    def _rooms(item):
        return {room.strip() for room in (item.get("room") or "").split(",") if room.strip()}

    @staticmethod
    def _label(item):
        name = item["name"]
        label = item.get("alias")
        display = f"{label} ({name})" if label and label != name else name
        return " · ".join(filter(None, (display, item["type"], item.get("model"), item.get("room") or "–")))

    @staticmethod
    def _selector(labels, *, multiple=True, mode=selector.SelectSelectorMode.DROPDOWN):
        return selector.SelectSelector(selector.SelectSelectorConfig(
            options=[{"value": key, "label": label} for key, label in labels.items()],
            multiple=multiple,
            mode=mode,
        ))


class DeviceConfigFlow(config_entries.ConfigSubentryFlow):
    """Configure an imported device through HA's native upper device row."""

    async def async_step_user(self, user_input=None):
        entry = self._get_entry()
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            return self.async_abort(reason="cannot_connect")
        if not hasattr(self, "catalog"):
            try:
                self.catalog = {item["device"]: item for item in await runtime.inventory()}
            except CONNECTION_ERRORS:
                return self.async_abort(reason="cannot_connect")
            self.groups = automatic_groups(self.catalog)
            index = member_index(self.groups, self.catalog)
            self.candidates = {}
            selected = set(settings(entry).get(CONF_DEVICES, ()))
            for source, item in self.catalog.items():
                key = index.get(source, source)
                members = self.groups[key]["members"] if key in self.groups else [source]
                if selected & set(members) or item["type"] in TECHNICAL_TYPES:
                    continue
                primary = self.groups.get(key, {}).get("primary", source)
                self.candidates[key] = DeviceOptions._label(self.catalog[primary])
        if not self.candidates:
            return self.async_abort(reason="no_devices")
        if user_input is not None and user_input.get("device") in self.candidates:
            self.device_key = user_input["device"]
            return await self.async_step_import()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("device"): DeviceOptions._selector(self.candidates, multiple=False),
        }))

    async def async_step_import(self, user_input=None):
        entry = self._get_entry()
        key = self.device_key
        group = self.groups.get(key)
        members = group["members"] if group else [key]
        rooms = set().union(*(DeviceOptions._rooms(self.catalog[source]) for source in members))
        areas = area_registry.async_get(self.hass)
        labels = label_registry.async_get(self.hass)
        existing = sorted(areas.async_list_areas(), key=lambda item: (item.name not in rooms, item.name.casefold()))
        choices = {f"area:{item.id}": item.name for item in existing}
        choices.update({f"room:{room}": room for room in sorted(rooms, key=str.casefold)
                        if not areas.async_get_area_by_name(room)})
        choices["none"] = "–"
        matches = [item.id for item in existing if item.name in rooms]
        default = f"area:{matches[0]}" if len(matches) == 1 else "none"
        errors = {}
        if user_input is not None:
            chosen = user_input.get("area", "none")
            names = user_input.get("labels", [])
            kind, _, value = chosen.partition(":")
            area = areas.async_get_area(value) if kind == "area" else None
            if chosen not in choices or any(name not in rooms for name in names):
                errors["base"] = "invalid_assignment"
            elif (kind == "room" and value in names) or (
                area and any(areas.async_get_area_by_name(name) == area for name in names)
            ):
                errors["base"] = "duplicate_assignment"
            elif set(members) & set(settings(entry).get(CONF_DEVICES, ())):
                return self.async_abort(reason="already_imported")
            else:
                if kind == "room":
                    area = areas.async_get_or_create(value)
                primary = group["primary"] if group else key
                return self.async_create_entry(
                    title=self.catalog[primary].get("alias") or self.catalog[primary]["name"],
                    unique_id=key, data={
                        "key": key, "members": members, "group": group,
                        "names": {source: self.catalog[source]["name"] for source in members},
                        "area_id": area.id if area else None,
                        "labels": [(labels.async_get_label_by_name(name) or labels.async_create(name)).label_id
                                   for name in names],
                        **{permission: list(members) for permission in PERMISSIONS},
                        CONF_LOGS: [],
                    },
                )
        return self.async_show_form(step_id="import", errors=errors, data_schema=vol.Schema({
            vol.Optional("area", default=default): DeviceOptions._selector(choices, multiple=False),
            vol.Optional("labels", default=[]): DeviceOptions._selector({room: room for room in sorted(rooms)}),
        }))

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            return self.async_abort(reason="cannot_connect")
        url = "/" + PANEL_PATH + "?" + urlencode({"device": runtime.identifier(subentry.data["key"])})
        return self.async_show_menu(step_id="reconfigure", menu_options=["permissions"],
                                   description_placeholders={"device": escape(subentry.title), "device_url": url})

    async def async_step_permissions(self, user_input=None):
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        runtime = getattr(entry, "runtime_data", None)
        if runtime is None:
            return self.async_abort(reason="cannot_connect")
        data = dict(subentry.data)
        members = data["members"]
        labels = {}
        for source in members:
            profile = runtime.profiles.get(source)
            labels[source] = profile["name"] if profile else data.get("names", {}).get(source, source)
        single_channel = len(members) == 1
        if user_input is not None:
            if single_channel:
                user_input = {**user_input, **{
                    key: members if user_input.get(key) else [] for key in PERMISSIONS
                }}
            if user_input.get(CONF_LOGS) and "device_logs" not in runtime.client.capabilities:
                return self.async_abort(reason="logs_require_update")
            if user_input.get("edit_assignment"):
                self.pending_permissions = user_input
                return await self.async_step_assignment()
            update_permissions(self.hass, entry, subentry, user_input,
                               "device_logs" in runtime.client.capabilities)
            return self.async_abort(reason="saved")
        if single_channel:
            permissions = {vol.Optional(key, default=bool(data.get(key))): bool for key in PERMISSIONS}
        else:
            permissions = {
                vol.Optional(key, default=data.get(key, [])): DeviceOptions._selector(
                    labels, mode=selector.SelectSelectorMode.LIST,
                )
                for key in PERMISSIONS
            }
        return self.async_show_form(
            step_id="permissions",
            description_placeholders={"device": subentry.title},
            data_schema=vol.Schema({
                **permissions,
                vol.Optional(CONF_LOGS, default=bool(data.get(CONF_LOGS))): bool,
                vol.Optional("edit_assignment", default=False): bool,
            }),
        )


    async def async_step_assignment(self, user_input=None):
        entry = self._get_entry()
        sub = self._get_reconfigure_subentry()
        runtime = entry.runtime_data
        if not hasattr(self, "assignment_catalog"):
            try:
                self.assignment_catalog = {
                    item["device"]: item for item in await runtime.inventory()
                }
            except CONNECTION_ERRORS:
                return self.async_abort(reason="cannot_connect")
        occupied = {source for other in device_subentries(entry) if other.subentry_id != sub.subentry_id
                    for source in other.data["members"]}
        eligible = {key: DeviceOptions._label(item) for key, item in self.assignment_catalog.items()
                    if key not in occupied}
        eligible.update({source: source for source in sub.data["members"] if source not in eligible})
        errors = {}
        if user_input is not None:
            members = sorted(set(user_input.get("members", ())) & eligible.keys())
            if not members:
                errors["base"] = "empty_group"
            else:
                old_group = sub.data.get("group") or {}
                primary = old_group.get("primary", sub.data["key"])
                if primary not in members:
                    primary = members[0]
                group = {"primary": primary, "members": members, "manual": True}
                values = {key: sorted(set(self.pending_permissions.get(key, ())) & set(members))
                          for key in PERMISSIONS}
                values[CONF_LOGS] = self.pending_permissions.get(CONF_LOGS, False)
                update_permissions(
                    self.hass, entry, sub, values, "device_logs" in runtime.client.capabilities,
                    assignment={"members": members, "group": group,
                                "names": {source: self.assignment_catalog.get(source, {}).get("name",
                                             sub.data.get("names", {}).get(source, source)) for source in members}},
                )
                return self.async_abort(reason="saved")
        return self.async_show_form(step_id="assignment", errors=errors, data_schema=vol.Schema({
            vol.Required("members", default=list(sub.data["members"])): DeviceOptions._selector(
                eligible, mode=selector.SelectSelectorMode.LIST,
            ),
        }))
