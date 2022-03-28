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

import time
import asyncio

from telethon.errors.rpcerrorlist import InputUserDeactivatedError

from telethon.utils import get_display_name

from aiogram.utils.exceptions import Unauthorized, TerminatedByOtherGetUpdates

from .gallery import Gallery
from .form import Form
from .bot_interaction import BotInteractions
from .events import Events
from .token_obtainment import TokenObtainment

import logging

logger = logging.getLogger(__name__)


class InlineManager(Gallery, Form, BotInteractions, Events, TokenObtainment):
    def __init__(self, client, db, allmodules) -> None:
        """Initialize InlineManager to create forms"""
        self._client = client
        self._db = db
        self._allmodules = allmodules

        self._token = db.get("hikka.inline", "bot_token", False)

        self._forms = {}
        self._galleries = {}
        self._custom_map = {}

        self.fsm = {}

        self._web_auth_tokens = []

        self._markup_ttl = 60 * 60 * 24

        self.init_complete = False

    def check_inline_security(self, func, user):
        """Checks if user with id `user` is allowed to run function `func`"""
        allow = (user in [self._me] + self._client.dispatcher.security._owner)  # fmt: skip

        if not hasattr(func, "__doc__") or not func.__doc__ or allow:
            return allow

        doc = func.__doc__

        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("@allow:"):
                allow_line = line.split(":")[1].strip()

                # First we check for possible group limits
                # like `sudo`, `support`, `all`. Then check
                # for the occurrence of user in overall string
                # This allows dev to use any delimiter he wants
                if (
                    "all" in allow_line
                    or "sudo" in allow_line
                    and user in self._client.dispatcher.security._sudo
                    or "support" in allow_line
                    and user in self._client.dispatcher.security._support
                    or str(user) in allow_line
                ):
                    allow = True

        # But don't hurry to return value, we need to check,
        # if there are any limits
        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("@restrict:"):
                restrict = line.split(":")[1].strip()

                if (
                    "all" in restrict
                    or "sudo" in restrict
                    and user in self._client.dispatcher.security._sudo
                    or "support" in restrict
                    and user in self._client.dispatcher.security._support
                    or str(user) in restrict
                ):
                    allow = True

        return allow

    async def _cleaner(self) -> None:
        """Cleans outdated _forms"""
        while True:
            for form_uid, form in self._forms.copy().items():
                if form["ttl"] < time.time():
                    del self._forms[form_uid]

            await asyncio.sleep(10)

    async def _register_manager(
        self,
        after_break: bool = False,
        ignore_token_checks: bool = False,
    ) -> None:
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
            self._bot_username = self.bot_username  # This is a temporary alias so the
            # developers can adapt their code
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

    async def _stop(self) -> None:
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
