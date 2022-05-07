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

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import atexit
import functools
import logging
import os
import subprocess
import sys
import asyncio
from typing import Union

import git
from git import Repo, GitCommandError
from telethon.tl.types import Message, DialogFilter
from telethon.tl.functions.messages import (
    UpdateDialogFilterRequest,
    GetDialogFiltersRequest,
)

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Updates itself"""

    strings = {
        "name": "Updater",
        "source": "ℹ️ <b>Read the source code from</b> <a href='{}'>here</a>",
        "restarting_caption": "🔄 <b>Restarting...</b>",
        "downloading": "🔄 <b>Downloading updates...</b>",
        "downloaded": "✅ <b>Downloaded successfully.\nPlease type</b> \n<code>.restart</code> <b>to restart the bot.</b>",
        "installing": "🔁 <b>Installing updates...</b>",
        "success": "✅ <b>Restart successful!</b>",
        "origin_cfg_doc": "Git origin URL, for where to update from",
        "btn_restart": "🔄 Restart",
        "btn_update": "⛵️ Update",
        "restart_confirm": "🔄 <b>Are you sure you want to restart?</b>",
        "update_confirm": "⛵️ <b>Are you sure you want to update?</b>",
        "cancel": "🚫 Cancel",
    }

    strings_ru = {
        "source": "ℹ️ <b>Исходный код можно прочитать</b> <a href='{}'>здесь</a>",
        "restarting_caption": "🔄 <b>Перезагрузка...</b>",
        "downloading": "🔄 <b>Скачивание обновлений...</b>",
        "downloaded": "✅ <b>Скачано успешно.\nНапиши</b> \n<code>.restart</code> <b>для перезагрузки юзербота.</b>",
        "installing": "🔁 <b>Установка обновлений...</b>",
        "success": "✅ <b>Перезагрузка успешна!</b>",
        "origin_cfg_doc": "Ссылка, из которой будут загружаться обновления",
        "btn_restart": "🔄 Перезагрузиться",
        "btn_update": "⛵️ Обновиться",
        "restart_confirm": "🔄 <b>Ты уверен, что хочешь перезагрузиться?</b>",
        "update_confirm": "⛵️ <b>Ты уверен, что хочешь обновиться?</b>",
        "cancel": "🚫 Отмена",
        "_cmd_doc_restart": "Перезагружает юзербот",
        "_cmd_doc_download": "Скачивает обновления",
        "_cmd_doc_update": "Обновляет юзербот",
        "_cmd_doc_source": "Ссылка на исходный код проекта",
        "_cls_doc": "Обновляет юзербот",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "GIT_ORIGIN_URL",
            "https://github.com/hikariatama/Hikka",
            lambda: self.strings("origin_cfg_doc"),
        )

    @loader.owner
    async def restartcmd(self, message: Message):
        """Restarts the userbot"""
        try:
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("restart_confirm"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_restart"),
                            "callback": self.inline_restart,
                        },
                        {"text": self.strings("cancel"), "callback": self.inline_close},
                    ],
                )
            ):
                raise
        except Exception:
            message = await utils.answer(message, self.strings("restarting_caption"))

            await self.restart_common(message)

    async def inline_restart(self, call: InlineCall):
        await call.edit(self.strings("restarting_caption"))
        await self.restart_common(call)

    async def inline_close(self, call: InlineCall):
        await call.delete()

    async def process_restart_message(self, msg_obj: Union[InlineCall, Message]):
        self.set(
            "selfupdatemsg",
            msg_obj.inline_message_id
            if hasattr(msg_obj, "inline_message_id")
            else f"{utils.get_chat_id(msg_obj)}:{msg_obj.id}",
        )

    async def restart_common(self, msg_obj: Union[InlineCall, Message]):
        if (
            hasattr(msg_obj, "form")
            and isinstance(msg_obj.form, dict)
            and "uid" in msg_obj.form
            and msg_obj.form["uid"] in self.inline._forms
            and "message" in self.inline._forms[msg_obj.form["uid"]]
        ):
            message = self.inline._forms[msg_obj.form["uid"]]["message"]
        else:
            message = msg_obj

        await self.process_restart_message(msg_obj)
        atexit.register(functools.partial(restart, *sys.argv[1:]))
        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)
        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()

        await message.client.disconnect()

    async def download_common(self):
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            r = origin.pull()
            new_commit = repo.head.commit
            for info in r:
                if info.old_commit:
                    for d in new_commit.diff(info.old_commit):
                        if d.b_path == "requirements.txt":
                            return True
            return False
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)
            return False

    @staticmethod
    def req_common():
        # Now we have downloaded new code, install requirements
        logger.debug("Installing new requirements...")
        try:
            subprocess.run(  # skipcq: PYL-W1510
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(
                        os.path.dirname(utils.get_base_dir()), "requirements.txt"
                    ),
                    "--user",
                ]
            )

        except subprocess.CalledProcessError:
            logger.exception("Req install failed")

    @loader.owner
    async def updatecmd(self, message: Message):
        """Downloads userbot updates"""
        try:
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("update_confirm"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_update"),
                            "callback": self.inline_update,
                        },
                        {"text": self.strings("cancel"), "callback": self.inline_close},
                    ],
                )
            ):
                raise
        except Exception:
            await self.inline_update(message)

    async def inline_update(
        self,
        msg_obj: Union[InlineCall, Message],
        hard: bool = False,
    ):
        # We don't really care about asyncio at this point, as we are shutting down
        if hard:
            os.system(f"cd {utils.get_base_dir()} && cd .. && git reset --hard HEAD")  # fmt: skip

        try:
            try:
                msg_obj = await utils.answer(msg_obj, self.strings("downloading"))
            except Exception:
                pass

            req_update = await self.download_common()

            try:
                msg_obj = await utils.answer(msg_obj, self.strings("installing"))
            except Exception:
                pass

            if req_update:
                self.req_common()

            try:
                msg_obj = await utils.answer(
                    msg_obj, self.strings("restarting_caption")
                )
            except Exception:
                pass

            await self.restart_common(msg_obj)
        except GitCommandError:
            if not hard:
                await self.inline_update(msg_obj, True)
                return

            logger.critical("Got update loop. Update manually via .terminal")
            return

    @loader.unrestricted
    async def sourcecmd(self, message: Message):
        """Links the source code of this project"""
        await utils.answer(
            message,
            self.strings("source").format(self.config["GIT_ORIGIN_URL"]),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

        if self.get("selfupdatemsg") is not None:
            try:
                await self.update_complete(client)
            except Exception:
                logger.exception("Failed to complete update!")

        self.set("selfupdatemsg", None)

        if self.get("do_not_create", False):
            return

        folders = await self._client(GetDialogFiltersRequest())

        if any(folder.title == "hikka" for folder in folders):
            return

        try:
            folder_id = (
                max(
                    folders,
                    key=lambda x: x.id,
                ).id
                + 1
            )
        except ValueError:
            folder_id = 2

        await self._client(
            UpdateDialogFilterRequest(
                folder_id,
                DialogFilter(
                    folder_id,
                    title="hikka",
                    pinned_peers=(
                        [
                            await self._client.get_input_entity(
                                self._client.loader.inline.bot_id
                            )
                        ]
                        if self._client.loader.inline.init_complete
                        else []
                    ),
                    include_peers=[
                        await self._client.get_input_entity(dialog.entity)
                        async for dialog in self._client.iter_dialogs(
                            None,
                            ignore_migrated=True,
                        )
                        if dialog.name
                        in {
                            "hikka-logs",
                            "hikka-onload",
                            "hikka-assets",
                            "hikka-backups",
                            "hikka-acc-switcher",
                        }
                        and dialog.is_channel
                        and (
                            dialog.entity.participants_count == 1
                            or dialog.entity.participants_count == 2
                            and dialog.name == "hikka-logs"
                        )
                        or (
                            self._client.loader.inline.init_complete
                            and dialog.entity.id == self._client.loader.inline.bot_id
                        )
                        or dialog.entity.id
                        in [1554874075, 1697279580, 1679998924]  # official hikka chats
                    ],
                    emoticon="🐱",
                    exclude_peers=[],
                    contacts=False,
                    non_contacts=False,
                    groups=False,
                    broadcasts=False,
                    bots=False,
                    exclude_muted=False,
                    exclude_read=False,
                    exclude_archived=False,
                ),
            )
        )

        self.set("do_not_create", True)

    async def update_complete(self, client):
        logger.debug("Self update successful! Edit message")
        msg = self.strings("success")
        ms = self.get("selfupdatemsg")

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            await asyncio.sleep(60)
            await self._client.delete_messages(chat_id, message_id)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=msg,
        )


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )
