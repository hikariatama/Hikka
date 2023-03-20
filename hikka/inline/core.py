"""Inline buttons, galleries and other Telegram-Bot-API stuff"""

# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging
import time
import typing

from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates, Unauthorized
from hikkatl.errors.rpcerrorlist import InputUserDeactivatedError, YouBlockedUserError
from hikkatl.tl.functions.contacts import UnblockRequest
from hikkatl.utils import get_display_name

from ..database import Database
from ..tl_cache import CustomTelegramClient
from ..translations import Translator
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
    """
    Inline buttons, galleries and other Telegram-Bot-API stuff
    :param client: Telegram client
    :param db: Database instance
    :param allmodules: All modules
    :type client: hikka.tl_cache.CustomTelegramClient
    :type db: hikka.database.Database
    :type allmodules: hikka.loader.Modules
    """

    def __init__(
        self,
        client: CustomTelegramClient,
        db: Database,
        allmodules: "Modules",  # type: ignore  # noqa: F821
    ):
        """Initialize InlineManager to create forms"""
        self._client = client
        self._db = db
        self._allmodules = allmodules
        self.translator: Translator = allmodules.translator

        self._units: typing.Dict[str, dict] = {}
        self._custom_map: typing.Dict[str, callable] = {}
        self.fsm: typing.Dict[str, str] = {}
        self._web_auth_tokens: typing.List[str] = []

        self._markup_ttl = 60 * 60 * 24
        self.init_complete = False

        self._token = db.get("hikka.inline", "bot_token", False)

        self._me: int = None
        self._name: str = None
        self._dp: Dispatcher = None
        self._task: asyncio.Future = None
        self._cleaner_task: asyncio.Future = None
        self.bot: Bot = None
        self.bot_id: int = None
        self.bot_username: str = None

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
        """
        Register manager
        :param after_break: Loop marker
        :param ignore_token_checks: If `True`, will not check for token
        :type after_break: bool
        :type ignore_token_checks: bool
        :return: None
        :rtype: None
        """
        self._me = self._client.tg_id
        self._name = get_display_name(self._client.hikka_me)

        if not ignore_token_checks:
            is_token_asserted = await self._assert_token()
            if not is_token_asserted:
                self.init_complete = False
                return

        self.init_complete = True

        self.bot = Bot(token=self._token, parse_mode=ParseMode.HTML)
        Bot.set_current(self.bot)
        self._bot = self.bot
        self._dp = Dispatcher(self.bot)

        try:
            bot_me = await self.bot.get_me()
            self.bot_username = bot_me.username
            self.bot_id = bot_me.id
        except Unauthorized:
            logger.critical("Token expired, revoking...")
            return await self._dp_revoke_token(False)

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

        self._task = asyncio.ensure_future(self._dp.start_polling())
        self._cleaner_task = asyncio.ensure_future(self._cleaner())

    async def _stop(self):
        """Stop the bot"""
        self._task.cancel()
        self._dp.stop_polling()
        self._cleaner_task.cancel()

    def pop_web_auth_token(self, token: str) -> bool:
        """
        Check if web confirmation button was pressed
        :param token: Token to check
        :type token: str
        :return: `True` if token was found, `False` otherwise
        :rtype: bool
        """
        if token not in self._web_auth_tokens:
            return False

        self._web_auth_tokens.remove(token)
        return True
