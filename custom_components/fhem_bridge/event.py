"""Events for selected FHEM device event keys."""

from homeassistant.components.event import EventEntity

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    """Expose the event keys defined in the server's profiles."""
    runtime = entry.runtime_data
    add_entities(entry.runtime_data, async_add_entities, [
        FhemEvent(runtime, device, profile["events"])
        for device, profile in runtime.profiles.items()
        if profile["events"]
    ])


class FhemEvent(FhemEntity, EventEntity):
    """A repeated FHEM event can trigger HA independently of its value."""

    def __init__(self, runtime, device, events):
        super().__init__(runtime, device, "event", None)
        self.use_semantic_name("events")
        self._attr_event_types = events

    def update_from_bridge(self, frame):
        if frame is None:
            self.async_write_ha_state()
        elif frame["type"] == "event" and frame["event"] in self.event_types:
            self._trigger_event(frame["event"], {"value": frame["value"], "raw": frame.get("raw", frame["value"])})
            self.async_write_ha_state()
