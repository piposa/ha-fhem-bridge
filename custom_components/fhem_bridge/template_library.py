"""Validated YAML defaults and writable, versioned device templates."""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from unicodedata import normalize

import voluptuous as vol
import yaml

from .calculator import CALCULATOR_UNITS
from .publication_schema import INPUT_DOMAINS, ITEM_SCHEMA, READING_MODES, SENSOR_METADATA
from .profiles import thermostat_supported
from .templates import DEVICE_LAYOUTS, Control, METER_READINGS, meter_kind

DEFAULT_PATH = Path(__file__).with_name("Vorlagen") / "Default"
_LOGGER = logging.getLogger(__name__)
_KEY = re.compile(r"[a-z0-9][a-z0-9-]{0,99}\Z")
_VERSION = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)-(\d{2,})")
MAX_FILE_SIZE = 1024 * 1024
LAYOUT_ROLES = {"metadata", "threshold"}


def version_order(version):
    if not isinstance(version, str) or not (match := _VERSION.fullmatch(version)):
        raise ValueError("Ungültige Vorlagenversion.")
    return datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%SZ"), int(match[2])


def next_version(*versions):
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    latest = max(map(version_order, filter(None, versions)), default=(now, 0))
    stamp = max(now, latest[0])
    counter = latest[1] + 1 if latest[0] == stamp else 1
    return f"{stamp:%Y-%m-%dT%H:%M:%SZ}-{counter:02}"


_CONTROL = {
    vol.Required("name"): str, vol.Required("label"): str,
    vol.Optional("modes"): [vol.In(INPUT_DOMAINS)],
    vol.Optional("reading"): str, vol.Optional("kind"): vol.In(("set", "get")),
    vol.Optional("device_type"): str,
}
def stored_item(value):
    if isinstance(value, dict):
        value = {key: data for key, data in value.items() if key != "key"}
    return ITEM_SCHEMA(value)


_READING = vol.Any(vol.In(READING_MODES), {
    vol.Required("mode"): vol.In(READING_MODES),
    vol.Optional("label"): vol.All(str, vol.Length(max=100)),
    vol.Optional("sensor_metadata"): SENSOR_METADATA,
    vol.Optional("unit_from"): vol.In(CALCULATOR_UNITS),
})
_ROLE = {
    vol.Required("name"): str, vol.Optional("layout"): vol.In(DEVICE_LAYOUTS | LAYOUT_ROLES),
    vol.Optional("readings"): {str: _READING},
    vol.Optional("remaining_readings"): vol.In(READING_MODES),
    vol.Optional("reading_suffixes"): {vol.Match(r"_[A-Za-z0-9]+\Z"): _READING},
    vol.Optional("binary"): [str], vol.Optional("electrical_readings"): bool,
    vol.Optional("controls"): [_CONTROL], vol.Optional("items"): [stored_item],
}
_MATCH = {
    vol.Optional("type"): str, vol.Optional("models"): [str],
    vol.Optional("model_prefixes"): [vol.All(str, vol.Length(min=1))],
    vol.Optional("device"): str, vol.Optional("channel"): str,
    vol.Optional("readings"): [str], vol.Optional("actions"): [str],
    vol.Optional("role"): str, vol.Optional("channels"): {str: str},
    vol.Optional("thermostat"): bool, vol.Optional("thermostat_role"): str,
}
_DOCUMENT = vol.Schema({
    vol.Required("schema"): 1, vol.Required("key"): vol.Match(_KEY),
    vol.Required("name"): vol.All(str, str.strip, vol.Length(min=1, max=100)),
    vol.Optional("description"): str, vol.Optional("automatic"): bool,
    vol.Required("origin"): vol.In(("default", "working", "custom")),
    vol.Required("version"): str, vol.Optional("base_version"): str,
    vol.Optional("match"): [_MATCH], vol.Optional("default_role"): str,
    vol.Optional("roles"): {str: _ROLE}, vol.Optional("items"): [stored_item],
})


def validate_document(value):
    doc = _DOCUMENT(value)
    current = version_order(doc["version"])
    if doc["origin"] == "working":
        if current < version_order(doc.get("base_version")):
            raise ValueError("Arbeitsversion liegt vor ihrer Standardversion.")
    elif "base_version" in doc:
        raise ValueError("Nur eine Arbeitskopie hat eine Standardversion.")
    roles = doc.get("roles", {})
    for rule in doc.get("match", []):
        if not (rule.get("type") or rule.get("models") or rule.get("model_prefixes") or rule.get("device")
                or rule.get("readings") or rule.get("actions") or rule.get("thermostat")):
            raise ValueError("Zuordnungsregel ohne Geräte- oder Funktionsmerkmale.")
        for key in [rule.get("role"), rule.get("thermostat_role"), *rule.get("channels", {}).values()]:
            if key is not None and key not in roles:
                raise ValueError(f"Unbekannte Kanalrolle: {key}")
    if doc.get("default_role") and doc["default_role"] not in roles:
        raise ValueError("Unbekannte Standard-Kanalrolle.")
    return doc


