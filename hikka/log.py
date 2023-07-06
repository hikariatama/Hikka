"""Main logging part"""

# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import inspect
import io
import linecache
import logging
import re
import sys
import traceback
import typing
from logging.handlers import RotatingFileHandler

import hikkatl
from aiogram.utils.exceptions import NetworkError

from . import utils
from .tl_cache import CustomTelegramClient
from .types import BotInlineCall, Module
from .web.debugger import WebDebugger

# Monkeypatch linecache to make interactive line debugger available
# in werkzeug web debugger
# This is weird, but the only adequate approach
# https://github.com/pallets/werkzeug/blob/3115aa6a6276939f5fd6efa46282e0256ff21f1a/src/werkzeug/debug/tbtools.py#L382-L416

old = linecache.getlines


def getlines(filename: str, module_globals=None) -> str:
    """
    Get the lines for a Python source file from the cache.
    Update the cache if it doesn't contain an entry for this file already.

    Modified version of original `linecache.getlines`, which returns the
    source code of Hikka and Dragon modules properly. This is needed for
    interactive line debugger in werkzeug web debugger.
    """

    try:
        if filename.startswith("<") and filename.endswith(">"):
            module = filename[1:-1].split(maxsplit=1)[-1]
            if (
                module.startswith("hikka.modules")
                or module.startswith("dragon.modules")
            ) and module in sys.modules:
                return list(
                    map(
                        lambda x: f"{x}\n",
                        sys.modules[module].__loader__.get_source().splitlines(),
                    )
                )
    except Exception:
        logging.debug("Can't get lines for %s", filename, exc_info=True)

    return old(filename, module_globals)


linecache.getlines = getlines


def override_text(exception: Exception) -> typing.Optional[str]:
    """Returns error-specific description if available, else `None`"""
    if isinstance(exception, NetworkError):
        return "✈️ <b>You have problems with internet connection on your server.</b>"

    return None


class HikkaException:
    def __init__(
        self,
        message: str,
        full_stack: str,
        sysinfo: typing.Optional[
            typing.Tuple[object, Exception, traceback.TracebackException]
        ] = None,
    ):
        self.message = message
        self.full_stack = full_stack
        self.sysinfo = sysinfo
        self.debug_url = None

    @classmethod
    def from_exc_info(
        cls,
        exc_type: object,
        exc_value: Exception,
        tb: traceback.TracebackException,
        stack: typing.Optional[typing.List[inspect.FrameInfo]] = None,
        comment: typing.Optional[typing.Any] = None,
    ) -> "HikkaException":
        def to_hashable(dictionary: dict) -> dict:
            dictionary = dictionary.copy()
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    dictionary[key] = to_hashable(value)
                else:
                    try:
                        if (
                            getattr(getattr(value, "__class__", None), "__name__", None)
                            == "Database"
                        ):
                            dictionary[key] = "<Database>"
                        elif isinstance(
                            value,
                            (hikkatl.TelegramClient, CustomTelegramClient),
                        ):
                            dictionary[key] = f"<{value.__class__.__name__}>"
                        elif len(str(value)) > 512:
                            dictionary[key] = f"{str(value)[:512]}..."
                        else:
                            dictionary[key] = str(value)
                    except Exception:
                        dictionary[key] = f"<{value.__class__.__name__}>"

            return dictionary

        full_traceback = traceback.format_exc().replace(
            "Traceback (most recent call last):\n",
            "",
        )

        line_regex = re.compile(r'  File "(.*?)", line ([0-9]+), in (.+)')

        def format_line(line: str) -> str:
            filename_, lineno_, name_ = line_regex.search(line).groups()

            return (
                f"👉 <code>{utils.escape_html(filename_)}:{lineno_}</code> <b>in</b>"
                f" <code>{utils.escape_html(name_)}</code>"
            )

        filename, lineno, name = next(
            (
                line_regex.search(line).groups()
                for line in reversed(full_traceback.splitlines())
                if line_regex.search(line)
            ),
            (None, None, None),
        )

        full_traceback = "\n".join(
            [
                (
                    format_line(line)
                    if line_regex.search(line)
                    else f"<code>{utils.escape_html(line)}</code>"
                )
                for line in full_traceback.splitlines()
            ]
        )

        caller = utils.find_caller(stack or inspect.stack())

        return cls(
            message=override_text(exc_value)
            or (
                "{}<b>🎯 Source:</b> <code>{}:{}</code><b> in"
                " </b><code>{}</code>\n<b>❓ Error:</b> <code>{}</code>{}"
            ).format(
                (
                    (
                        "🔮 <b>Cause: method </b><code>{}</code><b> of"
                        " </b><code>{}</code>\n\n"
                    ).format(
                        utils.escape_html(caller.__name__),
                        utils.escape_html(caller.__self__.__class__.__name__),
                    )
                    if (
                        caller
                        and hasattr(caller, "__self__")
                        and hasattr(caller, "__name__")
                    )
                    else ""
                ),
                utils.escape_html(filename),
                lineno,
                utils.escape_html(name),
                utils.escape_html(
                    "".join(
                        traceback.format_exception_only(exc_type, exc_value)
                    ).strip()
                ),
                (
                    "\n💭 <b>Message:</b>"
                    f" <code>{utils.escape_html(str(comment))}</code>"
                    if comment
                    else ""
                ),
            ),
            full_stack=full_traceback,
            sysinfo=(exc_type, exc_value, tb),
        )


