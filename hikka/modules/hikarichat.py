__version__ = (13, 0, 3)

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/hikarichat_icon.png
# meta banner: https://mods.hikariatama.ru/badges/hikarichat.jpg
# meta desc: Chat administrator toolkit, now with powerful free version
# meta developer: @hikarimods

# scope: disable_onload_docs
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.3.0
# requires: aiohttp websockets

import abc
import asyncio
import contextlib
import functools
import imghdr
import io
import json
import logging
import random
import re
import time
import typing
from math import ceil
from types import FunctionType

import aiohttp
import requests
import websockets
from aiogram.types import CallbackQuery, ChatPermissions
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError
from telethon.errors.rpcerrorlist import WebpageCurlFailedError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    GetFullChannelRequest,
    GetParticipantRequest,
    InviteToChannelRequest,
)
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import (
    Channel,
    ChannelParticipantCreator,
    Chat,
    ChatAdminRights,
    ChatBannedRights,
    DocumentAttributeAnimated,
    Message,
    MessageEntitySpoiler,
    MessageMediaUnsupported,
    User,
    UserStatusOnline,
)

from .. import loader, utils
from ..inline.types import InlineCall, InlineMessage

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    PIL_AVAILABLE = False
else:
    PIL_AVAILABLE = True

logger = logging.getLogger(__name__)

version = f"v{__version__[0]}.{__version__[1]}.{__version__[2]}stable"
ver = f"<i>HikariChat {version}</i>"

FLOOD_TIMEOUT = 0.8
FLOOD_TRESHOLD = 4


PROTECTS = {
    "antinsfw": "🔞 AntiNSFW",
    "antiarab": "🇵🇸 AntiArab",
    "antitagall": "🐵 AntiTagAll",
    "antihelp": "🐺 AntiHelp",
    "antiflood": "⏱ AntiFlood",
    "antichannel": "📯 AntiChannel",
    "antispoiler": "👻 AntiSpoiler",
    "report": "📣 Report",
    "antiexplicit": "🤬 AntiExplicit",
    "antiservice": "⚙️ AntiService",
    "antigif": "🎑 AntiGIF",
    "antizalgo": "🌀 AntiZALGO",
    "antistick": "🎨 AntiStick",
    "antilagsticks": "⚰️ AntiLagSticks",
    "cas": "🛡 CAS",
    "bnd": "💬 BND",
    "antiraid": "🚪 AntiRaid",
    "banninja": "🥷 BanNinja",
    "welcome": "👋 Welcome",
    "captcha": "🚥 Captcha",
}


def fit(line: str, max_size: int) -> str:
    if len(line) >= max_size:
        return line

    offsets_sum = max_size - len(line)

    return f"{' ' * ceil(offsets_sum / 2 - 1)}{line}{' ' * int(offsets_sum / 2 - 1)}"


def gen_table(t: typing.List[typing.List[str]]) -> bytes:
    table = ""
    header = t[0]
    rows_sizes = [len(i) + 2 for i in header]
    for row in t[1:]:
        rows_sizes = [max(len(j) + 2, rows_sizes[i]) for i, j in enumerate(row)]

    rows_lines = ["━" * i for i in rows_sizes]

    table += f"┏{('┯'.join(rows_lines))}┓\n"

    for line in t:
        table += f"┃⁣⁣ {' ┃⁣⁣ '.join([fit(row, rows_sizes[k]) for k, row in enumerate(line)])} ┃⁣⁣\n"
        table += "┠"

        for row in rows_sizes:
            table += f"{'─' * row}┼"

        table = table[:-1] + "┫\n"

    return "\n".join(table.splitlines()[:-1]) + "\n" + f"┗{('┷'.join(rows_lines))}┛\n"


def get_first_name(user: typing.Union[User, Channel]) -> str:
    """Returns first name of user or channel title"""
    return utils.escape_html(
        user.first_name if isinstance(user, User) else user.title
    ).strip()


def get_full_name(user: typing.Union[User, Channel]) -> str:
    return utils.escape_html(
        user.title
        if isinstance(user, Channel)
        else (
            f"{user.first_name} "
            + (user.last_name if getattr(user, "last_name", False) else "")
        )
    ).strip()


BANNED_RIGHTS = {
    "view_messages": False,
    "send_messages": False,
    "send_media": False,
    "send_stickers": False,
    "send_gifs": False,
    "send_games": False,
    "send_inline": False,
    "send_polls": False,
    "change_info": False,
    "invite_users": False,
}


class HikariChatAPI:
    def __init__(self):
        self._bot = "@hikka_userbot"

        self._queue = []
        self.feds = {}
        self.chats = {}
        self.variables = {}
        self.init_done = asyncio.Event()
        self._show_warning = True
        self._connected = False
        self._inited = False
        self._local = False

    async def init(
        self,
        client: "CustomTelegramClient",  # type: ignore
        db: "Database",  # type: ignore
        module: loader.Module,
    ):
        """Entry point"""
        self._client = client
        self._db = db
        self.module = module

        if not self.module.get("token"):
            await self._get_token()

        self._task = asyncio.ensure_future(self._connect())
        await self.init_done.wait()

    async def _wss(self):
        async with websockets.connect(
            f"wss://hikarichat.hikariatama.ru/ws/{self.module.get('token')}"
        ) as wss:
            init = json.loads(await wss.recv())

            logger.debug(f"HikariChat connection debug info {init}")

            if init["event"] == "startup":
                self.variables = init["variables"]
            elif init["event"] == "license_violation":
                await wss.close()
                raise Exception("local")

            self.init_done.set()

            logger.debug("HikariChat connected")
            self._show_warning = True
            self._connected = True
            self._inited = True

            while True:
                ans = json.loads(await wss.recv())

                if ans["event"] == "update_info":
                    self.chats = ans["chats"]
                    self.feds = ans["feds"]

                    await wss.send(json.dumps({"ok": True, "queue": self._queue}))
                    self._queue = []
                    for chat in self.chats:
                        if str(chat) not in self.module._linked_channels:
                            channel = (
                                await self._client(GetFullChannelRequest(int(chat)))
                            ).full_chat.linked_chat_id
                            self.module._linked_channels[str(chat)] = channel or False

                if ans["event"] == "queue_status":
                    await self._client.edit_message(
                        ans["chat_id"],
                        ans["message_id"],
                        ans["text"],
                    )

    async def _connect(self):
        while True:
            try:
                await self._wss()
            except Exception:
                logger.debug("HikariChat disconnection traceback", exc_info=True)

                if not self._inited:
                    self._local = True
                    self.variables = json.loads(
                        (
                            await utils.run_sync(
                                requests.get,
                                "https://gist.githubusercontent.com/hikariatama/31a8246c9c6ad0b451324969d6ff2940/raw/608509efd7fee6fa876227e1c8c3c7dc0a952892/variables.json",
                            )
                        ).text
                    )
                    self._feds = self.module.get("feds", {})
                    delattr(self, "feds")
                    self.chats = self.module.get("chats", {})
                    self._processor_task = asyncio.ensure_future(
                        self._queue_processor()
                    )
                    self.init_done.set()
                    self._task.cancel()
                    return

                self._connected = False
                if self._show_warning:
                    logger.debug("HikariChat disconnected, retry in 5 sec")
                    self._show_warning = False

            await asyncio.sleep(5)

    def request(self, payload: dict, message: typing.Optional[Message] = None):
        if isinstance(message, Message):
            payload = {
                **payload,
                **{
                    "chat_id": utils.get_chat_id(message),
                    "message_id": message.id,
                },
            }

        self._queue += [payload]

    def should_protect(self, chat_id: typing.Union[str, int], protection: str) -> bool:
        return (
            str(chat_id) in self.chats
            and protection in self.chats[str(chat_id)]
            and str(self.chats[str(chat_id)][protection][1]) == str(self.module._tg_id)
        )

    async def nsfw(self, photo: bytes) -> str:
        if not self.module.get("token"):
            logger.warning("Token is not sent, NSFW check forbidden")
            return "sfw"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                "POST",
                "https://hikarichat.hikariatama.ru/check_nsfw",
                headers={"Authorization": f"Bearer {self.module.get('token')}"},
                data={"file": photo},
            ) as resp:
                r = await resp.text()

                try:
                    r = json.loads(r)
                except Exception:
                    logger.exception("Failed to check NSFW")
                    return "sfw"

                if "error" in r and "Rate limit" in r["error"]:
                    logger.warning("NSFW checker ratelimit exceeded")
                    return "sfw"

                if "success" not in r:
                    logger.error(f"API error {json.dumps(r, indent=4)}")
                    return "sfw"

                return r["verdict"]

    async def _get_token(self):
        async with self._client.conversation(self._bot) as conv:
            m = await conv.send_message("/token")
            r = await conv.get_response()
            token = r.raw_text
            await m.delete()
            await r.delete()

            if not token.startswith("kirito_") and not token.startswith("asuna_"):
                raise loader.LoadError("Can't get token")

            self.module.set("token", token)

        await self._client.delete_dialog(self._bot)

    def __getattr__(self, attribute: str):
        if self._local and attribute == "feds":
            return {fed["shortname"]: fed for fed in self._feds.values()}

        raise AttributeError

    async def _queue_processor(self):
        while True:
            if not self._queue:
                await asyncio.sleep(1)
                continue

            ERROR = (
                "<emoji document_id=5300759756669984376>🚫</emoji> <b>API Error:"
                " </b><code>{}</code>"
            )

            async def assert_arguments(args: set, item: dict) -> bool:
                if any(i not in item.get("args", {}) for i in args):
                    if "chat_id" in item:
                        await self._client.edit_message(
                            item["chat_id"],
                            item["message_id"],
                            (
                                "<emoji document_id=5300759756669984376>🚫</emoji>"
                                " <b>Bad API arguments, PROKAZNIK!</b>"
                            ),
                        )
                    return False

                return True

            async def error(msg: str, item: dict):
                if "chat_id" in item:
                    await self._client.edit_message(
                        item["chat_id"],
                        item["message_id"],
                        ERROR.format(msg),
                    )

            feds_copy = self._feds.copy()
            chats_copy = self.chats.copy()

            item = self._queue.pop(0)
            u = str(self._client._tg_id)

            if item["action"] == "create federation":
                if not await assert_arguments({"shortname", "name"}, item):
                    continue

                t = "fed_" + "".join(
                    [
                        random.choice(list("abcdefghijklmnopqrstuvwyz1234567890"))
                        for _ in range(32)
                    ]
                )

                self._feds[t] = {
                    "shortname": item["args"]["shortname"],
                    "name": item["args"]["name"],
                    "chats": [],
                    "warns": {},
                    "admins": [u],
                    "owner": u,
                    "fdef": [],
                    "notes": {},
                    "uid": t,
                }

            if item["action"] == "add chat to federation":
                if not await assert_arguments({"uid", "cid"}, item):
                    continue

                if item["args"]["uid"] not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if str(item["args"]["cid"]) in self._feds[item["args"]["uid"]]["chats"]:
                    await error("Chat is already in this federation", item)
                    continue

                self._feds[item["args"]["uid"]]["chats"] += [str(item["args"]["cid"])]

            if item["action"] == "remove chat from federation":
                if not await assert_arguments({"uid", "cid"}, item):
                    continue

                if item["args"]["uid"] not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if (
                    str(item["args"]["cid"])
                    not in self._feds[item["args"]["uid"]]["chats"]
                ):
                    await error("Chat is not in this federation", item)
                    continue

                self._feds[item["args"]["uid"]]["chats"].remove(
                    str(item["args"]["cid"])
                )

            if item["action"] == "update protections":
                if not await assert_arguments({"protection", "state", "chat"}, item):
                    continue

                chat, protection, state = (
                    str(item["args"]["chat"]),
                    item["args"]["protection"],
                    item["args"]["state"],
                )

                if protection not in self.variables["protections"] + ["welcome"]:
                    await error("Unknown protection type", item)
                    continue

                if (
                    protection in self.variables["argumented_protects"]
                    and state not in self.variables["protect_actions"]
                    or protection not in self.variables["argumented_protects"]
                    and protection in self.variables["protections"]
                    and state not in {"on", "off"}
                ):
                    await error("Protection state invalid", item)
                    continue

                if chat not in self.chats:
                    self.chats[chat] = {}

                if state == "off":
                    if protection in self.chats[chat]:
                        del self.chats[chat][protection]
                else:
                    self.chats[chat][protection] = [state, u]

            if item["action"] == "delete federation":
                if not await assert_arguments({"uid"}, item):
                    continue

                uid = item["args"]["uid"]

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                del self._feds[uid]

            if item["action"] == "rename federation":
                if not await assert_arguments({"uid", "name"}, item):
                    continue

                uid, name = item["args"]["uid"], item["args"]["name"]

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                self._feds[uid]["name"] = name

            if item["action"] == "protect user":
                if not await assert_arguments({"uid", "user"}, item):
                    continue

                uid, user = item["args"]["uid"], item["args"]["user"]
                user = str(user)

                if not user.isdigit():
                    await error("Unexpected format for user", item)
                    continue

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if user in self._feds[uid]["fdef"]:
                    self._feds[uid]["fdef"].remove(user)
                else:
                    self._feds[uid]["fdef"] += [user]

            if item["action"] == "warn user":
                if not await assert_arguments({"uid", "user", "reason"}, item):
                    continue

                uid, user, reason = (
                    item["args"]["uid"],
                    item["args"]["user"],
                    item["args"]["reason"],
                )
                user = str(user)

                if not user.isdigit():
                    await error("Unexpected format for user", item)
                    continue

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if user not in self._feds[uid]["warns"]:
                    self._feds[uid]["warns"][user] = []

                self._feds[uid]["warns"][user] += [reason]

            if item["action"] == "forgive user warn":
                if not await assert_arguments({"uid", "user"}, item):
                    continue

                uid, user = item["args"]["uid"], item["args"]["user"]
                user = str(user)

                if not user.isdigit():
                    await error("Unexpected format for user", item)
                    continue

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if (
                    user not in self._feds[uid]["warns"]
                    or not self._feds[uid]["warns"][user]
                ):
                    await error("This user has no warns yet", item)
                    continue

                del self._feds[uid]["warns"][user][-1]

            if item["action"] == "clear all user warns":
                if not await assert_arguments({"uid", "user"}, item):
                    continue

                uid, user = item["args"]["uid"], item["args"]["user"]
                user = str(user)

                if not user.isdigit():
                    if not item["args"].get("silent", False):
                        await error("Unexpected format for user", item)
                    continue

                if uid not in self._feds:
                    if not item["args"].get("silent", False):
                        await error("Federation doesn't exist", item)
                    continue

                if not self._feds[uid].get("warns", {}).get(user):
                    if not item["args"].get("silent", False):
                        await error("This user has no warns yet", item)
                    continue

                del self._feds[uid]["warns"][user]

            if item["action"] == "clear federation warns":
                if not await assert_arguments({"uid"}, item):
                    continue

                uid = item["args"]["uid"]

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if not self._feds[uid].get("warns"):
                    await error("This federation has no warns yet", item)
                    continue

                del self._feds[uid]["warns"]

            if item["action"] == "new note":
                if not await assert_arguments({"uid", "shortname", "note"}, item):
                    continue

                uid, shortname, note = (
                    item["args"]["uid"],
                    item["args"]["shortname"],
                    item["args"]["note"],
                )

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                self._feds[uid]["notes"][shortname] = {"creator": u, "text": note}

            if item["action"] == "delete note":
                if not await assert_arguments({"uid", "shortname"}, item):
                    continue

                uid, shortname = item["args"]["uid"], item["args"]["shortname"]

                if uid not in self._feds:
                    await error("Federation doesn't exist", item)
                    continue

                if shortname not in self._feds[uid]["notes"]:
                    await error(f"Note not found ({uid=}, {shortname=})", item)
                    continue

                del self._feds[uid]["notes"][shortname]

            if feds_copy != self._feds:
                self.module.set("feds", self._feds)

            if chats_copy != self.chats:
                self.module.set("chats", self.chats)


api = HikariChatAPI()


def reverse_dict(d: dict) -> dict:
    return {val: key for key, val in d.items()}


@loader.tds
class HikariChatMod(loader.Module):
    """
    Advanced chat admin toolkit
    """

    __metaclass__ = abc.ABCMeta

    strings = {
        "name": "HikariChat",
        "args": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Args are"
            " incorrect</b>"
        ),
        "no_reason": "Not specified",
        "antitagall_on": (
            "<emoji document_id=5785175271011259591>🐵</emoji> <b>AntiTagAll is now on"
            " in this chat\nAction: {}</b>"
        ),
        "antitagall_off": (
            "<emoji document_id=5785175271011259591>🐵</emoji> <b>AntiTagAll is now off"
            " in this chat</b>"
        ),
        "antiarab_on": (
            "<emoji document_id=6323257144745395640>🇵🇸</emoji> <b>AntiArab is now on in"
            " this chat\nAction: {}</b>"
        ),
        "antiarab_off": (
            "<emoji document_id=6323257144745395640>🇵🇸</emoji> <b>AntiArab is now off"
            " in this chat</b>"
        ),
        "antilagsticks_on": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Destructive stickers"
            " protection is now on in this chat</b>"
        ),
        "antilagsticks_off": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Destructive stickers"
            " protection is now off in this chat</b>"
        ),
        "antizalgo_on": (
            "<emoji document_id=5213293263083018856>🌀</emoji> <b>AntiZALGO is now"
            " on in"
            " this chat\nAction: {}</b>"
        ),
        "antizalgo_off": (
            "<emoji document_id=5213293263083018856>🌀</emoji> <b>AntiZALGO is now off"
            " in this chat</b>"
        ),
        "antistick_on": (
            "<emoji document_id=5431456208487716895>🎨</emoji> <b>AntiStick is now"
            " on in"
            " this chat\nAction: {}</b>"
        ),
        "antistick_off": (
            "<emoji document_id=5431456208487716895>🎨</emoji> <b>AntiStick is now off"
            " in this chat</b>"
        ),
        "antihelp_on": (
            "<emoji document_id=5467759840463953770>🐺</emoji> <b>AntiHelp is now on in"
            " this chat</b>"
        ),
        "antihelp_off": (
            "<emoji document_id=5467759840463953770>🐺</emoji> <b>AntiHelp is now"
            " off in"
            " this chat</b>"
        ),
        "antiraid_on": (
            "<emoji document_id=6334359218593728345><emoji"
            " document_id=6037460928423791421>🚪</emoji></emoji> <b>AntiRaid is now on"
            " in this chat\nAction: {}</b>"
        ),
        "antiraid_off": (
            "<emoji document_id=6334359218593728345><emoji"
            " document_id=6037460928423791421>🚪</emoji></emoji> <b>AntiRaid is now off"
            " in this chat</b>"
        ),
        "bnd_on": (
            "<emoji document_id=5465300082628763143>💬</emoji> <b>Block-Non-Discussion"
            " is now on in this chat\nAction: {}</b>"
        ),
        "bnd_off": (
            "<emoji document_id=5465300082628763143>💬</emoji> <b>Block-Non-Discussion"
            " is now off in this chat</b>"
        ),
        "antiraid": (
            "<emoji document_id=6334359218593728345><emoji"
            " document_id=6037460928423791421>🚪</emoji></emoji> <b>AntiRaid is On."
            " I {}"
            ' <a href="{}">{}</a> in chat {}</b>'
        ),
        "antichannel_on": (
            "<emoji document_id=5470094069289984325>📯</emoji> <b>AntiChannel is now on"
            " in this chat</b>"
        ),
        "antichannel_off": (
            "<emoji document_id=5470094069289984325>📯</emoji> <b>AntiChannel is"
            " now off"
            " in this chat</b>"
        ),
        "report_on": (
            "<emoji document_id=5213203794619277246>📣</emoji> <b>Report is now on in"
            " this chat</b>"
        ),
        "report_off": (
            "<emoji document_id=5213203794619277246>📣</emoji> <b>Report is now off in"
            " this chat</b>"
        ),
        "antiflood_on": (
            "<emoji document_id=5384611567125928766>⏱</emoji> <b>AntiFlood is now on in"
            " this chat\nAction: {}</b>"
        ),
        "antiflood_off": (
            "<emoji document_id=5384611567125928766>⏱</emoji> <b>AntiFlood is now off"
            " in this chat</b>"
        ),
        "antispoiler_on": (
            "<emoji document_id=5798648862591684122>👻</emoji> <b>AntiSpoiler is now on"
            " in this chat</b>"
        ),
        "antispoiler_off": (
            "<emoji document_id=5798648862591684122>👻</emoji> <b>AntiSpoiler is"
            " now off"
            " in this chat</b>"
        ),
        "antigif_on": (
            "<emoji document_id=6048825205730577727>🎑</emoji> <b>AntiGIF is now on in"
            " this chat</b>"
        ),
        "antigif_off": (
            "<emoji document_id=6048825205730577727>🎑</emoji> <b>AntiGIF is now off in"
            " this chat</b>"
        ),
        "antiservice_on": (
            "<emoji document_id=5787237370709413702>⚙️</emoji> <b>AntiService is now on"
            " in this chat</b>"
        ),
        "antiservice_off": (
            "<emoji document_id=5787237370709413702>⚙️</emoji> <b>AntiService is now"
            " off in this chat</b>"
        ),
        "banninja_on": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja is now on in"
            " this chat</b>"
        ),
        "banninja_off": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja is now"
            " off in"
            " this chat</b>"
        ),
        "antiexplicit_on": (
            "<emoji document_id=5373123633415723713>🤬</emoji> <b>AntiExplicit is"
            " now on"
            " in this chat\nAction: {}</b>"
        ),
        "antiexplicit_off": (
            "<emoji document_id=5373123633415723713>🤬</emoji> <b>AntiExplicit is now"
            " off in this chat</b>"
        ),
        "captcha_on": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b>Captcha is now on in"
            " this chat\nAction: {}</b>"
        ),
        "captcha_off": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b>Captcha is now off in"
            " this chat</b>"
        ),
        "cas_on": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>CAS is now on in this"
            " chat\nAction: {}</b>"
        ),
        "cas_off": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>CAS is now off in this"
            " chat</b>"
        ),
        "antinsfw_on": (
            "<emoji document_id=4976982981341086273>🔞</emoji> <b>AntiNSFW is now on in"
            " this chat\nAction: {}</b>"
        ),
        "antinsfw_off": (
            "<emoji document_id=4976982981341086273>🔞</emoji> <b>AntiNSFW is now"
            " off in"
            " this chat</b>"
        ),
        "arabic_nickname": (
            '<emoji document_id=6323257144745395640>🇵🇸</emoji> <b><a href="{}">{}</a>'
            " has hieroglyphics in his nickname.\n👊 Action: I {}</b>"
        ),
        "zalgo": (
            '<emoji document_id=5213293263083018856>🌀</emoji> <b><a href="{}">{}</a>'
            " has ZALGO in his nickname.\n👊 Action: I {}</b>"
        ),
        "bnd": (
            '<emoji document_id=5465300082628763143>💬</emoji> <b><a href="{}">{}</a>'
            " sent a message to channel comments without being chat member.\n👊 Action:"
            " I {}</b>"
        ),
        "cas": (
            '<emoji document_id=5300855732009180995>🛡</emoji> <b><a href="{}">{}</a>'
            " appears to be in Combat Anti Spam database.\n👊 Action: I {}</b>"
        ),
        "stick": (
            "<emoji document_id=5431456208487716895>🎨</emoji> <b><a"
            ' href="{}">{}</a> is'
            " flooding stickers.\n👊 Action: I {}</b>"
        ),
        "explicit": (
            '<emoji document_id=5373123633415723713>🤬</emoji> <b><a href="{}">{}</a>'
            " sent explicit content.\n👊 Action: I {}</b>"
        ),
        "destructive_stick": (
            '<emoji document_id=5300759756669984376>🚫</emoji> <b><a href="{}">{}</a>'
            " sent destructive sticker.\n👊 Action: I {}</b>"
        ),
        "nsfw_content": (
            '<emoji document_id=4976982981341086273>🔞</emoji> <b><a href="{}">{}</a>'
            " sent NSFW content.\n👊 Action: I {}</b>"
        ),
        "flood": (
            '<emoji document_id=5384611567125928766>⏱</emoji> <b><a href="{}">{}</a> is'
            " flooding.\n👊 Action: I {}</b>"
        ),
        "tagall": (
            '<emoji document_id=5785175271011259591>🐵</emoji> <b><a href="{}">{}</a>'
            " used TagAll.\n👊 Action: I {}</b>"
        ),
        "fwarn": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji><emoji"
            ' document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a></b> got'
            " {}/{} federative warn\nReason: <b>{}</b>\n\n{}"
        ),
        "no_fed_warns": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>This federation has"
            " no warns yet</b>"
        ),
        "no_warns": (
            '<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b><a href="{}">{}</a>'
            " has no warns yet</b>"
        ),
        "warns": (
            '<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b><a href="{}">{}</a>'
            " has {}/{} warns</b>\n\n<i>{}</i>"
        ),
        "warns_adm_fed": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>Warns in this"
            " federation</b>:\n"
        ),
        "dwarn_fed": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>Forgave last"
            ' federative warn of <a href="tg://user?id={}">{}</a></b>'
        ),
        "clrwarns_fed": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>Forgave all"
            ' federative warns of <a href="tg://user?id={}">{}</a></b>'
        ),
        "warns_limit": (
            '<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b><a href="{}">{}</a>'
            " reached warns limit.\nAction: I {}</b>"
        ),
        "welcome": (
            "<emoji document_id=5472055112702629499>👋</emoji> <b>Now I will greet"
            " people in this chat</b>\n{}"
        ),
        "unwelcome": (
            "<emoji document_id=5472055112702629499>👋</emoji> <b>Now I will not greet"
            " people in this chat</b>"
        ),
        "chat404": "🔓 <b>I am not protecting this chat yet.</b>\n",
        "protections": (
            "<b><emoji document_id=6323257144745395640>🇵🇸</emoji>"
            " <code>.AntiArab</code> - Bans spammy arabs\n<b><emoji"
            " document_id=5467759840463953770>🐺</emoji> <code>.AntiHelp</code> -"
            " Removes frequent userbot commands\n<b><emoji"
            " document_id=5785175271011259591>🐵</emoji> <code>.AntiTagAll</code> -"
            " Restricts tagging all members\n<b><emoji"
            " document_id=5472055112702629499>👋</emoji> <code>.Welcome</code> - Greets"
            " new members\n<b><emoji document_id=6334359218593728345><emoji"
            " document_id=6037460928423791421>🚪</emoji></emoji> <code>.AntiRaid</code>"
            " - Bans all new members\n<b><emoji"
            " document_id=5470094069289984325>📯</emoji> <code>.AntiChannel</code> -"
            " Restricts writing on behalf of channels\n<b><emoji"
            " document_id=5798648862591684122>👻</emoji> <code>.AntiSpoiler</code> -"
            " Restricts spoilers\n<b><emoji document_id=6048825205730577727>🎑</emoji>"
            " <code>.AntiGIF</code> - Restricts GIFs\n<b>🍓 <code>.AntiNSFW</code> -"
            " Restricts NSFW photos and stickers\n<b><emoji"
            " document_id=5384611567125928766>⏱</emoji> <code>.AntiFlood</code> -"
            " Prevents flooding\n<b><emoji document_id=5373123633415723713>🤬</emoji>"
            " <code>.AntiExplicit</code> - Restricts explicit content\n<b><emoji"
            " document_id=5787237370709413702>⚙️</emoji> <code>.AntiService</code> -"
            " Removes service messages\n<b><emoji"
            " document_id=5213293263083018856>🌀</emoji> <code>.AntiZALGO</code> -"
            " Penalty for users with ZALGO in nickname\n<b><emoji"
            " document_id=5431456208487716895>🎨</emoji> <code>.AntiStick</code> -"
            " Prevents stickers flood\n<b><emoji"
            " document_id=5213107179329953547>🚥</emoji> <code>.Captcha</code> -"
            " Requires every new participant to complete captcha\n<b><emoji"
            " document_id=5215470334760721739>🛡</emoji> <code>.CAS</code> - Check every"
            " new participant through Combat Anti Spam\n<b><emoji"
            " document_id=5465300082628763143>💬</emoji> <code>.BND</code> - Restricts"
            " messages from users, which are not a participants of chat"
            " (comments)\n<b><emoji document_id=6323575131239089635>🥷</emoji>"
            " <code>.BanNinja</code> - Automatic version of AntiRaid\n<b>⚰️"
            " <code>.AntiLagSticks</code> - Bans laggy stickers\n<b>👾 Admin:"
            " </b><code>.ban</code> <code>.kick</code>"
            " <code>.mute</code>\n<code>.unban</code> <code>.unmute</code> <b>- Admin"
            " tools</b>\n<b><emoji document_id=5193091781327068499>👮‍♀️</emoji>"
            " Warns:</b> <code>.warn</code> <code>.warns</code>\n<code>.dwarn</code>"
            " <code>.clrwarns</code> <b>- Warning system</b>\n<b><emoji"
            " document_id=5773781976905421370>💼</emoji> Federations:</b>"
            " <code>.fadd</code> <code>.frm</code>"
            " <code>.newfed</code>\n<code>.namefed</code> <code>.fban</code>"
            " <code>.rmfed</code> <code>.feds</code>\n<code>.fpromote</code>"
            " <code>.fdemote</code>\n<code>.fdef</code> <code>.fdeflist</code> <b>-"
            " Controlling multiple chats</b>\n<b>🗒 Notes:</b> <code>.fsave</code>"
            " <code>.fstop</code> <code>.fnotes</code> <b>- Federative notes</b>"
        ),
        "not_admin": "🤷‍♂️ <b>I'm not admin here, or don't have enough rights</b>",
        "mute": (
            '<emoji document_id=5372800046284674872>🤐</emoji> <b><a href="{}">{}</a>'
            " was muted {}. Reason: </b><i>{}</i>\n\n{}"
        ),
        "mute_log": (
            '<emoji document_id=5372800046284674872>🤐</emoji> <b><a href="{}">{}</a>'
            ' was muted {} in <a href="{}">{}</a>. Reason: </b><i>{}</i>\n\n{}'
        ),
        "ban": (
            '<emoji document_id=5247152118069992250>🔒</emoji> <b><a href="{}">{}</a>'
            " was banned {}. Reason: </b><i>{}</i>\n\n{}"
        ),
        "ban_log": (
            '<emoji document_id=5247152118069992250>🔒</emoji> <b><a href="{}">{}</a>'
            ' was banned {} in <a href="{}">{}</a>. Reason: </b><i>{}</i>\n\n{}'
        ),
        "kick": (
            '<emoji document_id=6037460928423791421>🚪</emoji> <b><a href="{}">{}</a>'
            " was kicked. Reason: </b><i>{}</i>\n\n{}"
        ),
        "kick_log": (
            '<emoji document_id=6037460928423791421>🚪</emoji> <b><a href="{}">{}</a>'
            ' was kicked in <a href="{}">{}</a>. Reason: </b><i>{}</i>\n\n{}'
        ),
        "unmuted": (
            '<emoji document_id=5436040291507247633>🎉</emoji> <b><a href="{}">{}</a>'
            " was unmuted</b>"
        ),
        "unmuted_log": (
            '<emoji document_id=5436040291507247633>🎉</emoji> <b><a href="{}">{}</a>'
            ' was unmuted in <a href="{}">{}</a></b>'
        ),
        "unban": (
            '<emoji document_id=5469791106591890404>🪄</emoji> <b><a href="{}">{}</a>'
            " was unbanned</b>"
        ),
        "unban_log": (
            '<emoji document_id=5469791106591890404>🪄</emoji> <b><a href="{}">{}</a>'
            ' was unbanned in <a href="{}">{}</a></b>'
        ),
        "defense": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>Shield for <a"
            ' href="{}">{}</a> is now {}</b>'
        ),
        "no_defense": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>Federative defense"
            " list is empty</b>"
        ),
        "defense_list": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>Federative defense"
            " list:</b>\n{}"
        ),
        "fadded": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Current chat added to"
            ' federation "{}"</b>'
        ),
        "newfed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Created federation"
            ' "{}"</b>'
        ),
        "rmfed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Removed federation"
            ' "{}"</b>'
        ),
        "fed404": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federation not"
            " found</b>"
        ),
        "frem": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Current chat removed"
            ' from federation "{}"</b>'
        ),
        "f404": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Current chat is"
            " not in"
            ' federation "{}"</b>'
        ),
        "fexists": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Current chat is"
            ' already in federation "{}"</b>'
        ),
        "fedexists": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federation exists</b>"
        ),
        "joinfed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federation joined</b>"
        ),
        "namedfed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federation renamed to"
            " {}</b>"
        ),
        "nofed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Current chat is"
            " not in"
            " any federation</b>"
        ),
        "fban": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " was banned in federation {} {}\nReason: </b><i>{}</i>\n{}"
        ),
        "gban": (
            '<emoji document_id=5301059317753979286>🖕</emoji> <b><a href="{}">{}</a>'
            " was gbanned.</b>\n<b>Reason: </b><i>{}</i>\n\n{}"
        ),
        "gbanning": (
            "<emoji document_id=5301059317753979286>🖕</emoji> <b>Gbanning <a"
            ' href="{}">{}</a>...</b>'
        ),
        "gunban": (
            '<emoji document_id=6334872157947955302>🤗</emoji> <b><a href="{}">{}</a>'
            " was gunbanned.</b>\n\n{}"
        ),
        "gunbanning": (
            "<emoji document_id=6334872157947955302>🤗</emoji> <b>Gunbanning <a"
            ' href="{}">{}</a>...</b>'
        ),
        "in_n_chats": (
            "<emoji document_id=5379568936218009290>👎</emoji> <b>Banned in {}"
            " chat(-s)</b>"
        ),
        "unbanned_in_n_chats": (
            "<emoji document_id=5461129450341014019>✋️</emoji> <b>Unbanned in {}"
            " chat(-s)</b>"
        ),
        "fmute": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " muted in federation {} {}\nReason: </b><i>{}</i>\n{}"
        ),
        "funban": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " unbanned in federation </b><i>{}</i>\n"
        ),
        "funmute": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " unmuted in federation </b><i>{}</i>\n"
        ),
        "feds_header": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federations:</b>\n\n"
        ),
        "fed": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b>Federation "{}"'
            " info:</b>\n🔰 <b>Chats:</b>\n<b>{}</b>\n🔰 <b>Channels:</b>\n<b>{}</b>\n🔰"
            " <b>Admins:</b>\n<b>{}</b>\n🔰 <b>Warns: {}</b>\n"
        ),
        "no_fed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>This chat is not in"
            " any federation</b>"
        ),
        "fpromoted": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " promoted in federation {}</b>"
        ),
        "fdemoted": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " demoted in federation {}</b>"
        ),
        "api_error": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>api.hikariatama.ru"
            " Error!</b>\n<code>{}</code>"
        ),
        "fsave_args": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Usage: .fsave"
            " shortname &lt;reply&gt;</b>"
        ),
        "fstop_args": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Usage: .fstop"
            " shortname</b>"
        ),
        "fsave": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federative note"
            " </b><code>{}</code><b> saved!</b>"
        ),
        "fstop": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federative note"
            " </b><code>{}</code><b> removed!</b>"
        ),
        "fnotes": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Federative"
            " notes:</b>\n{}"
        ),
        "usage": "ℹ️ <b>Usage: .{} &lt;on/off&gt;</b>",
        "chat_only": "ℹ️ <b>This command is for chats only</b>",
        "version": (
            "<emoji document_id=5440551785284510215>🎢</emoji> <b>{}</b>\n\n<emoji"
            " document_id=5454182070156794055>🤘</emoji> <b>Author:"
            " t.me/hikariatama</b>\n<emoji document_id=6325750691088303497>☺️</emoji>"
            " <b>Downloaded from @hikarimods</b>\n<b>{}</b>"
        ),
        "error": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>HikariChat Issued"
            " error</b>"
        ),
        "reported": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            " reported this message to admins\nReason: </b><i>{}</i>"
        ),
        "no_federations": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>You have no active"
            " federations</b>"
        ),
        "clrallwarns_fed": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>Forgave all"
            " federative warns of federation</b>"
        ),
        "cleaning": (
            "<emoji document_id=5215493819641895305>🫥</emoji> <b>Looking for Deleted"
            " accounts...</b>"
        ),
        "deleted": (
            "<emoji document_id=5215493819641895305>🫥</emoji> <b>Removed {} Deleted"
            " accounts</b>"
        ),
        "fcleaning": (
            "<emoji document_id=5215493819641895305>🫥</emoji> <b>Looking for Deleted"
            " accounts in federation...</b>"
        ),
        "btn_unban": "🔓 Unban (ADM)",
        "btn_unmute": "🔈 Unmute (ADM)",
        "btn_unwarn": "♻️ De-Warn (ADM)",
        "inline_unbanned": (
            '🔓 <b><a href="{}">{}</a> unbanned by <a href="{}">{}</a></b>'
        ),
        "inline_unmuted": (
            '🔈 <b><a href="{}">{}</a> unmuted by <a href="{}">{}</a></b>'
        ),
        "inline_unwarned": (
            '♻️ <b>Forgave last warn of <a href="{}">{}</a> by <a href="{}">{}</a></b>'
        ),
        "inline_funbanned": (
            '🔓 <b><a href="{}">{}</a> unbanned in federation by <a'
            ' href="{}">{}</a></b>'
        ),
        "inline_funmuted": (
            '🔈 <b><a href="{}">{}</a> unmuted in federation by <a href="{}">{}</a></b>'
        ),
        "btn_funmute": "🔈 Fed Unmute (ADM)",
        "btn_funban": "🔓 Fed Unban (ADM)",
        "btn_mute": "🙊 Mute",
        "btn_ban": "🔒 Ban",
        "btn_fban": "💼 Fed Ban",
        "btn_del": "🗑 Delete",
        "inline_fbanned": (
            '<emoji document_id=5773781976905421370>💼</emoji> <b><a href="{}">{}</a>'
            ' banned in federation by <a href="{}">{}</a></b>'
        ),
        "inline_muted": '🙊 <b><a href="{}">{}</a> muted by <a href="{}">{}</a></b>',
        "inline_banned": (
            '<emoji document_id=5247152118069992250>🔒</emoji> <b><a href="{}">{}</a>'
            ' banned by <a href="{}">{}</a></b>'
        ),
        "inline_deleted": '🗑 <b>Deleted by <a href="{}">{}</a></b>',
        "sync": "🔄 <b>Syncing chats and feds with server in force mode...</b>",
        "sync_complete": "😌 <b>Successfully synced</b>",
        "rename_noargs": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Specify new"
            " federation"
            " name</b>"
        ),
        "rename_success": '😇 <b>Federation renamed to "</b><code>{}</code><b>"</b>',
        "suffix_removed": "📼 <b>Punishment suffix removed</b>",
        "suffix_updated": "📼 <b>New punishment suffix saved</b>\n\n{}",
        "processing_myrights": "😌 <b>Processing chats</b>",
        "logchat_removed": "📲 <b>Log chat disabled</b>",
        "logchat_invalid": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Log chat invalid</b>"
        ),
        "logchat_set": "📲 <b>Log chat updated to </b><code>{}</code>",
        "clnraid_args": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>Example usage:"
            " </b><code>.clnraid 10</code>"
        ),
        "clnraid_admin": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>Error occured while"
            " promoting cleaner. Please, ensure you have enough rights in chat</b>"
        ),
        "clnraid_started": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>RaidCleaner is in"
            " progress... Found {} users to kick...</b>"
        ),
        "clnraid_confirm": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>Please, confirm that"
            " you want to start RaidCleaner on {} users</b>"
        ),
        "clnraid_yes": "<emoji document_id=6323575131239089635>🥷</emoji> Start",
        "clnraid_cancel": "🔻 Cancel",
        "clnraid_stop": "🚨 Stop",
        "clnraid_complete": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>RaidCleaner complete!"
            " Removed: {} user(-s)</b>"
        ),
        "clnraid_cancelled": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>RaidCleaner"
            " cancelled."
            " Removed: {} user(-s)</b>"
        ),
        "smart_anti_raid_active": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja is working"
            " hard to prevent intrusion to this chat.</b>\n\n{}<i>Deleted {}"
            " bot(-s)</i>"
        ),
        "smart_anti_raid_off": "🚨 Stop",
        "smart_anti_raid_stopped": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja Stopped</b>"
        ),
        "banninja_report": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja has done his"
            " job.</b>\n<i>Deleted {} bot(-s)</i>\n\n🏹 <i>«BanNinja can handle any"
            " size"
            " of attack»</i> © <code>@hikariatama</code>"
        ),
        "forbid_messages": (
            "⚠️ <b>I've forbidden sending messages until attack is fully"
            " released</b>\n\n"
        ),
        "confirm_rmfed": (
            "⚠️ <b>Warning! This operation can't be reverted! Are you sure, "
            "you want to delete federation </b><code>{}</code><b>?</b>"
        ),
        "confirm_rmfed_btn": "🗑 Delete",
        "decline_rmfed_btn": "🔻 Cancel",
        "pil_unavailable": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Pillow package"
            " unavailable</b>"
        ),
        "action": "<action>",
        "configure": "Configure",
        "toggle": "Toggle",
        "no_protects": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>This chat has no"
            " active protections to show</b>"
        ),
        "from_where": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Reply to a message to"
            " purge from</b>"
        ),
        "no_notes": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>No notes found</b>"
        ),
        "complete_captcha": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b><a"
            ' href="tg://user?id={}">{}</a>, please, complete captcha within 5'
            " minutes</b>"
        ),
        "captcha_timeout": (
            '<emoji document_id=5213107179329953547>🚥</emoji> <b><a href="{}">{}</a>'
            " have not completed captcha in time.\n👊 Action: I {}</b>"
        ),
        "captcha_failed": (
            '<emoji document_id=5213107179329953547>🚥</emoji> <b><a href="{}">{}</a>'
            " failed captcha.\n👊 Action: I {}</b>"
        ),
        "fdef403": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>You can't {} this"
            " user, because he is under federative protection</b>"
        ),
    }

    strings_ru = {
        "complete_captcha": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b><a"
            ' href="tg://user?id={}">{}</a>, пожалуйста, пройди капчу в течение 5'
            " минут</b>"
        ),
        "captcha_timeout": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b><a"
            ' href="{}">{}</a> не'
            " прошел капчу вовремя.\n👊 Действие: {}</b>"
        ),
        "captcha_failed": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b><a"
            ' href="{}">{}</a> не'
            " прошел капчу.\n👊 Действие: {}</b>"
        ),
        "cas_on": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>CAS теперь включен в"
            " этом чате\nДействие: {}</b>"
        ),
        "cas_off": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>CAS теперь выключен в"
            " этом чате</b>"
        ),
        "cas": (
            '<emoji document_id=5300855732009180995>🛡</emoji> <b><a href="{}">{}</a>'
            " appears to be in Combat Anti Spam database.\n👊 Action: I {}</b>"
        ),
        "from_where": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Ответь на сообщение,"
            " начиная с которого надо удалить.</b>"
        ),
        "smart_anti_raid_active": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja работает в"
            " поте лица, отбивая атаку на этот чат.</b>\n\n{}<i>Удалено {} бот(-ов)</i>"
        ),
        "forbid_messages": (
            "⚠️ <b>Я запретил отправку сообщений, пока атака не будет полностью"
            " отражена</b>\n\n"
        ),
        "smart_anti_raid_off": "🚨 Остановить",
        "smart_anti_raid_stopped": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja"
            " остановлен</b>"
        ),
        "error": "😵 <b>Произошла ошибка HikariChat</b>",
        "args": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Неверные"
            " аргументы</b>"
        ),
        "no_reason": "Не указана",
        "antitagall_on": (
            "<emoji document_id=5785175271011259591>🐵</emoji> <b>AntiTagAll теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antitagall_off": (
            "<emoji document_id=5785175271011259591>🐵</emoji> <b>AntiTagAll теперь"
            " выключен в этом чате</b>"
        ),
        "antiarab_on": (
            "<emoji document_id=6323257144745395640>🇵🇸</emoji> <b>AntiArab теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antiarab_off": (
            "<emoji document_id=6323257144745395640>🇵🇸</emoji> <b>AntiArab теперь"
            " выключен в этом чате</b>"
        ),
        "antizalgo_on": (
            "<emoji document_id=5213293263083018856>🌀</emoji> <b>AntiZALGO теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antizalgo_off": (
            "<emoji document_id=5213293263083018856>🌀</emoji> <b>AntiZALGO теперь"
            " выключен в этом чате</b>"
        ),
        "antistick_on": (
            "<emoji document_id=5431456208487716895>🎨</emoji> <b>AntiStick теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antistick_off": (
            "<emoji document_id=5431456208487716895>🎨</emoji> <b>AntiStick теперь"
            " выключен в этом чате</b>"
        ),
        "antihelp_on": (
            "<emoji document_id=5467759840463953770>🐺</emoji> <b>AntiHelp теперь"
            " включен в этом чате</b>"
        ),
        "antihelp_off": (
            "<emoji document_id=5467759840463953770>🐺</emoji> <b>AntiHelp теперь"
            " выключен в этом чате</b>"
        ),
        "antiraid_on": (
            "<emoji document_id=6334359218593728345><emoji"
            " document_id=6037460928423791421>🚪</emoji></emoji> <b>AntiRaid теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antiraid_off": (
            "<emoji document_id=6334359218593728345><emoji"
            " document_id=6037460928423791421>🚪</emoji></emoji> <b>AntiRaid теперь"
            " выключен в этом чате</b>"
        ),
        "bnd_on": (
            "<emoji document_id=5465300082628763143>💬</emoji> <b>Block-Non-Discussion"
            " теперь включен в этом чате\nДействие: {}</b>"
        ),
        "bnd_off": (
            "<emoji document_id=5465300082628763143>💬</emoji> <b>Block-Non-Discussion"
            " теперь выключен в этом чате</b>"
        ),
        "antichannel_on": (
            "<emoji document_id=5470094069289984325>📯</emoji> <b>AntiChannel теперь"
            " включен в этом чате</b>"
        ),
        "antichannel_off": (
            "<emoji document_id=5470094069289984325>📯</emoji> <b>AntiChannel теперь"
            " выключен в этом чате</b>"
        ),
        "report_on": (
            "<emoji document_id=5213203794619277246>📣</emoji> <b>Report теперь включен"
            " в этом чате</b>"
        ),
        "report_off": (
            "<emoji document_id=5213203794619277246>📣</emoji> <b>Report теперь"
            " выключен"
            " в этом чате</b>"
        ),
        "antiflood_on": (
            "<emoji document_id=5384611567125928766>⏱</emoji> <b>AntiFlood теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antiflood_off": (
            "<emoji document_id=5384611567125928766>⏱</emoji> <b>AntiFlood теперь"
            " выключен в этом чате</b>"
        ),
        "antispoiler_on": (
            "<emoji document_id=5798648862591684122>👻</emoji> <b>AntiSpoiler теперь"
            " включен в этом чате</b>"
        ),
        "antispoiler_off": (
            "<emoji document_id=5798648862591684122>👻</emoji> <b>AntiSpoiler теперь"
            " выключен в этом чате</b>"
        ),
        "antigif_on": (
            "<emoji document_id=6048825205730577727>🎑</emoji> <b>AntiGIF теперь"
            " включен"
            " в этом чате</b>"
        ),
        "antigif_off": (
            "<emoji document_id=6048825205730577727>🎑</emoji> <b>AntiGIF теперь"
            " выключен в этом чате</b>"
        ),
        "antiservice_on": (
            "<emoji document_id=5787237370709413702>⚙️</emoji> <b>AntiService теперь"
            " включен в этом чате</b>"
        ),
        "antiservice_off": (
            "<emoji document_id=5787237370709413702>⚙️</emoji> <b>AntiService теперь"
            " выключен в этом чате</b>"
        ),
        "banninja_on": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja теперь"
            " включен в этом чате</b>"
        ),
        "banninja_off": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja теперь"
            " выключен в этом чате</b>"
        ),
        "antiexplicit_on": (
            "<emoji document_id=5373123633415723713>🤬</emoji> <b>AntiExplicit теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antiexplicit_off": (
            "<emoji document_id=5373123633415723713>🤬</emoji> <b>AntiExplicit теперь"
            " выключен в этом чате</b>"
        ),
        "antinsfw_on": (
            "<emoji document_id=4976982981341086273>🔞</emoji> <b>AntiNSFW теперь"
            " включен в этом чате\nДействие: {}</b>"
        ),
        "antinsfw_off": (
            "<emoji document_id=4976982981341086273>🔞</emoji> <b>AntiNSFW теперь"
            " выключен в этом чате</b>"
        ),
        "captcha_on": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b>Captcha теперь"
            " включена в этом чате\nДействие: {}</b>"
        ),
        "captcha_off": (
            "<emoji document_id=5213107179329953547>🚥</emoji> <b>Captcha теперь"
            " выключена в этом чате</b>"
        ),
        "no_fed_warns": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>This federation has"
            " no warns yet</b>"
        ),
        "warns_adm_fed": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>Warns in this"
            " federation</b>:\n"
        ),
        "welcome": (
            "<emoji document_id=5472055112702629499>👋</emoji> <b>Теперь я буду"
            " приветствовать людей в этом чате</b>\n{}"
        ),
        "unwelcome": (
            "<emoji document_id=5472055112702629499>👋</emoji> <b>Я больше не буду"
            " приветствовать людей в этом чате</b>"
        ),
        "chat404": "🔓 <b>Этот чат еще не защищен.</b>\n",
        "not_admin": "🤷‍♂️ <b>Я здесь не админ, или у меня недостаточно прав</b>",
        "no_defense": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>Федеративный список"
            " защиты пуст</b>"
        ),
        "defense_list": (
            "<emoji document_id=5300855732009180995>🛡</emoji> <b>Федеративный список"
            " защиты:</b>\n{}"
        ),
        "fed404": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федерация не"
            " найдена</b>"
        ),
        "fedexists": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федерация"
            " существует</b>"
        ),
        "joinfed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Присоединился к"
            " федерации</b>"
        ),
        "namedfed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федерация"
            " переименована в {}</b>"
        ),
        "nofed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Этот чат не находится"
            " ни в одной из федераций</b>"
        ),
        "feds_header": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федерации:</b>\n\n"
        ),
        "no_fed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Этот чат не находится"
            " ни в одной из федераций</b>"
        ),
        "api_error": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Ошибка"
            " api.hikariatama.ru!</b>\n<code>{}</code>"
        ),
        "fsave_args": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Пример: .fsave"
            " shortname &lt;reply&gt;</b>"
        ),
        "fstop_args": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Пример: .fstop"
            " shortname</b>"
        ),
        "fsave": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федеративная заметка"
            " </b><code>{}</code><b> сохранена!</b>"
        ),
        "fstop": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федеративная заметка"
            " </b><code>{}</code><b> удалена!</b>"
        ),
        "fnotes": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федеративные"
            " заметки:</b>\n{}"
        ),
        "usage": "ℹ️ <b>Пример: .{} &lt;on/off&gt;</b>",
        "chat_only": "ℹ️ <b>Эта команда предназначена для чатов</b>",
        "no_federations": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Нет активных"
            " федераций</b>"
        ),
        "clrallwarns_fed": (
            "<emoji document_id=5193091781327068499>👮‍♀️</emoji> <b>Прощены все"
            " предупреждения в федерации</b>"
        ),
        "cleaning": (
            "<emoji document_id=5215493819641895305>🫥</emoji> <b>Поиск удаленных"
            " аккаунтов...</b>"
        ),
        "deleted": (
            "<emoji document_id=5215493819641895305>🫥</emoji> <b>Удалено {} удаленных"
            " аккаунтов</b>"
        ),
        "fcleaning": (
            "<emoji document_id=5215493819641895305>🫥</emoji> <b>Поиск удаленных"
            " аккаунтов в федерации...</b>"
        ),
        "btn_unban": "🔓 Разбанить (админ)",
        "btn_unmute": "🔈 Размутить (админ)",
        "btn_unwarn": "♻️ Удалить предупреждение (админ)",
        "btn_funmute": "🔈 Размутить в федерации (админ)",
        "btn_funban": "🔓 Разбанить в федерации (админ)",
        "btn_mute": "🙊 Мут",
        "btn_ban": "🔒 Бан",
        "btn_fban": "💼 Фед. бан",
        "btn_del": "🗑 Удалить",
        "sync": (
            "🔄 <b>Принудительная синхронизация федераций и чатов с сервером...</b>"
        ),
        "sync_complete": "😌 <b>Сихнронизирован</b>",
        "rename_noargs": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Укажи имя"
            " федерации</b>"
        ),
        "suffix_removed": "📼 <b>Суффикс предупреждения удален</b>",
        "suffix_updated": "📼 <b>Установлен новый суффикс предупреждения</b>\n\n{}",
        "processing_myrights": "😌 <b>Обработка чатов</b>",
        "logchat_removed": "📲 <b>Логирование отключено</b>",
        "logchat_invalid": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Неверный чат"
            " логирования</b>"
        ),
        "logchat_set": "📲 <b>Чат логирования установлен на </b><code>{}</code>",
        "clnraid_args": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>Пример:"
            " </b><code>.clnraid 10</code>"
        ),
        "clnraid_admin": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>Ошибка выдачи прав"
            " боту. Убедись, что у тебя достаточно прав</b>"
        ),
        "clnraid_started": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>RaidCleaner"
            " активен..."
            " Найдено {} пользователей для бана...</b>"
        ),
        "clnraid_confirm": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>Подтвердите запуск"
            " RaidCleaner на {} пользователях</b>"
        ),
        "clnraid_yes": "<emoji document_id=6323575131239089635>🥷</emoji> Начать",
        "banninja_report": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>BanNinja закончил"
            " работу.</b>\n<i>Удалено {} бот(-ов)</i>\n\n🏹 <i>«BanNinja can handle any"
            " size of attack»</i> © <code>@hikariatama</code>"
        ),
        "clnraid_cancel": "🔻 Отмена",
        "clnraid_stop": "🚨 Остановить",
        "clnraid_complete": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>RaidCleaner закончил"
            " работу! Удалено: {} бот(-ов)</b>"
        ),
        "clnraid_cancelled": (
            "<emoji document_id=6323575131239089635>🥷</emoji> <b>RaidCleaner"
            " остановлен. Удалено: {} бот(-ов)</b>"
        ),
        "confirm_rmfed_btn": "🗑 Удалить",
        "decline_rmfed_btn": "🔻 Отмена",
        "pil_unavailable": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Библиотека Pillow"
            " недоступна</b>"
        ),
        "_cmd_doc_version": "Получить информацию о модуле",
        "_cmd_doc_deleted": "Очистка удалнных аккаунтов в чате",
        "_cmd_doc_fclean": "Очистка удаленных аккаунтов в федерации",
        "_cmd_doc_newfed": "<shortname> <имя> - Создать новую федерацию",
        "_cmd_doc_rmfed": "<shortname> - Удалить федерацию",
        "_cmd_doc_fpromote": "<пользователь> - Выдать пользователю права в федерации",
        "_cmd_doc_fdemote": (
            "<shortname> <пользователь> - Забрать у пользователя права в федерации"
        ),
        "_cmd_doc_fadd": "<федерация> - Добавить чат в федерацию",
        "_cmd_doc_frm": "Удалить чат из федерации",
        "_cmd_doc_fban": "<пользователь> [причина] - Забанить пользователя в федерации",
        "_cmd_doc_punishsuff": "Установить новый суффикс наказания",
        "_cmd_doc_sethclog": "Установить чат логирования",
        "_cmd_doc_funban": (
            "<пользователь> [причина] - Разбанить пользователя в федерации"
        ),
        "_cmd_doc_fmute": (
            "<пользователь> [причина] - Замутить пользователя в федерации"
        ),
        "_cmd_doc_funmute": (
            "<пользователь> [причина] - Разбанить пользователя в федерации"
        ),
        "_cmd_doc_kick": "<пользователь> [причина] - Кикнуть пользователя",
        "_cmd_doc_ban": "<пользователь> [причина] - Забанить пользователя",
        "_cmd_doc_mute": "<пользователь> [время] [причина] - Замутить пользователя",
        "_cmd_doc_unmute": "<пользователь> - Размутить пользователя",
        "_cmd_doc_unban": "<пользователь> - Разбанить пользователя",
        "_cmd_doc_protects": "Показать доступные защиты",
        "_cmd_doc_feds": "Показать федерации",
        "_cmd_doc_fed": "<shortname> - Информация о федерации",
        "_cmd_doc_pchat": "Показать защиты в чате",
        "_cmd_doc_warn": "<пользователь> - Предупредить пользователя",
        "_cmd_doc_warns": (
            "[пользователь] - Показать предупреждения в чате \\ у пользователя"
        ),
        "_cmd_doc_delwarn": "<пользователь> - Простить последнее предупреждение",
        "_cmd_doc_clrwarns": (
            "<пользователь> - Простить все предупреждения пользователя"
        ),
        "_cmd_doc_clrallwarns": "Простить все предупреждения в федерации",
        "_cmd_doc_welcome": "<text> - Изменить текст приветствовия",
        "_cmd_doc_fdef": (
            "<пользователь> - Включить\\выключить федеративную защиту пользователя"
        ),
        "_cmd_doc_fsave": "<note name> <reply> - Сохранить федеративную заметку",
        "_cmd_doc_fstop": "<note name> - Удалить федеративную заметку",
        "_cmd_doc_fnotes": "Показать федеративные заметки",
        "_cmd_doc_fdeflist": "Показать федеративный список защиты",
        "_cmd_doc_dmute": "Удалить и замутить",
        "_cmd_doc_dban": "Удалить и забанить",
        "_cmd_doc_dwarn": "Удалить и предупредить",
        "_cmd_doc_fsync": "Принудительная синхронизация федераций и чатов с сервером",
        "_cmd_doc_frename": "Переименовать федерацию",
        "_cmd_doc_myrights": "Показать все права администратора во всех чатах",
        "action": "<действие>",
        "configure": "Настроить",
        "toggle": "Включить\\выключить",
        "fed": (
            "<emoji document_id=5773781976905421370>💼</emoji> <b>Федерация"
            ' "{}":</b>\n🔰'
            " <b>Чаты:</b>\n<b>{}</b>\n🔰 <b>Каналы:</b>\n<b>{}</b>\n🔰"
            " <b>Админы:</b>\n<b>{}</b>\n🔰 <b>Предупреждения: {}</b>\n"
        ),
        "confirm_rmfed": (
            "⚠️ <b>Внимание! Это действие нельзя отменить! Ты уверен, что хочешь"
            " удалить федерацию </b><code>{}</code><b>?</b>"
        ),
        "_cls_doc": "Must-have модуль администратора чата",
        "no_notes": (
            "<emoji document_id=5300759756669984376>🚫</emoji> <b>Нет заметок</b>"
        ),
    }

    def __init__(self):
        self._punish_queue = []
        self._raid_cleaners = []
        self._global_queue = []
        self._captcha_db = {}
        self._captcha_messages = {}
        self._ban_ninja = {}
        self._ban_ninja_messages = []
        self._ban_ninja_forms = {}
        self._ban_ninja_progress = {}
        self._ban_ninja_tasks = {}
        self._ban_ninja_default_rights = {}
        self.flood_timeout = FLOOD_TIMEOUT
        self.flood_threshold = FLOOD_TRESHOLD
        self._my_protects = {}
        self._linked_channels = {}
        self._sticks_ratelimit = {}
        self._flood_fw_protection = {}
        self._ratelimit = {"notes": {}, "report": {}}
        self._delete_soon = []
        self._gban_cache = {}

        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "silent",
                False,
                lambda: "Do not notify about protections actions",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "join_ratelimit",
                10,
                lambda: (
                    "How many users per minute need to join until BanNinja activates"
                ),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "banninja_cooldown",
                300,
                lambda: "How long is BanNinja supposed to be active in seconds",
                validator=loader.validators.Integer(minimum=15),
            ),
            loader.ConfigValue(
                "warns_limit",
                7,
                lambda: "How many warns can be issued before ban",
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "close_on_raid",
                True,
                lambda: "Close chat on raid with active BanNinja",
                validator=loader.validators.Boolean(),
            ),
        )

    def render_table(self, t: typing.List[typing.List[str]]) -> bytes:
        table = gen_table(t)

        fnt = ImageFont.truetype(io.BytesIO(self.font), 20, encoding="utf-8")

        def get_t_size(text, fnt):
            if "\n" not in text:
                return fnt.getsize(text)

            w, h = 0, 0

            for line in text.split("\n"):
                line_size = fnt.getsize(line)
                if line_size[0] > w:
                    w = line_size[0]

                h += line_size[1]

            w += 10
            h += 10
            return (w, h)

        t_size = get_t_size(table, fnt)
        img = Image.new("RGB", t_size, (30, 30, 30))

        d = ImageDraw.Draw(img)
        d.text((5, 5), table, font=fnt, fill=(200, 200, 200))

        imgByteArr = io.BytesIO()
        img.save(imgByteArr, format="PNG")
        imgByteArr = imgByteArr.getvalue()

        return imgByteArr

    async def on_unload(self):
        with contextlib.suppress(Exception):
            self.api._task.cancel()

        with contextlib.suppress(Exception):
            self._pt_task.cancel()

        with contextlib.suppress(Exception):
            self.api._processor_task.cancel()

        with contextlib.suppress(Exception):
            for _, form in self._ban_ninja_forms.items():
                with contextlib.suppress(Exception):
                    await form.delete()

    def lookup(self, modname: str):
        return next(
            (
                mod
                for mod in self.allmodules.modules
                if mod.name.lower() == modname.lower()
            ),
            False,
        )

    async def check_admin(
        self,
        chat_id: typing.Union[Chat, Channel, int],
        user_id: typing.Union[User, int],
    ) -> bool:
        """
        Checks if user is admin in target chat
        """
        try:
            return (await self._client.get_permissions(chat_id, user_id)).is_admin
            # We could've ignored only ValueError to check
            # entity for validity, but there are many errors
            # possible to occur, so we ignore all of them, bc
            # actually we don't give a fuck about 'em
        except Exception:
            return (
                user_id in self._client.dispatcher.security._owner
                or user_id in self._client.dispatcher.security._sudo
            )

    def chat_command(function) -> FunctionType:
        """
        Decorator to allow execution of certain commands in chat only
        """

        @functools.wraps(function)
        async def wrapped(*args, **kwargs):
            if len(args) < 2 or not isinstance(args[1], Message):
                return await function(*args, **kwargs)

            if args[1].is_private:
                await utils.answer(args[1], args[0].strings("chat_only"))
                return

            return await function(*args, **kwargs)

        wrapped.__doc__ = function.__doc__
        wrapped.__module__ = function.__module__

        return wrapped

    def error_handler(function) -> FunctionType:
        """
        Decorator to handle functions' errors
        """

        @functools.wraps(function)
        async def wrapped(*args, **kwargs):
            try:
                return await function(*args, **kwargs)
            except Exception:
                logger.exception("Exception caught in HikariChat")

                if function.__name__.startswith("p__"):
                    return

                if function.__name__ == "watcher":
                    return

        wrapped.__doc__ = function.__doc__
        wrapped.__module__ = function.__module__

        return wrapped

    async def get_config(self, chat: typing.Union[str, int]) -> tuple:
        info = self.api.chats[str(chat)]
        cinfo = await self._client.get_entity(int(chat))

        answer_message = (
            f"🪆 <b>HikariChat protection</b>\n<b>{get_full_name(cinfo)}</b>\n\n"
        )

        protections = {
            key: value
            for key, value in PROTECTS.items()
            if key in self.api.variables["protections"]
        }

        btns = []
        for protection, style in protections.items():
            answer_message += (
                f"    <b>{style}</b>: {info[protection][0]}\n"
                if protection in info
                else ""
            )
            style = style if protection in info else style[2:]
            btns += [
                {
                    "text": style,
                    "callback": self._change_protection_state,
                    "args": (chat, protection),
                }
            ]

        fed = None
        for info in self.api.feds.values():
            if str(chat) in info["chats"]:
                fed = info

        answer_message += (
            f"\n<emoji document_id=5773781976905421370>💼</emoji> <b>{fed['name']}</b>"
            if fed
            else ""
        )

        btns = utils.chunks(btns, 3) + [[{"text": "❌ Close", "action": "close"}]]

        return {"text": answer_message, "reply_markup": btns}

    async def _inline_config(self, call: CallbackQuery, chat: typing.Union[str, int]):
        await call.edit(**(await self.get_config(chat)))

    async def _change_protection_state(
        self,
        call: CallbackQuery,
        chat: typing.Union[str, int],
        protection: str,
        state: typing.Optional[str] = None,
    ):
        if protection == "welcome":
            await call.answer("Use .welcome to configure this option!", show_alert=True)
            return

        if protection in self.api.variables["argumented_protects"]:
            if state is None:
                cinfo = await self._client.get_entity(int(chat))
                markup = utils.chunks(
                    [
                        {
                            "text": "🔒 Ban",
                            "callback": self._change_protection_state,
                            "args": (chat, protection, "ban"),
                        },
                        {
                            "text": "🙊 Mute",
                            "callback": self._change_protection_state,
                            "args": (chat, protection, "mute"),
                        },
                        {
                            "text": "🤕 Warn",
                            "callback": self._change_protection_state,
                            "args": (chat, protection, "warn"),
                        },
                        {
                            "text": "🚪 Kick",
                            "callback": self._change_protection_state,
                            "args": (chat, protection, "kick"),
                        },
                        {
                            "text": "😶‍🌫️ Delmsg",
                            "callback": self._change_protection_state,
                            "args": (chat, protection, "delmsg"),
                        },
                        {
                            "text": "🚫 Off",
                            "callback": self._change_protection_state,
                            "args": (chat, protection, "off"),
                        },
                    ],
                    3,
                ) + [
                    [
                        {
                            "text": "🔙 Back",
                            "callback": self._inline_config,
                            "args": (chat,),
                        }
                    ]
                ]
                current_state = (
                    "off"
                    if protection not in self.api.chats[str(chat)]
                    else self.api.chats[str(chat)][protection][0]
                )
                await call.edit(
                    (
                        f"🌁 <b>{get_full_name(cinfo)}</b>:"
                        f" <code>{PROTECTS[protection]}</code> (now: {current_state})"
                    ),
                    reply_markup=markup,
                )
            else:
                self.api.request(
                    {
                        "action": "update protections",
                        "args": {
                            "chat": chat,
                            "protection": protection,
                            "state": state,
                        },
                    }
                )
                await call.answer("Configuration value saved")
                if state != "off":
                    self.api.chats[str(chat)][protection] = [state, str(self._tg_id)]
                else:
                    del self.api.chats[str(chat)][protection]

                await self._inline_config(call, chat)
        else:
            current_state = protection in self.api.chats[str(chat)]
            self.api.request(
                {
                    "action": "update protections",
                    "args": {
                        "chat": chat,
                        "protection": protection,
                        "state": "off" if current_state else "on",
                    },
                }
            )

            await call.answer(
                f"{PROTECTS[protection]} -> {'off' if current_state else 'on'}"
            )

            if current_state:
                del self.api.chats[str(chat)][protection]
            else:
                self.api.chats[str(chat)][protection] = ["on", str(self._tg_id)]
            await self._inline_config(call, chat)

    @error_handler
    async def protect(self, message: Message, protection: str):
        """
        Protection toggle handler
        """
        args = utils.get_args_raw(message)
        chat = utils.get_chat_id(message)

        await self._promote_bot(chat)

        if protection in self.api.variables["argumented_protects"]:
            if args not in self.api.variables["protect_actions"] or args == "off":
                args = "off"
                await utils.answer(message, self.strings(f"{protection}_off"))
            else:
                await utils.answer(
                    message,
                    self.strings(f"{protection}_on").format(args),
                )
        elif args == "on":
            await utils.answer(message, self.strings(f"{protection}_on"))
        elif args == "off":
            await utils.answer(
                message,
                self.strings(f"{protection}_off").format(args),
            )
        else:
            await utils.answer(message, self.strings("usage").format(protection))
            return

        self.api.request(
            {
                "action": "update protections",
                "args": {"protection": protection, "state": args, "chat": chat},
            },
            message,
        )

    def protection_template(self, protection: str) -> FunctionType:
        """
        Template for protection toggler
        For internal use only
        """
        comments = self.api.variables["named_protects"]
        func_name = f"{protection}cmd"
        function = functools.partial(self.protect, protection=protection)
        function.__module__ = self.__module__
        function.__name__ = func_name
        function.__self__ = self

        args = (
            self.strings("action")
            if protection in self.api.variables["argumented_protects"]
            else "<on/off>"
        )

        action = (
            self.strings("configure")
            if protection in self.api.variables["argumented_protects"]
            else self.strings("toggle")
        )

        function.__doc__ = f"{args} - {action} {comments[protection]}"
        return function

    @staticmethod
    def convert_time(t: str) -> int:
        """
        Tries to export time from text
        """
        try:
            if not str(t)[:-1].isdigit():
                return 0

            if "d" in str(t):
                t = int(t[:-1]) * 60 * 60 * 24

            if "h" in str(t):
                t = int(t[:-1]) * 60 * 60

            if "m" in str(t):
                t = int(t[:-1]) * 60

            if "s" in str(t):
                t = int(t[:-1])

            t = int(re.sub(r"[^0-9]", "", str(t)))
        except ValueError:
            return 0

        return t

    async def ban(
        self,
        chat: typing.Union[Chat, int],
        user: typing.Union[User, Channel, int],
        period: int = 0,
        reason: str = None,
        message: typing.Optional[Message] = None,
        silent: bool = False,
    ):
        """Ban user in chat"""
        if str(user).isdigit():
            user = int(user)

        if reason is None:
            reason = self.strings("no_reason")

        try:
            await self.inline.bot.kick_chat_member(
                int(f"-100{getattr(chat, 'id', chat)}"),
                int(getattr(user, "id", user)),
            )
        except Exception:
            logger.debug("Can't ban with bot", exc_info=True)

            await self._client.edit_permissions(
                chat,
                user,
                until_date=(time.time() + period) if period else 0,
                **BANNED_RIGHTS,
            )

        if silent:
            return

        msg = self.strings("ban").format(
            utils.get_link(user),
            get_full_name(user),
            f"for {period // 60} min(-s)" if period else "forever",
            reason,
            self.get("punish_suffix", ""),
        )

        if self._is_inline:
            if self.get("logchat"):
                if not isinstance(chat, (Chat, Channel)):
                    chat = await self._client.get_entity(chat)

                await self.inline.form(
                    message=self.get("logchat"),
                    text=self.strings("ban_log").format(
                        utils.get_link(user),
                        get_full_name(user),
                        f"for {period // 60} min(-s)" if period else "forever",
                        utils.get_link(chat),
                        get_full_name(chat),
                        reason,
                        "",
                    ),
                    reply_markup={
                        "text": self.strings("btn_unban"),
                        "data": (
                            f"ub/{chat.id if isinstance(chat, (Chat, Channel)) else chat}/{user.id}"
                        ),
                    },
                    silent=True,
                )

                if isinstance(message, Message):
                    await utils.answer(message, msg)
                else:
                    await self._client.send_message(chat.id, msg)
            else:
                await self.inline.form(
                    message=(
                        message
                        if isinstance(message, Message)
                        else getattr(chat, "id", chat)
                    ),
                    text=msg,
                    reply_markup={
                        "text": self.strings("btn_unban"),
                        "data": (
                            f"ub/{chat.id if isinstance(chat, (Chat, Channel)) else chat}/{user.id}"
                        ),
                    },
                    silent=True,
                )
        else:
            await (utils.answer if message else self._client.send_message)(
                message or chat.id, msg
            )

    async def mute(
        self,
        chat: typing.Union[Chat, int],
        user: typing.Union[User, Channel, int],
        period: int = 0,
        reason: str = None,
        message: typing.Optional[Message] = None,
        silent: bool = False,
    ):
        """Mute user in chat"""
        if str(user).isdigit():
            user = int(user)

        if reason is None:
            reason = self.strings("no_reason")

        try:
            await self.inline.bot.restrict_chat_member(
                int(f"-100{getattr(chat, 'id', chat)}"),
                int(getattr(user, "id", user)),
                permissions=ChatPermissions(can_send_messages=False),
                until_date=time.time() + period,
            )
        except Exception:
            logger.debug("Can't mute with bot", exc_info=True)

            await self._client.edit_permissions(
                chat,
                user,
                until_date=time.time() + period,
                send_messages=False,
            )

        if silent:
            return

        msg = self.strings("mute").format(
            utils.get_link(user),
            get_full_name(user),
            f"for {period // 60} min(-s)" if period else "forever",
            reason,
            self.get("punish_suffix", ""),
        )

        if self._is_inline:
            if self.get("logchat"):
                if not isinstance(chat, (Chat, Channel)):
                    chat = await self._client.get_entity(chat)

                await self.inline.form(
                    message=self.get("logchat"),
                    text=self.strings("mute_log").format(
                        utils.get_link(user),
                        get_full_name(user),
                        f"for {period // 60} min(-s)" if period else "forever",
                        utils.get_link(chat),
                        get_full_name(chat),
                        reason,
                        "",
                    ),
                    reply_markup={
                        "text": self.strings("btn_unmute"),
                        "data": (
                            f"um/{chat.id if isinstance(chat, (Chat, Channel)) else chat}/{user.id}"
                        ),
                    },
                    silent=True,
                )

                if isinstance(message, Message):
                    await utils.answer(message, msg)
                else:
                    await self._client.send_message(chat.id, msg)
            else:
                await self.inline.form(
                    message=(
                        message
                        if isinstance(message, Message)
                        else getattr(chat, "id", chat)
                    ),
                    text=msg,
                    reply_markup={
                        "text": self.strings("btn_unmute"),
                        "data": (
                            f"um/{chat.id if isinstance(chat, (Chat, Channel)) else chat}/{user.id}"
                        ),
                    },
                    silent=True,
                )
        else:
            await (utils.answer if message else self._client.send_message)(
                message or chat.id, msg
            )

    @loader.inline_everyone
    async def actions_callback_handler(self, call: CallbackQuery):
        """
        Handles unmute, unban, unwarn etc. button clicks
        """
        if not re.match(r"[fbmudw]{1,3}\/[-0-9]+\/[-#0-9]+", call.data):
            return

        action, chat, user = call.data.split("/")

        msg_id = None

        try:
            user, msg_id = user.split("#")
            msg_id = int(msg_id)
        except Exception:
            pass

        chat, user = int(chat), int(user)

        if not await self.check_admin(chat, call.from_user.id):
            await call.answer("You are not admin")
            return

        try:
            user = await self._client.get_entity(user)
        except Exception:
            await call.answer("Unable to resolve entity")
            return

        try:
            adm = await self._client.get_entity(call.from_user.id)
        except Exception:
            await call.answer("Unable to resolve admin entity")
            return

        p = (
            await self._client(GetParticipantRequest(chat, call.from_user.id))
        ).participant

        owner = isinstance(p, ChannelParticipantCreator)

        if action == "ub":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            await self._client.edit_permissions(
                chat,
                user,
                until_date=0,
                **{right: True for right in BANNED_RIGHTS.keys()},
            )
            msg = self.strings("inline_unbanned").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )
            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "um":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            await self._client.edit_permissions(
                chat,
                user,
                until_date=0,
                send_messages=True,
            )
            msg = self.strings("inline_unmuted").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )
            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "dw":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            fed = await self.find_fed(chat)

            self.api.request(
                {
                    "action": "forgive user warn",
                    "args": {"uid": self.api.feds[fed]["uid"], "user": user.id},
                }
            )

            msg = self.strings("inline_unwarned").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )

            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "ufb":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            m = await self._client.send_message(
                chat, f"{self.get_prefix()}funban {user.id}"
            )
            await self.funbancmd(m)
            await m.delete()
            msg = self.strings("inline_funbanned").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )
            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "ufm":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            m = await self._client.send_message(
                chat, f"{self.get_prefix()}funmute {user.id}"
            )
            await self.funmutecmd(m)
            await m.delete()
            msg = self.strings("inline_funmuted").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )
            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "fb":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            m = await self._client.send_message(
                chat, f"{self.get_prefix()}fban {user.id}"
            )
            await self.fbancmd(m)
            await m.delete()
            msg = self.strings("inline_fbanned").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )
            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "m":
            if not owner and not p.admin_rights.ban_users:
                await call.answer("Not enough rights!")
                return

            await self.mute(chat, user, 0, silent=True)
            msg = self.strings("inline_muted").format(
                utils.get_link(user),
                get_full_name(user),
                utils.get_link(adm),
                get_full_name(adm),
            )
            try:
                await self.inline.bot.edit_message_text(
                    msg,
                    inline_message_id=call.inline_message_id,
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                )
            except Exception:
                await self._client.send_message(chat, msg)
        elif action == "d":
            if not owner and not p.admin_rights.delete_messages:
                await call.answer("Not enough rights!")
                return

            msg = self.strings("inline_deleted").format(
                utils.get_link(adm),
                get_full_name(adm),
            )

            await self.inline.bot.edit_message_text(
                msg,
                inline_message_id=call.inline_message_id,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
        else:
            return

        if msg_id is not None:
            await self._client.delete_messages(chat, message_ids=[msg_id])

    async def args_parser(
        self,
        message: Message,
        include_force: bool = False,
        include_silent: bool = False,
    ) -> tuple:
        """Get args from message"""
        args = " " + utils.get_args_raw(message)
        if include_force and " -f" in args:
            force = True
            args = args.replace(" -f", "")
        else:
            force = False

        if include_silent and " -s" in args:
            silent = True
            args = args.replace(" -s", "")
        else:
            silent = False

        args = args.strip()

        reply = await message.get_reply_message()

        if reply and not args:
            return (
                (await self._client.get_entity(reply.sender_id)),
                0,
                utils.escape_html(self.strings("no_reason")).strip(),
                *((force,) if include_force else []),
                *((silent,) if include_silent else []),
            )

        try:
            a = args.split()[0]
            if str(a).isdigit():
                a = int(a)
            user = await self._client.get_entity(a)
        except Exception:
            try:
                user = await self._client.get_entity(reply.sender_id)
            except Exception:
                return False

        t = ([arg for arg in args.split() if self.convert_time(arg)] or ["0"])[0]
        args = args.replace(t, "").replace("  ", " ")
        t = self.convert_time(t)

        if not reply:
            try:
                args = " ".join(args.split()[1:])
            except Exception:
                pass

        if time.time() + t >= 2208978000:  # 01.01.2040 00:00:00
            t = 0

        return (
            user,
            t,
            utils.escape_html(args or self.strings("no_reason")).strip(),
            *((force,) if include_force else []),
            *((silent,) if include_silent else []),
        )

    async def find_fed(self, message: typing.Union[Message, int]) -> str:
        """Find if chat belongs to any federation"""
        return next(
            (
                federation
                for federation, info in self.api.feds.items()
                if str(
                    utils.get_chat_id(message)
                    if isinstance(message, Message)
                    else message
                )
                in list(map(str, info["chats"]))
            ),
            None,
        )

    @error_handler
    async def punish(
        self,
        chat_id: int,
        user: typing.Union[int, Channel, User],
        violation: str,
        action: str,
        user_name: str,
        fulltime: bool = False,
        message: Message = None,
    ):
        """
        Callback, called if the protection is triggered
        Queue is being used to prevent spammy behavior
        It is being processed in a loop `_punish_queue_handler`
        """
        self._punish_queue += [
            [chat_id, user, violation, action, user_name, fulltime, message]
        ]

    @error_handler
    async def purgecmd(self, message: Message):
        """[user(-s)] - Clean message history starting from replied one"""
        if not message.is_reply:
            await utils.answer(message, self.strings("from_where", message))
            return

        from_users = set()
        args = utils.get_args(message)

        for arg in args:
            try:
                entity = await message.client.get_entity(arg)

                if isinstance(entity, User):
                    from_users.add(entity.id)
            except ValueError:
                pass

        messages = []

        async for msg in self._client.iter_messages(
            entity=message.peer_id,
            min_id=message.reply_to_msg_id - 1,
            reverse=True,
        ):
            logger.debug(msg)
            if (not from_users or msg.sender_id in from_users) and (
                not getattr(message.reply_to, "forum_topic", False)
                or msg.reply_to
                and (msg.reply_to.reply_to_top_id or msg.reply_to.reply_to_msg_id)
                == (
                    message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id
                )
            ):
                messages += [msg.id]

                if len(messages) >= 99:
                    await self._client.delete_messages(message.peer_id, messages)
                    messages.clear()

        if messages:
            await self._client.delete_messages(message.peer_id, messages)

    async def delcmd(self, message):
        """Delete the replied message"""
        await self._client.delete_messages(
            message.peer_id,
            [
                (
                    (
                        await self._client.iter_messages(
                            message.peer_id, 1, max_id=message.id
                        ).__anext__()
                    )
                    if not message.is_reply
                    else (await message.get_reply_message())
                ).id,
                message.id,
            ],
        )

    @loader.loop(interval=0.5, autostart=True)
    async def _punish_queue_handler(self):
        while self._punish_queue:
            (
                chat_id,
                user,
                violation,
                action,
                user_name,
                fulltime,
                message,
            ) = self._punish_queue.pop()
            if str(chat_id) not in self._flood_fw_protection:
                self._flood_fw_protection[str(chat_id)] = {}

            if (
                self._flood_fw_protection[str(chat_id)].get(str(user.id), 0)
                >= time.time()
            ):
                continue

            comment = None

            if action == "ban":
                comment = "banned him"
                await self.ban(
                    chat_id,
                    user,
                    0,
                    violation,
                    silent=str(chat_id) in self._ban_ninja or self.config["silent"],
                )
            elif action == "fban":
                comment = "f-banned him"
                await self.fbancmd(
                    await self._client.send_message(
                        chat_id,
                        f"{self.get_prefix()}fban {user.id} {violation}",
                    )
                )
            elif action == "delmsg":
                # Do nothing...
                ...
            elif action == "kick":
                comment = "kicked him"
                await self._client.kick_participant(chat_id, user)
            elif action == "mute":
                if fulltime:
                    comment = "muted him forever"
                    await self.mute(
                        chat_id,
                        user,
                        0,
                        violation,
                        silent=str(chat_id) in self._ban_ninja or self.config["silent"],
                    )
                else:
                    comment = "muted him for 1 hour"
                    await self.mute(
                        chat_id,
                        user,
                        60 * 60,
                        violation,
                        silent=str(chat_id) in self._ban_ninja or self.config["silent"],
                    )
            elif action == "warn":
                comment = "warned him"
                warn_msg = await self._client.send_message(
                    chat_id, f".warn {user.id} {violation}"
                )
                await self.allmodules.commands["warn"](warn_msg)
                await warn_msg.delete()

            if message is not None:
                try:
                    await self.inline.bot.delete_message(
                        int(f"-100{chat_id}"),
                        message.id,
                    )
                except Exception:
                    with contextlib.suppress(Exception):
                        await message.delete()

            if not comment:
                continue

            if str(chat_id) not in self._ban_ninja and not self.config["silent"]:
                self._flood_fw_protection[str(chat_id)][str(user.id)] = round(
                    time.time() + 10
                )
                await self._client.send_message(
                    chat_id,
                    self.strings(violation).format(
                        utils.get_link(user),
                        user_name,
                        comment,
                    ),
                )

    @error_handler
    async def versioncmd(self, message: Message):
        """Get module info"""
        await utils.answer(
            message,
            self.strings("version").format(
                ver,
                (
                    "✅ Connected"
                    if self.api._connected
                    else ("🔁 Connecting..." if self.api._inited else "🗃 Local")
                ),
            ),
        )

    @error_handler
    @chat_command
    async def deletedcmd(self, message: Message):
        """Remove deleted accounts from chat"""
        chat = await message.get_chat()

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        kicked = 0

        message = await utils.answer(message, self.strings("cleaning"))

        async for user in self._client.iter_participants(chat):
            if user.deleted:
                try:
                    await self._client.kick_participant(chat, user)
                    await self._client.edit_permissions(
                        chat,
                        user,
                        until_date=0,
                        **{right: True for right in BANNED_RIGHTS.keys()},
                    )
                    kicked += 1
                except Exception:
                    pass

        await utils.answer(message, self.strings("deleted").format(kicked))

    @error_handler
    @chat_command
    async def fcleancmd(self, message: Message):
        """Remove deleted accounts from federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        chats = self.api.feds[fed]["chats"]
        cleaned_in = []
        cleaned_in_c = []

        message = await utils.answer(message, self.strings("fcleaning"))

        overall = 0

        for c in chats:
            try:
                if str(c).isdigit():
                    c = int(c)
                chat = await self._client.get_entity(c)
            except Exception:
                continue

            if not chat.admin_rights and not chat.creator:
                continue

            try:
                kicked = 0
                async for user in self._client.iter_participants(chat):
                    if user.deleted:
                        try:
                            await self._client.kick_participant(chat, user)
                            await self._client.edit_permissions(
                                chat,
                                user,
                                until_date=0,
                                **{right: True for right in BANNED_RIGHTS.keys()},
                            )
                            kicked += 1
                        except Exception:
                            pass

                overall += kicked
                cleaned_in += [
                    "👥 <a"
                    f' href="{utils.get_link(chat)}">{utils.escape_html(chat.title)}</a>'
                    f" - {kicked}"
                ]
            except UserAdminInvalidError:
                pass

            if str(c) in self._linked_channels and self._linked_channels[str(c)]:
                channel = await self._client.get_entity(self._linked_channels[str(c)])
                kicked = 0
                try:
                    async for user in self._client.iter_participants(
                        self._linked_channels[str(c)]
                    ):
                        if user.deleted:
                            try:
                                await self._client.kick_participant(
                                    self._linked_channels[str(c)],
                                    user,
                                )
                                await self._client.edit_permissions(
                                    self._linked_channels[str(c)],
                                    user,
                                    until_date=0,
                                    **{right: True for right in BANNED_RIGHTS.keys()},
                                )
                                kicked += 1
                            except Exception:
                                pass

                    overall += kicked
                    cleaned_in_c += [
                        "<emoji document_id=5213203794619277246>📣</emoji> <a"
                        f' href="{utils.get_link(channel)}">{utils.escape_html(channel.title)}</a>'
                        f" - {kicked}"
                    ]
                except ChatAdminRequiredError:
                    pass

        await utils.answer(
            message,
            self.strings("deleted").format(overall)
            + "\n\n<b>"
            + "\n".join(cleaned_in)
            + "</b>"
            + "\n\n<b>"
            + "\n".join(cleaned_in_c)
            + "</b>",
        )

    @error_handler
    @chat_command
    async def newfedcmd(self, message: Message):
        """<shortname> <name> - Create new federation"""
        args = utils.get_args_raw(message)
        if not args or args.count(" ") == 0:
            await utils.answer(message, self.strings("args"))
            return

        shortname, name = args.split(maxsplit=1)
        if shortname in self.api.feds:
            await utils.answer(message, self.strings("fedexists"))
            return

        self.api.request(
            {
                "action": "create federation",
                "args": {"shortname": shortname, "name": name},
            },
            message,
        )

        await utils.answer(message, self.strings("newfed").format(name))

    async def inline__confirm_rmfed(self, call: CallbackQuery, args: str):
        name = self.api.feds[args]["name"]

        self.api.request(
            {"action": "delete federation", "args": {"uid": self.api.feds[args]["uid"]}}
        )

        await call.edit(self.strings("rmfed").format(name))

    @error_handler
    @chat_command
    async def rmfedcmd(self, message: Message):
        """<shortname> - Remove federation"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        if args not in self.api.feds:
            await utils.answer(message, self.strings("fed404"))
            return

        await self.inline.form(
            self.strings("confirm_rmfed").format(
                utils.escape_html(self.api.feds[args]["name"])
            ),
            message=message,
            reply_markup=[
                {
                    "text": self.strings("confirm_rmfed_btn"),
                    "callback": self.inline__confirm_rmfed,
                    "args": (args,),
                },
                {
                    "text": self.strings("decline_rmfed_btn"),
                    "action": "close",
                },
            ],
            silent=True,
        )

    @error_handler
    @chat_command
    async def fpromotecmd(self, message: Message):
        """<user> - Promote user in federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        if not reply and not args:
            await utils.answer(message, self.strings("args"))
            return

        user = reply.sender_id if reply else args
        try:
            try:
                if str(user).isdigit():
                    user = int(user)
                obj = await self._client.get_entity(user)
            except Exception:
                await utils.answer(message, self.strings("args"))
                return

            name = get_full_name(obj)
        except Exception:
            await utils.answer(message, self.strings("args"))
            return

        self.api.request(
            {
                "action": "promote user in federation",
                "args": {"uid": self.api.feds[fed]["uid"], "user": obj.id},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("fpromoted").format(
                utils.get_link(obj),
                name,
                self.api.feds[fed]["name"],
            ),
        )

    @error_handler
    @chat_command
    async def fdemotecmd(self, message: Message):
        """<shortname> <reply|user> - Demote user in federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        if not reply and not args:
            await utils.answer(message, self.strings("args"))
            return

        user = reply.sender_id if reply else args
        try:
            try:
                if str(user).isdigit():
                    user = int(user)
                obj = await self._client.get_entity(user)
            except Exception:
                await utils.answer(message, self.strings("args"))
                return

            user = obj.id

            name = get_full_name(obj)
        except Exception:
            logger.exception("Parsing entity exception")
            name = "User"

        self.api.request(
            {
                "action": "demote user in federation",
                "args": {"uid": self.api.feds[fed]["uid"], "user": obj.id},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("fdemoted").format(
                user,
                name,
                self.api.feds[fed]["name"],
            ),
        )

    @error_handler
    @chat_command
    async def faddcmd(self, message: Message):
        """<fed name> - Add chat to federation"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        if args not in self.api.feds:
            await utils.answer(message, self.strings("fed404"))
            return

        chat = utils.get_chat_id(message)

        self.api.request(
            {
                "action": "add chat to federation",
                "args": {"uid": self.api.feds[args]["uid"], "cid": chat},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("fadded").format(
                self.api.feds[args]["name"],
            ),
        )

    @error_handler
    @chat_command
    async def frmcmd(self, message: Message):
        """Remove chat from federation"""
        fed = await self.find_fed(message)
        if not fed:
            await utils.answer(message, self.strings("fed404"))
            return

        chat = utils.get_chat_id(message)

        self.api.request(
            {
                "action": "remove chat from federation",
                "args": {"uid": self.api.feds[fed]["uid"], "cid": chat},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("frem").format(
                self.api.feds[fed]["name"],
            ),
        )

    @loader.command(
        ru_doc=(
            "<реплай | юзер> [причина] [-s] - Заблокировать пользователя во всех чатах,"
            " где ты админ"
        )
    )
    async def gban(self, message: Message):
        """<reply|user> [reason] [-s] - Ban user in all chats where you are admin"""
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        if not reply and not args:
            await utils.answer(message, self.strings("args"))
            return

        a = await self.args_parser(message, include_silent=True)

        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, t, reason, silent = a

        message = await utils.answer(
            message,
            self.strings("gbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ),
        )

        if not self._gban_cache or self._gban_cache["exp"] < time.time():
            self._gban_cache = {
                "exp": int(time.time()) + 10 * 60,
                "chats": [
                    chat.entity.id
                    async for chat in self._client.iter_dialogs()
                    if (
                        (
                            isinstance(chat.entity, Chat)
                            or (
                                isinstance(chat.entity, Channel)
                                and getattr(chat.entity, "megagroup", False)
                            )
                        )
                        and chat.entity.admin_rights
                        and chat.entity.participants_count > 5
                        and chat.entity.admin_rights.ban_users
                    )
                ],
            }

        chats = ""
        counter = 0

        for chat in self._gban_cache["chats"]:
            try:
                await self.ban(chat, user, 0, reason, silent=True)
            except Exception:
                pass
            else:
                chats += '▫️ <b><a href="{}">{}</a></b>\n'.format(
                    utils.get_entity_url(await self._client.get_entity(chat, exp=0)),
                    utils.escape_html(
                        get_full_name(await self._client.get_entity(chat, exp=0))
                    ),
                )
                counter += 1

        await utils.answer(
            message,
            self.strings("gban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                reason,
                self.strings("in_n_chats").format(counter) if silent else chats,
            ),
        )

    @loader.command(
        ru_doc=(
            "<реплай | юзер> [причина] [-s] - Разблокировать пользователя во всех"
            " чатах, где ты админ"
        )
    )
    async def gunban(self, message: Message):
        """<reply|user> [reason] [-s] - Unban user in all chats where you are admin"""
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        if not reply and not args:
            await utils.answer(message, self.strings("args"))
            return

        a = await self.args_parser(message, include_silent=True)

        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, t, reason, silent = a

        message = await utils.answer(
            message,
            self.strings("gunbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ),
        )

        if not self._gban_cache or self._gban_cache["exp"] < time.time():
            self._gban_cache = {
                "exp": int(time.time()) + 10 * 60,
                "chats": [
                    chat.entity.id
                    async for chat in self._client.iter_dialogs()
                    if (
                        (
                            isinstance(chat.entity, Chat)
                            or (
                                isinstance(chat.entity, Channel)
                                and getattr(chat.entity, "megagroup", False)
                            )
                        )
                        and chat.entity.admin_rights
                        and chat.entity.participants_count > 5
                        and chat.entity.admin_rights.ban_users
                    )
                ],
            }

        chats = ""
        counter = 0

        for chat in self._gban_cache["chats"]:
            try:
                await self._client.edit_permissions(
                    chat,
                    user,
                    until_date=0,
                    **{right: True for right in BANNED_RIGHTS.keys()},
                )
            except Exception:
                pass
            else:
                chats += '▫️ <b><a href="{}">{}</a></b>\n'.format(
                    utils.get_entity_url(await self._client.get_entity(chat, exp=0)),
                    utils.escape_html(
                        get_full_name(await self._client.get_entity(chat, exp=0))
                    ),
                )
                counter += 1

        await utils.answer(
            message,
            self.strings("gunban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                (
                    self.strings("unbanned_in_n_chats").format(counter)
                    if silent
                    else chats
                ),
            ),
        )

    @error_handler
    @chat_command
    async def fbancmd(self, message: Message):
        """<reply | user> [reason] - Ban user in federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        a = await self.args_parser(message, include_force=True)

        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, t, reason, force = a

        if not force and user.id in list(map(int, self.api.feds[fed]["fdef"])):
            await utils.answer(message, self.strings("fdef403").format("fban"))
            return

        chats = self.api.feds[fed]["chats"]

        banned_in = []

        for c in chats:
            try:
                if str(c).isdigit():
                    c = int(c)
                chat = await self._client.get_entity(c)
            except Exception:
                continue

            if not chat.admin_rights and not chat.creator:
                continue

            try:
                await self.ban(chat, user, t, reason, message, silent=True)
                banned_in += [
                    f'<a href="{utils.get_link(chat)}">{get_full_name(chat)}</a>'
                ]
            except Exception:
                pass

        msg = (
            self.strings("fban").format(
                utils.get_link(user),
                get_first_name(user),
                self.api.feds[fed]["name"],
                f"for {t // 60} min(-s)" if t else "forever",
                reason,
                self.get("punish_suffix", ""),
            )
            + "\n\n<b>"
            + "\n".join(banned_in)
            + "</b>"
        )

        if self._is_inline:
            punishment_info = {
                "reply_markup": {
                    "text": self.strings("btn_funban"),
                    "data": f"ufb/{utils.get_chat_id(message)}/{user.id}",
                },
            }

            if self.get("logchat"):
                await utils.answer(message, msg)
                await self.inline.form(
                    text=self.strings("fban").format(
                        utils.get_link(user),
                        get_first_name(user),
                        self.api.feds[fed]["name"],
                        f"for {t // 60} min(-s)" if t else "forever",
                        reason,
                        "",
                    )
                    + "<b>"
                    + "\n".join(banned_in)
                    + "</b>",
                    message=self.get("logchat"),
                    **punishment_info,
                    silent=True,
                )
            else:
                await self.inline.form(
                    text=msg, message=message, **punishment_info, silent=True
                )
        else:
            await utils.answer(message, msg)

        self.api.request(
            {
                "action": "clear all user warns",
                "args": {
                    "uid": self.api.feds[fed]["uid"],
                    "user": user.id,
                    "silent": True,
                },
            },
            message,
        )

        reply = await message.get_reply_message()
        if reply:
            await reply.delete()

    @error_handler
    @chat_command
    async def punishsuffcmd(self, message: Message):
        """Set new punishment suffix"""
        if not utils.get_args_raw(message):
            self.set("punish_suffix", "")
            await utils.answer(message, self.strings("suffix_removed"))
        else:
            suffix = utils.get_args_raw(message)
            self.set("punish_suffix", suffix)
            await utils.answer(message, self.strings("suffix_updated").format(suffix))

    @error_handler
    @chat_command
    async def sethclogcmd(self, message: Message):
        """Set logchat"""
        if not utils.get_args_raw(message):
            self.set("logchat", "")
            await utils.answer(message, self.strings("logchat_removed"))
            return

        logchat = utils.get_args_raw(message)
        if logchat.isdigit():
            logchat = int(logchat)

        try:
            logchat = await self._client.get_entity(logchat)
        except Exception:
            await utils.answer(message, self.strings("logchat_invalid"))
            return

        self.set("logchat", logchat.id)
        await utils.answer(
            message,
            self.strings("logchat_set").format(utils.escape_html(logchat.title)),
        )

    @error_handler
    @chat_command
    async def funbancmd(self, message: Message):
        """<user> [reason] - Unban user in federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        a = await self.args_parser(message)

        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, _, _ = a

        chats = self.api.feds[fed]["chats"]

        unbanned_in = []

        for c in chats:
            try:
                if str(c).isdigit():
                    c = int(c)
                chat = await self._client.get_entity(c)
            except Exception:
                continue

            if not chat.admin_rights and not chat.creator:
                continue

            try:
                await self._client.edit_permissions(
                    chat,
                    user,
                    until_date=0,
                    **{right: True for right in BANNED_RIGHTS.keys()},
                )
                unbanned_in += [chat.title]
            except UserAdminInvalidError:
                pass

        m = (
            self.strings("funban").format(
                utils.get_link(user),
                get_first_name(user),
                self.api.feds[fed]["name"],
            )
            + "<b>"
            + "\n".join(unbanned_in)
            + "</b>"
        )

        if self.get("logchat"):
            await self._client.send_message(self.get("logchat"), m)

        await utils.answer(message, m)

    @error_handler
    @chat_command
    async def fmutecmd(self, message: Message):
        """<reply | user> [reason] - Mute user in federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        a = await self.args_parser(message, include_force=True)

        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, t, reason, force = a

        if not force and user.id in list(map(int, self.api.feds[fed]["fdef"])):
            await utils.answer(message, self.strings("fdef403").format("fmute"))
            return

        chats = self.api.feds[fed]["chats"]

        muted_in = []

        for c in chats:
            try:
                if str(c).isdigit():
                    c = int(c)
                chat = await self._client.get_entity(c)
            except Exception:
                continue

            if not chat.admin_rights and not chat.creator:
                continue

            try:
                await self.mute(chat, user, t, reason, message, silent=True)
                muted_in += [
                    f'<a href="{utils.get_link(chat)}">{get_full_name(chat)}</a>'
                ]
            except Exception:
                pass

        msg = (
            self.strings("fmute").format(
                utils.get_link(user),
                get_first_name(user),
                self.api.feds[fed]["name"],
                f"for {t // 60} min(-s)" if t else "forever",
                reason,
                self.get("punish_suffix", ""),
            )
            + "\n\n<b>"
            + "\n".join(muted_in)
            + "</b>"
        )

        if self._is_inline:
            punishment_info = {
                "reply_markup": {
                    "text": self.strings("btn_funmute"),
                    "data": f"ufm/{utils.get_chat_id(message)}/{user.id}",
                },
            }

            if self.get("logchat"):
                await utils.answer(message, msg)
                await self.inline.form(
                    text=self.strings("fmute").format(
                        utils.get_link(user),
                        get_first_name(user),
                        self.api.feds[fed]["name"],
                        f"for {t // 60} min(-s)" if t else "forever",
                        reason,
                        "",
                    )
                    + "\n\n<b>"
                    + "\n".join(muted_in)
                    + "</b>",
                    message=self.get("logchat"),
                    **punishment_info,
                    silent=True,
                )
            else:
                await self.inline.form(
                    text=msg, message=message, **punishment_info, silent=True
                )
        else:
            await utils.answer(message, msg)

    @error_handler
    @chat_command
    async def funmutecmd(self, message: Message):
        """<user> [reason] - Unban user in federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        a = await self.args_parser(message)

        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, _, _ = a

        chats = self.api.feds[fed]["chats"]

        unbanned_in = []

        for c in chats:
            try:
                if str(c).isdigit():
                    c = int(c)
                chat = await self._client.get_entity(c)
            except Exception:
                continue

            if not chat.admin_rights and not chat.creator:
                continue

            try:
                await self._client.edit_permissions(
                    chat,
                    user,
                    until_date=0,
                    **{right: True for right in BANNED_RIGHTS.keys()},
                )
                unbanned_in += [chat.title]
            except UserAdminInvalidError:
                pass

        msg = (
            self.strings("funmute").format(
                utils.get_link(user),
                get_first_name(user),
                self.api.feds[fed]["name"],
            )
            + "\n\n<b>"
            + "\n".join(unbanned_in)
            + "</b>"
        )

        await utils.answer(message, msg)

        if self.get("logchat"):
            await self._client.send_message(self.get("logchat"), msg)

    @error_handler
    @chat_command
    async def kickcmd(self, message: Message):
        """<user> [reason] - Kick user"""
        chat = await message.get_chat()

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        user, reason = None, None

        try:
            if reply:
                user = await self._client.get_entity(reply.sender_id)
                reason = args or self.strings
            else:
                uid = args.split(maxsplit=1)[0]
                if str(uid).isdigit():
                    uid = int(uid)
                user = await self._client.get_entity(uid)
                reason = (
                    args.split(maxsplit=1)[1]
                    if len(args.split(maxsplit=1)) > 1
                    else self.strings("no_reason")
                )
        except Exception:
            await utils.answer(message, self.strings("args"))
            return

        try:
            await self._client.kick_participant(utils.get_chat_id(message), user)
            msg = self.strings("kick").format(
                utils.get_link(user),
                get_first_name(user),
                reason,
                self.get("punish_suffix", ""),
            )
            await utils.answer(message, msg)

            if self.get("logchat"):
                await self._client.send_message(
                    self.get("logchat"),
                    self.strings("kick_log").format(
                        utils.get_link(user),
                        get_first_name(user),
                        utils.get_link(chat),
                        get_first_name(chat),
                        reason,
                        "",
                    ),
                )
        except UserAdminInvalidError:
            await utils.answer(message, self.strings("not_admin"))
            return

    @error_handler
    @chat_command
    async def bancmd(self, message: Message):
        """<user> [reason] - Ban user"""
        chat = await message.get_chat()

        a = await self.args_parser(message, include_force=True)
        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, t, reason, force = a

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        fed = await self.find_fed(message)
        if (
            not force
            and fed in self.api.feds
            and user.id in list(map(int, self.api.feds[fed]["fdef"]))
        ):
            await utils.answer(message, self.strings("fdef403").format("ban"))
            return

        try:
            await self.ban(chat, user, t, reason, message)
        except UserAdminInvalidError:
            await utils.answer(message, self.strings("not_admin"))
            return

    @error_handler
    @chat_command
    async def mutecmd(self, message: Message):
        """<user> [time] [reason] - Mute user"""
        chat = await message.get_chat()

        a = await self.args_parser(message, include_force=True)
        if not a:
            await utils.answer(message, self.strings("args"))
            return

        user, t, reason, force = a

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        fed = await self.find_fed(message)
        if (
            not force
            and fed in self.api.feds
            and user.id in list(map(int, self.api.feds[fed]["fdef"]))
        ):
            await utils.answer(message, self.strings("fdef403").format("mute"))
            return

        try:
            await self.mute(chat, user, t, reason, message)
        except UserAdminInvalidError:
            await utils.answer(message, self.strings("not_admin"))
            return

    @error_handler
    @chat_command
    async def unmutecmd(self, message: Message):
        """<reply | user> - Unmute user"""
        chat = await message.get_chat()

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        user = None

        try:
            if args.isdigit():
                args = int(args)
            user = await self._client.get_entity(args)
        except Exception:
            try:
                user = await self._client.get_entity(reply.sender_id)
            except Exception:
                await utils.answer(message, self.strings("args"))
                return

        try:
            await self._client.edit_permissions(
                chat,
                user,
                until_date=0,
                send_messages=True,
            )
            msg = self.strings("unmuted").format(
                utils.get_link(user), get_first_name(user)
            )
            await utils.answer(message, msg)

            if self.get("logchat"):
                await self._client.send_message(
                    self.get("logchat"),
                    self.strings("unmuted_log").format(
                        utils.get_link(user),
                        get_first_name(user),
                        utils.get_link(chat),
                        get_first_name(chat),
                    ),
                )
        except UserAdminInvalidError:
            await utils.answer(message, self.strings("not_admin"))
            return

    @error_handler
    @chat_command
    async def unbancmd(self, message: Message):
        """<user> - Unban user"""
        chat = await message.get_chat()

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        user = None

        try:
            if args.isdigit():
                args = int(args)
            user = await self._client.get_entity(args)
        except Exception:
            try:
                user = await self._client.get_entity(reply.sender_id)
            except Exception:
                await utils.answer(message, self.strings("args"))
                return

        try:
            await self._client.edit_permissions(
                chat,
                user,
                until_date=0,
                **{right: True for right in BANNED_RIGHTS.keys()},
            )
            msg = self.strings("unban").format(
                utils.get_link(user), get_first_name(user)
            )
            await utils.answer(message, msg)

            if self.get("logchat"):
                await self._client.send_message(
                    self.get("logchat"),
                    self.strings("unban_log").format(
                        utils.get_link(user),
                        get_first_name(user),
                        utils.get_link(chat),
                        get_first_name(chat),
                    ),
                )
        except UserAdminInvalidError:
            await utils.answer(message, self.strings("not_admin"))
            return

    @error_handler
    async def protectscmd(self, message: Message):
        """typing.List available filters"""
        await utils.answer(
            message,
            (
                self.strings("protections")
                if self.api._inited
                else "\n".join(
                    [
                        line
                        for line in self.strings("protections").splitlines()
                        if "antinsfw" not in line.lower()
                        and "report" not in line.lower()
                    ]
                )
            ),
        )

    @error_handler
    async def fedscmd(self, message: Message):
        """typing.List federations"""
        res = self.strings("feds_header")

        if not self.api.feds:
            await utils.answer(message, self.strings("no_federations"))
            return

        for shortname, config in self.api.feds.copy().items():
            res += f"    ☮️ <b>{config['name']}</b> (<code>{shortname}</code>)"
            for chat in config["chats"]:
                try:
                    if str(chat).isdigit():
                        chat = int(chat)
                    c = await self._client.get_entity(chat)
                except Exception:
                    continue

                res += (
                    "\n        <b>- <a"
                    f" href=\"tg://resolve?domain={getattr(c, 'username', '')}\">{c.title}</a></b>"
                )

            res += (
                "\n        <b><emoji document_id=5193091781327068499>👮‍♀️</emoji>"
                f" {len(config.get('warns', []))} warns</b>\n\n"
            )

        await utils.answer(message, res)

    @error_handler
    @chat_command
    async def fedcmd(self, message: Message):
        """<shortname> - Info about federation"""
        args = utils.get_args_raw(message)
        chat = utils.get_chat_id(message)

        fed = await self.find_fed(message)

        if (not args or args not in self.api.feds) and not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        if not args or args not in self.api.feds:
            args = fed

        res = self.strings("fed")

        fed = args

        admins = ""
        for admin in self.api.feds[fed]["admins"]:
            try:
                if str(admin).isdigit():
                    admin = int(admin)
                user = await self._client.get_entity(admin)
            except Exception:
                continue
            name = get_full_name(user)
            status = (
                "<code> 🧃 online</code>"
                if isinstance(getattr(user, "status", None), UserStatusOnline)
                else ""
            )
            admins += (
                f' <b>👤 <a href="{utils.get_link(user)}">{name}</a></b>{status}\n'
            )

        chats = ""
        channels = ""
        for chat in self.api.feds[fed]["chats"]:
            try:
                if str(chat).isdigit():
                    chat = int(chat)
                c = await self._client.get_entity(chat)
            except Exception:
                continue

            if str(chat) in self._linked_channels:
                try:
                    channel = await self._client.get_entity(
                        self._linked_channels[str(chat)]
                    )
                    channels += (
                        " <b><emoji document_id=5213203794619277246>📣</emoji> <a"
                        f' href="{utils.get_link(channel)}">{utils.escape_html(channel.title)}</a></b>\n'
                    )
                except Exception:
                    pass

            chats += (
                " <b>🫂 <a"
                f' href="{utils.get_link(c)}">{utils.escape_html(c.title)}</a></b>\n'
            )

        await utils.answer(
            message,
            res.format(
                self.api.feds[fed]["name"],
                chats or "-",
                channels or "-",
                admins or "-",
                len(self.api.feds[fed].get("warns", [])),
            ),
        )

    @error_handler
    @chat_command
    async def pchatcmd(self, message: Message):
        """typing.List protection for current chat"""
        chat_id = utils.get_chat_id(message)
        try:
            await self.inline.form(
                message=message,
                **(await self.get_config(chat_id)),
                manual_security=True,
                silent=True,
            )
        except KeyError:
            await utils.answer(message, self.strings("no_protects"))

    @error_handler
    @chat_command
    async def warncmd(self, message: Message):
        """<user> - Warn user"""
        chat = await message.get_chat()

        if not chat.admin_rights and not chat.creator:
            await utils.answer(message, self.strings("not_admin"))
            return

        args = utils.get_args_raw(message)

        if " -f" in args:
            args = args.replace(" -f", "")
            force = True
        else:
            force = False

        reply = await message.get_reply_message()
        user = None
        if reply:
            user = await self._client.get_entity(reply.sender_id)
            reason = args or self.strings("no_reason")
        else:
            try:
                u = args.split(maxsplit=1)[0]
                if u.isdigit():
                    u = int(u)

                user = await self._client.get_entity(u)
            except IndexError:
                await utils.answer(message, self.strings("args"))
                return

            try:
                reason = args.split(maxsplit=1)[1]
            except IndexError:
                reason = self.strings("no_reason")

        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        if not force and user.id in list(map(int, self.api.feds[fed]["fdef"])):
            await utils.answer(message, self.strings("fdef403").format("warn"))
            return

        self.api.request(
            {
                "action": "warn user",
                "args": {
                    "uid": self.api.feds[fed]["uid"],
                    "user": user.id,
                    "reason": reason,
                },
            },
            message,
        )
        warns = self.api.feds[fed].get("warns", {}).get(str(user.id), []) + [reason]

        if len(warns) >= self.config["warns_limit"]:
            user_name = get_first_name(user)
            chats = self.api.feds[fed]["chats"]
            for c in chats:
                if str(c).isdigit():
                    c = int(str(c))

                await self._client(
                    EditBannedRequest(
                        c,
                        user,
                        ChatBannedRights(
                            until_date=time.time() + 60**2 * 24 * 7,
                            send_messages=True,
                        ),
                    )
                )

                if c == utils.get_chat_id(message):
                    await self._client.send_message(
                        c,
                        self.strings("warns_limit").format(
                            utils.get_link(user),
                            user_name,
                            "muted him in federation for 7 days",
                        ),
                    )

            if message.out:
                await message.delete()

            self.api.request(
                {
                    "action": "clear all user warns",
                    "args": {"uid": self.api.feds[fed]["uid"], "user": user.id},
                },
                message,
            )
        else:
            msg = self.strings("fwarn", message).format(
                utils.get_link(user),
                get_first_name(user),
                len(warns),
                self.config["warns_limit"],
                reason,
                self.get("punish_suffix", ""),
            )

            if self._is_inline:
                punishment_info = {
                    "reply_markup": {
                        "text": self.strings("btn_unwarn"),
                        "data": f"dw/{utils.get_chat_id(message)}/{user.id}",
                    },
                }

                if self.get("logchat"):
                    await utils.answer(message, msg)
                    await self.inline.form(
                        text=self.strings("fwarn", message).format(
                            utils.get_link(user),
                            get_first_name(user),
                            len(warns),
                            self.config["warns_limit"],
                            reason,
                            "",
                        ),
                        message=self.get("logchat"),
                        **punishment_info,
                        silent=True,
                    )
                else:
                    await self.inline.form(
                        text=msg, message=message, **punishment_info, silent=True
                    )
            else:
                await utils.answer(message, msg)

    @error_handler
    @chat_command
    async def warnscmd(self, message: Message):
        """[user] - Show warns in chat \\ of user"""
        chat_id = utils.get_chat_id(message)

        fed = await self.find_fed(message)

        async def check_member(user_id):
            try:
                await self._client.get_permissions(chat_id, user_id)
                return True
            except Exception:
                return False

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        warns = self.api.feds[fed].get("warns", {})

        if not warns:
            await utils.answer(message, self.strings("no_fed_warns"))
            return

        async def send_user_warns(usid):
            try:
                if int(usid) < 0:
                    usid = int(str(usid)[4:])
            except Exception:
                pass

            if not warns:
                await utils.answer(message, self.strings("no_fed_warns"))
                return

            if str(usid) not in warns or not warns[str(usid)]:
                user_obj = await self._client.get_entity(usid)
                await utils.answer(
                    message,
                    self.strings("no_warns").format(
                        utils.get_link(user_obj), get_full_name(user_obj)
                    ),
                )
            else:
                user_obj = await self._client.get_entity(usid)
                _warns = ""
                processed = []
                for warn in warns[str(usid)].copy():
                    if warn in processed:
                        continue
                    processed += [warn]
                    _warns += (
                        "<emoji document_id=4974362561664254705>🛑</emoji> <i>"
                        + warn
                        + (
                            f" </i><b>[x{warns[str(usid)].count(warn)}]</b><i>"
                            if warns[str(usid)].count(warn) > 1
                            else ""
                        )
                        + "</i>\n"
                    )
                await utils.answer(
                    message,
                    self.strings("warns").format(
                        utils.get_link(user_obj),
                        get_full_name(user_obj),
                        len(warns[str(usid)]),
                        self.config["warns_limit"],
                        _warns,
                    ),
                )

        if not await self.check_admin(chat_id, message.sender_id):
            await send_user_warns(message.sender_id)
        else:
            reply = await message.get_reply_message()
            args = utils.get_args_raw(message)
            if not reply and not args:
                res = self.strings("warns_adm_fed")
                for user, _warns in warns.copy().items():
                    try:
                        user_obj = await self._client.get_entity(int(user))
                    except Exception:
                        continue

                    if isinstance(user_obj, User):
                        try:
                            name = get_full_name(user_obj)
                        except TypeError:
                            continue
                    else:
                        name = user_obj.title

                    res += (
                        "<emoji document_id=5467759840463953770>🐺</emoji> <b><a"
                        f' href="{utils.get_link(user_obj)}">' + name + "</a></b>\n"
                    )
                    processed = []
                    for warn in _warns.copy():
                        if warn in processed:
                            continue
                        processed += [warn]
                        res += (
                            "<code>   </code>🏴󠁧󠁢󠁥󠁮󠁧󠁿 <i>"
                            + warn
                            + (
                                f" </i><b>[x{_warns.count(warn)}]</b><i>"
                                if _warns.count(warn) > 1
                                else ""
                            )
                            + "</i>\n"
                        )

                await utils.answer(message, res)
                return
            elif reply:
                await send_user_warns(reply.sender_id)
            elif args:
                await send_user_warns(args)

    @error_handler
    @chat_command
    async def delwarncmd(self, message: Message):
        """<user> - Forgave last warn"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        user = None

        if reply:
            user = await self._client.get_entity(reply.sender_id)
        else:
            if args.isdigit():
                args = int(args)

            try:
                user = await self._client.get_entity(args)
            except IndexError:
                await utils.answer(message, self.strings("args"))
                return

        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        self.api.request(
            {
                "action": "forgive user warn",
                "args": {"uid": self.api.feds[fed]["uid"], "user": user.id},
            },
            message,
        )

        msg = self.strings("dwarn_fed").format(
            utils.get_link(user), get_first_name(user)
        )

        await utils.answer(message, msg)

        if self.get("logchat", False):
            await self._client.send_message(self.get("logchat"), msg)

    @error_handler
    @chat_command
    async def clrwarnscmd(self, message: Message):
        """<reply | user_id | username> - Remove all warns from user"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        user = None
        if reply:
            user = await self._client.get_entity(reply.sender_id)
        else:
            if args.isdigit():
                args = int(args)

            try:
                user = await self._client.get_entity(args)
            except IndexError:
                await utils.answer(message, self.strings("args"))
                return

        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        self.api.request(
            {
                "action": "clear all user warns",
                "args": {"uid": self.api.feds[fed]["uid"], "user": user.id},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("clrwarns_fed").format(
                utils.get_link(user), get_first_name(user)
            ),
        )

    @error_handler
    @chat_command
    async def clrallwarnscmd(self, message: Message):
        """Remove all warns from current federation"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        self.api.request(
            {
                "action": "clear federation warns",
                "args": {"uid": self.api.feds[fed]["uid"]},
            },
            message,
        )

        await utils.answer(message, self.strings("clrallwarns_fed"))

    @error_handler
    @chat_command
    async def welcomecmd(self, message: Message):
        """<text> - Change welcome text"""
        chat_id = utils.get_chat_id(message)
        args = utils.get_args_raw(message) or "off"

        self.api.request(
            {
                "action": "update protections",
                "args": {"protection": "welcome", "state": args, "chat": chat_id},
            },
            message,
        )

        if args and args != "off":
            await utils.answer(message, self.strings("welcome").format(args))
        else:
            await utils.answer(message, self.strings("unwelcome"))

    @error_handler
    @chat_command
    async def fdefcmd(self, message: Message):
        """<user> - Toggle global user invulnerability"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        user = None
        if reply:
            user = await self._client.get_entity(reply.sender_id)
        else:
            if str(args).isdigit():
                args = int(args)

            try:
                user = await self._client.get_entity(args)
            except Exception:
                await utils.answer(message, self.strings("args"))
                return

        self.api.request(
            {
                "action": "protect user",
                "args": {"uid": self.api.feds[fed]["uid"], "user": user.id},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("defense").format(
                utils.get_link(user),
                get_first_name(user),
                "on" if str(user.id) not in self.api.feds[fed]["fdef"] else "off",
            ),
        )

    @error_handler
    @chat_command
    async def fsavecmd(self, message: Message):
        """<note name> <reply> - Save federative note"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        if not reply or not args or not reply.text:
            await utils.answer(message, self.strings("fsave_args"))
            return

        self.api.request(
            {
                "action": "new note",
                "args": {
                    "uid": self.api.feds[fed]["uid"],
                    "shortname": args,
                    "note": reply.text,
                },
            },
            message,
        )

        await utils.answer(message, self.strings("fsave").format(args))

    @error_handler
    @chat_command
    async def fstopcmd(self, message: Message):
        """<note name> - Remove federative note"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("fstop_args"))
            return

        self.api.request(
            {
                "action": "delete note",
                "args": {"uid": self.api.feds[fed]["uid"], "shortname": args},
            },
            message,
        )

        await utils.answer(message, self.strings("fstop").format(args))

    @error_handler
    @chat_command
    async def fnotescmd(self, message: Message, from_watcher: bool = False):
        """Show federative notes"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        res = {}
        cache = {}

        for shortname, note in self.api.feds[fed].get("notes", {}).items():
            if int(note["creator"]) != self._tg_id and from_watcher:
                continue

            try:
                if int(note["creator"]) not in cache:
                    obj = await self._client.get_entity(int(note["creator"]))
                    cache[int(note["creator"])] = obj.first_name or obj.title
                key = (
                    f'<a href="{utils.get_link(obj)}">{cache[int(note["creator"])]}</a>'
                )
                if key not in res:
                    res[key] = ""
                res[key] += f"  <code>{shortname}</code>\n"
            except Exception:
                key = "unknown"
                if key not in res:
                    res[key] = ""
                res[key] += f"  <code>{shortname}</code>\n"

        notes = "".join(f"\nby {owner}:\n{note}" for owner, note in res.items())

        if not notes and not from_watcher:
            await utils.answer(message, self.strings("no_notes"))
            return

        if not notes:
            return

        await utils.answer(message, self.strings("fnotes").format(notes))

    @error_handler
    @chat_command
    async def fdeflistcmd(self, message: Message):
        """Show global invulnerable users"""
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        if not self.api.feds[fed].get("fdef", []):
            await utils.answer(message, self.strings("no_defense"))
            return

        res = ""
        for user in self.api.feds[fed].get("fdef", []).copy():
            try:
                u = await self._client.get_entity(int(user), exp=0)
            except Exception:
                self.api.request(
                    {
                        "action": "protect user",
                        "args": {"uid": self.api.feds[fed]["uid"], "user": user},
                    },
                    message,
                )
                await asyncio.sleep(0.2)
                continue

            tit = get_full_name(u)

            res += f'  🇻🇦 <a href="{utils.get_link(u)}">{tit}</a>\n'

        await utils.answer(message, self.strings("defense_list").format(res))
        return

    @error_handler
    @chat_command
    async def dmutecmd(self, message: Message):
        """Delete and mute"""
        reply = await message.get_reply_message()
        await self.mutecmd(message)
        await reply.delete()

    @error_handler
    @chat_command
    async def dbancmd(self, message: Message):
        """Delete and ban"""
        reply = await message.get_reply_message()
        await self.bancmd(message)
        await reply.delete()

    @error_handler
    @chat_command
    async def dwarncmd(self, message: Message):
        """Delete and warn"""
        reply = await message.get_reply_message()
        await self.warncmd(message)
        await reply.delete()

    @error_handler
    @chat_command
    async def frenamecmd(self, message: Message):
        """Rename federation"""
        args = utils.get_args_raw(message)
        fed = await self.find_fed(message)

        if not fed:
            await utils.answer(message, self.strings("no_fed"))
            return

        if not args:
            await utils.answer(message, self.strings("rename_noargs"))
            return

        self.api.request(
            {
                "action": "rename federation",
                "args": {"uid": self.api.feds[fed]["uid"], "name": args},
            },
            message,
        )

        await utils.answer(
            message,
            self.strings("rename_success").format(utils.escape_html(args)),
        )

    @error_handler
    @chat_command
    async def clnraidcmd(self, message: Message):
        """<number of users> - Clean raid"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            await utils.answer(message, self.strings("clnraid_args"))
            return

        args = min(int(args), 10000)

        await self.inline.form(
            message=message,
            text=self.strings("clnraid_confirm").format(args),
            reply_markup=[
                {
                    "text": self.strings("clnraid_yes"),
                    "callback": self._clnraid,
                    "args": (utils.get_chat_id(message), args),
                },
                {
                    "text": self.strings("clnraid_cancel"),
                    "action": "close",
                },
            ],
            silent=True,
        )

    async def _clnraid(
        self,
        call: typing.Union[InlineCall, InlineMessage],
        chat_id: int,
        quantity: int,
    ) -> InlineCall:
        if call is not None:
            await call.edit(self.strings("clnraid_started").format(quantity))

        deleted = 0
        actually_deleted = 0
        async for log_msg in self._client.iter_admin_log(chat_id, join=True):
            if deleted >= quantity:
                break

            deleted += 1

            try:
                await self.inline.bot.kick_chat_member(
                    int(f"-100{chat_id}"),
                    log_msg.user.id,
                )
            except Exception:
                logger.debug("Can't kick member", exc_info=True)
            else:
                actually_deleted += 1

        if call is not None:
            await call.edit(self.strings("clnraid_complete").format(actually_deleted))

        return call

    @error_handler
    async def myrightscmd(self, message: Message):
        """typing.List your admin rights in all chats"""
        if not PIL_AVAILABLE:
            await utils.answer(message, self.strings("pil_unavailable"))
            return

        message = await utils.answer(message, self.strings("processing_myrights"))

        rights = []
        async for chat in self._client.iter_dialogs():
            ent = chat.entity

            if (
                not (
                    isinstance(ent, Chat)
                    or (isinstance(ent, Channel) and getattr(ent, "megagroup", False))
                )
                or not ent.admin_rights
                or ent.participants_count < 5
            ):
                continue

            r = ent.admin_rights

            rights += [
                [
                    ent.title if len(ent.title) < 30 else f"{ent.title[:30]}...",
                    "YES" if r.change_info else "-----",
                    "YES" if r.delete_messages else "-----",
                    "YES" if r.ban_users else "-----",
                    "YES" if r.invite_users else "-----",
                    "YES" if r.pin_messages else "-----",
                    "YES" if r.add_admins else "-----",
                ]
            ]

        await self._client.send_file(
            message.peer_id,
            self.render_table(
                [
                    [
                        "Chat",
                        "change_info",
                        "delete_messages",
                        "ban_users",
                        "invite_users",
                        "pin_messages",
                        "add_admins",
                    ]
                ]
                + rights
            ),
        )

        if message.out:
            await message.delete()

    @error_handler
    async def p__antiservice(self, chat_id: typing.Union[str, int], message: Message):
        if (
            self.api.should_protect(chat_id, "antiservice")
            and str(chat_id) not in self._ban_ninja
            and getattr(message, "action_message", False)
        ):
            if self.api.should_protect(chat_id, "captcha") and (
                getattr(message, "user_joined", False)
                or getattr(message, "user_added", False)
            ):
                self._delete_soon += [(message, time.time() + 5 * 60)]
                return

            try:
                await self.inline.bot.delete_message(
                    int(f"-100{chat_id}"),
                    message.action_message.id,
                )
            except Exception:
                await message.delete()

    async def _update_ban_ninja(self, chat_id: str):
        while (
            chat_id in self._ban_ninja_forms and self._ban_ninja[chat_id] > time.time()
        ):
            try:
                await self._ban_ninja_forms[chat_id].edit(
                    self.strings("smart_anti_raid_active").format(
                        (
                            self.strings("forbid_messages")
                            if self.config["close_on_raid"]
                            else ""
                        ),
                        self._ban_ninja_progress[chat_id],
                    ),
                    {
                        "text": self.strings("smart_anti_raid_off"),
                        "callback": self.disable_smart_anti_raid,
                        "args": (chat_id,),
                    },
                )
            except Exception:
                pass

            await asyncio.sleep(15)

        try:
            await self.disable_smart_anti_raid(None, chat_id)
        except Exception:
            pass

    @error_handler
    async def p__banninja(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        message: Message,
    ) -> bool:
        if not (
            self.api.should_protect(chat_id, "banninja")
            and (
                getattr(message, "user_joined", False)
                or getattr(message, "user_added", False)
            )
        ):
            return False

        chat_id = str(chat_id)

        if chat_id in self._ban_ninja:
            if self._ban_ninja[chat_id] > time.time():
                self._ban_ninja[chat_id] = time.time() + int(
                    self.config["banninja_cooldown"]
                )
                await self.inline.bot.kick_chat_member(int(f"-100{chat_id}"), user_id)

                self._ban_ninja_progress[chat_id] += 1

                try:
                    await self.inline.bot.delete_message(
                        int(f"-100{chat_id}"),
                        message.action_message.id,
                    )
                except MessageToDeleteNotFound:
                    pass
                except MessageCantBeDeleted:
                    await self._promote_bot(chat_id)
                    await self.inline.bot.delete_message(
                        int(f"-100{chat_id}"),
                        message.action_message.id,
                    )
                logger.debug(
                    f"BanNinja is active in chat {chat_id=}, I kicked {user_id=}"
                )
                return True

            await self.disable_smart_anti_raid(None, chat_id)

        if chat_id not in self._join_ratelimit:
            self._join_ratelimit[chat_id] = []

        self._join_ratelimit[chat_id] += [[user_id, round(time.time())]]

        processed = []

        for u, t in self._join_ratelimit[chat_id].copy():
            if u in processed or t + 60 < time.time():
                self._join_ratelimit[chat_id].remove([u, t])
            else:
                processed += [u]

        self.set("join_ratelimit", self._join_ratelimit)

        if len(self._join_ratelimit[chat_id]) >= self.config["join_ratelimit"]:
            if chat_id in self._ban_ninja:
                return False

            self._ban_ninja[chat_id] = (
                round(time.time()) + self.config["banninja_cooldown"]
            )
            form = await self.inline.form(
                self.strings("smart_anti_raid_active").format(
                    (
                        self.strings("forbid_messages")
                        if self.config["close_on_raid"]
                        else ""
                    ),
                    self.config["join_ratelimit"],
                ),
                message=int(chat_id),
                reply_markup={
                    "text": self.strings("smart_anti_raid_off"),
                    "callback": self.disable_smart_anti_raid,
                    "args": (chat_id,),
                },
                silent=True,
            )

            if self.config["close_on_raid"]:
                try:
                    chat = await message.get_chat()
                    self._ban_ninja_default_rights[chat_id] = chat.default_banned_rights
                    await self._client(
                        EditChatDefaultBannedRightsRequest(
                            chat.id,
                            ChatBannedRights(send_messages=True, until_date=2**31 - 1),
                        )
                    )
                except Exception:
                    pass

            self._ban_ninja_forms[chat_id] = form
            self._ban_ninja_progress[chat_id] = self.config["join_ratelimit"]
            self._ban_ninja_tasks[chat_id] = asyncio.ensure_future(
                self._update_ban_ninja(chat_id)
            )

            await (
                await self._clnraid(
                    call=(
                        await self.inline.form(
                            self.strings("clnraid_started").format("*loading*"),
                            message=int(chat_id),
                            reply_markup={"text": ".", "action": "close"},
                            silent=True,
                        )
                    ),
                    chat_id=int(chat_id),
                    quantity=self.config["join_ratelimit"],
                )
            ).delete()

            messages = []
            users = []
            for u, m in self._ban_ninja_messages:
                if u not in users:
                    if len(users) > self.config["join_ratelimit"]:
                        break

                    users += [u]

                messages += [m]

            for m in messages:
                try:
                    await self.inline.bot.delete_message(
                        int(f"-100{utils.get_chat_id(m)}"),
                        m.id,
                    )
                except MessageToDeleteNotFound:
                    pass
                except MessageCantBeDeleted:
                    await self._promote_bot(utils.get_chat_id(m))
                    await self.inline.bot.delete_message(
                        int(f"-100{utils.get_chat_id(m)}"),
                        m.id,
                    )
                except Exception:
                    await m.delete()

            try:
                await self._client.pin_message(int(chat_id), form.form["message_id"])
            except Exception:
                pass

        return False

    async def disable_smart_anti_raid(self, call: InlineCall, chat_id: int):
        chat_id = str(chat_id)
        if chat_id in self._ban_ninja:
            del self._ban_ninja[chat_id]
            if call:
                await call.edit(self.strings("smart_anti_raid_stopped"))

            if call:
                await call.answer("Success")

            try:
                await self._client.unpin_message(
                    int(chat_id),
                    self._ban_ninja_forms[str(chat_id)].form["message_id"],
                )
            except Exception:
                pass

            if self.config["close_on_raid"]:
                try:
                    await self._client(
                        EditChatDefaultBannedRightsRequest(
                            int(chat_id),
                            self._ban_ninja_default_rights[chat_id],
                        )
                    )
                    del self._ban_ninja_default_rights[chat_id]
                except Exception:
                    pass

            await self._client.send_message(
                int(chat_id),
                self.strings("banninja_report").format(
                    self._ban_ninja_progress[chat_id]
                ),
            )

            if chat_id in self._ban_ninja_forms:
                await self._ban_ninja_forms[chat_id].delete()
                del self._ban_ninja_forms[chat_id]

            if chat_id in self._ban_ninja_progress:
                del self._ban_ninja_progress[chat_id]

            if chat_id in self._ban_ninja_tasks:
                self._ban_ninja_tasks[chat_id].cancel()
                del self._ban_ninja_tasks[chat_id]

            return

        await call.answer("Already stopped")

    @error_handler
    async def p__antiraid(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
        chat: typing.Union[Chat, Channel],
    ) -> bool:
        if self.api.should_protect(chat_id, "antiraid") and (
            getattr(message, "user_joined", False)
            or getattr(message, "user_added", False)
        ):
            action = self.api.chats[str(chat_id)]["antiraid"][0]
            if action == "kick":
                await self._client.send_message(
                    "me",
                    self.strings("antiraid").format(
                        "kicked",
                        user.id,
                        get_full_name(user),
                        utils.escape_html(chat.title),
                    ),
                )

                await self._client.kick_participant(chat_id, user)
            elif action == "ban":
                await self._client.send_message(
                    "me",
                    self.strings("antiraid").format(
                        "banned",
                        user.id,
                        get_full_name(user),
                        utils.escape_html(chat.title),
                    ),
                )

                await self.ban(chat, user, 0, "antiraid")
            elif action == "mute":
                await self._client.send_message(
                    "me",
                    self.strings("antiraid").format(
                        "muted",
                        user.id,
                        get_full_name(user),
                        utils.escape_html(chat.title),
                    ),
                )

                await self.mute(chat, user, 0, "antiraid")

            return True

        return False

    async def _captcha_invalid(
        self,
        call: InlineCall,
        chat_id: int,
        user: User,
    ):
        if call.from_user.id != user.id:
            await call.answer("Not for you....")
            return

        with contextlib.suppress(KeyError):
            del self._captcha_db[chat_id][user.id]

        await call.answer("Sorry ☹️")

        await self.punish(
            chat_id,
            user,
            "captcha_failed",
            self.api.chats[str(chat_id)]["captcha"][0],
            get_full_name(user),
            fulltime=True,
            message=None,
        )

        with contextlib.suppress(Exception):
            await self._captcha_messages[chat_id][user.id].delete()

    async def _captcha_valid(self, call: InlineCall, chat_id: int, user_id: int):
        if call.from_user.id != user_id:
            await call.answer("Not for you....")
            return

        if self._captcha_db[chat_id][user_id]["unmute"]:
            await self._client.edit_permissions(
                int(chat_id),
                int(user_id),
                until_date=0,
                send_messages=True,
            )

        with contextlib.suppress(KeyError):
            del self._captcha_db[chat_id][user_id]

        with contextlib.suppress(Exception):
            await self._captcha_messages[chat_id][user_id].delete()

        await call.answer("Welcome!")

    @error_handler
    async def p__captcha(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
        chat: Chat,
    ) -> bool:
        if not (
            self.api.should_protect(chat_id, "captcha")
            and str(chat_id) not in self._ban_ninja
            and (
                getattr(message, "user_joined", False)
                or getattr(message, "user_added", False)
            )
        ):
            return False

        valid = utils.rand(6)
        invalid = [utils.rand(6) for _ in range(5)]

        markup = [
            {
                "text": i,
                "callback": self._captcha_invalid,
                "args": (chat_id, user),
            }
            for i in invalid
        ] + [
            {"text": valid, "callback": self._captcha_valid, "args": (chat_id, user_id)}
        ]

        random.shuffle(markup)
        markup = utils.chunks(markup, 2)

        unmute = False

        if not (
            await self._client.get_permissions(int(chat_id), int(user_id))
        ).is_banned:
            unmute = True
            await self.mute(chat, user, 15 * 60, "captcha_processing", silent=True)

        for _ in range(5):
            try:
                m = await self.inline.form(
                    message=(await message.reply("🪄 <b>Loading captcha...</b>")),
                    text=self.strings("complete_captcha").format(
                        user.id,
                        get_full_name(user),
                    ),
                    photo=f"https://hikarichat.hikariatama.ru/captcha/{valid}",
                    reply_markup=markup,
                    disable_security=True,
                )
            except WebpageCurlFailedError:
                await asyncio.sleep(0.5)
            else:
                break

        if chat_id not in self._captcha_db:
            self._captcha_db[chat_id] = {}

        if chat_id not in self._captcha_messages:
            self._captcha_messages[chat_id] = {}

        self._captcha_db[chat_id][user_id] = {
            "time": time.time() + 5 * 60,
            "user": user,
            "unmute": unmute,
        }

        self._captcha_messages[chat_id][user_id] = m

        self._ban_ninja_messages = [(user_id, m)] + self._ban_ninja_messages

    @error_handler
    async def p__cas(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
        chat: Chat,
    ) -> bool:
        if not (
            self.api.should_protect(chat_id, "cas")
            and str(chat_id) not in self._ban_ninja
            and (
                getattr(message, "user_joined", False)
                or getattr(message, "user_added", False)
            )
        ):
            return False

        return (
            self.api.chats[str(chat_id)]["cas"][0]
            if (
                (
                    await utils.run_sync(
                        requests.get,
                        f"https://api.cas.chat/check?user_id={user_id}",
                    )
                )
                .json()
                .get("result", {})
                .get("offenses", False)
            )
            else False
        )

    @error_handler
    async def p__welcome(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
        chat: Chat,
    ) -> bool:
        if not (
            self.api.should_protect(chat_id, "welcome")
            and str(chat_id) not in self._ban_ninja
            and (
                getattr(message, "user_joined", False)
                or getattr(message, "user_added", False)
            )
        ):
            return False

        m = await self._client.send_message(
            chat_id,
            self.api.chats[str(chat_id)]["welcome"][0]
            .replace("{user}", get_full_name(user))
            .replace("{chat}", utils.escape_html(chat.title))
            .replace(
                "{mention}",
                f'<a href="{utils.get_link(user)}">{get_full_name(user)}</a>',
            ),
            reply_to=message.action_message.id,
        )

        self._ban_ninja_messages = [(user_id, m)] + self._ban_ninja_messages

        return True

    @error_handler
    async def p__report(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ):
        if not self.api.should_protect(chat_id, "report") or not getattr(
            message,
            "reply_to_msg_id",
            False,
        ):
            return

        reply = await message.get_reply_message()
        if (
            str(user_id) not in self._ratelimit["report"]
            or self._ratelimit["report"][str(user_id)] < time.time()
        ) and (
            (
                message.raw_text.startswith("#report")
                or message.raw_text.startswith("/report")
            )
            and reply
        ):
            fed = await self.find_fed(message)
            if fed in self.api.feds and reply.sender_id in list(
                map(int, self.api.feds[fed]["fdef"])
            ):
                await utils.answer(message, self.strings("fdef403").format("report"))
                return

            chat = await message.get_chat()

            reason = (
                message.raw_text.split(maxsplit=1)[1]
                if message.raw_text.count(" ") >= 1
                else self.strings("no_reason")
            )

            self.api.request(
                {
                    "action": "report",
                    "args": {
                        "chat": chat_id,
                        "reason": reason,
                        "link": await utils.get_message_link(reply, chat),
                        "user_link": utils.get_link(user),
                        "user_name": get_full_name(user),
                        "text_thumbnail": (getattr(reply, "raw_text", "") or "")[:1024]
                        or "<media>",
                    },
                },
                message,
            )

            msg = self.strings("reported").format(
                utils.get_link(user),
                get_full_name(user),
                reason,
            )

            if self._is_inline:
                m = await self._client.send_message(
                    chat.id,
                    "🌘 <b>Reporting message to admins...</b>",
                    reply_to=message.reply_to_msg_id,
                )
                await self.inline.form(
                    message=m,
                    text=msg,
                    reply_markup=[
                        [
                            {
                                "text": self.strings("btn_mute"),
                                "data": f"m/{chat.id}/{reply.sender_id}#{reply.id}",
                            },
                            {
                                "text": self.strings("btn_ban"),
                                "data": f"b/{chat.id}/{reply.sender_id}#{reply.id}",
                            },
                        ],
                        [
                            {
                                "text": self.strings("btn_fban"),
                                "data": f"fb/{chat.id}/{reply.sender_id}#{reply.id}",
                            },
                            {
                                "text": self.strings("btn_del"),
                                "data": f"d/{chat.id}/{reply.sender_id}#{reply.id}",
                            },
                        ],
                    ],
                    silent=True,
                )
            else:
                await (utils.answer if message else self._client.send_message)(
                    message or chat.id,
                    msg,
                )

            self._ratelimit["report"][str(user_id)] = time.time() + 30

            try:
                await self.inline.bot.delete_message(
                    int(f"-100{chat_id}"),
                    getattr(message, "action_message", message).id,
                )
            except MessageToDeleteNotFound:
                pass
            except MessageCantBeDeleted:
                await self._promote_bot(chat_id)
                await self.inline.bot.delete_message(
                    int(f"-100{chat_id}"),
                    getattr(message, "action_message", message).id,
                )

    @error_handler
    async def _promote_bot(self, chat_id: int):
        try:
            await self._client(
                InviteToChannelRequest(
                    int(chat_id),
                    [self.inline.bot_username],
                )
            )
        except Exception:
            logger.warning(
                "Unable to invite cleaner to chat. Maybe he's already there?"
            )

        try:
            await self._client(
                EditAdminRequest(
                    channel=int(chat_id),
                    user_id=self.inline.bot_username,
                    admin_rights=ChatAdminRights(ban_users=True, delete_messages=True),
                    rank="HikariChat",
                )
            )
        except Exception:
            logger.exception("Cleaner promotion failed!")

    @error_handler
    async def p__antiflood(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        if self.api.should_protect(chat_id, "antiflood"):
            if str(chat_id) not in self._flood_cache:
                self._flood_cache[str(chat_id)] = {}

            if str(user_id) not in self._flood_cache[str(chat_id)]:
                self._flood_cache[str(chat_id)][str(user_id)] = []

            for item in self._flood_cache[str(chat_id)][str(user_id)].copy():
                if time.time() - item > self.flood_timeout:
                    self._flood_cache[str(chat_id)][str(user_id)].remove(item)

            self._flood_cache[str(chat_id)][str(user_id)].append(
                round(time.mktime(message.date.timetuple()))
                if getattr(message, "date", False)
                else round(time.time())
            )
            self.set("flood_cache", self._flood_cache)

            if (
                len(self._flood_cache[str(chat_id)][str(user_id)])
                >= self.flood_threshold
            ):
                return self.api.chats[str(chat_id)]["antiflood"][0]

        return False

    @error_handler
    async def p__antichannel(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> bool:
        if (
            self.api.should_protect(chat_id, "antichannel")
            and getattr(message, "sender_id", 0) < 0
        ):
            await self.ban(chat_id, user_id, 0, "", None, True)
            try:
                await self.inline.bot.delete_message(int(f"-100{chat_id}"), message.id)
            except Exception:
                await message.delete()

            return True

        return False

    @error_handler
    async def p__antigif(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> bool:
        if self.api.should_protect(chat_id, "antigif"):
            try:
                if (
                    message.media
                    and DocumentAttributeAnimated() in message.media.document.attributes
                ):
                    await message.delete()
                    return True
            except Exception:
                pass

        return False

    @error_handler
    async def p__antispoiler(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> bool:
        if self.api.should_protect(chat_id, "antispoiler"):
            try:
                if any(isinstance(_, MessageEntitySpoiler) for _ in message.entities):
                    await message.delete()
                    return True
            except Exception:
                pass

        return False

    @error_handler
    async def p__antiexplicit(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        if self.api.should_protect(chat_id, "antiexplicit"):
            text = getattr(message, "raw_text", "")
            P = "пПnPp"
            I = "иИiI1uІИ́Їіи́ї"  # noqa: E741
            E = "еЕeEЕ́е́"
            D = "дДdD"
            Z = "зЗ3zZ3"
            M = "мМmM"
            U = "уУyYuUУ́у́"
            O = "оОoO0О́о́"  # noqa: E741
            L = "лЛlL1"
            A = "аАaAА́а́@"
            N = "нНhH"
            G = "гГgG"
            K = "кКkK"
            R = "рРpPrR"
            H = "хХxXhH"
            YI = "йЙyуУY"
            YA = "яЯЯ́я́"
            YO = "ёЁ"
            YU = "юЮЮ́ю́"
            B = "бБ6bB"
            T = "тТtT1"
            HS = "ъЪ"
            SS = "ьЬ"
            Y = "ыЫ"

            occurrences = re.findall(
                rf"""\b[0-9]*(\w*[{P}][{I}{E}][{Z}][{D}]\w*|(?:[^{I}{U}\s]+|{N}{I})?(?<!стра)[{H}][{U}][{YI}{E}{YA}{YO}{I}{L}{YU}](?!иг)\w*|\w*[{B}][{L}](?:[{YA}]+[{D}{T}]?|[{I}]+[{D}{T}]+|[{I}]+[{A}]+)(?!х)\w*|(?:\w*[{YI}{U}{E}{A}{O}{HS}{SS}{Y}{YA}][{E}{YO}{YA}{I}][{B}{P}](?!ы\b|ол)\w*|[{E}{YO}][{B}]\w*|[{I}][{B}][{A}]\w+|[{YI}][{O}][{B}{P}]\w*)|\w*(?:[{P}][{I}{E}][{D}][{A}{O}{E}]?[{R}](?!о)\w*|[{P}][{E}][{D}][{E}{I}]?[{G}{K}])|\w*[{Z}][{A}{O}][{L}][{U}][{P}]\w*|\w*[{M}][{A}][{N}][{D}][{A}{O}]\w*|\w*[{G}][{O}{A}][{N}][{D}][{O}][{N}]\w*)""",
                text,
            )

            occurrences = [
                word
                for word in occurrences
                if all(
                    excl not in word for excl in self.api.variables["censor_exclusions"]
                )
            ]

            if occurrences:
                return self.api.chats[str(chat_id)]["antiexplicit"][0]

        return False

    @error_handler
    async def p__antinsfw(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        if not self.api.should_protect(chat_id, "antinsfw"):
            return False

        media = False

        if getattr(message, "sticker", False):
            media = message.sticker
        elif getattr(message, "media", False):
            media = message.media

        if not media:
            return False

        photo = io.BytesIO()
        await self._client.download_media(message.media, photo)
        photo.seek(0)

        if imghdr.what(photo) not in self.api.variables["image_types"]:
            return False

        response = await self.api.nsfw(photo)
        if response != "nsfw":
            return False

        todel = []
        async for _ in self._client.iter_messages(
            message.peer_id,
            reverse=True,
            offset_id=message.id - 1,
        ):
            todel += [_]
            if _.sender_id != message.sender_id:
                break

        await self._client.delete_messages(
            message.peer_id,
            message_ids=todel,
            revoke=True,
        )

        return self.api.chats[str(chat_id)]["antinsfw"][0]

    @error_handler
    async def p__antitagall(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        return (
            self.api.chats[str(chat_id)]["antitagall"][0]
            if self.api.should_protect(chat_id, "antitagall")
            and getattr(message, "text", False)
            and message.text.count("tg://user?id=") >= 5
            else False
        )

    @error_handler
    async def p__antihelp(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> bool:
        if not self.api.should_protect(chat_id, "antihelp") or not getattr(
            message, "text", False
        ):
            return False

        search = message.text
        if "@" in search:
            search = search[: search.find("@")]

        if (
            not search.split()
            or search.split()[0][1:] not in self.api.variables["blocked_commands"]
        ):
            return False

        await message.delete()
        return True

    @error_handler
    async def p__antiarab(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        return (
            self.api.chats[str(chat_id)]["antiarab"][0]
            if (
                self.api.should_protect(chat_id, "antiarab")
                and (
                    getattr(message, "user_joined", False)
                    or getattr(message, "user_added", False)
                )
                and (
                    len(re.findall("[\u4e00-\u9fff]+", get_full_name(user))) != 0
                    or len(re.findall("[\u0621-\u064a]+", get_full_name(user))) != 0
                )
            )
            else False
        )

    @error_handler
    async def p__antizalgo(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        return (
            self.api.chats[str(chat_id)]["antizalgo"][0]
            if (
                self.api.should_protect(chat_id, "antizalgo")
                and len(
                    re.findall(
                        "[\u200f\u200e\u0300-\u0361\u0316-\u0362\u0334-\u0338\u0363-\u036f\u3164\ud83d\udd07\u0020\u00a0\u2000-\u2009\u200a\u2028\u205f\u1160\ufff4]",
                        get_full_name(user),
                    )
                )
                / len(get_full_name(user))
                >= 0.6
            )
            else False
        )

    @error_handler
    async def p__bnd(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        if not self.api.should_protect(chat_id, "bnd"):
            return False

        if (
            self.get("bnd_cache", {}).get(str(chat_id), {}).get(str(user_id), 0)
            >= time.time()
        ):
            return False

        try:
            assert (
                (
                    await self.inline.bot.get_chat_member(
                        int(f"-100{chat_id}"),
                        int(user_id),
                    )
                ).status
            ) not in {"left", "kicked"}
        except Exception:
            return self.api.chats[str(chat_id)]["bnd"][0]
        else:
            bnd_cache = self.get("bnd_cache", {})
            bnd_cache.setdefault(str(chat_id), {}).update(
                {str(user_id): round(time.time()) + 60}
            )
            self.set("bnd_cache", bnd_cache)
            return False

    @error_handler
    async def p__antistick(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        if not self.api.should_protect(chat_id, "antistick") or not (
            getattr(message, "sticker", False)
            or getattr(message, "media", False)
            and isinstance(message.media, MessageMediaUnsupported)
        ):
            return False

        sender = user.id
        if sender not in self._sticks_ratelimit:
            self._sticks_ratelimit[sender] = []

        self._sticks_ratelimit[sender] += [round(time.time())]

        for timing in self._sticks_ratelimit[sender].copy():
            if time.time() - timing > 60:
                self._sticks_ratelimit[sender].remove(timing)

        if len(self._sticks_ratelimit[sender]) > self._sticks_limit:
            return self.api.chats[str(chat_id)]["antistick"][0]

    @error_handler
    async def p__antilagsticks(
        self,
        chat_id: typing.Union[str, int],
        user_id: typing.Union[str, int],
        user: typing.Union[User, Channel],
        message: Message,
    ) -> typing.Union[bool, str]:
        res = (
            self.api.should_protect(chat_id, "antilagsticks")
            and getattr(message, "sticker", False)
            and getattr(message.sticker, "id", False)
            in self.api.variables["destructive_sticks"]
        )
        if res:
            await message.delete()

        return res

    @error_handler
    async def watcher(self, message: Message):
        self._global_queue += [message]

    @error_handler
    async def _global_queue_handler(self):
        while True:
            while self._global_queue:
                await self._global_queue_handler_process(self._global_queue.pop(0))

            for chat_id, info in self._captcha_db.copy().items():
                for user_id, captcha in info.copy().items():
                    if captcha["time"] < time.time():
                        del self._captcha_db[chat_id][user_id]
                        await self.punish(
                            chat_id,
                            captcha["user"],
                            "captcha_timeout",
                            self.api.chats[str(chat_id)]["captcha"][0],
                            get_full_name(captcha["user"]),
                            fulltime=True,
                            message=None,
                        )
                        with contextlib.suppress(Exception):
                            await self._captcha_messages[chat_id][user_id].delete()

            for message, deletion_ts in self._delete_soon.copy():
                if deletion_ts < time.time():
                    with contextlib.suppress(Exception):
                        await message.delete()

                    with contextlib.suppress(Exception):
                        self._delete_soon.remove((message, deletion_ts))

            await asyncio.sleep(0.01)

    @error_handler
    async def _global_queue_handler_process(self, message: Message):
        if not isinstance(getattr(message, "chat", 0), (Chat, Channel)):
            return

        chat_id = utils.get_chat_id(message)

        if (
            isinstance(getattr(message, "chat", 0), Channel)
            and not getattr(message, "megagroup", False)
            and int(chat_id) in reverse_dict(self._linked_channels)
        ):
            actual_chat = str(reverse_dict(self._linked_channels)[int(chat_id)])
            await self.p__antiservice(actual_chat, message)
            return

        await self.p__antiservice(chat_id, message)

        try:
            user_id = (
                getattr(message, "sender_id", False)
                or message.action_message.action.users[0]
            )
        except Exception:
            try:
                user_id = message.action_message.action.from_id.user_id
            except Exception:
                try:
                    user_id = message.from_id.user_id
                except Exception:
                    try:
                        user_id = message.action_message.from_id.user_id
                    except Exception:
                        try:
                            user_id = message.action.from_user.id
                        except Exception:
                            try:
                                user_id = (await message.get_user()).id
                            except Exception:
                                logger.debug(
                                    f"Can't extract entity from event {type(message)}"
                                )
                                return

        user_id = (
            int(str(user_id)[4:]) if str(user_id).startswith("-100") else int(user_id)
        )

        if await self.p__banninja(chat_id, user_id, message):
            return

        fed = await self.find_fed(message)

        if fed in self.api.feds:
            if (
                getattr(message, "raw_text", False)
                and (
                    str(user_id) not in self._ratelimit["notes"]
                    or self._ratelimit["notes"][str(user_id)] < time.time()
                )
                and not message.raw_text.startswith(self.get_prefix())
            ):
                logger.debug("Checking message for notes...")
                if message.raw_text.lower().strip() in ["#заметки", "#notes", "/notes"]:
                    self._ratelimit["notes"][str(user_id)] = time.time() + 3
                    if any(
                        str(note["creator"]) == str(self._tg_id)
                        for _, note in self.api.feds[fed]["notes"].items()
                    ):
                        await self.fnotescmd(
                            await message.reply(
                                f"<code>{self.get_prefix()}fnotes</code>"
                            ),
                            True,
                        )

                for note, note_info in self.api.feds[fed]["notes"].items():
                    if str(note_info["creator"]) != str(self._tg_id):
                        continue

                    if note.lower() in message.raw_text.lower():
                        txt = note_info["text"]
                        self._ratelimit["notes"][str(user_id)] = time.time() + 3

                        if not txt.startswith("@inline"):
                            await utils.answer(message, txt)
                            break

                        txt = "\n".join(txt.splitlines()[1:])
                        buttons = []
                        button_re = r"\[(.+)\]\((https?://.*)\)"
                        txt_r = []
                        for line in txt.splitlines():
                            if re.match(button_re, re.sub(r"<.*?>", "", line).strip()):
                                match = re.search(
                                    button_re, re.sub(r"<.*?>", "", line).strip()
                                )
                                buttons += [
                                    [{"text": match.group(1), "url": match.group(2)}]
                                ]
                            else:
                                txt_r += [line]

                        if not buttons:
                            await utils.answer(message, txt)
                            break

                        await self.inline.form(
                            message=message,
                            text="\n".join(txt_r),
                            reply_markup=buttons,
                            silent=True,
                        )

            if int(user_id) in (
                list(map(int, self.api.feds[fed]["fdef"]))
                + list(self._linked_channels.values())
            ):
                return

        if str(chat_id) not in self.api.chats or not self.api.chats[str(chat_id)]:
            return

        try:
            user = await self._client.get_entity(user_id)
        except ValueError:
            return

        chat = await message.get_chat()
        user_name = get_full_name(user)

        args = (chat_id, user_id, user, message)

        await self.p__report(*args)

        try:
            if (
                await self._client.get_perms_cached(chat_id, message.sender_id)
            ).is_admin:
                return
        except Exception:
            pass

        if await self.p__antiraid(*args, chat):
            return

        cas_result = False
        if self.api.should_protect(chat_id, "cas"):
            cas_result = await self.p__cas(*args, chat)

        if cas_result:
            await self.punish(
                chat_id,
                user,
                "cas",
                cas_result,
                user_name,
                message=message,
            )
            return

        r = await self.p__antiarab(*args)
        if r:
            await self.punish(
                chat_id,
                user,
                "arabic_nickname",
                r,
                user_name,
                message=message,
            )
            return

        if await self.p__welcome(*args, chat) and not self.api.should_protect(
            chat_id,
            "captcha",
        ):
            return

        if await self.p__captcha(*args, chat):
            return

        if getattr(message, "action", ""):
            return

        await self.p__report(*args)

        r = await self.p__bnd(*args)
        if r:
            await self.punish(chat_id, user, "bnd", r, user_name, message=message)
            return

        r = await self.p__antiflood(*args)
        if r:
            await self.punish(chat_id, user, "flood", r, user_name, message=message)
            return

        if await self.p__antichannel(*args):
            return

        r = await self.p__antizalgo(*args)
        if r:
            await self.punish(chat_id, user, "zalgo", r, user_name, message=message)
            return

        if await self.p__antigif(*args):
            return

        r = await self.p__antilagsticks(*args)
        if r:
            await self.punish(
                chat_id, user, "destructive_stick", "ban", user_name, message=message
            )
            return

        r = await self.p__antistick(*args)
        if r:
            await self.punish(chat_id, user, "stick", r, user_name, message=message)
            return

        if await self.p__antispoiler(*args):
            return

        r = await self.p__antiexplicit(*args)
        if r:
            await self.punish(chat_id, user, "explicit", r, user_name, message=message)
            return

        r = await self.p__antinsfw(*args)
        if r:
            await self.punish(
                chat_id,
                user,
                "nsfw_content",
                r,
                user_name,
                message=message,
            )
            return

        r = await self.p__antitagall(*args)
        if r:
            await self.punish(chat_id, user, "tagall", r, user_name, message=message)
            return

        await self.p__antihelp(*args)

    async def client_ready(
        self,
        client: "CustomTelegramClient",  # type: ignore
        db: "hikka.database.Database",  # type: ignore
    ):
        """Entry point"""
        global api

        self._is_inline = self.inline.init_complete

        self._sticks_limit = 7

        self._join_ratelimit = self.get("join_ratelimit", {})
        self._flood_cache = self.get("flood_cache", {})

        self.api = api
        await api.init(client, db, self)

        for protection in self.api.variables["protections"]:
            setattr(self, f"{protection}cmd", self.protection_template(protection))

        # We can override class docstings because of abc meta
        self.__doc__ = (
            "Advanced chat admin toolkit\nNow became free...\n\n💻 Developer:"
            " t.me/hikariatama\n📣"
            " Downloaded from: @hikarimods\n\n"
            + f"📦Version: {version}\n"
            + ("🗃 Local" if not self.api._inited else "⭐️ Full")
        )

        self._pt_task = asyncio.ensure_future(self._global_queue_handler())

        if PIL_AVAILABLE:
            asyncio.ensure_future(self._download_font())

    async def _download_font(self):
        self.font = (
            await utils.run_sync(
                requests.get,
                "https://github.com/hikariatama/assets/raw/master/EversonMono.ttf",
            )
        ).content
