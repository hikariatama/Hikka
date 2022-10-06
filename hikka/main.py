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


#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html


import argparse
import asyncio
import collections
import importlib
import json
import logging
import os
import random
import socket
import sqlite3
import sys
from math import ceil
import typing
import telethon
from telethon import events
from telethon.errors.rpcerrorlist import (
    ApiIdInvalidError,
    AuthKeyDuplicatedError,
    PhoneNumberInvalidError,
)
from telethon.network.connection import (
    ConnectionTcpFull,
    ConnectionTcpMTProxyRandomizedIntermediate,
)
from telethon.sessions import SQLiteSession, MemorySession

from . import database, loader, utils, version
from .dispatcher import CommandDispatcher
from .translations import Translator
from .version import __version__
from .tl_cache import CustomTelegramClient

try:
    from .web import core
except ImportError:
    web_available = False
    logging.exception("Unable to import web")
else:
    web_available = True

BASE_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if "OKTETO" not in os.environ and "DOCKER" not in os.environ
    else "/data"
)

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

try:
    import uvloop

    uvloop.install()
except Exception:
    pass


def run_config(data_root: str):
    """Load configurator.py"""
    from . import configurator

    return configurator.api_config(data_root)


def get_config_key(key: str) -> typing.Union[str, bool]:
    """
    Parse and return key from config
    :param key: Key name in config
    :return: Value of config key or `False`, if it doesn't exist
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

        return config.get(key, False)
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
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        # If it doesn't exist, just default config to none
        # It won't cause problems, bc after new save
        # we will create new one
        config = {}

    # Assign config value
    config[key] = value

    # And save config
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

    return True


def gen_port() -> int:
    """
    Generates random free port in case of VDS, and
    8080 in case of Okteto
    In case of Docker, also return 8080, as it's already
    exposed by default
    :returns: Integer value of generated port
    """
    if any(trigger in os.environ for trigger in {"OKTETO", "DOCKER"}):
        return 8080

    # But for own server we generate new free port, and assign to it

    port = get_config_key("port")
    if port:
        return port

    # If we didn't get port from config, generate new one
    # First, try to randomly get port
    port = random.randint(1024, 65536)

    # Then ensure it's free
    while not socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ).connect_ex(("localhost", port)):
        # Until we find the free port, generate new one
        port = random.randint(1024, 65536)

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
    arguments = parser.parse_args()
    logging.debug(arguments)
    if sys.platform == "win32":
        # Subprocess support; not needed in 3.8 but not harmful
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    return arguments


class SuperList(list):
    """
    Makes able: await self.allclients.send_message("foo", "bar")
    """

    def __getattribute__(self, attr: str) -> typing.Any:
        if hasattr(list, attr):
            return list.__getattribute__(self, attr)

        for obj in self:  # TODO: find other way
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

    omit_log = False

    def __init__(self):
        self.arguments = parse_arguments()
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
                    self.arguments.data_root or BASE_DIR,
                    session.rsplit(".session", maxsplit=1)[0],
                )
            )
            for session in filter(
                lambda f: f.startswith("hikka-") and f.endswith(".session"),
                os.listdir(self.arguments.data_root or BASE_DIR),
            )
        ]

    def _get_api_token(self):
        """Get API Token from disk or environment"""
        api_token_type = collections.namedtuple("api_token", ("ID", "HASH"))

        # Try to retrieve credintials from file, or from env vars
        try:
            with open(
                os.path.join(
                    self.arguments.data_root or BASE_DIR,
                    "api_token.txt",
                )
            ) as f:
                api_token = api_token_type(*[line.strip() for line in f.readlines()])
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
        if not web_available or getattr(self.arguments, "disable_web", False):
            self.web = None
            return

        self.web = core.Web(
            data_root=self.arguments.data_root,
            api_token=self.api_token,
            proxy=self.proxy,
            connection=self.conn,
        )

    def _get_token(self):
        """Reads or waits for user to enter API credentials"""
        while self.api_token is None:
            if self.arguments.no_auth:
                return
            if self.web:
                self.loop.run_until_complete(
                    self.web.start(
                        self.arguments.port,
                        proxy_pass=True,
                    )
                )
                self.loop.run_until_complete(self._web_banner())
                self.loop.run_until_complete(self.web.wait_for_api_token_setup())
                self.api_token = self.web.api_token
            else:
                run_config(self.arguments.data_root)
                importlib.invalidate_caches()
                self._get_api_token()

    async def save_client_session(self, client: CustomTelegramClient):
        if hasattr(client, "_tg_id"):
            telegram_id = client._tg_id
        else:
            me = await client.get_me()
            telegram_id = me.id
            client._tg_id = telegram_id
            client.tg_id = telegram_id
            client.hikka_me = me

        session = SQLiteSession(
            os.path.join(
                self.arguments.data_root or BASE_DIR,
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
        for _ in range(ceil(timeout * polling_interval)):
            await asyncio.sleep(polling_interval)

            for client in self.clients:
                if client.loader.inline.pop_web_auth_token(token):
                    return True

        return False

    def _initial_setup(self) -> bool:
        """Responsible for first start"""
        if self.arguments.no_auth:
            return False

        if not self.web:
            try:
                phone = input("Phone: ")
                client = CustomTelegramClient(
                    MemorySession(),
                    self.api_token.ID,
                    self.api_token.HASH,
                    connection=self.conn,
                    proxy=self.proxy,
                    connection_retries=None,
                    device_model="Hikka",
                )

                client.start(phone)

                asyncio.ensure_future(self.save_client_session(client))

                self.clients += [client]
            except (EOFError, OSError):
                raise

            return True

        if not self.web.running.is_set():
            self.loop.run_until_complete(
                self.web.start(
                    self.arguments.port,
                    proxy_pass=True,
                )
            )
            asyncio.ensure_future(self._web_banner())

        self.loop.run_until_complete(self.web.wait_for_clients_setup())

        return True

    def _init_clients(self) -> bool:
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
                    device_model="Hikka",
                )

                client.start(phone=raise_auth if self.web else lambda: input("Phone: "))

                client.phone = "never gonna give you up"

                self.clients += [client]
            except sqlite3.OperationalError:
                logging.error(
                    "Check that this is the only instance running. "
                    "If that doesn't help, delete the file '%s'",
                    session.filename,
                )
                continue
            except (TypeError, AuthKeyDuplicatedError):
                os.remove(os.path.join(BASE_DIR, f"{session}.session"))
                self.sessions.remove(session)
            except (ValueError, ApiIdInvalidError):
                # Bad API hash/ID
                run_config(self.arguments.data_root)
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

    def _init_loop(self):
        """Initializes main event loop and starts handler for each client"""
        loops = [self.amain_wrapper(client) for client in self.clients]
        self.loop.run_until_complete(asyncio.gather(*loops))

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

            build = repo.heads[0].commit.hexsha
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = r"Update required" if diff else r"Up-to-date"

            _platform = utils.get_named_platform()

            logo1 = f"""

                        █ █ █ █▄▀ █▄▀ ▄▀█
                        █▀█ █ █ █ █ █ █▀█

                     • Build: {build[:7]}
                     • Version: {'.'.join(list(map(str, list(__version__))))}
                     • {upd}
                     • Platform: {_platform}
                     """

            if not self.omit_log:
                print(logo1)
                web_url = (
                    f"🌐 Web url: {self.web.url}\n"
                    if self.web and hasattr(self.web, "url")
                    else ""
                )
                logging.info(
                    "🌘 Hikka %s started\n🔏 GitHub commit SHA: %s (%s)\n%s%s",
                    ".".join(list(map(str, list(__version__)))),
                    build[:7],
                    upd,
                    web_url,
                    _platform,
                )
                self.omit_log = True

            logging.info("- Started for %s -", client._tg_id)
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

    async def amain(self, first: bool, client: CustomTelegramClient):
        """Entrypoint for async init, run once for each user"""
        client.parse_mode = "HTML"
        await client.start()

        db = database.Database(client)
        await db.init()

        logging.debug("Got DB")
        logging.debug("Loading logging config...")

        translator = Translator(client, db)

        await translator.init()
        modules = loader.Modules(client, db, self.clients, translator)
        client.loader = modules

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

    def main(self):
        """Main entrypoint"""
        self._init_web()
        save_config_key("port", self.arguments.port)
        self._get_token()

        if (
            not self.clients  # Search for already inited clients
            and not self.sessions  # Search for already added sessions
            or not self._init_clients()  # Attempt to read sessions from env
        ) and not self._initial_setup():  # Otherwise attempt to run setup
            return

        self.loop.set_exception_handler(
            lambda _, x: logging.error(
                "Exception on event loop! %s",
                x["message"],
                exc_info=x.get("exception", None),
            )
        )

        self._init_loop()


telethon.extensions.html.CUSTOM_EMOJIS = not get_config_key("disable_custom_emojis")

hikka = Hikka()
