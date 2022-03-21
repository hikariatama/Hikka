"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

import aiohttp_jinja2


class Web:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.router.add_get("/", self.root)
        self.app.router.add_get("/is_restart_complete", lambda r: True)
        self.app.router.add_post("/restart", self.restart)

    @aiohttp_jinja2.template("root.jinja2")
    async def root(self, request):
        return {}

    async def restart(self, request):
        cl = self.client_data[list(self.client_data.keys())[0]]
        m = await cl[1].send_message("me", "<b>Restarting...</b>")
        for mod in cl[0].modules:
            if mod.__class__.__name__ == "UpdaterMod":
                await mod.restart_common(m)
