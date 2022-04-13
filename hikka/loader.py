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
import os
import sys

from . import utils, security
from .translations.dynamic import Strings
from .inline.core import InlineManager
from ._types import Module, LoadError, ModuleConfig  # noqa: F401
from importlib.machinery import ModuleSpec

from typing import Any

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

MODULES_NAME = "modules"
ru_keys = 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'
en_keys = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"

DATA_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if "OKTETO" not in os.environ
    else "/data"
)

LOADED_MODULES_DIR = os.path.join(DATA_DIR, "loaded_modules")

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
        self.__doc__ = self.strings["_cls_doc"]
        return self.config_complete._old_(self, *args, **kwargs)

    config_complete._old_ = cls.config_complete
    cls.config_complete = config_complete

    for command, func in get_commands(cls).items():
        cls.strings["_cmd_doc_" + command] = inspect.getdoc(func)

    cls.strings["_cls_doc"] = inspect.getdoc(cls)

    return cls


tds = translatable_docstring  # Shorter name for modules to use


def ratelimit(func):
    """Decorator that causes ratelimiting for this command to be enforced more strictly"""
    func.ratelimit = True
    return func


def get_commands(mod):
    """Introspect the module to get its commands"""
    # https://stackoverflow.com/a/34452/5509575
    return {
        method_name[:-3]: getattr(mod, method_name)
        for method_name in dir(mod)
        if callable(getattr(mod, method_name))
        and len(method_name) > 3
        and method_name[-3:] == "cmd"
    }


def get_inline_handlers(mod):
    """Introspect the module to get its inline handlers"""
    return {
        method_name[:-15]: getattr(mod, method_name)
        for method_name in dir(mod)
        if callable(getattr(mod, method_name))
        and len(method_name) > 15
        and method_name[-15:] == "_inline_handler"
    }


def get_callback_handlers(mod):
    """Introspect the module to get its callback handlers"""
    return {
        method_name[:-17]: getattr(mod, method_name)
        for method_name in dir(mod)
        if callable(getattr(mod, method_name))
        and len(method_name) > 17
        and method_name[-17:] == "_callback_handler"
    }


class Modules:
    """Stores all registered modules"""

    def __init__(self):
        self.commands = {}
        self.inline_handlers = {}
        self.callback_handlers = {}
        self.aliases = {}
        self.modules = []  # skipcq: PTC-W0052
        self.watchers = []
        self._log_handlers = []
        self._compat_layer = None
        self.client = None
        self._initial_registration = True
        self.added_modules = None

    def register_all(self, db, mods=None):
        """Load all modules in the module directory"""
        self._db = db

        if self._compat_layer is None:
            from . import compat  # noqa

            self._compat_layer = compat.activate([])

        external_mods = []

        if not mods:
            mods = [
                os.path.join(utils.get_base_dir(), MODULES_NAME, mod)
                for mod in filter(
                    lambda x: (
                        len(x) > 3
                        and x[-3:] == ".py"
                        and x[0] != "_"
                        and ("OKTETO" in os.environ or x != "okteto.py")
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
                    lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
                    os.listdir(LOADED_MODULES_DIR),
                )
            ]

        logging.debug(mods)

        for mod in mods:
            try:
                module_name = f"{__package__}.{MODULES_NAME}.{os.path.basename(mod)[:-3]}"
                logging.debug(module_name)
                spec = importlib.util.spec_from_file_location(module_name, mod)
                self.register_module(spec, module_name, "<core>")
            except BaseException as e:
                logging.exception(f"Failed to load core module {mod} due to {e}:")

        for mod in external_mods:
            try:
                module_name = f"{__package__}.{MODULES_NAME}.{os.path.basename(mod)[:-3]}"
                logging.debug(module_name)
                spec = importlib.util.spec_from_file_location(module_name, mod)
                self.register_module(spec, module_name, "<file>")
            except BaseException as e:
                logging.exception(f"Failed to load module {mod} due to {e}:")

    def register_module(
        self,
        spec: ModuleSpec,
        module_name: str,
        origin: str = "<core>",
        save_fs: bool = False,
    ) -> Module:
        """Register single module from importlib spec"""
        from .compat import uniborg

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        module.borg = uniborg.UniborgClient(module_name)
        spec.loader.exec_module(module)
        ret = None

        for key, value in vars(module).items():
            if key.endswith("Mod") and issubclass(value, Module):
                ret = value()

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
            path = os.path.join(LOADED_MODULES_DIR, f"{cls_name}.py")

            if not os.path.isfile(path) and origin == "<string>":
                with open(path, "w") as f:
                    f.write(spec.loader.data.decode("utf-8"))

                logging.debug(f"Saved {cls_name} to file")

        return ret

    def register_commands(self, instance: Module) -> None:
        """Register commands from instance"""
        for command in instance.commands.copy():
            # Restrict overwriting core modules' commands
            if (
                command.lower()
                in {
                    "help",
                    "dlmod",
                    "loadmod",
                    "unloadmod",
                    "logs",
                    "ping",
                    "hikka",
                    "e",
                    "eval",
                    "settings",
                    "restart",
                    "update",
                    "ch_hikka_bot",
                    "security",
                    "inlinesec",
                    "info",
                }
                and command.lower() in self.commands
            ):
                logging.warning(
                    f"Command {command} is core and will not be overwritten by {instance}"
                )
                del instance.commands[command]
                continue

            # Verify that command does not already exist, or,
            # if it does, the command must be from the same class name
            if command.lower() in self.commands:
                if (
                    hasattr(instance.commands[command], "__self__")
                    and hasattr(self.commands[command], "__self__")
                    and instance.commands[command].__self__.__class__.__name__
                    != self.commands[command].__self__.__class__.__name__
                ):
                    logging.debug(f"Duplicate command {command}")
                logging.debug(f"Replacing command for {self.commands[command]}")  # fmt: skip

            if not instance.commands[command].__doc__:
                logging.debug(f"Missing docs for {command}")

            self.commands.update({command.lower(): instance.commands[command]})

        for handler in instance.inline_handlers.copy():
            if handler.lower() in self.inline_handlers:
                if (
                    hasattr(instance.inline_handlers[handler], "__self__")
                    and hasattr(self.inline_handlers[handler], "__self__")
                    and instance.inline_handlers[handler].__self__.__class__.__name__
                    != self.inline_handlers[handler].__self__.__class__.__name__
                ):
                    logging.debug(f"Duplicate inline_handler {handler}")
                logging.debug(f"Replacing inline_handler for {self.inline_handlers[handler]}")  # fmt: skip

            if not instance.inline_handlers[handler].__doc__:
                logging.debug(f"Missing docs for {handler}")

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
                logging.debug(f"Duplicate callback_handler {handler}")

            self.callback_handlers.update(
                {handler.lower(): instance.callback_handlers[handler]}
            )

    def register_watcher(self, instance: Module) -> None:
        """Register watcher from instance"""
        try:
            if instance.watcher:
                for watcher in self.watchers:
                    if (
                        hasattr(watcher, "__self__")
                        and watcher.__self__.__class__.__name__
                        == instance.watcher.__self__.__class__.__name__
                    ):
                        logging.debug(f"Removing watcher for update {watcher}")
                        self.watchers.remove(watcher)
                self.watchers += [instance.watcher]
        except AttributeError:
            pass

    def complete_registration(self, instance: Module) -> None:
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

        for module in self.modules:
            if module.__class__.__name__ == instance.__class__.__name__:
                if getattr(module, "__origin__", "") == "<core>":
                    raise RuntimeError(f"Attempted to overwrite core module {module}")

                logging.debug(f"Removing module for update {module}")
                self.modules.remove(module)
                asyncio.ensure_future(
                    asyncio.wait_for(
                        asyncio.gather(
                            module.on_unload(),
                        ),
                        timeout=5,
                    )
                )

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

    def send_config(self, db, babel, skip_hook: bool = False) -> None:
        """Configure modules"""
        for mod in self.modules:
            self.send_config_one(mod, db, babel, skip_hook)

    @staticmethod
    def send_config_one(mod, db, babel=None, skip_hook: bool = False) -> None:
        """Send config to single instance"""
        if hasattr(mod, "config"):
            modcfg = db.get(mod.__module__, "__config__", {})
            for conf in mod.config.keys():
                if conf in modcfg.keys():
                    mod.config[conf] = modcfg[conf]
                else:
                    try:
                        mod.config[conf] = os.environ[f"{mod.__module__}.{conf}"]
                    except KeyError:
                        mod.config[conf] = mod.config.getdef(conf)

        if babel is not None and not hasattr(mod, "name"):
            mod.name = mod.strings["name"]

        if hasattr(mod, "strings") and babel is not None:
            mod.strings = Strings(mod.__module__, mod.strings, babel)

        if skip_hook:
            return

        mod.babel = babel

        try:
            mod.config_complete()
        except Exception as e:
            logging.exception(f"Failed to send mod config complete signal due to {e}")
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

        await self._compat_layer.client_ready(client)

        try:
            await asyncio.gather(
                *[
                    self.send_ready_one(mod, client, db, allclients)
                    for mod in self.modules
                ]
            )
            await asyncio.gather(
                *[mod._client_ready2(client, db) for mod in self.modules]
            )
        except Exception as e:
            logging.exception(f"Failed to send mod init complete signal due to {e}")

        if self.added_modules:
            await self.added_modules(self)

    async def send_ready_one(self, mod, client, db, allclients):
        mod.allclients = allclients
        mod.inline = self.inline

        try:
            await mod.client_ready(client, db)
        except Exception as e:
            logging.exception(f"Failed to send mod init complete signal for {mod} due to {e}, attempting unload")  # fmt: skip
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
                worked += [module.__class__.__name__]

                name = module.__class__.__name__
                path = os.path.join(LOADED_MODULES_DIR, f"{name}.py")

                if os.path.isfile(path):
                    os.remove(path)
                    logging.debug(f"Removed {name} file")

                logging.debug(f"Removing module for unload {module}")
                self.modules.remove(module)

                asyncio.ensure_future(
                    asyncio.wait_for(
                        asyncio.gather(
                            module.on_unload(),
                        ),
                        timeout=5,
                    )
                )

                to_remove += module.commands.values()
                if hasattr(module, "watcher"):
                    to_remove += [module.watcher]

        logging.debug(f"{to_remove=}, {worked=}")
        for watcher in self.watchers.copy():
            if watcher in to_remove:
                logging.debug(f"Removing watcher for unload {watcher}")
                self.watchers.remove(watcher)

        aliases_to_remove = []

        for name, command in self.commands.copy().items():
            if command in to_remove:
                logging.debug(f"Removing command for unload {command}")
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

    async def log(self, type_, *, group=None, affected_uids=None, data=None):
        return await asyncio.gather(
            *[fun(type_, group, affected_uids, data) for fun in self._log_handlers]
        )

    def register_logger(self, logger):
        self._log_handlers.append(logger)
