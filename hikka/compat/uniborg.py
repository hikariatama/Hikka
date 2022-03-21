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

# pylint: disable=R,C,W0613,W0212 # This is bad code, just let it be.

import asyncio
import datetime
import logging
import re
import sys
import tempfile
from functools import wraps

import telethon

from .util import get_cmd_name, MarkdownBotPassthrough
from .. import loader

logger = logging.getLogger(__name__)


class UniborgClient(MarkdownBotPassthrough):
    instance_count = 0

    class __UniborgShimMod__Base(loader.Module):
        def __init__(self, borg):
            super().__init__()
            self._borg = borg
            self.commands = borg._commands
            for func in self.commands.values():
                func.__self__ = self
            self.strings = {"name": f"UniBorg{str(self._borg.instance_id)}"}
            self.__module__ = borg._module
            self._client = None

        async def watcher(self, message):
            for w in self._borg._watchers:
                await w(message)

        async def client_ready(self, client, db):
            self._client = client
            self._borg.__under = client

    def registerfunc(self, _):
        self._wrapper = type(
            f"UniborgShim__{self._module}", (self.__UniborgShimMod__Base,), {}
        )(self)

        return self._wrapper

    def __init__(self, module_name):  # skipcq: PYL-W0231
        self.instance_id = -1
        self._storage = None
        self._config = UniborgConfig()
        self._commands = {}
        self._watchers = []
        self._unknowns = []
        self._wrapper = None  # Set in registerfunc
        self._module = module_name
        sys.modules[self._module].__dict__["logger"] = logging.getLogger(self._module)
        sys.modules[self._module].__dict__["storage"] = self._storage
        sys.modules[self._module].__dict__["Config"] = self._config

    def _ensure_unknowns(self):
        self._commands[f"borgcmd{str(self.instance_id)}"] = self._unknown_command()

    def _unknown_command(self):
        # this way, the `self` is wrapped as a nonlocal, so __self__ can be modified
        def _unknown_command_inner(message):
            message.message = (
                "." + message.message[len(f"borgcmd{str(self.instance_id)}") + 1 :]
            )

            return asyncio.gather(*[uk(message, "") for uk in self._unknowns])

        return _unknown_command_inner

    def on(self, event):  # noqa: C901 # legacy code that works fine
        if self.instance_id < 0:
            type(self).instance_count += 1
            self.instance_id = type(self).instance_count

        def subreg(func):
            logger.debug(event)

            self._module = func.__module__
            sys.modules[self._module].__dict__["register"] = self.registerfunc

            if event.outgoing:
                # Command based thing
                use_unknown = False
                if not event.pattern:
                    self._ensure_unknowns()
                    use_unknown = True

                cmd = get_cmd_name(event.pattern.__self__.pattern)

                if not cmd:
                    self._ensure_unknowns()
                    use_unknown = True

                @wraps(func)
                def commandhandler(message, pre="."):
                    """Closure to execute command when handler activated and regex matched"""
                    logger.debug("Command triggered")
                    if match := re.match(
                        event.pattern.__self__.pattern, pre + message.message, re.I
                    ):
                        logger.debug("and matched")
                        message.message = (
                            pre + message.message
                        )  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)
                        # Put it off as long as possible so event handlers register
                        sys.modules[self._module].__dict__[
                            "borg"
                        ] = MarkdownBotPassthrough(self._wrapper._client)

                        return func(event2)
                    else:
                        logger.debug(
                            (
                                f"but not matched cmd {message.message} regex "
                                + event.pattern.__self__.pattern
                            )
                        )

                if use_unknown:
                    self._unknowns += [commandhandler]
                else:
                    if commandhandler.__doc__ is None:
                        commandhandler.__doc__ = "Undocumented external command"

                    self._commands[cmd] = commandhandler
            elif event.incoming:

                @wraps(func)
                def watcherhandler(message):
                    """Closure to execute watcher when handler activated and regex matched"""
                    if match := re.match(
                        event.pattern.__self__.pattern, message.message, re.I
                    ):
                        logger.debug("and matched")
                        message.message = (
                            message.message
                        )  # Framework strips prefix, give them a generic one
                        event2 = MarkdownBotPassthrough(message)
                        # Try to emulate the expected format for an event
                        event2.pattern_match = match
                        event2.message = MarkdownBotPassthrough(message)

                        return func(event2)

                    return asyncio.gather()

                # Return a coroutine
                self._watchers += [
                    watcherhandler
                ]  # Add to list of watchers so we can call later.
            else:
                logger.error("event not incoming or outgoing")
                return func

            return func

        return subreg


class Uniborg:
    def __init__(self, clients):
        self.__all__ = "util"


