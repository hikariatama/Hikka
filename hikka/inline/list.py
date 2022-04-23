from .types import InlineUnit, InlineMessage
from .. import utils

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from aiogram.utils.exceptions import RetryAfter

from typing import Union, List as _List
from types import FunctionType
from telethon.tl.types import Message
import logging
import asyncio
import time
import functools


logger = logging.getLogger(__name__)


class List(InlineUnit):
    async def list(
        self,
        message: Union[Message, int],
        strings: _List[str],
        *,
        force_me: bool = False,
        always_allow: Union[list, None] = None,
        manual_security: bool = False,
        disable_security: bool = False,
        ttl: Union[int, bool] = False,
        on_unload: Union[FunctionType, None] = None,
        silent: bool = False,
    ) -> Union[bool, str]:
        """
        Processes inline lists
        Args:
            message
                Where to send list. Can be either `Message` or `int`
            strings
                List of strings, which should become inline list
            force_me
                Either this list buttons must be pressed only by owner scope or no
            always_allow
                Users, that are allowed to press buttons in addition to previous rules
            ttl
                Time, when the list is going to be unloaded. Unload means, that the list
                will become unusable. Pay attention, that ttl can't
                be bigger, than default one (1 day) and must be either `int` or `False`
            on_unload
                Callback, called when list is unloaded and/or closed. You can clean up trash
                or perform another needed action
            manual_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to avoid this, pass `manual_security=True`
            disable_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to disable all security checks on this list in particular, pass `disable_security=True`
            silent
                Whether the list must be sent silently (w/o "Loading inline list..." message)
        """

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

        if not isinstance(strings, list) or not strings:
            logger.error("Invalid type for `strings`")
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

        list_uid = utils.rand(30)
        btn_call_data = {
            key: utils.rand(16)
            for key in {
                "back",
                "next",
                "close",
            }
        }

        perms_map = self._find_caller_sec_map() if not manual_security else None

        self._lists[list_uid] = {
            "chat": None,
            "message_id": None,
            "uid": list_uid,
            "btn_call_data": btn_call_data,
            "current_index": 0,
            "strings": strings,
            "future": asyncio.Event(),
            **({"ttl": round(time.time()) + ttl} if ttl else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"on_unload": on_unload} if callable(on_unload) else {}),
            **({"always_allow": always_allow} if always_allow else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
        }

        default_map = {
            **(
                {"ttl": self._lists[list_uid]["ttl"]}
                if "ttl" in self._lists[list_uid]
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
                    self._list_back,
                    btn_call_data=btn_call_data,
                    list_uid=list_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["close"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._delete_unit_message,
                    unit_uid=list_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["next"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._list_next,
                    btn_call_data=btn_call_data,
                    list_uid=list_uid,
                )
            ),
            **default_map,
        }

        if isinstance(message, Message) and not silent:
            try:
                status_message = await (
                    message.edit if message.out else message.respond
                )("🌘 <b>Loading inline list...</b>")
            except Exception:
                status_message = None
        else:
            status_message = None

        try:
            q = await self._client.inline_query(self.bot_username, list_uid)
            m = await q[0].click(
                utils.get_chat_id(message) if isinstance(message, Message) else message,
                reply_to=message.reply_to_msg_id
                if isinstance(message, Message)
                else None,
            )
        except Exception:
            logger.exception("Error sending inline list")
            del self._lists[list_uid]
            return

        await self._lists[list_uid]["future"].wait()
        del self._lists[list_uid]["future"]

        self._lists[list_uid]["chat"] = utils.get_chat_id(m)
        self._lists[list_uid]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        return InlineMessage(self, list_uid, self._lists[list_uid]["inline_message_id"])

    async def _list_back(
        self,
        call: CallbackQuery,
        btn_call_data: _List[str] = None,
        list_uid: str = None,
    ):
        if not self._lists[list_uid]["current_index"]:
            await call.answer("No way back", show_alert=True)
            return

        self._lists[list_uid]["current_index"] -= 1

        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=self._lists[list_uid]["strings"][
                    self._lists[list_uid]["current_index"]
                ],
                parse_mode="HTML",
                reply_markup=self._list_markup(list_uid),
            )
            await call.answer()
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds",
                show_alert=True,
            )
        except Exception:
            logger.exception("Exception while trying to edit list")
            await call.answer("Error occurred", show_alert=True)
            return

    async def _list_next(
        self,
        call: CallbackQuery,
        btn_call_data: _List[str] = None,
        func: FunctionType = None,
        list_uid: str = None,
    ):
        self._lists[list_uid]["current_index"] += 1
        # If we exceeded limit in list
        if self._lists[list_uid]["current_index"] >= len(
            self._lists[list_uid]["strings"]
        ):
            await call.answer("No entries left...", show_alert=True)
            self._lists[list_uid]["current_index"] -= 1
            return

        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=self._lists[list_uid]["strings"][
                    self._lists[list_uid]["current_index"]
                ],
                parse_mode="HTML",
                reply_markup=self._list_markup(list_uid),
            )
            await call.answer()
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds",
                show_alert=True,
            )
            return
        except Exception:
            logger.exception("Exception while trying to edit list")
            await call.answer("Error occurred", show_alert=True)
            return

    def _list_markup(self, list_uid: str) -> InlineKeyboardMarkup:
        """Converts `btn_call_data` into a aiogram markup"""
        markup = InlineKeyboardMarkup()
        markup.add(
            *(
                [
                    InlineKeyboardButton(
                        f"⏪ [{self._lists[list_uid]['current_index']} / {len(self._lists[list_uid]['strings'])}]",
                        callback_data=self._lists[list_uid]["btn_call_data"]["back"],
                    )
                ]
                if self._lists[list_uid]["current_index"] > 0
                else []
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=self._lists[list_uid]["btn_call_data"]["close"],
            ),
            *(
                [
                    InlineKeyboardButton(
                        f"⏩ [{self._lists[list_uid]['current_index'] + 2} / {len(self._lists[list_uid]['strings'])}]",
                        callback_data=self._lists[list_uid]["btn_call_data"]["next"],
                    ),
                ]
                if self._lists[list_uid]["current_index"]
                < len(self._lists[list_uid]["strings"]) - 1
                else []
            ),
        )

        return markup

    async def _list_inline_handler(self, inline_query: InlineQuery):
        for strings in self._lists.copy().values():
            if (
                inline_query.from_user.id == self._me
                and inline_query.query == strings["uid"]
            ):
                await inline_query.answer(
                    [
                        InlineQueryResultArticle(
                            id=utils.rand(20),
                            title="Hikka",
                            input_message_content=InputTextMessageContent(
                                self._lists[inline_query.query]["strings"][0],
                                "HTML",
                                disable_web_page_preview=True,
                            ),
                            reply_markup=self._list_markup(inline_query.query),
                        )
                    ],
                    cache_time=60,
                )
