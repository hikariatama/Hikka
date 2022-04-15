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
import collections
import logging
import re
from telethon import types
import traceback
from telethon.tl.types import Message
from typing import Union, Tuple
from types import FunctionType

from . import utils, main, security

# Keys for layout switch
ru_keys = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'
en_keys = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"


def _decrement_ratelimit(delay, data, key, severity):
    def inner():
        data[key] = max(0, data[key] - severity)

    asyncio.get_event_loop().call_later(delay, inner)


class CommandDispatcher:
    def __init__(self, modules, db, no_nickname=False):
        self._modules = modules
        self._db = db
        self.security = security.SecurityManager(db)
        self.no_nickname = no_nickname
        self._ratelimit_storage_user = collections.defaultdict(int)
        self._ratelimit_storage_chat = collections.defaultdict(int)
        self._ratelimit_max_user = db.get(__name__, "ratelimit_max_user", 30)
        self._ratelimit_max_chat = db.get(__name__, "ratelimit_max_chat", 100)
        self.check_security = self.security.check

    async def init(self, client):
        await self.security.init(client)
        me = await client.get_me()
        self._me = me.id
        self._cached_username = me.username.lower() if me.username else str(me.id)

    async def _handle_ratelimit(self, message, func):
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
                    and grep in re.sub("<.*?>", "", line)
                    and (not ungrep or ungrep not in re.sub("<.*?>", "", line))
                ):
                    res.append(line.replace(grep, f"<u>{grep}</u>"))

                if not grep and ungrep and ungrep not in re.sub("<.*?>", "", line):
                    res.append(line)

            cont = (
                (f"contain <b>{grep}</b>" if grep else "")
                + (" and" if grep and ungrep else "")
                + ((" do not contain <b>" + ungrep + "</b>") if ungrep else "")
            )

            if res:
                text = f"<i>💬 Lines that {cont}:</i>\n" + ("\n".join(res))
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
    ) -> Union[bool, Tuple[Message, str, str, FunctionType]]:
        if not hasattr(event, "message") or not hasattr(event.message, "message"):
            return False

        prefix = self._db.get(main.__name__, "command_prefix", False) or "."
        if isinstance(prefix, list):
            prefix = prefix[0]
            self._db.set(main.__name__, "command_prefix", prefix)

        if len(prefix) != 1:
            prefix = "."
            self._db.set(main.__name__, "command_prefix", prefix)
            logging.warning("Prefix has been reset to a default one («.»)")

        change = str.maketrans(ru_keys + en_keys, en_keys + ru_keys)
        message = utils.censor(event.message)

        if event.message.message.startswith(prefix):
            pass
        elif event.message.message.startswith(str.translate(prefix, change)):
            prefix = str.translate(prefix, change)
            message.message = str.translate(message.message, change)
        else:
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
            and len(message.message) > len(prefix)
            and message.message[: len(prefix) * 2] == prefix * 2
            and message.message != len(message.message) // len(prefix) * prefix
        ):
            # Allow escaping commands using .'s
            entities = utils.relocate_entities(
                message.entities,
                -len(prefix),
                message.message,
            )

            await message.edit(
                message.message[len(prefix) :],
                parse_mode=lambda s: (s, entities or ()),
            )
            return False

        message.message = message.message[len(prefix) :]

        if not message.message:
            return False  # Message is just the prefix

        utils.relocate_entities(message.entities, -len(prefix))

        try:
            initiator = event.sender_id
        except Exception:
            initiator = 0

        command = message.message.split(maxsplit=1)[0]
        tag = command.split("@", maxsplit=1)

        if len(tag) == 2:
            if tag[1] == "me":
                if not message.out:
                    return False
            elif tag[1].lower() != self._cached_username:
                return False
        elif (
            event.mentioned
            and event.message is not None
            and event.message.message is not None
            and f"@{self._cached_username}" not in event.message.message
        ):
            pass
        elif (
            not event.is_private
            and not self.no_nickname
            and not event.out
            and not self._db.get(main.__name__, "no_nickname", False)
            and command not in self._db.get(main.__name__, "nonickcmds", [])
            and initiator not in self._db.get(main.__name__, "nonickusers", [])
            and utils.get_chat_id(event) not in self._db.get(main.__name__, "nonickchats", [])
        ):
            logging.debug("Ignoring message without nickname")
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
            logging.warning("Ignoring message in datachat \\ logging chat")
            return False

        message.message = txt + message.message[len(command) :]

        if (
            f"{str(utils.get_chat_id(message))}.{func.__self__.__module__}"
            in blacklist_chats
        ):
            logging.debug("Command is blacklisted in chat")
            return False

        if (
            whitelist_modules
            and f"{utils.get_chat_id(message)}.{func.__self__.__module__}"
            not in whitelist_modules
        ):
            logging.debug("Command is not whitelisted in chat")
            return False

        if self._db.get(main.__name__, "grep", False):
            message = self._handle_grep(message)

        return message, prefix, txt, func

    async def handle_command(self, event: Message) -> None:
        """Handle all commands"""
        message = await self._handle_command(event)
        if not message:
            return

        message, prefix, _, func = message

        asyncio.ensure_future(
            self.future_dispatcher(
                func,
                message,
                self.command_exc,
                prefix,
            )
        )

    async def command_exc(self, e, message, prefix):
        logging.exception("Command failed")
        if not self._db.get(main.__name__, "inlinelogs", True):
            try:
                txt = f"<b>🚫 Command</b> <code>{utils.escape_html(prefix)}{utils.escape_html(message.message)}</code><b> failed!</b>"
                await (message.edit if message.out else message.reply)(txt)
            except Exception:
                pass
            return

        try:
            exc = traceback.format_exc()
            # Remove `Traceback (most recent call last):`
            exc = "\n".join(exc.splitlines()[1:])
            txt = (
                f"<b>🚫 Command</b> <code>{utils.escape_html(prefix)}{utils.escape_html(message.message)}</code><b> failed!</b>\n\n"
                f"<b>⛑ Traceback:</b>\n<code>{exc}</code>"
            )
            await (message.edit if message.out else message.reply)(txt)
        except Exception:
            pass

    async def watcher_exc(self, e, message) -> None:
        logging.exception("Error running watcher")

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
                or (
                    whitelist_modules
                    and (
                        f"{str(utils.get_chat_id(message))}." + func.__self__.__module__
                    )
                    not in whitelist_modules
                )
            ):
                logging.debug(f"Ignored watcher of module {modname}")
                continue

            # Avoid weird AttributeErrors in weird dochub modules by settings placeholder
            # of attributes
            for placeholder in {"text", "raw_text"}:
                if not hasattr(event, placeholder):
                    setattr(event, placeholder, "")

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
        func: FunctionType,
        message: Message,
        exception_handler: FunctionType,
        *args,
    ) -> None:
        try:
            await func(message)
        except BaseException as e:
            await exception_handler(e, message, *args)
