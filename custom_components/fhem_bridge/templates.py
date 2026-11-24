"""Built-in device-page defaults selected by FHEM metadata."""

from dataclasses import dataclass

from .profiles import dimmer_profile, homematic_pwm_dimmer, input_modes

DEVICE_LAYOUTS = {"cover", "awning", "contact", "motion", "outlet", "thermostat", "switch",
                  "remote", "display", "smoke", "illuminance", "temperature", "meter", "level", "dimmer", "weather"}
PASSIVE_LAYOUTS = {"contact", "motion", "smoke", "remote", "display", "illuminance",
                   "temperature", "meter", "metadata", "threshold", "level", "weather"}
ACTUATOR_LAYOUTS = {"cover", "awning"}
COVER_BUTTON_COMMANDS = {"turn_on": "on", "turn_off": "off", "open": "open", "close": "close", "stop": "stop"}
METER_READINGS = {"power": "W", "voltage": "V", "current": "A", "frequency": "Hz"}
METER_ALIASES = {"p": "power", "u": "voltage", "i": "current", "frequ": "frequency", "freq": "frequency"}
def meter_kind(reading):
    name = reading.lower()
    return METER_ALIASES.get(name, name)


def accepts_no_arguments(description):
    if not description or description.get("technical"):
        return False
    fields = description["fields"]
    return fields is not None and all(field.get("optional") for field in fields)


def cover_commands(layout, catalog, fs20):
    """Prefer semantic commands. FS20 on retracts, off extends."""
    opening = ("open", "extend", "down") if layout == "awning" else ("open", "up")
    closing = ("close", "retract", "up") if layout == "awning" else ("close", "down")
    if fs20:
        opening += ("off",) if layout == "awning" else ("on",)
        closing += ("on",) if layout == "awning" else ("off",)
    return [next((name for name in names if accepts_no_arguments(catalog.get(name))), "")
            for names in (opening, closing, ("stop",))]


def dimmer_outputs(runtime):
    """Yield the physical channels exposed as native dimmers."""
    profiles = runtime.profiles
    explicit_outputs = {
        runtime.device_key(device)
        for device, profile in profiles.items()
        if runtime.publications.resolved[device]["layout"] == "dimmer" and dimmer_profile(profile)
        and str(profile["attributes"].get("chanNo") or "").lstrip("0") == "1"
    }
    for device, profile in profiles.items():
        layout = runtime.publications.resolved[device]["layout"]
        if layout in ACTUATOR_LAYOUTS | PASSIVE_LAYOUTS or layout == "switch":
            continue
        if (homematic_pwm_dimmer(profile) and not profile["attributes"].get("chanNo")
                and runtime.device_key(device) in explicit_outputs):
            continue
        dimmer = dimmer_profile(profile)
        if dimmer:
            yield device, dimmer


def redundant_button_actions(resolved):
    """Identify automatic buttons that already have an equivalent control."""
    covered = set(resolved["cover"] or ())
    redundant = {action for action, command in COVER_BUTTON_COMMANDS.items() if command in covered}
    if any(item["kind"] == "set" and item["name"] == "toggle"
           and item["mode"] == "button" and not item["arguments"]
           for item in resolved["commands"].values()):
        redundant.add("toggle")
    return redundant


@dataclass(frozen=True)
class Control:
    name: str
    label: str
    modes: tuple[str, ...] = ()
    reading: str | None = None
    kind: str = "set"
    device_type: str | None = None


def control_default(control, description, readings):
    """Use the preferred widget only when FHEM exposes matching arguments."""
    fields = description["fields"]
    if description.get("technical") or fields is None:
        return None
    if not fields:
        mode = "button"
    elif len(fields) != len(control.modes) or any(
        preferred not in input_modes(field)
        for preferred, field in zip(control.modes, fields, strict=True)
    ):
        return None
    elif (control.kind == "set" and control.modes == ("select",)
          and control.reading in readings and fields[0]["type"] == "select" and not fields[0].get("custom")):
        mode = "select"
    else:
        mode = "direct" if control.kind == "set" and len(fields) == 1 else "form"
    return {
        "kind": control.kind, "name": control.name, "label": control.label, "variant": "default",
        "mode": mode, "input_modes": list(control.modes), "arguments": [],
        **({"reading": control.reading} if mode == "select" else {}),
    }
