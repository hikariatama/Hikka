# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import builtins
import importlib
import inspect
import io
import logging
import os
import subprocess
import sys
import traceback
import typing
from io import BytesIO
from sys import version_info

import git

try:
    from PIL import Image
except Exception:
    PIP_AVAILABLE = False
else:
    PIP_AVAILABLE = True

from hikkapyro import Client, errors, types

from .. import version
from .._internal import restart
from ..database import Database
from ..tl_cache import CustomTelegramClient
from ..types import JSONSerializable

DRAGON_EMOJI = "<emoji document_id=5375360100196163660>🐲</emoji>"

native_import = builtins.__import__
logger = logging.getLogger(__name__)


class ImportLock:
    # This is used to ensure, that dynamic dragon import passes in
    # the right client. Whenever one of the clients attempts to install
    # dragon-specific module, it must aqcuire the `import_lock` or wait
    # until it's released. Then set the `current_client` variable to self.

    def __init__(self):
        self.lock = asyncio.Lock()
        self.current_client = None

    def __call__(self, client: CustomTelegramClient) -> typing.ContextManager:
        self.current_client = client
        return self

    async def __aenter__(self):
        await self.lock.acquire()

    async def __aexit__(self, *_):
        self.current_client = None
        self.lock.release()


import_lock = ImportLock()


class DragonDb:
    def __init__(self, db: Database):
        self.db = db

    def get(
        self,
        module: str,
        variable: str,
        default: typing.Optional[typing.Any] = None,
    ) -> JSONSerializable:
        return self.db.get(f"dragon.{module}", variable, default)

    def set(self, module: str, variable: str, value: JSONSerializable) -> bool:
        return self.db.set(f"dragon.{module}", variable, value)

    def get_collection(self, module: str) -> typing.Dict[str, JSONSerializable]:
        return dict.get(self.db, f"dragon.{module}", {})

    def remove(self, module: str, variable: str) -> JSONSerializable:
        if f"dragon.{module}" not in self.db:
            return None

        return self.db[f"dragon.{module}"].pop(variable, None)

    def close(self):
        pass


class DragonDbWrapper:
    def __init__(self, db: DragonDb):
        self.db = db


class Notifier:
    def __init__(self, modules_help: "ModulesHelpDict"):
        self.modules_help = modules_help
        self.cache = {}

    def __enter__(self):
        self.modules_help.notifier = self
        return self

    def __exit__(self, *_):
        self.modules_help.notifier = None

    def notify(self, key: str, value: dict):
        self.cache[key] = value

    @property
    def modname(self):
        return next(iter(self.cache), "Unknown")

    @property
    def commands(self):
        return {
            key.split()[0]: (
                (key.split()[1] + " - ") if len(key.split()) > 1 else ""
            ) + value
            for key, value in self.cache[self.modname].items()
        }


class ModulesHelpDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notifier = None

    def append(self, obj: dict):
        # convert help from old to new type
        module_name = list(obj.keys())[0]
        cmds = obj[module_name]
        commands = {}
        for cmd in cmds:
            cmd_name = list(cmd.keys())[0]
            cmd_desc = cmd[cmd_name]
            commands[cmd_name] = cmd_desc
        self[module_name] = commands

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.notifier:
            self.notifier.notify(key, value)

    def get_notifier(self) -> Notifier:
        return Notifier(self)


class DragonMisc:
    def __init__(self, client: CustomTelegramClient):
        self.client = client
        self.modules_help = ModulesHelpDict()
        self.requirements_list = []

        self.python_version = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"

        self.gitrepo = git.Repo(
            path=os.path.abspath(os.path.join(os.path.dirname(version.__file__), ".."))
        )
        self.commits_since_tag = 0
        self.userbot_version = version.__version__

    @property
    def prefix(self):
        return self.client.loader.get_prefix("dragon")


class DragonConfig:
    def __init__(self, client: CustomTelegramClient):
        self.api_id = client.api_id
        self.api_hash = client.api_hash

        self.db_type = ""
        self.db_url = ""
        self.db_name = ""

        self.test_server = False


