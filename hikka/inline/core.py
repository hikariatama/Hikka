"""Inline buttons, galleries and other Telegram-Bot-API stuff"""

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import Unauthorized, TerminatedByOtherGetUpdates

import time
import asyncio

from telethon.errors.rpcerrorlist import InputUserDeactivatedError
from telethon.utils import get_display_name

from .gallery import Gallery
from .query_gallery import QueryGallery
from .form import Form
from .bot_interaction import BotInteractions
from .events import Events
from .token_obtainment import TokenObtainment
from .utils import Utils
from .list import List

import logging

logger = logging.getLogger(__name__)


class InlineManager(
    Utils,
    Events,
    TokenObtainment,
    Form,
    Gallery,
    QueryGallery,
    List,
    BotInteractions,
):
    def __init__(self, client, db, allmodules):
        """Initialize InlineManager to create forms"""
        self._client = client
        self._db = db
        self._allmodules = allmodules

        self._token = db.get("hikka.inline", "bot_token", False)

        self._forms = {}
        self._galleries = {}
        self._lists = {}
        self._custom_map = {}

        self.fsm = {}

        self._web_auth_tokens = []

        self._markup_ttl = 60 * 60 * 24

        self.init_complete = False

    async def _cleaner(self):
        """Cleans outdated _forms"""
        while True:
            for form_uid, form in self._forms.copy().items():
                if form.get("ttl", time.time() + self._markup_ttl) < time.time():
                    del self._forms[form_uid]

            for gallery_uid, gallery in self._galleries.copy().items():
                if gallery.get("ttl", time.time() + self._markup_ttl) < time.time():
                    del self._galleries[gallery_uid]

            for map_uid, config in self._custom_map.copy().items():
                if config.get("ttl", time.time() + self._markup_ttl) < time.time():
                    del self._custom_map[map_uid]

            await asyncio.sleep(5)

    async def _register_manager(
        self,
        after_break: bool = False,
        ignore_token_checks: bool = False,
    ):
        # Get info about user to use it in this class
        me = await self._client.get_me()
        self._me = me.id
        self._name = get_display_name(me)

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
        self.bot = Bot(token=self._token)
        self._bot = self.bot  # This is a temporary alias so the
        # developers can adapt their code
        self._dp = Dispatcher(self.bot)

        # Get bot username to call inline queries
        try:
            self.bot_username = (await self.bot.get_me()).username
            self.bot_id = (await self.bot.get_me()).id
        except Unauthorized:
            logger.critical("Token expired, revoking...")
            return await self._dp_revoke_token(False)

        # Start the bot in case it can send you messages
        try:
            m = await self._client.send_message(self.bot_username, "/start")
        except (InputUserDeactivatedError, ValueError):
            self._db.set("hikka.inline", "bot_token", None)
            self._token = False

            if not after_break:
                return await self._register_manager(True)

            self.init_complete = False
            return False
        except Exception:
            self.init_complete = False
            logger.critical("Initialization of inline manager failed!")
            logger.exception("due to")
            return False

        await self._client.delete_messages(self.bot_username, m)

        # Register required event handlers inside aiogram
        self._dp.register_inline_handler(
            self._inline_handler,
            lambda inline_query: True,
        )

        self._dp.register_callback_query_handler(
            self._callback_query_handler,
            lambda query: True,
        )

        self._dp.register_chosen_inline_handler(
            self._chosen_inline_handler,
            lambda chosen_inline_query: True,
        )

        self._dp.register_message_handler(
            self._message_handler,
            lambda *args: True,
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
