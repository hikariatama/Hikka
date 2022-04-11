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

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import functools
import io
import logging
import os
import shlex
import time
from datetime import timedelta
import telethon
from telethon.tl.custom.message import Message
from telethon.tl.types import (
    PeerUser,
    PeerChat,
    PeerChannel,
    User,
    MessageMediaWebPage,
    Channel,
    InputPeerNotifySettings,
    MessageEntityMentionName,
)

import grapheme

from telethon.hints import Entity

from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.functions.account import UpdateNotifySettingsRequest

from aiogram.types import CallbackQuery

from .inline.types import InlineCall

import random

from typing import Tuple, Union, List, Any

import re

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


def get_args(message: Message) -> List[str]:
    """Get arguments from message (str or Message), return list of arguments"""
    try:
        message = message.message
    except AttributeError:
        pass

    if not message:
        return False

    message = message.split(maxsplit=1)

    if len(message) <= 1:
        return []

    message = message[1]

    try:
        split = shlex.split(message)
    except ValueError:
        return message  # Cannot split, let's assume that it's just one long message

    return list(filter(lambda x: len(x) > 0, split))


def get_args_raw(message: Message) -> str:
    """Get the parameters to the command as a raw string (not split)"""
    try:
        message = message.message
    except AttributeError:
        pass

    if not message:
        return False

    args = message.split(maxsplit=1)

    if len(args) > 1:
        return args[1]

    return ""


def get_args_split_by(message: Message, separator: str) -> List[str]:
    """Split args with a specific separator"""
    raw = get_args_raw(message)
    mess = raw.split(separator)

    return [section.strip() for section in mess if section]


def get_chat_id(message: Message) -> int:
    """Get the chat ID, but without -100 if its a channel"""
    return telethon.utils.resolve_id(message.chat_id)[0]


def get_entity_id(entity: Entity) -> int:

    return telethon.utils.get_peer_id(entity)


def escape_html(text: str, /) -> str:
    """Pass all untrusted/potentially corrupt input here"""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_quotes(text: str, /) -> str:
    """Escape quotes to html quotes"""
    return escape_html(text).replace('"', "&quot;")


def get_base_dir() -> str:
    """Get directory of this file"""
    from . import __main__

    return get_dir(__main__.__file__)


def get_dir(mod: str) -> str:
    """Get directory of given module"""
    return os.path.abspath(os.path.dirname(os.path.abspath(mod)))


async def get_user(message: Message) -> Union[None, User]:
    """Get user who sent message, searching if not found easily"""
    try:
        return await message.client.get_entity(message.sender_id)
    except ValueError:  # Not in database. Lets go looking for them.
        logging.debug("user not in session cache. searching...")

    if isinstance(message.peer_id, PeerUser):
        try:
            await message.client.get_dialogs()
        except telethon.rpcerrorlist.BotMethodInvalid:
            return None

        return await message.client.get_entity(message.sender_id)

    if isinstance(message.peer_id, (PeerChannel, PeerChat)):
        try:
            return await message.client.get_entity(message.sender_id)
        except Exception:
            pass

        async for user in message.client.iter_participants(
            message.peer_id,
            aggressive=True,
        ):
            if user.id == message.sender_id:
                return user

        logging.error("User isn't in the group where they sent the message")
        return None

    logging.error("`peer_id` is not a user, chat or channel")
    return None


def run_sync(func, *args, **kwargs):
    """Run a non-async function in a new thread and return an awaitable"""
    # Returning a coro
    return asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(func, *args, **kwargs),
    )


def run_async(loop, coro):
    """Run an async function as a non-async function, blocking till it's done"""
    # When we bump minimum support to 3.7, use run()
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def censor(
    obj,
    to_censor=None,
    replace_with="redacted_{count}_chars",
):
    """May modify the original object, but don't rely on it"""
    if to_censor is None:
        to_censor = ["phone"]

    for k, v in vars(obj).items():
        if k in to_censor:
            setattr(obj, k, replace_with.format(count=len(v)))
        elif k[0] != "_" and hasattr(v, "__dict__"):
            setattr(obj, k, censor(v, to_censor, replace_with))

    return obj


