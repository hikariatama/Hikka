#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#    Modded by GeekTG Team

import asyncio
import logging

import telethon

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class NoCollisionsMod(loader.Module):
    """Makes sure only 1 userbot is running at a time"""

    strings = {
        "name": "Anti-collisions",
        "killed": "<b>All userbots killed</b>",
        "deadbeff": "<code>DEADBEEF</code>",
    }

    @loader.owner
    async def cleanbotscmd(self, message):
        """Kills all userbots except 1, selected according to which is fastest (approx)"""
        try:
            await utils.answer(message, self.strings("deadbeff", message))
            await asyncio.sleep(5)
            await utils.answer(message, self.strings("killed", message))
        except telethon.errors.rpcerrorlist.MessageNotModifiedError:
            handler = logging.getLogger().handlers[0]
            handler.setLevel(logging.CRITICAL)

            for client in self.allclients:
                # Terminate main loop of all running clients
                # Won't work if not all clients are ready
                if client is not message.client:
                    await client.disconnect()

            await message.client.disconnect()
