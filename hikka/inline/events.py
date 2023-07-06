# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import inspect
import logging
import re
import typing
from asyncio import Event

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
from .types import BotInlineCall, InlineCall, InlineQuery, InlineUnit

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
                and mod.__class__.__name__ != "InlineStuff"
            ):
                continue

            try:
                await mod.aiogram_watcher(message)
            except Exception:
                logger.exception("Error on running aiogram watcher!")

    async def _inline_handler(self, inline_query: AiogramInlineQuery):
        """Inline query handler (forms' calls)"""
        if not (query := inline_query.query):
            await self._query_help(inline_query)
            return

        cmd = query.split()[0].lower()
        if (
            cmd in self._allmodules.inline_handlers
            and await self.check_inline_security(
                func=self._allmodules.inline_handlers[cmd],
                user=inline_query.from_user.id,
            )
        ):
            instance = InlineQuery(inline_query)

            try:
                if not (
                    result := await self._allmodules.inline_handlers[cmd](instance)
                ):
                    return
            except Exception:
                logger.exception("Error on running inline watcher!")
                return

            if isinstance(result, dict):
                result = [result]

            if not isinstance(result, list):
                logger.error(
                    "Got invalid type from inline handler. It must be `dict`, got `%s`",
                    type(result),
                )
                await instance.e500()
                return

            for res in result:
                mandatory = ["message", "photo", "gif", "video", "file"]
                if all(item not in res for item in mandatory):
                    logger.error(
                        (
                            "Got invalid type from inline handler. It must contain one"
                            " of `%s`"
                        ),
                        mandatory,
                    )
                    await instance.e500()
                    return

                if "file" in res and "mime_type" not in res:
                    logger.error(
                        "Got invalid type from inline handler. It contains field"
                        " `file`, so it must contain `mime_type` as well"
                    )

            try:
                await inline_query.answer(
                    [
                        (
                            InlineQueryResultArticle(
                                id=utils.rand(20),
                                title=self.sanitise_text(res["title"]),
                                description=self.sanitise_text(res.get("description")),
                                input_message_content=InputTextMessageContent(
                                    self.sanitise_text(res["message"]),
                                    "HTML",
                                    disable_web_page_preview=True,
                                ),
                                thumb_url=res.get("thumb"),
                                thumb_width=128,
                                thumb_height=128,
                                reply_markup=self.generate_markup(
                                    res.get("reply_markup")
                                ),
                            )
                            if "message" in res
                            else (
                                InlineQueryResultPhoto(
                                    id=utils.rand(20),
                                    title=self.sanitise_text(res.get("title")),
                                    description=self.sanitise_text(
                                        res.get("description")
                                    ),
                                    caption=self.sanitise_text(res.get("caption")),
                                    parse_mode="HTML",
                                    thumb_url=res.get("thumb", res["photo"]),
                                    photo_url=res["photo"],
                                    reply_markup=self.generate_markup(
                                        res.get("reply_markup")
                                    ),
                                )
                                if "photo" in res
                                else (
                                    InlineQueryResultGif(
                                        id=utils.rand(20),
                                        title=self.sanitise_text(res.get("title")),
                                        caption=self.sanitise_text(res.get("caption")),
                                        parse_mode="HTML",
                                        thumb_url=res.get("thumb", res["gif"]),
                                        gif_url=res["gif"],
                                        reply_markup=self.generate_markup(
                                            res.get("reply_markup")
                                        ),
                                    )
                                    if "gif" in res
                                    else (
                                        InlineQueryResultVideo(
                                            id=utils.rand(20),
                                            title=self.sanitise_text(res.get("title")),
                                            description=self.sanitise_text(
                                                res.get("description")
                                            ),
                                            caption=self.sanitise_text(
                                                res.get("caption")
                                            ),
                                            parse_mode="HTML",
                                            thumb_url=res.get("thumb", res["video"]),
                                            video_url=res["video"],
                                            mime_type="video/mp4",
                                            reply_markup=self.generate_markup(
                                                res.get("reply_markup")
                                            ),
                                        )
                                        if "video" in res
                                        else InlineQueryResultDocument(
                                            id=utils.rand(20),
                                            title=self.sanitise_text(res.get("title")),
                                            description=self.sanitise_text(
                                                res.get("description")
                                            ),
                                            caption=self.sanitise_text(
                                                res.get("caption")
                                            ),
                                            parse_mode="HTML",
                                            thumb_url=res.get("thumb", res["file"]),
                                            document_url=res["file"],
                                            mime_type=res["mime_type"],
                                            reply_markup=self.generate_markup(
                                                res.get("reply_markup")
                                            ),
                                        )
                                    )
                                )
                            )
                        )
                        for res in result
                    ],
                    cache_time=0,
                )
            except Exception:
                logger.exception(
                    "Exception when answering inline query with result from %s",
                    cmd,
                )
                return

        await self._form_inline_handler(inline_query)
        await self._gallery_inline_handler(inline_query)
        await self._list_inline_handler(inline_query)

    async def _callback_query_handler(
        self,
        call: CallbackQuery,
        reply_markup: typing.Optional[
            typing.List[typing.List[typing.Dict[str, typing.Any]]]
        ] = None,
    ):
        """Callback query handler (buttons' presses)"""
        if reply_markup is None:
            reply_markup = []

        if re.search(r"authorize_web_(.{8})", call.data):
            self._web_auth_tokens += [re.search(r"authorize_web_(.{8})", call.data)[1]]
            return

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
                        "Can't process update, because of corrupted button: %s",
                        button,
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
                    elif call.from_user.id not in (
                        self._client.dispatcher.security._owner
                        + unit.get("always_allow", [])
                        + button.get("always_allow", [])
                    ):
                        await call.answer(self.translator.getkey("inline.button403"))
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
                            (
                                "Error occurred while processing request. More info in"
                                " logs"
                            ),
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
                await call.answer(self.translator.getkey("inline.button403"))
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
        _help = []
        for name, fun in self._allmodules.inline_handlers.items():
            if not await self.check_inline_security(
                func=fun,
                user=inline_query.from_user.id,
            ):
                continue

            try:
                doc = inspect.getdoc(fun)
            except Exception:
                doc = "🦥 No docs"

            try:
                thumb = getattr(fun, "thumb_url", None) or fun.__self__.hikka_meta_pic
            except Exception:
                thumb = None

            thumb = thumb or "https://img.icons8.com/fluency/50/000000/info-squared.png"

            _help += [
                (
                    InlineQueryResultArticle(
                        id=utils.rand(20),
                        title=self.translator.getkey("inline.command").format(name),
                        description=doc,
                        input_message_content=InputTextMessageContent(
                            (
                                self.translator.getkey("inline.command_msg").format(
                                    utils.escape_html(name),
                                    utils.escape_html(doc),
                                )
                            ),
                            "HTML",
                            disable_web_page_preview=True,
                        ),
                        thumb_url=thumb,
                        thumb_width=128,
                        thumb_height=128,
                        reply_markup=self.generate_markup(
                            {
                                "text": self.translator.getkey("inline.run_command"),
                                "switch_inline_query_current_chat": f"{name} ",
                            }
                        ),
                    ),
                    (
                        f"🎹 <code>@{self.bot_username} {utils.escape_html(name)}</code>"
                        f" - {utils.escape_html(doc)}\n"
                    ),
                )
            ]

        if not _help:
            await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.rand(20),
                        title=self.translator.getkey("inline.show_inline_cmds"),
                        description=self.translator.getkey("inline.no_inline_cmds"),
                        input_message_content=InputTextMessageContent(
                            self.translator.getkey("inline.no_inline_cmds_msg"),
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
                    title=self.translator.getkey("inline.show_inline_cmds"),
                    description=(
                        self.translator.getkey("inline.inline_cmds").format(len(_help))
                    ),
                    input_message_content=InputTextMessageContent(
                        (
                            self.translator.getkey("inline.inline_cmds_msg").format(
                                "\n".join(map(lambda x: x[1], _help))
                            )
                        ),
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url=(
                        "https://img.icons8.com/fluency/50/000000/info-squared.png"
                    ),
                    thumb_width=128,
                    thumb_height=128,
                )
            ]
            + [i[0] for i in _help],
            cache_time=0,
        )
