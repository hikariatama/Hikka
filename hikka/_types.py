import ast
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from .inline.types import *  # skipcq: PYL-W0614
from . import validators  # skipcq: PY-W2000

from telethon.tl.types import Message

logger = logging.getLogger(__name__)


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


class LoadError(Exception):
    """Tells user, why your module can't be loaded, if raised in `client_ready`"""

    def __init__(self, error_message: str):  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class CoreOverwriteError(Exception):
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


class SelfUnload(Exception):
    """Silently unloads module, if raised in `client_ready`"""

    def __init__(self, error_message: Optional[str] = ""):  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class StopLoop(Exception):
    """Stops the loop, in which is raised"""


class ModuleConfig(dict):
    """Stores config for each mod, that needs them"""

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


class _Placeholder:
    """Placeholder to determine if the default value is going to be set"""


@dataclass(repr=True)
class ConfigValue:
    option: str
    default: Any = None
    doc: Union[callable, str] = "No description"
    value: Any = field(default_factory=_Placeholder)
    validator: Optional[callable] = None

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
            try:
                value = ast.literal_eval(value)
            except Exception:
                pass

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
                            f"Config value was broken ({value}), so it was reset to {self.default}"
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
                            f"Config value was None, so it was reset to {defaults[self.validator.internal_id]}"
                        )
                        value = defaults[self.validator.internal_id]

            # This attribute will tell the `Loader` to save this value in db
            self._save_marker = True

        object.__setattr__(self, key, value)
