"""Shared FHEM entity identity and state dispatch."""

from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity


def switch_supported(profile):
    """Recognize the explicit switch profile."""
    return "state" in profile["readings"] and {"turn_on", "turn_off"} <= profile["actions"].keys()


class FhemEntity(Entity):
    """Base for entities linked to a FHEM definition."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    control_command = None

    def __init__(self, runtime, device, key, name):
        self.runtime = runtime
        self.device = device
        self.key = key
        self._attr_unique_id = f"{runtime.identifier(device)}/{key}"
        self._bridge_hidden = None
        self._attr_name = self.name_on_device(name)
        self._attr_device_info = runtime.device_info(device)

    def name_on_device(self, name):
        if self.runtime.primary_source(self.runtime.device_key(self.device)) not in (None, self.device):
            profile = self.runtime.profiles[self.device]
            channel = profile["attributes"].get("alias") or profile["name"]
            return f"{channel} · {name}" if name else channel
        return name

    def use_semantic_name(self, key):
        """Let HA translate the entity name while keeping the channel context."""
        del self._attr_name
        if self.runtime.primary_source(self.runtime.device_key(self.device)) not in (None, self.device):
            profile = self.runtime.profiles[self.device]
            channel = profile["attributes"].get("alias") or profile["name"]
            self._attr_translation_key = f"{key}_channel"
            self._attr_translation_placeholders = {"channel": channel}
        else:
            self._attr_translation_key = key

    @property
    def icon(self):
        return "mdi:lock" if self.blocked_reason else getattr(self, "_attr_icon", None)

    @property
    def blocked_reason(self):
        if self.control_command:
            return self.runtime.command_blocked(self.device, "set", self.control_command)
        return None

    @property
    def extra_state_attributes(self):
        attributes = dict(getattr(self, "_attr_extra_state_attributes", None) or {})
        if self.control_command:
            attributes["fhem_permission"] = self.blocked_reason or "allowed"
        return attributes or None

    @property
    def available(self):
        return self.device in self.runtime.active and self.blocked_reason is None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if self._bridge_hidden is not None:
            registry = er.async_get(self.hass)
            entry = registry.async_get(self.entity_id)
            if entry and entry.hidden_by != er.RegistryEntryHider.USER:
                hide = er.RegistryEntryHider.INTEGRATION if self._bridge_hidden else None
                if entry.hidden_by != hide:
                    registry.async_update_entity(self.entity_id, hidden_by=hide)
        if self.bridge_reading is None:
            listeners = self.runtime.listeners[self.device]
        else:
            listeners = self.runtime.reading_listeners[self.device][self.bridge_reading]
        listeners.add(self.update_from_bridge)
        self.async_on_remove(lambda: listeners.discard(self.update_from_bridge))

    @property
    def bridge_reading(self):
        """Use a keyed listener when only one reading affects this entity."""
        return None

    @callback
    def update_from_bridge(self, frame):
        """Refresh after a state update."""
        if frame is None or frame["type"] == "reading":
            self.async_write_ha_state()
