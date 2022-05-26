import asyncio
import functools
import logging
import time
from types import FunctionType
from typing import List as _List
from typing import Optional, Union

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.utils.exceptions import RetryAfter
from telethon.tl.types import Message

from .. import utils
from .types import InlineMessage, InlineUnit

logger = logging.getLogger(__name__)


class List(InlineUnit):
    async def list(
        self,
        message: Union[Message, int],
        strings: _List[str],
        *,
        force_me: Optional[bool] = False,
        always_allow: Optional[list] = None,
        manual_security: Optional[bool] = False,
        disable_security: Optional[bool] = False,
        ttl: Optional[Union[int, bool]] = False,
        on_unload: Optional[FunctionType] = None,
        silent: Optional[bool] = False,
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

        if len(strings) > 50:
            logger.error(f"Too much pages for `strings` ({len(strings)})")
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

        unit_uid = utils.rand(16)
        btn_call_data = {key: utils.rand(10) for key in {"back", "next", "close"}}

        perms_map = self._find_caller_sec_map() if not manual_security else None

        self._units[unit_uid] = {
            "type": "list",
            "chat": None,
            "message_id": None,
            "uid": unit_uid,
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
                {"ttl": self._units[unit_uid]["ttl"]}
                if "ttl" in self._units[unit_uid]
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
                    unit_uid=unit_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["close"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._delete_unit_message,
                    unit_uid=unit_uid,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["next"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._list_next,
                    btn_call_data=btn_call_data,
                    unit_uid=unit_uid,
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
            q = await self._client.inline_query(self.bot_username, unit_uid)
            m = await q[0].click(
                utils.get_chat_id(message) if isinstance(message, Message) else message,
                reply_to=message.reply_to_msg_id
                if isinstance(message, Message)
                else None,
            )
        except Exception:
            logger.exception("Error sending inline list")
            del self._units[unit_uid]
            return

        await self._units[unit_uid]["future"].wait()
        del self._units[unit_uid]["future"]

        self._units[unit_uid]["chat"] = utils.get_chat_id(m)
        self._units[unit_uid]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        return InlineMessage(self, unit_uid, self._units[unit_uid]["inline_message_id"])

    async def _list_back(
        self,
        call: CallbackQuery,
        btn_call_data: _List[str] = None,
        unit_uid: str = None,
    ):
        if not self._units[unit_uid]["current_index"]:
            await call.answer("No way back", show_alert=True)
            return

        self._units[unit_uid]["current_index"] -= 1

        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=self._units[unit_uid]["strings"][
                    self._units[unit_uid]["current_index"]
                ],
                reply_markup=self._list_markup(unit_uid),
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
        unit_uid: str = None,
    ):
        self._units[unit_uid]["current_index"] += 1
        # If we exceeded limit in list
        if self._units[unit_uid]["current_index"] >= len(
            self._units[unit_uid]["strings"]
        ):
            await call.answer("No entries left...", show_alert=True)
            self._units[unit_uid]["current_index"] -= 1
            return

        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=self._units[unit_uid]["strings"][
                    self._units[unit_uid]["current_index"]
                ],
                reply_markup=self._list_markup(unit_uid),
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

    def _list_markup(self, unit_uid: str) -> InlineKeyboardMarkup:
        """Converts `btn_call_data` into a aiogram markup"""
        markup = InlineKeyboardMarkup()
        markup.add(
            *(
                [
                    InlineKeyboardButton(
                        f"⏪ [{self._units[unit_uid]['current_index']} / {len(self._units[unit_uid]['strings'])}]",
                        callback_data=self._units[unit_uid]["btn_call_data"]["back"],
                    )
                ]
                if self._units[unit_uid]["current_index"] > 0
                else []
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=self._units[unit_uid]["btn_call_data"]["close"],
            ),
            *(
                [
                    InlineKeyboardButton(
                        f"⏩ [{self._units[unit_uid]['current_index'] + 2} / {len(self._units[unit_uid]['strings'])}]",
                        callback_data=self._units[unit_uid]["btn_call_data"]["next"],
                    ),
                ]
                if self._units[unit_uid]["current_index"]
                < len(self._units[unit_uid]["strings"]) - 1
                else []
            ),
        )

        return markup

    async def _list_inline_handler(self, inline_query: InlineQuery):
        for unit in self._units.copy().values():
            if (
                inline_query.from_user.id == self._me
                and inline_query.query == unit["uid"]
                and unit["type"] == "list"
            ):
                await inline_query.answer(
                    [
                        InlineQueryResultArticle(
                            id=utils.rand(20),
                            title="Hikka",
                            input_message_content=InputTextMessageContent(
                                unit["strings"][0],
                                "HTML",
                                disable_web_page_preview=True,
                            ),
                            reply_markup=self._list_markup(inline_query.query),
                        )
                    ],
                    cache_time=60,
                )
