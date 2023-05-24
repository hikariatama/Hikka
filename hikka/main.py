"""Main script, where all the fun starts"""

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


# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html


import argparse
import asyncio
import collections
import contextlib
import importlib
import json
import logging
import os
import random
import socket
import sqlite3
import typing
from getpass import getpass
from pathlib import Path

import hikkatl
from hikkatl import events
from hikkatl.errors import (
    ApiIdInvalidError,
    AuthKeyDuplicatedError,
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)
from hikkatl.network.connection import (
    ConnectionTcpFull,
    ConnectionTcpMTProxyRandomizedIntermediate,
)
from hikkatl.password import compute_check
from hikkatl.sessions import MemorySession, SQLiteSession
from hikkatl.tl.functions.account import GetPasswordRequest
from hikkatl.tl.functions.auth import CheckPasswordRequest

from . import database, loader, utils, version
from ._internal import print_banner
from .dispatcher import CommandDispatcher
from .qr import QRCode
from .tl_cache import CustomTelegramClient
from .translations import Translator
from .version import __version__

try:
    from .web import core
except ImportError:
    web_available = False
    logging.exception("Unable to import web")
else:
    web_available = True

BASE_DIR = (
    "/data"
    if "DOCKER" in os.environ
    else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

BASE_PATH = Path(BASE_DIR)
CONFIG_PATH = BASE_PATH / "config.json"

IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "")
IS_CODESPACES = "CODESPACES" in os.environ
IS_DOCKER = "DOCKER" in os.environ
IS_RAILWAY = "RAILWAY" in os.environ
IS_GOORM = "GOORM" in os.environ
IS_LAVHOST = "LAVHOST" in os.environ
IS_WSL = False
with contextlib.suppress(Exception):
    from platform import uname

    if "microsoft-standard" in uname().release:
        IS_WSL = True

# fmt: off
LATIN_MOCK = [
    "Amor", "Arbor", "Astra", "Aurum", "Bellum", "Caelum",
    "Calor", "Candor", "Carpe", "Celer", "Certo", "Cibus",
    "Civis", "Clemens", "Coetus", "Cogito", "Conexus",
    "Consilium", "Cresco", "Cura", "Cursus", "Decus",
    "Deus", "Dies", "Digitus", "Discipulus", "Dominus",
    "Donum", "Dulcis", "Durus", "Elementum", "Emendo",
    "Ensis", "Equus", "Espero", "Fidelis", "Fides",
    "Finis", "Flamma", "Flos", "Fortis", "Frater", "Fuga",
    "Fulgeo", "Genius", "Gloria", "Gratia", "Gravis",
    "Habitus", "Honor", "Hora", "Ignis", "Imago",
    "Imperium", "Inceptum", "Infinitus", "Ingenium",
    "Initium", "Intra", "Iunctus", "Iustitia", "Labor",
    "Laurus", "Lectus", "Legio", "Liberi", "Libertas",
    "Lumen", "Lux", "Magister", "Magnus", "Manus",
    "Memoria", "Mens", "Mors", "Mundo", "Natura",
    "Nexus", "Nobilis", "Nomen", "Novus", "Nox",
    "Oculus", "Omnis", "Opus", "Orbis", "Ordo", "Os",
    "Pax", "Perpetuus", "Persona", "Petra", "Pietas",
    "Pons", "Populus", "Potentia", "Primus", "Proelium",
    "Pulcher", "Purus", "Quaero", "Quies", "Ratio",
    "Regnum", "Sanguis", "Sapientia", "Sensus", "Serenus",
    "Sermo", "Signum", "Sol", "Solus", "Sors", "Spes",
    "Spiritus", "Stella", "Summus", "Teneo", "Terra",
    "Tigris", "Trans", "Tribuo", "Tristis", "Ultimus",
    "Unitas", "Universus", "Uterque", "Valde", "Vates",
    "Veritas", "Verus", "Vester", "Via", "Victoria",
    "Vita", "Vox", "Vultus", "Zephyrus"
]
# fmt: on


