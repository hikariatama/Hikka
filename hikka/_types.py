import logging
from telethon.tl.types import Message


class Module:
    strings = {"name": "Unknown"}

    """There is no help for this module"""

    def config_complete(self):
        """Called when module.config is populated"""

    async def client_ready(self, client, db):
        """Called after client is ready (after config_loaded)"""

    async def on_unload(self):
        """Called after unloading / reloading module"""

    async def _client_ready2(self, client, db):
        """Called after client_ready, for internal use only. Must not be used by non-core modules"""

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
    """Tells user, why your module can't be loaded, if rased in `client_ready`"""

    def __init__(self, error_message: str):  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class SelfUnload(Exception):
    """Silently unloads module, if raised in `client_ready`"""

    def __init__(self, error_message: str = ""):  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


class StopLoop(Exception):
    """Stops the loop, in which is raised"""


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

    def getdoc(self, key: str, message: Message = None) -> str:
        """Get the documentation by key"""
        ret = self._docstrings[key]
        if callable(ret):
            try:
                ret = ret(message)
            except TypeError:  # Invalid number of params
                logging.debug(f"{key} using legacy doc trnsl")
                ret = ret()

        return ret

    def getdef(self, key: str) -> str:
        """Get the default value by key"""
        return self._defaults[key]
