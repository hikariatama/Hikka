# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging
import os
import random
from threading import Thread

from werkzeug import Request, Response
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import BaseWSGIServer, make_server

from .. import main, utils
from . import proxypass

logger = logging.getLogger(__name__)


class ServerThread(Thread):
    def __init__(self, server: BaseWSGIServer):
        Thread.__init__(self)
        self.server = server

    def run(self):
        logger.debug("Starting werkzeug debug server")
        self.server.serve_forever()

    def shutdown(self):
        logger.debug("Shutting down werkzeug debug server")
        self.server.shutdown()


class WebDebugger:
    def __init__(self):
        self._url = None
        self.exceptions = {}
        self.pin = str(random.randint(100000, 999999))
        self.port = main.gen_port("werkzeug_port", True)
        main.save_config_key("werkzeug_port", self.port)
        self._proxypasser = proxypass.ProxyPasser(self._url_changed)
        asyncio.ensure_future(self._getproxy())
        self._create_server()
        self._controller = ServerThread(self._server)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        self._controller.start()
        utils.atexit(self._controller.shutdown)
        self.proxy_ready = asyncio.Event()

    async def _getproxy(self):
        self._url = await self._proxypasser.get_url(self.port)
        self.proxy_ready.set()

    def _url_changed(self, url: str):
        self._url = url

    def _create_server(self) -> BaseWSGIServer:
        logger.debug("Creating new werkzeug server instance")
        os.environ["WERKZEUG_DEBUG_PIN"] = self.pin
        os.environ["WERKZEUG_RUN_MAIN"] = "true"

        @Request.application
        def app(request):
            if request.args.get("ping", "N").upper() == "Y":
                return Response("ok")

            if request.args.get("shutdown", "N").upper() == "Y":
                self._server._BaseServer__shutdown_request = True
                return Response("Shutdown!")

            raise self.exceptions.get(request.args.get("ex_id"), Exception("idk"))

        app = DebuggedApplication(app, evalex=True, pin_security=True)

        try:
            fd = int(os.environ["WERKZEUG_SERVER_FD"])
        except (LookupError, ValueError):
            fd = None

        self._server = make_server(
            "localhost",
            self.port,
            app,
            threaded=False,
            processes=1,
            request_handler=None,
            passthrough_errors=False,
            ssl_context=None,
            fd=fd,
        )

        return self._server

    @property
    def url(self) -> str:
        return self._url or f"http://127.0.0.1:{self.port}"

    def feed(self, exc_type, exc_value, exc_traceback) -> str:
        logger.debug("Feeding exception %s to werkzeug debugger", exc_type)
        id_ = utils.rand(8)
        self.exceptions[id_] = exc_type(exc_value).with_traceback(exc_traceback)
        return self.url.strip("/") + f"?ex_id={id_}"
