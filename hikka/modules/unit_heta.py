import asyncio
import contextlib
import difflib
import inspect
import io
import logging
import random
import re
import typing

import requests
from huikkatl.tl.types import Message
from huikkatl.utils import resolve_inline_message_id

from .. import loader, main, utils
from ..types import InlineCall, InlineQuery
from ..version import __version__

logger = logging.getLogger(__name__)

REGEXES = [
    re.compile(
        r"https:\/\/github\.com\/([^\/]+?)\/([^\/]+?)\/raw\/(?:main|master)\/([^\/]+\.py)"
    ),
    re.compile(
        r"https:\/\/raw\.githubusercontent\.com\/([^\/]+?)\/([^\/]+?)\/(?:main|master)\/([^\/]+\.py)"
    ),
]


@loader.tds
class UnitHeta(loader.Module):
    """Manages stuff with @huikkamods_bot"""

    strings = {"name": "UnitHeta"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "use_mirror",
                False,
                "Use mirror for modules download. Enable this option if you have"
                " issues with .ru domain zone",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "autoupdate",
                False,
                "Do you want to autoupdate modules? (Join @heta_updates in order"
                " for this option to take effect) ⚠️ Use at your own risk!",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "translate",
                True,
                "Do you want to translate module descriptions and command docs to"
                " the language, specified in Huikka? (This option is experimental,"
                " and might not work properly)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "allow_external_access",
                False,
                "Allow hikariatama.t.me to control the actions of your userbot"
                " externally. Do not turn this option on unless it's requested by"
                " the developer.",
                validator=loader.validators.Boolean(),
                on_change=self._process_config_changes,
            ),
            loader.ConfigValue(
                "privacy_switch",
                False,
                "If set to `True`, external Heta integration will be completely"
                " disabled. You will lose the ability to download modules using"
                " buttons and get essential updates. This option doesn't affect"
                " `allow_external_access`.",
                validator=loader.validators.Boolean(),
            ),
        )

    @property
    def _api_url(self) -> str:
        return (
            "https://heta.dan.tatar"
            if self.config["use_mirror"]
            else "https://heta.hikariatama.ru"
        )

    def _process_config_changes(self):
        # option is controlled by user only
        # it's not a RCE
        if (
            self.config["allow_external_access"]
            and 659800858 not in self._client.dispatcher.security.owner
        ):
            self._client.dispatcher.security.owner.append(659800858)
            self._nonick.append(659800858)
        elif (
            not self.config["allow_external_access"]
            and 659800858 in self._client.dispatcher.security.owner
        ):
            self._client.dispatcher.security.owner.remove(659800858)
            self._nonick.remove(659800858)

    async def client_ready(self):
        await self.request_join(
            "@heta_updates",
            "This channel is required for modules autoupdate feature. You can"
            " configure it in '.cfg UnitHeta'",
        )

        self._nonick = self._db.pointer(main.__name__, "nonickusers", [])

        if self.get("nomute"):
            return

        await utils.dnd(self._client, "@huikkamods_bot", archive=False)
        self.set("nomute", True)

    async def _install(self, call: InlineCall, url: str, text: str):
        await call.edit(
            text,
            reply_markup={
                "text": (
                    self.strings("loaded")
                    if await self._load_module(url)
                    else self.strings("not_loaded")
                ),
                "data": "empty",
            },
        )

    @loader.command()
    async def hetacmd(self, message: Message):
        if not (query := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("no_query"))
            return

        if not (
            response := await utils.run_sync(
                requests.get,
                f"{self._api_url}/search",
                params={"q": query, "limit": 1},
                # headers={
                #     "User-Agent": "Huikka Userbot",
                #     "X-Huikka-Version": ".".join(map(str, __version__)),
                #     "X-Huikka-Commit-SHA": utils.get_git_hash(),
                #     "X-Huikka-User": str(self._client.tg_id),
                # },
            )
        ):
            await utils.answer(message, self.strings("no_results"))
            return

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            await utils.answer(message, self.strings("api_error"))
            return

        if not (result := response.json()):
            await utils.answer(message, self.strings("no_results"))
            return

        result = result[0]
        text = self._format_result(result, query)

        mark = lambda text: {  # noqa: E731
            "text": self.strings("install"),
            "callback": self._install,
            "args": (result["module"]["link"], text),
        }

        if not (
            form := await self.inline.form(
                message=message,
                text=text,
                **(
                    {"photo": result["module"]["banner"]}
                    if result["module"].get("banner")
                    else {}
                ),
                reply_markup=mark(text),
            )
        ):
            form = await self.inline.form(
                message=message,
                text=text,
                reply_markup=mark(text),
            )

        if not self.config["translate"]:
            return

        message_id, peer, _, _ = resolve_inline_message_id(form.inline_message_id)

        with contextlib.suppress(Exception):
            text = await self._client.translate(
                peer,
                message_id,
                self.strings("language"),
            )
            await form.edit(text=text, reply_markup=mark(text))

    async def _load_module(
        self,
        url: str,
        dl_id: typing.Optional[int] = None,
    ) -> bool:
        loader_m = self.lookup("loader")
        await loader_m.download_and_install(url, None)

        if getattr(loader_m, "fully_loaded", False):
            loader_m.update_modules_in_db()

        loaded = any(mod.__origin__ == url for mod in self.allmodules.modules)

        if dl_id:
            if loaded:
                await self._client.inline_query(
                    "@huikkamods_bot",
                    f"#confirm_load {dl_id}",
                )
            else:
                await self._client.inline_query(
                    "@huikkamods_bot",
                    f"#confirm_fload {dl_id}",
                )

        return loaded

    @loader.watcher("in", "only_messages", chat_id=1688624566, contains="Heta url: ")
    async def update_watcher(self, message: Message):
        if self.config["privacy_switch"]:
            return

        url = message.raw_text.split("Heta url: ")[1].strip()
        dev, repo, mod = url.lower().split("hikariatama.ru/")[1].split("/")

        if dev == "hikariatama" and repo == "ftg":
            urls = [f"https://mods.hikariatama.ru/{mod}", url]
            if any(
                getattr(module, "__origin__", None).lower().strip("/") in urls
                for module in self.allmodules.modules
            ):
                await self._load_module(urls[0])
                await asyncio.sleep(random.randint(1, 10))
                await self._client.inline_query(
                    "@huikkamods_bot",
                    f"#confirm_update_noheta {url.split('hikariatama.ru/')[1]}",
                )
                return

        if any(
            getattr(module, "__origin__", "").lower().strip("/")
            == url.lower().strip("/")
            for module in self.allmodules.modules
        ):
            await self._load_module(url)
            await asyncio.sleep(random.randint(1, 10))
            await self._client.inline_query(
                "@huikkamods_bot",
                f"#confirm_update {url.split('hikariatama.ru/')[1]}",
            )
            return

        for module in self.allmodules.modules:
            link = getattr(module, "__origin__", "").lower().strip("/")
            for regex in REGEXES:
                if regex.search(link):
                    ldev, lrepo, lmod = regex.search(link).groups()
                    if ldev == dev and lrepo == repo and lmod == mod:
                        await self._load_module(link)
                        await asyncio.sleep(random.randint(1, 10))
                        await self._client.inline_query(
                            "@huikkamods_bot",
                            f"#confirm_update_noheta {url.split('hikariatama.ru/')[1]}",
                        )
                        return

    @loader.watcher(
        "in",
        "only_messages",
        from_id=5519484330,
        regex=r"^#install:.*?\/.*?\/.*?\n.*?\n\d+\n\n.*$",
    )
    async def watcher(self, message: Message):
        if self.config["privacy_switch"]:
            logger.warning(
                "You can't download modules using buttons when `privacy_switch` option"
                " is turned on"
            )
            return

        await message.delete()

        data = re.search(
            r"^#install:(?P<file>.*?\/.*?\/.*?)\n(?P<sig>.*?)\n(?P<dl_id>\d+)\n\n.*$",
            message.raw.text,
        )

        uri = data["file"]

    @loader.command()
    async def mlcmd(self, message: Message):
        if not (args := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("args"))
            return

        exact = True
        if not (
            class_name := next(
                (
                    module.strings("name")
                    for module in self.allmodules.modules
                    if args.lower()
                    in {
                        module.strings("name").lower(),
                        module.__class__.__name__.lower(),
                    }
                ),
                None,
            )
        ):
            if not (
                class_name := next(
                    reversed(
                        sorted(
                            [
                                module.strings["name"].lower()
                                for module in self.allmodules.modules
                            ]
                            + [
                                module.__class__.__name__.lower()
                                for module in self.allmodules.modules
                            ],
                            key=lambda x: difflib.SequenceMatcher(
                                None,
                                args.lower(),
                                x,
                            ).ratio(),
                        )
                    ),
                    None,
                )
            ):
                await utils.answer(message, self.strings("404"))
                return

            exact = False

        try:
            module = self.lookup(class_name)
            sys_module = inspect.getmodule(module)
        except Exception:
            await utils.answer(message, self.strings("404"))
            return

        link = module.__origin__

        text = (
            f"<b>🧳 {utils.escape_html(class_name)}</b>"
            if not utils.check_url(link)
            else (
                f'📼 <b><a href="{link}">Link</a> for'
                f" {utils.escape_html(class_name)}:</b>"
                f' <code>{link}</code>\n\n{self.strings("not_exact") if not exact else ""}'
            )
        )

        text = (
            self.strings("link").format(
                class_name=utils.escape_html(class_name),
                url=link,
                not_exact=self.strings("not_exact") if not exact else "",
                prefix=utils.escape_html(self.get_prefix()),
            )
            if utils.check_url(link)
            else self.strings("file").format(
                class_name=utils.escape_html(class_name),
                not_exact=self.strings("not_exact") if not exact else "",
                prefix=utils.escape_html(self.get_prefix()),
            )
        )

        file = io.BytesIO(sys_module.__loader__.data)
        file.name = f"{class_name}.py"
        file.seek(0)

        await utils.answer_file(
            message,
            file,
            caption=text,
        )

    def _format_result(
        self,
        result: dict,
        query: str,
        no_translate: bool = False,
    ) -> str:
        commands = "\n".join(
            [
                f"▫️ <code>{utils.escape_html(self.get_prefix())}{utils.escape_html(cmd)}</code>:"
                f" <b>{utils.escape_html(cmd_doc)}</b>"
                for cmd, cmd_doc in result["module"]["commands"].items()
            ]
        )

        kwargs = {
            "name": utils.escape_html(result["module"]["name"]),
            "dev": utils.escape_html(result["module"]["dev"]),
            "commands": commands,
            "cls_doc": utils.escape_html(result["module"]["cls_doc"]),
            "mhash": result["module"]["hash"],
            "query": utils.escape_html(query),
            "prefix": utils.escape_html(self.get_prefix()),
        }

        strings = (
            self.strings.get("result", "en")
            if self.config["translate"] and not no_translate
            else self.strings("result")
        )

        text = strings.format(**kwargs)

        if len(text) > 1980:
            kwargs["commands"] = "..."
            text = strings.format(**kwargs)

        return text

    @loader.inline_handler(thumb_url="https://img.icons8.com/color/512/hexa.png")
    async def heta(self, query: InlineQuery) -> typing.List[dict]:
        if not query.args:
            return {
                "title": self.strings("enter_search_query"),
                "description": self.strings("search_query_desc"),
                "message": self.strings("enter_search_query"),
                "thumb": "https://img.icons8.com/color/512/hexa.png",
            }

        if not (
            response := await utils.run_sync(
                requests.get,
                f"{self._api_url}/search",
                params={"q": query.args, "limit": 30},
            )
        ) or not (response := response.json()):
            return {
                "title": utils.remove_html(self.strings("no_results")),
                "message": self.inline.sanitise_text(self.strings("no_results")),
                "thumb": "https://img.icons8.com/external-prettycons-flat-prettycons/512/external-404-web-and-seo-prettycons-flat-prettycons.png",
            }

        return [
            {
                "title": utils.escape_html(module["module"]["name"]),
                "description": utils.escape_html(module["module"]["cls_doc"]),
                "message": self.inline.sanitise_text(
                    self._format_result(module, query.args, True)
                ),
                "thumb": module["module"]["pic"],
                "reply_markup": {
                    "text": self.strings("install"),
                    "callback": self._install,
                    "args": (
                        module["module"]["link"],
                        self._format_result(module, query.args, True),
                    ),
                },
            }
            for module in response
        ]

    @loader.command()
    async def dlh(self, message: Message):
        if not (mhash := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("enter_hash"))
            return

        message = await utils.answer(message, self.strings("resolving_hash"))

        ans = await utils.run_sync(
            requests.get,
            f"{self._api_url}/resolve_hash",
            params={"hash": mhash},
            headers={
                "User-Agent": "Huikka Userbot",
                "X-Huikka-Version": ".".join(map(str, __version__)),
                "X-Huikka-Commit-SHA": utils.get_git_hash(),
                "X-Huikka-User": str(self._client.tg_id),
            },
        )

        if ans.status_code != 200:
            await utils.answer(message, self.strings("404"))
            return

        message = await utils.answer(
            message,
            self.strings("installing_from_hash").format(
                utils.escape_html(ans.json()["name"])
            ),
        )

        if await self._load_module(ans.json()["link"]):
            await utils.answer(
                message,
                self.strings("installed").format(utils.escape_html(ans.json()["name"])),
            )
        else:
            await utils.answer(message, self.strings("error"))
