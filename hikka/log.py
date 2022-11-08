"""Main logging part"""

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import inspect
import io
import json
import linecache
import logging
import os
import re
import sys
import traceback
import typing
from logging.handlers import RotatingFileHandler

import telethon

from . import utils
from .tl_cache import CustomTelegramClient
from .types import BotInlineCall, Module
from .web.debugger import WebDebugger

# Monkeypatch linecache to make interactive line debugger available
# in werkzeug web debugger
# This is weird, but the only adequate approach
# https://github.com/pallets/werkzeug/blob/3115aa6a6276939f5fd6efa46282e0256ff21f1a/src/werkzeug/debug/tbtools.py#L382-L416

old = linecache.getlines


def getlines(filename, module_globals=None):
    """Get the lines for a Python source file from the cache.
    Update the cache if it doesn't contain an entry for this file already."""

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


class HikkaException:
    def __init__(
        self,
        message: str,
        local_vars: str,
        full_stack: str,
        sysinfo: typing.Optional[
            typing.Tuple[object, Exception, traceback.TracebackException]
        ] = None,
    ):
        self.message = message
        self.local_vars = local_vars
        self.full_stack = full_stack
        self.sysinfo = sysinfo

    @classmethod
    def from_exc_info(
        cls,
        exc_type: object,
        exc_value: Exception,
        tb: traceback.TracebackException,
        stack: typing.Optional[typing.List[inspect.FrameInfo]] = None,
    ) -> "HikkaException":
        def to_hashable(dictionary: dict) -> dict:
            dictionary = dictionary.copy()
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    dictionary[key] = to_hashable(value)
                else:
                    if (
                        getattr(getattr(value, "__class__", None), "__name__", None)
                        == "Database"
                    ):
                        dictionary[key] = "<Database>"
                    elif isinstance(
                        value,
                        (telethon.TelegramClient, CustomTelegramClient),
                    ):
                        dictionary[key] = f"<{value.__class__.__name__}>"
                    elif len(str(value)) > 512:
                        dictionary[key] = f"{str(value)[:512]}..."
                    else:
                        dictionary[key] = str(value)

            return dictionary

        full_stack = traceback.format_exc().replace(
            "Traceback (most recent call last):\n", ""
        )

        line_regex = r'  File "(.*?)", line ([0-9]+), in (.+)'

        def format_line(line: str) -> str:
            filename_, lineno_, name_ = re.search(line_regex, line).groups()
            with contextlib.suppress(Exception):
                filename_ = os.path.basename(filename_)

            return (
                f"👉 <code>{utils.escape_html(filename_)}:{lineno_}</code> <b>in</b>"
                f" <code>{utils.escape_html(name_)}</code>"
            )

        filename, lineno, name = next(
            (
                re.search(line_regex, line).groups()
                for line in reversed(full_stack.splitlines())
                if re.search(line_regex, line)
            ),
            (None, None, None),
        )

        full_stack = "\n".join(
            [
                format_line(line)
                if re.search(line_regex, line)
                else f"<code>{utils.escape_html(line)}</code>"
                for line in full_stack.splitlines()
            ]
        )

        with contextlib.suppress(Exception):
            filename = os.path.basename(filename)

        caller = utils.find_caller(stack or inspect.stack())
        cause_mod = (
            "🪬 <b>Possible cause: method"
            f" </b><code>{utils.escape_html(caller.__name__)}</code><b> of module"
            f" </b><code>{utils.escape_html(caller.__self__.__class__.__name__)}</code>\n"
            if caller and hasattr(caller, "__self__") and hasattr(caller, "__name__")
            else ""
        )

        return HikkaException(
            message=(
                f"<b>🚫 Error!</b>\n{cause_mod}\n<b>🗄 Where:</b>"
                f" <code>{utils.escape_html(filename)}:{lineno}</code><b>"
                f" in </b><code>{utils.escape_html(name)}</code>\n<b>❓ What:</b>"
                f" <code>{utils.escape_html(''.join(traceback.format_exception_only(exc_type, exc_value)).strip())}</code>"
            ),
            local_vars=(
                f"<code>{utils.escape_html(json.dumps(to_hashable(tb.tb_frame.f_locals), indent=4))}</code>"
            ),
            full_stack=full_stack,
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

    def __init__(self, targets: list, capacity: int, web_debugger: WebDebugger):
        super().__init__(0)
        self.targets = targets
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.NOTSET  # Default loglevel
        self._queue = []
        self.tg_buff = []
        self._mods = {}
        self.force_send_all = False
        self.tg_level = 20
        self.web_debugger = web_debugger
        self._send_lock = asyncio.Lock()

    def install_tg_log(self, mod: Module):
        if getattr(self, "_task", False):
            self._task.cancel()

        self._mods[mod.tg_id] = mod

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
        bot: "aiogram.Bot",  # type: ignore
        item: HikkaException,
    ):
        chunks = (
            item.message
            + "\n\n<b>🦝 Locals:</b>\n"
            + item.local_vars
            + "\n\n"
            + "<b>🪐 Full trace:</b>\n"
            + item.full_stack
        )

        chunks = list(utils.smart_split(*telethon.extensions.html.parse(chunks), 4096))

        await call.edit(
            chunks[0],
            reply_markup=[
                {"text": "🐞 Web debugger", "url": item.debug_url},
            ]
            if item.debug_url
            else None,
        )

        for chunk in chunks[1:]:
            await bot.send_message(chat_id=call.chat_id, text=chunk)

    def _gen_web_debug_button(self, item: HikkaException) -> list:
        if not item.sysinfo:
            return []

        try:
            url = self.web_debugger.feed(*item.sysinfo)
        except Exception:
            item.debug_url = None
            return []

        item.debug_url = url

        return [
            {
                "text": "🐞 Web debugger",
                "url": url,
            }
        ]

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
                        self._mods[client_id]._logchat,
                        item[0].message,
                        reply_markup=self._mods[client_id].inline.generate_markup(
                            [
                                {
                                    "text": "🪐 Full trace",
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
                        self._mods[client_id]._logchat,
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
                                self._mods[client_id]._logchat,
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
                logging.debug(record.__dict__)
                self.tg_buff += [
                    (
                        HikkaException.from_exc_info(
                            *record.exc_info,
                            stack=record.__dict__.get("stack", None),
                        ),
                        caller,
                    )
                ]
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
    web_debugger = WebDebugger()
    logging.getLogger().addHandler(
        TelegramLogsHandler((handler, rotating_handler), 7000, web_debugger)
    )
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.captureWarnings(True)
