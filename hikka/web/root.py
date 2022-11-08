"""Main bot page"""

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import collections
import functools
import os
import re
import string
import time

import aiohttp_jinja2
import requests
import telethon
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
from telethon.errors.rpcerrorlist import FloodWaitError, YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

from .. import database, main, utils
from .._internal import restart
from ..tl_cache import CustomTelegramClient
from ..version import __version__

DATA_DIR = (
    "/data"
    if "DOCKER" in os.environ
    else os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
)


class Web:
    def __init__(self, **kwargs):
        self.sign_in_clients = {}
        self._pending_client = None
        self._sessions = []
        self._ratelimit = {}
        self.api_token = kwargs.pop("api_token")
        self.data_root = kwargs.pop("data_root")
        self.connection = kwargs.pop("connection")
        self.proxy = kwargs.pop("proxy")

        self.app.router.add_get("/", self.root)
        self.app.router.add_put("/setApi", self.set_tg_api)
        self.app.router.add_post("/sendTgCode", self.send_tg_code)
        self.app.router.add_post("/check_session", self.check_session)
        self.app.router.add_post("/web_auth", self.web_auth)
        self.app.router.add_post("/tgCode", self.tg_code)
        self.app.router.add_post("/finishLogin", self.finish_login)
        self.app.router.add_post("/custom_bot", self.custom_bot)
        self.api_set = asyncio.Event()
        self.clients_set = asyncio.Event()

    @aiohttp_jinja2.template("root.jinja2")
    async def root(self, _):
        return {
            "skip_creds": self.api_token is not None,
            "tg_done": bool(self.client_data),
            "lavhost": "LAVHOST" in os.environ,
        }

    async def check_session(self, request: web.Request) -> web.Response:
        return web.Response(body=("1" if self._check_session(request) else "0"))

    def wait_for_api_token_setup(self):
        return self.api_set.wait()

    def wait_for_clients_setup(self):
        return self.clients_set.wait()

    def _check_session(self, request: web.Request) -> bool:
        return (
            request.cookies.get("session", None) in self._sessions
            if main.hikka.clients
            else True
        )

    async def _check_bot(
        self,
        client: CustomTelegramClient,
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

    async def custom_bot(self, request: web.Request) -> web.Response:
        if not self._check_session(request):
            return web.Response(status=401)

        text = await request.text()
        client = self._pending_client
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
        return web.Response(body="OK")

    async def set_tg_api(self, request: web.Request) -> web.Response:
        if not self._check_session(request):
            return web.Response(status=401, body="Authorization required")

        text = await request.text()

        if len(text) < 36:
            return web.Response(
                status=400,
                body="API ID and HASH pair has invalid length",
            )

        api_id = text[32:]
        api_hash = text[:32]

        if any(c not in string.hexdigits for c in api_hash) or any(
            c not in string.digits for c in api_id
        ):
            return web.Response(
                status=400,
                body="You specified invalid API ID and/or API HASH",
            )

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
        return web.Response(body="ok")

    async def send_tg_code(self, request: web.Request) -> web.Response:
        if not self._check_session(request):
            return web.Response(status=401, body="Authorization required")

        if self._pending_client:
            return web.Response(status=208, body="Already pending")

        text = await request.text()
        phone = telethon.utils.parse_phone(text)

        if not phone:
            return web.Response(status=400, body="Invalid phone number")

        client = CustomTelegramClient(
            telethon.sessions.MemorySession(),
            self.api_token.ID,
            self.api_token.HASH,
            connection=self.connection,
            proxy=self.proxy,
            connection_retries=None,
            device_model=f"Hikka on {utils.get_named_platform().split(maxsplit=1)[1]}",
            app_version=f"Hikka v{__version__[0]}.{__version__[1]}.{__version__[2]}",
        )

        self._pending_client = client

        await client.connect()
        try:
            await client.send_code_request(phone)
        except FloodWaitError as e:
            return web.Response(
                status=429,
                body=(
                    f"You got FloodWait of {e.seconds} seconds. Wait the specified"
                    " amount of time and try again."
                ),
            )

        return web.Response(body="ok")

    async def tg_code(self, request: web.Request) -> web.Response:
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

        if not password:
            try:
                await self._pending_client.sign_in(phone, code=code)
            except telethon.errors.SessionPasswordNeededError:
                return web.Response(
                    status=401,
                    body="2FA Password required",
                )  # Requires 2FA login
            except telethon.errors.PhoneCodeExpiredError:
                return web.Response(status=404, body="Code expired")
            except telethon.errors.PhoneCodeInvalidError:
                return web.Response(status=403, body="Invalid code")
            except telethon.errors.FloodWaitError as e:
                return web.Response(
                    status=421,
                    body=(
                        f"You got FloodWait of {e.seconds} seconds. Wait the specified"
                        " amount of time and try again."
                    ),
                )
        else:
            try:
                await self._pending_client.sign_in(phone, password=password)
            except telethon.errors.PasswordHashInvalidError:
                return web.Response(
                    status=403,
                    body="Invalid 2FA password",
                )  # Invalid 2FA password
            except telethon.errors.FloodWaitError as e:
                return web.Response(
                    status=421,
                    body=(
                        f"You got FloodWait of {e.seconds} seconds. Wait the specified"
                        " amount of time and try again."
                    ),
                )

        await main.hikka.save_client_session(self._pending_client)
        return web.Response()

    async def finish_login(self, request: web.Request) -> web.Response:
        if not self._check_session(request):
            return web.Response(status=401)

        if not self._pending_client:
            return web.Response(status=400)

        first_session = not bool(main.hikka.clients)

        # Client is ready to pass in to dispatcher
        main.hikka.clients = list(set(main.hikka.clients + [self._pending_client]))
        self._pending_client = None

        self.clients_set.set()

        if not first_session:
            restart()

        return web.Response()

    async def web_auth(self, request: web.Request) -> web.Response:
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
                    user[1].tg_id,
                    "🌘🔐 <b>Click button below to confirm web application"
                    f" ops</b>\n\n<b>Client IP</b>: {ips}\n{cities}\n<i>If you did not"
                    " request any codes, simply ignore this message</i>",
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
                ops += [
                    functools.partial(
                        bot.delete_message,
                        chat_id=msg.chat.id,
                        message_id=msg.message_id,
                    )
                ]
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
                await op()
            return web.Response(body="TIMEOUT")

        for op in ops:
            await op()

        self._sessions += [session]

        return web.Response(body=session)
