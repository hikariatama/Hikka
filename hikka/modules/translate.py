# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from hikkatl.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class Translator(loader.Module):
    """Translates text (obviously)"""

    e = "<emoji document_id=5210952531676504517>❌</emoji>"

    strings = {
        "name": "Translator",
        "no_args": f"{e} <b>No arguments provided</b>",
        "error": f"{e} <b>Unable to translate text</b>",
        "language": "en",
    }

    strings_ru = {
        "no_args": f"{e} <b>Не указаны аргументы</b>",
        "error": f"{e} <b>Не удалось перевести текст</b>",
        "language": "ru",
        "_cls_doc": "Переводит текст (очевидно)",
    }

    strings_de = {
        "no_args": f"{e} <b>Keine Argumente angegeben</b>",
        "error": f"{e} <b>Konnte Text nicht übersetzen</b>",
        "language": "de",
        "_cls_doc": "Übersetzt den Text (offensichtlich)",
    }

    strings_es = {
        "no_args": f"{e} <b>No se han proporcionado argumentos</b>",
        "error": f"{e} <b>No se pudo traducir el texto</b>",
        "language": "es",
        "_cls_doc": "Traduce el texto (obviamente)",
    }

    strings_uz = {
        "no_args": f"{e} <b>Argumentlar berilmadi</b>",
        "error": f"{e} <b>Matnni tarjima qilishda xatolik yuz berdi</b>",
        "language": "uz",
        "_cls_doc": "Matnni tarjima qilish (a'lohida)",
    }

    strings_tr = {
        "no_args": f"{e} <b>Argümanlar verilmedi</b>",
        "error": f"{e} <b>Metin çevirilemedi</b>",
        "language": "tr",
        "_cls_doc": "Metni çevir (açıkçası)",
    }

    strings_kk = {
        "no_args": f"{e} <b>Аргументтер көрсетілмеген</b>",
        "error": f"{e} <b>Мәтінді тілден түсірмеді</b>",
        "language": "kk",
        "_cls_doc": "Мәтінді тілден түсір (ағылшындай)",
    }

    strings_it = {
        "no_args": f"{e} <b>Nessun argomento fornito</b>",
        "error": f"{e} <b>Impossibile tradurre il testo</b>",
        "language": "it",
        "_cls_doc": "Traduci il testo (ovviamente)",
    }

    strings_fr = {
        "no_args": f"{e} <b>Aucun argument fourni</b>",
        "error": f"{e} <b>Impossible de traduire le texte</b>",
        "language": "fr",
        "_cls_doc": "Traduit le texte (évidemment)",
    }

    strings_tt = {
        "no_args": f"{e} <b>Аргументлар күрсәтелмәгән</b>",
        "error": f"{e} <b>Мәтинне тәрҗемә итү мөмкин түгел</b>",
        "language": "tt",
        "_cls_doc": "Мәтинне тәрҗемә итү (ағылшындай)",
    }

    @loader.command(
        ru_doc="[язык] [текст] - Перевести текст",
        de_doc="[Sprache] [Text] - Übersetze Text",
        es_doc="[idioma] [texto] - Traducir texto",
        uz_doc="[til] [matn] - Matnni tarjima qilish",
        tr_doc="[dil] [metin] - Metni çevir",
        kk_doc="[тіл] [мәтін] - Мәтінді тілден түсір",
        it_doc="[lingua] [testo] - Traduci testo",
        fr_doc="[langue] [texte] - Traduire le texte",
        tt_doc="[тил] [мәтин] - Мәтинне тәрҗемә итү",
    )
    async def tr(self, message: Message):
        """[language] [text] - Translate text"""
        if not (args := utils.get_args_raw(message)):
            text = None
            lang = self.strings("language")
        else:
            lang = args.split(maxsplit=1)[0]
            if len(lang) != 2:
                text = args
                lang = self.strings("language")
            else:
                try:
                    text = args.split(maxsplit=1)[1]
                except IndexError:
                    text = None

        if not text:
            if not (reply := await message.get_reply_message()):
                await utils.answer(message, self.strings("no_args"))
                return

            text = reply.raw_text
            entities = reply.entities
        else:
            entities = []

        message.raw_text = text
        message.entities = entities

        try:
            await utils.answer(
                message,
                await self._client.translate(message.peer_id, message, lang),
            )
        except Exception:
            logger.exception("Unable to translate text")
            await utils.answer(message, self.strings("error"))
