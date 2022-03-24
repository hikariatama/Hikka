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

from .. import loader, main
import logging
import aiogram
import os
import git

from telethon.utils import get_display_name
from ..inline import InlineQuery, rand

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
        self.markup = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
        self.markup.row(
            aiogram.types.inline_keyboard.InlineKeyboardButton(
                "🤵‍♀️ Support chat", url="https://t.me/hikka_talks"
            )
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

        is_termux = bool(os.popen('echo $PREFIX | grep -o "com.termux"').read())  # skipcq: BAN-B605, BAN-B607
        is_okteto = "OKTETO" in os.environ
        is_lavhost = "LAVHOST" in os.environ

        if is_termux:
            platform = "🕶 Termux"
        elif is_okteto:
            platform = "☁️ Okteto"
        elif is_lavhost:
            platform = f"✌️ lavHost {os.environ['LAVHOST']}"
        else:
            platform = "📻 VDS"

        await query.answer(
            [
                aiogram.types.inline_query_result.InlineQueryResultArticle(
                    id=rand(20),
                    title="Send userbot info",
                    description="ℹ This will not compromise any sensitive data",
                    input_message_content=aiogram.types.input_message_content.InputTextMessageContent(
                        f"""
<b>👩‍🎤 Hikka Userbot</b>
<b>🤴 Owner: <a href="tg://user?id={self._me.id}">{get_display_name(self._me)}</a></b>\n
<b>🔮 Version: </b><i>{".".join(list(map(str, list(main.__version__))))}</i>
<b>🧱 Build: </b><a href="https://github.com/hikariatama/Hikka/commit/{ver}">{ver[:8] or "Unknown"}</a>
<b>{upd}</b>

<b>{platform}</b>
""",
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
