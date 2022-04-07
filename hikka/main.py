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


# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
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

from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import (
    PhoneNumberInvalidError,
    ApiIdInvalidError,
    AuthKeyDuplicatedError,
)
from telethon.network.connection import ConnectionTcpFull
from telethon.network.connection import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.sessions import SQLiteSession

from . import utils, loader, database
from .dispatcher import CommandDispatcher
from .translations.core import Translator

from math import ceil
from .version import __version__
from typing import Union

try:
    from .web import core
except ImportError:
    web_available = False
    logging.exception("Unable to import web")
else:
    web_available = True

is_okteto = "OKTETO" in os.environ

omit_log = False

DATA_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if not is_okteto
    else "/data"
)

CONFIG_PATH = os.path.join(DATA_DIR, "config.json")


def run_config(db: database.Database, data_root: str, phone: Union[str, int] = None, modules: list = None) -> None:
    """Load configurator.py"""
    from . import configurator

    return configurator.run(db, data_root, phone, phone is None, modules)


def get_config_key(key: str) -> Union[str, bool]:
    """Parse and return key from config"""
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.loads(f.read())

        return config.get(key, False)
    except FileNotFoundError:
        return False


def save_config_key(key: str, value: str) -> bool:
    try:
        # Try to open our newly created json config
        with open(CONFIG_PATH, "r") as f:
            config = json.loads(f.read())
    except FileNotFoundError:
        # If it doesn't exist, just default config to none
        # It won't cause problems, bc after new save
        # we will create new one
        config = {}

    # Assign config value
    config[key] = value

    # And save config
    with open(CONFIG_PATH, "w") as f:
        f.write(json.dumps(config))

    return True


def gen_port() -> int:
    if "OKTETO" in os.environ:
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


