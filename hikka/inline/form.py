#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import copy
import logging
import os
import time
from asyncio import Event
from typing import List, Optional, Union
import random
from urllib.parse import urlparse
import grapheme
import traceback

from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
    InlineQueryResultDocument,
    InlineQueryResultGif,
    InlineQueryResultVideo,
    InlineQueryResultLocation,
    InlineQueryResultAudio,
)
from telethon.tl.types import Message
from telethon.errors.rpcerrorlist import ChatSendInlineForbiddenError

from .. import utils, main
from .types import InlineMessage, InlineUnit

logger = logging.getLogger(__name__)

VERIFICATION_EMOJIES = list(
    grapheme.graphemes(
        "👨‍🏫👩‍🏫👨‍🎤🧑‍🎤👩‍🎤👨‍🎓👩‍🎓👩‍🍳👩‍🌾👩‍⚕️🕵️‍♀️💂‍♀️👷‍♂️👮‍♂️👴🧑‍🦳👩‍🦳👱‍♀️👩‍🦰👨‍🦱👩‍⚖️🧙‍♂️🧝‍♀️🧛‍♀️"
        "🎅🧚‍♂️🙆‍♀️🙍‍♂️👩‍👦🧶🪢🪡🧵🩲👖👕👚🦺👗👙🩱👘🥻🩴🥿🧦🥾👟👞"
        "👢👡👠🪖👑💍👝👛👜💼🌂🥽🕶👓🧳🎒🐶🐱🐭🐹🐰🦊🐻🐷🐮"
        "🦁🐯🐨🐻‍❄️🐼🐽🐸🐵🙈🙉🙊🐒🦆🐥🐣🐤🐦🐧🐔🦅🦉🦇🐺🐗🐴"
        "🦄🐜🐞🐌🦋🐛🪱🐝🪰🪲🪳🦟🦗🕷🕸🐙🦕🦖🦎🐍🐢🦂🦑🦐🦞"
        "🦀🐡🐠🐟🐅🐊🦭🦈🐋🐳🐬🐆🦓🦍🦧🦣🐘🦛🐃🦬🦘🦒🐫🐪🦏"
        "🐂🐄🐎🐖🐏🐑🦙🐈🐕‍🦺🦮🐩🐕🦌🐐🐈‍⬛🪶🐓🦃🦤🦚🦜🦡🦨🦝🐇"
        "🕊🦩🦢🦫🦦🦥🐁🐀🐿🦔🌳🌲🌵🐲🐉🐾🎋🍂🍁🍄🐚🌾🪨💐🌷"
        "🥀🌺🌸🌻🌞🌜🌘🌗🌎🪐💫⭐️✨⚡️☄️💥☀️🌪🔥🌈🌤⛅️❄️⛄️🌊"
        "☂️🍏🍎🍐🍊🍋🍌🍉🥭🍑🍒🍈🫐🍓🍇🍍🥥🥝🍅🥑🥦🧔‍♂️"
    )
)


class Form(InlineUnit):
    async def form(
        self,
        text: str,
        message: Union[Message, int],
        reply_markup: Union[List[List[dict]], List[dict], dict] = None,
        *,
        force_me: Optional[bool] = False,
        always_allow: Optional[List[list]] = None,
        manual_security: Optional[bool] = False,
        disable_security: Optional[bool] = False,
        ttl: Optional[int] = None,
        on_unload: Optional[callable] = None,
        photo: Optional[str] = None,
        gif: Optional[str] = None,
        file: Optional[str] = None,
        mime_type: Optional[str] = None,
        video: Optional[str] = None,
        location: Optional[str] = None,
        audio: Optional[Union[dict, str]] = None,
        silent: Optional[bool] = False,
    ) -> Union[InlineMessage, bool]:
        """
        Send inline form to chat
        :param text: Content of inline form. HTML markdown supported
        :param message: Where to send inline. Can be either `Message` or `int`
        :param reply_markup: List of buttons to insert in markup. List of dicts with keys: text, callback
        :param force_me: Either this form buttons must be pressed only by owner scope or no
        :param always_allow: Users, that are allowed to press buttons in addition to previous rules
        :param ttl: Time, when the form is going to be unloaded. Unload means, that the form
                    buttons with inline queries and callback queries will become unusable, but
                    buttons with type url will still work as usual. Pay attention, that ttl can't
                    be bigger, than default one (1 day) and must be either `int` or `False`
        :param on_unload: Callback, called when form is unloaded and/or closed. You can clean up trash
                          or perform another needed action
        :param manual_security: By default, Hikka will try to inherit inline buttons security from the caller (command)
                                If you want to avoid this, pass `manual_security=True`
        :param disable_security: By default, Hikka will try to inherit inline buttons security from the caller (command)
                                 If you want to disable all security checks on this form in particular, pass `disable_security=True`
        :param photo: Attach a photo to the form. URL must be supplied
        :param gif: Attach a gif to the form. URL must be supplied
        :param file: Attach a file to the form. URL must be supplied
        :param mime_type: Only needed, if `file` field is not empty. Must be either 'application/pdf' or 'application/zip'
        :param video: Attach a video to the form. URL must be supplied
        :param location: Attach a map point to the form. List/tuple must be supplied (latitude, longitude)
                         Example: (55.749931, 48.742371)
                         ⚠️ If you pass this parameter, you'll need to pass empty string to `text` ⚠️
        :param audio: Attach a audio to the form. Dict or URL must be supplied
        :param silent: Whether the form must be sent silently (w/o "Loading inline form..." message)
        :return: If form is sent, returns :obj:`InlineMessage`, otherwise returns `False`
        """
        with contextlib.suppress(AttributeError):
            _hikka_client_id_logging_tag = copy.copy(self._client.tg_id)

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

        if photo and (not isinstance(photo, str) or not utils.check_url(photo)):
            logger.error("Invalid type for `photo`")
            return False
        
        try:
            path = urlparse(photo).path
            ext = os.path.splitext(path)[1]
        except Exception:
            ext = None

        if photo is not None and ext in {".gif", ".mp4"}:
            gif = copy.copy(photo)
            photo = None

        if gif and (not isinstance(gif, str) or not utils.check_url(gif)):
            logger.error("Invalid type for `gif`")
            return False

        if file and (not isinstance(file, str) or not utils.check_url(file)):
            logger.error("Invalid type for `file`")
            return False

        if file and not mime_type:
            logger.error(
                "You must pass `mime_type` along with `file` field\n"
                "It may be either 'application/zip' or 'application/pdf'"
            )
            return False

        if video and (not isinstance(video, str) or not utils.check_url(video)):
            logger.error("Invalid type for `video`")
            return False

        if isinstance(audio, str):
            audio = {"url": audio}

        if audio and (
            not isinstance(audio, dict)
            or "url" not in audio
            or not utils.check_url(audio["url"])
        ):
            logger.error("Invalid type for `audio`")
            return False

        if location and (
            not isinstance(location, (list, tuple))
            or len(location) != 2
            or not all(isinstance(item, float) for item in location)
        ):
            logger.error("Invalid type for `location`")
            return False

        if [
            photo is not None,
            gif is not None,
            file is not None,
            video is not None,
            audio is not None,
            location is not None,
        ].count(True) > 1:
            logger.error("You passed two or more exclusive parameters simultaneously")
            return False

        reply_markup = self._validate_markup(reply_markup) or []

        if not isinstance(force_me, bool):
            logger.error("Invalid type for `force_me`")
            return False

        if not isinstance(always_allow, list):
            logger.error("Invalid type for `always_allow`")
            return False

        if not isinstance(ttl, int) and ttl:
            logger.error("Invalid type for `ttl`")
            return False

        if isinstance(message, Message) and not silent:
            try:
                status_message = await (
                    message.edit if message.out else message.respond
                )("🌘 <b>Loading inline form...</b>")
            except Exception:
                status_message = None
        else:
            status_message = None

        unit_id = utils.rand(16)

        perms_map = self._find_caller_sec_map() if not manual_security else None

        self._units[unit_id] = {
            "type": "form",
            "text": text,
            "buttons": reply_markup,
            "chat": None,
            "message_id": None,
            "uid": unit_id,
            "on_unload": on_unload,
            "future": Event(),
            **({"photo": photo} if photo else {}),
            **({"video": video} if video else {}),
            **({"gif": gif} if gif else {}),
            **({"location": location} if location else {}),
            **({"audio": audio} if audio else {}),
            **({"location": location} if location else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"ttl": round(time.time()) + ttl} if ttl else {}),
            **({"always_allow": always_allow} if always_allow else {}),
        }

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
        except Exception:
            logger.exception("Can't send form")

            if not self._db.get(main.__name__, "inlinelogs", True):
                msg = "<b>🚫 Form invoke failed! More info in logs</b>"
            else:
                exc = traceback.format_exc()
                # Remove `Traceback (most recent call last):`
                exc = "\n".join(exc.splitlines()[1:])
                msg = (
                    "<b>🚫 Form invoke failed!</b>\n\n"
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

        inline_message_id = self._units[unit_id]["inline_message_id"]

        if (
            not any(
                any("callback" in button or "input" in button for button in row)
                for row in reply_markup
            )
            and not ttl
        ):
            del self._units[unit_id]
            logger.debug(
                f"Unloading form {unit_id}, because it "
                "doesn't contain any button callbacks"
            )

        return InlineMessage(self, unit_id, inline_message_id)

    async def _form_inline_handler(self, inline_query: InlineQuery):
        try:
            query = inline_query.query.split()[0]
        except IndexError:
            return

        for unit in self._units.copy().values():
            for button in utils.array_sum(unit.get("buttons", [])):
                if (
                    "_switch_query" in button
                    and "input" in button
                    and button["_switch_query"] == query
                    and inline_query.from_user.id
                    in [self._me]
                    + self._client.dispatcher.security._owner
                    + unit.get("always_allow", [])
                ):
                    await inline_query.answer(
                        [
                            InlineQueryResultArticle(
                                id=utils.rand(20),
                                title=button["input"],
                                description=(
                                    "⚠️ Do not remove ID!"
                                    f" {random.choice(VERIFICATION_EMOJIES)}"
                                ),
                                input_message_content=InputTextMessageContent(
                                    "🔄 <b>Transferring value to userbot...</b>\n"
                                    "<i>This message will be deleted automatically</i>"
                                    if inline_query.from_user.id == self._me
                                    else "🔄 <b>Transferring value to userbot...</b>",
                                    "HTML",
                                    disable_web_page_preview=True,
                                ),
                            )
                        ],
                        cache_time=60,
                    )
                    return

        if (
            inline_query.query not in self._units
            or self._units[inline_query.query]["type"] != "form"
        ):
            return

        # Otherwise, answer it with templated form
        form = self._units[inline_query.query]
        if "photo" in form:
            await inline_query.answer(
                [
                    InlineQueryResultPhoto(
                        id=utils.rand(20),
                        title="Hikka",
                        description="Hikka",
                        caption=form.get("text"),
                        parse_mode="HTML",
                        photo_url=form["photo"],
                        thumb_url=(
                            "https://img.icons8.com/cotton/452/moon-satellite.png"
                        ),
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                    )
                ],
                cache_time=0,
            )
        elif "gif" in form:
            await inline_query.answer(
                [
                    InlineQueryResultGif(
                        id=utils.rand(20),
                        title="Hikka",
                        caption=form.get("text"),
                        parse_mode="HTML",
                        gif_url=form["gif"],
                        thumb_url=(
                            "https://img.icons8.com/cotton/452/moon-satellite.png"
                        ),
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                    )
                ],
                cache_time=0,
            )
        elif "video" in form:
            await inline_query.answer(
                [
                    InlineQueryResultVideo(
                        id=utils.rand(20),
                        title="Hikka",
                        description="Hikka",
                        caption=form.get("text"),
                        parse_mode="HTML",
                        video_url=form["video"],
                        thumb_url=(
                            "https://img.icons8.com/cotton/452/moon-satellite.png"
                        ),
                        mime_type="video/mp4",
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                    )
                ],
                cache_time=0,
            )
        elif "file" in form:
            await inline_query.answer(
                [
                    InlineQueryResultDocument(
                        id=utils.rand(20),
                        title="Hikka",
                        description="Hikka",
                        caption=form.get("text"),
                        parse_mode="HTML",
                        document_url=form["file"],
                        mime_type=form["mime_type"],
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                    )
                ],
                cache_time=0,
            )
        elif "location" in form:
            await inline_query.answer(
                [
                    InlineQueryResultLocation(
                        id=utils.rand(20),
                        latitude=form["location"][0],
                        longitude=form["location"][1],
                        title="Hikka",
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                    )
                ],
                cache_time=0,
            )
        elif "audio" in form:
            await inline_query.answer(
                [
                    InlineQueryResultAudio(
                        id=utils.rand(20),
                        audio_url=form["audio"]["url"],
                        caption=form.get("text"),
                        parse_mode="HTML",
                        title=form["audio"].get("title", "Hikka"),
                        performer=form["audio"].get("performer"),
                        audio_duration=form["audio"].get("duration"),
                        reply_markup=self.generate_markup(
                            form["uid"],
                        ),
                    )
                ],
                cache_time=0,
            )
        else:
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
