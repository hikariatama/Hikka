#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html


import ast
import asyncio
import contextlib
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Union
from importlib.abc import SourceLoader
from telethon.tl.types import Message

from .inline.types import (  # skipcq: PY-W2000
    InlineMessage,
    BotInlineMessage,
    InlineCall,
    BotInlineCall,
    InlineUnit,
    BotMessage,
    InlineQuery,
)
from . import validators  # skipcq: PY-W2000
from .pointers import (  # skipcq: PY-W2000
    PointerList,
    PointerDict,
)

logger = logging.getLogger(__name__)


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


class Module:
    strings = {"name": "Unknown"}

    """There is no help for this module"""

    def config_complete(self):
        """Called when module.config is populated"""

    async def client_ready(self, client, db):
        """Called after client is ready (after config_loaded)"""

    async def on_unload(self):
        """Called after unloading / reloading module"""

    async def on_dlmod(self, client, db):
        """
        Called after the module is first time loaded with .dlmod or .loadmod

        Possible use-cases:
        - Send reaction to author's channel message
        - Join author's channel
        - Create asset folder
        - ...

        ⚠️ Note, that any error there will not interrupt module load, and will just
        send a message to logs with verbosity INFO and exception traceback
        """

    def __getattr__(self, name: str):
        if name in {"hikka_commands", "commands"}:
            return get_commands(self)

        if name in {"hikka_inline_handlers", "inline_handlers"}:
            return get_inline_handlers(self)

        if name in {"hikka_callback_handlers", "callback_handlers"}:
            return get_callback_handlers(self)

        if name in {"hikka_watchers", "watchers"}:
            return get_watchers(self)

        raise AttributeError(f"Module has no attribute {name}")


class Library:
    """All external libraries must have a class-inheritant from this class"""


class LoadError(Exception):
    """Tells user, why your module can't be loaded, if raised in `client_ready`"""

    def __init__(self, error_message: str):  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class CoreOverwriteError(LoadError):
    """Is being raised when core module or command is overwritten"""

    def __init__(self, module: Optional[str] = None, command: Optional[str] = None):
        self.type = "module" if module else "command"
        self.target = module or command
        super().__init__()

    def __str__(self) -> str:
        return (
            f"Module {self.target} will not be overwritten, because it's core"
            if self.type == "module"
            else f"Command {self.target} will not be overwritten, because it's core"
        )


class CoreUnloadError(Exception):
    """Is being raised when user tries to unload core module"""

    def __init__(self, module: str):
        self.module = module
        super().__init__()

    def __str__(self) -> str:
        return f"Module {self.module} will not be unloaded, because it's core"


class SelfUnload(Exception):
    """Silently unloads module, if raised in `client_ready`"""

    def __init__(self, error_message: Optional[str] = ""):
        super().__init__()
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class SelfSuspend(Exception):
    """
    Silently suspends module, if raised in `client_ready`
    Commands and watcher will not be registered if raised
    Module won't be unloaded from db and will be unfreezed after restart, unless
    the exception is raised again
    """

    def __init__(self, error_message: Optional[str] = ""):
        super().__init__()
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class StopLoop(Exception):
    """Stops the loop, in which is raised"""


class ModuleConfig(dict):
    """Stores config for modules and apparently libraries"""

    def __init__(self, *entries):
        if all(isinstance(entry, ConfigValue) for entry in entries):
            # New config format processing
            self._config = {config.option: config for config in entries}
        else:
            # Legacy config processing
            keys = []
            values = []
            defaults = []
            docstrings = []
            for i, entry in enumerate(entries):
                if i % 3 == 0:
                    keys += [entry]
                elif i % 3 == 1:
                    values += [entry]
                    defaults += [entry]
                else:
                    docstrings += [entry]

            self._config = {
                key: ConfigValue(option=key, default=default, doc=doc)
                for key, default, doc in zip(keys, defaults, docstrings)
            }

        super().__init__(
            {option: config.value for option, config in self._config.items()}
        )

    def getdoc(self, key: str, message: Message = None) -> str:
        """Get the documentation by key"""
        ret = self._config[key].doc

        if callable(ret):
            try:
                # Compatibility tweak
                # does nothing in Hikka
                ret = ret(message)
            except Exception:
                ret = ret()

        return ret

    def getdef(self, key: str) -> str:
        """Get the default value by key"""
        return self._config[key].default

    def __setitem__(self, key: str, value: Any):
        self._config[key].value = value
        self.update({key: value})

    def set_no_raise(self, key: str, value: Any):
        self._config[key].set_no_raise(value)
        self.update({key: value})

    def __getitem__(self, key: str) -> Any:
        try:
            return self._config[key].value
        except KeyError:
            return None