def parse_arguments() -> None:
    """Parse the arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", "-s", action="store_true")
    parser.add_argument("--port", dest="port", action="store", default=gen_port(), type=int)  # fmt: skip
    parser.add_argument("--phone", "-p", action="append")
    parser.add_argument("--token", "-t", action="append", dest="tokens")
    parser.add_argument("--no-nickname", "-nn", dest="no_nickname", action="store_true")
    parser.add_argument("--hosting", "-lh", dest="hosting", action="store_true")
    parser.add_argument("--web-only", dest="web_only", action="store_true")
    parser.add_argument("--no-web", dest="disable_web", action="store_false")
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
        "--docker-deps-internal",
        dest="docker_deps_internal",
        action="store_true",
        help="This is for internal use only. If you use it, things will go wrong.",
    )
    parser.add_argument(
        "--root",
        dest="disable_root_check",
        action="store_true",
        help="Disable `force_insecure` warning",
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

    def __getattribute__(self, attr):
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
    def __init__(self) -> None:
        super().__init__()


def raise_auth():
    raise InteractiveAuthRequired()


class Hikka:
    def __init__(self):
        self.arguments = parse_arguments()
        self.loop = asyncio.get_event_loop()

        self.clients = SuperList()
        self._get_phones()
        self._get_api_token()
        self._get_proxy()

    def _get_proxy(self) -> None:
        """
        Get proxy tuple from --proxy-host, --proxy-port and --proxy-secret
        and connection to use (depends on proxy - provided or not)
        """
        if (
            self.arguments.proxy_host is not None
            and self.arguments.proxy_port is not None
            and self.arguments.proxy_secret is not None
        ):
            logging.debug(f"Using proxy: {self.arguments.proxy_host}:{self.arguments.proxy_port}")  # fmt: skip
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

    def _get_phones(self) -> None:
        """Get phones from the --phone, and environment"""
        phones = {
            phone.split(":", maxsplit=1)[0]: phone
            for phone in map(
                lambda f: f[6:-8],
                filter(
                    lambda f: f.startswith("hikka-") and f.endswith(".session"),
                    os.listdir(
                        self.arguments.data_root or DATA_DIR,
                    ),
                ),
            )
        }

        phones.update(
            **(
                {
                    phone.split(":", maxsplit=1)[0]: phone
                    for phone in self.arguments.phone
                }
                if self.arguments.phone
                else {}
            )
        )

        self.phones = phones

    def _get_api_token(self) -> None:
        """Get API Token from disk or environment"""
        api_token_type = collections.namedtuple("api_token", ("ID", "HASH"))

        # Try to retrieve credintials from file, or from env vars
        try:
            with open(
                os.path.join(
                    self.arguments.data_root or DATA_DIR,
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

    def _init_web(self) -> None:
        """Initialize web"""
        if web_available and not getattr(self.arguments, "disable_web", False):
            self.web = None
            return

        self.web = core.Web(
            data_root=self.arguments.data_root,
            api_token=self.api_token,
            proxy=self.proxy,
            connection=self.conn,
        )

    def _get_token(self) -> None:
        """Reads or waits for user to enter API credentials"""
        while self.api_token is None:
            if self.arguments.no_auth:
                return
            if self.web:
                self.loop.run_until_complete(self.web.start(self.arguments.port))
                self._web_banner()
                self.loop.run_until_complete(self.web.wait_for_api_token_setup())
                self.api_token = self.web.api_token
            else:
                run_config({}, self.arguments.data_root)
                importlib.invalidate_caches()
                self._get_api_token()

    async def fetch_clients_from_web(self) -> None:
        """Imports clients from web module"""
        for client in self.web.clients:
            session = SQLiteSession(
                os.path.join(
                    self.arguments.data_root or DATA_DIR,
                    f"hikka-+{'x' * (len(client.phone) - 5)}{client.phone[-4:]}-{(await client.get_me()).id}",
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

        self.clients = list(set(self.clients + self.web.clients))

    def _web_banner(self) -> None:
        """Shows web banner"""
        print("✅ Web mode ready for configuration")
        print(f"🌐 Please visit http://127.0.0.1:{self.web.port}")

    async def wait_for_web_auth(self, token: str) -> None:
        """Waits for web auth confirmation in Telegram"""
        timeout = 5 * 60
        polling_interval = 1
        for _ in range(ceil(timeout * polling_interval)):
            await asyncio.sleep(polling_interval)

            for client in self.clients:
                if client.loader.inline.pop_web_auth_token(token):
                    return True

    def _initial_setup(self) -> bool:
        """Responsible for first start"""
        if self.arguments.no_auth:
            return False

        if not self.web:
            try:
                phone = input("Please enter your phone: ")
                self.phones = {phone.split(":", maxsplit=1)[0]: phone}
            except (EOFError, OSError):
                raise

            return True

        if not self.web.running.is_set():
            self.loop.run_until_complete(self.web.start(self.arguments.port))
            self._web_banner()

        self.loop.run_until_complete(self.web.wait_for_clients_setup())

        return True

    def _init_clients(self) -> None:
        """Reads session from disk and inits them"""
        for phone_id, phone in self.phones.items():
            session = os.path.join(
                self.arguments.data_root or DATA_DIR,
                f'hikka{f"-{phone_id}" if phone_id else ""}',
            )

            try:
                client = TelegramClient(
                    session,
                    self.api_token.ID,
                    self.api_token.HASH,
                    connection=self.conn,
                    proxy=self.proxy,
                    connection_retries=None,
                    device_model="Hikka",
                )

                client.start(phone=raise_auth if self.web else lambda: input("Phone: "))
                client.phone = phone

                self.clients.append(client)
            except sqlite3.OperationalError:
                print(
                    "Check that this is the only instance running. "
                    f"If that doesn't help, delete the file named 'hikka-{phone or ''}.session'"
                )
                continue
            except (TypeError, AuthKeyDuplicatedError):
                os.remove(f"{session}.session")
                self.main()
            except (ValueError, ApiIdInvalidError):
                # Bad API hash/ID
                run_config({}, self.arguments.data_root)
                return
            except PhoneNumberInvalidError:
                print(
                    "Phone number is incorrect. Use international format (+XX...) "
                    "and don't put spaces in it."
                )
                continue
            except InteractiveAuthRequired:
                print(f"Session {session} was terminated and re-auth is required")
                continue

    def _init_loop(self) -> None:
        loops = [self.amain_wrapper(client) for client in self.clients]
        self.loop.run_until_complete(asyncio.gather(*loops))

    async def amain_wrapper(self, client) -> None:
        """Wrapper around amain"""
        async with client:
            first = True
            while await self.amain(first, client):
                first = False

    async def _badge(self, client) -> None:
        """Call the badge in shell"""
        global omit_log
        try:
            import git

            repo = git.Repo()

            build = repo.heads[0].commit.hexsha
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            upd = r"Update required" if diff else r"Up-to-date"

            _platform = utils.get_named_platform()

            logo1 = f"""

                        █ █ █ █▄▀ █▄▀ ▄▀█
                        █▀█ █ █ █ █ █ █▀█

                     • Build: {build[:7]}
                     • Version: {'.'.join(list(map(str, list(__version__))))}
                     • {upd}
                     • Platform: {_platform}
                     - Started for {(await client.get_me()).id} -"""

            print(logo1)
            if not omit_log:
                logging.info(
                    "🌘 Hikka started\n"
                    f"GitHub commit SHA: {build[:7]} ({upd})\n"
                    f"Hikka version: {'.'.join(list(map(str, list(__version__))))}\n"
                    f"Platform: {_platform}"
                )
                omit_log = True
        except Exception:
            logging.exception("Badge error")

    async def _handle_setup(self, client, db) -> None:
        await db.init()
        modules = loader.Modules()
        babelfish = Translator([], [], self.arguments.data_root)
        await babelfish.init(client)

        modules.register_all(db)

        modules.send_config(db, babelfish)
        await modules.send_ready(client, db, self.clients)

        for handler in logging.getLogger().handlers:
            handler.setLevel(50)

        db_ = db.read()
        db_ = run_config(
            db_,
            self.arguments.data_root,
            getattr(client, "phone", "Unknown Number"),
            modules,
        )

    async def _add_dispatcher(self, client, modules, db) -> None:
        dispatcher = CommandDispatcher(modules, db, self.arguments.no_nickname)
        client.dispatcher = dispatcher
        await dispatcher.init(client)
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

    async def amain(self, first, client) -> None:
        """Entrypoint for async init, run once for each user"""
        setup = self.arguments.setup
        web_only = self.arguments.web_only
        client.parse_mode = "HTML"
        await client.start()

        handlers = logging.getLogger().handlers
        db = database.Database(client)
        await db.init()

        if setup:
            self._handle_setup(client, db)
            return False

        logging.debug("got db")
        logging.info("Loading logging config...")
        for handler in handlers:
            handler.setLevel(db.get(__name__, "loglevel", logging.WARNING))

        to_load = ["loader.py"] if self.arguments.docker_deps_internal else None

        babelfish = Translator(
            db.get(__name__, "langpacks", []),
            db.get(__name__, "language", ["en"]),
            self.arguments.data_root,
        )

        await babelfish.init(client)
        modules = loader.Modules()
        client.loader = modules

        if self.arguments.docker_deps_internal:
            # Loader has installed all dependencies
            return  # We are done

        if self.web:
            await self.web.add_loader(client, modules, db)
            await self.web.start_if_ready(
                len(self.clients),
                self.arguments.port,
            )

        if not web_only:
            await self._add_dispatcher(client, modules, db)

        modules.register_all(db, to_load)
        modules.send_config(db, babelfish)
        await modules.send_ready(client, db, self.clients)

        if first:
            await self._badge(client)

        await client.run_until_disconnected()

    def main(self) -> None:
        """Main entrypoint"""
        self._init_web()
        save_config_key("port", self.arguments.port)
        self._get_token()

        if not self.clients and not self.phones and not self._initial_setup():
            return

        self._init_clients()

        self.loop.set_exception_handler(
            lambda _, x: logging.error(
                f"Exception on event loop! {x['message']}",
                exc_info=x.get("exception", None),
            )
        )

        self._init_loop()


hikka = Hikka()
