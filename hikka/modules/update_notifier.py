# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/fluency/48/000000/available-updates.png
# scope: inline
# scope: hikka_only

from .. import loader, utils, main  # noqa: F401
from telethon.tl.types import Message  # noqa: F401

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import asyncio
import logging
import git
from typing import Union
import time

from ..types import LoadError

logger = logging.getLogger(__name__)


@loader.tds
class AutoUpdaterMod(loader.Module):
    """Tracks latest Hikka releases, and notifies you, if update is required"""

    strings = {
        "name": "AutoUpdater",
        "update_required": "🌒 <b>Hikka Update available!</b>\n\nNew Hikka version released.\n🔮 <b>Hikka <s>{}</s> -> {}</b>\n\n{}",
    }

    _notified = None
    _pending = None
    _db = None
    _client = None
    _me = None
    _markup = None
    _task = None

    def get_commit(self) -> Union[str, bool]:
        try:
            return git.Repo().heads[0].commit.hexsha
        except Exception:
            return False

    def get_changelog(self) -> str:
        try:
            repo = git.Repo()
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            if not diff:
                return False
        except Exception:
            return False

        res = "\n".join(
            f"<b>{commit.split()[0]}</b>: <i>{utils.escape_html(' '.join(commit.split()[1:]))}</i>"
            for commit in diff.splitlines()[:10]
        )

        if diff.count("\n") >= 10:
            res += f"\n<i><b>🎥 And {len(diff.splitlines()) - 10} more...</b></i>"

        return res

    def get_latest(self) -> str:
        try:
            return list(git.Repo().iter_commits("origin/master", max_count=1))[0].hexsha
        except Exception:
            return ""

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._me = (await client.get_me()).id

        try:
            git.Repo()
        except Exception as e:
            raise LoadError("Can't load due to repo init error") from e

        self._markup = InlineKeyboardMarkup()
        self._markup.add(
            InlineKeyboardButton(
                "🔄 Update",
                callback_data="hikka_update",
            )
        )
        self._markup.add(
            InlineKeyboardButton(
                "🚫 Ignore",
                callback_data="hikka_upd_ignore",
            )
        )

        self._task = asyncio.ensure_future(self.poller())

    async def on_unload(self) -> None:
        self._task.cancel()

    async def poller(self) -> None:
        while True:
            if self.get("ignore_until", 0) > time.time():
                await asyncio.sleep(self.get("ignore_until") - time.time())
                continue

            if not self.get_changelog():
                await asyncio.sleep(60)
                continue

            try:
                self._pending = self.get_latest()

                if (
                    self.get("ignore_permanent", False)
                    and self.get("ignore_permanent") == self._pending
                ):
                    await asyncio.sleep(120)
                    continue

                if (
                    self._pending != self.get_commit()
                    and self._pending != self._notified
                ):
                    await self.inline.bot.send_message(
                        self._me,
                        self.strings("update_required").format(
                            self.get_commit()[:6],
                            self.get_latest()[:6],
                            self.get_changelog(),
                        ),
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=self._markup,
                    )

                    self.set("ignore_permanent", False)
                    self.set("ignore_until", 0)

                    self._notified = self._pending
            except Exception:
                # We need to catch error manually because of
                # `ensure_future`
                logger.exception("Error occurred while fetching update")

            await asyncio.sleep(60)

    async def update_callback_handler(self, call: CallbackQuery) -> None:
        """
        Process update buttons clicks
        @allow: sudo
        """
        if call.data not in {"hikka_update", "hikka_upd_ignore"}:
            return

        if call.data == "hikka_upd_ignore":
            self.set("ignore_permanent", self._pending)
            await call.answer("Notifications about this update have been suppressed")
            return

        m = await self._client.send_message(
            self.inline.bot_username,
            "<code>.update</code>",
        )

        await self.inline.bot.delete_message(
            call.message.chat.id,
            call.message.message_id,
        )

        await self.allmodules.commands["update"](m)