class TelegramLogsHandler(logging.Handler):
    """
    Keeps 2 buffers.
    One for dispatched messages.
    One for unused messages.
    When the length of the 2 together is 100
    truncate to make them 100 together,
    first trimming handled then unused.
    """

    def __init__(self, targets: list, capacity: int):
        super().__init__(0)
        self.buffer = []
        self.handledbuffer = []
        self._queue = []
        self._mods = {}
        self.tg_buff = []
        self.force_send_all = False
        self.tg_level = 20
        self.ignore_common = False
        self.web_debugger = None
        self.targets = targets
        self.capacity = capacity
        self.lvl = logging.NOTSET
        self._send_lock = asyncio.Lock()

    def install_tg_log(self, mod: Module):
        if getattr(self, "_task", False):
            self._task.cancel()

        self._mods[mod.tg_id] = mod

        if mod.db.get(__name__, "debugger", False):
            self.web_debugger = WebDebugger()

        self._task = asyncio.ensure_future(self.queue_poller())

    async def queue_poller(self):
        while True:
            await self.sender()
            await asyncio.sleep(3)

    def setLevel(self, level: int):
        self.lvl = level

    def dump(self):
        """Return a list of logging entries"""
        return self.handledbuffer + self.buffer

    def dumps(
        self,
        lvl: int = 0,
        client_id: typing.Optional[int] = None,
    ) -> typing.List[str]:
        """Return all entries of minimum level as list of strings"""
        return [
            self.targets[0].format(record)
            for record in (self.buffer + self.handledbuffer)
            if record.levelno >= lvl
            and (not record.hikka_caller or client_id == record.hikka_caller)
        ]

    async def _show_full_trace(
        self,
        call: BotInlineCall,
        bot: "aiogram.Bot",  # type: ignore  # noqa: F821
        item: HikkaException,
    ):
        chunks = item.message + "\n\n<b>🪐 Full traceback:</b>\n" + item.full_stack

        chunks = list(utils.smart_split(*hikkatl.extensions.html.parse(chunks), 4096))

        await call.edit(
            chunks[0],
            reply_markup=self._gen_web_debug_button(item),
        )

        for chunk in chunks[1:]:
            await bot.send_message(chat_id=call.chat_id, text=chunk)

    def _gen_web_debug_button(self, item: HikkaException) -> list:
        if not item.sysinfo:
            return []

        if not (url := item.debug_url):
            try:
                url = self.web_debugger.feed(*item.sysinfo)
            except Exception:
                url = None

            item.debug_url = url

        return [
            (
                {
                    "text": "🐞 Web debugger",
                    "url": url,
                }
                if self.web_debugger
                else {
                    "text": "🪲 Start debugger",
                    "callback": self._start_debugger,
                    "args": (item,),
                }
            )
        ]

    async def _start_debugger(
        self,
        call: "InlineCall",  # type: ignore  # noqa: F821
        item: HikkaException,
    ):
        if not self.web_debugger:
            self.web_debugger = WebDebugger()
            await self.web_debugger.proxy_ready.wait()

        url = self.web_debugger.feed(*item.sysinfo)
        item.debug_url = url

        await call.edit(
            item.message,
            reply_markup=self._gen_web_debug_button(item),
        )

        await call.answer(
            (
                "Web debugger started. You can get PIN using .debugger command. \n⚠️"
                " !DO NOT GIVE IT TO ANYONE! ⚠️"
            ),
            show_alert=True,
        )

    def get_logid_by_client(self, client_id: int) -> int:
        return self._mods[client_id].logchat

    async def sender(self):
        async with self._send_lock:
            self._queue = {
                client_id: utils.chunks(
                    utils.escape_html(
                        "".join(
                            [
                                item[0]
                                for item in self.tg_buff
                                if isinstance(item[0], str)
                                and (
                                    not item[1]
                                    or item[1] == client_id
                                    or self.force_send_all
                                )
                            ]
                        )
                    ),
                    4096,
                )
                for client_id in self._mods
            }

            self._exc_queue = {
                client_id: [
                    self._mods[client_id].inline.bot.send_message(
                        self._mods[client_id].logchat,
                        item[0].message,
                        reply_markup=self._mods[client_id].inline.generate_markup(
                            [
                                {
                                    "text": "🪐 Full traceback",
                                    "callback": self._show_full_trace,
                                    "args": (
                                        self._mods[client_id].inline.bot,
                                        item[0],
                                    ),
                                    "disable_security": True,
                                },
                                *self._gen_web_debug_button(item[0]),
                            ],
                        ),
                    )
                    for item in self.tg_buff
                    if isinstance(item[0], HikkaException)
                    and (not item[1] or item[1] == client_id or self.force_send_all)
                ]
                for client_id in self._mods
            }

            for exceptions in self._exc_queue.values():
                for exc in exceptions:
                    await exc

            self.tg_buff = []

            for client_id in self._mods:
                if client_id not in self._queue:
                    continue

                if len(self._queue[client_id]) > 5:
                    logfile = io.BytesIO(
                        "".join(self._queue[client_id]).encode("utf-8")
                    )
                    logfile.name = "hikka-logs.txt"
                    logfile.seek(0)
                    await self._mods[client_id].inline.bot.send_document(
                        self._mods[client_id].logchat,
                        logfile,
                        caption=(
                            "<b>🧳 Journals are too big to be sent as separate"
                            " messages</b>"
                        ),
                    )

                    self._queue[client_id] = []
                    continue

                while self._queue[client_id]:
                    if chunk := self._queue[client_id].pop(0):
                        asyncio.ensure_future(
                            self._mods[client_id].inline.bot.send_message(
                                self._mods[client_id].logchat,
                                f"<code>{chunk}</code>",
                                disable_notification=True,
                            )
                        )

    def emit(self, record: logging.LogRecord):
        try:
            caller = next(
                (
                    frame_info.frame.f_locals["_hikka_client_id_logging_tag"]
                    for frame_info in inspect.stack()
                    if isinstance(
                        getattr(getattr(frame_info, "frame", None), "f_locals", {}).get(
                            "_hikka_client_id_logging_tag"
                        ),
                        int,
                    )
                ),
                False,
            )

            if not isinstance(caller, int):
                caller = None
        except Exception:
            caller = None

        record.hikka_caller = caller

        if record.levelno >= self.tg_level:
            if record.exc_info:
                exc = HikkaException.from_exc_info(
                    *record.exc_info,
                    stack=record.__dict__.get("stack", None),
                    comment=record.msg % record.args,
                )

                if not self.ignore_common or all(
                    field not in exc.message
                    for field in [
                        "InputPeerEmpty() does not have any entity type",
                        "https://docs.telethon.dev/en/stable/concepts/entities.html",
                    ]
                ):
                    self.tg_buff += [(exc, caller)]
            else:
                self.tg_buff += [
                    (
                        _tg_formatter.format(record),
                        caller,
                    )
                ]

        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if self.handledbuffer:
                del self.handledbuffer[0]
            else:
                del self.buffer[0]

        self.buffer.append(record)

        if record.levelno >= self.lvl >= 0:
            self.acquire()
            try:
                for precord in self.buffer:
                    for target in self.targets:
                        if record.levelno >= target.level:
                            target.handle(precord)

                self.handledbuffer = (
                    self.handledbuffer[-(self.capacity - len(self.buffer)) :]
                    + self.buffer
                )
                self.buffer = []
            finally:
                self.release()


_main_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="%",
)
_tg_formatter = logging.Formatter(
    fmt="[%(levelname)s] %(name)s: %(message)s\n",
    datefmt=None,
    style="%",
)

rotating_handler = RotatingFileHandler(
    filename="hikka.log",
    mode="a",
    maxBytes=10 * 1024 * 1024,
    backupCount=1,
    encoding="utf-8",
    delay=0,
)

rotating_handler.setFormatter(_main_formatter)


def init():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(_main_formatter)
    logging.getLogger().handlers = []
    logging.getLogger().addHandler(
        TelegramLogsHandler((handler, rotating_handler), 7000)
    )
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger("hikkatl").setLevel(logging.WARNING)
    logging.getLogger("hikkapyro").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.captureWarnings(True)
