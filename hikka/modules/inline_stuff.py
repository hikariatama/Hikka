# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the CC BY-NC-ND 4.0
# 🌐 https://creativecommons.org/licenses/by-nc-nd/4.0

# scope: inline
# scope: hikka_only
# meta developer: @hikariatama

from .. import loader, utils
from telethon.tl.types import Message
from aiogram.types import CallbackQuery
import logging
import re

logger = logging.getLogger(__name__)


@loader.tds
class InlineStuffMod(loader.Module):
    """Provides support for inline stuff"""

    strings = {"name": "InlineStuff"}

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._bot_id = (await self.inline.bot.get_me()).id

    async def inline__close(self, call: CallbackQuery) -> None:
        await call.delete()

    async def watcher(self, message: Message) -> None:
        if (
            not getattr(message, "out", False)
            or not getattr(message, "via_bot_id", False)
            or message.via_bot_id != self._bot_id
            or "Loading Hikka gallery..." not in getattr(message, "raw_text", "")
        ):
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text).group(1)

        await self.inline.gallery(
            message=utils.get_chat_id(message),
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
        )

        await message.delete()
