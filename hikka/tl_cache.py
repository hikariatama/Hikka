#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import copy
import time
import asyncio
import logging
from typing import Optional, Union
from xml.dom.minidom import Entity
from telethon.hints import EntityLike
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelFull

logger = logging.getLogger(__name__)


def hashable(value):
    """Determine whether `value` can be hashed."""
    try:
        hash(value)
    except TypeError:
        return False

    return True


class CacheRecord:
    def __init__(
        self,
        hashable_entity: "Hashable",  # type: ignore
        resolved_entity: EntityLike,
        exp: int,
    ):
        self.entity = copy.deepcopy(resolved_entity)
        self._hashable_entity = copy.deepcopy(hashable_entity)
        self._exp = round(time.time() + exp)
        self.ts = time.time()

    def expired(self):
        return self._exp < time.time()

    def __eq__(self, record: "CacheRecord"):
        return hash(record) == hash(self)

    def __hash__(self):
        return hash(self._hashable_entity)

    def __str__(self):
        return f"CacheRecord of {self.entity}"

    def __repr__(self):
        return f"CacheRecord(entity={type(self.entity).__name__}(...), exp={self._exp})"


class CacheRecordPerms:
    def __init__(
        self,
        hashable_entity: "Hashable",  # type: ignore
        hashable_user: "Hashable",  # type: ignore
        resolved_perms: EntityLike,
        exp: int,
    ):
        self.perms = copy.deepcopy(resolved_perms)
        self._hashable_entity = copy.deepcopy(hashable_entity)
        self._hashable_user = copy.deepcopy(hashable_user)
        self._exp = round(time.time() + exp)
        self.ts = time.time()

    def expired(self):
        return self._exp < time.time()

    def __eq__(self, record: "CacheRecordPerms"):
        return hash(record) == hash(self)

    def __hash__(self):
        return hash((self._hashable_entity, self._hashable_user))

    def __str__(self):
        return f"CacheRecordPerms of {self.perms}"

    def __repr__(self):
        return (
            f"CacheRecordPerms(perms={type(self.perms).__name__}(...), exp={self._exp})"
        )


class CacheRecordFullChannel:
    def __init__(self, channel_id: int, full_channel: ChannelFull, exp: int):
        self.channel_id = channel_id
        self.full_channel = full_channel
        self._exp = round(time.time() + exp)
        self.ts = time.time()

    def expired(self):
        return self._exp < time.time()

    def __eq__(self, record: "CacheRecordFullChannel"):
        return hash(record) == hash(self)

    def __hash__(self):
        return hash((self._hashable_entity, self._hashable_user))

    def __str__(self):
        return f"CacheRecordFullChannel of {self.channel_id}"

    def __repr__(self):
        return (
            f"CacheRecordFullChannel(channel_id={self.channel_id}(...),"
            f" exp={self._exp})"
        )


def install_entity_caching(client: TelegramClient):
    client._hikka_entity_cache = {}

    old = client.get_entity

    async def new(
        entity: EntityLike,
        exp: Optional[int] = 5 * 60,
        force: Optional[bool] = False,
    ):
        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _hikka_client_id_logging_tag = copy.copy(client.tg_id)  # skipcq

        if not hashable(entity):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    f"Can't parse hashable from {entity=}, using legacy resolve"
                )
                return await old(entity)
        else:
            hashable_entity = entity

        if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
            hashable_entity = int(str(hashable_entity)[4:])

        if (
            not force
            and hashable_entity
            and hashable_entity in client._hikka_entity_cache
            and (
                not exp
                or client._hikka_entity_cache[hashable_entity].ts + exp > time.time()
            )
        ):
            logger.debug(
                "Using cached entity"
                f" {entity} ({type(client._hikka_entity_cache[hashable_entity].entity).__name__})"
            )
            return copy.deepcopy(client._hikka_entity_cache[hashable_entity].entity)

        resolved_entity = await old(entity)

        if resolved_entity:
            cache_record = CacheRecord(hashable_entity, resolved_entity, exp)
            client._hikka_entity_cache[hashable_entity] = cache_record
            logger.debug(f"Saved hashable_entity {hashable_entity} to cache")

            if getattr(resolved_entity, "id", None):
                logger.debug(f"Saved resolved_entity id {resolved_entity.id} to cache")
                client._hikka_entity_cache[resolved_entity.id] = cache_record

            if getattr(resolved_entity, "username", None):
                logger.debug(
                    f"Saved resolved_entity username @{resolved_entity.username} to"
                    " cache"
                )
                client._hikka_entity_cache[
                    f"@{resolved_entity.username}"
                ] = cache_record
                client._hikka_entity_cache[resolved_entity.username] = cache_record

        return copy.deepcopy(resolved_entity)

    async def cleaner(client: TelegramClient):
        while True:
            for record, record_data in client._hikka_entity_cache.copy().items():
                if record_data.expired():
                    del client._hikka_entity_cache[record]
                    logger.debug(f"Cleaned outdated cache {record=}")

            await asyncio.sleep(3)

    client.get_entity = new
    client.force_get_entity = old
    asyncio.ensure_future(cleaner(client))
    logger.debug("Monkeypatched client with entity cacher")


