# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import base64
import difflib
import inspect
import io
import logging
import random
import re
import typing

import requests
import rsa
from hikkatl.tl.types import Message
from hikkatl.utils import resolve_inline_message_id

from .. import loader, utils
from ..types import InlineCall

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
    """Manages stuff with @hikkamods_bot"""

    e = "<emoji document_id=5210952531676504517>❌</emoji>"
    w = "<emoji document_id=5312383351217201533>⚠️</emoji>"
    moon = "<emoji document_id=5188377234380954537>🌘</emoji>"
    link = "<emoji document_id=5280658777148760247>🌐</emoji>"
    f = "<emoji document_id=5433653135799228968>📁</emoji>"

    strings = {
        "name": "UnitHeta",
        "no_query": f"{e} <b>You must specify query</b>",
        "no_results": f"{e} <b>No results</b>",
        "api_error": f"{e} <b>API is having issues</b>",
        "result": (
            "🥰 <b>Results for</b> <code>{query}</code><b>:</b>\n\n🧳 <code>{name}</code>"
            " <b>by</b> <code>{dev}</code>\n👨‍🏫 <i>{cls_doc}</i>\n\n📚"
            " <b>Commands:</b>\n{commands}\n\n🔗 <b>Install:</b> <code>{prefix}dlm"
            " {link}</code>"
        ),
        "install": "🪄 Install",
        "loaded": "✅ Sucessfully installed",
        "not_loaded": "❌ Installation failed",
        "language": "en",
        "404": f"{e} <b>Module not found</b>",
        "not_exact": (
            f"{w} <b>No exact match has been found, so the closest result is shown"
            " instead</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Link</a> of</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>File of</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>in"
            " reply to this message to install</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>You must specify arguments</b>",
    }

    strings_ru = {
        "no_query": f"{e} <b>Вы должны указать запрос</b>",
        "no_results": f"{e} <b>Нет результатов</b>",
        "api_error": f"{e} <b>С API случилась беда</b>",
        "result": (
            "🥰 <b>Результаты для</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>от</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Команды:</b>\n{commands}\n\n🔗 <b>Установить:</b>"
            " <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Установить",
        "loaded": "✅ Успешно установлено",
        "not_loaded": "❌ Установка не удалась",
        "language": "ru",
        "_cls_doc": "Управляет вещами, связанными с @hikkamods_bot",
        "404": f"{e} <b>Модуль не найден</b>",
        "not_exact": (
            f"{w} <b>Точного совпадения не найдено, поэтому показан ближайший"
            " результат</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Ссылка</a> на</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Файл</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>в"
            " ответ на это сообщение, чтобы установить</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Вы должны указать аргументы</b>",
    }

    strings_es = {
        "no_query": f"{e} <b>Debes especificar una consulta</b>",
        "no_results": f"{e} <b>No hay resultados</b>",
        "api_error": f"{e} <b>Hay problemas con la API</b>",
        "result": (
            "🥰 <b>Resultados para</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>por</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Comandos:</b>\n{commands}\n\n🔗 <b>Instalar:</b>"
            " <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Instalar",
        "loaded": "✅ Instalado con éxito",
        "not_loaded": "❌ La instalación falló",
        "language": "es",
        "_cls_doc": "Administra cosas relacionadas con @hikkamods_bot",
        "404": f"{e} <b>Módulo no encontrado</b>",
        "not_exact": (
            f"{w} <b>No se ha encontrado una coincidencia exacta, por lo que se muestra"
            " el resultado más cercano</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Enlace</a> de</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Archivo de</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>en"
            " respuesta a este mensaje para instalar</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Debes especificar argumentos</b>",
    }

    strings_de = {
        "no_query": f"{e} <b>Du musst eine Abfrage angeben</b>",
        "no_results": f"{e} <b>Keine Ergebnisse</b>",
        "api_error": f"{e} <b>Es gibt Probleme mit der API</b>",
        "result": (
            "🥰 <b>Ergebnisse für</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>von</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Befehle:</b>\n{commands}\n\n🔗"
            " <b>Installieren:</b> <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Installieren",
        "loaded": "✅ Erfolgreich installiert",
        "not_loaded": "❌ Die Installation ist fehlgeschlagen",
        "language": "de",
        "_cls_doc": "Verwaltet Dinge, die mit @hikkamods_bot zu tun haben",
        "404": f"{e} <b>Modul nicht gefunden</b>",
        "not_exact": (
            f"{w} <b>Es wurde keine exakte Übereinstimmung gefunden, daher wird"
            " stattdessen das nächstgelegene Ergebnis angezeigt</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Link</a> zu</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Datei</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>in"
            " Antwort auf diese Nachricht, um sie zu installieren</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Du musst Argumente angeben</b>",
    }

    strings_fr = {
        "no_query": f"{e} <b>Vous devez spécifier une requête</b>",
        "no_results": f"{e} <b>Aucun résultat</b>",
        "api_error": f"{e} <b>Quelque chose s'est mal passé avec l'API</b>",
        "result": (
            "🥰 <b>Résultats pour</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>par</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Commandes:</b>\n{commands}\n\n🔗"
            " <b>Installer:</b> <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Installer",
        "loaded": "✅ Installation réussie",
        "not_loaded": "❌ Installation échouée",
        "language": "fr",
        "_cls_doc": "Gère les choses liées à @hikkamods_bot",
        "404": f"{e} <b>Module introuvable</b>",
        "not_exact": (
            f"{w} <b>Aucune correspondance exacte n'a été trouvée, le résultat le plus"
            " proche est donc affiché</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Lien</a> vers</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Fichier</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>en"
            " réponse à ce message pour l'installer</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Vous devez spécifier des arguments</b>",
    }

    strings_uz = {
        "no_query": f"{e} <b>Siz so'rovni belgilamadingiz</b>",
        "no_results": f"{e} <b>Natija topilmadi</b>",
        "api_error": f"{e} <b>API bilan muammo yuz berdi</b>",
        "result": (
            "🥰 <b>Ushbu</b> <code>{query}</code><b>uchun natijalar:</b>\n\n🧳"
            " <code>{name}</code> <b>to'g'risida</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Komandalar:</b>\n{commands}\n\n🔗"
            " <b>O'rnatish:</b> <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 O'rnatish",
        "loaded": "✅ Muvaffaqiyatli o'rnatildi",
        "not_loaded": "❌ O'rnatish muvaffaqiyatsiz bo'ldi",
        "language": "uz",
        "_cls_doc": "@hikkamods_bot bilan bog'liq narsalarni boshqarish",
        "404": f"{e} <b>Modul topilmadi</b>",
        "not_exact": (
            f"{w} <b>To'g'ri mos keladigan natija topilmadi, shuning uchun eng yaqin"
            " natija ko'rsatiladi</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Havola</a> bo\'yicha</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Fayl</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>bu"
            " habarga javob qilib, uni o'rnatish uchun</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Siz argumentlarni belgilamadingiz</b>",
    }

    strings_tr = {
        "no_query": f"{e} <b>Bir sorgu belirtmelisiniz</b>",
        "no_results": f"{e} <b>Sonuç yok</b>",
        "api_error": f"{e} <b>API ile ilgili bir sorun oluştu</b>",
        "result": (
            "🥰 <b>Sonuçlar için</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>geliştirici</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Komutlar:</b>\n{commands}\n\n🔗 <b>Yükle:</b>"
            " <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Yükle",
        "loaded": "✅ Başarıyla yüklendi",
        "not_loaded": "❌ Yükleme başarısız oldu",
        "language": "tr",
        "_cls_doc": "@hikkamods_bot ile ilgili şeyleri yönetir",
        "404": f"{e} <b>Modül bulunamadı</b>",
        "not_exact": (
            f"{w} <b>Herhangi bir tam eşleşme bulunamadığından, en yakın sonuç"
            " gösteriliyor</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Bağlantı</a> için</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Dosya</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>bu"
            " mesaja yanıt olarak yüklemek için</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Argümanlar belirtmelisiniz</b>",
    }

    strings_it = {
        "no_query": f"{e} <b>Devi specificare una query</b>",
        "no_results": f"{e} <b>Nessun risultato</b>",
        "api_error": f"{e} <b>Si è verificato un'errore con l'API</b>",
        "result": (
            "🥰 <b>Risultati per</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>da</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Comandi:</b>\n{commands}\n\n🔗 <b>Installare:</b>"
            " <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Installare",
        "loaded": "✅ Installazione riuscita",
        "not_loaded": "❌ Installazione non riuscita",
        "language": "it",
        "_cls_doc": "Gestisce le cose relative a @hikkamods_bot",
        "404": f"{e} <b>Modulo non trovato</b>",
        "not_exact": (
            f"{w} <b>Nessuna corrispondenza esatta trovata, quindi viene visualizzato"
            " il risultato più vicino</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Collegamento</a> per</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>File</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code>"
            " <b>questo messaggio come risposta per installarlo</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>È necessario specificare gli argomenti</b>",
    }

    strings_kk = {
        "no_query": f"{e} <b>Сұранымды көрсетуіңіз керек</b>",
        "no_results": f"{e} <b>Нәтижелер жоқ</b>",
        "api_error": f"{e} <b>API-ға қате кетті</b>",
        "result": (
            "🥰 <b>Сұранымдың нәтижелері</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>төлесін</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Командалар:</b>\n{commands}\n\n🔗 <b>Орнату:</b>"
            " <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Орнату",
        "loaded": "✅ Орнату сәтті аяқталды",
        "not_loaded": "❌ Орнату сәтсіз аяқталды",
        "language": "kk",
        "_cls_doc": "@hikkamods_bot-ға қатысты барлық қызметтерді басқару",
        "404": f"{e} <b>Модуль табылмады</b>",
        "not_exact": (
            f"{w} <b>Толық сәйкес келетін нәтижелер табылмады, сондықтан ең жақын"
            " нәтиже көрсетіледі</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Сілтеме</a> үшін</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Файл</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>осы"
            " хабарламаны жауап болар енгізу үшін</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Аргументтерді көрсетуіңіз керек</b>",
    }

    strings_tt = {
        "no_query": f"{e} <b>Зиндергә мәгълүматләр кертмәгәнсез</b>",
        "no_results": f"{e} <b>Нәтиҗәләр табылмады</b>",
        "api_error": f"{e} <b>API-сәхифәсе белән хата</b>",
        "result": (
            "🥰 <b>Зиндергә нәтиҗәләр</b> <code>{query}</code><b>:</b>\n\n🧳"
            " <code>{name}</code> <b>төзәтелгән</b> <code>{dev}</code>\n👨‍🏫"
            " <i>{cls_doc}</i>\n\n📚 <b>Командалар:</b>\n{commands}\n\n🔗"
            " <b>Установить:</b> <code>{prefix}dlm {link}</code>"
        ),
        "install": "🪄 Установить",
        "loaded": "✅ Установка уңышлы тамамланды",
        "not_loaded": "❌ Установка үтәлмәде",
        "language": "tt",
        "_cls_doc": "@hikkamods_bot-җә белән үзгәртүләрне башкару",
        "404": f"{e} <b>Модуль табылмады</b>",
        "not_exact": (
            f"{w} <b>Тулы тапкыр килгән нәтиҗәләр табылмады, сондыктан ең яңа нәтиҗә"
            " күрсәтелә</b>"
        ),
        "link": (
            f'{link} <b><a href="{{url}}">Сылтама</a> өчен</b>'
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}dlm"
            " {url}</code>\n\n{not_exact}"
        ),
        "file": (
            f"{f} <b>Файл</b>"
            f" <code>{{class_name}}</code>\n\n{moon} <code>{{prefix}}lm</code> <b>осы"
            " хәбәрне кабул килгәндә</b>\n\n{not_exact}"
        ),
        "args": f"{e} <b>Аргументларны күрсәтмәгәнсез</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "autoupdate",
                False,
                (
                    "Do you want to autoupdate modules? (Join @heta_updates in order"
                    " for this option to take effect) ⚠️ Use at your own risk!"
                ),
                validator=loader.validators.Boolean(),
            ),
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
        if self.config["autoupdate"]:
            await self.request_join(
                "@heta_updates",
                "This channel is the source of update notifications",
            )

        if self.get("nomute"):
            return

        await utils.dnd(self._client, "@hikkamods_bot", archive=False)
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

    @loader.command(
        ru_doc="<запрос> - Ищет модули в репозитории Heta",
        de_doc="<Anfrage> - Sucht Module im Heta-Repository",
        uz_doc="<so'rov> - Heta ombori uchun modullarni qidiradi",
        tr_doc="<sorgu> - Heta deposunda modülleri arar",
        it_doc="<richiesta> - Cerca moduli nel repository Heta",
        fr_doc="<requête> - Recherche des modules dans le référentiel Heta",
        kk_doc="<сұраным> - Heta орталығында модульларды іздейді",
        tt_doc="<зиндергә> - Heta депозиториясендә модульләрне таба",
        es_doc="<consulta> - Busca módulos en el repositorio Heta",
    )
    async def heta(self, message: Message):
        """<query> - Searches Heta repository for modules"""
        if not (query := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("no_query"))
            return

        if not (
            response := await utils.run_sync(
                requests.get,
                "https://heta.hikariatama.ru/search",
                params={"q": query, "limit": 1},
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
            "link": result["module"]["link"],
            "query": utils.escape_html(query),
            "prefix": utils.escape_html(self.get_prefix()),
        }

        strings = (
            self.strings._base_strings["result"]
            if self.config["translate"]
            else self.strings("result")
        )

        text = strings.format(**kwargs)

        if len(text) > 2048:
            kwargs["commands"] = "..."
            text = strings.format(**kwargs)

        mark = lambda text: {
            "text": self.strings("install"),
            "callback": self._install,
            "args": (result["module"]["link"], text),
        }

        form = await self.inline.form(
            message=message,
            text=text,
            **(
                {"photo": result["module"]["banner"]}
                if result["module"].get("banner")
                else {}
            ),
            reply_markup=mark(text),
        )

        if not self.config["translate"]:
            return

        message_id, peer, _, _ = resolve_inline_message_id(form.inline_message_id)

        try:
            text = await self._client.translate(
                peer,
                message_id,
                self.strings("language"),
            )
            await form.edit(text=text, reply_markup=mark(text))
        except Exception:
            text = self.strings("result").format(**kwargs)
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

        loaded = any(
            link == url for link in loader_m.get("loaded_modules", {}).values()
        )

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

    @loader.watcher("in", "only_messages", chat_id=1688624566, contains="Heta url: ")
    async def update_watcher(self, message: Message):
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
                    "@hikkamods_bot",
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
                "@hikkamods_bot",
                f"#confirm_update {url.split('hikariatama.ru/')[1]}",
            )
            return

        for module in self.allmodules.modules:
            link = getattr(module, "__origin__", "").lower().strip("/")
            for regex in REGEXES:
                if regex.search(link):
                    dev, repo, mod = regex.search(link).groups()
                    if dev == dev and repo == repo and mod == mod:
                        await self._load_module(link)
                        await asyncio.sleep(random.randint(1, 10))
                        await self._client.inline_query(
                            "@hikkamods_bot",
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
        await message.delete()

        data = re.search(
            r"^#install:(?P<file>.*?\/.*?\/.*?)\n(?P<sig>.*?)\n(?P<dl_id>\d+)\n\n.*$",
            message.raw.text,
        )

        uri = data["file"]
        try:
            rsa.verify(
                rsa.compute_hash(uri.encode(), "SHA-1"),
                base64.b64decode(data["sig"]),
                rsa.PublicKey(
                    7110455561671499155469672749235101198284219627796886527432331759773809536504953770286294224729310191037878347906574131955439231159825047868272932664151403,
                    65537,
                ),
            )
        except rsa.pkcs1.VerificationError:
            logger.error("Got message with non-verified signature %s", uri)
            return

        await self._load_module(
            f"https://heta.hikariatama.ru/{uri}",
            int(data["dl_id"]),
        )

    @loader.command(
        ru_doc="<имя модуля> - Отправить ссылку на модуль",
        de_doc="<Modulname> - Send link to module",
        es_doc="<nombre del módulo> - Enviar enlace al módulo",
        uz_doc="<modul nomi> - Modulga havola yuborish",
        tr_doc="<modül adı> - Modül bağlantısını gönder",
        fr_doc="<nom du module> - Envoyer le lien vers le module",
        it_doc="<nome del modulo> - Invia il link al modulo",
        tt_doc="<модуль исеме> - Модульга сылтама җибәрү",
        kk_doc="<модуль атауы> - Модульге сілтеме жіберу",
    )
    async def mlcmd(self, message: Message):
        """<module name> - Send link to module"""
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
