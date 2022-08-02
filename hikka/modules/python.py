#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import itertools
import logging
import sys
from types import ModuleType
import os
from typing import Any

import telethon
from meval import meval
from telethon.errors.rpcerrorlist import MessageIdInvalidError
from telethon.tl.types import Message

from .. import loader, main, utils
from ..inline.types import InlineCall
from ..log import HikkaException

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
        "err": "<b>🎬 Code:</b>\n<code>{}</code>\n\n<b>🚫 Error:</b>\n{}",
        "db_permission": (
            "⚠️ <b>Do not use </b><code>db.set</code><b>, </b><code>db.get</code><b> "
            "and other db operations. You have core modules to control anything you "
            "want</b>\n\n<i>Theses commands may <b><u>crash</u></b> your userbot or "
            "even make it <b><u>unusable</u></b>! Do it on your own risk</i>\n\n<i>"
            "If you issue any errors after allowing this option, <b><u>you will not "
            "get any help in support chat</u></b>!</i>"
        ),
    }

    strings_ru = {
        "eval": "<b>🎬 Код:</b>\n<code>{}</code>\n<b>🪄 Результат:</b>\n<code>{}</code>",
        "err": "<b>🎬 Код:</b>\n<code>{}</code>\n\n<b>🚫 Ошибка:</b>\n{}",
        "db_permission": (
            "⚠️ <b>Не используй </b><code>db.set</code><b>, </b><code>db.get</code><b>"
            " и другие операции с базой данных. У тебя есть встроенные модуля для"
            " управления ей</b>\n\n<i>Эти команды могут <b><u>нарушить работу</u></b>"
            " юзербота, или вообще <b><u>сломать</u></b> его! Используй эти команды на"
            " свой страх и риск</i>\n\n<i>Если появятся какие-либо проблемы, вызванные"
            " после этой команды, <b><u>ты не получишь помощи в чате</u></b>!</i>"
        ),
        "_cmd_doc_eval": "Алиас для команды .e",
        "_cmd_doc_e": "Выполняет Python кодировка",
        "_cls_doc": "Выполняет Python код",
    }

    async def client_ready(self, client, _):
        self._phone = (await client.get_me()).phone

    @loader.owner
    async def evalcmd(self, message: Message):
        """Alias for .e command"""
        await self.ecmd(message)

    async def inline__allow(self, call: InlineCall):
        await call.answer("Now you can access db through .e command", show_alert=True)
        self._db.set(main.__name__, "enable_db_eval", True)
        await call.delete()

    @loader.owner
    async def ecmd(self, message: Message):
        """Evaluates python code"""
        ret = self.strings("eval")
        try:
            result = await meval(
                utils.get_args_raw(message),
                globals(),
                **await self.getattrs(message),
            )
        except FakeDbException:
            await self.inline.form(
                self.strings("db_permission"),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": "✅ Allow",
                            "callback": self.inline__allow,
                        },
                        {"text": "🚫 Cancel", "action": "close"},
                    ]
                ],
            )
            return
        except Exception:
            item = HikkaException.from_exc_info(*sys.exc_info())
            exc = (
                "\n<b>🪐 Full stack:</b>\n\n"
                + "\n".join(item.full_stack.splitlines()[:-1])
                + "\n\n"
                + "😵 "
                + item.full_stack.splitlines()[-1]
            )
            exc = exc.replace(str(self._phone), "📵")

            if os.environ.get("DATABASE_URL"):
                exc = exc.replace(
                    os.environ.get("DATABASE_URL"),
                    "postgre://**************************",
                )

            if os.environ.get("hikka_session"):
                exc = exc.replace(
                    os.environ.get("hikka_session"),
                    "StringSession(**************************)",
                )

            await utils.answer(
                message,
                self.strings("err").format(
                    utils.escape_html(utils.get_args_raw(message)),
                    exc,
                ),
            )

            return

        if callable(getattr(result, "stringify", None)):
            with contextlib.suppress(Exception):
                result = str(result.stringify())

        result = str(result)

        ret = ret.format(
            utils.escape_html(utils.get_args_raw(message)),
            utils.escape_html(result),
        )

        ret = ret.replace(str(self._phone), "📵")

        if postgre := os.environ.get("DATABASE_URL") or main.get_config_key(
            "postgre_uri"
        ):
            ret = ret.replace(postgre, "postgre://**************************")

        if redis := os.environ.get("REDIS_URL") or main.get_config_key("redis_uri"):
            ret = ret.replace(redis, "redis://**************************")

        if os.environ.get("hikka_session"):
            ret = ret.replace(
                os.environ.get("hikka_session"),
                "StringSession(**************************)",
            )

        with contextlib.suppress(MessageIdInvalidError):
            await utils.answer(message, ret)

    async def getattrs(self, message: Message) -> dict:
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
                "lookup": self.lookup,
                "self": self,
            },
            **(
                {
                    "db": self._db,
                }
                if self._db.get(main.__name__, "enable_db_eval", False)
                else {
                    "db": FakeDb(),
                }
            ),
        }

    def get_sub(self, obj: Any, _depth: int = 1) -> dict:
        """Get all callable capitalised objects in an object recursively, ignoring _*"""
        return {
            **dict(
                filter(
                    lambda x: x[0][0] != "_"
                    and x[0][0].upper() == x[0][0]
                    and callable(x[1]),
                    obj.__dict__.items(),
                )
            ),
            **dict(
                itertools.chain.from_iterable(
                    [
                        self.get_sub(y[1], _depth + 1).items()
                        for y in filter(
                            lambda x: x[0][0] != "_"
                            and isinstance(x[1], ModuleType)
                            and x[1] != obj
                            and x[1].__package__.rsplit(".", _depth)[0]
                            == "telethon.tl",
                            obj.__dict__.items(),
                        )
                    ]
                )
            ),
        }
