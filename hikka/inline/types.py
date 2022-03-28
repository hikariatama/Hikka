from aiogram.types import Message as AiogramMessage, InlineQuery as AiogramInlineQuery


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
