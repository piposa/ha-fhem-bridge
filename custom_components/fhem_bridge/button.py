"""Buttons for zero-argument FHEM actions."""

from asyncio import Lock
from time import monotonic

from homeassistant.components.button import ButtonEntity

from .device_config import add_entities
from .entity_refresh import managed_entities
from .entity import FhemEntity, switch_supported
from .published_entity import PublishedCommand, published_commands
from .templates import COVER_BUTTON_COMMANDS, dimmer_outputs, redundant_button_actions


@managed_entities
async def async_setup_entry(hass, entry, async_add_entities):
    """Expose approved no-argument actions as buttons."""
    runtime = entry.runtime_data
    dimmers = {device for device, _ in dimmer_outputs(runtime)}
    add_entities(entry.runtime_data, async_add_entities, [
        FhemButton(runtime, device, action)
        for device, profile in runtime.profiles.items()
        for redundant in (redundant_button_actions(runtime.publications.resolved[device]),)
        for action, schema in profile["actions"].items()
        if not schema and action in COVER_BUTTON_COMMANDS.keys() | {"toggle"} and action not in redundant
        and not (action == "toggle" and device in dimmers)
        and not (action in {"turn_on", "turn_off"} and switch_supported(profile))
    ])
    add_entities(entry.runtime_data, async_add_entities, published_commands(runtime, {"button", "form"}, PublishedButton))


class FhemButton(FhemEntity, ButtonEntity):
    """One explicitly authorized action."""

    control_command = "on"

    def __init__(self, runtime, device, action):
        super().__init__(runtime, device, f"action/{action}", action)
        siblings = runtime.group_sources(runtime.device_key(device))
        matching = sum(
            source in runtime.writable and runtime.profiles[source]["actions"].get(action) == {}
            for source in siblings
        )
        if matching <= 1:
            self._attr_name = action
        if action == "toggle":
            self.use_semantic_name("toggle")
        self.action = action
        self.control_command = COVER_BUTTON_COMMANDS.get(action, action)

    async def async_press(self):
        await self.runtime.execute(self.device, "set", self.control_command, [])

    def update_from_bridge(self, frame):
        if frame is None:
            self.async_write_ha_state()


class PublishedButton(PublishedCommand, ButtonEntity):
    def __init__(self, runtime, device, key, item):
        super().__init__(runtime, device, key, item)
        self.press_lock = Lock()
        self.observe_until = 0
        self.observation = None

    async def async_press(self):
        values = self.form_values() if self.item["mode"] == "form" else self.item["arguments"]
        async with self.press_lock:
            await self._press(values)

    async def _press(self, values):
        if self.item.get("observe"):
            self.observe_until = monotonic() + 30
            self.observation = None
            self._attr_extra_state_attributes = {"status": "pending"}
        try:
            if self.item["mode"] == "form":
                fallback = self.item["form_fields"] if self.item["fields"] is None else None
                result = await self.send(values, fallback_fields=fallback)
            else:
                result = await self.send(values, typed=self.item.get("typed", False))
        except BaseException:
            self.observe_until = 0
            self._attr_extra_state_attributes = None
            if self.item["kind"] == "get":
                self.async_write_ha_state()
            raise
        if self.item["kind"] == "get":
            self._attr_extra_state_attributes = {
                key: result[key] for key in ("status", "result", "truncated") if key in result
            }
            if result["status"] == "accepted" and self.observation:
                self._attr_extra_state_attributes.update(self.observation)
            if result["status"] != "accepted":
                self.observe_until = 0
            self.async_write_ha_state()

    def update_from_bridge(self, frame):
        if frame is None:
            self.observe_until = 0
            self.async_write_ha_state()
        elif frame["type"] == "reading" and self.observe_until > monotonic() and frame["reading"] == self.item.get("observe"):
            self.observe_until = 0
            self.observation = {
                "observed_reading": frame["reading"], "observed_value": frame["value"],
                "observed_at": frame.get("source_ts"),
            }
            if self._attr_extra_state_attributes.get("status") == "accepted":
                self._attr_extra_state_attributes.update(self.observation)
                self.async_write_ha_state()
