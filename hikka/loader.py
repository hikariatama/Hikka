"""Registers modules"""

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import inspect
import logging
import os
import re
import sys
from uuid import uuid4
import requests
import copy

import importlib
import importlib.util
import importlib.machinery
from functools import partial, wraps

from telethon.utils import is_list_like
from telethon.tl.tlobject import TLObject
from telethon.tl.types import Message, InputPeerNotifySettings, Channel
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.hints import EntityLike

from types import FunctionType
import typing

from . import security, utils, validators, version
from .types import (
    ConfigValue,  # skipcq
    LoadError,
    Module,
    Library,
    ModuleConfig,  # skipcq
    LibraryConfig,
    SelfUnload,
    SelfSuspend,
    StopLoop,
    InlineMessage,
    CoreOverwriteError,
    CoreUnloadError,
    StringLoader,
    get_commands,
    get_inline_handlers,
    JSONSerializable,
)
from .inline.core import InlineManager
from .inline.types import InlineCall
from .translations import Strings, Translator
from .database import Database

import gc as _gc
import types as _types

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


def proxy0(data):
    def proxy1():
        return data

    return proxy1


_CELLTYPE = type(proxy0(None).__closure__[0])


def replace_all_refs(replace_from: typing.Any, replace_to: typing.Any) -> typing.Any:
    """
    :summary: Uses the :mod:`gc` module to replace all references to obj
              :attr:`replace_from` with :attr:`replace_to` (it tries it's best,
              anyway).
    :param replace_from: The obj you want to replace.
    :param replace_to: The new objject you want in place of the old one.
    :returns: The replace_from
    """
    # https://github.com/cart0113/pyjack/blob/dd1f9b70b71f48335d72f53ee0264cf70dbf4e28/pyjack.py

    _gc.collect()

    hit = False
    for referrer in _gc.get_referrers(replace_from):
        # FRAMES -- PASS THEM UP
        if isinstance(referrer, _types.FrameType):
            continue

        # DICTS
        if isinstance(referrer, dict):
            cls = None

            # THIS CODE HERE IS TO DEAL WITH DICTPROXY TYPES
            if "__dict__" in referrer and "__weakref__" in referrer:
                for cls in _gc.get_referrers(referrer):
                    if inspect.isclass(cls) and cls.__dict__ == referrer:
                        break

            for key, value in referrer.items():
                # REMEMBER TO REPLACE VALUES ...
                if value is replace_from:
                    hit = True
                    value = replace_to
                    referrer[key] = value
                    if cls:  # AGAIN, CLEANUP DICTPROXY PROBLEM
                        setattr(cls, key, replace_to)
                # AND KEYS.
                if key is replace_from:
                    hit = True
                    del referrer[key]
                    referrer[replace_to] = value

        elif isinstance(referrer, list):
            for i, value in enumerate(referrer):
                if value is replace_from:
                    hit = True
                    referrer[i] = replace_to

        elif isinstance(referrer, set):
            referrer.remove(replace_from)
            referrer.add(replace_to)
            hit = True

        elif isinstance(
            referrer,
            (
                tuple,
                frozenset,
            ),
        ):
            new_tuple = []
            for obj in referrer:
                if obj is replace_from:
                    new_tuple.append(replace_to)
                else:
                    new_tuple.append(obj)
            replace_all_refs(referrer, type(referrer)(new_tuple))

        elif isinstance(referrer, _CELLTYPE):

            def _proxy0(data):
                def proxy1():
                    return data

                return proxy1

            proxy = _proxy0(replace_to)
            newcell = proxy.__closure__[0]
            replace_all_refs(referrer, newcell)

        elif isinstance(referrer, _types.FunctionType):
            localsmap = {}
            for key in ["code", "globals", "name", "defaults", "closure"]:
                orgattr = getattr(referrer, f"__{key}__")
                localsmap[key] = replace_to if orgattr is replace_from else orgattr
            localsmap["argdefs"] = localsmap["defaults"]
            del localsmap["defaults"]
            newfn = _types.FunctionType(**localsmap)
            replace_all_refs(referrer, newfn)

        else:
            logger.debug("%s is not supported.", referrer)

    if hit is False:
        raise AttributeError(f"Object '{replace_from}' not found")

    return replace_from


async def stop_placeholder() -> bool:
    return True


class Placeholder:
    """Placeholder"""


VALID_PIP_PACKAGES = re.compile(
    r"^\s*# ?requires:(?: ?)((?:{url} )*(?:{url}))\s*$".format(
        url=r"[-[\]_.~:/?#@!$&'()*+,;%<=>a-zA-Z0-9]+"
    ),
    re.MULTILINE,
)

