#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from aiogram.types import Message as AiogramMessage
from typing import Optional, Union
from .types import InlineUnit


logger = logging.getLogger(__name__)


class BotPM(InlineUnit):
    def set_fsm_state(self, user: Union[str, int], state: Union[str, bool]) -> bool:
        if not isinstance(user, (str, int)):
            logger.error("Invalid type for `user` in `set_fsm_state`")
            return False

        if not isinstance(state, (str, bool)):
            logger.error("Invalid type for `state` in `set_fsm_state`")
            return False

        if state:
            self.fsm[str(user)] = state
        elif str(user) in self.fsm:
            del self.fsm[str(user)]

        return True

    ss = set_fsm_state

    def get_fsm_state(self, user: Union[str, int]) -> Union[bool, str]:
        if not isinstance(user, (str, int)):
            logger.error("Invalid type for `user` in `get_fsm_state`")
            return False

        return self.fsm.get(str(user), False)

    gs = get_fsm_state

    async def _bot_message_answer(self, text: str = None, message: AiogramMessage = None, parse_mode: Optional[str] = "HTML", disable_web_page_preview: Optional[bool] = True, **kwargs) -> bool:
        try:
            await self.bot.send_message(
                message.chat.id,
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                **kwargs
            )

        except Exception:
            return False

        return True
