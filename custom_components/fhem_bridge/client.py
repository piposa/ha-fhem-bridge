"""Asynchronous JSON Lines transport for HABridge."""

import asyncio
from collections import Counter
from hashlib import sha256
from hmac import compare_digest
import json
import ssl

FRAME_LIMIT = 65536
TIMEOUT = 8


class BridgeError(Exception):
    """The bridge rejected a request or became unreachable."""

    def __init__(self, code, detail=None):
        super().__init__(code)
        self.detail = detail


def _tls_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def _fingerprint(writer):
    ssl_object = writer.get_extra_info("ssl_object")
    certificate = ssl_object.getpeercert(binary_form=True) if ssl_object else None
    if not certificate:
        raise BridgeError("missing_certificate")
    return sha256(certificate).hexdigest()


async def probe_fingerprint(host, port):
    """Fetch the presented certificate without sending credentials."""
    async with asyncio.timeout(TIMEOUT):
        _, writer = await asyncio.open_connection(host, port, ssl=_tls_context())
    try:
        return _fingerprint(writer)
    finally:
        writer.close()
        try:
            async with asyncio.timeout(2):
                await writer.wait_closed()
        except (OSError, TimeoutError):
            writer.transport.abort()
        except BaseException:
            writer.transport.abort()
            raise


