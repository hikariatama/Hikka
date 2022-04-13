from .types import InlineUnit
from .. import utils

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import logging
from typing import Union
from types import FunctionType
from .. import security
from .._types import Module
import inspect
from telethon.tl.types import Message

import re

URL_REGEX = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

logger = logging.getLogger(__name__)


class Utils(InlineUnit):
    def _generate_markup(
        self,
        form_uid: Union[str, list],
        /,
    ) -> Union[None, InlineKeyboardMarkup]:
        """Generate markup for form or list of `dict`s"""
        if not form_uid:
            return None

        markup = InlineKeyboardMarkup()

        map_ = (
            self._forms[form_uid]["buttons"] if isinstance(form_uid, str) else form_uid
        )

        map_ = self._normalize_markup(map_)

        for row in map_:
            for button in row:
                if not isinstance(button, dict):
                    logger.error(f"Button {button} is not a `dict`, but `{type(button)}` in {map_}")  # fmt: skip
                    return None

                if "callback" in button and "_callback_data" not in button:
                    button["_callback_data"] = utils.rand(30)

                if "input" in button and "_switch_query" not in button:
                    button["_switch_query"] = utils.rand(10)

        for row in map_:
            line = []
            for button in row:
                try:
                    if "url" in button:
                        if not re.match(URL_REGEX, button["url"]):
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
                    elif "input" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                switch_inline_query_current_chat=button["_switch_query"] + " ",  # fmt: skip
                            )
                        ]
                    elif "data" in button:
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                callback_data=button["data"],
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

    async def check_inline_security(self, *, func: FunctionType, user: int, message: Union[Message, None] = None) -> bool:
        """Checks if user with id `user` is allowed to run function `func`"""
        return await self._client.dispatcher.security.check(
            func=func,
            user=user,
            message=message,
        )

    def _find_caller_sec_map(self) -> Union[FunctionType, None]:
        try:
            return next(
                next(
                    lambda: self._db.get(security.__name__, "masks", {}).get(
                        f"{getattr(cls_, stack_entry.function).__module__}.{stack_entry.function}",
                        getattr(
                            getattr(cls_, stack_entry.function),
                            "security",
                            self._client.dispatcher.security._default,
                        ),
                    )
                    for name, cls_ in stack_entry.frame.f_globals.items()
                    if name.endswith("Mod") and issubclass(cls_, Module)
                )
                for stack_entry in inspect.stack()
                if hasattr(stack_entry, "function")
                and (
                    stack_entry.function.endswith("cmd")
                    or stack_entry.function.endswith("_inline_handler")
                )
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
