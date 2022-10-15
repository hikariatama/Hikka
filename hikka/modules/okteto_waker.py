#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging
import os
import time

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.functions.messages import (
    GetScheduledHistoryRequest,
    DeleteScheduledMessagesRequest,
)
from telethon.tl.types import Message

from .. import loader, main, utils

logger = logging.getLogger(__name__)


@loader.tds
class OktetoMod(loader.Module):
    """Helps Hikka to stay awake on Okteto"""

    strings = {"name": "Okteto"}
    strings_ru = {"_cls_doc": "Помогает Hikka оставаться активной на Okteto"}
    strings_de = {"_cls_doc": "Hilft Hikka, auf Okteto wach zu bleiben"}
    strings_uz = {"_cls_doc": "Okteto-da Hikka-ni yashaydigan yordam beradi"}
    strings_hi = {"_cls_doc": "Okteto पर Hikka को जागा रखने में मदद करता है"}

    _env_wait_interval = 10
    _overall_polling_interval = 30 * 60
    _plan = 2 * 24 * 60 * 60
    _messages_interval = 30 * 60
    _exception_timeout = 10
    _send_interval = 5
    _bot = "@WebpageBot"

    async def client_ready(self):
        if "OKTETO" not in os.environ:
            messages = (
                await self._client(
                    GetScheduledHistoryRequest(
                        peer=self._bot,
                        hash=0,
                    ),
                )
            ).messages

            if messages:
                logger.info("Deleting previously scheduled Okteto pinger messages")

            await self._client(
                DeleteScheduledMessagesRequest(
                    self._bot,
                    [message.id for message in messages],
                )
            )

            raise loader.SelfUnload

        await utils.dnd(self._client, self._bot, True)
        self._task = asyncio.ensure_future(self._okteto_pinger())

    async def on_unload(self):
        self._task.cancel()

    async def _okteto_pinger(self):
        """Creates queue to Webpage bot to reset Okteto polling after app goes to sleep
        """
        while True:
            try:
                if not main.get_config_key("okteto_uri"):
                    await asyncio.sleep(self._env_wait_interval)
                    continue

                uri = main.get_config_key("okteto_uri")
                current_queue = (
                    await self._client(
                        GetScheduledHistoryRequest(
                            peer=self._bot,
                            hash=0,
                        ),
                    )
                ).messages

                try:
                    last_date = max(
                        time.mktime(m.date.timetuple()) for m in current_queue
                    )
                except ValueError:
                    last_date = time.time()

                while last_date < time.time() + self._plan:
                    last_date += self._messages_interval
                    try:
                        await self._client.send_message(
                            self._bot,
                            f"{uri}?hash={utils.rand(6)}",
                            schedule=last_date,
                        )
                    except YouBlockedUserError:
                        await self._client(UnblockRequest(id=self._bot))
                        await self._client.send_message(
                            self._bot,
                            f"{uri}?hash={utils.rand(6)}",
                            schedule=last_date,
                        )

                    logger.debug("Scheduled Okteto pinger to %s", last_date)
                    await asyncio.sleep(self._send_interval)

                await asyncio.sleep(self._overall_polling_interval)
            except Exception:
                logger.exception("Caught exception on Okteto poller")
                await asyncio.sleep(self._exception_timeout)

    async def watcher(self, message: Message):
        if (
            not getattr(message, "raw_text", False)
            or not main.get_config_key("okteto_uri")
            or (
                main.get_config_key("okteto_uri") not in message.raw_text
                and "Link previews was updated successfully" not in message.raw_text
            )
            or utils.get_chat_id(message) != 169642392
        ):
            return

        if message.out:
            await asyncio.sleep(1)

        await message.delete()
