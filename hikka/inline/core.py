"""Inline buttons, galleries and other Telegram-Bot-API stuff"""

# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging
import time

from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates, Unauthorized
from telethon.errors.rpcerrorlist import InputUserDeactivatedError, YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest
from telethon.utils import get_display_name

from ..database import Database
from ..tl_cache import CustomTelegramClient
from .bot_pm import BotPM
from .events import Events
from .form import Form
from .gallery import Gallery
from .list import List
from .query_gallery import QueryGallery
from .token_obtainment import TokenObtainment
from .utils import Utils

logger = logging.getLogger(__name__)


class InlineManager(
    Utils,
    Events,
    TokenObtainment,
    Form,
    Gallery,
    QueryGallery,
    List,
    BotPM,
):
    def __init__(
        self,
        client: CustomTelegramClient,
        db: Database,
        allmodules: "Modules",  # type: ignore
    ):
        """Initialize InlineManager to create forms"""
        self._client = client
        self._db = db
        self._allmodules = allmodules

        self._units = {}
        self._custom_map = {}
        self.fsm = {}
        self._web_auth_tokens = []

        self._markup_ttl = 60 * 60 * 24
        self.init_complete = False

        self._token = db.get("hikka.inline", "bot_token", False)

    async def _cleaner(self):
        """Cleans outdated inline units"""
        while True:
            for unit_id, unit in self._units.copy().items():
                if (unit.get("ttl") or (time.time() + self._markup_ttl)) < time.time():
                    del self._units[unit_id]

            await asyncio.sleep(5)

    async def register_manager(
        self,
        after_break: bool = False,
        ignore_token_checks: bool = False,
    ):
        # Get info about user to use it in this class
        self._me = self._client.tg_id
        self._name = get_display_name(self._client.hikka_me)

        if not ignore_token_checks:
            # Assert that token is set to valid, and if not,
            # set `init_complete` to `False` and return
            is_token_asserted = await self._assert_token()
            if not is_token_asserted:
                self.init_complete = False
                return

        # We successfully asserted token, so set `init_complete` to `True`
        self.init_complete = True

        # Create bot instance and dispatcher
        self.bot = Bot(token=self._token, parse_mode=ParseMode.HTML)
        Bot.set_current(self.bot)
        self._bot = self.bot  # This is a temporary alias so the
        # developers can adapt their code
        self._dp = Dispatcher(self.bot)

        # Get bot username to call inline queries
        try:
            bot_me = await self.bot.get_me()
            self.bot_username = bot_me.username
            self.bot_id = bot_me.id
        except Unauthorized:
            logger.critical("Token expired, revoking...")
            return await self._dp_revoke_token(False)

        # Start the bot in case it can send you messages
        try:
            m = await self._client.send_message(self.bot_username, "/start hikka init")
        except (InputUserDeactivatedError, ValueError):
            self._db.set("hikka.inline", "bot_token", None)
            self._token = False

            if not after_break:
                return await self.register_manager(True)

            self.init_complete = False
            return False
        except YouBlockedUserError:
            await self._client(UnblockRequest(id=self.bot_username))
            try:
                m = await self._client.send_message(
                    self.bot_username, "/start hikka init"
                )
            except Exception:
                logger.critical("Can't unblock users bot", exc_info=True)
                return False
        except Exception:
            self.init_complete = False
            logger.critical("Initialization of inline manager failed!", exc_info=True)
            return False

        await self._client.delete_messages(self.bot_username, m)

        # Register required event handlers inside aiogram
        self._dp.register_inline_handler(
            self._inline_handler,
            lambda _: True,
        )

        self._dp.register_callback_query_handler(
            self._callback_query_handler,
            lambda _: True,
        )

        self._dp.register_chosen_inline_handler(
            self._chosen_inline_handler,
            lambda _: True,
        )

        self._dp.register_message_handler(
            self._message_handler,
            lambda *_: True,
            content_types=["any"],
        )

        old = self.bot.get_updates
        revoke = self._dp_revoke_token

        async def new(*args, **kwargs):
            nonlocal revoke, old
            try:
                return await old(*args, **kwargs)
            except TerminatedByOtherGetUpdates:
                await revoke()
            except Unauthorized:
                logger.critical("Got Unauthorized")
                await self._stop()

        self.bot.get_updates = new

        # Start polling as the separate task, just in case we will need
        # to force stop this coro. It should be cancelled only by `stop`
        # because it stops the bot from getting updates
        self._task = asyncio.ensure_future(self._dp.start_polling())
        self._cleaner_task = asyncio.ensure_future(self._cleaner())

    async def _stop(self):
        self._task.cancel()
        self._dp.stop_polling()
        self._cleaner_task.cancel()

    def pop_web_auth_token(self, token) -> bool:
        """Check if web confirmation button was pressed"""
        if token not in self._web_auth_tokens:
            return False

        self._web_auth_tokens.remove(token)
        return True


if __name__ == "__main__":
    raise Exception("This file must be called as a module")
