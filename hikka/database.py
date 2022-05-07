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
from typing import Any, Union

from telethon.tl.functions.channels import EditTitleRequest
from telethon.tl.types import Message

from . import utils

DATA_DIR = (
    os.path.normpath(os.path.join(utils.get_base_dir(), ".."))
    if "OKTETO" not in os.environ
    else "/data"
)

logger = logging.getLogger(__name__)


class Database(dict):
    _next_revision_call = 0
    _revisions = []
    _assets = None
    _me = None

    def __init__(self, client):
        super().__init__()
        self._client = client

    def __repr__(self):
        return object.__repr__(self)

    async def init(self):
        """Asynchronous initialisation unit"""
        self._me = await self._client.get_me()
        self._db_path = os.path.join(DATA_DIR, f"config-{self._me.id}.json")
        self.read()

        try:
            channel_entity = await (
                dialog.entity
                async for dialog in self._client.iter_dialogs(
                    None,
                    ignore_migrated=True,
                )
                if (
                    dialog.name in {f"hikka-{self._me.id}-assets", "hikka-assets"}
                    and dialog.is_channel
                    and dialog.entity.participants_count == 1
                )
            ).__anext__()

            if channel_entity.title != "hikka-assets":
                await self._client(EditTitleRequest(channel_entity, "hikka-assets"))
                await utils.set_avatar(
                    self._client,
                    channel_entity,
                    "https://raw.githubusercontent.com/hikariatama/assets/master/hikka-assets.png",
                )
                logger.info("Made legacy assets migration")
        except Exception:
            pass

        self._assets, _ = await utils.asset_channel(
            self._client,
            "hikka-assets",
            "🌆 Your Hikka assets will be stored here",
            archive=True,
            avatar="https://raw.githubusercontent.com/hikariatama/assets/master/hikka-assets.png",
        )

    def read(self) -> str:
        """Read database"""
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.loads(f.read())
                self.update(**data)
                return data
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            logger.warning("Database read failed! Creating new one...")
            return {}

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

    def __setitem__(self, key: str, value: dict) -> bool:
        if not isinstance(value, dict):
            raise RuntimeError("Attempted to write non-dict value in a first layer of database")  # fmt: skip

        dict.__setitem__(self, key, value)
        return self.save()

    def __delitem__(self, key: str) -> bool:
        dict.__delitem__(self, key)
        return self.save()
