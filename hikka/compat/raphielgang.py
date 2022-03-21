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

# pylint: disable=R,C,W0613 # This is bad code, just let it be. We will delete it at some point, perhaps?

import asyncio
import inspect
import logging
import re
import sys
from functools import wraps

try:
    import pymongo
    import redis
except ImportError:
    logging.debug("Unable to load database modules for compat")

from .. import loader
from .util import get_cmd_name, MarkdownBotPassthrough

logger = logging.getLogger(__name__)


class RaphielgangConfig:
    def __init__(self, clients):
        self.__all__ = [
            "bots",
            "API_KEY",
            "API_HASH",
            "CONSOLE_LOGGER_VERBOSE",
            "LOGS",
            "BOTLOG_CHATID",
            "BOTLOG",
            "PM_AUTO_BAN",
            "DB_URI",
            "OCR_SPACE_API_KEY",
            "REM_BG_API_KEY",
            "CHROME_DRIVER",
            "GOOGLE_CHROME_BIN",
            "OPEN_WEATHER_MAP_APPID",
            "WELCOME_MUTE",
            "ANTI_SPAMBOT",
            "ANTI_SPAMBOT_SHOUT",
            "YOUTUBE_API_KEY",
            "CLEAN_WELCOME",
            "BIO_PREFIX",
            "DEFAULT_BIO",
            "LASTFM_API",
            "LASTFM_SECRET",
            "LASTFM_USERNAME",
            "LASTFM_PASSWORD_PLAIN",
            "LASTFM_PASS",
            "lastfm",
            "G_DRIVE_CLIENT_ID",
            "G_DRIVE_CLIENT_SECRET",
            "G_DRIVE_AUTH_TOKEN_DATA",
            "GDRIVE_FOLDER_ID",
            "TEMP_DOWNLOAD_DIRECTORY",
            "COUNT_MSG",
            "USERS",
            "COUNT_PM",
            "LASTMSG",
            "ENABLE_KILLME",
            "CMD_HELP",
            "AFKREASON",
            "ZALG_LIST",
            "BRAIN_CHECKER",
            "CURRENCY_API",
            "SPOTIFY_USERNAME",
            "SPOTIFY_PASS",
            "ISAFK",
            "ALIVE_NAME",
            "LOGGER_GROUP",
            "HELPER",
            "MONGO_URI",
            "GENIUS_API_TOKEN",
            "FORCE_REDIS_AVAIL",
            "FORCE_MONGO_AVAIL",
        ]

        self.bots = clients

        # pylint: disable=C0103
        # Static 'cos I cba
        self.API_KEY = 12345
        self.API_HASH = "0123456789abcdef0123456789abcdef"
        self.CONSOLE_LOGGER_VERBOSE = False
        self.LOGS = logging.getLogger("raphielgang-compat")
        self.BOTLOG_CHATID = 0
        self.BOTLOG = False
        self.PM_AUTO_BAN = False
        self.DB_URI = None
        self.OCR_SPACE_API_KEY = None
        self.REM_BG_API_KEY = None
        self.CHROME_DRIVER = None
        self.GOOGLE_CHROME_BIN = None
        self.OPEN_WEATHER_MAP_APPID = None
        self.WELCOME_MUTE = False
        self.ANTI_SPAMBOT = False
        self.ANTI_SPAMBOT_SHOUT = False
        self.YOUTUBE_API_KEY = None
        self.CLEAN_WELCOME = None
        self.BIO_PREFIX = None
        self.DEFAULT_BIO = None
        self.LASTFM_API = None
        self.LASTFM_SECRET = None
        self.LASTFM_USERNAME = None
        self.LASTFM_PASSWORD_PLAIN = None
        self.LASTFM_PASS = None
        self.lastfm = None
        self.G_DRIVE_CLIENT_ID = None
        self.G_DRIVE_CLIENT_SECRET = None
        self.G_DRIVE_AUTH_TOKEN_DATA = None
        self.GDRIVE_FOLDER_ID = None
        self.TEMP_DOWNLOAD_DIRECTORY = "./downloads"
        self.COUNT_MSG = 0
        self.USERS = {}
        self.COUNT_PM = {}
        self.LASTMSG = {}
        self.ENABLE_KILLME = False
        self.CMD_HELP = {}
        self.AFKREASON = "no reason"
        self.ZALG_LIST = [
            [
                "̖",
                " ̗",
                " ̘",
                " ̙",
                " ̜",
                " ̝",
                " ̞",
                " ̟",
                " ̠",
                " ̤",
                " ̥",
                " ̦",
                " ̩",
                " ̪",
                " ̫",
                " ̬",
                " ̭",
                " ̮",
                " ̯",
                " ̰",
                " ̱",
                " ̲",
                " ̳",
                " ̹",
                " ̺",
                " ̻",
                " ̼",
                " ͅ",
                " ͇",
                " ͈",
                " ͉",
                " ͍",
                " ͎",
                " ͓",
                " ͔",
                " ͕",
                " ͖",
                " ͙",
                " ͚",
                " ",
            ],
            [
                " ̍",
                " ̎",
                " ̄",
                " ̅",
                " ̿",
                " ̑",
                " ̆",
                " ̐",
                " ͒",
                " ͗",
                " ͑",
                " ̇",
                " ̈",
                " ̊",
                " ͂",
                " ̓",
                " ̈́",
                " ͊",
                " ͋",
                " ͌",
                " ̃",
                " ̂",
                " ̌",
                " ͐",
                " ́",
                " ̋",
                " ̏",
                " ̽",
                " ̉",
                " ͣ",
                " ͤ",
                " ͥ",
                " ͦ",
                " ͧ",
                " ͨ",
                " ͩ",
                " ͪ",
                " ͫ",
                " ͬ",
                " ͭ",
                " ͮ",
                " ͯ",
                " ̾",
                " ͛",
                " ͆",
                " ̚",
            ],
            [
                " ̕",
                " ̛",
                " ̀",
                " ́",
                " ͘",
                " ̡",
                " ̢",
                " ̧",
                " ̨",
                " ̴",
                " ̵",
                " ̶",
                " ͜",
                " ͝",
                " ͞",
                " ͟",
                " ͠",
                " ͢",
                " ̸",
                " ̷",
                " ͡",
            ],
        ]
        self.BRAIN_CHECKER = []
        self.is_mongo_alive = lambda: self.MONGO_URI is not None
        self.is_redis_alive = lambda: self.REDIS.ping()
        self.CURRENCY_API = None
        self.SPOTIFY_USERNAME = None
        self.SPOTIFY_PASS = None
        self.ISAFK = False
        self.ALIVE_NAME = (
            "`**PPE bad! Use **[friendly-telegram](https://t.me/friendlytgbot)`."
        )

        self.GDRIVE_FOLDER = self.GDRIVE_FOLDER_ID
        self.GENIUS_API_TOKEN = ""

        # And some for "AliHasan7671"
        self.LOGGER_GROUP = 0
        self.HELPER = {}  # What is this even?

        self.FORCE_REDIS_AVAIL = False
        self.FORCE_MONGO_AVAIL = False

        # Databases
        def is_mongo_alive():
            if self.FORCE_MONGO_AVAIL:
                return True
            if self.MONGO_URI is None:
                return False
            try:
                return self.MONGOCLIENT.ismongos is not None
            except pymongo.errors.ServerSelectionTimeoutError:
                return False

        self.is_mongo_alive = is_mongo_alive

        def is_redis_alive():
            if self.FORCE_REDIS_AVAIL:
                return True
            try:
                self.REDIS.ping()
            except redis.exceptions.ConnectionError:
                return False
            else:
                return True

        self.is_redis_alive = is_redis_alive
        # pylint: enable=C0103

        self.__passthrus = []
        self.mongoclient = None

    @property
    def bot(self):
        if not len(self.__passthrus):
            self.__passthrus += [
                MarkdownBotPassthrough(self.bots[0] if len(self.bots) else None)
            ]
        return self.__passthrus[0]

    @property
    def MONGOCLIENT(self):
        if self.MONGO_URI is not None and self.mongoclient is None:
            self.mongoclient = pymongo.MongoClient(
                self.MONGO_URI, 27017, serverSelectionTimeoutMS=1
            )
        return self.mongoclient

    @property
    def MONGO(self):
        if self.MONGOCLIENT is not None:
            return self.MONGOCLIENT.userbot

    @property
    def REDIS(self):
        return redis.StrictRedis(host="localhost", port=6379, db=0)

    async def client_ready(self, client):
        self.bots += [client]
        logging.debug(len(self.__passthrus))
        logging.debug(len(self.bots))
        try:
            self.__passthrus[
                len(self.bots) - 1
            ].__under = client  # pylint:disable=W0212 # Ewwww, but needed
        except IndexError:
            pass


