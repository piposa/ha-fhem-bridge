"""Explicit on/off switches."""

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity, switch_supported
from .profiles import dimmer_profile, fs20_power_state, switch_feedback, tasmota_model
from .templates import ACTUATOR_LAYOUTS, PASSIVE_LAYOUTS


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up explicitly writable switch profiles."""
    runtime = entry.runtime_data
    add_entities(entry.runtime_data, async_add_entities, [
        FhemSwitch(runtime, device)
        for device, profile in runtime.profiles.items()
        if runtime.publications.resolved[device]["layout"] not in ACTUATOR_LAYOUTS | PASSIVE_LAYOUTS
        and (runtime.publications.resolved[device]["layout"] != "dimmer" or not dimmer_profile(profile))
        and (switch_supported(profile) or (
            runtime.publications.resolved[device]["layout"] == "outlet"
            and {"turn_on", "turn_off"} <= profile["actions"].keys()
        ))
    ])


class FhemSwitch(FhemEntity, SwitchEntity):
    """A FHEM on/off device."""

    control_command = "on"

    def __init__(self, runtime, device):
        super().__init__(runtime, device, "switch", None)
        if runtime.publications.resolved.get(device, {}).get("layout") == "outlet":
            self._attr_device_class = SwitchDeviceClass.OUTLET

    @property
    def is_on(self):
        profile = self.runtime.profiles[self.device]
        value = self.runtime.values.get((self.device, "state"))
        if tasmota_model(profile):
            feedback = switch_feedback(profile)
            if feedback != "state":
                confirmed = self.runtime.values.get((self.device, feedback), "").lower()
                if confirmed in {"on", "off"}:
                    return confirmed == "on"
            value = (value or "").lower().removeprefix("set_")
        if profile["type"] == "FS20":
            return fs20_power_state(value)
        return {"on": True, "off": False}.get(value)

    async def async_turn_on(self, **kwargs):
        await self.runtime.execute(self.device, "set", "on", [])

    async def async_turn_off(self, **kwargs):
        await self.runtime.execute(self.device, "set", "off", [])

    @property
    def bridge_reading(self):
        return "state" if switch_feedback(self.runtime.profiles[self.device]) == "state" else None

    def update_from_bridge(self, frame):
        if frame is None or (frame["type"] == "reading" and frame["reading"] in {"state", switch_feedback(self.runtime.profiles[self.device])}):
            self.async_write_ha_state()
