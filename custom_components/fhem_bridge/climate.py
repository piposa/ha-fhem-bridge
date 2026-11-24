"""Native climate entities for supported FHEM thermostat channels."""

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity
from .profiles import finite_number, thermostat_family, thermostat_supported


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    runtime = entry.runtime_data
    add_entities(entry.runtime_data, async_add_entities, [
        FhemThermostat(runtime, device)
        for device, profile in runtime.profiles.items()
        if thermostat_supported(profile)
    ])


class FhemThermostat(FhemEntity, ClimateEntity):
    control_command = "desired-temp"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_max_temp = 30
    _attr_target_temperature_step = 0.5

    def __init__(self, runtime, device):
        super().__init__(runtime, device, "thermostat", None)
        profile = runtime.profiles[device]
        family = thermostat_family(profile)
        self.fht = family == "fht"
        self.max_thermostat = family == "max"
        self.target_reading = "desiredTemperature" if self.max_thermostat else "desired-temp"
        self.control_command = self.target_reading
        self.mode_reading = "mode" if self.fht or self.max_thermostat else "controlMode"
        self._attr_min_temp = 6 if self.fht else 5
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        mode_command = "mode" if self.fht else "controlMode"
        if self.max_thermostat or (mode_command in profile["actions"] and self.mode_reading in profile["readings"]):
            self._attr_hvac_modes.insert(0, HVACMode.AUTO)

    def reading(self, name):
        return self.runtime.values.get((self.device, name))

    @property
    def hvac_mode(self):
        target = self.reading(self.target_reading)
        if target == "off" or finite_number(target) == (5.5 if self.fht else 4.5):
            return HVACMode.OFF
        if self.reading(self.mode_reading) == "auto" and HVACMode.AUTO in self.hvac_modes:
            return HVACMode.AUTO
        return HVACMode.HEAT if target is not None else None

    @property
    def hvac_action(self):
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        valve = self.reading("valveposition" if self.max_thermostat else "actuator" if self.fht else "ValvePosition")
        if isinstance(valve, str):
            valve = valve.rstrip(" %")
        position = finite_number(valve)
        if position is not None:
            return HVACAction.HEATING if position > 0 else HVACAction.IDLE
        return None

    @property
    def native_current_temperature(self):
        return finite_number(self.reading("temperature" if self.max_thermostat else "measured-temp"))

    @property
    def native_target_temperature(self):
        return finite_number(self.reading(self.target_reading))

    @property
    def current_humidity(self):
        return finite_number(self.reading("humidity"))

    async def async_set_temperature(self, **kwargs):
        if "temperature" in kwargs:
            await self.runtime.execute(self.device, "set", self.control_command, [kwargs["temperature"]])

    async def async_set_hvac_mode(self, hvac_mode):
        if self.max_thermostat:
            if hvac_mode == HVACMode.AUTO:
                arguments = ["auto"]
            elif hvac_mode == HVACMode.OFF:
                arguments = ["manual", "off"]
            elif hvac_mode == HVACMode.HEAT and (value := self.native_target_temperature) is not None:
                arguments = ["manual", value]
            else:
                raise HomeAssistantError("Set a target temperature before switching to manual mode")
            await self.runtime.execute(self.device, "set", self.control_command, arguments)
            return
        if hvac_mode == HVACMode.AUTO:
            command, value = ("mode" if self.fht else "controlMode"), "auto"
        elif hvac_mode == HVACMode.OFF:
            command, value = "desired-temp", "off"
        elif self.fht and "mode" in self.runtime.profiles[self.device]["actions"]:
            command, value = "mode", "manual"
        elif not self.fht and "controlManu" in self.runtime.profiles[self.device]["actions"]:
            value = self.native_target_temperature
            if value is None or not self.min_temp <= value <= self.max_temp:
                raise HomeAssistantError("Set a target temperature before switching to manual mode")
            command = "controlManu"
        else:
            raise HomeAssistantError("Set the target temperature to start heating")
        await self.runtime.execute(self.device, "set", command, [value])
