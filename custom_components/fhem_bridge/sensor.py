"""Sensors for FHEM readings and device metadata."""

import re

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory

from .calculator import calculator_prices
from .const import DOMAIN
from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity
from .profiles import finite_number
from .reading_names import sensor_reading_name
from .templates import METER_READINGS, meter_kind

OUTLET_CLASSES = {
    "power": SensorDeviceClass.POWER, "voltage": SensorDeviceClass.VOLTAGE,
    "current": SensorDeviceClass.CURRENT, "frequency": SensorDeviceClass.FREQUENCY,
}


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    """Create sensors from the server's allowed readings."""
    runtime = entry.runtime_data
    async_add_entities([BridgeStatus(runtime)])
    entities = []
    for device, profile in runtime.profiles.items():
        entities.append(FhemMetadata(runtime, device))
        entities.extend(
            FhemCalculatorPrice(runtime, device, unit, value, price_unit)
            for unit, (value, price_unit) in calculator_prices(profile).items()
        )
        entities.extend(
            FhemReading(runtime, device, reading, mode)
            for reading, mode in runtime.publications.resolved[device]["readings"].items()
            if mode in {"sensor", "diagnostic", "hidden"}
        )
    add_entities(entry.runtime_data, async_add_entities, entities)


class BridgeStatus(SensorEntity):
    """Report the common session independently of the imported devices."""

    _attr_name = "Verbindungsstatus"
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime):
        self.runtime = runtime
        self._attr_unique_id = f"bridge-status:{runtime.entry.unique_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)}, "name": "FHEM Bridge",
            "manufacturer": "FHEM",
        }

    @property
    def native_value(self):
        if self.runtime.connected:
            return "online"
        return "error" if self.runtime.connection_error else "offline"

    @property
    def icon(self):
        return {
            "online": "mdi:lan-connect",
            "offline": "mdi:lan-disconnect",
            "error": "mdi:alert-circle-outline",
        }[self.native_value]

    @property
    def extra_state_attributes(self):
        runtime = self.runtime
        return {
            "configured_devices": len({runtime.device_key(source) for source in runtime.selected}),
            "configured_definitions": len(runtime.selected),
            "active_definitions": len(runtime.active),
            "last_connected": runtime.last_connected,
            "last_disconnected": runtime.last_disconnected,
            "reason": runtime.connection_error or runtime.disconnect_reason,
            "last_error": runtime.last_connection_error,
            "subscription_errors": {
                runtime.profiles[device]["name"]: reason
                for device, reason in runtime.subscription_errors.items()
            },
        }

    async def async_added_to_hass(self):
        listener = lambda _: self.async_write_ha_state()
        listeners = self.runtime.listeners[self._attr_unique_id]
        listeners.add(listener)
        self.async_on_remove(lambda: listeners.discard(listener))


