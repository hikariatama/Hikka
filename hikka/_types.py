import logging
from telethon.tl.types import Message


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


class LoadError(Exception):
    def __init__(self, error_message: str) -> None:  # skipcq: PYL-W0231
        self._error = error_message

    def __str__(self) -> str:
        return self._error


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
