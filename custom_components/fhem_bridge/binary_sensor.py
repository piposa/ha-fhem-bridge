"""Readings explicitly published as binary states."""

from datetime import timedelta
import re

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity
from .reading_names import BINARY_READING_NAMES

ON = {"1", "on", "yes", "true", "open", "opened", "motion", "present", "offen", "auf"}
OFF = {"0", "off", "no", "false", "closed", "close", "no motion", "absent", "geschlossen", "zu"}
TIMED_ON = re.compile(r"(?:on(?:-old)?-for-timer|on) (\d+(?:\.\d+)?)")
MAX_CONTACT_STATUS = re.compile(r"(opened|closed)(?: \(battery low\))?(?: \(rf error\))?")
CONTACT_TARGET = re.compile(r"(open|closed|tilted) \(to [^()]+\)")
TIMED_OFF = re.compile(r"off(?:-for-timer)? \d+(?:\.\d+)?")


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    runtime = entry.runtime_data
    add_entities(entry.runtime_data, async_add_entities, [
        FhemBinaryReading(runtime, device, reading)
        for device, result in runtime.publications.resolved.items()
        for reading, mode in result["readings"].items()
        if mode == "binary"
    ])


class FhemBinaryReading(FhemEntity, BinarySensorEntity):
    def __init__(self, runtime, device, reading):
        result = runtime.publications.resolved[device]
        label = result.get("choices", {}).get(f"reading:{reading}", {}).get("label")
        super().__init__(runtime, device, f"reading/{reading}", label or reading)
        self.reading = reading
        layout = result.get("layout")
        self._attr_device_class = {
            "contact": BinarySensorDeviceClass.OPENING, "motion": BinarySensorDeviceClass.MOTION,
            "smoke": BinarySensorDeviceClass.SMOKE,
        }.get(layout)
        if layout == "weather" and reading in {"israining", "is_raining"}:
            self._attr_device_class = BinarySensorDeviceClass.MOISTURE
        name = "rain_detected" if layout == "weather" and reading in {"israining", "is_raining"} else (
            BINARY_READING_NAMES.get(self.device_class)
        )
        if name and not label:
            self.use_semantic_name(name)
        self._has_homematic_contact_target = (
            self._attr_device_class == BinarySensorDeviceClass.OPENING
            and runtime.profiles[device]["type"] == "CUL_HM" and reading in {"contact", "state"}
        )
        self._has_max_contact_status = (
            self._attr_device_class == BinarySensorDeviceClass.OPENING
            and runtime.profiles[device]["type"] == "MAX" and reading == "state"
        )
        self._cancel_expiry = None

    def _value(self):
        value = (self.runtime.values.get((self.device, self.reading)) or "").strip().lower()
        if self._has_homematic_contact_target and (match := CONTACT_TARGET.fullmatch(value)):
            return match[1]
        if self._has_max_contact_status and (match := MAX_CONTACT_STATUS.fullmatch(value)):
            return match[1]
        return value

    def _expiry(self, timed):
        stamp = self.runtime.timestamps.get((self.device, self.reading))
        timestamp = dt_util.parse_datetime(stamp) if stamp else None
        seconds = float(timed[1])
        if timestamp is not None and 0 <= seconds <= 15360:
            return dt_util.as_utc(timestamp) + timedelta(seconds=seconds)
        return None

    @property
    def is_on(self):
        value = self._value()
        if self.device_class == BinarySensorDeviceClass.MOTION and (timed := TIMED_ON.fullmatch(value)):
            expiry = self._expiry(timed)
            return expiry > dt_util.utcnow() if expiry is not None else None
        if self.device_class == BinarySensorDeviceClass.MOTION and TIMED_OFF.fullmatch(value):
            return False
        if self.device_class == BinarySensorDeviceClass.OPENING and value == "tilted":
            return True
        if self.device_class == BinarySensorDeviceClass.MOTION:
            if value == "nomotion":
                return False
            if value.startswith("on "):
                return True
        if self.device_class == BinarySensorDeviceClass.SMOKE:
            if value in {"smoke-alarm", "smoke-forward", "smoke alarm"}:
                return True
            if value in {"no alarm", "normal"}:
                return False
        return True if value in ON else False if value in OFF else None

    def _clear_expiry(self):
        if self._cancel_expiry:
            self._cancel_expiry()
            self._cancel_expiry = None

    @callback
    def _expire(self, _now):
        self._cancel_expiry = None
        self.async_write_ha_state()

    def _schedule_expiry(self):
        self._clear_expiry()
        if self.device_class == BinarySensorDeviceClass.MOTION and (timed := TIMED_ON.fullmatch(self._value())):
            expiry = self._expiry(timed)
            if expiry is not None and expiry > dt_util.utcnow():
                self._cancel_expiry = async_track_point_in_utc_time(
                    self.hass, self._expire, expiry
                )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(self._clear_expiry)
        self._schedule_expiry()

    @property
    def extra_state_attributes(self):
        timestamp = self.runtime.timestamps.get((self.device, self.reading))
        return {"fhem_timestamp": timestamp} if timestamp else None

    @property
    def bridge_reading(self):
        return self.reading

    def update_from_bridge(self, frame):
        if frame is None or (frame["type"] == "reading" and frame["reading"] == self.reading):
            self._schedule_expiry()
            self.async_write_ha_state()
