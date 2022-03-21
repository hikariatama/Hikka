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

#    Modded by GeekTG Team

import asyncio
import collections
import logging
import re
from telethon import types
import traceback

from . import utils, main, security, loader

# Keys for layout switch
ru_keys = """ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГ
ШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ, """
en_keys = """`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{
}ASDFGHJKL:"|ZXCVBNM<>? """


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
            message, security.OWNER | security.SUDO | security.SUPPORT
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

    async def handle_command(self, event):
        """Handle all commands"""
        if not hasattr(event, "message") or not hasattr(event.message, "message"):
            return

        # Fix bug when after reacting message command gets executed
        if getattr(event, "reactions", False):
            return

        # Empty string evaluates to False, so the `or` activates
        prefix = self._db.get(main.__name__, "command_prefix", False) or "."
        if isinstance(prefix, list):
            prefix = prefix[0]
            self._db.set(main.__name__, "command_prefix", prefix)

        change = str.maketrans(ru_keys + en_keys, en_keys + ru_keys)

        if event.message.message.startswith(prefix):
            translated = False
        elif event.message.message.startswith(str.translate(prefix, change)):
            prefix = str.translate(prefix, change)
            translated = True
        else:
            return

        logging.debug("Incoming command!")

        if event.sticker or event.dice or event.audio:
            logging.debug("Ignoring invisible or potentially forwarded command.")
            return

        if event.via_bot_id:
            logging.debug("Ignoring inline bot.")
            return

        message = utils.censor(event.message)
        blacklist_chats = self._db.get(main.__name__, "blacklist_chats", [])
        whitelist_chats = self._db.get(main.__name__, "whitelist_chats", [])
        whitelist_modules = self._db.get(main.__name__, "whitelist_modules", [])

        if utils.get_chat_id(message) in blacklist_chats or (
            whitelist_chats and utils.get_chat_id(message) not in whitelist_chats
        ):
            logging.debug("Message is blacklisted")
            return

        if (
            message.out
            and len(message.message) > len(prefix)
            and message.message[: len(prefix) * 2] == prefix * 2
            and message.message != len(message.message) // len(prefix) * prefix
        ):
            # Allow escaping commands using .'s
            entities = utils.relocate_entities(
                message.entities, -len(prefix), message.message
            )
            await message.edit(
                message.message[len(prefix) :], parse_mode=lambda s: (s, entities or ())
            )
            return

        logging.debug(message)
        # Make sure we don't get confused about spaces or other stuff in the prefix
        message.message = message.message[len(prefix) :]

        if translated:
            message.message = str.translate(message.message, change)

        if not message.message:
            return  # Message is just the prefix

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
                    return
            elif tag[1].lower() != self._cached_username:
                return
        elif (
            event.mentioned
            and event.message is not None
            and event.message.message is not None
            and "@" + self._cached_username not in event.message.message
        ):
            pass
        elif (
            not event.is_private
            and not self.no_nickname
            and not event.out
            and not self._db.get(main.__name__, "no_nickname", False)
            and command not in self._db.get(main.__name__, "nonickcmds", [])
            and initiator not in self._db.get(main.__name__, "nonickusers", [])
        ):
            logging.debug("Ignoring message without nickname")
            return

        txt, func = self._modules.dispatch(tag[0])

        if func is not None:
            if not await self._handle_ratelimit(message, func):
                return

            if not await self.security.check(message, func):
                return

            if message.is_channel and message.is_group:
                my_id = (await message.client.get_me(True)).user_id
                chat = await message.get_chat()
                if (
                    chat.title.startswith(f"friendly-{my_id}-")
                    or chat.title == "geektg-log"
                ):
                    logging.warning("Ignoring message in datachat \\ logging chat")
                    return

            message.message = txt + message.message[len(command) :]

            if (
                str(utils.get_chat_id(message)) + "." + func.__self__.__module__
                in blacklist_chats
            ):
                logging.debug("Command is blacklisted in chat")
                return

            if (
                whitelist_modules
                and f"{utils.get_chat_id(message)}.{func.__self__.__module__}"
                not in whitelist_modules
            ):  # noqa
                logging.debug("Command is not whitelisted in chat")
                return

            if self._db.get(main.__name__, "grep", False):
                if "||grep" in message.text or "|| grep" in message.text:
                    message.raw_text = message.raw_text.replace(
                        "||grep", "|grep"
                    ).replace("|| grep", "| grep")
                    message.text = message.text.replace("||grep", "|grep").replace(
                        "|| grep", "| grep"
                    )
                    message.message = message.message.replace(
                        "||grep", "|grep"
                    ).replace("|| grep", "| grep")
                else:
                    grep = False
                    if "| grep" in message.text or "|grep" in message.text:
                        grep = message.text[message.text.find("grep ") + 5 :]
                        message.text = message.text[
                            : (
                                message.text.find(" | grep")
                                if message.text.find(" | grep") > 0
                                else message.text.find("|grep")
                            )
                        ]  # noqa

                    if grep:
                        ungrep = False

                        if "-v" in grep:
                            ungrep = grep[
                                grep.find("-v ")
                                + 3 : (
                                    grep.find("grep") if "grep" in grep else len(grep)
                                )
                            ]
                            grep = grep[: grep.find("-v")] + (
                                grep[grep.find("grep") + 4 :] if "grep" in grep else ""
                            )

                        grep = utils.escape_html(grep).strip() if grep else False
                        ungrep = utils.escape_html(ungrep).strip() if ungrep else False

                        old_edit = message.edit
                        old_reply = message.reply
                        old_respond = message.respond

                        def process_text(text):
                            nonlocal grep, ungrep
                            res = []

                            for line in text.split("\n"):
                                if (
                                    grep
                                    and grep in re.sub("<.*?>", "", line)
                                    and (
                                        not ungrep
                                        or ungrep not in re.sub("<.*?>", "", line)
                                    )
                                ):
                                    res.append(line.replace(grep, f"<u>{grep}</u>"))

                                if (
                                    not grep
                                    and ungrep
                                    and ungrep not in re.sub("<.*?>", "", line)
                                ):
                                    res.append(line)

                            cont = (
                                (f"contain <b>{grep}</b>" if grep else "")
                                + (" and" if grep and ungrep else "")
                                + (
                                    (" do not contain <b>" + ungrep + "</b>")
                                    if ungrep
                                    else ""
                                )
                            )

                            if res:
                                text = f"<i>💬 Lines that {cont}:</i>\n" + (
                                    "\n".join(res)
                                )
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

            # Feature for CommandsLogger module
            try:
                if getattr(loader, "mods", False):
                    for mod in loader.mods:
                        if mod.name == "CommandsLogger":
                            await mod.process_log(message)
            except Exception:
                pass

            try:
                await func(message)
            except Exception:
                logging.exception("Command failed")
                if not self._db.get(main.__name__, "inlinelogs", True):
                    try:
                        txt = f"<b>🚫 Command</b> <code>{prefix}{utils.escape_html(message.message)}</code><b> failed!</b>"
                        await (message.edit if message.out else message.reply)(txt)
                    except Exception:
                        pass
                else:
                    try:
                        exc = traceback.format_exc()
                        exc = "\n".join(
                            exc.split("\n")[1:]
                        )  # Remove `Traceback (most recent call last):`
                        txt = f"<b>🚫 Command</b> <code>{prefix}{utils.escape_html(message.message)}</code><b> failed!</b>\n\n<b>⛑ Traceback:</b>\n<code>{exc}</code>"
                        await (message.edit if message.out else message.reply)(txt)
                    except Exception:
                        pass

    async def handle_incoming(self, event):
        """Handle all incoming messages"""
        logging.debug("Incoming message!")
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
            ):
                logging.debug(f"Ignored watcher of module {modname}")
                continue

            if (
                f"{str(utils.get_chat_id(message))}.{func.__self__.__module__}"
                in blacklist_chats
            ):
                logging.debug("Command is blacklisted in chat")
                continue

            if (
                whitelist_modules
                and (f"{str(utils.get_chat_id(message))}." + func.__self__.__module__)
                not in whitelist_modules
            ):
                logging.debug("Command is not whitelisted in chat")
                continue

            try:
                await func(message)
            except Exception as e:
                logging.exception(f"Error running watcher {e}")
