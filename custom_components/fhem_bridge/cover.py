"""Expose explicitly mapped FHEM shutters as native Home Assistant covers."""

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    runtime = entry.runtime_data
    add_entities(runtime, async_add_entities, [
        FhemCover(runtime, device, result["cover"])
        for device, result in runtime.publications.resolved.items() if result["cover"]
    ])


class FhemCover(FhemEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_assumed_state = True

    def __init__(self, runtime, device, commands):
        super().__init__(runtime, device, "cover", None)
        if runtime.publications.resolved.get(device, {}).get("layout") == "awning":
            self._attr_device_class = CoverDeviceClass.AWNING
        self.open_command, self.close_command, self.stop_command = commands
        self.control_command = self.open_command
        self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        if self.stop_command:
            self._attr_supported_features |= CoverEntityFeature.STOP

    @property
    def is_closed(self):
        state = self.runtime.values.get((self.device, "state"))
        return {"closed": True, "retracted": True, "open": False, "opened": False, "extended": False}.get(state)

    async def async_open_cover(self, **kwargs):
        await self.runtime.execute(self.device, "set", self.open_command, [])

    async def async_close_cover(self, **kwargs):
        await self.runtime.execute(self.device, "set", self.close_command, [])

    async def async_stop_cover(self, **kwargs):
        if self.stop_command:
            await self.runtime.execute(self.device, "set", self.stop_command, [])
