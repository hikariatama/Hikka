# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import os

from .. import loader, main, utils, heroku

logger = logging.getLogger(__name__)


@loader.tds
class HerokuMod(loader.Module):
    """Stuff related to Hikka Heroku installation"""

    strings = {"name": "Heroku"}

    async def client_ready(self, client, db):

        self._db = db
        self._client = client
        self._bot = "@WebpageBot"

        if "DYNO" not in os.environ:
            raise loader.SelfUnload

        await utils.dnd(client, await client.get_entity(self._bot), True)

        self._heroku_url = heroku.get_app(api_token=main.hikka.api_token)[0].web_url
        self._heroku_pinger.start()

    @loader.loop(interval=20 * 60, wait_before=True)
    async def _heroku_pinger(self):
        """Sends request to Heroku webapp through WebpageBot"""
        async with self._client.conversation(self._bot) as conv:
            m = await conv.send_message(self._heroku_url)
            r = await conv.get_response()
            await m.delete()
            await r.delete()
