# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import difflib
import inspect
import logging

from telethon.extensions.html import CUSTOM_EMOJIS
from telethon.tl.types import Message

from .. import loader, utils
from ..compat.dragon import DRAGON_EMOJI
from ..types import DragonModule

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """Shows help for modules and commands"""

    strings = {
        "name": "Help",
        "undoc": "🦥 No docs",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} mods available,"
            " {} hidden:</b>"
        ),
        "no_mod": "🚫 <b>Specify module to hide</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} modules hidden,"
            " {} modules shown:</b>\n{}\n{}"
        ),
        "support": (
            "{} <b>Link to</b> <a href='https://t.me/hikka_talks'>support chat</a></b>"
        ),
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Userbot is not"
            " fully loaded, so not all modules are shown</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>No exact match"
            " occured, so the closest result is shown instead</b>"
        ),
        "request_join": "You requested link for Hikka support chat",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>This is a core"
            " module. You can't unload it nor replace</b>"
        ),
    }

    strings_ru = {
        "undoc": "🦥 Нет описания",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} модулей доступно,"
            " {} скрыто:</b>"
        ),
        "no_mod": "🚫 <b>Укажи модуль(-и), которые нужно скрыть</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} модулей скрыто,"
            " {} модулей показано:</b>\n{}\n{}"
        ),
        "support": (
            "{} <b>Ссылка на</b> <a href='https://t.me/hikka_talks'>чат помощи</a></b>"
        ),
        "_cls_doc": "Показывает помощь по модулям",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Юзербот еще не"
            " загрузился полностью, поэтому показаны не все модули</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Точного совпадения"
            " не нашлось, поэтому было выбрано наиболее подходящее</b>"
        ),
        "request_join": "Вы запросили ссылку на чат помощи Hikka",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Это встроенный"
            " модуль. Вы не можете его выгрузить или заменить</b>"
        ),
    }

    strings_it = {
        "undoc": "🦥 Nessuna documentazione",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} moduli disponibili,"
            " {} nascosti:</b>"
        ),
        "no_mod": "🚫 <b>Specifica il modulo da nascondere</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} moduli nascosti,"
            " {} moduli mostrati:</b>\n{}\n{}"
        ),
        "support": (
            "{} <b>Link al</b> <a href='https://t.me/hikka_talks'>chat di"
            " supporto</a></b>"
        ),
        "_cls_doc": "Mostra l'aiuto per i moduli",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>L'userbot non è"
            " stato completamente caricato, quindi non tutti i moduli sono mostrati</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Nessuna"
            " corrispondenza esatta è stata trovata, quindi è stato mostrato il"
            " risultato più simile</b>"
        ),
        "request_join": "Hai richiesto il link per il gruppo di supporto Hikka",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Questo è un modulo"
            " principale. Non puoi scaricarlo né sostituirlo</b>"
        ),
    }

    strings_de = {
        "undoc": "🦥 Keine Dokumentation",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} Module verfügbar,"
            " {} versteckt:</b>"
        ),
        "no_mod": "🚫 <b>Gib das Modul an, das du verstecken willst</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} Module versteckt,"
            " {} Module angezeigt:</b>\n{}\n{}"
        ),
        "support": (
            "{} <b>Link zum</b> <a href='https://t.me/hikka_talks'>Supportchat</a></b>"
        ),
        "_cls_doc": "Zeigt Hilfe zu Modulen an",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Der Userbot ist noch"
            " nicht vollständig geladen, daher werden nicht alle Module angezeigt</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Es wurde kein exakter"
            " Treffer gefunden, daher wird das nächstbeste Ergebnis angezeigt</b>"
        ),
        "request_join": "Du hast den Link zum Supportchat angefordert",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Dies ist ein"
            " eingebauter Modul. Du kannst ihn nicht entladen oder ersetzen</b>"
        ),
    }

    strings_tr = {
        "undoc": "🦥 Dokümantasyon yok",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} adet modül mevcut,"
            " {} gizli:</b>"
        ),
        "no_mod": "🚫 <b>Gizlemek istediğin modülü belirt</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} adet modül"
            " gizlendi, {} adet modül gösterildi:</b>\n{}\n{}"
        ),
        "support": "{} <b><a href='https://t.me/hikka_talks'>Destek sohbeti</a></b>",
        "_cls_doc": "Modül yardımını gösterir",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Kullanıcı botu"
            " henüz tam olarak yüklenmediğinden, tüm modüller görüntülenmez</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Herhangi bir"
            " eşleşme bulunamadığından, en uygun sonuç gösterildi</b>"
        ),
        "request_join": "Hikka Destek sohbetinin davet bağlantısını istediniz",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Bu dahili"
            " b,r modül. Bu modülü kaldıramaz veya değiştiremezsin</b>"
        ),
    }

    strings_uz = {
        "undoc": "🦥 Hujjatlanmagan",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} Umumiy modullar,"
            " yashirin {}:</b>"
        ),
        "no_mod": "🚫 <b>Yashirish uchun modul kiriting</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} yashirin,"
            " {} modullar ko'rsatilgan:</b>\n{}\n{}"
        ),
        "support": "{} <b><a href='https://t.me/hikka_talks'>Yordam chat</a></b>",
        "_cls_doc": "Modul yordamini ko'rsatadi",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Foydalanuvchi boti"
            " hali to'liq yuklanmaganligi sababli, barcha modullar ko'rsatilmaydi</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Hech qanday moslik"
            " topilmadi, shuning uchun eng mos natija ko'rsatildi</b>"
        ),
        "request_join": "Siz yordam chat havolasini so'radingiz",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Bu bir qo'shimcha"
            " modul, uni o'chirib yoki o'zgartirib bo'lmaysiz</b>"
        ),
    }

    strings_es = {
        "undoc": "🦥 Sin documentar",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} módulos,"
            " {} ocultos:</b>"
        ),
        "no_mod": "🚫 <b>Por favor, introduce el módulo que deseas ocultar</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} ocultos,"
            " {} módulos mostrados:</b>\n{}\n{}"
        ),
        "support": "{} <b><a href='https://t.me/hikka_talks'>Chat de soporte</a></b>",
        "_cls_doc": "Muestra la ayuda del módulo",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>El bot no se ha"
            " cargado por completoaún, por lo que no se muestran todos los módulos</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>No se encontraron"
            " resultados exactos, por lo que se muestran los resultados más"
            " relevantes</b>"
        ),
        "request_join": "Se ha solicitado el enlace al chat de soporte",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Este es un módulo"
            " corazón, por loque no se puede eliminar o modificar</b>"
        ),
    }

    strings_kk = {
        "undoc": "🦥 Құжатталмаған",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} қосымша модуль,"
            " {} жасырын:</b>"
        ),
        "no_mod": "🚫 <b>Жасыру үшін модуль енгізіңіз</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} жасырын,"
            " {} модуль көрсетілді:</b>\n{}\n{}"
        ),
        "support": "{} <b><a href='https://t.me/hikka_talks'>Көмек сөйлесу</a></b>",
        "_cls_doc": "Модуль көмектерін көрсетеді",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Пайдаланушы боты"
            " әлде бірінші бетіне жүктелгеннен кейін, барлық модулдер көрсетілмейді</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Ешқандай"
            " таптырылмаған нәтиже жоқ, сондықтан ең қанағаттары көрсетілді</b>"
        ),
        "request_join": "Сіз көмек сөйлесудің сілтемесін сұрағансыз",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Бұл қосымша модуль,"
            " оны жою немесе өзгерту мүмкін емес</b>"
        ),
    }

    strings_tt = {
        "undoc": "🦥 Тасвирлау юк",
        "all_header": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} модульләр бар,"
            " {} яшерелгән:</b>"
        ),
        "no_mod": "🚫 <b>Яшерергә кирәк булган модульне күрсәтегез (- һәм)</b>",
        "hidden_shown": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>{} модуль яшерелгән,"
            " {} модуль яшерелгән:</b>\n{}\n{}"
        ),
        "support": (
            "{} <b>Сылтама</b> <href='https://t.me/hikka_talks'>ярдәм чаты</a></b>"
        ),
        "_cls_doc": "Модульләр буенча ярдәм күрсәтә",
        "partial_load": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Юзербот әле тулысынча"
            " йөкләнмәгән, шуңа күрә барлык модульләр дә күрсәтелмәгән</b>"
        ),
        "not_exact": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Төгәл матч табылмады,"
            " шуңа күрә иң яхшысы сайланды</b>"
        ),
        "request_join": "Сез Hikka ярдәм чатына сылтама сорадыгыз",
        "core_notice": (
            "<emoji document_id=5312383351217201533>☝️</emoji> <b>Бу урнаштырылган"
            " модуль. Сез аны бушатырга яки алыштыра алмыйсыз</b>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "core_emoji",
                "▪️",
                lambda: "Core module bullet",
                validator=loader.validators.Emoji(length=1),
            ),
            loader.ConfigValue(
                "hikka_emoji",
                "🌘",
                lambda: "Hikka-only module bullet",
                validator=loader.validators.Emoji(length=1),
            ),
            loader.ConfigValue(
                "plain_emoji",
                "▫️",
                lambda: "Plain module bullet",
                validator=loader.validators.Emoji(length=1),
            ),
            loader.ConfigValue(
                "empty_emoji",
                "🙈",
                lambda: "Empty modules bullet",
                validator=loader.validators.Emoji(length=1),
            ),
        )

    @loader.command(
        ru_doc=(
            "<модуль или модули> - Спрятать модуль(-и) из помощи\n*Разделяй модули"
            " пробелами"
        ),
        it_doc=(
            "<module o moduli> - Nascondi il modulo (- i) dalla guida\n*Separa i moduli"
            " spazi"
        ),
        de_doc=(
            "<Modul oder Module> - Verstecke Modul(-e) aus der Hilfe\n*Modulnamen"
            " mit Leerzeichen trennen"
        ),
        tr_doc=(
            "<modül veya modüller> - Yardımdan modül(-ler) gizle\n*Modülleri boşluk"
            " ile ayır"
        ),
        uz_doc=(
            "<modul yoki modullar> - Modul(-lar) yordamidan yashirish\n*Modullarni"
            " bo'sh joy bilan ajratish"
        ),
        es_doc=(
            "<módulo o módulos> - Oculta el módulo (-s) de la ayuda\n*Separa los"
            " módulos con espacios"
        ),
        kk_doc=(
            "<модуль немесе модульдер> - Анықтамадан модульді (-дерді)"
            " жасыру\n*Модульдерді бос қойып айыр"
        ),
    )
    async def helphide(self, message: Message):
        """<module or modules> - Hide module(-s) from help
        *Split modules by spaces"""
        modules = utils.get_args(message)
        if not modules:
            await utils.answer(message, self.strings("no_mod"))
            return

        modules = list(
            filter(lambda module: self.lookup(module, include_dragon=True), modules)
        )
        currently_hidden = self.get("hide", [])
        hidden, shown = [], []
        for module in modules:
            module = self.lookup(module, include_dragon=True)
            module = (
                module.name
                if isinstance(module, DragonModule)
                else module.__class__.__name__
            )
            if module in currently_hidden:
                currently_hidden.remove(module)
                shown += [module]
            else:
                currently_hidden += [module]
                hidden += [module]

        self.set("hide", currently_hidden)

        await utils.answer(
            message,
            self.strings("hidden_shown").format(
                len(hidden),
                len(shown),
                "\n".join([f"👁‍🗨 <i>{m}</i>" for m in hidden]),
                "\n".join([f"👁 <i>{m}</i>" for m in shown]),
            ),
        )

    def find_aliases(self, command: str) -> list:
        """Find aliases for command"""
        aliases = []
        _command = self.allmodules.commands[command]
        if getattr(_command, "alias", None) and not (
            aliases := getattr(_command, "aliases", None)
        ):
            aliases = [_command.alias]

        return aliases or []

    async def modhelp(self, message: Message, args: str):
        module = self.lookup(args, include_dragon=True)

        if not module:
            cmd = args.lower().strip(self.get_prefix())
            if method := self.allmodules.dispatch(cmd)[1]:
                module = method.__self__

        exact = True
        if not module:
            module = self.lookup(
                next(
                    (
                        reversed(
                            sorted(
                                [
                                    module.strings["name"]
                                    for module in self.allmodules.modules
                                ],
                                key=lambda x: difflib.SequenceMatcher(
                                    None,
                                    args.lower(),
                                    x,
                                ).ratio(),
                            )
                        )
                    ),
                    None,
                )
            )

            exact = False

        is_dragon = isinstance(module, DragonModule)

        try:
            name = module.strings("name")
        except (KeyError, AttributeError):
            name = getattr(module, "name", "ERROR")

        _name = (
            f"{utils.escape_html(name)} (v{module.__version__[0]}.{module.__version__[1]}.{module.__version__[2]})"
            if hasattr(module, "__version__")
            else utils.escape_html(name)
        )

        reply = f'{DRAGON_EMOJI if is_dragon else "<emoji document_id=5188377234380954537>🌘</emoji>"} <b>{_name}</b>:'
        if module.__doc__:
            reply += (
                "<i>\n<emoji document_id=5787544344906959608>ℹ️</emoji> "
                + utils.escape_html(inspect.getdoc(module))
                + "\n</i>"
            )

        commands = (
            module.commands
            if is_dragon
            else {
                name: func
                for name, func in module.commands.items()
                if await self.allmodules.check_security(message, func)
            }
        )

        if hasattr(module, "inline_handlers") and not is_dragon:
            for name, fun in module.inline_handlers.items():
                reply += f'\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{f"@{self.inline.bot_username} {name}"}</code> {utils.escape_html(inspect.getdoc(fun)) if fun.__doc__ else self.strings("undoc")}'

        for name, fun in commands.items():
            reply += f'''\n<emoji document_id=4971987363145188045>▫️</emoji> <code>{self.get_prefix("dragon" if is_dragon else None)}{name}</code>{f""" ({", ".join(f'<code>{self.get_prefix("dragon" if is_dragon else None)}{alias}</code>' for alias in self.find_aliases(name))})""" if self.find_aliases(name) else ""} {utils.escape_html(fun) if is_dragon else utils.escape_html(inspect.getdoc(fun)) if fun.__doc__ else self.strings("undoc")}'''

        await utils.answer(
            message,
            reply
            + ("" if exact else f"\n\n{self.strings('not_exact')}")
            + (
                f"\n\n{self.strings('core_notice')}"
                if module.__origin__.startswith("<core")
                else ""
            ),
        )

    @loader.unrestricted
    @loader.command(
        ru_doc="[модуль] [-f] - Показать помощь",
        it_doc="[modulo] [-f] - Mostra l'aiuto",
        de_doc="[Modul] [-f] - Hilfe anzeigen",
        tr_doc="[modül] [-f] - Yardımı göster",
        uz_doc="[modul] [-f] - Yordamni ko'rsatish",
        es_doc="[módulo] [-f] - Mostrar ayuda",
        kk_doc="[модуль] [-f] - Анықтама көрсету",
    )
    async def help(self, message: Message):
        """[module] [-f] - Show help"""
        args = utils.get_args_raw(message)
        force = False
        if "-f" in args:
            args = args.replace(" -f", "").replace("-f", "")
            force = True

        if args:
            await self.modhelp(message, args)
            return

        hidden = self.get("hide", [])

        reply = self.strings("all_header").format(
            len(self.allmodules.modules) + len(self.allmodules.dragon_modules),
            0
            if force
            else sum(
                module.__class__.__name__ in hidden
                for module in self.allmodules.modules
            )
            + sum(module.name in hidden for module in self.allmodules.dragon_modules),
        )
        shown_warn = False

        plain_ = []
        core_ = []
        inline_ = []
        no_commands_ = []
        dragon_ = []

        for mod in self.allmodules.dragon_modules:
            if mod.name in self.get("hide", []) and not force:
                continue

            tmp = f"\n{DRAGON_EMOJI} <code>{mod.name}</code>"
            first = True

            for cmd in mod.commands:
                cmd = cmd.split()[0]
                if first:
                    tmp += f": ( {cmd}"
                    first = False
                else:
                    tmp += f" | {cmd}"

            dragon_ += [f"{tmp} )"]

        for mod in self.allmodules.modules:
            if not hasattr(mod, "commands"):
                logger.debug("Module %s is not inited yet", mod.__class__.__name__)
                continue

            if mod.__class__.__name__ in self.get("hide", []) and not force:
                continue

            tmp = ""

            try:
                name = mod.strings["name"]
            except KeyError:
                name = getattr(mod, "name", "ERROR")

            inline = (
                hasattr(mod, "callback_handlers")
                and mod.callback_handlers
                or hasattr(mod, "inline_handlers")
                and mod.inline_handlers
            )

            if not inline:
                for cmd_ in mod.commands.values():
                    try:
                        inline = "await self.inline.form(" in inspect.getsource(
                            cmd_.__code__
                        )
                    except Exception:
                        pass

            core = mod.__origin__.startswith("<core")

            if core:
                emoji = self.config["core_emoji"]
            elif inline:
                emoji = self.config["hikka_emoji"]
            else:
                emoji = self.config["plain_emoji"]

            if (
                not getattr(mod, "commands", None)
                and not getattr(mod, "inline_handlers", None)
                and not getattr(mod, "callback_handlers", None)
            ):
                no_commands_ += [f'\n{self.config["empty_emoji"]} <code>{name}</code>']
                continue

            tmp += f"\n{emoji} <code>{name}</code>"
            first = True

            commands = [
                name
                for name, func in mod.commands.items()
                if await self.allmodules.check_security(message, func) or force
            ]

            for cmd in commands:
                if first:
                    tmp += f": ( {cmd}"
                    first = False
                else:
                    tmp += f" | {cmd}"

            icommands = [
                name
                for name, func in mod.inline_handlers.items()
                if await self.inline.check_inline_security(
                    func=func,
                    user=message.sender_id,
                )
                or force
            ]

            for cmd in icommands:
                if first:
                    tmp += f": ( 🤖 {cmd}"
                    first = False
                else:
                    tmp += f" | 🤖 {cmd}"

            if commands or icommands:
                tmp += " )"
                if core:
                    core_ += [tmp]
                elif inline:
                    inline_ += [tmp]
                else:
                    plain_ += [tmp]
            elif not shown_warn and (mod.commands or mod.inline_handlers):
                reply = (
                    "<i>You have permissions to execute only these"
                    f" commands</i>\n{reply}"
                )
                shown_warn = True

        plain_.sort(key=lambda x: x.split()[1])
        core_.sort(key=lambda x: x.split()[1])
        inline_.sort(key=lambda x: x.split()[1])
        no_commands_.sort(key=lambda x: x.split()[1])
        no_commands_ = "".join(no_commands_) if force else ""
        dragon_.sort()

        partial_load = (
            ""
            if self.lookup("Loader").fully_loaded
            else f"\n\n{self.strings('partial_load')}"
        )

        await utils.answer(
            message,
            f'{reply}\n{"".join(core_)}{"".join(plain_)}{"".join(inline_)}{"".join(dragon_)}{no_commands_}{partial_load}',
        )

    @loader.command(
        ru_doc="Показать ссылку на чат помощи Hikka",
        it_doc="Mostra il link al gruppo di supporto Hikka",
        de_doc="Zeige den Link zum Hikka-Hilfe-Chat",
        tr_doc="Hikka yardım sohbetinin bağlantısını göster",
        uz_doc="Hikka yordam sohbatining havolasini ko'rsatish",
        es_doc="Mostrar enlace al chat de ayuda de Hikka",
        kk_doc="Hikka анықтама сөйлесушісінің сілтемесін көрсету",
    )
    async def support(self, message):
        """Get link of Hikka support chat"""
        if message.out:
            await self.request_join("@hikka_talks", self.strings("request_join"))

        await utils.answer(
            message,
            self.strings("support").format(
                (
                    utils.get_platform_emoji()
                    if self._client.hikka_me.premium and CUSTOM_EMOJIS
                    else "🌘"
                )
            ),
        )
