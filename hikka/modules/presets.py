# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging

from .. import loader, utils
from ..inline.types import BotInlineMessage, InlineCall

logger = logging.getLogger(__name__)


PRESETS = {
    "fun": [
        "https://mods.hikariatama.ru/aniquotes.py",
        "https://mods.hikariatama.ru/artai.py",
        "https://mods.hikariatama.ru/inline_ghoul.py",
        "https://mods.hikariatama.ru/lovemagic.py",
        "https://mods.hikariatama.ru/mindgame.py",
        "https://mods.hikariatama.ru/moonlove.py",
        "https://mods.hikariatama.ru/neko.py",
        "https://mods.hikariatama.ru/purr.py",
        "https://mods.hikariatama.ru/rpmod.py",
        "https://mods.hikariatama.ru/scrolller.py",
        "https://mods.hikariatama.ru/tictactoe.py",
        "https://mods.hikariatama.ru/trashguy.py",
        "https://mods.hikariatama.ru/truth_or_dare.py",
        "https://mods.hikariatama.ru/sticks.py",
        "https://mods.hikariatama.ru/premium_sticks.py",
        "https://heta.hikariatama.ru/MoriSummerz/ftg-mods/magictext.py",
        "https://heta.hikariatama.ru/HitaloSama/FTG-modules-repo/quotes.py",
        "https://heta.hikariatama.ru/HitaloSama/FTG-modules-repo/spam.py",
        "https://heta.hikariatama.ru/SkillsAngels/Modules/IrisLab.py",
        "https://heta.hikariatama.ru/Fl1yd/FTG-Modules/arts.py",
        "https://heta.hikariatama.ru/SkillsAngels/Modules/Complements.py",
        "https://heta.hikariatama.ru/Den4ikSuperOstryyPer4ik/Astro-modules/Compliments.py",
        "https://heta.hikariatama.ru/vsecoder/hikka_modules/mazemod.py",
    ],
    "chat": [
        "https://mods.hikariatama.ru/activists.py",
        "https://mods.hikariatama.ru/banstickers.py",
        "https://mods.hikariatama.ru/hikarichat.py",
        "https://mods.hikariatama.ru/inactive.py",
        "https://mods.hikariatama.ru/keyword.py",
        "https://mods.hikariatama.ru/tagall.py",
        "https://mods.hikariatama.ru/voicechat.py",
        "https://mods.hikariatama.ru/vtt.py",
        "https://heta.hikariatama.ru/SekaiYoneya/Friendly-telegram/BanMedia.py",
        "https://heta.hikariatama.ru/iamnalinor/FTG-modules/swmute.py",
        "https://heta.hikariatama.ru/GeekTG/FTG-Modules/filter.py",
    ],
    "service": [
        "https://mods.hikariatama.ru/account_switcher.py",
        "https://mods.hikariatama.ru/surl.py",
        "https://mods.hikariatama.ru/httpsc.py",
        "https://mods.hikariatama.ru/img2pdf.py",
        "https://mods.hikariatama.ru/latex.py",
        "https://mods.hikariatama.ru/pollplot.py",
        "https://mods.hikariatama.ru/sticks.py",
        "https://mods.hikariatama.ru/temp_chat.py",
        "https://mods.hikariatama.ru/vtt.py",
        "https://heta.hikariatama.ru/vsecoder/hikka_modules/accounttime.py",
        "https://heta.hikariatama.ru/vsecoder/hikka_modules/searx.py",
        "https://heta.hikariatama.ru/iamnalinor/FTG-modules/swmute.py",
    ],
    "downloaders": [
        "https://mods.hikariatama.ru/musicdl.py",
        "https://mods.hikariatama.ru/uploader.py",
        "https://mods.hikariatama.ru/porn.py",
        "https://mods.hikariatama.ru/web2file.py",
        "https://heta.hikariatama.ru/AmoreForever/amoremods/instsave.py",
        "https://heta.hikariatama.ru/CakesTwix/Hikka-Modules/tikcock.py",
        "https://heta.hikariatama.ru/CakesTwix/Hikka-Modules/InlineYouTube.py",
        "https://heta.hikariatama.ru/CakesTwix/Hikka-Modules/InlineSpotifyDownloader.py",
        "https://heta.hikariatama.ru/GeekTG/FTG-Modules/downloader.py",
        "https://heta.hikariatama.ru/Den4ikSuperOstryyPer4ik/Astro-modules/dl_yt_previews.py",
    ],
}


@loader.tds
class Presets(loader.Module):
    """Suggests new Hikka users a packs of modules to load"""

    strings = {"name": "Presets"}

    async def client_ready(self):
        self._markup = utils.chunks(
            [
                {
                    "text": self.strings(f"_{preset}_title"),
                    "callback": self._preset,
                    "args": (preset,),
                }
                for preset in PRESETS
            ],
            1,
        )

        if self.get("sent"):
            return

        self.set("sent", True)
        await self._menu()

    async def _menu(self):
        await self.inline.bot.send_message(
            self._client.tg_id,
            self.strings("welcome"),
            reply_markup=self.inline.generate_markup(self._markup),
        )

    async def _back(self, call: InlineCall):
        await call.edit(self.strings("welcome"), reply_markup=self._markup)

    async def _install(self, call: InlineCall, preset: str):
        await call.delete()
        m = await self._client.send_message(
            self.inline.bot_id,
            self.strings("installing").format(preset),
        )
        for i, module in enumerate(PRESETS[preset]):
            await m.edit(
                self.strings("installing_module").format(
                    preset,
                    i,
                    len(PRESETS[preset]),
                    module,
                )
            )
            try:
                await self.lookup("loader").download_and_install(module, None)
            except Exception:
                logger.exception("Failed to install module %s", module)

            await asyncio.sleep(1)

        if self.lookup("loader").fully_loaded:
            self.lookup("loader").update_modules_in_db()

        await m.edit(self.strings("installed").format(preset))
        await self._menu()

    def _is_installed(self, link: str) -> bool:
        return any(
            link.strip().lower() == installed.strip().lower()
            for installed in self.lookup("loader").get("loaded_modules", {}).values()
        )

    async def _preset(self, call: InlineCall, preset: str):
        await call.edit(
            self.strings("preset").format(
                self.strings(f"_{preset}_title"),
                self.strings(f"_{preset}_desc"),
                "\n".join(
                    map(
                        lambda x: x[0],
                        sorted(
                            [
                                (
                                    "{} <b>{}</b>".format(
                                        (
                                            self.strings("already_installed")
                                            if self._is_installed(link)
                                            else "▫️"
                                        ),
                                        link.rsplit("/", maxsplit=1)[1].split(".")[0],
                                    ),
                                    int(self._is_installed(link)),
                                )
                                for link in PRESETS[preset]
                            ],
                            key=lambda x: x[1],
                            reverse=True,
                        ),
                    )
                ),
            ),
            reply_markup=[
                {"text": self.strings("back"), "callback": self._back},
                {
                    "text": self.strings("install"),
                    "callback": self._install,
                    "args": (preset,),
                },
            ],
        )

    async def aiogram_watcher(self, message: BotInlineMessage):
        if message.text != "/presets" or message.from_user.id != self._client.tg_id:
            return

        await self._menu()
