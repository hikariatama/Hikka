# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import os
from random import choice

from .. import loader, translations, utils
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


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    async def client_ready(self):
        if self.get("disable_quickstart"):
            raise loader.SelfUnload

        self.mark = (
            lambda: [
                [
                    {
                        "text": self.strings("btn_support"),
                        "url": "https://t.me/hikka_talks",
                    }
                ],
            ]
            + [
                [
                    {
                        "text": "👩‍⚖️ Privacy Policy",
                        "url": "https://docs.google.com/document/d/15m6-pb1Eya8Zn4y0_7JEdvMLAo_v050rFMaWrjDjvMs/edit?usp=sharing",
                    },
                    {
                        "text": "📜 EULA",
                        "url": "https://docs.google.com/document/d/1sZBk24SWLBLoGxcsZHW8yP7yLncToPGUP1FJ4dS6z5I/edit?usp=sharing",
                    },
                ]
            ]
            + utils.chunks(
                [
                    {
                        "text": self.strings.get("language", lang),
                        "callback": self._change_lang,
                        "args": (lang,),
                    }
                    for lang in translations.SUPPORTED_LANGUAGES
                ],
                3,
            )
        )

        self.text = (
            lambda: self.strings("base")
            + (
                "\n"
                + (
                    self.strings("railway")
                    if "RAILWAY" in os.environ
                    else (self.strings("lavhost") if "LAVHOST" in os.environ else "")
                )
            ).rstrip()
        )

        await self.inline.bot.send_animation(self._client.tg_id, animation=choice(imgs))
        await self.inline.bot.send_message(
            self._client.tg_id,
            self.text(),
            reply_markup=self.inline.generate_markup(self.mark()),
            disable_web_page_preview=True,
        )

        self.set("disable_quickstart", True)

    async def _change_lang(self, call: BotInlineCall, lang: str):
        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.answer(self.strings("language_saved"))
        await call.edit(text=self.text(), reply_markup=self.mark())
