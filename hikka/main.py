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

import argparse
import asyncio
import atexit
import collections
import functools
import importlib
import json
import logging
import os
import platform
import random
import signal
import socket
import sqlite3
import sys
import time

import requests
from requests import get
from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import (
    PhoneNumberInvalidError,
    MessageNotModifiedError,
    ApiIdInvalidError,
    AuthKeyDuplicatedError,
)
from telethon.network.connection import ConnectionTcpFull
from telethon.network.connection import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.sessions import StringSession, SQLiteSession
from telethon.tl.functions.channels import DeleteChannelRequest

from . import utils, loader, heroku
from .database import backend, frontend
from .dispatcher import CommandDispatcher
from .translations.core import Translator

__version__ = (3, 1, 24)
try:
    from .web import core
except ImportError:
    web_available = False
    logging.exception("Unable to import web")
else:
    web_available = True


def run_config(db, data_root, phone=None, modules=None):
    """Load configurator.py"""
    from . import configurator

    return configurator.run(db, data_root, phone, phone is None, modules)


def get_config_key(key):
    """Parse and return key from config"""
    try:
        with open("config.json", "r") as f:
            config = json.loads(f.read())

        return config.get(key, False)
    except FileNotFoundError:
        return False


def save_config_key(key, value):
    try:
        # Try to open our newly created json config
        with open("config.json", "r") as f:
            config = json.loads(f.read())
    except FileNotFoundError:
        # If it doesn't exist, just default config to none
        # It won't cause problems, bc after new save
        # we will create new one
        config = {}

    # Assign config value
    config[key] = value

    # And save config
    with open("config.json", "w") as f:
        f.write(json.dumps(config))

    return True


save_config_key("use_fs_for_modules", get_config_key("use_fs_for_modules"))


def gen_port():
    # In case of heroku you always need to use 8080
    if "DYNO" in os.environ:
        return 8080

    # But for own server we generate new free port, and assign to it

    port = get_config_key("port")
    if port:
        return port

    # If we didn't get port from config, generate new one
    # First, try to randomly get port
    port = random.randint(1024, 65536)

    # Then ensure it's free
    while (
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(
            ("localhost", port)
        )
        == 0
    ):
        # Until we find the free port, generate new one
        port = random.randint(1024, 65536)

    return port


def save_db_type(use_file_db):
    return save_config_key("use_file_db", use_file_db)


def parse_arguments():
    """Parse the arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", "-s", action="store_true")
    parser.add_argument(
        "--port", dest="port", action="store", default=gen_port(), type=int
    )
    parser.add_argument("--phone", "-p", action="append")
    parser.add_argument("--token", "-t", action="append", dest="tokens")
    parser.add_argument("--heroku", action="store_true")
    parser.add_argument("--no-nickname", "-nn", dest="no_nickname", action="store_true")
    parser.add_argument("--no-inline", dest="use_inline", action="store_false")
    parser.add_argument("--hosting", "-lh", dest="hosting", action="store_true")
    parser.add_argument("--default-app", "-da", dest="default_app", action="store_true")
    parser.add_argument("--web-only", dest="web_only", action="store_true")
    parser.add_argument("--no-web", dest="web", action="store_false")
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
        "--heroku-web-internal",
        dest="heroku_web_internal",
        action="store_true",
        help="This is for internal use only. If you use it, things will go wrong.",
    )
    parser.add_argument(
        "--heroku-deps-internal",
        dest="heroku_deps_internal",
        action="store_true",
        help="This is for internal use only. If you use it, things will go wrong.",
    )
    parser.add_argument(
        "--docker-deps-internal",
        dest="docker_deps_internal",
        action="store_true",
        help="This is for internal use only. If you use it, things will go wrong.",
    )
    parser.add_argument(
        "--heroku-restart-internal",
        dest="heroku_restart_internal",
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


def get_phones(arguments):
    """Get phones from the --token, --phone, and environment"""
    phones = {
        phone.split(":", maxsplit=1)[0]: phone
        for phone in map(
            lambda f: f[18:-8],
            filter(
                lambda f: f.startswith("friendly-telegram-") and f.endswith(".session"),
                os.listdir(
                    arguments.data_root or os.path.dirname(utils.get_base_dir())
                ),
            ),
        )
    }

    phones.update(
        **(
            {phone.split(":", maxsplit=1)[0]: phone for phone in arguments.phone}
            if arguments.phone
            else {}
        )
    )

    authtoken = os.environ.get("authorization_strings", False)  # for heroku
    if authtoken and not arguments.setup:
        try:
            authtoken = json.loads(authtoken)
        except json.decoder.JSONDecodeError:
            logging.warning("authtoken invalid")
            authtoken = False

    if arguments.setup or (arguments.tokens and not authtoken):
        authtoken = {}
    if arguments.tokens:
        for token in arguments.tokens:
            phone = sorted(filter(lambda phone: ":" not in phone, phones.values()))[0]
            del phones[phone]
            authtoken[phone] = token

    return phones, authtoken


def get_api_token(arguments, use_default_app=False):
    """Get API Token from disk or environment"""
    api_token_type = collections.namedtuple("api_token", ("ID", "HASH"))

    # Allow user to use default API credintials
    # These are android ones
    if use_default_app:
        return api_token_type(2040, "b18441a1ff607e10a989891a5462e627")

    # Try to retrieve credintials from file, or from env vars
    try:
        with open(
            os.path.join(
                arguments.data_root or os.path.dirname(utils.get_base_dir()),
                "api_token.txt",
            )
        ) as f:
            api_token = api_token_type(*[line.strip() for line in f.readlines()])
    except FileNotFoundError:
        try:
            from . import api_token
        except ImportError:
            try:
                api_token = api_token_type(os.environ["api_id"], os.environ["api_hash"])
            except KeyError:
                api_token = None

    return api_token


def get_proxy(arguments):
    """Get proxy tuple from --proxy-host, --proxy-port and --proxy-secret
    and connection to use (depends on proxy - provided or not)"""
    if (
        arguments.proxy_host is not None
        and arguments.proxy_port is not None
        and arguments.proxy_secret is not None
    ):
        logging.debug("Using proxy: %s:%s", arguments.proxy_host, arguments.proxy_port)
        return (
            (arguments.proxy_host, arguments.proxy_port, arguments.proxy_secret),
            ConnectionTcpMTProxyRandomizedIntermediate,
        )

    return None, ConnectionTcpFull


def sigterm(app, signum, handler):  # skipcq: PYL-W0613
    if app is not None:
        dyno = os.environ["DYNO"]
        if dyno.startswith("web") and app.process_formation()["web"].quantity:
            # If we are just idling, start the worker, but otherwise shutdown gracefully
            app.scale_formation_process("worker-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK", 1)
        elif (
            dyno.startswith("restarter")
            and app.process_formation()[
                "restarter-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK"
            ].quantity
        ):
            # If this dyno is restarting, it means we should start the web dyno
            app.batch_scale_formation_processes(
                {
                    "web": 1,
                    "worker-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK": 0,
                    "restarter-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK": 0,
                }
            )
    # This ensures that we call atexit hooks and close FDs when Heroku kills us un-gracefully
    sys.exit(143)  # SIGTERM + 128


class SuperList(list):
    """
    Makes able: await self.allclients.send_message("foo", "bar")
    """

    def __getattribute__(self, attr):
        if hasattr(list, attr):
            return list.__getattribute__(self, attr)

        for obj in self:  # TODO: find other way
            _ = getattr(obj, attr)
            if callable(_):
                if asyncio.iscoroutinefunction(_):

                    async def foobar(*args, **kwargs):
                        return [await getattr(__, attr)(*args, **kwargs) for __ in self]

                    return foobar
                return lambda *args, **kwargs: [
                    getattr(__, attr)(*args, **kwargs) for __ in self
                ]

            return [getattr(x, attr) for x in self]


def main():  # noqa: C901
    """Main entrypoint"""
    arguments = parse_arguments()
    loop = asyncio.get_event_loop()

    clients = SuperList()
    phones, authtoken = get_phones(arguments)
    api_token = get_api_token(arguments, arguments.default_app)
    proxy, conn = get_proxy(arguments)

    if web_available:
        web = (
            core.Web(
                data_root=arguments.data_root,
                api_token=api_token,
                proxy=proxy,
                connection=conn,
                hosting=arguments.hosting,
                default_app=arguments.default_app,
            )
            if arguments.web
            else None
        )
    elif arguments.heroku_web_internal:
        raise RuntimeError("Web required but unavailable")
    else:
        web = None

    save_config_key("port", arguments.port)

    while api_token is None:
        if arguments.no_auth:
            return
        if web:
            loop.run_until_complete(web.start(arguments.port))
            print("Web mode ready for configuration")  # noqa: T001
            if not arguments.heroku_web_internal:
                port = str(web.port)
                if platform.system() == "Linux" and not os.path.exists(
                    "/etc/os-release"
                ):
                    print(f"Please visit http://localhost:{port}")
                else:
                    ipaddress = get("https://api.ipify.org").text
                    print(
                        f"Please visit http://{ipaddress}:{port} or http://localhost:{port}"
                    )
            loop.run_until_complete(web.wait_for_api_token_setup())
            api_token = web.api_token
        else:
            run_config({}, arguments.data_root)
            importlib.invalidate_caches()
            api_token = get_api_token(arguments)

    if os.environ.get("authorization_strings", False):
        if (
            os.environ.get("DYNO", False)
            or arguments.heroku_web_internal
            or arguments.heroku_deps_internal
        ):
            app, _ = heroku.get_app(
                os.environ["authorization_strings"],
                os.environ["heroku_api_token"],
                api_token,
                False,
                True,
            )
        if arguments.heroku_web_internal:
            app.scale_formation_process("worker-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK", 0)
            signal.signal(signal.SIGTERM, functools.partial(sigterm, app))
        elif arguments.heroku_deps_internal:
            try:
                app.scale_formation_process("web", 0)
                app.scale_formation_process(
                    "worker-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK", 0
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code != 404:
                    # The dynos don't exist on the very first deployment, so don't try to scale
                    raise
            else:
                atexit.register(
                    functools.partial(
                        app.scale_formation_process,
                        "restarter-DO-NOT-TURN-ON-OR-THINGS-WILL-BREAK",
                        1,
                    )
                )
        elif arguments.heroku_restart_internal:
            signal.signal(signal.SIGTERM, functools.partial(sigterm, app))
            while True:
                time.sleep(60)
        elif os.environ.get("DYNO", False):
            signal.signal(signal.SIGTERM, functools.partial(sigterm, app))

    if authtoken:
        for phone, token in authtoken.items():
            try:
                clients += [
                    TelegramClient(
                        StringSession(token),
                        api_token.ID,
                        api_token.HASH,
                        connection=conn,
                        proxy=proxy,
                        connection_retries=None,
                    ).start()
                ]
            except ValueError:
                run_config({}, arguments.data_root)
                return

            clients[-1].phone = phone  # for consistency

    if not clients and not phones:
        if arguments.no_auth:
            return

        if web:
            if not web.running.is_set():
                loop.run_until_complete(web.start(arguments.port))
                print("Web mode ready for configuration")  # noqa: T001
                if not arguments.heroku_web_internal:
                    port = str(web.port)
                    if platform.system() == "Linux" and not os.path.exists(
                        "/etc/os-release"
                    ):
                        print(f"Please visit http://localhost:{port}")
                    else:
                        ipaddress = get("https://api.ipify.org").text
                        print(
                            f"Please visit http://{ipaddress}:{port} or http://localhost:{port}"
                        )
            loop.run_until_complete(web.wait_for_clients_setup())
            arguments.heroku = web.heroku_api_token
            clients = web.clients
            for client in clients:
                if arguments.heroku:
                    session = StringSession()
                else:
                    session = SQLiteSession(
                        os.path.join(
                            arguments.data_root
                            or os.path.dirname(utils.get_base_dir()),
                            f"friendly-telegram-+{'X' * (len(client.phone) - 5)}{client.phone[-4:]}",
                        )
                    )

                session.set_dc(
                    client.session.dc_id,
                    client.session.server_address,
                    client.session.port,
                )
                session.auth_key = client.session.auth_key
                if not arguments.heroku:
                    session.save()
                client.session = session
        else:
            try:
                phone = input("Please enter your phone: ")
                phones = {phone.split(":", maxsplit=1)[0]: phone}
            except EOFError:
                print("=" * 30)
                print(
                    "Hello. If you are seeing this, it means YOU ARE DOING SOMETHING WRONG!\n"
                    "It is likely that you tried to deploy to heroku -\n"
                    "you cannot do this via the web interface.\n"
                    "\n"
                    "To deploy to heroku, go to\n"
                    "https://friendly-telegram.gitlab.io/heroku to learn more\n"
                    "\n"
                    "In addition, you seem to have forked the friendly-telegram repo. THIS IS WRONG!\n"
                    "You should remove the forked repo, and read https://friendly-telegram.gitlab.io\n"
                    "\n"
                    "If you're not using Heroku, then you are using a non-interactive prompt but\n"
                    "you have not got a session configured, meaning authentication to Telegram is\n"
                    "impossible.\n"
                    "\n"
                    "THIS ERROR IS YOUR FAULT. DO NOT REPORT IT AS A BUG!\n"
                    "Goodbye.\n"
                )

                sys.exit(1)

    for phone_id, phone in phones.items():
        if arguments.heroku:
            session = StringSession()
        else:
            session = os.path.join(
                arguments.data_root or os.path.dirname(utils.get_base_dir()),
                f"friendly-telegram{(('-' + phone_id) if phone_id else '')}",
            )

        try:
            client = TelegramClient(
                session,
                api_token.ID,
                api_token.HASH,
                connection=conn,
                proxy=proxy,
                connection_retries=None,
            )

            client.start()
            client.phone = phone

            clients.append(client)
        except sqlite3.OperationalError as ex:
            print(
                f"Error initialising phone {(phone or 'unknown')} {','.join(ex.args)}\n"  # noqa
                ": this is probably your fault. Try checking that this is the only instance running and"
                "that the session is not copied. If that doesn't help, delete the file named"
                f"'friendly-telegram-{phone if phone else ''}.session'"
            )
            continue
        except (TypeError, AuthKeyDuplicatedError):
            os.remove(f"{session}.session")
            main()
        except (ValueError, ApiIdInvalidError):
            # Bad API hash/ID
            run_config({}, arguments.data_root)
            return
        except PhoneNumberInvalidError:
            print(
                "Please check the phone number. Use international format (+XX...)"  # noqa: T001
                " and don't put spaces in it."
            )
            continue

    if arguments.heroku:
        if isinstance(arguments.heroku, str):
            key = arguments.heroku
        else:
            key = input(
                "Please enter your Heroku API key (from https://dashboard.heroku.com/account): "
            ).strip()

        app = heroku.publish(clients, key, api_token)
        print(
            "Installed to heroku successfully! Type .help in Telegram for help."
        )  # noqa: T001
        if web:
            web.redirect_url = app.web_url
            web.ready.set()
            loop.run_until_complete(web.root_redirected.wait())
        return

    loop.set_exception_handler(
        lambda _, x: logging.error(
            "Exception on event loop! %s",
            x["message"],
            exc_info=x.get("exception", None),
        )
    )

    loops = [amain_wrapper(client, clients, web, arguments) for client in clients]
    loop.run_until_complete(asyncio.gather(*loops))


async def amain_wrapper(client, *args, **kwargs):
    """Wrapper around amain so we don't have to manually clear all locals on soft restart"""
    async with client:
        first = True
        while await amain(first, client, *args, **kwargs):
            first = False


