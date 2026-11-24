"""Interpret FHEM command descriptions and enrich known device families."""

from datetime import date, time
from decimal import Decimal
import math
import re


def finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def slider_field(field):
    """HA numeric entities require finite bounds and a real step."""
    return field["type"] == "number" and all(
        finite_number(field.get(key)) is not None for key in ("min", "max", "step")
    )


def input_modes(field):
    """The device page can render each argument as a native entity."""
    if field["type"] == "select" and not field.get("optional"):
        return ["select", "text"]
    if slider_field(field) and not field.get("optional"):
        return ["box", "slider", "text"]
    return ["text"]


def custom_input(field):
    """Validate a user-authored field for a command without a documented schema."""
    field = dict(field)
    if field["type"] == "number" and (
        not slider_field(field) or field["min"] >= field["max"] or field["step"] <= 0
    ):
        raise ValueError("Numeric fields need a minimum, maximum and positive step")
    if field["type"] == "select" and (
        not field.get("options") or any(not option for option in field["options"])
        or len(set(field["options"])) != len(field["options"])
    ):
        raise ValueError("Selection fields need unique, nonempty choices")
    field["modes"] = input_modes(field)
    return field


def serialize_argument(field, value):
    """Validate and serialize one form value without losing its argument boundary."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Invalid FHEM argument")
    value = format(Decimal(str(value)), "f") if isinstance(value, float) and math.isfinite(value) else str(value)
    kind = field["type"]
    if kind == "select" and value not in field["options"]:
        raise ValueError("Select an offered value")
    if kind == "multiple" and not field.get("custom") and any(
        item not in field["options"] for item in value.split(",")
    ):
        raise ValueError("Select only offered values")
    if kind == "number":
        value = value.strip().replace(",", ".")
        number = finite_number(value)
        minimum = field.get("min", -math.inf)
        if number is None or not minimum <= number <= field.get("max", math.inf):
            raise ValueError("Enter a number in the permitted range")
        step = field.get("step")
        if isinstance(step, (float, int)):
            index = (number - minimum) / step
            if not math.isfinite(index) or not math.isclose(index, round(index), rel_tol=0, abs_tol=1e-8):
                raise ValueError("Enter a value on the permitted step")
        if wire := field.get("wire_values"):
            return wire[round(index)]
        if re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value):
            return format(Decimal(value), "f")
        raise ValueError("Enter a decimal number")
    if kind == "time":
        if not re.fullmatch(r"[0-9]{2}:[0-9]{2}", value):
            raise ValueError("Enter a time as HH:MM")
        time.fromisoformat(value)
    if kind == "date":
        value = date.fromisoformat(value).strftime(field.get("format", "%Y-%m-%d"))
    return value


def serialize_inputs(fields, values):
    """Validate ordered form arguments; trailing unset optional fields are omitted."""
    if len(values) > 256:
        raise ValueError("Too many FHEM arguments")
    if fields is None:
        return [serialize_argument({"type": "text"}, value) for value in values]
    if len(values) > len(fields):
        raise ValueError("Too many arguments for this command")
    result = []
    missing = False
    for index, field in enumerate(fields):
        value = values[index] if index < len(values) else None
        if value is None or (value == "" and not field.get("allow_empty")):
            if not field.get("optional"):
                raise ValueError(f"Argument {index + 1} is required")
            missing = True
        else:
            if missing:
                raise ValueError(f"Fill the arguments before argument {index + 1}")
            try:
                result.append(serialize_argument(field, value))
            except ValueError as err:
                raise ValueError(f"Argument {index + 1}: {err}") from err
    return result


def parse_specs(raw):
    """Keep the original option strings, including unknown widgets."""
    return {
        name: spec if separator else ""
        for item in raw.split()
        for name, separator, spec in (item.partition(":"),)
    }


MAX_THERMOSTATS = {
    "heatingthermostat", "heatingthermostatplus", "wallmountedthermostat", "virtualthermostat",
}


def thermostat_family(profile):
    """Identify thermostat protocols using module and hardware metadata."""
    if profile["type"] == "FHT":
        return "fht"
    model = profile["attributes"].get("model") or profile.get("device_model")
    if profile["type"] == "MAX" and model and model.casefold() in MAX_THERMOSTATS:
        return "max"
    if profile["type"] == "CUL_HM":
        if model in {"HM-CC-RT-DN", "HM-CC-RT-DN-BOM"}:
            return "cul_hm_rt"
        if model == "HM-TC-IT-WM-W-EU":
            return "cul_hm_wall"
    return None


def thermostat_supported(profile):
    family = thermostat_family(profile)
    if family == "max":
        return "desiredTemperature" in profile["actions"]
    if family is None or "desired-temp" not in profile["actions"]:
        return False
    if family == "fht":
        return True
    channel = str(profile["attributes"].get("chanNo") or "").lstrip("0")
    return channel == ("2" if family == "cul_hm_wall" else "4") if channel else {"measured-temp", "desired-temp"} <= set(profile["readings"])


def homematic_pwm_dimmer(profile):
    """Recognize the 12–24 V Homematic PWM dimmer and its second revision."""
    model = profile["attributes"].get("model") or profile.get("device_model") or ""
    return profile["type"] == "CUL_HM" and model.upper() in {
        "HM-LC-DIM1PWM-CV", "HM-LC-DIM1PWM-CV-2", "HM-LC-DIM1PWM-CV2",
    }


def tasmota_model(profile):
    if profile["type"] != "MQTT2_DEVICE":
        return ""
    model = str(profile["attributes"].get("model") or profile.get("device_model") or "").casefold()
    return model if model == "tasmota" or model.startswith("tasmota_") else ""


def switch_feedback(profile):
    """The Tasmota POW template sends commands to POWER1."""
    if tasmota_model(profile) == "tasmota_pow" and "POWER1" in profile["readings"]:
        return "POWER1"
    return "state"


def fs20_power_state(value):
    """Interpret the FHEM switch state, including timed on/off commands."""
    command = (value or "").partition(" ")[0]
    if command == "on" or command.startswith("on-"):
        return True
    if command == "off" or command.startswith("off-"):
        return False
    return None


def dimmer_profile(profile):
    """Return the command and feedback for a verified dimmer family."""
    if not {"turn_on", "turn_off"} <= profile["actions"].keys():
        return None
    attributes = profile["attributes"]
    if (
        profile["type"] == "FS20" and attributes.get("model") in {"fs20di", "fs20di10", "fs20du"}
        and "dim" in profile["actions"] and "state" in profile["readings"]
    ):
        return "dim", "state"
    pwm = homematic_pwm_dimmer(profile)
    channel = str(attributes.get("chanNo") or "").lstrip("0")
    if pwm and channel not in {"", "1"}:
        return None
    if (profile["type"] == "CUL_HM" and (pwm or attributes.get("subType") == "dimmer")
            and "pct" in profile["actions"] and "pct" in profile["readings"]):
        return "pct", "pct"
    return None


def fields_for(profile, kind, name, spec):
    """Convert a known widget to fields or leave the argument list editable."""
    if kind == "set" and name == "mode" and profile["type"] == "FHT" and not spec:
        return [{"type": "select", "options": ["auto", "manual", "holiday_short", "holiday"]}]
    if kind == "set" and name == "controlMode" and thermostat_supported(profile):
        available = ["auto", "manual", "boost", "day", "night"]
        declared = spec.removeprefix("select,").split(",") if spec else available
        options = [option for option in available if option in declared]
        if options:
            return [{"type": "select", "options": options}]
    parts = spec.split(",")
    widget, values = parts[0], parts[1:]
    if spec == "noArg":
        return []
    if kind == "set" and profile["type"] == "FS20" and name == "dim" and widget == "slider":
        # FS20 labels its quantized steps as 06, 12, 18, 25 etc. when encoding the Set argument.
        return [
            {"type": "number", "label": "percent", "unit": "%", "min": 0, "max": 100, "step": 6.25,
             "display": "slider",
             "wire_values": ["0", *[str(int(step * 6.25)) for step in range(1, 17)]]},
            {"type": "number", "label": "seconds", "step": "any", "min": 0, "max": 15360, "optional": True},
        ]
    if widget == "slider" and len(values) >= 3:
        minimum, step, maximum = map(finite_number, values[:3])
        if None not in (minimum, step, maximum) and minimum <= maximum and step > 0:
            return [{"type": "number", "min": minimum, "max": maximum, "step": step, "display": "slider"}]
        return None
    if widget == "selectnumbers":
        if len(values) < 5:
            return None
        minimum, step, maximum, digits = map(finite_number, values[:4])
        scale = values[4]
        if (None in (minimum, step, maximum, digits) or minimum >= maximum
                or step <= 0 or not digits.is_integer() or not 0 <= digits <= 8):
            return None
        if scale == "log10" and minimum > 0:
            start, end = math.log10(minimum), math.log10(maximum)
            convert = lambda n: maximum if n >= end else 10 ** n
        elif scale == "lin":
            start, end = minimum, maximum
            convert = lambda n: n
        else:
            return None
        count = (end - start) / step
        if not math.isfinite(count) or count > 256:
            return None
        steps = math.ceil(count) if scale == "log10" else math.floor(count + 1e-10)
        options = list(dict.fromkeys(f"{convert(start + i * step):.{int(digits)}f}" for i in range(steps + 1)))
        return [{"type": "select", "options": options}]
    if widget in {"multiple", "multiple-strict", "select"} and values:
        return [{"type": "multiple" if widget.startswith("multiple") else "select",
                 "options": values, "custom": widget == "multiple"}]
    if widget in {"time", "textField", "textField-long", "textFieldNL", "textFieldNL-long"}:
        return [{"type": "time" if widget == "time" else "text", "multiline": widget != "textField"}]
    if widget.startswith(("uzsu", "icon", "sortable", "colorpicker")) or widget in {"knob", "bitfield", "widgetList"}:
        return None
    if spec:
        if widget in {"slider", "select", "multiple", "multiple-strict"}:
            return None
        if "noArg" in parts:
            return None
        return [{"type": "select", "options": parts}]
    if kind == "attr":
        return [{"type": "text", "multiline": True}]
    if kind == "set" and not spec:
        if profile["type"] == "FS20":
            if name in {"on-for-timer", "off-for-timer", "on-old-for-timer", "on-old-for-timer-prev",
                        "on-100-for-timer-prev", "timer", "ramp-on-time", "ramp-off-time"}:
                return [{"type": "number", "label": "seconds", "step": "any", "min": 0, "max": 15360}]
            if name in {"on", "off", "toggle", "up", "down", "open", "close", "extend", "retract", "stop"} or name.startswith("dim"):
                return [{"type": "number", "label": "seconds", "step": "any", "min": 0,
                         "max": 15360, "optional": True}]
        if profile["type"] == "CUL_HM":
            model = str(profile["attributes"].get("model") or profile.get("device_model") or "").upper()
            if model == "HM-DIS-WM55" and name == "displayWM":
                return [
                    {"type": "select", "options": ["short", "long"], "label": "press"},
                    {"type": "select", "options": [f"line{index}" for index in range(1, 7)], "label": "line"},
                    {"type": "text", "label": "text"},
                    {"type": "select", "options": ["nc", "off", "white", "red", "orange", "yellow", "green", "blue"],
                     "label": "color"},
                    {"type": "select", "options": ["nc", "off", "on", "open", "closed", "error", "ok",
                                                    "info", "newMsg", "serviceMsg", "sigGreen", "sigYellow",
                                                    "sigRed", "ic12", "ic13", "noIcon"], "label": "icon"},
                ]
            if model in {"HM-LC-SW2-FM", "HM-LC-SW4-DR", "HM-LC-SW4-SM", "HM-ES-PMSW1-PL"}:
                if name == "on-for-timer":
                    return [{"type": "number", "label": "seconds", "min": 0, "step": "any"}]
                if name == "on-till":
                    return [{"type": "time", "label": "time"}]
        if profile["type"] == "CUL_HM" and name == "pct":
            return [
                {"type": "number", "label": "percent", "min": 0, "max": 100, "step": "any"},
                {"type": "number", "label": "hold", "min": 0, "step": "any", "optional": True},
                {"type": "number", "label": "ramp", "min": 0, "step": "any", "optional": True},
            ]
        if profile["type"] == "CUL_HM" and name == "controlParty" and thermostat_supported(profile):
            return [
                {"type": "number", "label": "temperature", "unit": "°C", "min": 5, "max": 30, "step": 0.5},
                {"type": "date", "label": "startDate", "format": "%d.%m.%y"},
                {"type": "time", "label": "startTime"},
                {"type": "date", "label": "endDate", "format": "%d.%m.%y"},
                {"type": "time", "label": "endTime"},
            ]
        if name == "desired-temp" and thermostat_supported(profile):
            return [{"type": "number", "label": "temperature", "min": 5, "max": 30, "step": 0.5}]
    return None


def command_description(profile, kind, name, spec, override=None):
    """Resolve the same fields for the panel, publications and typed calls."""
    fields = fields_for(profile, kind, name, spec)
    if override:
        display = fields_for(profile, kind, name, override)
        if fields is None and display:
            # FHEM may only know the widget through an installation's override.
            fields = display
        elif fields and display and len(fields) == len(display):
            for field, hint in zip(fields, display, strict=True):
                if hint["type"] == "text":
                    field["display"] = "text"
    if fields:
        for field in fields:
            field["modes"] = input_modes(field)
    return {"name": name, "spec": spec, "fields": fields}
