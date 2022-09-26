#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import typing

from .types import InlineUnit


logger = logging.getLogger(__name__)


class BotPM(InlineUnit):
    def set_fsm_state(
        self,
        user: typing.Union[str, int],
        state: typing.Union[str, bool],
    ) -> bool:
        if not isinstance(user, (str, int)):
            logger.error(
                "Invalid type for `user` in `set_fsm_state`. Expected `str` or `int`,"
                " got %s",
                type(user),
            )
            return False

        if not isinstance(state, (str, bool)):
            logger.error(
                "Invalid type for `state` in `set_fsm_state`. Expected `str` or `bool`,"
                " got %s",
                type(state),
            )
            return False

        if state:
            self.fsm[str(user)] = state
        elif str(user) in self.fsm:
            del self.fsm[str(user)]

        return True

    ss = set_fsm_state

    def get_fsm_state(self, user: typing.Union[str, int]) -> typing.Union[bool, str]:
        if not isinstance(user, (str, int)):
            logger.error(
                "Invalid type for `user` in `get_fsm_state`. Expected `str` or `int`,"
                " got %s",
                type(user),
            )
            return False

        return self.fsm.get(str(user), False)

    gs = get_fsm_state
