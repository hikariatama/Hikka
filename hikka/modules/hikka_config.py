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

from .. import loader, utils
from ..inline.types import InlineCall
from telethon.tl.types import Message
import logging
from typing import Union
import ast

logger = logging.getLogger(__name__)


@loader.tds
class HikkaConfigMod(loader.Module):
    """Interactive configurator for Hikka Userbot"""

    strings = {
        "name": "HikkaConfig",
        "configure": "🎚 <b>Here you can configure your modules' configs</b>",
        "configuring_mod": "🎚 <b>Choose config option for mod</b> <code>{}</code>",
        "configuring_option": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Default: </b><code>{}</code>\n\n<b>Current: </b><code>{}</code>",
        "option_saved": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code><b> saved!</b>\n<b>Current: </b><code>{}</code>",
    }

    strings_ru = {
        "configure": "🎚 <b>Здесь можно управлять настройками модулей</b>",
        "configuring_mod": "🎚 <b>Выбери параметр для модуля</b> <code>{}</code>",
        "configuring_option": "🎚 <b>Управление параметром </b><code>{}</code><b> модуля </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Стандартное значение: </b><code>{}</code>\n\n<b>Текущее значение: </b><code>{}</code>",
        "option_saved": "🎚 <b>Параметр </b><code>{}</code><b> модуля </b><code>{}</code><b> сохранен!</b>\n<b>Текущее значение: </b><code>{}</code>",
        "_cmd_doc_config": "Настройки модулей",
        "_cls_doc": "Интерактивный конфигуратор Hikka",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._bot_id = (await self.inline.bot.get_me()).id
        self._forms = {}

    @staticmethod
    async def inline__close(call: InlineCall):  # noqa
        await call.delete()

    async def inline__set_config(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
    ):  # noqa
        for module in self.allmodules.modules:
            if module.strings("name") == mod:
                module.config[option] = query
                if query:
                    try:
                        query = ast.literal_eval(query)
                    except (ValueError, SyntaxError):
                        pass

                    self._db.setdefault(
                        module.__class__.__name__, {}
                    ).setdefault("__config__", {})[option] = query
                else:
                    try:
                        del self._db.setdefault(
                            module.__class__.__name__, {}
                        ).setdefault("__config__", {})[option]
                    except KeyError:
                        pass

                self.allmodules.send_config_one(module, self._db, skip_hook=True)
                self._db.save()

        await call.edit(
            self.strings("option_saved").format(mod, option, query),
            reply_markup=[
                [
                    {
                        "text": "👈 Back",
                        "callback": self.inline__configure,
                        "args": (mod,),
                    },
                    {"text": "🚫 Close", "callback": self.inline__close},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__configure_option(
        self,
        call: InlineCall,
        mod: str,
        config_opt: str,
    ):  # noqa
        for module in self.allmodules.modules:
            if module.strings("name") == mod:
                await call.edit(
                    self.strings("configuring_option").format(
                        utils.escape_html(config_opt),
                        utils.escape_html(mod),
                        utils.escape_html(module.config.getdoc(config_opt)),
                        utils.escape_html(module.config.getdef(config_opt)),
                        utils.escape_html(module.config[config_opt]),
                    ),
                    reply_markup=[
                        [
                            {
                                "text": "✍️ Enter value",
                                "input": "✍️ Enter new configuration value for this option",
                                "handler": self.inline__set_config,
                                "args": (mod, config_opt, call.inline_message_id),
                            }
                        ],
                        [
                            {
                                "text": "👈 Back",
                                "callback": self.inline__configure,
                                "args": (mod,),
                            },
                            {"text": "🚫 Close", "callback": self.inline__close},
                        ],
                    ],
                )

    async def inline__configure(self, call: InlineCall, mod: str):
        btns = []
        for module in self.allmodules.modules:
            if module.strings("name") == mod:
                for param in module.config:
                    btns += [
                        {
                            "text": param,
                            "callback": self.inline__configure_option,
                            "args": (mod, param),
                        }
                    ]

        await call.edit(
            self.strings("configuring_mod").format(utils.escape_html(mod)),
            reply_markup=list(utils.chunks(btns, 2))
            + [
                [
                    {"text": "👈 Back", "callback": self.inline__global_config},
                    {"text": "🚫 Close", "callback": self.inline__close},
                ]
            ],
        )

    async def inline__global_config(
        self,
        call: Union[Message, InlineCall],
    ):
        to_config = [
            mod.strings("name")
            for mod in self.allmodules.modules
            if hasattr(mod, "config")
        ]
        kb = []
        for mod_row in utils.chunks(to_config, 3):
            row = [
                {"text": btn, "callback": self.inline__configure, "args": (btn,)}
                for btn in mod_row
            ]
            kb += [row]

        kb += [[{"text": "🚫 Close", "callback": self.inline__close}]]

        if isinstance(call, Message):
            await self.inline.form(
                self.strings("configure"),
                reply_markup=kb,
                message=call,
            )
        else:
            await call.edit(self.strings("configure"), reply_markup=kb)

    async def configcmd(self, message: Message):
        """Configure modules"""
        await self.inline__global_config(message)

    async def watcher(self, message: Message):
        if (
            not getattr(message, "out", False)
            or not getattr(message, "via_bot_id", False)
            or message.via_bot_id != self._bot_id
            or "This message is gonna be deleted..."
            not in getattr(message, "raw_text", "")
        ):
            return

        await message.delete()
