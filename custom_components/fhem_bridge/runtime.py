"""Bridge connection lifecycle and HA state dispatch."""

import asyncio
import base64
from collections import defaultdict
from contextlib import suppress
from datetime import UTC, datetime
from itertools import batched
import logging
import json
import random
from time import monotonic
from urllib.parse import quote

from homeassistant.components import persistent_notification
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr

from .calculator import calculator_attributes
from .client import FRAME_LIMIT, BridgeClient, BridgeError
from .device_config import settings, device_subentries, CONF_LOGS
from .const import (
    CONF_DEVICE_ALIASES, CONF_DEVICE_GROUPS, CONF_DEVICES, CONF_EDIT_ATTRIBUTES,
    CONF_FINGERPRINT, CONF_IMPORT_AREAS, CONF_IMPORT_LABELS, CONF_QUERY, CONF_TECHNICAL, CONF_WRITABLE, DOMAIN, PANEL_PATH,
)
from .groups import member_index
from .entity_refresh import refresh_platform

from .profiles import command_description, fields_for, parse_specs, serialize_inputs
from .publications import Publications, technical
from .template_library import model_of

_LOGGER = logging.getLogger(__name__)
_SYNC_LOGGER = logging.getLogger(__name__ + ".sync")
_SETUP_LOGGER = logging.getLogger("custom_components.fhem_bridge.config_flow.diagnostics")
_DEVICE_LOGGER = logging.getLogger(__name__ + ".device_logs")
_DEVICE_LOGGER.setLevel(logging.INFO)
CONNECTION_ERRORS = (BridgeError, OSError, TimeoutError, ValueError, KeyError)
READINGS_PER_BATCH = 64
LEGACY_READING_LIMIT = 128


def make_client(data, push=None):
    """Create a transport for a configured endpoint."""
    return BridgeClient(data["host"], data["port"], data["token"], data.get(CONF_FINGERPRINT, ""), push)


