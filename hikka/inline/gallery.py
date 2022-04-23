from .types import InlineUnit
from .. import utils

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto,
    InputMediaAnimation,
    InlineQueryResultPhoto,
    InlineQuery,
    InlineQueryResultGif,
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
        elem = self.lst[0]
        del self.lst[0]
        return elem


class Gallery(InlineUnit):
    async def gallery(
        self,
        message: Union[Message, int],
        next_handler: Union[FunctionType, List[str]],
        caption: Union[str, FunctionType] = "",
        *,
        force_me: bool = False,
        always_allow: Union[list, None] = None,
        manual_security: bool = False,
        disable_security: bool = False,
        ttl: Union[int, bool] = False,
        on_unload: Union[FunctionType, None] = None,
        preload: Union[bool, int] = False,
        gif: bool = False,
        silent: bool = False,
        _reattempt: bool = False,
    ) -> Union[bool, str]:
        """
        Processes inline gallery
        Args:
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
            gif
                Whether the gallery will be filled with gifs. If you omit this argument and specify
                gifs in `next_handler`, they will be interpreted as plain images (not GIFs!)
            manual_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to avoid this, pass `manual_security=True`
            disable_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to disable all security checks on this gallery in particular, pass `disable_security=True`
            silent
                Whether the gallery must be sent silently (w/o "Loading inline gallery..." message)
        """

        if not isinstance(caption, str) and not callable(caption):
            logger.error("Invalid type for `caption`")
            return False

        if not isinstance(manual_security, bool):
            logger.error("Invalid type for `manual_security`")
            return False

        if not isinstance(silent, bool):
            logger.error("Invalid type for `silent`")
            return False

        if not isinstance(disable_security, bool):
            logger.error("Invalid type for `disable_security`")
            return False

        if not isinstance(message, (Message, int)):
            logger.error("Invalid type for `message`")
            return False

        if not isinstance(force_me, bool):
            logger.error("Invalid type for `force_me`")
            return False

        if not isinstance(gif, bool):
            logger.error("Invalid type for `gif`")
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
        btn_call_data = {
            key: utils.rand(16)
            for key in {
                "back",
                "next",
                "close",
                "show",
            }
        }

        try:
            photo_url = await self._call_photo(next_handler)
            if not photo_url:
                return False
        except Exception:
            logger.exception("Error while parsing first photo in gallery")
            return False

        perms_map = self._find_caller_sec_map() if not manual_security else None

        self._galleries[gallery_uid] = {
            "caption": caption,
            "chat": None,
            "message_id": None,
            "uid": gallery_uid,
            "photo_url": (photo_url if isinstance(photo_url, str) else photo_url[0]),
            "next_handler": next_handler,
            "btn_call_data": btn_call_data,
            "photos": [photo_url] if isinstance(photo_url, str) else photo_url,
            "current_index": 0,
            **({"ttl": round(time.time()) + ttl} if ttl else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"on_unload": on_unload} if callable(on_unload) else {}),
            **({"preload": preload} if preload else {}),
            **({"gif": gif} if gif else {}),
            **({"always_allow": always_allow} if always_allow else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
        }

        default_map = {
            **(
                {"ttl": self._galleries[gallery_uid]["ttl"]}
                if "ttl" in self._galleries[gallery_uid]
                else {}
            ),
            **({"always_allow": always_allow} if always_allow else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
        }

        self._custom_map[btn_call_data["back"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_back,
                    btn_call_data=btn_call_data,
                    gallery_uid=gallery_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["close"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._delete_unit_message,
                    unit_uid=gallery_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["next"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_next,
                    func=next_handler,
                    btn_call_data=btn_call_data,
                    gallery_uid=gallery_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["show"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_slideshow,
                    btn_call_data=btn_call_data,
                    gallery_uid=gallery_uid,
                )
            ),
            **default_map,
        }

        if isinstance(message, Message) and not silent:
            try:
                status_message = await (
                    message.edit if message.out else message.respond
                )("🌘 <b>Loading inline gallery...</b>")
            except Exception:
                status_message = None
        else:
            status_message = None

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

            if _reattempt:
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
                caption=caption,
                message=message,
                next_handler=next_handler,
                force_me=force_me,
                always_allow=always_allow,
                ttl=ttl,
                on_unload=on_unload,
                preload=preload,
                _reattempt=True,
            )

        self._galleries[gallery_uid]["chat"] = utils.get_chat_id(m)
        self._galleries[gallery_uid]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        asyncio.ensure_future(self._load_gallery_photos(gallery_uid))

        return gallery_uid

    async def _call_photo(self, callback: FunctionType) -> Union[str, bool]:
        """Parses photo url from `callback`. Returns url on success, otherwise `False`"""
        if asyncio.iscoroutinefunction(callback):
            photo_url = await callback()
        elif getattr(callback, "__call__", False):
            photo_url = callback()
        elif isinstance(callback, str):
            photo_url = callback
        elif isinstance(callback, list):
            photo_url = callback[0]
        else:
            logger.error("Invalid type for `next_handler`")
            return False

        if not isinstance(photo_url, (str, list)):
            logger.error("Got invalid result from `next_handler`")
            return False

        return photo_url

    async def _load_gallery_photos(self, gallery_uid: str):
        """Preloads photo. Should be called via ensure_future"""
        photo_url = await self._call_photo(self._galleries[gallery_uid]["next_handler"])

        self._galleries[gallery_uid]["photos"] += (
            [photo_url] if isinstance(photo_url, str) else photo_url
        )

        # If only one preload was insufficient to load needed amount of photos
        if self._galleries[gallery_uid].get("preload", False) and len(
            self._galleries[gallery_uid]["photos"]
        ) - self._galleries[gallery_uid]["current_index"] < self._galleries[
            gallery_uid
        ].get(
            "preload", False
        ):
            # Start load again
            asyncio.ensure_future(self._load_gallery_photos(gallery_uid))

    async def _gallery_slideshow_loop(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        gallery_uid: str = None,
    ):
        while True:
            await asyncio.sleep(7)

            if gallery_uid not in self._galleries or not self._galleries[
                gallery_uid
            ].get("slideshow", False):
                return

            await self._custom_map[btn_call_data["next"]]["handler"](
                call,
                *self._custom_map[btn_call_data["next"]].get("args", []),
                **self._custom_map[btn_call_data["next"]].get("kwargs", {}),
            )

    async def _gallery_slideshow(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        gallery_uid: str = None,
    ):
        if not self._galleries[gallery_uid].get("slideshow", False):
            self._galleries[gallery_uid]["slideshow"] = True
            await self.bot.edit_message_reply_markup(
                inline_message_id=call.inline_message_id,
                reply_markup=self._gallery_markup(gallery_uid),
            )
            await call.answer("✅ Slideshow on")
        else:
            del self._galleries[gallery_uid]["slideshow"]
            await self.bot.edit_message_reply_markup(
                inline_message_id=call.inline_message_id,
                reply_markup=self._gallery_markup(gallery_uid),
            )
            await call.answer("🚫 Slideshow off")
            return

        asyncio.ensure_future(
            self._gallery_slideshow_loop(
                call,
                btn_call_data,
                gallery_uid,
            )
        )

    async def _gallery_back(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        gallery_uid: str = None,
    ):
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
                media=self._get_current_media(gallery_uid),
                reply_markup=self._gallery_markup(gallery_uid),
            )
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds",
                show_alert=True,
            )
        except Exception:
            logger.exception("Exception while trying to edit media")
            await call.answer("Error occurred", show_alert=True)
            return

    def _get_current_media(
        self,
        gallery_uid: str,
    ) -> Union[InputMediaPhoto, InputMediaAnimation]:
        """Return current media, which should be updated in gallery"""
        return (
            InputMediaPhoto(
                media=self._get_next_photo(gallery_uid),
                caption=self._get_caption(gallery_uid),
                parse_mode="HTML",
            )
            if not self._galleries[gallery_uid].get("gif", False)
            else InputMediaAnimation(
                media=self._get_next_photo(gallery_uid),
                caption=self._get_caption(gallery_uid),
                parse_mode="HTML",
            )
        )

    async def _gallery_next(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        func: FunctionType = None,
        gallery_uid: str = None,
    ):
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

        if self._galleries[gallery_uid].get("preload", False) and len(
            self._galleries[gallery_uid]["photos"]
        ) - self._galleries[gallery_uid]["current_index"] < self._galleries[
            gallery_uid
        ].get(
            "preload", False
        ):
            logger.debug(f"Started preload for gallery {gallery_uid}")
            asyncio.ensure_future(self._load_gallery_photos(gallery_uid))

        try:
            await self.bot.edit_message_media(
                inline_message_id=call.inline_message_id,
                media=self._get_current_media(gallery_uid),
                reply_markup=self._gallery_markup(gallery_uid),
            )
        except (InvalidHTTPUrlContent, BadRequest):
            logger.debug("Error fetching photo content, attempting load next one")
            del self._galleries[gallery_uid]["photos"][
                self._galleries[gallery_uid]["current_index"]
            ]
            self._galleries[gallery_uid]["current_index"] -= 1
            return await self._gallery_next(call, btn_call_data, func, gallery_uid)
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds",
                show_alert=True,
            )
            return
        except Exception:
            logger.exception("Exception while trying to edit media")
            await call.answer("Error occurred", show_alert=True)
            return

    def _get_next_photo(self, gallery_uid: str) -> str:
        """Returns next photo"""
        try:
            return self._galleries[gallery_uid]["photos"][
                self._galleries[gallery_uid]["current_index"]
            ]
        except IndexError:
            logger.error(
                "Got IndexError in `_get_next_photo`. "
                f"{self._galleries[gallery_uid]['current_index']=} / "
                f"{len(self._galleries[gallery_uid]['photos'])=}"
            )
            return self._galleries[gallery_uid]["photos"][0]

    def _get_caption(self, gallery_uid: str) -> str:
        """Calls and returnes caption for gallery"""
        return (
            self._galleries[gallery_uid]["caption"]
            if isinstance(self._galleries[gallery_uid]["caption"], str)
            or not callable(self._galleries[gallery_uid]["caption"])
            else self._galleries[gallery_uid]["caption"]()
        )

    def _gallery_markup(self, gallery_uid: str) -> InlineKeyboardMarkup:
        """Converts `btn_call_data` into a aiogram markup"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "⏪",
                callback_data=self._galleries[gallery_uid]["btn_call_data"]["back"],
            ),
            InlineKeyboardButton(
                "▶️"
                if not self._galleries[gallery_uid].get("slideshow", False)
                else "⏸",
                callback_data=self._galleries[gallery_uid]["btn_call_data"]["show"],
            ),
            InlineKeyboardButton(
                "⏩",
                callback_data=self._galleries[gallery_uid]["btn_call_data"]["next"],
            ),
        )

        markup.add(
            InlineKeyboardButton(
                "❌ Close",
                callback_data=self._galleries[gallery_uid]["btn_call_data"]["close"],
            ),
        )

        return markup

    async def _gallery_inline_handler(self, inline_query: InlineQuery):
        for gallery in self._galleries.copy().values():
            if (
                inline_query.from_user.id == self._me
                and inline_query.query == gallery["uid"]
            ):
                if not gallery.get("gif", False):
                    await inline_query.answer(
                        [
                            InlineQueryResultPhoto(
                                id=utils.rand(20),
                                title="Processing inline gallery",
                                photo_url=gallery["photo_url"],
                                thumb_url="https://img.icons8.com/fluency/344/loading.png",
                                caption=self._get_caption(gallery["uid"]),
                                description="Processing inline gallery",
                                reply_markup=self._gallery_markup(
                                    gallery["uid"],
                                ),
                                parse_mode="HTML",
                            )
                        ],
                        cache_time=0,
                    )
                    return

                await inline_query.answer(
                    [
                        InlineQueryResultGif(
                            id=utils.rand(20),
                            title="Processing inline gallery",
                            gif_url=gallery["photo_url"],
                            thumb_url="https://img.icons8.com/fluency/344/loading.png",
                            caption=self._get_caption(gallery["uid"]),
                            parse_mode="HTML",
                            reply_markup=self._gallery_markup(
                                gallery["uid"],
                            ),
                        )
                    ]
                )
