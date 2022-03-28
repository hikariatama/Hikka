from aiogram.types import Message as AiogramMessage, InlineQuery as AiogramInlineQuery


class InlineCall:
    def __init__(self):
        self.delete = None
        self.unload = None
        self.edit = None
        super().__init__()


class InlineUnit:
    def __init__(self):
        pass


class BotMessage(AiogramMessage):
    def __init__(self):
        super().__init__()


class InlineQuery:
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