class FhemReading(FhemEntity, SensorEntity):
    """A generic FHEM reading."""

    def __init__(self, runtime, device, reading, mode="sensor"):
        item = runtime.publications.resolved[device]["choices"].get(f"reading:{reading}", {})
        super().__init__(runtime, device, f"reading/{reading}", item.get("label") or reading)
        self.reading = reading
        if mode == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_visible_default = mode != "hidden"
        explicit = f"reading:{reading}" in runtime.publications.resolved[device]["choices"]
        if explicit:
            self._bridge_hidden = mode == "hidden"
        if explicit or device not in runtime.publications.data["legacy"]:
            measurement = {
                "temperature": (SensorDeviceClass.TEMPERATURE, "°C"),
                "measured-temp": (SensorDeviceClass.TEMPERATURE, "°C"),
                "humidity": (SensorDeviceClass.HUMIDITY, "%"),
                "dewpoint": (SensorDeviceClass.TEMPERATURE, "°C"),
            }.get(reading)
            if measurement:
                self._attr_device_class, self._attr_native_unit_of_measurement = measurement
                self._attr_state_class = SensorStateClass.MEASUREMENT
        profile = runtime.profiles[device]
        self._has_esa_power_sentinel = profile["type"] == "ESA2000" and reading in {"actual", "max"}
        quantity = meter_kind(reading)
        self._outlet_measurement = (
            runtime.publications.resolved[device].get("layout") == "outlet"
            and quantity in METER_READINGS
        )
        if self._outlet_measurement:
            self._attr_device_class = OUTLET_CLASSES[quantity]
            self._attr_native_unit_of_measurement = METER_READINGS[quantity]
            self._attr_state_class = SensorStateClass.MEASUREMENT
        model = profile["attributes"].get("model") or profile.get("device_model") or ""
        if profile["type"] == "CUL_HM" and model.upper() == "HM-SEN-LI-O" and reading == "brightness":
            self._attr_device_class = SensorDeviceClass.ILLUMINANCE
            self._attr_native_unit_of_measurement = "lx"
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if profile["type"] == "CUL_HM" and model.upper() == "HM-ES-TX-WM":
            if reading in {"gasCnt", "gasCntCalc"}:
                self._attr_device_class = SensorDeviceClass.GAS
                self._attr_native_unit_of_measurement = "m³"
                self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            elif reading == "power":
                self._attr_device_class = SensorDeviceClass.POWER
                self._attr_native_unit_of_measurement = "W"
                self._attr_state_class = SensorStateClass.MEASUREMENT
            elif reading in {"energy", "energyCalc"}:
                self._attr_device_class = SensorDeviceClass.ENERGY
                self._attr_native_unit_of_measurement = "Wh"
                self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        if profile["type"] == "CUL_HM" and model.upper().startswith("HM-ES-PMSW1-"):
            electric = {
                "power": (SensorDeviceClass.POWER, "W"),
                "energy": (SensorDeviceClass.ENERGY, "Wh"),
                "energyCalc": (SensorDeviceClass.ENERGY, "Wh"),
                "voltage": (SensorDeviceClass.VOLTAGE, "V"),
                "current": (SensorDeviceClass.CURRENT, "mA"),
                "frequency": (SensorDeviceClass.FREQUENCY, "Hz"),
            }.get(reading)
            if electric:
                self._attr_device_class, self._attr_native_unit_of_measurement = electric
                self._attr_state_class = (
                    SensorStateClass.TOTAL_INCREASING if reading in {"energy", "energyCalc"}
                    else SensorStateClass.MEASUREMENT
                )

        if (metadata := item.get("sensor_metadata")) is not None:
            self._attr_device_class = metadata.get("device_class")
            self._attr_state_class = metadata.get("state_class")
            self._attr_native_unit_of_measurement = metadata.get("unit_of_measurement")
        if not item.get("label") and (name := sensor_reading_name(reading, self.device_class, mode)):
            self.use_semantic_name(name)

    @property
    def native_value(self):
        value = self.runtime.values.get((self.device, self.reading))
        if self._outlet_measurement and isinstance(value, str):
            match = re.fullmatch(r"\s*([+-]?\d+(?:[.,]\d+)?)\s*([A-Za-z]+)\s*", value)
            if match:
                number = finite_number(match[1].replace(",", "."))
                if number is None:
                    return None
                if match[2] == self.native_unit_of_measurement:
                    return number
                if match[2] == "mA" and self.native_unit_of_measurement == "A":
                    return number / 1000
        unit = self.native_unit_of_measurement
        if self.device_class is not None or self.state_class is not None or unit is not None:
            if unit and isinstance(value, str):
                value = value.strip().removesuffix(unit)
            number = finite_number(value)
            return None if self._has_esa_power_sentinel and number == -1 else number
        return value if value is None or len(value) <= 255 else None

    @property
    def extra_state_attributes(self):
        timestamp = self.runtime.timestamps.get((self.device, self.reading))
        return {"fhem_timestamp": timestamp} if timestamp else None

    @property
    def bridge_reading(self):
        return self.reading

    def update_from_bridge(self, frame):
        if frame is None or (frame["type"] == "reading" and frame["reading"] == self.reading):
            self.async_write_ha_state()


class FhemCalculatorPrice(FhemEntity, SensorEntity):
    """A configured FHEM tariff for Home Assistant's cost calculation."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime, device, unit, value, price_unit):
        key = "energy" if unit == "kWh" else "volume"
        super().__init__(runtime, device, f"price/{key}", f"Arbeitspreis pro {unit}")
        self._attr_native_value = value
        self._attr_native_unit_of_measurement = price_unit

    def update_from_bridge(self, frame):
        if frame is None:
            self.async_write_ha_state()


class FhemMetadata(FhemEntity, SensorEntity):
    """Show the FHEM name and selected display metadata."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, runtime, device):
        super().__init__(runtime, device, "metadata", "FHEM")

    @property
    def native_value(self):
        return self.runtime.profiles[self.device]["name"]

    @property
    def extra_state_attributes(self):
        profile = self.runtime.profiles[self.device]
        return {"fhem_type": profile["type"], "fuuid": self.device, **profile["attributes"]}

    def update_from_bridge(self, frame):
        if frame is None:
            self.async_write_ha_state()
