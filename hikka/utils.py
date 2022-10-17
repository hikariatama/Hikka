"""Utilities"""

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import functools
import io
import json
import logging
import os
import random
import re
import shlex
import string
import time
import inspect
from datetime import timedelta
import typing
from urllib.parse import urlparse

import git
import grapheme
import requests
import telethon
from telethon import hints
from telethon.tl.custom.message import Message
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditPhotoRequest,
    EditAdminRequest,
    InviteToChannelRequest,
)
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
    SetHistoryTTLRequest,
)
from telethon.tl.types import (
    Channel,
    InputPeerNotifySettings,
    MessageEntityBankCard,
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityPre,
    MessageEntitySpoiler,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUnknown,
    MessageEntityUrl,
    MessageMediaWebPage,
    PeerChannel,
    PeerChat,
    PeerUser,
    User,
    Chat,
    UpdateNewChannelMessage,
    ChatAdminRights,
)

from aiogram.types import Message as AiogramMessage

from .inline.types import InlineCall, InlineMessage
from .types import Module, ListLike
from .tl_cache import CustomTelegramClient


FormattingEntity = typing.Union[
    MessageEntityUnknown,
    MessageEntityMention,
    MessageEntityHashtag,
    MessageEntityBotCommand,
    MessageEntityUrl,
    MessageEntityEmail,
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityCashtag,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityBankCard,
    MessageEntitySpoiler,
]

emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

parser = telethon.utils.sanitize_parse_mode("html")
logger = logging.getLogger(__name__)


def get_args(message: typing.Union[Message, str]) -> typing.List[str]:
    """
    Get arguments from message
    :param message: Message or string to get arguments from
    :return: List of arguments
    """
    if not (message := getattr(message, "message", message)):
        return False

    if len(message := message.split(maxsplit=1)) <= 1:
        return []

    message = message[1]

    try:
        split = shlex.split(message)
    except ValueError:
        return message  # Cannot split, let's assume that it's just one long message

    return list(filter(lambda x: len(x) > 0, split))


def get_args_raw(message: typing.Union[Message, str]) -> str:
    """
    Get the parameters to the command as a raw string (not split)
    :param message: Message or string to get arguments from
    :return: Raw string of arguments
    """
    if not (message := getattr(message, "message", message)):
        return False

    return args[1] if len(args := message.split(maxsplit=1)) > 1 else ""


def get_args_html(message: Message) -> str:
    """
    Get the parameters to the command as string with HTML (not split)
    :param message: Message to get arguments from
    :return: String with HTML arguments
    """
    prefix = message.client.loader.get_prefix()

    if not (message := message.text):
        return False

    if prefix not in message:
        return message

    raw_text, entities = parser.parse(message)

    raw_text = parser._add_surrogate(raw_text)

    try:
        command = raw_text[
            raw_text.index(prefix) : raw_text.index(" ", raw_text.index(prefix) + 1)
        ]
    except ValueError:
        return ""

    command_len = len(command) + 1

    return parser.unparse(
        parser._del_surrogate(raw_text[command_len:]),
        relocate_entities(entities, -command_len, raw_text[command_len:]),
    )


def get_args_split_by(
    message: typing.Union[Message, str],
    separator: str,
) -> typing.List[str]:
    """
    Split args with a specific separator
    :param message: Message or string to get arguments from
    :param separator: Separator to split by
    :return: List of arguments
    """
    return [
        section.strip() for section in get_args_raw(message).split(separator) if section
    ]


def get_chat_id(message: typing.Union[Message, AiogramMessage]) -> int:
    """
    Get the chat ID, but without -100 if its a channel
    :param message: Message to get chat ID from
    :return: Chat ID
    """
    return telethon.utils.resolve_id(
        getattr(message, "chat_id", None)
        or getattr(getattr(message, "chat", None), "id", None)
    )[0]


def get_entity_id(entity: hints.Entity) -> int:
    """
    Get entity ID
    :param entity: Entity to get ID from
    :return: Entity ID
    """
    return telethon.utils.get_peer_id(entity)


def escape_html(text: str, /) -> str:  # sourcery skip
    """
    Pass all untrusted/potentially corrupt input here
    :param text: Text to escape
    :return: Escaped text
    """
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_quotes(text: str, /) -> str:
    """
    Escape quotes to html quotes
    :param text: Text to escape
    :return: Escaped text
    """
    return escape_html(text).replace('"', "&quot;")


