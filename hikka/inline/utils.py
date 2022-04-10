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
                        line += [
                            InlineKeyboardButton(
                                button["text"],
                                url=button.get("url", None),
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

    async def check_inline_security(self, func: FunctionType, user: int) -> bool:
        """Checks if user with id `user` is allowed to run function `func`"""
        allow = (user in [self._me] + self._client.dispatcher.security._owner)  # fmt: skip

        if not hasattr(func, "__doc__") or not func.__doc__ or allow:
            return allow

        doc = func.__doc__

        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("@allow:"):
                allow_line = line.split(":")[1].strip()

                # First we check for possible group limits
                # like `sudo`, `support`, `all`. Then check
                # for the occurrence of user in overall string
                # This allows dev to use any delimiter he wants
                if (
                    "all" in allow_line
                    or "sudo" in allow_line
                    and user in self._client.dispatcher.security._sudo
                    or "support" in allow_line
                    and user in self._client.dispatcher.security._support
                    or str(user) in allow_line
                ):
                    allow = True

        # But don't hurry to return value, we need to check,
        # if there are any limits
        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("@restrict:"):
                restrict = line.split(":")[1].strip()

                if (
                    "all" in restrict
                    or "sudo" in restrict
                    and user in self._client.dispatcher.security._sudo
                    or "support" in restrict
                    and user in self._client.dispatcher.security._support
                    or str(user) in restrict
                ):
                    allow = True

        if allow:
            return True

        config = self._db.get(security.__name__, "masks", {}).get(
            f"{func.__module__}.{func.__name__}",
            self._client.dispatcher.security._default,
        )

        owner = config & security.OWNER
        sudo = config & security.SUDO
        support = config & security.SUPPORT
        everyone = config & security.EVERYONE

        return (
            owner
            and user in self._client.dispatcher.security._owner
            or sudo
            and user in self._client.dispatcher.security._sudo
            or support
            and user in self._client.dispatcher.security._support
            or everyone
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