def read_document(content):
    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValueError("Vorlagendatei ist zu groß.")
    if any(isinstance(token, (yaml.AliasToken, yaml.AnchorToken)) for token in yaml.scan(content)):
        raise ValueError("YAML-Anker und Aliase werden für Vorlagen nicht unterstützt.")
    return yaml.safe_load(content)


def parse_document(content):
    return validate_document(read_document(content))


def template_body(doc):
    return {key: value for key, value in doc.items() if key not in {"origin", "version", "base_version"}}


def template_key(name, existing):
    stem = re.sub(r"[^a-z0-9]+", "-", normalize("NFKD", name).encode("ascii", "ignore").decode().lower())
    stem = stem.strip("-")[:85] or "vorlage"
    key, suffix = stem, 2
    while key in existing:
        key = f"{stem}-{suffix}"
        suffix += 1
    return key


def working_copy(default):
    return {**default, "origin": "working", "base_version": default["version"]}


def model_of(profile):
    return str(profile["attributes"].get("model") or profile.get("device_model") or "")


def matched_rule(doc, device, profile, *, automatic=True):
    model = model_of(profile)
    channel = str(profile["attributes"].get("chanNo") or "00").zfill(2)
    candidates = []
    for rule in doc.get("match", []):
        if (rule.get("type", profile["type"]) != profile["type"]
                or ("device" in rule and rule["device"] not in {device, profile.get("name")})
                or rule.get("channel", channel).zfill(2) != channel
                or not set(rule.get("readings", ())) <= set(profile["readings"])
                or not set(rule.get("actions", ())) <= set(profile["actions"])
                or (rule.get("thermostat") and not thermostat_supported(profile))):
            continue
        models = {name.casefold() for name in rule.get("models", ())}
        prefixes = tuple(prefix.casefold() for prefix in rule.get("model_prefixes", ()))
        if (models or prefixes) and model.casefold() not in models and not model.casefold().startswith(prefixes):
            continue
        functional = rule.get("readings") or rule.get("actions") or rule.get("thermostat")
        if automatic and model and functional and not (models or prefixes) and not rule.get("device"):
            continue
        model_rank = 2 if model.casefold() in models else int(bool(prefixes))
        rank = (bool(rule.get("device")), model_rank, bool(rule.get("channel")), bool(functional), bool(rule.get("type")))
        candidates.append((rank, rule))
    return max(candidates, key=lambda item: item[0], default=None)


def automatic_template(documents, device, profile):
    model = model_of(profile).casefold()
    # A model-named default takes precedence over a generic default with the
    # same match, including older working copies of the generic template.
    matches = [(match[0] + (doc["origin"] == "custom", key == model), key) for key, doc in documents.items()
               if doc.get("automatic", doc["origin"] != "custom")
               and (match := matched_rule(doc, device, profile))]
    if not matches:
        return None
    rank, key = max(matches)
    return key if sum(candidate == rank for candidate, _ in matches) == 1 else None


def template_role_id(doc, device, profile):
    match = matched_rule(doc, device, profile, automatic=False)
    rule = match[1] if match else {}
    channel = str(profile["attributes"].get("chanNo") or "00").zfill(2)
    role = (rule.get("thermostat_role") if thermostat_supported(profile) else None)
    return role or rule.get("channels", {}).get(channel) or rule.get("role") or doc.get("default_role")


def template_role(doc, device, profile):
    return doc.get("roles", {}).get(template_role_id(doc, device, profile), {}) if doc else {}


def role_readings(role, profile):
    readings = profile["readings"]
    suffixes = role.get("reading_suffixes", {})
    modes = {
        name: suffixes["_" + name.rsplit("_", 1)[-1]]
        for name in readings if "_" in name and "_" + name.rsplit("_", 1)[-1] in suffixes
    }
    modes.update(role.get("readings", {}))
    layout = role.get("layout")
    if "state" in readings:
        if layout in {"cover", "awning", "switch", "outlet", "dimmer", "level"}:
            modes.setdefault("state", "internal")
        elif layout in {"temperature", "weather", "illuminance", "motion", "smoke", "meter"}:
            modes.setdefault("state", "diagnostic")
    if layout == "thermostat" and profile["type"] == "FHT" and {"temperature", "measured-temp"} <= set(readings):
        modes.setdefault("temperature", "internal")
    if role.get("electrical_readings"):
        for name in readings:
            if meter_kind(name) in METER_READINGS:
                modes.setdefault(name, "sensor")
    if layout == "contact":
        for name in ("state", "contact", "Window"):
            if name in readings:
                modes.setdefault(name, "diagnostic")
    if (binary := next((name for name in role.get("binary", ()) if name in readings), None)):
        modes[binary] = "binary"
    if remaining := role.get("remaining_readings"):
        for name in readings:
            modes.setdefault(name, remaining)
    return modes