def get_base_dir() -> str:
    """
    Get directory of this file
    :return: Directory of this file
    """
    return get_dir(__file__)


def get_dir(mod: str) -> str:
    """
    Get directory of given module
    :param mod: Module's `__file__` to get directory of
    :return: Directory of given module
    """
    return os.path.abspath(os.path.dirname(os.path.abspath(mod)))


async def get_user(message: Message) -> typing.Optional[User]:
    """
    Get user who sent message, searching if not found easily
    :param message: Message to get user from
    :return: User who sent message
    """
    try:
        return await message.client.get_entity(message.sender_id)
    except ValueError:  # Not in database. Lets go looking for them.
        logger.debug("User not in session cache. Searching...")

    if isinstance(message.peer_id, PeerUser):
        await message.client.get_dialogs()
        return await message.client.get_entity(message.sender_id)

    if isinstance(message.peer_id, (PeerChannel, PeerChat)):
        with contextlib.suppress(Exception):
            return await message.client.get_entity(message.sender_id)
        async for user in message.client.iter_participants(
            message.peer_id,
            aggressive=True,
        ):
            if user.id == message.sender_id:
                return user

        logger.error("User isn't in the group where they sent the message")
        return None

    logger.error("`peer_id` is not a user, chat or channel")
    return None


def run_sync(func, *args, **kwargs):
    """
    Run a non-async function in a new thread and return an awaitable
    :param func: Sync-only function to execute
    :return: Awaitable coroutine
    """
    return asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(func, *args, **kwargs),
    )


def run_async(loop: asyncio.AbstractEventLoop, coro: typing.Awaitable) -> typing.Any:
    """
    Run an async function as a non-async function, blocking till it's done
    :param loop: Event loop to run the coroutine in
    :param coro: Coroutine to run
    :return: Result of the coroutine
    """
    # When we bump minimum support to 3.7, use run()
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def censor(
    obj: typing.Any,
    to_censor: typing.Optional[typing.Iterable[str]] = None,
    replace_with: str = "redacted_{count}_chars",
):
    """
    May modify the original object, but don't rely on it
    :param obj: Object to censor, preferrably telethon
    :param to_censor: Iterable of strings to censor
    :param replace_with: String to replace with, {count} will be replaced with the number of characters
    :return: Censored object
    """
    if to_censor is None:
        to_censor = ["phone"]

    for k, v in vars(obj).items():
        if k in to_censor:
            setattr(obj, k, replace_with.format(count=len(v)))
        elif k[0] != "_" and hasattr(v, "__dict__"):
            setattr(obj, k, censor(v, to_censor, replace_with))

    return obj


def relocate_entities(
    entities: typing.List[FormattingEntity],
    offset: int,
    text: typing.Optional[str] = None,
) -> typing.List[FormattingEntity]:
    """
    Move all entities by offset (truncating at text)
    :param entities: List of entities
    :param offset: Offset to move by
    :param text: Text to truncate at
    :return: List of entities
    """
    length = len(text) if text is not None else 0

    for ent in entities.copy() if entities else ():
        ent.offset += offset
        if ent.offset < 0:
            ent.length += ent.offset
            ent.offset = 0
        if text is not None and ent.offset + ent.length > length:
            ent.length = length - ent.offset
        if ent.length <= 0:
            entities.remove(ent)

    return entities


