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
from typing import Union

import git
from git import Repo, GitCommandError
from telethon.tl.types import Message
from aiogram.types import CallbackQuery

from .. import loader, utils

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

    def __init__(self):
        self.config = loader.ModuleConfig(
            "GIT_ORIGIN_URL",
            "https://github.com/hikariatama/Hikka",
            lambda m: self.strings("origin_cfg_doc", m),
        )

    @loader.owner
    async def restartcmd(self, message: Message) -> None:
        """Restarts the userbot"""
        if self.inline.init_complete and await self.inline.form(
            message=message,
            text=self.strings(
                "restart_confirm",
                message,
            ),
            reply_markup=[
                {
                    "text": self.strings("btn_restart"),
                    "callback": self.inline_restart,
                },
                {"text": self.strings("cancel"), "callback": self.inline_close},
            ],
        ):
            return

        message = await utils.answer(message, self.strings("restarting_caption"))
        if isinstance(message, (list, set, tuple)):
            message = message[0]

        await self.restart_common(message)

    async def inline_restart(self, call: CallbackQuery) -> None:
        await call.edit(self.strings("restarting_caption"))
        await self.restart_common(call)

    async def inline_close(self, call: CallbackQuery) -> None:
        await call.delete()

    async def prerestart_common(self, call: Union[CallbackQuery, Message]) -> None:
        logger.debug(f"Self-update. {sys.executable} -m {utils.get_base_dir()}")
        if hasattr(call, "inline_message_id"):
            self._db.set(__name__, "selfupdatemsg", call.inline_message_id)
        else:
            self._db.set(
                __name__, "selfupdatemsg", f"{utils.get_chat_id(call)}:{call.id}"
            )

    async def restart_common(self, call: Union[CallbackQuery, Message]) -> None:
        if (
            hasattr(call, "form")
            and isinstance(call.form, dict)
            and "uid" in call.form
            and call.form["uid"] in self.inline._forms
            and "message" in self.inline._forms[call.form["uid"]]
        ):
            message = self.inline._forms[call.form["uid"]]["message"]
        else:
            message = call

        await self.prerestart_common(call)
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
    def req_common() -> None:
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
    async def updatecmd(self, message: Message) -> None:
        """Downloads userbot updates"""
        if "--force" not in (utils.get_args_raw(message) or "") and self.inline.init_complete and await self.inline.form(
            message=message,
            text=self.strings(
                "update_confirm",
                message,
            ),
            reply_markup=[
                {
                    "text": self.strings("btn_update"),
                    "callback": self.inline_update,
                },
                {"text": self.strings("cancel"), "callback": self.inline_close},
            ],
        ):
            return

        await self.inline_update(message)

    async def inline_update(
        self,
        call: Union[CallbackQuery, Message],
        hard: bool = False,
    ) -> None:
        # We don't really care about asyncio at this point, as we are shutting down
        if hard:
            os.system(f"cd {utils.get_base_dir()} && cd .. && git reset --hard HEAD")  # fmt: skip

        try:
            try:
                await utils.answer(call, self.strings("downloading"))
            except Exception:
                pass

            req_update = await self.download_common()

            try:
                await utils.answer(call, self.strings("installing"))
            except Exception:
                pass

            if req_update:
                self.req_common()

            try:
                await utils.answer(call, self.strings("restarting_caption"))
            except Exception:
                pass

            await self.restart_common(call)
        except GitCommandError:
            if not hard:
                await self.inline_update(call, True)
                return

            logger.critical("Got update loop. Update manually via .terminal")
            return

    @loader.unrestricted
    async def sourcecmd(self, message: Message) -> None:
        """Links the source code of this project"""
        await utils.answer(
            message,
            self.strings("source", message).format(self.config["GIT_ORIGIN_URL"]),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._me = await client.get_me()
        self._client = client

        if db.get(__name__, "selfupdatemsg") is not None:
            try:
                await self.update_complete(client)
            except Exception:
                logger.exception("Failed to complete update!")

        self._db.set(__name__, "selfupdatemsg", None)

    async def update_complete(self, client):
        logger.debug("Self update successful! Edit message")
        msg = self.strings("success")
        ms = self._db.get(__name__, "selfupdatemsg")

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=msg,
            parse_mode="HTML",
        )


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )
