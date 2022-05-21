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

import logging
from typing import Union, Any

from telethon.tl.types import Message

from .. import loader, utils, translations
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class HikkaConfigMod(loader.Module):
    """Interactive configurator for Hikka Userbot"""

    strings = {
        "name": "HikkaConfig",
        "configure": "🎚 <b>Here you can configure your modules' configs</b>",
        "configuring_mod": "🎚 <b>Choose config option for mod</b> <code>{}</code>",
        "configuring_option": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Default: </b><code>{}</code>\n\n<b>Current: </b><code>{}</code>\n\n{}",
        "option_saved": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code><b> saved!</b>\n<b>Current: </b><code>{}</code>",
        "args": "🚫 <b>You specified incorrect args</b>",
        "no_mod": "🚫 <b>Module doesn't exist</b>",
        "no_option": "🚫 <b>Configuration option doesn't exist</b>",
        "validation_error": "🚫 <b>You entered incorrect config value. \nError: {}</b>",
        "try_again": "🔁 Try again",
        "typehint": "🕵️ <b>Must be a {}</b>",
        "set": "set",
    }

    strings_ru = {
        "configure": "🎚 <b>Здесь можно управлять настройками модулей</b>",
        "configuring_mod": "🎚 <b>Выбери параметр для модуля</b> <code>{}</code>",
        "configuring_option": "🎚 <b>Управление параметром </b><code>{}</code><b> модуля </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Стандартное: </b><code>{}</code>\n\n<b>Текущее: </b><code>{}</code>\n\n{}",
        "option_saved": "🎚 <b>Параметр </b><code>{}</code><b> модуля </b><code>{}</code><b> сохранен!</b>\n<b>Текущее значение: </b><code>{}</code>",
        "_cmd_doc_config": "Настройки модулей",
        "_cmd_doc_fconfig": "<имя модуля> <имя конфига> <значение> - Расшифровывается как ForceConfig - Принудительно устанавливает значение в конфиге, если это не удалось сделать через inline бота",
        "_cls_doc": "Интерактивный конфигуратор Hikka",
        "args": "🚫 <b>Ты указал неверные аргументы</b>",
        "no_mod": "🚫 <b>Модуль не существует</b>",
        "no_option": "🚫 <b>У модуля нет такого значения конфига</b>",
        "validation_error": "🚫 <b>Введено некорректное значение конфига. \nОшибка: {}</b>",
        "try_again": "🔁 Попробовать еще раз",
        "typehint": "🕵️ <b>Должно быть {}</b>",
        "set": "поставить",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._forms = {}

    @staticmethod
    async def inline__close(call: InlineCall):
        await call.delete()

    @staticmethod
    def prep_value(value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, list) and value:
            return ", ".join(list(map(str, value)))

        return value

    async def inline__set_config(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
    ):
        try:
            self.lookup(mod).config[option] = query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                utils.escape_html(self.prep_value(self.lookup(mod).config[option])),
            ),
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

    async def inline__set_bool(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                },
            )
            return

        validator = self.lookup(mod).config._config[option].validator
        doc = utils.escape_html(
            validator.doc.get(
                self._db.get(translations.__name__, "lang", "en"), validator.doc["en"]
            )
        )

        current = self.lookup(mod).config[option]

        await call.edit(
            self.strings("configuring_option").format(
                utils.escape_html(option),
                utils.escape_html(mod),
                utils.escape_html(self.lookup(mod).config.getdoc(option)),
                utils.escape_html(
                    self.prep_value(self.lookup(mod).config.getdef(option))
                ),
                utils.escape_html(self.prep_value(current)),
                self.strings("typehint").format(doc) if doc else "",
            ),
            reply_markup=[
                [
                    *(
                        [
                            {
                                "text": f"✅ {self.strings('set')} `True`",
                                "callback": self.inline__set_bool,
                                "args": (mod, option, True),
                            }
                        ]
                        if not current
                        else [
                            {
                                "text": f"❌ {self.strings('set')} `False`",
                                "callback": self.inline__set_bool,
                                "args": (mod, option, False),
                            }
                        ]
                    ),
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

        await call.answer("✅")

    async def inline__configure_option(
        self,
        call: InlineCall,
        mod: str,
        config_opt: str,
    ):
        module = self.lookup(mod)
        try:
            validator = module.config._config[config_opt].validator
            doc = utils.escape_html(
                validator.doc.get(
                    self._db.get(translations.__name__, "lang", "en"),
                    validator.doc["en"],
                )
            )
        except Exception:
            doc = None
            validator = None
        else:
            if validator.internal_id == "Boolean":
                await call.edit(
                    self.strings("configuring_option").format(
                        utils.escape_html(config_opt),
                        utils.escape_html(mod),
                        utils.escape_html(module.config.getdoc(config_opt)),
                        utils.escape_html(
                            self.prep_value(module.config.getdef(config_opt))
                        ),
                        utils.escape_html(self.prep_value(module.config[config_opt])),
                        self.strings("typehint").format(doc) if doc else "",
                    ),
                    reply_markup=[
                        [
                            *(
                                [
                                    {
                                        "text": f"✅ {self.strings('set')} `True`",
                                        "callback": self.inline__set_bool,
                                        "args": (mod, config_opt, True),
                                    }
                                ]
                                if not module.config[config_opt]
                                else [
                                    {
                                        "text": f"❌ {self.strings('set')} `False`",
                                        "callback": self.inline__set_bool,
                                        "args": (mod, config_opt, False),
                                    }
                                ]
                            ),
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
                return

        await call.edit(
            self.strings("configuring_option").format(
                utils.escape_html(config_opt),
                utils.escape_html(mod),
                utils.escape_html(module.config.getdoc(config_opt)),
                utils.escape_html(self.prep_value(module.config.getdef(config_opt))),
                utils.escape_html(self.prep_value(module.config[config_opt])),
                self.strings("typehint").format(doc) if doc else "",
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
            if hasattr(mod, "config") and callable(mod.strings)
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

    async def fconfigcmd(self, message: Message):
        """<module_name> <propery_name> <config_value> - Stands for ForceConfig - Set the config value if it is not possible using default method"""
        args = utils.get_args_raw(message).split(maxsplit=2)

        if len(args) < 3:
            await utils.answer(message, self.strings("args"))
            return

        mod, option, value = args

        instance = self.lookup(mod)
        if not instance:
            await utils.answer(message, self.strings("no_mod"))
            return

        if option not in instance.config:
            await utils.answer(message, self.strings("no_option"))
            return

        instance.config[option] = value
        await utils.answer(
            message,
            self.strings("option_saved").format(
                utils.escape_html(option),
                utils.escape_html(mod),
                utils.escape_html(self.prep_value(instance.config[option])),
            ),
        )
