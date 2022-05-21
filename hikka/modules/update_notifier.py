# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: inline

import asyncio
import logging
from typing import Union

import git

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class UpdateNotifierMod(loader.Module):
    """Tracks latest Hikka releases, and notifies you, if update is required"""

    strings = {
        "name": "UpdateNotifier",
        "update_required": "🌘 <b>Hikka Update available!</b>\n\nNew Hikka version released.\n🔮 <b>Hikka <s>{}</s> -> {}</b>\n\n{}",
        "more": "\n<i><b>🎥 And {} more...</b></i>",
    }

    strings_ru = {
        "update_required": "🌘 <b>Доступно обновление Hikka!</b>\n\nОпубликована новая версия Hikka.\n🔮 <b>Hikka <s>{}</s> -> {}</b>\n\n{}",
        "more": "\n<i><b>🎥 И еще {}...</b></i>",
    }

    _notified = None

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "disable_notifications",
                False,
                lambda: "Disable update notifications",
                validator=loader.validators.Boolean(),
            )
        )

    def get_commit(self) -> Union[str, bool]:
        try:
            return git.Repo().heads[0].commit.hexsha
        except Exception:
            return False

    def get_changelog(self) -> str:
        try:
            repo = git.Repo()

            for remote in repo.remotes:
                remote.fetch()

            if not (diff := repo.git.log(["HEAD..origin/master", "--oneline"])):
                return False
        except Exception:
            return False

        res = "\n".join(
            f"<b>{commit.split()[0]}</b>: <i>{utils.escape_html(' '.join(commit.split()[1:]))}</i>"
            for commit in diff.splitlines()[:10]
        )

        if diff.count("\n") >= 10:
            res += self.strings("more").format(len(diff.splitlines()) - 10)

        return res

    def get_latest(self) -> str:
        try:
            return list(git.Repo().iter_commits("origin/master", max_count=1))[0].hexsha
        except Exception:
            return ""

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

        if self.config["disable_notifications"]:
            raise loader.SelfUnload

        try:
            git.Repo()
        except Exception as e:
            raise loader.LoadError("Can't load due to repo init error") from e

        self._markup = self.inline.generate_markup(
            [
                {"text": "🔄 Update", "data": "hikka_update"},
                {"text": "🚫 Ignore", "data": "hikka_upd_ignore"},
            ]
        )

        self._task = asyncio.ensure_future(self.poller())

    async def on_unload(self):
        self._task.cancel()

    async def poller(self):
        while True:
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
                    m = await self.inline.bot.send_message(
                        self._tg_id,
                        self.strings("update_required").format(
                            self.get_commit()[:6],
                            f'<a href="https://github.com/hikariatama/Hikka/compare/{self.get_commit()[:12]}...{self.get_latest()[:12]}">{self.get_latest()[:6]}</a>',
                            self.get_changelog(),
                        ),
                        disable_web_page_preview=True,
                        reply_markup=self._markup,
                    )

                    self._notified = self._pending
                    self.set("ignore_permanent", False)

                    await self._delete_all_upd_messages()

                    self.set("upd_msg", m.message_id)
            except Exception:
                # We need to catch error manually because of
                # `ensure_future`
                logger.exception("Error occurred while fetching update")

            await asyncio.sleep(60)

    async def _delete_all_upd_messages(self):
        for client in self.allclients:
            try:
                await client.loader.inline.bot.delete_message(
                    client._tg_id,
                    client.loader._db.get("UpdateNotifier", "upd_msg"),
                )
            except Exception:
                pass

    async def update_callback_handler(self, call: InlineCall):
        """Process update buttons clicks"""
        if call.data not in {"hikka_update", "hikka_upd_ignore"}:
            return

        if call.data == "hikka_upd_ignore":
            self.set("ignore_permanent", self._pending)
            await call.answer("Notifications about this update have been suppressed")
            return

        m = await self._client.send_message(
            self.inline.bot_username,
            f"<code>{self.get_prefix()}update --force</code>",
        )

        await self._delete_all_upd_messages()

        try:
            await self.inline.bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass

        await self.allmodules.commands["update"](m)