# The core machinery will fail to identify any register() function in the module.
# So we need to introspect the module and add register(), and a shimmed class to store state

# Please don't refactor this class. Even while writing it only God knew how it worked.


__hours_wasted_here = 6


# // don't touch
class RaphielgangEvents:
    def __init__(self, clients):
        self.instances = {}

    class RaphielgangEventsSub:
        class __RaphielgangShimMod__Base(loader.Module):
            instance_count = 0

            # E1101 is triggered because pylint thinks that inspect.getmro(type(self))[1] means
            # type(super()), and it's correct, but this is a base class and is never used. As a result, pylint
            # incorrectly thinks that type(super()) resolves to loader.Module, and can't find .instance_count.
            # Perhaps there's a way to annotate it? I don't think so.

            def __init__(self, events_instance):
                super().__init__()
                inspect.getmro(type(self))[
                    1
                ].instance_count += 1  # pylint: disable=E1101 # See above
                self.instance_id = inspect.getmro(type(self))[
                    1
                ].instance_count  # pylint: disable=E1101 # See above
                self._events = events_instance
                self.commands = events_instance.commands
                for func in self.commands.values():
                    if hasattr(func, "__self__"):
                        func.__self__.__module__ = events_instance.module
                    else:
                        func.__self__ = self
                self.strings = {"name": f"RaphielGang{str(self.instance_id)}"}
                self.unknowns = events_instance.unknowns
                self.__module__ = events_instance.module

            async def watcher(self, message):
                for watcher in self._events.watchers:
                    await watcher(message)

        def __init__(self):
            self.module = None
            self._setup_complete = False
            self.watchers = []
            self.commands = {}
            self.unknowns = []
            self.instance_id = -1

        def _ensure_unknowns(self):
            self.commands[f"raphcmd{str(self.instance_id)}"] = self._unknown_command

        def _unknown_command(self, message):
            """A command that could not be understood by the compat system, you must put the raw command after."""
            message.message = message.message[
                len(f"raphcmd{str(self.instance_id)}") + 1 :
            ]
            return asyncio.gather(*[uk(message, "") for uk in self.unknowns])

        def register(self, *args, **kwargs):  # noqa: C901 # legacy code that works fine
            if len(args) == 1 and args[0] is True:
                # This is the register() function in normal ftg modules
                # Create a fake type, instantiate it with our own self
                return type(
                    "RaphielgangShim__" + self.module,
                    (self.__RaphielgangShimMod__Base,),
                    {},
                )(self)

            def subreg(func):  # ALWAYS return func.
                logger.debug(kwargs)
                sys.modules[func.__module__].__dict__["registration"] = self.register
                if not self._setup_complete:
                    self.module = func.__module__
                    self._setup_complete = True
                if kwargs.get("outgoing", False) or not kwargs.get("incoming", False):
                    # Command-based thing
                    use_unknown = False
                    if "pattern" not in kwargs.keys():
                        self._ensure_unknowns()
                        use_unknown = True
                    else:
                        cmd = get_cmd_name(kwargs["pattern"])
                        if not cmd:
                            self._ensure_unknowns()
                            use_unknown = True

                    @wraps(func)
                    def commandhandler(message, pre="."):
                        """Closure to execute command when handler activated and regex matched"""
                        logger.debug("Command triggered")
                        # Framework strips prefix, give them a generic one
                        message.message = pre + message.message
                        match = re.match(
                            kwargs.get("pattern", r"^\b$"), message.message, re.I
                        )
                        if "pattern" not in kwargs or match:
                            logger.debug("and matched")
                            event = MarkdownBotPassthrough(message)
                            # Try to emulate the expected format for an event
                            event.pattern_match = match
                            event.message = message
                            return func(event)  # Return a coroutine
                        else:
                            logger.debug(
                                "but not matched "
                                + message.message
                                + " / "
                                + kwargs.get("pattern", "None")
                            )
                            return asyncio.gather()  # passthru coro

                    if use_unknown:
                        self.unknowns += [commandhandler]
                    else:
                        if commandhandler.__doc__ is None:
                            commandhandler.__doc__ = "Undocumented external command"
                        self.commands[
                            cmd
                        ] = commandhandler  # Add to list of commands so we can call later
                elif kwargs.get("incoming", False):
                    # Watcher-based thing

                    @wraps(func)
                    def subwatcher(message):
                        """Closure to execute watcher when handler activated and regex matched"""
                        match = re.match(
                            message.message, kwargs.get("pattern", r"^\b$"), re.I
                        )
                        if "pattern" not in kwargs or match:
                            event = message
                            # Try to emulate the expected format for an event
                            event = MarkdownBotPassthrough(message)
                            # Try to emulate the expected format for an event
                            event.pattern_match = match
                            event.message = MarkdownBotPassthrough(message)
                            return func(event)  # Return a coroutine
                        return asyncio.gather()

                    self.watchers += [
                        subwatcher
                    ]  # Add to list of watchers so we can call later.
                else:
                    logger.error("event not incoming or outgoing or neither or both")
                    return func
                return func

            self.instance_id = kwargs["__instance_number"]
            return subreg

    def register(self, *args, **kwargs):
        if len(args) == 1:
            logger.debug("Register for %s", args[0])
            return self.instances[args[0]].register(
                True
            )  # Passthrough if we have enough info
        elif len(args) != 0:
            logger.error(args)
            raise TypeError("Takes at most one parameter")

        def subreg(func):
            if func.__module__ not in self.instances:
                self.instances[func.__module__] = self.RaphielgangEventsSub()
            kwargs["__instance_number"] = list(self.instances.keys()).index(
                func.__module__
            )
            return self.instances[func.__module__].register(**kwargs)(func)

        return subreg

    def errors_handler(self, func):
        """Do nothing as this is handled by ftg framework by default"""
        return func

    async def client_ready(self, client):
        pass


class RaphielgangDatabase:
    @staticmethod
    def __new__(cls, *args, **kwargs):
        try:
            from . import dbhelper
        except ImportError:
            return super().__new__(cls)
        else:
            return dbhelper

    def __init__(self, clients):
        self._clients = clients