USER_INSTALL = "PIP_TARGET" not in os.environ and "VIRTUAL_ENV" not in os.environ


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
        stop_clause: typing.Union[str, None],
    ):
        self.func = func
        self.interval = interval
        self._wait_before = wait_before
        self._stop_clause = stop_clause
        self.autostart = autostart

    def _stop(self, *args, **kwargs):
        self._wait_for_stop.set()

    def stop(self, *args, **kwargs):
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(
                self.module_instance.allmodules.client.tg_id
            )

        if self._task:
            logger.debug("Stopped loop for method %s", self.func)
            self._wait_for_stop = asyncio.Event()
            self.status = False
            self._task.add_done_callback(self._stop)
            self._task.cancel()
            return asyncio.ensure_future(self._wait_for_stop.wait())

        logger.debug("Loop is not running")
        return asyncio.ensure_future(stop_placeholder())

    def start(self, *args, **kwargs):
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(
                self.module_instance.allmodules.client.tg_id
            )

        if not self._task:
            logger.debug("Started loop for method %s", self.func)
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
    autostart: typing.Optional[bool] = False,
    wait_before: typing.Optional[bool] = False,
    stop_clause: typing.Optional[str] = None,
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

    @wraps(cls.config_complete)
    def config_complete(self, *args, **kwargs):
        def proccess_decorators(mark: str, obj: str):
            nonlocal self
            for attr in dir(func_):
                if (
                    attr.endswith("_doc")
                    and len(attr) == 6
                    and isinstance(getattr(func_, attr), str)
                ):
                    var = f"strings_{attr.split('_')[0]}"
                    if not hasattr(self, var):
                        setattr(self, var, {})

                    getattr(self, var).setdefault(f"{mark}{obj}", getattr(func_, attr))

        for command_, func_ in get_commands(cls).items():
            proccess_decorators("_cmd_doc_", command_)
            try:
                func_.__doc__ = self.strings[f"_cmd_doc_{command_}"]
            except AttributeError:
                func_.__func__.__doc__ = self.strings[f"_cmd_doc_{command_}"]

        for inline_handler_, func_ in get_inline_handlers(cls).items():
            proccess_decorators("_ihandle_doc_", inline_handler_)
            try:
                func_.__doc__ = self.strings[f"_ihandle_doc_{inline_handler_}"]
            except AttributeError:
                func_.__func__.__doc__ = self.strings[f"_ihandle_doc_{inline_handler_}"]

        self.__doc__ = self.strings["_cls_doc"]

        return (
            True
            if kwargs.pop("reload_dynamic_translate", None)
            else self.config_complete._old_(self, *args, **kwargs)
        )


    config_complete._old_ = cls.config_complete
    cls.config_complete = config_complete

    for command_, func in get_commands(cls).items():
        cls.strings[f"_cmd_doc_{command_}"] = inspect.getdoc(func)

    for inline_handler_, func in get_inline_handlers(cls).items():
        cls.strings[f"_ihandle_doc_{inline_handler_}"] = inspect.getdoc(func)

    cls.strings["_cls_doc"] = inspect.getdoc(cls)

    return cls


tds = translatable_docstring  # Shorter name for modules to use


def ratelimit(func: callable):
    """Decorator that causes ratelimiting for this command to be enforced more strictly
    """
    func.ratelimit = True
    return func


def tag(*tags, **kwarg_tags):
    """
    Tag function (esp. watchers) with some tags
    Currently available tags:
        • `no_commands` - Ignore all userbot commands in watcher
        • `only_commands` - Capture only userbot commands in watcher
        • `out` - Capture only outgoing events
        • `in` - Capture only incoming events
        • `only_messages` - Capture only messages (not join events)
        • `editable` - Capture only messages, which can be edited (no forwards etc.)
        • `no_media` - Capture only messages without media and files
        • `only_media` - Capture only messages with media and files
        • `only_photos` - Capture only messages with photos
        • `only_videos` - Capture only messages with videos
        • `only_audios` - Capture only messages with audios
        • `only_docs` - Capture only messages with documents
        • `only_stickers` - Capture only messages with stickers
        • `only_inline` - Capture only messages with inline queries
        • `only_channels` - Capture only messages with channels
        • `only_groups` - Capture only messages with groups
        • `only_pm` - Capture only messages with private chats
        • `startswith` - Capture only messages that start with given text
        • `endswith` - Capture only messages that end with given text
        • `contains` - Capture only messages that contain given text
        • `regex` - Capture only messages that match given regex
        • `filter` - Capture only messages that pass given function
        • `from_id` - Capture only messages from given user
        • `chat_id` - Capture only messages from given chat
        • `thumb_url` - Works for inline command handlers. Will be shown in help

    Usage example:

    @loader.tag("no_commands", "out")
    @loader.tag("no_commands", out=True)
    @loader.tag(only_messages=True)
    @loader.tag("only_messages", "only_pm", regex=r"^[.] ?hikka$", from_id=659800858)

    💡 These tags can be used directly in `@loader.watcher`:
    @loader.watcher("no_commands", out=True)
    """

    def inner(func: callable):
        for _tag in tags:
            setattr(func, _tag, True)

        for _tag, value in kwarg_tags.items():
            setattr(func, _tag, value)

        return func

    return inner


def _mark_method(mark: str, *args, **kwargs) -> callable:
    """
    Mark method as a method of a class
    """

    def decorator(func: callable) -> callable:
        setattr(func, mark, True)
        for arg in args:
            setattr(func, arg, True)

        for kwarg, value in kwargs.items():
            setattr(func, kwarg, value)

        return func

    return decorator


