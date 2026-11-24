"""Publish one-argument FHEM selection commands."""

from homeassistant.components.select import SelectEntity

from .device_config import add_entities
from .entity_refresh import managed_entities
from .published_entity import PublishedCommand, PublishedInput, published_commands, published_inputs


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    add_entities(entry.runtime_data, async_add_entities, published_commands(entry.runtime_data, "select", FhemSelect))
    add_entities(entry.runtime_data, async_add_entities, published_inputs(entry.runtime_data, {"select"}, FhemSelectInput))


class FhemSelect(PublishedCommand, SelectEntity):
    @property
    def options(self):
        return self.item["fields"][0]["options"]

    @property
    def current_option(self):
        return self.reported if self.reported in self.options else None

    async def async_select_option(self, option):
        await self.send([option])


class FhemSelectInput(PublishedInput, SelectEntity):
    @property
    def options(self):
        return self.field["options"]

    @property
    def current_option(self):
        return self.input_value

    async def async_select_option(self, option):
        await self.set_input(option)
