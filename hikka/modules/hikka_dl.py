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
# scope: hikka_only
# meta developer: @hikariatama

from .. import loader
import websockets
import logging
import asyncio
from .._types import LoadError
import json
import re

logger = logging.getLogger(__name__)


@loader.tds
class HikkaDLMod(loader.Module):
    """Downloads stuff"""

    strings = {"name": "HikkaDL"}

    async def _wss(self) -> None:
        async with websockets.connect("wss://hikka.hikariatama.ru/ws") as wss:
            await wss.send(self.get("token"))

            while True:
                ans = json.loads(await wss.recv())
                logger.debug(ans)
                if ans["event"] == "dlmod":
                    try:
                        msg = (
                            await self._client.get_messages(
                                ans["channel"],
                                ids=[ans["message_id"]],
                            )
                        )[0]
                    except Exception:
                        await wss.send("msg_404")
                        continue

                    try:
                        link = re.search(
                            r".dlmod (https?://.*?\.py)",
                            msg.raw_text,
                        ).group(1)
                    except Exception:
                        await wss.send("link_404")
                        continue

                    m = await self._client.send_message("me", f".dlmod {link}")
                    await self.allmodules.commands["dlmod"](m)
                    await wss.send(
                        (await self._client.get_messages(m.peer_id, ids=[m.id]))[
                            0
                        ].raw_text.splitlines()[0]
                    )
                    await m.delete()

    async def _connect(self) -> None:
        while True:
            try:
                await self._wss()
            except Exception:
                logger.debug("Socket disconnected, retry in 10 sec")

            await asyncio.sleep(10)

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._bot = "@hikka_userbot"

        if not self.get("token"):
            async with client.conversation(self._bot) as conv:
                m = await conv.send_message("/token")
                r = await conv.get_response()
                token = r.raw_text
                await m.delete()
                await r.delete()
                if not token.startswith("kirito_") and not token.startswith("asuna_"):
                    raise LoadError("Can't get token")
                self.set("token", token)

        self._task = asyncio.ensure_future(self._connect())

    async def on_unload(self) -> None:
        self._task.cancel()
