# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @hikariatama

import logging

from telethon.tl.functions.channels import EditAdminRequest, InviteToChannelRequest
from telethon.tl.types import ChatAdminRights

from .. import loader, utils


@loader.tds
class HikkaLoggerMod(loader.Module):
    """Transfer your Hikka logs to classic bot"""

    strings = {"name": "AmoreLogger"}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

        chat, is_new = await utils.asset_channel(
            self._client,
            "amore-logs",
            "🌌 Your Amore logs will appear in this chat",
            silent=True,
        )

        self._logchat = int(f"-100{chat.id}")

        logger = logging.getLogger(__name__)

        if not is_new or all(
            participant.id != self.inline.bot_id
            for participant in (await self._client.get_participants(chat))
        ):
            logging.getLogger().handlers[0].install_tg_log(self)
            logger.debug(f"Bot logging installed for {self._logchat}")
            return

        logger.debug("New logging chat created, init setup...")

        try:
            await self._client(InviteToChannelRequest(chat, [self.inline.bot_username]))
        except Exception:
            logger.warning("Unable to invite logger to chat")

        try:
            await self._client(
                EditAdminRequest(
                    channel=chat,
                    user_id=self.inline.bot_username,
                    admin_rights=ChatAdminRights(ban_users=True),
                    rank="Logger",
                )
            )
        except Exception:
            pass

        try:
            await utils.set_avatar(
                self._client,
                chat,
                "https://i.imgur.com/MWoMKp0.jpeg",
            )
        except Exception:
            pass

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug(f"Bot logging installed for {self._logchat}")
