"""Apply publication changes to the affected Home Assistant entities."""

from collections import defaultdict
from copy import deepcopy
from functools import wraps

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import async_get_current_platform


def _configuration(entity):
    """Capture the constructor's declarative fields before HA attaches the entity."""
    return type(entity), deepcopy({
        key: value for key, value in vars(entity).items()
        if isinstance(value, (str, int, float, bool, dict, list, tuple, set, frozenset, type(None)))
    })


def managed_entities(setup):
    @wraps(setup)
    async def register(hass, entry, async_add_entities):
        runtime = entry.runtime_data
        platform = async_get_current_platform()

        async def build():
            entities = {}

            def collect(items, **options):
                for entity in items:
                    entities[entity.unique_id] = (entity, options, _configuration(entity))

            await setup(hass, entry, collect)
            return entities

        tracked = await build()
        runtime.entity_platforms[platform.domain] = platform, build, tracked
        grouped = defaultdict(list)
        for entity, options, _ in tracked.values():
            grouped[options.get("config_subentry_id")].append(entity)
        for owner, entities in grouped.items():
            async_add_entities(entities, config_subentry_id=owner)

    return register


async def refresh_platform(platform, build, tracked, devices, present):
    proposed = await build()
    additions = defaultdict(list)
    for unique_id in tracked.keys() | proposed.keys():
        old = tracked.get(unique_id)
        new = proposed.get(unique_id)
        candidates = [record[0] for record in (old, new) if record]
        if not any(getattr(entity, "device", None) in devices for entity in candidates):
            continue
        if old and new and old[1:] == new[1:]:
            continue
        if old:
            entity = old[0]
            entity_id = entity.entity_id
            if entity_id is not None and platform.entities.get(entity_id) is entity:
                await platform.async_remove_entity(entity_id)
            del tracked[unique_id]
            if not new and entity.device in present:
                registry = er.async_get(platform.hass)
                key = registry.async_get_entity_id(platform.domain, platform.platform_name, unique_id)
                if key is not None:
                    registry.async_remove(key)
        if new:
            entity, options, _ = new
            additions[options.get("config_subentry_id")].append((unique_id, new))
    for owner, records in additions.items():
        await platform.async_add_entities([record[0] for _, record in records], config_subentry_id=owner)
        tracked.update(records)
