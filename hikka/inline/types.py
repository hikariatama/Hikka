from aiogram.types import (
    Message as AiogramMessage,
    InlineQuery as AiogramInlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
)
import logging
from .. import utils

logger = logging.getLogger(__name__)


class InlineMessage:
    """Aiogram message, send via inline bot"""

    def __init__(
        self,
        inline_manager: "InlineManager",  # noqa: F821
        unit_uid: str,
        inline_message_id: str,
    ):
        self.inline_message_id = inline_message_id
        self.unit_uid = unit_uid
        self.inline_manager = inline_manager
        self._units = {
            **inline_manager._forms,
            **inline_manager._lists,
            **inline_manager._galleries,
        }
        self.form = (
            {"id": unit_uid, **self._units[unit_uid]} if unit_uid in self._units else {}
        )

    async def edit(self, *args, **kwargs) -> "InlineMessage":
        if "unit_uid" in kwargs:
            kwargs.pop("unit_uid")

        if "inline_message_id" in kwargs:
            kwargs.pop("inline_message_id")

        return await self.inline_manager._edit_unit(
            *args,
            unit_uid=self.unit_uid,
            inline_message_id=self.inline_message_id,
            **kwargs,
        )

    async def delete(self, *args, **kwargs):
        if "unit_uid" in kwargs:
            kwargs.pop("unit_uid")

        return await self.inline_manager._delete_unit_message(
            *args,
            unit_uid=self.unit_uid,
            **kwargs,
        )

    async def unload(self, *args, **kwargs):
        if "unit_uid" in kwargs:
            kwargs.pop("unit_uid")

        return await self.inline_manager._unload_unit(
            *args,
            unit_uid=self.unit_uid,
            **kwargs,
        )


class InlineCall(CallbackQuery, InlineMessage):
    """Modified version of classic aiogram `CallbackQuery`"""

    def __init__(
        self,
        call: CallbackQuery,
        inline_manager: "InlineManager",  # noqa: F821
        unit_uid: str,
    ):
        CallbackQuery.__init__(self)

        for attr in {
            "id",
            "from_user",
            "message",
            "inline_message_id",
            "chat_instance",
            "data",
            "game_short_name",
        }:
            setattr(self, attr, getattr(call, attr, None))

        InlineMessage.__init__(
            self,
            inline_manager,
            unit_uid,
            call.inline_message_id,
        )


class InlineUnit:
    """InlineManager extension type. For internal use only"""

    def __init__(self):
        """Made just for type specification"""


class BotMessage(AiogramMessage):
    """Modified version of original Aiogram Message"""

    def __init__(self):
        super().__init__()


class InlineQuery(AiogramInlineQuery):
    """Modified version of original Aiogram InlineQuery"""

    def __init__(self, inline_query: AiogramInlineQuery):
        super().__init__(self)

        for attr in {"id", "from_user", "query", "offset", "chat_type", "location"}:
            setattr(self, attr, getattr(inline_query, attr, None))

        self.inline_query = inline_query
        self.args = (
            self.inline_query.query.split(maxsplit=1)[1]
            if len(self.inline_query.query.split()) > 1
            else ""
        )

    async def e400(self):
        await self.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="🚫 400",
                    description="Bad request. You need to pass right arguments, follow module's documentation",
                    input_message_content=InputTextMessageContent(
                        "😶‍🌫️ <i>There is nothing here...</i>",
                        parse_mode="HTML",
                    ),
                    thumb_url="https://img.icons8.com/color/344/swearing-male--v1.png",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )

    async def e403(self):
        await self.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="🚫 403",
                    description="You have no permissions to access this result",
                    input_message_content=InputTextMessageContent(
                        "😶‍🌫️ <i>There is nothing here...</i>",
                        parse_mode="HTML",
                    ),
                    thumb_url="https://img.icons8.com/external-wanicon-flat-wanicon/344/external-forbidden-new-normal-wanicon-flat-wanicon.png",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )

    async def e404(self):
        await self.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="🚫 404",
                    description="No results found",
                    input_message_content=InputTextMessageContent(
                        "😶‍🌫️ <i>There is nothing here...</i>",
                        parse_mode="HTML",
                    ),
                    thumb_url="https://img.icons8.com/external-justicon-flat-justicon/344/external-404-error-responsive-web-design-justicon-flat-justicon.png",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )

    async def e426(self):
        await self.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="🚫 426",
                    description="You need to update Hikka before sending this request",
                    input_message_content=InputTextMessageContent(
                        "😶‍🌫️ <i>There is nothing here...</i>",
                        parse_mode="HTML",
                    ),
                    thumb_url="https://img.icons8.com/fluency/344/approve-and-update.png",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )

    async def e500(self):
        await self.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="🚫 500",
                    description="Internal userbot error while processing request. More info in logs",
                    input_message_content=InputTextMessageContent(
                        "😶‍🌫️ <i>There is nothing here...</i>",
                        parse_mode="HTML",
                    ),
                    thumb_url="https://img.icons8.com/external-vitaliy-gorbachev-flat-vitaly-gorbachev/344/external-error-internet-security-vitaliy-gorbachev-flat-vitaly-gorbachev.png",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )
