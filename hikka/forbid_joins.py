#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

from telethon import TelegramClient
from telethon.utils import is_list_like

import inspect
import logging

from . import loader

logger = logging.getLogger(__name__)

# ⚠️⚠️  WARNING!  ⚠️⚠️
# If you are a module developer, and you'll try to bypass this protection to
# force user join your channel, you will be added to SCAM modules
# list and you will be banned from Hikka federation.
# Let USER decide, which channel he will follow. Do not be so petty
# I hope, you understood me.
# Thank you


def install_join_forbidder(client: TelegramClient) -> TelegramClient:
    if hasattr(client, "_forbid_join_tag"):
        return client

    old_call = client._call

    async def new_call(
        sender: "MTProtoSender",  # type: ignore
        request: "TLRequest",  # type: ignore
        ordered: bool = False,
        flood_sleep_threshold: int = None,
    ):
        not_tuple = False
        if not is_list_like(request):
            not_tuple = True
            request = (request,)

        new_request = []

        for item in request:
            if item.CONSTRUCTOR_ID in {615851205, 1817183516}:
                if next(
                    (
                        frame_info.frame.f_locals["self"]
                        for frame_info in inspect.stack()
                        if hasattr(frame_info, "frame")
                        and hasattr(frame_info.frame, "f_locals")
                        and isinstance(frame_info.frame.f_locals, dict)
                        and "self" in frame_info.frame.f_locals
                        and isinstance(frame_info.frame.f_locals["self"], loader.Module)
                        and frame_info.frame.f_locals["self"].__class__.__name__
                        not in {
                            "APIRatelimiterMod",
                            "ForbidJoinMod",
                            "HelpMod",
                            "LoaderMod",
                            "HikkaSettingsMod",
                        }
                        # APIRatelimiterMod is a core proxy, so it wraps around every module in Hikka, if installed
                        # ForbidJoinMod is also a Core proxy, so it wraps around every module in Hikka, if installed
                        # HelpMod uses JoinChannelRequest for .support command
                        # LoaderMod prompts user to join developers' channels
                        # HikkaSettings prompts user to join channels, required by modules
                    ),
                    None,
                ):
                    logger.debug(
                        "🎉 I protected you from unintented"
                        f" {item.__class__.__name__} ({item})!"
                    )
                    continue

            new_request += [item]

        if not new_request:
            return

        return await old_call(
            sender,
            new_request[0] if not_tuple else tuple(new_request),
            ordered,
            flood_sleep_threshold,
        )

    client._call = new_call
    client._joins_forbidden = True
    logger.debug("🎉 JoinForbidder installed!")
    return client