class UniborgUtil:
    def __init__(self, clients):
        self._clients = clients

    def admin_cmd(self, *args, **kwargs):
        """Uniborg uses this for sudo users but we don't have that concept."""
        if len(args) > 0:
            if len(args) != 1:
                raise TypeError("Takes exactly 0 or 1 args")

            kwargs["pattern"] = args[0]
        else:
            kwargs.setdefault("pattern", ".*")

        if not (
            kwargs["pattern"].startswith(".") or kwargs["pattern"].startswith(r"\.")
        ):
            kwargs["pattern"] = r"\." + kwargs["pattern"]

        if "incoming" not in kwargs.keys() and "outgoing" not in kwargs.keys():
            kwargs["outgoing"] = True

        if "allow_sudo" in kwargs.keys():
            del kwargs["allow_sudo"]

        return telethon.events.NewMessage(**kwargs)

    async def progress(self, *args, **kwargs):
        pass

    async def is_read(self, *args, **kwargs):
        return False  # Meh.

    def humanbytes(self, size):
        return f"{str(size)} bytes"

    def time_formatter(self, ms):
        return str(datetime.timedelta(milliseconds=ms))


class UniborgConfig:
    __all__ = [
        "GOOGLE_CHROME_BIN",
        "SCREEN_SHOT_LAYER_ACCESS_KEY",
        "PRIVATE_GROUP_BOT_API_ID",
        "IBM_WATSON_CRED_URL",
        "IBM_WATSON_CRED_PASSWORD",
        "TELEGRAPH_SHORT_NAME",
        "OCR_SPACE_API_KEY",
        "G_BAN_LOGGER_GROUP",
        "TG_GLOBAL_ALBUM_LIMIT",
        "TG_BOT_TOKEN_BF_HER",
        "TG_BOT_USER_NAME_BF_HER",
        "ANTI_FLOOD_WARN_MODE",
        "GIT_REPO_NAME",
        "MAX_ANTI_FLOOD_MESSAGES",
        "CHATS_TO_MONITOR_FOR_ANTI_FLOOD",
        "REM_BG_API_KEY",
        "NO_P_M_SPAM",
        "MAX_FLOOD_IN_P_M_s",
        "NC_LOG_P_M_S",
        "PM_LOGGR_BOT_API_ID",
        "DB_URI",
        "NO_OF_BUTTONS_DISPLAYED_IN_H_ME_CMD",
        "COMMAND_HAND_LER",
        "SUDO_USERS",
        "G_DRIVE_CLIENT_ID",
        "G_DRIVE_CLIENT_SECRET",
        "G_DRIVE_AUTH_TOKEN_DATA",
        "TELE_GRAM_2FA_CODE",
        "GROUP_REG_SED_EX_BOT_S",
        "GOOGLE_CHROME_DRIVER",
        "OPEN_WEATHER_MAP_APPID",
        "GITHUB_ACCESS_TOKEN",
        "GIT_USER_NAME",
    ]

    GOOGLE_CHROME_BIN = None
    SCREEN_SHOT_LAYER_ACCESS_KEY = None
    PRIVATE_GROUP_BOT_API_ID = None
    IBM_WATSON_CRED_URL = None
    IBM_WATSON_CRED_PASSWORD = None
    TELEGRAPH_SHORT_NAME = "UniborgShimFriendlyTelegram"
    OCR_SPACE_API_KEY = None
    G_BAN_LOGGER_GROUP = None
    TG_BOT_TOKEN_BF_HER = None  # Oh yes, her bf (botfather owo)
    TG_BOT_USER_NAME_BF_HER = None
    ANTI_FLOOD_WARN_MODE = None
    MAX_ANTI_FLOOD_MESSAGES = 10
    CHATS_TO_MONITOR_FOR_ANTI_FLOOD = []
    REM_BG_API_KEY = None
    NO_P_M_SPAM = False
    MAX_FLOOD_IN_P_M_s = 3  # Default from spechide
    NC_LOG_P_M_S = False
    PM_LOGGR_BOT_API_ID = -100
    DB_URI = None
    NO_OF_BUTTONS_DISPLAYED_IN_H_ME_CMD = 5
    COMMAND_HAND_LER = r"\."
    SUDO_USERS = set()  # Don't add anyone here!
    G_DRIVE_CLIENT_ID = None
    G_DRIVE_CLIENT_SECRET = None
    G_DRIVE_AUTH_TOKEN_DATA = None
    TELE_GRAM_2FA_CODE = None
    GROUP_REG_SED_EX_BOT_S = None
    GOOGLE_CHROME_DRIVER = None
    OPEN_WEATHER_MAP_APPID = None

    # === SNIP ===
    # this stuff should never get changed, because its either unused, stupid or dangerous.
    TMP_DOWNLOAD_DIRECTORY = tempfile.mkdtemp()
    MAX_MESSAGE_SIZE_LIMIT = 4095
    UB_BLACK_LIST_CHAT = set()
    LOAD = []
    NO_LOAD = []
    CHROME_DRIVER = GOOGLE_CHROME_DRIVER
    CHROME_BIN = GOOGLE_CHROME_BIN
    TEMP_DIR = TMP_DOWNLOAD_DIRECTORY
    TG_GLOBAL_ALBUM_LIMIT = 9  # What does this do o.O?
    GITHUB_ACCESS_TOKEN = None
    GIT_REPO_NAME = None
    GIT_USER_NAME = None
