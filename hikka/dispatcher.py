"""Obviously, dispatches stuff"""

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2022 The Authors

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
import collections
import copy
import inspect
import logging
import re
import traceback
from typing import Tuple, Union

from telethon import types
from telethon.tl.types import Message

from . import main, security, utils
from .database import Database
from .loader import Modules

# Keys for layout switch
ru_keys = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'
en_keys = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
ALL_TAGS = [
    "no_commands",
    "only_commands",
    "out",
    "in",
    "only_messages",
    "editable",
    "no_media",
    "only_media",
    "only_photos",
    "only_videos",
    "only_audios",
    "only_stickers",
    "only_docs",
    "only_inline",
    "only_channels",
    "only_groups",
    "only_pm",
    "startswith",
    "endswith",
    "contains",
    "func",
    "from_id",
    "chat_id",
    "regex",
]


def _decrement_ratelimit(delay, data, key, severity):
    def inner():
        data[key] = max(0, data[key] - severity)

    asyncio.get_event_loop().call_later(delay, inner)


class CommandDispatcher:
    def __init__(self, modules: Modules, db: Database, no_nickname: bool = False):
        self._modules = modules
        self._db = db
        self.security = security.SecurityManager(db)
        self.no_nickname = no_nickname
        self._ratelimit_storage_user = collections.defaultdict(int)
        self._ratelimit_storage_chat = collections.defaultdict(int)
        self._ratelimit_max_user = db.get(__name__, "ratelimit_max_user", 30)
        self._ratelimit_max_chat = db.get(__name__, "ratelimit_max_chat", 100)
        self.check_security = self.security.check

    async def init(self, client: "TelegramClient"):  # type: ignore
        await self.security.init(client)
        me = await client.get_me()

        self.client = client  # Intended to be used to track user in logging

        self._me = me.id
        self._cached_username = me.username.lower() if me.username else str(me.id)

    async def _handle_ratelimit(self, message: Message, func: callable) -> bool:
        if await self.security.check(
            message,
            security.OWNER | security.SUDO | security.SUPPORT,
        ):
            return True

        func = getattr(func, "__func__", func)
        ret = True
        chat = self._ratelimit_storage_chat[message.chat_id]

        if message.sender_id:
            user = self._ratelimit_storage_user[message.sender_id]
            severity = (5 if getattr(func, "ratelimit", False) else 2) * (
                (user + chat) // 30 + 1
            )
            user += severity
            self._ratelimit_storage_user[message.sender_id] = user
            if user > self._ratelimit_max_user:
                ret = False
            else:
                self._ratelimit_storage_chat[message.chat_id] = chat

            _decrement_ratelimit(
                self._ratelimit_max_user * severity,
                self._ratelimit_storage_user,
                message.sender_id,
                severity,
            )
        else:
            severity = (5 if getattr(func, "ratelimit", False) else 2) * (
                chat // 15 + 1
            )

        chat += severity

        if chat > self._ratelimit_max_chat:
            ret = False

        _decrement_ratelimit(
            self._ratelimit_max_chat * severity,
            self._ratelimit_storage_chat,
            message.chat_id,
            severity,
        )

        return ret

    def _handle_grep(self, message: Message) -> Message:
        # Allow escaping grep with double stick
        if "||grep" in message.text or "|| grep" in message.text:
            message.raw_text = re.sub(r"\|\| ?grep", "| grep", message.raw_text)
            message.text = re.sub(r"\|\| ?grep", "| grep", message.text)
            message.message = re.sub(r"\|\| ?grep", "| grep", message.message)
            return message

        grep = False
        if not re.search(r".+\| ?grep (.+)", message.raw_text):
            return message

        grep = re.search(r".+\| ?grep (.+)", message.raw_text).group(1)
        message.text = re.sub(r"\| ?grep.+", "", message.text)
        message.raw_text = re.sub(r"\| ?grep.+", "", message.raw_text)
        message.message = re.sub(r"\| ?grep.+", "", message.message)

        ungrep = False

        if re.search(r"-v (.+)", grep):
            ungrep = re.search(r"-v (.+)", grep).group(1)
            grep = re.sub(r"(.+) -v .+", r"\g<1>", grep)

        grep = utils.escape_html(grep).strip() if grep else False
        ungrep = utils.escape_html(ungrep).strip() if ungrep else False

        old_edit = message.edit
        old_reply = message.reply
        old_respond = message.respond

        def process_text(text: str) -> str:
            nonlocal grep, ungrep
            res = []

            for line in text.split("\n"):
                if (
                    grep
                    and grep in utils.remove_html(line)
                    and (not ungrep or ungrep not in utils.remove_html(line))
                ):
                    res.append(
                        utils.remove_html(line, escape=True).replace(
                            grep, f"<u>{grep}</u>"
                        )
                    )

                if not grep and ungrep and ungrep not in utils.remove_html(line):
                    res.append(utils.remove_html(line, escape=True))

            cont = (
                (f"contain <b>{grep}</b>" if grep else "")
                + (" and" if grep and ungrep else "")
                + ((" do not contain <b>" + ungrep + "</b>") if ungrep else "")
            )

            if res:
                text = f"<i>💬 Lines that {cont}:</i>\n" + "\n".join(res)
            else:
                text = f"💬 <i>No lines that {cont}</i>"

            return text

        async def my_edit(text, *args, **kwargs):
            text = process_text(text)
            kwargs["parse_mode"] = "HTML"
            return await old_edit(text, *args, **kwargs)

        async def my_reply(text, *args, **kwargs):
            text = process_text(text)
            kwargs["parse_mode"] = "HTML"
            return await old_reply(text, *args, **kwargs)

        async def my_respond(text, *args, **kwargs):
            text = process_text(text)
            kwargs["parse_mode"] = "HTML"
            return await old_respond(text, *args, **kwargs)

        message.edit = my_edit
        message.reply = my_reply
        message.respond = my_respond

        return message

    async def _handle_command(
        self,
        event,
        watcher: bool = False,
    ) -> Union[bool, Tuple[Message, str, str, callable]]:
        if not hasattr(event, "message") or not hasattr(event.message, "message"):
            return False

        prefix = self._db.get(main.__name__, "command_prefix", False) or "."
        change = str.maketrans(ru_keys + en_keys, en_keys + ru_keys)
        message = utils.censor(event.message)

        if not event.message.message:
            return False

        if (
            event.message.message.startswith(str.translate(prefix, change))
            and str.translate(prefix, change) != prefix
        ):
            message.message = str.translate(message.message, change)
            message.text = str.translate(message.text, change)
        elif not event.message.message.startswith(prefix):
            return False

        if (
            event.sticker
            or event.dice
            or event.audio
            or event.via_bot_id
            or getattr(event, "reactions", False)
        ):
            return False

        blacklist_chats = self._db.get(main.__name__, "blacklist_chats", [])
        whitelist_chats = self._db.get(main.__name__, "whitelist_chats", [])
        whitelist_modules = self._db.get(main.__name__, "whitelist_modules", [])

        if utils.get_chat_id(message) in blacklist_chats or (
            whitelist_chats and utils.get_chat_id(message) not in whitelist_chats
        ):
            return False

        if (
            message.out
            and len(message.message) > 2
            and message.message.startswith(prefix * 2)
            and any(s != prefix for s in message.message)
        ):
            # Allow escaping commands using .'s
            if not watcher:
                await message.edit(
                    message.message[1:],
                    parse_mode=lambda s: (
                        s,
                        utils.relocate_entities(message.entities, -1, message.message)
                        or (),
                    ),
                )
            return False

        if not message.message or len(message.message) == 1:
            return False  # Message is just the prefix

        initiator = getattr(event, "sender_id", 0)

        command = message.message[1:].strip().split(maxsplit=1)[0]
        tag = command.split("@", maxsplit=1)

        if len(tag) == 2:
            if tag[1] == "me":
                if not message.out:
                    return False
            elif tag[1].lower() != self._cached_username:
                return False
        elif (
            event.out
            or event.mentioned
            and event.message is not None
            and event.message.message is not None
            and f"@{self._cached_username}" not in command.lower()
        ):
            pass
        elif (
            not event.is_private
            and not self.no_nickname
            and not self._db.get(main.__name__, "no_nickname", False)
            and command not in self._db.get(main.__name__, "nonickcmds", [])
            and initiator not in self._db.get(main.__name__, "nonickusers", [])
            and utils.get_chat_id(event)
            not in self._db.get(main.__name__, "nonickchats", [])
        ):
            return False

        txt, func = self._modules.dispatch(tag[0])

        if (
            not func
            or not await self._handle_ratelimit(message, func)
            or not await self.security.check(message, func)
        ):
            return False

        if (
            message.is_channel
            and message.is_group
            and message.chat.title.startswith("hikka-")
            and message.chat.title != "hikka-logs"
        ):
            if not watcher:
                logging.warning("Ignoring message in datachat \\ logging chat")
            return False

        message.message = prefix + txt + message.message[len(prefix + command) :]

        if (
            f"{str(utils.get_chat_id(message))}.{func.__self__.__module__}"
            in blacklist_chats
            or whitelist_modules
            and f"{utils.get_chat_id(message)}.{func.__self__.__module__}"
            not in whitelist_modules
        ):
            return False

        if await self._handle_tags(event, func):
            return False

        if self._db.get(main.__name__, "grep", False) and not watcher:
            message = self._handle_grep(message)

        return message, prefix, txt, func

    async def handle_command(self, event: Message):
        """Handle all commands"""
        message = await self._handle_command(event)
        if not message:
            return

        message, _, _, func = message

        asyncio.ensure_future(
            self.future_dispatcher(
                func,
                message,
                self.command_exc,
            )
        )

    async def command_exc(self, e, message: Message):
        logging.exception("Command failed", extra={"stack": inspect.stack()})
        if not self._db.get(main.__name__, "inlinelogs", True):
            try:
                txt = (
                    "<b>🚫 Call</b>"
                    f" <code>{utils.escape_html(message.message)}</code><b>"
                    " failed!</b>"
                )
                await (message.edit if message.out else message.reply)(txt)
            except Exception:
                pass
            return

        try:
            exc = traceback.format_exc()
            # Remove `Traceback (most recent call last):`
            exc = "\n".join(exc.splitlines()[1:])
            txt = (
                "<b>🚫 Call</b>"
                f" <code>{utils.escape_html(message.message)}</code><b>"
                f" failed!</b>\n\n<b>🧾 Logs:</b>\n<code>{utils.escape_html(exc)}</code>"
            )
            await (message.edit if message.out else message.reply)(txt)
        except Exception:
            pass

    async def watcher_exc(self, e, message: Message):
        logging.exception("Error running watcher", extra={"stack": inspect.stack()})

    async def _handle_tags(self, event, func: callable) -> bool:
        message = getattr(event, "message", event)
        return (
            (
                getattr(func, "no_commands", False)
                and await self._handle_command(event, watcher=True)
            )
            or (
                getattr(func, "only_commands", False)
                and not await self._handle_command(event, watcher=True)
            )
            or (getattr(func, "out", False) and not getattr(message, "out", True))
            or (getattr(func, "in", False) and getattr(message, "out", True))
            or (
                getattr(func, "only_messages", False)
                and not isinstance(message, types.Message)
            )
            or (
                getattr(func, "editable", False)
                and (
                    getattr(message, "fwd_from", False)
                    or not getattr(message, "out", False)
                    or getattr(message, "sticker", False)
                    or getattr(message, "via_bot_id", False)
                )
            )
            or (
                getattr(func, "no_media", False)
                and isinstance(message, types.Message)
                and getattr(message, "media", False)
            )
            or (
                getattr(func, "only_media", False)
                and (
                    not isinstance(message, types.Message)
                    or not getattr(message, "media", False)
                )
            )
            or (
                getattr(func, "only_photos", False)
                and not utils.mime_type(message).startswith("image/")
            )
            or (
                getattr(func, "only_videos", False)
                and not utils.mime_type(message).startswith("video/")
            )
            or (
                getattr(func, "only_audios", False)
                and not utils.mime_type(message).startswith("audio/")
            )
            or (
                getattr(func, "only_stickers", False)
                and not getattr(message, "sticker", False)
            )
            or (
                getattr(func, "only_docs", False)
                and not getattr(message, "document", False)
            )
            or (
                getattr(func, "only_inline", False)
                and not getattr(message, "via_bot_id", False)
            )
            or (
                getattr(func, "only_channels", False)
                and (
                    not getattr(message, "is_channel", False)
                    and getattr(message, "is_group", False)
                    or getattr(message, "is_private", False)
                )
            )
            or (
                getattr(func, "only_groups", False)
                and not getattr(message, "is_group", False)
            )
            or (
                getattr(func, "only_pm", False)
                and not getattr(message, "is_private", False)
            )
            or (
                getattr(func, "startswith", False)
                and (
                    not isinstance(message, Message)
                    or isinstance(func.startswith, str)
                    and not message.raw_text.startswith(
                        getattr(func, "startswith")
                    )
                )
            )
            or (
                getattr(func, "endswith", False)
                and (
                    not isinstance(message, Message)
                    or isinstance(func.endswith, str)
                    and not message.raw_text.endswith(getattr(func, "endswith"))
                )
            )
            or (
                getattr(func, "contains", False)
                and (
                    not isinstance(message, Message)
                    or isinstance(func.contains, str)
                    and getattr(func, "contains") not in message.raw_text
                )
            )
            or (
                getattr(func, "func", False)
                and callable(func.func)
                and not func.func(message)
            )
            or (
                getattr(func, "from_id", False)
                and getattr(message, "sender_id", None) != func.from_id
            )
            or getattr(func, "chat_id", False)
            and utils.get_chat_id(message)
            != (
                int(str(func.chat_id)[4:])
                if str(func.chat_id).startswith("-100")
                else func.chat_id
            )
            or (
                getattr(func, "regex", False)
                and (
                    not isinstance(message, Message)
                    or not re.search(func.regex, message.raw_text)
                )
            )
        )

    async def handle_incoming(self, event):
        """Handle all incoming messages"""
        message = utils.censor(getattr(event, "message", event))

        blacklist_chats = self._db.get(main.__name__, "blacklist_chats", [])
        whitelist_chats = self._db.get(main.__name__, "whitelist_chats", [])
        whitelist_modules = self._db.get(main.__name__, "whitelist_modules", [])

        if utils.get_chat_id(message) in blacklist_chats or (
            whitelist_chats and utils.get_chat_id(message) not in whitelist_chats
        ):
            logging.debug("Message is blacklisted")
            return

        for func in self._modules.watchers:
            bl = self._db.get(main.__name__, "disabled_watchers", {})
            modname = str(func.__self__.__class__.strings["name"])

            if (
                modname in bl
                and isinstance(message, types.Message)
                and (
                    "*" in bl[modname]
                    or utils.get_chat_id(message) in bl[modname]
                    or "only_chats" in bl[modname]
                    and message.is_private
                    or "only_pm" in bl[modname]
                    and not message.is_private
                    or "out" in bl[modname]
                    and not message.out
                    or "in" in bl[modname]
                    and message.out
                )
                or f"{str(utils.get_chat_id(message))}.{func.__self__.__module__}"
                in blacklist_chats
                or whitelist_modules
                and f"{str(utils.get_chat_id(message))}.{func.__self__.__module__}"
                not in whitelist_modules
                or await self._handle_tags(event, func)
            ):
                tags = ", ".join(
                    f"{tag}={getattr(func, tag, None)}" for tag in ALL_TAGS
                )
                logging.debug(f"Ignored watcher of module {modname} {tags}")
                continue

            # Avoid weird AttributeErrors in weird dochub modules by settings placeholder
            # of attributes
            for placeholder in {"text", "raw_text"}:
                try:
                    if not hasattr(message, placeholder):
                        setattr(message, placeholder, "")
                except UnicodeDecodeError:
                    pass

            # Run watcher via ensure_future so in case user has a lot
            # of watchers with long actions, they can run simultaneously
            asyncio.ensure_future(
                self.future_dispatcher(
                    func,
                    message,
                    self.watcher_exc,
                )
            )

    async def future_dispatcher(
        self,
        func: callable,
        message: Message,
        exception_handler: callable,
        *args,
    ):
        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)  # skipcq
        try:
            await func(message)
        except BaseException as e:
            await exception_handler(e, message, *args)