def command(*args, **kwargs):
    """
    Decorator that marks function as userbot command
    """
    return _mark_method("is_command", *args, **kwargs)


def debug_method(*args, **kwargs):
    """
    Decorator that marks function as IDM (Internal Debug Method)
    :param name: Name of the method
    """
    return _mark_method("is_debug_method", *args, **kwargs)


def inline_handler(*args, **kwargs):
    """
    Decorator that marks function as inline handler
    """
    return _mark_method("is_inline_handler", *args, **kwargs)


def watcher(*args, **kwargs):
    """
    Decorator that marks function as watcher
    """
    return _mark_method("is_watcher", *args, **kwargs)


def callback_handler(*args, **kwargs):
    """
    Decorator that marks function as callback handler
    """
    return _mark_method("is_callback_handler", *args, **kwargs)


def raw_handler(*updates: TLObject):
    """
    Decorator that marks function as raw telethon events handler
    Use it to prevent zombie-event-handlers, left by unloaded modules
    :param updates: Update(-s) to handle
    ⚠️ Do not try to simulate behavior of this decorator by yourself!
    ⚠️ This feature won't work, if you dynamically declare method with decorator!
    """

    def inner(func: callable):
        func.is_raw_handler = True
        func.updates = updates
        func.id = uuid4().hex
        return func

    return inner


