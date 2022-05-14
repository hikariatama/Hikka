"""Loads and registers modules"""

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: inline

import asyncio
import importlib
import inspect
import logging
import os
import re
import ast
import sys
import uuid
from collections import ChainMap
from importlib.machinery import ModuleSpec
from typing import Optional, Union
from urllib.parse import urlparse

import requests
import telethon
from telethon.tl.types import Message

from .. import loader, main, utils
from ..compat import geek
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

VALID_URL = r"[-[\]_.~:/?#@!$&'()*+,;%<=>a-zA-Z0-9]+"

VALID_PIP_PACKAGES = re.compile(
    r"^\s*# ?requires:(?: ?)((?:{url} )*(?:{url}))\s*$".format(url=VALID_URL),
    re.MULTILINE,
)

USER_INSTALL = "PIP_TARGET" not in os.environ and "VIRTUAL_ENV" not in os.environ

GIT_REGEX = re.compile(
    r"^https?://github\.com((?:/[a-z0-9-]+){2})(?:/tree/([a-z0-9-]+)((?:/[a-z0-9-]+)*))?/?$",
    flags=re.IGNORECASE,
)


def unescape_percent(text):
    i = 0
    ln = len(text)
    is_handling_percent = False
    out = ""

    while i < ln:
        char = text[i]

        if char == "%" and not is_handling_percent:
            is_handling_percent = True
            i += 1
            continue

        if char == "d" and is_handling_percent:
            out += "."
            is_handling_percent = False
            i += 1
            continue

        out += char
        is_handling_percent = False
        i += 1

    return out


def get_git_api(url):
    m = GIT_REGEX.search(url)

    if m is None:
        return None

    branch = m.group(2)
    path_ = m.group(3)
    api_url = f"https://api.github.com/repos{m.group(1)}/contents"

    if path_ is not None and len(path_) > 0:
        api_url += path_

    if branch:
        api_url += f"?ref={branch}"

    return api_url


