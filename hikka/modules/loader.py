"""Loads and registers modules"""

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import copy
import functools
import importlib
import inspect
import logging
import os
import re
import ast
import sys
import time
import uuid
from collections import ChainMap
from importlib.machinery import ModuleSpec
import typing

from urllib.parse import urlparse

import requests
import telethon
from telethon.tl.types import Message, Channel
from telethon.tl.functions.channels import JoinChannelRequest

from .. import loader, main, utils
from ..compat import geek
from ..inline.types import InlineCall
from ..types import CoreOverwriteError, CoreUnloadError

logger = logging.getLogger(__name__)


@loader.tds
class LoaderMod(loader.Module):
    """Loads modules"""

    strings = {
        "name": "Loader",
        "repo_config_doc": "URL to a module repo",
        "avail_header": (
            "<emoji document_id=6321352876505434037>🎢</emoji><b> Modules from repo</b>"
        ),
        "select_preset": "<b>⚠️ Please select a preset</b>",
        "no_preset": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Preset not found</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Preset loaded</b>"
        ),
        "no_module": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Module not available"
            " in repo.</b>"
        ),
        "no_file": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> File not found</b>"
        ),
        "provide_module": "<b>⚠️ Provide a module to load</b>",
        "bad_unicode": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Invalid Unicode"
            " formatting in module</b>"
        ),
        "load_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Loading failed. See"
            " logs for details</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b> Module"
            " </b><code>{}</code>{}<b> loaded {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>What class needs to be unloaded?</b>",
        "unloaded": (
            "<emoji document_id=5469654973308476699>💣</emoji><b> Module {}"
            " unloaded.</b>"
        ),
        "not_unloaded": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Module not"
            " unloaded.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Requirements"
            " installation failed</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5386399931378440814>🕶</emoji> <b>Requirements"
            " installation failed</b>\n<b>The most common reason is that Termux doesn't"
            " support many libraries. Don't report it as bug, this can't be solved.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Installing"
            " requirements:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Requirements"
            " installed, but a restart is required for </b><code>{}</code><b> to"
            " apply</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> All modules"
            " deleted</b>"
        ),
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 No docs",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 No docs",
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module requires"
            " Hikka inline feature and initialization of InlineManager"
            " failed</b>\n<i>Please, remove one of your old bots from @BotFather and"
            " restart userbot to load this module</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module requires"
            " Hikka {}+\nPlease, update with </b><code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>This module requires"
            " FFMPEG, which is not installed</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5431376038628171216>👨‍💻</emoji> <b>Developer:"
            " </b>{}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Dependencies:"
            " </b>\n{}"
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
            " </b><code>{}</code>"
        ),
        "blob_link": (
            "\n🚸 <b>Do not use `blob` links to download modules. Consider switching to"
            " `raw` instead</b>"
        ),
        "suggest_subscribe": (
            "\n\n<emoji document_id=5456129670321806826>⭐️</emoji><b>This module is"
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
            " core module </b><code>{}</code><b></b>\n\n<emoji"
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
            " </b><code>{}</code><b> requests permission to join channel <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Reason: {}</b>\n\n<i>Waiting'
            ' for <a href="https://t.me/{}">approval</a>...</i>'
        ),
    }

    strings_ru = {
        "repo_config_doc": "Ссылка для загрузки модулей",
        "add_repo_config_doc": "Дополнительные репозитории",
        "avail_header": (
            "<emoji document_id=6321352876505434037>🎢</emoji><b> Официальные модули"
            " из репозитория</b>"
        ),
        "select_preset": "<b>⚠️ Выбери пресет</b>",
        "no_preset": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Пресет не найден</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Пресет загружен</b>"
        ),
        "no_module": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Модуль недоступен в"
            " репозитории.</b>"
        ),
        "no_file": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Файл не найден</b>"
        ),
        "provide_module": "<b>⚠️ Укажи модуль для загрузки</b>",
        "bad_unicode": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Неверная кодировка"
            " модуля</b>"
        ),
        "load_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Загрузка не"
            " увенчалась успехом. Смотри логи.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b> Модуль"
            " </b><code>{}</code>{}<b> загружен {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>А что выгружать то?</b>",
        "unloaded": (
            "<emoji document_id=5469654973308476699>💣</emoji><b> Модуль {}"
            " выгружен.</b>"
        ),
        "not_unloaded": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Модуль не"
            " выгружен.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Ошибка установки"
            " зависимостей</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5386399931378440814>🕶</emoji> <b>Ошибка установки"
            " зависимостей</b>\n<b>Наиболее часто возникает из-за того, что Termux не"
            " поддерживает многие библиотеки. Не сообщайте об этом как об ошибке, это"
            " не может быть исправлено.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Устанавливаю"
            " зависимости:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Зависимости"
            " установлены, но нужна перезагрузка для применения </b><code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Модули удалены</b>"
        ),
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 Нет описания",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 Нет описания",
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этому модулю"
            " требуется Hikka версии {}+\nОбновись с помощью </b><code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Этому модулю"
            " требуется FFMPEG, который не установлен</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5431376038628171216>👨‍💻</emoji> <b>Разработчик:"
            " </b>{}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Зависимости:"
            " </b>\n{}"
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
            " </b><code>{}</code>"
        ),
        "blob_link": (
            "\n🚸 <b>Не используй `blob` ссылки для загрузки модулей. Лучше загружать из"
            " `raw`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Ссылка:"
            " </b><code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n<emoji document_id=5456129670321806826>⭐️</emoji><b>Этот модуль"
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
            " выгрузить встроенный модуль </b><code>{}</code><b></b>\n\n<emoji"
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
            " </b><code>{}</code><b> запрашивает разрешение на вступление в канал <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Причина:'
            ' {}</b>\n\n<i>Ожидание <a href="https://t.me/{}">подтверждения</a>...</i>'
        ),
    }

    strings_de = {
        "repo_config_doc": "Modul-Download-Link",
        "add_repo_config_doc": "Zusätzliche Repositorys",
        "avail_header": (
            "<emoji document_id=6321352876505434037>🎢</emoji><b> Offizielle Module"
            "aus Repository</b>"
        ),
        "select_preset": "<b>⚠️ Voreinstellung auswählen</b>",
        "no_preset": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Voreinstellung nicht"
            " gefunden</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Voreinstellung"
            " geladen</b>"
        ),
        "no_module": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Modul nicht verfügbar"
            " in Repositorys.</b>"
        ),
        "no_file": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b>Datei nicht"
            " gefunden</b>"
        ),
        "provide_module": "<b>⚠️ Geben Sie ein zu ladendes Modul an</b>",
        "bad_unicode": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Ungültige Codierung"
            "Modul</b>"
        ),
        "load_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Lädt nicht"
            " war erfolgreich. Sehen Sie sich die Protokolle an.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b> Modul"
            " </b><code>{}</code>{}<b> geladen {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Was soll dann hochgeladen werden?</b>",
        "unloaded": (
            "<emoji document_id=5469654973308476699>💣</emoji><b> {} Modul entladen.</b>"
        ),
        "not_unloaded": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Modul nicht"
            " entladen.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Installation"
            " fehlgeschlagen Abhängigkeiten</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5386399931378440814>🕶</emoji> <b>Installation"
            " fehlgeschlagenAbhängigkeiten</b>\n<b>Tritt am häufigsten auf, weil Termux"
            " dies nicht tutunterstützt viele Bibliotheken. Melden Sie dies nicht als"
            " Fehler, es ist kann nicht behoben werden.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Wird installiert"
            " Abhängigkeiten:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Abhängigkeiten"
            " installiert, muss aber neu gestartet werden, um </b><code>{}</code>"
            " anzuwenden"
        ),
        "all_modules_deleted": (
            "<emoji document_id=6323332130579416910>✅</emoji><b>Module entfernt</b>"
        ),
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 Keine Beschreibung",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 Keine Beschreibung",
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Zu diesem Modul"
            "erfordert Hikka-Version {}+\nUpdate mit </b><code>.update</code>"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Zu diesem Modul"
            "benötigt FFMPEG, das nicht installiert ist</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5431376038628171216>👨‍💻</emoji> <b>Entwickler:"
            "</b>{}"
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
            "\n🚸 <b>Verwenden Sie keine `Blob`-Links, um Module zu laden. Laden Sie"
            " besser von`roh`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Link:"
            "</b><code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n<emoji document_id=5456129670321806826>⭐️</emoji><b>Dieses Modul"
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
            " integriertes Modul entladen"
            " </b><code>{}</code><b></b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
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
            " </b><code>{}</code><b> bittet um Erlaubnis, Kanal <a beizutreten"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Grund:'
            ' {}</b>\n\n<i>Warten auf <a href="https://t.me/{}">Bestätigung</a>...</i>'
        ),
    }

    strings_tr = {
        "repo_config_doc": "Bir modül deposunun URL'si",
        "avail_header": (
            "<emoji document_id=6321352876505434037>🎢</emoji><b> Depodan modüller</b>"
        ),
        "select_preset": "<b>⚠️ Lütfen bir ön ayar seçin</b>",
        "no_preset": (
            "<emoji document_id=53752013968596607943>🚫</emoji><b> Ön ayar"
            " bulunamadı</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Ön ayar yüklendi</b>"
        ),
        "no_module": (
            "<emoji document_id=53752013968596607943>🚫</emoji><b> Modül mevcut değil"
            " depoda.</b>"
        ),
        "no_file": (
            "<emoji document_id=53752013968596607943>🚫</emoji><b> Dosya bulunamadı</b>"
        ),
        "provide_module": "<b>⚠️ Yüklenecek bir modül sağlayın</b>",
        "bad_unicode": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Geçersiz Unicode"
            " modülde biçimlendirme</b>"
        ),
        "load_failed": (
            "<emoji document_id=53752013968596607943>🚫</emoji><b> Yükleme başarısız"
            " oldu. Bkz. ayrıntılar için günlükler</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b> Modülü"
            " </b><code>{}</code>{}<b> yüklendi {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Hangi sınıfın kaldırılması gerekiyor?</b>",
        "unloaded": (
            "<emoji document_id=546965497330847699>💣</emoji><b> Modül {}"
            " boşaltıldı.</b>"
        ),
        "not_unloaded": (
            "<emoji document_id=53752013968596607943>🚫</emoji><b> Modül yok"
            " boşaltıldı.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Gereksinimler"
            " yükleme başarısız oldu</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5386399931378440814>🕶</emoji> <b>Gereksinimler"
            " kurulum başarısız oldu</b>\n<b>En yaygın neden Termux'un çalışmamasıdır"
            " birçok kütüphaneyi destekler. Hata olarak bildirme, bu çözülemez.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Yükleniyor"
            " gereksinimler:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Gereksinimler"
            " yüklendi, ancak </b><code>{}</code><b> için yeniden başlatma gerekiyor"
            "uygula</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Tüm modüller"
            " silindi</b>"
        ),
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 Doküman yok",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 Doküman yok",
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül gerektirir"
            " Hikka satır içi özelliği ve InlineManager'ın başlatılması"
            " başarısız</b>\n<i>Lütfen eski botlarınızdan birini @BotFather'dan"
            " kaldırın ve bu modülü yüklemek için userbot'u yeniden başlatın</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül gerektirir"
            " Hikka {}+\nLütfen, </b><code>.update</code> ile güncelleyin"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül gerektirir"
            "Yüklü olmayan FFMPEG</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5431376038628171216>👨‍💻</emoji> <b>Geliştirici:"
            " </b>{}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>Bağımlılıklar:"
            " </b>\n{}"
        ),
        "module_fs": (
            "💿 <b>Bu modülü dosya sistemine kaydetmek ister misiniz?"
            " yeniden başlattıktan sonra kaldırıldı mı?</b>"
        ),
        "save": "💿 Kaydet",
        "no_save": "🚫 Kaydetme",
        "save_for_all": "💽 Her zaman fs'ye kaydet",
        "never_save": "🚫 Asla fs'ye kaydetme",
        "will_save_fs": (
            "💽 Artık .loadmod ile yüklenen tüm modüller dosya sistemine kaydedilecek"
        ),
        "add_repo_config_doc": "Yüklenecek ek depolar",
        "share_link_doc": ".dlmod'un sonuç mesajında ​​modül bağlantısını paylaşın",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Bağlantı:"
            " </b><code>{}</code>"
        ),
        "blob_link": (
            "\n🚸 <b>Modülleri indirmek için `blob` bağlantılarını kullanmayın. Geçiş"
            " yapmayı düşünün 'ham' yerine</b>"
        ),
        "suggest_subscribe": (
            "\n\n<emoji document_id=5456129670321806826>⭐️</emoji><b>Bu modül {}"
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
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modül çekirdeği"
            " geçersiz kılmaya çalıştı (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Hata olarak"
            " bildirmeyin.Çekirdek modüllerin bazılarıyla değiştirilmesini önlemek için"
            " bir güvenlik önlemi önemsiz</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Bu modülçekirdek"
            " komutu geçersiz kılmaya çalıştı (</b><code>{}{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Hata olarak"
            " bildirmeyin.Çekirdek modüllerin komutlarının değiştirilmesini önlemek"
            " için bir güvenlik önlemidir biraz önemsiz</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Yükleyemezsiniz"
            " çekirdek modül </b><code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> Hata olarak"
            " bildirmeyin.Çekirdek modüllerin bazılarıyla değiştirilmesini önlemek için"
            " bir güvenlik önlemi önemsiz</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Yükleyemezsiniz"
            "kütüphane</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>Modül"
            " </b><code>{}</code><b> kanalına katılmak için izin istiyor <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Sebep: {}</b>\n\n<i>Bekliyor'
            ' <a href="https://t.me/{}">onay</a>...</i> için'
        ),
    }

    strings_hi = {
        "repo_config_doc": "मॉड्यूल रेपो का URL",
        "avail_header": (
            "<emoji document_id=6321352876505434037>🎢</emoji><b> रेपो से मॉड्यूल</b>"
        ),
        "select_preset": "<b>⚠️ कृपया एक प्रीसेट चुनें</b>",
        "no_preset": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> प्रीसेट नहीं मिला</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> प्रीसेट लोड किया"
            " गया</b>"
        ),
        "no_module": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> मॉड्यूल उपलब्ध नहीं है"
            "रेपो में।</b>"
        ),
        "no_file": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> फ़ाइल नहीं मिली</b>"
        ),
        "provide_module": "<b>⚠️ लोड करने के लिए एक मॉड्यूल प्रदान करें</b>",
        "bad_unicode": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> अमान्य यूनिकोड"
            "मॉड्यूल में स्वरूपण</b>"
        ),
        "load_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> लोड हो रहा है विफल।"
            " देखेंविवरण के लिए लॉग</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b> मॉड्यूल"
            " </b><code>{}</code>{}<b> लोड किया गया {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>किस वर्ग को अनलोड करने की आवश्यकता है?</b>",
        "unloaded": (
            "<emoji document_id=5469654973308476699>💣</emoji><b> मॉड्यूल {}"
            "अनलोड किया गया।</b>"
        ),
        "not_unloaded": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> मॉड्यूल नहीं"
            "अनलोड किया गया।</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> आवश्यकताएँ"
            "स्थापना विफल</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5386399931378440814>🕶</emoji> <b>आवश्यकताएं इंस्टॉलेशन"
            " विफल</b>\n<b>सबसे आम कारण यह है कि टर्मक्स नहीं करता हैकई पुस्तकालयों का"
            " समर्थन करें। इसे बग के रूप में रिपोर्ट न करें, इसे हल नहीं किया जा सकता"
            " है।</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> इंस्टॉल करना"
            "आवश्यकताएं:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> आवश्यकताएँ स्थापित है,"
            " लेकिन </b><code>{}</code><b> से के लिए पुनः आरंभ करना आवश्यक हैलागू"
            " करें</b>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> सभी मॉड्यूल"
            "हटाया गया</b>"
        ),
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 नो डॉक्स",
        "ihandler": "\n🎹 <कोड>{}</कोड> {}",
        "undoc_ihandler": "🦥 नो डॉक्स",
        "inline_init_failed": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>इस मॉड्यूल की आवश्यकता"
            " हैहिक्का इनलाइन फीचर और इनलाइनमैनेजर का इनिशियलाइज़ेशन"
            " विफल</b>\n<i>कृपया, @BotFather से अपना एक पुराना बॉट हटा दें औरइस मॉड्यूल"
            " को लोड करने के लिए यूजरबॉट को पुनरारंभ करें</i>"
        ),
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>इस मॉड्यूल की आवश्यकता"
            " हैहिक्का {}+\nकृपया, </b><code>.update</code> से अपडेट करें"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>इस मॉड्यूल की आवश्यकता"
            " है FFMPEG, जो स्थापित नहीं है</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5431376038628171216>👨‍💻</emoji> <b>डेवलपर: </b>{}"
        ),
        "depends_from": (
            "\n\n<emoji document_id=5431736674147114227>📦</emoji> <b>निर्भरता: </b>\n{}"
        ),
        "by": "द्वारा",
        "module_fs": (
            "💿 <b>क्या आप इस मॉड्यूल को फाइल सिस्टम में सहेजना चाहेंगे, इसलिए यह नहीं"
            " मिलेगापुनः आरंभ करने के बाद अनलोड किया गया?</b>"
        ),
        "save": "💿 सहेजें",
        "no_save": "🚫 सेव न करें",
        "save_for_all": "💽 हमेशा fs में सेव करें",
        "never_save": "🚫 कभी भी fs में सेव न करें",
        "will_save_fs": (
            "💽 अब .loadmod से लोड किए गए सभी मॉड्यूल फाइल सिस्टम में सहेजे जाएंगे"
        ),
        "add_repo_config_doc": "लोड करने के लिए अतिरिक्त रेपो",
        "share_link_doc": ".dlmod के परिणाम संदेश में मॉड्यूल लिंक साझा करें",
        "modlink": (
            "\n\n<emoji document_id=6037284117505116849>🌐</emoji> <b>लिंक:"
            " </b><कोड>{}</कोड>"
        ),
        "blob_link": (
            "\n🚸 <b>मॉड्यूल डाउनलोड करने के लिए `ब्लॉब` लिंक का उपयोग न करें। स्विच"
            " करने पर विचार करें इसके बजाय 'कच्चा'</b>"
        ),
        "suggest_subcribe": (
            "\n\n<emoji document_id=5456129670321806826>⭐️</emoji><b>यह मॉड्यूल है {}"
            " द्वारा बनाया गया। क्या आप डेवलपर का समर्थन करने के लिए इस चैनल से जुड़ना"
            " चाहते हैं?</b>"
        ),
        "subscribe": "💬 सदस्यता लें",
        "no_subscribe": "🚫 सब्सक्राइब न करें",
        "subscribed": "💬 सब्स्क्राइब्ड",
        "not_subcribed": "🚫 मैं अब इस चैनल को सब्सक्राइब करने का सुझाव नहीं दूंगा",
        "confirm_clearmodules": (
            "⚠️ <b>क्या आप वाकई सभी मॉड्यूल साफ़ करना चाहते हैं?</b>"
        ),
        "clearmodules": "🗑 मॉड्यूल साफ़ करें",
        "cancel": "🚫 रद्द करें",
        "overwrite_module": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>यह मॉड्यूल मूल एक को"
            " ओवरराइड करने का प्रयास किया (</b><code>{}</code><b>)</b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> इसे बग के रूप में रिपोर्ट न"
            " करें।कोर मॉड्यूल को कुछ के साथ बदलने से रोकने के लिए यह एक सुरक्षा उपाय"
            " हैजंक</i>"
        ),
        "overwrite_command": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>यह मॉड्यूलकोर कमांड को"
            " ओवरराइड करने का प्रयास किया (</b><code>{}{}</code><b>)</b>\n\n<इमोजी"
            " document_id=5472146462362048818>💡</emoji><i> इसे बग के रूप में रिपोर्ट न"
            " करें।यह कोर मॉड्यूल के कमांड को बदलने से रोकने के लिए एक सुरक्षा उपाय"
            " हैकुछ कबाड़</i>"
        ),
        "unload_core": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>आप अनलोड नहीं कर सकते"
            " कोर मॉड्यूल </b><code>{}</code><b></b>\n\n<emoji"
            " document_id=5472146462362048818>💡</emoji><i> इसे बग के रूप में रिपोर्ट न"
            " करें।कोर मॉड्यूल को कुछ के साथ बदलने से रोकने के लिए यह एक सुरक्षा उपाय"
            " हैजंक</i>"
        ),
        "cannot_unload_lib": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>आप अनलोड नहीं कर सकते"
            "लाइब्रेरी</b>"
        ),
        "wait_channel_approve": (
            "<emoji document_id=5469741319330996757>💫</emoji> <b>मॉड्यूल"
            " </b><code>{}</code><b> चैनल से जुड़ने की अनुमति का अनुरोध करता है <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> कारण: {}</b>\n\n<i>प्रतीक्षा'
            ' के लिए <a href="https://t.me/{}">स्वीकृति</a>...</i>'
        ),
    }

    strings_uz = {
        "repo_config_doc": "Modulni yuklab olish havolasi",
        "add_repo_config_doc": "Qo'shimcha omborlar",
        "avail_header": (
            "<emoji document_id=6321352876505434037>🎢</emoji><b> Rasmiy modullar"
            "ombordan</b>"
        ),
        "select_preset": "<b>⚠️ Oldindan sozlashni tanlang</b>",
        "no_preset": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Oldindan sozlash"
            " topilmadi</b>"
        ),
        "preset_loaded": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Oldindan"
            " o'rnatilgan</b>"
        ),
        "no_module": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> modul mavjud emas"
            " omborlar</b>"
        ),
        "no_file": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Fayl topilmadi</b>"
        ),
        "provide_module": "<b>⚠️ Yuklanadigan modulni belgilang</b>",
        "bad_unicode": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> yaroqsiz kodlash"
            "modul</b>"
        ),
        "load_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Yuklanmayapti"
            " Muvaffaqiyatli. Jurnallarga qarang.</b>"
        ),
        "loaded": (
            "<emoji document_id=5188377234380954537>🌘</emoji><b> moduli"
            " </b><code>{}</code>{}<b> yuklangan {}</b>{}{}{}{}{}{}"
        ),
        "no_class": "<b>Unda nima yuklash kerak?</b>",
        "unloaded": (
            "<emoji document_id=5469654973308476699>💣</emoji><b> {} moduli"
            " tushirildi.</b>"
        ),
        "not_loaded": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> Modul emas"
            " tushirildi.</b>"
        ),
        "requirements_failed": (
            "<emoji document_id=5375201396859607943>🚫</emoji><b> O'rnatish amalga"
            " oshmadi bog'liqliklar</b>"
        ),
        "requirements_failed_termux": (
            "<emoji document_id=5386399931378440814>🕶</emoji> <b>O'rnatish amalga"
            " oshmadi bog'liqliklar</b>\n<b>Ko'pincha Termux bo'lmagani uchun paydo"
            " bo'ladiko'p kutubxonalarni qo'llab-quvvatlaydi. Buni xato deb xabar"
            " qilmang, bu tuzatib bo'lmaydi.</b>"
        ),
        "requirements_installing": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> O'rnatilmoqda"
            " bog'liqliklar:\n\n{}</b>"
        ),
        "requirements_restart": (
            "<emoji document_id=5445284980978621387>🚀</emoji><b> Bog'liqlar o'rnatildi,"
            " lekin qo'llash uchun qayta ishga tushirish kerak </b><code>{}</code>"
        ),
        "all_modules_deleted": (
            "<emoji document_id=6323332130579416910>✅</emoji><b> Modullar olib"
            " tashlandi</b>"
        ),
        "single_cmd": "\n▫️ <code>{}{}</code> {}",
        "undoc_cmd": "🦥 Tavsif yo'q",
        "ihandler": "\n🎹 <code>{}</code> {}",
        "undoc_ihandler": "🦥 Tavsif yo'q",
        "version_incompatible": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulgaHikka"
            " versiyasini {}+\n</b><code>.update</code> bilan yangilashni talab qiladi"
        ),
        "ffmpeg_required": (
            "<emoji document_id=5454225457916420314>😖</emoji> <b>Ushbu modulga"
            "o'rnatilmagan FFMPEG talab qiladi</b>"
        ),
        "developer": (
            "\n\n<emoji document_id=5431376038628171216>👨‍💻</emoji> <b>Ishlab"
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
            "\n🚸 <b>Modullarni yuklash uchun `blob` havolalaridan foydalanmang. Bu"
            " yerdan yuklagan ma`qul.`xom`</b>"
        ),
        "raw_link": (
            "\n<emoji document_id=6037284117505116849>🌐</emoji> <b>Havola:"
            "</b><code>{}</code>"
        ),
        "suggest_subscribe": (
            "\n\n<emoji document_id=5456129670321806826>⭐️</emoji><b>Ushbu modul {}"
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
            " o'rnatilgan modulni yuklash"
            " </b><code>{}</code><b></b>\n\n<emojidocument_id=5472146462362048818>💡</emoji><i>"
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
            " </b><code>{}</code><b> kanaliga qo'shilish uchun ruxsat so'ramoqda <a"
            ' href="https://t.me/{}">{}</a>.\n\n<b><emoji'
            ' document_id="5467666648263564704">❓</emoji> Sabab:'
            ' {}</b>\n\n<i><a href="https://t.me/{}">tasdiqlash</a> kutilmoqda...</i>'
        ),
    }

    _fully_loaded = False
    _links_cache = {}

    def __init__(self):
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

    async def client_ready(self):
        self.allmodules.add_aliases(self.lookup("settings").get("aliases", {}))

        main.hikka.ready.set()

        asyncio.ensure_future(self._update_modules())
        asyncio.ensure_future(self.get_repo_list("full"))
        self._react_queue = []

    @loader.loop(interval=120, autostart=True)
    async def _react_processor(self):
        if not self._react_queue:
            return

        developer_entity, modname = self._react_queue.pop(0)
        try:
            await (
                await self._client.get_messages(
                    developer_entity, limit=1, search=modname
                )
            )[0].react("❤️")
            self.set(
                "reacted",
                self.get("reacted", []) + [f"{developer_entity.id}/{modname}"],
            )
        except Exception:
            logger.debug("Unable to react to %s about %s", developer_entity.id, modname)

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
                self._db.setdefault(mod.__class__.__name__, {}).setdefault(
                    "__config__", {}
                )[option] = config.value

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
                self._db.setdefault(lib.__class__.__name__, {}).setdefault(
                    "__config__", {}
                )[option] = config.value

        self._db.save()

    def _update_modules_in_db(self):
        if self.allmodules.secure_boot:
            return

        self.set(
            "loaded_modules",
            {
                module.__class__.__name__: module.__origin__
                for module in self.allmodules.modules
                if module.__origin__.startswith("http")
            },
        )

    @loader.owner
    @loader.command(ru_doc="Загрузить модуль из официального репозитория")
    async def dlmod(self, message: Message):
        """Install a module from the official module repo"""
        if args := utils.get_args(message):
            args = args[0]

            await self.download_and_install(args, message)
            if self._fully_loaded:
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
    @loader.command(ru_doc="Установить пресет модулей")
    async def dlpreset(self, message: Message):
        """Set modules preset"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("select_preset"))
            return

        await self.get_repo_list(args[0])
        self.set("chosen_preset", args[0])

        await utils.answer(message, self.strings("preset_loaded"))
        await self.allmodules.commands["restart"](
            await message.reply(f"{self.get_prefix()}restart --force")
        )

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

    async def get_links_list(self):
        def converter(repo_dict: dict) -> list:
            return list(dict(ChainMap(*list(repo_dict.values()))).values())

        links = await self.get_repo_list("full")
        # Make `MODULES_REPO` primary one
        main_repo = list(links[self.config["MODULES_REPO"]].values())
        del links[self.config["MODULES_REPO"]]
        return main_repo + converter(links)

    async def _find_link(self, module_name: str) -> typing.Union[str, bool]:
        links = await self.get_links_list()
        return next(
            (
                link
                for link in links
                if link.lower().endswith(f"/{module_name.lower()}.py")
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
    @loader.command(ru_doc="Загрузить модуль из файла")
    async def loadmod(self, message: Message):
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

    async def _send_stats(self, url: str, retry: bool = False):
        """Send anonymous stats to Hikka"""
        try:
            if not self.get("token"):
                self.set(
                    "token",
                    (
                        await (await self._client.get_messages("@hikka_ub", ids=[10]))[
                            0
                        ].click(0)
                    ).message,
                )

            res = await utils.run_sync(
                requests.post,
                "https://heta.hikariatama.ru/stats",
                data={"url": url},
                headers={"X-Hikka-Token": self.get("token")},
            )

            if res.status_code == 403:
                if retry:
                    return

                self.set("token", None)
                return await self._send_stats(url, retry=True)
        except Exception:
            logger.debug("Failed to send stats", exc_info=True)

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
            ver = re.search(r"# ?scope: ?hikka_min ((\d+\.){2}\d+)", doc).group(1)
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

        try:
            try:
                spec = ModuleSpec(
                    module_name,
                    loader.StringLoader(
                        doc, f"<string {uid}>" if origin == "<string>" else origin
                    ),
                    origin=f"<string {uid}>" if origin == "<string>" else origin,
                )
                instance = await self.allmodules.register_module(
                    spec,
                    module_name,
                    origin,
                    save_fs=save_fs,
                )
            except ImportError as e:
                logger.info(
                    "Module loading failed, attemping dependency installation (%s)",
                    e.name,
                )
                # Let's try to reinstall dependencies
                try:
                    requirements = list(
                        filter(
                            lambda x: not x.startswith(("-", "_", ".")),
                            map(
                                str.strip,
                                loader.VALID_PIP_PACKAGES.search(doc)[1].split(),
                            ),
                        )
                    )
                except TypeError:
                    logger.warning(
                        "No valid pip packages specified in code, attemping"
                        " installation from error"
                    )
                    requirements = [e.name]

                logger.debug("Installing requirements: %s", requirements)

                if not requirements:
                    raise Exception("Nothing to install") from e

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
                            "\n".join(f"▫️ {req}" for req in requirements)
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
                    await self.allmodules.unload_module(instance.__class__.__name__)

                with contextlib.suppress(Exception):
                    self.allmodules.modules.remove(instance)

                if message:
                    await utils.answer(
                        message,
                        "<emoji document_id=5454225457916420314>😖</emoji>"
                        f" <b>{utils.escape_html(str(e))}</b>",
                    )
                return
        except BaseException as e:
            logger.exception("Loading external module failed due to %s", e)

            if message is not None:
                await utils.answer(message, self.strings("load_failed"))

            return

        instance.inline = self.inline

        if hasattr(instance, "__version__") and isinstance(instance.__version__, tuple):
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
                    await self.allmodules.unload_module(instance.__class__.__name__)

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
                logging.debug(f"Unloading {instance}, because it raised `SelfUnload`")
                with contextlib.suppress(Exception):
                    await self.allmodules.unload_module(instance.__class__.__name__)

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
                logging.debug(f"Suspending {instance}, because it raised `SelfSuspend`")
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
                and self._db.get(main.__name__, "stats", True)
                and url is not None
                and utils.check_url(url)
            ):
                await self._send_stats(url)

        for alias, cmd in self.lookup("settings").get("aliases", {}).items():
            if cmd in instance.commands:
                self.allmodules.add_alias(alias, cmd)

        try:
            modname = instance.strings("name")
        except KeyError:
            modname = getattr(instance, "name", "ERROR")

        try:
            if developer in self._client._hikka_entity_cache and getattr(
                await self._client.get_entity(developer), "left", True
            ):
                developer_entity = await self._client.force_get_entity(developer)
            else:
                developer_entity = await self._client.get_entity(developer)
        except Exception:
            developer_entity = None

        if not isinstance(developer_entity, Channel):
            developer_entity = None

        if (
            developer_entity is not None
            and f"{developer_entity.id}/{modname}" not in self.get("reacted", [])
        ):
            self._react_queue += [(developer_entity, modname)]

        if message is None:
            return

        modhelp = ""

        if instance.__doc__:
            modhelp += f"<i>\nℹ️ {utils.escape_html(inspect.getdoc(instance))}</i>\n"

        subscribe = ""
        subscribe_markup = None

        depends_from = []
        for key in dir(instance):
            value = getattr(instance, key)
            if isinstance(value, loader.Library):
                depends_from.append(
                    "▫️ <code>{}</code><b> {} </b><code>{}</code>".format(
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
            await utils.answer(message, loaded_msg(), reply_markup=subscribe_markup)
        except telethon.errors.rpcerrorlist.MediaCaptionTooLongError:
            await message.reply(loaded_msg(False))

    async def _inline__subscribe(
        self,
        call: InlineCall,
        entity: int,
        msg: callable,
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
    @loader.command(ru_doc="Выгрузить модуль")
    async def unloadmod(self, message: Message):
        """Unload module by class name"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("no_class"))
            return

        instance = self.lookup(args)

        if issubclass(instance.__class__, loader.Library):
            await utils.answer(message, self.strings("cannot_unload_lib"))
            return

        try:
            worked = await self.allmodules.unload_module(args)
        except CoreUnloadError as e:
            await utils.answer(message, self.strings("unload_core").format(e.module))
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
                ", ".join(
                    [(mod[:-3] if mod.endswith("Mod") else mod) for mod in worked]
                )
            )
            if worked
            else self.strings("not_unloaded")
        )

        await utils.answer(message, msg)

    @loader.owner
    @loader.command(ru_doc="Удалить все модули")
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

    async def _inline__clearmodules(self, call: InlineCall):
        self.set("loaded_modules", {})

        for file in os.scandir(loader.LOADED_MODULES_DIR):
            os.remove(file)

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

            self._update_modules_in_db()

            aliases = {
                alias: cmd
                for alias, cmd in self.lookup("settings").get("aliases", {}).items()
                if self.allmodules.add_alias(alias, cmd)
            }

            self.lookup("settings").set("aliases", aliases)

        self._fully_loaded = True

        with contextlib.suppress(AttributeError):
            await self.lookup("Updater").full_restart_complete(self._secure_boot)

    async def reload_core(self) -> int:
        """Forcefully reload all core modules"""
        self._fully_loaded = False

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

        self._fully_loaded = True
        return len(loaded)
