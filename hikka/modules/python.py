"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

import logging
import telethon
from meval import meval
from .. import loader, utils, main
from traceback import format_exc
import itertools
from types import ModuleType
from telethon.tl.types import Message
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


class FakeDbException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FakeDb:
    def __getattr__(self, *args, **kwargs):
        raise FakeDbException("Database read-write permission required")


@loader.tds
class PythonMod(loader.Module):
    """Evaluates python code"""

    strings = {
        "name": "Python",
        "eval": "<b>🎬 Code:</b>\n<code>{}</code>\n<b>🪄 Result:</b>\n<code>{}</code>",
        "err": "<b>🎬 Code:</b>\n<code>{}</code>\n\n<b>🚫 Error:</b>\n<code>{}</code>",
        "db_permission": "⚠️ <b>Do not use </b><code>db.set</code><b>, </b><code>db.get</code><b> and other db operations. You have core modules to control anything you want</b>\n\n<i>Theses commands may <b><u>crash</u></b> your userbot or even make it <b><u>unusable</u></b>! Do it on your own risk</i>\n\n<i>If you issue any errors after allowing this option, <b><u>you will not get any help in support chat</u></b>!</i>"
    }

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    def lookup(self, modname: str):
        return next(
            (
                mod
                for mod in self.allmodules.modules
                if mod.name.lower() == modname.lower()
            ),
            False,
        )

    @loader.owner
    async def evalcmd(self, message: Message) -> None:
        """Alias for .e command"""
        await self.ecmd(message)

    async def inline__close(self, call: CallbackQuery) -> None:
        await call.answer("Operation cancelled")
        await call.delete()

    async def inline__allow(self, call: CallbackQuery) -> None:
        await call.answer("Now you can access db through .e command", show_alert=True)
        self._db.set(main.__name__, "enable_db_eval", True)
        await call.delete()

    @loader.owner
    async def ecmd(self, message: Message) -> None:
        """Evaluates python code"""
        phone = self._client.phone
        ret = self.strings("eval", message)
        try:
            it = await meval(
                utils.get_args_raw(message), globals(), **await self.getattrs(message)
            )
        except FakeDbException:
            await self.inline.form(
                self.strings('db_permission'),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": "✅ Allow",
                            "callback": self.inline__allow,
                        },
                        {
                            "text": "🚫 Cancel",
                            "callback": self.inline__close
                        }
                    ]
                ]
            )
            return
        except Exception:
            exc = format_exc().replace(phone, "📵")
            await utils.answer(
                message,
                self.strings("err", message).format(
                    utils.escape_html(utils.get_args_raw(message)),
                    utils.escape_html(exc),
                ),
            )

            return
        ret = ret.format(
            utils.escape_html(utils.get_args_raw(message)), utils.escape_html(it)
        )
        ret = ret.replace(str(phone), "📵")
        await utils.answer(message, ret)

    async def getattrs(self, message):
        reply = await message.get_reply_message()
        return {
            **{
                "message": message,
                "client": self._client,
                "reply": reply,
                "r": reply,
                **self.get_sub(telethon.tl.types),
                **self.get_sub(telethon.tl.functions),
                "event": message,
                "chat": message.to_id,
                "telethon": telethon,
                "utils": utils,
                "main": main,
                "loader": loader,
                "f": telethon.tl.functions,
                "c": self._client,
                "m": message,
                "loader": loader,
                "lookup": self.lookup,
                "self": self,
            },
            **(
                {
                    "db": self._db,
                } if self._db.get(main.__name__, "enable_db_eval", False) else {
                    "db": FakeDb(),
                }
            )
        }

    def get_sub(self, it, _depth: int = 1) -> dict:
        """Get all callable capitalised objects in an object recursively, ignoring _*"""
        return {
            **dict(
                filter(
                    lambda x: x[0][0] != "_"
                    and x[0][0].upper() == x[0][0]
                    and callable(x[1]),
                    it.__dict__.items(),
                )
            ),
            **dict(
                itertools.chain.from_iterable(
                    [
                        self.get_sub(y[1], _depth + 1).items()
                        for y in filter(
                            lambda x: x[0][0] != "_"
                            and isinstance(x[1], ModuleType)
                            and x[1] != it
                            and x[1].__package__.rsplit(".", _depth)[0]
                            == "telethon.tl",
                            it.__dict__.items(),
                        )
                    ]
                )
            ),
        }
