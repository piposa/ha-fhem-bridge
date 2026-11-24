"""Publish one-argument FHEM text commands."""

from homeassistant.components.text import TextEntity

from .device_config import add_entities
from .entity_refresh import managed_entities
from .published_entity import PublishedCommand, PublishedInput, published_commands, published_inputs


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    add_entities(entry.runtime_data, async_add_entities, published_commands(entry.runtime_data, "text", FhemText))
    add_entities(entry.runtime_data, async_add_entities, published_inputs(entry.runtime_data, {"text"}, FhemTextInput))


class FhemText(PublishedCommand, TextEntity):
    _attr_native_min = 0
    _attr_native_max = 255

    @property
    def native_value(self):
        return self.reported if self.reported is not None and len(self.reported) <= self.native_max else None

    async def async_set_value(self, value):
        await self.send([value])


class FhemTextInput(PublishedInput, TextEntity):
    _attr_native_min = 0
    _attr_native_max = 255

    @property
    def native_value(self):
        return str(self.input_value) if self.input_value is not None else ""

    async def async_set_value(self, value):
        await self.set_input(value)
