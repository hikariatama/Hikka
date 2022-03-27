# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

from .. import loader
import logging
import asyncio
import os
import time
from telethon.tl.functions.messages import GetScheduledHistoryRequest

logger = logging.getLogger(__name__)


@loader.tds
class OktetoMod(loader.Module):
    """Stuff related to Hikka Okteto cloud installation"""

    strings = {"name": "Okteto"}

    async def client_ready(self, client, db) -> None:
        if "OKTETO" not in os.environ:
            raise loader.LoadError(
                "This module can be loaded only if userbot is installed to ☁️ Okteto"
            )

        self._db = db
        self._client = client
        self._env_wait_interval = 10
        self._overall_polling_interval = 60 * 60
        self._plan = 3 * 24 * 60 * 60
        self._messages_interval = 60 * 60
        self._exception_timeout = 10
        self._send_interval = 5
        self._bot = "@WebpageBot"
        self._task = asyncio.ensure_future(self._okteto_poller())

    async def on_unload(self) -> None:
        self._task.cancel()

    async def _okteto_poller(self) -> None:
        """Creates queue to Webpage bot to reset Okteto polling after app goes to sleep"""
        while True:
            try:
                if "OKTETO_URI" not in os.environ:
                    await asyncio.sleep(self._env_wait_interval)
                    continue

                uri = os.environ["OKTETO_URI"]
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
                    await self._client.send_message(
                        self._bot,
                        uri,
                        schedule=last_date,
                    )
                    logger.debug(f"Scheduled Okteto pinger to {last_date}")
                    await asyncio.sleep(self._send_interval)

                await asyncio.sleep(self._overall_polling_interval)
            except Exception:
                logger.exception("Caught exception on Okteto poller")
                await asyncio.sleep(self._exception_timeout)
