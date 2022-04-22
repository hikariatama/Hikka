# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: inline

import time

import logging
from io import BytesIO

from .. import loader, utils, main

from typing import Union
from telethon.tl.types import Message

import aiogram
import inspect
import asyncio
import os

logger = logging.getLogger(__name__)
DEBUG_MODS_DIR = os.path.join(utils.get_base_dir(), "debug_modules")

if not os.path.isdir(DEBUG_MODS_DIR):
    os.mkdir(DEBUG_MODS_DIR, mode=0o755)

for mod in os.scandir(DEBUG_MODS_DIR):
    os.remove(mod.path)


@loader.tds
class TestMod(loader.Module):
    """Perform operations based on userbot self-testing"""

    _memory = {}

    strings = {
        "name": "Tester",
        "set_loglevel": "🚫 <b>Please specify verbosity as an integer or string</b>",
        "no_logs": "ℹ️ <b>You don't have any logs at verbosity {}.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": "🌘 <b>Hikka logs with verbosity </b><code>{}</code>\n\n👩‍🎤 <b>Hikka version: {}.{}.{}</b>{}\n⏱ <b>Uptime: {}</b>\n<b>{}</b>\n\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{} InlineLogs</b>",
        "suspend_invalid_time": "🚫 <b>Invalid time to suspend</b>",
        "suspended": "🥶 <b>Bot suspended for</b> <code>{}</code> <b>seconds</b>",
        "results_ping": "⏱ <b>Ping:</b> <code>{}</code> <b>ms</b>",
        "confidential": "⚠️ <b>Log level </b><code>{}</code><b> may reveal your confidential info, be careful</b>",
        "confidential_text": (
            "⚠️ <b>Log level </b><code>{0}</code><b> may reveal your confidential info, "
            "be careful</b>\n<b>Type </b><code>.logs {0} force_insecure</code><b> "
            "to ignore this warning</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Choose log level</b>",
        "database_unlocked": "🚫 DB eval unlocked",
        "database_locked": "✅ DB eval locked",
        "bad_module": "🚫 <b>Module not found</b>",
        "debugging_enabled": "🧑‍💻 <b>Debugging mode enabled for module </b><code>{0}</code>\n<i>Go to directory named `debug_modules`, edit file named `{0}.py` and see changes in real time</i>",
        "debugging_disabled": "✅ <b>Debugging disabled</b>",
    }

    @staticmethod
    async def dumpcmd(message: Message) -> None:
        """Use in reply to get a dump of a message"""
        if not message.is_reply:
            return

        await utils.answer(
            message,
            "<code>"
            + utils.escape_html((await message.get_reply_message()).stringify())
            + "</code>",
        )

    @staticmethod
    async def cancel(call: aiogram.types.CallbackQuery) -> None:
        await call.delete()

    async def watchdog(self) -> None:
        while True:
            try:
                for mod in os.scandir(DEBUG_MODS_DIR):
                    last_modified = os.stat(mod.path).st_mtime
                    cls_ = mod.path.split("/")[-1].split(".py")[0]

                    if cls_ not in self._memory:
                        self._memory[cls_] = last_modified
                        continue

                    if self._memory[cls_] == last_modified:
                        continue

                    self._memory[cls_] = last_modified
                    logger.debug(f"Reloading debug module {cls_}")
                    with open(mod.path, "r") as f:
                        try:
                            await next(
                                module
                                for module in self.allmodules.modules
                                if module.__class__.__name__ == "LoaderMod"
                            ).load_module(
                                f.read(),
                                None,
                                save_fs=False,
                            )
                        except Exception:
                            logger.exception("Failed to reload module in watchdog")
            except Exception:
                logger.exception("Failed debugging watchdog")
                return

            await asyncio.sleep(1)

    async def debugmodcmd(self, message: Message) -> None:
        """[module] - For developers: Open module for debugging
        You will be able to track changes in real-time"""
        args = utils.get_args_raw(message)
        instance = None
        for module in self.allmodules.modules:
            if (
                module.__class__.__name__.lower() == args.lower()
                or module.strings["name"].lower() == args.lower()
            ):
                if os.path.isfile(
                    os.path.join(
                        DEBUG_MODS_DIR,
                        f"{module.__class__.__name__}.py",
                    )
                ):
                    os.remove(
                        os.path.join(
                            DEBUG_MODS_DIR,
                            f"{module.__class__.__name__}.py",
                        )
                    )

                    try:
                        delattr(module, "hikka_debug")
                    except AttributeError:
                        pass

                    await utils.answer(message, self.strings("debugging_disabled"))
                    return

                module.hikka_debug = True
                instance = module
                break

        if not instance:
            await utils.answer(message, self.strings("bad_module"))
            return

        with open(
            os.path.join(
                DEBUG_MODS_DIR,
                f"{instance.__class__.__name__}.py",
            ),
            "wb",
        ) as f:
            f.write(inspect.getmodule(instance).__loader__.data)

        await utils.answer(
            message,
            self.strings("debugging_enabled").format(instance.__class__.__name__),
        )

    async def logscmd(
        self,
        message: Union[Message, aiogram.types.CallbackQuery],
        force: bool = False,
        lvl: Union[int, None] = None,
    ) -> None:
        """<level> - Dumps logs. Loglevels below WARNING may contain personal info."""
        if not isinstance(lvl, int):
            args = utils.get_args_raw(message)
            try:
                try:
                    lvl = int(args.split()[0])
                except ValueError:
                    lvl = getattr(logging, args.split()[0].upper(), None)
            except IndexError:
                lvl = None

        if not isinstance(lvl, int):
            try:
                if not self.inline.init_complete or not await self.inline.form(
                    text=self.strings("choose_loglevel"),
                    reply_markup=[
                        [
                            {
                                "text": "🚨 Critical",
                                "callback": self.logscmd,
                                "args": (False, 50),
                            },
                            {
                                "text": "🚫 Error",
                                "callback": self.logscmd,
                                "args": (False, 40),
                            },
                        ],
                        [
                            {
                                "text": "⚠️ Warning",
                                "callback": self.logscmd,
                                "args": (False, 30),
                            },
                            {
                                "text": "ℹ️ Info",
                                "callback": self.logscmd,
                                "args": (False, 20),
                            },
                        ],
                        [
                            {
                                "text": "🧑‍💻 Debug",
                                "callback": self.logscmd,
                                "args": (False, 10),
                            },
                            {
                                "text": "👁 All",
                                "callback": self.logscmd,
                                "args": (False, 0),
                            },
                        ],
                        [{"text": "🚫 Cancel", "callback": self.cancel}],
                    ],
                    message=message,
                ):
                    raise
            except Exception:
                await utils.answer(message, self.strings("set_loglevel"))

            return

        logs = "\n\n".join(
            [
                ("\n".join(handler.dumps(lvl)))
                for handler in logging.getLogger().handlers
            ]
        )

        named_lvl = (
            lvl
            if lvl not in logging._levelToName
            else logging._levelToName[lvl]  # skipcq: PYL-W0212
        )

        if (
            lvl < logging.WARNING
            and not force
            and (
                not isinstance(message, Message)
                or "force_insecure" not in message.raw_text.lower()
            )
        ):
            try:
                if not self.inline.init_complete:
                    raise

                cfg = {
                    "text": self.strings("confidential").format(named_lvl),
                    "reply_markup": [
                        {
                            "text": "📤 Send anyway",
                            "callback": self.logscmd,
                            "args": [True, lvl],
                        },
                        {"text": "🚫 Cancel", "callback": self.cancel},
                    ],
                }
                if isinstance(message, Message):
                    if not await self.inline.form(**cfg, message=message):
                        raise
                else:
                    await message.edit(**cfg)
            except Exception:
                await utils.answer(
                    message,
                    self.strings("confidential_text").format(named_lvl),
                )

            return

        if len(logs) <= 2:
            if isinstance(message, Message):
                await utils.answer(message, self.strings("no_logs").format(named_lvl))
            else:
                await message.edit(self.strings("no_logs").format(named_lvl))
                await message.unload()

            return

        btoken = self._db.get("hikka.inline", "bot_token", False)
        if btoken:
            logs = logs.replace(
                btoken,
                f'{btoken.split(":")}:***************************',
            )

        hikka_token = self._db.get("HikkaDL", "token", False)
        if hikka_token:
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")}_********************************',
            )

        hikka_token = self._db.get("Kirito", "token", False)
        if hikka_token:
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")}_********************************',
            )

        logs = BytesIO(logs.encode("utf-16"))
        logs.name = self.strings("logs_filename")

        ghash = utils.get_git_hash()

        other = (
            *main.__version__,
            f' <i><a href="https://github.com/hikariatama/Hikka/commit/{ghash}">({ghash[:8]})</a></i>'
            if ghash
            else "",
            utils.formatted_uptime(),
            utils.get_named_platform(),
            self.strings(
                f"database_{'un' if self._db.get(main.__name__, 'enable_db_eval', False) else ''}locked"
            ),
            "🚫" if self._db.get(main.__name__, "no_nickname", False) else "✅",
            "🚫" if self._db.get(main.__name__, "grep", False) else "✅",
            "🚫" if self._db.get(main.__name__, "inlinelogs", False) else "✅",
        )

        if isinstance(message, Message):
            await message.delete()
            await utils.answer(
                message,
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )
        else:
            await message.delete()
            await self._client.send_file(
                message.form["chat"],
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )

    @loader.owner
    async def suspendcmd(self, message: Message) -> None:
        """<time> - Suspends the bot for N seconds"""
        try:
            time_sleep = float(utils.get_args_raw(message))
            await utils.answer(
                message, self.strings("suspended", message).format(str(time_sleep))
            )
            time.sleep(time_sleep)
        except ValueError:
            await utils.answer(message, self.strings("suspend_invalid_time", message))

    async def pingcmd(self, message: Message) -> None:
        """Test your userbot ping"""
        start = time.perf_counter_ns()
        message = await utils.answer(
            message, "<code>🐻 Bear with us while ping is checking...</code>"
        )
        end = time.perf_counter_ns()

        if isinstance(message, (list, tuple, set)):
            message = message[0]

        ms = (end - start) * 0.000001

        await utils.answer(message, self.strings("results_ping").format(round(ms, 3)))

    async def client_ready(self, client, db) -> None:
        self._client = client
        self._db = db
        self._task = asyncio.ensure_future(self.watchdog())
