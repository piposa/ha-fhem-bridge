"""Resolve FHEM object selections and reusable templates."""

from asyncio import Lock, gather
from itertools import batched
from time import monotonic
from uuid import uuid4

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er

from .client import BridgeError
from .const import DOMAIN
from .profiles import dimmer_profile, input_modes, serialize_inputs, slider_field, switch_feedback, thermostat_family, thermostat_supported
from .publication_schema import FEEDBACK_MODES, INPUT_DOMAINS
from .template_library import (
    TemplateLibrary, automatic_template, matched_rule, model_of, next_version, parse_document, role_controls,
    role_readings, template_body, template_key, template_role, validate_document, working_copy,
)
from .calculator import calculator_metadata
from .templates import ACTUATOR_LAYOUTS, accepts_no_arguments, control_default, cover_commands, dimmer_outputs, redundant_button_actions

def device_class(profile):
    """Match class templates by module, model and channel role."""
    attrs = profile["attributes"]
    channel = attrs.get("chanNo", "")
    classic_thermostat = (
        thermostat_family(profile) == "cul_hm_rt"
        and channel.lstrip("0") == "4"
    )
    role = "thermostat" if classic_thermostat or thermostat_supported(profile) else channel or attrs.get("subType", "")
    model = attrs.get("model") or profile.get("device_model") or ""
    if not model and not role and (
        profile["type"] in {"CUL_WS", "TSCUL_WS"}
        or profile["type"] in {"HMS", "TSHMS"} and "temperature" in profile["readings"]
    ):
        role = "profile:weather"
    if not model and not role and profile.get("functional_template"):
        role = "profile:" + profile["functional_template"]
    return [profile["type"], model, role]


def shareable_class(profile):
    module, model, role = device_class(profile)
    if module == "HMCCUCHN":
        return bool(model and role)
    if module == "HMCCUDEV":
        return bool(model)
    return bool(model or role)


def rule_matches(rule, device, profile):
    if rule["scope"] == "device":
        return device == rule["match"]
    if rule["scope"] == "selected":
        return device in rule["match"]
    if not rule["future"] and device not in rule["devices"]:
        return False
    if rule["scope"] == "type":
        return profile["type"] == rule["match"]
    match = device_class(profile)
    if match == rule["match"]:
        return True
    # Preserve existing class rules saved before inherited models were used.
    return not profile["attributes"].get("model") and [match[0], "", match[2]] == rule["match"]


def choices(rule_list, device, profile):
    """Merge per key so local exclusions survive changes to a template."""
    merged = {}
    for scope, future in (("type", None), ("class", True), ("class", False), ("selected", None), ("device", None)):
        level = {}
        for rule in rule_list:
            if (not rule.get("assignment") and rule["scope"] == scope
                    and (future is None or bool(rule["future"]) == future) and rule_matches(rule, device, profile)):
                for key, value in rule["items"].items():
                    if key in level and level[key] != value:
                        raise HomeAssistantError(f"Konflikt zwischen Vorlagen für {profile['name']}: {key}")
                    level[key] = value
        merge_items(merged, level)
    return merged


def merge_items(items, overrides):
    for key, item in overrides.items():
        base = items.get(key, {}) if item["kind"] == "reading" else {}
        inherited = {field: base[field] for field in ("sensor_metadata", "label")
                     if field in base and (field not in item or field == "label" and not item[field])}
        items[key] = {**item, **inherited}


def template_assignment(rules, device, profile):
    priority = {"type": 0, "class": 1, "selected": 2, "device": 3}
    return max(
        (rule for rule in reversed(rules) if rule.get("assignment") and rule_matches(rule, device, profile)),
        key=lambda rule: (priority[rule["scope"]], rule["scope"] == "class" and not rule["future"]), default=None,
    )


def technical(profile, command):
    return command.lower() in {"raw", "reset", "factoryreset", "pair", "unpair", "regset", "regbulk",
                               "saveconfig", "fwupdate", "devicerename", "peerbulk", "peersmart",
                               "assignhmkey", "getregraw"} or (
        profile["type"].lower() in {"cul", "tscul", "signalduino", "hmlan", "hmuartlgw"}
    )


def command_modes(kind, fields, reading):
    modes = ["button"]
    if fields != []:
        modes.insert(0, "form")
    if kind == "set" and (fields is None or len(fields) == 1):
        modes.insert(0, "direct")
    if kind == "set" and reading and fields and len(fields) == 1:
        field = fields[0]
        mode = field["type"]
        if mode in FEEDBACK_MODES and not field.get("custom") and (mode != "number" or slider_field(field)):
            modes.append(mode)
            if mode == "number":
                modes.append("number_slider")
    return modes


def default_reading(name, profile):
    if profile["type"] in {"HMCCUDEV", "HMCCUCHN"}:
        datapoint = name.rsplit(".", 1)[-1]
        if datapoint in {"ACTUAL_TEMPERATURE", "HUMIDITY", "POWER", "ENERGY_COUNTER", "CURRENT", "VOLTAGE", "FREQUENCY"}:
            return "sensor"
    if profile["type"] == "CUL_HM" and name == "energyCalc":
        return "sensor"
    if name in {"temperature", "measured-temp", "humidity", "actuator", "ValvePosition", "pct",
                "power", "energy", "voltage", "current", "frequency", "pressure", "brightness", "state"}:
        return "sensor"
    if name.lower() in {"battery", "batterylevel", "rssi", "motorerr", "commstate"}:
        return "diagnostic"
    return "off"


def needed_readings(profile):
    """Keep feedback needed by the existing native entities."""
    result = {"state"} if {"turn_on", "turn_off"} <= profile["actions"].keys() else set()
    if result:
        result.add(switch_feedback(profile))
    if thermostat_supported(profile):
        if profile["type"] == "MAX":
            result.update({"temperature", "desiredTemperature", "mode", "valveposition"} & set(profile["readings"]))
        else:
            result.update(("measured-temp", "desired-temp"))
            result.update({"mode", "controlMode", "actuator", "ValvePosition", "humidity"} & set(profile["readings"]))
    if dimmer := dimmer_profile(profile):
        result.add(dimmer[1])
    return result


def command_feedback(item):
    """Return the subscribed reading used by a direct control or a Get observer."""
    if item["mode"] in FEEDBACK_MODES:
        return item["reading"]
    return item.get("observe")