def role_controls(role):
    return [Control(**{**item, "modes": tuple(item.get("modes", ()))}) for item in role.get("controls", ())]


class TemplateLibrary:
    """Keep file I/O off the event loop and catalog state scoped to one bridge."""

    def __init__(self, path, defaults=DEFAULT_PATH):
        self.path = Path(path)
        self.default_path = defaults
        self.defaults = {}
        self.files = {}
        self.paths = {}
        self.errors = {}
        self.blocked = set()
        self.updated = set()
        self.loaded = False

    @property
    def documents(self):
        return {**self.defaults, **self.files}

    @property
    def updates(self):
        return {key for key, doc in self.files.items()
                if doc["origin"] == "working" and key in self.defaults
                and version_order(self.defaults[key]["version"]) > version_order(doc["base_version"])}

    def _read(self, folder, origins):
        documents, paths, blocked = {}, {}, set()
        for path in sorted([*folder.glob("*.yaml"), *folder.glob("*.yml")]):
            key = None
            try:
                if path.is_symlink() or path.stat().st_size > MAX_FILE_SIZE:
                    raise ValueError("Unzulässige Vorlagendatei.")
                raw = read_document(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and isinstance(raw.get("key"), str) and _KEY.fullmatch(raw["key"]):
                    key = raw["key"]
                doc = validate_document(raw)
                if doc["origin"] not in origins:
                    raise ValueError("Vorlagenherkunft passt nicht zum Verzeichnis.")
                if key in paths or key in blocked:
                    documents.pop(key, None)
                    first = paths.pop(key, None)
                    if first:
                        self.errors[str(first)] = f"Doppelter Vorlagenschlüssel {key}"
                    blocked.add(key)
                    raise ValueError(f"Doppelter Vorlagenschlüssel {key}")
                documents[key], paths[key] = doc, path
            except (OSError, UnicodeError, ValueError, vol.Invalid, yaml.YAMLError) as err:
                if key is not None:
                    blocked.add(key)
                    documents.pop(key, None)
                    paths.pop(key, None)
                self.errors[str(path)] = str(err)
        return documents, paths, blocked

    def load(self):
        self.errors = {}
        self.defaults, _, _ = self._read(self.default_path, {"default"})
        self.files, self.paths, self.blocked = self._read(self.path, {"working", "custom"})
        for key, doc in list(self.files.items()):
            if doc["origin"] == "custom" and key in self.defaults:
                self.errors[str(self.paths[key])] = "Schlüssel wird bereits von einer mitgelieferten Vorlage verwendet."
                self.files.pop(key)
                self.blocked.add(key)
                continue
            default = self.defaults.get(key)
            if not default or doc["origin"] != "working":
                continue
            if doc["version"] == doc["base_version"]:
                try:
                    if doc["base_version"] == default["version"] and template_body(doc) != template_body(default):
                        self.write({**doc, "version": next_version(doc["version"])})
                    elif key in self.updates:
                        self.write(working_copy(default))
                        self.updated.add(key)
                except OSError as err:
                    self.errors[str(self.paths[key])] = str(err)
        self.loaded = True
        for path, error in self.errors.items():
            _LOGGER.warning("Could not apply FHEM template %s: %s", path, error)

    def write(self, doc):
        doc = validate_document(doc)
        key = doc["key"]
        if key in self.blocked:
            raise OSError(f"Vorlagenschlüssel {key} ist durch einen Dateikonflikt gesperrt.")
        self.path.mkdir(parents=True, exist_ok=True)
        path = self.paths.get(key)
        if path is None:
            stem = self.path / f"{key}.yaml"
            path, suffix = stem, 2
            while path.exists() or path.is_symlink():
                path = stem.with_name(f"{key}-{suffix}.yaml")
                suffix += 1
        raw = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False)
        temporary = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=self.path, delete=False) as file:
                temporary = Path(file.name)
                file.write(raw)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        self.files[key], self.paths[key] = doc, path

    def remove(self, key):
        if key in self.files:
            self.paths[key].unlink(missing_ok=True)
            del self.paths[key]
            del self.files[key]

    def ensure_copies(self, keys):
        for key in sorted((keys & self.defaults.keys()) - self.files.keys() - self.blocked):
            try:
                self.write(working_copy(self.defaults[key]))
            except OSError as err:
                self.errors[key] = str(err)
                _LOGGER.warning("Could not create FHEM template working copy %s: %s", key, err)
