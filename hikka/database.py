import asyncio
import logging

from telethon.tl.custom import Message as CustomMessage
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.tl.types import Message, Channel
import json
import os
from typing import Any

from . import main

ORIGIN = "/".join(main.__file__.split("/")[:-2])

logger = logging.getLogger(__name__)


class Database(dict):
    def __init__(self, client):
        self._client = client
        self._me = None
        self._assets = None
        self._anti_double_asset_lock = asyncio.Lock()
        self._assets_already_exists = False
        self.close = lambda: None

    def __repr__(self):
        return object.__repr__(self)

    async def init(self):
        self._me = await self._client.get_me()
        self._db_path = os.path.join(ORIGIN, f"config-{self._me.id}.json")
        self.read()

    async def _find_asset_channel(self) -> Channel:
        async for dialog in self._client.iter_dialogs(None, ignore_migrated=True):
            if dialog.name == f"hikka-{self._me.id}-assets" and dialog.is_channel:
                members = await self._client.get_participants(dialog, limit=2)

                if len(members) != 1:
                    continue

                logger.debug(f"Found asset chat! It is {dialog.id}.")
                return dialog.entity

    async def _make_asset_channel(self) -> Channel:
        async with self._anti_double_asset_lock:
            if self._assets_already_exists:
                return await self._find_data_channel()
            self._assets_already_exists = True
            return (
                await self._client(
                    CreateChannelRequest(
                        f"hikka-{self._me.id}-assets",
                        "// Don't touch",
                        megagroup=True,
                    )
                )
            ).chats[0]

    def read(self) -> str:
        """
        Read database
        """
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                data = json.loads(f.read())
                self.update(**data)
                return data
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            logger.exception("Database read failed! Creating new one...")
            return {}

    def save(self) -> bool:
        """
        Save database
        """
        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(self))
        except Exception:
            logger.exception("Database save failed!")
            return False

        return True

    async def store_asset(self, message):
        if not self._assets:
            self._assets = await self._find_asset_channel()

        if not self._assets:
            self._assets = await self._make_asset_channel()

        return (
            (await self._client.send_message(self._assets, message)).id
            if isinstance(message, (Message, CustomMessage))
            else (
                await self._client.send_message(
                    self._assets,
                    file=message,
                    force_document=True,
                )
            ).id
        )

    async def fetch_asset(self, id_):
        if not self._assets:
            self._assets = await self._find_asset_channel()

        if not self._assets:
            return None

        ret = await self._client.get_messages(self._assets, ids=[id_])

        if not ret:
            return None

        return ret[0]

    def get(self, owner: str, key: str, default: Any = None) -> Any:
        try:
            return self[owner][key]
        except KeyError:
            return default

    def set(self, owner, key, value):
        super().setdefault(owner, {})[key] = value
        return self.save()
