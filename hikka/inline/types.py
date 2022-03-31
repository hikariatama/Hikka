from aiogram.types import (
    Message as AiogramMessage,
    InlineQuery as AiogramInlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from .. import utils


class InlineCall:
    """Modified version of original Aiogram CallbackQuery"""

    def __init__(self):
        self.delete = None
        self.unload = None
        self.edit = None
        super().__init__()


class InlineUnit:
    """InlineManager extension type. For internal use only"""

    def __init__(self):
        """Made just for type specification"""


class BotMessage(AiogramMessage):
    """Modified version of original Aiogram Message"""

    def __init__(self):
        super().__init__()


class InlineQuery:
    """Modified version of original Aiogram InlineQuery"""

    def __init__(self, inline_query: AiogramInlineQuery) -> None:
        self.inline_query = inline_query

        # Inherit original `InlineQuery` attributes for
        # easy access
        for attr in dir(inline_query):
            if attr.startswith("__") and attr.endswith("__"):
                continue  # Ignore magic attrs

            if hasattr(self, attr):
                continue  # Do not override anything

            try:
                setattr(self, attr, getattr(inline_query, attr))
            except AttributeError:
                pass  # There are some non-writable native attrs
                # So just ignore them

        self.args = (
            self.inline_query.query.split(maxsplit=1)[1]
            if len(self.inline_query.query.split()) > 1
            else ""
        )

    async def e400(self) -> None:
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

    async def e403(self) -> None:
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

    async def e404(self) -> None:
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

    async def e426(self) -> None:
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

    async def e500(self) -> None:
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
