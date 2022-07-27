#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: inline

import logging

import git
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, main, utils
from ..inline.types import InlineQuery

logger = logging.getLogger(__name__)


@loader.tds
class HikkaInfoMod(loader.Module):
    """Show userbot info"""

    strings = {
        "name": "HikkaInfo",
        "owner": "Owner",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "send_info": "Send userbot info",
        "description": "ℹ This will not compromise any sensitive info",
        "up-to-date": "<b>😌 Up-to-date</b>",
        "update_required": "<b>😕 Update required </b><code>.update</code>",
        "_cfg_cst_msg": (
            "Custom message for info. May contain {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime} keywords"
        ),
        "_cfg_cst_btn": "Custom button for info. Leave empty to remove button",
        "_cfg_banner": "URL to image banner",
    }

    strings_ru = {
        "owner": "Владелец",
        "version": "Версия",
        "build": "Сборка",
        "prefix": "Префикс",
        "send_info": "Отправить информацию о юзерботе",
        "description": "ℹ Это не раскроет никакой личной информации",
        "_ihandle_doc_info": "Отправить информацию о юзерботе",
        "up-to-date": "😌 Актуальная версия",
        "update_required": "😕 Требуется обновление </b><code>.update</code><b>",
        "_cfg_cst_msg": (
            "Кастомный текст сообщения в info. Может содержать ключевые слова {me},"
            " {version}, {build}, {prefix}, {platform}, {upd}, {uptime}"
        ),
        "_cfg_cst_btn": (
            "Кастомная кнопка в сообщении в info. Оставь пустым, чтобы убрать кнопку"
        ),
        "_cfg_banner": "Ссылка на баннер-картинку",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button",
                ["🌘 Support chat", "https://t.me/hikka_talks"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Union(
                    loader.validators.Series(fixed_len=2),
                    loader.validators.NoneType(),
                ),
            ),
            loader.ConfigValue(
                "banner_url",
                "https://github.com/hikariatama/assets/raw/master/hikka_banner.png",
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Link(),
            ),
        )

    async def client_ready(self, client, _):
        self._me = await client.get_me()

    def _render_info(self) -> str:
        ver = utils.get_git_hash() or "Unknown"

        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = (
            "<b><a"
            f' href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></b>'
        )
        version = f'<i>{".".join(list(map(str, list(main.__version__))))}</i>'
        build = (
            f'<a href="https://github.com/hikariatama/Hikka/commit/{ver}">#{ver[:8]}</a>'
        )
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"
        platform = utils.get_named_platform()

        return (
            (
                "<b>🌘 Hikka</b>\n"
                if "hikka" not in self.config["custom_message"].lower()
                else ""
            )
            + self.config["custom_message"].format(
                me=me,
                version=version,
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=utils.formatted_uptime(),
            )
            if self.config["custom_message"] and self.config["custom_message"] != "no"
            else (
                "<b>🌘 Hikka</b>\n"
                f'<b>🤴 {self.strings("owner")}: </b>{me}\n\n'
                f"<b>🔮 {self.strings('version')}: </b>{version} {build}\n"
                f"<b>{upd}</b>\n\n"
                f"<b>📼 {self.strings('prefix')}: </b>{prefix}\n"
                f"<b>{platform}</b>\n"
            )
        )

    def _get_mark(self):
        return (
            {
                "text": self.config["custom_button"][0],
                "url": self.config["custom_button"][1],
            }
            if self.config["custom_button"]
            else None
        )

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Send userbot info"""

        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            "message": self._render_info(),
            "thumb": (
                "https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png"
            ),
            "reply_markup": self._get_mark(),
        }

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Send userbot info"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup=self._get_mark(),
            **(
                {"photo": self.config["banner_url"]}
                if self.config["banner_url"]
                else {}
            ),
        )

    @loader.unrestricted
    async def hikkainfocmd(self, message: Message):
        """[en/ru - default en] - Send info aka 'What is Hikka?'"""
        args = utils.get_args_raw(message)
        args = args if args in {"en", "ru"} else "en"

        await utils.answer(
            message,
            "🌘 <b>Hikka</b>\n\n"
            "Brand new userbot for Telegram with a lot of features, "
            "aka InlineGalleries, forms etc. Userbot - software, running "
            "on your Telegram account. If you write a command to any chat, it will "
            "get executed right there. Check out live examples at "
            '<a href="https://github.com/hikariatama/Hikka">GitHub</a>'
            if args == "en"
            else (
                "🌘 <b>Hikka</b>\n\nНовый юзербот для Telegram с огромным количеством"
                " функций, из которых: Инлайн галереи, формы и другое. Юзербот -"
                " программа, которая запускается на твоем Telegram-аккаунте. Когда ты"
                " пишешь команду в любом чате, она сразу же выполняется. Обрати"
                " внимание на живые примеры на <a"
                ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
            ),
        )
