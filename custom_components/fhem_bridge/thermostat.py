"""Read and write device-native schedules on supported FHEM thermostats."""

from hashlib import sha256
from itertools import batched, chain
import json
import re
from time import monotonic

from homeassistant.exceptions import HomeAssistantError

from .profiles import finite_number, thermostat_family, thermostat_supported
from .runtime import CONNECTION_ERRORS

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
HM_READINGS = {day: f"R_{index}_tempList{day}" for index, day in enumerate(("Sat", "Sun", *DAYS[:5]))}
FHT_TEMPERATURES = ("day-temp", "night-temp")
FHT_WINDOWS = {
    day: tuple(f"{day.lower()}-{bound}{slot}" for slot in (1, 2) for bound in ("from", "to"))
    for day in DAYS
}


def schedule_family(profile):
    """Expose Homematic schedules on the climate channel only."""
    family = thermostat_family(profile)
    if family != "cul_hm_rt":
        return "fht" if family == "fht" else None
    channel = str(profile["attributes"].get("chanNo") or "").lstrip("0")
    if channel == "4" or (not channel and thermostat_supported(profile)):
        return family
    return None


def minutes(value, step):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]|24:00", value):
        raise ValueError("Use HH:MM (00:00–24:00)")
    hour, minute = map(int, value.split(":"))
    if minute % step:
        raise ValueError(f"Times must be in {step}-minute increments")
    return hour * 60 + minute


def temperature(value, minimum, maximum):
    number = finite_number(value)
    if number is None or not minimum <= number <= maximum or number * 2 % 1:
        raise ValueError(f"Use temperatures from {minimum} to {maximum} °C in 0.5 °C increments")
    return number


def normalize(family, days, temperatures=None):
    """Validate a complete week before preparing any device writes."""
    if not isinstance(days, dict) or days.keys() != set(DAYS):
        raise ValueError("A schedule must contain all seven days")
    if family == "fht":
        if not isinstance(temperatures, list) or len(temperatures) != 2:
            raise ValueError("FHT requires a day and night temperature")
        # FHT also reports the hardware's special off/on settings as 5.5/30.5.
        temperatures = [temperature(value, 5.5, 30.5) for value in temperatures]
    week = {}
    for day in DAYS:
        rows = days[day]
        if not isinstance(rows, list) or not (
            len(rows) == 2 if family == "fht" else 1 <= len(rows) <= 13
        ):
            raise ValueError(f"{day}: invalid number of intervals")
        if any(not isinstance(row, list) or len(row) != 2 for row in rows):
            raise ValueError(f"{day}: invalid interval")
        previous = 0
        intervals = []
        for first, second in rows:
            if family == "fht":
                start, end = minutes(first, 10), minutes(second, 10)
                if start != 1440 and end != 1440:
                    if start > end or (start < end and start < previous):
                        raise ValueError(f"{day}: comfort windows must be ordered and cannot overlap")
                    if start < end:
                        previous = end
                intervals.append([first, second])
            else:
                end = minutes(first, 5)
                if end <= previous:
                    raise ValueError(f"{day}: end times must be in increasing order")
                previous = end
                intervals.append([first, temperature(second, 5, 30)])
        if family == "cul_hm_rt" and previous != 1440:
            raise ValueError(f"{day}: the final interval must end at 24:00")
        week[day] = intervals
    return {"days": week, "temperatures": temperatures}


def revision(values):
    return sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


