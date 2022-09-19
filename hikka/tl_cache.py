#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import copy
import inspect
import time
import asyncio
import logging
import typing

from telethon import TelegramClient
from telethon.hints import EntityLike
from telethon.utils import is_list_like
from telethon.network import MTProtoSender
from telethon.tl.tlobject import TLRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChannelFull, UserFull

from .types import (
    CacheRecord,
    CacheRecordPerms,
    CacheRecordFullChannel,
    CacheRecordFullUser,
    Module,
)

logger = logging.getLogger(__name__)


def hashable(value: typing.Any) -> bool:
    """
    Determine whether `value` can be hashed.

    This is a copy of `collections.abc.Hashable` from Python 3.8.
    """

    try:
        hash(value)
    except TypeError:
        return False

    return True


class CustomTelegramClient(TelegramClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hikka_entity_cache = {}
        self._hikka_perms_cache = {}
        self._hikka_fullchannel_cache = {}
        self._hikka_fulluser_cache = {}
        self.__forbidden_constructors = []
        asyncio.ensure_future(self.cleaner())

    async def force_get_entity(self, *args, **kwargs):
        """Forcefully makes a request to Telegram to get the entity."""

        return await self.get_entity(*args, force=True, **kwargs)

    async def get_entity(
        self,
        entity: EntityLike,
        exp: int = 5 * 60,
        force: bool = False,
    ):
        """
        Gets the entity and cache it

        :param entity: Entity to fetch
        :param exp: Expiration time of the cache record and maximum time of already cached record
        :param force: Whether to force refresh the cache (make API request)
        :return: :obj:`Entity`
        """

        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _hikka_client_id_logging_tag = copy.copy(self.tg_id)  # skipcq

        if not hashable(entity):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    "Can't parse hashable from entity %s, using legacy resolve",
                    entity,
                )
                return await TelegramClient.get_entity(self, entity)
        else:
            hashable_entity = entity

        if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
            hashable_entity = int(str(hashable_entity)[4:])

        if (
            not force
            and hashable_entity
            and hashable_entity in self._hikka_entity_cache
            and (
                not exp
                or self._hikka_entity_cache[hashable_entity].ts + exp > time.time()
            )
        ):
            logger.debug(
                "Using cached entity %s (%s)",
                entity,
                type(self._hikka_entity_cache[hashable_entity].entity).__name__,
            )
            return copy.deepcopy(self._hikka_entity_cache[hashable_entity].entity)

        resolved_entity = await TelegramClient.get_entity(self, entity)

        if resolved_entity:
            cache_record = CacheRecord(hashable_entity, resolved_entity, exp)
            self._hikka_entity_cache[hashable_entity] = cache_record
            logger.debug("Saved hashable_entity %s to cache", hashable_entity)

            if getattr(resolved_entity, "id", None):
                logger.debug("Saved resolved_entity id %s to cache", resolved_entity.id)
                self._hikka_entity_cache[resolved_entity.id] = cache_record

            if getattr(resolved_entity, "username", None):
                logger.debug(
                    "Saved resolved_entity username @%s to cache",
                    resolved_entity.username,
                )
                self._hikka_entity_cache[f"@{resolved_entity.username}"] = cache_record
                self._hikka_entity_cache[resolved_entity.username] = cache_record

        return copy.deepcopy(resolved_entity)

    async def get_perms_cached(
        self,
        entity: EntityLike,
        user: typing.Optional[EntityLike] = None,
        exp: int = 5 * 60,
        force: bool = False,
    ):
        """
        Gets the permissions of the user in the entity and cache it

        :param entity: Entity to fetch
        :param user: User to fetch
        :param exp: Expiration time of the cache record and maximum time of already cached record
        :param force: Whether to force refresh the cache (make API request)
        :return: :obj:`ChatPermissions`
        """

        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _hikka_client_id_logging_tag = copy.copy(self.tg_id)  # skipcq

        entity = await self.get_entity(entity)
        user = await self.get_entity(user) if user else None

        if not hashable(entity) or not hashable(user):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    "Can't parse hashable from entity %s, using legacy method",
                    entity,
                )
                return await self.get_permissions(entity, user)

            try:
                hashable_user = next(
                    getattr(user, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(user, attr, None)
                )
            except StopIteration:
                logger.debug(
                    "Can't parse hashable from user %s, using legacy method",
                    user,
                )
                return await self.get_permissions(entity, user)
        else:
            hashable_entity = entity
            hashable_user = user

        if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
            hashable_entity = int(str(hashable_entity)[4:])

        if str(hashable_user).isdigit() and int(hashable_user) < 0:
            hashable_user = int(str(hashable_user)[4:])

        if (
            not force
            and hashable_entity
            and hashable_user
            and hashable_user in self._hikka_perms_cache.get(hashable_entity, {})
            and (
                not exp
                or self._hikka_perms_cache[hashable_entity][hashable_user].ts + exp
                > time.time()
            )
        ):
            logger.debug("Using cached perms %s (%s)", hashable_entity, hashable_user)
            return copy.deepcopy(
                self._hikka_perms_cache[hashable_entity][hashable_user].perms
            )

        resolved_perms = await self.get_permissions(entity, user)

        if resolved_perms:
            cache_record = CacheRecordPerms(
                hashable_entity,
                hashable_user,
                resolved_perms,
                exp,
            )
            self._hikka_perms_cache.setdefault(hashable_entity, {})[
                hashable_user
            ] = cache_record
            logger.debug("Saved hashable_entity %s perms to cache", hashable_entity)

            def save_user(key: typing.Union[str, int]):
                nonlocal self, cache_record, user, hashable_user
                if getattr(user, "id", None):
                    self._hikka_perms_cache.setdefault(key, {})[user.id] = cache_record

                if getattr(user, "username", None):
                    self._hikka_perms_cache.setdefault(key, {})[
                        f"@{user.username}"
                    ] = cache_record
                    self._hikka_perms_cache.setdefault(key, {})[
                        user.username
                    ] = cache_record

            if getattr(entity, "id", None):
                logger.debug("Saved resolved_entity id %s perms to cache", entity.id)
                save_user(entity.id)

            if getattr(entity, "username", None):
                logger.debug(
                    "Saved resolved_entity username @%s perms to cache",
                    entity.username,
                )
                save_user(f"@{entity.username}")
                save_user(entity.username)

        return copy.deepcopy(resolved_perms)

    async def get_fullchannel(
        self,
        entity: EntityLike,
        exp: int = 300,
        force: bool = False,
    ) -> ChannelFull:
        """
        Gets the FullChannelRequest and cache it

        :param entity: Channel to fetch ChannelFull of
        :param exp: Expiration time of the cache record and maximum time of already cached record
        :param force: Whether to force refresh the cache (make API request)
        :return: :obj:`ChannelFull`
        """
        if not hashable(entity):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"channel_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    "Can't parse hashable from entity %s, using legacy fullchannel"
                    " request",
                    entity,
                )
                return await self(GetFullChannelRequest(channel=entity))
        else:
            hashable_entity = entity

        if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
            hashable_entity = int(str(hashable_entity)[4:])

        if (
            not force
            and self._hikka_fullchannel_cache.get(hashable_entity)
            and not self._hikka_fullchannel_cache[hashable_entity].expired()
            and self._hikka_fullchannel_cache[hashable_entity].ts + exp > time.time()
        ):
            return self._hikka_fullchannel_cache[hashable_entity].full_channel

        result = await self(GetFullChannelRequest(channel=entity))
        self._hikka_fullchannel_cache[hashable_entity] = CacheRecordFullChannel(
            hashable_entity,
            result,
            exp,
        )
        return result

    async def get_fulluser(
        self,
        entity: EntityLike,
        exp: int = 300,
        force: bool = False,
    ) -> UserFull:
        """
        Gets the FullUserRequest and cache it

        :param entity: User to fetch UserFull of
        :param exp: Expiration time of the cache record and maximum time of already cached record
        :param force: Whether to force refresh the cache (make API request)
        :return: :obj:`UserFull`
        """
        if not hashable(entity):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"user_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    "Can't parse hashable from entity %s, using legacy fulluser"
                    " request",
                    entity,
                )
                return await self(GetFullUserRequest(entity))
        else:
            hashable_entity = entity

        if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
            hashable_entity = int(str(hashable_entity)[4:])

        if (
            not force
            and self._hikka_fulluser_cache.get(hashable_entity)
            and not self._hikka_fulluser_cache[hashable_entity].expired()
            and self._hikka_fulluser_cache[hashable_entity].ts + exp > time.time()
        ):
            return self._hikka_fulluser_cache[hashable_entity].full_user

        result = await self(GetFullUserRequest(entity))
        self._hikka_fulluser_cache[hashable_entity] = CacheRecordFullUser(
            hashable_entity,
            result,
            exp,
        )
        return result

    async def _call(
        self,
        sender: MTProtoSender,
        request: TLRequest,
        ordered: bool = False,
        flood_sleep_threshold: typing.Optional[int] = None,
    ):
        """
        Calls the given request and handles user-side forbidden constructors

        :param sender: Sender to use
        :param request: Request to send
        :param ordered: Whether to send the request ordered
        :param flood_sleep_threshold: Flood sleep threshold
        :return: The result of the request
        """

        # ⚠️⚠️  WARNING!  ⚠️⚠️
        # If you are a module developer, and you'll try to bypass this protection to
        # force user join your channel, you will be added to SCAM modules
        # list and you will be banned from Hikka federation.
        # Let USER decide, which channel he will follow. Do not be so petty
        # I hope, you understood me.
        # Thank you

        if not self.__forbidden_constructors:
            return await TelegramClient._call(
                self,
                sender,
                request,
                ordered,
                flood_sleep_threshold,
            )

        not_tuple = False
        if not is_list_like(request):
            not_tuple = True
            request = (request,)

        new_request = []

        for item in request:
            if item.CONSTRUCTOR_ID in self.__forbidden_constructors and next(
                (
                    frame_info.frame.f_locals["self"]
                    for frame_info in inspect.stack()
                    if hasattr(frame_info, "frame")
                    and hasattr(frame_info.frame, "f_locals")
                    and isinstance(frame_info.frame.f_locals, dict)
                    and "self" in frame_info.frame.f_locals
                    and isinstance(frame_info.frame.f_locals["self"], Module)
                    and not getattr(
                        frame_info.frame.f_locals["self"], "__origin__", ""
                    ).startswith("<core")
                ),
                None,
            ):
                logger.debug(
                    "🎉 I protected you from unintented %s (%s)!",
                    item.__class__.__name__,
                    item,
                )
                continue

            new_request += [item]

        if not new_request:
            return

        return await TelegramClient._call(
            self,
            sender,
            new_request[0] if not_tuple else tuple(new_request),
            ordered,
            flood_sleep_threshold,
        )

    def forbid_constructor(self, constructor: int):
        """
        Forbids the given constructor to be called

        :param constructor: Constructor id to forbid
        """
        self.__forbidden_constructors.extend([constructor])
        self.__forbidden_constructors = list(set(self.__forbidden_constructors))

    def forbid_constructors(self, constructors: list):
        """
        Forbids the given constructors to be called.
        All existing forbidden constructors will be removed

        :param constructors: Constructor ids to forbid
        """
        self.__forbidden_constructors = list(set(constructors))

    async def cleaner(self):
        """Cleans outdated cache records"""

        while True:
            for record, record_data in self._hikka_entity_cache.copy().items():
                if record_data.expired():
                    del self._hikka_entity_cache[record]
                    logger.debug("Cleaned outdated cache record %s", record)

            for chat, chat_data in self._hikka_perms_cache.copy().items():
                for user, user_data in chat_data.copy().items():
                    if user_data.expired():
                        del self._hikka_perms_cache[chat][user]
                        logger.debug(
                            "Cleaned outdated perms cache chat %s user %s",
                            chat,
                            user,
                        )

            for channel_id, record in self._hikka_fullchannel_cache.copy().items():
                if record.expired():
                    del self._hikka_fullchannel_cache[channel_id]
                    logger.debug(
                        "Cleaned outdated fullchannel cache channel_id %s",
                        channel_id,
                    )

            for user_id, record in self._hikka_fulluser_cache.copy().items():
                if record.expired():
                    del self._hikka_fulluser_cache[user_id]
                    logger.debug("Cleaned outdated fulluser cache user_id %s", user_id)

            await asyncio.sleep(3)