class Publications:
    def __init__(self, runtime):
        self.runtime = runtime
        self.store = Store(runtime.hass, 1, f"{DOMAIN}.{runtime.entry.entry_id}.publications")
        self.data = {"rules": [], "legacy": []}
        self.library = TemplateLibrary(runtime.hass.config.path(DOMAIN, "Vorlagen", runtime.entry.entry_id))
        self.pending = {}
        self.lock = Lock()
        self.resolved = {}

    async def load_library(self):
        if not self.library.loaded:
            await self.runtime.hass.async_add_executor_job(self.library.load)
        self.data["templates"] = self.library.documents

    async def load(self):
        await self.load_library()
        data = await self.store.async_load()
        if data is None:
            self.data["legacy"] = list(self.runtime.selected)
            await self.store.async_save(self.data)
        else:
            rules = []
            for rule in data["rules"]:
                if not rule.get("assignment") and (layout := rule["items"].get("layout:device")):
                    rules.append({**rule, "id": f"{rule['id']}-layout", "assignment": True,
                                  "items": {"layout:device": layout}})
                    items = {key: item for key, item in rule["items"].items() if key != "layout:device"}
                    if items:
                        rules.append({**rule, "items": items})
                else:
                    rules.append(rule)
            for key, template in data.get("templates", {}).items():
                if key not in self.library.documents:
                    doc = {"schema": 1, "key": key, "origin": "custom", "version": next_version(),
                           "name": template["name"], "items": list(template["items"].values())}
                    await self.runtime.hass.async_add_executor_job(self.library.write, doc)
            stored = {key: value for key, value in data.items() if key != "templates"}
            if "templates" in data:
                await self.store.async_save(stored)
            self.data = {**stored, "rules": rules, "templates": self.library.documents}

    def readings(self, device, profile, items):
        legacy = device in self.data["legacy"]
        modes = {
            name: items.get(f"reading:{name}", {}).get("mode", "sensor" if legacy else default_reading(name, profile))
            for name in profile["readings"]
        }
        return modes

    async def resolve(self, device, profile, rules, templates=None):
        if templates is None:
            if not self.library.loaded:
                await self.load_library()
            templates = self.data["templates"]
        assignment = template_assignment(rules, device, profile)
        automatic = automatic_template(templates, device, profile)
        key = assignment.get("template") if assignment else None
        disabled = bool(assignment and assignment.get("disabled"))
        document = templates.get(key) if key else templates.get(automatic)
        if disabled:
            document = None
        role = template_role(document, device, profile)
        if document and not role and document["origin"] == "custom" and not document.get("roles"):
            role = template_role(templates.get(automatic), device, profile)
        preset = {}
        if document:
            for item in [*document.get("items", []), *role.get("items", [])]:
                merge_items(preset, {item["key"]: item})
        if assignment:
            merge_items(preset, assignment["items"])
        overrides = preset
        merge_items(overrides, choices(rules, device, profile))
        manual = overrides.get("layout:device", {}).get("mode")
        if manual and manual != role.get("layout"):
            alternate = next((entry for entry in templates.values()
                              if entry.get("default_role") == manual
                              and entry["origin"] in {"default", "working"}
                              and entry["key"] != "metering-outlet"), None)
            role = template_role(alternate, device, profile)
        layout = manual or role.get("layout")
        items = {}
        by_kind = {}
        for name, setting in role_readings(role, profile).items():
            if name in profile["readings"]:
                key = f"reading:{name}"
                fields = {"mode": setting} if isinstance(setting, str) else setting
                item = {"key": key, "kind": "reading", "name": name, **fields}
                if (unit_from := item.pop("unit_from", None)) and "sensor_metadata" in item:
                    item["sensor_metadata"] = calculator_metadata(profile, item["sensor_metadata"], unit_from)
                items[key] = item
        for control in role_controls(role):
            if control.device_type and control.device_type != profile["type"]:
                continue
            if (control.kind == "set" and control.name == "toggle" and control.label == "Umschalten"
                    and profile["actions"].get("toggle") == {}):
                continue
            key = f"{control.kind}:{control.name}:default"
            if key in overrides:
                continue
            if control.kind not in by_kind:
                by_kind[control.kind] = await self.runtime.command_catalog(device, profile, control.kind)
            description = by_kind[control.kind].get(control.name)
            if description and (item := control_default(control, description, profile["readings"])):
                items[key] = {**item, "key": key}
        merge_items(items, overrides)
        readings = self.readings(device, profile, items)
        commands = {}
        skipped = {}
        cover = None
        if layout in ACTUATOR_LAYOUTS:
            catalog = await self.runtime.command_catalog(device, profile, "set")
            by_kind["set"] = catalog
            manual = overrides.get("layout:device", {})
            names = manual.get("arguments") or cover_commands(layout, catalog, profile["type"] == "FS20")
            if (names[0] and names[1] and names[0] != names[1]
                    and all(not name or accepts_no_arguments(catalog.get(name)) for name in names)):
                cover = names
            else:
                skipped["layout:device"] = "Fahrbefehle fehlen oder benötigen Eingaben"
        for key, item in items.items():
            kind = item["kind"]
            command = item["name"]
            if kind == "layout":
                if item["mode"] == "thermostat" and not thermostat_supported(profile):
                    skipped[key] = "Heizungssteuerung fehlt auf diesem FHEM-Kanal. Die Vorlage kann trotzdem übernommen werden."
                continue
            if item["mode"] == "off":
                continue
            if kind == "reading":
                if command not in readings:
                    skipped[key] = "Reading fehlt"
                continue
            if kind not in by_kind:
                by_kind[kind] = await self.runtime.command_catalog(device, profile, kind)
            if command not in by_kind[kind]:
                skipped[key] = "Befehl fehlt"
                continue
            fields = by_kind[kind][command]["fields"]
            reading = item.get("reading") or command
            mode = item["mode"]
            if mode not in command_modes(kind, fields, reading in readings):
                skipped[key] = "Bedienelement nicht kompatibel"
                continue
            if mode == "button" and item.get("typed"):
                try:
                    serialize_inputs(fields, item["arguments"])
                except ValueError:
                    skipped[key] = "Argumente nicht kompatibel"
                    continue
            elif mode == "button" and fields == [] and item["arguments"]:
                # Stored presets from older versions contain wire arguments.
                skipped[key] = "Argumente nicht kompatibel"
                continue
            if mode in {"form", "direct"}:
                requested = item.get("input_modes", [])
                form_fields = fields if fields is not None else item.get("input_fields") or [
                    {"type": "text", "modes": ["text"]} for _ in requested
                ]
                if not form_fields or len(requested) != len(form_fields) or (mode == "direct" and len(requested) != 1) or any(
                    mode not in input_modes(field) for mode, field in zip(requested, form_fields, strict=True)
                ):
                    skipped[key] = "Eingabefelder nicht kompatibel"
                    continue
                item = {**item, "form_fields": form_fields}
            observe = item.get("reading") if kind == "get" else None
            if observe and observe not in readings:
                skipped[key] = "Reading für Abfrage fehlt"
                continue
            commands[key] = {**item, "fields": fields, "reading": reading, "observe": observe}
        return {"readings": readings, "commands": commands, "skipped": skipped, "choices": items,
                "cover": cover, "layout": layout, "automatic_template": automatic,
                "effective_template": document["key"] if document else None,
                "role": role.get("name"), "model": model_of(profile), "template_disabled": disabled}

    async def sync(self, profiles, *, partial=False, failures=None):
        await self.load_library()
        documents = self.data["templates"]
        keys = set()
        for device, profile in profiles.items():
            automatic = automatic_template(documents, device, profile)
            profile["functional_template"] = automatic if not model_of(profile) else None
            assignment = template_assignment(self.data["rules"], device, profile) or {}
            if not assignment.get("disabled"):
                key = assignment.get("template") or automatic
                if key:
                    keys.add(key)
        if (keys & self.library.defaults.keys()) - self.library.files.keys() - self.library.blocked:
            await self.runtime.hass.async_add_executor_job(self.library.ensure_copies, keys)
            self.data["templates"] = self.library.documents
        async def resolve(device):
            try:
                return await self.resolve(device, profiles[device], self.data["rules"])
            except (BridgeError, TimeoutError) as err:
                if failures is None or (isinstance(err, BridgeError) and str(err) not in {
                        "bad_request", "not_allowed", "limit_exceeded", "catalog_changed"}):
                    raise
                failures[device] = str(err) or type(err).__name__
                return None

        resolved = {}
        for batch in batched(profiles, 4):
            results = await gather(*(resolve(device) for device in batch))
            resolved.update((device, result) for device, result in zip(batch, results, strict=True)
                            if result is not None)
        if partial:
            self.resolved.update(resolved)
        else:
            self.resolved = resolved

    def subscription(self, device, profile):
        resolved = self.resolved[device]
        names = {name for name, mode in resolved["readings"].items() if mode != "off"}
        if resolved["cover"]:
            names.add("state")
        names.update(needed_readings(profile))
        names.update(filter(None, map(command_feedback, resolved["commands"].values())))
        return sorted(names.intersection(profile["readings"]))

    def reconcile_registry(self):
        """Remove withdrawn publications while retaining IDs of active entities."""
        registry = er.async_get(self.runtime.hass)
        by_prefix = {
            self.runtime.identifier(device): result for device, result in self.resolved.items()
        }
        dimmers = {self.runtime.identifier(device) for device, _ in dimmer_outputs(self.runtime)}
        for entry in er.async_entries_for_config_entry(registry, self.runtime.entry.entry_id):
            if entry.domain == "button" and "/action/" in entry.unique_id:
                prefix, _, action = entry.unique_id.partition("/action/")
                result = by_prefix.get(prefix)
                if ((action == "toggle" and prefix in dimmers)
                        or (result is not None and action in redundant_button_actions(result))):
                    registry.async_remove(entry.entity_id)
                continue
            prefix, separator, tail = entry.unique_id.partition("/reading/")
            if not separator:
                prefix, separator, tail = entry.unique_id.partition("/published_input/")
                if separator:
                    result = by_prefix.get(prefix)
                    if not result:
                        continue
                    key, _, slot = tail.rpartition("/")
                    item = result["choices"].get(key, {})
                    modes = item.get("input_modes", []) if item.get("mode") in {"form", "direct"} else []
                    if not slot.isdecimal() or int(slot) >= len(modes) or INPUT_DOMAINS.get(modes[int(slot)]) != entry.domain:
                        registry.async_remove(entry.entity_id)
                    continue
                if entry.domain == "cover" and entry.unique_id.endswith("/cover"):
                    result = by_prefix.get(entry.unique_id.removesuffix("/cover"))
                    if result is not None and not result["cover"]:
                        registry.async_remove(entry.entity_id)
                    continue
                prefix, _, tail = entry.unique_id.partition("/published/")
                result = by_prefix.get(prefix)
                if not result:
                    continue
                item = result["choices"].get(tail)
                mode = item["mode"] if item else None
                domain = {"form": "button", "number_slider": "number"}.get(mode, mode)
                if domain != entry.domain:
                    registry.async_remove(entry.entity_id)
                continue
            result = by_prefix.get(prefix)
            if not result or tail not in result["readings"]:
                continue
            mode = result["readings"][tail]
            domain = "binary_sensor" if mode == "binary" else "sensor"
            if mode in {"internal", "off"} or entry.domain != domain:
                registry.async_remove(entry.entity_id)
            elif entry.hidden_by == er.RegistryEntryHider.INTEGRATION and mode != "hidden":
                registry.async_update_entity(entry.entity_id, hidden_by=None)

    async def preview(self, device, scope, future, draft, rule_id=None, remove=False, *,
                      assignment=False, template_id=None, devices=(), template_name=None, reset_keys=(),
                      disabled=False, template_role_id=None, copy_from=None):
        profile = self.runtime.profiles[device]
        targets = sorted(set(devices))
        match = {"device": device, "type": profile["type"], "class": device_class(profile), "selected": targets}[scope]
        async with self.lock:
            templates = self.data.get("templates", {})
            if template_name is not None:
                if template_id and template_id not in templates:
                    raise HomeAssistantError("Die Vorlage ist nicht mehr verfügbar.")
                template_id = template_id or template_key(template_name, templates)
                original = templates.get(template_id)
                source = templates.get(copy_from) if copy_from and not original else None
                if copy_from and source is None:
                    raise HomeAssistantError("Die Quellvorlage ist nicht verfügbar.")
                if source:
                    original = {**template_body(source), "key": template_id, "name": template_name,
                                "origin": "custom", "automatic": False, "version": next_version()}
                doc = dict(original or {"schema": 1, "key": template_id, "origin": "custom",
                                        "name": template_name, "version": next_version(), "items": []})
                if doc["origin"] == "default":
                    doc = working_copy(doc)
                target = doc
                if template_role_id:
                    roles = dict(doc.get("roles", {}))
                    if template_role_id not in roles:
                        raise HomeAssistantError("Die Kanalrolle ist nicht verfügbar.")
                    target = roles[template_role_id] = dict(roles[template_role_id])
                    doc["roles"] = roles
                items = {item["key"]: item for item in target.get("items", [])}
                for item in draft:
                    if item["mode"] == "inherit":
                        items.pop(item["key"], None)
                    else:
                        items[item["key"]] = item
                target["items"] = list(items.values())
                doc["name"] = template_name
                if original and template_body(doc) != template_body(original):
                    doc["version"] = next_version(doc["version"])
                updated = {**templates, template_id: validate_document(doc)}
                rules = self.data["rules"]
                if reset_keys:
                    assigned = template_assignment(rules, device, profile)
                    if not assigned or assigned.get("template") != template_id:
                        raise HomeAssistantError("Die Vorlage muss diesem Gerät zugewiesen sein.")
                    copied = set(reset_keys) & items.keys()
                    rules = []
                    for rule in self.data["rules"]:
                        if rule.get("assignment") or rule["scope"] != "device" or rule["match"] != device:
                            rules.append(rule)
                            continue
                        remaining = {key: item for key, item in rule["items"].items() if key not in copied}
                        if remaining:
                            rules.append({**rule, "items": remaining})
                candidates = self.template_candidates(template_id, updated, rules)
                return await self._preview_changes(device, rules, updated, candidates, template_id,
                                                   file_change=("write", updated[template_id]))
            if template_id and (not assignment or template_id not in templates):
                raise HomeAssistantError("Die Vorlage ist nicht mehr verfügbar.")
            if scope == "selected" and (not targets or not set(targets) <= self.runtime.profiles.keys()):
                raise HomeAssistantError("Wähle importierte Geräte aus.")
            existing = next((rule for rule in self.data["rules"] if rule["id"] == rule_id), None)
            if (rule_id or remove) and existing is None:
                raise HomeAssistantError("Vorlage wurde bereits entfernt.")
            if existing:
                if (existing["scope"] != scope or bool(existing.get("assignment")) != assignment
                        or not rule_matches({**existing, "future": True}, device, profile)):
                    raise HomeAssistantError("Diese Anpassung gehört zu einem anderen Geltungsbereich.")
                if scope != "selected":
                    match = existing["match"]
            elif scope == "class" and not shareable_class(profile):
                raise HomeAssistantError("Für dieses Gerät ist keine eindeutige Geräteklasse verfügbar.")
            items = dict(existing["items"]) if existing and not assignment else {}
            for item in draft:
                key = item["key"]
                if assignment and item["kind"] != "layout":
                    raise HomeAssistantError("Eine Zuweisung enthält nur die Gerätevorlage.")
                if item["mode"] == "inherit":
                    items.pop(key, None)
                else:
                    items[key] = item
            rule = {
                "id": rule_id or uuid4().hex, "scope": scope, "match": match,
                "future": future, "devices": [], "items": items,
                **({"assignment": True, "template": template_id, "disabled": disabled} if assignment else {}),
            }
            candidates = {
                candidate: candidate_profile for candidate, candidate_profile in self.runtime.profiles.items()
                if rule_matches({**rule, "future": True}, candidate, candidate_profile)
            }
            rule["devices"] = sorted(set(candidates) | set(existing["devices"] if existing else ()))
            rules = [
                other for other in self.data["rules"] if other["id"] != rule_id
                and not (assignment and other.get("assignment") and other["scope"] == scope and other["match"] == match)
            ]
            if (items or assignment) and not remove:
                rules.append(rule)
            if existing:
                candidates.update({key: candidate for key, candidate in self.runtime.profiles.items()
                                   if rule_matches(existing, key, candidate)})
            return await self._preview_changes(device, rules, templates, candidates)

    async def preview_device(self, device, items, template=None, *, scope="device", future=False,
                             devices=(), shared_id=None):
        """Review a draft or the changed scope of an existing customization."""
        async with self.lock:
            profiles = self.runtime.profiles
            profile = profiles[device]
            rules = list(self.data["rules"])
            documents = self.data["templates"]
            targets = sorted(set(devices))
            if scope == "class" and not shareable_class(profile):
                raise HomeAssistantError("Für dieses Gerät ist keine eindeutige Geräteklasse verfügbar.")
            if scope == "selected" and (not targets or not set(targets) <= profiles.keys()):
                raise HomeAssistantError("Wähle mindestens ein importiertes Gerät aus.")
            match = {"device": device, "class": device_class(profile), "selected": targets}[scope]
            preview_scope = {"scope": scope, "match": match, "future": True}
            candidates = {key: value for key, value in profiles.items() if rule_matches(preview_scope, key, value)}
            affected = set(candidates)
            if shared_id:
                previous = next((rule for rule in rules if rule["id"] == shared_id and not rule.get("assignment")
                                 and rule["scope"] != "device" and rule_matches(rule, device, profile)), None)
                if previous is None:
                    raise HomeAssistantError("Die gemeinsame Anpassung ist nicht mehr verfügbar.")
                rules.remove(previous)
                affected.update(key for key, value in profiles.items() if rule_matches(previous, key, value))
                items = list(previous["items"].values())
                template = None
            if template is not None and template.get("key") and template["key"] not in documents:
                raise HomeAssistantError("Die Vorlage ist nicht mehr verfügbar.")
            for assignment, changes in ((False, items), (True, template)):
                if not changes:
                    continue
                previous = [rule for rule in rules if rule["scope"] == scope
                            and rule["match"] == match and bool(rule.get("assignment")) == assignment]
                same_scope = [rule for rule in previous if scope != "class" or bool(rule["future"]) == future]
                if assignment:
                    key, disabled = template.get("key"), template["disabled"]
                    layout = template.get("layout")
                    if layout and layout["kind"] != "layout":
                        raise HomeAssistantError("Die Vorlagenauswahl enthält keine gültige Gerätedarstellung.")
                    overrides = {layout["key"]: layout} if layout and layout["mode"] != "inherit" else {}
                else:
                    overrides = {key: item for rule in same_scope for key, item in rule["items"].items()}
                    for item in items:
                        if item["mode"] == "inherit":
                            overrides.pop(item["key"], None)
                        else:
                            merge_items(overrides, {item["key"]: item})
                rules = [rule for rule in rules if rule not in same_scope]
                affected.update(key for key, value in profiles.items()
                                if any(rule_matches(rule, key, value) for rule in same_scope))
                if overrides or assignment:
                    rules.append({"id": same_scope[-1]["id"] if same_scope else uuid4().hex, "scope": scope,
                                  "match": match, "future": future, "devices": list(candidates), "items": overrides,
                                  **({"assignment": True, "template": key, "disabled": disabled} if assignment else {})})
            result = await self._preview_changes(device, rules, documents, {key: profiles[key] for key in sorted(affected)})
            result["affected"] = [entry["name"] for entry in candidates.values()]
            keys = {item["key"] for item in items}
            if scope != "device":
                for row, target in zip(result["rows"], (key for key in sorted(affected) if key in self.resolved), strict=True):
                    if target not in candidates:
                        continue
                    exceptions = {item["name"] for rule in rules if rule["scope"] == "device"
                                  and rule["match"] == target and not rule.get("assignment")
                                  for key, item in rule["items"].items() if key in keys}
                    if template and any(rule["scope"] == "device" and rule["match"] == target
                                        and rule.get("assignment") for rule in rules):
                        exceptions.add("Gerätevorlage")
                    if exceptions:
                        row["customizations"] = sorted(exceptions)
            return result

    def template_candidates(self, key, documents, rules):
        return {
            device: profile for device, profile in self.runtime.profiles.items()
            if ((self.resolved.get(device) or {}).get("effective_template") == key
                or ((rule := template_assignment(rules, device, profile) or {}).get("template") == key)
                or (not rule.get("template") and not rule.get("disabled")
                    and (automatic_template(documents, device, profile) == key
                         or (key in documents and documents[key].get("automatic", documents[key]["origin"] != "custom")
                             and matched_rule(documents[key], device, profile)))))
        }

    async def preview_library(self, action, key=None, content=None, name=None, draft=None):
        async with self.lock:
            documents = self.data["templates"]
            rules = self.data["rules"]
            current = documents.get(key)
            if action in {"reset", "delete", "copy"} and current is None:
                raise HomeAssistantError("Die Vorlage ist nicht mehr verfügbar.")
            if action == "reset":
                if key not in self.library.defaults:
                    raise HomeAssistantError("Für diese Vorlage gibt es keinen mitgelieferten Standard.")
                updated = {**documents, key: self.library.defaults[key]}
                file_change = ("remove", key)
            elif action == "delete":
                if current["origin"] != "custom":
                    raise HomeAssistantError("Verwende für mitgelieferte Vorlagen „Auf Standard zurücksetzen“.")
                updated = {item: doc for item, doc in documents.items() if item != key}
                rules = [rule for rule in rules if rule.get("template") != key]
                file_change = ("remove", key)
            else:
                if action == "create":
                    if not name:
                        raise HomeAssistantError("Gib einen Vorlagennamen ein.")
                    key = template_key(name, documents)
                    doc = {"schema": 1, "key": key, "name": name, "origin": "custom",
                           "version": next_version(), "items": []}
                elif action == "copy":
                    name = name or current["name"] + " (Kopie)"
                    key = template_key(name, documents)
                    doc = {**template_body(current), "key": key, "name": name, "origin": "custom",
                           "automatic": False, "version": next_version()}
                elif action == "edit":
                    if key and current is None:
                        raise HomeAssistantError("Die Vorlage ist nicht mehr verfügbar.")
                    if not key:
                        key = template_key(str(draft.get("name") or ""), documents)
                    if current and current["origin"] == "default":
                        current = working_copy(current)
                    metadata = {"schema": 1, "key": key, "origin": "custom", "version": next_version()}
                    if current:
                        metadata.update({field: current[field] for field in
                                         ("origin", "version", "base_version") if field in current})
                    body = {field: draft[field] for field in
                            ("name", "description", "automatic", "match", "default_role", "roles", "items")
                            if field in draft}
                    doc = validate_document({**body, **metadata})
                    if current and template_body(doc) != template_body(current):
                        doc["version"] = next_version(doc["version"])
                    if doc.get("automatic") and not doc.get("match"):
                        raise HomeAssistantError("Wähle mindestens eine Zuordnungsregel für den automatischen Standard.")
                else:
                    incoming = parse_document(content or "")
                    key = key or incoming["key"]
                    current = documents.get(key)
                    if current:
                        doc = working_copy(current) if current["origin"] == "default" else dict(current)
                        doc = {**template_body(incoming), "key": key, "origin": doc["origin"],
                               "version": doc["version"],
                               **({"base_version": doc["base_version"]} if "base_version" in doc else {})}
                        if template_body(doc) != template_body(current):
                            doc["version"] = next_version(doc["version"])
                    else:
                        doc = {**template_body(incoming), "origin": "custom", "automatic": False,
                               "version": next_version()}
                doc = validate_document(doc)
                updated = {**documents, key: doc}
                file_change = ("write", doc)
            candidates = self.template_candidates(key, updated, rules)
            return await self._preview_changes(None, rules, updated, candidates, key, file_change=file_change)

    async def _preview_changes(self, device, rules, templates, candidates, edited_template=None, *, file_change=None):
        rows = []
        for batch in batched(candidates, 4):
            results = await gather(*(self.resolve(candidate, candidates[candidate], rules, templates) for candidate in batch))
            for candidate, target in zip(batch, results, strict=True):
                prior = self.resolved.get(candidate)
                if prior is None:
                    continue
                differences = [
                    f"{key}: {prior['readings'].get(key, '–')} → {target['readings'].get(key, '–')}"
                    for key in sorted(prior["readings"].keys() | target["readings"].keys())
                    if prior["readings"].get(key) != target["readings"].get(key)
                ]
                for key in sorted(prior["readings"].keys() & target["readings"].keys()):
                    old_metadata = prior["choices"].get(f"reading:{key}", {}).get("sensor_metadata", {})
                    new_metadata = target["choices"].get(f"reading:{key}", {}).get("sensor_metadata", {})
                    for field in ("device_class", "state_class", "unit_of_measurement"):
                        if old_metadata.get(field) != new_metadata.get(field):
                            differences.append(
                                f"{key} · {field}: {old_metadata.get(field, '–')} → {new_metadata.get(field, '–')}"
                            )
                if (prior.get("cover") != target["cover"] or prior.get("layout") != target["layout"]
                        or prior.get("effective_template") != target["effective_template"]
                        or bool(prior.get("template_disabled")) != target["template_disabled"]):
                    def name(result):
                        if result.get("template_disabled"):
                            return "Keine Vorlage"
                        key = result.get("effective_template")
                        return templates.get(key, self.data["templates"].get(key, {})).get("name") or result.get("layout") or "Automatisch"
                    differences.append(f"Vorlage: {name(prior)} → {name(target)}")
                for key in sorted(prior["commands"].keys() | target["commands"].keys()):
                    previous = prior["commands"].get(key)
                    current = target["commands"].get(key)
                    if previous != current:
                        operation = "ändern" if previous and current else "hinzufügen" if current else "entfernen"
                        differences.append(f"{(current or previous)['label']}: {operation}")
                samples = []
                for reading, mode in sorted(target["readings"].items()):
                    if mode in {"off", "internal"}:
                        continue
                    previous = prior["choices"].get(f"reading:{reading}", {})
                    current = target["choices"].get(f"reading:{reading}", {})
                    if prior["readings"].get(reading) == mode and previous == current:
                        continue
                    metadata = current.get("sensor_metadata", {})
                    samples.append({
                        "name": current.get("label") or reading,
                        "value": self.runtime.values.get((candidate, reading)),
                        "unit": metadata.get("unit_of_measurement"),
                        "device_class": metadata.get("device_class"),
                    })
                rows.append({
                    "name": candidates[candidate]["name"], "samples": samples,
                    "skipped": target["skipped"],
                    "changes": len(differences), "details": differences,
                    **({"customizations": sorted({item["name"] for item in choices(
                        rules, candidate, candidates[candidate]
                    ).values()})} if edited_template else {}),
                })
        token = uuid4().hex
        now = monotonic()
        self.pending = {key: value for key, value in self.pending.items() if now - value[0] < 180}
        if len(self.pending) >= 16:
            self.pending.pop(next(iter(self.pending)))
        self.pending[token] = (now, self.data, rules, device, edited_template, file_change, tuple(candidates))
        result = {"token": token, "rows": rows}
        if device is not None and edited_template in templates and device not in candidates:
            profile = self.runtime.profiles[device]
            probe = {"id": "preview", "scope": "device", "match": device, "future": False,
                     "devices": [device], "items": {}, "assignment": True, "template": edited_template}
            reference = await self.resolve(device, profile, [*rules, probe], templates)
            result["reference"] = {"name": profile["name"], "skipped": reference["skipped"]}
        return result

    async def commit(self, token, device, *, with_sources=False):
        async with self.lock:
            preview = self.pending.pop(token, None)
            if preview is None or preview[3] != device or preview[1] is not self.data or monotonic() - preview[0] > 180:
                raise HomeAssistantError("Die Vorschau ist abgelaufen. Bitte erneut prüfen.")
            rules = preview[2]
            file_change = preview[5]
            if file_change:
                operation, argument = file_change
                if operation == "write":
                    await self.runtime.hass.async_add_executor_job(self.library.write, argument)
            stored = {key: value for key, value in self.data.items() if key != "templates"}
            if rules != stored["rules"]:
                await self.store.async_save({**stored, "rules": rules})
            if file_change and operation == "remove":
                try:
                    await self.runtime.hass.async_add_executor_job(self.library.remove, argument)
                except OSError:
                    if rules != stored["rules"]:
                        await self.store.async_save(stored)
                    raise
            self.data = {**stored, "rules": rules, "templates": self.library.documents}
            return (preview[4], preview[6]) if with_sources else preview[4]
