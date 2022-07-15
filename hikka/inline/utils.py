#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import inspect
import logging
import contextlib
import io
import os
from copy import deepcopy
from typing import List, Optional, Union
from urllib.parse import urlparse
import functools

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAnimation,
    InputMediaDocument,
    InputMediaAudio,
    InputMediaPhoto,
    InputMediaVideo,
)

from aiogram.utils.exceptions import (
    MessageIdInvalid,
    MessageNotModified,
    RetryAfter,
    BadRequest,
)

from .. import utils
from .._types import Module
from .types import InlineUnit, InlineCall

logger = logging.getLogger(__name__)


class Utils(InlineUnit):
    def _generate_markup(
        self,
        markup_obj: Union[str, list],
    ) -> Union[None, InlineKeyboardMarkup]:
        """Generate markup for form or list of `dict`s"""
        if not markup_obj:
            return None

        if isinstance(markup_obj, InlineKeyboardMarkup):
            return markup_obj

        markup = InlineKeyboardMarkup()

        map_ = (
            self._units[markup_obj]["buttons"]
            if isinstance(markup_obj, str)
            else markup_obj
        )

        map_ = self._normalize_markup(map_)

        setup_callbacks = False

        for row in map_:
            for button in row:
                if not isinstance(button, dict):
                    logger.error(
                        f"Button {button} is not a `dict`, but `{type(button)}` in"
                        f" {map_}"
                    )
                    return None

                if "callback" not in button:
                    if button.get("action") == "close":
                        button["callback"] = self._close_unit_handler

                    if button.get("action") == "unload":
                        button["callback"] = self._unload_unit_handler

                    if button.get("action") == "answer":
                        if not button.get("text"):
                            logger.error(
                                f"Button {button} has no `text` to answer with"
                            )
                            return None

                        button["callback"] = functools.partial(
                            self._answer_unit_handler,
                            show_alert=button.get("show_alert", False),
                            text=button["text"],
                        )

                if "callback" in button and "_callback_data" not in button:
                    button["_callback_data"] = utils.rand(30)
                    setup_callbacks = True

                if "input" in button and "_switch_query" not in button:
                    button["_switch_query"] = utils.rand(10)

        for row in map_:
            line = []
            for button in row:
                try:
                    if "url" in button:
                        if not utils.check_url(button["url"]):
                            logger.warning(
                                "Button have not been added to form, "
                                "because its url is invalid"
                            )
                            continue

                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                url=button["url"],
                            )
                        ]
                    elif "callback" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                callback_data=button["_callback_data"],
                            )
                        ]
                        if setup_callbacks:
                            self._custom_map[button["_callback_data"]] = {
                                "handler": button["callback"],
                                **(
                                    {"always_allow": button["always_allow"]}
                                    if button.get("always_allow", False)
                                    else {}
                                ),
                                **(
                                    {"args": button["args"]}
                                    if button.get("args", False)
                                    else {}
                                ),
                                **(
                                    {"kwargs": button["kwargs"]}
                                    if button.get("kwargs", False)
                                    else {}
                                ),
                                **(
                                    {"force_me": True}
                                    if button.get("force_me", False)
                                    else {}
                                ),
                                **(
                                    {"disable_security": True}
                                    if button.get("disable_security", False)
                                    else {}
                                ),
                            }
                    elif "input" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                switch_inline_query_current_chat=button["_switch_query"]
                                + " ",
                            )
                        ]
                    elif "data" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                callback_data=button["data"],
                            )
                        ]
                    elif "switch_inline_query_current_chat" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                switch_inline_query_current_chat=button[
                                    "switch_inline_query_current_chat"
                                ],
                            )
                        ]
                    elif "switch_inline_query" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                switch_inline_query_current_chat=button[
                                    "switch_inline_query"
                                ],
                            )
                        ]
                    else:
                        logger.warning(
                            "Button have not been added to "
                            "form, because it is not structured "
                            f"properly. {button}"
                        )
                except KeyError:
                    logger.exception(
                        "Error while forming markup! Probably, you "
                        "passed wrong type combination for button. "
                        "Contact developer of module."
                    )
                    return False

            markup.row(*line)

        return markup

    generate_markup = _generate_markup

    async def _close_unit_handler(self, call: InlineCall):
        await call.delete()

    async def _unload_unit_handler(self, call: InlineCall):
        await call.unload()

    async def _answer_unit_handler(self, call: InlineCall, text: str, show_alert: bool):
        await call.answer(text, show_alert=show_alert)

    async def check_inline_security(self, *, func: callable, user: int) -> bool:
        """Checks if user with id `user` is allowed to run function `func`"""
        return await self._client.dispatcher.security.check(
            func=func,
            user=user,
            message=None,
        )

    def _find_caller_sec_map(self) -> Union[callable, None]:
        try:
            for stack_entry in inspect.stack():
                if hasattr(stack_entry, "function") and (
                    stack_entry.function.endswith("cmd")
                    or stack_entry.function.endswith("_inline_handler")
                ):
                    logger.debug(f"Found caller: {stack_entry.function}")
                    return next(
                        lambda: self._client.dispatcher.security.get_flags(
                            getattr(
                                cls_,
                                stack_entry.function,
                            ),
                        )
                        for name, cls_ in stack_entry.frame.f_globals.items()
                        if name.endswith("Mod") and issubclass(cls_, Module)
                    )
        except Exception:
            logger.debug("Can't parse security mask in form", exc_info=True)

        return None

    def _normalize_markup(self, reply_markup: Union[dict, list]) -> list:
        if isinstance(reply_markup, dict):
            return [[reply_markup]]

        if isinstance(reply_markup, list) and any(
            isinstance(i, dict) for i in reply_markup
        ):
            return [reply_markup]

        return reply_markup

    async def _edit_unit(
        self,
        text: str,
        reply_markup: List[List[dict]] = None,
        *,
        photo: Optional[str] = None,
        file: Optional[str] = None,
        video: Optional[str] = None,
        audio: Optional[Union[dict, str]] = None,
        gif: Optional[str] = None,
        mime_type: Optional[str] = None,
        force_me: Union[bool, None] = None,
        disable_security: Union[bool, None] = None,
        always_allow: Union[List[int], None] = None,
        disable_web_page_preview: bool = True,
        query: CallbackQuery = None,
        unit_id: str = None,
        inline_message_id: Optional[str] = None,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
    ) -> bool:
        """
        Edits unit message
        :param text: Text of message
        :param reply_markup: Inline keyboard
        :param photo: Url to a valid photo to attach to message
        :param file: Url to a valid file to attach to message
        :param video: Url to a valid video to attach to message
        :param audio: Url to a valid audio to attach to message
        :param gif: Url to a valid gif to attach to message
        :param mime_type: Mime type of file
        :param force_me: Allow only userbot owner to interact with buttons
        :param disable_security: Disable security check for buttons
        :param always_allow: List of user ids, which will always be allowed
        :param disable_web_page_preview: Disable web page preview
        :param query: Callback query
        :return: Status of edit"""
        if isinstance(reply_markup, (list, dict)):
            reply_markup = self._normalize_markup(reply_markup)
        elif reply_markup is None:
            reply_markup = [[]]

        if not isinstance(text, str):
            logger.error("Invalid type for `text`")
            return False

        if photo and (not isinstance(photo, str) or not utils.check_url(photo)):
            logger.error("Invalid type for `photo`")
            return False

        if gif and (not isinstance(gif, str) or not utils.check_url(gif)):
            logger.error("Invalid type for `gif`")
            return False

        if file and (
            not isinstance(file, str, bytes, io.BytesIO)
            or (isinstance(file, str) and not utils.check_url(file))
        ):
            logger.error("Invalid type for `file`")
            return False

        if file and not mime_type:
            logger.error(
                "You must pass `mime_type` along with `file` field\n"
                "It may be either 'application/zip' or 'application/pdf'"
            )
            return False

        if video and (not isinstance(video, str) or not utils.check_url(video)):
            logger.error("Invalid type for `video`")
            return False

        if isinstance(audio, str):
            audio = {"url": audio}

        if audio and (
            not isinstance(audio, dict)
            or "url" not in audio
            or not utils.check_url(audio["url"])
        ):
            logger.error("Invalid type for `audio`")
            return False

        media_params = [
            photo is None,
            gif is None,
            file is None,
            video is None,
            audio is None,
        ]

        if media_params.count(False) > 1:
            logger.error("You passed two or more exclusive parameters simultaneously")
            return False

        if unit_id is not None and unit_id in self._units:
            unit = self._units[unit_id]

            unit["buttons"] = reply_markup

            if isinstance(force_me, bool):
                unit["force_me"] = force_me

            if isinstance(disable_security, bool):
                unit["disable_security"] = disable_security

            if isinstance(always_allow, list):
                unit["always_allow"] = always_allow
        else:
            unit = {}

        if not chat_id or not message_id:
            inline_message_id = (
                inline_message_id
                or unit.get("inline_message_id", False)
                or getattr(query, "inline_message_id", None)
            )

        if not chat_id and not message_id and not inline_message_id:
            logger.warning(
                "Attempted to edit message with no `inline_message_id`. "
                "Possible reasons:\n"
                "- Form was sent without buttons and due to "
                "the limits of Telegram API can't be edited\n"
                "- There is an in-userbot error, which you should report"
            )
            return False

        # If passed `photo` is gif
        try:
            path = urlparse(photo).path
            ext = os.path.splitext(path)[1]
        except Exception:
            ext = None

        if photo is not None and ext in {".gif", ".mp4"}:
            gif = deepcopy(photo)
            photo = None

        if file is not None:
            media = InputMediaDocument(file, caption=text, parse_mode="HTML")
        elif photo is not None:
            media = InputMediaPhoto(photo, caption=text, parse_mode="HTML")
        elif audio is not None:
            media = InputMediaAudio(
                audio["url"],
                title=audio.get("title"),
                performer=audio.get("performer"),
                duration=audio.get("duration"),
                caption=text,
                parse_mode="HTML",
            )
        elif video is not None:
            media = InputMediaVideo(video, caption=text, parse_mode="HTML")
        elif gif is not None:
            media = InputMediaAnimation(gif, caption=text, parse_mode="HTML")
        else:
            try:
                await self.bot.edit_message_text(
                    text,
                    **(
                        {"inline_message_id": inline_message_id}
                        if inline_message_id
                        else {"chat_id": chat_id, "message_id": message_id}
                    ),
                    disable_web_page_preview=disable_web_page_preview,
                    reply_markup=self.generate_markup(
                        reply_markup
                        if isinstance(reply_markup, list)
                        else unit.get("buttons", [])
                    ),
                )
            except MessageNotModified:
                if query:
                    with contextlib.suppress(Exception):
                        await query.answer()

                return False
            except RetryAfter as e:
                logger.info(f"Sleeping {e.timeout}s on aiogram FloodWait...")
                await asyncio.sleep(e.timeout)
                return await self._edit_unit(**utils.get_kwargs())
            except MessageIdInvalid:
                with contextlib.suppress(Exception):
                    await query.answer(
                        "I should have edited some message, but it is deleted :("
                    )

                return False
            except BadRequest as e:
                if "There is no text in the message to edit" not in str(e):
                    raise

                try:
                    await self.bot.edit_message_caption(
                        caption=text,
                        **(
                            {"inline_message_id": inline_message_id}
                            if inline_message_id
                            else {"chat_id": chat_id, "message_id": message_id}
                        ),
                        reply_markup=self.generate_markup(
                            reply_markup
                            if isinstance(reply_markup, list)
                            else unit.get("buttons", [])
                        ),
                    )
                except Exception:
                    return False
                else:
                    return True
            else:
                return True

        try:
            await self.bot.edit_message_media(
                **(
                    {"inline_message_id": inline_message_id}
                    if inline_message_id
                    else {"chat_id": chat_id, "message_id": message_id}
                ),
                media=media,
                reply_markup=self.generate_markup(
                    reply_markup
                    if isinstance(reply_markup, list)
                    else unit.get("buttons", [])
                ),
            )
        except RetryAfter as e:
            logger.info(f"Sleeping {e.timeout}s on aiogram FloodWait...")
            await asyncio.sleep(e.timeout)
            return await self._edit_unit(**utils.get_kwargs())
        except MessageIdInvalid:
            with contextlib.suppress(Exception):
                await query.answer(
                    "I should have edited some message, but it is deleted :("
                )
            return False
        else:
            return True

    async def _delete_unit_message(
        self,
        call: CallbackQuery = None,
        unit_id: str = None,
    ) -> bool:
        """Params `self`, `unit_id` are for internal use only, do not try to pass them"""
        if getattr(getattr(call, "message", None), "chat", None):
            try:
                await self.bot.delete_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                )
            except Exception:
                return False

            return True

        if not unit_id and hasattr(call, "unit_id") and call.unit_id:
            unit_id = call.unit_id

        try:
            await self._client.delete_messages(
                self._units[unit_id]["chat"],
                [self._units[unit_id]["message_id"]],
            )

            await self._unload_unit(None, unit_id)
        except Exception:
            return False

        return True

    async def _unload_unit(
        self,
        call: CallbackQuery = None,
        unit_id: str = None,
    ) -> bool:
        """Params `self`, `unit_id` are for internal use only, do not try to pass them"""
        try:
            if "on_unload" in self._units[unit_id] and callable(
                self._units[unit_id]["on_unload"]
            ):
                self._units[unit_id]["on_unload"]()

            if unit_id in self._units:
                del self._units[unit_id]
            else:
                return False
        except Exception:
            return False

        return True

    def build_pagination(
        self,
        callback: callable,
        total_pages: int,
        unit_id: Optional[str] = None,
        current_page: Optional[int] = None,
    ) -> List[dict]:
        # Based on https://github.com/pystorage/pykeyboard/blob/master/pykeyboard/inline_pagination_keyboard.py#L4
        if current_page is None:
            current_page = self._units[unit_id]["current_index"] + 1

        if total_pages <= 5:
            return [
                [
                    {"text": number, "args": (number - 1,), "callback": callback}
                    if number != current_page
                    else {
                        "text": f"· {number} ·",
                        "args": (number - 1,),
                        "callback": callback,
                    }
                    for number in range(1, total_pages + 1)
                ]
            ]

        if current_page <= 3:
            return [
                [
                    {
                        "text": f"· {number} ·",
                        "args": (number - 1,),
                        "callback": callback,
                    }
                    if number == current_page
                    else {
                        "text": f"{number} ›",
                        "args": (number - 1,),
                        "callback": callback,
                    }
                    if number == 4
                    else {
                        "text": f"{total_pages} »",
                        "args": (total_pages - 1,),
                        "callback": callback,
                    }
                    if number == 5
                    else {
                        "text": number,
                        "args": (number - 1,),
                        "callback": callback,
                    }
                    for number in range(1, 6)
                ]
            ]

        if current_page > total_pages - 3:
            return [
                [
                    {"text": "« 1", "args": (0,), "callback": callback},
                    {
                        "text": f"‹ {total_pages - 3}",
                        "args": (total_pages - 4,),
                        "callback": callback,
                    },
                ]
                + [
                    {
                        "text": f"· {number} ·",
                        "args": (number - 1,),
                        "callback": callback,
                    }
                    if number == current_page
                    else {
                        "text": number,
                        "args": (number - 1,),
                        "callback": callback,
                    }
                    for number in range(total_pages - 2, total_pages + 1)
                ]
            ]

        return [
            [
                {"text": "« 1", "args": (0,), "callback": callback},
                {
                    "text": f"‹ {current_page - 1}",
                    "args": (current_page - 2,),
                    "callback": callback,
                },
                {
                    "text": f"· {current_page} ·",
                    "args": (current_page - 1,),
                    "callback": callback,
                },
                {
                    "text": f"{current_page + 1} ›",
                    "args": (current_page,),
                    "callback": callback,
                },
                {
                    "text": f"{total_pages} »",
                    "args": (total_pages - 1,),
                    "callback": callback,
                },
            ]
        ]

    def _validate_markup(
        self,
        buttons: Optional[Union[List[List[dict]], List[dict], dict]],
    ) -> list:
        if buttons is None:
            buttons = []

        if not isinstance(buttons, (list, dict)):
            logger.error(
                "Reply markup ommited because passed type is not valid"
                f" ({type(buttons)})"
            )
            return None

        buttons = self._normalize_markup(buttons)

        if not all(all(isinstance(button, dict) for button in row) for row in buttons):
            logger.error(
                "Reply markup ommited because passed invalid type for one of the"
                " buttons"
            )
            return None

        if not all(
            all(
                "url" in button
                or "callback" in button
                or "input" in button
                or "data" in button
                or "action" in button
                for button in row
            )
            for row in buttons
        ):
            logger.error(
                "Invalid button specified. "
                "Button must contain one of the following fields:\n"
                "  - `url`\n"
                "  - `callback`\n"
                "  - `input`\n"
                "  - `data`\n"
                "  - `action`"
            )
            return None

        return buttons
