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

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest

logger = logging.getLogger(__name__)


@loader.tds
class InlineStuffMod(loader.Module):
    """Provides support for inline stuff"""

    strings = {
        "name": "InlineStuff",
        "bot_username_invalid": "🚫 <b>Specified bot username is invalid. It must end with </b><code>bot</code><b> and contain at least 4 symbols</b>",
        "bot_username_occupied": "🚫 <b>This username is already occupied</b>",
        "bot_updated": "😌 <b>Config successfully saved. Restart userbot to apply changes</b>",
    }

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

        await message.delete()

        m = await message.respond("🌘 <b>Opening gallery... wait</b>")

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get("disable_security", False),
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    async def ch_hikka_botcmd(self, message: Message) -> None:
        """<username> - Change your Hikka inline bot username"""
        args = utils.get_args_raw(message).strip("@")
        if not args or not args.lower().endswith("bot") or len(args) <= 4:
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("hikka.inline", "custom_bot", args)
        self._db.set("hikka.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))