LibraryConfig = ModuleConfig


class _Placeholder:
    """Placeholder to determine if the default value is going to be set"""


async def wrap(func: Awaitable):
    with contextlib.suppress(Exception):
        return await func()


def syncwrap(func: Callable):
    with contextlib.suppress(Exception):
        return func()


@dataclass(repr=True)
class ConfigValue:
    option: str
    default: Any = None
    doc: Union[callable, str] = "No description"
    value: Any = field(default_factory=_Placeholder)
    validator: Optional[callable] = None
    on_change: Optional[Union[Awaitable, Callable]] = None

    def __post_init__(self):
        if isinstance(self.value, _Placeholder):
            self.value = self.default

    def set_no_raise(self, value: Any) -> bool:
        """
        Sets the config value w/o ValidationError being raised
        Should not be used uninternally
        """
        return self.__setattr__("value", value, ignore_validation=True)

    def __setattr__(
        self,
        key: str,
        value: Any,
        *,
        ignore_validation: Optional[bool] = False,
    ) -> bool:
        if key == "value":
            with contextlib.suppress(Exception):
                value = ast.literal_eval(value)
            # Convert value to list if it's tuple just not to mess up
            # with json convertations
            if isinstance(value, (set, tuple)):
                value = list(value)

            if isinstance(value, list):
                value = [
                    item.strip() if isinstance(item, str) else item for item in value
                ]

            if self.validator is not None:
                if value is not None:
                    try:
                        value = self.validator.validate(value)
                    except validators.ValidationError as e:
                        if not ignore_validation:
                            raise e

                        logger.debug(
                            f"Config value was broken ({value}), so it was reset to"
                            f" {self.default}"
                        )

                        value = self.default
                else:
                    defaults = {
                        "String": "",
                        "Integer": 0,
                        "Boolean": False,
                        "Series": [],
                        "Float": 0.0,
                    }

                    if self.validator.internal_id in defaults:
                        logger.debug(
                            "Config value was None, so it was reset to"
                            f" {defaults[self.validator.internal_id]}"
                        )
                        value = defaults[self.validator.internal_id]

            # This attribute will tell the `Loader` to save this value in db
            self._save_marker = True

            if not ignore_validation and callable(self.on_change):
                if inspect.iscoroutinefunction(self.on_change):
                    asyncio.ensure_future(wrap(self.on_change))
                else:
                    syncwrap(self.on_change)

        object.__setattr__(self, key, value)


def _get_members(
    mod: Module,
    ending: str,
    attribute: Optional[str] = None,
    strict: bool = False,
) -> dict:
    """Get method of module, which end with ending"""
    return {
        (
            method_name.rsplit(ending, maxsplit=1)[0]
            if (method_name == ending if strict else method_name.endswith(ending))
            else method_name
        ): getattr(mod, method_name)
        for method_name in dir(mod)
        if callable(getattr(mod, method_name))
        and (
            (method_name == ending if strict else method_name.endswith(ending))
            or attribute
            and getattr(getattr(mod, method_name), attribute, False)
        )
    }


def get_commands(mod: Module) -> dict:
    """Introspect the module to get its commands"""
    return _get_members(mod, "cmd", "is_command")


def get_inline_handlers(mod: Module) -> dict:
    """Introspect the module to get its inline handlers"""
    return _get_members(mod, "_inline_handler", "is_inline_handler")


def get_callback_handlers(mod: Module) -> dict:
    """Introspect the module to get its callback handlers"""
    return _get_members(mod, "_callback_handler", "is_callback_handler")


def get_watchers(mod: Module) -> dict:
    """Introspect the module to get its watchers"""
    return _get_members(
        mod,
        "watcher",
        "is_watcher",
        strict=True,
    )
