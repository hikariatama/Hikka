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
import inspect
import os

import aiohttp_jinja2
import jinja2
from aiohttp import web

from . import initial_setup, root


class Web(initial_setup.Web, root.Web):
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
        super().__init__(**kwargs)
        self.app.router.add_get("/favicon.ico", self.favicon)

    async def start_if_ready(self, total_count, port):
        if total_count <= len(self.client_data):
            if not self.running.is_set():
                await self.start(port)
            self.ready.set()

    async def start(self, port):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.port = os.environ.get("PORT", port)
        site = web.TCPSite(self.runner, None, self.port)
        await site.start()
        self.running.set()

    async def stop(self):
        await self.runner.shutdown()
        await self.runner.cleanup()
        self.running.clear()
        self.ready.clear()

    async def add_loader(self, client, loader, db):
        self.client_data[(await client.get_me(True)).user_id] = (loader, client, db)

    @staticmethod
    async def favicon(request):
        return web.Response(
            status=301, headers={"Location": "https://i.imgur.com/xEOkgCj.jpeg"}
        )