async def answer(
    message: typing.Union[Message, InlineCall, InlineMessage],
    response: str,
    *,
    reply_markup: typing.Optional[
        typing.Union[typing.List[typing.List[dict]], typing.List[dict], dict]
    ] = None,
    **kwargs,
) -> typing.Union[InlineCall, InlineMessage, Message]:
    """
    Use this to give the response to a command
    :param message: Message to answer to. Can be a tl message or hikka inline object
    :param response: Response to send
    :param reply_markup: Reply markup to send. If specified, inline form will be used
    :return: Message or inline object

    :example:
        >>> await utils.answer(message, "Hello world!")
        >>> await utils.answer(
            message,
            "https://some-url.com/photo.jpg",
            caption="Hello, this is your photo!",
            asfile=True,
        )
        >>> await utils.answer(
            message,
            "Hello world!",
            reply_markup={"text": "Hello!", "data": "world"},
            silent=True,
            disable_security=True,
        )
    """
    # Compatibility with FTG\GeekTG

    if isinstance(message, list) and message:
        message = message[0]

    if reply_markup is not None:
        if not isinstance(reply_markup, (list, dict)):
            raise ValueError("reply_markup must be a list or dict")

        if reply_markup:
            kwargs.pop("message", None)
            if isinstance(message, (InlineMessage, InlineCall)):
                await message.edit(response, reply_markup, **kwargs)
                return

            reply_markup = message.client.loader.inline._normalize_markup(reply_markup)
            result = await message.client.loader.inline.form(
                response,
                message=message if message.out else get_chat_id(message),
                reply_markup=reply_markup,
                **kwargs,
            )
            return result

    if isinstance(message, (InlineMessage, InlineCall)):
        await message.edit(response)
        return message

    kwargs.setdefault("link_preview", False)

    if not (edit := (message.out and not message.via_bot_id and not message.fwd_from)):
        kwargs.setdefault(
            "reply_to",
            getattr(message, "reply_to_msg_id", None),
        )

    parse_mode = telethon.utils.sanitize_parse_mode(
        kwargs.pop(
            "parse_mode",
            message.client.parse_mode,
        )
    )

    if isinstance(response, str) and not kwargs.pop("asfile", False):
        text, entities = parse_mode.parse(response)

        if len(text) >= 4096 and not hasattr(message, "hikka_grepped"):
            try:
                if not message.client.loader.inline.init_complete:
                    raise

                strings = list(smart_split(text, entities, 4096))

                if len(strings) > 10:
                    raise

                list_ = await message.client.loader.inline.list(
                    message=message,
                    strings=strings,
                )

                if not list_:
                    raise

                return list_
            except Exception:
                file = io.BytesIO(text.encode("utf-8"))
                file.name = "command_result.txt"

                result = await message.client.send_file(
                    message.peer_id,
                    file,
                    caption=message.client.loader._lookup("translations").strings(
                        "too_long"
                    ),
                )

                if message.out:
                    await message.delete()

                return result

        result = await (message.edit if edit else message.respond)(
            text,
            parse_mode=lambda t: (t, entities),
            **kwargs,
        )
    elif isinstance(response, Message):
        if message.media is None and (
            response.media is None or isinstance(response.media, MessageMediaWebPage)
        ):
            result = await message.edit(
                response.message,
                parse_mode=lambda t: (t, response.entities or []),
                link_preview=isinstance(response.media, MessageMediaWebPage),
            )
        else:
            result = await message.respond(response, **kwargs)
    else:
        if isinstance(response, bytes):
            response = io.BytesIO(response)
        elif isinstance(response, str):
            response = io.BytesIO(response.encode("utf-8"))

        if name := kwargs.pop("filename", None):
            response.name = name

        if message.media is not None and edit:
            await message.edit(file=response, **kwargs)
        else:
            kwargs.setdefault(
                "reply_to",
                getattr(message, "reply_to_msg_id", None),
            )
            result = await message.client.send_file(message.peer_id, response, **kwargs)
            if message.out:
                await message.delete()

    return result


async def get_target(message: Message, arg_no: int = 0) -> typing.Optional[int]:
    """
    Get target from message
    :param message: Message to get target from
    :param arg_no: Argument number to get target from
    :return: Target
    """

    if any(
        isinstance(entity, MessageEntityMentionName)
        for entity in (message.entities or [])
    ):
        e = sorted(
            filter(lambda x: isinstance(x, MessageEntityMentionName), message.entities),
            key=lambda x: x.offset,
        )[0]
        return e.user_id

    if len(get_args(message)) > arg_no:
        user = get_args(message)[arg_no]
    elif message.is_reply:
        return (await message.get_reply_message()).sender_id
    elif hasattr(message.peer_id, "user_id"):
        user = message.peer_id.user_id
    else:
        return None

    try:
        entity = await message.client.get_entity(user)
    except ValueError:
        return None
    else:
        if isinstance(entity, User):
            return entity.id


def merge(a: dict, b: dict, /) -> dict:
    """
    Merge with replace dictionary a to dictionary b
    :param a: Dictionary to merge
    :param b: Dictionary to merge to
    :return: Merged dictionary
    """
    for key in a:
        if key in b:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                b[key] = merge(a[key], b[key])
            elif isinstance(a[key], list) and isinstance(b[key], list):
                b[key] = list(set(b[key] + a[key]))
            else:
                b[key] = a[key]

        b[key] = a[key]

    return b


