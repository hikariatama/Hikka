"""Loads and registers modules"""

# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import ast
import asyncio
import contextlib
import copy
import functools
import importlib
import inspect
import logging
import os
import re
import shutil
import sys
import time
import typing
import uuid
from collections import ChainMap
from importlib.machinery import ModuleSpec
from urllib.parse import urlparse

import requests
import telethon
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Message

from .. import loader, main, utils
from .._local_storage import RemoteStorage
from ..compat import dragon, geek
from ..compat.pyroproxy import PyroProxyClient
from ..inline.types import InlineCall
from ..types import CoreOverwriteError, CoreUnloadError, DragonModule

logger = logging.getLogger(__name__)


class FakeLock:
    async def __aenter__(self, *args):
        pass

    async def __aexit__(self, *args):
        pass


class FakeNotifier:
    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass


@loader.tds
class LoaderMod(loader.Module):
    """Loads modules"""

    strings = {
        "name": "Loader",
        "repo_config_doc": "URL to a module repo",
        "avail_header": "🎢 <b>Modules from repo</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Please select a"
            " preset</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Preset not found</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Preset loaded</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Module not available"
            " in repo.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>File not found</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Provide a module to"
            " load</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Invalid Unicode"
            " formatting in module</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Loading failed. See"
            " logs for details</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Module"
            "</b> <code>{}</code>{} <b>loaded {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>What class needs to be unloaded?</b>",
        "unloaded": "{} <b>Module {} unloaded.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Module not"
            " unloaded.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Requirements"
            " installation failed</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>Requirements"
            " installation failed</b>\n<b>The most common reason is that Termux doesn't"
            " support many libraries. Don't report it as bug, this can't be solved.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Installing"
            " requirements:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Requirements"
            " installed, but a restart is required for</b> <code>{}</code> <b>to"
            " apply</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>All modules"
            " deleted</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> No docs",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module requires"
            " Hikka inline feature and initialization of InlineManager"
            " failed</b>\n<i>Please, remove one of your old bots from @BotFather and"
            " restart userbot to load this module</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module requires"
            " Hikka {}+\nPlease, update with</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module requires"
            " FFMPEG, which is not installed</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Developer:</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Dependencies:"
            "</b> \n{}"
        ),
        "by": "by",
        "module_fs": (
            "💿 <b>Would you like to save this module to filesystem, so it won't get"
            " unloaded after restart?</b>"
        ),
        "save": "💿 Save",
        "no_save": "🚫 Don't save",
        "save_for_all": "💽 Always save to fs",
        "never_save": "🚫 Never save to fs",
        "will_save_fs": (
            "💽 Now all modules, loaded with .loadmod will be saved to filesystem"
        ),
        "add_repo_config_doc": "Additional repos to load from",
        "share_link_doc": "Share module link in result message of .dlmod",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Link:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>Do not use `blob`"
            " links to download modules. Consider switching to `raw` instead</b>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>This module is"
            " made by {}. Do you want to join this channel to support developer?</b>"
        ),
        "subscribe": "💬 Subscribe",
        "no_subscribe": "🚫 Don't subscribe",
        "subscribed": "💬 Subscribed",
        "not_subscribed": "🚫 I will no longer suggest subscribing to this channel",
        "confirm_clearmodules": "⚠️ <b>Are you sure you want to clear all modules?</b>",
        "clearmodules": "🗑 Clear modules",
        "cancel": "🚫 Cancel",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module"
            " attempted to override the core one (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Don't report it as bug."
            " It's a security measure to prevent replacing core modules with some"
            " junk</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module"
            " attempted to override the core command"
            " (</b><code>{}{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Don't report it as bug."
            " It's a security measure to prevent replacing core modules' commands with"
            " some junk</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>You can't unload"
            " core module</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Don't report it as bug."
            " It's a security measure to prevent replacing core modules with some"
            " junk</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>You can't unload"
            " library</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Module"
            "</b> <code>{}</code> <b>requests permission to join channel <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Reason: {}</b>\n\n<i>Waiting'
            ' for <a href="https://t.me/{}">approval</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Installing module"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>is already added</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>added</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You need to specify"
            " repo to add</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>is not added</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>deleted</b>"
        ),
    }

    strings_ru = {
        "repo_config_doc": "Ссылка для загрузки модулей",
        "add_repo_config_doc": "Дополнительные репозитории",
        "avail_header": "🎢 <b>Официальные модули из репозитория</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Выбери пресет</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Пресет не найден</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Пресет загружен</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Модуль недоступен в"
            " репозитории.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Файл не найден</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Укажи модуль для"
            " загрузки</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Неверная кодировка"
            " модуля</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Загрузка не"
            " увенчалась успехом. Смотри логи.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Модуль"
            "</b> <code>{}</code>{} <b>загружен {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>А что выгружать то?</b>",
        "unloaded": "{} <b>Модуль {} выгружен.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Модуль не"
            " выгружен.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ошибка установки"
            " зависимостей</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>Ошибка установки"
            " зависимостей</b>\n<b>Наиболее часто возникает из-за того, что Termux не"
            " поддерживает многие библиотеки. Не сообщайте об этом как об ошибке, это"
            " не может быть исправлено.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Устанавливаю"
            " зависимости:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Зависимости"
            " установлены, но нужна перезагрузка для применения</b> <code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Модули удалены</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Нет описания",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этому модулю"
            " требуется Hikka версии {}+\nОбновись с помощью</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этому модулю"
            " требуется FFMPEG, который не установлен</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Разработчик:"
            "</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Зависимости:"
            "</b> \n{}"
        ),
        "by": "от",
        "module_fs": (
            "💿 <b>Ты хочешь сохранить модуль на жесткий диск, чтобы он не выгружался"
            " при перезагрузке?</b>"
        ),
        "save": "💿 Сохранить",
        "no_save": "🚫 Не сохранять",
        "save_for_all": "💽 Всегда сохранять",
        "never_save": "🚫 Никогда не сохранять",
        "will_save_fs": (
            "💽 Теперь все модули, загруженные из файла, будут сохраняться на жесткий"
            " диск"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этому модулю нужен"
            " HikkaInline, а инициализация менеджера инлайна неудачна</b>\n<i>Попробуй"
            " удалить одного из старых ботов в @BotFather и перезагрузить юзербота</i>"
        ),
        "_cmd_doc_dlmod": "Скачивает и устаналвивает модуль из репозитория",
        "_cmd_doc_dlpreset": "Скачивает и устанавливает определенный набор модулей",
        "_cmd_doc_loadmod": "Скачивает и устанавливает модуль из файла",
        "_cmd_doc_unloadmod": "Выгружает (удаляет) модуль",
        "_cmd_doc_clearmodules": "Выгружает все установленные модули",
        "_cls_doc": "Загружает модули",
        "share_link_doc": "Указывать ссылку на модуль после загрузки через .dlmod",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Ссылка:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>Не используй"
            " `blob` ссылки для загрузки модулей. Лучше загружать из `raw`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Ссылка:"
            "</b> <code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Этот модуль"
            " сделан {}. Подписаться на него, чтобы поддержать разработчика?</b>"
        ),
        "subscribe": "💬 Подписаться",
        "no_subscribe": "🚫 Не подписываться",
        "subscribed": "💬 Подписался!",
        "unsubscribed": "🚫 Я больше не буду предлагать подписаться на этот канал",
        "confirm_clearmodules": (
            "⚠️ <b>Вы уверены, что хотите выгрузить все модули?</b>"
        ),
        "clearmodules": "🗑 Выгрузить модули",
        "cancel": "🚫 Отмена",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этот модуль"
            " попытался перезаписать встроенный (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Это не ошибка, а мера"
            " безопасности, требуемая для предотвращения замены встроенных модулей"
            " всяким хламом. Не сообщайте о ней в support чате</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этот модуль"
            " попытался перезаписать встроенную команду"
            " (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Это не ошибка, а мера"
            " безопасности, требуемая для предотвращения замены команд встроенных"
            " модулей всяким хламом. Не сообщайте о ней в support чате</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ты не можешь"
            " выгрузить встроенный модуль</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Это не ошибка, а мера"
            " безопасности, требуемая для предотвращения замены встроенных модулей"
            " всяким хламом. Не сообщайте о ней в support чате</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ты не можешь"
            " выгрузить библиотеку</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Модуль"
            "</b> <code>{}</code> <b>запрашивает разрешение на вступление в канал <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Причина:'
            ' {}</b>\n\n<i>Ожидание <a href="https://t.me/{}">подтверждения</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Устанавливаю модуль"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>уже добавлен</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>добавлен</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Вы должны указать"
            " репозиторий для добавления</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>не добавлен</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>удален</b>"
        ),
    }

    strings_it = {
        "repo_config_doc": "Link per il download dei moduli",
        "add_repo_config_doc": "Repository aggiuntivi",
        "avail_header": "🎢 <b>Moduli ufficiali dal repository</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Seleziona un"
            " preset</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Preset non trovato</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Preset caricato</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Il modulo non è"
            " disponibile nel repository.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>File non trovato</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Specifica il modulo"
            " da caricare</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Codifica modulo"
            " errata</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Caricamento non"
            " riuscito. Vedi i log.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Modulo"
            "</b> <code>{}</code>{} <b>caricato {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Cosa devo scaricare?</b>",
        "unloaded": "{} <b>Modulo {} scaricato.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modulo non"
            " scaricato.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Errore di"
            " installazione dei requisiti</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>Errore"
            " nell'installazione dei requisiti</b>\n<b>Si verifica più frequentemente"
            " perché Termux non supporta molte librerie. Non segnalare questo come"
            " errore, non può essere corretto.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Installazione"
            " dei requisiti:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>I requisiti sono"
            " installati, ma è necessario riavviare per applicare</b> <code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>I moduli sono stati"
            " eliminati</b>"
        ),
        "undoc": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Nessuna descrizione"
        ),
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Questo modulo"
            " richiede Hikka versione {}+\nAggiornati con</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Questo modulo"
            " richiede FFMPEG, che non è installato</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Sviluppatore:"
            "</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Dependenze:"
            "</b> \n{}"
        ),
        "by": "di",
        "module_fs": (
            "💿 <b>Vuoi salvare il modulo sul disco fisso per non scaricarlo"
            " al riavvio?</b>"
        ),
        "save": "💿 Salva",
        "no_save": "🚫 Non salvare",
        "save_for_all": "💽 Salva sempre",
        "never_save": "🚫 Non salvare mai",
        "will_save_fs": (
            "💽 Ora tutti i moduli caricati da file verranno salvati sul disco fisso"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Questo modulo ha"
            " bisogno di HikkaInline, ma l'inizializzazione del gestore inline è"
            " fallita</b>\n<i>Prova a rimuovere uno dei vecchi bot in @BotFather e"
            " riavviare l'utente</i>"
        ),
        "_cmd_doc_dlmod": "Scarica e installa il modulo dal repository",
        "_cmd_doc_dlpreset": "Scarica e installa un insieme specifico di moduli",
        "_cmd_doc_loadmod": "Scarica e installa il modulo dal file",
        "_cmd_doc_unloadmod": "Scarica (rimuovi) il modulo",
        "_cmd_doc_clearmodules": "Scarica tutti i moduli installati",
        "_cls_doc": "Carica moduli",
        "share_link_doc": (
            "Specifica il link del modulo dopo aver caricato tramite .dlmod"
        ),
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Link:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>Non usare"
            " `blob` link per caricare i moduli. È meglio caricare da `raw`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Link:"
            "</b> <code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Questo modulo"
            " è stato fatto da {}. Sottoscrivere per sostenere il sviluppatore?</b>"
        ),
        "subscribe": "💬 Sottoscrivi",
        "no_subscribe": "🚫 Non sottoscrivere",
        "subscribed": "💬 Sottoscritto!",
        "unsubscribed": "🚫 Non ti chiederò più di sottoscrivere questo canale",
        "confirm_clearmodules": (
            "⚠️ <b>Sei sicuro di voler scaricare tutti i moduli?</b>"
        ),
        "clearmodules": "🗑 Scaricare i moduli",
        "cancel": "🚫 Annulla",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Questo modulo ha"
            " tentato di sovrascrivere un modulo integrato"
            " (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Non è un errore, ma un"
            " misura di sicurezza richiesta per impedire di sovrascrivere i moduli"
            " integrati con qualsiasi schifo. Non segnalare questo errore nel supporto"
            " chat</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Questo modulo ha"
            " tentato di sovrascrivere un comando integrato"
            " (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Non è un errore, ma un"
            " misura di sicurezza richiesta per impedire di sovrascrivere i comandi"
            " integrati con qualsiasi schifo. Non segnalare questo errore nel supporto"
            " chat</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Non puoi scaricare un"
            " modulo integrato</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Non è un errore, ma un"
            " misura di sicurezza richiesta per impedire di sovrascrivere i moduli"
            " integrati con qualsiasi schifo. Non segnalare questo errore nel supporto"
            " chat</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Non puoi"
            " scaricare una libreria</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Il modulo</b>"
            " <code>{}</code> <b>sta richiedendo l'approvazione per entrare nel canale"
            ' <a href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Motivo: {}</b>\n\n<i>In'
            ' attesa di <a href="https://t.me/{}">conferma</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Sto installando il"
            " modulo</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Il repo</b>"
            " <code>{}</code> <b>è già stato aggiunto</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Il repo</b>"
            " <code>{}</code> <b>è stato aggiunto</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Devi specificare il"
            " repo da aggiungere</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Il repo</b>"
            " <code>{}</code> <b>non è stato aggiunto</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Il repo</b>"
            " <code>{}</code> <b>è stato rimosso</b>"
        ),
    }

    strings_de = {
        "repo_config_doc": "Modul-Download-Link",
        "add_repo_config_doc": "Zusätzliche Repositorys",
        "avail_header": "🎢 <b>Offizielle Moduleaus Repository</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Voreinstellung"
            " auswählen</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Voreinstellung nicht"
            " gefunden</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Voreinstellung"
            " geladen</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modul nicht verfügbar"
            " in Repositorys.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji><b>Datei nicht"
            " gefunden</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Geben Sie ein zu"
            " ladendes Modul an</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ungültige Codierung"
            "Modul</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Lädt nicht"
            " war erfolgreich. Sehen Sie sich die Protokolle an.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Modul"
            "</b> <code>{}</code>{} <b>geladen {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Was soll dann hochgeladen werden?</b>",
        "unloaded": "{} <b>{} Modul entladen.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modul nicht"
            " entladen.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Installation"
            " fehlgeschlagen Abhängigkeiten</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>Installation"
            " fehlgeschlagenAbhängigkeiten</b>\n<b>Tritt am häufigsten auf, weil Termux"
            " dies nicht tutunterstützt viele Bibliotheken. Melden Sie dies nicht als"
            " Fehler, es ist kann nicht behoben werden.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Wird installiert"
            " Abhängigkeiten:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Abhängigkeiten"
            " installiert, muss aber neu gestartet werden, um</b> <code>{}</code>"
            " anzuwenden"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji><b>Module entfernt</b>"
        ),
        "undoc": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Keine Beschreibung"
        ),
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Zu diesem Modul"
            "erfordert Hikka-Version {}+\nUpdate mit</b> <code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Zu diesem Modul"
            "benötigt FFMPEG, das nicht installiert ist</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Entwickler:</b>{}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Abhängigkeiten:"
            "</b>\n{}"
        ),
        "by": "von",
        "module_fs": (
            "💿 <b>Sie möchten das Modul auf Ihrer Festplatte speichern, damit es nicht"
            " entladen wird.beim Neustart?</b>"
        ),
        "save": "💿 Speichern",
        "no_save": "🚫 Nicht speichern",
        "save_for_all": "💽 Immer speichern",
        "never_save": "🚫 Nie speichern",
        "will_save_fs": (
            "💽 Jetzt werden alle aus der Datei geladenen Module auf der Festplatte"
            " gespeichertScheibe"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Dieses Modul benötigt"
            " Initialisierung von HikkaInline und Inline-Manager"
            " fehlgeschlagen</b>\n<i>Versuchen Sie esLösche einen der alten Bots in"
            " @BotFather und lade den Userbot neu</i>"
        ),
        "_cmd_doc_dlmod": "Modul aus dem Repository herunterladen und installieren",
        "_cmd_doc_dlpreset": (
            "Lädt einen bestimmten Satz von Modulen herunter und installiert ihn"
        ),
        "_cmd_doc_loadmod": (
            "Lädt ein Modul aus einer Datei herunter und installiert es"
        ),
        "_cmd_doc_unloadmod": "Entlädt (löscht) ein Modul",
        "_cmd_doc_clearmodules": "Entlädt alle installierten Module",
        "_cls_doc": "Module laden",
        "share_link_doc": (
            "Stellen Sie nach dem Laden über .dlmod einen Link zum Modul bereit"
        ),
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Link:"
            "</b><code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>Verwenden Sie"
            " keine `Blob`-Links, um Module zu laden. Laden Sie besser von`roh`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Link:"
            "</b><code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Dieses Modul"
            " Erledigt von {}. Abonnieren, um den Entwickler zu unterstützen?</b>"
        ),
        "subscribe": "💬 Abonnieren",
        "no_subscribe": "🚫 Nicht abonnieren",
        "subscribed": "💬 Abonniert!",
        "unsubscribed": "🚫 Ich werde nicht wieder anbieten, diesen Kanal zu abonnieren",
        "confirm_clearmodules": (
            "⚠️ <b>Sind Sie sicher, dass Sie alle Module entladen möchten?</b>"
        ),
        "clearmodules": "🗑 Module entladen",
        "cancel": "🚫 Stornieren",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Dieses Modulversucht,"
            " eingebautes (</b><code>{}</code><b>) zu"
            " überschreiben</b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
            " Dies ist kein Fehler, sondern eine MaßnahmeSicherheit erforderlich, um"
            " den Austausch von eingebauten Modulen zu verhindern mit allerlei Müll."
            " Melde es nicht im Support-Chat</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Dieses Modulversucht"
            " eingebauten Befehl zu überschreiben"
            " (</b><code>{}</code><b>)</b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
            " Dies ist kein Fehler, sondern eine MaßnahmeSicherheit erforderlich, um"
            " die Ersetzung eingebauter Befehle zu verhindernModule mit allerlei Müll."
            " Melde es nicht im Support-Chat</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Das kannst du nicht"
            " integriertes Modul entladen</b>"
            " <code>{}</code><b></b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
            " Dies ist kein Fehler, sondern eine MaßnahmeSicherheit erforderlich, um"
            " den Austausch von eingebauten Modulen zu verhindern mit allerlei Müll."
            " Melde es nicht im Support-Chat</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Das kannst du nicht"
            "Bibliothek entladen</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Modul"
            "</b> <code>{}</code> <b>bittet um Erlaubnis, Kanal <a beizutreten"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Grund:'
            ' {}</b>\n\n<i>Warten auf <a href="https://t.me/{}">Bestätigung</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Modul installieren"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>wurde bereits hinzugefügt</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>wurde hinzugefügt</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Du musst ein Repo"
            " angeben um es hinzuzufügen</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>wurde nicht hinzugefügt</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>wurde gelöscht</b>"
        ),
    }

    strings_tr = {
        "repo_config_doc": "Bir modül deposunun URL'si",
        "avail_header": "🎢 <b>Depodan modüller</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Lütfen bir ön ayar"
            " seçin</b>"
        ),
        "no_preset": (
            "<emoji document_id=53752013968596607943>🚫</emoji> <b>Ön ayar"
            " bulunamadı</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Ön ayar yüklendi</b>"
        ),
        "no_module": (
            "<emoji document_id=53752013968596607943>🚫</emoji> <b>Modül depoda mevcut"
            " değil.</b>"
        ),
        "no_file": (
            "<emoji document_id=53752013968596607943>🚫</emoji> <b>Dosya bulunamadı</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Yüklenecek bir modül"
            " sağlayın</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modülde geçersiz"
            " Unicode biçimlendirmesi</b>"
        ),
        "load_failed": (
            "<emoji document_id=53752013968596607943>🚫</emoji> <b>Yükleme başarısız"
            " oldu. Ayrıntılar için kayıtlara bakınız</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b>"
            "</b>  <code>{}</code>{} <b>isimli modül yüklendi {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Hangi modülün kaldırılması gerekiyor?</b>",
        "unloaded": "{} <b>{} isimli modül kaldırıldı.</b>",
        "not_unloaded": (
            "<emoji document_id=53752013968596607943>🚫</emoji> <b>Modül "
            " kaldırılamadı.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Gereksinimlerin"
            " yüklemesi başarısız oldu</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>Gereksinimlerin"
            " kurulumu başarısız oldu</b>\n<b>Bu hatanın en yaygın nedeni Termux'un"
            " birçok kütüphaneyi desteklememesidir. Lütfen bu hatayı bildirme,"
            " çözülmesi imkansız.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Gereksinimler"
            " yükleniyor:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Gereksinimler"
            " yüklendi, ancak</b> <code>{}</code> <b>uygulanabilmesi için yeniden"
            " başlatma gerekiyor</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Tüm modüller"
            " silindi</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Doküman yok",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül Hikka satır"
            " içi özelliği gerektiriyor fakat InlineManager'ın yüklenirken hata"
            " verdi</b>\n<i>Lütfen eski botlarınızdan birini @BotFather'dan kaldırın ve"
            " bu modülü yüklemek için kullanıcı botunu yeniden başlatın</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül Hikka {}"
            " sürümünü gerektirmektedir.+\nLütfen,</b> <code>.update</code> kodu ile"
            " Hikka'yı güncelleyin"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül yüklü"
            " olmayan.FFMPEG kütüphanesini gerektirmektedir</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Geliştirici:"
            "</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Bağımlılıklar:"
            "</b> \n{}"
        ),
        "module_fs": (
            "💿 <b>Bu modülü dosya sistemine kaydetmek (FS) ister misiniz?"
            " kaydederseniz yeniden başlattığınızda kaldırılmayacaktır.</b>"
        ),
        "save": "💿 Kaydet",
        "no_save": "🚫 Kaydetme",
        "save_for_all": "💽 Her zaman FS'ye kaydet",
        "never_save": "🚫 Asla FS'ye kaydetme",
        "will_save_fs": (
            "💽 Artık .loadmod ile yüklenen tüm modüller dosya sistemine kaydedilecek"
        ),
        "add_repo_config_doc": "Yüklenecek ek depolar",
        "share_link_doc": ".dlmod'un sonuç mesajında ​​modül bağlantısını paylaşın",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Bağlantı:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>Modülleri"
            " indirmek için `blob` bağlantılarını kullanmayın. Onun yerine 'raw'"
            " kullanabilirsiniz</b>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Bu modül {}"
            " tarafından yapılmıştır. Geliştiriciyi desteklemek için bu kanala katılmak"
            " ister misiniz?</b>"
        ),
        "subscribe": "💬 Abone ol",
        "no_subscribe": "🚫 Abone olma",
        "subscribed": "💬 Abone olundu",
        "not_subscribed": "🚫 Artık bu kanala abone olmayı önermeyeceğim",
        "confirm_clearmodules": (
            "⚠️ <b>Tüm modülleri silmek istediğinizden emin misiniz?</b>"
        ),
        "clearmodules": "🗑 Modülleri temizle",
        "cancel": "🚫 İptal",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül, çekirdeği"
            " geçersiz kılmaya çalıştı (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Lütfen bunu hata olarak"
            " bildirmeyin. Bu, çekirdek modüllerin değiştirilmesini önlemek için"
            " bir güvenlik önlemidir</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül, çekirdek"
            " komutu geçersiz kılmaya çalıştı (</b><code>{}{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Lütfen bunu hata olarak"
            " bildirmeyin. Bu, Çekirdek modüllerin komutlarının değiştirilmesini"
            " önlemek için bir güvenlik önlemidir.</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Çekirdek modülleri"
            " kaldıramazsınız</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> lütfen bunu hata olarak"
            " bildirmeyin. Bu, Çekirdek modüllerin  değiştirilmesini önlemek için"
            " bir güvenlik önlemidir.</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Kütüphaneyi"
            " kaldıramazsınız</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Modül"
            "</b> <code>{}</code> <b>kanalına katılmak için izin istiyor <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Sebep: {}</b>\n\n<i>Onay'
            ' <a href="https://t.me/{}">bekliyor</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Modül yükleme"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>zaten eklenmiş</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>eklendi</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Eklemek için repo"
            " belirtmeniz gerekli</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>eklenmemiş</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>silindi</b>"
        ),
    }

    strings_uz = {
        "repo_config_doc": "Modulni yuklab olish havolasi",
        "add_repo_config_doc": "Qo'shimcha omborlar",
        "avail_header": "🎢 <b>Rasmiy modullarombordan</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Oldindan sozlashni"
            " tanlang</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Oldindan sozlash"
            " topilmadi</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Oldindan"
            " o'rnatilgan</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>modul mavjud emas"
            " omborlar</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Fayl topilmadi</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Yuklanadigan modulni"
            " belgilang</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>yaroqsiz kodlash"
            "modul</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Yuklanmayapti"
            " Muvaffaqiyatli. Jurnallarga qarang.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>moduli"
            "</b> <code>{}</code>{} <b>yuklangan {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Unda nima yuklash kerak?</b>",
        "unloaded": "{} <b>{} moduli tushirildi.</b>",
        "not_loaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modul emas"
            " tushirildi.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>O'rnatish amalga"
            " oshmadi bog'liqliklar</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>O'rnatish amalga"
            " oshmadi bog'liqliklar</b>\n<b>Ko'pincha Termux bo'lmagani uchun paydo"
            " bo'ladiko'p kutubxonalarni qo'llab-quvvatlaydi. Buni xato deb xabar"
            " qilmang, bu tuzatib bo'lmaydi.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>O'rnatilmoqda"
            " bog'liqliklar:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Bog'liqlar o'rnatildi,"
            " lekin qo'llash uchun qayta ishga tushirish kerak</b> <code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Modullar olib"
            " tashlandi</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Tavsif yo'q",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulgaHikka"
            " versiyasini {}+\n</b><code>.update</code> bilan yangilashni talab qiladi"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulga"
            "o'rnatilmagan FFMPEG talab qiladi</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Ishlab"
            " chiquvchi:</b>{}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Bog'liqlar:"
            "</b>\n{}"
        ),
        "by": "dan",
        "module_fs": (
            "💿 <b>Siz modulni yuklamasligi uchun qattiq diskingizga saqlamoqchisiz"
            " qayta ishga tushirishdami</b>"
        ),
        "save": "💿 Saqlash",
        "no_save": "🚫 Kerakmas",
        "save_for_all": "💽 Har vaqt saqlash",
        "never_save": "🚫 Hechqachon saqlamaslik",
        "will_save_fs": (
            "💽 Endi fayldan yuklangan barcha modullar qattiq diskda saqlanadidisk"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulga kerak"
            " HikkaInline va inline menejeri ishga tushirilmadi</b>\n<i>Sinab"
            " ko'ring @BotFather'dagi eski botlardan birini o'chirib tashlang va"
            " userbotni qayta yuklang</i>"
        ),
        "_cmd_doc_dlmod": "Modulni ombordan yuklab oling va o'rnating",
        "_cmd_doc_dlpreset": "Muayyan modullar to'plamini yuklab oladi va o'rnatadi",
        "_cmd_doc_loadmod": "Fayldan modulni yuklab oladi va o'rnatadi",
        "_cmd_doc_unloadmod": "Modulni yuklaydi (o'chiradi)",
        "_cmd_doc_clearmodules": "Barcha o'rnatilgan modullarni yuklaydi",
        "_cls_doc": "Modullarni yuklaydi",
        "share_link_doc": (
            ".dlmod orqali yuklangandan so'ng modulga havolani taqdim eting"
        ),
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Havola:"
            "</b><code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>Modullarni"
            " yuklash uchun `blob` havolalaridan foydalanmang. Bu yerdan yuklagan"
            " ma`qul.`xom`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Havola:"
            "</b><code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Ushbu modul {}"
            " tomonidan amalga oshirildi. Ishlab chiquvchini qo'llab-quvvatlash uchun"
            " unga obuna bo'lasizmi?</b>"
        ),
        "subscribe": "💬 Obuna bo'lish",
        "no_subscribe": "🚫 Shart emas",
        "subscribed": "💬 Obuna bo'ldingiz",
        "unsubscribed": "🚫 Men bu kanalga boshqa obuna bo'lishni taklif qilmayman",
        "confirm_clearmodules": (
            "⚠️ <b>Haqiqatan ham barcha modullarni olib tashlamoqchimisiz?</b>"
        ),
        "clearmodules": "🗑 modullarni tushirish",
        "cancel": "🚫 Bekor qilish",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulo'rnatilgan"
            " (</b><code>{}</code><b>)</b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
            " Bu xato emas, balki o'lchovO'rnatilgan modullarni almashtirishni oldini"
            " olish uchun zarur bo'lgan xavfsizlik Har xil keraksiz narsalar bilan. Bu"
            " haqda qo'llab-quvvatlash chatida xabar bermang</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulo'rnatilgan"
            " buyruqni qayta yozishga harakat qildim"
            " (</b><code>{}</code><b>)</b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
            " Bu xato emas, balki o'lchovO'rnatilgan buyruqlarni almashtirishni oldini"
            " olish uchun zarur bo'lgan xavfsizlik har xil keraksiz narsalarga ega"
            " modullar. Bu haqda qo'llab-quvvatlash chatida xabar bermang</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Siz qila olmaysiz"
            " o'rnatilgan modulni yuklash</b>"
            " <code>{}</code><b></b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
            " Bu xato emas, balki o'lchovO'rnatilgan modullarni almashtirishni oldini"
            " olish uchun zarur bo'lgan xavfsizlik Har xil keraksiz narsalar bilan. Bu"
            " haqda qo'llab-quvvatlash chatida xabar bermang</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Siz qila olmaysiz"
            " kutubxonani olib tashlash</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Modul"
            "</b> <code>{}</code> <b>kanaliga qo'shilish uchun ruxsat so'ramoqda <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Sabab:'
            ' {}</b>\n\n<i><a href="https://t.me/{}">tasdiqlash</a> kutilmoqda...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Modulni o'rnatish"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>aldaqqa qo'shilgan</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>qo'shildi</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo qo'shish uchun"
            " sizga kerak</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Repo</b>"
            " <code>{}</code> <b>qo'shilmagan</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Repo</b>"
            " <code>{}</code> <b>o'chirildi</b>"
        ),
    }

    strings_es = {
        "repo_config_doc": "Enlace al repositorio de módulos",
        "avail_header": "🎢 <b>Módulos del repositorio</b>",
        "select_preset": (
            "<b>⚠️ Por favor, selecciona una configuración preestablecida</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No se encontraron"
            " configuraciones preestablecidas</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Configuración"
            " preestablecida cargada</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No se encontró el"
            " módulo en el repositorio.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No se encontró el"
            " archivo</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Proporcione el módulo"
            " para cargarlo</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Formato de módulo"
            " unicode inválido</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Falló la carga. Revise"
            " el registro para obtener más detalles.</b>"
        ),
        "loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>El módulo"
            "</b> <code>{}</code>{} <b>cargado en {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>¿Qué clase desea deshabilitar?</b>",
        "unloaded": "{} <b>Módulo {} descargado.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>El módulo no se"
            " descargó.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Falló la instalación"
            " de requisitos</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Falló la instalación"
            " de requisitos</b>\n<b>El motivo más común es que Termux no esté"
            " instalado, que es el que soporta la mayoría de las bibliotecas. No lo"
            " informe como un error, no se puede resolver.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Instalando"
            " requerimientos:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Requerimientos"
            " instalados, pero es necesario reiniciar</b> <code>{}</code> <b>para"
            " completar la operación.</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Todos los"
            " módulos eliminados</b>"
        ),
        "undoc": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Sin documentación"
        ),
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Este módulo"
            " requiere la existencia de Hikka inline y falló"
            " inicializar InlineManager</b>\n<i>Elimina uno de los bots anteriores de"
            " @BotFather y reinicia el bot para cargar este módulo.</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Este módulo"
            " requiere Hikka {}+\nPor favor,</b> <code>.update</code> para actualizar."
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Este módulo"
            " requiere FFMPEG, no está instalado</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Desarrollador:"
            "</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Depende de:"
            "</b> \n{}"
        ),
        "by": "por",
        "module_fs": (
            "💿 <b>¿Quieres guardar este módulo en el sistema de archivos? Será"
            " eliminado al reiniciar y desinstalarlo.</b>"
        ),
        "save": "💿 Guardar",
        "no_save": "🚫 No guardar",
        "save_for_all": "💽 Guardar todos los módulos en el sistema de archivos",
        "never_save": "🚫 No guardar todos los módulos en el sistema de archivos",
        "will_save_fs": (
            "💽 Ahora se guardarán todos los módulos cargados por .loadmod en el"
            " sistema de archivos."
        ),
        "add_repo_config_doc": "Repositorio adicional para descargar desde él",
        "share_link_doc": "Compartir enlace de descarga de .dlmod",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Enlace:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>No uses enlaces"
            " `blob` para descargar módulos. Usa `raw` en cambio</b>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Este módulo"
            " fue creado por: {}. ¿Quieres suscribirte a este canal para apoyar al"
            " desarrollador?</b>"
        ),
        "subscribe": "💬 Suscribirse",
        "no_subscribe": "🚫 No quiero suscribirme",
        "subscribed": "💬 Suscribirse",
        "not_subscribed": (
            "🚫 No se han enviado sugerencias de suscripción a este canal todavía."
        ),
        "confirm_clearmodules": (
            "⚠️ <b>¿Realmente quieres borrar todos los módulos?</b>"
        ),
        "clearmodules": "🗑 Borrar módulos",
        "cancel": "🚫 Cancelar",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Intentaste redefinir"
            " el código base del módulo (</b><code>{}</code><b>)</b>.\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> No informes de este error"
            " como un error. Esta es una característica de seguridad para evitar que se"
            " reemplace el código base de los módulos"
            " basura</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Intentaste redefinir"
            " este comando base (</b><code>{}{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> No informes de este error"
            " como un error. Este es el código base del comando"
            " basura</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>No se puede"
            " desactivar. módulo base</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> No informes de este error"
            " como un error. Este es un módulo base que no se puede basura</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>No se puede"
            " desactivar. biblioteca</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>El módulo"
            "</b> <code>{}</code> <b>solicita permiso para unirse al canal <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Motivo: {}</b>\n\n<i>Espera'
            ' <a href="https://t.me/{}">aprobación</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Módulo de instalación"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>El repositorio</b>"
            " <code>{}</code> <b>ya ha sido añadido</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>El repositorio</b>"
            " <code>{}</code> <b>ha sido añadido</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Necesitas especificar"
            " el repositorio a añadir</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>El repositorio</b>"
            " <code>{}</code> <b>no ha sido añadido</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>El repositorio</b>"
            " <code>{}</code> <b>ha sido eliminado</b>"
        ),
    }

    strings_kk = {
        "repo_config_doc": "Модульдерді жүктеу үшін сілтеме",
        "add_repo_config_doc": "Қосымша қоры",
        "avail_header": "🎢 <b>Репозиториядан қолданылатын официалды модульдер</b>",
        "select_preset": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Пресетті таңда</b>"
        ),
        "no_preset": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Пресет табылмады</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Пресет жүктелді</b>"
        ),
        "no_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Репозиторияда модуль"
            " жоқ.</b>"
        ),
        "no_file": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Файл табылмады</b>"
        ),
        "provide_module": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Жүктелетін модульді"
            " көрсет</b>"
        ),
        "bad_unicode": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Модульдің"
            " кодировкасы дұрыс емес</b>"
        ),
        "load_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Жүктелу сәтсіз"
            " аяқталды. Журналдарды қараңыз.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Модуль"
            "</b> <code>{}</code>{} <b>жүктелді {}</b>{}{}{}{}{}{}"
        ),
        "unloaded": "{} <b>Модуль {} аяқталды.</b>",
        "not_unloaded": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Модуль аяқталған"
            " жоқ.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Талаптарды орнату"
            " сәтсіз аяқталды</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5407025283456835913>🕶</emoji> <b>Талаптарды орнату"
            " сәтсіз аяқталды</b>\n<b>Бұл тұтынуы қызметінде Termux қолдау көрсетуге"
            " мүмкін емес бірнеше кітапханаларды қолданады. Осындай тұтынуын"
            " жібермеңіз, бүгін олдынайғы өзгертілмейді.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5328311576736833844>🚀</emoji> <b>Зависимостерді"
            " орнатуда:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5875145601682771643>🚀</emoji> <b>Зависимостер"
            " орнатылды, бірақ</b> <code>{}</code> <b>үшін қайта іске қосу"
            " керек</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Барлық модульдер"
            " жойылды</b>"
        ),
        "undoc": "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> Сипаттама жоқ",
        "ihandler": (
            "\n<emoji document_id=5372981976804366741>🤖</emoji> <code>{}</code> {}"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Бұл модульге"
            " Hikka {}+ туралы\n</b><code>.update</code> <b>коммандасын"
            " пайдаланып жаңартыңыз</b>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Бұл модульге"
            " FFMPEG керек, бірақ орнатылмаған</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5875452644599795072>🫶</emoji> <b>Әзірлеуші:</b> {}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Сыртқылар:"
            "</b> \n{}"
        ),
        "by": "кімнен",
        "module_fs": (
            "💿 <b>Сіз модульді жүктеудің кездесуін қалай болса, сіз оны жүктеп жинауға"
            " боладыңыз ба?</b>"
        ),
        "save": "💿 Сақтау",
        "no_save": "🚫 Сақтау",
        "save_for_all": "💽 Барлығында сақтау",
        "never_save": "🚫 Ешқашан сақтау",
        "will_save_fs": (
            "💽 Бұл уақыттан бастап, барлық файлдан жүктелген модульдер жүктеп жиналады"
        ),
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Бұл модульде"
            " HikkaInline талап етіледі, бірақ ондың инициализациясы"
            " ұмытты</b>\n<i>Ескі боттарды @BotFather-дан жоюға және ботты қайта"
            " жүктеуіңізді ұсыныңыз</i>"
        ),
        "_cmd_doc_dlmod": "Репозиториянан модульді жүктеу және орнату",
        "_cmd_doc_dlpreset": "Белгіленген нұсқа модулдерді жүктеу және орнату",
        "_cmd_doc_loadmod": "Файлдан модульді жүктеу және орнату",
        "_cmd_doc_unloadmod": "Модульді жою",
        "_cmd_doc_clearmodules": "Барлық орнатылған модульді жою",
        "_cls_doc": "Модульді жүктеу",
        "share_link_doc": (
            ".dlmod командасынан модульді жүктеуден кейін модульдің сілтемесін көрсету"
        ),
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Сілтеме:"
            "</b> <code>{}</code>"
        ),
        "blob_link": (
            "\n\n<emoji document_id=5312383351217201533>⚠️</emoji> <b>`blob` сілтемесін"
            " модульді жүктеу үшін пайдаланбаңыз. `raw` сілтемесін пайдалануға"
            " болады</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Сілтеме:"
            "</b> <code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n⭐️ <b>Бұл модуль {} жасады. Әкімшіге және модульдің жасаушысына қолдау"
            " үшін жазылыңыз ба?</b>"
        ),
        "subscribe": "💬 Бақылау",
        "no_subscribe": "🚫 Бақыламау",
        "subscribed": "💬 Бақылдым!",
        "unsubscribed": "🚫 Мен бұл каналға бақыламаймын",
        "confirm_clearmodules": "⚠️ <b>Барлық модульдерді жоюға сенімдісіз бе?</b>",
        "clearmodules": "🗑 Модульдерді жою",
        "cancel": "🚫 Болдырмау",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Бұл модуль қосымша"
            " модульдің жоғарғы бетін өзгертті (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Бұл қате емес, бұл құрамын"
            " қорғау үшін тиіс, қосымша модульдерді құрамын өзгерткенде қосымша"
            " модульдердің құрамын құрмасы үшін керек. Сұраныс чатына хабарламаңызды"
            " жібермеңізді сұраймыз</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Бұл модуль қосымша"
            " модульдің командасын өзгертті (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Бұл қате емес, бұл құрамын"
            " қорғау үшін тиіс, қосымша модульдерді құрамын өзгерткенде қосымша"
            " модульдердің құрамын құрмасы үшін керек. Сұраныс чатына хабарламаңызды"
            " жібермеңізді сұраймыз</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Сіз бастапқы"
            " модульді жоюға болмайсыз</b> <code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Бұл қате емес, ал құралдар"
            " қорғасын тұрақты жоғарыластыру үшін қажет. Бұл хабарламаны support"
            " чатына жібермеңіз</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Сіз біблиотеканы"
            " жоюға болмайсыз</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Модуль"
            "</b> <code>{}</code> <b>жүйеге қосылуы үшін <a"
            ' href="https://t.me/{}">{}</a> каналына кіруге рұқсат беру үшін сұраныс'
            ' жіберген.\n\n<b><emoji document_id="5467666648263564704">❓</emoji>'
            " Себебі: {}</b>\n\n<i>Рұқсат беру үшін <a"
            ' href="https://t.me/{}">күтіңіз</a>...</i>'
        ),
        "installing": (
            "<emoji document_id=5325792861885570739>🕔</emoji> <b>Модульді орнату"
            "</b> <code>{}</code><b>...</b>"
        ),
        "repo_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>іске қосылған</b>"
        ),
        "repo_added": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>қосылды</b>"
        ),
        "no_repo": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Қосу үшін repo"
            " белгілеуіңіз керек</b>"
        ),
        "repo_not_exists": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>қосылмаған</b>"
        ),
        "repo_deleted": (
            "<emoji document_id=5784993237412351403>✅</emoji> <b>Репозиторий</b>"
            " <code>{}</code> <b>жойылды</b>"
        ),
    }

    fully_loaded = False
    _links_cache = {}

    def __init__(self):
        self._pending_stats = []
        self._react_queue = []

        self._storage = RemoteStorage()

        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "MODULES_REPO",
                "https://mods.hikariatama.ru",
                lambda: self.strings("repo_config_doc"),
                validator=loader.validators.Link(),
            ),
            loader.ConfigValue(
                "ADDITIONAL_REPOS",
                # Currenly the trusted developers are specified
                [
                    "https://github.com/hikariatama/host/raw/master",
                    "https://github.com/MoriSummerz/ftg-mods/raw/main",
                    "https://gitlab.com/CakesTwix/friendly-userbot-modules/-/raw/master",
                ],
                lambda: self.strings("add_repo_config_doc"),
                validator=loader.validators.Series(validator=loader.validators.Link()),
            ),
            loader.ConfigValue(
                "share_link",
                doc=lambda: self.strings("share_link_doc"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def _async_init(self):
        modules = list(
            filter(
                lambda x: not x.startswith("https://mods.hikariatama.ru"),
                utils.array_sum(
                    map(
                        lambda x: list(x.values()),
                        (await self.get_repo_list("full")).values(),
                    )
                ),
            )
        )
        logger.debug("Modules: %s", modules)
        asyncio.ensure_future(self._storage.preload(modules))
        asyncio.ensure_future(self._storage.preload_main_repo())

    async def client_ready(self):
        self._reacted = self.pointer("reacted", [])
        self._token_msg = (await self._client.get_messages("@hikka_ub", ids=[10]))[0]

        self.allmodules.add_aliases(self.lookup("settings").get("aliases", {}))

        main.hikka.ready.set()

        asyncio.ensure_future(self._update_modules())
        asyncio.ensure_future(self._async_init())

    @loader.loop(interval=120, autostart=True)
    async def _react_processor(self):
        if not self._react_queue:
            return

        developer_entity, modname = self._react_queue.pop(0)
        try:
            await (
                await self._client.get_messages(
                    developer_entity,
                    limit=1,
                    search=modname,
                )
            )[0].react("❤️")
            self._reacted += [f"{developer_entity.id}/{modname}"]
        except Exception:
            logger.debug(
                "Unable to react to %s about %s",
                developer_entity.id,
                modname,
                exc_info=True,
            )

    @loader.loop(interval=3, wait_before=True, autostart=True)
    async def _config_autosaver(self):
        for mod in self.allmodules.modules:
            if (
                not hasattr(mod, "config")
                or not mod.config
                or not isinstance(mod.config, loader.ModuleConfig)
            ):
                continue

            for option, config in mod.config._config.items():
                if not hasattr(config, "_save_marker"):
                    continue

                delattr(mod.config._config[option], "_save_marker")
                mod.pointer("__config__", {})[option] = config.value

        for lib in self.allmodules.libraries:
            if (
                not hasattr(lib, "config")
                or not lib.config
                or not isinstance(lib.config, loader.ModuleConfig)
            ):
                continue

            for option, config in lib.config._config.items():
                if not hasattr(config, "_save_marker"):
                    continue

                delattr(lib.config._config[option], "_save_marker")
                lib._lib_pointer("__config__", {})[option] = config.value

        self._db.save()

    def update_modules_in_db(self):
        if self.allmodules.secure_boot:
            return

        self.set(
            "loaded_modules",
            {
                **{
                    module.__class__.__name__: module.__origin__
                    for module in self.allmodules.modules
                    if module.__origin__.startswith("http")
                },
                **{
                    module.name: module.url
                    for module in self.allmodules.dragon_modules
                    if module.url
                },
            },
        )

    @loader.owner
    @loader.command(
        ru_doc="Загрузить модуль из официального репозитория",
        it_doc="Carica un modulo dal repository ufficiale",
        de_doc="Lade ein Modul aus dem offiziellen Repository",
        tr_doc="Resmi depodan bir modül yükler",
        uz_doc="Ofitsial repodan modulni yuklash",
        es_doc="Cargar un módulo desde el repositorio oficial",
        kk_doc="Официалдық репозиториянан модульді жүктеу",
        alias="dlm",
    )
    async def dlmod(self, message: Message):
        """Install a module from the official module repo"""
        if args := utils.get_args(message):
            args = args[0]

            await self.download_and_install(args, message)
            if self.fully_loaded:
                self.update_modules_in_db()
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
    @loader.command(
        ru_doc="Установить пресет модулей",
        it_doc="Installa un preset di moduli",
        de_doc="Installiere ein Modul-Preset",
        tr_doc="Modül önbelleğini yükle",
        uz_doc="Modul presetini o'rnatish",
        es_doc="Instalar un conjunto de módulos",
        kk_doc="Модульдің пресетін орнату",
    )
    async def dlpreset(self, message: Message):
        """Set modules preset"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("select_preset"))
            return

        await self.get_repo_list(args[0])
        self.set("chosen_preset", args[0])

        await utils.answer(message, self.strings("preset_loaded"))
        await self.invoke("restart", "-f", message=message)

    async def _get_modules_to_load(self):
        preset = self.get("chosen_preset")

        if preset != "disable":
            possible_mods = (
                await self.get_repo_list(preset, only_primary=True)
            ).values()
            todo = dict(ChainMap(*possible_mods))
        else:
            todo = {}

        todo.update(**self.get("loaded_modules", {}))
        logger.debug("Loading modules: %s", todo)
        return todo

    async def _get_repo(self, repo: str, preset: str) -> str:
        repo = repo.strip("/")
        preset_id = f"{repo}/{preset}"

        if self._links_cache.get(preset_id, {}).get("exp", 0) >= time.time():
            return self._links_cache[preset_id]["data"]

        res = await utils.run_sync(
            requests.get,
            f"{repo}/{preset}.txt",
        )

        if not str(res.status_code).startswith("2"):
            logger.debug(
                "Can't load repo %s, preset %s because of %s status code",
                repo,
                preset,
                res.status_code,
            )
            return []

        self._links_cache[preset_id] = {
            "exp": time.time() + 5 * 60,
            "data": [link for link in res.text.strip().splitlines() if link],
        }

        return self._links_cache[preset_id]["data"]

    async def get_repo_list(
        self,
        preset: typing.Optional[str] = None,
        only_primary: bool = False,
    ) -> dict:
        if preset is None or preset == "none":
            preset = "minimal"

        return {
            repo: {
                f"Mod/{repo_id}/{i}": f'{repo.strip("/")}/{link}.py'
                for i, link in enumerate(set(await self._get_repo(repo, preset)))
            }
            for repo_id, repo in enumerate(
                [self.config["MODULES_REPO"]]
                + ([] if only_primary else self.config["ADDITIONAL_REPOS"])
            )
            if repo.startswith("http")
        }

    async def get_links_list(self) -> typing.List[str]:
        links = await self.get_repo_list("full")
        main_repo = list(links.pop(self.config["MODULES_REPO"]).values())
        return main_repo + list(dict(ChainMap(*list(links.values()))).values())

    async def _find_link(self, module_name: str) -> typing.Union[str, bool]:
        return next(
            filter(
                lambda link: link.lower().endswith(f"/{module_name.lower()}.py"),
                await self.get_links_list(),
            ),
            False,
        )

    async def download_and_install(
        self,
        module_name: str,
        message: typing.Optional[Message] = None,
    ):
        try:
            blob_link = False
            module_name = module_name.strip()
            if urlparse(module_name).netloc:
                url = module_name
                if re.match(
                    r"^(https:\/\/github\.com\/.*?\/.*?\/blob\/.*\.py)|"
                    r"(https:\/\/gitlab\.com\/.*?\/.*?\/-\/blob\/.*\.py)$",
                    url,
                ):
                    url = url.replace("/blob/", "/raw/")
                    blob_link = True
            else:
                url = await self._find_link(module_name)

                if not url:
                    if message is not None:
                        await utils.answer(message, self.strings("no_module"))

                    return False

            if message:
                message = await utils.answer(
                    message,
                    self.strings("installing").format(module_name),
                )

            try:
                r = await self._storage.fetch(url)
            except requests.exceptions.HTTPError:
                if message is not None:
                    await utils.answer(message, self.strings("no_module"))

                return False

            return await self.load_module(
                r,
                message,
                module_name,
                url,
                blob_link=blob_link,
            )
        except Exception:
            logger.exception("Failed to load %s", module_name)

    async def _inline__load(
        self,
        call: InlineCall,
        doc: str,
        path_: str,
        mode: str,
    ):
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

        await self.load_module(doc, call, origin=path_ or "<string>", save_fs=save)

    @loader.owner
    @loader.command(
        ru_doc="Загрузить модуль из файла",
        it_doc="Carica un modulo da un file",
        de_doc="Lade Modul aus Datei",
        tr_doc="Dosyadan modül yükle",
        uz_doc="Fayldan modulni yuklash",
        es_doc="Cargar módulo desde archivo",
        kk_doc="Файлдан модульді жүктеу",
        alias="lm",
    )
    async def loadmod(self, message: Message):
        """Loads the module file"""
        msg = message if message.file else (await message.get_reply_message())

        if msg is None or msg.media is None:
            await utils.answer(message, self.strings("provide_module"))
            return

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
                message = await message.respond("🌘", reply_to=utils.get_topic(message))

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

    @loader.loop(interval=120, autostart=True)
    async def _stats_sender(self):
        if not self._pending_stats or not self._db.get(main.__name__, "stats", True):
            return

        try:
            if not self.get("token"):
                self.set("token", (await self._token_msg.click(0)).message)

            res = await utils.run_sync(
                requests.post,
                "https://heta.hikariatama.ru/stats",
                data={"urls": ",".join(self._pending_stats[:50])},
                headers={"X-Hikka-Token": self.get("token")},
            )

            if res.status_code == 403:
                self.set("token", None)

            if res.status_code in range(200, 207):
                self._pending_stats = (
                    self._pending_stats[50:] if len(self._pending_stats) > 50 else []
                )

            res.raise_for_status()
        except Exception:
            logger.debug("Failed to send stats", exc_info=True)

    async def _send_stats(self, url: str, _=None):
        """Send anonymous stats to Hikka"""
        if self._db.get(main.__name__, "stats", True):
            self._pending_stats += [url]

    async def load_module(
        self,
        doc: str,
        message: Message,
        name: typing.Optional[str] = None,
        origin: str = "<string>",
        did_requirements: bool = False,
        save_fs: bool = False,
        blob_link: bool = False,
    ):
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
            ver = re.search(r"# ?scope: ?hikka_min ((?:\d+\.){2}\d+)", doc).group(1)
            ver_ = tuple(map(int, ver.split(".")))
            if main.__version__ < ver_:
                if isinstance(message, Message):
                    if getattr(message, "file", None):
                        m = utils.get_chat_id(message)
                        await message.edit("")
                    else:
                        m = message

                    await self.inline.form(
                        self.strings("version_incompatible").format(ver),
                        m,
                        reply_markup=[
                            {
                                "text": self.lookup("updater").strings("btn_update"),
                                "callback": self.lookup("updater").inline_update,
                            },
                            {
                                "text": self.lookup("updater").strings("cancel"),
                                "action": "close",
                            },
                        ],
                    )
                return

        developer = re.search(r"# ?meta developer: ?(.+)", doc)
        developer = developer.group(1) if developer else False

        blob_link = self.strings("blob_link") if blob_link else ""

        if utils.check_url(name):
            url = copy.deepcopy(name)
        elif utils.check_url(origin):
            url = copy.deepcopy(origin)
        else:
            url = None

        if name is None:
            try:
                node = ast.parse(doc)
                uid = next(
                    n.name
                    for n in node.body
                    if isinstance(n, ast.ClassDef)
                    and any(
                        isinstance(base, ast.Attribute)
                        and base.value.id == "Module"
                        or isinstance(base, ast.Name)
                        and base.id == "Module"
                        for base in n.bases
                    )
                )
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

        is_dragon = "@Client.on_message" in doc

        if is_dragon:
            module_name = f"dragon.modules.{uid}"
            if not self._client.pyro_proxy:
                self._client.pyro_proxy = PyroProxyClient(self._client)
                await self._client.pyro_proxy.start()
                await self._client.pyro_proxy.dispatcher.start()
                dragon.apply_compat(self._client)
        else:
            module_name = f"hikka.modules.{uid}"
            doc = geek.compat(doc)

        async def core_overwrite(e: CoreOverwriteError):
            nonlocal message

            with contextlib.suppress(Exception):
                self.allmodules.modules.remove(instance)

            if not message:
                return

            await utils.answer(
                message,
                self.strings(f"overwrite_{e.type}").format(
                    *(e.target,)
                    if e.type == "module"
                    else (self.get_prefix(), e.target)
                ),
            )

        async with (dragon.import_lock if is_dragon else lambda _: FakeLock())(
            self._client
        ):
            with (
                self._client.dragon_compat.misc.modules_help.get_notifier
                if is_dragon
                else FakeNotifier
            )() as notifier:
                try:
                    try:
                        spec = ModuleSpec(
                            module_name,
                            loader.StringLoader(doc, f"<external {module_name}>"),
                            origin=f"<external {module_name}>",
                        )
                        instance = await self.allmodules.register_module(
                            spec,
                            module_name,
                            origin,
                            save_fs=save_fs,
                            is_dragon=is_dragon,
                        )

                        if is_dragon:
                            dragon_module, instance = instance
                            instance.url = url
                    except ImportError as e:
                        logger.info(
                            "Module loading failed, attemping dependency installation"
                            " (%s)",
                            e.name,
                        )
                        # Let's try to reinstall dependencies
                        try:
                            requirements = list(
                                filter(
                                    lambda x: not x.startswith(("-", "_", ".")),
                                    map(
                                        str.strip,
                                        loader.VALID_PIP_PACKAGES.search(doc)[
                                            1
                                        ].split(),
                                    ),
                                )
                            )
                        except TypeError:
                            logger.warning(
                                "No valid pip packages specified in code, attemping"
                                " installation from error"
                            )
                            requirements = [
                                {
                                    "sklearn": "scikit-learn",
                                    "pil": "Pillow",
                                    "telethon": "Hikka-TL",
                                    "pyrogram": "Hikka-Pyro",
                                }.get(e.name.lower(), e.name)
                            ]

                        if not requirements:
                            raise Exception("Nothing to install") from e

                        logger.debug("Installing requirements: %s", requirements)

                        if did_requirements:
                            if message is not None:
                                await utils.answer(
                                    message,
                                    self.strings("requirements_restart").format(e.name),
                                )

                            return

                        if message is not None:
                            await utils.answer(
                                message,
                                self.strings("requirements_installing").format(
                                    "\n".join(
                                        "<emoji"
                                        " document_id=4971987363145188045>▫️</emoji>"
                                        f" {req}"
                                        for req in requirements
                                    )
                                ),
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
                            *["--user"] if loader.USER_INSTALL else [],
                            *requirements,
                        )

                        rc = await pip.wait()

                        if rc != 0:
                            if message is not None:
                                if "com.termux" in os.environ.get("PREFIX", ""):
                                    await utils.answer(
                                        message,
                                        self.strings("requirements_failed_termux"),
                                    )
                                else:
                                    await utils.answer(
                                        message,
                                        self.strings("requirements_failed"),
                                    )

                            return

                        importlib.invalidate_caches()

                        kwargs = utils.get_kwargs()
                        kwargs["did_requirements"] = True

                        return await self.load_module(**kwargs)  # Try again
                    except CoreOverwriteError as e:
                        await core_overwrite(e)
                        return
                    except loader.LoadError as e:
                        with contextlib.suppress(Exception):
                            await self.allmodules.unload_module(
                                instance.__class__.__name__
                            )

                        with contextlib.suppress(Exception):
                            self.allmodules.modules.remove(instance)

                        if message:
                            await utils.answer(
                                message,
                                "<emoji document_id=5454225457916420314>😖</emoji>"
                                f" <b>{utils.escape_html(str(e))}</b>",
                            )
                        return
                except Exception as e:
                    logger.exception("Loading external module failed due to %s", e)

                    if message is not None:
                        await utils.answer(message, self.strings("load_failed"))

                    return

                if hasattr(instance, "__version__") and isinstance(
                    instance.__version__, tuple
                ):
                    version = (
                        "<b><i>"
                        f" (v{'.'.join(list(map(str, list(instance.__version__))))})</i></b>"
                    )
                else:
                    version = ""

                try:
                    try:
                        self.allmodules.send_config_one(instance)

                        async def inner_proxy():
                            nonlocal instance, message
                            while True:
                                if hasattr(instance, "hikka_wait_channel_approve"):
                                    if message:
                                        (
                                            module,
                                            channel,
                                            reason,
                                        ) = instance.hikka_wait_channel_approve
                                        message = await utils.answer(
                                            message,
                                            self.strings("wait_channel_approve").format(
                                                module,
                                                channel.username,
                                                utils.escape_html(channel.title),
                                                utils.escape_html(reason),
                                                self.inline.bot_username,
                                            ),
                                        )
                                        return

                                await asyncio.sleep(0.1)

                        task = asyncio.ensure_future(inner_proxy())
                        await self.allmodules.send_ready_one(
                            instance,
                            no_self_unload=True,
                            from_dlmod=bool(message),
                        )
                        task.cancel()
                    except CoreOverwriteError as e:
                        await core_overwrite(e)
                        return
                    except loader.LoadError as e:
                        with contextlib.suppress(Exception):
                            await self.allmodules.unload_module(
                                instance.__class__.__name__
                            )

                        with contextlib.suppress(Exception):
                            self.allmodules.modules.remove(instance)

                        if message:
                            await utils.answer(
                                message,
                                "<emoji document_id=5454225457916420314>😖</emoji>"
                                f" <b>{utils.escape_html(str(e))}</b>",
                            )
                        return
                    except loader.SelfUnload as e:
                        logger.debug(
                            "Unloading %s, because it raised `SelfUnload`", instance
                        )
                        with contextlib.suppress(Exception):
                            await self.allmodules.unload_module(
                                instance.__class__.__name__
                            )

                        with contextlib.suppress(Exception):
                            self.allmodules.modules.remove(instance)

                        if message:
                            await utils.answer(
                                message,
                                "<emoji document_id=5454225457916420314>😖</emoji>"
                                f" <b>{utils.escape_html(str(e))}</b>",
                            )
                        return
                    except loader.SelfSuspend as e:
                        logger.debug(
                            "Suspending %s, because it raised `SelfSuspend`", instance
                        )
                        if message:
                            await utils.answer(
                                message,
                                "🥶 <b>Module suspended itself\nReason:"
                                f" {utils.escape_html(str(e))}</b>",
                            )
                        return
                except Exception as e:
                    logger.exception("Module threw because of %s", e)

                    if message is not None:
                        await utils.answer(message, self.strings("load_failed"))

                    return

                instance.hikka_meta_pic = next(
                    (
                        line.replace(" ", "").split("#metapic:", maxsplit=1)[1]
                        for line in doc.splitlines()
                        if line.replace(" ", "").startswith("#metapic:")
                    ),
                    None,
                )

                with contextlib.suppress(Exception):
                    if (
                        not any(
                            line.replace(" ", "") == "#scope:no_stats"
                            for line in doc.splitlines()
                        )
                        and url is not None
                        and utils.check_url(url)
                    ):
                        await self._send_stats(url)

                if is_dragon:
                    instance.name = (
                        "Dragon" + notifier.modname[0].upper() + notifier.modname[1:]
                    )
                    instance.commands = notifier.commands
                    self.allmodules.register_dragon(dragon_module, instance)
                else:
                    for alias, cmd in (
                        self.lookup("settings").get("aliases", {}).items()
                    ):
                        if cmd in instance.commands:
                            self.allmodules.add_alias(alias, cmd)

            try:
                modname = instance.strings("name")
            except (KeyError, AttributeError):
                modname = getattr(instance, "name", "ERROR")

            try:
                developer_entity = await (
                    self._client.force_get_entity
                    if (
                        developer in self._client._hikka_entity_cache
                        and getattr(
                            await self._client.get_entity(developer), "left", True
                        )
                    )
                    else self._client.get_entity
                )(developer)
            except Exception:
                developer_entity = None

            if not isinstance(developer_entity, Channel):
                developer_entity = None

            if (
                developer_entity is not None
                and f"{developer_entity.id}/{modname}" not in self._reacted
            ):
                self._react_queue += [(developer_entity, modname)]

            if message is None:
                return

            modhelp = ""

            if instance.__doc__:
                modhelp += (
                    "<i>\n<emoji document_id=5787544344906959608>ℹ️</emoji>"
                    f" {utils.escape_html(inspect.getdoc(instance))}</i>\n"
                )

            subscribe = ""
            subscribe_markup = None

            depends_from = []
            for key in dir(instance):
                value = getattr(instance, key)
                if isinstance(value, loader.Library):
                    depends_from.append(
                        "<emoji document_id=4971987363145188045>▫️</emoji>"
                        " <code>{}</code> <b>{}</b> <code>{}</code>".format(
                            value.__class__.__name__,
                            self.strings("by"),
                            (
                                value.developer
                                if isinstance(getattr(value, "developer", None), str)
                                else "Unknown"
                            ),
                        )
                    )

            depends_from = (
                self.strings("depends_from").format("\n".join(depends_from))
                if depends_from
                else ""
            )

            def loaded_msg(use_subscribe: bool = True):
                nonlocal modname, version, modhelp, developer, origin, subscribe, blob_link, depends_from
                return self.strings("loaded").format(
                    modname.strip(),
                    version,
                    utils.ascii_face(),
                    modhelp,
                    developer if not subscribe or not use_subscribe else "",
                    depends_from,
                    (
                        self.strings("modlink").format(origin)
                        if origin != "<string>" and self.config["share_link"]
                        else ""
                    ),
                    blob_link,
                    subscribe if use_subscribe else "",
                )

            if developer:
                if developer.startswith("@") and developer not in self.get(
                    "do_not_subscribe", []
                ):
                    if (
                        developer_entity
                        and getattr(developer_entity, "left", True)
                        and self._db.get(main.__name__, "suggest_subscribe", True)
                    ):
                        subscribe = self.strings("suggest_subscribe").format(
                            f"@{utils.escape_html(developer_entity.username)}"
                        )
                        subscribe_markup = [
                            {
                                "text": self.strings("subscribe"),
                                "callback": self._inline__subscribe,
                                "args": (
                                    developer_entity.id,
                                    functools.partial(loaded_msg, use_subscribe=False),
                                    True,
                                ),
                            },
                            {
                                "text": self.strings("no_subscribe"),
                                "callback": self._inline__subscribe,
                                "args": (
                                    developer,
                                    functools.partial(loaded_msg, use_subscribe=False),
                                    False,
                                ),
                            },
                        ]

                developer = self.strings("developer").format(
                    utils.escape_html(developer)
                    if isinstance(developer_entity, Channel)
                    else f"<code>{utils.escape_html(developer)}</code>"
                )
            else:
                developer = ""

            if any(
                line.replace(" ", "") == "#scope:disable_onload_docs"
                for line in doc.splitlines()
            ):
                await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
                return

            for _name, fun in sorted(
                instance.commands.items(),
                key=lambda x: x[0],
            ):
                modhelp += "\n{} <code>{}{}</code> {}".format(
                    (
                        dragon.DRAGON_EMOJI
                        if is_dragon
                        else "<emoji document_id=4971987363145188045>▫️</emoji>"
                    ),
                    self.get_prefix("dragon" if is_dragon else None),
                    _name,
                    (
                        utils.escape_html(fun)
                        if is_dragon
                        else (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings("undoc")
                        )
                    ),
                )

            if self.inline.init_complete and not is_dragon:
                for _name, fun in sorted(
                    instance.inline_handlers.items(),
                    key=lambda x: x[0],
                ):
                    modhelp += self.strings("ihandler").format(
                        f"@{self.inline.bot_username} {_name}",
                        (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings("undoc")
                        ),
                    )

            try:
                await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
            except telethon.errors.rpcerrorlist.MediaCaptionTooLongError:
                await message.reply(loaded_msg(False))

    async def _inline__subscribe(
        self,
        call: InlineCall,
        entity: int,
        msg: typing.Callable[[], str],
        subscribe: bool,
    ):
        if not subscribe:
            self.set("do_not_subscribe", self.get("do_not_subscribe", []) + [entity])
            await utils.answer(call, msg())
            await call.answer(self.strings("not_subscribed"))
            return

        await self._client(JoinChannelRequest(entity))
        await utils.answer(call, msg())
        await call.answer(self.strings("subscribed"))

    @loader.owner
    @loader.command(
        ru_doc="Выгрузить модуль",
        it_doc="Scarica il modulo",
        de_doc="Entlädt ein Modul",
        tr_doc="Bir modülü kaldırır",
        uz_doc="Modulni o'chirish",
        es_doc="Descargar el módulo",
        kk_doc="Модульді жою",
    )
    async def unloadmod(self, message: Message):
        """Unload module by class name"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("no_class"))
            return

        instance = self.lookup(args, include_dragon=True)

        if issubclass(instance.__class__, loader.Library):
            await utils.answer(message, self.strings("cannot_unload_lib"))
            return

        is_dragon = isinstance(instance, DragonModule)

        if is_dragon:
            worked = [instance.name] if self.allmodules.unload_dragon(instance) else []
        else:
            try:
                worked = await self.allmodules.unload_module(args)
            except CoreUnloadError as e:
                await utils.answer(
                    message,
                    self.strings("unload_core").format(e.module),
                )
                return

        if not self.allmodules.secure_boot:
            self.set(
                "loaded_modules",
                {
                    mod: link
                    for mod, link in self.get("loaded_modules", {}).items()
                    if mod not in worked
                },
            )

        msg = (
            self.strings("unloaded").format(
                dragon.DRAGON_EMOJI
                if is_dragon
                else "<emoji document_id=5784993237412351403>✅</emoji>",
                ", ".join(
                    [(mod[:-3] if mod.endswith("Mod") else mod) for mod in worked]
                ),
            )
            if worked
            else self.strings("not_unloaded")
        )

        await utils.answer(message, msg)

    @loader.owner
    @loader.command(
        ru_doc="Удалить все модули",
        it_doc="Rimuovi tutti i moduli",
        de_doc="Entfernt alle Module",
        tr_doc="Tüm modülleri kaldırır",
        uz_doc="Barcha modullarni o'chirish",
        es_doc="Eliminar todos los módulos",
        kk_doc="Барлық модульді жою",
    )
    async def clearmodules(self, message: Message):
        """Delete all installed modules"""
        await self.inline.form(
            self.strings("confirm_clearmodules"),
            message,
            reply_markup=[
                {
                    "text": self.strings("clearmodules"),
                    "callback": self._inline__clearmodules,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    @loader.command(
        ru_doc="Добавить дополнительный репозиторий",
        it_doc="Aggiungi un repository aggiuntivo",
        de_doc="Fügt ein zusätzliches Repository hinzu",
        tr_doc="Ek bir depo ekler",
        uz_doc="Qo'shimcha repozitoriyani qo'shish",
        es_doc="Añadir un repositorio adicional",
        kk_doc="Қосымша қойымдық қосу",
    )
    async def addrepo(self, message: Message):
        """Add a repository to the list of repositories"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_repo"))
            return

        if args in self.config["ADDITIONAL_REPOS"]:
            await utils.answer(message, self.strings("repo_exists"))
            return

        self.config["ADDITIONAL_REPOS"].value = self.config["ADDITIONAL_REPOS"] + [args]

        await utils.answer(message, self.strings("repo_added").format(args))

    @loader.command(
        ru_doc="Удалить дополнительный репозиторий",
        it_doc="Rimuovi un repository aggiuntivo",
        de_doc="Entfernt ein zusätzliches Repository",
        tr_doc="Ek bir depoyu kaldırır",
        uz_doc="Qo'shimcha repozitoriyani o'chirish",
        es_doc="Eliminar un repositorio adicional",
        kk_doc="Қосымша қойымдықты жою",
    )
    async def delrepo(self, message: Message):
        """Remove a repository from the list of repositories"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_repo"))
            return

        if args not in self.config["ADDITIONAL_REPOS"]:
            await utils.answer(message, self.strings("repo_not_exists"))
            return

        self.config["ADDITIONAL_REPOS"].value = [
            repo for repo in self.config["ADDITIONAL_REPOS"] if repo != args
        ]

        await utils.answer(message, self.strings("repo_deleted").format(args))

    async def _inline__clearmodules(self, call: InlineCall):
        self.set("loaded_modules", {})

        for file in os.scandir(loader.LOADED_MODULES_DIR):
            try:
                shutil.rmtree(file.path)
            except Exception:
                logger.debug("Failed to remove %s", file.path, exc_info=True)

        self.set("chosen_preset", "none")

        await utils.answer(call, self.strings("all_modules_deleted"))
        await self.lookup("Updater").restart_common(call)

    async def _update_modules(self):
        todo = await self._get_modules_to_load()

        self._secure_boot = False

        if self._db.get(loader.__name__, "secure_boot", False):
            self._db.set(loader.__name__, "secure_boot", False)
            self._secure_boot = True
        else:
            for mod in todo.values():
                await self.download_and_install(mod)

            self.update_modules_in_db()

            aliases = {
                alias: cmd
                for alias, cmd in self.lookup("settings").get("aliases", {}).items()
                if self.allmodules.add_alias(alias, cmd)
            }

            self.lookup("settings").set("aliases", aliases)

        self.fully_loaded = True

        with contextlib.suppress(AttributeError):
            await self.lookup("Updater").full_restart_complete(self._secure_boot)

    async def reload_core(self) -> int:
        """Forcefully reload all core modules"""
        self.fully_loaded = False

        if self._secure_boot:
            self._db.set(loader.__name__, "secure_boot", True)

        for module in self.allmodules.modules:
            if module.__origin__.startswith("<core"):
                module.__origin__ = "<reload-core>"

        loaded = await self.allmodules.register_all(no_external=True)
        for instance in loaded:
            self.allmodules.send_config_one(instance)
            await self.allmodules.send_ready_one(
                instance,
                no_self_unload=False,
                from_dlmod=False,
            )

        self.fully_loaded = True
        return len(loaded)