async def read_week(runtime, device):
    """Fetch cached FHEM readings without a radio request."""
    if device not in runtime.active:
        raise HomeAssistantError("The FHEM channel is unavailable")
    family = schedule_family(runtime.profiles[device])
    if family is None:
        raise HomeAssistantError("No supported schedule for this FHEM channel")
    names = (
        (*FHT_TEMPERATURES, *chain.from_iterable(FHT_WINDOWS.values()))
        if family == "fht" else ("R_tempList_State", *HM_READINGS.values())
    )
    readings = {}
    try:
        for batch in batched(names, 16):
            reply = await runtime.client.request("read", device=device, readings=list(batch))
            readings.update({item["reading"]: item["value"] for item in reply["items"]})
    except CONNECTION_ERRORS as err:
        raise HomeAssistantError("Could not read the schedule from FHEM") from err
    try:
        if family == "fht":
            days = {
                day: [list(pair) for pair in batched([readings[name] for name in keys], 2)]
                for day, keys in FHT_WINDOWS.items()
            }
            week = normalize(family, days, [readings[name] for name in FHT_TEMPERATURES])
        else:
            days = {
                day: [list(pair) for pair in batched(readings[name].split(), 2)]
                for day, name in HM_READINGS.items()
            }
            week = normalize(family, days)
    except (KeyError, ValueError):
        if family == "fht":
            week = {
                "days": {day: [list(pair) for pair in batched(
                    [readings.get(name, "24:00") for name in keys], 2
                )] for day, keys in FHT_WINDOWS.items()},
                "temperatures": [readings.get(name, "") for name in FHT_TEMPERATURES],
            }
        else:
            week = {
                "days": {day: [list(pair) for pair in batched(readings.get(name, "").split(), 2) if len(pair) == 2]
                         or [["24:00", ""]] for day, name in HM_READINGS.items()},
                "temperatures": None,
            }
        is_draft = True
    else:
        is_draft = family != "fht" and readings.get("R_tempList_State") != "verified"
    current_revision = revision(readings)
    pending_revision, expires = runtime.schedule_pending.get(device, (None, 0))
    pending = current_revision == pending_revision and monotonic() < expires
    if not pending:
        runtime.schedule_pending.pop(device, None)
    return {**week, "family": family, "revision": current_revision, "pending": pending, "draft": is_draft,
            "writable": not pending and runtime.enhanced and device in runtime.writable}


def schedule_changes(family, old, new):
    """Translate only changed settings into individual FHEM requests."""
    if family == "fht":
        temperatures = [
            (name, value) for name, before, value in zip(
                FHT_TEMPERATURES, old["temperatures"], new["temperatures"], strict=True
            ) if old["draft"] or before != value
        ]
        if temperatures:
            yield "temperatures", temperatures
        for day in DAYS:
            pairs = [
                (name, value) for name, before, value in zip(
                    FHT_WINDOWS[day], chain.from_iterable(old["days"][day]),
                    chain.from_iterable(new["days"][day]), strict=True
                ) if old["draft"] or before != value
            ]
            if pairs:
                yield day, pairs
    else:
        for day in DAYS:
            if old["draft"] or old["days"][day] != new["days"][day]:
                yield day, [(f"tempList{day}", *chain.from_iterable(new["days"][day]))]


async def write_week(runtime, device, expected, days, temperatures):
    """Validate the whole draft and report any partially accepted update."""
    if not runtime.enhanced or device not in runtime.writable:
        raise HomeAssistantError("Writing is not enabled for this thermostat")
    async with runtime.schedule_locks[hash(device) % len(runtime.schedule_locks)]:
        current = await read_week(runtime, device)
        if not current["writable"] or current["revision"] != expected:
            raise HomeAssistantError("The FHEM schedule changed or is pending. Reload it before saving")
        try:
            draft = normalize(current["family"], days, temperatures)
            changes = list(schedule_changes(current["family"], current, draft))
            if not changes:
                return {"accepted": []}
            catalog = await runtime.command_catalog(device, runtime.profiles[device], "set")
        except CONNECTION_ERRORS as err:
            raise HomeAssistantError(f"Could not prepare the schedule: {err}") from err
        for _, commands in changes:
            for command, *_ in commands:
                if command not in catalog or (catalog[command]["technical"] and device not in runtime.technical):
                    raise HomeAssistantError(f"FHEM does not allow schedule command {command}")
        accepted = []
        runtime.schedule_pending[device] = current["revision"], monotonic() + 300
        for group, commands in changes:
            command, *arguments = chain.from_iterable(commands)
            try:
                await runtime.execute(device, "set", command, arguments)
            except HomeAssistantError as err:
                earlier = ", ".join(accepted) or "none"
                raise HomeAssistantError(f"{group}: {err}. Earlier groups accepted by FHEM: {earlier}") from err
            accepted.append(group)
        return {"accepted": accepted}
