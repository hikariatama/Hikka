#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: inline

import asyncio
import contextlib
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
        "update_required": (
            "🌘 <b>Hikka Update available!</b>\n\nNew Hikka version released.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 And {} more...</b></i>",
    }

    strings_ru = {
        "update_required": (
            "🌘 <b>Доступно обновление Hikka!</b>\n\nОпубликована новая версия Hikka.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 И еще {}...</b></i>",
    }

    _notified = None

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "disable_notifications",
                doc=lambda: "Disable update notifications",
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
            f"<b>{commit.split()[0]}</b>:"
            f" <i>{utils.escape_html(' '.join(commit.split()[1:]))}</i>"
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

    async def client_ready(self):
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

        self.poller.start()

    @loader.loop(interval=60)
    async def poller(self):
        if self.config["disable_notifications"] or not self.get_changelog():
            return

        self._pending = self.get_latest()

        if (
            self.get("ignore_permanent", False)
            and self.get("ignore_permanent") == self._pending
        ):
            await asyncio.sleep(60)
            return

        if self._pending not in [self.get_commit(), self._notified]:
            m = await self.inline.bot.send_message(
                self.tg_id,
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

    async def _delete_all_upd_messages(self):
        for client in self.allclients:
            with contextlib.suppress(Exception):
                await client.loader.inline.bot.delete_message(
                    client.tg_id,
                    client.loader._db.get("UpdateNotifierMod", "upd_msg"),
                )

    @loader.callback_handler()
    async def update(self, call: InlineCall):
        """Process update buttons clicks"""
        if call.data not in {"hikka_update", "hikka_upd_ignore"}:
            return

        if call.data == "hikka_upd_ignore":
            self.set("ignore_permanent", self._pending)
            await call.answer("Notifications about this update have been suppressed")
            return

        await self._delete_all_upd_messages()

        with contextlib.suppress(Exception):
            await call.delete()

        await self.allmodules.commands["update"](
            await self._client.send_message(
                self.inline.bot_username,
                f"<code>{self.get_prefix()}update --force</code>",
            )
        )
