# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import inspect
from .. import loader, utils, main, security
from telethon.tl.functions.channels import JoinChannelRequest
import logging
import difflib

from telethon.tl.types import Message

logger = logging.getLogger(__name__)


@loader.tds
class HelpMod(loader.Module):
    """Help module, made specifically for Hikka with <3"""

    strings = {
        "name": "Help",
        "bad_module": "<b>🚫 <b>Module</b> <code>{}</code> <b>not found</b>",
        "single_mod_header": "📼 <b>{}</b>:",
        "single_cmd": "\n▫️ <code>{}{}</code> 👉🏻 ",
        "undoc_cmd": "🦥 No docs",
        "all_header": "🌘 <b>{} mods available, {} hidden:</b>",
        "mod_tmpl": "\n{} <code>{}</code>",
        "first_cmd_tmpl": ": ( {}",
        "cmd_tmpl": " | {}",
        "no_mod": "🚫 <b>Specify module to hide</b>",
        "hidden_shown": "🌘 <b>{} modules hidden, {} modules shown:</b>\n{}\n{}",
        "ihandler": "\n🎹 <code>{}</code> 👉🏻 ",
        "undoc_ihandler": "🦥 No docs",
        "joined": "🌘 <b>Joined the</b> <a href='https://t.me/hikka_talks'>support chat</a>",
        "join": "🌘 <b>Join the</b> <a href='https://t.me/hikka_talks'>support chat</a>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "core_emoji",
            "▪️",
            lambda: "Core module bullet",
            "hikka_emoji",
            "🌘",
            lambda: "Hikka-only module bullet",
            "plain_emoji",
            "▫️",
            lambda: "Plain module bullet",
        )

    async def helphidecmd(self, message: Message):
        """<module or modules> - Hide module(-s) from help
        *Split modules by spaces"""
        modules = utils.get_args(message)
        if not modules:
            await utils.answer(message, self.strings("no_mod", message))
            return

        mods = [
            i.strings["name"]
            for i in self.allmodules.modules
            if hasattr(i, "strings") and "name" in i.strings
        ]

        modules = list(filter(lambda module: module in mods, modules))
        currently_hidden = self.get("hide", [])
        hidden, shown = [], []
        for module in modules:
            if module in currently_hidden:
                currently_hidden.remove(module)
                shown += [module]
            else:
                currently_hidden += [module]
                hidden += [module]

        self.set("hide", currently_hidden)

        await utils.answer(
            message,
            self.strings("hidden_shown", message).format(
                len(hidden),
                len(shown),
                "\n".join([f"👁‍🗨 <i>{m}</i>" for m in hidden]),
                "\n".join([f"👁 <i>{m}</i>" for m in shown]),
            ),
        )

    @loader.unrestricted
    async def helpcmd(self, message: Message):
        """[module] [-f] - Show help"""
        args = utils.get_args_raw(message)
        force = False
        if "-f" in args:
            args = args.replace(" -f", "").replace("-f", "")
            force = True

        prefix = utils.escape_html(
            (self._db.get(main.__name__, "command_prefix", False) or ".")
        )

        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.strings("name", message).lower() == args.lower():
                    module = mod

            if not module:
                args = args.lower()
                args = args[1:] if args.startswith(prefix) else args
                if args in self.allmodules.commands:
                    module = self.allmodules.commands[args].__self__

            if not module:
                module_name = next(  # skipcq: PTC-W0063
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
                )

                module = next(  # skipcq: PTC-W0063
                    module
                    for module in self.allmodules.modules
                    if module.strings["name"] == module_name
                )

            try:
                name = module.strings("name")
            except KeyError:
                name = getattr(module, "name", "ERROR")

            reply = self.strings("single_mod_header", message).format(
                utils.escape_html(name)
            )
            if module.__doc__:
                reply += (
                    "<i>\nℹ️ " + utils.escape_html(inspect.getdoc(module)) + "\n</i>"
                )

            commands = {
                name: func
                for name, func in module.commands.items()
                if await self.allmodules.check_security(message, func)
            }

            if hasattr(module, "inline_handlers"):
                for name, fun in module.inline_handlers.items():
                    reply += self.strings("ihandler", message).format(
                        f"@{self.inline.bot_username} {name}"
                    )

                    if fun.__doc__:
                        reply += utils.escape_html(
                            "\n".join(
                                [
                                    line.strip()
                                    for line in inspect.getdoc(fun).splitlines()
                                    if not line.strip().startswith("@")
                                ]
                            )
                        )
                    else:
                        reply += self.strings("undoc_ihandler", message)

            for name, fun in commands.items():
                reply += self.strings("single_cmd", message).format(prefix, name)
                if fun.__doc__:
                    reply += utils.escape_html(inspect.getdoc(fun))
                else:
                    reply += self.strings("undoc_cmd", message)

            await utils.answer(message, reply)
            return

        count = 0
        for i in self.allmodules.modules:
            try:
                if i.commands or i.inline_handlers:
                    count += 1
            except Exception:
                pass

        mods = [
            i.strings["name"]
            for i in self.allmodules.modules
            if hasattr(i, "strings") and "name" in i.strings
        ]

        hidden = list(filter(lambda module: module in mods, self.get("hide", [])))
        self.set("hide", hidden)

        reply = self.strings("all_header", message).format(
            count, len(hidden) if not force else 0
        )
        shown_warn = False

        plain_ = []
        core_ = []
        inline_ = []

        for mod in self.allmodules.modules:
            if not hasattr(mod, "commands"):
                logger.error(f"Module {mod.__class__.__name__} is not inited yet")
                continue

            if mod.strings["name"] in self.get("hide", []) and not force:
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

            for cmd_ in mod.commands.values():
                try:
                    "self.inline.form(" in inspect.getsource(cmd_.__code__)
                except Exception:
                    pass

            core = mod.__origin__ == "<core>"

            if core:
                emoji = self.config["core_emoji"]
            elif inline:
                emoji = self.config["hikka_emoji"]
            else:
                emoji = self.config["plain_emoji"]

            tmp += self.strings("mod_tmpl", message).format(emoji, name)

            first = True

            commands = [
                name
                for name, func in mod.commands.items()
                if await self.allmodules.check_security(message, func) or force
            ]

            for cmd in commands:
                if first:
                    tmp += self.strings("first_cmd_tmpl", message).format(cmd)
                    first = False
                else:
                    tmp += self.strings("cmd_tmpl", message).format(cmd)

            icommands = [
                name
                for name, func in mod.inline_handlers.items()
                if await self.inline.check_inline_security(
                    func=func, user=message.sender_id
                )
                or force
            ]

            for cmd in icommands:
                if first:
                    tmp += self.strings("first_cmd_tmpl", message).format(f"🎹 {cmd}")
                    first = False
                else:
                    tmp += self.strings("cmd_tmpl", message).format(f"🎹 {cmd}")

            if commands or icommands:
                tmp += " )"
                if core:
                    core_ += [tmp]
                elif inline:
                    inline_ += [tmp]
                else:
                    plain_ += [tmp]
            elif not shown_warn and (mod.commands or mod.inline_handlers):
                reply = f"<i>You have permissions to execute only this commands</i>\n{reply}"
                shown_warn = True

        plain_.sort(key=lambda x: x.split()[1])
        core_.sort(key=lambda x: x.split()[1])
        inline_.sort(key=lambda x: x.split()[1])

        await utils.answer(
            message,
            f"{reply}\n{''.join(core_)}{''.join(plain_)}{''.join(inline_)}",
        )

    async def supportcmd(self, message):
        """Joins the support Hikka chat"""
        if await self.allmodules.check_security(
            message,
            security.OWNER | security.SUDO,
        ):
            await self._client(JoinChannelRequest("https://t.me/hikka_talks"))

            try:
                await self.inline.form(
                    self.strings("joined", message),
                    reply_markup=[
                        [{"text": "👩‍💼 Chat", "url": "https://t.me/hikka_talks"}]
                    ],
                    ttl=10,
                    message=message,
                )
            except Exception:
                await utils.answer(message, self.strings("joined", message))
        else:
            try:
                await self.inline.form(
                    self.strings("join", message),
                    reply_markup=[
                        [{"text": "👩‍💼 Chat", "url": "https://t.me/hikka_talks"}]
                    ],
                    ttl=10,
                    message=message,
                )
            except Exception:
                await utils.answer(message, self.strings("join", message))

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
