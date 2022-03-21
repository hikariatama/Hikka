#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#    Modded by GeekTG Team

import logging

import telethon
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import GetFullChatRequest

from . import main

logger = logging.getLogger(__name__)

OWNER = 1 << 0
SUDO = 1 << 1
SUPPORT = 1 << 2
GROUP_OWNER = 1 << 3
GROUP_ADMIN_ADD_ADMINS = 1 << 4
GROUP_ADMIN_CHANGE_INFO = 1 << 5
GROUP_ADMIN_BAN_USERS = 1 << 6
GROUP_ADMIN_DELETE_MESSAGES = 1 << 7
GROUP_ADMIN_PIN_MESSAGES = 1 << 8
GROUP_ADMIN_INVITE_USERS = 1 << 9
GROUP_ADMIN = 1 << 10
GROUP_MEMBER = 1 << 11
PM = 1 << 12

BITMAP = {
    "OWNER": OWNER,
    "SUDO": SUDO,
    "SUPPORT": SUPPORT,
    "GROUP_OWNER": GROUP_OWNER,
    "GROUP_ADMIN_ADD_ADMINS": GROUP_ADMIN_ADD_ADMINS,
    "GROUP_ADMIN_CHANGE_INFO": GROUP_ADMIN_CHANGE_INFO,
    "GROUP_ADMIN_BAN_USERS": GROUP_ADMIN_BAN_USERS,
    "GROUP_ADMIN_DELETE_MESSAGES": GROUP_ADMIN_DELETE_MESSAGES,
    "GROUP_ADMIN_PIN_MESSAGES": GROUP_ADMIN_PIN_MESSAGES,
    "GROUP_ADMIN_INVITE_USERS": GROUP_ADMIN_INVITE_USERS,
    "GROUP_ADMIN": GROUP_ADMIN,
    "GROUP_MEMBER": GROUP_MEMBER,
    "PM": PM,
}

GROUP_ADMIN_ANY = (
    GROUP_ADMIN_ADD_ADMINS
    | GROUP_ADMIN_CHANGE_INFO
    | GROUP_ADMIN_BAN_USERS
    | GROUP_ADMIN_DELETE_MESSAGES
    | GROUP_ADMIN_PIN_MESSAGES
    | GROUP_ADMIN_INVITE_USERS
    | GROUP_ADMIN
)

DEFAULT_PERMISSIONS = OWNER | SUDO

PUBLIC_PERMISSIONS = GROUP_OWNER | GROUP_ADMIN_ANY | GROUP_MEMBER | PM

ALL = (1 << 13) - 1


def owner(func):
    return _sec(func, OWNER)


def sudo(func):
    return _sec(func, OWNER | SUDO)


def support(func):
    return _sec(func, OWNER | SUDO | SUPPORT)


def group_owner(func):
    return _sec(func, OWNER | SUDO | GROUP_OWNER)


def group_admin_add_admins(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN_ADD_ADMINS)


def group_admin_change_info(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN_CHANGE_INFO)


def group_admin_ban_users(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN_BAN_USERS)


def group_admin_delete_messages(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN_DELETE_MESSAGES)


def group_admin_pin_messages(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN_PIN_MESSAGES)


def group_admin_invite_users(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN_INVITE_USERS)


def group_admin(func):
    return _sec(func, OWNER | SUDO | GROUP_ADMIN)


def group_member(func):
    return _sec(func, OWNER | SUDO | GROUP_MEMBER)


def pm(func):
    return _sec(func, OWNER | SUDO | PM)


def unrestricted(func):
    return _sec(func, ALL)


def _sec(func, flags):
    prev = getattr(func, "security", 0)
    func.security = prev | flags
    return func