async def set_avatar(
    client: CustomTelegramClient,
    peer: hints.Entity,
    avatar: str,
) -> bool:
    """
    Sets an entity avatar
    :param client: Client to use
    :param peer: Peer to set avatar to
    :param avatar: Avatar to set
    :return: True if avatar was set, False otherwise
    """
    if isinstance(avatar, str) and check_url(avatar):
        f = (
            await run_sync(
                requests.get,
                avatar,
            )
        ).content
    elif isinstance(avatar, bytes):
        f = avatar
    else:
        return False

    res = await client(
        EditPhotoRequest(
            channel=peer,
            photo=await client.upload_file(f, file_name="photo.png"),
        )
    )

    with contextlib.suppress(Exception):
        await client.delete_messages(
            peer,
            message_ids=[
                next(
                    update
                    for update in res.updates
                    if isinstance(update, UpdateNewChannelMessage)
                ).message.id
            ],
        )
    return True


async def invite_inline_bot(
    client: CustomTelegramClient,
    peer: hints.EntityLike,
) -> None:
    """
    Invites inline bot to a chat
    :param client: Client to use
    :param peer: Peer to invite bot to
    :return: None
    :raise RuntimeError: If error occurred while inviting bot
    """

    try:
        await client(InviteToChannelRequest(peer, [client.loader.inline.bot_username]))
    except Exception as e:
        raise RuntimeError(
            "Can't invite inline bot to old asset chat, which is required by module"
        ) from e

    with contextlib.suppress(Exception):
        await client(
            EditAdminRequest(
                channel=peer,
                user_id=client.loader.inline.bot_username,
                admin_rights=ChatAdminRights(ban_users=True),
                rank="Hikka",
            )
        )


async def asset_channel(
    client: CustomTelegramClient,
    title: str,
    description: str,
    *,
    channel: bool = False,
    silent: bool = False,
    archive: bool = False,
    invite_bot: bool = False,
    avatar: typing.Optional[str] = None,
    ttl: typing.Optional[int] = None,
    _folder: typing.Optional[str] = None,
) -> typing.Tuple[Channel, bool]:
    """
    Create new channel (if needed) and return its entity
    :param client: Telegram client to create channel by
    :param title: Channel title
    :param description: Description
    :param channel: Whether to create a channel or supergroup
    :param silent: Automatically mute channel
    :param archive: Automatically archive channel
    :param invite_bot: Add inline bot and assure it's in chat
    :param avatar: Url to an avatar to set as pfp of created peer
    :param ttl: Time to live for messages in channel
    :return: Peer and bool: is channel new or pre-existent
    """
    if not hasattr(client, "_channels_cache"):
        client._channels_cache = {}

    if (
        title in client._channels_cache
        and client._channels_cache[title]["exp"] > time.time()
    ):
        return client._channels_cache[title]["peer"], False

    async for d in client.iter_dialogs():
        if d.title == title:
            client._channels_cache[title] = {"peer": d.entity, "exp": int(time.time())}
            if invite_bot and all(
                participant.id != client.loader.inline.bot_id
                for participant in (
                    await client.get_participants(d.entity, limit=100)
                )
            ):
                await invite_inline_bot(client, d.entity)

            return d.entity, False

    peer = (
        await client(
            CreateChannelRequest(
                title,
                description,
                megagroup=not channel,
            )
        )
    ).chats[0]

    if invite_bot:
        await invite_inline_bot(client, peer)

    if silent:
        await dnd(client, peer, archive)
    elif archive:
        await client.edit_folder(peer, 1)

    if avatar:
        await set_avatar(client, peer, avatar)

    if ttl:
        await client(SetHistoryTTLRequest(peer=peer, period=ttl))

    if _folder:
        if _folder != "hikka":
            raise NotImplementedError

        folders = await client(GetDialogFiltersRequest())

        try:
            folder = next(folder for folder in folders if folder.title == "hikka")
        except Exception:
            folder = None

        if folder is not None and all(
            peer.id != getattr(folder_peer, "channel_id", None)
            for folder_peer in folder.include_peers
        ):
            folder.include_peers += [await client.get_input_entity(peer)]

            await client(
                UpdateDialogFilterRequest(
                    folder.id,
                    folder,
                )
            )

    client._channels_cache[title] = {"peer": peer, "exp": int(time.time())}
    return peer, True


async def dnd(
    client: CustomTelegramClient,
    peer: hints.Entity,
    archive: bool = True,
) -> bool:
    """
    Mutes and optionally archives peer
    :param peer: Anything entity-link
    :param archive: Archive peer, or just mute?
    :return: `True` on success, otherwise `False`
    """
    try:
        await client(
            UpdateNotifySettingsRequest(
                peer=peer,
                settings=InputPeerNotifySettings(
                    show_previews=False,
                    silent=True,
                    mute_until=2**31 - 1,
                ),
            )
        )

        if archive:
            await client.edit_folder(peer, 1)
    except Exception:
        logger.exception("utils.dnd error")
        return False

    return True


def get_link(user: typing.Union[User, Channel], /) -> str:
    """
    Get telegram permalink to entity
    :param user: User or channel
    :return: Link to entity
    """
    return (
        f"tg://user?id={user.id}"
        if isinstance(user, User)
        else (
            f"tg://resolve?domain={user.username}"
            if getattr(user, "username", None)
            else ""
        )
    )


def chunks(_list: ListLike, n: int, /) -> typing.List[typing.List[typing.Any]]:
    """
    Split provided `_list` into chunks of `n`
    :param _list: List to split
    :param n: Chunk size
    :return: List of chunks
    """
    return [_list[i : i + n] for i in range(0, len(_list), n)]


def get_named_platform() -> str:
    """
    Returns formatted platform name
    :return: Platform name
    """
    with contextlib.suppress(Exception):
        if os.path.isfile("/proc/device-tree/model"):
            with open("/proc/device-tree/model") as f:
                model = f.read()
                if "Orange" in model:
                    return f"🍊 {model}"

                return f"🍇 {model}" if "Raspberry" in model else f"❓ {model}"
    with contextlib.suppress(Exception):
        from platform import uname

        if "microsoft-standard" in uname().release:
            return "🍁 WSL"
    if "GOORM" in os.environ:
        return "🦾 GoormIDE"

    if "RAILWAY" in os.environ:
        return "🚂 Railway"

    if "DOCKER" in os.environ:
        return "🐳 Docker"

    if "com.termux" in os.environ.get("PREFIX", ""):
        return "🕶 Termux"

    if "OKTETO" in os.environ:
        return "☁️ Okteto"

    if "CODESPACES" in os.environ:
        return "🐈‍⬛ Codespaces"

    return f"✌️ lavHost {os.environ['LAVHOST']}" if "LAVHOST" in os.environ else "📻 VDS"


def get_platform_emoji(client: typing.Optional[CustomTelegramClient] = None) -> str:
    """
    Returns custom emoji for current platform
    :client: It is recommended to pass the client in here in order
        to provide correct emojis for rtl languages. Make sure, that other strings
        you use, are adapted to rtl languages as well. Otherwise, the string
        will be broken.
    :return: Emoji entity in string
    """
    BASE = (
        "<emoji document_id={}>🌘</emoji>",
        "<emoji document_id=5195311729663286630>🌘</emoji>",
        "<emoji document_id=5195045669324201904>🌘</emoji>",
    )

    if client and (
        client.loader._db.get("hikka.translations", "lang", False) or ""
    ).startswith("ar"):
        BASE = tuple(reversed(BASE))

    BASE = "".join(BASE)

    if "GOORM" in os.environ:
        return BASE.format(5298947740032573902)

    if "OKTETO" in os.environ:
        return BASE.format(5192767786174128165)

    if "CODESPACES" in os.environ:
        return BASE.format(5194976881127989720)

    if "com.termux" in os.environ.get("PREFIX", ""):
        return BASE.format(5193051778001673828)

    if "RAILWAY" in os.environ:
        return BASE.format(5199607521593007466)

    return BASE.format(5192765204898783881)


def uptime() -> int:
    """
    Returns userbot uptime in seconds
    :return: Uptime in seconds
    """
    return round(time.perf_counter() - init_ts)


def formatted_uptime() -> str:
    """
    Returnes formmated uptime
    :return: Formatted uptime
    """
    return f"{str(timedelta(seconds=uptime()))}"