def install_perms_caching(client: TelegramClient):
    client._hikka_perms_cache = {}

    old = client.get_permissions

    async def new(
        entity: EntityLike,
        user: Optional[EntityLike] = None,
        exp: Optional[int] = 5 * 60,
        force: Optional[bool] = False,
    ):
        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _hikka_client_id_logging_tag = copy.copy(client.tg_id)  # skipcq

        entity = await client.get_entity(entity)
        user = await client.get_entity(user) if user else None

        if not hashable(entity) or not hashable(user):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    f"Can't parse hashable from {entity=}, using legacy method"
                )
                return await old(entity, user)

            try:
                hashable_user = next(
                    getattr(user, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(user, attr, None)
                )
            except StopIteration:
                logger.debug(f"Can't parse hashable from {user=}, using legacy method")
                return await old(entity, user)
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
            and hashable_user in client._hikka_perms_cache.get(hashable_entity, {})
            and (
                not exp
                or client._hikka_perms_cache[hashable_entity][hashable_user].ts + exp
                > time.time()
            )
        ):
            logger.debug(f"Using cached perms {hashable_entity} ({hashable_user})")
            return copy.deepcopy(
                client._hikka_perms_cache[hashable_entity][hashable_user].perms
            )

        resolved_perms = await old(entity, user)

        if resolved_perms:
            cache_record = CacheRecordPerms(
                hashable_entity,
                hashable_user,
                resolved_perms,
                exp,
            )
            client._hikka_perms_cache.setdefault(hashable_entity, {})[
                hashable_user
            ] = cache_record
            logger.debug(f"Saved hashable_entity {hashable_entity} perms to cache")

            def save_user(key: Union[str, int]):
                nonlocal client, cache_record, user, hashable_user
                if getattr(user, "id", None):
                    client._hikka_perms_cache.setdefault(key, {})[
                        user.id
                    ] = cache_record

                if getattr(user, "username", None):
                    client._hikka_perms_cache.setdefault(key, {})[
                        f"@{user.username}"
                    ] = cache_record
                    client._hikka_perms_cache.setdefault(key, {})[
                        user.username
                    ] = cache_record

            if getattr(entity, "id", None):
                logger.debug(f"Saved resolved_entity id {entity.id} perms to cache")
                save_user(entity.id)

            if getattr(entity, "username", None):
                logger.debug(
                    f"Saved resolved_entity username @{entity.username} perms to cache"
                )
                save_user(f"@{entity.username}")
                save_user(entity.username)

        return copy.deepcopy(resolved_perms)

    async def cleaner(client: TelegramClient):
        while True:
            for chat, chat_data in client._hikka_perms_cache.copy().items():
                for user, user_data in chat_data.items().copy():
                    if user_data.expired():
                        del client._hikka_perms_cache[chat][user]
                        logger.debug(f"Cleaned outdated perms cache {chat=} {user=}")

            await asyncio.sleep(3)

    client.get_perms_cached = new
    asyncio.ensure_future(cleaner(client))
    logger.debug("Monkeypatched client with perms cacher")


def install_fullchannel_caching(client: TelegramClient):
    client._hikka_fullchannel_cache = {}

    async def get_fullchannel(
        entity: EntityLike,
        exp: Optional[int] = 300,
        force: Optional[bool] = False,
    ) -> ChannelFull:
        """
        Gets the FullChannelRequest and cache it
        :param channel_id: Channel to fetch ChannelFull of
        :param exp: Expiration time of the cache record and maximum time of already cached record
        :param force: Whether to force refresh the cache (make API request)
        :return: :obj:`FullChannel`
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
                    f"Can't parse hashable from {entity=}, using legacy fullchannel request"
                )
                return await client(GetFullChannelRequest(channel=entity))
        else:
            hashable_entity = entity

        if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
            hashable_entity = int(str(hashable_entity)[4:])

        if (
            not force
            and client._hikka_fullchannel_cache.get(hashable_entity)
            and not client._hikka_fullchannel_cache[hashable_entity].expired()
            and client._hikka_fullchannel_cache[hashable_entity].ts + exp > time.time()
        ):
            return client._hikka_fullchannel_cache[hashable_entity].full_channel

        result = await client(GetFullChannelRequest(channel=entity))
        client._hikka_fullchannel_cache[hashable_entity] = CacheRecordFullChannel(
            hashable_entity,
            result,
            exp,
        )
        return result
    
    async def cleaner(client: TelegramClient):
        while True:
            for channel_id, record in client._hikka_fullchannel_cache.copy().items():
                if record.expired():
                    del client._hikka_fullchannel_cache[channel_id]
                    logger.debug(f"Cleaned outdated fullchannel cache {channel_id=}")

            await asyncio.sleep(3)
    
    client.get_fullchannel = get_fullchannel
    asyncio.ensure_future(cleaner(client))
    logger.debug("Monkeypatched client with fullchannel cacher")
