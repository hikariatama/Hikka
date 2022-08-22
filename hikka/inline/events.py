#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import inspect
import logging
import re
from asyncio import Event
from typing import List

from aiogram.types import CallbackQuery, ChosenInlineResult
from aiogram.types import InlineQuery as AiogramInlineQuery
from aiogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultDocument,
    InlineQueryResultGif,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InputTextMessageContent,
)
from aiogram.types import Message as AiogramMessage

from .. import utils
from .types import InlineCall, InlineQuery, InlineUnit, BotInlineCall

logger = logging.getLogger(__name__)


class Events(InlineUnit):
    async def _message_handler(self, message: AiogramMessage):
        """Processes incoming messages"""
        if message.chat.type != "private" or message.text == "/start hikka init":
            return

        for mod in self._allmodules.modules:
            if (
                not hasattr(mod, "aiogram_watcher")
                or message.text == "/start"
                and mod.__class__.__name__ != "InlineStuffMod"
            ):
                continue

            try:
                await mod.aiogram_watcher(message)
            except BaseException:
                logger.exception("Error on running aiogram watcher!")

    async def _inline_handler(self, inline_query: AiogramInlineQuery):
        """Inline query handler (forms' calls)"""
        # Retrieve query from passed object
        query = inline_query.query

        # If we didn't get any query, return help
        if not query:
            await self._query_help(inline_query)
            return

        # First, dispatch all registered inline handlers
        cmd = inline_query.query.split()[0].lower()
        if (
            cmd in self._allmodules.inline_handlers
            and await self.check_inline_security(
                func=self._allmodules.inline_handlers[cmd],
                user=inline_query.from_user.id,
            )
        ):
            instance = InlineQuery(inline_query)

            try:
                result = await self._allmodules.inline_handlers[cmd](instance)
            except BaseException:
                logger.exception("Error on running inline watcher!")
                return

            if not result:
                return

            if isinstance(result, dict):
                result = [result]

            if not isinstance(result, list):
                logger.error(
                    "Got invalid type from inline handler. It must be `dict`, got"
                    f" `{type(result)}`"
                )
                await instance.e500()
                return

            for res in result:
                mandatory = {"message", "photo", "gif", "video", "file"}
                if all(item not in res for item in mandatory):
                    logger.error(
                        "Got invalid type from inline handler. It must contain one of"
                        f" `{mandatory}`"
                    )
                    await instance.e500()
                    return

                if "file" in res and "mime_type" not in res:
                    logger.error(
                        "Got invalid type from inline handler. It contains field"
                        " `file`, so it must contain `mime_type` as well"
                    )

            inline_result = []

            for res in result:
                if "message" in res:
                    inline_result += [
                        InlineQueryResultArticle(
                            id=utils.rand(20),
                            title=res["title"],
                            description=res.get("description"),
                            input_message_content=InputTextMessageContent(
                                res["message"],
                                "HTML",
                                disable_web_page_preview=True,
                            ),
                            thumb_url=res.get("thumb"),
                            thumb_width=128,
                            thumb_height=128,
                            reply_markup=self.generate_markup(res.get("reply_markup")),
                        )
                    ]
                elif "photo" in res:
                    inline_result += [
                        InlineQueryResultPhoto(
                            id=utils.rand(20),
                            title=res.get("title"),
                            description=res.get("description"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["photo"]),
                            photo_url=res["photo"],
                            reply_markup=self.generate_markup(res.get("reply_markup")),
                        )
                    ]
                elif "gif" in res:
                    inline_result += [
                        InlineQueryResultGif(
                            id=utils.rand(20),
                            title=res.get("title"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["gif"]),
                            gif_url=res["gif"],
                            reply_markup=self.generate_markup(res.get("reply_markup")),
                        )
                    ]
                elif "video" in res:
                    inline_result += [
                        InlineQueryResultVideo(
                            id=utils.rand(20),
                            title=res.get("title"),
                            description=res.get("description"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["video"]),
                            video_url=res["video"],
                            mime_type="video/mp4",
                            reply_markup=self.generate_markup(res.get("reply_markup")),
                        )
                    ]
                elif "file" in res:
                    inline_result += [
                        InlineQueryResultDocument(
                            id=utils.rand(20),
                            title=res.get("title"),
                            description=res.get("description"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["file"]),
                            document_url=res["file"],
                            mime_type=res["mime_type"],
                            reply_markup=self.generate_markup(res.get("reply_markup")),
                        )
                    ]

            try:
                await inline_query.answer(inline_result, cache_time=0)
            except Exception:
                logger.exception(
                    f"Exception when answering inline query with result from {cmd}"
                )
                return

        await self._form_inline_handler(inline_query)
        await self._gallery_inline_handler(inline_query)
        await self._list_inline_handler(inline_query)

    async def _callback_query_handler(
        self,
        call: CallbackQuery,
        reply_markup: List[List[dict]] = None,
    ):
        """Callback query handler (buttons' presses)"""
        if reply_markup is None:
            reply_markup = []

        if re.search(r"authorize_web_(.{8})", call.data):
            self._web_auth_tokens += [re.search(r"authorize_web_(.{8})", call.data)[1]]
            return

        # First, dispatch all registered callback handlers
        for func in self._allmodules.callback_handlers.values():
            if await self.check_inline_security(func=func, user=call.from_user.id):
                try:
                    await func(
                        (
                            BotInlineCall
                            if getattr(getattr(call, "message", None), "chat", None)
                            else InlineCall
                        )(call, self, None)
                    )
                except Exception:
                    logger.exception("Error on running callback watcher!")
                    await call.answer(
                        "Error occured while processing request. More info in logs",
                        show_alert=True,
                    )
                    continue

        for unit_id, unit in self._units.copy().items():
            for button in utils.array_sum(unit.get("buttons", [])):
                if not isinstance(button, dict):
                    logger.warning(
                        f"Can't process update, because of corrupted button: {button}"
                    )
                    continue

                if button.get("_callback_data") == call.data:
                    if (
                        button.get("disable_security", False)
                        or unit.get("disable_security", False)
                        or (
                            unit.get("force_me", False)
                            and call.from_user.id == self._me
                        )
                        or not unit.get("force_me", False)
                        and (
                            await self.check_inline_security(
                                func=unit.get(
                                    "perms_map",
                                    lambda: self._client.dispatcher.security._default,
                                )(),  # we call it so we can get reloaded rights in runtime
                                user=call.from_user.id,
                            )
                            if "message" in unit
                            else False
                        )
                    ):
                        pass
                    elif (
                        call.from_user.id
                        not in self._client.dispatcher.security._owner
                        + unit.get("always_allow", [])
                        + button.get("always_allow", [])
                    ):
                        await call.answer("You are not allowed to press this button!")
                        return

                    try:
                        result = await button["callback"](
                            (
                                BotInlineCall
                                if getattr(getattr(call, "message", None), "chat", None)
                                else InlineCall
                            )(call, self, unit_id),
                            *button.get("args", []),
                            **button.get("kwargs", {}),
                        )
                    except Exception:
                        logger.exception("Error on running callback watcher!")
                        await call.answer(
                            "Error occurred while "
                            "processing request. "
                            "More info in logs",
                            show_alert=True,
                        )
                        return

                    return result

        if call.data in self._custom_map:
            if (
                self._custom_map[call.data].get("disable_security", False)
                or (
                    self._custom_map[call.data].get("force_me", False)
                    and call.from_user.id == self._me
                )
                or not self._custom_map[call.data].get("force_me", False)
                and (
                    await self.check_inline_security(
                        func=self._custom_map[call.data].get(
                            "perms_map",
                            lambda: self._client.dispatcher.security._default,
                        )(),
                        user=call.from_user.id,
                    )
                    if "message" in self._custom_map[call.data]
                    else False
                )
            ):
                pass
            elif (
                call.from_user.id not in self._client.dispatcher.security._owner
                and call.from_user.id
                not in self._custom_map[call.data].get("always_allow", [])
            ):
                await call.answer("You are not allowed to press this button!")
                return

            await self._custom_map[call.data]["handler"](
                (
                    BotInlineCall
                    if getattr(getattr(call, "message", None), "chat", None)
                    else InlineCall
                )(call, self, None),
                *self._custom_map[call.data].get("args", []),
                **self._custom_map[call.data].get("kwargs", {}),
            )
            return

    async def _chosen_inline_handler(
        self,
        chosen_inline_query: ChosenInlineResult,
    ):
        query = chosen_inline_query.query

        if not query:
            return

        for unit_id, unit in self._units.items():
            if (
                unit_id == query
                and "future" in unit
                and isinstance(unit["future"], Event)
            ):
                unit["inline_message_id"] = chosen_inline_query.inline_message_id
                unit["future"].set()
                return

        for unit_id, unit in self._units.copy().items():
            for button in utils.array_sum(unit.get("buttons", [])):
                if (
                    "_switch_query" in button
                    and "input" in button
                    and button["_switch_query"] == query.split()[0]
                    and chosen_inline_query.from_user.id
                    in [self._me]
                    + self._client.dispatcher.security._owner
                    + unit.get("always_allow", [])
                ):

                    query = query.split(maxsplit=1)[1] if len(query.split()) > 1 else ""

                    try:
                        return await button["handler"](
                            InlineCall(chosen_inline_query, self, unit_id),
                            query,
                            *button.get("args", []),
                            **button.get("kwargs", {}),
                        )
                    except Exception:
                        logger.exception(
                            "Exception while running chosen query watcher!"
                        )
                        return

    async def _query_help(self, inline_query: InlineQuery):
        _help = ""
        for name, fun in self._allmodules.inline_handlers.items():
            # If user doesn't have enough permissions
            # to run this inline command, do not show it
            # in help
            if not await self.check_inline_security(
                func=fun,
                user=inline_query.from_user.id,
            ):
                continue

            # Retrieve docs from func
            try:
                doc = utils.escape_html(inspect.getdoc(fun))
            except Exception:
                doc = "🦥 No docs"

            _help += f"🎹 <code>@{self.bot_username} {name}</code> - {doc}\n"

        if not _help:
            await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.rand(20),
                        title="Show available inline commands",
                        description="You have no available commands",
                        input_message_content=InputTextMessageContent(
                            "<b>😔 There are no available inline commands or you lack"
                            " access to them</b>",
                            "HTML",
                            disable_web_page_preview=True,
                        ),
                        thumb_url=(
                            "https://img.icons8.com/fluency/50/000000/info-squared.png"
                        ),
                        thumb_width=128,
                        thumb_height=128,
                    )
                ],
                cache_time=0,
            )
            return

        await inline_query.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="Show available inline commands",
                    description=(
                        f"You have {len(_help.splitlines())} available command(-s)"
                    ),
                    input_message_content=InputTextMessageContent(
                        f"<b>ℹ️ Available inline commands:</b>\n\n{_help}",
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url=(
                        "https://img.icons8.com/fluency/50/000000/info-squared.png"
                    ),
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )
