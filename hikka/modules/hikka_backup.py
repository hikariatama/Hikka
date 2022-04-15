# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @hikariatama

from .. import loader, utils
from telethon.tl.types import Message
import logging
from aiogram.types import CallbackQuery
import time
import asyncio
import io
import json
import datetime
from telethon.tl.functions.channels import EditPhotoRequest

import requests

logger = logging.getLogger(__name__)


@loader.tds
class HikkaBackupMod(loader.Module):
    """Automatic database backup"""

    strings = {
        "name": "HikkaBackup",
        "period": "⌚️ <b>Hewwo! I'm Asuna</b> - your personal backup manager. Please, select the periodicity of automatic database backups",
        "saved": "✅ Backup period saved. You can re-configure it later with .set_backup_period",
        "never": "✅ I will not make automatic backups. You can re-configure it later with .set_backup_period",
        "invalid_args": "🚫 <b>Specify correct backup period in hours, or `0` to disable</b>",
    }

    async def on_unload(self) -> None:
        self._task.cancel()

    async def client_ready(self, client, db) -> None:
        self._db = db
        self._client = client
        self._me = (await client.get_me()).id
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self._me,
                photo="https://i.pinimg.com/originals/94/e5/9c/94e59c1fbecd7b842d7feeecb58f8fd6.jpg",
                caption=self.strings("period"),
                reply_markup=self.inline._generate_markup(
                    utils.chunks(
                        [
                            {"text": f"🕰 {i} h", "data": f"backup_period/{i}"}
                            for i in {1, 2, 4, 6, 8, 12, 24, 48, 168}
                        ],
                        3,
                    )
                    + [[{"text": "🚫 Never", "data": "backup_period/never"}]]
                ),
                parse_mode="HTML",
            )

        self._backup_channel, is_new = await utils.asset_channel(
            self._client,
            "hikka-backups",
            "📼 Your database backups will appear there",
            silent=True,
            archive=True,
        )

        self._task = asyncio.ensure_future(self.handler())

        if not is_new:
            return

        try:
            f = (
                await utils.run_sync(
                    requests.get,
                    "https://i.imgur.com/0wa2kEu.jpeg",
                )
            ).content

            await self._client(
                EditPhotoRequest(
                    channel=self._backup_channel,
                    photo=await self._client.upload_file(f, file_name="photo.jpg"),
                )
            )
        except Exception:
            pass

    async def backup_period_callback_handler(self, call: CallbackQuery) -> None:
        if not call.data.startswith("backup_period"):
            return

        if call.data == "backup_period/never":
            self.set("period", "disabled")
            await call.answer(self.strings("never"), show_alert=True)

            await self.inline.bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
            return

        period = int(call.data.split("/")[1]) * 60 * 60

        self.set("period", period)
        self.set("last_backup", round(time.time()))

        await call.answer(self.strings("saved"), show_alert=True)

        await self.inline.bot.delete_message(
            call.message.chat.id,
            call.message.message_id,
        )

    async def set_backup_periodcmd(self, message: Message) -> None:
        """<time in hours> - Change backup frequency"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit() or int(args) not in range(200):
            await utils.answer(message, self.strings("invalid_args"))
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(message, f"<b>{self.strings('never')}</b>")
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(message, f"<b>{self.strings('saved')}</b>")

    async def handler(self) -> None:
        while True:
            try:
                if not self.get("period"):
                    await asyncio.sleep(3)
                    continue

                if not self.get("last_backup"):
                    self.set("last_backup", round(time.time()))
                    await asyncio.sleep(self.get("period"))
                    continue

                if self.get("period") == "disabled":
                    return

                await asyncio.sleep(
                    self.get("last_backup") + self.get("period") - time.time()
                )

                backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
                backup.name = f"hikka-db-backup-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.json"

                await self._client.send_file(
                    self._backup_channel,
                    backup,
                )
                self.set("last_backup", round(time.time()))
            except Exception:
                logger.exception("HikkaBackup failed")
                await asyncio.sleep(3)
