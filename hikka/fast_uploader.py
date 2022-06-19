# https://gist.github.com/painor/7e74de80ae0c819d3e9abcf9989a8dd6
# copied from https://github.com/tulir/mautrix-telegram/blob/master/mautrix_telegram/util/parallel_file_transfer.py
# Copyright (C) 2021 Tulir Asokan

import asyncio
import contextlib
import hashlib
import inspect
import io
import logging
import math
import os
from collections import defaultdict
from typing import (
    AsyncGenerator,
    Awaitable,
    BinaryIO,
    DefaultDict,
    List,
    Optional,
    Tuple,
    Union,
)

import time

from telethon import TelegramClient, helpers, utils
from telethon.crypto import AuthKey
from telethon.network import MTProtoSender
from telethon.tl.alltlobjects import LAYER
from telethon.tl.functions import InvokeWithLayerRequest
from telethon.tl.functions.auth import (
    ExportAuthorizationRequest,
    ImportAuthorizationRequest,
)
from telethon.tl.functions.upload import (
    GetFileRequest,
    SaveBigFilePartRequest,
    SaveFilePartRequest,
)
from telethon.tl.types import (
    Document,
    InputDocumentFileLocation,
    InputFile,
    InputFileBig,
    InputFileLocation,
    InputPeerPhotoFileLocation,
    InputPhotoFileLocation,
    TypeInputFile,
    Message,
)

from .inline.types import InlineMessage
from .utils import answer

log: logging.Logger = logging.getLogger("telethon")

TypeLocation = Union[
    Document,
    InputDocumentFileLocation,
    InputPeerPhotoFileLocation,
    InputFileLocation,
    InputPhotoFileLocation,
]


class DownloadSender:
    client: TelegramClient
    sender: MTProtoSender
    request: GetFileRequest
    remaining: int
    stride: int

    def __init__(
        self,
        client: TelegramClient,
        sender: MTProtoSender,
        file: TypeLocation,
        offset: int,
        limit: int,
        stride: int,
        count: int,
    ) -> None:
        self.sender = sender
        self.client = client
        self.request = GetFileRequest(file, offset=offset, limit=limit)
        self.stride = stride
        self.remaining = count

    async def next(self) -> Optional[bytes]:
        if not self.remaining:
            return None

        result = await self.client._call(self.sender, self.request)
        self.remaining -= 1
        self.request.offset += self.stride
        return result.bytes

    def disconnect(self) -> Awaitable[None]:
        return self.sender.disconnect()


