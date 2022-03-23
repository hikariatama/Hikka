#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import json
import logging


class NotifyingFuture(asyncio.Future):
    def __init__(self, *args, **kwargs):
        self.__to_notify_on_await = kwargs.pop("on_await", None)
        super().__init__(*args, **kwargs)

    def __await__(self):
        if callable(self.__to_notify_on_await):
            self.__to_notify_on_await()
        return super().__await__()


# Not thread safe, use the event loop!
class Database(dict):
    def __init__(self, backend, noop=False):
        super().__init__()
        self._noop = noop or backend is None
        self._backend = backend
        self._pending = None
        self._loading = True
        self._waiter = asyncio.Event()
        self._sync_future = None

    def __repr__(self):
        return object.__repr__(self)

    async def init(self):
        if self._backend is None:
            self._loading = False
            self._waiter.set()
            return

        await self._backend.init(self.reload)
        db = await self._backend.do_download()

        if db is not None:
            try:
                self.update(**json.loads(db))
            except Exception:
                # Don't worry if its corrupted. Just set it to {} and let it be fixed on next upload
                pass

        self._loading = False
        self._waiter.set()

    async def close(self):
        try:
            await self.save()
        except Exception:
            logging.info("Database close failed", exc_info=True)

        if self._backend is not None:
            self._backend.close()

    def save(self):
        self._set()

    def get(self, owner, key, default=None):
        try:
            return self[owner][key]
        except KeyError:
            return default

    def set(self, owner, key, value):
        super().setdefault(owner, {})[key] = value
        return self.save()

    def _cancel_then_set(self):
        if self._pending is not None and not self._pending.cancelled():
            self._pending.cancel()

        self._pending = asyncio.ensure_future(self._set())
        # Restart the task, but without the delay, because someone is waiting for us

    async def _set(self):
        self._backend.save(self)

    async def reload(self, event):
        if self._noop:
            return

        try:
            self._waiter.clear()
            self._loading = True

            if self._pending is not None:
                self._pending.cancel()

            db = await self._backend.do_download()
            self.clear()
            self.update(**json.loads(db))
        finally:
            self._loading = False
            self._waiter.set()

    async def store_asset(self, message):
        return await self._backend.store_asset(message)

    async def fetch_asset(self, message):
        return await self._backend.fetch_asset(message)


async def _wait_then_do(time, task, *args, **kwargs):
    await asyncio.sleep(time)
    return await task(*args, **kwargs)
