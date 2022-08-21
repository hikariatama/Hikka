#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: inline

import logging
import time
from typing import List, Union

from telethon.tl.types import Message, PeerUser, User
from telethon.utils import get_display_name
from telethon.hints import EntityLike

from .. import loader, security, utils, main
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
    SUDO,
    SUPPORT,
)

logger = logging.getLogger(__name__)


@loader.tds
class HikkaSecurityMod(loader.Module):
    """Control security settings"""

    service_strings = {
        "for": "for",
        "forever": "forever",
        "user": "user",
        "chat": "chat",
        "command": "command",
        "module": "module",
        "day": "day",
        "days": "days",
        "hour": "hour",
        "hours": "hours",
        "minute": "minute",
        "minutes": "minutes",
        "second": "second",
        "seconds": "seconds",
    }

    service_strings_ru = {
        "for": "на",
        "forever": "навсегда",
        "command": "команду",
        "module": "модуль",
        "chat": "чату",
        "user": "пользователю",
        "day": "день",
        "days": "дня(-ей)",
        "hour": "час",
        "hours": "часа(-ов)",
        "minute": "минута",
        "minutes": "минут(-ы)",
        "second": "секунда",
        "seconds": "секунд(-ы)",
    }

    strings = {
        "name": "HikkaSecurity",
        "no_command": "🚫 <b>Command </b><code>{}</code><b> not found!</b>",
        "permissions": (
            "🔐 <b>Here you can configure permissions for </b><code>{}{}</code>"
        ),
        "close_menu": "🙈 Close this menu",
        "global": (
            "🔐 <b>Here you can configure global bounding mask. If the permission is"
            " excluded here, it is excluded everywhere!</b>"
        ),
        "owner": "😎 Owner",
        "sudo": "🧐 Sudo",
        "support": "🤓 Support",
        "group_owner": "🧛‍♂️ Group owner",
        "group_admin_add_admins": "🧑‍⚖️ Admin (add members)",
        "group_admin_change_info": "🧑‍⚖️ Admin (change info)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (ban)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (delete msgs)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (pin)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (invite)",
        "group_admin": "🧑‍⚖️ Admin (any)",
        "group_member": "👥 In group",
        "pm": "🤙 In PM",
        "everyone": "🌍 Everyone (Inline)",
        "owner_list": (
            "<emoji document_id='5386399931378440814'>😎</emoji> <b>Users in group"
            " </b><code>owner</code><b>:</b>\n\n{}"
        ),
        "sudo_list": (
            "<emoji document_id='5418133868475587618'>🧐</emoji> <b>Users in group"
            " </b><code>sudo</code><b>:</b>\n\n{}"
        ),
        "support_list": (
            "<emoji document_id='5415729507128580146'>🤓</emoji> <b>Users in group"
            " </b><code>support</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id='5386399931378440814'>😎</emoji> <b>There is no users in"
            " group </b><code>owner</code>"
        ),
        "no_sudo": (
            "<emoji document_id='5418133868475587618'>🧐</emoji> <b>There is no users in"
            " group </b><code>sudo</code>"
        ),
        "no_support": (
            "<emoji document_id='5415729507128580146'>🤓</emoji> <b>There is no users in"
            " group </b><code>support</code>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>owner</code>'
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>sudo</code>'
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>support</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>owner</code>'
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>sudo</code>'
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>support</code>'
        ),
        "no_user": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Specify user to"
            " permit</b>"
        ),
        "not_a_user": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Specified entity is"
            " not a user</b>"
        ),
        "li": '⦿ <b><a href="tg://user?id={}">{}</a></b>',
        "warning": (
            "⚠️ <b>Please, confirm, that you want to add <a"
            ' href="tg://user?id={}">{}</a> to group </b><code>{}</code><b>!\nThis'
            " action may reveal personal info and grant full or partial access to"
            " userbot to this user</b>"
        ),
        "cancel": "🚫 Cancel",
        "confirm": "👑 Confirm",
        "enable_nonick_btn": "🔰 Enable",
        "self": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>You can't"
            " promote/demote yourself!</b>"
        ),
        "suggest_nonick": "🔰 <i>Do you want to enable NoNick for this user?</i>",
        "user_nn": '🔰 <b>NoNick for <a href="tg://user?id={}">{}</a> enabled</b>',
        "what": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>You need to specify"
            " the type of target as first argument (</b><code>user</code><b> or"
            " </b><code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>You didn't specify"
            " the target of security rule</b>"
        ),
        "no_rule": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>You didn't specify"
            " the rule (module or command)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Please, confirm that you want to give {} <a href='{}'>{}</a> a"
            " permission to use {} </b><code>{}</code><b> {}?</b>"
        ),
        "rule_added": (
            "🔐 <b>You gave {} <a href='{}'>{}</a> a"
            " permission to use {} </b><code>{}</code><b> {}</b>"
        ),
        "confirm_btn": "👑 Confirm",
        "cancel_btn": "🚫 Cancel",
        "multiple_rules": (
            "🔐 <b>Unable to unambiguously determine the security rule. Please, choose"
            " the one you meant:</b>\n\n{}"
        ),
        "rules": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Targeted security"
            " rules:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>No targeted security"
            " rules</b>"
        ),
        "owner_target": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>This user is owner"
            " and can't be promoted by targeted security</b>"
        ),
        "rules_removed": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Targeted security"
            ' rules for <a href="{}">{}</a> removed</b>'
        ),
        **service_strings,
    }

    strings_ru = {
        "no_command": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Команда"
            " </b><code>{}</code><b> не найдена!</b>"
        ),
        "permissions": (
            "🔐 <b>Здесь можно настроить разрешения для команды </b><code>{}{}</code>"
        ),
        "close_menu": "🙈 Закрыть это меню",
        "global": (
            "🔐 <b>Здесь можно настроить глобальную исключающую маску. Если тумблер"
            " выключен здесь, он выключен для всех команд</b>"
        ),
        "owner": "😎 Владелец",
        "sudo": "🧐 Sudo",
        "support": "🤓 Помощник",
        "group_owner": "🧛‍♂️ Влад. группы",
        "group_admin_add_admins": "🧑‍⚖️ Админ (добавлять участников)",
        "group_admin_change_info": "🧑‍⚖️ Админ (изменять инфо)",
        "group_admin_ban_users": "🧑‍⚖️ Админ (банить)",
        "group_admin_delete_messages": "🧑‍⚖️ Админ (удалять сообщения)",
        "group_admin_pin_messages": "🧑‍⚖️ Админ (закреплять)",
        "group_admin_invite_users": "🧑‍⚖️ Админ (приглашать)",
        "group_admin": "🧑‍⚖️ Админ (любой)",
        "group_member": "👥 В группе",
        "pm": "🤙 В лс",
        "owner_list": (
            "<emoji document_id='5386399931378440814'>😎</emoji> <b>Пользователи группы"
            " </b><code>owner</code><b>:</b>\n\n{}"
        ),
        "sudo_list": (
            "<emoji document_id='5418133868475587618'>🧐</emoji> <b>Пользователи группы"
            " </b><code>sudo</code><b>:</b>\n\n{}"
        ),
        "support_list": (
            "<emoji document_id='5415729507128580146'>🤓</emoji> <b>Пользователи группы"
            " </b><code>support</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id='5386399931378440814'>😎</emoji> <b>Нет пользователей в"
            " группе </b><code>owner</code>"
        ),
        "no_sudo": (
            "<emoji document_id='5418133868475587618'>🧐</emoji> <b>Нет пользователей в"
            " группе </b><code>sudo</code>"
        ),
        "no_support": (
            "<emoji document_id='5415729507128580146'>🤓</emoji> <b>Нет пользователей в"
            " группе </b><code>support</code>"
        ),
        "no_user": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Укажи, кому выдавать"
            " права</b>"
        ),
        "not_a_user": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Указанная цель - не"
            " пользователь</b>"
        ),
        "cancel": "🚫 Отмена",
        "confirm": "👑 Подтвердить",
        "self": (
            "<emoji document_id='5415905755406539934'>🚫</emoji> <b>Нельзя управлять"
            " своими правами!</b>"
        ),
        "warning": (
            '⚠️ <b>Ты действительно хочешь добавить <a href="tg://user?id={}">{}</a> в'
            " группу </b><code>{}</code><b>!\nЭто действие может передать частичный или"
            " полный доступ к юзерботу этому пользователю!</b>"
        ),
        "suggest_nonick": (
            "🔰 <i>Хочешь ли ты включить NoNick для этого пользователя?</i>"
        ),
        "user_nn": '🔰 <b>NoNick для <a href="tg://user?id={}">{}</a> включен</b>',
        "enable_nonick_btn": "🔰 Включить",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу </b><code>owner</code>'
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу </b><code>sudo</code>'
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу </b><code>support</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы </b><code>owner</code>'
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы </b><code>sudo</code>'
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы </b><code>support</code>'
        ),
        "_cls_doc": "Управление настройками безопасности",
        "what": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>Вам нужно указать"
            " тип цели первым аргументов (</b><code>user</code><b> or"
            " </b><code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>Не указана цель"
            " правила безопасности</b>"
        ),
        "no_rule": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>Не указано правило"
            " безопасности (модуль или команда)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Пожалуйста, подтвердите что хотите выдать {} <a href='{}'>{}</a>"
            " право использовать {} </b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Не получилось однозначно распознать правила безопасности. Выберите"
            " то, которое имели ввиду:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Вы выдали {} <a href='{}'>{}</a> право"
            " использовать {} </b><code>{}</code><b> {}</b>"
        ),
        "rules": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Таргетированные"
            " правила безопасности:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>Нет таргетированных"
            " правил безопасности</b>"
        ),
        "owner_target": (
            "<emoji document_id='6053166094816905153'>🚫</emoji> <b>Этот пользователь -"
            " владелец, его права не могут управляться таргетированной"
            " безопасностью</b>"
        ),
        "rules_removed": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Правила"
            ' таргетированной безопасности для <a href="{}">{}</a> удалены</b>'
        ),
        **service_strings_ru,
    }

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
                "Security value set but not applied. Consider enabling this value in"
                f" .{'inlinesec' if is_inline else 'security'}",
                show_alert=True,
            )
        else:
            await call.answer("Security value set!")

        await call.edit(
            self.strings("permissions").format(
                f"@{self.inline.bot_username} " if is_inline else self.get_prefix(),
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
    ) -> List[List[dict]]:
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

    def _build_markup_global(self, is_inline: bool = False) -> List[List[dict]]:
        perms = self._get_current_bm(is_inline)
        return utils.chunks(
            [
                {
                    "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                    "callback": self.inline__switch_perm_bm,
                    "args": (group, not level, is_inline),
                }
                for group, level in perms.items()
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
            {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
                "everyone": bool(perms & EVERYONE),
            }
            if is_inline
            else {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
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
        config = self._db.get(security.__name__, "masks", {}).get(
            f"{command.__module__}.{command.__name__}",
            getattr(command, "security", self._client.dispatcher.security.default),
        )

        return self._perms_map(config, is_inline)

    @loader.owner
    @loader.command(ru_doc="[команда] - Настроить разрешения для команды")
    async def security(self, message: Message):
        """[command] - Configure command's security settings"""
        args = utils.get_args_raw(message).lower().strip()
        if args and args not in self.allmodules.commands:
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

        cmd = self.allmodules.commands[args]

        await self.inline.form(
            self.strings("permissions").format(self.get_prefix(), args),
            reply_markup=self._build_markup(cmd),
            message=message,
            ttl=5 * 60,
        )

    @loader.owner
    @loader.command(ru_doc="[команда] - Настроить разрешения для инлайн команды")
    async def inlinesec(self, message: Message):
        """[command] - Configure inline command's security settings"""
        args = utils.get_args_raw(message).lower().strip()
        if not args:
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

        i_handler = self.allmodules.inline_handlers[args]
        await self.inline.form(
            self.strings("permissions").format(f"@{self.inline.bot_username} ", args),
            reply_markup=self._build_markup(i_handler, True),
            message=message,
            ttl=5 * 60,
        )

    async def _resolve_user(self, message: Message):
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)

        if not args and not reply:
            await utils.answer(message, self.strings("no_user"))
            return

        user = None

        if args:
            try:
                if str(args).isdigit():
                    args = int(args)

                user = await self._client.get_entity(args)
            except Exception:
                pass

        if user is None:
            user = await self._client.get_entity(reply.sender_id)

        if not isinstance(user, (User, PeerUser)):
            await utils.answer(message, self.strings("not_a_user"))
            return

        if user.id == self.tg_id:
            await utils.answer(message, self.strings("self"))
            return

        return user

    async def _add_to_group(
        self,
        message: Union[Message, InlineCall],  # noqa: F821
        group: str,
        confirmed: bool = False,
        user: int = None,
    ):
        if user is None:
            user = await self._resolve_user(message)
            if not user:
                return

        if isinstance(user, int):
            user = await self._client.get_entity(user)

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

        m = (
            self.strings(f"{group}_added").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            )
            + "\n\n"
            + self.strings("suggest_nonick")
        )

        await utils.answer(message, m)
        await message.edit(
            m,
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

    async def _remove_from_group(self, message: Message, group: str):
        user = await self._resolve_user(message)
        if not user:
            return

        if user.id in getattr(self._client.dispatcher.security, group):
            getattr(self._client.dispatcher.security, group).remove(user.id)

        m = self.strings(f"{group}_removed").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        await utils.answer(message, m)

    async def _list_group(self, message: Message, group: str):
        _resolved_users = []
        for user in getattr(self._client.dispatcher.security, group) + (
            [self.tg_id] if group == "owner" else []
        ):
            try:
                _resolved_users += [await self._client.get_entity(user)]
            except Exception:
                pass

        if _resolved_users:
            await utils.answer(
                message,
                self.strings(f"{group}_list").format(
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
        else:
            await utils.answer(message, self.strings(f"no_{group}"))

    @loader.command(ru_doc="<пользователь> - Добавить пользователя в группу `sudo`")
    async def sudoadd(self, message: Message):
        """<user> - Add user to `sudo`"""
        await self._add_to_group(message, "sudo")

    @loader.command(ru_doc="<пользователь> - Добавить пользователя в группу `owner`")
    async def owneradd(self, message: Message):
        """<user> - Add user to `owner`"""
        await self._add_to_group(message, "owner")

    @loader.command(ru_doc="<пользователь> - Добавить пользователя в группу `support`")
    async def supportadd(self, message: Message):
        """<user> - Add user to `support`"""
        await self._add_to_group(message, "support")

    @loader.command(ru_doc="<пользователь> - Удалить пользователя из группы `sudo`")
    async def sudorm(self, message: Message):
        """<user> - Remove user from `sudo`"""
        await self._remove_from_group(message, "sudo")

    @loader.command(ru_doc="<пользователь> - Удалить пользователя из группы `owner`")
    async def ownerrm(self, message: Message):
        """<user> - Remove user from `owner`"""
        await self._remove_from_group(message, "owner")

    @loader.command(ru_doc="<пользователь> - Удалить пользователя из группы `support`")
    async def supportrm(self, message: Message):
        """<user> - Remove user from `support`"""
        await self._remove_from_group(message, "support")

    @loader.command(ru_doc="Показать список пользователей в группе `sudo`")
    async def sudolist(self, message: Message):
        """List users in `sudo`"""
        await self._list_group(message, "sudo")

    @loader.command(ru_doc="Показать список пользователей в группе `owner`")
    async def ownerlist(self, message: Message):
        """List users in `owner`"""
        await self._list_group(message, "owner")

    @loader.command(ru_doc="Показать список пользователей в группе `support`")
    async def supportlist(self, message: Message):
        """List users in `support`"""
        await self._list_group(message, "support")

    def _lookup(self, needle: str) -> str:
        return (
            []
            if needle.lower().startswith(self.get_prefix())
            else (
                [f"module/{self.lookup(needle).__class__.__name__}"]
                if self.lookup(needle)
                else []
            )
        ) + (
            [f"command/{needle.lower().strip(self.get_prefix())}"]
            if needle.lower().strip(self.get_prefix()) in self.allmodules.commands
            else []
        )

    @staticmethod
    def _extract_time(args: list) -> int:
        suffixes = {
            "d": 24 * 60 * 60,
            "h": 60 * 60,
            "m": 60,
            "s": 1,
        }
        for suffix, quantifier in suffixes.items():
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

    def _convert_time(self, duration: int) -> str:
        return (
            (
                f"{duration // (24 * 60 * 60)} "
                + self.strings(f"day{'s' if duration // (24 * 60 * 60) > 1 else ''}")
            )
            if duration >= 24 * 60 * 60
            else (
                (
                    f"{duration // (60 * 60)} "
                    + self.strings(f"hour{'s' if duration // (60 * 60) > 1 else ''}")
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

    async def _add_rule(
        self,
        call: InlineCall,
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
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
                rule.split("/", maxsplit=1)[1],
                (self.strings("for") + " " + self._convert_time(duration))
                if duration
                else self.strings("forever"),
            )
        )

    async def _confirm(
        self,
        obj: Union[Message, InlineMessage],
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
                rule.split("/", maxsplit=1)[1],
                (self.strings("for") + " " + self._convert_time(duration))
                if duration
                else self.strings("forever"),
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
                    int(args[1]) if args[1].isdigit() else args[1]
                )
            except (ValueError, TypeError):
                if not message.is_private:
                    target = await self._client.get_entity(message.peer_id)
                else:
                    await utils.answer(message, self.strings("no_target"))
                    return

        duration = self._extract_time(args)

        possible_rules = utils.array_sum([self._lookup(arg) for arg in args])
        if not possible_rules:
            await utils.answer(message, self.strings("no_rule"))
            return

        if len(possible_rules) > 1:

            def case(text: str) -> str:
                return text.upper()[0] + text[1:]

            await self.inline.form(
                message=message,
                text=self.strings("multiple_rules").format(
                    "\n".join(
                        f"🛡 <b>{case(self.strings(i.split('/')[0]))} </b><code>{i.split('/', maxsplit=1)[1]}</code>"
                        for i in possible_rules
                    )
                ),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": (
                                f"🛡 {case(self.strings(i.split('/')[0]))} {i.split('/', maxsplit=1)[1]}"
                            ),
                            "callback": self._confirm,
                            "args": ("chat", target, i, duration),
                        }
                        for i in possible_rules
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
                    int(args[1]) if args[1].isdigit() else args[1]
                )
            except (ValueError, TypeError):
                if message.is_private:
                    target = await self._client.get_entity(message.peer_id)
                elif message.is_reply:
                    target = await self._client.get_entity(
                        (await message.get_reply_message()).sender_id
                    )
                else:
                    await utils.answer(message, self.strings("no_target"))
                    return

        if target.id in self._client.dispatcher.security.owner:
            await utils.answer(message, self.strings("owner_target"))
            return

        duration = self._extract_time(args)

        possible_rules = utils.array_sum([self._lookup(arg) for arg in args])
        if not possible_rules:
            await utils.answer(message, self.strings("no_rule"))
            return

        if len(possible_rules) > 1:

            def case(text: str) -> str:
                return text.upper()[0] + text[1:]

            await self.inline.form(
                message=message,
                text=self.strings("multiple_rules").format(
                    "\n".join(
                        f"🛡 <b>{case(self.strings(i.split('/')[0]))} </b><code>{i.split('/', maxsplit=1)[1]}</code>"
                        for i in possible_rules
                    )
                ),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": (
                                f"🛡 {case(self.strings(i.split('/')[0]))} {i.split('/', maxsplit=1)[1]}"
                            ),
                            "callback": self._confirm,
                            "args": ("user", target, i, duration),
                        }
                        for i in possible_rules
                    ],
                    3,
                ),
            )
            return

        await self._confirm(message, "user", target, possible_rules[0], duration)

    @loader.command(
        ru_doc='<"user"/"chat"> - Удалить правило таргетированной безопасности'
    )
    async def tsecrm(self, message: Message):
        """<"user"/"chat"> - Remove targeted security rule"""
        if (
            not self._client.dispatcher.security.tsec_chat
            and not self._client.dispatcher.security.tsec_user
        ):
            await utils.answer(message, self.strings("no_rules"))
            return

        args = utils.get_args_raw(message)
        if not args or args not in {"user", "chat"}:
            await utils.answer(message, self.strings("no_target"))
            return

        if args == "user":
            if not message.is_private and not message.is_reply:
                await utils.answer(message, self.strings("no_target"))
                return
            if message.is_private:
                target = await self._client.get_entity(message.peer_id)
            elif message.is_reply:
                target = await self._client.get_entity(
                    (await message.get_reply_message()).sender_id
                )
            else:
                await utils.answer(message, self.strings("no_target"))
                return

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
        elif args == "chat":
            if message.is_private:
                await utils.answer(message, self.strings("no_target"))
                return

            target = await self._client.get_entity(message.peer_id)

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
            return

    @loader.command(
        ru_doc=(
            '<"user"/"chat"> [цель - пользователь или чат] [правило - команда или'
            " модуль] [время] - Настроить таргетированную безопасность"
        )
    )
    async def tsec(self, message: Message):
        """<"user"/"chat"> [target user or chat] [rule (command/module)] [time] - Add new targeted security rule"""
        args = utils.get_args(message)
        if not args:
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
                            "<emoji document_id='6037355667365300960'>👥</emoji> <b><a"
                            f" href='{rule['entity_url']}'>{utils.escape_html(rule['entity_name'])}</a>"
                            f" {self._convert_time(int(rule['expires'] - time.time()))} {self.strings('for')} {self.strings(rule['rule_type'])}</b>"
                            f" <code>{rule['rule']}</code>"
                            for rule in self._client.dispatcher.security.tsec_chat
                        ]
                        + [
                            "<emoji document_id='6037122016849432064'>👤</emoji> <b><a"
                            f" href='{rule['entity_url']}'>{utils.escape_html(rule['entity_name'])}</a>"
                            f" {self._convert_time(int(rule['expires'] - time.time()))} {self.strings('for')} {self.strings(rule['rule_type'])}</b>"
                            f" <code>{rule['rule']}</code>"
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
