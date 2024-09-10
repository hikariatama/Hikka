# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import logging
import time
import typing

from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from .. import utils
from .types import InlineUnit

logger = logging.getLogger(__name__)


class QueryGallery(InlineUnit):
    async def query_gallery(
        self,
        query: InlineQuery,
        items: typing.List[typing.Dict[str, typing.Any]],
        *,
        force_me: bool = False,
        disable_security: bool = False,
        always_allow: typing.Optional[typing.List[int]] = None,
    ) -> bool:
        """
        Answer inline query with a bunch of inline galleries
        :param query: `InlineQuery` which should be answered with inline gallery
        :param items: Array of dicts with inline results.
                      Each dict *must* has a:
                          - `title` - The title of the result
                          - `description` - Short description of the result
                          - `next_handler` - Inline gallery handler. Callback or awaitable
                      Each dict *can* has a:
                          - `caption` - Caption of photo. Defaults to `""`
                          - `force_me` - Whether the button must be accessed only by owner. Defaults to `False`
                          - `disable_security` - Whether to disable the security checks at all. Defaults to `False`
        :param force_me: Either this gallery buttons must be pressed only by owner scope or no
        :param always_allow: Users, that are allowed to press buttons in addition to previous rules
        :param disable_security: By default, Hikka will try to check security of gallery
                                 If you want to disable all security checks on this gallery in particular, pass `disable_security=True`
        :return: Status of answer
        """
        if not isinstance(force_me, bool):
            logger.error(
                "Invalid type for `force_me`. Expected `bool`, got %s",
                type(force_me),
            )
            return False

        if not isinstance(disable_security, bool):
            logger.error(
                "Invalid type for `disable_security`. Expected `bool`, got %s",
                type(disable_security),
            )
            return False

        if always_allow and not isinstance(always_allow, list):
            logger.error(
                "Invalid type for `always_allow`. Expected `list`, got %s",
                type(always_allow),
            )
            return False

        if not always_allow:
            always_allow = []

        if (
            not isinstance(items, list)
            or not all(isinstance(i, dict) for i in items)
            or not all(
                "title" in i
                and "description" in i
                and "next_handler" in i
                and (
                    callable(i["next_handler"])
                    or asyncio.iscoroutinefunction(i)
                    or isinstance(i, list)
                )
                and isinstance(i["title"], str)
                and isinstance(i["description"], str)
                for i in items
            )
        ):
            logger.error("Invalid `items` specified in query gallery")
            return False

        result = []
        for i in items:
            if "thumb_handler" not in i:
                photo_url = await self._call_photo(i["next_handler"])
                if not photo_url:
                    return False

                if isinstance(photo_url, list):
                    photo_url = photo_url[0]

                if not isinstance(photo_url, str):
                    logger.error(
                        "Invalid result from `next_handler`. Expected `str`, got %s",
                        type(photo_url),
                    )
                    continue
            else:
                photo_url = await self._call_photo(i["thumb_handler"])
                if not photo_url:
                    return False

                if isinstance(photo_url, list):
                    photo_url = photo_url[0]

                if not isinstance(photo_url, str):
                    logger.error(
                        "Invalid result from `thumb_handler`. Expected `str`, got %s",
                        type(photo_url),
                    )
                    continue

            id_ = utils.rand(16)

            self._custom_map[id_] = {
                "handler": i["next_handler"],
                "ttl": round(time.time()) + 120,
                **({"always_allow": always_allow} if always_allow else {}),
                **({"force_me": force_me} if force_me else {}),
                **({"disable_security": disable_security} if disable_security else {}),
                **({"caption": i["caption"]} if "caption" in i else {}),
            }

            result += [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title=i["title"],
                    description=i["description"],
                    input_message_content=InputTextMessageContent(
                        f"🌘 <b>Opening gallery...</b>\n<i>#id: {id_}</i>",
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url=photo_url,
                    thumb_width=128,
                    thumb_height=128,
                )
            ]

        await query.answer(result, cache_time=0)
        return True
