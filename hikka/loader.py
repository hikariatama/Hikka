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

"""Loads modules from disk and dispatches stuff, and stores state"""

import asyncio
import functools
import importlib
import importlib.util
import inspect
import logging
import os
import sys
import json

from . import utils, security, inline
from .translations.dynamic import Strings


class LoadError(Exception):
    def __init__(self, error_message):  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


def use_fs_for_modules():
    try:
        with open("config.json", "r") as f:
            config = json.loads(f.read())
    except Exception:
        return False

    return config.get("use_fs_for_modules", False)


def test(*args, **kwargs):
    return lambda func: func


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

MODULES_NAME = "modules"
ru_keys = """ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГ
        ШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ, """
en_keys = """`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{
        }ASDFGHJKL:"|ZXCVBNM<>? """


LOADED_MODULES_DIR = os.path.join(utils.get_base_dir(), "loaded_modules")

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


class ModuleConfig(dict):
    """Like a dict but contains doc for each key"""

    def __init__(self, *entries):
        keys = []
        values = []
        defaults = []
        docstrings = []
        for i, entry in enumerate(entries):
            if i % 3 == 0:
                keys.append(entry)
            elif i % 3 == 1:
                values.append(entry)
                defaults.append(entry)
            else:
                docstrings.append(entry)

        super().__init__(zip(keys, values))
        self._docstrings = dict(zip(keys, docstrings))
        self._defaults = dict(zip(keys, defaults))

    def getdoc(self, key, message=None):
        """Get the documentation by key"""
        ret = self._docstrings[key]
        if callable(ret):
            try:
                ret = ret(message)
            except TypeError:  # Invalid number of params
                logging.debug("%s using legacy doc trnsl", key)
                ret = ret()

        return ret

    def getdef(self, key):
        """Get the default value by key"""
        return self._defaults[key]


