#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import os
from random import choice

from .. import loader, translations
from ..inline.types import BotInlineCall

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

📼 <b>You can find and install modules using @hikkamods_bot. Simply enter your search query and click ⛩ Install on needed module</b>

📣 <b>Check out community made channels with modules: <a href="https://t.me/hikka_ub/126">show</a></b>

💁‍♀️ <b>Quickstart:</b>

1️⃣ <b>Type </b><code>.help</code> <b>to see modules list</b>
2️⃣ <b>Type </b><code>.help &lt;ModuleName/command&gt;</code> <b>to see help of module ModuleName</b>
3️⃣ <b>Type </b><code>.dlmod &lt;link&gt;</code> <b>to load module from link</b>
4️⃣ <b>Type </b><code>.loadmod</code> <b>with reply to file to install module from it</b>
5️⃣ <b>Type </b><code>.unloadmod &lt;ModuleName&gt;</code> <b>to unload module ModuleName</b>
"""


TEXT_RU = """🌘🇷🇺 <b>Привет.</b> Твой юзербот <b>Hikka</b> установлен.

❓ <b>Нужна помощь?</b> Вступай в наш чат поддержки. Мы помогаем <b>всем</b>.

📼 <b>Ты можешь искать и устанавливать модули через @hikkamods_bot. Просто введи поисковый запрос и нажми ⛩ Install на нужном модуле</b>

📣 <b>Загляни в каналы с модулями, созданными комьюнити: <a href="https://t.me/hikka_ub/126">показать</a></b>

💁‍♀️ <b>Быстрый гайд:</b>

1️⃣ <b>Напиши </b><code>.help</code> <b>чтобы увидеть список модулей</b>
2️⃣ <b>Напиши </b><code>.help &lt;Название модуля/команда&gt;</code> <b>чтобы увидеть описание модуля</b>
3️⃣ <b>Напиши </b><code>.dlmod &lt;ссылка&gt;</code> <b>чтобы загрузить модуль из ссылка</b>
4️⃣ <b>Напиши </b><code>.loadmod</code> <b>ответом на файл, чтобы загрузить модуль из него</b>
5️⃣ <b>Напиши </b><code>.unloadmod &lt;Название модуля&gt;</code> <b>чтобы выгрузить модуль</b>

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

if "RAILWAY" in os.environ:
    TEXT += (
        "🚂 <b>Your userbot is installed on Railway</b>. This platform has only <b>500"
        " free hours per month</b>. Once this limit is reached, your <b>Hikka will be"
        " frozen</b>. Next month <b>you will need to go to https://railway.app and"
        " restart it</b>."
    )
    TEXT_RU += (
        "🚂 <b>Твой юзербот установлен на Railway</b>. На этой платформе ты получаешь"
        " только <b>500 бесплатных часов в месяц</b>. Когда лимит будет достигнет, твой"
        " <b>юзербот будет заморожен</b>. В следующем месяце <b>ты должен будешь"
        " перейти на https://railway.app и перезапустить его</b>."
    )


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    strings = {"name": "Quickstart"}

    async def client_ready(self):
        if self._db.get("hikka", "disable_quickstart", False):
            raise loader.SelfUnload

        self.mark = (
            lambda lang: [
                [{"text": "🥷 Support chat", "url": "https://t.me/hikka_talks"}],
                [
                    {
                        "text": "🇷🇺 Изменить язык",
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
                        "text": "🇬🇧 Switch language",
                        "callback": self._change_lang,
                        "args": ("en",),
                    }
                ],
            ]
        )

        await self.inline.bot.send_animation(self._client.tg_id, animation=choice(imgs))
        await self.inline.bot.send_message(
            self._client.tg_id,
            TEXT,
            reply_markup=self.inline.generate_markup(self.mark("en")),
            disable_web_page_preview=True,
        )

        self._db.set("hikka", "disable_quickstart", True)

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