class SecurityManager:
    def __init__(self, db):
        self._any_admin = db.get(__name__, "any_admin", False)
        self._default = db.get(__name__, "default", DEFAULT_PERMISSIONS)
        self._db = db
        self._reload_rights()

    def _reload_rights(self) -> None:
        self._owner = self._db.get(__name__, "owner", []).copy()
        self._sudo = list(
            set(
                self._db.get(__name__, "sudo", []).copy()
                + ([self._me] if hasattr(self, "_me") else [])
            )
        )
        self._support = self._db.get(__name__, "support", []).copy()

    async def init(self, client):
        self._client = client
        self._me = (await client.get_me()).id

    def get_flags(self, func):
        if isinstance(func, int):
            config = func
        else:
            # Return masks there so user don't need to reboot
            # every time he changes permissions. It doesn't
            # decrease security at all, bc user anyway can
            # access this attribute
            config = self._db.get(__name__, "masks", {}).get(
                f"{func.__module__}.{func.__name__}",
                getattr(func, "security", self._default),
            )

        if config & ~ALL:
            logger.error("Security config contains unknown bits")
            return False

        return config & self._db.get(__name__, "bounding_mask", DEFAULT_PERMISSIONS)

    async def _check(self, message, func):
        self._reload_rights()
        config = self.get_flags(func)

        if not config:  # Either False or 0, either way we can failfast
            return False

        logger.debug("Checking security match for %d", config)

        f_owner = config & OWNER
        f_sudo = config & SUDO
        f_support = config & SUPPORT
        f_group_owner = config & GROUP_OWNER
        f_group_admin_add_admins = config & GROUP_ADMIN_ADD_ADMINS
        f_group_admin_change_info = config & GROUP_ADMIN_CHANGE_INFO
        f_group_admin_ban_users = config & GROUP_ADMIN_BAN_USERS
        f_group_admin_delete_messages = config & GROUP_ADMIN_DELETE_MESSAGES
        f_group_admin_pin_messages = config & GROUP_ADMIN_PIN_MESSAGES
        f_group_admin_invite_users = config & GROUP_ADMIN_INVITE_USERS
        f_group_admin = config & GROUP_ADMIN
        f_group_member = config & GROUP_MEMBER
        f_pm = config & PM

        f_group_admin_any = (
            f_group_admin_add_admins
            or f_group_admin_change_info
            or f_group_admin_ban_users
            or f_group_admin_delete_messages
            or f_group_admin_pin_messages
            or f_group_admin_invite_users
            or f_group_admin
        )

        if f_owner and message.sender_id in self._owner + [self._me]:
            return True

        if f_sudo and message.sender_id in self._sudo:
            return True

        if f_support and message.sender_id in self._support:
            return True

        if message.sender_id in self._db.get(main.__name__, "blacklist_users", []):
            return False

        if f_pm and message.is_private:
            return True

        if f_group_member and message.is_group:
            return True

        if message.is_channel:
            if not message.is_group:
                if message.edit_date:
                    return False

                chat = await message.get_chat()

                if not chat.creator and not (
                    chat.admin_rights and chat.admin_rights.post_messages
                ):
                    return False

                if self._any_admin and f_group_admin_any:
                    return True

                if f_group_admin:
                    return True
            else:
                if f_group_admin_any or f_group_owner:
                    participant = await message.client(
                        GetParticipantRequest(
                            await message.get_input_chat(),
                            await message.get_input_sender(),
                        )
                    )
                    participant = participant.participant

                    if isinstance(
                        participant, telethon.types.ChannelParticipantCreator
                    ):
                        return True

                    if isinstance(participant, telethon.types.ChannelParticipantAdmin):
                        if self._any_admin and f_group_admin_any:
                            return True
                        rights = participant.admin_rights

                        if (
                            f_group_admin
                            or f_group_admin_add_admins
                            and rights.add_admins
                            or f_group_admin_change_info
                            and rights.change_info
                            or f_group_admin_ban_users
                            and rights.ban_users
                            or f_group_admin_delete_messages
                            and rights.delete_messages
                            or f_group_admin_pin_messages
                            and rights.pin_messages
                            or f_group_admin_invite_users
                            and rights.invite_users
                        ):
                            return True

                chat = await message.get_chat()

            if message.out:
                if chat.creator and f_group_owner:
                    return True
                me_id = (await message.client.get_me(True)).user_id

                if (
                    f_owner
                    and me_id in self._owner
                    or f_sudo
                    and me_id in self._sudo
                    or f_support
                    and me_id in self._support
                ):
                    return True

        elif message.is_group:
            if f_group_admin_any or f_group_owner:
                full_chat = await message.client(GetFullChatRequest(message.chat_id))
                participants = full_chat.full_chat.participants.participants
                participant = next(
                    (
                        possible_participant
                        for possible_participant in participants
                        if possible_participant.user_id == message.sender_id
                    ),
                    None,
                )

                if not participant:
                    return

                if isinstance(participant, telethon.types.ChatParticipantCreator):
                    return True

            if (
                isinstance(participant, telethon.types.ChatParticipantAdmin)
                and f_group_admin_any
            ):
                return True

        return False

    check = _check
