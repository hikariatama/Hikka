from .types import InlineUnit
from .. import utils

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto,
    InlineQueryResultPhoto,
    InlineQuery,
)

from aiogram.utils.exceptions import InvalidHTTPUrlContent, BadRequest, RetryAfter

from typing import Union, List
from types import FunctionType
from telethon.tl.types import Message
import logging
import asyncio
import time
import functools

logger = logging.getLogger(__name__)


class ListGalleryHelper:
    def __init__(self, lst: List[str]):
        self.lst = lst

    def __call__(self):
        elem = self.lst[-1]
        del self.lst[-1]
        return elem


class Gallery(InlineUnit):
    async def gallery(
        self,
        caption: Union[str, FunctionType],
        message: Union[Message, int],
        next_handler: Union[FunctionType, List[str]],
        force_me: bool = True,
        always_allow: Union[list, None] = None,
        ttl: Union[int, bool] = False,
        on_unload: Union[FunctionType, None] = None,
        preload: Union[bool, int] = False,
        reattempt: bool = False,
    ) -> Union[bool, str]:
        """
        Processes inline gallery
            caption
                    Caption for photo, or callable, returning caption
            message
                    Where to send inline. Can be either `Message` or `int`
            next_handler
                    Callback function, which must return url for next photo or list with photo urls
            force_me
                    Either this gallery buttons must be pressed only by owner scope or no
            always_allow
                    Users, that are allowed to press buttons in addition to previous rules
            ttl
                    Time, when the gallery is going to be unloaded. Unload means, that the gallery
                    will become unusable. Pay attention, that ttl can't
                    be bigger, than default one (1 day) and must be either `int` or `False`
            on_unload
                    Callback, called when gallery is unloaded and/or closed. You can clean up trash
                    or perform another needed action
            preload
                    Either to preload gallery photos beforehand or no. If yes - specify threshold to
                    be loaded. Toggle this attribute, if your callback is too slow to load photos
                    in real time
        """

        if not isinstance(caption, str) and not callable(caption):
            logger.error("Invalid type for `caption`")
            return False

        if not isinstance(message, (Message, int)):
            logger.error("Invalid type for `message`")
            return False

        if not isinstance(force_me, bool):
            logger.error("Invalid type for `force_me`")
            return False

        if (
            not isinstance(preload, (bool, int))
            or isinstance(preload, bool)
            and preload
        ):
            logger.error("Invalid type for `preload`")
            return False

        if always_allow and not isinstance(always_allow, list):
            logger.error("Invalid type for `always_allow`")
            return False

        if not always_allow:
            always_allow = []

        if not isinstance(ttl, int) and ttl:
            logger.error("Invalid type for `ttl`")
            return False

        if isinstance(ttl, int) and (ttl > self._markup_ttl or ttl < 10):
            ttl = self._markup_ttl
            logger.debug("Defaulted ttl, because it breaks out of limits")

        if isinstance(next_handler, list):
            if all(isinstance(i, str) for i in next_handler):
                next_handler = ListGalleryHelper(next_handler)
            else:
                logger.error("Invalid type for `next_handler`")
                return False

        gallery_uid = utils.rand(30)
        btn_call_data = [utils.rand(16), utils.rand(16), utils.rand(16)]

        try:
            if asyncio.iscoroutinefunction(next_handler):
                photo_url = await next_handler()
            elif getattr(next_handler, "__call__", False):
                photo_url = next_handler()
            else:
                raise Exception("Invalid type for `next_handler`")

            if not isinstance(photo_url, (str, list)):
                raise Exception("Got invalid result from `next_handler`")
        except Exception:
            logger.exception("Error while parsing first photo in gallery")
            return False

        self._galleries[gallery_uid] = {
            "caption": caption,
            "ttl": round(time.time()) + ttl or self._markup_ttl,
            "force_me": force_me,
            "always_allow": always_allow,
            "chat": None,
            "message_id": None,
            "uid": gallery_uid,
            "photo_url": (photo_url if isinstance(photo_url, str) else photo_url[0]),
            "next_handler": next_handler,
            "btn_call_data": btn_call_data,
            "photos": [photo_url] if isinstance(photo_url, str) else photo_url,
            "current_index": 0,
            "on_unload": on_unload,
            "preload": preload,
        }

        self._custom_map[btn_call_data[0]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_back,
                    btn_call_data=btn_call_data,
                    gallery_uid=gallery_uid,
                )
            ),
            "always_allow": always_allow,
            "force_me": force_me,
        }

        self._custom_map[btn_call_data[1]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_close,
                    btn_call_data=btn_call_data,
                    gallery_uid=gallery_uid,
                )
            ),
            "always_allow": always_allow,
            "force_me": force_me,
        }

        self._custom_map[btn_call_data[2]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_next,
                    func=next_handler,
                    btn_call_data=btn_call_data,
                    gallery_uid=gallery_uid,
                )
            ),
            "always_allow": always_allow,
            "force_me": force_me,
        }

        try:
            q = await self._client.inline_query(self.bot_username, gallery_uid)
            m = await q[0].click(
                utils.get_chat_id(message) if isinstance(message, Message) else message,
                reply_to=message.reply_to_msg_id
                if isinstance(message, Message)
                else None,
            )
        except Exception:
            logger.exception("Error sending inline gallery")

            del self._galleries[gallery_uid]

            if reattempt:
                msg = (
                    "🚫 <b>A problem occurred with inline bot "
                    "while processing query. Check logs for "
                    "further info.</b>"
                )

                if isinstance(message, Message):
                    await (message.edit if message.out else message.respond)(msg)
                else:
                    await self._client.send_message(message, msg)

                return False

            return await self.gallery(
                caption,
                message,
                next_handler,
                force_me,
                always_allow,
                ttl,
                on_unload,
                preload,
                True,
            )

        self._galleries[gallery_uid]["chat"] = utils.get_chat_id(m)
        self._galleries[gallery_uid]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        asyncio.ensure_future(self._load_gallery_photos(gallery_uid))

        return gallery_uid

    async def _load_gallery_photos(self, gallery_uid: str) -> None:
        """Preloads photo. Should be called via ensure_future"""
        if asyncio.iscoroutinefunction(self._galleries[gallery_uid]["next_handler"]):
            photo_url = await self._galleries[gallery_uid]["next_handler"]()
        elif getattr(self._galleries[gallery_uid]["next_handler"], "__call__", False):
            photo_url = self._galleries[gallery_uid]["next_handler"]()
        else:
            raise Exception("Invalid type for `next_handler`")

        if not isinstance(photo_url, (str, list)):
            raise Exception("Got invalid result from `next_handler`")

        self._galleries[gallery_uid]["photos"] += (
            [photo_url] if isinstance(photo_url, str) else photo_url
        )

        # If only one preload was insufficient to load needed amount of photos
        if (
            self._galleries[gallery_uid]["preload"]
            and len(self._galleries[gallery_uid]["photos"])
            - self._galleries[gallery_uid]["current_index"]
            < self._galleries[gallery_uid]["preload"]
        ):
            # Start load again
            asyncio.ensure_future(self._load_gallery_photos(gallery_uid))

    async def _gallery_back(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        gallery_uid: str = None,
    ) -> None:
        queue = self._galleries[gallery_uid]["photos"]

        if not queue:
            await call.answer("No way back", show_alert=True)
            return

        self._galleries[gallery_uid]["current_index"] -= 1

        if self._galleries[gallery_uid]["current_index"] < 0:
            self._galleries[gallery_uid]["current_index"] = 0
            await call.answer("No way back")
            return

        try:
            await self.bot.edit_message_media(
                inline_message_id=call.inline_message_id,
                media=InputMediaPhoto(
                    media=self._get_next_photo(gallery_uid),
                    caption=self._get_caption(gallery_uid),
                    parse_mode="HTML",
                ),
                reply_markup=self._gallery_markup(btn_call_data),
            )
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds", show_alert=True
            )
        except Exception:
            logger.exception("Exception while trying to edit media")
            await call.answer("Error occurred", show_alert=True)
            return

    async def _gallery_close(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        gallery_uid: str = None,
    ) -> bool:
        try:
            await self._client.delete_messages(
                self._galleries[gallery_uid]["chat"],
                [self._galleries[gallery_uid]["message_id"]],
            )

            if callable(self._galleries[gallery_uid]["on_unload"]):
                self._galleries[gallery_uid]["on_unload"]()

            del self._galleries[gallery_uid]
        except Exception:
            return False

        return True

    async def _gallery_next(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        func: FunctionType = None,
        gallery_uid: str = None,
    ) -> None:
        self._galleries[gallery_uid]["current_index"] += 1
        # If we exceeded photos limit in gallery and need to preload more
        if self._galleries[gallery_uid]["current_index"] >= len(
            self._galleries[gallery_uid]["photos"]
        ):
            await self._load_gallery_photos(gallery_uid)

        # If we still didn't get needed photo index
        if self._galleries[gallery_uid]["current_index"] >= len(
            self._galleries[gallery_uid]["photos"]
        ):
            await call.answer("Can't load next photo")
            return

        if (
            self._galleries[gallery_uid]["preload"]
            and len(self._galleries[gallery_uid]["photos"])
            - self._galleries[gallery_uid]["current_index"]
            < self._galleries[gallery_uid]["preload"]
        ):
            logger.debug(f"Started preload for gallery {gallery_uid}")
            asyncio.ensure_future(self._load_gallery_photos(gallery_uid))

        try:
            await self.bot.edit_message_media(
                inline_message_id=call.inline_message_id,
                media=InputMediaPhoto(
                    media=self._get_next_photo(gallery_uid),
                    caption=self._get_caption(gallery_uid),
                    parse_mode="HTML",
                ),
                reply_markup=self._gallery_markup(btn_call_data),
            )
        except (InvalidHTTPUrlContent, BadRequest):
            logger.warning("Error fetching photo content, attempting load next one")
            del self._galleries[gallery_uid]["photos"][
                self._galleries[gallery_uid]["current_index"]
            ]
            self._galleries[gallery_uid]["current_index"] -= 1
            await self._gallery_next(call, btn_call_data, func, gallery_uid)
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds", show_alert=True
            )
        except Exception:
            logger.exception("Exception while trying to edit media")
            await call.answer("Error occurred", show_alert=True)

    def _get_next_photo(self, gallery_uid: str) -> str:
        """Returns next photo"""
        return self._galleries[gallery_uid]["photos"][
            self._galleries[gallery_uid]["current_index"]
        ]

    def _get_caption(self, gallery_uid: str) -> str:
        """Calls and returnes caption for gallery"""
        return (
            self._galleries[gallery_uid]["caption"]
            if isinstance(self._galleries[gallery_uid]["caption"], str)
            or not callable(self._galleries[gallery_uid]["caption"])
            else self._galleries[gallery_uid]["caption"]()
        )

    def _gallery_markup(self, btn_call_data: List[str]) -> InlineKeyboardMarkup:
        """Converts `btn_call_data` into a aiogram markup"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("⬅️", callback_data=btn_call_data[0]),
            InlineKeyboardButton("❌", callback_data=btn_call_data[1]),
            InlineKeyboardButton("➡️", callback_data=btn_call_data[2]),
        )

        return markup

    async def _gallery_inline_handler(self, inline_query: InlineQuery) -> None:
        for gallery in self._galleries.copy().values():
            if (
                inline_query.from_user.id
                in [self._me]
                + self._client.dispatcher.security._owner
                + gallery["always_allow"]
                and inline_query.query == gallery["uid"]
            ):
                await inline_query.answer(
                    [
                        InlineQueryResultPhoto(
                            id=utils.rand(20),
                            title="Processing inline gallery",
                            photo_url=gallery["photo_url"],
                            thumb_url="https://img.icons8.com/fluency/344/loading.png",
                            caption=self._get_caption(gallery["uid"]),
                            description=self._get_caption(gallery["uid"]),
                            reply_markup=self._gallery_markup(gallery["btn_call_data"]),
                            parse_mode="HTML",
                        )
                    ],
                    cache_time=0,
                )
                return