def ascii_face() -> str:
    """
    Returnes cute ASCII-art face
    :return: ASCII-art face
    """
    return escape_html(
        random.choice(
            [
                "ヽ(๑◠ܫ◠๑)ﾉ",
                "(◕ᴥ◕ʋ)",
                "ᕙ(`▽´)ᕗ",
                "(✿◠‿◠)",
                "(▰˘◡˘▰)",
                "(˵ ͡° ͜ʖ ͡°˵)",
                "ʕっ•ᴥ•ʔっ",
                "( ͡° ᴥ ͡°)",
                "(๑•́ ヮ •̀๑)",
                "٩(^‿^)۶",
                "(っˆڡˆς)",
                "ψ(｀∇´)ψ",
                "⊙ω⊙",
                "٩(^ᴗ^)۶",
                "(´・ω・)っ由",
                "( ͡~ ͜ʖ ͡°)",
                "✧♡(◕‿◕✿)",
                "โ๏௰๏ใ ื",
                "∩｡• ᵕ •｡∩ ♡",
                "(♡´౪`♡)",
                "(◍＞◡＜◍)⋈。✧♡",
                "╰(✿´⌣`✿)╯♡",
                "ʕ•ᴥ•ʔ",
                "ᶘ ◕ᴥ◕ᶅ",
                "▼・ᴥ・▼",
                "ฅ^•ﻌ•^ฅ",
                "(΄◞ิ౪◟ิ‵)",
                "٩(^ᴗ^)۶",
                "ᕴｰᴥｰᕵ",
                "ʕ￫ᴥ￩ʔ",
                "ʕᵕᴥᵕʔ",
                "ʕᵒᴥᵒʔ",
                "ᵔᴥᵔ",
                "(✿╹◡╹)",
                "(๑￫ܫ￩)",
                "ʕ·ᴥ·　ʔ",
                "(ﾉ≧ڡ≦)",
                "(≖ᴗ≖✿)",
                "（〜^∇^ )〜",
                "( ﾉ･ｪ･ )ﾉ",
                "~( ˘▾˘~)",
                "(〜^∇^)〜",
                "ヽ(^ᴗ^ヽ)",
                "(´･ω･`)",
                "₍ᐢ•ﻌ•ᐢ₎*･ﾟ｡",
                "(。・・)_且",
                "(=｀ω´=)",
                "(*•‿•*)",
                "(*ﾟ∀ﾟ*)",
                "(☉⋆‿⋆☉)",
                "ɷ◡ɷ",
                "ʘ‿ʘ",
                "(。-ω-)ﾉ",
                "( ･ω･)ﾉ",
                "(=ﾟωﾟ)ﾉ",
                "(・ε・`*) …",
                "ʕっ•ᴥ•ʔっ",
                "(*˘︶˘*)",
            ]
        )
    )


def array_sum(
    array: typing.List[typing.List[typing.Any]], /
) -> typing.List[typing.Any]:
    """
    Performs basic sum operation on array
    :param array: Array to sum
    :return: Sum of array
    """
    result = []
    for item in array:
        result += item

    return result


def rand(size: int, /) -> str:
    """
    Return random string of len `size`
    :param size: Length of string
    :return: Random string
    """
    return "".join(
        [random.choice("abcdefghijklmnopqrstuvwxyz1234567890") for _ in range(size)]
    )