async def amain(first, client, allclients, web, arguments):
    """Entrypoint for async init, run once for each user"""
    setup = arguments.setup
    web_only = arguments.web_only
    client.parse_mode = "HTML"
    await client.start()

    handlers = logging.getLogger().handlers
    db = backend.CloudBackend(client)

    if setup:
        await db.init(lambda e: None)
        jdb = await db.do_download()

        try:
            pdb = json.loads(jdb)
        except (json.decoder.JSONDecodeError, TypeError):
            pdb = {}

        modules = loader.Modules(arguments.use_inline)
        babelfish = Translator([], [], arguments.data_root)
        await babelfish.init(client)
        modules.register_all(babelfish)
        fdb = frontend.Database(db, True)
        await fdb.init()
        modules.send_config(fdb, babelfish)
        await modules.send_ready(
            client, fdb, allclients
        )  # Allow normal init even in setup

        for handler in handlers:
            handler.setLevel(50)

        pdb = run_config(
            pdb,
            arguments.data_root,
            getattr(client, "phone", "Unknown Number"),
            modules,
        )

        if pdb is None:
            await client(DeleteChannelRequest(db.db))
            return

        try:
            await db.do_upload(json.dumps(pdb))
        except MessageNotModifiedError:
            pass

        return False

    db = frontend.Database(
        db, arguments.heroku_deps_internal or arguments.docker_deps_internal
    )
    await db.init()

    logging.debug("got db")
    logging.info("Loading logging config...")
    for handler in handlers:
        handler.setLevel(db.get(__name__, "loglevel", logging.WARNING))

    to_load = None
    if arguments.heroku_deps_internal or arguments.docker_deps_internal:
        to_load = ["loader.py"]

    babelfish = Translator(
        db.get(__name__, "langpacks", []),
        db.get(__name__, "language", ["en"]),
        arguments.data_root,
    )

    await babelfish.init(client)

    modules = loader.Modules()
    no_nickname = arguments.no_nickname

    if not (arguments.heroku_deps_internal or arguments.docker_deps_internal):
        if web:
            await web.add_loader(client, modules, db)
            await web.start_if_ready(len(allclients), arguments.port)
        if not web_only:
            dispatcher = CommandDispatcher(modules, db, no_nickname)
            client.dispatcher = dispatcher
    if arguments.heroku_deps_internal or arguments.docker_deps_internal:
        # Loader has installed all dependencies
        return  # We are done

    if not web_only:
        await dispatcher.init(client)
        modules.check_security = dispatcher.check_security

        client.add_event_handler(dispatcher.handle_incoming, events.NewMessage)

        client.add_event_handler(dispatcher.handle_incoming, events.ChatAction)

        client.add_event_handler(
            dispatcher.handle_command, events.NewMessage(forwards=False)
        )

        client.add_event_handler(dispatcher.handle_command, events.MessageEdited())

    modules.register_all(babelfish, to_load)

    modules.send_config(db, babelfish)

    await modules.send_ready(client, db, allclients)

    if first:
        try:
            import git

            repo = git.Repo()

            build = repo.heads[0].commit.hexsha
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            upd = r"\33[31mUpdate required" if diff else r"Up-to-date"

            termux = bool(
                os.popen('echo $PREFIX | grep -o "com.termux"').read()
            )  # skipcq: BAN-B605, BAN-B607
            is_heroku = os.environ.get("DYNO", False)

            _platform = r"Termux" if termux else (r"Heroku" if is_heroku else "VDS")

            logo1 = f"""
                                      )
                   (               ( /(
                   ) )   (   (    )())
                  (()/(   )  ) |((_)
                   /((_)_((_)((_)|_((_)
                  (_)/ __| __| __| |/ /
                    | (_ | _|| _|  ' <
                      ___|___|___|_|_\\

                     • Build: {build[:7]}
                     • Version: {'.'.join(list(map(str, list(__version__))))}
                     • {upd}
                     • Platform: {_platform}
                     - Started for {(await client.get_me(True)).user_id} -"""

            print(logo1)

            logging.info(f"=== BUILD: {build} ===")
            logging.info(
                f"=== VERSION: {'.'.join(list(map(str, list(__version__))))} ==="
            )
            logging.info(
                f"=== PLATFORM: {'Termux' if termux else ('Heroku' if is_heroku else 'VDS')} ==="
            )
        except Exception:
            logging.exception(
                "Badge error"
            )  # This part is not so necessary, so if error occures, ignore it

    await client.run_until_disconnected()

    # Previous line will stop code execution, so this part is
    # reached only when client is by some reason disconnected
    # At this point we need to close database
    await db.close()
    return False
