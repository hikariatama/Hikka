# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import copy
import datetime
import functools
import logging
import re
import typing

import hikkatl
from hikkapyro import Client as PyroClient
from hikkapyro import errors as pyro_errors
from hikkapyro import raw

from .. import utils
from ..tl_cache import CustomTelegramClient
from ..version import __version__

PROXY = {
    pyro_object: hikkatl.tl.alltlobjects.tlobjects[constructor_id]
    for constructor_id, pyro_object in raw.all.objects.items()
    if constructor_id in hikkatl.tl.alltlobjects.tlobjects
}

REVERSED_PROXY = {
    **{tl_object: pyro_object for pyro_object, tl_object in PROXY.items()},
    **{
        tl_object: raw.all.objects[tl_object.CONSTRUCTOR_ID]
        for _, tl_object in utils.iter_attrs(hikkatl.tl.custom)
        if getattr(tl_object, "CONSTRUCTOR_ID", None) in raw.all.objects
    },
}

PYRO_ERRORS = {
    cls.ID: cls
    for _, cls in utils.iter_attrs(pyro_errors)
    if hasattr(cls, "ID") and issubclass(cls, pyro_errors.RPCError)
}


logger = logging.getLogger(__name__)


class PyroProxyClient(PyroClient):
    """
    Pyrogram client that redirects all requests to telethon's handler
    :param tl_client: telethon client
    :type tl_client: CustomTelegramClient
    """

    def __init__(self, tl_client: CustomTelegramClient):
        self.tl_client = tl_client
        super().__init__(
            name="proxied_pyrogram_client",
            api_id=tl_client.api_id,
            api_hash=tl_client.api_hash,
            app_version=".".join(map(str, __version__)) + " x64",
            lang_code="en",
            in_memory=True,
            phone_number=tl_client.hikka_me.phone,
        )

        # We need to set this to True so pyro thinks he's connected
        # even tho it's not. We don't need to connect to Telegram as
        # we redirect all requests to telethon's handler
        self.is_connected = True
        self.conn = tl_client.session._conn

    async def start(self):
        """
        Starts the client
        :return: None
        """
        self.me = await self.get_me()
        self.tl_client.raw_updates_processor = self._on_event

    def _on_event(
        self,
        event: typing.Union[
            hikkatl.tl.types.Updates,
            hikkatl.tl.types.UpdatesCombined,
            hikkatl.tl.types.UpdateShort,
        ],
    ):
        asyncio.ensure_future(self.handle_updates(self._tl2pyro(event)))

    async def invoke(
        self,
        query: raw.core.TLObject,
        *args,
        **kwargs,
    ) -> typing.Union[typing.List[raw.core.TLObject], raw.core.TLObject]:
        """
        Invokes a Pyrogram request through telethon
        :param query: Pyrogram request
        :return: Pyrogram response
        :raises RPCError: if Telegram returns an error
        :rtype: typing.Union[typing.List[raw.core.TLObject], raw.core.TLObject]
        """
        logger.debug(
            "Running Pyrogram's invoke of %s with Telethon proxying",
            query.__class__.__name__,
        )
        if self.tl_client.session.takeout_id:
            query = raw.functions.InvokeWithTakeout(
                takeout_id=self.tl_client.session.takeout_id,
                query=query,
            )

        try:
            r = await self.tl_client(self._pyro2tl(query))
        except hikkatl.errors.rpcerrorlist.RPCError as e:
            raise self._tl_error2pyro(e)

        return self._tl2pyro(r)

    @staticmethod
    def _tl_error2pyro(
        error: hikkatl.errors.rpcerrorlist.RPCError,
    ) -> pyro_errors.RPCError:
        rpc = (
            re.sub(r"([A-Z])", r"_\1", error.__class__.__name__)
            .upper()
            .strip("_")
            .rsplit("ERROR", maxsplit=1)[0]
            .strip("_")
        )
        if rpc in PYRO_ERRORS:
            return PYRO_ERRORS[rpc]()

        return PYRO_ERRORS.get(
            f"{rpc}_X",
            PYRO_ERRORS.get(
                f"{rpc}_0",
                pyro_errors.RPCError,
            ),
        )()

    def _pyro2tl(self, pyro_obj: raw.core.TLObject) -> hikkatl.tl.TLObject:
        """
        Recursively converts Pyrogram TLObjects to Telethon TLObjects (methods,
        types and everything else, which is in tl schema)
        :param pyro_obj: Pyrogram TLObject
        :return: Telethon TLObject
        :raises TypeError: if it's not possible to convert Pyrogram TLObject to
        Telethon TLObject
        """
        pyro_obj = self._convert(pyro_obj)
        if isinstance(pyro_obj, list):
            return [self._pyro2tl(i) for i in pyro_obj]

        if isinstance(pyro_obj, dict):
            return {k: self._pyro2tl(v) for k, v in pyro_obj.items()}

        if not isinstance(pyro_obj, raw.core.TLObject):
            return pyro_obj

        if type(pyro_obj) not in PROXY:
            raise TypeError(
                f"Cannot convert Pyrogram's {type(pyro_obj)} to Telethon TLObject"
            )

        return PROXY[type(pyro_obj)](
            **{
                attr: self._pyro2tl(getattr(pyro_obj, attr))
                for attr in pyro_obj.__slots__
            }
        )

    def _tl2pyro(self, tl_obj: hikkatl.tl.TLObject) -> raw.core.TLObject:
        """
        Recursively converts Telethon TLObjects to Pyrogram TLObjects (methods,
        types and everything else, which is in tl schema)
        :param tl_obj: Telethon TLObject
        :return: Pyrogram TLObject
        :raises TypeError: if it's not possible to convert Telethon TLObject to
        Pyrogram TLObject
        """
        tl_obj = self._convert(tl_obj)
        if (
            isinstance(getattr(tl_obj, "from_id", None), int)
            and tl_obj.from_id
            and hasattr(tl_obj, "sender_id")
        ):
            tl_obj = copy.copy(tl_obj)
            tl_obj.from_id = hikkatl.tl.types.PeerUser(tl_obj.sender_id)

        if isinstance(tl_obj, list):
            return [self._tl2pyro(i) for i in tl_obj]

        if isinstance(tl_obj, dict):
            return {k: self._tl2pyro(v) for k, v in tl_obj.items()}

        if isinstance(tl_obj, int) and str(tl_obj).startswith("-100"):
            return int(str(tl_obj)[4:])

        if not isinstance(tl_obj, hikkatl.tl.TLObject):
            return tl_obj

        if type(tl_obj) not in REVERSED_PROXY:
            raise TypeError(
                f"Cannot convert Telethon's {type(tl_obj)} to Pyrogram TLObject"
            )

        hints = typing.get_type_hints(REVERSED_PROXY[type(tl_obj)].__init__) or {}

        return REVERSED_PROXY[type(tl_obj)](
            **{
                attr: self._convert_types(
                    hints.get(attr),
                    self._tl2pyro(getattr(tl_obj, attr)),
                )
                for attr in REVERSED_PROXY[type(tl_obj)].__slots__
            }
        )

    @staticmethod
    def _get_origin(hint: typing.Any) -> typing.Any:
        try:
            return typing.get_origin(hint)
        except Exception:
            return None

    def _convert_types(self, hint: typing.Any, value: typing.Any) -> typing.Any:
        if not value and (
            self._get_origin(hint) in {typing.List, list}
            or (
                self._get_origin(hint) is typing.Union
                and any(
                    self._get_origin(i) in {typing.List, list} for i in hint.__args__
                )
            )
        ):
            return []

        return value

    def _convert(self, obj: typing.Any) -> typing.Any:
        if isinstance(obj, datetime.datetime):
            return int(obj.timestamp())

        return obj

    async def resolve_peer(
        self,
        *args,
        **kwargs,
    ) -> "typing.Union[hikkapyro.raw.types.PeerChat, hikkapyro.raw.types.PeerChannel, hikkapyro.raw.types.PeerUser]":  # type: ignore  # noqa: E501, F821
        """
        Resolve a peer (user, chat or channel) from the given input.
        :param args: Arguments to pass to the Telethon client's
        :return: The resolved peer
        :rtype: typing.Union[hikkapyro.raw.types.PeerChat, hikkapyro.raw.types.PeerChannel, hikkapyro.raw.types.PeerUser]
        """
        return self._tl2pyro(await self.tl_client.get_entity(*args, **kwargs))

    async def fetch_peers(
        self,
        peers: typing.List[
            typing.Union[raw.types.User, raw.types.Chat, raw.types.Channel]
        ],
    ) -> bool:
        """
        Fetches the given peers (users, chats or channels) from the server.
        :param peers: List of peers to fetch
        :return: True if the peers were fetched successfully
        :rtype: bool
        """
        return any(getattr(peer, "min", False) for peer in peers)

    @property
    def iter_chat_members(self):
        """Alias for :obj:`get_chat_members <pyrogram.Client.get_chat_members>`"""
        return self.get_chat_members

    @property
    def iter_dialogs(self):
        """Alias for :obj:`get_dialogs <pyrogram.Client.get_dialogs>`"""
        return self.get_dialogs

    @property
    def iter_history(self):
        """Alias for :obj:`get_history <pyrogram.Client.get_history>`"""
        return self.get_chat_history

    @property
    def iter_profile_photos(self):
        """Alias for :obj:`get_profile_photos <pyrogram.Client.get_profile_photos>`"""
        return self.get_chat_photos

    async def save_file(
        self,
        path: typing.Union[str, typing.BinaryIO],
        file_id: int = None,
        file_part: int = 0,
        progress: typing.Callable = None,
        progress_args: tuple = (),
    ) -> raw.types.InputFileLocation:
        """
        Save a file to the given path.
        :param path: The path to save the file to
        :param file_id: The file ID to save
        :param file_part: The file part to save
        :param progress: A callback function to track the progress
        :param progress_args: Arguments to pass to the progress callback
        :return: The file location
        :rtype: :obj:`InputFileLocation <pyrogram.api.types.InputFileLocation>`
        """
        return self._tl2pyro(
            await self.tl_client.upload_file(
                path,
                part_size_kb=file_part,
                progress_callback=(
                    functools.partial(progress, *progress_args)
                    if progress and callable(progress)
                    else None
                ),
            )
        )
