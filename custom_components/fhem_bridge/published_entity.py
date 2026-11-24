"""Shared entity behavior for user-selected FHEM commands."""

from asyncio import Lock

from homeassistant.exceptions import HomeAssistantError

from .entity import FhemEntity
from .profiles import serialize_argument


def published_commands(runtime, mode, factory):
    modes = {mode} if isinstance(mode, str) else mode
    return [
        factory(runtime, device, key, item)
        for device, result in runtime.publications.resolved.items()
        for key, item in result["commands"].items()
        if item["mode"] in modes
    ]


class PublishedCommand(FhemEntity):
    def __init__(self, runtime, device, key, item):
        super().__init__(runtime, device, f"published/{key}", item["label"] or item["name"])
        self._attr_name = item["label"] or item["name"]
        self.publication_key = key
        self.item = item
        self._bridge_hidden = item.get("hidden", False)
        self._attr_entity_registry_visible_default = not self._bridge_hidden

    @property
    def blocked_reason(self):
        return self.runtime.command_blocked(self.device, self.item["kind"], self.item["name"])

    @property
    def extra_state_attributes(self):
        return {**(getattr(self, "_attr_extra_state_attributes", None) or {}),
                "fhem_permission": self.blocked_reason or "allowed"}

    @property
    def available(self):
        return super().available and self.publication_key in (
            self.runtime.publications.resolved.get(self.device, {}).get("commands", {})
        )

    @property
    def reported(self):
        value = self.runtime.values.get((self.device, self.item["reading"]))
        if self.item["name"] == "controlMode" and value and value.startswith("set_"):
            return None
        return value

    async def send(self, args, *, typed=True, fallback_fields=None):
        if not self.available:
            raise HomeAssistantError("Diese FHEM-Funktion ist derzeit nicht verfügbar.")
        return await self.runtime.execute(
            self.device, self.item["kind"], self.item["name"],
            [] if typed else args, inputs=args if typed else None, fallback_fields=fallback_fields,
        )

    def form_values(self):
        return [
            self.runtime.input_values.get((self.device, self.publication_key, index))
            for index in range(len(self.item["form_fields"]))
        ]

    def update_from_bridge(self, frame):
        if frame is None or (frame["type"] == "reading" and frame["reading"] == self.item["reading"]):
            self.async_write_ha_state()


def published_inputs(runtime, modes, factory):
    return [
        factory(runtime, device, key, item, index, mode)
        for device, result in runtime.publications.resolved.items()
        for key, item in result["commands"].items()
        if item["mode"] in {"form", "direct"}
        for index, mode in enumerate(item["input_modes"])
        if mode in modes
    ]


INPUT_LABELS = {
    "seconds": "Dauer (Sekunden)", "percent": "Prozent", "temperature": "Temperatur",
    "hold": "Haltezeit", "ramp": "Rampe", "startDate": "Startdatum", "endDate": "Enddatum",
    "startTime": "Startzeit", "endTime": "Endzeit",
}


class PublishedInput(PublishedCommand):
    """Input for a staged or direct FHEM command."""

    def __init__(self, runtime, device, key, item, index, mode):
        super().__init__(runtime, device, key, item)
        self.input_key = device, key, index
        self.field = item["form_fields"][index]
        self.input_mode = mode
        self.direct_lock = Lock() if item["mode"] == "direct" else None
        self._attr_unique_id = f"{runtime.identifier(device)}/published_input/{key}/{index}"
        label = self.field.get("label")
        label = INPUT_LABELS.get(label, label or f"Argument {index + 1}")
        if self.direct_lock is None:
            self._attr_name = f"{item['label']} · {label}"

    @property
    def input_value(self):
        return self.runtime.input_values.get(self.input_key)

    async def set_input(self, value):
        if self.direct_lock is None:
            self.stage_value(value)
            return
        async with self.direct_lock:
            if value == "" and not self.field.get("allow_empty"):
                self.runtime.input_values.pop(self.input_key, None)
            else:
                fallback = self.item["form_fields"] if self.item["fields"] is None else None
                await self.send([value], fallback_fields=fallback)
                self.runtime.input_values[self.input_key] = value
            self.async_write_ha_state()

    def stage_value(self, value):
        self.runtime.input_values.pop(self.input_key, None)
        try:
            if value != "":
                serialize_argument(self.field, value)
                self.runtime.input_values[self.input_key] = value
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        finally:
            self.async_write_ha_state()

    def update_from_bridge(self, frame):
        if frame is None:
            self.async_write_ha_state()