class UploadSender:
    client: TelegramClient
    sender: MTProtoSender
    request: Union[SaveFilePartRequest, SaveBigFilePartRequest]
    part_count: int
    stride: int
    previous: Optional[asyncio.Task]
    loop: asyncio.AbstractEventLoop

    def __init__(
        self,
        client: TelegramClient,
        sender: MTProtoSender,
        file_id: int,
        part_count: int,
        big: bool,
        index: int,
        stride: int,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.client = client
        self.sender = sender
        self.part_count = part_count

        if big:
            self.request = SaveBigFilePartRequest(file_id, index, part_count, b"")
        else:
            self.request = SaveFilePartRequest(file_id, index, b"")

        self.stride = stride
        self.previous = None
        self.loop = loop

    async def next(self, data: bytes) -> None:
        if self.previous:
            await self.previous

        self.previous = self.loop.create_task(self._next(data))

    async def _next(self, data: bytes) -> None:
        self.request.bytes = data

        log.debug(
            f"Sending file part {self.request.file_part}/{self.part_count}"
            f" with {len(data)} bytes"
        )

        await self.client._call(self.sender, self.request)
        self.request.file_part += self.stride

    async def disconnect(self) -> None:
        if self.previous:
            await self.previous

        return await self.sender.disconnect()


class ParallelTransferrer:
    client: TelegramClient
    loop: asyncio.AbstractEventLoop
    dc_id: int
    senders: Optional[List[Union[DownloadSender, UploadSender]]]
    auth_key: AuthKey
    upload_ticker: int

    def __init__(self, client: TelegramClient, dc_id: Optional[int] = None) -> None:
        self.client = client
        self.loop = self.client.loop
        self.dc_id = dc_id or self.client.session.dc_id
        self.auth_key = (
            None
            if dc_id and self.client.session.dc_id != dc_id
            else self.client.session.auth_key
        )
        self.senders = None
        self.upload_ticker = 0

    async def _cleanup(self) -> None:
        await asyncio.gather(*[sender.disconnect() for sender in self.senders])
        self.senders = None

    @staticmethod
    def _get_connection_count(
        file_size: int,
        max_count: int = 20,
        full_size: int = 100 * 1024 * 1024,
    ) -> int:
        if file_size > full_size:
            return max_count

        return math.ceil((file_size / full_size) * max_count)

    async def _init_download(
        self,
        connections: int,
        file: TypeLocation,
        part_count: int,
        part_size: int,
    ) -> None:
        minimum, remainder = divmod(part_count, connections)

        def get_part_count() -> int:
            nonlocal remainder
            if remainder > 0:
                remainder -= 1
                return minimum + 1

            return minimum

        # The first cross-DC sender will export+import the authorization, so we always create it
        # before creating any other senders.
        self.senders = [
            await self._create_download_sender(
                file,
                0,
                part_size,
                connections * part_size,
                get_part_count(),
            ),
            *await asyncio.gather(
                *[
                    self._create_download_sender(
                        file,
                        i,
                        part_size,
                        connections * part_size,
                        get_part_count(),
                    )
                    for i in range(1, connections)
                ]
            ),
        ]

    async def _create_download_sender(
        self,
        file: TypeLocation,
        index: int,
        part_size: int,
        stride: int,
        part_count: int,
    ) -> DownloadSender:
        return DownloadSender(
            self.client,
            await self._create_sender(),
            file,
            index * part_size,
            part_size,
            stride,
            part_count,
        )

    async def _init_upload(
        self,
        connections: int,
        file_id: int,
        part_count: int,
        big: bool,
    ) -> None:
        self.senders = [
            await self._create_upload_sender(file_id, part_count, big, 0, connections),
            *await asyncio.gather(
                *[
                    self._create_upload_sender(file_id, part_count, big, i, connections)
                    for i in range(1, connections)
                ]
            ),
        ]

    async def _create_upload_sender(
        self,
        file_id: int,
        part_count: int,
        big: bool,
        index: int,
        stride: int,
    ) -> UploadSender:
        return UploadSender(
            self.client,
            await self._create_sender(),
            file_id,
            part_count,
            big,
            index,
            stride,
            loop=self.loop,
        )

    async def _create_sender(self) -> MTProtoSender:
        dc = await self.client._get_dc(self.dc_id)
        sender = MTProtoSender(self.auth_key, loggers=self.client._log)
        await sender.connect(
            self.client._connection(
                dc.ip_address,
                dc.port,
                dc.id,
                loggers=self.client._log,
                proxy=self.client._proxy,
            )
        )
        if not self.auth_key:
            log.debug(f"Exporting auth to DC {self.dc_id}")
            auth = await self.client(ExportAuthorizationRequest(self.dc_id))
            self.client._init_request.query = ImportAuthorizationRequest(
                id=auth.id,
                bytes=auth.bytes,
            )
            req = InvokeWithLayerRequest(LAYER, self.client._init_request)
            await sender.send(req)
            self.auth_key = sender.auth_key
        return sender

    async def init_upload(
        self,
        file_id: int,
        file_size: int,
        part_size_kb: Optional[float] = None,
        connection_count: Optional[int] = None,
    ) -> Tuple[int, int, bool]:
        connection_count = connection_count or self._get_connection_count(file_size)
        part_size = (part_size_kb or utils.get_appropriated_part_size(file_size)) * 1024
        part_count = (file_size + part_size - 1) // part_size
        is_large = file_size > 10 * 1024 * 1024
        await self._init_upload(connection_count, file_id, part_count, is_large)
        return part_size, part_count, is_large

    async def upload(self, part: bytes) -> None:
        await self.senders[self.upload_ticker].next(part)
        self.upload_ticker = (self.upload_ticker + 1) % len(self.senders)

    async def finish_upload(self) -> None:
        await self._cleanup()

    async def download(
        self,
        file: TypeLocation,
        file_size: int,
        part_size_kb: Optional[float] = None,
        connection_count: Optional[int] = None,
    ) -> AsyncGenerator[bytes, None]:
        connection_count = connection_count or self._get_connection_count(file_size)
        part_size = (part_size_kb or utils.get_appropriated_part_size(file_size)) * 1024
        part_count = math.ceil(file_size / part_size)
        log.debug(
            "Starting parallel download: "
            f"{connection_count} {part_size} {part_count} {file!s}"
        )

        await self._init_download(connection_count, file, part_count, part_size)

        part = 0

        while part < part_count:
            tasks = []

            for sender in self.senders:
                tasks.append(self.loop.create_task(sender.next()))

            for task in tasks:
                data = await task

                if not data:
                    break

                yield data
                part += 1
                log.debug(f"Part {part} downloaded")

        log.debug("Parallel download finished, cleaning up connections")
        await self._cleanup()


parallel_transfer_locks: DefaultDict[int, asyncio.Lock] = defaultdict(
    lambda: asyncio.Lock()
)


def stream_file(file_to_stream: BinaryIO, chunk_size=1024):
    while True:
        data_read = file_to_stream.read(chunk_size)
        if not data_read:
            break

        yield data_read


async def _internal_transfer_to_telegram(
    client: TelegramClient,
    response: BinaryIO,
    progress_callback: callable,
    filename: Optional[str] = None,
) -> Tuple[TypeInputFile, int]:
    file_id = helpers.generate_random_long()
    file_size = (
        response.getbuffer().nbytes
        if isinstance(response, io.BytesIO)
        else os.path.getsize(response.name)
    )

    if not filename:
        if isinstance(response, io.BytesIO) and getattr(response, "name", False):
            filename = response.name
        else:
            filename = "unnamed"

    hash_md5 = hashlib.md5()
    uploader = ParallelTransferrer(client)
    part_size, part_count, is_large = await uploader.init_upload(file_id, file_size)
    buffer = bytearray()
    for data in stream_file(response):
        if progress_callback:
            r = progress_callback(response.tell(), file_size)
            if inspect.isawaitable(r):
                await r

        if not is_large:
            hash_md5.update(data)

        if len(buffer) == 0 and len(data) == part_size:
            await uploader.upload(data)
            continue

        new_len = len(buffer) + len(data)

        if new_len >= part_size:
            cutoff = part_size - len(buffer)
            buffer.extend(data[:cutoff])
            await uploader.upload(bytes(buffer))
            buffer.clear()
            buffer.extend(data[cutoff:])
        else:
            buffer.extend(data)

    if len(buffer) > 0:
        await uploader.upload(bytes(buffer))

    await uploader.finish_upload()

    return (
        (InputFileBig(file_id, part_count, filename), file_size)
        if is_large
        else (InputFile(file_id, part_count, filename, hash_md5.hexdigest()), file_size)
    )


def _progressbar(progress: int) -> str:
    filled = int(10 * progress // 100)
    return f'{"▰" * filled}{"▱" * (10 - filled)}'


async def _download_file(
    location: Union[Message, TypeLocation] = None,
    progress_callback: callable = None,
    message_object: Optional[Union[Message, InlineMessage]] = None,
    _client: TelegramClient = None,
) -> BinaryIO:
    if not hasattr(location, "size") or location.size <= 1024 * 1024:
        return io.BytesIO(await _client.download_file(location, bytes))

    size = location.size
    dc_id, location = utils.get_input_location(location)

    # We lock the transfers because telegram has connection count limits
    downloader = ParallelTransferrer(_client, dc_id)
    downloaded = downloader.download(location, size)

    ratelimiter = time.time() + 3

    if progress_callback is None and message_object is not None:

        async def default_progress_callback(current: int, total: int):
            nonlocal message_object, ratelimiter
            if ratelimiter > time.time():
                return

            ratelimiter = time.time() + 3

            percentage = round(current * 100 / total)
            try:
                message_object = await answer(
                    message_object,
                    (
                        "🌘 <b>Hikka is downloading a file...</b>\n"
                        f"<code>{_progressbar(percentage)} {percentage}%</code>"
                    ),
                )
            except Exception:
                pass

        progress_callback = default_progress_callback

    _out = io.BytesIO()

    async for x in downloaded:
        _out.write(x)
        if progress_callback:
            r = progress_callback(_out.tell(), size)
            if inspect.isawaitable(r):
                await r

    if message_object is not None:
        try:
            message_object = await answer(
                message_object,
                "🌘 <b>File ready, processing...</b>",
            )
        except Exception:
            pass

    return _out


async def download_file(
    location: Union[Message, TypeLocation] = None,
    progress_callback: callable = None,
    message_object: Optional[Union[Message, InlineMessage]] = None,
    _client: TelegramClient = None,
) -> BinaryIO:
    """
    Uses multi-threading to quickly download file to Telegram servers
    :param location: From where to download file? If it's not possible to do via fast_downloader
                     it will be downloaded through classic tools instead
    :param progress_callback: Must be a synchronous or asynchronous function handling callback
                              You can instead pass `message_object`, Hikka will generate handler
                              for you
    :param message_object: Must be a telethon message object or an instance, generated by callback
                           handler / form, which can be passed to `utils.answer`
    """
    if getattr(location, "document", None):
        location = location.document

    return io.BytesIO(await _client.download_file(location, bytes))

    result = None

    try:
        result = await _download_file(
            location, progress_callback, message_object, _client
        )
        assert result
    except (Exception, GeneratorExit):
        raise

    if not result:
        logging.debug(
            "Can't download through fast_uploader, using legacy one", exc_info=True
        )
        result = await _client.download_file(location, bytes)

    return result


async def upload_file(
    file: Union[BinaryIO, bytes] = None,
    progress_callback: callable = None,
    filename: Optional[str] = None,
    message_object: Optional[Union[Message, InlineMessage]] = None,
    _client: TelegramClient = None,
) -> TypeInputFile:
    """
    Uses multi-threading to quickly upload file to Telegram servers
    :param file: Can be a BinaryIO (file handler, `io` handler) or a bytes
                 If bytes were passed, they will be converted to BytesIO
                 If passed object has a filename, it can be parsed instead of `filename`
    :param progress_callback: Must be a synchronous or asynchronous function handling callback
                              You can instead pass `message_object`, Hikka will generate handler
                              for you
    :param filename: If your `file` has no attribute `name` or you want to override it, pass here
                     a valid string with filename
    :param message_object: Must be a telethon message object or an instance, generated by callback
                           handler / form, which can be passed to `utils.answer`
    """
    if not hasattr(file, "read"):
        file = io.BytesIO(file)

    return await _client.upload_file(file, file_name=filename)

    try:

        with contextlib.suppress(Exception):
            try:
                size = file.getvalue()
            except AttributeError:
                size = file.read()
                file.seek(0)

            if len(size) < 1024 * 1024:
                return await _client.upload_file(file, file_name=filename)

        ratelimiter = time.time() + 3

        if progress_callback is None and message_object is not None:

            async def default_progress_callback(current: int, total: int):
                nonlocal message_object, ratelimiter
                if ratelimiter > time.time():
                    return

                ratelimiter = time.time() + 3

                percentage = round(current * 100 / total)
                try:
                    message_object = await answer(
                        message_object,
                        (
                            "🌘 <b>Hikka is uploading a file...</b>\n"
                            f"<code>{_progressbar(percentage)} {percentage}%</code>"
                        ),
                    )
                except Exception:
                    pass

            progress_callback = default_progress_callback

        res = (
            await _internal_transfer_to_telegram(
                _client,
                file,
                progress_callback,
                filename,
            )
        )[0]

        if message_object is not None:
            try:
                message_object = await answer(
                    message_object,
                    "🌘 <b>File ready, processing...</b>",
                )
            except Exception:
                pass

        return res
    except (Exception,):
        logging.debug(
            "Can't upload through fast_uploader, using legacy one", exc_info=True
        )
        return await _client.upload_file(file, file_name=filename)
