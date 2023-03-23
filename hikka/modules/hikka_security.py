# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import time
import typing

from hikkatl.hints import EntityLike
from hikkatl.tl.types import Message, PeerUser, User
from hikkatl.utils import get_display_name

from .. import loader, main, security, utils
from ..inline.types import InlineCall, InlineMessage
from ..security import (
    DEFAULT_PERMISSIONS,
    EVERYONE,
    GROUP_ADMIN,
    GROUP_ADMIN_ADD_ADMINS,
    GROUP_ADMIN_BAN_USERS,
    GROUP_ADMIN_CHANGE_INFO,
    GROUP_ADMIN_DELETE_MESSAGES,
    GROUP_ADMIN_INVITE_USERS,
    GROUP_ADMIN_PIN_MESSAGES,
    GROUP_MEMBER,
    GROUP_OWNER,
    PM,
)


@loader.tds
class HikkaSecurityMod(loader.Module):
    """Control security settings"""

    strings = {"name": "HikkaSecurity"}

    async def inline__switch_perm(
        self,
        call: InlineCall,
        command: str,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        cmd = (
            self.allmodules.inline_handlers[command]
            if is_inline
            else self.allmodules.commands[command]
        )

        mask = self._db.get(security.__name__, "masks", {}).get(
            f"{cmd.__module__}.{cmd.__name__}",
            getattr(cmd, "security", security.DEFAULT_PERMISSIONS),
        )

        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        masks = self._db.get(security.__name__, "masks", {})
        masks[f"{cmd.__module__}.{cmd.__name__}"] = mask
        self._db.set(security.__name__, "masks", masks)

        if (
            not self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS)
            & bit
            and level
        ):
            await call.answer(
                (
                    "Security value set but not applied. Consider enabling this value"
                    f" in .{'inlinesec' if is_inline else 'security'}"
                ),
                show_alert=True,
            )
        else:
            await call.answer("Security value set!")

        await call.edit(
            self.strings("permissions").format(
                utils.escape_html(
                    f"@{self.inline.bot_username} " if is_inline else self.get_prefix()
                ),
                command,
            ),
            reply_markup=self._build_markup(cmd, is_inline),
        )

    async def inline__switch_perm_bm(
        self,
        call: InlineCall,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        mask = self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS)
        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        self._db.set(security.__name__, "bounding_mask", mask)

        await call.answer("Bounding mask value set!")
        await call.edit(
            self.strings("global"),
            reply_markup=self._build_markup_global(is_inline),
        )

    def _build_markup(
        self,
        command: callable,
        is_inline: bool = False,
    ) -> typing.List[typing.List[dict]]:
        perms = self._get_current_perms(command, is_inline)
        return (
            utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                        "callback": self.inline__switch_perm,
                        "args": (
                            command.__name__.rsplit("_inline_handler", maxsplit=1)[0],
                            group,
                            not level,
                            is_inline,
                        ),
                    }
                    for group, level in perms.items()
                ],
                2,
            )
            + [[{"text": self.strings("close_menu"), "action": "close"}]]
            if is_inline
            else utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                        "callback": self.inline__switch_perm,
                        "args": (
                            command.__name__.rsplit("cmd", maxsplit=1)[0],
                            group,
                            not level,
                            is_inline,
                        ),
                    }
                    for group, level in perms.items()
                ],
                2,
            )
            + [
                [
                    {
                        "text": self.strings("close_menu"),
                        "action": "close",
                    }
                ]
            ]
        )

    def _build_markup_global(
        self,
        is_inline: bool = False,
    ) -> typing.List[typing.List[dict]]:
        return utils.chunks(
            [
                {
                    "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                    "callback": self.inline__switch_perm_bm,
                    "args": (group, not level, is_inline),
                }
                for group, level in self._get_current_bm(is_inline).items()
            ],
            2,
        ) + [[{"text": self.strings("close_menu"), "action": "close"}]]

    def _get_current_bm(self, is_inline: bool = False) -> dict:
        return self._perms_map(
            self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS),
            is_inline,
        )

    @staticmethod
    def _perms_map(perms: int, is_inline: bool) -> dict:
        return (
            {"everyone": bool(perms & EVERYONE)}
            if is_inline
            else {
                "group_owner": bool(perms & GROUP_OWNER),
                "group_admin_add_admins": bool(perms & GROUP_ADMIN_ADD_ADMINS),
                "group_admin_change_info": bool(perms & GROUP_ADMIN_CHANGE_INFO),
                "group_admin_ban_users": bool(perms & GROUP_ADMIN_BAN_USERS),
                "group_admin_delete_messages": bool(
                    perms & GROUP_ADMIN_DELETE_MESSAGES
                ),
                "group_admin_pin_messages": bool(perms & GROUP_ADMIN_PIN_MESSAGES),
                "group_admin_invite_users": bool(perms & GROUP_ADMIN_INVITE_USERS),
                "group_admin": bool(perms & GROUP_ADMIN),
                "group_member": bool(perms & GROUP_MEMBER),
                "pm": bool(perms & PM),
                "everyone": bool(perms & EVERYONE),
            }
        )

    def _get_current_perms(
        self,
        command: callable,
        is_inline: bool = False,
    ) -> dict:
        return self._perms_map(
            self._db.get(security.__name__, "masks", {}).get(
                f"{command.__module__}.{command.__name__}",
                getattr(command, "security", self._client.dispatcher.security.default),
            ),
            is_inline,
        )

    @loader.command()
    async def security(self, message: Message):
        """[command] - Configure command's security settings"""
        if (
            args := utils.get_args_raw(message).lower().strip()
        ) and args not in self.allmodules.commands:
            await utils.answer(message, self.strings("no_command").format(args))
            return

        if not args:
            await self.inline.form(
                self.strings("global"),
                reply_markup=self._build_markup_global(),
                message=message,
                ttl=5 * 60,
            )
            return

        await self.inline.form(
            self.strings("permissions").format(self.get_prefix(), args),
            reply_markup=self._build_markup(self.allmodules.commands[args]),
            message=message,
            ttl=5 * 60,
        )

    @loader.command()
    async def inlinesec(self, message: Message):
        """[command] - Configure inline command's security settings"""
        if not (args := utils.get_args_raw(message).lower().strip()):
            await self.inline.form(
                self.strings("global"),
                reply_markup=self._build_markup_global(True),
                message=message,
                ttl=5 * 60,
            )
            return

        if args not in self.allmodules.inline_handlers:
            await utils.answer(message, self.strings("no_command").format(args))
            return

        await self.inline.form(
            self.strings("permissions").format(f"@{self.inline.bot_username} ", args),
            reply_markup=self._build_markup(
                self.allmodules.inline_handlers[args],
                True,
            ),
            message=message,
            ttl=5 * 60,
        )

    async def _resolve_user(self, message: Message):
        if not (args := utils.get_args_raw(message)) and not (
            reply := await message.get_reply_message()
        ):
            await utils.answer(message, self.strings("no_user"))
            return

        user = None

        if args:
            with contextlib.suppress(Exception):
                if str(args).isdigit():
                    args = int(args)

                user = await self._client.get_entity(args, exp=0)

        if user is None:
            try:
                user = await self._client.get_entity(reply.sender_id, exp=0)
            except ValueError:
                user = await reply.get_sender()

        if not isinstance(user, (User, PeerUser)):
            await utils.answer(message, self.strings("not_a_user"))
            return

        if user.id == self.tg_id:
            await utils.answer(message, self.strings("self"))
            return

        return user

    async def _add_to_group(
        self,
        message: typing.Union[Message, InlineCall],
        group: str,
        confirmed: bool = False,
        user: int = None,
    ):
        if user is None and not (user := await self._resolve_user(message)):
            return

        if isinstance(user, int):
            user = await self._client.get_entity(user, exp=0)

        if not confirmed:
            await self.inline.form(
                self.strings("warning").format(
                    user.id,
                    utils.escape_html(get_display_name(user)),
                    group,
                ),
                message=message,
                ttl=10 * 60,
                reply_markup=[
                    {
                        "text": self.strings("cancel"),
                        "action": "close",
                    },
                    {
                        "text": self.strings("confirm"),
                        "callback": self._add_to_group,
                        "args": (group, True, user.id),
                    },
                ],
            )
            return

        if user.id not in getattr(self._client.dispatcher.security, group):
            getattr(self._client.dispatcher.security, group).append(user.id)

        await message.edit(
            (
                self.strings(f"{group}_added").format(
                    user.id,
                    utils.escape_html(get_display_name(user)),
                )
                + "\n\n"
                + self.strings("suggest_nonick")
            ),
            reply_markup=[
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
                {
                    "text": self.strings("enable_nonick_btn"),
                    "callback": self._enable_nonick,
                    "args": (user,),
                },
            ],
        )

    async def _enable_nonick(self, call: InlineCall, user: User):
        self._db.set(
            main.__name__,
            "nonickusers",
            list(set(self._db.get(main.__name__, "nonickusers", []) + [user.id])),
        )

        await call.edit(
            self.strings("user_nn").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            )
        )

        await call.unload()

    @loader.command()
    async def owneradd(self, message: Message):
        """<user> - Add user to `owner`"""
        await self._add_to_group(message, "owner")

    @loader.command()
    async def ownerrm(self, message: Message):
        """<user> - Remove user from `owner`"""
        if not (user := await self._resolve_user(message)):
            return

        if user.id in self._client.dispatcher.security.owner:
            self._client.dispatcher.security.owner.remove(user.id)

        await utils.answer(
            message,
            self.strings("owner_removed").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            ),
        )

    @loader.command()
    async def ownerlist(self, message: Message):
        """List users in `owner`"""
        _resolved_users = []
        for user in set(self._client.dispatcher.security.owner + [self.tg_id]):
            with contextlib.suppress(Exception):
                _resolved_users += [await self._client.get_entity(user, exp=0)]

        if not _resolved_users:
            await utils.answer(message, self.strings("no_owner"))
            return

        await utils.answer(
            message,
            self.strings("owner_list").format(
                "\n".join(
                    [
                        self.strings("li").format(
                            i.id, utils.escape_html(get_display_name(i))
                        )
                        for i in _resolved_users
                    ]
                )
            ),
        )

    def _lookup(self, needle: str) -> str:
        return (
            (
                []
                if needle.lower().startswith(self.get_prefix())
                else (
                    [f"module/{self.lookup(needle).__class__.__name__}"]
                    if self.lookup(needle)
                    else []
                )
            )
            + (
                [f"command/{needle.lower().strip(self.get_prefix())}"]
                if needle.lower().strip(self.get_prefix()) in self.allmodules.commands
                else []
            )
            + (
                [f"inline/{needle.lower().strip('@')}"]
                if needle.lower().strip("@") in self.allmodules.inline_handlers
                else []
            )
        )

    @staticmethod
    def _extract_time(args: list) -> int:
        for suffix, quantifier in {
            "d": 24 * 60 * 60,
            "h": 60 * 60,
            "m": 60,
            "s": 1,
        }.items():
            duration = next(
                (
                    int(arg.rsplit(suffix, maxsplit=1)[0])
                    for arg in args
                    if arg.endswith(suffix)
                    and arg.rsplit(suffix, maxsplit=1)[0].isdigit()
                ),
                None,
            )
            if duration is not None:
                return duration * quantifier

        return 0

    def _convert_time(self, duration: int) -> str:
        return (
            self.strings("forever")
            if not duration or duration < 0
            else (
                (
                    f"{duration // (24 * 60 * 60)} "
                    + self.strings(
                        f"day{'s' if duration // (24 * 60 * 60) > 1 else ''}"
                    )
                )
                if duration >= 24 * 60 * 60
                else (
                    (
                        f"{duration // (60 * 60)} "
                        + self.strings(
                            f"hour{'s' if duration // (60 * 60) > 1 else ''}"
                        )
                    )
                    if duration >= 60 * 60
                    else (
                        (
                            f"{duration // 60} "
                            + self.strings(f"minute{'s' if duration // 60 > 1 else ''}")
                        )
                        if duration >= 60
                        else (
                            f"{duration} "
                            + self.strings(f"second{'s' if duration > 1 else ''}")
                        )
                    )
                )
            )
        )

    async def _add_rule(
        self,
        call: InlineCall,
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
        if rule.startswith("inline") and target_type == "chat":
            await call.edit(self.strings("chat_inline"))
            return

        self._client.dispatcher.security.add_rule(
            target_type,
            target,
            rule,
            duration,
        )

        await call.edit(
            self.strings("rule_added").format(
                self.strings(target_type),
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                self.strings(rule.split("/", maxsplit=1)[0]),
                (
                    (
                        f"@{self.inline.bot_username} "
                        if rule.split("/", maxsplit=1)[0] == "inline"
                        else ""
                    )
                    + rule.split("/", maxsplit=1)[1]
                ),
                (
                    (self.strings("for") + " " + self._convert_time(duration))
                    if duration
                    else self.strings("forever")
                ),
            )
        )

    async def _confirm(
        self,
        obj: typing.Union[Message, InlineMessage],
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
        await utils.answer(
            obj,
            self.strings("confirm_rule").format(
                self.strings(target_type),
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                self.strings(rule.split("/", maxsplit=1)[0]),
                (
                    (
                        f"@{self.inline.bot_username} "
                        if rule.split("/", maxsplit=1)[0] == "inline"
                        else ""
                    )
                    + rule.split("/", maxsplit=1)[1]
                ),
                (
                    (self.strings("for") + " " + self._convert_time(duration))
                    if duration
                    else self.strings("forever")
                ),
            ),
            reply_markup=[
                {
                    "text": self.strings("confirm_btn"),
                    "callback": self._add_rule,
                    "args": (target_type, target, rule, duration),
                },
                {"text": self.strings("cancel_btn"), "action": "close"},
            ],
        )

    async def _tsec_chat(self, message: Message, args: list):
        if len(args) == 1 and message.is_private:
            await utils.answer(message, self.strings("no_target"))
            return

        if len(args) >= 2:
            try:
                if not args[1].isdigit() and not args[1].startswith("@"):
                    raise ValueError

                target = await self._client.get_entity(
                    int(args[1]) if args[1].isdigit() else args[1],
                    exp=0,
                )
            except (ValueError, TypeError):
                if not message.is_private:
                    target = await self._client.get_entity(message.peer_id, exp=0)
                else:
                    await utils.answer(message, self.strings("no_target"))
                    return

        if not (possible_rules := utils.array_sum([self._lookup(arg) for arg in args])):
            await utils.answer(message, self.strings("no_rule"))
            return

        duration = self._extract_time(args)

        if len(possible_rules) > 1:

            def case(text: str) -> str:
                return text.upper()[0] + text[1:]

            await self.inline.form(
                message=message,
                text=self.strings("multiple_rules").format(
                    "\n".join(
                        "🛡 <b>{}</b> <code>{}</code>".format(
                            case(self.strings(rule.split("/")[0])),
                            rule.split("/", maxsplit=1)[1],
                        )
                        for rule in possible_rules
                    )
                ),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": "🛡 {} {}".format(
                                case(self.strings(rule.split("/")[0])),
                                rule.split("/", maxsplit=1)[1],
                            ),
                            "callback": self._confirm,
                            "args": ("chat", target, rule, duration),
                        }
                        for rule in possible_rules
                    ],
                    3,
                ),
            )
            return

        await self._confirm(message, "chat", target, possible_rules[0], duration)

    async def _tsec_user(self, message: Message, args: list):
        if len(args) == 1 and not message.is_private and not message.is_reply:
            await utils.answer(message, self.strings("no_target"))
            return

        if len(args) >= 2:
            try:
                if not args[1].isdigit() and not args[1].startswith("@"):
                    raise ValueError

                target = await self._client.get_entity(
                    int(args[1]) if args[1].isdigit() else args[1],
                    exp=0,
                )
            except (ValueError, TypeError):
                if message.is_private:
                    target = await self._client.get_entity(message.peer_id, exp=0)
                elif message.is_reply:
                    target = await self._client.get_entity(
                        (await message.get_reply_message()).sender_id,
                        exp=0,
                    )
                else:
                    await utils.answer(message, self.strings("no_target"))
                    return

        if target.id in self._client.dispatcher.security.owner:
            await utils.answer(message, self.strings("owner_target"))
            return

        duration = self._extract_time(args)

        if not (possible_rules := utils.array_sum([self._lookup(arg) for arg in args])):
            await utils.answer(message, self.strings("no_rule"))
            return

        if len(possible_rules) > 1:

            def case(text: str) -> str:
                return text.upper()[0] + text[1:]

            await self.inline.form(
                message=message,
                text=self.strings("multiple_rules").format(
                    "\n".join(
                        "🛡 <b>{}</b> <code>{}</code>".format(
                            case(self.strings(rule.split("/")[0])),
                            rule.split("/", maxsplit=1)[1],
                        )
                        for rule in possible_rules
                    )
                ),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": "🛡 {} {}".format(
                                case(self.strings(rule.split("/")[0])),
                                rule.split("/", maxsplit=1)[1],
                            ),
                            "callback": self._confirm,
                            "args": ("user", target, rule, duration),
                        }
                        for rule in possible_rules
                    ],
                    3,
                ),
            )
            return

        await self._confirm(message, "user", target, possible_rules[0], duration)

    @loader.command(
        ru_doc=(
            '<"user"/"chat"> <правило - модуль или команда> - Удалить правило'
            " таргетированной безопасности\nНапример: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        fr_doc=(
            '<"user"/"chat"> <règle - module ou commande> - Supprimer la règle de'
            " sécurité ciblée\nPar exemple: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        es_doc=(
            '<"user"/"chat"> <regla - módulo o comando> - Eliminar la regla de'
            " seguridad dirigida\nPor ejemplo: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        de_doc=(
            '<"user"/"chat"> <Regel - Modul oder Befehl> - Entferne die Regel der'
            " zielgerichteten Sicherheit\nBeispiel: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        it_doc=(
            '<"user"/"chat"> <regola - modulo o comando> - Rimuovi la regola di'
            " sicurezza mirata\nEsempio: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        tr_doc=(
            '<"user"/"chat"> <kural - modül veya komut> - Hedefli güvenlik kuralını'
            " kaldır\nÖrnek: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        uz_doc=(
            '<"user"/"chat"> <qoida - modul yoki buyruq> - Maqsadli xavfsizlik'
            " qoidasini olib tashlang\nMasalan: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        kk_doc=(
            '<"user"/"chat"> <құқық - модуль немесе команда> - Мақсатты қауіпсіздік'
            " құқығын өшіріңіз\nМысалы: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        tt_doc=(
            '<"user"/"chat"> <көйләү - модуль немесе команда> - Мақсатлы қауіпсіздік'
            " көйләүен өшерү\nМисаллы: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
    )
    async def tsecrm(self, message: Message):
        """
        <"user"/"chat"> <rule - command or module> - Remove targeted security rule
        For example: .tsecrm user ban, .tsecrm chat HikariChat
        """
        if (
            not self._client.dispatcher.security.tsec_chat
            and not self._client.dispatcher.security.tsec_user
        ):
            await utils.answer(message, self.strings("no_rules"))
            return

        if not (args := utils.get_args(message)) or args[0] not in {"user", "chat"}:
            await utils.answer(message, self.strings("no_target"))
            return

        if args[0] == "user":
            if not message.is_private and not message.is_reply:
                await utils.answer(message, self.strings("no_target"))
                return

            if message.is_private:
                target = await self._client.get_entity(message.peer_id, exp=0)
            elif message.is_reply:
                target = await self._client.get_entity(
                    (await message.get_reply_message()).sender_id,
                    exp=0,
                )

            if not self._client.dispatcher.security.remove_rule(
                "user",
                target.id,
                args[1],
            ):
                await utils.answer(message, self.strings("no_rules"))
                return

            await utils.answer(
                message,
                self.strings("rule_removed").format(
                    utils.get_entity_url(target),
                    utils.escape_html(get_display_name(target)),
                    utils.escape_html(args[1]),
                ),
            )
            return

        if message.is_private:
            await utils.answer(message, self.strings("no_target"))
            return

        target = await self._client.get_entity(message.peer_id, exp=0)

        if not self._client.dispatcher.security.remove_rule("chat", target.id, args[1]):
            await utils.answer(message, self.strings("no_rules"))
            return

        await utils.answer(
            message,
            self.strings("rule_removed").format(
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                utils.escape_html(args[1]),
            ),
        )

    @loader.command(
        ru_doc=(
            '<"user"/"chat"> - Очистить правила таргетированной безопасности\nНапример:'
            " .tsecclr user, .tsecclr chat"
        ),
        fr_doc=(
            '<"user"/"chat"> - Supprimer les règles de sécurité ciblées\nPar exemple:'
            " .tsecclr user, .tsecclr chat"
        ),
        es_doc=(
            '<"user"/"chat"> - Eliminar las reglas de seguridad dirigidas\nPor ejemplo:'
            " .tsecclr user, .tsecclr chat"
        ),
        de_doc=(
            '<"user"/"chat"> - Entferne die Regeln der zielgerichteten'
            " Sicherheit\nBeispiel: .tsecclr user, .tsecclr chat"
        ),
        it_doc=(
            '<"user"/"chat"> - Rimuovi le regole di sicurezza mirate\nEsempio: .tsecclr'
            " user, .tsecclr chat"
        ),
        tr_doc=(
            '<"user"/"chat"> - Hedefli güvenlik kurallarını temizle\nÖrnek: .tsecclr'
            " user, .tsecclr chat"
        ),
        uz_doc=(
            '<"user"/"chat"> - Maqsadli xavfsizlik qoidalarini tozalash\nMasalan:'
            " .tsecclr user, .tsecclr chat"
        ),
        kk_doc=(
            '<"user"/"chat"> - Мақсатты қауіпсіздік құқығын тазалаңыз\nМысалы: .tsecclr'
            " user, .tsecclr chat"
        ),
        tt_doc=(
            '<"user"/"chat"> - Мақсатлы қауіпсіздік көйләүен тазалаңыз\nМисаллы:'
            " .tsecclr user, .tsecclr chat"
        ),
    )
    async def tsecclr(self, message: Message):
        """
        <"user"/"chat"> - Clear targeted security rules
        For example: .tsecclr user, .tsecclr chat
        """
        if (
            not self._client.dispatcher.security.tsec_chat
            and not self._client.dispatcher.security.tsec_user
        ):
            await utils.answer(message, self.strings("no_rules"))
            return

        if not (args := utils.get_args_raw(message)) or args not in {"user", "chat"}:
            await utils.answer(message, self.strings("no_target"))
            return

        if args == "user":
            if not message.is_private and not message.is_reply:
                await utils.answer(message, self.strings("no_target"))
                return

            if message.is_private:
                target = await self._client.get_entity(message.peer_id, exp=0)
            elif message.is_reply:
                target = await self._client.get_entity(
                    (await message.get_reply_message()).sender_id,
                    exp=0,
                )

            if not self._client.dispatcher.security.remove_rules("user", target.id):
                await utils.answer(message, self.strings("no_rules"))
                return

            await utils.answer(
                message,
                self.strings("rules_removed").format(
                    utils.get_entity_url(target),
                    utils.escape_html(get_display_name(target)),
                ),
            )
            return

        if message.is_private:
            await utils.answer(message, self.strings("no_target"))
            return

        target = await self._client.get_entity(message.peer_id, exp=0)

        if not self._client.dispatcher.security.remove_rules("chat", target.id):
            await utils.answer(message, self.strings("no_rules"))
            return

        await utils.answer(
            message,
            self.strings("rules_removed").format(
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
            ),
        )

    @loader.command(
        ru_doc=(
            '<"user"/"chat"> [цель пользователя или чата] [правило (команда/модуль)]'
            " [время] - Добавить новое правило таргетированной безопасности\nНапример:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        fr_doc=(
            '<"user"/"chat"> [cible utilisateur ou chat] [règle (commande/module)]'
            " [temps] - Ajouter une nouvelle règle de sécurité ciblée\nPar exemple:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        es_doc=(
            '<"user"/"chat"> [objetivo de usuario o chat] [regla (comando/módulo)]'
            " [tiempo] - Agregar una nueva regla de seguridad dirigida\nPor ejemplo:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        de_doc=(
            '<"user"/"chat"> [Zielbenutzer oder Chat] [Regel (Befehl/Modul)] [Zeit] -'
            " Füge eine neue zielgerichtete Sicherheitsregel hinzu\nBeispiel: .tsec"
            " user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        it_doc=(
            '<"user"/"chat"> [utente o chat di destinazione] [regola (comando/modulo)]'
            " [tempo] - Aggiungi una nuova regola di sicurezza mirata\nEsempio: .tsec"
            " user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        tr_doc=(
            '<"user"/"chat"> [hedef kullanıcı veya sohbet] [kural (komut/modül)]'
            " [zaman] - Yeni hedefli güvenlik kuralı ekleyin\nÖrnek: .tsec user ban 1d,"
            " .tsec chat weather 1h, .tsec user HikariChat"
        ),
        uz_doc=(
            '<"user"/"chat"> [maqsadli foydalanuvchi yoki chat] [qoida (buyruq/modul)]'
            " [vaqt] - Yangi maqsadli xavfsizlik qoidasini qo`shing\nMasalan: .tsec"
            " user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        kk_doc=(
            '<"user"/"chat"> [мақсатты пайдаланушы немесе сөйлесу] [құқық'
            " (команда/модуль)] [уақыт] - Жаңа мақсатты қауіпсіздік құқығын"
            " қосыңыз\nМысалы: .tsec user ban 1d, .tsec chat weather 1h, .tsec user"
            " HikariChat"
        ),
        tt_doc=(
            '<"user"/"chat"> [мәҗбүри кулланучы немесе сөйләшү] [җөйләү'
            " (команда/модуль)] [вакыт] - Яңа мәҗбүри һаҡлылык җөйләүен өстәү\nМисалы:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
    )
    async def tsec(self, message: Message):
        """
        <"user"/"chat"> [target user or chat] [rule (command/module)] [time] - Add new targeted security rule
        For example: .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat
        """
        if not (args := utils.get_args(message)):
            if (
                not self._client.dispatcher.security.tsec_chat
                and not self._client.dispatcher.security.tsec_user
            ):
                await utils.answer(message, self.strings("no_rules"))
                return

            await utils.answer(
                message,
                self.strings("rules").format(
                    "\n".join(
                        [
                            "<emoji document_id=6037355667365300960>👥</emoji> <b><a"
                            " href='{}'>{}</a> {} {} {}</b> <code>{}</code>".format(
                                rule["entity_url"],
                                utils.escape_html(rule["entity_name"]),
                                self._convert_time(int(rule["expires"] - time.time())),
                                self.strings("for"),
                                self.strings(rule["rule_type"]),
                                rule["rule"],
                            )
                            for rule in self._client.dispatcher.security.tsec_chat
                        ]
                        + [
                            "<emoji document_id=6037122016849432064>👤</emoji> <b><a"
                            " href='{}'>{}</a> {} {} {}</b> <code>{}</code>".format(
                                rule["entity_url"],
                                utils.escape_html(rule["entity_name"]),
                                self._convert_time(int(rule["expires"] - time.time())),
                                self.strings("for"),
                                self.strings(rule["rule_type"]),
                                rule["rule"],
                            )
                            for rule in self._client.dispatcher.security.tsec_user
                        ]
                    )
                ),
            )
            return

        if args[0] not in {"user", "chat"}:
            await utils.answer(message, self.strings("what"))
            return

        await getattr(self, f"_tsec_{args[0]}")(message, args)
