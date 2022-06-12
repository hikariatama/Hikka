import asyncio
import contextlib
import copy
import functools
import logging
import time
import traceback
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
from telethon.errors.rpcerrorlist import ChatSendInlineForbiddenError

from .. import utils, main
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
        custom_buttons: Optional[Union[_List[_List[dict]], _List[dict], dict]] = None,
    ) -> Union[bool, InlineMessage]:
        """
        Send inline list to chat
        :param message: Where to send list. Can be either `Message` or `int`
        :param strings: List of strings, which should become inline list
        :param force_me: Either this list buttons must be pressed only by owner scope or no
        :param always_allow: Users, that are allowed to press buttons in addition to previous rules
        :param ttl: Time, when the list is going to be unloaded. Unload means, that the list
                    will become unusable. Pay attention, that ttl can't
                    be bigger, than default one (1 day) and must be either `int` or `False`
        :param on_unload: Callback, called when list is unloaded and/or closed. You can clean up trash
                          or perform another needed action
        :param manual_security: By default, Hikka will try to inherit inline buttons security from the caller (command)
                                If you want to avoid this, pass `manual_security=True`
        :param disable_security: By default, Hikka will try to inherit inline buttons security from the caller (command)
                                 If you want to disable all security checks on this list in particular, pass `disable_security=True`
        :param silent: Whether the list must be sent silently (w/o "Loading inline list..." message)
        :param custom_buttons: Custom buttons to add above native ones
        :return: If list is sent, returns :obj:`InlineMessage`, otherwise returns `False`
        """
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self._client._tg_id)

        if custom_buttons is None:
            custom_buttons = []

        if not isinstance(custom_buttons, (list, dict)):
            logger.error("Invalid type for `custom_buttons`")
            return False

        custom_buttons = self._normalize_markup(custom_buttons)

        if not all(
            all(isinstance(button, dict) for button in row) for row in custom_buttons
        ):
            logger.error("Invalid type for one of the buttons. It must be `dict`")
            return False

        if not all(
            all(
                "url" in button
                or "callback" in button
                or "input" in button
                or "data" in button
                or "action" in button
                for button in row
            )
            for row in custom_buttons
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

        unit_id = utils.rand(16)
        btn_call_data = {key: utils.rand(10) for key in {"back", "next", "close"}}

        perms_map = self._find_caller_sec_map() if not manual_security else None

        self._units[unit_id] = {
            "type": "list",
            "chat": None,
            "message_id": None,
            "uid": unit_id,
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
                {"ttl": self._units[unit_id]["ttl"]}
                if "ttl" in self._units[unit_id]
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
                    unit_id=unit_id,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["close"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._delete_unit_message,
                    unit_id=unit_id,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["next"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._list_next,
                    btn_call_data=btn_call_data,
                    unit_id=unit_id,
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

        async def answer(msg: str):
            nonlocal message
            if isinstance(message, Message):
                await (message.edit if message.out else message.respond)(msg)
            else:
                await self._client.send_message(message, msg)

        try:
            q = await self._client.inline_query(self.bot_username, unit_id)
            m = await q[0].click(
                utils.get_chat_id(message) if isinstance(message, Message) else message,
                reply_to=message.reply_to_msg_id
                if isinstance(message, Message)
                else None,
            )
        except ChatSendInlineForbiddenError:
            await answer("🚫 <b>You can't send inline units in this chat</b>")
        except Exception as e:
            logger.exception("Can't send list")

            if not self._db.get(main.__name__, "inlinelogs", True):
                msg = f"<b>🚫 List invoke failed! More info in logs</b>"
            else:
                exc = traceback.format_exc()
                # Remove `Traceback (most recent call last):`
                exc = "\n".join(exc.splitlines()[1:])
                msg = (
                    f"<b>🚫 List invoke failed!</b>\n\n"
                    f"<b>🧾 Logs:</b>\n<code>{exc}</code>"
                )

            del self._units[unit_id]
            await answer(msg)

            return False

        await self._units[unit_id]["future"].wait()
        del self._units[unit_id]["future"]

        self._units[unit_id]["chat"] = utils.get_chat_id(m)
        self._units[unit_id]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        return InlineMessage(self, unit_id, self._units[unit_id]["inline_message_id"])

    async def _list_back(
        self,
        call: CallbackQuery,
        btn_call_data: _List[str] = None,
        unit_id: str = None,
    ):
        if not self._units[unit_id]["current_index"]:
            await call.answer("No way back", show_alert=True)
            return

        self._units[unit_id]["current_index"] -= 1

        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=self._units[unit_id]["strings"][
                    self._units[unit_id]["current_index"]
                ],
                reply_markup=self._list_markup(unit_id),
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
        unit_id: str = None,
    ):
        self._units[unit_id]["current_index"] += 1
        # If we exceeded limit in list
        if self._units[unit_id]["current_index"] >= len(
            self._units[unit_id]["strings"]
        ):
            await call.answer("No entries left...", show_alert=True)
            self._units[unit_id]["current_index"] -= 1
            return

        try:
            await self.bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=self._units[unit_id]["strings"][
                    self._units[unit_id]["current_index"]
                ],
                reply_markup=self._list_markup(unit_id),
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

    def _list_markup(self, unit_id: str) -> InlineKeyboardMarkup:
        """Converts `btn_call_data` into a aiogram markup"""
        markup = InlineKeyboardMarkup()
        markup.add(
            *(
                [
                    InlineKeyboardButton(
                        f"⏪ [{self._units[unit_id]['current_index']} / {len(self._units[unit_id]['strings'])}]",
                        callback_data=self._units[unit_id]["btn_call_data"]["back"],
                    )
                ]
                if self._units[unit_id]["current_index"] > 0
                else []
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=self._units[unit_id]["btn_call_data"]["close"],
            ),
            *(
                [
                    InlineKeyboardButton(
                        f"⏩ [{self._units[unit_id]['current_index'] + 2} / {len(self._units[unit_id]['strings'])}]",
                        callback_data=self._units[unit_id]["btn_call_data"]["next"],
                    ),
                ]
                if self._units[unit_id]["current_index"]
                < len(self._units[unit_id]["strings"]) - 1
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
