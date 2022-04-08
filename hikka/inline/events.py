from .types import InlineUnit, InlineCall
from aiogram.types import (
    Message as AiogramMessage,
    InlineQuery as AiogramInlineQuery,
    CallbackQuery,
    ChosenInlineResult,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQueryResultPhoto,
    InlineQueryResultGif,
    InlineQueryResultVideo,
    InlineQueryResultDocument,
)
import logging
from typing import List
import re
from .. import utils
from .types import InlineQuery
import functools
import inspect
from telethon.tl.types import Message

logger = logging.getLogger(__name__)


class Events(InlineUnit):
    async def _message_handler(self, message: AiogramMessage) -> None:
        """Processes incoming messages"""
        if message.chat.type != "private":
            return

        for mod in self._allmodules.modules:
            if not hasattr(mod, "aiogram_watcher"):
                continue

            setattr(
                message,
                "answer",
                functools.partial(
                    self._bot_message_answer,
                    message=message,
                ),
            )

            try:
                await mod.aiogram_watcher(message)
            except BaseException:
                logger.exception("Error on running aiogram watcher!")

    async def _inline_handler(self, inline_query: AiogramInlineQuery) -> None:
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
                self._allmodules.inline_handlers[cmd],
                inline_query.from_user.id,
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

            if not isinstance(result, list) or not all(
                (
                    "message" in res
                    or "photo" in res
                    or "gif" in res
                    or "video" in res
                    or "file" in res
                    and "mime_type" in res
                )
                and "title" in res
                for res in result
            ):
                logger.error("Got invalid type from inline handler. Refer to docs for more info")  # fmt: skip
                return

            inline_result = []

            for res in result:
                if "message" in res:
                    inline_result += [
                        InlineQueryResultArticle(
                            id=utils.rand(20),
                            title=res["title"],
                            description=res.get("description", None),
                            input_message_content=InputTextMessageContent(
                                res["message"],
                                "HTML",
                                disable_web_page_preview=True,
                            ),
                            thumb_url=res.get("thumb", None),
                            thumb_width=128,
                            thumb_height=128,
                            reply_markup=self._generate_markup(
                                res.get("reply_markup", None)
                            ),
                        )
                    ]
                elif "photo" in res:
                    inline_result += [
                        InlineQueryResultPhoto(
                            id=utils.rand(20),
                            title=res.get("title", None),
                            description=res.get("description", None),
                            caption=res.get("caption", None),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["photo"]),
                            photo_url=res["photo"],
                            reply_markup=self._generate_markup(
                                res.get("reply_markup", None)
                            ),
                        )
                    ]
                elif "gif" in res:
                    inline_result += [
                        InlineQueryResultGif(
                            id=utils.rand(20),
                            title=res.get("title", None),
                            caption=res.get("caption", None),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["gif"]),
                            gif_url=res["gif"],
                            reply_markup=self._generate_markup(
                                res.get("reply_markup", None)
                            ),
                        )
                    ]
                elif "video" in res:
                    inline_result += [
                        InlineQueryResultVideo(
                            id=utils.rand(20),
                            title=res.get("title", None),
                            description=res.get("description", None),
                            caption=res.get("caption", None),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["video"]),
                            video_url=res["video"],
                            mime_type="video/mp4",
                            reply_markup=self._generate_markup(
                                res.get("reply_markup", None)
                            ),
                        )
                    ]
                elif "file" in res:
                    inline_result += [
                        InlineQueryResultDocument(
                            id=utils.rand(20),
                            title=res.get("title", None),
                            description=res.get("description", None),
                            caption=res.get("caption", None),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["file"]),
                            document_url=res["file"],
                            mime_type=res["mime_type"],
                            reply_markup=self._generate_markup(
                                res.get("reply_markup", None)
                            ),
                        )
                    ]

            try:
                await inline_query.answer(inline_result)
            except Exception:
                logger.exception(f"Exception when answering inline query with result from {cmd}")  # fmt: skip
                return

        await self._form_inline_handler(inline_query)
        await self._gallery_inline_handler(inline_query)
        await self._list_inline_handler(inline_query)

    async def _check_inline_sec_by_mask(
        self,
        *,
        mask: int,
        user: int,
        message: Message,
    ) -> bool:
        """Checks if user is able to execute command with provided security mask"""
        return await self._client.dispatcher.security._check(
            message=message,
            func=mask,
            user=user,
        )

    async def _callback_query_handler(
        self,
        query: CallbackQuery,
        reply_markup: List[List[dict]] = None,
    ) -> None:
        """Callback query handler (buttons' presses)"""
        if reply_markup is None:
            reply_markup = []

        if re.search(r"authorize_web_(.{8})", query.data):
            self._web_auth_tokens += [
                re.search(r"authorize_web_(.{8})", query.data).group(1)
            ]
            return

        # First, dispatch all registered callback handlers
        for func in self._allmodules.callback_handlers.values():
            if await self.check_inline_security(func, query.from_user.id):
                try:
                    await func(query)
                except Exception:
                    logger.exception("Error on running callback watcher!")
                    await query.answer(
                        "Error occured while processing request. More info in logs",
                        show_alert=True,
                    )
                    continue

        for form_uid, form in self._forms.copy().items():
            for button in utils.array_sum(form.get("buttons", [])):
                if button.get("_callback_data", None) == query.data:
                    if (
                        form.get("disable_security", False)
                        or (
                            form.get("force_me", False)
                            and query.from_user.id == self._me
                        )
                        or not form.get("force_me", False)
                        and (
                            await self._check_inline_sec_by_mask(
                                mask=form.get(
                                    "perms_map",
                                    lambda: self._client.dispatcher.security._default,
                                )(),
                                user=query.from_user.id,
                                message=form["message"],
                            )
                            if "message" in form
                            else False
                        )
                    ):
                        pass
                    elif (
                        query.from_user.id
                        not in self._client.dispatcher.security._owner
                        and query.from_user.id not in form.get("always_allow", [])
                    ):
                        await query.answer("You are not allowed to press this button!")
                        return

                    query.delete = functools.partial(
                        self._callback_query_delete,
                        form=form,
                        form_uid=form_uid,
                    )

                    query.unload = functools.partial(
                        self._callback_query_unload,
                        form_uid=form_uid,
                    )

                    query.edit = functools.partial(
                        self._callback_query_edit,
                        query=query,
                        form=form,
                        form_uid=form_uid,
                    )

                    query.form = {"id": form_uid, **form}

                    try:
                        return await button["callback"](
                            query,
                            *button.get("args", []),
                            **button.get("kwargs", {}),
                        )
                    except Exception:
                        logger.exception("Error on running callback watcher!")
                        await query.answer(
                            "Error occurred while "
                            "processing request. "
                            "More info in logs",
                            show_alert=True,
                        )
                        return

                    del self._forms[form_uid]

        if query.data in self._custom_map:
            if (
                self._custom_map[query.data].get("disable_security", False)
                or (
                    self._custom_map[query.data].get("force_me", False)
                    and query.from_user.id == self._me
                )
                or not self._custom_map[query.data].get("force_me", False)
                and (
                    await self._check_inline_sec_by_mask(
                        mask=self._custom_map[query.data].get(
                            "perms_map",
                            lambda: self._client.dispatcher.security._default,
                        )(),
                        user=query.from_user.id,
                        message=self._custom_map[query.data]["message"],
                    )
                    if "message" in self._custom_map[query.data]
                    else False
                )
            ):
                pass
            elif (
                query.from_user.id not in self._client.dispatcher.security._owner
                and query.from_user.id
                not in self._custom_map[query.data].get("always_allow", [])
            ):
                await query.answer("You are not allowed to press this button!")
                return

            await self._custom_map[query.data]["handler"](
                query,
                *self._custom_map[query.data].get("args", []),
                **self._custom_map[query.data].get("kwargs", {}),
            )
            return

    async def _chosen_inline_handler(
        self,
        chosen_inline_query: ChosenInlineResult,
    ) -> None:
        query = chosen_inline_query.query

        for form_uid, form in self._forms.copy().items():
            for button in utils.array_sum(form.get("buttons", [])):
                if (
                    "_switch_query" in button
                    and "input" in button
                    and button["_switch_query"] == query.split()[0]
                    and chosen_inline_query.from_user.id
                    in [self._me]
                    + self._client.dispatcher.security._owner
                    + form.get("always_allow", [])
                ):

                    query = query.split(maxsplit=1)[1] if len(query.split()) > 1 else ""

                    call = InlineCall()

                    call.delete = functools.partial(
                        self._callback_query_delete,
                        form=form,
                        form_uid=form_uid,
                    )
                    call.unload = functools.partial(
                        self._callback_query_unload,
                        form_uid=form_uid,
                    )
                    call.edit = functools.partial(
                        self._callback_query_edit,
                        query=chosen_inline_query,
                        form=form,
                        form_uid=form_uid,
                    )

                    try:
                        return await button["handler"](
                            call,
                            query,
                            *button.get("args", []),
                            **button.get("kwargs", {}),
                        )
                    except Exception:
                        logger.exception(
                            "Exception while running chosen query watcher!"
                        )
                        return

    async def _query_help(self, inline_query: InlineQuery) -> None:
        _help = ""
        for name, fun in self._allmodules.inline_handlers.items():
            # If user doesn't have enough permissions
            # to run this inline command, do not show it
            # in help
            if not await self.check_inline_security(fun, inline_query.from_user.id):
                continue

            # Retrieve docs from func
            try:
                doc = utils.escape_html(
                    "\n".join(
                        [
                            line.strip()
                            for line in inspect.getdoc(fun).splitlines()
                            if not line.strip().startswith("@")
                        ]
                    )
                )
            except AttributeError:
                doc = "🦥 No docs"

            _help += f"🎹 <code>@{self.bot_username} {name}</code> - {doc}\n"

        await inline_query.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="Show available inline commands",
                    description=f"You have {len(_help.splitlines())} available command(-s)",
                    input_message_content=InputTextMessageContent(
                        f"<b>ℹ️ Available inline commands:</b>\n\n{_help}",
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url="https://img.icons8.com/fluency/50/000000/info-squared.png",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )
