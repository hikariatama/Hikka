"""
█ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
█▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

© Copyright 2022
https://t.me/hikariatama

🔒 Licensed under the GNU GPLv3
🌐 https://www.gnu.org/licenses/agpl-3.0.html
"""

import aiohttp_jinja2


class Web:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.router.add_get("/", self.root)

    @aiohttp_jinja2.template("root.jinja2")
    async def root(self, request):
        return {}
