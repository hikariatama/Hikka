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

import asyncio
import inspect
import logging
import io
from typing import Optional

from . import utils
from ._types import Module

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


class TelegramLogsHandler(logging.Handler):
    """
    Keeps 2 buffers.
    One for dispatched messages.
    One for unused messages.
    When the length of the 2 together is 100
    truncate to make them 100 together,
    first trimming handled then unused.
    """

    def __init__(self, target, capacity: int):
        super().__init__(0)
        self.target = target
        self.capacity = capacity
        self.buffer = []
        self.handledbuffer = []
        self.lvl = logging.NOTSET  # Default loglevel
        self._queue = []
        self.tg_buff = []
        self._mods = {}
        self.force_send_all = False

    def install_tg_log(self, mod: Module):
        if getattr(self, "_task", False):
            self._task.cancel()

        self._mods[mod._tg_id] = mod

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

    def dumps(self, lvl: Optional[int] = 0, client_id: Optional[int] = None) -> list:
        """Return all entries of minimum level as list of strings"""
        return [
            self.target.format(record)
            for record in (self.buffer + self.handledbuffer)
            if record.levelno >= lvl
            and (not record.hikka_caller or client_id == record.hikka_caller)
        ]

    async def sender(self):
        self._queue = {
            client_id: utils.chunks(
                utils.escape_html(
                    "".join(
                        [
                            item[0]
                            for item in self.tg_buff
                            if not item[1]
                            or item[1] == client_id
                            or self.force_send_all
                        ]
                    )
                ),
                4096,
            )
            for client_id in self._mods
        }

        self.tg_buff = []

        for client_id in self._mods:
            if client_id not in self._queue:
                continue

            if len(self._queue[client_id]) > 5:
                file = io.BytesIO("".join(self._queue[client_id]).encode("utf-8"))
                file.name = "hikka-logs.txt"
                file.seek(0)
                await self._mods[client_id].inline.bot.send_document(
                    self._mods[client_id]._logchat,
                    file,
                    parse_mode="HTML",
                    caption="<b>🧳 Journals are too big to be sent as separate messages</b>",
                )

                self._queue[client_id] = []
                continue

            while self._queue[client_id]:
                chunk = self._queue[client_id].pop(0)

                if not chunk:
                    continue

                asyncio.ensure_future(
                    self._mods[client_id].inline.bot.send_message(
                        self._mods[client_id]._logchat,
                        f"<code>{chunk}</code>",
                        parse_mode="HTML",
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

            assert isinstance(caller, int)
        except Exception:
            caller = None

        record.hikka_caller = caller

        if record.levelno >= 20:
            self.tg_buff += [
                (
                    ("🚫 " if record.exc_info else "") + _tg_formatter.format(record),
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
                    self.target.handle(precord)

                self.handledbuffer = (
                    self.handledbuffer[-(self.capacity - len(self.buffer)) :]
                    + self.buffer
                )
                self.buffer = []
            finally:
                self.release()


def init():
    handler = logging.StreamHandler()
    handler.setFormatter(_main_formatter)
    logging.getLogger().handlers = []
    logging.getLogger().addHandler(TelegramLogsHandler(handler, 7000))
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.captureWarnings(True)
