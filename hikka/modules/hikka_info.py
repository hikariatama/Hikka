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
from telethon.tl.types import Message

logger = logging.getLogger(__name__)


@loader.tds
class HikkaInfoMod(loader.Module):
    """Show userbot info"""

    strings = {"name": "HikkaInfo"}

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._me = await client.get_me()
        self.markup = {"text": "🤵‍♀️ Support chat", "url": "https://t.me/hikka_talks"}

    def _render_info(self) -> str:
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

        return (
            "<b>👩‍🎤 Hikka Userbot</b>\n"
            f'<b>🤴 Owner: <a href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></b>\n\n'
            f"<b>🔮 Version: </b><i>{'.'.join(list(map(str, list(main.__version__))))}</i>\n"
            f"<b>🧱 Build: </b><a href=\"https://github.com/hikariatama/Hikka/commit/{ver}\">{ver[:8] or 'Unknown'}</a>\n"
            f"<b>📼 Command prefix: </b>«<code>{utils.escape_html((self._db.get(main.__name__, 'command_prefix', False) or '.')[0])}</code>»\n"
            f"<b>{upd}</b>\n"
            f"<b>{utils.get_named_platform()}</b>\n"
        )

    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """
        Send userbot info
        @allow: all
        """

        return {
            "title": "Send userbot info",
            "description": "ℹ This will not compromise any sensitive data",
            "message": self._render_info(),
            "thumb": "https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png",
            "reply_markup": self.markup,
        }

    async def infocmd(self, message: Message) -> None:
        """Send userbot info"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup=self.markup,
        )
