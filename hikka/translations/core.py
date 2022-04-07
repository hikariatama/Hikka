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

import json
import logging

import telethon
from babel import negotiate_locale
from telethon.tl.types import MessageEntityHashtag

logger = logging.getLogger(__name__)

MAGIC = "#hikka_translate_pack"


class Translator:
    def __init__(self, packs, languages, data_root):
        self._packs = packs
        self._languages = languages
        self._data_root = data_root

    async def init(self, client):
        self._data = {}
        for pack in self._packs:
            try:
                [message] = await client.get_messages(pack, 1)
            except (ValueError, telethon.errors.rpcerrorlist.ChannelPrivateError):
                # We can't access the channel
                logger.warning(
                    f"No translation pack found for {pack}",
                    exc_info=True,
                )
                continue
            if not message.document or not message.entities:
                logger.info(f"Last message in translation pack {pack} has no document/entities")  # fmt: skip
                continue
            found = False
            for ent in filter(
                lambda x: isinstance(x, MessageEntityHashtag), message.entities
            ):
                if (
                    message.message[ent.offset : ent.offset + ent.length] == MAGIC
                    and message.file
                ):
                    logger.debug("Got translation message")
                    found = True
                    break
            if not found:
                logger.info("Didn't find translation hashtags")
                continue
            try:
                ndata = json.loads(
                    (await message.download_media(bytes)).decode("utf-8")
                )
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                logger.exception(f"Unable to decode {pack}")
                continue
            try:
                self._data.setdefault(ndata["language"], {}).update(ndata["data"])
            except KeyError:
                logger.exception("Translation pack follows wrong format")

    def set_preferred_languages(self, languages):
        self._languages = languages

    def getkey(self, key, lang_code=None):
        locales = []
        for locale, strings in self._data.items():
            if key in strings:
                locales += [locale]
        target_locales = [lang_code] if lang_code else self._languages
        locale = negotiate_locale(target_locales, locales)
        return self._data.get(locale, {}).get(key, False)

    def gettext(self, english_text):
        return self.getkey(english_text) or english_text