def relocate_entities(
    entities: list,
    offset: int,
    text: Union[str, None] = None,
) -> list:
    """Move all entities by offset (truncating at text)"""
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
    message: Union[Message, CallbackQuery],
    response: str,
    **kwargs,
) -> list:
    """Use this to give the response to a command"""
    if isinstance(message, (CallbackQuery, InlineCall)):
        return await message.edit(response)

    if isinstance(message, list):
        delete_job = asyncio.ensure_future(
            message[0].client.delete_messages(
                message[0].input_chat,
                message[1:],
            )
        )
        message = message[0]
    else:
        delete_job = None

    kwargs.setdefault("link_preview", False)

    edit = message.out

    if not edit:
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
        text, entity = parse_mode.parse(response)

        if len(text) >= 4096:
            try:
                list_ = await message.client.loader.inline.list(
                    message=message,
                    strings=list(smart_split(text, entity, 4096)),
                )

                if not message.client.loader.inline.init_complete or not list_:
                    raise

                return [list_]
            except Exception:
                file = io.BytesIO(text.encode("utf-8"))
                file.name = "command_result.txt"

                result = [
                    await message.client.send_file(
                        message.peer_id,
                        file,
                        caption="<b>📤 Command output seems to be too long, so it's sent in file.</b>",
                    ),
                ]

                if message.out:
                    await message.delete()

                return result

        result = [
            await (message.edit if edit else message.respond)(
                text, parse_mode=lambda t: (t, entity), **kwargs
            )
        ]
    elif isinstance(response, Message):
        if message.media is None and (
            response.media is None or isinstance(response.media, MessageMediaWebPage)
        ):
            result = (
                await message.edit(
                    response.message,
                    parse_mode=lambda t: (t, response.entities or []),
                    link_preview=isinstance(response.media, MessageMediaWebPage),
                ),
            )
        else:
            result = (await message.respond(response, **kwargs),)
    else:
        if isinstance(response, bytes):
            response = io.BytesIO(response)

        if isinstance(response, str):
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
            result = (
                await message.client.send_file(message.chat_id, response, **kwargs),
            )

    if delete_job:
        await delete_job

    return result


async def get_target(message: Message, arg_no: int = 0) -> Union[int, None]:
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


def merge(a: dict, b: dict) -> dict:
    """Merge with replace dictionary a to dictionary b"""
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


async def asset_channel(
    client: "TelegramClient",  # noqa: F821
    title: str,
    description: str,
    *,
    silent: bool = False,
    archive: bool = False,
) -> Tuple[Channel, bool]:
    """
    Create new channel (if needed) and return its entity
    @client: Telegram client to create channel by
    @title: Channel title
    @description: Description
    @silent: Automatically mute channel
    @archive: Automatically archive channel
    Returns peer and bool: is channel new or pre-existent
    """
    async for d in client.iter_dialogs():
        if d.title == title:
            return d.entity, False

    peer = (
        await client(
            CreateChannelRequest(
                title,
                description,
                megagroup=True,
            )
        )
    ).chats[0]

    if silent:
        await dnd(client, peer, archive)

    return peer, True


async def dnd(
    client: "TelegramClient",  # noqa: F821
    peer: Entity,
    archive: bool = True,
) -> bool:
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
        logging.exception("utils.dnd error")
        return False

    return True


def get_link(user: Union[User, Channel], /) -> str:
    """Get telegram permalink to entity"""
    return (
        f"tg://user?id={user.id}"
        if isinstance(user, User)
        else (
            f"tg://resolve?domain={user.username}"
            if getattr(user, "username", None)
            else ""
        )
    )


def chunks(_list: Union[list, tuple, set], n: int, /) -> list:
    """Split provided `_list` into chunks of `n`"""
    return [_list[i : i + n] for i in range(0, len(_list), n)]