class Runtime:
    """Own the session for one bridge and dispatch per-device changes."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.client = None
        self.task = None
        options = settings(entry)
        self.loaded_settings = options
        self.connected = False
        self.last_connected = None
        self.last_disconnected = None
        self.last_connection_error = None
        self.connection_error = None
        self.disconnect_reason = None
        self.selected = tuple(options.get(CONF_DEVICES, ()))
        self.groups = options.get(CONF_DEVICE_GROUPS, {})
        self.source_groups = member_index(self.groups, set(self.selected))
        self.device_aliases = entry.options.get(CONF_DEVICE_ALIASES, {})
        self.writable = frozenset(options.get(CONF_WRITABLE, ()))
        self.query = frozenset(options.get(CONF_QUERY, ()))
        self.edit_attributes = frozenset(options.get(CONF_EDIT_ATTRIBUTES, ()))
        self.technical = frozenset(options.get(CONF_TECHNICAL, ()))
        self.log_devices = frozenset(options.get(CONF_LOGS, ()))
        self._permission_stamp = object()
        self._permission_sets = {}
        self.controls_cache = {}
        self.controls_locks = defaultdict(asyncio.Lock)
        self.catalog_cache = {}
        self.catalog_locks = [asyncio.Lock() for _ in range(8)]
        self.legacy_startup_catalog_lock = asyncio.Lock()
        self.schedule_locks = [asyncio.Lock() for _ in range(8)]
        self.schedule_pending = {}
        self.catalog_epoch = 0
        self.device_catalog_epochs = {}
        self.inventory_epoch = 0
        self.profile_epoch = None
        self.inventory_cache = None
        self.inventory_lock = asyncio.Lock()
        self.sync_lock = asyncio.Lock()
        self.subscription_plan = {}
        self.subscription_streams = {}
        self.inactive_sources = set()
        self.entity_platforms = {}
        self.sync_number = 0
        self.sync_revision = None
        self.recovering_sources = set()
        self.retry_delays = {}
        self.retry_at = {}
        self.retry_handle = None
        self.input_values = {}
        self.timestamps = {}
        self.profiles = {}
        self.values = {}
        self.active = set()
        self.subscription_errors = {}
        self.sequences = {}
        self.streams = set()
        self.listeners = defaultdict(set)
        self.reading_listeners = defaultdict(lambda: defaultdict(set))
        self.snapshot_ready = asyncio.Event()
        self.changed = asyncio.Event()
        self.catalog_dirty = False
        self.legacy_reconnect = False
        self.metadata_dirty = set()

        self.publications = Publications(self)
        self.attribute_upload_lock = asyncio.Lock()
        self.configuration_lock = asyncio.Lock()
        self.config_status = None
        self.config_notification_context = None

    async def start(self):
        """Load profiles before the entity platforms start."""
        for phase, operation in (("templates", self.publications.load), ("initial_sync", self._connect)):
            started = monotonic()
            _SETUP_LOGGER.debug("Bridge %s setup phase=%s started", self.entry.entry_id, phase)
            try:
                await operation()
            finally:
                elapsed = (monotonic() - started) * 1000
                log = _SETUP_LOGGER.warning if elapsed >= 3000 else _SETUP_LOGGER.debug
                log("Bridge %s setup phase=%s finished after %.0f ms",
                    self.entry.entry_id, phase, elapsed)

    def supervise(self):
        """Maintain the session after the platforms have loaded."""
        self.task = self.entry.async_create_background_task(
            self.hass, self._run(), "FHEM Bridge session"
        )

    async def stop(self):
        """Stop reconnecting and close the current session."""
        if self.retry_handle is not None:
            self.retry_handle.cancel()
            self.retry_handle = None
        if self.task is not None:
            self.task.cancel()
            await asyncio.wait({self.task})
            if not self.task.cancelled():
                self.task.result()
        if self.client is not None:
            await self.client.close()

    async def _connect(self):
        entry_id = self.entry.entry_id
        _LOGGER.debug("Bridge entry %s: opening TLS session and authenticating", entry_id)
        self.sequences.clear()
        if self.retry_handle is not None:
            self.retry_handle.cancel()
            self.retry_handle = None
        self.retry_at.clear()
        self.retry_delays.clear()
        self.metadata_dirty.clear()
        self.sync_revision = None
        self.client = make_client(self.entry.data, self._push)
        try:
            server_id = await self.client.connect()
            self.client.reader_task.add_done_callback(lambda _: self.changed.set())
            if server_id != self.entry.unique_id:
                raise BridgeError("unexpected_server")
            _LOGGER.debug("Bridge entry %s: session authenticated, synchronizing %d definitions",
                          entry_id, len(self.selected))
            if "config_status_push" in self.client.capabilities:
                self.client.heartbeat = self.entry.async_create_background_task(
                    self.hass, self.client.keepalive(), "FHEM Bridge heartbeat"
                )
            await self._sync()
            if "config_save" in self.client.capabilities:
                await self.configuration_status()
            self.connected = True
            self.connection_error = self.disconnect_reason = None
            self.last_connected = datetime.now(UTC)
            self._notify_all()
            _LOGGER.debug("Bridge entry %s online with %d active definitions", entry_id, len(self.active))
        except BaseException:
            await self.client.close()
            raise

    async def _sync(self):
        async with self.sync_lock:
            self.catalog_dirty = False
            epoch = getattr(self.client, "epoch", None)
            retained = self.profiles if epoch is not None and epoch == self.profile_epoch else {}
            if not retained:
                self.controls_cache.clear()
                self.invalidate_catalog()
            self.profile_epoch = epoch
            self.inventory_cache = None
            self.subscription_plan.clear()
            self.subscription_streams.clear()
            self.inactive_sources.clear()
            self.recovering_sources.clear()
            self.streams.clear()
            self.values.clear()
            self.timestamps.clear()
            self.active.clear()
            started = monotonic()
            failures = {}
            profiles = await self.client.descriptions(self.selected, self.selected, cached=retained,
                                                      failures=failures)
            described = monotonic()
            for device, profile in profiles.items():
                if retained.get(device) is not profile:
                    if error := await self._read_calculator_units(device, profile):
                        failures[device] = error
            units = monotonic()
            changed_profiles = {device: profile for device, profile in profiles.items()
                                if retained.get(device) is not profile and device not in failures}
            for device in self.publications.resolved.keys() - profiles.keys():
                self.publications.resolved.pop(device)
            if retained:
                await self.publications.sync(changed_profiles, partial=True, failures=failures)
            else:
                await self.publications.sync(changed_profiles, failures=failures)
            profiles = {device: profile for device, profile in profiles.items() if device not in failures}
            self.subscription_errors = dict(failures)
            self._profile_failures(failures)
            resolved = monotonic()
            previous_profiles = self.profiles
            self.profiles = profiles
            await self._subscribe_profiles(profiles)
            subscribed = monotonic()
            self._update_device_names(profiles)
            if self.entity_platforms:
                changed = {device for device in previous_profiles.keys() | profiles.keys()
                           if previous_profiles.get(device) != profiles.get(device)}
                await self.refresh_entities(changed)
            self._notify_all()
            self._log_sync("session", started, {
                "profiles": described - started, "attributes": units - described,
                "publications": resolved - units, "subscriptions": subscribed - resolved,
                "entity_updates": monotonic() - subscribed,
            })

    def _log_sync(self, reason, started, phases):
        self.sync_number += 1
        elapsed = monotonic() - started
        _SYNC_LOGGER.log(
            logging.WARNING if elapsed >= 5 else logging.DEBUG,
            "Bridge %s sync=%d reason=%s revision=%s total_ms=%.0f active=%d failed=%d phases_ms=%s",
            self.entry.entry_id, self.sync_number, reason, self.sync_revision, elapsed * 1000,
            len(self.active), len(self.subscription_errors),
            {name: round(duration * 1000) for name, duration in phases.items()},
        )

    async def _subscribe_profiles(self, profiles, *, incremental=False):
        registry = dr.async_get(self.hass)
        batches = []
        plans = {}
        read_count = 0
        filtered = "reading_filter" in self.client.capabilities
        can_extend = filtered and "subscribe_more" in self.client.capabilities
        for device, profile in profiles.items():
            item = registry.async_get_device_by_identifier(
                (DOMAIN, self.identifier(self.device_key(device))), self.entry.entry_id,
            )
            if item and item.disabled:
                await self._remove_subscriptions((device,))
                continue
            rights = tuple(device in getattr(self, name) for name in
                           ("writable", "query", "edit_attributes", "technical", "log_devices"))
            if not profile["readings"] and not profile["events"] and not any(rights):
                await self._remove_subscriptions((device,))
                continue
            names = tuple(self.publications.subscription(device, profile) if filtered else profile["readings"])
            plan = (profile["name"], names, rights, profile.get("device_instance"))
            if incremental and device not in self.recovering_sources and self.subscription_plan.get(device) == plan:
                self.retry_delays.pop(device, None)
                if self.retry_at.pop(device, None) is not None:
                    self._schedule_retry()
                continue
            if not can_extend and len(names) > LEGACY_READING_LIMIT:
                reason = f"{len(names)} readings exceed the server limit of {LEGACY_READING_LIMIT}. Update HABridge."
                await self._remove_subscriptions((device,))
                self.subscription_errors[device] = reason
                _SYNC_LOGGER.warning("FHEM subscription skipped for %s: %s", profile["name"], reason)
                continue
            plans[device] = plan
            first_count = min(len(names), READINGS_PER_BATCH) if can_extend else len(names)
            if incremental or not batches or len(batches[-1]) == 16 or read_count + first_count > READINGS_PER_BATCH:
                batches.append([])
                read_count = 0
            batches[-1].append(device)
            read_count += first_count
        for batch in batches:
            await self._subscribe_batch(batch, plans, incremental, filtered, can_extend)

    async def _subscribe_batch(self, batch, plans, incremental, filtered, can_extend):
        start = monotonic()
        self.inactive_sources.difference_update(batch)
        replace = incremental and "subscription_delta" in self.client.capabilities
        fields = {"writable": [device for device in batch if plans[device][2][0]]}
        if self.enhanced:
            fields.update({key: [device for device in batch if plans[device][2][index]] for index, key in
                           enumerate(("query", "edit_attributes", "technical"), 1)})
        if "device_logs" in self.client.capabilities:
            fields[CONF_LOGS] = [device for device in batch if plans[device][2][4]]
        if filtered:
            fields["readings"] = {device: list(plans[device][1][:READINGS_PER_BATCH] if can_extend
                                               else plans[device][1]) for device in batch}
        if replace:
            fields["replace"] = True
            device = batch[0]
            previous = self.subscription_plan.get(device)
            fields["reset"] = (device in self.recovering_sources or not previous or previous[0] != plans[device][0]
                               or previous[3] != plans[device][3])
            if previous and not fields["reset"] and can_extend:
                retained = sorted(set(previous[1]) & set(plans[device][1]))
                if len(json.dumps(retained)) <= FRAME_LIMIT // 2:
                    fields["retain_readings"] = retained
        failed = None
        stream = None
        try:
            reply = await self.client.request("subscribe", devices=batch,
                                              append=replace or bool(self.subscription_streams), **fields)
            stream = reply["stream"]
            replied = monotonic()
            async with asyncio.timeout(8):
                while stream not in self.sequences:
                    self.snapshot_ready.clear()
                    await self.snapshot_ready.wait()
            snapshot = monotonic()
        except (BridgeError, TimeoutError) as err:
            if isinstance(err, BridgeError) and str(err) not in {"not_allowed", "bad_request", "limit_exceeded"}:
                raise
            if isinstance(err, TimeoutError) and "subscription_delta" not in self.client.capabilities:
                raise
            if isinstance(err, BridgeError) and len(batch) > 1:
                for device in batch:
                    await self._subscribe_batch([device], plans, incremental, filtered, can_extend)
                return
            failed = str(err) or type(err).__name__
            await self._remove_subscriptions(batch, force=True)
        if failed:
            for device in batch:
                self.subscription_errors[device] = failed
                if failed in {"TimeoutError", "not_allowed"}:
                    self._retry_device(device)
            _SYNC_LOGGER.warning("Bridge %s revision=%s subscription failed devices=%s reason=%s",
                                 self.entry.entry_id, self.sync_revision, batch, failed)
            return

        self.subscription_streams.update(dict.fromkeys(batch, stream))
        retained = set() if reply.get("reset") else set(fields.get("retain_readings", ()))
        for device in batch:
            try:
                tail = (name for name in plans[device][1][READINGS_PER_BATCH:] if name not in retained)
                for page in batched(tail if can_extend else (), READINGS_PER_BATCH):
                    extension = await self.client.request("subscribe_more", device=device, readings=page)
                    if extension["stream"] != stream:
                        raise BridgeError("unexpected_subscription_stream")
            except (BridgeError, TimeoutError) as err:
                if isinstance(err, BridgeError) and str(err) not in {"not_allowed", "bad_request", "limit_exceeded"}:
                    raise
                if "subscription_delta" not in self.client.capabilities:
                    raise
                await self._remove_subscriptions((device,), force=True)
                self.subscription_errors[device] = str(err) or type(err).__name__
                if self.subscription_errors[device] in {"TimeoutError", "not_allowed"}:
                    self._retry_device(device)
                _SYNC_LOGGER.warning("Bridge %s revision=%s subscription extension failed device=%s reason=%s",
                                     self.entry.entry_id, self.sync_revision, device, self.subscription_errors[device])
                continue
            previous = self.subscription_plan.get(device)
            if previous:
                for name in set(previous[1]) - set(plans[device][1]):
                    self.values.pop((device, name), None)
                    self.timestamps.pop((device, name), None)
            self.subscription_plan[device] = plans[device]
            self.subscription_streams[device] = stream
            self.subscription_errors.pop(device, None)
            self.recovering_sources.discard(device)
            self.retry_delays.pop(device, None)
            if self.retry_at.pop(device, None) is not None:
                self._schedule_retry()
            self.active.add(device)
        elapsed = monotonic() - start
        if elapsed >= 3 or _SYNC_LOGGER.isEnabledFor(logging.DEBUG):
            _SYNC_LOGGER.log(logging.WARNING if elapsed >= 3 else logging.DEBUG,
                             "Bridge %s revision=%s request=%s batch=%s reply_ms=%.0f snapshot_wait_ms=%.0f extension_ms=%.0f",
                             self.entry.entry_id, self.sync_revision, reply.get("id"), batch,
                             (replied - start) * 1000, (snapshot - replied) * 1000, (monotonic() - snapshot) * 1000)

    def _profile_failures(self, failures):
        for device, reason in failures.items():
            if device not in self.active:
                self.subscription_errors[device] = reason
            if reason in {"TimeoutError", "catalog_changed", "not_allowed"}:
                self._retry_device(device)
            _SYNC_LOGGER.warning("Bridge %s revision=%s profile unavailable device=%s reason=%s",
                                 self.entry.entry_id, self.sync_revision, device, reason)

    def _retry_device(self, device):
        if device not in self.retry_at:
            delay = min(2 * self.retry_delays.get(device, 2.5), 60)
            self.retry_delays[device] = delay
            self.retry_at[device] = self.hass.loop.time() + delay
        self._schedule_retry()

    def _schedule_retry(self):
        if self.retry_handle is not None:
            self.retry_handle.cancel()
        self.retry_handle = (self.hass.loop.call_at(min(self.retry_at.values()), self._retry_due)
                             if self.retry_at else None)

    @callback
    def _retry_due(self):
        self.retry_handle = None
        now = self.hass.loop.time()
        due = {device for device, instant in self.retry_at.items() if instant <= now}
        for device in due:
            del self.retry_at[device]
        if due:
            self.metadata_dirty.update(due)
            self.changed.set()
        self._schedule_retry()

    async def _remove_subscriptions(self, devices, *, force=False):
        devices = tuple(devices)
        ids = [device for device in devices if force or device in self.subscription_streams]
        self.inactive_sources.update(devices)
        for device in devices:
            self.active.discard(device)
            self.subscription_plan.pop(device, None)
            for key in [key for key in self.values if key[0] == device]:
                self.values.pop(key, None)
                self.timestamps.pop(key, None)
        if ids and "subscription_delta" in self.client.capabilities:
            try:
                await self.client.request("unsubscribe", devices=ids)
            except TimeoutError:
                # Keep tracking the old stream until a later replacement succeeds.
                _SYNC_LOGGER.warning("Bridge %s: unsubscribe timed out for %s", self.entry.entry_id, ids)
                return
        for device in devices:
            self.subscription_streams.pop(device, None)
        if "subscription_delta" in self.client.capabilities:
            current = set(self.subscription_streams.values())
            # Keep a stream during a batch until its subscriptions are installed.
            self.streams.intersection_update(current)
            self.sequences = {stream: seq for stream, seq in self.sequences.items() if stream in self.streams}

    def _update_device_names(self, profiles):
        registry = dr.async_get(self.hass)
        for key in {self.device_key(device) for device in profiles}:
            primary = self.primary_source(key)
            if primary is None:
                continue
            profile = self.profiles[primary]
            item = registry.async_get_device_by_identifier((DOMAIN, self.identifier(key)), self.entry.entry_id)
            if item is not None:
                registry.async_update_device(
                    item.id, name=profile["attributes"].get("alias") or profile["name"]
                )

    async def _read_calculator_units(self, device, profile):
        names = calculator_attributes(profile)
        units = {}
        if names and "attribute_values" in self.client.capabilities:
            try:
                reply = await self.client.request("attribute_values", device=device, attributes=list(names))
            except (BridgeError, TimeoutError) as err:
                if isinstance(err, BridgeError) and str(err) not in {"not_allowed", "catalog_changed"}:
                    raise
                return str(err) or type(err).__name__
            profile["calculator_units"] = {name: reply["values"].get(name) for name in names}
            return
        for name in names:
            try:
                result = await self._read_attributes(device, profile, attribute=name)
            except HomeAssistantError as err:
                _LOGGER.warning("Could not determine %s for %s: %s", name, profile["name"], err)
                units[name] = None
            else:
                units[name] = result["value"]
        profile["calculator_units"] = units

    async def _refresh_metadata(self, *, reconcile=False):
        devices = set(self.selected) if reconcile else self.metadata_dirty & set(self.selected)
        self.metadata_dirty.difference_update(devices)
        if not devices:
            return
        async with self.sync_lock:
            started = monotonic()
            failures = {}
            profiles = await self.client.descriptions(sorted(devices), devices,
                                                      cached=self.profiles if reconcile else None, failures=failures)
            described = monotonic()
            previous_resolved = self.publications.resolved.copy()
            changed = set()
            removed = devices - profiles.keys() - failures.keys()
            for device in removed:
                if device in self.profiles:
                    await self._remove_subscriptions((device,))
                    del self.profiles[device]
                    self.publications.resolved.pop(device, None)
                    self.subscription_errors.pop(device, None)
                    changed.add(device)
            refresh = {}
            for device, profile in profiles.items():
                previous = self.profiles.get(device)
                if previous and all(previous.get(key) == value for key, value in profile.items()) and device in self.active:
                    continue
                if error := await self._read_calculator_units(device, profile):
                    failures[device] = error
                    continue
                refresh[device] = profile
                if previous is None or any(previous.get(key) != profile.get(key) for key in
                                           ("name", "type", "attributes", "device_model", "calculator_units", "actions", "readings")):
                    changed.add(device)
            units = monotonic()
            if refresh:
                await self.publications.sync(refresh, partial=True, failures=failures)
            refresh = {device: profile for device, profile in refresh.items() if device not in failures}
            self._profile_failures(failures)
            resolved = monotonic()
            if refresh:
                self.profiles.update(refresh)
                await self._subscribe_changed(refresh)
            subscribed = monotonic()
            changed.update(device for device in refresh
                           if previous_resolved.get(device) != self.publications.resolved.get(device))
            self._update_device_names(refresh)
            await self.refresh_entities(changed)
            self._notify_devices(devices)
            self._log_sync("reconcile" if reconcile else "metadata", started, {
                "profiles": described - started, "attributes": units - described,
                "publications": resolved - units, "subscriptions": subscribed - resolved,
                "entity_updates": monotonic() - subscribed,
            })

    async def refresh_entities(self, devices):
        if not devices or not self.entity_platforms:
            return
        groups = {self.device_key(source) for source in devices}
        affected = set(devices) | {source for source in self.selected if self.device_key(source) in groups}
        for platform, build, tracked in self.entity_platforms.values():
            await refresh_platform(platform, build, tracked, affected, self.profiles)

    async def apply_permissions(self):
        """Apply rights in place when the devices and grouping did not change."""
        if "subscription_delta" not in self.client.capabilities or not self.connected:
            return False
        names = dict(zip(
            (CONF_WRITABLE, CONF_QUERY, CONF_EDIT_ATTRIBUTES, CONF_TECHNICAL, CONF_LOGS),
            ("writable", "query", "edit_attributes", "technical", "log_devices"),
            strict=True,
        ))
        async with self.sync_lock:
            previous = self.loaded_settings
            # Recheck after acquiring the lock; simultaneous forms may have saved another change.
            updated = settings(self.entry)
            if {k: v for k, v in updated.items() if k not in names} != {
                    k: v for k, v in previous.items() if k not in names}:
                return False
            affected = set()
            for key, field in names.items():
                before, after = frozenset(previous.get(key, ())), frozenset(updated.get(key, ()))
                setattr(self, field, after)
                affected.update(before ^ after)
            profiles = {device: self.profiles[device] for device in affected if device in self.profiles}
            await self._subscribe_changed(profiles)
            self.loaded_settings = updated
            self._notify_devices(affected)
            return True

    async def refresh_publications(self, devices):
        async with self.sync_lock:
            started = monotonic()
            old = self.publications.resolved.copy()
            profiles = {device: self.profiles[device] for device in devices if device in self.profiles}
            await self.publications.sync(profiles, partial=True)
            resolved = monotonic()
            changes = {device for device, result in self.publications.resolved.items()
                       if old.get(device) != result}
            if changes:
                profiles = {device: self.profiles[device] for device in changes}
                await self._subscribe_changed(profiles)
                subscribed = monotonic()
                await self.refresh_entities(changes)
                self._notify_devices(changes)
                self._log_sync("publications", started, {
                    "publications": resolved - started, "subscriptions": subscribed - resolved,
                    "entity_updates": monotonic() - subscribed,
                })
            if self.legacy_reconnect:
                self.changed.set()

    async def _subscribe_changed(self, profiles):
        if "subscription_delta" in self.client.capabilities:
            await self._subscribe_profiles(profiles, incremental=True)
            return
        # Older versions can safely append newly restored sources. A changed
        # live subscription requires the original full-session fallback.
        if any(device in self.active and
               (profile["name"], tuple(self.publications.subscription(device, profile))) !=
               self.subscription_plan.get(device, (None, ()))[0:2]
               for device, profile in profiles.items()):
            self.legacy_reconnect = True
            return
        await self._subscribe_profiles({device: profile for device, profile in profiles.items()
                                       if device not in self.active})

    async def _run(self):
        delay = 1
        retry_reason = None
        try:
            while True:
                try:
                    if self.client.writer is None or self.client.writer.is_closing():
                        await self.client.close()
                        await self._connect()
                    delay = 1
                    retry_reason = None
                    while True:
                        if self.client.writer.is_closing():
                            raise self.client.read_error or BridgeError("connection_closed")
                        if self.legacy_reconnect:
                            self.legacy_reconnect = False
                            raise BridgeError("legacy_subscription_refresh")
                        if self.catalog_dirty:
                            self.catalog_dirty = False
                            await self._refresh_metadata(reconcile=True)
                            continue
                        if self.metadata_dirty:
                            await self._refresh_metadata()
                            continue
                        self.changed.clear()
                        try:
                            async with asyncio.timeout(15):
                                await self.changed.wait()
                        except TimeoutError:
                            if "config_save" in self.client.capabilities:
                                if "config_status_push" not in self.client.capabilities:
                                    await self.configuration_status()
                            else:
                                await self.client.request("ping")
                except CONNECTION_ERRORS as err:
                    reason = str(err) if isinstance(err, BridgeError) else type(err).__name__
                    if self.connected:
                        self.last_disconnected = datetime.now(UTC)
                        _LOGGER.warning("Bridge entry %s connection interrupted (%s)", self.entry.entry_id, reason)
                    elif reason != retry_reason:
                        _LOGGER.warning("Bridge entry %s reconnect failed (%s)", self.entry.entry_id, reason)
                    retry_reason = reason
                    self.connected = False
                    _LOGGER.debug("Bridge entry %s reconnect scheduled in about %d s (%s)",
                                  self.entry.entry_id, delay, reason)
                    offline = isinstance(err, (TimeoutError, ConnectionError)) or reason == "connection_closed"
                    self.disconnect_reason = reason if offline else None
                    self.connection_error = None if offline else reason
                    if self.connection_error:
                        self.last_connection_error = self.connection_error
                    self.active.clear()
                    self._notify_all()
                    await self.client.close()
                    await asyncio.sleep(delay + random.random())
                    delay = min(delay * 2, 60)
        finally:
            await self.client.close()

    def _push(self, frame):
        kind = frame["type"]
        if kind == "config_status":
            self.update_config_status(frame)
            return
        if kind == "log":
            device = frame.get("device")
            if device in self.log_devices and device in self.current_permissions[CONF_LOGS]:
                _DEVICE_LOGGER.info("FHEM [%s]: %s", self.profiles.get(device, {}).get("name", device), frame["message"])
            return
        if kind == "catalog_changed":
            device = frame.get("device")
            scope = frame.get("scope")
            self.sync_revision = frame.get("revision")
            if scope in (None, "inventory", "reconcile"):
                self.inventory_epoch += 1
                self.inventory_cache = None
            if scope == "controls" or frame.get("controls"):
                self.invalidate_catalog()
                self.controls_cache.clear()
            affected = set(self.groups.get(device, {}).get("members", ()))
            if device in self.selected:
                affected.add(device)
            if affected:
                for source in affected:
                    self.invalidate_catalog(source)
                    self.controls_cache.pop(source, None)
                self.metadata_dirty.update(affected)
                self.changed.set()
            elif device is None and scope in (None, "reconcile"):
                self.invalidate_catalog()
                self.controls_cache.clear()
                self.catalog_dirty = True
                self.changed.set()
            return
        if kind == "snapshot":
            for item in frame["items"]:
                if item["device"] not in self.inactive_sources:
                    self._record(item)
            return
        if kind == "snapshot_end":
            self.streams.add(frame["stream"])
            self.sequences[frame["stream"]] = frame["seq"]
            self.snapshot_ready.set()
            return
        if kind in {"reading", "readings", "event", "reading_gap"}:
            stream = frame["stream"]
            if kind == "reading_gap" or frame["seq"] != self.sequences.get(stream, -2) + 1:
                affected = {source for source, channel in self.subscription_streams.items() if channel == stream}
                if not affected or "subscription_delta" not in self.client.capabilities:
                    raise BridgeError("sequence_gap")
                self.recovering_sources.update(affected)
                self.active.difference_update(affected)
                self.metadata_dirty.update(affected)
                self._notify_devices(affected)
                self.changed.set()
                _SYNC_LOGGER.warning("Bridge %s: sequence gap in %s; refreshing %d definitions",
                                     self.entry.entry_id, stream, len(affected))
            self.sequences[stream] = frame["seq"]
            if stream not in self.streams:
                return
            if kind == "event":
                if frame["device"] not in self.inactive_sources:
                    for listener in tuple(self.listeners.get(frame["device"], ())):
                        listener(frame)
                return
            if kind == "reading_gap":
                return
            items = frame["items"] if kind == "readings" else (frame,)
            changed = []
            for item in items:
                device, name = item["device"], item["reading"]
                if device in self.recovering_sources or device in self.inactive_sources:
                    continue
                key = (device, name)
                if self.values.get(key) == item["value"] and self.timestamps.get(key) == item.get("source_ts"):
                    continue
                self._record(item)
                changed.append({**item, "type": "reading"})
            for item in changed:
                device, name = item["device"], item["reading"]
                for listener in tuple(self.reading_listeners.get(device, {}).get(name, ())):
                    listener(item)
                for listener in tuple(self.listeners.get(device, ())):
                    listener(item)

    def _record(self, item):
        key = (item["device"], item["reading"])
        self.values[key] = item["value"]
        self.timestamps[key] = item.get("source_ts")

    def _notify_devices(self, devices):
        for device in devices:
            self._notify_source(device)
        for listener in tuple(self.listeners.get(f"bridge-status:{self.entry.unique_id}", ())):
            listener(None)

    def _notify_source(self, device):
        for listener in tuple(self.listeners.get(device, ())):
            listener(None)
        for listeners in self.reading_listeners.get(device, {}).values():
            for listener in tuple(listeners):
                listener(None)

    def _notify_all(self):
        for device in self.listeners.keys() | self.reading_listeners.keys():
            self._notify_source(device)

    def identifier(self, device):
        """Keep identities stable across FHEM name and alias changes."""
        return f"{self.entry.unique_id}/{device}"

    def device_key(self, source):
        return self.source_groups.get(source, source)

    def group_sources(self, key):
        group = self.groups.get(key)
        if group is None:
            return [key] if key in self.active else []
        primary = group["primary"]
        return [
            source for source in [primary, *(source for source in group["members"] if source != primary)]
            if source in self.active and self.device_key(source) == key
        ]

    def primary_source(self, key):
        sources = self.group_sources(key)
        return sources[0] if sources else None

    def device_info(self, source):
        key = self.device_key(source)
        primary = self.groups.get(key, {}).get("primary", source)
        profile = self.profiles.get(primary, self.profiles[source])
        attrs = profile["attributes"]
        sub = next((sub for sub in device_subentries(self.entry) if sub.data["key"] == key), None)
        area_id = sub.data.get("area_id") if sub and "area_id" in sub.data else self.entry.options.get(CONF_IMPORT_AREAS, {}).get(key)
        area = ar.async_get(self.hass).async_get_area(area_id) if area_id else None
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.identifier(key))},
            name=attrs.get("alias") or profile["name"],
            model=attrs.get("model") or profile["type"],
            suggested_area=area.name if area else None,
            configuration_url=f"homeassistant://{PANEL_PATH}?device={quote(self.identifier(key), safe='')}",
        )

    def listen_for_imported_devices(self):
        """Apply the import labels once when HA registers a new device."""
        assignments = {
            (DOMAIN, self.identifier(key)): set(labels)
            for key, labels in self.entry.options.get(CONF_IMPORT_LABELS, {}).items()
        }
        assignments.update({(DOMAIN, self.identifier(sub.data["key"])): set(sub.data["labels"])
                            for sub in device_subentries(self.entry) if sub.data.get("labels")})
        if not assignments:
            return lambda: None
        registry = dr.async_get(self.hass)
        labels = lr.async_get(self.hass)

        @callback
        def add_labels(event):
            if event.data["action"] != "create":
                return
            device = registry.async_get(event.data["device_id"])
            if device is None or device.config_entry_id != self.entry.entry_id:
                return
            selected = set().union(*(assignments.pop(identifier, ()) for identifier in device.identifiers))
            selected = {label for label in selected if labels.async_get_label(label) is not None}
            if selected - device.labels:
                registry.async_update_device(device.id, labels=device.labels | selected)

        return self.hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, add_labels)

    def migrate_group_devices(self):
        """Move existing channel entities into the group while retaining entity IDs."""
        devices = dr.async_get(self.hass)
        entities = er.async_get(self.hass)
        owners = {sub.data["key"]: sub.subentry_id for sub in device_subentries(self.entry)}
        prefix = self.identifier("")
        visible = {self.device_key(source) for source in self.selected}
        targets = {}
        previous_devices = {old_id for old_id, source in self.device_aliases.items()
                            if source in self.active and self.device_key(source) != source}
        for item in er.async_entries_for_config_entry(entities, self.entry.entry_id):
            if not item.unique_id.startswith(prefix):
                continue
            source = item.unique_id.removeprefix(prefix).split("/", 1)[0]
            if source not in self.active:
                continue
            key = self.device_key(source)
            if key not in targets:
                targets[key] = devices.async_get_device_by_identifier((DOMAIN, self.identifier(key)), self.entry.entry_id)
            target = targets[key]
            if target is None:
                targets[key] = target = devices.async_get_or_create(
                    config_entry_id=self.entry.entry_id, config_subentry_id=owners.get(key), **self.device_info(source)
                )
            if item.device_id != target.id:
                if item.device_id:
                    previous_devices.add(item.device_id)
                entities.async_update_entity(item.entity_id, device_id=target.id)
        for old_id in previous_devices:
            old = devices.async_get(old_id)
            if old is None or old.config_entry_id != self.entry.entry_id:
                continue
            if any(domain == DOMAIN and identifier.startswith(prefix) and identifier.removeprefix(prefix) in visible
                   for domain, identifier in old.identifiers):
                continue
            if not er.async_entries_for_device(entities, old_id, include_disabled_entities=True):
                devices.async_remove_device(old_id)

    async def write(self, device, operation, **fields):
        if device not in self.active:
            raise HomeAssistantError("FHEM device is unavailable")
        if operation == "set_attribute":
            if device not in self.current_permissions[CONF_EDIT_ATTRIBUTES]:
                raise HomeAssistantError("FHEM attribute changes are not allowed")
        else:
            action = fields.get("action", "")
            command = {"turn_on": "on", "turn_off": "off"}.get(action, action)
            if reason := self.command_blocked(device, "set", command):
                raise HomeAssistantError(f"FHEM command blocked: {reason}")
        return await self._command(device, operation, **fields)

    async def _command(self, device, operation, **fields):
        try:
            return await self.client.request(operation, device=device, **fields)
        except BridgeError as err:
            if str(err) == "connection_closed":
                raise HomeAssistantError("FHEM command outcome is unknown") from err
            raise HomeAssistantError(err.detail or f"FHEM command failed ({err})") from err
        except (OSError, TimeoutError) as err:
            raise HomeAssistantError("FHEM command outcome is unknown") from err

    @property
    def enhanced(self):
        return self.client is not None and "device_controls" in self.client.capabilities

    @property
    def current_permissions(self):
        stamp = getattr(self.entry, "modified_at", None)
        if stamp != self._permission_stamp:
            options = settings(self.entry)
            self._permission_sets = {
                key: frozenset(options.get(key, ()))
                for key in (CONF_DEVICES, CONF_WRITABLE, CONF_QUERY, CONF_EDIT_ATTRIBUTES, CONF_TECHNICAL, CONF_LOGS)
            }
            self._permission_stamp = stamp
        return self._permission_sets

    def permission_flags(self, device):
        return {
            "writable": device in self.current_permissions[CONF_WRITABLE],
            "query": device in self.current_permissions[CONF_QUERY],
            "edit_attributes": device in self.current_permissions[CONF_EDIT_ATTRIBUTES],
            "technical": device in self.current_permissions[CONF_TECHNICAL],
        }

    def command_blocked(self, device, kind, command):
        current = self.current_permissions
        if device not in current.get(CONF_DEVICES, ()):
            return "device_unavailable"
        permission = CONF_QUERY if kind == "get" else CONF_WRITABLE
        if device not in current.get(permission, ()):
            return "get_not_allowed" if kind == "get" else "set_not_allowed"
        if technical(self.profiles[device], command) and device not in current.get(CONF_TECHNICAL, ()):
            return "technical_not_allowed"
        return None

    async def execute(self, device, kind, command, arguments, *, inputs=None, fallback_fields=None):
        if device not in self.active:
            raise HomeAssistantError("FHEM device is unavailable")
        if reason := self.command_blocked(device, kind, command):
            raise HomeAssistantError(f"FHEM command blocked: {reason}. Open this device's options.")
        profile = self.profiles[device]
        metadata = {}
        if inputs is not None:
            if arguments:
                raise HomeAssistantError("Use either inputs or arguments")
            try:
                catalog = await self.command_catalog(device, profile, kind)
                if command not in catalog:
                    raise HomeAssistantError("FHEM no longer advertises this command")
                description = catalog[command]
                fields = description["fields"] if description["fields"] is not None else fallback_fields
                arguments = serialize_inputs(fields, inputs)
                metadata["expected_spec"] = description["spec"]
            except CONNECTION_ERRORS as err:
                raise HomeAssistantError(f"Could not prepare FHEM command: {err}") from err
        if not self.enhanced:
            if kind != "set":
                raise HomeAssistantError("Update 98_HABridge.pm for Get commands")
            alias = {"on": "turn_on", "off": "turn_off"}.get(command, command)
            return await self.write(device, "invoke", action=alias, args={"values": arguments})
        return await self._command(device, "execute", kind=kind, command=command, arguments=arguments, **metadata)

    async def edit_attribute(self, device, attribute, value=None, remove=False):
        if not self.enhanced or device not in self.current_permissions[CONF_EDIT_ATTRIBUTES] or device not in self.active:
            raise HomeAssistantError("Attribute changes are not enabled for this FHEM device")
        await self._command(device, "edit_attribute", attribute=attribute, value=value, remove=remove)
        self.controls_cache.pop(device, None)
        self.invalidate_catalog(device)

    async def inventory(self):
        """Share the import catalog until its own revision changes."""
        async with self.inventory_lock:
            if self.inventory_cache is not None:
                return self.inventory_cache
            epoch = self.inventory_epoch
            catalog = await self.client.catalog()
            if epoch == self.inventory_epoch:
                self.inventory_cache = catalog
            return catalog

    def invalidate_catalog(self, device=None):
        if device is None:
            self.catalog_epoch += 1
            self.device_catalog_epochs.clear()
            self.catalog_cache.clear()
        else:
            self.device_catalog_epochs[device] = self.device_catalog_epochs.get(device, 0) + 1
            for kind in ("set", "get", "attr", "ui"):
                self.catalog_cache.pop((device, kind), None)

    async def catalog_section(self, device, kind):
        """Coalesce reads of each section and keep a bounded cache of raw metadata."""
        key = device, kind
        async with self.catalog_locks[hash(key) % len(self.catalog_locks)]:
            cached = self.catalog_cache.get(key)
            if cached and monotonic() - cached[0] < 12:
                return cached[1]
            for attempt in range(2):
                epoch = self.catalog_epoch, self.device_catalog_epochs.get(device)
                try:
                    if not self.connected and "paced_requests" not in self.client.capabilities and kind != "ui":
                        async with self.legacy_startup_catalog_lock:
                            result = await self._read_catalog_section(device, kind)
                            await asyncio.sleep(0.01)
                    else:
                        result = await self._read_catalog_section(device, kind)
                    break
                except BridgeError as err:
                    if str(err) != "catalog_changed" or attempt:
                        raise
            size = len(json.dumps(result, ensure_ascii=True))
            if epoch == (self.catalog_epoch, self.device_catalog_epochs.get(device)) and size <= 64 * 1024:
                self.catalog_cache.pop(key, None)
                if len(self.catalog_cache) >= 96:
                    self.catalog_cache.pop(next(iter(self.catalog_cache)))
                self.catalog_cache[key] = monotonic(), result
            return result

    async def _read_catalog_section(self, device, kind):
        response = await self.client.request("device_controls", device=device, section=kind, offset=0)
        if kind == "ui":
            return response["ui"]
        parts = [response["value"]]
        revision = response["revision"]
        while (offset := response["next_offset"]) is not None:
            response = await self.client.request(
                "device_controls", device=device, section=kind, offset=offset, revision=revision,
                **({"snapshot": response["snapshot"]} if "snapshot" in response else {}),
            )
            parts.append(response["value"])
        return "".join(parts)

    async def command_catalog(self, device, profile, kind, ui=None):
        if self.enhanced:
            raw = parse_specs(await self.catalog_section(device, kind))
            if ui is None:
                ui = await self.catalog_section(device, "ui")
        elif kind == "set":
            raw = {{"turn_on": "on", "turn_off": "off"}.get(key, key): "" if spec else "noArg"
                   for key, spec in profile["actions"].items()}
        else:
            raw = {}
        overrides = parse_specs((ui or {}).get("widgetOverride") or "")
        return {
            name: {**command_description(profile, kind, name, spec, overrides.get(name)),
                   "technical": technical(profile, name)}
            for name, spec in raw.items() if not name.startswith("-")
        }

    async def controls(self, device, refresh=False):
        if device not in self.active:
            raise HomeAssistantError("FHEM device is unavailable")
        async with self.controls_locks[device]:
            if refresh:
                self.invalidate_catalog(device)
                names = self.publications.subscription(device, self.profiles[device])
                try:
                    for batch in batched(names, 16):
                        response = await self.client.request("read", device=device, readings=list(batch))
                        for item in response["items"]:
                            self._record(item)
                except CONNECTION_ERRORS as err:
                    raise HomeAssistantError("Could not refresh FHEM readings") from err
                self._notify_source(device)
            cached = self.controls_cache.get(device)
            if not refresh and cached and monotonic() - cached[0] < 45:
                return {**cached[1], **self.permission_flags(device)}
            try:
                result = await self._controls(device)
            except BridgeError as err:
                if str(err) != "catalog_changed":
                    raise HomeAssistantError(f"Could not read FHEM device ({err})") from err
                try:
                    result = await self._controls(device)
                except CONNECTION_ERRORS as retry:
                    raise HomeAssistantError("FHEM device changed while reading its controls") from retry
            except CONNECTION_ERRORS as err:
                raise HomeAssistantError("Could not read FHEM device") from err
            size = len(json.dumps(result, ensure_ascii=True))
            if size <= 256 * 1024:
                self.controls_cache.pop(device, None)
                while self.controls_cache and (
                    len(self.controls_cache) >= 48
                    or size + sum(item[2] for item in self.controls_cache.values()) > 2 * 1024 * 1024
                ):
                    del self.controls_cache[next(iter(self.controls_cache))]
                self.controls_cache[device] = (monotonic(), result, size)
            return result

    async def _controls(self, device):
        profile = await self.client.request("describe", device=device, commands=True)
        ui = await self.catalog_section(device, "ui") if self.enhanced else {}
        commands = {kind: await self.command_catalog(device, profile, kind, ui) for kind in ("set", "get")}
        attrs = parse_specs(await self.catalog_section(device, "attr")) if self.enhanced else {}
        values = {} if self.supports_attribute_editor else (await self.attributes(device, profile))["attributes"]
        attrs.update({name: "" for name in values.keys() - attrs.keys()})
        self.profiles[device]["readings"] = profile["readings"]
        overrides = parse_specs(ui.get("widgetOverride") or "")
        favorites = (ui.get("webCmd") or "up:down:on:off:desired-temp:dim:pct:on-for-timer:off-for-timer").split(":")
        return {
            "name": profile["attributes"].get("alias") or profile["name"],
            "type": profile["type"], "model": profile["attributes"].get("model"),
            "enhanced": self.enhanced, **self.permission_flags(device), "attributes": values,
            "favorites": [item for item in favorites if item in commands["set"]],
            "sections": {
                **{kind: list(catalog.values()) for kind, catalog in commands.items()},
                "attr": [{"name": name, "spec": spec,
                          "fields": fields_for(profile, "attr", name, overrides.get(name, spec)) or
                          [{"type": "text", "multiline": True, "optional": True}]}
                         for name, spec in attrs.items()],
            },
        }

    @property
    def supports_attribute_editor(self):
        return self.client is not None and "attribute_editor" in self.client.capabilities

    async def attribute_overview(self, device):
        if not self.supports_attribute_editor:
            return {"supported": False}
        if device not in self.active:
            raise HomeAssistantError("FHEM device is unavailable")
        items = []
        fields = {}
        while True:
            reply = await self.client.request("attribute_list", device=device, **fields)
            items.extend(reply["items"])
            if reply["next_offset"] is None:
                break
            fields = {"offset": reply["next_offset"], "revision": reply["revision"]}
        raw = parse_specs(await self.catalog_section(device, "attr"))
        overrides = parse_specs((await self.catalog_section(device, "ui")).get("widgetOverride") or "")
        profile = self.profiles[device]
        return {"supported": True, "items": items, "writable": device in self.current_permissions[CONF_EDIT_ATTRIBUTES],
                "catalog": {name: fields_for(profile, "attr", name, overrides.get(name, spec))
                            for name, spec in raw.items()}}

    async def update_attribute(self, device, attribute, expected, value=None, remove=False):
        if (not self.supports_attribute_editor or device not in self.active
                or device not in self.current_permissions[CONF_EDIT_ATTRIBUTES]):
            raise HomeAssistantError("Attribute changes are not enabled for this FHEM device")
        if not remove and value is None:
            raise HomeAssistantError("Enter an attribute value")
        async with self.attribute_upload_lock:
            if remove:
                reply = await self._command(device, "edit_attribute", attribute=attribute, expected=expected, remove=True)
            else:
                data = value.replace("\r", "").encode("utf-8")
                opened = await self._command(device, "attribute_begin", attribute=attribute, expected=expected)
                upload = opened["upload"]
                try:
                    # Keep up to four small requests in flight. The server verifies the byte offsets.
                    for start in range(0, len(data), 4 * 6144):
                        chunks = range(start, min(start + 4 * 6144, len(data)), 6144)
                        replies = await asyncio.gather(*(self._command(
                            device, "attribute_chunk", upload=upload, offset=offset,
                            data=base64.b64encode(data[offset:offset + 6144]).decode("ascii"),
                        ) for offset in chunks), return_exceptions=True)
                        for item in replies:
                            if isinstance(item, BaseException):
                                raise item
                    reply = await self._command(device, "attribute_finish", upload=upload, size=len(data))
                except (ConnectionError, HomeAssistantError, BridgeError, asyncio.CancelledError):
                    with suppress(Exception):
                        await self._command(device, "attribute_abort", upload=upload)
                    raise
            self.controls_cache.pop(device, None)
            self.invalidate_catalog(device)
            return reply

    async def configuration_status(self, details=False, save=False):
        if self.client is None or "config_save" not in self.client.capabilities:
            return {"supported": False}
        async with self.configuration_lock:
            status = await self.client.request("config_save" if save else "config_status", details=details)
            self.update_config_status(status)
        return {"supported": True, **status}

    def update_config_status(self, status):
        state = {key: status.get(key) for key in ("dirty", "can_save", "save_error")}
        name = self.entry.title
        endpoint = f"{self.entry.data.get('host', '?')}:{self.entry.data.get('port', 19091)}"
        context = (name, endpoint)
        if state == self.config_status and context == self.config_notification_context:
            return
        self.config_status = state
        self.config_notification_context = context
        identity = f"fhem_bridge_config_{self.entry.entry_id}"
        if state["dirty"] or state["save_error"]:
            url = f"/{PANEL_PATH}?bridge={quote(self.entry.entry_id)}&config=1"
            message = ("FHEM meldet einen Fehler beim Speichern der Konfiguration." if state["save_error"]
                       else "In FHEM gibt es ungespeicherte Änderungen.")
            persistent_notification.async_create(
                self.hass, f"FHEM-Instanz: {endpoint}\n\n{message}\n\n[Konfiguration dieser Bridge öffnen]({url})",
                title=f"FHEM-Konfiguration · {name}", notification_id=identity,
            )
        else:
            persistent_notification.async_dismiss(self.hass, identity)

    async def attributes(self, device, profile=None, *, attribute=None):
        """Fetch every defined attribute on demand, outside entity state."""
        if device not in self.active:
            raise HomeAssistantError("FHEM device is unavailable")
        return await self._read_attributes(device, profile, attribute=attribute)

    async def _read_attributes(self, device, profile, *, attribute):
        try:
            if profile is None:
                profile = await self.client.request("describe", device=device)
            result = {}
            tag = None
            names = profile["attribute_names"]
            if attribute is not None and attribute not in names:
                return {"value": None, "tag": "missing"}
            for name in names if attribute is None else (attribute,):
                parts = []
                fields = {"revision": profile["revision"], **({"tag": True} if attribute is not None else {})}
                while True:
                    reply = await self.client.request("attributes", device=device, attribute=name, **fields)
                    tag = reply.get("tag", tag)
                    parts.append(reply["value"])
                    offset = reply["next_offset"]
                    if offset is None:
                        break
                    fields = {"offset": offset, "revision": reply["revision"]}
                if reply["encoding"] == "base64":
                    raw = b"".join(base64.b64decode(part) for part in parts)
                    try:
                        result[name] = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        result[name] = {"encoding": "base64", "value": base64.b64encode(raw).decode()}
                else:
                    result[name] = "".join(parts)
            if attribute is not None:
                return {"value": result[attribute], "tag": tag}
            return {"attributes": result, "editable_attributes": sorted(result) if device in (self.edit_attributes if self.enhanced else self.writable) else []}
        except CONNECTION_ERRORS as err:
            raise HomeAssistantError(f"Could not read FHEM attributes ({err})") from err
