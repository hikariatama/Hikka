import re


def compat(code: str) -> str:
    """
    Reformats modules, built for GeekTG to work with Huikka
    :param code: code to reformat
    :return: reformatted code
    :rtype: str
    :example:
    ```python
        code = '''
            from ..inline import GeekInlineQuery, rand
            from ..inline import rand, InlineQueryResultArticle
            from ..inline import InlineQueryResultArticle, rand
            from ..inline import rand, InlineQueryResultArticle, InputTextMessageContent
        '''
        print(compat(code))
    ```
    """
    return "\n".join(
        [
            re.sub(
                r"^( *)from \.\.inline import (.+)$",
                r"\1from ..inline.types import \2",
                re.sub(
                    r"^( *)from \.\.inline import rand[^,]*$",
                    "\1from ..utils import rand",
                    re.sub(
                        r"^( *)from \.\.inline import rand, ?(.+)$",
                        r"\1from ..inline.types import \2\n\1from ..utils import rand",
                        re.sub(
                            r"^( *)from \.\.inline import (.+), ?rand[^,]*$",
                            r"\1from ..inline.types import \2\n\1from ..utils import"
                            r" rand",
                            re.sub(
                                r"^( *)from \.\.inline import (.+), ?rand, ?(.+)$",
                                r"\1from ..inline.types import \2, \3\n\1from ..utils"
                                r" import rand",
                                line.replace("GeekInlineQuery", "InlineQuery").replace(
                                    "self.inline._bot",
                                    "self.inline.bot",
                                ),
                                flags=re.M,
                            ),
                            flags=re.M,
                        ),
                        flags=re.M,
                    ),
                    flags=re.M,
                ),
                flags=re.M,
            )
            for line in code.splitlines()
        ]
    )
