from .types import InlineUnit, InlineCall
from aiogram.types import (
    Message as AiogramMessage,
    InlineQuery as AiogramInlineQuery,
    CallbackQuery,
    ChosenInlineResult,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
import logging
from typing import List
import re
from .. import utils
from .types import InlineQuery
import functools
import inspect

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
        for mod in self._allmodules.modules:
            if (
                not hasattr(mod, "inline_handlers")
                or not isinstance(mod.inline_handlers, dict)
                or not mod.inline_handlers
            ):
                continue

            instance = InlineQuery(inline_query)

            for query_text, query_func in mod.inline_handlers.items():
                if inline_query.query.split()[
                    0
                ].lower() == query_text.lower() and self.check_inline_security(
                    query_func, inline_query.from_user.id
                ):
                    try:
                        await query_func(instance)
                    except BaseException:
                        logger.exception("Error on running inline watcher!")

        await self._form_inline_handler(inline_query)
        await self._gallery_inline_handler(inline_query)

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
        for mod in self._allmodules.modules:
            if (
                not hasattr(mod, "callback_handlers")
                or not isinstance(mod.callback_handlers, dict)
                or not mod.callback_handlers
            ):
                continue

            for query_func in mod.callback_handlers.values():
                if self.check_inline_security(query_func, query.from_user.id):
                    try:
                        await query_func(query)
                    except Exception:
                        logger.exception("Error on running callback watcher!")
                        await query.answer(
                            "Error occured while processing request. More info in logs",
                            show_alert=True,
                        )
                        return

        for form_uid, form in self._forms.copy().items():
            for button in utils.array_sum(form.get("buttons", [])):
                if button.get("_callback_data", None) == query.data:
                    if (
                        form["force_me"]
                        and query.from_user.id != self._me
                        and query.from_user.id
                        not in self._client.dispatcher.security._owner
                        and query.from_user.id not in form["always_allow"]
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
                self._custom_map[query.data]["force_me"]
                and query.from_user.id != self._me
                and query.from_user.id not in self._client.dispatcher.security._owner
                and query.from_user.id
                not in self._custom_map[query.data]["always_allow"]
            ):
                await query.answer("You are not allowed to press this button!")
                return

            await self._custom_map[query.data]["handler"](query)
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
                    + form["always_allow"]
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
        for mod in self._allmodules.modules:
            if (
                not hasattr(mod, "inline_handlers")
                or not isinstance(mod.inline_handlers, dict)
                or not mod.inline_handlers
            ):
                continue

            _ihandlers = dict(mod.inline_handlers.items())
            for name, fun in _ihandlers.items():
                # If user doesn't have enough permissions
                # to run this inline command, do not show it
                # in help
                if not self.check_inline_security(fun, inline_query.from_user.id):
                    continue

                # Retrieve docs from func
                doc = utils.escape_html(
                    "\n".join(
                        [
                            line.strip()
                            for line in inspect.getdoc(fun).splitlines()
                            if not line.strip().startswith("@")
                        ]
                    )
                )

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
