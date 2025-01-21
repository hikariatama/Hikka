# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import difflib
import json
import logging
from typing import Dict, Literal, Optional, TypeVar, List, Tuple, Union
from dataclasses import dataclass

import requests
from hikkatl.tl.types import Message
from hikkatl.utils import resolve_inline_message_id

from .. import loader, utils
from ..types import InlineCall, InlineQuery

logger = logging.getLogger(__name__)

T = TypeVar("T")


def array_sum(array: List[List[T]]) -> List[T]:
    """Performs basic sum operation on array"""
    result: List[T] = []
    for item in array:
        result += item

    return result


@dataclass
class HetaModule:
    name: str
    repo: str
    link: str
    libs: List[str]
    hash: str
    commands: Dict[str, str]
    pic: Optional[str]
    banner: Optional[str]
    cls_doc: str


@loader.tds
class NewUnitHeta(loader.Module):
    """Manages stuff with heta.dan.tatar"""

    strings = {
        "name": "NewUnitHeta",
        "no_query": "<emoji document_id=5210952531676504517>❌</emoji> <b>You must specify query</b>",
        "no_results": "<emoji document_id=5210952531676504517>❌</emoji> <b>No results</b>",
        "api_error": "<emoji document_id=5210952531676504517>❌</emoji> <b>API is having issues</b>",
        "result": "🥰 <b>Results for</b> <code>{query}</code><b>:</b>\n\n🧳 <code>{name}</code> <b>by</b> <code>{dev}</code>\n👨‍🏫 <i>{cls_doc}</i>\n\n📚 <b>Commands:</b>\n{commands}\n\n🔗 <b>Install:</b> <code>{prefix}ndlh {mhash}</code>",
        "install": "🪄 Install",
        "loaded": "✅ Sucessfully installed",
        "not_loaded": "❌ Installation failed",
        "language": "en",
        "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Module not found</b>",
        "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>No exact match has been found, so the closest result is shown instead</b>",
        "link": '<emoji document_id=5280658777148760247>🌐</emoji> <b><a href="{url}">Link</a> of</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}',
        "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>File of</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>in reply to this message to install</b>\n\n{not_exact}",
        "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>You must specify arguments</b>",
        "_cmd_doc_heta": "<query> - Searches Heta repository for modules",
        "_cmd_doc_ml": "<module name> - Send link to module",
        "_cls_doc": "Manages stuff with @hikkamods_bot",
        "enter_search_query": "🔎 Enter search query",
        "search_query_desc": "Command, module name, description, etc.",
        "_ihandle_doc_heta": "Searches Heta repository for modules",
        "enter_hash": "<emoji document_id=5210952531676504517>❌</emoji> <b>You must specify hash</b>",
        "resolving_hash": "<emoji document_id=5325731315004218660>⏳</emoji> <b>Resolving hash...</b>",
        "installing_from_hash": "<emoji document_id=5325731315004218660>⏳</emoji> <b>Installing module</b> <code>{}</code> <b>...</b>",
        "installed": "<emoji document_id=5398001711786762757>✅</emoji> <b>Installed</b> <code>{}</code>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Error while installing module</b>",
        "_cmd_doc_ndlh": "<hash> - Install module from hash",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "translate",
                True,
                (
                    "Do you want to translate module descriptions and command docs to"
                    " the language, specified in Hikka? (This option is experimental,"
                    " and might not work properly)"
                ),
                validator=loader.validators.Boolean(),
            ),
        )

    async def client_ready(self):
        self._hetadb: List[HetaModule] = list(
            map(
                lambda x: HetaModule(
                    **{
                        **x,
                        "link": x["link"].replace("hikariatama.ru", "dan.tatar"),
                        "libs": list(
                            map(
                                lambda y: y[:-3].replace("hikariatama.ru", "dan.tatar"),
                                x["libs"],
                            )
                        ),
                    }
                ),
                json.loads(
                    (
                        await utils.run_sync(
                            requests.get,
                            "https://heta.dan.tatar/modules.json",
                        )
                    ).text
                ),
            )
        )
        self._raw_repos = [
            "hikariatama/ftg",
            "MoriSummerz/ftg-mods",
            "vsecoder/hikka_modules",
            "AmoreForever/amoremods",
            "DziruModules/hikkamods",
            "Codwizer/ReModules",
            "kamolgks/Hikkamods",
            "thomasmod/hikkamods",
            "sqlmerr/hikka_mods",
            "N3rcy/modules",
            "dorotorothequickend/DorotoroModules",
            "anon97945/hikka-mods",
            "GD-alt/mm-hikka-mods",
            "SkillsAngels/Modules",
            "shadowhikka/sh.modules",
            "Den4ikSuperOstryyPer4ik/Astro-modules",
            "GeekTG/FTG-Modules",
            "SekaiYoneya/Friendly-telegram",
            "iamnalinor/FTG-modules",
            "blazedzn/ftg-modules",
            "skillzmeow/skillzmods_hikka",
            "HitaloSama/FTG-modules-repo",
            "D4n13l3k00/FTG-Modules",
            "Fl1yd/FTG-Modules",
            "Ijidishurka/modules",
            "trololo65/Modules",
            "AlpacaGang/ftg-modules",
            "KeyZenD/modules",
            "Yahikoro/Modules-for-FTG",
            "Sad0ff/modules-ftg",
            "m4xx1m/FTG",
            "CakesTwix/Hikka-Modules",
        ]

    def _search_by_command(self, query: str) -> List[Tuple[HetaModule, float]]:
        results: List[Tuple[HetaModule, float]] = array_sum(
            [
                [
                    (module, difflib.SequenceMatcher(None, query, command).ratio())
                    for command in module.commands
                    if difflib.SequenceMatcher(None, query, command).ratio() >= 0.6
                ]
                for module in self._hetadb
            ]
        )

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _search_by_command_doc(self, query: str) -> List[Tuple[HetaModule, float]]:
        results: List[Tuple[HetaModule, float]] = array_sum(
            [
                [
                    (module, difflib.SequenceMatcher(None, query, command_doc).ratio())
                    for command_doc in module.commands.values()
                ]
                for module in self._hetadb
            ]
        )

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _search_by_module_name(self, query: str) -> List[Tuple[HetaModule, float]]:
        results: List[Tuple[HetaModule, float]] = array_sum(
            [
                [(module, difflib.SequenceMatcher(None, query, module.name).ratio())]
                for module in self._hetadb
                if difflib.SequenceMatcher(None, query, module.name).ratio() >= 0.4
            ]
        )

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _search_by_module_doc(self, query: str) -> List[Tuple[HetaModule, float]]:
        results: List[Tuple[HetaModule, float]] = array_sum(
            [
                [(module, difflib.SequenceMatcher(None, query, module.cls_doc).ratio())]
                for module in self._hetadb
            ]
        )

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _search_by_developer(self, query: str) -> List[Tuple[HetaModule, float]]:
        results: List[Tuple[HetaModule, float]] = array_sum(
            [
                [(module, 1)]
                for module in self._hetadb
                if query.lower() == module.repo.split("/")[0].lower()
            ]
        )

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _search(self, query: str) -> List[Tuple[str, HetaModule, float]]:
        if mod := next(
            (module for module in self._hetadb if module.hash == query), None
        ):
            return [("Hash", mod, 1)]

        raw_results = array_sum(
            [
                [
                    ("Command name", *result)
                    for result in self._search_by_command(query)
                ],
                [
                    ("Command doc", *result)
                    for result in self._search_by_command_doc(query)
                ],
                [
                    ("Module name", *result)
                    for result in self._search_by_module_name(query)
                ],
                [
                    ("Module doc", *result)
                    for result in self._search_by_module_doc(query)
                ],
                [("Developer", *result) for result in self._search_by_developer(query)],
            ]
        )

        return raw_results

    def search(
        self,
        query: str,
        page: Union[int, Literal[False]] = 0,
    ) -> Optional[
        Union[Tuple[str, HetaModule, float], List[Tuple[str, HetaModule, float]]]
    ]:
        raw_results = self._search(query)
        raw_results.sort(
            key=lambda x: x[2],
            reverse=True,
        )

        results: List[Tuple[str, HetaModule, float]] = []
        for result in raw_results:
            if not any(found[1].link == result[1].link for found in results):
                results.append(result)

        results.sort(
            key=lambda x: (
                x[2],
                self._raw_repos.index(x[1].repo),
            ),
            reverse=True,
        )

        if page is not False:
            if page >= len(results):
                return None

            return results[page]

        return results

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
    async def nhetacmd(self, message: Message):
        """
        <query> - Searches Heta repository for modules
        """

        if not (query := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("no_query"))
            return

        result = self.search(query)
        if not result:
            await utils.answer(message, self.strings("no_results"))
            return

        text = self._format_result(result[1], query)

        mark = lambda text: {  # noqa: E731
            "text": self.strings("install"),
            "callback": self._install,
            "args": (result[1].link, text),
        }

        form = await self.inline.form(
            message=message,
            text=text,
            **({"photo": result[1].banner} if result[1].banner else {}),
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
        dl_id: Optional[int] = None,
    ) -> bool:
        loader_m = self.lookup("loader")
        await loader_m.download_and_install(url, None)

        if getattr(loader_m, "fully_loaded", False):
            loader_m.update_modules_in_db()

        loaded = any(mod.__origin__ == url for mod in self.allmodules.modules)

        if dl_id:
            if loaded:
                await self._client.inline_query(
                    "@hikkamods_bot",
                    f"#confirm_load {dl_id}",
                )
            else:
                await self._client.inline_query(
                    "@hikkamods_bot",
                    f"#confirm_fload {dl_id}",
                )

        return loaded

    def _format_result(
        self,
        module: HetaModule,
        query: str,
        no_translate: bool = False,
    ) -> str:
        commands = "\n".join(
            [
                f"▫️ <code>{utils.escape_html(self.get_prefix())}{utils.escape_html(cmd)}</code>:"
                f" <b>{utils.escape_html(cmd_doc)}</b>"
                for cmd, cmd_doc in module.commands.items()
            ]
        )

        kwargs = {
            "name": utils.escape_html(module.name),
            "dev": utils.escape_html(module.repo),
            "commands": commands,
            "cls_doc": utils.escape_html(module.cls_doc),
            "mhash": module.hash,
            "query": utils.escape_html(query),
            "prefix": utils.escape_html(self.get_prefix()),
        }

        strings = (
            self.strings.get("result", "en")
            if self.config["translate"] and not no_translate
            else self.strings("result")
        )

        text = strings.format(**kwargs)

        if len(text) > 2048:
            kwargs["commands"] = "..."
            text = strings.format(**kwargs)

        return text

    @loader.inline_handler(thumb_url="https://img.icons8.com/color/512/hexa.png")
    async def nheta(self, query: InlineQuery) -> Union[List[dict], dict]:
        """
        <query> - Searches Heta repository for modules
        """

        if not query.args:
            return {
                "title": self.strings("enter_search_query"),
                "description": self.strings("search_query_desc"),
                "message": self.strings("enter_search_query"),
                "thumb": "https://img.icons8.com/color/512/hexa.png",
            }

        res = self.search(query.args, False)
        if not res:
            return {
                "title": utils.remove_html(self.strings("no_results")),
                "message": self.inline.sanitise_text(self.strings("no_results")),
                "thumb": "https://img.icons8.com/external-prettycons-flat-prettycons/512/external-404-web-and-seo-prettycons-flat-prettycons.png",
            }

        res = res[:50]

        return [
            {
                "title": utils.escape_html(module[1].name),
                "description": utils.escape_html(module[1].cls_doc),
                "message": self.inline.sanitise_text(
                    self._format_result(module[1], query.args, True)
                ),
                "thumb": module[1].pic,
                "reply_markup": {
                    "text": self.strings("install"),
                    "callback": self._install,
                    "args": (
                        module[1].link,
                        self._format_result(module[1], query.args, True),
                    ),
                },
            }
            for module in res
        ]

    @loader.command()
    async def ndlh(self, message: Message):
        """
        <hash> - Install module from hash
        """

        if not (mhash := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("enter_hash"))
            return

        message = await utils.answer(message, self.strings("resolving_hash"))

        res = next(
            (module for module in self._hetadb if module.hash == mhash),
            None,
        )
        if not res:
            await utils.answer(message, self.strings("404"))
            return

        message = await utils.answer(
            message,
            self.strings("installing_from_hash").format(
                utils.escape_html(res.name),
            ),
        )

        if await self._load_module(res.link):
            await utils.answer(
                message,
                self.strings("installed").format(utils.escape_html(res.name)),
            )
        else:
            await utils.answer(message, self.strings("error"))
