"""Shared validation for stored and submitted publications."""

import re

import voluptuous as vol

from homeassistant.components.sensor.const import DEVICE_CLASS_STATE_CLASSES, DEVICE_CLASS_UNITS

from .profiles import custom_input
from .templates import ACTUATOR_LAYOUTS, DEVICE_LAYOUTS

READING_MODES = {"sensor", "diagnostic", "hidden", "internal", "off", "binary"}
FEEDBACK_MODES = {"select", "number", "number_slider", "text"}
INPUT_DOMAINS = {"select": "select", "box": "number", "slider": "number", "text": "text"}
MAX_PUBLISHED_INPUTS = 32


SENSOR_CLASSES = {
    key: {
        "units": sorted(unit for unit in DEVICE_CLASS_UNITS.get(key, ()) if unit is not None),
        "state_classes": sorted(states),
    }
    for key, states in DEVICE_CLASS_STATE_CLASSES.items()
    if key in DEVICE_CLASS_UNITS or key == "monetary"
}
SENSOR_STATE_CLASSES = sorted({state for states in DEVICE_CLASS_STATE_CLASSES.values() for state in states})


def validate_sensor_metadata(metadata):
    device_class = metadata.get("device_class")
    state_class = metadata.get("state_class")
    unit = metadata.get("unit_of_measurement")
    if device_class:
        limits = SENSOR_CLASSES[device_class]
        if state_class and state_class not in limits["state_classes"]:
            raise vol.Invalid("State class is incompatible with device class")
        if device_class == "monetary":
            if not unit or not re.fullmatch(r"[A-Z]{3}", unit):
                raise vol.Invalid("Monetary sensors require an ISO currency code")
        elif unit not in DEVICE_CLASS_UNITS[device_class]:
            raise vol.Invalid("Unit is incompatible with device class")
    return metadata


SENSOR_METADATA = vol.All(vol.Schema({
    vol.Optional("device_class"): vol.In(SENSOR_CLASSES),
    vol.Optional("state_class"): vol.In(SENSOR_STATE_CLASSES),
    vol.Optional("unit_of_measurement"): vol.All(str, str.strip, vol.Length(min=1, max=64)),
}), validate_sensor_metadata)


def publication_item(item):
    kind, name, mode = item["kind"], item["name"], item["mode"]
    if kind != "reading" and "sensor_metadata" in item:
        raise vol.Invalid("Sensor metadata is only supported for readings")
    if kind == "layout":
        args = item["arguments"]
        if name != "device" or mode not in DEVICE_LAYOUTS | {"inherit"} or (
            mode in ACTUATOR_LAYOUTS and (
                len(args) != 3 or not all(isinstance(arg, str) for arg in args)
                or not args[0] or not args[1] or args[0] == args[1]
            )
        ):
            raise vol.Invalid("Invalid device template")
        return {**item, "key": "layout:device"}
    if not name or len(name) > 128:
        raise vol.Invalid("Invalid FHEM name")
    if kind == "reading":
        if mode not in READING_MODES | {"inherit"}:
            raise vol.Invalid("Invalid reading visibility")
        return {**item, "key": f"reading:{name}"}
    if mode not in FEEDBACK_MODES | {"button", "form", "direct", "off", "inherit"}:
        raise vol.Invalid("Invalid command control")
    if mode not in {"off", "inherit"} and (not item["label"].strip() or len(item["label"]) > 100):
        raise vol.Invalid("Invalid control label")
    if len(item["arguments"]) > 256 or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", item["variant"]):
        raise vol.Invalid("Invalid command arguments or variant")
    if item.get("input_fields"):
        try:
            item = {**item, "input_fields": [custom_input(field) for field in item["input_fields"]]}
        except ValueError as err:
            raise vol.Invalid(str(err)) from err
    return {**item, "key": f"{kind}:{name}:{item['variant']}"}


ITEM_SCHEMA = vol.All(vol.Schema({
    vol.Required("kind"): vol.In(("reading", "set", "get", "layout")),
    vol.Required("name"): str,
    vol.Required("mode"): str,
    vol.Optional("label", default=""): str,
    vol.Optional("variant", default="default"): str,
    vol.Optional("reading"): str,
    vol.Optional("sensor_metadata"): SENSOR_METADATA,
    vol.Optional("hidden", default=False): bool,
    vol.Optional("arguments", default=list): [vol.Any(str, int, float)],
    vol.Optional("typed", default=False): bool,
    vol.Optional("input_modes", default=list): vol.All(
        [vol.In(INPUT_DOMAINS)], vol.Length(max=MAX_PUBLISHED_INPUTS)
    ),
    vol.Optional("input_fields", default=list): vol.All([{
        vol.Required("type"): vol.In(("number", "select", "text")),
        vol.Optional("label"): vol.All(str, vol.Length(max=80)),
        vol.Optional("min"): vol.Any(int, float),
        vol.Optional("max"): vol.Any(int, float),
        vol.Optional("step"): vol.Any(int, float),
        vol.Optional("options"): vol.All([vol.All(str, vol.Length(max=120))], vol.Length(max=256)),
        vol.Optional("modes"): [vol.In(INPUT_DOMAINS)],
    }], vol.Length(max=MAX_PUBLISHED_INPUTS)),
}), publication_item)
