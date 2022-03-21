"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

# meta pic: https://img.icons8.com/external-flatart-icons-flat-flatarticons/64/000000/external-info-hotel-services-flatart-icons-flat-flatarticons.png
# scope: inline

from .. import loader, main
import logging
import aiogram
import os
import git

from telethon.utils import get_display_name
from ..inline import GeekInlineQuery, rand

logger = logging.getLogger(__name__)


@loader.tds
class GeekInfoMod(loader.Module):
    """Show userbot info (geek3.1.0alpha+)"""

    strings = {"name": "GeekInfo"}

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
                "🤵‍♀️ Support chat", url="https://t.me/chat_ftg"
            )
        )

    async def info_inline_handler(self, query: GeekInlineQuery) -> None:
        """
        Send userbot info
        @allow: all
        """

        try:
            repo = git.Repo()
            ver = repo.heads[0].commit.hexsha

            diff = repo.git.log(["HEAD..origin/alpha", "--oneline"])
            upd = (
                "⚠️ Update required </b><code>.update</code><b>"
                if diff
                else "✅ Up-to-date"
            )
        except Exception:
            ver = "unknown"
            upd = ""

        termux = bool(os.popen('echo $PREFIX | grep -o "com.termux"').read())  # skipcq: BAN-B605, BAN-B607
        heroku = os.environ.get("DYNO", False)

        platform = (
            "🕶 Termux"
            if termux
            else (
                "⛎ Heroku"
                if heroku
                else (
                    f"✌️ lavHost {os.environ['LAVHOST']}"
                    if "LAVHOST" in os.environ
                    else "📻 VDS"
                )
            )
        )

        await query.answer(
            [
                aiogram.types.inline_query_result.InlineQueryResultArticle(
                    id=rand(20),
                    title="Send userbot info",
                    description="ℹ This will not compromise any sensitive data",
                    input_message_content=aiogram.types.input_message_content.InputTextMessageContent(
                        f"""
<b>🕶 GeekTG Userbot</b>
<b>🤴 Owner: <a href="tg://user?id={self._me.id}">{get_display_name(self._me)}</a></b>\n
<b>🔮 Version: </b><i>{".".join(list(map(str, list(main.__version__))))}</i>
<b>🧱 Build: </b><a href="https://github.com/GeekTG/Friendly-Telegram/commit/{ver}">{ver[:8] or "Unknown"}</a>
<b>{upd}</b>

<b>{platform}</b>
""",
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url="https://github.com/GeekTG/Friendly-Telegram/raw/master/friendly-telegram/bot_avatar.png",
                    thumb_width=128,
                    thumb_height=128,
                    reply_markup=self.markup,
                )
            ],
            cache_time=0,
        )
