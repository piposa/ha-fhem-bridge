"""Diagnostic downloads without tokens, attribute contents or reading values."""

from .device_config import CONF_LOGS, PERMISSIONS, settings
from .const import CONF_DEVICES, DOMAIN


def diagnostics(entry, sources=None):
    current = settings(entry)
    runtime = getattr(entry, "runtime_data", None)
    chosen = set(current.get(CONF_DEVICES, ())) if sources is None else set(sources)
    return {
        "connection": {
            "connected": bool(runtime and runtime.client and runtime.client.writer and not runtime.client.writer.is_closing()),
            "capabilities": sorted(runtime.client.capabilities) if runtime and runtime.client else [],
            "frames": dict(getattr(runtime.client, "frames", {})) if runtime and runtime.client else {},
            "bytes": dict(getattr(runtime.client, "bytes", {})) if runtime and runtime.client else {},
        },
        "devices": [
            {
                "source": source,
                "type": profile.get("type"),
                "model": profile.get("attributes", {}).get("model") or profile.get("device_model"),
                "group": runtime.device_key(source),
                "readings": list(profile.get("readings", [])),
                "actions": sorted(profile.get("actions", {})),
                "permissions": {key: source in current.get(key, ()) for key in (*PERMISSIONS, CONF_LOGS)},
                "publications": [
                    {"key": key, "mode": item.get("mode")}
                    for key, item in runtime.publications.resolved.get(source, {}).get("choices", {}).items()
                ],
            }
            for source in sorted(chosen)
            if runtime and (profile := runtime.profiles.get(source)) is not None
        ],
    }


async def async_get_config_entry_diagnostics(hass, entry):
    return diagnostics(entry)


async def async_get_device_diagnostics(hass, entry, device):
    runtime = getattr(entry, "runtime_data", None)
    sources = []
    if runtime:
        prefix = f"{entry.unique_id}/"
        for domain, identifier in device.identifiers:
            if domain == DOMAIN and identifier.startswith(prefix):
                key = identifier.removeprefix(prefix)
                sources.extend(runtime.groups.get(key, {}).get("members", [key]))
    return diagnostics(entry, sources)
