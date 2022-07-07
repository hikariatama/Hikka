"""Responsible for web init and mandatory ops"""

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
import inspect
import logging
import os
import re
import subprocess
import atexit

import aiohttp_jinja2
import jinja2
from aiohttp import web

from . import root


class Web(root.Web):
    def __init__(self, **kwargs):
        self.runner = None
        self.port = None
        self.running = asyncio.Event()
        self.ready = asyncio.Event()
        self.client_data = {}
        self.app = web.Application()
        aiohttp_jinja2.setup(
            self.app,
            filters={"getdoc": inspect.getdoc, "ascii": ascii},
            loader=jinja2.FileSystemLoader("web-resources"),
        )
        self.app["static_root_url"] = "/static"

        super().__init__(**kwargs)
        self.app.router.add_get("/favicon.ico", self.favicon)
        self.app.router.add_static("/static/", "web-resources/static")

    async def start_if_ready(self, total_count: int, port: int):
        if total_count <= len(self.client_data):
            if not self.running.is_set():
                await self.start(port)

            self.ready.set()

    async def _sleep_for_task(self, callback: callable, data: bytes, delay: int):
        await asyncio.sleep(delay)
        await callback(data.decode("utf-8"))

    async def _read_stream(self, callback: callable, stream, delay: int):
        last_task = None
        for getline in iter(stream.readline, ""):
            data_chunk = await getline
            if not data_chunk:
                if last_task:
                    last_task.cancel()
                    await callback(data_chunk.decode("utf-8"))
                    if not self._stream_processed.is_set():
                        self._stream_processed.set()
                break

            if last_task:
                last_task.cancel()

            last_task = asyncio.ensure_future(
                self._sleep_for_task(callback, data_chunk, delay)
            )

    def _kill_tunnel(self):
        try:
            self._sproc.kill()
        except Exception:
            pass
        else:
            logging.debug("Proxy pass tunnel killed")

    async def _reopen_tunnel(self):
        await asyncio.sleep(3600)
        self._kill_tunnel()
        self._stream_processed.clear()
        self._tunnel_url = None
        url = await asyncio.wait_for(self._get_proxy_pass_url(self.port), timeout=10)

        if not url:
            raise Exception("Failed to get proxy pass url")

        self._tunnel_url = url
        asyncio.ensure_future(self._reopen_tunnel())

    async def _process_stream(self, stdout_line: str):
        if self._stream_processed.is_set():
            return

        regex = r"[a-zA-Z0-9]\.lhrtunnel\.link tunneled.*(https:\/\/.*\.link)"

        if re.search(regex, stdout_line):
            logging.debug(f"Proxy pass tunneled: {stdout_line}")
            self._tunnel_url = re.search(regex, stdout_line).group(1)
            self._stream_processed.set()
            atexit.register(self._kill_tunnel)

    async def _get_proxy_pass_url(self, port: int) -> str:
        logging.debug("Starting proxy pass shell")
        self._sproc = await asyncio.create_subprocess_shell(
            f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} nokey@localhost.run",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._stream_processed = asyncio.Event()
        logging.debug("Starting proxy pass reader")
        asyncio.ensure_future(
            self._read_stream(
                self._process_stream,
                self._sproc.stdout,
                1,
            )
        )

        await self._stream_processed.wait()

        if hasattr(self, "_tunnel_url"):
            return self._tunnel_url

        return None

    async def get_url(self, proxy_pass: bool):
        url = None

        if all(option in os.environ for option in {"LAVHOST", "USER", "SERVER"}):
            return f"https://{os.environ['USER']}.{os.environ['SERVER']}.lavhost.ml"

        if "DYNO" not in os.environ and proxy_pass:
            with contextlib.suppress(Exception):
                self._kill_tunnel()
                url = await asyncio.wait_for(
                    self._get_proxy_pass_url(self.port),
                    timeout=10,
                )

        if not url:
            ip = (
                "127.0.0.1"
                if "DOCKER" not in os.environ
                else subprocess.run(
                    ["hostname", "-i"],
                    stdout=subprocess.PIPE,
                    check=True,
                )
                .stdout.decode("utf-8")
                .strip()
            )

            url = f"http://{ip}:{self.port}"
        else:
            asyncio.ensure_future(self._reopen_tunnel())

        self.url = url
        return url

    async def start(self, port: int, proxy_pass: bool = False):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.port = os.environ.get("PORT", port)
        site = web.TCPSite(self.runner, None, self.port)
        await site.start()

        await self.get_url(proxy_pass)

        self.running.set()

    async def stop(self):
        await self.runner.shutdown()
        await self.runner.cleanup()
        self.running.clear()
        self.ready.clear()

    async def add_loader(
        self,
        client: "TelegramClient",  # type: ignore
        loader: "Modules",  # type: ignore
        db: "Database",  # type: ignore
    ):
        self.client_data[client._tg_id] = (loader, client, db)

    @staticmethod
    async def favicon(request):
        return web.Response(
            status=301,
            headers={"Location": "https://i.imgur.com/IRAiWBo.jpeg"},
        )
