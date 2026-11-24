"""Native light control for explicitly recognized FHEM dimmers."""

from homeassistant.components.light import ColorMode, LightEntity

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity
from .profiles import finite_number, fs20_power_state
from .templates import dimmer_outputs


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    runtime = entry.runtime_data
    add_entities(runtime, async_add_entities, [
        FhemDimmer(runtime, device, *dimmer) for device, dimmer in dimmer_outputs(runtime)
    ])


class FhemDimmerControl(FhemEntity):
    """Shared state and level commands for the light and its device-page slider."""

    def __init__(self, runtime, device, command, reading, key):
        super().__init__(runtime, device, key, None)
        self.command = command
        self.control_command = command
        self.reading = reading

    @property
    def level(self):
        value = self.runtime.values.get((self.device, self.reading), "")
        if self.command == "dim":
            if fs20_power_state(value) is False:
                return 0
            if value.startswith("dim") and value.endswith("%"):
                level = finite_number(value[3:-1])
                return round(level / 6.25) * 6.25 if level is not None else None
            return None
        return finite_number(value)

    async def set_level(self, value):
        if self.command == "dim":
            # FS20 accepts the integer spelling of its 16 steps (dim06%, dim12%, …).
            level = max(0, min(16, round(value / 6.25)))
            if level == 0:
                await self.runtime.execute(self.device, "set", "off", [])
                return
            value = int(level * 6.25)
        await self.runtime.execute(self.device, "set", self.command, [value])


class FhemDimmer(FhemDimmerControl, LightEntity):
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(self, runtime, device, command, reading):
        super().__init__(runtime, device, command, reading, "dimmer")

    @property
    def brightness(self):
        level = self.level
        return round(max(0, min(100, level)) * 255 / 100) if level is not None else None

    @property
    def is_on(self):
        level = self.level
        if level is not None:
            return level > 0
        value = self.runtime.values.get((self.device, "state"))
        return fs20_power_state(value) if self.command == "dim" else {"on": True, "off": False}.get(value)

    async def async_turn_on(self, **kwargs):
        if "brightness" not in kwargs:
            await self.runtime.execute(self.device, "set", "on", [])
            return
        if not kwargs["brightness"]:
            await self.async_turn_off()
            return
        level = kwargs["brightness"] * 100 / 255
        if self.command == "dim":
            level = max(6.25, level)
        else:
            level = round(level * 2) / 2
        await self.set_level(level)

    async def async_turn_off(self, **kwargs):
        await self.runtime.execute(self.device, "set", "off", [])
