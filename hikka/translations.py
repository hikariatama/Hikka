# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import json
import logging
import os
import typing

import requests

from . import utils
from .database import Database
from .tl_cache import CustomTelegramClient
from .types import Module

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self, client: CustomTelegramClient, db: Database):
        self._client = client
        self.db = db

    async def init(self) -> bool:
        self._data = {}
        if not (lang := self.db.get(__name__, "lang", False)):
            return False

        for language in lang.split(" "):
            if utils.check_url(language):
                try:
                    ndata = (await utils.run_sync(requests.get, lang)).json()
                except Exception:
                    logger.exception("Unable to decode %s", lang)
                    continue

                data = ndata.get("data", ndata)

                if any(not isinstance(i, str) for i in data.values()):
                    logger.exception(
                        "Translation pack format is not valid (typecheck failed)"
                    )
                    continue

                self._data.update(data)
                continue

            possible_pack_path = os.path.join(
                utils.get_base_dir(),
                f"langpacks/{language}.json",
            )

            if os.path.isfile(possible_pack_path):
                with open(possible_pack_path, "r") as f:
                    self._data.update(json.load(f))

                return True

        return True

    def getkey(self, key: str) -> typing.Any:
        return self._data.get(key, False)

    def gettext(self, text: str) -> typing.Any:
        return self.getkey(text) or text


class Strings:
    def __init__(self, mod: Module, translator: Translator):
        self._mod = mod
        self._translator = translator

        if not translator:
            logger.debug("Module %s got empty translator %s", mod, translator)

        self._base_strings = mod.strings  # Back 'em up, bc they will get replaced

    def __getitem__(self, key: str) -> str:
        return (
            self._translator.getkey(f"{self._mod.__module__}.{key}")
            if self._translator is not None
            else False
        ) or (
            getattr(
                self._mod,
                next(
                    (
                        f"strings_{lang}"
                        for lang in self._translator.db.get(
                            __name__,
                            "lang",
                            "en",
                        ).split(" ")
                        if hasattr(self._mod, f"strings_{lang}")
                        and isinstance(getattr(self._mod, f"strings_{lang}"), dict)
                        and key in getattr(self._mod, f"strings_{lang}")
                    ),
                    utils.rand(32),
                ),
                self._base_strings,
            )
            if self._translator is not None
            else self._base_strings
        ).get(
            key,
            self._base_strings.get(key, "Unknown strings"),
        )

    def __call__(
        self,
        key: str,
        _: typing.Optional[typing.Any] = None,  # Compatibility tweak for FTG\GeekTG
    ) -> str:
        return self.__getitem__(key)

    def __iter__(self):
        return self._base_strings.__iter__()
