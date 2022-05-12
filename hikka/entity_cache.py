import time
import asyncio
import logging
from telethon.hints import EntityLike
from telethon import TelegramClient

logger = logging.getLogger(__name__)


def hashable(value):
    """Determine whether `value` can be hashed."""
    try:
        hash(value)
    except TypeError:
        return False

    return True


class CacheRecord:
    def __init__(
        self,
        hashable_entity: "Hashable",  # noqa: F821
        resolved_entity: EntityLike,
    ):
        self.entity = resolved_entity
        self._hashable_entity = hashable_entity
        self._exp = round(time.time() + 5 * 60)

    def expired(self):
        return self._exp < time.time()

    def __eq__(self, record: "CacheRecord"):
        return hash(record._hashable_entity) == hash(self._hashable_entity)

    def __hash__(self):
        return hash(self._hashable_entity)

    def __str__(self):
        return f"CacheRecord of {self.entity}"

    def __repr__(self):
        return f"CacheRecord(entity={type(self.entity).__name__}(...), exp={self._exp})"


def install_entity_caching(client: TelegramClient):
    client._hikka_cache = {}

    old = client.get_entity

    async def new(entity: EntityLike):
        if not hashable(entity):
            hashable_entity = next(
                getattr(entity, attr)
                for attr in {"user_id", "channel_id", "chat_id", "id"}
                if hasattr(entity, attr)
            )
        else:
            hashable_entity = entity

        if hashable_entity and hashable_entity in client._hikka_cache:
            logger.debug(
                f"Using cached {entity=} ({type(client._hikka_cache[hashable_entity].entity).__name__})"
            )
            return client._hikka_cache[hashable_entity].entity

        resolved_entity = await old(entity)

        if resolved_entity:
            cache_record = CacheRecord(hashable_entity, resolved_entity)
            client._hikka_cache[hashable_entity] = cache_record
            logger.debug(f"Saved {hashable_entity=} to cache")

            if hasattr(resolved_entity, "id"):
                logger.debug(f"Saved {resolved_entity.id=} to cache")
                client._hikka_cache[resolved_entity.id] = cache_record

            if hasattr(resolved_entity, "username"):
                logger.debug(f"Saved @{resolved_entity.username=} to cache")
                client._hikka_cache[f"@{resolved_entity.username}"] = cache_record

        return resolved_entity

    async def cleaner(client: TelegramClient):
        while True:
            for record, record_data in client._hikka_cache.copy().items():
                if record_data.expired():
                    del client._hikka_cache[record]
                    logger.debug(f"Cleaned outdated cache {record=}")

            await asyncio.sleep(3)

    client.get_entity = new
    asyncio.ensure_future(cleaner(client))
    logger.debug("Monkeypatched client with cacher")
