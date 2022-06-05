# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import json
import logging
import os
import time
import asyncio

try:
    import psycopg2
except ImportError as e:
    if "DYNO" in os.environ:
        raise e

try:
    import redis
except ImportError as e:
    if "DYNO" in os.environ:
        raise e


from typing import Any, Union

from telethon.tl.functions.channels import EditTitleRequest
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import ChannelsTooMuchError

from . import utils, main

DATA_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if "OKTETO" not in os.environ and "DOCKER" not in os.environ
    else "/data"
)

logger = logging.getLogger(__name__)


class NoAssetsChannel(Exception):
    """Raised when trying to read/store asset with no asset channel present"""


class Database(dict):
    _next_revision_call = 0
    _revisions = []
    _assets = None
    _me = None
    _postgre = None
    _redis = None
    _saving_task = None

    def __init__(self, client):
        super().__init__()
        self._client = client

    def __repr__(self):
        return object.__repr__(self)

    def _postgre_save_sync(self):
        self._postgre.execute(
            "DELETE FROM hikka WHERE id = %s; INSERT INTO hikka (id, data) VALUES (%s, %s);",
            (self._client._tg_id, self._client._tg_id, json.dumps(self)),
        )
        self._postgre.connection.commit()

    def _redis_save_sync(self):
        with self._redis.pipeline() as pipe:
            pipe.set(
                str(self._client._tg_id),
                json.dumps(self, ensure_ascii=True),
            )
            pipe.execute()

    async def remote_force_save(self) -> bool:
        """Force save database to remote endpoint without waiting"""
        if not self._postgre and not self._redis:
            return False

        if self._postgre:
            await utils.run_sync(self._postgre_save_sync)
            logger.debug("Published db to PostgreSQL")
        elif self._redis:
            await utils.run_sync(self._redis_save_sync)
            logger.debug("Published db to Redis")

        return True

    async def _postgre_save(self) -> bool:
        """Save database to postgresql"""
        if not self._postgre:
            return False

        await asyncio.sleep(5)

        await utils.run_sync(self._postgre_save_sync)

        logger.debug("Published db to PostgreSQL")

        self._saving_task = None
        return True

    async def _redis_save(self) -> bool:
        """Save database to redis"""
        if not self._redis:
            return False

        await asyncio.sleep(5)

        await utils.run_sync(self._redis_save_sync)

        logger.debug("Published db to Redis")

        self._saving_task = None
        return True

    async def postgre_init(self) -> bool:
        """Init postgresql database"""
        POSTGRE_URI = os.environ.get("DATABASE_URL") or main.get_config_key(
            "postgre_uri"
        )

        if not POSTGRE_URI:
            return False

        conn = psycopg2.connect(POSTGRE_URI, sslmode="require")

        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS hikka (id integer, data text);")
        self._postgre = cur

    async def redis_init(self) -> bool:
        """Init redis database"""
        REDIS_URI = os.environ.get("REDIS_URL") or main.get_config_key("redis_uri")

        if not REDIS_URI:
            return False

        self._redis = redis.Redis.from_url(REDIS_URI)

    async def init(self):
        """Asynchronous initialization unit"""
        if os.environ.get("DATABASE_URL") or main.get_config_key("postgre_uri"):
            await self.postgre_init()
        elif os.environ.get("REDIS_URL") or main.get_config_key("redis_uri"):
            await self.redis_init()

        self._db_path = os.path.join(DATA_DIR, f"config-{self._client._tg_id}.json")
        self.read()

        try:
            self._assets, _ = await utils.asset_channel(
                self._client,
                "hikka-assets",
                "🌆 Your Hikka assets will be stored here",
                archive=True,
                avatar="https://raw.githubusercontent.com/hikariatama/assets/master/hikka-assets.png",
            )
        except ChannelsTooMuchError:
            self._assets = None
            logger.critical(
                "Can't find and/or create assets folder\n"
                "This may cause several consequences, such as:\n"
                "- Non working assets feature (e.g. notes)\n"
                "- This error will occur every restart\n\n"
                "You can solve this by leaving some channels/groups"
            )

    def read(self):
        """Read database and stores it in self"""
        if self._postgre:
            try:
                self._postgre.execute(
                    "SELECT data FROM hikka WHERE id=%s;",
                    (self._client._tg_id,),
                )
                self.update(
                    **json.loads(
                        self._postgre.fetchall()[0][0],
                    ),
                )
            except Exception:
                logger.exception("Error reading postgresql database")
            return
        elif self._redis:
            try:
                self.update(
                    **json.loads(
                        self._redis.get(
                            str(self._client._tg_id),
                        ).decode(),
                    )
                )
            except Exception:
                logger.exception("Error reading redis database")
            return

        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.loads(f.read())
                self.update(**data)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            logger.warning("Database read failed! Creating new one...")

    def process_db_autofix(self, db: dict) -> bool:
        if not utils.is_serializable(db):
            return False

        for key, value in db.copy().items():
            if not isinstance(key, (str, int)):
                logger.warning(f"DbAutoFix: Dropped {key=} , because it is not string or int")  # fmt: skip
                continue

            if not isinstance(value, dict):
                # If value is not a dict (module values), drop it,
                # otherwise it may cause problems
                del db[key]
                logger.warning(f"DbAutoFix: Dropped {key=}, because it is non-dict {type(value)=}")  # fmt: skip
                continue

            for subkey in value:
                if not isinstance(subkey, (str, int)):
                    del db[key][subkey]
                    logger.warning(f"DbAutoFix: Dropped {subkey=} of db[{key}], because it is not string or int")  # fmt: skip
                    continue

        return True

    def save(self) -> bool:
        """Save database"""
        if not self.process_db_autofix(self):
            try:
                rev = self._revisions.pop()
                while not self.process_db_autofix(rev):
                    rev = self._revisions.pop()
            except IndexError:
                raise RuntimeError(
                    "Can't find revision to restore broken database from "
                    "database is most likely broken and will lead to problems, "
                    "so its save is forbidden."
                )

            self.clear()
            self.update(**rev)

            raise RuntimeError(
                "Rewriting database to the last revision "
                "because new one destructed it"
            )

        if self._next_revision_call < time.time():
            self._revisions += [dict(self)]
            self._next_revision_call = time.time() + 3

        while len(self._revisions) > 15:
            self._revisions.pop()

        if self._postgre:
            if not self._saving_task:
                self._saving_task = asyncio.ensure_future(self._postgre_save())
            return True
        elif self._redis:
            if not self._saving_task:
                self._saving_task = asyncio.ensure_future(self._redis_save())
            return True

        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(self))
        except Exception:
            logger.exception("Database save failed!")
            return False

        return True

    async def store_asset(self, message: Message) -> int:
        """
        Save assets
        returns asset_id as integer
        """
        if not self._assets:
            raise NoAssetsChannel("Tried to save asset to non-existing asset channel")  # fmt: skip

        return (
            (await self._client.send_message(self._assets, message)).id
            if isinstance(message, Message)
            else (
                await self._client.send_message(
                    self._assets,
                    file=message,
                    force_document=True,
                )
            ).id
        )

    async def fetch_asset(self, asset_id: int) -> Union[None, Message]:
        """Fetch previously saved asset by its asset_id"""
        if not self._assets:
            raise NoAssetsChannel("Tried to fetch asset from non-existing asset channel")  # fmt: skip

        asset = await self._client.get_messages(self._assets, ids=[asset_id])

        if not asset:
            return None

        return asset[0]

    def get(self, owner: str, key: str, default: Any = None) -> Any:
        """Get database key"""
        try:
            return self[owner][key]
        except KeyError:
            return default

    def set(self, owner: str, key: str, value: Any) -> bool:
        """Set database key"""
        if not utils.is_serializable(owner):
            raise RuntimeError(
                "Attempted to write object to "
                f"{owner=} ({type(owner)=}) of database. It is not "
                "JSON-serializable key which will cause errors"
            )

        if not utils.is_serializable(key):
            raise RuntimeError(
                "Attempted to write object to "
                f"{key=} ({type(key)=}) of database. It is not "
                "JSON-serializable key which will cause errors"
            )

        if not utils.is_serializable(value):
            raise RuntimeError(
                "Attempted to write object of "
                f"{key=} ({type(value)=}) to database. It is not "
                "JSON-serializable value which will cause errors"
            )

        super().setdefault(owner, {})[key] = value
        return self.save()
