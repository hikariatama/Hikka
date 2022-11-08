import asyncio
import random

from werkzeug.debug import DebuggedApplication
from werkzeug import Request, Response
from werkzeug.serving import make_server, BaseWSGIServer
import os
from threading import Thread

from .. import main, utils
from . import proxypass


class ServerThread(Thread):
    def __init__(self, server: BaseWSGIServer):
        Thread.__init__(self)
        self.server = server

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


class WebDebugger:
    def __init__(self):
        self.pin = str(random.randint(100000, 999999))
        self.port = main.gen_port("werkzeug_port", True)
        main.save_config_key("werkzeug_port", self.port)
        self._url = None
        self._proxypasser = proxypass.ProxyPasser()
        asyncio.ensure_future(self._getproxy())
        self._create_server()
        self._controller = ServerThread(self._server)
        self._controller.start()
        self.exceptions = {}

    async def _getproxy(self):
        self._url = await self._proxypasser.get_url(self.port)

    def _create_server(self) -> BaseWSGIServer:
        os.environ["WERKZEUG_DEBUG_PIN"] = self.pin
        os.environ["WERKZEUG_RUN_MAIN"] = "true"

        @Request.application
        def app(request):
            if request.args.get("ping", "N").upper() == "Y":
                return Response("ok")
            if request.args.get("shutdown", "N").upper() == "Y":
                self._server._BaseServer__shutdown_request = True
                return Response("Shutdown!")
            else:
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
        id_ = utils.rand(8)
        self.exceptions[id_] = exc_type(exc_value).with_traceback(exc_traceback)
        return self.url.strip("/") + f"?ex_id={id_}"
