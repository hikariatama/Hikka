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
# requires: websockets

import asyncio
import json
import logging
import re

import websockets
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.functions.messages import SendReactionRequest

from .. import loader

logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    "https://github.com/morisummerz/ftg-mods/raw/main",
    "https://raw.githubusercontent.com/morisummerz/ftg-mods/main",
    "https://mods.morisummer.ml",
    "https://gitlab.com/cakestwix/friendly-userbot-modules/-/raw/master",
    "https://twix.nonfalse-networks.net.ua/modules",
    "https://mods.hikariatama.ru",
    "https://raw.githubusercontent.com/hikariatama/ftg/master",
    "https://github.com/hikariatama/ftg/raw/master",
    "https://raw.githubusercontent.com/hikariatama/host/master",
    "https://github.com/hikariatama/host/raw/master",
]


class RefreshToken(Exception):
    """Placeholder"""


@loader.tds
class HikkaDLMod(loader.Module):
    """Downloads stuff"""

    strings = {"name": "HikkaDL"}

    _connected = False

    async def _wss(self):
        logger.debug("Connecting to HikkaDL websocket....")
        async with websockets.connect(
            f"wss://hikka.hikariatama.ru/ws/{self.get('token')}"
        ) as wss:
            while True:
                ans = json.loads(await wss.recv())
                self._connected = True
                self._no_revoke = False
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
                            r".dlmod (https://[^ ]*\.py)",
                            msg.raw_text,
                        ).group(1)
                    except Exception:
                        await wss.send("link_404")
                        continue

                    if "/".join(link.split("/")[:-1]).lower() not in ALLOWED_ORIGINS:
                        await wss.send("🚫 Origin is not allowed")
                        continue

                    # Modules' creators spend so much time to create cool modules
                    # so this code part is a little propriety gesture. Send a ❤
                    # to a message with a link to currently downloading module
                    try:
                        await self._client(
                            SendReactionRequest(
                                peer=ans["channel"],
                                msg_id=ans["message_id"],
                                reaction="❤️",
                            )
                        )
                    except Exception:
                        pass

                    m = await self._client.send_message("me", f".dlmod {link}")

                    if "dlmod" not in self.allmodules.commands:
                        await wss.send(
                            "Loader is unavailable. Perhaps, userbot is not yet fully loaded"
                        )
                        continue

                    await self.allmodules.commands["dlmod"](m)
                    load = (await self._client.get_messages(m.peer_id, ids=[m.id]))[0]
                    await wss.send(load.raw_text.splitlines()[0])
                    await m.delete()

                if ans["event"] == "update":
                    logger.debug("Socket keep-alive timer expired, reconnecting...")
                    return

                if ans["event"] == "invalid_token":
                    logger.debug("Refreshing token...")
                    raise RefreshToken

    async def _connect(self):
        self._no_revoke = False
        while True:
            try:
                await self._wss()
            except RefreshToken:
                logger.debug("Token became invalid, revoking...")
                await self._get_token()
            except Exception:
                logger.debug("Socket disconnected, retry in 5 sec", exc_info=True)
                self._connected = False
                await asyncio.sleep(5)

    async def _get_token(self):
        async with self._client.conversation(self._bot) as conv:
            m = await conv.send_message("/token")
            r = await conv.get_response()
            token = r.raw_text
            await m.delete()
            await r.delete()

            if not token.startswith("kirito_") and not token.startswith("asuna_"):
                raise loader.LoadError("Can't get token")

            self.set("token", token)

        await self._client.delete_dialog(self._bot)

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._bot = "@hikka_userbot"

        await self._client(UnblockRequest(id=self._bot))

        if not self.get("token"):
            await self._get_token()

        self._task = asyncio.ensure_future(self._connect())

    async def on_unload(self):
        self._task.cancel()
