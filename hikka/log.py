"""Main logging part"""

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

import logging
import asyncio
import traceback
from ._types import Module
from . import utils

_formatter = logging.Formatter


class MemoryHandler(logging.Handler):
    """
    Keeps 2 buffers.
    One for dispatched messages.
    One for unused messages.
    When the length of the 2 together is 100
    truncate to make them 100 together,
    first trimming handled then unused.
    """

    def __init__(self, target, capacity: int) -> None:
        super().__init__(0)
        self.target = target
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.WARNING  # Default loglevel
        self._queue = []
        self.tg_buff = ""
        self._mods = {}

    def install_tg_log(self, mod: Module) -> None:
        if getattr(self, "_task", False):
            self._task.cancel()

        if getattr(self, "_task_2", False):
            self._task_2.cancel()

        self._mods[mod._me] = mod

        self._task = asyncio.ensure_future(self.queue_poller())
        self._task_2 = asyncio.ensure_future(self.send_poller())

    async def queue_poller(self) -> None:
        while True:
            if self._queue:
                await self.sender()

            await asyncio.sleep(3)

    async def send_poller(self) -> None:
        while True:
            if self.tg_buff:
                await self.emit_to_tg()

            await asyncio.sleep(7)

    def setLevel(self, level: int) -> None:
        self.lvl = level

    def dump(self) -> None:
        """Return a list of logging entries"""
        return self.handledbuffer + self.buffer

    def dumps(self, lvl: int = 0) -> list:
        """Return all entries of minimum level as list of strings"""
        return [
            self.target.format(record)
            for record in (self.buffer + self.handledbuffer)
            if record.levelno >= lvl
        ]

    async def emit_to_tg(self):
        for chunk in utils.chunks(
            utils.escape_html(self.tg_buff),
            4083,
        ):
            self._queue += [f"<code>{chunk}</code>"]

        self.tg_buff = ""

    async def sender(self):
        chunk = self._queue.pop(0)

        if not chunk:
            return

        for mod in self._mods.values():
            await mod.inline.bot.send_message(
                mod._logchat,
                f"<code>{chunk}</code>",
                parse_mode="HTML",
                disable_notification=True,
            )

    def emit(self, record) -> None:
        if record.exc_info is not None:
            exc = (
                "\n🚫 Traceback:\n"
                + "\n".join(
                    [
                        line
                        for line in traceback.format_exception(*record.exc_info)[1:]
                        if "hikka/dispatcher.py" not in line
                        and "    await func(message)" not in line
                    ]
                ).strip()
            )
        else:
            exc = ""

        if record.levelno >= 20:
            try:
                self.tg_buff += f"[{record.levelname}] {record.name}: {str(record.msg) % record.args}{exc}\n"
            except TypeError:
                self.tg_buff += f"[{record.levelname}] {record.name}: {record.msg}\n"

            if exc:
                asyncio.ensure_future(self.emit_to_tg())

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
                    self.target.handle(precord)
                self.handledbuffer = (
                    self.handledbuffer[-(self.capacity - len(self.buffer)) :]
                    + self.buffer
                )
                self.buffer = []
            finally:
                self.release()


def init():
    formatter = _formatter(logging.BASIC_FORMAT, "")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.getLogger().handlers = []
    logging.getLogger().addHandler(MemoryHandler(handler, 5000))
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.captureWarnings(True)
