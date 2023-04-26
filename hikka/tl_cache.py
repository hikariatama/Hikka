# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import copy
import inspect
import logging
import time
import typing

from hikkatl import TelegramClient
from hikkatl.errors.rpcerrorlist import TopicDeletedError
from hikkatl.hints import EntityLike
from hikkatl.network import MTProtoSender
from hikkatl.tl.functions.channels import GetFullChannelRequest
from hikkatl.tl.functions.users import GetFullUserRequest
from hikkatl.tl.tlobject import TLRequest
from hikkatl.tl.types import (
    ChannelFull,
    Message,
    Updates,
    UpdatesCombined,
    UpdateShort,
    UserFull,
)
from hikkatl.utils import is_list_like

from .types import (
    CacheRecordEntity,
    CacheRecordFullChannel,
    CacheRecordFullUser,
    CacheRecordPerms,
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

        self._hikka_entity_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordEntity,
        ] = {}

        self._hikka_perms_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordPerms,
        ] = {}

        self._hikka_fullchannel_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordFullChannel,
        ] = {}

        self._hikka_fulluser_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordFullUser,
        ] = {}

        self._forbidden_constructors: typing.List[int] = []

        self._raw_updates_processor: typing.Optional[
            typing.Callable[
                [typing.Union[Updates, UpdatesCombined, UpdateShort]],
                typing.Any,
            ]
        ] = None

    @property
    def raw_updates_processor(self) -> typing.Optional[callable]:
        return self._raw_updates_processor

    @raw_updates_processor.setter
    def raw_updates_processor(self, value: callable):
        if self._raw_updates_processor is not None:
            raise ValueError("raw_updates_processor is already set")

        if not callable(value):
            raise ValueError("raw_updates_processor must be callable")

        self._raw_updates_processor = value

    @property
    def hikka_entity_cache(self) -> typing.Dict[int, CacheRecordEntity]:
        return self._hikka_entity_cache

    @property
    def hikka_perms_cache(self) -> typing.Dict[int, CacheRecordPerms]:
        return self._hikka_perms_cache

    @property
    def hikka_fullchannel_cache(self) -> typing.Dict[int, CacheRecordFullChannel]:
        return self._hikka_fullchannel_cache

    @property
    def hikka_fulluser_cache(self) -> typing.Dict[int, CacheRecordFullUser]:
        return self._hikka_fulluser_cache

    @property
    def forbidden_constructors(self) -> typing.List[str]:
        return self._forbidden_constructors

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
        _hikka_client_id_logging_tag = copy.copy(self.tg_id)  # noqa: F841

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
            cache_record = CacheRecordEntity(hashable_entity, resolved_entity, exp)
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
        _hikka_client_id_logging_tag = copy.copy(self.tg_id)  # noqa: F841

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
                    (
                        "Can't parse hashable from entity %s, using legacy fullchannel"
                        " request"
                    ),
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
            and not self._hikka_fullchannel_cache[hashable_entity].expired
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
                    (
                        "Can't parse hashable from entity %s, using legacy fulluser"
                        " request"
                    ),
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
            and not self._hikka_fulluser_cache[hashable_entity].expired
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

    @staticmethod
    def _find_message_obj_in_frame(
        chat_id: int,
        frame: inspect.FrameInfo,
    ) -> typing.Optional[Message]:
        """
        Finds the message object from the frame
        """
        logger.debug("Finding message object in frame %s", frame)
        return next(
            (
                obj
                for obj in frame.frame.f_locals.values()
                if isinstance(obj, Message)
                and getattr(obj.reply_to, "forum_topic", False)
                and chat_id == getattr(obj.peer_id, "channel_id", None)
            ),
            None,
        )

    async def _find_message_obj_in_stack(
        self,
        chat: EntityLike,
        stack: typing.List[inspect.FrameInfo],
    ) -> typing.Optional[Message]:
        """
        Finds the message object from the stack
        """
        chat_id = (await self.get_entity(chat, exp=0)).id
        logger.debug("Finding message object in stack for chat %s", chat_id)
        return next(
            (
                self._find_message_obj_in_frame(chat_id, frame_info)
                for frame_info in stack
                if self._find_message_obj_in_frame(chat_id, frame_info)
            ),
            None,
        )

    async def _find_topic_in_stack(
        self,
        chat: EntityLike,
        stack: typing.List[inspect.FrameInfo],
    ) -> typing.Optional[Message]:
        """
        Finds the message object from the stack
        """
        message = await self._find_message_obj_in_stack(chat, stack)
        return (
            (message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id)
            if message
            else None
        )

    async def _topic_guesser(
        self,
        native_method: typing.Callable[..., typing.Awaitable[Message]],
        stack: typing.List[inspect.FrameInfo],
        *args,
        **kwargs,
    ):
        no_retry = kwargs.pop("_topic_no_retry", False)
        try:
            return await native_method(self, *args, **kwargs)
        except TopicDeletedError:
            if no_retry:
                raise

            logger.debug("Topic deleted, trying to guess topic id")

            topic = await self._find_topic_in_stack(args[0], stack)

            logger.debug("Guessed topic id: %s", topic)

            if not topic:
                raise

            kwargs["reply_to"] = topic
            kwargs["_topic_no_retry"] = True
            return await self._topic_guesser(native_method, stack, *args, **kwargs)

    async def send_file(self, *args, **kwargs) -> Message:
        return await self._topic_guesser(
            TelegramClient.send_file,
            inspect.stack(),
            *args,
            **kwargs,
        )

    async def send_message(self, *args, **kwargs) -> Message:
        return await self._topic_guesser(
            TelegramClient.send_message,
            inspect.stack(),
            *args,
            **kwargs,
        )

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

        not_tuple = False
        if not is_list_like(request):
            not_tuple = True
            request = (request,)

        new_request = []

        for item in request:
            if item.CONSTRUCTOR_ID in self._forbidden_constructors and next(
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
        self._forbidden_constructors.extend([constructor])
        self._forbidden_constructors = list(set(self._forbidden_constructors))

    def forbid_constructors(self, constructors: list):
        """
        Forbids the given constructors to be called.
        All existing forbidden constructors will be removed

        :param constructors: Constructor ids to forbid
        """
        self._forbidden_constructors = list(set(constructors))

    def _handle_update(
        self: "CustomTelegramClient",
        update: typing.Union[Updates, UpdatesCombined, UpdateShort],
    ):
        if self._raw_updates_processor is not None:
            self._raw_updates_processor(update)

        super()._handle_update(update)
