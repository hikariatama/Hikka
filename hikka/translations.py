# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import json
import logging
import typing
from pathlib import Path

import requests
from ruamel.yaml import YAML

from . import utils
from .database import Database
from .tl_cache import CustomTelegramClient
from .types import Module

logger = logging.getLogger(__name__)
yaml = YAML(typ="safe")

PACKS = Path(__file__).parent / "langpacks"
SUPPORTED_LANGUAGES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "fr": "🇫🇷 Français",
    "it": "🇮🇹 Italiano",
    "de": "🇩🇪 Deutsch",
    "tr": "🇹🇷 Türkçe",
    "uz": "🇺🇿 O'zbekcha",
    "es": "🇪🇸 Español",
    "kk": "🇰🇿 Қазақша",
    "tt": "🥟 Татарча",
}


def fmt(text: str, kwargs: dict) -> str:
    for key, value in kwargs.items():
        if f"{{{key}}}" in text:
            text = text.replace(f"{{{key}}}", str(value))

    return text


class BaseTranslator:
    def _get_pack_content(
        self,
        pack: Path,
        prefix: str = "hikka.modules.",
    ) -> typing.Optional[dict]:
        return self._get_pack_raw(pack.read_text(), pack.suffix, prefix)

    def _get_pack_raw(
        self,
        content: str,
        suffix: str,
        prefix: str = "hikka.modules.",
    ) -> typing.Optional[dict]:
        if suffix == ".json":
            return json.loads(content)

        content = yaml.load(content)
        if all(len(key) == 2 for key in content):
            return {
                language: {
                    {
                        (
                            f"{module.strip('$')}.{key}"
                            if module.startswith("$")
                            else f"{prefix}{module}.{key}"
                        ): value
                        for module, strings in pack.items()
                        for key, value in strings.items()
                        if key != "name"
                    }
                }
                for language, pack in content.items()
            }

        return {
            (
                f"{module.strip('$')}.{key}"
                if module.startswith("$")
                else f"{prefix}{module}.{key}"
            ): value
            for module, strings in content.items()
            for key, value in strings.items()
            if key != "name"
        }

    def getkey(self, key: str) -> typing.Any:
        return self._data.get(key, False)

    def gettext(self, text: str) -> typing.Any:
        return self.getkey(text) or text

    async def load_module_translations(self, pack_url: str) -> typing.Union[bool, dict]:
        try:
            data = yaml.load((await utils.run_sync(requests.get, pack_url)).text)
        except Exception:
            logger.exception("Unable to decode %s", pack_url)
            return False

        if any(len(key) != 2 for key in data):
            return data

        if lang := self.db.get(__name__, "lang", False):
            return next(
                (data[language] for language in lang.split() if language in data),
                data.get("en", {}),
            )

        return data.get("en", {})


class Translator(BaseTranslator):
    def __init__(self, client: CustomTelegramClient, db: Database):
        self._client = client
        self.db = db
        self._data = {}
        self.raw_data = {}

    async def init(self) -> bool:
        self._data = self._get_pack_content(PACKS / "en.yml")
        self.raw_data["en"] = self._data.copy()
        any_ = False
        if lang := self.db.get(__name__, "lang", False):
            for language in lang.split():
                if utils.check_url(language):
                    try:
                        data = self._get_pack_raw(
                            (await utils.run_sync(requests.get, language)).text,
                            language.split(".")[-1],
                        )
                    except Exception:
                        logger.exception("Unable to decode %s", language)
                        continue

                    self._data.update(data)
                    self.raw_data[language] = data
                    any_ = True
                    continue

                for possible_path in [
                    PACKS / f"{language}.json",
                    PACKS / f"{language}.yml",
                ]:
                    if possible_path.exists():
                        data = self._get_pack_content(possible_path)
                        self._data.update(data)
                        self.raw_data[language] = data
                        any_ = True

        for language in SUPPORTED_LANGUAGES:
            if language not in self.raw_data and (PACKS / f"{language}.yml").exists():
                self.raw_data[language] = self._get_pack_content(
                    PACKS / f"{language}.yml"
                )

        return any_


class ExternalTranslator(BaseTranslator):
    def __init__(self):
        self.data = {}
        for lang in SUPPORTED_LANGUAGES:
            self.data[lang] = self._get_pack_content(PACKS / f"{lang}.yml", prefix="")

    def get(self, key: str, lang: str) -> str:
        return self.data[lang].get(key, False) or key

    def getdict(self, key: str, **kwargs) -> dict:
        return {
            lang: fmt(self.data[lang].get(key, False) or key, kwargs)
            for lang in self.data
        }


class Strings:
    def __init__(self, mod: Module, translator: Translator):  # skipcq: PYL-W0621
        self._mod = mod
        self._translator = translator

        if not translator:
            logger.debug("Module %s got empty translator %s", mod, translator)

        self._base_strings = mod.strings  # Back 'em up, bc they will get replaced
        self.external_strings = {}

    def get(self, key: str, lang: typing.Optional[str] = None) -> str:
        try:
            return self._translator.raw_data[lang][f"{self._mod.__module__}.{key}"]
        except KeyError:
            return self[key]

    def __getitem__(self, key: str) -> str:
        return (
            self.external_strings.get(key, None)
            or (
                self._translator.getkey(f"{self._mod.__module__}.{key}")
                if self._translator is not None
                else False
            )
            or (
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
        )

    def __call__(
        self,
        key: str,
        _: typing.Optional[typing.Any] = None,  # Compatibility tweak for FTG\GeekTG
    ) -> str:
        return self.__getitem__(key)

    def __iter__(self):
        return self._base_strings.__iter__()


translator = ExternalTranslator()
