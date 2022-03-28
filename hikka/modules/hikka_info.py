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

from .. import loader, main, utils
import logging
import git

from telethon.utils import get_display_name
from ..inline.types import InlineQuery
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logger = logging.getLogger(__name__)


@loader.tds
class HikkaInfoMod(loader.Module):
    """Show userbot info"""

    strings = {"name": "HikkaInfo"}

    def get(self, *args) -> dict:
        return self._db.get(self.strings["name"], *args)

    def set(self, *args) -> None:
        return self._db.set(self.strings["name"], *args)

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._me = await client.get_me()
        self.markup = InlineKeyboardMarkup()
        self.markup.row(
            InlineKeyboardButton("🤵‍♀️ Support chat", url="https://t.me/hikka_talks")
        )

    async def info_inline_handler(self, query: InlineQuery) -> None:
        """
        Send userbot info
        @allow: all
        """

        try:
            repo = git.Repo()
            ver = repo.heads[0].commit.hexsha
        except Exception:
            ver = "unknown"

        try:
            diff = repo.git.log(["HEAD..origin/alpha", "--oneline"])
            upd = (
                "⚠️ Update required </b><code>.update</code><b>"
                if diff
                else "✅ Up-to-date"
            )
        except Exception:
            upd = ""

        await query.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="Send userbot info",
                    description="ℹ This will not compromise any sensitive data",
                    input_message_content=InputTextMessageContent(
                        (
                            "<b>👩‍🎤 Hikka Userbot</b>\n"
                            f'<b>🤴 Owner: <a href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></b>\n\n'
                            f"<b>🔮 Version: </b><i>{'.'.join(list(map(str, list(main.__version__))))}</i>\n"
                            f"<b>🧱 Build: </b><a href=\"https://github.com/hikariatama/Hikka/commit/{ver}\">{ver[:8] or 'Unknown'}</a>\n"
                            f"<b>{upd}</b>\n"
                            f"<b>{utils.get_named_platform()}</b>\n"
                        ),
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url="https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png",
                    thumb_width=128,
                    thumb_height=128,
                    reply_markup=self.markup,
                )
            ],
            cache_time=0,
        )