class DragonScripts:
    def __init__(self, misc: DragonMisc):
        self.interact_with_to_delete = []
        self.misc = misc

    @staticmethod
    def text(message: types.Message):
        return message.text if message.text else message.caption

    @staticmethod
    def restart():
        restart()

    @staticmethod
    def format_exc(e: Exception, hint: str = None):
        traceback.print_exc()
        if isinstance(e, errors.RPCError):
            return (
                "<b>Telegram API error!</b>\n"
                f"<code>[{e.CODE} {e.ID or e.NAME}] - {e.MESSAGE}</code>"
            )

        hint_text = f"\n\n<b>Hint: {hint}</b>" if hint else ""

        return f"<b>Error!</b>\n<code>{e.__class__.__name__}: {e}</code>" + hint_text

    @staticmethod
    def with_reply(func):
        async def wrapped(client: Client, message: types.Message):
            if not message.reply_to_message:
                await message.edit("<b>Reply to message is required</b>")
            else:
                return await func(client, message)

        return wrapped

    async def interact_with(self, message: types.Message) -> types.Message:
        """
        Check history with bot and return bot's response
        Example:
        .. code-block:: python
            bot_msg = await interact_with(await bot.send_message("@BotFather", "/start"))
        :param message: already sent message to bot
        :return: bot's response
        """

        await asyncio.sleep(1)
        # noinspection PyProtectedMember
        response = await message._client.get_history(message.chat.id, limit=1)
        seconds_waiting = 0

        while response[0].from_user.is_self:
            seconds_waiting += 1
            if seconds_waiting >= 5:
                raise RuntimeError("bot didn't answer in 5 seconds")

            await asyncio.sleep(1)
            # noinspection PyProtectedMember
            response = await message._client.get_history(message.chat.id, limit=1)

        self.interact_with_to_delete.append(message.message_id)
        self.interact_with_to_delete.append(response[0].message_id)

        return response[0]

    def format_module_help(self, module_name: str):
        commands = self.misc.modules_help[module_name]

        help_text = (
            f"{DRAGON_EMOJI} <b>Help for"
            f" </b><code>{module_name}</code>\n\n<b>Usage:</b>\n"
        )

        for command, desc in commands.items():
            cmd = command.split(maxsplit=1)
            args = " <code>" + cmd[1] + "</code>" if len(cmd) > 1 else ""
            help_text += (
                f"<code>{self.misc.prefix}{cmd[0]}</code>{args} — <i>{desc}</i>\n"
            )

        return help_text

    def format_small_module_help(self, module_name: str):
        commands = self.misc.modules_help[module_name]

        help_text = (
            f"{DRAGON_EMOJI }<b>Help for </b><code>{module_name}</code>\n\n<b>Commands"
            " list:</b>\n"
        )

        for command in commands:
            cmd = command.split(maxsplit=1)
            args = " <code>" + cmd[1] + "</code>" if len(cmd) > 1 else ""
            help_text += f"<code>{self.misc.prefix}{cmd[0]}</code>{args}\n"

        help_text += (
            f"\n<b>Get full usage:</b> <code>{self.misc.prefix}help"
            f" {module_name}</code>"
        )

        return help_text

    def import_library(
        self,
        library_name: str,
        package_name: typing.Optional[str] = None,
    ):
        """
        Loads a library, or installs it in ImportError case
        :param library_name: library name (import example...)
        :param package_name: package name in PyPi (pip install example)
        :return: loaded module
        """
        if package_name is None:
            package_name = library_name

        self.misc.requirements_list.append(package_name)

        try:
            return importlib.import_module(library_name)
        except ImportError:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-q",
                    "--disable-pip-version-check",
                    "--no-warn-script-location",
                    *(
                        ["--user"]
                        if "PIP_TARGET" not in os.environ
                        and "VIRTUAL_ENV" not in os.environ
                        else []
                    ),
                    package_name,
                ],
                check=False,
            )

            if completed.returncode != 0:
                raise RuntimeError(
                    f"Failed to install library {package_name} (pip exited with code"
                    f" {completed.returncode})"
                )

            return importlib.import_module(library_name)

    @staticmethod
    def resize_image(
        input_img: typing.Union[bytes, io.BytesIO],
        output: typing.Optional[io.BytesIO] = None,
        img_type: str = "PNG",
    ) -> io.BytesIO:
        if not PIP_AVAILABLE:
            raise RuntimeError("Install Pillow with: pip install Pillow -U")

        if output is None:
            output = BytesIO()
            output.name = f"sticker.{img_type.lower()}"

        with Image.open(input_img) as img:
            # We used to use thumbnail(size) here, but it returns with a *max* dimension of 512,512
            # rather than making one side exactly 512 so we have to calculate dimensions manually :(
            if img.width == img.height:
                size = (512, 512)
            elif img.width < img.height:
                size = (max(512 * img.width // img.height, 1), 512)
            else:
                size = (512, max(512 * img.height // img.width, 1))

            img.resize(size).save(output, img_type)

        return output


class DragonCompat:
    def __init__(self, client: CustomTelegramClient):
        self.client = client
        self.db = DragonDbWrapper(DragonDb(client.loader.db))
        self.misc = DragonMisc(client)
        self.scripts = DragonScripts(self.misc)
        self.config = DragonConfig(client)


def patched_import(name: str, *args, **kwargs):
    caller = inspect.currentframe().f_back
    caller_name = caller.f_globals.get("__name__")
    if name.startswith("utils") and caller_name.startswith("dragon"):
        if not import_lock.current_client:
            raise RuntimeError("Dragon client not set")

        if name.split(".", maxsplit=1)[1] in {"db", "misc", "scripts", "config"}:
            return getattr(
                import_lock.current_client.dragon_compat,
                name.split(".", maxsplit=1)[1],
            )

        raise ImportError(f"Unknown module {name}")

    if name.startswith("telethon"):
        return native_import("hikkatl" + name[8:], *args, **kwargs)

    if name.startswith("pyrogram"):
        return native_import("hikkapyro" + name[8:], *args, **kwargs)

    return native_import(name, *args, **kwargs)


builtins.__import__ = patched_import


def apply_compat(client: CustomTelegramClient):
    client.dragon_compat = DragonCompat(client)
