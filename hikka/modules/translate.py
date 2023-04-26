# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from hikkatl.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class Translator(loader.Module):
    """Translates text (obviously)"""

    strings = {"name": "Translator"}

    @loader.command()
    async def tr(self, message: Message):
        if not (args := utils.get_args_raw(message)):
            text = None
            lang = self.strings("language")
        else:
            lang = args.split(maxsplit=1)[0]
            if len(lang) != 2:
                text = args
                lang = self.strings("language")
            else:
                try:
                    text = args.split(maxsplit=1)[1]
                except IndexError:
                    text = None

        if not text:
            if not (reply := await message.get_reply_message()):
                await utils.answer(message, self.strings("no_args"))
                return

            text = reply.raw_text
            entities = reply.entities
        else:
            entities = []

        try:
            await utils.answer(
                message,
                await self._client.translate(
                    message.peer_id,
                    message,
                    lang,
                    raw_text=text,
                    entities=entities,
                ),
            )
        except Exception:
            logger.exception("Unable to translate text")
            await utils.answer(message, self.strings("error"))