def smart_split(
    text: str,
    entities: typing.List[FormattingEntity],
    length: int = 4096,
    split_on: ListLike = ("\n", " "),
    min_length: int = 1,
) -> typing.Iterator[str]:
    """
    Split the message into smaller messages.
    A grapheme will never be broken. Entities will be displaced to match the right location. No inputs will be mutated.
    The end of each message except the last one is stripped of characters from [split_on]
    :param text: the plain text input
    :param entities: the entities
    :param length: the maximum length of a single message
    :param split_on: characters (or strings) which are preferred for a message break
    :param min_length: ignore any matches on [split_on] strings before this number of characters into each message
    :return: iterator, which returns strings

    :example:
        >>> utils.smart_split(
            *telethon.extensions.html.parse(
                "<b>Hello, world!</b>"
            )
        )
        <<< ["<b>Hello, world!</b>"]
    """

    # Authored by @bsolute
    # https://t.me/LonamiWebs/27777

    encoded = text.encode("utf-16le")
    pending_entities = entities
    text_offset = 0
    bytes_offset = 0
    text_length = len(text)
    bytes_length = len(encoded)

    while text_offset < text_length:
        if bytes_offset + length * 2 >= bytes_length:
            yield parser.unparse(
                text[text_offset:],
                list(sorted(pending_entities, key=lambda x: x.offset)),
            )
            break

        codepoint_count = len(
            encoded[bytes_offset : bytes_offset + length * 2].decode(
                "utf-16le",
                errors="ignore",
            )
        )

        for search in split_on:
            search_index = text.rfind(
                search,
                text_offset + min_length,
                text_offset + codepoint_count,
            )
            if search_index != -1:
                break
        else:
            search_index = text_offset + codepoint_count

        split_index = grapheme.safe_split_index(text, search_index)

        split_offset_utf16 = (
            len(text[text_offset:split_index].encode("utf-16le"))
        ) // 2
        exclude = 0

        while (
            split_index + exclude < text_length
            and text[split_index + exclude] in split_on
        ):
            exclude += 1

        current_entities = []
        entities = pending_entities.copy()
        pending_entities = []

        for entity in entities:
            if (
                entity.offset < split_offset_utf16
                and entity.offset + entity.length > split_offset_utf16 + exclude
            ):
                # spans boundary
                current_entities.append(
                    _copy_tl(
                        entity,
                        length=split_offset_utf16 - entity.offset,
                    )
                )
                pending_entities.append(
                    _copy_tl(
                        entity,
                        offset=0,
                        length=entity.offset
                        + entity.length
                        - split_offset_utf16
                        - exclude,
                    )
                )
            elif entity.offset < split_offset_utf16 < entity.offset + entity.length:
                # overlaps boundary
                current_entities.append(
                    _copy_tl(
                        entity,
                        length=split_offset_utf16 - entity.offset,
                    )
                )
            elif entity.offset < split_offset_utf16:
                # wholly left
                current_entities.append(entity)
            elif (
                entity.offset + entity.length
                > split_offset_utf16 + exclude
                > entity.offset
            ):
                # overlaps right boundary
                pending_entities.append(
                    _copy_tl(
                        entity,
                        offset=0,
                        length=entity.offset
                        + entity.length
                        - split_offset_utf16
                        - exclude,
                    )
                )
            elif entity.offset + entity.length > split_offset_utf16 + exclude:
                # wholly right
                pending_entities.append(
                    _copy_tl(
                        entity,
                        offset=entity.offset - split_offset_utf16 - exclude,
                    )
                )

        current_text = text[text_offset:split_index]
        yield parser.unparse(
            current_text,
            list(sorted(current_entities, key=lambda x: x.offset)),
        )

        text_offset = split_index + exclude
        bytes_offset += len(current_text.encode("utf-16le"))


def _copy_tl(o, **kwargs):
    d = o.to_dict()
    del d["_"]
    d.update(kwargs)
    return o.__class__(**d)


def check_url(url: str) -> bool:
    """
    Statically checks url for validity
    :param url: URL to check
    :return: True if valid, False otherwise
    """
    try:
        return bool(urlparse(url).netloc)
    except Exception:
        return False


def get_git_hash() -> typing.Union[str, bool]:
    """
    Get current Hikka git hash
    :return: Git commit hash
    """
    try:
        return git.Repo().head.commit.hexsha
    except Exception:
        return False


def get_commit_url() -> str:
    """
    Get current Hikka git commit url
    :return: Git commit url
    """
    try:
        hash_ = get_git_hash()
        return (
            f'<a href="https://github.com/hikariatama/Hikka/commit/{hash_}">#{hash_[:7]}</a>'
        )
    except Exception:
        return "Unknown"


def is_serializable(x: typing.Any, /) -> bool:
    """
    Checks if object is JSON-serializable
    :param x: Object to check
    :return: True if object is JSON-serializable, False otherwise
    """
    try:
        json.dumps(x)
        return True
    except Exception:
        return False


def get_lang_flag(countrycode: str) -> str:
    """
    Gets an emoji of specified countrycode
    :param countrycode: 2-letter countrycode
    :return: Emoji flag
    """
    if (
        len(
            code := [
                c
                for c in countrycode.lower()
                if c in string.ascii_letters + string.digits
            ]
        )
        == 2
    ):
        return "".join([chr(ord(c.upper()) + (ord("🇦") - ord("A"))) for c in code])

    return countrycode


def get_entity_url(
    entity: typing.Union[User, Channel],
    openmessage: bool = False,
) -> str:
    """
    Get link to object, if available
    :param entity: Entity to get url of
    :param openmessage: Use tg://openmessage link for users
    :return: Link to object or empty string
    """
    return (
        (
            f"tg://openmessage?id={entity.id}"
            if openmessage
            else f"tg://user?id={entity.id}"
        )
        if isinstance(entity, User)
        else (
            f"tg://resolve?domain={entity.username}"
            if getattr(entity, "username", None)
            else ""
        )
    )


