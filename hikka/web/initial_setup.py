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
import os
import re
import string

import aiohttp_jinja2
import telethon
from aiohttp import web

from .. import utils


class Web:
    def __init__(self, **kwargs):
        self.heroku_api_token = os.environ.get("heroku_api_token")
        self.api_token = kwargs.pop("api_token")
        self.data_root = kwargs.pop("data_root")
        self.connection = kwargs.pop("connection")
        self.hosting = kwargs.pop("hosting")
        self.default_app = kwargs.pop("default_app")
        self.proxy = kwargs.pop("proxy")
        self.redirect_url = None
        super().__init__(**kwargs)
        self.app.router.add_get("/initialSetup", self.initial_setup)
        self.app.router.add_put("/setApi", self.set_tg_api)
        self.app.router.add_post("/sendTgCode", self.send_tg_code)
        self.app.router.add_post("/tgCode", self.tg_code)
        self.app.router.add_post("/finishLogin", self.finish_login)
        self.api_set = asyncio.Event()
        self.sign_in_clients = {}
        self.clients = []
        self.clients_set = asyncio.Event()
        self.root_redirected = asyncio.Event()

    async def root(self, request):
        if self.clients_set.is_set():
            await self.ready.wait()
        if self.redirect_url:
            self.root_redirected.set()
            return web.Response(status=302, headers={"Location": self.redirect_url})
        if self.client_data:
            return await super().root(request)
        return await self.initial_setup(request)

    @aiohttp_jinja2.template("initial_root.jinja2")
    async def initial_setup(self, request):
        return {
            "api_done": self.api_token is not None,
            "tg_done": bool(self.client_data),
            "heroku_token": self.heroku_api_token,
            "hosting": self.hosting,
            "default_app": self.default_app,
        }

    def wait_for_api_token_setup(self):
        return self.api_set.wait()

    def wait_for_clients_setup(self):
        return self.clients_set.wait()

    async def set_tg_api(self, request):
        text = await request.text()
        if len(text) < 36:
            return web.Response(status=400)
        api_id = text[32:]
        api_hash = text[:32]
        if any(c not in string.hexdigits for c in api_hash) or any(
            c not in string.digits for c in api_id
        ):
            return web.Response(status=400)
        with open(
            os.path.join(
                self.data_root or os.path.dirname(utils.get_base_dir()), "api_token.txt"
            ),
            "w",
        ) as f:
            f.write(api_id + "\n" + api_hash)
        self.api_token = collections.namedtuple("api_token", ("ID", "HASH"))(
            api_id, api_hash
        )
        self.api_set.set()
        return web.Response()

    async def send_tg_code(self, request):
        text = await request.text()
        phone = telethon.utils.parse_phone(text)
        if not phone:
            return web.Response(status=400)
        client = telethon.TelegramClient(
            telethon.sessions.MemorySession(),
            self.api_token.ID,
            self.api_token.HASH,
            connection=self.connection,
            proxy=self.proxy,
            connection_retries=None,
        )
        await client.connect()
        await client.send_code_request(phone)
        self.sign_in_clients[phone] = client
        return web.Response()

    async def tg_code(self, request):
        text = await request.text()
        if len(text) < 6:
            return web.Response(status=400)
        split = text.split("\n", 2)
        if len(split) not in (2, 3):
            return web.Response(status=400)
        code = split[0]
        phone = telethon.utils.parse_phone(split[1])
        password = split[2]
        if (
            (len(code) != 5 and not password)
            or any(c not in string.digits for c in code)
            or not phone
        ):
            return web.Response(status=400)
        client = self.sign_in_clients[phone]
        if not password:
            try:
                user = await client.sign_in(phone, code=code)
            except telethon.errors.SessionPasswordNeededError:
                return web.Response(status=401)  # Requires 2FA login
            except telethon.errors.PhoneCodeExpiredError:
                return web.Response(status=404)
            except telethon.errors.PhoneCodeInvalidError:
                return web.Response(status=403)
            except telethon.errors.FloodWaitError:
                return web.Response(status=421)
        else:
            try:
                user = await client.sign_in(phone, password=password)
            except telethon.errors.PasswordHashInvalidError:
                return web.Response(status=403)  # Invalid 2FA password
            except telethon.errors.FloodWaitError:
                return web.Response(status=421)
        del self.sign_in_clients[phone]
        client.phone = f"+{user.phone}"
        self.clients.append(client)
        return web.Response()

    async def finish_login(self, request):
        if not self.clients:
            return web.Response(status=400)
        text = await request.text()
        if text:
            if not re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", text):
                return web.Response(status=400)
            self.heroku_api_token = text
        else:
            self.heroku_api_token = None
        self.clients_set.set()
        return web.Response()
