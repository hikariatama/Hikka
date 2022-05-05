# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/emoji/344/shield-emoji.png
# meta developer: @hikariatama

from .. import loader, utils
from ..inline.types import InlineCall
from telethon.tl.types import Message
import logging
import time
import io
import json
import random
import asyncio

logger = logging.getLogger(__name__)


@loader.tds
class APIRatelimiterMod(loader.Module):
    """Helps userbot avoid spamming Telegram API"""

    strings = {
        "name": "APIRatelimiter",
        "warning": (
            "🚫 <b>WARNING!</b>\n\n"
            "Your account exceeded the limit of requests, "
            "specified in config. In order to prevent "
            "Telegram API Flood, userbot has been <b>fully frozen</b> "
            "for {} seconds. Further info is provided in attached file. \n\n"
            "It is recommended to get help in <code>{prefix}support</code> group!\n\n"
            "If you think, that it is an intended behavior, then wait until userbot gets unlocked "
            "and next time, when you will be going to perform such an operation, use "
            "<code>{prefix}suspend_api_protect</code> &lt;time in seconds&gt;"
        ),
        "args_invalid": "🚫 <b>Invalid arguments</b>",
        "suspended_for": "✅ <b>API Flood Protection is disabled for {} seconds</b>",
        "test": "⚠️ <b>This action will expose your account to flooding Telegram API.</b> <i>In order to confirm, that you really know, what you are doing, complete this simple test - find the emoji, differing from others</i>",
        "on": "✅ <b>Protection enabled</b>",
        "off": "🚫 <b>Protection disabled</b>",
        "u_sure": "⚠️ <b>Are you sure?</b>",
    }

    strings_ru = {
        "warning": (
            "🚫 <b>ВНИМАНИЕ!</b>\n\n"
            "Аккаунт вышел за лимиты запросов, указанные в конфиге. "
            "С целью предотвращения флуда Telegram API, юзербот был <b>полностью заморожен</b> "
            "на {} секунд. Дополнительная информация прикреплена в файле ниже. \n\n"
            "Рекомендуется обратиться за помощью в <code>{prefix}support</code> группу!\n\n"
            "Если ты считаешь, что это запланированное поведение юзербота, просто подожди, пока закончится таймер "
            "и в следующий раз, когда запланируешь выполнять такую ресурсозатратную операцию, используй "
            "<code>{prefix}suspend_api_protect</code> &lt;время в секундах&gt;"
        ),
        "args_invalid": "🚫 <b>Неверные аргументы</b>",
        "suspended_for": "✅ <b>Защита API отключена на {} секунд</b>",
        "test": "⚠️ <b>Это действие открывает юзерботу возможность флудить Telegram API.</b> <i>Для того, чтобы убедиться, что ты действительно уверен в том, что делаешь - реши простенький тест - найди отличающийся эмодзи.</i>",
        "on": "✅ <b>Защита включена</b>",
        "off": "🚫 <b>Защита отключена</b>",
        "u_sure": "⚠️ <b>Ты уверен?</b>",
    }

    _ratelimiter = []
    _suspend_until = 0
    _lock = False

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("time_sample", 15, lambda: "Time sample DO NOT TOUCH"),
            loader.ConfigValue("threshold", 100, lambda: "Threshold DO NOT TOUCH"),
            loader.ConfigValue("local_floodwait", 30, lambda: "Local FW DO NOT TOUCH"),
        )

    async def client_ready(self, client, db):
        self._client = client
        asyncio.ensure_future(self._install_protection())

    async def _install_protection(self):
        await asyncio.sleep(30)  # Restart lock
        if hasattr(self._client._call, "_old_call_rewritten"):
            raise loader.SelfUnload("Already installed")

        self._me = (await self._client.get_me()).id
        old_call = self._client._call

        async def new_call(
            sender: "MTProtoSender",  # noqa: F821
            request: "TLRequest",  # noqa: F821
            ordered: bool = False,
            flood_sleep_threshold: int = None,
        ):
            if time.perf_counter() > self._suspend_until and not self.get(
                "disable_protection",
                True,
            ):
                request_name = type(request).__name__
                self._ratelimiter += [[request_name, time.perf_counter()]]

                self._ratelimiter = list(
                    filter(
                        lambda x: time.perf_counter() - x[1]
                        < int(self.config["time_sample"]),
                        self._ratelimiter,
                    )
                )

                if (
                    len(self._ratelimiter) > int(self.config["threshold"])
                    and not self._lock
                ):
                    self._lock = True
                    report = io.BytesIO(
                        json.dumps(
                            self._ratelimiter,
                            indent=4,
                        ).encode("utf-8")
                    )
                    report.name = "local_fw_report.json"

                    await self.inline.bot.send_document(
                        self._me,
                        report,
                        caption=self.strings("warning").format(
                            self.config["local_floodwait"],
                            prefix=self.get_prefix(),
                        ),
                        parse_mode="HTML",
                    )

                    # It is intented to use time.sleep instead of asyncio.sleep
                    time.sleep(int(self.config["local_floodwait"]))
                    self._lock = False

            return await old_call(sender, request, ordered, flood_sleep_threshold)

        self._client._call = new_call
        self._client._old_call_rewritten = old_call
        self._client._call._hikka_overwritten = True
        logger.debug("Successfully installed ratelimiter")

    async def on_unload(self):
        if hasattr(self._client, "_old_call_rewritten"):
            self._client._call = self._client._old_call_rewritten
            delattr(self._client, "_old_call_rewritten")
            logger.debug("Successfully uninstalled ratelimiter")

    async def suspend_api_protectcmd(self, message: Message):
        """<time in seconds> - Suspend API Ratelimiter for n seconds"""
        args = utils.get_args_raw(message)

        if not args or not args.isdigit():
            await utils.answer(message, self.strings("args_invalid"))
            return

        self._suspend_until = time.perf_counter() + int(args)
        await utils.answer(message, self.strings("suspended_for").format(args))

    async def api_fw_protectioncmd(self, message: Message):
        """Only for people, who know what they're doing"""
        await self.inline.form(
            message=message,
            text=self.strings("u_sure"),
            reply_markup=[
                {"text": "🚫 No", "callback": self._cancel},
                {"text": "✅ Yes", "callback": self._finish},
            ],
        )

    async def _cancel(self, call: InlineCall):
        await call.answer("Goodbye!")
        await call.delete()

    def _generate_silly_markup(
        self,
        emoji1: str,
        emoji2: str,
        callback: callable,
    ) -> list:
        markup = [{"text": emoji1, "callback": self._cancel}] * (8**2 - 1) + [
            {"text": emoji2, "callback": callback}
        ]
        random.shuffle(markup)
        return utils.chunks(markup, 8)

    async def _finish(self, call: InlineCall):
        state = self.get("disable_protection", True)
        self.set("disable_protection", not state)
        await call.edit(self.strings("on" if state else "off"))
