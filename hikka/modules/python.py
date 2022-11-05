#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import itertools
import os
import sys
import typing
from types import ModuleType

import telethon
from meval import meval
from telethon.errors.rpcerrorlist import MessageIdInvalidError
from telethon.tl.types import Message

from .. import loader, main, utils
from ..log import HikkaException


@loader.tds
class PythonMod(loader.Module):
    """Evaluates python code"""

    strings = {
        "name": "Python",
        "eval": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Code:</b>\n<code>{}</code>\n<emoji"
            " document_id=5197688912457245639>✅</emoji><b>"
            " Result:</b>\n<code>{}</code>"
        ),
        "err": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Code:</b>\n<code>{}</code>\n\n<emoji"
            " document_id=5312526098750252863>🚫</emoji><b> Error:</b>\n{}"
        ),
    }

    strings_ru = {
        "eval": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Код:</b>\n<code>{}</code>\n<emoji"
            " document_id=5197688912457245639>✅</emoji><b>"
            " Результат:</b>\n<code>{}</code>"
        ),
        "err": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Код:</b>\n<code>{}</code>\n\n<emoji"
            " document_id=5312526098750252863>🚫</emoji><b> Ошибка:</b>\n{}"
        ),
        "_cls_doc": "Выполняет Python код",
    }

    strings_de = {
        "eval": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Code:</b>\n<code>{}</code>\n<emoji"
            " document_id=5197688912457245639>✅</emoji><b>"
            " Resultat:</b>\n<code>{}</code>"
        ),
        "err": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Code:</b>\n<code>{}</code>\n\n<emoji"
            " document_id=5312526098750252863>🚫</emoji><b> Fehler:</b>\n{}"
        ),
        "_cls_doc": "Führt Python Code aus",
    }

    strings_tr = {
        "eval": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Kod:</b>\n<code>{}</code>\n<emoji"
            " document_id=5197688912457245639>✅</emoji><b>"
            " Sonuç:</b>\n<code>{}</code>"
        ),
        "err": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Kod:</b>\n<code>{}</code>\n\n<emoji"
            " document_id=5312526098750252863>🚫</emoji><b> Hata:</b>\n{}"
        ),
        "_cls_doc": "Python kodunu çalıştırır",
    }

    strings_uz = {
        "eval": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Kod:</b>\n<code>{}</code>\n<emoji"
            " document_id=5197688912457245639>✅</emoji><b>"
            " Natija:</b>\n<code>{}</code>"
        ),
        "err": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Kod:</b>\n<code>{}</code>\n\n<emoji"
            " document_id=5312526098750252863>🚫</emoji><b> Xato:</b>\n{}"
        ),
        "_cls_doc": "Python kodini ishga tushiradi",
    }

    strings_es = {
        "eval": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Código:</b>\n<code>{}</code>\n<emoji"
            " document_id=5197688912457245639>✅</emoji><b>"
            " Resultado:</b>\n<code>{}</code>"
        ),
        "err": (
            "<emoji document_id=4985626654563894116>💻</emoji><b>"
            " Código:</b>\n<code>{}</code>\n\n<emoji"
            " document_id=5312526098750252863>🚫</emoji><b> Error:</b>\n{}"
        ),
        "_cls_doc": "Ejecuta código Python",
    }

    @loader.owner
    @loader.command(
        ru_doc="Алиас для команды .e",
        de_doc="Alias für den Befehl .e",
        tr_doc="Komut .e için takma ad",
        uz_doc="Buyruq .e uchun alohida nom",
        es_doc="Alias para el comando .e",
    )
    async def eval(self, message: Message):
        """Alias for .e command"""
        await self.e(message)

    @loader.owner
    @loader.command(
        ru_doc="Выполняет Python код",
        de_doc="Führt Python Code aus",
        tr_doc="Python kodu çalıştırır",
        uz_doc="Python kodini ishga tushiradi",
        es_doc="Ejecuta código Python",
    )
    async def e(self, message: Message):
        """Evaluates python code"""
        ret = self.strings("eval")
        try:
            result = await meval(
                utils.get_args_raw(message),
                globals(),
                **await self.getattrs(message),
            )
        except Exception:
            item = HikkaException.from_exc_info(*sys.exc_info())
            exc = (
                "\n<b>🪐 Full stack:</b>\n\n"
                + "\n".join(item.full_stack.splitlines()[:-1])
                + "\n\n"
                + "🚫 "
                + item.full_stack.splitlines()[-1]
            )
            exc = exc.replace(str(self._client.hikka_me.phone), "📵")

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

        ret = ret.replace(str(self._client.hikka_me.phone), "📵")

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
                "db": self.db,
            },
        }

    def get_sub(self, obj: typing.Any, _depth: int = 1) -> dict:
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