class Module:
    strings = {"name": "Unknown"}

    """There is no help for this module"""

    def config_complete(self):
        """Will be called when module.config is populated"""

    async def client_ready(self, client, db):
        """Will be called after client is ready (after config_loaded)"""

    async def on_unload(self):
        """Will be called after unloading / reloading module"""

    # Called after client_ready, for internal use only. Must not be used by non-core modules
    async def _client_ready2(self, client, db):
        pass


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

    def __init__(self, use_inline=True):
        self.commands = {}
        self.aliases = {}
        self.modules = []  # skipcq: PTC-W0052
        self.watchers = []
        self._compat_layer = None
        self._log_handlers = []
        self.client = None
        self._initial_registration = True
        self.added_modules = None
        self.use_inline = use_inline
        self._fs = "DYNO" not in os.environ

    def register_all(self, babelfish, mods=None):  # skipcq: PYL-W0613
        # TODO: remove babelfish
        """Load all modules in the module directory"""
        if self._compat_layer is None:
            from . import compat  # Avoid circular import

            self._compat_layer = compat.activate([])

        if not mods:
            mods = [
                os.path.join(utils.get_base_dir(), MODULES_NAME, mod)
                for mod in filter(
                    lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
                    os.listdir(os.path.join(utils.get_base_dir(), MODULES_NAME)),
                )
            ]

            if self._fs and use_fs_for_modules():
                mods += [
                    os.path.join(LOADED_MODULES_DIR, mod)
                    for mod in filter(
                        lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
                        os.listdir(LOADED_MODULES_DIR),
                    )
                ]

        logging.debug(mods)

        for mod in mods:
            try:
                module_name = (
                    f"{__package__}.{MODULES_NAME}.{os.path.basename(mod)[:-3]}"
                )
                logging.debug(module_name)
                spec = importlib.util.spec_from_file_location(module_name, mod)
                self.register_module(spec, module_name)
            except BaseException as e:
                logging.exception(f"Failed to load module %s due to {e}:", mod)

    def register_module(self, spec, module_name, origin="<file>"):
        """Register single module from importlib spec"""
        from .compat import uniborg

        module = importlib.util.module_from_spec(spec)
        sys.modules[
            module_name
        ] = module  # Do this early for the benefit of RaphielGang compat layer
        module.borg = uniborg.UniborgClient(module_name)
        spec.loader.exec_module(module)
        ret = None

        for key, value in vars(module).items():
            if key.endswith("Mod") and issubclass(value, Module):
                ret = value()

        if hasattr(module, '__version__'):
            ret.__version__ = module.__version__

        if ret is None:
            ret = module.register(module_name)
            if not isinstance(ret, Module):
                raise TypeError(f"Instance is not a Module, it is {type(ret)}")

        self.complete_registration(ret)
        ret.__origin__ = origin

        cls_name = ret.__class__.__name__

        if self._fs and use_fs_for_modules():
            path = os.path.join(LOADED_MODULES_DIR, f"{cls_name}.py")

            if not os.path.isfile(path) and origin == "<string>":
                with open(path, "w") as f:
                    f.write(spec.loader.data.decode("utf-8"))

                logging.debug(f"Saved {cls_name} to file")

        return ret

    def register_commands(self, instance):
        """Register commands from instance"""
        for command in instance.commands.copy():
            # Verify that command does not already exist, or,
            # if it does, the command must be from the same class name
            if command.lower() in self.commands:
                if (
                    hasattr(instance.commands[command], "__self__")
                    and hasattr(self.commands[command], "__self__")
                    and instance.commands[command].__self__.__class__.__name__
                    != self.commands[command].__self__.__class__.__name__
                ):
                    logging.debug("Duplicate command %s", command)

                logging.debug("Replacing command for %r", self.commands[command])

            if not instance.commands[command].__doc__:
                logging.debug("Missing docs for %s", command)

            self.commands.update({command.lower(): instance.commands[command]})

    def register_watcher(self, instance):
        """Register watcher from instance"""
        try:
            if instance.watcher:
                for watcher in self.watchers:
                    if (
                        hasattr(watcher, "__self__")
                        and watcher.__self__.__class__.__name__
                        == instance.watcher.__self__.__class__.__name__
                    ):
                        logging.debug("Removing watcher for update %r", watcher)
                        self.watchers.remove(watcher)
                self.watchers += [instance.watcher]
        except AttributeError:
            pass

    def complete_registration(self, instance):
        """Complete registration of instance"""
        instance.allmodules = self
        instance.geektg = True
        instance.log = self.log  # Like botlog from PP
        for module in self.modules:
            if module.__class__.__name__ == instance.__class__.__name__:
                logging.debug("Removing module for update %r", module)
                self.modules.remove(module)
                asyncio.ensure_future(
                    asyncio.wait_for(asyncio.gather(module.on_unload()), timeout=5)
                )

        self.modules += [instance]

    def dispatch(self, command):
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

    def send_config(self, db, babel, skip_hook=False):
        """Configure modules"""
        for mod in self.modules:
            self.send_config_one(mod, db, babel, skip_hook)

    @staticmethod
    def send_config_one(mod, db, babel=None, skip_hook=False):
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

        # Register inline manager anyway, so the modules
        # can access its `init_complete`
        inline_manager = inline.InlineManager(client, db, self)

        # Register only if it is not disabled
        if self.use_inline:
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
            )  # pylint: disable=W0212
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
            logging.exception(
                f"Failed to send mod init complete signal for %r due to {e}, attempting unload",
                mod,
            )
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

    def get_classname(self, name):
        return next(
            (
                module.__class__.__module__
                for module in reversed(self.modules)
                if name in (module.name, module.__class__.__module__)
            ),
            name,
        )

    def unload_module(self, classname):
        """Remove module and all stuff from it"""
        worked = []
        to_remove = []

        for module in self.modules:
            if classname in (module.name, module.__class__.__name__):
                worked += [module.__module__]

                name = module.__class__.__name__
                if self._fs and use_fs_for_modules():
                    path = os.path.join(LOADED_MODULES_DIR, f"{name}.py")

                    if os.path.isfile(path):
                        os.remove(path)
                        logging.debug(f"Removed {name} file")

                logging.debug("Removing module for unload %r", module)
                self.modules.remove(module)

                asyncio.ensure_future(
                    asyncio.wait_for(asyncio.gather(module.on_unload()), timeout=5)
                )

                to_remove += module.commands.values()
                if hasattr(module, "watcher"):
                    to_remove += [module.watcher]

        logging.debug("to_remove: %r", to_remove)
        for watcher in self.watchers.copy():
            if watcher in to_remove:
                logging.debug("Removing watcher for unload %r", watcher)
                self.watchers.remove(watcher)

        aliases_to_remove = []

        for name, command in self.commands.copy().items():
            if command in to_remove:
                logging.debug("Removing command for unload %r", command)
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
