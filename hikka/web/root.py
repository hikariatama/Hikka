"""Main bot page"""

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
import collections
import os
import string

import aiohttp_jinja2
import telethon
from aiohttp import web
import atexit
import functools
import logging
import sys
import re
import requests
import time

from .. import utils, main, database

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

DATA_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if "OKTETO" not in os.environ and "DOCKER" not in os.environ
    else "/data"
)


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )


class Web:
    sign_in_clients = {}
    clients = []
    _sessions = []
    _ratelimit = {}

    def __init__(self, **kwargs):
        self.api_token = kwargs.pop("api_token")
        self.data_root = kwargs.pop("data_root")
        self.connection = kwargs.pop("connection")
        self.proxy = kwargs.pop("proxy")
        super().__init__(**kwargs)
        self.app.router.add_get("/", self.root)
        self.app.router.add_put("/setApi", self.set_tg_api)
        self.app.router.add_post("/sendTgCode", self.send_tg_code)
        self.app.router.add_post("/check_session", self.check_session)
        self.app.router.add_post("/web_auth", self.web_auth)
        self.app.router.add_post("/okteto", self.okteto)
        self.app.router.add_post("/tgCode", self.tg_code)
        self.app.router.add_post("/finishLogin", self.finish_login)
        self.app.router.add_post("/custom_bot", self.custom_bot)
        self.api_set = asyncio.Event()
        self.clients_set = asyncio.Event()

    @aiohttp_jinja2.template("root.jinja2")
    async def root(self, request):
        return {
            "skip_creds": self.api_token is not None,
            "tg_done": bool(self.client_data),
            "okteto": "OKTETO" in os.environ,
            "lavhost": "LAVHOST" in os.environ,
        }

    async def check_session(self, request):
        return web.Response(body=("1" if self._check_session(request) else "0"))

    def wait_for_api_token_setup(self):
        return self.api_set.wait()

    def wait_for_clients_setup(self):
        return self.clients_set.wait()

    def _check_session(self, request) -> bool:
        if not main.hikka.clients:
            return True

        return request.cookies.get("session", None) in self._sessions

    async def _check_bot(
        self,
        client: "TelegramClient",  # noqa: F821
        username: str,
    ) -> bool:
        async with client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    async def custom_bot(self, request):
        if not self._check_session(request):
            return web.Response(status=401)

        text = await request.text()
        client = self.clients[0]
        db = database.Database(client)
        await db.init()

        text = text.strip("@")

        if any(
            litera not in (string.ascii_letters + string.digits + "_")
            for litera in text
        ) or not text.lower().endswith("bot"):
            return web.Response(body="OCCUPIED")

        try:
            await client.get_entity(f"@{text}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(client, text):
                return web.Response(body="OCCUPIED")

        db.set("hikka.inline", "custom_bot", text)

    async def set_tg_api(self, request):
        if not self._check_session(request):
            return web.Response(status=401)

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
            os.path.join(self.data_root or DATA_DIR, "api_token.txt"),
            "w",
        ) as f:
            f.write(api_id + "\n" + api_hash)

        self.api_token = collections.namedtuple("api_token", ("ID", "HASH"))(
            api_id,
            api_hash,
        )

        self.api_set.set()
        return web.Response()

    async def send_tg_code(self, request):
        if not self._check_session(request):
            return web.Response(status=401)

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
            device_model="Hikka",
        )

        await client.connect()
        await client.send_code_request(phone)

        self.sign_in_clients[phone] = client
        return web.Response()

    async def okteto(self, request):
        if main.get_config_key("okteto_uri"):
            return web.Response(status=418)

        text = await request.text()
        main.save_config_key("okteto_uri", text)
        return web.Response(body="URI_SAVED")

    async def tg_code(self, request):
        if not self._check_session(request):
            return web.Response(status=401)

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
        if not self._check_session(request):
            return web.Response(status=401)

        if not self.clients:
            return web.Response(status=400)

        first_session = not bool(main.hikka.clients)
        await main.hikka.fetch_clients_from_web()

        self.clients_set.set()

        if not first_session:
            atexit.register(functools.partial(restart, *sys.argv[1:]))
            handler = logging.getLogger().handlers[0]
            handler.setLevel(logging.CRITICAL)
            for client in main.hikka.clients:
                await client.disconnect()

            sys.exit(0)

        return web.Response()

    async def web_auth(self, request):
        if self._check_session(request):
            return web.Response(body=request.cookies.get("session", "unauthorized"))

        token = utils.rand(8)

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "🔓 Authorize user",
                callback_data=f"authorize_web_{token}",
            )
        )

        ips = request.headers.get("X-FORWARDED-FOR", None) or request.remote
        cities = []

        for ip in re.findall(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ips):
            if ip not in self._ratelimit:
                self._ratelimit[ip] = []

            if (
                len(
                    list(
                        filter(lambda x: time.time() - x < 3 * 60, self._ratelimit[ip])
                    )
                )
                >= 3
            ):
                return web.Response(status=429)

            self._ratelimit[ip] = list(
                filter(lambda x: time.time() - x < 3 * 60, self._ratelimit[ip])
            )

            self._ratelimit[ip] += [time.time()]
            try:
                res = (
                    await utils.run_sync(
                        requests.get,
                        f"https://freegeoip.app/json/{ip}",
                    )
                ).json()
                cities += [
                    f"<i>{utils.get_lang_flag(res['country_code'])} {res['country_name']} {res['region_name']} {res['city']} {res['zip_code']}</i>"
                ]
            except Exception:
                pass

        cities = (
            ("<b>🏢 Possible cities:</b>\n\n" + "\n".join(cities) + "\n")
            if cities
            else ""
        )

        ops = []

        for user in self.client_data.values():
            try:
                bot = user[0].inline.bot
                msg = await bot.send_message(
                    (await user[1].get_me()).id,
                    (
                        "🌘🔐 <b>Click button below to confirm web application ops</b>\n\n"
                        f"<b>Client IP</b>: {ips}\n"
                        f"{cities}"
                        "\n<i>If you did not request any codes, simply ignore this message</i>"
                    ),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
                ops += [bot.delete_message(msg.chat.id, msg.message_id)]
            except Exception:
                pass

        session = f"hikka_{utils.rand(16)}"

        if not ops:
            # If no auth message was sent, just leave it empty
            # probably, request was a bug and user doesn't have
            # inline bot or did not authorize any sessions
            return web.Response(body=session)

        if not await main.hikka.wait_for_web_auth(token):
            for op in ops:
                await op
            return web.Response(body="TIMEOUT")

        for op in ops:
            await op

        self._sessions += [session]

        return web.Response(body=session)
