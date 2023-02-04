# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging
import os
import re
import typing

from .. import utils

logger = logging.getLogger(__name__)


class ProxyPasser:
    def __init__(self, change_url_callback: callable = lambda _: None):
        self._tunnel_url = None
        self._sproc = None
        self._url_available = asyncio.Event()
        self._url_available.set()
        self._lock = asyncio.Lock()
        self._change_url_callback = change_url_callback

    async def _sleep_for_task(self, callback: callable, data: bytes, delay: int):
        await asyncio.sleep(delay)
        await callback(data.decode("utf-8"))

    async def _read_stream(
        self,
        callback: callable,
        stream: typing.BinaryIO,
        delay: int,
    ) -> None:
        last_task = None
        for getline in iter(stream.readline, ""):
            data_chunk = await getline
            if not data_chunk and last_task:
                last_task.cancel()
                await callback(data_chunk.decode("utf-8"))
                if not self._url_available.is_set():
                    self._url_available.set()

            if last_task:
                last_task.cancel()

            last_task = asyncio.ensure_future(
                self._sleep_for_task(callback, data_chunk, delay)
            )

    def kill(self):
        try:
            self._sproc.terminate()
        except Exception:
            logger.exception("Failed to kill proxy pass process")
        else:
            logger.debug("Proxy pass tunnel killed")

    async def _process_stream(self, stdout_line: str) -> None:
        regex = r"tunneled.*?(https:\/\/.*?\..*?\.[a-z]+)"

        if re.search(regex, stdout_line):
            self._tunnel_url = re.search(regex, stdout_line)[1]
            self._change_url_callback(self._tunnel_url)
            logger.debug("Proxy pass tunneled: %s", self._tunnel_url)
            self._url_available.set()

    async def get_url(self, port: int) -> typing.Optional[str]:
        async with self._lock:
            if self._tunnel_url:
                try:
                    await asyncio.wait_for(self._sproc.wait(), timeout=0.05)
                except asyncio.TimeoutError:
                    return self._tunnel_url
                else:
                    self.kill()

            if "DOCKER" in os.environ:
                # We're in a Docker container, so we can't use ssh
                # Also, the concept of Docker is to keep
                # everything isolated, so we can't proxy-pass to
                # open web.
                return None

            logger.debug("Starting proxy pass shell for port %d", port)
            self._sproc = await asyncio.create_subprocess_shell(
                "ssh -o StrictHostKeyChecking=no -R"
                f" 80:127.0.0.1:{port} nokey@localhost.run",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            utils.atexit(self.kill)

            self._url_available = asyncio.Event()
            logger.debug("Starting proxy pass reader for port %d", port)
            asyncio.ensure_future(
                self._read_stream(
                    self._process_stream,
                    self._sproc.stdout,
                    1,
                )
            )

            try:
                await asyncio.wait_for(self._url_available.wait(), 15)
            except asyncio.TimeoutError:
                self.kill()
                self._tunnel_url = None
                return await self.get_url(port)

            logger.debug("Proxy pass tunnel url to port %d: %s", port, self._tunnel_url)

            return self._tunnel_url
