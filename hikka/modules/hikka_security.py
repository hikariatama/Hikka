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

from types import FunctionType
from typing import List, Union
from telethon.tl.types import Message, User, PeerUser
from .. import loader, utils, main, security
from telethon.utils import get_display_name

import logging
import aiogram
from ..security import (
    SUDO,
    SUPPORT,
    GROUP_OWNER,
    GROUP_ADMIN_ADD_ADMINS,
    GROUP_ADMIN_CHANGE_INFO,
    GROUP_ADMIN_BAN_USERS,
    GROUP_ADMIN_DELETE_MESSAGES,
    GROUP_ADMIN_PIN_MESSAGES,
    GROUP_ADMIN_INVITE_USERS,
    GROUP_ADMIN,
    GROUP_MEMBER,
    PM,
    DEFAULT_PERMISSIONS,
    EVERYONE,
)

logger = logging.getLogger(__name__)


@loader.tds
class HikkaSecurityMod(loader.Module):
    """Control security settings"""

    strings = {
        "name": "HikkaSecurity",
        "no_command": "🚫 <b>Command </b><code>{}</code><b> not found!</b>",
        "permissions": "🔐 <b>Here you can configure permissions for </b><code>{}{}</code>",
        "close_menu": "🙈 Close this menu",
        "global": "🔐 <b>Here you can configure global bounding mask. If the permission is excluded here, it is excluded everywhere!</b>",
        "owner": "🤴 Owner",
        "sudo": "🤵 Sudo",
        "support": "💁‍♂️ Support",
        "group_owner": "🧛‍♂️ Group owner",
        "group_admin_add_admins": "👨‍💻 Admin (add members)",
        "group_admin_change_info": "👨‍💻 Admin (change info)",
        "group_admin_ban_users": "👨‍💻 Admin (ban)",
        "group_admin_delete_messages": "👨‍💻 Admin (delete msgs)",
        "group_admin_pin_messages": "👨‍💻 Admin (pin)",
        "group_admin_invite_users": "👨‍💻 Admin (invite)",
        "group_admin": "👨‍💻 Admin (any)",
        "group_member": "👥 In group",
        "pm": "🤙 In PM",
        "everyone": "🌍 Everyone (Inline)",
        "owner_list": "🤴 <b>Users in group </b><code>owner</code><b>:</b>\n\n{}",
        "sudo_list": "🤵‍♀️ <b>Users in group </b><code>sudo</code><b>:</b>\n\n{}",
        "support_list": "🙋‍♂️ <b>Users in group </b><code>support</code><b>:</b>\n\n{}",
        "no_owner": "🤴 <b>There is no users in group </b><code>owner</code>",
        "no_sudo": "🤵‍♀️ <b>There is no users in group </b><code>sudo</code>",
        "no_support": "🙋‍♂️ <b>There is no users in group </b><code>support</code>",
        "owner_added": '🤴 <b><a href="tg://user?id={}">{}</a> added to group </b><code>owner</code>',
        "sudo_added": '🤵‍♀️ <b><a href="tg://user?id={}">{}</a> added to group </b><code>sudo</code>',
        "support_added": '🙋‍♂️ <b><a href="tg://user?id={}">{}</a> added to group </b><code>support</code>',
        "owner_removed": '🤴 <b><a href="tg://user?id={}">{}</a> removed from group </b><code>owner</code>',
        "sudo_removed": '🤵‍♀️ <b><a href="tg://user?id={}">{}</a> removed from group </b><code>sudo</code>',
        "support_removed": '🙋‍♂️ <b><a href="tg://user?id={}">{}</a> removed from group </b><code>support</code>',
        "no_user": "🚫 <b>Specify user to permit</b>",
        "not_a_user": "🚫 <b>Specified entity is not a user</b>",
        "li": '⦿ <b><a href="tg://user?id={}">{}</a></b>',
        "warning": (
            '⚠️ <b>Please, confirm, that you want to add <a href="tg://user?id={}">{}</a> '
            "to group </b><code>{}</code><b>!\nThis action may reveal personal info and grant "
            "full or partial access to userbot to this user</b>"
        ),
        "cancel": "🚫 Cancel",
        "confirm": "👑 Confirm",
        "self": "🚫 <b>You can't promote/demote yourself!</b>",
    }

    strings_ru = {
        "no_command": "🚫 <b>Команда </b><code>{}</code><b> не найдена!</b>",
        "permissions": "🔐 <b>Здесь можно настроить разрешения для команды </b><code>{}{}</code>",
        "close_menu": "🙈 Закрыть это меню",
        "global": "🔐 <b>Здесь можно настроить глобальную исключающую маску. Если тумблер выключен здесь, он выключен для всех команд</b>",
        "owner": "🤴 Владелец",
        "sudo": "🤵 Sudo",
        "support": "💁‍♂️ Помощник",
        "group_owner": "🧛‍♂️ Влад. группы",
        "group_admin_add_admins": "👨‍💻 Админ (добавлять участников)",
        "group_admin_change_info": "👨‍💻 Админ (изменять инфо)",
        "group_admin_ban_users": "👨‍💻 Админ (банить)",
        "group_admin_delete_messages": "👨‍💻 Админ (удалять сообщения)",
        "group_admin_pin_messages": "👨‍💻 Админ (закреплять)",
        "group_admin_invite_users": "👨‍💻 Админ (приглашать)",
        "group_admin": "👨‍💻 Админ (любой)",
        "group_member": "👥 В группе",
        "pm": "🤙 В лс",
        "owner_list": "🤴 <b>Пользователи группы </b><code>owner</code><b>:</b>\n\n{}",
        "sudo_list": "🤵‍♀️ <b>Пользователи группы </b><code>sudo</code><b>:</b>\n\n{}",
        "support_list": "🙋‍♂️ <b>Пользователи группы </b><code>support</code><b>:</b>\n\n{}",
        "no_owner": "🤴 <b>Нет пользователей в группе </b><code>owner</code>",
        "no_sudo": "🤵‍♀️ <b>Нет пользователей в группе </b><code>sudo</code>",
        "no_support": "🙋‍♂️ <b>Нет пользователей в группе </b><code>support</code>",
        "no_user": "🚫 <b>Укажи, кому выдавать права</b>",
        "not_a_user": "🚫 <b>Указанная цель - не пользователь</b>",
        "cancel": "🚫 Отмена",
        "confirm": "👑 Подтвердить",
        "self": "🚫 <b>Нельзя управлять своими правами!</b>",
        "warning": (
            "⚠️ <b>Ты действительно хочешь добавить <a href=\"tg://user?id={}\">{}</a> "
            "в группу </b><code>{}</code><b>!\nЭто действие может передать частичный или"
            " полный доступ к юзерботу этому пользователю!</b>"
        ),
        "_cmd_doc_security": "[команда] - Изменить настройки безопасности для команды",
        "_cmd_doc_sudoadd": "<пользователь> - Добавить пользователя в группу `sudo`",
        "_cmd_doc_owneradd": "<пользователь> - Добавить пользователя в группу `owner`",
        "_cmd_doc_supportadd": "<пользователь> - Добавить пользователя в группу `support`",
        "_cmd_doc_sudorm": "<пользователь> - Удалить пользователя из группы `sudo`",
        "_cmd_doc_ownerrm": "<пользователь> - Удалить пользователя из группы `owner`",
        "_cmd_doc_supportrm": "<пользователь> - Удалить пользователя из группы `support`",
        "_cmd_doc_sudolist": "Показать пользователей в группе `sudo`",
        "_cmd_doc_ownerlist": "Показать пользователей в группе `owner`",
        "_cmd_doc_supportlist": "Показать пользователей в группе `support`",
        "_cls_doc": "Управление настройками безопасности",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def inline__switch_perm(
        self,
        call: aiogram.types.CallbackQuery,
        command: str,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        cmd = (
            self.allmodules.commands[command]
            if not is_inline
            else self.allmodules.inline_handlers[command]
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
                f"Security value set but not applied. Consider enabling this value in .{'inlinesec' if is_inline else 'security'}",
                show_alert=True,
            )
        else:
            await call.answer("Security value set!")

        await call.edit(
            self.strings("permissions").format(
                self.get_prefix() if not is_inline else f"@{self.inline.bot_username} ",
                command,
            ),
            reply_markup=self._build_markup(cmd, is_inline),
        )

    async def inline__switch_perm_bm(
        self,
        call: aiogram.types.CallbackQuery,
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

    @staticmethod
    async def inline_close(call: aiogram.types.CallbackQuery):
        await call.delete()

    def _build_markup(
        self,
        command: FunctionType,
        is_inline: bool = False,
    ) -> List[List[dict]]:
        perms = self._get_current_perms(command, is_inline)
        if not is_inline:
            return utils.chunks(
                [
                    {
                        "text": f"{('🚫' if not level else '✅')} {self.strings[group]}",
                        "callback": self.inline__switch_perm,
                        "args": (
                            command.__name__[:-3],
                            group,
                            not level,
                            is_inline,
                        ),
                    }
                    for group, level in perms.items()
                ],
                2,
            ) + [[{"text": self.strings("close_menu"), "callback": self.inline_close}]]

        return utils.chunks(
            [
                {
                    "text": f"{('🚫' if not level else '✅')} {self.strings[group]}",
                    "callback": self.inline__switch_perm,
                    "args": (
                        command.__name__[:-15],
                        group,
                        not level,
                        is_inline,
                    ),
                }
                for group, level in perms.items()
            ],
            2,
        ) + [[{"text": self.strings("close_menu"), "callback": self.inline_close}]]

    def _build_markup_global(self, is_inline: bool = False) -> List[List[dict]]:
        perms = self._get_current_bm(is_inline)
        return utils.chunks(
            [
                {
                    "text": f"{('🚫' if not level else '✅')} {self.strings[group]}",
                    "callback": self.inline__switch_perm_bm,
                    "args": (group, not level, is_inline),
                }
                for group, level in perms.items()
            ],
            2,
        ) + [[{"text": self.strings("close_menu"), "callback": self.inline_close}]]

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
                "group_owner": bool(perms & GROUP_OWNER),
                "group_admin_add_admins": bool(perms & GROUP_ADMIN_ADD_ADMINS),
                "group_admin_change_info": bool(perms & GROUP_ADMIN_CHANGE_INFO),
                "group_admin_ban_users": bool(perms & GROUP_ADMIN_BAN_USERS),
                "group_admin_delete_messages": bool(perms & GROUP_ADMIN_DELETE_MESSAGES),  # fmt: skip
                "group_admin_pin_messages": bool(perms & GROUP_ADMIN_PIN_MESSAGES),
                "group_admin_invite_users": bool(perms & GROUP_ADMIN_INVITE_USERS),
                "group_admin": bool(perms & GROUP_ADMIN),
                "group_member": bool(perms & GROUP_MEMBER),
                "pm": bool(perms & PM),
                "everyone": bool(perms & EVERYONE),
            }
            if not is_inline
            else {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
                "everyone": bool(perms & EVERYONE),
            }
        )

    def _get_current_perms(
        self,
        command: FunctionType,
        is_inline: bool = False,
    ) -> dict:
        config = self._db.get(security.__name__, "masks", {}).get(
            f"{command.__module__}.{command.__name__}",
            getattr(command, "security", self._client.dispatcher.security._default),
        )

        return self._perms_map(config, is_inline)

    async def securitycmd(self, message: Message):
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

    async def inlineseccmd(self, message: Message):
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

        if user.id == self._tg_id:
            await utils.answer(message, self.strings("self"))
            return

        return user

    async def _add_to_group(
        self,
        message: Union[Message, "aigoram.types.CallbackQuery"],  # noqa: F821
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
                    user.id, utils.escape_html(get_display_name(user)), group
                ),
                message=message,
                ttl=10 * 60,
                reply_markup=[
                    [
                        {
                            "text": self.strings("cancel"),
                            "callback": self.inline_close,
                        },
                        {
                            "text": self.strings("confirm"),
                            "callback": self._add_to_group,
                            "args": (group, True, user.id),
                        },
                    ]
                ],
            )
            return

        self._db.set(
            security.__name__,
            group,
            list(set(self._db.get(security.__name__, group, []) + [user.id])),
        )

        m = self.strings(f"{group}_added").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        if isinstance(message, Message):
            await utils.answer(
                message,
                m,
            )
        else:
            await message.edit(m)

    async def _remove_from_group(self, message: Message, group: str):
        user = await self._resolve_user(message)
        if not user:
            return

        self._db.set(
            security.__name__,
            group,
            list(set(self._db.get(security.__name__, group, [])) - set([user.id])),
        )

        m = self.strings(f"{group}_removed").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        await utils.answer(message, m)

    async def _list_group(self, message: Message, group: str):
        _resolved_users = []
        for user in self._db.get(security.__name__, group, []) + (
            [self._tg_id] if group == "owner" else []
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

    async def sudoaddcmd(self, message: Message):
        """<user> - Add user to `sudo`"""
        await self._add_to_group(message, "sudo")

    async def owneraddcmd(self, message: Message):
        """<user> - Add user to `owner`"""
        await self._add_to_group(message, "owner")

    async def supportaddcmd(self, message: Message):
        """<user> - Add user to `support`"""
        await self._add_to_group(message, "support")

    async def sudormcmd(self, message: Message):
        """<user> - Remove user from `sudo`"""
        await self._remove_from_group(message, "sudo")

    async def ownerrmcmd(self, message: Message):
        """<user> - Remove user from `owner`"""
        await self._remove_from_group(message, "owner")

    async def supportrmcmd(self, message: Message):
        """<user> - Remove user from `support`"""
        await self._remove_from_group(message, "support")

    async def sudolistcmd(self, message: Message):
        """List users in `sudo`"""
        await self._list_group(message, "sudo")

    async def ownerlistcmd(self, message: Message):
        """List users in `owner`"""
        await self._list_group(message, "owner")

    async def supportlistcmd(self, message: Message):
        """List users in `support`"""
        await self._list_group(message, "support")
