# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import json
import logging

import requests
import os
from . import utils

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self, client, db):
        self._client = client
        self.db = db

    async def init(self) -> bool:
        self._data = {}
        pack = self.db.get(__name__, "pack", False)
        if not pack:
            return False

        possible_pack_path = os.path.join(
            utils.get_base_dir(),
            f"langpacks/{pack}.json",
        )

        if os.path.isfile(possible_pack_path) and pack == self.db.get(
            __name__, "lang", False
        ):
            with open(possible_pack_path, "r") as f:
                self._data = json.loads(f.read())

            return True

        if not utils.check_url(pack):
            return False

        try:
            ndata = (await utils.run_sync(requests.get, pack)).json()
        except Exception:
            logger.exception(f"Unable to decode {pack}")
            return False

        data = ndata.get("data", ndata)

        if any(not isinstance(i, str) for i in data.values()):
            logger.exception("Translation pack format is not valid (typecheck failed)")
            return False

        self._data = data
        return True

    def getkey(self, key):
        return self._data.get(key, False)

    def gettext(self, text):
        return self.getkey(text) or text


class Strings:
    def __init__(self, mod, translator):
        self._mod = mod
        self._translator = translator
        if not translator:
            logger.debug(f"Module {mod=} got empty translator {translator=}")
        self._base_strings = mod.strings  # Back 'em up, bc they will get replaced

    def __getitem__(self, key: str) -> str:
        return (
            self._translator.getkey(f"{self._mod.__module__}.{key}")
            if self._translator is not None
            else False
        ) or (
            getattr(
                self._mod,
                f"strings_{self._translator.db.get(__name__, 'lang', 'en')}",
                self._base_strings,
            )
            if self._translator is not None
            else self._base_strings
        ).get(
            key,
            self._base_strings.get(key, "Unknown strings"),
        )

    def __call__(self, key: str, _=None) -> str:  # `_` is a compatibility tweak
        return self.__getitem__(key)

    def __iter__(self):
        return self._base_strings.__iter__()
