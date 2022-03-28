from .types import InlineUnit

from aiogram.types import Message as AiogramMessage

from typing import Union
import logging

logger = logging.getLogger(__name__)


class BotInteractions(InlineUnit):
    def ss(self, user: Union[str, int], state: Union[str, bool]) -> bool:
        if not isinstance(user, (str, int)):
            logger.error("Invalid type for `user` in `ss`")
            return False

        if not isinstance(state, (str, bool)):
            logger.error("Invalid type for `state` in `ss`")
            return False

        if state:
            self.fsm[str(user)] = state
        elif str(user) in self.fsm:
            del self.fsm[str(user)]

        return True

    def gs(self, user: Union[str, int]) -> Union[bool, str]:
        if not isinstance(user, (str, int)):
            logger.error("Invalid type for `user` in `gs`")
            return False

        return self.fsm.get(str(user), False)

    async def _bot_message_answer(  # skipcq: PYL-E0213
        mod,
        text: str = None,
        message: AiogramMessage = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        **kwargs,
    ) -> bool:
        try:
            await mod.bot.send_message(
                message.chat.id,
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                **kwargs,
            )
        except Exception:
            return False

        return True
