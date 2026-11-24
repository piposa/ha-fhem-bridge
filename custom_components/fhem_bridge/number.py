"""Publish one-argument FHEM numeric commands."""

from homeassistant.components.number import NumberEntity, NumberMode

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity
from .light import FhemDimmerControl
from .profiles import finite_number
from .published_entity import PublishedCommand, PublishedInput, published_commands, published_inputs
from .templates import dimmer_outputs


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    add_entities(entry.runtime_data, async_add_entities, published_commands(entry.runtime_data, {"number", "number_slider"}, FhemNumber))
    add_entities(entry.runtime_data, async_add_entities, published_inputs(entry.runtime_data, {"box", "slider"}, FhemNumberInput))

    runtime = entry.runtime_data
    add_entities(runtime, async_add_entities, [
        FhemDimmerLevel(runtime, device, *dimmer) for device, dimmer in dimmer_outputs(runtime)
    ])
    add_entities(runtime, async_add_entities, [
        FhemAnalogLevel(runtime, device)
        for device, profile in runtime.profiles.items()
        if runtime.publications.resolved[device]["layout"] == "level"
        and "pct" in profile["actions"] and "pct" in profile["readings"]
    ])


class FhemDimmerLevel(FhemDimmerControl, NumberEntity):
    """Expose the dimming level as a slider in the HA device controls."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_unit_of_measurement = "%"

    def __init__(self, runtime, device, command, reading):
        super().__init__(runtime, device, command, reading, "dimmer-level")
        self.use_semantic_name("dimmer_level")
        self._attr_native_step = 6.25 if command == "dim" else 0.5

    @property
    def native_value(self):
        return self.level

    async def async_set_native_value(self, value):
        await self.set_level(value)


class FhemAnalogLevel(FhemEntity, NumberEntity):
    """Expose the FHEM percentage without assuming a configured voltage range."""

    control_command = "pct"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "%"

    def __init__(self, runtime, device):
        super().__init__(runtime, device, "analog-level", None)
        self.use_semantic_name("output_level")

    @property
    def native_value(self):
        return finite_number(self.runtime.values.get((self.device, "pct")))

    async def async_set_native_value(self, value):
        await self.runtime.execute(self.device, "set", "pct", [value])

    def update_from_bridge(self, frame):
        if frame is None or (frame["type"] == "reading" and frame["reading"] == "pct"):
            self.async_write_ha_state()


class FhemNumber(PublishedCommand, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, runtime, device, key, item):
        super().__init__(runtime, device, key, item)
        if item["mode"] == "number_slider":
            self._attr_mode = NumberMode.SLIDER
        field = item["fields"][0]
        self._attr_native_min_value = field["min"]
        self._attr_native_max_value = field["max"]
        self._attr_native_step = field["step"]
        if field.get("label") == "temperature":
            self._attr_native_unit_of_measurement = "°C"

    @property
    def native_value(self):
        return finite_number(self.reported)

    async def async_set_native_value(self, value):
        await self.send([value])


class FhemNumberInput(PublishedInput, NumberEntity):
    def __init__(self, runtime, device, key, item, index, mode):
        super().__init__(runtime, device, key, item, index, mode)
        self._attr_mode = NumberMode.SLIDER if mode == "slider" else NumberMode.BOX
        self._attr_native_min_value = self.field["min"]
        self._attr_native_max_value = self.field["max"]
        self._attr_native_step = self.field["step"]
        self._attr_native_unit_of_measurement = self.field.get("unit")

    @property
    def native_value(self):
        return finite_number(self.input_value)

    async def async_set_native_value(self, value):
        await self.set_input(value)
