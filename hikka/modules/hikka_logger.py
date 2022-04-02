"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    © Copyright 2022 t.me/hikariatama
    Licensed under CC BY-NC-ND 4.0

    🌐 https://creativecommons.org/licenses/by-nc-nd/4.0
"""

# meta developer: @hikariatama

from .. import loader, utils
import logging

from telethon.tl.functions.channels import (
    InviteToChannelRequest,
    EditAdminRequest,
    EditPhotoRequest,
)

import requests
from telethon.tl.types import ChatAdminRights


@loader.tds
class HikkaLoggerMod(loader.Module):
    """Transfer your Hikka logs to classic bot"""

    strings = {"name": "HikkaLogger"}

    async def client_ready(self, client, db) -> None:
        self._client = client
        self._db = db
        self._me = (await client.get_me()).id

        chat, is_new = await utils.asset_channel(
            self._client,
            "hikka-logs",
            "👩‍🎤 Your Hikka logs will appear in this chat",
            silent=True,
        )

        self._logchat = int(f"-100{chat.id}")

        logger = logging.getLogger(__name__)

        if not is_new:
            logging.getLogger().handlers[0].install_tg_log(self)
            logger.info(f"Bot logging installed for {self._logchat}")
            return

        logger.info("New logging chat created, init setup...")

        try:
            await self._client(InviteToChannelRequest(chat, [self.inline.bot_username]))
        except Exception:
            logger.warning("Unable to invite logger to chat. Maybe he's already there?")

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
            f = (
                await utils.run_sync(
                    requests.get,
                    "https://i.imgur.com/MWoMKp0.jpeg",
                )
            ).content

            await self._client(
                EditPhotoRequest(
                    channel=chat,
                    photo=await self._client.upload_file(f, file_name="photo.jpg"),
                )
            )
        except Exception:
            pass

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.info(f"Bot logging installed for {self._logchat}")
