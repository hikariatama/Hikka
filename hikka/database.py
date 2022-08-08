#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
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

from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import ChannelsTooMuchError

from . import utils, main
from ._types import (
    PointerBool,
    PointerInt,
    PointerStr,
    PointerList,
    PointerDict,
    PointerTuple,
)

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
        with self._postgre, self._postgre.cursor() as cur:
            cur.execute(
                "UPDATE hikka SET data = %s WHERE id = %s;",
                (json.dumps(self), self._client.tg_id),
            )

    def _redis_save_sync(self):
        with self._redis.pipeline() as pipe:
            pipe.set(
                str(self._client.tg_id),
                json.dumps(self, ensure_ascii=True),
            )
            pipe.execute()

    async def remote_force_save(self) -> bool:
        """Force save database to remote endpoint without waiting"""
        if not self._postgre and not self._redis:
            return False

        if self._redis:
            await utils.run_sync(self._redis_save_sync)
            logger.debug("Published db to Redis")
        else:
            await utils.run_sync(self._postgre_save_sync)
            logger.debug("Published db to PostgreSQL")

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

        with conn, conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS hikka (id bigint, data text);")

            with contextlib.suppress(Exception):
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM hikka WHERE id=%s);",
                    (self._client.tg_id,),
                )

                if not cur.fetchone()[0]:
                    cur.execute(
                        "INSERT INTO hikka (id, data) VALUES (%s, %s);",
                        (self._client.tg_id, json.dumps(self)),
                    )

            with contextlib.suppress(Exception):
                cur.execute(
                    "SELECT (column_name, data_type) "
                    "FROM information_schema.columns "
                    "WHERE table_name = 'hikka' AND column_name = 'id';"
                )

                if "integer" in cur.fetchone()[0].lower():
                    logger.warning(
                        "Made legacy migration from integer to bigint "
                        "in postgresql database"
                    )
                    cur.execute("ALTER TABLE hikka ALTER COLUMN id TYPE bigint;")

        self._postgre = conn

    async def redis_init(self) -> bool:
        """Init redis database"""
        if REDIS_URI := os.environ.get("REDIS_URL") or main.get_config_key("redis_uri"):
            self._redis = redis.Redis.from_url(REDIS_URI)
        else:
            return False

    async def init(self):
        """Asynchronous initialization unit"""
        if os.environ.get("REDIS_URL") or main.get_config_key("redis_uri"):
            await self.redis_init()
        elif os.environ.get("DATABASE_URL") or main.get_config_key("postgre_uri"):
            await self.postgre_init()

        self._db_path = os.path.join(DATA_DIR, f"config-{self._client.tg_id}.json")
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
            logger.error(
                "Can't find and/or create assets folder\n"
                "This may cause several consequences, such as:\n"
                "- Non working assets feature (e.g. notes)\n"
                "- This error will occur every restart\n\n"
                "You can solve this by leaving some channels/groups"
            )

    def read(self):
        """Read database and stores it in self"""
        if self._redis:
            try:
                self.update(
                    **json.loads(
                        self._redis.get(
                            str(self._client.tg_id),
                        ).decode(),
                    )
                )
            except Exception:
                logger.exception("Error reading redis database")
            return

        if self._postgre:
            try:
                with self._postgre, self._postgre.cursor() as cur:
                    cur.execute(
                        "SELECT data FROM hikka WHERE id=%s;",
                        (self._client.tg_id,),
                    )
                    self.update(
                        **json.loads(
                            cur.fetchall()[0][0],
                        ),
                    )
            except Exception:
                logger.exception("Error reading postgresql database")
            return

        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                self.update(**json.load(f))
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            logger.warning("Database read failed! Creating new one...")

    def process_db_autofix(self, db: dict) -> bool:
        if not utils.is_serializable(db):
            return False

        for key, value in db.copy().items():
            if not isinstance(key, (str, int)):
                logger.warning(
                    f"DbAutoFix: Dropped {key=} , because it is not string or int"
                )
                continue

            if not isinstance(value, dict):
                # If value is not a dict (module values), drop it,
                # otherwise it may cause problems
                del db[key]
                logger.warning(
                    f"DbAutoFix: Dropped {key=}, because it is non-dict {type(value)=}"
                )
                continue

            for subkey in value:
                if not isinstance(subkey, (str, int)):
                    del db[key][subkey]
                    logger.warning(
                        f"DbAutoFix: Dropped {subkey=} of db[{key}], because it is not"
                        " string or int"
                    )
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
                "Rewriting database to the last revision because new one destructed it"
            )

        if self._next_revision_call < time.time():
            self._revisions += [dict(self)]
            self._next_revision_call = time.time() + 3

        while len(self._revisions) > 15:
            self._revisions.pop()

        if self._redis:
            if not self._saving_task:
                self._saving_task = asyncio.ensure_future(self._redis_save())
            return True

        if self._postgre:
            if not self._saving_task:
                self._saving_task = asyncio.ensure_future(self._postgre_save())
            return True

        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                json.dump(self, f, indent=4)
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
            raise NoAssetsChannel("Tried to save asset to non-existing asset channel")

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
            raise NoAssetsChannel(
                "Tried to fetch asset from non-existing asset channel"
            )

        asset = await self._client.get_messages(self._assets, ids=[asset_id])

        return asset[0] if asset else None

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

    def pointer(self, owner: str, key: str, default: Any = None) -> Any:
        """Get a pointer to database key"""
        value = self.get(owner, key, default)
        mapping = {
            int: PointerInt,
            str: PointerStr,
            bool: PointerBool,
            list: PointerList,
            dict: PointerDict,
            tuple: PointerTuple,
        }

        pointer_constructor = next(
            (pointer for type_, pointer in mapping.items() if isinstance(value, type_)),
            None,
        )

        if pointer_constructor is None:
            raise ValueError(
                f"Pointer for type {type(value).__name__} is not implemented"
            )

        return pointer_constructor(self, owner, key, default)
