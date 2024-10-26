# ©️ Ваше имя, 2024
# Это файл является частью Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# Вы можете распространять и/или изменять его в соответствии с условиями GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import git
from hikkatl.tl.types import Message
from hikkatl.utils import get_display_name

from .. import loader, utils, version
from ..inline.types import InlineQuery


@loader.tds
class HikkaExtendedInfoMod(loader.Module):
    """Отображает расширенную информацию о боте"""

    strings = {"name": "HikkaExtendedInfo"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                "Информация о боте:",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_buttons",
                ["🌐 Поддержка", "https://t.me/hikka_talks"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Union(
                    loader.validators.Series(fixed_len=2),
                    loader.validators.NoneType(),
                ),
            ),
            loader.ConfigValue(
                "banner_url",
                "https://0x0.st/XgAX.jpg",
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Link(),
            ),
        )

    def _render_info(self) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = '<b><a href="tg://user?id={}">{}</a></b>'.format(
            self._client.hikka_me.id,
            utils.escape_html(get_display_name(self._client.hikka_me)),
        )
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        platform = utils.get_named_platform()

        return (
            f'<b>🌘 Hikka</b>\n'
            f'<b>Пользователь:</b> {me}\n'
            f'<b>Версия:</b> {_version}\n'
            f'<b>Платформа:</b> {platform}\n'
            f'<b>Статус обновления:</b> {upd}\n'
            f'<b>Время работы:</b> {utils.formatted_uptime()}'
        )

    def _get_buttons(self):
        buttons = []
        if self.config["custom_buttons"]:
            buttons.append({
                "text": self.config["custom_buttons"][0],
                "url": self.config["custom_buttons"][1],
            })
        return buttons

    @loader.inline_handler()
    @loader.inline_everyone
    async def info(self, _: InlineQuery) -> dict:
        """Отправить информацию о боте"""

        return {
            "title": self.strings("send_info"),
            "description": "Расширенная информация о боте",
            "photo": self.config["banner_url"],
            "caption": self._render_info(),
            "thumb": "https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png",
            "reply_markup": {"inline_keyboard": [self._get_buttons()]},
        }

    @loader.command()
    async def infocmd(self, message: Message):
        """Команда для отображения информации о боте"""
        await utils.answer(message, self._render_info())

    @loader.command()
    async def setinfo(self, message: Message):
        """Установить кастомное сообщение"""
        if not (args := utils.get_args_html(message)):
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))

    @loader.command()
    async def addbutton(self, message: Message):
        """Добавить новую кнопку"""
        if not (args := utils.get_args(message)):
            return await utils.answer(message, "Укажите текст и ссылку кнопки.")

        if len(args) < 2:
            return await utils.answer(message, "Требуется текст и ссылка для кнопки.")

        button_text, button_url = args[0], args[1]
        self.config["custom_buttons"] = [button_text, button_url]
        await utils.answer(message, "Кнопка добавлена.")
