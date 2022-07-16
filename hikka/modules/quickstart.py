#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import os
from random import choice

from .. import loader, translations
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)
imgs = [
    "https://i.gifer.com/GmUB.gif",
    "https://i.gifer.com/Afdn.gif",
    "https://i.gifer.com/3uvT.gif",
    "https://i.gifer.com/2qQQ.gif",
    "https://i.gifer.com/Lym6.gif",
    "https://i.gifer.com/IjT4.gif",
    "https://i.gifer.com/A9H.gif",
    
]

TEXT = """🌘🇬🇧 <b>Hello.</b> You've just installed <b>Hikka</b> userbot.

❓ <b>Need help?</b> Feel free to join our support chat. We help <b>everyone</b>.

📼 <b>You can find and install modules using @hikkamods_bot. Simply enter your search query and click 📥 Install on needed module</b>

"""


TEXT_RU = """🌘🇷🇺 <b>Привет.</b> Твой юзербот <b>Hikka</b> установлен.

❓ <b>Нужна помощь?</b> Вступай в наш чат поддержки. Мы помогаем <b>всем</b>.

📼 <b>Ты можешь искать и устанавливать модули через @hikkamods_bot. Просто введи поисковый запрос и нажми 📥 Install на нужном модуле</b>

"""

if "OKTETO" in os.environ:
    TEXT += (
        "☁️ <b>Your userbot is installed on Okteto</b>. You will get notifications from"
        " @WebpageBot. Do not block him."
    )
    TEXT_RU += (
        "☁️ <b>Твой юзербот установлен на Okteto</b>. Ты будешь получать уведомления от"
        " @WebpageBot. Не блокируй его."
    )

if "DYNO" in os.environ:
    TEXT += (
        "♓️ <b>Your userbot is installed on Heroku</b>. You will get notifications from"
        " @WebpageBot. Do not block him."
    )
    TEXT_RU += (
        "♓️ <b>Твой юзербот установлен на Heroku</b>. Ты будешь получать уведомления от"
        " @WebpageBot. Не блокируй его."
    )


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    strings = {"name": "Quickstart"}

    async def client_ready(self, client, db):
        if db.get("hikka", "disable_quickstart", False):
            raise loader.SelfUnload

        self.mark = (
            lambda lang: [
                [{"text": "🥷 Support chat", "url": "https://t.me/hikka_talks"}],
                [
                    {
                        "text": "🇷🇺 Русский",
                        "callback": self._change_lang,
                        "args": ("ru",),
                    }
                ],
            ]
            if lang == "en"
            else [
                [{"text": "🥷 Чат помощи", "url": "https://t.me/hikka_talks"}],
                [
                    {
                        "text": "🇬🇧 English",
                        "callback": self._change_lang,
                        "args": ("en",),
                    }
                ],
            ]
        )

        await self.inline.bot.send_animation(
            client.tg_id,
            animation=choice(imgs),
            caption=TEXT,
            reply_markup=self.inline.generate_markup(self.mark("en")),
        )

        db.set("hikka", "disable_quickstart", True)

    async def _change_lang(self, call: BotInlineCall, lang: str):
        if lang == "ru":
            self._db.set(translations.__name__, "lang", "ru")
            await self.translator.init()
            await call.answer("🇷🇺 Язык сохранен!")
            await call.edit(text=TEXT_RU, reply_markup=self.mark("ru"))
        elif lang == "en":
            self._db.set(translations.__name__, "lang", "en")
            await self.translator.init()
            await call.answer("🇬🇧 Language saved!")
            await call.edit(text=TEXT, reply_markup=self.mark("en"))
