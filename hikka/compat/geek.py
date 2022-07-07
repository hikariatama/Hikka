#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import re


def compat(code: str) -> str:
    """Reformats modules, built for GeekTG to work with Hikka"""
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
                            r"\1from ..inline.types import \2\n\1from ..utils import rand",
                            re.sub(
                                r"^( *)from \.\.inline import (.+), ?rand, ?(.+)$",
                                r"\1from ..inline.types import \2, \3\n\1from ..utils import rand",
                                line.replace("GeekInlineQuery", "InlineQuery").replace(
                                    "self.inline._bot", "self.inline.bot"
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