class Modules:
    """Stores all registered modules"""

    def __init__(
        self,
        client: "CustomTelegramClient",  # type: ignore
        db: Database,
        allclients: list,
        translator: Translator,
    ):
        self._initial_registration = True
        self.commands = {}
        self.inline_handlers = {}
        self.callback_handlers = {}
        self.aliases = {}
        self.modules = []  # skipcq: PTC-W0052
        self.libraries = []
        self.watchers = []
        self._log_handlers = []
        self._core_commands = []
        self.__approve = []
        self.allclients = allclients
        self.client = client
        self._db = db
        self._translator = translator
        self.secure_boot = False
        asyncio.ensure_future(self._junk_collector())

    async def _junk_collector(self):
        """
        Periodically reloads commands, inline handlers, callback handlers and watchers from loaded
        modules to prevent zombie handlers
        """
        while True:
            await asyncio.sleep(30)
            commands = {}
            inline_handlers = {}
            callback_handlers = {}
            watchers = []
            for module in self.modules:
                commands |= module.hikka_commands
                inline_handlers |= module.hikka_inline_handlers
                callback_handlers |= module.hikka_callback_handlers
                watchers.extend(module.hikka_watchers.values())

            self.commands = commands
            self.inline_handlers = inline_handlers
            self.callback_handlers = callback_handlers
            self.watchers = watchers

            logger.debug(
                "Reloaded %s commands,"
                " %s inline handlers,"
                " %s callback handlers and"
                " %s watchers",
                len(self.commands),
                len(self.inline_handlers),
                len(self.callback_handlers),
                len(self.watchers),
            )

    async def register_all(
        self,
        mods: typing.Optional[typing.List[str]] = None,
        no_external: bool = False,
    ) -> typing.List[Module]:
        """Load all modules in the module directory"""
        external_mods = []

        if not mods:
            mods = [
                os.path.join(utils.get_base_dir(), MODULES_NAME, mod)
                for mod in filter(
                    lambda x: (x.endswith(".py") and not x.startswith("_")),
                    os.listdir(os.path.join(utils.get_base_dir(), MODULES_NAME)),
                )
            ]

            self.secure_boot = self._db.get(__name__, "secure_boot", False)

            external_mods = (
                []
                if self.secure_boot
                else [
                    os.path.join(LOADED_MODULES_DIR, mod)
                    for mod in filter(
                        lambda x: (
                            x.endswith(f"{self.client.tg_id}.py")
                            and not x.startswith("_")
                        ),
                        os.listdir(LOADED_MODULES_DIR),
                    )
                ]
            )

        loaded = []
        loaded += await self._register_modules(mods)

        if not no_external:
            loaded += await self._register_modules(external_mods, "<file>")

        return loaded

    async def _register_modules(
        self,
        modules: list,
        origin: str = "<core>",
    ) -> typing.List[Module]:
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        loaded = []

        for mod in modules:
            try:
                mod_shortname = (
                    os.path.basename(mod)
                    .rsplit(".py", maxsplit=1)[0]
                    .rsplit("_", maxsplit=1)[0]
                )
                module_name = f"{__package__}.{MODULES_NAME}.{mod_shortname}"
                user_friendly_origin = (
                    "<core {}>" if origin == "<core>" else "<file {}>"
                ).format(mod_shortname)

                logger.debug("Loading %s from filesystem", module_name)

                with open(mod, "r") as file:
                    spec = importlib.machinery.ModuleSpec(
                        module_name,
                        StringLoader(file.read(), user_friendly_origin),
                        origin=user_friendly_origin,
                    )

                loaded += [await self.register_module(spec, module_name, origin)]
            except BaseException as e:
                logger.exception("Failed to load module %s due to %s:", mod, e)

        return loaded

    async def register_module(
        self,
        spec: importlib.machinery.ModuleSpec,
        module_name: str,
        origin: str = "<core>",
        save_fs: bool = False,
    ) -> Module:
        """Register single module from importlib spec"""
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

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

        await self.complete_registration(ret)
        ret.__origin__ = origin

        cls_name = ret.__class__.__name__

        if save_fs:
            path = os.path.join(
                LOADED_MODULES_DIR,
                f"{cls_name}_{self.client.tg_id}.py",
            )

            if origin == "<string>":
                with open(path, "w") as f:
                    f.write(spec.loader.data.decode("utf-8"))

                logger.debug("Saved class %s to path %s", cls_name, path)

        return ret

    def add_aliases(self, aliases: dict):
        """Saves aliases and applies them to <core>/<file> modules"""
        self.aliases.update(aliases)
        for alias, cmd in aliases.items():
            self.add_alias(alias, cmd)

    def register_raw_handlers(self, instance: Module):
        """Register event handlers for a module"""
        for name, handler in utils.iter_attrs(instance):
            if getattr(handler, "is_raw_handler", False):
                self.client.dispatcher.raw_handlers.append(handler)
                logger.debug(
                    "Registered raw handler %s for %s. ID: %s",
                    name,
                    instance.__class__.__name__,
                    handler.id,
                )

    def register_commands(self, instance: Module):
        """Register commands from instance"""
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        if instance.__origin__.startswith("<core"):
            self._core_commands += list(
                map(lambda x: x.lower(), list(instance.hikka_commands))
            )

        for _command, cmd in instance.hikka_commands.items():
            # Restrict overwriting core modules' commands
            if (
                _command.lower() in self._core_commands
                and not instance.__origin__.startswith("<core")
            ):
                with contextlib.suppress(Exception):
                    self.modules.remove(instance)

                raise CoreOverwriteError(command=_command)

            self.commands.update({_command.lower(): cmd})

        for alias, cmd in self.aliases.copy().items():
            if cmd in instance.hikka_commands:
                self.add_alias(alias, cmd)

        self.register_inline_stuff(instance)

    def register_inline_stuff(self, instance: Module):
        for name, func in instance.hikka_inline_handlers.copy().items():
            if name.lower() in self.inline_handlers:
                if (
                    hasattr(func, "__self__")
                    and hasattr(self.inline_handlers[name], "__self__")
                    and (
                        func.__self__.__class__.__name__
                        != self.inline_handlers[name].__self__.__class__.__name__
                    )
                ):
                    logger.debug(
                        "Duplicate inline_handler %s of %s",
                        name,
                        instance.__class__.__name__,
                    )

                logger.debug(
                    "Replacing inline_handler %s for %s",
                    self.inline_handlers[name],
                    instance.__class__.__name__,
                )

            self.inline_handlers.update({name.lower(): func})

        for name, func in instance.hikka_callback_handlers.copy().items():
            if name.lower() in self.callback_handlers and (
                hasattr(func, "__self__")
                and hasattr(self.callback_handlers[name], "__self__")
                and func.__self__.__class__.__name__
                != self.callback_handlers[name].__self__.__class__.__name__
            ):
                logger.debug(
                    "Duplicate callback_handler %s of %s",
                    name,
                    instance.__class__.__name__,
                )

            self.callback_handlers.update({name.lower(): func})

    def unregister_inline_stuff(self, instance: Module, purpose: str):
        for name, func in instance.hikka_inline_handlers.copy().items():
            if name.lower() in self.inline_handlers and (
                hasattr(func, "__self__")
                and hasattr(self.inline_handlers[name], "__self__")
                and func.__self__.__class__.__name__
                == self.inline_handlers[name].__self__.__class__.__name__
            ):
                del self.inline_handlers[name.lower()]
                logger.debug(
                    "Unregistered inline_handler %s of %s for %s",
                    name,
                    instance.__class__.__name__,
                    purpose,
                )

        for name, func in instance.hikka_callback_handlers.copy().items():
            if name.lower() in self.callback_handlers and (
                hasattr(func, "__self__")
                and hasattr(self.callback_handlers[name], "__self__")
                and func.__self__.__class__.__name__
                == self.callback_handlers[name].__self__.__class__.__name__
            ):
                del self.callback_handlers[name.lower()]
                logger.debug(
                    "Unregistered callback_handler %s of %s for %s",
                    name,
                    instance.__class__.__name__,
                    purpose,
                )

    def register_watchers(self, instance: Module):
        """Register watcher from instance"""
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        for _watcher in self.watchers:
            if _watcher.__self__.__class__.__name__ == instance.__class__.__name__:
                logger.debug("Removing watcher %s for update", _watcher)
                self.watchers.remove(_watcher)

        for _watcher in instance.hikka_watchers.values():
            self.watchers += [_watcher]

    def _lookup(self, modname: str):
        return next(
            (lib for lib in self.libraries if lib.name.lower() == modname.lower()),
            False,
        ) or next(
            (
                mod
                for mod in self.modules
                if mod.__class__.__name__.lower() == modname.lower()
                or mod.name.lower() == modname.lower()
            ),
            False,
        )

    @property
    def get_approved_channel(self):
        return self.__approve.pop(0) if self.__approve else None

    async def _approve(
        self,
        call: InlineCall,
        channel: EntityLike,
        event: asyncio.Event,
    ):
        local_event = asyncio.Event()
        self.__approve += [(channel, local_event)]
        await local_event.wait()
        event.status = local_event.status
        event.set()
        await call.edit(
            "💫 <b>Joined <a"
            f' href="https://t.me/{channel.username}">{utils.escape_html(channel.title)}</a></b>',
            gif="https://static.hikari.gay/0d32cbaa959e755ac8eef610f01ba0bd.gif",
        )

    async def _decline(
        self,
        call: InlineCall,
        channel: EntityLike,
        event: asyncio.Event,
    ):
        self._db.set(
            "hikka.main",
            "declined_joins",
            list(set(self._db.get("hikka.main", "declined_joins", []) + [channel.id])),
        )
        event.status = False
        event.set()
        await call.edit(
            "✖️ <b>Declined joining <a"
            f' href="https://t.me/{channel.username}">{utils.escape_html(channel.title)}</a></b>',
            gif="https://static.hikari.gay/0d32cbaa959e755ac8eef610f01ba0bd.gif",
        )

    async def _request_join(
        self,
        peer: EntityLike,
        reason: str,
        assure_joined: typing.Optional[bool] = False,
        _module: Module = None,
    ) -> bool:
        """
        Request to join a channel.
        :param peer: The channel to join.
        :param reason: The reason for joining.
        :param assure_joined: If set, module will not be loaded unless the required channel is joined.
                              ⚠️ Works only in `client_ready`!
                              ⚠️ If user declines to join channel, he will not be asked to
                              join again, so unless he joins it manually, module will not be loaded
                              ever.
        :return: Status of the request.
        :rtype: bool
        :notice: This method will block module loading until the request is approved or declined.
        """
        event = asyncio.Event()
        await self.client(
            UpdateNotifySettingsRequest(
                peer=self.inline.bot_username,
                settings=InputPeerNotifySettings(show_previews=False, silent=False),
            )
        )

        channel = await self.client.get_entity(peer)
        if channel.id in self._db.get("hikka.main", "declined_joins", []):
            if assure_joined:
                raise LoadError(
                    f"You need to join @{channel.username} in order to use this module"
                )

            return False

        if not isinstance(channel, Channel):
            raise TypeError("`peer` field must be a channel")

        if getattr(channel, "left", True):
            channel = await self.client.force_get_entity(peer)

        if not getattr(channel, "left", True):
            return True

        _module.strings._base_strings["_hikka_internal_request_join"] = (
            f"💫 <b>Module </b><code>{_module.__class__.__name__}</code><b> requested to"
            " join channel <a"
            f" href='https://t.me/{channel.username}'>{utils.escape_html(channel.title)}</a></b>\n\n<b>❓"
            f" Reason: </b><i>{utils.escape_html(reason)}</i>"
        )

        if not hasattr(_module, "strings_ru"):
            _module.strings_ru = {}

        _module.strings_ru["_hikka_internal_request_join"] = (
            f"💫 <b>Модуль </b><code>{_module.__class__.__name__}</code><b> запросил"
            " разрешение на вступление в канал <a"
            f" href='https://t.me/{channel.username}'>{utils.escape_html(channel.title)}</a></b>\n\n<b>❓"
            f" Причина: </b><i>{utils.escape_html(reason)}</i>"
        )

        await self.inline.bot.send_animation(
            self.client.tg_id,
            "https://static.hikari.gay/ab3adf144c94a0883bfe489f4eebc520.gif",
            caption=_module.strings("_hikka_internal_request_join"),
            reply_markup=self.inline.generate_markup(
                [
                    {
                        "text": "💫 Approve",
                        "callback": self._approve,
                        "args": (channel, event),
                    },
                    {
                        "text": "✖️ Decline",
                        "callback": self._decline,
                        "args": (channel, event),
                    },
                ]
            ),
        )

        _module.hikka_wait_channel_approve = (
            _module.__class__.__name__,
            channel,
            reason,
        )
        await event.wait()

        with contextlib.suppress(AttributeError):
            delattr(_module, "hikka_wait_channel_approve")

        if assure_joined and not event.status:
            raise LoadError(
                f"You need to join @{channel.username} in order to use this module"
            )

        return event.status

    def get_prefix(self) -> str:
        return self._db.get("hikka.main", "command_prefix", ".")

    async def complete_registration(self, instance: Module):
        """Complete registration of instance"""
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        instance.allclients = self.allclients
        instance.allmodules = self
        instance.hikka = True
        instance.get = partial(self._get, _owner=instance.__class__.__name__)
        instance.set = partial(self._set, _owner=instance.__class__.__name__)
        instance.pointer = partial(self._pointer, _owner=instance.__class__.__name__)
        instance.get_prefix = self.get_prefix
        instance.client = self.client
        instance._client = self.client
        instance.db = self._db
        instance._db = self._db
        instance.lookup = self._lookup
        instance.import_lib = self._mod_import_lib
        instance.tg_id = self.client.tg_id
        instance._tg_id = self.client.tg_id
        instance.request_join = partial(self._request_join, _module=instance)

        instance.animate = self._animate

        for module in self.modules:
            if module.__class__.__name__ == instance.__class__.__name__:
                if module.__origin__.startswith("<core"):
                    raise CoreOverwriteError(
                        module=module.__class__.__name__[:-3]
                        if module.__class__.__name__.endswith("Mod")
                        else module.__class__.__name__
                    )

                logger.debug("Removing module %s for update", module)
                await module.on_unload()

                self.modules.remove(module)
                for method in dir(module):
                    if isinstance(getattr(module, method), InfiniteLoop):
                        getattr(module, method).stop()
                        logger.debug(
                            "Stopped loop in module %s, method %s", module, method
                        )

        self.modules += [instance]

    def _get(
        self,
        key: str,
        default: typing.Optional[JSONSerializable] = None,
        _owner: str = None,
    ) -> JSONSerializable:
        return self._db.get(_owner, key, default)

    def _set(self, key: str, value: JSONSerializable, _owner: str = None) -> bool:
        return self._db.set(_owner, key, value)

    def _pointer(
        self,
        key: str,
        default: typing.Optional[JSONSerializable] = None,
        _owner: str = None,
    ) -> JSONSerializable:
        return self._db.pointer(_owner, key, default)

    async def _mod_import_lib(
        self,
        url: str,
        *,
        suspend_on_error: typing.Optional[bool] = False,
        _did_requirements: bool = False,
    ) -> object:
        """
        Import library from url and register it in :obj:`Modules`
        :param url: Url to import
        :param suspend_on_error: Will raise :obj:`loader.SelfSuspend` if library can't be loaded
        :return: :obj:`Library`
        :raise: SelfUnload if :attr:`suspend_on_error` is True and error occurred
        :raise: HTTPError if library is not found
        :raise: ImportError if library doesn't have any class which is a subclass of :obj:`loader.Library`
        :raise: ImportError if library name doesn't end with `Lib`
        :raise: RuntimeError if library throws in :method:`init`
        :raise: RuntimeError if library classname exists in :obj:`Modules`.libraries
        """

        def _raise(e: Exception):
            if suspend_on_error:
                raise SelfSuspend("Required library is not available or is corrupted.")

            raise e

        if not utils.check_url(url):
            _raise(ValueError("Invalid url for library"))

        code = await utils.run_sync(requests.get, url)
        code.raise_for_status()
        code = code.text

        if re.search(r"# ?scope: ?hikka_min", code):
            ver = tuple(
                map(
                    int,
                    re.search(r"# ?scope: ?hikka_min ((\d+\.){2}\d+)", code)[1].split(
                        "."
                    ),
                )
            )

            if version.__version__ < ver:
                _raise(
                    RuntimeError(
                        f"Library requires Hikka version {'{}.{}.{}'.format(*ver)}+"
                    )
                )

        module = f"hikka.libraries.{url.replace('%', '%%').replace('.', '%d')}"
        origin = f"<library {url}>"

        spec = importlib.machinery.ModuleSpec(
            module,
            StringLoader(code, origin),
            origin=origin,
        )
        try:
            instance = importlib.util.module_from_spec(spec)
            sys.modules[module] = instance
            spec.loader.exec_module(instance)
        except ImportError as e:
            logger.info(
                "Library loading failed, attemping dependency installation (%s)",
                e.name,
            )
            # Let's try to reinstall dependencies
            try:
                requirements = list(
                    filter(
                        lambda x: not x.startswith(("-", "_", ".")),
                        map(
                            str.strip,
                            VALID_PIP_PACKAGES.search(code)[1].split(),
                        ),
                    )
                )
            except TypeError:
                logger.warning(
                    "No valid pip packages specified in code, attemping"
                    " installation from error"
                )
                requirements = [e.name]

            logger.debug("Installing requirements: %s", requirements)

            if not requirements or _did_requirements:
                _raise(e)

            pip = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-q",
                "--disable-pip-version-check",
                "--no-warn-script-location",
                *["--user"] if USER_INSTALL else [],
                *requirements,
            )

            rc = await pip.wait()

            if rc != 0:
                _raise(e)

            importlib.invalidate_caches()

            kwargs = utils.get_kwargs()
            kwargs["_did_requirements"] = True

            return await self._mod_import_lib(**kwargs)  # Try again

        lib_obj = next(
            (
                value()
                for value in vars(instance).values()
                if inspect.isclass(value) and issubclass(value, Library)
            ),
            None,
        )

        if not lib_obj:
            _raise(ImportError("Invalid library. No class found"))

        if not lib_obj.__class__.__name__.endswith("Lib"):
            _raise(
                ImportError(
                    "Invalid library. Classname {} does not end with 'Lib'".format(
                        lib_obj.__class__.__name__
                    )
                )
            )

        if (
            all(
                line.replace(" ", "") != "#scope:no_stats" for line in code.splitlines()
            )
            and self._db.get("hikka.main", "stats", True)
            and url is not None
            and utils.check_url(url)
        ):
            with contextlib.suppress(Exception):
                await self._lookup("loader")._send_stats(url)

        lib_obj.client = self.client
        lib_obj._client = self.client  # skipcq
        lib_obj.db = self._db
        lib_obj._db = self._db  # skipcq
        lib_obj.name = lib_obj.__class__.__name__
        lib_obj.source_url = url.strip("/")

        lib_obj.lookup = self._lookup
        lib_obj.inline = self.inline
        lib_obj.tg_id = self.client.tg_id
        lib_obj.allmodules = self
        lib_obj._lib_get = partial(
            self._get,
            _owner=lib_obj.__class__.__name__,
        )
        lib_obj._lib_set = partial(
            self._set,
            _owner=lib_obj.__class__.__name__,
        )
        lib_obj._lib_pointer = partial(
            self._pointer,
            _owner=lib_obj.__class__.__name__,
        )
        lib_obj.get_prefix = self.get_prefix

        for old_lib in self.libraries:
            if old_lib.name == lib_obj.name and (
                not isinstance(getattr(old_lib, "version", None), tuple)
                and not isinstance(getattr(lib_obj, "version", None), tuple)
                or old_lib.version >= lib_obj.version
            ):
                logger.debug("Using existing instance of library %s", old_lib.name)
                return old_lib

        if hasattr(lib_obj, "init"):
            if not callable(lib_obj.init):
                _raise(ValueError("Library init() must be callable"))

            try:
                await lib_obj.init()
            except Exception:
                _raise(RuntimeError("Library init() failed"))

        if hasattr(lib_obj, "config"):
            if not isinstance(lib_obj.config, LibraryConfig):
                _raise(
                    RuntimeError("Library config must be a `LibraryConfig` instance")
                )

            libcfg = lib_obj.db.get(
                lib_obj.__class__.__name__,
                "__config__",
                {},
            )

            for conf in lib_obj.config:
                with contextlib.suppress(Exception):
                    lib_obj.config.set_no_raise(
                        conf,
                        (
                            libcfg[conf]
                            if conf in libcfg
                            else os.environ.get(f"{lib_obj.__class__.__name__}.{conf}")
                            or lib_obj.config.getdef(conf)
                        ),
                    )

        if hasattr(lib_obj, "strings"):
            lib_obj.strings = Strings(lib_obj, self._translator)

        lib_obj.translator = self._translator

        for old_lib in self.libraries:
            if old_lib.name == lib_obj.name:
                if hasattr(old_lib, "on_lib_update") and callable(
                    old_lib.on_lib_update
                ):
                    await old_lib.on_lib_update(lib_obj)

                replace_all_refs(old_lib, lib_obj)
                logger.debug(
                    "Replacing existing instance of library %s with updated object",
                    lib_obj.name,
                )
                return lib_obj

        self.libraries += [lib_obj]
        return lib_obj

    def dispatch(self, _command: str) -> tuple:
        """Dispatch command to appropriate module"""

        return next(
            (
                (cmd, self.commands[cmd.lower()])
                for cmd in [_command, self.aliases.get(_command.lower())]
                if cmd and cmd.lower() in self.commands
            ),
            (_command, None),
        )

    def send_config(self, skip_hook: bool = False):
        """Configure modules"""
        for mod in self.modules:
            self.send_config_one(mod, skip_hook)

    def send_config_one(self, mod: Module, skip_hook: bool = False):
        """Send config to single instance"""
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        if hasattr(mod, "config"):
            modcfg = self._db.get(
                mod.__class__.__name__,
                "__config__",
                {},
            )
            try:
                for conf in mod.config:
                    with contextlib.suppress(validators.ValidationError):
                        mod.config.set_no_raise(
                            conf,
                            (
                                modcfg[conf]
                                if conf in modcfg
                                else os.environ.get(f"{mod.__class__.__name__}.{conf}")
                                or mod.config.getdef(conf)
                            ),
                        )
            except AttributeError:
                logger.warning(
                    "Got invalid config instance. Expected `ModuleConfig`, got %s, %s",
                    type(mod.config),
                    mod.config,
                )

        if not hasattr(mod, "name"):
            mod.name = mod.strings["name"]

        if skip_hook:
            return

        if hasattr(mod, "strings"):
            mod.strings = Strings(mod, self._translator)

        mod.translator = self._translator

        try:
            mod.config_complete()
        except Exception as e:
            logger.exception("Failed to send mod config complete signal due to %s", e)
            raise

    async def send_ready(self):
        """Send all data to all modules"""
        # Init inline manager anyway, so the modules
        # can access its `init_complete`
        inline_manager = InlineManager(self.client, self._db, self)

        await inline_manager._register_manager()

        # We save it to `Modules` attribute, so not to re-init
        # it everytime module is loaded. Then we can just
        # re-assign it to all modules
        self.inline = inline_manager

        try:
            await asyncio.gather(*[self.send_ready_one(mod) for mod in self.modules])
        except Exception as e:
            logger.exception("Failed to send mod init complete signal due to %s", e)

    async def _animate(
        self,
        message: typing.Union[Message, InlineMessage],
        frames: typing.List[str],
        interval: typing.Union[float, int],
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

        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        if interval < 0.1:
            logger.warning(
                "Resetting animation interval to 0.1s, because it may get you in"
                " floodwaits bro"
            )
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
        no_self_unload: bool = False,
        from_dlmod: bool = False,
    ):
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        mod.inline = self.inline

        for method in dir(mod):
            if isinstance(getattr(mod, method), InfiniteLoop):
                setattr(getattr(mod, method), "module_instance", mod)

                if getattr(mod, method).autostart:
                    getattr(mod, method).start()

                logger.debug("Added module %s to method %s", mod, method)

        if from_dlmod:
            try:
                if len(inspect.signature(mod.on_dlmod).parameters) == 2:
                    await mod.on_dlmod(self.client, self._db)
                else:
                    await mod.on_dlmod()
            except Exception:
                logger.info("Can't process `on_dlmod` hook", exc_info=True)

        try:
            if len(inspect.signature(mod.client_ready).parameters) == 2:
                await mod.client_ready(self.client, self._db)
            else:
                await mod.client_ready()
        except SelfUnload as e:
            if no_self_unload:
                raise e

            logger.debug("Unloading %s, because it raised SelfUnload", mod)
            self.modules.remove(mod)
        except SelfSuspend as e:
            if no_self_unload:
                raise e

            logger.debug("Suspending %s, because it raised SelfSuspend", mod)
            return
        except Exception as e:
            logger.exception(
                "Failed to send mod init complete signal for %s due to %s,"
                " attempting unload",
                mod,
                e,
            )
            self.modules.remove(mod)
            raise

        self.unregister_commands(mod, "update")
        self.unregister_raw_handlers(mod, "update")

        self.register_commands(mod)
        self.register_watchers(mod)
        self.register_raw_handlers(mod)

    def get_classname(self, name: str) -> str:
        return next(
            (
                module.__class__.__module__
                for module in reversed(self.modules)
                if name in (module.name, module.__class__.__module__)
            ),
            name,
        )

    async def unload_module(self, classname: str) -> typing.List[str]:
        """Remove module and all stuff from it"""
        worked = []

        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self.client.tg_id)

        for module in self.modules:
            if classname.lower() in (
                module.name.lower(),
                module.__class__.__name__.lower(),
            ):
                if module.__origin__.startswith("<core"):
                    raise CoreUnloadError(module.__class__.__name__)

                worked += [module.__class__.__name__]

                name = module.__class__.__name__
                path = os.path.join(
                    LOADED_MODULES_DIR,
                    f"{name}_{self.client.tg_id}.py",
                )

                if os.path.isfile(path):
                    os.remove(path)
                    logger.debug("Removed %s file at path %s", name, path)

                logger.debug("Removing module %s for unload", module)
                self.modules.remove(module)

                await module.on_unload()

                self.unregister_raw_handlers(module, "unload")
                self.unregister_loops(module, "unload")
                self.unregister_commands(module, "unload")
                self.unregister_watchers(module, "unload")
                self.unregister_inline_stuff(module, "unload")

        logger.debug("Worked: %s", worked)
        return worked

    def unregister_loops(self, instance: Module, purpose: str):
        for name, method in utils.iter_attrs(instance):
            if isinstance(method, InfiniteLoop):
                logger.debug(
                    "Stopping loop for %s in module %s, method %s",
                    purpose,
                    instance.__class__.__name__,
                    name,
                )
                method.stop()

    def unregister_commands(self, instance: Module, purpose: str):
        for name, cmd in self.commands.copy().items():
            if cmd.__self__.__class__.__name__ == instance.__class__.__name__:
                logger.debug(
                    "Removing command %s of module %s for %s",
                    name,
                    instance.__class__.__name__,
                    purpose,
                )
                del self.commands[name]
                for alias, _command in self.aliases.copy().items():
                    if _command == name:
                        del self.aliases[alias]

    def unregister_watchers(self, instance: Module, purpose: str):
        for _watcher in self.watchers.copy():
            if _watcher.__self__.__class__.__name__ == instance.__class__.__name__:
                logger.debug(
                    "Removing watcher %s of module %s for %s",
                    _watcher,
                    instance.__class__.__name__,
                    purpose,
                )
                self.watchers.remove(_watcher)

    def unregister_raw_handlers(self, instance: Module, purpose: str):
        """Unregister event handlers for a module"""
        for handler in self.client.dispatcher.raw_handlers:
            if handler.__self__.__class__.__name__ == instance.__class__.__name__:
                self.client.dispatcher.raw_handlers.remove(handler)
                logger.debug(
                    "Unregistered raw handler of module %s for %s. ID: %s",
                    instance.__class__.__name__,
                    purpose,
                    handler.id,
                )

    def add_alias(self, alias: str, cmd: str) -> bool:
        """Make an alias"""
        if cmd not in self.commands:
            return False

        self.aliases[alias.lower().strip()] = cmd
        return True

    def remove_alias(self, alias: str) -> bool:
        """Remove an alias"""
        return bool(self.aliases.pop(alias.lower().strip(), None))

    async def log(self, *args, **kwargs):
        """Unnecessary placeholder for logging"""
