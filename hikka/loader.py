"""Registers modules"""

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
import functools
import importlib
import importlib.util
import inspect
import logging
import re
import os
import sys
from importlib.abc import SourceLoader
from importlib.machinery import ModuleSpec
from types import FunctionType
from typing import Any, Optional, Union, List
from telethon.tl.types import Message

from . import security, utils, validators  # noqa: F401
from ._types import (  # noqa: F401
    ConfigValue,
    LoadError,
    Module,
    ModuleConfig,
    SelfUnload,
    StopLoop,
    InlineMessage,
)
from .fast_uploader import download_file, upload_file
from .inline.core import InlineManager
from .translations import Strings

logger = logging.getLogger(__name__)

owner = security.owner
sudo = security.sudo
support = security.support
group_owner = security.group_owner
group_admin_add_admins = security.group_admin_add_admins
group_admin_change_info = security.group_admin_change_info
group_admin_ban_users = security.group_admin_ban_users
group_admin_delete_messages = security.group_admin_delete_messages
group_admin_pin_messages = security.group_admin_pin_messages
group_admin_invite_users = security.group_admin_invite_users
group_admin = security.group_admin
group_member = security.group_member
pm = security.pm
unrestricted = security.unrestricted
inline_everyone = security.inline_everyone


class StringLoader(SourceLoader):
    """Load a python module/file from a string"""

    def __init__(self, data: str, origin: str):
        self.data = data.encode("utf-8") if isinstance(data, str) else data
        self.origin = origin

    def get_code(self, fullname: str) -> str:
        return (
            compile(source, self.origin, "exec", dont_inherit=True)
            if (source := self.get_source(fullname))
            else None
        )

    def get_filename(self, *args, **kwargs) -> str:
        return self.origin

    def get_data(self, *args, **kwargs) -> bytes:
        return self.data


async def stop_placeholder() -> bool:
    return True


class InfiniteLoop:
    _task = None
    status = False
    module_instance = None  # Will be passed later

    def __init__(
        self,
        func: FunctionType,
        interval: int,
        autostart: bool,
        wait_before: bool,
        stop_clause: Union[str, None],
    ):
        logger.debug(f"Inited new loop {func=}, {interval=}")
        self.func = func
        self.interval = interval
        self._wait_before = wait_before
        self._stop_clause = stop_clause
        self.autostart = autostart

    def _stop(self, *args, **kwargs):
        self._wait_for_stop.set()

    def stop(self, *args, **kwargs):
        if self._task:
            logger.debug(f"Stopped loop for {self.func}")
            self._wait_for_stop = asyncio.Event()
            self.status = False
            self._task.add_done_callback(self._stop)
            self._task.cancel()
            return asyncio.ensure_future(self._wait_for_stop.wait())

        logger.debug("Loop is not running")
        return asyncio.ensure_future(stop_placeholder())

    def start(self, *args, **kwargs):
        if not self._task:
            logger.debug(f"Started loop for {self.func}")
            self._task = asyncio.ensure_future(self.actual_loop(*args, **kwargs))
        else:
            logger.debug("Attempted to start already running loop")

    async def actual_loop(self, *args, **kwargs):
        # Wait for loader to set attribute
        while not self.module_instance:
            await asyncio.sleep(0.01)

        if isinstance(self._stop_clause, str) and self._stop_clause:
            self.module_instance.set(self._stop_clause, True)

        self.status = True

        while self.status:
            if self._wait_before:
                await asyncio.sleep(self.interval)

            if (
                isinstance(self._stop_clause, str)
                and self._stop_clause
                and not self.module_instance.get(self._stop_clause, False)
            ):
                break

            try:
                await self.func(self.module_instance, *args, **kwargs)
            except StopLoop:
                break
            except Exception:
                logger.exception("Error running loop!")

            if not self._wait_before:
                await asyncio.sleep(self.interval)

        self._wait_for_stop.set()

        self.status = False

    def __del__(self):
        self.stop()


def loop(
    interval: int = 5,
    autostart: Optional[bool] = False,
    wait_before: Optional[bool] = False,
    stop_clause: Optional[str] = None,
) -> FunctionType:
    """
    Create new infinite loop from class method
    :param interval: Loop iterations delay
    :param autostart: Start loop once module is loaded
    :param wait_before: Insert delay before actual iteration, rather than after
    :param stop_clause: Database key, based on which the loop will run.
                       This key will be set to `True` once loop is started,
                       and will stop after key resets to `False`
    :attr status: Boolean, describing whether the loop is running
    """

    def wrapped(func):
        return InfiniteLoop(func, interval, autostart, wait_before, stop_clause)

    return wrapped


MODULES_NAME = "modules"
ru_keys = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'
en_keys = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"

BASE_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if "OKTETO" not in os.environ and "DOCKER" not in os.environ
    else "/data"
)

LOADED_MODULES_DIR = os.path.join(BASE_DIR, "loaded_modules")

if not os.path.isdir(LOADED_MODULES_DIR):
    os.mkdir(LOADED_MODULES_DIR, mode=0o755)


def translatable_docstring(cls):
    """Decorator that makes triple-quote docstrings translatable"""

    @functools.wraps(cls.config_complete)
    def config_complete(self, *args, **kwargs):
        for command_, func_ in get_commands(cls).items():
            try:
                func_.__doc__ = self.strings[f"_cmd_doc_{command_}"]
            except AttributeError:
                func_.__func__.__doc__ = self.strings[f"_cmd_doc_{command_}"]

        for inline_handler_, func_ in get_inline_handlers(cls).items():
            try:
                func_.__doc__ = self.strings[f"_ihandle_doc_{inline_handler_}"]
            except AttributeError:
                func_.__func__.__doc__ = self.strings[f"_ihandle_doc_{inline_handler_}"]

        self.__doc__ = self.strings["_cls_doc"]
        return self.config_complete._old_(self, *args, **kwargs)

    config_complete._old_ = cls.config_complete
    cls.config_complete = config_complete

    for command, func in get_commands(cls).items():
        cls.strings[f"_cmd_doc_{command}"] = inspect.getdoc(func)

    for inline_handler, func in get_inline_handlers(cls).items():
        cls.strings[f"_ihandle_doc_{inline_handler}"] = inspect.getdoc(func)

    cls.strings["_cls_doc"] = inspect.getdoc(cls)

    return cls


tds = translatable_docstring  # Shorter name for modules to use


def ratelimit(func):
    """Decorator that causes ratelimiting for this command to be enforced more strictly"""
    func.ratelimit = True
    return func


def get_commands(mod):
    """Introspect the module to get its commands"""
    return {
        method_name.rsplit("cmd", maxsplit=1)[0]: getattr(mod, method_name)
        for method_name in dir(mod)
        if callable(getattr(mod, method_name)) and method_name.endswith("cmd")
    }


def get_inline_handlers(mod):
    """Introspect the module to get its inline handlers"""
    return {
        method_name.rsplit("_inline_handler", maxsplit=1)[0]: getattr(mod, method_name)
        for method_name in dir(mod)
        if callable(getattr(mod, method_name))
        and method_name.endswith("_inline_handler")
    }


def get_callback_handlers(mod):
    """Introspect the module to get its callback handlers"""
    return {
        method_name.rsplit("_callback_handler", maxsplit=1)[0]: getattr(
            mod,
            method_name,
        )
        for method_name in dir(mod)
        if callable(getattr(mod, method_name))
        and method_name.endswith("_callback_handler")
    }


class Modules:
    """Stores all registered modules"""

    client = None
    added_modules = None
    _initial_registration = True

    def __init__(self):
        self.commands = {}
        self.inline_handlers = {}
        self.callback_handlers = {}
        self.aliases = {}
        self.modules = []  # skipcq: PTC-W0052
        self.watchers = []
        self._log_handlers = []
        self._core_commands = []

    def register_all(self, client, db, mods=None):
        """Load all modules in the module directory"""
        self._db = db

        external_mods = []

        if not mods:
            mods = [
                os.path.join(utils.get_base_dir(), MODULES_NAME, mod)
                for mod in filter(
                    lambda x: (
                        x.endswith(".py")
                        and not x.startswith("_")
                        and (
                            not db.get("hikka", "disable_quickstart", False)
                            or x != "quickstart.py"
                        )
                        and (
                            db.get("hikka.main", "use_dl_btn", True)
                            or x != "hikka_dl.py"
                        )
                    ),
                    os.listdir(os.path.join(utils.get_base_dir(), MODULES_NAME)),
                )
            ]

            external_mods = [
                os.path.join(LOADED_MODULES_DIR, mod)
                for mod in filter(
                    lambda x: (
                        x.endswith(f"{client._tg_id}.py") and not x.startswith("_")
                    ),
                    os.listdir(LOADED_MODULES_DIR),
                )
            ]

            for mod in os.listdir(LOADED_MODULES_DIR):
                if not re.match(
                    r"[a-zA-Zа-яА-Я0-9_]+_[0-9]+\.py", mod
                ) and mod.endswith(".py"):
                    new_name = mod.rsplit(".py")[0] + f"_{client._tg_id}.py"
                    os.rename(
                        os.path.join(LOADED_MODULES_DIR, mod),
                        os.path.join(LOADED_MODULES_DIR, new_name),
                    )
                    external_mods += [new_name]
                    logger.debug(f"Made legacy migration from {mod=} to {new_name=}")

        self._register_modules(mods)
        self._register_modules(external_mods, "<file>")

    def _register_modules(self, modules: list, origin: str = "<core>"):
        for mod in modules:
            try:
                module_name = (
                    f"{__package__}."
                    f"{MODULES_NAME}."
                    f"{os.path.basename(mod).rsplit('.py', maxsplit=1)[0].rsplit('_', maxsplit=1)[0]}"
                )

                logger.debug(f"Loading {module_name} from filesystem")

                with open(mod, "r") as file:
                    spec = ModuleSpec(
                        module_name,
                        StringLoader(file.read(), origin),
                        origin=origin,
                    )

                self.register_module(spec, module_name, origin)
            except BaseException as e:
                logger.exception(f"Failed to load module {mod} due to {e}:")

    def register_module(
        self,
        spec: ModuleSpec,
        module_name: str,
        origin: str = "<core>",
        save_fs: bool = False,
    ) -> Module:
        """Register single module from importlib spec"""
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        ret = None

        ret = next(
            (
                value()
                for value in vars(module).values()
                if inspect.isclass(value) and issubclass(value, Module)
            ),
            None,
        )

        if hasattr(module, "__version__"):
            ret.__version__ = module.__version__

        if ret is None:
            ret = module.register(module_name)
            if not isinstance(ret, Module):
                raise TypeError(f"Instance is not a Module, it is {type(ret)}")

        self.complete_registration(ret)
        ret.__origin__ = origin

        cls_name = ret.__class__.__name__

        if save_fs:
            path = os.path.join(
                LOADED_MODULES_DIR,
                f"{cls_name}_{self.client._tg_id}.py",
            )

            if origin == "<string>":
                with open(path, "w") as f:
                    f.write(spec.loader.data.decode("utf-8"))

                logger.debug(f"Saved {cls_name=} to {path=}")

        return ret

    def add_aliases(self, aliases: dict):
        """Saves aliases and applies them to <core>/<file> modules"""
        self.aliases.update(aliases)
        for alias, cmd in aliases.items():
            self.add_alias(alias, cmd)

    def register_commands(self, instance: Module):
        """Register commands from instance"""
        if getattr(instance, "__origin__", "") == "<core>":
            self._core_commands += list(map(lambda x: x.lower(), instance.commands))

        for command in instance.commands.copy():
            # Restrict overwriting core modules' commands
            if (
                command.lower() in self._core_commands
                and getattr(instance, "__origin__", "") != "<core>"
            ):
                try:
                    self.modules.remove(instance)
                except Exception:
                    pass
                raise RuntimeError(f"Command {command} is core and will not be overwritten by {instance}")  # fmt: skip

            # Verify that command does not already exist, or,
            # if it does, the command must be from the same class name
            if command.lower() in self.commands:
                if (
                    hasattr(instance.commands[command], "__self__")
                    and hasattr(self.commands[command], "__self__")
                    and instance.commands[command].__self__.__class__.__name__
                    != self.commands[command].__self__.__class__.__name__
                ):
                    logger.debug(f"Duplicate command {command}")
                logger.debug(f"Replacing command for {self.commands[command]}")  # fmt: skip

            if not instance.commands[command].__doc__:
                logger.debug(f"Missing docs for {command}")

            self.commands.update({command.lower(): instance.commands[command]})

        for alias, cmd in self.aliases.items():
            if cmd in instance.commands:
                self.add_alias(alias, cmd)

        for handler in instance.inline_handlers.copy():
            if handler.lower() in self.inline_handlers:
                if (
                    hasattr(instance.inline_handlers[handler], "__self__")
                    and hasattr(self.inline_handlers[handler], "__self__")
                    and instance.inline_handlers[handler].__self__.__class__.__name__
                    != self.inline_handlers[handler].__self__.__class__.__name__
                ):
                    logger.debug(f"Duplicate inline_handler {handler}")
                logger.debug(f"Replacing inline_handler for {self.inline_handlers[handler]}")  # fmt: skip

            if not instance.inline_handlers[handler].__doc__:
                logger.debug(f"Missing docs for {handler}")

            self.inline_handlers.update(
                {handler.lower(): instance.inline_handlers[handler]}
            )

        for handler in instance.callback_handlers.copy():
            if handler.lower() in self.callback_handlers and (
                hasattr(instance.callback_handlers[handler], "__self__")
                and hasattr(self.callback_handlers[handler], "__self__")
                and instance.callback_handlers[handler].__self__.__class__.__name__
                != self.callback_handlers[handler].__self__.__class__.__name__
            ):
                logger.debug(f"Duplicate callback_handler {handler}")
            self.callback_handlers.update({handler.lower(): instance.callback_handlers[handler]})  # fmt: skip

    def register_watcher(self, instance: Module):
        """Register watcher from instance"""
        try:
            if instance.watcher:
                for watcher in self.watchers:
                    if (
                        hasattr(watcher, "__self__")
                        and watcher.__self__.__class__.__name__
                        == instance.watcher.__self__.__class__.__name__
                    ):
                        logger.debug(f"Removing watcher for update {watcher}")
                        self.watchers.remove(watcher)

                self.watchers += [instance.watcher]
        except AttributeError:
            pass

    def _lookup(self, modname: str):
        return next(
            (mod for mod in self.modules if mod.name.lower() == modname.lower()),
            False,
        )

    def complete_registration(self, instance: Module):
        """Complete registration of instance"""
        instance.allmodules = self
        instance.hikka = True
        instance.get = functools.partial(
            self._mod_get,
            mod=instance.strings["name"],
        )
        instance.set = functools.partial(
            self._mod_set,
            mod=instance.strings["name"],
        )

        instance.get_prefix = lambda: (
            self._db.get("hikka.main", "command_prefix", False) or "."
        )

        instance.lookup = self._lookup

        for module in self.modules:
            if module.__class__.__name__ == instance.__class__.__name__:
                if getattr(module, "__origin__", "") == "<core>":
                    raise RuntimeError(f"Attempted to overwrite core module {module}")

                logger.debug(f"Removing module for update {module}")
                asyncio.ensure_future(module.on_unload())

                self.modules.remove(module)
                for method in dir(module):
                    if isinstance(getattr(module, method), InfiniteLoop):
                        getattr(module, method).stop()
                        logger.debug(f"Stopped loop in {module=}, {method=}")

        self.modules += [instance]

    def _mod_get(self, *args, mod: str = None) -> Any:
        return self._db.get(mod, *args)

    def _mod_set(self, *args, mod: str = None) -> bool:
        return self._db.set(mod, *args)

    def dispatch(self, command: str) -> tuple:
        """Dispatch command to appropriate module"""
        change = str.maketrans(ru_keys + en_keys, en_keys + ru_keys)
        try:
            return command, self.commands[command.lower()]
        except KeyError:
            try:
                cmd = self.aliases[command.lower()]
                return cmd, self.commands[cmd.lower()]
            except KeyError:
                try:
                    cmd = self.aliases[str.translate(command, change).lower()]
                    return cmd, self.commands[cmd.lower()]
                except KeyError:
                    try:
                        cmd = str.translate(command, change).lower()
                        return cmd, self.commands[cmd.lower()]
                    except KeyError:
                        return command, None

    def send_config(self, db, translator, skip_hook: bool = False):
        """Configure modules"""
        for mod in self.modules:
            self.send_config_one(mod, db, translator, skip_hook)

    @staticmethod
    def send_config_one(
        mod: "Module",
        db: "Database",  # noqa: F821
        translator: "Translator" = None,  # noqa: F821
        skip_hook: bool = False,
    ):
        """Send config to single instance"""
        if hasattr(mod, "config"):
            modcfg = db.get(
                mod.__class__.__name__,
                "__config__",
                {},
            )
            try:
                for conf in mod.config.keys():
                    try:
                        mod.config.set_no_raise(
                            conf,
                            (
                                modcfg[conf]
                                if conf in modcfg.keys()
                                else os.environ.get(f"{mod.__class__.__name__}.{conf}")
                                or mod.config.getdef(conf)
                            ),
                        )
                    except validators.ValidationError:
                        pass
            except AttributeError:
                logger.warning(
                    f"Got invalid config instance. Expected `ModuleConfig`, got {type(mod.config)=}, {mod.config=}"
                )

        if skip_hook:
            return

        if not hasattr(mod, "name"):
            mod.name = mod.strings["name"]

        if hasattr(mod, "strings"):
            mod.strings = Strings(mod, translator)

        mod.translator = translator

        try:
            mod.config_complete()
        except Exception as e:
            logger.exception(f"Failed to send mod config complete signal due to {e}")
            raise

    async def send_ready(self, client, db, allclients):
        """Send all data to all modules"""
        self.client = client

        # Init inline manager anyway, so the modules
        # can access its `init_complete`
        inline_manager = InlineManager(client, db, self)

        await inline_manager._register_manager()

        # We save it to `Modules` attribute, so not to re-init
        # it everytime module is loaded. Then we can just
        # re-assign it to all modules
        self.inline = inline_manager

        try:
            await asyncio.gather(
                *[
                    self.send_ready_one(mod, client, db, allclients)
                    for mod in self.modules
                ]
            )
        except Exception as e:
            logger.exception(f"Failed to send mod init complete signal due to {e}")

        if self.added_modules:
            await self.added_modules(self)

    async def _animate(
        self,
        message: Union[Message, InlineMessage],
        frames: List[str],
        interval: Union[float, int],
        *,
        inline: bool = False,
    ) -> None:
        """
        Animate message
        :param message: Message to animate
        :param frames: A List of strings which are the frames of animation
        :param interval: Animation delay
        :param inline: Whether to use inline bot for animation
        :returns message:

        Please, note that if you set `inline=True`, first frame will be shown with an empty
        button due to the limitations of Telegram API
        """

        if interval < 0.1:
            logger.warning("Resetting animation interval to 0.1s, because it may get you in floodwaits bro")  # fmt: skip
            interval = 0.1

        for frame in frames:
            if isinstance(message, Message):
                if inline:
                    message = await self.inline.form(
                        message=message,
                        text=frame,
                        reply_markup={"text": "\u0020\u2800", "data": "empty"},
                    )
                else:
                    message = await utils.answer(message, frame)
            elif isinstance(message, InlineMessage) and inline:
                await message.edit(frame)

            await asyncio.sleep(interval)

        return message

    async def send_ready_one(
        self,
        mod: Module,
        client: "TelegramClient",  # noqa: F821
        db: "Database",  # noqa: F821
        allclients: list,
        no_self_unload: bool = False,
        from_dlmod: bool = False,
    ):
        mod.allclients = allclients
        mod._client = client
        mod._tg_id = client._tg_id

        mod.inline = self.inline
        mod.animate = self._animate

        mod.fast_upload = functools.partial(upload_file, _client=client)
        mod.fast_download = functools.partial(download_file, _client=client)

        for method in dir(mod):
            if isinstance(getattr(mod, method), InfiniteLoop):
                setattr(getattr(mod, method), "module_instance", mod)

                if getattr(mod, method).autostart:
                    getattr(mod, method).start()

                logger.debug(f"Added {mod=} to {method=}")

        if from_dlmod:
            try:
                await mod.on_dlmod(client, db)
            except Exception:
                logger.info("Can't process `on_dlmod` hook", exc_info=True)

        try:
            await mod.client_ready(client, db)
        except SelfUnload as e:
            if no_self_unload:
                raise e

            logger.debug(f"Unloading {mod}, because it raised SelfUnload")
            self.modules.remove(mod)
        except Exception as e:
            logger.exception(f"Failed to send mod init complete signal for {mod} due to {e}, attempting unload")  # fmt: skip
            self.modules.remove(mod)
            raise

        if not hasattr(mod, "commands"):
            mod.commands = get_commands(mod)

        if not hasattr(mod, "inline_handlers"):
            mod.inline_handlers = get_inline_handlers(mod)

        if not hasattr(mod, "callback_handlers"):
            mod.callback_handlers = get_callback_handlers(mod)

        self.register_commands(mod)
        self.register_watcher(mod)
        if not self._initial_registration and self.added_modules:
            await self.added_modules(self)

    def get_classname(self, name: str) -> str:
        return next(
            (
                module.__class__.__module__
                for module in reversed(self.modules)
                if name in (module.name, module.__class__.__module__)
            ),
            name,
        )

    def unload_module(self, classname: str) -> bool:
        """Remove module and all stuff from it"""
        worked = []
        to_remove = []

        for module in self.modules:
            if classname.lower() in (
                module.name.lower(),
                module.__class__.__name__.lower(),
            ):
                if getattr(module, "__origin__", "") == "<core>":
                    raise RuntimeError("You can't unload core module")

                worked += [module.__class__.__name__]

                name = module.__class__.__name__
                path = os.path.join(
                    LOADED_MODULES_DIR,
                    f"{name}_{self.client._tg_id}.py",
                )

                if os.path.isfile(path):
                    os.remove(path)
                    logger.debug(f"Removed {name} file at {path=}")

                logger.debug(f"Removing module for unload {module}")
                self.modules.remove(module)

                asyncio.ensure_future(module.on_unload())

                for method in dir(module):
                    if isinstance(getattr(module, method), InfiniteLoop):
                        getattr(module, method).stop()
                        logger.debug(f"Stopped loop in {module=}, {method=}")

                to_remove += module.commands.values()
                if hasattr(module, "watcher"):
                    to_remove += [module.watcher]

        logger.debug(f"{to_remove=}, {worked=}")
        for watcher in self.watchers.copy():
            if watcher in to_remove:
                logger.debug(f"Removing {watcher=} for unload")
                self.watchers.remove(watcher)

        aliases_to_remove = []

        for name, command in self.commands.copy().items():
            if command in to_remove:
                logger.debug(f"Removing {command=} for unload")
                del self.commands[name]
                aliases_to_remove.append(name)

        for alias, command in self.aliases.copy().items():
            if command in aliases_to_remove:
                del self.aliases[alias]

        return worked

    def add_alias(self, alias, cmd):
        """Make an alias"""
        if cmd not in self.commands:
            return False

        self.aliases[alias.lower().strip()] = cmd
        return True

    def remove_alias(self, alias):
        """Remove an alias"""
        try:
            del self.aliases[alias.lower().strip()]
        except KeyError:
            return False

        return True

    async def log(
        self,
        type_,
        *,
        group=None,
        affected_uids=None,
        data=None,
    ):
        return await asyncio.gather(*[fun(type_, group, affected_uids, data) for fun in self._log_handlers])  # fmt: skip

    def register_logger(self, _logger):
        self._log_handlers += [_logger]