async def get_message_link(
    message: Message,
    chat: typing.Optional[typing.Union[Chat, Channel]] = None,
) -> str:
    """
    Get link to message
    :param message: Message to get link of
    :param chat: Chat, where message was sent
    :return: Link to message
    """
    if message.is_private:
        return (
            f"tg://openmessage?user_id={get_chat_id(message)}&message_id={message.id}"
        )

    if not chat:
        chat = await message.get_chat()

    return (
        f"https://t.me/{chat.username}/{message.id}"
        if getattr(chat, "username", False)
        else f"https://t.me/c/{chat.id}/{message.id}"
    )


def remove_html(text: str, escape: bool = False, keep_emojis: bool = False) -> str:
    """
    Removes HTML tags from text
    :param text: Text to remove HTML from
    :param escape: Escape HTML
    :param keep_emojis: Keep custom emojis
    :return: Text without HTML
    """
    return (escape_html if escape else str)(
        re.sub(
            r"(<\/?a.*?>|<\/?b>|<\/?i>|<\/?u>|<\/?strong>|<\/?em>|<\/?code>|<\/?strike>|<\/?del>|<\/?pre.*?>)"
            if keep_emojis
            else r"(<\/?a.*?>|<\/?b>|<\/?i>|<\/?u>|<\/?strong>|<\/?em>|<\/?code>|<\/?strike>|<\/?del>|<\/?pre.*?>|<\/?emoji.*?>)",
            "",
            text,
        )
    )


def get_kwargs() -> typing.Dict[str, typing.Any]:
    """
    Get kwargs of function, in which is called
    :return: kwargs
    """
    # https://stackoverflow.com/a/65927265/19170642
    keys, _, _, values = inspect.getargvalues(inspect.currentframe().f_back)
    return {key: values[key] for key in keys if key != "self"}


def mime_type(message: Message) -> str:
    """
    Get mime type of document in message
    :param message: Message with document
    :return: Mime type or empty string if not present
    """
    return (
        ""
        if not isinstance(message, Message) or not getattr(message, "media", False)
        else getattr(getattr(message, "media", False), "mime_type", False) or ""
    )


def find_caller(
    stack: typing.Optional[typing.List[inspect.FrameInfo]] = None,
) -> typing.Any:
    """
    Attempts to find command in stack
    :param stack: Stack to search in
    :return: Command-caller or None
    """
    caller = next(
        (
            frame_info
            for frame_info in stack or inspect.stack()
            if hasattr(frame_info, "function")
            and any(
                inspect.isclass(cls_)
                and issubclass(cls_, Module)
                and cls_ is not Module
                for cls_ in frame_info.frame.f_globals.values()
            )
        ),
        None,
    )

    return (
        next(
            (
                getattr(cls_, caller.function, None)
                for cls_ in caller.frame.f_globals.values()
                if inspect.isclass(cls_) and issubclass(cls_, Module)
            ),
            None,
        )
        if caller
        else next(
            (
                frame_info.frame.f_locals["func"]
                for frame_info in stack or inspect.stack()
                if hasattr(frame_info, "function")
                and frame_info.function == "future_dispatcher"
                and (
                    "CommandDispatcher"
                    in getattr(
                        getattr(frame_info, "frame", None), "f_globals", {}
                    )
                )
            ),
            None,
        )
    )


def validate_html(html: str) -> str:
    """
    Removes broken tags from html
    :param html: HTML to validate
    :return: Valid HTML
    """
    text, entities = telethon.extensions.html.parse(html)
    return telethon.extensions.html.unparse(escape_html(text), entities)


def iter_attrs(obj: typing.Any, /) -> typing.Iterator[typing.Tuple[str, typing.Any]]:
    """
    Iterates over attributes of object
    :param obj: Object to iterate over
    :return: Iterator of attributes and their values
    """
    return ((attr, getattr(obj, attr)) for attr in dir(obj))


init_ts = time.perf_counter()


# GeekTG Compatibility
def get_git_info() -> typing.Tuple[str, str]:
    """
    Get git info
    :return: Git info
    """
    hash_ = get_git_hash()
    return (
        hash_,
        f"https://github.com/hikariatama/Hikka/commit/{hash_}" if hash_ else "",
    )


def get_version_raw() -> str:
    """
    Get the version of the userbot
    :return: Version in format %s.%s.%s
    """
    from . import version

    return ".".join(map(str, list(version.__version__)))


get_platform_name = get_named_platform
