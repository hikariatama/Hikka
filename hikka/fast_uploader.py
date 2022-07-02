import io
from typing import BinaryIO, Optional, Union
from telethon.tl.types import TypeInputFile, Message
from telethon import TelegramClient


async def download_file(
    location: Message = None,  # type: ignore
    progress_callback=None,
    message_object=None,
    _client: TelegramClient = None,
) -> BinaryIO:
    """
    ⚠️ WARNING! Deprecated method!
    Will be removed in next major update
    :param location: From where to download file? If it's not possible to do via fast_downloader
                     it will be downloaded through classic tools instead
    :param progress_callback: Redundant
    :param message_object: Redundant
    """
    if getattr(location, "document", None):
        location = location.document

    return io.BytesIO(await _client.download_file(location, bytes))


async def upload_file(
    file: Union[BinaryIO, bytes] = None,
    progress_callback=None,
    filename: Optional[str] = None,
    message_object=None,
    _client: TelegramClient = None,
) -> TypeInputFile:
    """
    ⚠️ WARNING! Deprecated method!
    Will be removed in next major update
    :param file: Can be a BinaryIO (file handler, `io` handler) or a bytes
                 If bytes were passed, they will be converted to BytesIO
                 If passed object has a filename, it can be parsed instead of `filename`
    :param progress_callback: Redundant
    :param filename: Filename to be used for uploading
    :param message_object: Redundant
    """
    if not hasattr(file, "read"):
        file = io.BytesIO(file)

    return await _client.upload_file(file, file_name=filename)
