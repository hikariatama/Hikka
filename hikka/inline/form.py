import logging
import time
from asyncio import Event
from types import FunctionType
from typing import List, Optional, Union

from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)
from telethon.tl.types import Message

from .. import utils
from .types import InlineMessage, InlineUnit

logger = logging.getLogger(__name__)


class Form(InlineUnit):
    async def form(
        self,
        text: str,
        message: Union[Message, int],
        reply_markup: Union[List[List[dict]], List[dict], dict] = None,
        *,
        force_me: Optional[bool] = False,
        always_allow: Optional[Union[List[list], None]] = None,
        manual_security: Optional[bool] = False,
        disable_security: Optional[bool] = False,
        ttl: Optional[Union[int, bool]] = False,
        on_unload: Optional[Union[FunctionType, None]] = None,
        photo: Optional[Union[str, None]] = None,
        silent: Optional[bool] = False,
    ) -> Union[str, bool]:
        """
        Creates inline form with callback
        Args:
            text
                Content of inline form. HTML markdown supported
            message
                Where to send inline. Can be either `Message` or `int`
            reply_markup
                List of buttons to insert in markup. List of dicts with
                keys: text, callback
            force_me
                Either this form buttons must be pressed only by owner scope or no
            always_allow
                Users, that are allowed to press buttons in addition to previous rules
            ttl
                Time, when the form is going to be unloaded. Unload means, that the form
                buttons with inline queries and callback queries will become unusable, but
                buttons with type url will still work as usual. Pay attention, that ttl can't
                be bigger, than default one (1 day) and must be either `int` or `False`
            on_unload
                Callback, called when form is unloaded and/or closed. You can clean up trash
                or perform another needed action
            manual_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to avoid this, pass `manual_security=True`
            disable_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to disable all security checks on this form in particular, pass `disable_security=True`
            photo
                Attach the photo to the form. URL must be supplied
            silent
                Whether the form must be sent silently (w/o "Loading inline form..." message)
        """

        if reply_markup is None:
            reply_markup = []

        if always_allow is None:
            always_allow = []

        if not isinstance(text, str):
            logger.error("Invalid type for `text`")
            return False

        if not isinstance(silent, bool):
            logger.error("Invalid type for `silent`")
            return False

        if not isinstance(manual_security, bool):
            logger.error("Invalid type for `manual_security`")
            return False

        if not isinstance(disable_security, bool):
            logger.error("Invalid type for `disable_security`")
            return False

        if not isinstance(message, (Message, int)):
            logger.error("Invalid type for `message`")
            return False

        if not isinstance(reply_markup, (list, dict)):
            logger.error("Invalid type for `reply_markup`")
            return False

        if photo and not isinstance(photo, str):
            logger.error("Invalid type for `photo`")
            return False

        reply_markup = self._normalize_markup(reply_markup)

        if not all(
            all(isinstance(button, dict) for button in row) for row in reply_markup
        ):
            logger.error("Invalid type for one of the buttons. It must be `dict`")
            return False

        if not all(
            all(
                "url" in button
                or "callback" in button
                or "input" in button
                or "data" in button
                for button in row
            )
            for row in reply_markup
        ):
            logger.error(
                "Invalid button specified. "
                "Button must contain one of the following fields:\n"
                "  - `url`\n"
                "  - `callback`\n"
                "  - `input`\n"
                "  - `data`"
            )
            return False

        if not isinstance(force_me, bool):
            logger.error("Invalid type for `force_me`")
            return False

        if not isinstance(always_allow, list):
            logger.error("Invalid type for `always_allow`")
            return False

        if not isinstance(ttl, int) and ttl:
            logger.error("Invalid type for `ttl`")
            return False

        if isinstance(ttl, int) and (ttl > self._markup_ttl or ttl < 10):
            ttl = None
            logger.debug("Defaulted ttl, because it breaks out of limits")

        if isinstance(message, Message) and not silent:
            try:
                status_message = await (
                    message.edit if message.out else message.respond
                )("🌘 <b>Loading inline form...</b>")
            except Exception:
                status_message = None
        else:
            status_message = None

        form_uid = utils.rand(30)

        perms_map = None if manual_security else self._find_caller_sec_map()

        self._forms[form_uid] = {
            "text": text,
            "buttons": reply_markup,
            "chat": None,
            "message_id": None,
            "uid": form_uid,
            "on_unload": on_unload,
            "future": Event(),
            **({"photo": photo} if photo else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"ttl": round(time.time()) + ttl} if ttl else {}),
            **({"always_allow": always_allow} if always_allow else {}),
        }

        try:
            q = await self._client.inline_query(self.bot_username, form_uid)
            m = await q[0].click(
                utils.get_chat_id(message) if isinstance(message, Message) else message,
                reply_to=message.reply_to_msg_id
                if isinstance(message, Message)
                else None,
            )
        except Exception:
            msg = (
                "🚫 <b>A problem occurred with inline bot "
                "while processing query. Check logs for "
                "further info.</b>"
            )

            del self._forms[form_uid]
            if isinstance(message, Message):
                await (message.edit if message.out else message.respond)(msg)
            else:
                await self._client.send_message(message, msg)

            return False

        await self._forms[form_uid]["future"].wait()
        del self._forms[form_uid]["future"]

        self._forms[form_uid]["chat"] = utils.get_chat_id(m)
        self._forms[form_uid]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        inline_message_id = self._forms[form_uid]["inline_message_id"]

        if not any(
            any("callback" in button or "input" in button for button in row)
            for row in reply_markup
        ):
            del self._forms[form_uid]
            logger.debug(
                f"Unloading form {form_uid}, because it "
                "doesn't contain any button callbacks"
            )

        return InlineMessage(self, form_uid, inline_message_id)

    async def _form_inline_handler(self, inline_query: InlineQuery):
        for form in self._forms.copy().values():
            for button in utils.array_sum(form.get("buttons", [])):
                if (
                    "_switch_query" in button
                    and "input" in button
                    and button["_switch_query"] == inline_query.query.split()[0]
                    and inline_query.from_user.id
                    in [self._me]
                    + self._client.dispatcher.security._owner
                    + form.get("always_allow", [])
                ):
                    await inline_query.answer(
                        [
                            InlineQueryResultArticle(
                                id=utils.rand(20),
                                title=button["input"],
                                description="⚠️ Please, do not remove identifier!",
                                input_message_content=InputTextMessageContent(
                                    "🔄 <b>Transferring value to userbot...</b>\n"
                                    "<i>This message is gonna be deleted...</i>",
                                    "HTML",
                                    disable_web_page_preview=True,
                                ),
                            )
                        ],
                        cache_time=60,
                    )
                    return

        if inline_query.query not in self._forms:
            return

        # Otherwise, answer it with templated form
        form = self._forms[inline_query.query]
        if not form.get("photo", False):
            await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.rand(20),
                        title="Hikka",
                        input_message_content=InputTextMessageContent(
                            form["text"],
                            "HTML",
                            disable_web_page_preview=True,
                        ),
                        reply_markup=self.generate_markup(inline_query.query),
                    )
                ],
                cache_time=0,
            )
        else:
            await inline_query.answer(
                [
                    InlineQueryResultPhoto(
                        id=utils.rand(20),
                        title="Processing inline form",
                        photo_url=form["photo"],
                        thumb_url="https://img.icons8.com/fluency/344/loading.png",
                        caption=form["text"],
                        description="Processing inline form",
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                        parse_mode="HTML",
                    )
                ],
                cache_time=0,
            )