def generate_app_name() -> str:
    """
    Generate random app name
    :return: Random app name
    :example: "Cresco Cibus Consilium"
    """
    return " ".join(random.choices(LATIN_MOCK, k=3))


def get_app_name() -> str:
    """
    Generates random app name or gets the saved one of present
    :return: App name
    :example: "Cresco Cibus Consilium"
    """
    if not (app_name := get_config_key("app_name")):
        app_name = generate_app_name()
        save_config_key("app_name", app_name)

    return app_name


try:
    import uvloop

    uvloop.install()
except Exception:
    pass


def run_config():
    """Load configurator.py"""
    from . import configurator

    return configurator.api_config(IS_TERMUX or None)


def get_config_key(key: str) -> typing.Union[str, bool]:
    """
    Parse and return key from config
    :param key: Key name in config
    :return: Value of config key or `False`, if it doesn't exist
    """
    try:
        return json.loads(CONFIG_PATH.read_text()).get(key, False)
    except FileNotFoundError:
        return False


def save_config_key(key: str, value: str) -> bool:
    """
    Save `key` with `value` to config
    :param key: Key name in config
    :param value: Desired value in config
    :return: `True` on success, otherwise `False`
    """
    try:
        # Try to open our newly created json config
        config = json.loads(CONFIG_PATH.read_text())
    except FileNotFoundError:
        # If it doesn't exist, just default config to none
        # It won't cause problems, bc after new save
        # we will create new one
        config = {}

    # Assign config value
    config[key] = value
    # And save config
    CONFIG_PATH.write_text(json.dumps(config, indent=4))
    return True


def gen_port(cfg: str = "port", no8080: bool = False) -> int:
    """
    Generates random free port in case of VDS.
    In case of Docker, also return 8080, as it's already exposed by default.
    :returns: Integer value of generated port
    """
    if "DOCKER" in os.environ and not no8080:
        return 8080

    # But for own server we generate new free port, and assign to it
    if port := get_config_key(cfg):
        return port

    # If we didn't get port from config, generate new one
    # First, try to randomly get port
    while port := random.randint(1024, 65536):
        if socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(
            ("localhost", port)
        ):
            break

    return port