@loader.tds
class LoaderMod(loader.Module):
    """Loads modules"""

    strings = {
        "name": "Loader",
        "repo_config_doc": "Fully qualified URL to a module repo",
        "avail_header": "<b>📲 Official modules from repo</b>",
        "select_preset": "<b>⚠️ Please select a preset</b>",
        "no_preset": "<b>🚫 Preset not found</b>",
        "preset_loaded": "<b>✅ Preset loaded</b>",
        "no_module": "<b>🚫 Module not available in repo.</b>",
        "no_file": "<b>🚫 File not found</b>",
        "provide_module": "<b>⚠️ Provide a module to load</b>",
        "bad_unicode": "<b>🚫 Invalid Unicode formatting in module</b>",
        "load_failed": "<b>🚫 Loading failed. See logs for details</b>",
        "loaded": "<b>🔭 Module </b><code>{}</code>{}<b> loaded {}</b>{}",
        "no_class": "<b>What class needs to be unloaded?</b>",
        "unloaded": "<b>🧹 Module unloaded.</b>",
        "not_unloaded": "<b>🚫 Module not unloaded.</b>",
        "requirements_failed": "<b>🚫 Requirements installation failed</b>",
        "requirements_installing": "<b>🔄 Installing requirements...</b>",
        "requirements_restart": "<b>🔄 Requirements installed, but a restart is required</b>",
        "all_modules_deleted": "<b>✅ All modules deleted</b>",
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 No docs",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 No docs",
        "inline_init_failed": (
            "🚫 <b>This module requires Hikka inline feature and "
            "initialization of InlineManager failed</b>\n"
            "<i>Please, remove one of your old bots from @BotFather and "
            "restart userbot to load this module</i>"
        ),
        "version_incompatible": "🚫 <b>This module requires Hikka {}+\nPlease, update with </b><code>.update</code>",
        "ffmpeg_required": "🚫 <b>This module requires FFMPEG, which is not installed</b>",
        "developer": "\n\n💻 <b>Developer: </b><code>{}</code>",
        "module_fs": "💿 <b>Would you like to save this module to filesystem, so it won't get unloaded after restart?</b>",
        "save": "💿 Save",
        "no_save": "🚫 Don't save",
        "save_for_all": "💽 Always save to fs",
        "never_save": "🚫 Never save to fs",
        "will_save_fs": "💽 Now all modules, loaded with .loadmod will be saved to filesystem",
        "add_repo_config_doc": "Additional repos to load from, separated with «|»",
    }

    strings_ru = {
        "repo_config_doc": "Ссылка для загрузки модулей",
        "add_repo_config_doc": "Дополнительные репозитории, разделенные «|»",
        "avail_header": "<b>📲 Официальные модули из репозитория</b>",
        "select_preset": "<b>⚠️ Выбери пресет</b>",
        "no_preset": "<b>🚫 Пресет не найден</b>",
        "preset_loaded": "<b>✅ Пресет загружен</b>",
        "no_module": "<b>🚫 Модуль недоступен в репозитории.</b>",
        "no_file": "<b>🚫 Файл не найден</b>",
        "provide_module": "<b>⚠️ Укажи модуль для загрузки</b>",
        "bad_unicode": "<b>🚫 Неверная кодировка модуля</b>",
        "load_failed": "<b>🚫 Загрузка не увенчалась успехом. Смотри логи.</b>",
        "loaded": "<b>🔭 Модуль </b><code>{}</code>{}<b> загружен {}</b>{}",
        "no_class": "<b>А что выгружать то?</b>",
        "unloaded": "<b>🧹 Модуль выгружен.</b>",
        "not_unloaded": "<b>🚫 Модуль не выгружен.</b>",
        "requirements_failed": "<b>🚫 Ошибка установки зависимостей</b>",
        "requirements_installing": "<b>🔄 Устанавливаю зависимости...</b>",
        "requirements_restart": "<b>🔄 Зависимости установлены, но нужна перезагрузка</b>",
        "all_modules_deleted": "<b>✅ Модули удалены</b>",
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 Нет описания",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 Нет описания",
        "version_incompatible": "🚫 <b>Этому модулю требуется Hikka версии {}+\nОбновись с помощью </b><code>.update</code>",
        "ffmpeg_required": "🚫 <b>Этому модулю требуется FFMPEG, который не установлен</b>",
        "developer": "\n\n💻 <b>Разработчик: </b><code>{}</code>",
        "module_fs": "💿 <b>Ты хочешь сохранить модуль на жесткий диск, чтобы он не выгружался при перезагрузке?</b>",
        "save": "💿 Сохранить",
        "no_save": "🚫 Не сохранять",
        "save_for_all": "💽 Всегда сохранять",
        "never_save": "🚫 Никогда не сохранять",
        "will_save_fs": "💽 Теперь все модули, загруженные из файла, будут сохраняться на жесткий диск",
        "inline_init_failed": "🚫 <b>Этому модулю нужен HikkaInline, а инициализация менеджера инлайна неудачна</b>\n<i>Попробуй удалить одного из старых ботов в @BotFather и перезагрузить юзербота</i>",
        "_cmd_doc_dlmod": "Скачивает и устаналвивает модуль из репозитория",
        "_cmd_doc_dlpreset": "Скачивает и устанавливает определенный набор модулей",
        "_cmd_doc_loadmod": "Скачивает и устанавливает модуль из файла",
        "_cmd_doc_unloadmod": "Выгружает (удаляет) модуль",
        "_cmd_doc_clearmodules": "Выгружает все установленные модули",
        "_cls_doc": "Загружает модули",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "MODULES_REPO",
                "https://mods.hikariatama.ru/",
                lambda: self.strings("repo_config_doc"),
            ),
            loader.ConfigValue(
                "ADDITIONAL_REPOS",
                # Currenly the trusted developers are specified
                (
                    "https://github.com/hikariatama/host/raw/master/|"
                    "https://github.com/MoriSummerz/ftg-mods/raw/main/|"
                    "https://gitlab.com/CakesTwix/friendly-userbot-modules/-/raw/master/"
                ),
                lambda: self.strings("add_repo_config_doc"),
            ),
        )

    def _update_modules_in_db(self) -> None:
        self.set(
            "loaded_modules",
            {
                module.__class__.__name__: module.__origin__
                for module in self.allmodules.modules
                if module.__origin__.startswith("http")
            },
        )

    @loader.owner
    async def dlmodcmd(self, message: Message) -> None:
        """Downloads and installs a module from the official module repo"""
        if args := utils.get_args(message):
            args = args[0]

            await self.download_and_install(args, message)
            self._update_modules_in_db()
        else:
            await self.inline.list(
                message,
                [
                    self.strings("avail_header")
                    + f"\n☁️ {repo.strip('/')}\n\n"
                    + "\n".join(
                        [
                            " | ".join(chunk)
                            for chunk in utils.chunks(
                                [
                                    f"<code>{i}</code>"
                                    for i in sorted(
                                        [
                                            utils.escape_html(
                                                i.split("/")[-1].split(".")[0]
                                            )
                                            for i in mods.values()
                                        ]
                                    )
                                ],
                                5,
                            )
                        ]
                    )
                    for repo, mods in (await self.get_repo_list("full")).items()
                ],
            )

    @loader.owner
    async def dlpresetcmd(self, message: Message) -> None:
        """Set modules preset"""
        args = utils.get_args(message)

        if not args:
            await utils.answer(message, self.strings("select_preset"))
            return

        try:
            await self.get_repo_list(args[0])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                await utils.answer(message, self.strings("no_preset"))
                return

            raise

        self.set("chosen_preset", args[0])
        self.set("loaded_modules", {})

        await utils.answer(message, self.strings("preset_loaded"))
        await self.allmodules.commands["restart"](
            await message.reply(f"{self.get_prefix()}restart --force")
        )

    async def _get_modules_to_load(self):
        preset = self.get("chosen_preset", None)

        if preset != "disable":
            possible_mods = (
                await self.get_repo_list(preset)
            ).values()
            todo = dict(ChainMap(*possible_mods))
        else:
            todo = {}

        todo.update(**self.get("loaded_modules", {}))
        return todo

    async def _get_repo(self, repo: str, preset: str) -> str:
        res = await utils.run_sync(
            requests.get,
            f'{repo.strip("/")}/{preset}.txt',
        )
        if not str(res.status_code).startswith("2"):
            logger.debug(f"Can't load {repo=}, {preset=}, {res.status_code=}")
            return ""

        return res.text

    async def get_repo_list(self, preset: Optional[str] = None):
        if preset is None or preset == "none":
            preset = "minimal"

        return {
            repo: {
                f"Preset_mod_{repo_id}_{i}": f'{repo.strip("/")}/{link}.py'
                for i, link in enumerate(
                    set(
                        filter(
                            lambda x: x,
                            (await self._get_repo(repo, preset)).split("\n"),
                        )
                    )
                )
            }
            for repo_id, repo in enumerate(
                [self.config["MODULES_REPO"]]
                + self.config["ADDITIONAL_REPOS"].split("|")
            )
            if repo.startswith("http")
        }

    async def get_links_list(self):
        def converter(repo_dict: dict) -> list:
            return list(dict(ChainMap(*list(repo_dict.values()))).values())

        links = await self.get_repo_list("full")
        # Make `MODULES_REPO` primary one
        main_repo = list(links[self.config["MODULES_REPO"]].values())
        del links[self.config["MODULES_REPO"]]
        return main_repo + converter(links)

    async def download_and_install(
        self,
        module_name: str,
        message: Optional[Message] = None,
    ):
        try:
            if urlparse(module_name).netloc:
                url = module_name
            else:
                links = await self.get_links_list()

                try:
                    url = next(
                        link
                        for link in links
                        if link.lower().endswith(f"{module_name.lower()}.py")
                    )
                except Exception:
                    if message is not None:
                        await utils.answer(message, self.strings("no_module"))

                    return False

            r = await utils.run_sync(requests.get, url)

            if r.status_code == 404:
                if message is not None:
                    await utils.answer(message, self.strings("no_module"))

                return False

            r.raise_for_status()
            return await self.load_module(
                r.content.decode("utf-8"),
                message,
                module_name,
                url,
            )
        except Exception:
            logger.exception(f"Failed to load {module_name}")

    async def _inline__load(
        self,
        call: InlineCall,
        doc: str,
        path_: Union[str, None],
        mode: str,
    ) -> None:
        save = False
        if mode == "all_yes":
            self._db.set(main.__name__, "permanent_modules_fs", True)
            self._db.set(main.__name__, "disable_modules_fs", False)
            await call.answer(self.strings("will_save_fs"))
            save = True
        elif mode == "all_no":
            self._db.set(main.__name__, "disable_modules_fs", True)
            self._db.set(main.__name__, "permanent_modules_fs", False)
        elif mode == "once":
            save = True

        if path_ is not None:
            await self.load_module(doc, call, origin=path_, save_fs=save)
        else:
            await self.load_module(doc, call, save_fs=save)

    @loader.owner
    async def loadmodcmd(self, message: Message) -> None:
        """Loads the module file"""
        msg = message if message.file else (await message.get_reply_message())

        if msg is None or msg.media is None:
            if args := utils.get_args(message):
                try:
                    path_ = args[0]
                    with open(path_, "rb") as f:
                        doc = f.read()
                except FileNotFoundError:
                    await utils.answer(message, self.strings("no_file"))
                    return
            else:
                await utils.answer(message, self.strings("provide_module"))
                return
        else:
            path_ = None
            doc = await msg.download_media(bytes)

        logger.debug("Loading external module...")

        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await utils.answer(message, self.strings("bad_unicode"))
            return

        if not self._db.get(
            main.__name__,
            "disable_modules_fs",
            False,
        ) and not self._db.get(main.__name__, "permanent_modules_fs", False):
            if message.file:
                await message.edit("")
                message = await message.respond("🌘")

            if await self.inline.form(
                self.strings("module_fs"),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": self.strings("save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "once"),
                        },
                        {
                            "text": self.strings("no_save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "no"),
                        },
                    ],
                    [
                        {
                            "text": self.strings("save_for_all"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "all_yes"),
                        }
                    ],
                    [
                        {
                            "text": self.strings("never_save"),
                            "callback": self._inline__load,
                            "args": (doc, path_, "all_no"),
                        }
                    ],
                ],
            ):
                return

        if path_ is not None:
            await self.load_module(
                doc,
                message,
                origin=path_,
                save_fs=self._db.get(main.__name__, "permanent_modules_fs", False)
                and not self._db.get(main.__name__, "disable_modules_fs", False),
            )
        else:
            await self.load_module(
                doc,
                message,
                save_fs=self._db.get(main.__name__, "permanent_modules_fs", False)
                and not self._db.get(main.__name__, "disable_modules_fs", False),
            )

    async def load_module(
        self,
        doc: str,
        message: Message,
        name: Optional[Union[str, None]] = None,
        origin: Optional[str] = "<string>",
        did_requirements: Optional[bool] = False,
        save_fs: Optional[bool] = False,
    ) -> None:
        if any(
            line.replace(" ", "") == "#scope:ffmpeg" for line in doc.splitlines()
        ) and os.system("ffmpeg -version 1>/dev/null 2>/dev/null"):
            if isinstance(message, Message):
                await utils.answer(message, self.strings("ffmpeg_required"))
            return

        if (
            any(line.replace(" ", "") == "#scope:inline" for line in doc.splitlines())
            and not self.inline.init_complete
        ):
            if isinstance(message, Message):
                await utils.answer(message, self.strings("inline_init_failed"))
            return

        if re.search(r"# ?scope: ?hikka_min", doc):
            ver = re.search(
                r"# ?scope: ?hikka_min ([0-9]+\.[0-9]+\.[0-9]+)",
                doc,
            ).group(1)
            ver_ = tuple(map(int, ver.split(".")))
            if main.__version__ < ver_:
                if isinstance(message, Message):
                    await utils.answer(
                        message,
                        self.strings("version_incompatible").format(ver),
                    )
                return

        developer = re.search(r"# ?meta developer: ?(.+)", doc)
        developer = developer.group(1) if developer else False
        developer = (
            self.strings("developer").format(utils.escape_html(developer))
            if developer
            else ""
        )

        if name is None:
            try:
                node = ast.parse(doc)
                uid = next(n.name for n in node.body if isinstance(n, ast.ClassDef))
            except Exception:
                logger.debug(
                    "Can't parse classname from code, using legacy uid instead",
                    exc_info=True,
                )
                uid = "__extmod_" + str(uuid.uuid4())
        else:
            if name.startswith(self.config["MODULES_REPO"]):
                name = name.split("/")[-1].split(".py")[0]

            uid = name.replace("%", "%%").replace(".", "%d")

        module_name = f"hikka.modules.{uid}"

        doc = geek.compat(doc)

        try:
            try:
                spec = ModuleSpec(
                    module_name,
                    loader.StringLoader(doc, origin),
                    origin=origin,
                )
                instance = self.allmodules.register_module(
                    spec,
                    module_name,
                    origin,
                    save_fs=save_fs,
                )
            except ImportError as e:
                logger.info(
                    "Module loading failed, attemping dependency installation",
                    exc_info=True,
                )
                # Let's try to reinstall dependencies
                try:
                    requirements = list(
                        filter(
                            lambda x: x and x[0] not in {"-", "_", "."},
                            map(
                                str.strip,
                                VALID_PIP_PACKAGES.search(doc)[1].split(" "),
                            ),
                        )
                    )
                except TypeError:
                    logger.warning("No valid pip packages specified in code, attemping installation from error")  # fmt: skip
                    requirements = [e.name]

                logger.debug(f"Installing requirements: {requirements}")

                if not requirements:
                    raise Exception("Nothing to install") from e

                if did_requirements:
                    if message is not None:
                        await utils.answer(
                            message,
                            self.strings("requirements_restart"),
                        )

                    return

                if message is not None:
                    await utils.answer(
                        message,
                        self.strings("requirements_installing"),
                    )

                pip = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-q",
                    "--disable-pip-version-check",
                    "--no-warn-script-location",
                    *["--user"] if USER_INSTALL else [],
                    *requirements,
                )

                rc = await pip.wait()

                if rc != 0:
                    if message is not None:
                        await utils.answer(
                            message,
                            self.strings("requirements_failed"),
                        )

                    return

                importlib.invalidate_caches()

                return await self.load_module(
                    doc,
                    message,
                    name,
                    origin,
                    True,
                    save_fs,
                )  # Try again
            except loader.LoadError as e:
                try:
                    self.allmodules.modules.remove(instance)  # skipcq: PYL-E0601
                except ValueError:
                    pass

                if message:
                    await utils.answer(message, f"🚫 <b>{utils.escape_html(str(e))}</b>")
                return
        except BaseException as e:
            logger.exception(f"Loading external module failed due to {e}")

            if message is not None:
                await utils.answer(message, self.strings("load_failed"))

            return

        instance.inline = self.inline

        if hasattr(instance, "__version__") and isinstance(instance.__version__, tuple):
            version = f"<b><i> (v{'.'.join(list(map(str, list(instance.__version__))))})</i></b>"
        else:
            version = ""

        try:
            try:
                self.allmodules.send_config_one(instance, self._db, self.translator)
                await self.allmodules.send_ready_one(
                    instance,
                    self._client,
                    self._db,
                    self.allclients,
                    no_self_unload=True,
                    from_dlmod=bool(message),
                )
            except loader.LoadError as e:
                try:
                    self.allmodules.modules.remove(instance)
                except ValueError:
                    pass

                if message:
                    await utils.answer(message, f"🚫 <b>{utils.escape_html(str(e))}</b>")
                return
            except loader.SelfUnload as e:
                logging.debug(f"Unloading {instance}, because it raised `SelfUnload`")
                try:
                    self.allmodules.modules.remove(instance)
                except ValueError:
                    pass

                if message:
                    await utils.answer(message, f"🚫 <b>{utils.escape_html(str(e))}</b>")
                return
        except Exception as e:
            logger.exception(f"Module threw because {e}")

            if message is not None:
                await utils.answer(message, self.strings("load_failed"))

            return

        if message is not None:
            try:
                modname = instance.strings("name")
            except KeyError:
                modname = getattr(instance, "name", "ERROR")

            modhelp = ""

            if instance.__doc__:
                modhelp += (
                    f"<i>\nℹ️ {utils.escape_html(inspect.getdoc(instance))}</i>\n"
                )

            if any(
                line.replace(" ", "") == "#scope:disable_onload_docs"
                for line in doc.splitlines()
            ):
                await utils.answer(
                    message,
                    self.strings("loaded").format(
                        modname.strip(),
                        version,
                        utils.ascii_face(),
                        modhelp,
                    )
                    + developer,
                )
                return

            for _name, fun in sorted(
                instance.commands.items(),
                key=lambda x: x[0],
            ):
                modhelp += self.strings("single_cmd").format(
                    self.get_prefix(),
                    _name,
                    (
                        utils.escape_html(inspect.getdoc(fun))
                        if fun.__doc__
                        else self.strings("undoc_cmd")
                    ),
                )

            if self.inline.init_complete:
                if hasattr(instance, "inline_handlers"):
                    for _name, fun in sorted(
                        instance.inline_handlers.items(),
                        key=lambda x: x[0],
                    ):
                        modhelp += self.strings("ihandler").format(
                            f"@{self.inline.bot_username} {_name}",
                            (
                                utils.escape_html(inspect.getdoc(fun))
                                if fun.__doc__
                                else self.strings("undoc_ihandler")
                            ),
                        )

            try:
                await utils.answer(
                    message,
                    self.strings("loaded").format(
                        modname.strip(),
                        version,
                        utils.ascii_face(),
                        modhelp,
                    )
                    + developer,
                )
            except telethon.errors.rpcerrorlist.MediaCaptionTooLongError:
                await message.reply(
                    self.strings("loaded").format(
                        modname.strip(),
                        version,
                        utils.ascii_face(),
                        modhelp,
                    )
                    + developer
                )

        return

    @loader.owner
    async def unloadmodcmd(self, message: Message) -> None:
        """Unload module by class name"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("no_class"))
            return

        worked = self.allmodules.unload_module(args)

        self.set(
            "loaded_modules",
            {
                mod: link
                for mod, link in self.get("loaded_modules", {}).items()
                if mod not in worked
            },
        )

        await utils.answer(
            message,
            self.strings("unloaded" if worked else "not_unloaded"),
        )

    @loader.owner
    async def clearmodulescmd(self, message: Message) -> None:
        """Delete all installed modules"""
        self.set("loaded_modules", {})

        for file in os.scandir(loader.LOADED_MODULES_DIR):
            os.remove(file)

        self.set("chosen_preset", "none")

        await utils.answer(message, self.strings("all_modules_deleted"))

        await self.allmodules.commands["restart"](
            await message.reply(f"{self.get_prefix()}restart --force")
        )

    async def _update_modules(self):
        todo = await self._get_modules_to_load()
        for mod in todo.values():
            await self.download_and_install(mod)

        self._update_modules_in_db()
        self._fully_loaded = True

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._fully_loaded = False

        main.hikka.ready.set()

        if not self.get("loaded_modules", False):
            self.set("loaded_modules", self._db.get(__name__, "loaded_modules", {}))
            self._db.set(__name__, "loaded_modules", {})

        # Legacy db migration
        if isinstance(self.get("loaded_modules", {}), list):
            self.set(
                "loaded_modules",
                {
                    f"Loaded_module_{i}": link
                    for i, link in enumerate(self.get("loaded_modules", {}))
                },
            )

        asyncio.ensure_future(self._update_modules())
        asyncio.ensure_future(self._modules_config_autosaver())

    async def _modules_config_autosaver(self):
        while True:
            await asyncio.sleep(3)
            for mod in self.allmodules.modules:
                if not hasattr(mod, "config") or not mod.config:
                    continue

                for option, config in mod.config._config.items():
                    if not hasattr(config, "_save_marker"):
                        continue

                    delattr(mod.config._config[option], "_save_marker")
                    self._db.setdefault(mod.__class__.__name__, {},).setdefault(
                        "__config__", {}
                    )[option] = config.value
