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

    strings = {
        "name": "HikkaInfo",
        "owner": "Owner",
        "version": "Version",
        "build": "Build",
        "prefix": "Command prefix",
        "send_info": "Send userbot info",
        "description": "ℹ This will not compromise any sensitive info",
        "up-to-date": "✅ Up-to-date",
        "update_required": "⚠️ Update required </b><code>.update</code><b>",
        "_cfg_doc_custom_message": "Custom message for info. May contain {me}, {version}, {build}, {prefix}, {platform} keywords",
        "_cfg_doc_custom_button": "Custom button for info",
    }

    strings_ru = {
        "owner": "Владелец",
        "version": "Версия",
        "build": "Сборка",
        "prefix": "Префикс команд",
        "send_info": "Отправить информацию о юзерботе",
        "description": "ℹ Это не раскроет никакой личной информации",
        "_ihandle_doc_info": "Отправить информацию о юзерботе",
        "up-to-date": "✅ Актуальная версия",
        "update_required": "⚠️ Требуется обновление </b><code>.update</code><b>",
        "_cfg_doc_custom_message": "Кастомный текст сообщения в info. Может содержать ключевые слова {me}, {version}, {build}, {prefix}, {platform}",
        "_cfg_doc_custom_button": "Кастомная кнопка в сообщении в info",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "custom_message",
            "no",
            lambda: self.strings("_cfg_doc_custom_message"),
            "custom_button",
            "🌘 Support chat|https://t.me/hikka_talks",
            lambda: self.strings("_cfg_doc_custom_button"),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    def _render_info(self) -> str:
        ver = utils.get_git_hash() or "Unknown"

        try:
            repo = git.Repo()
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = f'<b><a href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></b>'
        version = f'<i>{".".join(list(map(str, list(main.__version__))))}</i>'
        build = f'<a href="https://github.com/hikariatama/Hikka/commit/{ver}">{ver[:8]}</a>'  # fmt: skip
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"
        platform = utils.get_named_platform()

        return (
            self.config["custom_message"].format(
                me=me,
                version=version,
                build=build,
                prefix=prefix,
                platform=platform,
            )
            if self.config["custom_message"] != "no"
            else (
                "<b>🌘 Hikka Userbot</b>\n"
                f'<b>🤴 {self.strings("owner")}: </b>{me}\n\n'
                f"<b>🔮 {self.strings('version')}: </b>{version}\n"
                f"<b>🧱 {self.strings('build')}: </b>{build}\n\n"
                f"<b>📼 {self.strings('prefix')}: </b>{prefix}\n"
                f"<b>{upd}</b>\n"
                f"<b>{platform}</b>\n"
            )
        )

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Send userbot info"""

        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            "message": self._render_info(),
            "thumb": "https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png",
            "reply_markup": {
                "text": self.config["custom_button"].split("|")[0],
                "url": self.config["custom_button"].split("|")[1],
            },
        }

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Send userbot info"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup={
                "text": self.config["custom_button"].split("|")[0],
                "url": self.config["custom_button"].split("|")[1],
            },
        )

    @loader.unrestricted
    async def hikkainfocmd(self, message: Message):
        """[en/ru - default en] - Send info aka 'What is Hikka?'"""
        args = utils.get_args_raw(message)
        args = args if args in {"en", "ru"} else "en"

        await utils.answer(
            message,
            (
                "🌘 <b>Hikka</b>\n\n"
                "Brand new userbot for Telegram with a lot of features, "
                "aka InlineGalleries, Forms and others. Userbot - software, running "
                "on your Telegram account. If you write a command to any chat, it will "
                "get executed right there. Check out live examples at "
                '<a href="https://github.com/hikariatama/Hikka">GitHub</a>'
            )
            if args == "en"
            else (
                "🌘 <b>Hikka</b>\n\n"
                "Новый юзербот для Telegram с огромным количеством функций, "
                "из которых: Инлайн Галереи, формы и другое. Юзербот - программа, "
                "которая запускается на твоем Telegram-аккаунте. Когда ты пишешь "
                "команду в любом чате, она сразу же выполняется. Обрати внимание "
                'на живые примеры на <a href="https://github.com/hikariatama/Hikka">GitHub</a>'
            ),
        )