def parse_arguments() -> dict:
    """
    Parses the arguments
    :returns: Dictionary with arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port",
        dest="port",
        action="store",
        default=gen_port(),
        type=int,
    )
    parser.add_argument("--phone", "-p", action="append")
    parser.add_argument("--no-web", dest="disable_web", action="store_true")
    parser.add_argument(
        "--qr-login",
        dest="qr_login",
        action="store_true",
        help=(
            "Use QR code login instead of phone number (will only work if scanned from"
            " another device)"
        ),
    )
    parser.add_argument(
        "--data-root",
        dest="data_root",
        default="",
        help="Root path to store session files in",
    )
    parser.add_argument(
        "--no-auth",
        dest="no_auth",
        action="store_true",
        help="Disable authentication and API token input, exitting if needed",
    )
    parser.add_argument(
        "--proxy-host",
        dest="proxy_host",
        action="store",
        help="MTProto proxy host, without port",
    )
    parser.add_argument(
        "--proxy-port",
        dest="proxy_port",
        action="store",
        type=int,
        help="MTProto proxy port",
    )
    parser.add_argument(
        "--proxy-secret",
        dest="proxy_secret",
        action="store",
        help="MTProto proxy secret",
    )
    parser.add_argument(
        "--root",
        dest="disable_root_check",
        action="store_true",
        help="Disable `force_insecure` warning",
    )
    parser.add_argument(
        "--proxy-pass",
        dest="proxy_pass",
        action="store_true",
        help="Open proxy pass tunnel on start (not needed on setup)",
    )
    parser.add_argument(
        "--no-tty",
        dest="tty",
        action="store_false",
        default=True,
        help="Do not print colorful output using ANSI escapes",
    )
    arguments = parser.parse_args()
    logging.debug(arguments)
    return arguments


class SuperList(list):
    """
    Makes able: await self.allclients.send_message("foo", "bar")
    """

    def __getattribute__(self, attr: str) -> typing.Any:
        if hasattr(list, attr):
            return list.__getattribute__(self, attr)

        for obj in self:
            attribute = getattr(obj, attr)
            if callable(attribute):
                if asyncio.iscoroutinefunction(attribute):

                    async def foobar(*args, **kwargs):
                        return [await getattr(_, attr)(*args, **kwargs) for _ in self]

                    return foobar
                return lambda *args, **kwargs: [
                    getattr(_, attr)(*args, **kwargs) for _ in self
                ]

            return [getattr(x, attr) for x in self]


class InteractiveAuthRequired(Exception):
    """Is being rased by Telethon, if phone is required"""


def raise_auth():
    """Raises `InteractiveAuthRequired`"""
    raise InteractiveAuthRequired()


class Hikka:
    """Main userbot instance, which can handle multiple clients"""

    def __init__(self):
        global BASE_DIR, BASE_PATH, CONFIG_PATH
        self.omit_log = False
        self.arguments = parse_arguments()
        if self.arguments.data_root:
            BASE_DIR = self.arguments.data_root
            BASE_PATH = Path(BASE_DIR)
            CONFIG_PATH = BASE_PATH / "config.json"
        self.loop = asyncio.get_event_loop()

        self.clients = SuperList()
        self.ready = asyncio.Event()
        self._read_sessions()
        self._get_api_token()
        self._get_proxy()

    def _get_proxy(self):
        """
        Get proxy tuple from --proxy-host, --proxy-port and --proxy-secret
        and connection to use (depends on proxy - provided or not)
        """
        if (
            self.arguments.proxy_host is not None
            and self.arguments.proxy_port is not None
            and self.arguments.proxy_secret is not None
        ):
            logging.debug(
                "Using proxy: %s:%s",
                self.arguments.proxy_host,
                self.arguments.proxy_port,
            )
            self.proxy, self.conn = (
                (
                    self.arguments.proxy_host,
                    self.arguments.proxy_port,
                    self.arguments.proxy_secret,
                ),
                ConnectionTcpMTProxyRandomizedIntermediate,
            )
            return

        self.proxy, self.conn = None, ConnectionTcpFull

    def _read_sessions(self):
        """Gets sessions from environment and data directory"""
        self.sessions = []
        self.sessions += [
            SQLiteSession(
                os.path.join(
                    BASE_DIR,
                    session.rsplit(".session", maxsplit=1)[0],
                )
            )
            for session in filter(
                lambda f: f.startswith("hikka-") and f.endswith(".session"),
                os.listdir(BASE_DIR),
            )
        ]

    def _get_api_token(self):
        """Get API Token from disk or environment"""
        api_token_type = collections.namedtuple("api_token", ("ID", "HASH"))

        # Try to retrieve credintials from config, or from env vars
        try:
            # Legacy migration
            if not get_config_key("api_id"):
                api_id, api_hash = (
                    line.strip()
                    for line in (Path(BASE_DIR) / "api_token.txt")
                    .read_text()
                    .splitlines()
                )
                save_config_key("api_id", int(api_id))
                save_config_key("api_hash", api_hash)
                (Path(BASE_DIR) / "api_token.txt").unlink()
                logging.debug("Migrated api_token.txt to config.json")

            api_token = api_token_type(
                get_config_key("api_id"),
                get_config_key("api_hash"),
            )
        except FileNotFoundError:
            try:
                from . import api_token
            except ImportError:
                try:
                    api_token = api_token_type(
                        os.environ["api_id"],
                        os.environ["api_hash"],
                    )
                except KeyError:
                    api_token = None

        self.api_token = api_token

    def _init_web(self):
        """Initialize web"""
        if (
            not web_available
            or getattr(self.arguments, "disable_web", False)
            or IS_TERMUX
        ):
            self.web = None
            return

        self.web = core.Web(
            data_root=BASE_DIR,
            api_token=self.api_token,
            proxy=self.proxy,
            connection=self.conn,
        )

    async def _get_token(self):
        """Reads or waits for user to enter API credentials"""
        while self.api_token is None:
            if self.arguments.no_auth:
                return
            if self.web:
                await self.web.start(self.arguments.port, proxy_pass=True)
                await self._web_banner()
                await self.web.wait_for_api_token_setup()
                self.api_token = self.web.api_token
            else:
                run_config()
                importlib.invalidate_caches()
                self._get_api_token()

    async def save_client_session(self, client: CustomTelegramClient):
        if hasattr(client, "tg_id"):
            telegram_id = client.tg_id
        else:
            if not (me := await client.get_me()):
                raise RuntimeError("Attempted to save non-inited session")

            telegram_id = me.id
            client._tg_id = telegram_id
            client.tg_id = telegram_id
            client.hikka_me = me

        session = SQLiteSession(
            os.path.join(
                BASE_DIR,
                f"hikka-{telegram_id}",
            )
        )

        session.set_dc(
            client.session.dc_id,
            client.session.server_address,
            client.session.port,
        )

        session.auth_key = client.session.auth_key

        session.save()
        client.session = session
        # Set db attribute to this client in order to save
        # custom bot nickname from web
        client.hikka_db = database.Database(client)
        await client.hikka_db.init()

    async def _web_banner(self):
        """Shows web banner"""
        logging.info("✅ Web mode ready for configuration")
        logging.info("🌐 Please visit %s", self.web.url)

    async def wait_for_web_auth(self, token: str) -> bool:
        """
        Waits for web auth confirmation in Telegram
        :param token: Token to wait for
        :return: True if auth was successful, False otherwise
        """
        timeout = 5 * 60
        polling_interval = 1
        for _ in range(timeout * polling_interval):
            await asyncio.sleep(polling_interval)

            for client in self.clients:
                if client.loader.inline.pop_web_auth_token(token):
                    return True

        return False

    async def _phone_login(self, client: CustomTelegramClient) -> bool:
        phone = input(
            "\033[0;96mEnter phone: \033[0m"
            if IS_TERMUX or self.arguments.tty
            else "Enter phone: "
        )

        await client.start(phone)

        await self.save_client_session(client)
        self.clients += [client]
        return True

    async def _initial_setup(self) -> bool:
        """Responsible for first start"""
        if self.arguments.no_auth:
            return False

        if not self.web:
            client = CustomTelegramClient(
                MemorySession(),
                self.api_token.ID,
                self.api_token.HASH,
                connection=self.conn,
                proxy=self.proxy,
                connection_retries=None,
                device_model=get_app_name(),
                system_version="Windows 10",
                app_version=".".join(map(str, __version__)) + " x64",
                lang_code="en",
                system_lang_code="en-US",
            )
            await client.connect()

            print(
                (
                    "\033[0;96m{}\033[0m" if IS_TERMUX or self.arguments.tty else "{}"
                ).format(
                    "You can use QR-code to login from another device (your friend's"
                    " phone, for example)."
                )
            )

            if (
                input(
                    "\033[0;96mUse QR code? [y/N]: \033[0m"
                    if IS_TERMUX or self.arguments.tty
                    else "Use QR code? [y/N]: "
                ).lower()
                != "y"
            ):
                return await self._phone_login(client)

            print("\033[0;96mLoading QR code...\033[0m")
            qr_login = await client.qr_login()

            def print_qr():
                qr = QRCode()
                qr.add_data(qr_login.url)
                print("\033[2J\033[3;1f")
                qr.print_ascii(invert=True)
                print("\033[0;96mScan the QR code above to log in.\033[0m")
                print("\033[0;96mPress Ctrl+C to cancel.\033[0m")

            async def qr_login_poll() -> bool:
                logged_in = False
                while not logged_in:
                    try:
                        logged_in = await qr_login.wait(10)
                    except asyncio.TimeoutError:
                        try:
                            await qr_login.recreate()
                            print_qr()
                        except SessionPasswordNeededError:
                            return True
                    except SessionPasswordNeededError:
                        return True
                    except KeyboardInterrupt:
                        print("\033[2J\033[3;1f")
                        return None

                return False

            if (qr_logined := await qr_login_poll()) is None:
                return await self._phone_login(client)

            if qr_logined:
                print_banner("2fa.txt")
                password = await client(GetPasswordRequest())
                while True:
                    _2fa = getpass(
                        f"\033[0;96mEnter 2FA password ({password.hint}): \033[0m"
                        if IS_TERMUX or self.arguments.tty
                        else f"Enter 2FA password ({password.hint}): "
                    )
                    try:
                        await client._on_login(
                            (
                                await client(
                                    CheckPasswordRequest(
                                        compute_check(password, _2fa.strip())
                                    )
                                )
                            ).user
                        )
                    except PasswordHashInvalidError:
                        print("\033[0;91mInvalid 2FA password!\033[0m")
                    except FloodWaitError as e:
                        seconds, minutes, hours = (
                            e.seconds % 3600 % 60,
                            e.seconds % 3600 // 60,
                            e.seconds // 3600,
                        )
                        seconds, minutes, hours = (
                            f"{seconds} second(-s)",
                            f"{minutes} minute(-s) " if minutes else "",
                            f"{hours} hour(-s) " if hours else "",
                        )
                        print(
                            "\033[0;91mYou got FloodWait error! Please wait"
                            f" {hours}{minutes}{seconds}\033[0m"
                        )
                        return False
                    else:
                        break

            print_banner("success.txt")
            print("\033[0;92mLogged in successfully!\033[0m")
            await self.save_client_session(client)
            self.clients += [client]
            return True

        if not self.web.running.is_set():
            await self.web.start(
                self.arguments.port,
                proxy_pass=True,
            )
            await self._web_banner()

        await self.web.wait_for_clients_setup()

        return True

    async def _init_clients(self) -> bool:
        """
        Reads session from disk and inits them
        :returns: `True` if at least one client started successfully
        """
        for session in self.sessions.copy():
            try:
                client = CustomTelegramClient(
                    session,
                    self.api_token.ID,
                    self.api_token.HASH,
                    connection=self.conn,
                    proxy=self.proxy,
                    connection_retries=None,
                    device_model=get_app_name(),
                    system_version="Windows 10",
                    app_version=".".join(map(str, __version__)) + " x64",
                    lang_code="en",
                    system_lang_code="en-US",
                )

                await client.start(
                    phone=(
                        raise_auth
                        if self.web
                        else lambda: input(
                            "\033[0;96mEnter phone: \033[0m"
                            if IS_TERMUX or self.arguments.tty
                            else "Enter phone: "
                        )
                    )
                )
                client.phone = "never gonna give you up"

                self.clients += [client]
            except sqlite3.OperationalError:
                logging.error(
                    (
                        "Check that this is the only instance running. "
                        "If that doesn't help, delete the file '%s'"
                    ),
                    session.filename,
                )
                continue
            except (TypeError, AuthKeyDuplicatedError):
                Path(session.filename).unlink(missing_ok=True)
                self.sessions.remove(session)
            except (ValueError, ApiIdInvalidError):
                # Bad API hash/ID
                run_config()
                return False
            except PhoneNumberInvalidError:
                logging.error(
                    "Phone number is incorrect. Use international format (+XX...) "
                    "and don't put spaces in it."
                )
                self.sessions.remove(session)
            except InteractiveAuthRequired:
                logging.error(
                    "Session %s was terminated and re-auth is required",
                    session.filename,
                )
                self.sessions.remove(session)

        return bool(self.sessions)

    async def amain_wrapper(self, client: CustomTelegramClient):
        """Wrapper around amain"""
        async with client:
            first = True
            me = await client.get_me()
            client._tg_id = me.id
            client.tg_id = me.id
            client.hikka_me = me
            while await self.amain(first, client):
                first = False

    async def _badge(self, client: CustomTelegramClient):
        """Call the badge in shell"""
        try:
            import git

            repo = git.Repo()

            build = utils.get_git_hash()
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = "Update required" if diff else "Up-to-date"

            logo = (
                "█ █ █ █▄▀ █▄▀ ▄▀█\n"
                "█▀█ █ █ █ █ █ █▀█\n\n"
                f"• Build: {build[:7]}\n"
                f"• Version: {'.'.join(list(map(str, list(__version__))))}\n"
                f"• {upd}\n"
            )

            if not self.omit_log:
                print(logo)
                web_url = (
                    f"🌐 Web url: {self.web.url}"
                    if self.web and hasattr(self.web, "url")
                    else ""
                )
                logging.debug(
                    "\n🌘 Hikka %s #%s (%s) started\n%s",
                    ".".join(list(map(str, list(__version__)))),
                    build[:7],
                    upd,
                    web_url,
                )
                self.omit_log = True

            await client.hikka_inline.bot.send_animation(
                logging.getLogger().handlers[0].get_logid_by_client(client.tg_id),
                "https://github.com/hikariatama/assets/raw/master/hikka_banner.mp4",
                caption=(
                    "🌘 <b>Hikka {} started!</b>\n\n🌳 <b>GitHub commit SHA: <a"
                    ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>\n✊'
                    " <b>Update status: {}</b>\n<b>{}</b>".format(
                        ".".join(list(map(str, list(__version__)))),
                        build,
                        build[:7],
                        upd,
                        web_url,
                    )
                ),
            )

            logging.debug(
                "· Started for %s · Prefix: «%s» ·",
                client.tg_id,
                client.hikka_db.get(__name__, "command_prefix", False) or ".",
            )
        except Exception:
            logging.exception("Badge error")

    async def _add_dispatcher(
        self,
        client: CustomTelegramClient,
        modules: loader.Modules,
        db: database.Database,
    ):
        """Inits and adds dispatcher instance to client"""
        dispatcher = CommandDispatcher(modules, client, db)
        client.dispatcher = dispatcher
        modules.check_security = dispatcher.check_security

        client.add_event_handler(
            dispatcher.handle_incoming,
            events.NewMessage,
        )

        client.add_event_handler(
            dispatcher.handle_incoming,
            events.ChatAction,
        )

        client.add_event_handler(
            dispatcher.handle_command,
            events.NewMessage(forwards=False),
        )

        client.add_event_handler(
            dispatcher.handle_command,
            events.MessageEdited(),
        )

        client.add_event_handler(
            dispatcher.handle_raw,
            events.Raw(),
        )

    async def amain(self, first: bool, client: CustomTelegramClient):
        """Entrypoint for async init, run once for each user"""
        client.parse_mode = "HTML"
        await client.start()

        db = database.Database(client)
        client.hikka_db = db
        await db.init()

        logging.debug("Got DB")
        logging.debug("Loading logging config...")

        translator = Translator(client, db)

        await translator.init()
        modules = loader.Modules(client, db, self.clients, translator)
        client.loader = modules

        client.pyro_proxy = None  # Will be set later if needed

        if self.web:
            await self.web.add_loader(client, modules, db)
            await self.web.start_if_ready(
                len(self.clients),
                self.arguments.port,
                proxy_pass=self.arguments.proxy_pass,
            )

        await self._add_dispatcher(client, modules, db)

        await modules.register_all(None)
        modules.send_config()
        await modules.send_ready()

        if first:
            await self._badge(client)

        await client.run_until_disconnected()

    async def _main(self):
        """Main entrypoint"""
        self._init_web()
        save_config_key("port", self.arguments.port)
        await self._get_token()

        if (
            not self.clients and not self.sessions or not await self._init_clients()
        ) and not await self._initial_setup():
            return

        self.loop.set_exception_handler(
            lambda _, x: logging.error(
                "Exception on event loop! %s",
                x["message"],
                exc_info=x.get("exception", None),
            )
        )

        await asyncio.gather(*[self.amain_wrapper(client) for client in self.clients])

    def main(self):
        """Main entrypoint"""
        self.loop.run_until_complete(self._main())
        self.loop.close()


hikkatl.extensions.html.CUSTOM_EMOJIS = not get_config_key("disable_custom_emojis")

hikka = Hikka()