class BridgeClient:
    """A single TLS connection with correlated requests and push frames."""

    def __init__(self, host, port, token, fingerprint, push=None):
        self.host = host
        self.port = port
        self.token = token
        self.fingerprint = fingerprint
        self.push = push
        self.writer = None
        self.reader_task = None
        self.read_error = None
        self.pending = {}
        self.serial = 0
        self.epoch = None
        self.heartbeat = None
        self.last_request = 0
        self.frames = Counter()
        self.bytes = Counter()
        self.capabilities = frozenset()

    async def connect(self):
        """Verify TLS and negotiate the server protocol."""
        self.read_error = None
        try:
            async with asyncio.timeout(TIMEOUT):
                reader, self.writer = await asyncio.open_connection(
                    self.host, self.port, ssl=_tls_context(), limit=FRAME_LIMIT
                )
                if not compare_digest(_fingerprint(self.writer), self.fingerprint):
                    raise BridgeError("certificate_changed")
                self.reader_task = asyncio.create_task(self._read(reader, self.writer))
                hello = await self.request("hello", token=self.token, version=1, features=["reading_batches"])
            required = {"subscribe_append", "ha_selection", "attributes", "set_attribute"}
            if hello.get("version") != 1 or not required.issubset(hello.get("capabilities", [])):
                raise BridgeError("incompatible_protocol")
            if not isinstance(hello.get("server_id"), str) or not hello["server_id"]:
                raise BridgeError("invalid_server_identity")
            self.capabilities = frozenset(hello["capabilities"])
            self.epoch = hello.get("epoch")
            return hello["server_id"]
        except BaseException:
            await self.close()
            raise

    async def close(self):
        """Close the transport and fail outstanding calls."""
        heartbeat, self.heartbeat = self.heartbeat, None
        if heartbeat is not None:
            heartbeat.cancel()
        writer, self.writer = self.writer, None
        reader_task, self.reader_task = self.reader_task, None
        if writer is not None:
            writer.close()
        for future in self.pending.values():
            if not future.done():
                future.set_exception(BridgeError("connection_closed"))
        if reader_task is not None and not reader_task.done():
            reader_task.cancel()
            # Wait for the reader without consuming cancellation of the caller.
            await asyncio.wait({reader_task})
            if not reader_task.cancelled():
                reader_task.result()
        if writer is not None:
            try:
                async with asyncio.timeout(2):
                    await writer.wait_closed()
            except TimeoutError:
                writer.transport.abort()
            except OSError:
                pass

    async def keepalive(self):
        """Keep the writer responsive while independent synchronization awaits data."""
        try:
            while self.writer is not None and not self.writer.is_closing():
                await asyncio.sleep(15)
                if asyncio.get_running_loop().time() - self.last_request >= 15:
                    await self.request("ping")
        except (OSError, TimeoutError, BridgeError) as err:
            self.read_error = err
            if self.writer is not None:
                self.writer.close()

    async def request(self, operation, **fields):
        """Send one request and wait for its correlated reply."""
        if self.writer is None or self.writer.is_closing():
            raise BridgeError("connection_closed")
        self.serial += 1
        request_id = str(self.serial)
        payload = json.dumps({"op": operation, "id": request_id, **fields}).encode() + b"\n"
        if len(payload) > FRAME_LIMIT:
            raise BridgeError("frame_too_large")
        future = asyncio.get_running_loop().create_future()
        self.pending[request_id] = future
        try:
            async with asyncio.timeout(TIMEOUT):
                self.last_request = asyncio.get_running_loop().time()
                self.writer.write(payload)
                self.frames["tx:" + operation] += 1
                self.bytes["tx:" + operation] += len(payload)
                await self.writer.drain()
                reply = await future
        finally:
            self.pending.pop(request_id, None)
            if not future.done():
                future.cancel()
            elif not future.cancelled():
                future.exception()
        if not reply.get("ok"):
            error = reply.get("error", {})
            raise BridgeError(error.get("code", "fhem_error"), error.get("message"))
        return reply

    async def _read(self, reader, writer):
        try:
            while line := await reader.readline():
                if len(line) > FRAME_LIMIT or not line.endswith(b"\n"):
                    raise BridgeError("invalid_frame")
                frame = json.loads(line)
                if not isinstance(frame, dict):
                    raise BridgeError("invalid_frame")
                kind = "reply" if "id" in frame else frame.get("type")
                if not isinstance(kind, str) or kind not in {
                        "reply", "reading", "readings", "event", "snapshot", "snapshot_end", "catalog_changed",
                        "config_status", "log", "reading_gap"}:
                    kind = "unknown"
                self.frames["rx:" + kind] += 1
                self.bytes["rx:" + kind] += len(line)
                if "id" in frame:
                    future = self.pending.get(frame["id"])
                    if future is not None and not future.done():
                        future.set_result(frame)
                elif self.push is not None:
                    self.push(frame)
        except (OSError, ValueError, TypeError, KeyError, BridgeError) as err:
            if isinstance(err, (BridgeError, OSError)):
                self.read_error = err
            else:
                self.read_error = BridgeError("invalid_frame")
        finally:
            writer.close()
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(self.read_error or BridgeError("connection_closed"))

    async def descriptions(self, devices, writable=(), *, cached=None, failures=None):
        """Pace FHEM calls that enumerate commands on its main loop."""
        profiles = {}
        writable = set(writable)
        for device in devices:
            commands = device in writable
            previous = cached.get(device) if cached and "profile_cache" in self.capabilities else None
            validators = {}
            if previous and {"revision", "reading_schema", "device_instance"} <= previous.keys():
                validators = {"if_revision": previous["revision"], "reading_schema": previous["reading_schema"],
                              "device_instance": previous["device_instance"]}
            try:
                profile = await self.request("describe", device=device, commands=commands, **validators)
                if profile.get("unchanged") and previous:
                    profiles[device] = previous
                    continue
                model_reading = {"CUL_WS": "DEVTYPE", "ESA2000": "type"}.get(profile.get("type"))
                if (model_reading and not profile["attributes"].get("model") and model_reading in profile["readings"]):
                    await self._read_telegram_model(device, profile, model_reading)
            except (BridgeError, TimeoutError) as err:
                if str(err) == "not_allowed":
                    continue
                if failures is None or (isinstance(err, BridgeError) and str(err) not in {
                        "bad_request", "limit_exceeded", "catalog_changed"}):
                    raise
                failures[device] = str(err) or type(err).__name__
                continue
            profiles[device] = profile
            if commands:
                await asyncio.sleep(0.01)
        return profiles

    async def _read_telegram_model(self, device, profile, reading):
        """Read the telegram family when the module publishes one."""
        try:
            reply = await self.request("read", device=device, readings=[reading])
        except BridgeError as err:
            if str(err) != "not_allowed":
                raise
            return
        if (items := reply.get("items")) and (value := items[0].get("value")) and value.lower() != "unknown":
            profile["device_model"] = value

    async def catalog(self):
        """Fetch a consistent paginated catalog."""
        for attempt in range(3):
            items = []
            fields = {}
            try:
                while True:
                    reply = await self.request("list", **fields)
                    items.extend(reply["items"])
                    offset = reply["next_offset"]
                    if offset is None:
                        return items
                    fields = {"offset": offset, "revision": reply["revision"]}
            except BridgeError as err:
                if str(err) != "catalog_changed" or attempt == 2:
                    raise
        raise BridgeError("catalog_changed")