def get_named_platform() -> str:
    """Returns formatted platform name"""
    if os.path.isfile('/proc/device-tree/model'):
        with open('/proc/device-tree/model') as f:
            model = f.read()
            return f"🍇 {model}" if model.startswith("Raspberry") else f"❓ {model}"

    is_termux = bool(os.popen('echo $PREFIX | grep -o "com.termux"').read())

    is_okteto = "OKTETO" in os.environ
    is_lavhost = "LAVHOST" in os.environ

    if is_termux:
        return "🕶 Termux"

    if is_okteto:
        return "☁️ Okteto"

    if is_lavhost:
        return f"✌️ lavHost {os.environ['LAVHOST']}"

    return "📻 VDS"


def uptime() -> int:
    """Returns userbot uptime in seconds"""
    return round(time.perf_counter() - init_ts)


def formatted_uptime() -> str:
    """Returnes formmated uptime"""
    return "{}".format(str(timedelta(seconds=uptime())))


def ascii_face() -> str:
    """Returnes cute ASCII-art face"""
    return random.choice(
        [
            "ヽ(๑◠ܫ◠๑)ﾉ",
            "☜(⌒▽⌒)☞",
            "/|\\ ^._.^ /|\\",
            "(◕ᴥ◕ʋ)",
            "ᕙ(`▽´)ᕗ",
            "(☞ﾟ∀ﾟ)☞",
            "(✿◠‿◠)",
            "(▰˘◡˘▰)",
            "(˵ ͡° ͜ʖ ͡°˵)",
            "ʕっ•ᴥ•ʔっ",
            "( ͡° ᴥ ͡°)",
            "ʕ♥ᴥ♥ʔ",
            "\\m/,(> . <)_\\m/",
            "(๑•́ ヮ •̀๑)",
            "٩(^‿^)۶",
            "(っˆڡˆς)",
            "ψ(｀∇´)ψ",
            "⊙ω⊙",
            "٩(^ᴗ^)۶",
            "(´・ω・)っ由",
            "※\\(^o^)/※",
            "٩(*❛⊰❛)～❤",
            "( ͡~ ͜ʖ ͡°)",
            "✧♡(◕‿◕✿)",
            "โ๏௰๏ใ ื",
            "∩｡• ᵕ •｡∩ ♡",
            "(♡´౪`♡)",
            "(◍＞◡＜◍)⋈。✧♡",
            "♥(ˆ⌣ˆԅ)",
            "╰(✿´⌣`✿)╯♡",
            "ʕ•ᴥ•ʔ",
            "ᶘ ◕ᴥ◕ᶅ",
            "▼・ᴥ・▼",
            "【≽ܫ≼】",
            "ฅ^•ﻌ•^ฅ",
            "(΄◞ิ౪◟ิ‵)",
        ]
    )


def array_sum(array: List[Any], /) -> List[Any]:
    """Performs basic sum operation on array"""
    result = []
    for item in array:
        result += item

    return result


def rand(size: int, /) -> str:
    """Return random string of len `size`"""
    return "".join(
        [random.choice("abcdefghijklmnopqrstuvwxyz1234567890") for _ in range(size)]
    )


def smart_split(text, entities, length=4096, split_on=("\n", " "), min_length=1):
    """
    Split the message into smaller messages.
    A grapheme will never be broken. Entities will be displaced to match the right location. No inputs will be mutated.
    The end of each message except the last one is stripped of characters from [split_on]
    :param text: the plain text input
    :param entities: the entities
    :param length: the maximum length of a single message
    :param split_on: characters (or strings) which are preferred for a message break
    :param min_length: ignore any matches on [split_on] strings before this number of characters into each message
    :return:
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
        assert split_index > text_offset
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
            else:
                assert entity.length <= exclude
                # ignore entity in whitespace
        current_text = text[text_offset:split_index]
        yield parser.unparse(
            current_text,
            list(sorted(current_entities, key=lambda x: x.offset)),
        )
        text_offset = split_index + exclude
        bytes_offset += len(current_text.encode("utf-16le"))
        assert bytes_offset % 2 == 0


def _copy_tl(o, **kwargs):
    d = o.to_dict()
    del d["_"]
    d.update(kwargs)
    return o.__class__(**d)


init_ts = time.perf_counter()
