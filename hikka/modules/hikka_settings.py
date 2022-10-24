#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import atexit
import random
import sys
import os

import telethon
from telethon.tl.types import Message
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.utils import get_display_name

from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

ALL_INVOKES = [
    "clear_entity_cache",
    "clear_fulluser_cache",
    "clear_fullchannel_cache",
    "clear_perms_cache",
    "clear_cache",
    "reload_core",
    "inspect_cache",
    "inspect_modules",
]


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )


@loader.tds
class HikkaSettingsMod(loader.Module):
    """Advanced settings for Hikka Userbot"""

    strings = {
        "name": "HikkaSettings",
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Watchers:</b>\n\n<b>{}</b>"
        ),
        "no_args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>No arguments"
            " specified</b>"
        ),
        "invoke404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Internal debug method"
            " </b><code>{}</code><b> not found, ergo can't be invoked</b>"
        ),
        "module404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Module</b>"
            " <code>{}</code> <b>not found</b>"
        ),
        "invoke": (
            "<emoji document_id=5215519585150706301>👍</emoji> <b>Invoked internal debug"
            " method </b><code>{}</code>\n\n<emoji"
            " document_id=5784891605601225888>🔵</emoji> <b>Result:\n{}</b>"
        ),
        "invoking": (
            "<emoji document_id=5213452215527677338>⏳</emoji> <b>Invoking internal"
            " debug method </b><code>{}</code><b> of </b><code>{}</code><b>...</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Watcher {} not"
            " found</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Watcher {} is now"
            " <u>disabled</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Watcher {} is now"
            " <u>enabled</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>You need to specify"
            " watcher name</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick for this user"
            " is now {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Please, specify"
            " command to toggle NoNick for</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick for"
            " </b><code>{}</code><b> is now {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Command not found</b>"
        ),
        "inline_settings": "⚙️ <b>Here you can configure your Hikka settings</b>",
        "confirm_update": (
            "🧭 <b>Please, confirm that you want to update. Your userbot will be"
            " restarted</b>"
        ),
        "confirm_restart": "🔄 <b>Please, confirm that you want to restart</b>",
        "suggest_fs": "✅ Suggest FS for modules",
        "do_not_suggest_fs": "🚫 Suggest FS for modules",
        "use_fs": "✅ Always use FS for modules",
        "do_not_use_fs": "🚫 Always use FS for modules",
        "btn_restart": "🔄 Restart",
        "btn_update": "🧭 Update",
        "close_menu": "😌 Close menu",
        "custom_emojis": "✅ Custom emojis",
        "no_custom_emojis": "🚫 Custom emojis",
        "suggest_subscribe": "✅ Suggest subscribe to channel",
        "do_not_suggest_subscribe": "🚫 Suggest subscribe to channel",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>This command must be"
            " executed in chat</b>"
        ),
        "nonick_warning": (
            "Warning! You enabled NoNick with default prefix! "
            "You may get muted in Hikka chats. Change prefix or "
            "disable NoNick!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Reply to a message"
            " of user, which needs to be added to NoNick</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>This action will fully remove Hikka from this account and can't be"
            " reverted!</b>\n\n<i>- Hikka chats will be removed\n- Session will be"
            " terminated and removed\n- Hikka inline bot will be removed</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>Are you really sure you want to delete Hikka?</b>"
        ),
        "deauth_yes": "I'm sure",
        "deauth_no_1": "I'm not sure",
        "deauth_no_2": "I'm uncertain",
        "deauth_no_3": "I'm struggling to answer",
        "deauth_cancel": "🚫 Cancel",
        "deauth_confirm_btn": "😢 Delete",
        "uninstall": "😢 <b>Uninstalling Hikka...</b>",
        "uninstalled": (
            "😢 <b>Hikka uninstalled. Web interface is still active, you can add another"
            " account</b>"
        ),
        "logs_cleared": "🗑 <b>Logs cleared</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick is enabled"
            " for these commands:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick is enabled"
            " for these users:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick is enabled"
            " for these chats:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Nothing to"
            " show...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>This command gives access to your Hikka web interface. It's not"
            " recommended to run it in public group chats. Consider using it in <a"
            " href='tg://openmessage?user_id={}'>Saved messages</a>. Type"
            " </b><code>{}proxypass force_insecure</code><b> to ignore this warning</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>This command gives access to your Hikka web interface. It's not"
            " recommended to run it in public group chats. Consider using it in <a"
            " href='tg://openmessage?user_id={}'>Saved messages</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Opening tunnel to Hikka web interface...</b>",
        "tunnel_opened": "🎉 <b>Tunnel opened. This link is valid for about 1 hour</b>",
        "web_btn": "🌍 Web interface",
        "btn_yes": "🚸 Open anyway",
        "btn_no": "🔻 Cancel",
        "lavhost_web": (
            "✌️ <b>This link leads to your Hikka web interface on lavHost</b>\n\n<i>💡"
            " You'll need to authorize using lavHost credentials, specified on"
            " registration</i>"
        ),
        "disable_stats": "✅ Anonymous stats allowed",
        "enable_stats": "🚫 Anonymous stats disabled",
    }

    strings_ru = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Смотрители:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Смотритель {} не"
            " найден</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Смотритель {} теперь"
            " <u>выключен</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Смотритель {} теперь"
            " <u>включен</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Укажи имя"
            " смотрителя</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Состояние NoNick для"
            " этого пользователя: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Укажи команду, для"
            " которой надо включить\\выключить NoNick</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Состояние NoNick для"
            " </b><code>{}</code><b>: {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Команда не найдена</b>"
        ),
        "inline_settings": "⚙️ <b>Здесь можно управлять настройками Hikka</b>",
        "confirm_update": "🧭 <b>Подтвердите обновление. Юзербот будет перезагружен</b>",
        "confirm_restart": "🔄 <b>Подтвердите перезагрузку</b>",
        "suggest_fs": "✅ Предлагать сохранение модулей",
        "do_not_suggest_fs": "🚫 Предлагать сохранение модулей",
        "use_fs": "✅ Всегда сохранять модули",
        "do_not_use_fs": "🚫 Всегда сохранять модули",
        "btn_restart": "🔄 Перезагрузка",
        "btn_update": "🧭 Обновление",
        "close_menu": "😌 Закрыть меню",
        "custom_emojis": "✅ Кастомные эмодзи",
        "no_custom_emojis": "🚫 Кастомные эмодзи",
        "suggest_subscribe": "✅ Предлагать подписку на канал",
        "do_not_suggest_subscribe": "🚫 Предлагать подписку на канал",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Эту команду нужно"
            " выполнять в чате</b>"
        ),
        "_cls_doc": "Дополнительные настройки Hikka",
        "nonick_warning": (
            "Внимание! Ты включил NoNick со стандартным префиксом! "
            "Тебя могут замьютить в чатах Hikka. Измени префикс или "
            "отключи глобальный NoNick!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Ответь на сообщение"
            " пользователя, для которого нужно включить NoNick</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>Это действие полностью удалит Hikka с этого аккаунта! Его нельзя"
            " отменить</b>\n\n<i>- Все чаты, связанные с Hikka будут удалены\n- Сессия"
            " Hikka будет сброшена\n- Инлайн бот Hikka будет удален</i>"
        ),
        "deauth_confirm_step2": "⚠️ <b>Ты точно уверен, что хочешь удалить Hikka?</b>",
        "deauth_yes": "Я уверен",
        "deauth_no_1": "Я не уверен",
        "deauth_no_2": "Не точно",
        "deauth_no_3": "Нет",
        "deauth_cancel": "🚫 Отмена",
        "deauth_confirm_btn": "😢 Удалить",
        "uninstall": "😢 <b>Удаляю Hikka...</b>",
        "uninstalled": (
            "😢 <b>Hikka удалена. Веб-интерфейс все еще активен, можно добавить другие"
            " аккаунты!</b>"
        ),
        "logs_cleared": "🗑 <b>Логи очищены</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick включен для"
            " этих команд:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick включен для"
            " этих пользователей:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick включен для"
            " этих чатов:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Нечего"
            " показывать...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>Эта команда дает доступ к веб-интерфейсу Hikka. Ее выполнение в"
            " публичных чатах является угрозой безопасности. Предпочтительно выполнять"
            " ее в <a href='tg://openmessage?user_id={}'>Избранных сообщениях</a>."
            " Выполни </b><code>{}proxypass force_insecure</code><b> чтобы отключить"
            " это предупреждение</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>Эта команда дает доступ к веб-интерфейсу Hikka. Ее выполнение в"
            " публичных чатах является угрозой безопасности. Предпочтительно выполнять"
            " ее в <a href='tg://openmessage?user_id={}'>Избранных сообщениях</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Открываю тоннель к веб-интерфейсу Hikka...</b>",
        "tunnel_opened": (
            "🎉 <b>Тоннель открыт. Эта ссылка будет активна не более часа</b>"
        ),
        "web_btn": "🌍 Веб-интерфейс",
        "btn_yes": "🚸 Все равно открыть",
        "btn_no": "🔻 Закрыть",
        "lavhost_web": (
            "✌️ <b>По этой ссылке ты попадешь в веб-интерфейс Hikka на"
            " lavHost</b>\n\n<i>💡 Тебе нужно будет авторизоваться, используя данные,"
            " указанные при настройке lavHost</i>"
        ),
        "disable_stats": "✅ Анонимная стата разрешена",
        "enable_stats": "🚫 Анонимная стата запрещена",
    }

    strings_de = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Beobachter:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Beobachter {} nicht"
            "gefunden</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Watcher {} ist jetzt"
            " <u>aus</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Watcher {} ist jetzt"
            " <u>aktiviert</u></b>"
        ),
        "arg": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Bitte geben Sie einen"
            " Namen einHausmeister</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick-Status für"
            " dieser Benutzer: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Geben Sie einen Befehl"
            " anwas NoNick aktivieren/\\deaktivieren sollte</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick-Status für"
            " </b><code>{}</code><b>: {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Befehl nicht"
            " gefunden</b>"
        ),
        "inline_settings": (
            "⚙️ <b>Hier können Sie Ihre Hikka-Einstellungen verwalten</b>"
        ),
        "confirm_update": (
            "🧭 <b>Bestätige das Update. Der Userbot wird neu gestartet</b>"
        ),
        "confirm_restart": "🔄 <b>Neustart bestätigen</b>",
        "suggest_fs": "✅ Speichermodule vorschlagen",
        "do_not_suggest_fs": "🚫 Speichermodule vorschlagen",
        "use_fs": "✅ Module immer speichern",
        "do_not_use_fs": "🚫 Module immer speichern",
        "btn_restart": "🔄 Neustart",
        "btn_update": "🧭 Aktualisieren",
        "close_menu": "😌 Menü schließen",
        "custom_emojis": "✅ Benutzerdefinierte Emojis",
        "no_custom_emojis": "🚫 Benutzerdefinierte Emojis",
        "suggest_subscribe": "✅ Kanalabonnement vorschlagen",
        "do_not_suggest_subscribe": "🚫 Kanalabonnement vorschlagen",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Dieser Befehl benötigt"
            "im Chat ausführen</b>"
        ),
        "_cls_doc": "Erweiterte Hikka-Einstellungen",
        "nonick_warning": (
            "Achtung! Sie haben NoNick mit dem Standard-Präfix eingefügt!Sie sind"
            " möglicherweise in Hikka-Chats stummgeschaltet. Ändern Sie das Präfix oder"
            " schalten Sie das globale NoNick aus!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Auf Nachricht"
            " antwortenBenutzer soll NoNick aktivieren</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>Diese Aktion wird Hikka vollständig von diesem Konto entfernen! Er"
            " kann nichtAbbrechen</b>\n\n<i>- Alle Hikka-bezogenen Chats werden"
            " gelöscht\n- SitzungHikka wird zurückgesetzt\n- Hikkas Inline-Bot wird"
            " gelöscht</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>Sind Sie sicher, dass Sie Hikka deinstallieren möchten?</b>"
        ),
        "deauth_yes": "Ich bin sicher",
        "deauth_no_1": "Ich bin mir nicht sicher",
        "deauth_no_2": "Nicht sicher",
        "deauth_no_3": "Nein",
        "deauth_cancel": "🚫 Abbrechen",
        "deauth_confirm_btn": "😢 Löschen",
        "uninstall": "😢 <b>Hikka wird deinstalliert...</b>",
        "uninstalled": (
            "😢 <b>Hikka wurde entfernt. Die Weboberfläche ist noch aktiv, andere können"
            " hinzugefügt werdenKonten!</b>"
        ),
        "logs_cleared": "🗑 <b>Protokolle gelöscht</b>",
        "cmd_nn_liste": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick aktiviert für"
            " diese Befehle:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick aktiviert für"
            " diese Benutzer:</b>\n\n{}"
        ),
        "chat_nn_liste": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick aktiviert für"
            " diese Chats:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Nichtszeigen...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>Dieser Befehl ermöglicht den Zugriff auf die Hikka-Weboberfläche."
            " Seine Ausführung inÖffentliche Chats sind ein Sicherheitsrisiko. Am"
            " besten durchführen es in <a href='tg://openmessage?user_id={}'>Empfohlene"
            " Nachrichten</a>.Führen Sie </b><code>{}proxypass force_insecure</code><b>"
            " zum Deaktivieren ausDies ist eine Warnung</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>Dieser Befehl ermöglicht den Zugriff auf die Hikka-Weboberfläche."
            " Seine Ausführung inÖffentliche Chats sind ein Sicherheitsrisiko. Am"
            " besten durchführen sie in <a"
            " href='tg://openmessage?user_id={}'>Empfohlene Nachrichten</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Öffne einen Tunnel zur Hikka-Weboberfläche...</b>",
        "tunnel_opened": (
            "🎉 <b>Der Tunnel ist offen. Dieser Link ist nicht länger als eine Stunde"
            " aktiv</b>"
        ),
        "web_btn": "🌍 Webinterface",
        "btn_yes": "🚸 Trotzdem geöffnet",
        "btn_no": "🔻Schließen",
        "lavhost_web": (
            "✌️ <b>Dieser Link führt Sie zur Hikka-Weboberfläche auf"
            " lavHost</b>\n\n<i>💡 Sie müssen sich mit Ihren Zugangsdaten anmelden,"
            "beim Setzen von lavHost angegeben</i>"
        ),
        "disable_stats": "✅ Anonyme Statistiken sind erlaubt",
        "enable_stats": "🚫 Anonyme Statistiken deaktiviert",
    }

    strings_tr = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>İzleyiciler:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>İzleyici {} değil"
            " bulundu</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>İzleyici {} şimdi"
            " <u>kapalı</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>İzleyici {} şimdi"
            " <u>etkin</u></b>"
        ),
        "arg": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Lütfen bir ad girin"
            "bekçi</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick durumu için"
            " bu kullanıcı: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Bir komut belirtin"
            "hangisi NoNick'i etkinleştirmeli/\\devre dışı bırakmalıdır</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick durumu için"
            " </b><code>{}</code><b>: {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Komut bulunamadı</b>"
        ),
        "inline_settings": "⚙️ <b>Buradan Hikka ayarlarınızı yönetebilirsiniz</b>",
        "confirm_update": (
            "🧭 <b>Güncellemeyi onaylayın. Kullanıcı robotu yeniden başlatılacak</b>"
        ),
        "confirm_restart": "🔄 <b>Yeniden başlatmayı onayla</b>",
        "suggest_fs": "✅ Kaydetme modülleri öner",
        "do_not_suggest_fs": "🚫 Modüllerin kaydedilmesini öner",
        "use_fs": "✅ Modülleri her zaman kaydet",
        "do_not_use_fs": "🚫 Modülleri her zaman kaydet",
        "btn_restart": "🔄 Yeniden Başlat",
        "btn_update": "🧭 Güncelle",
        "close_menu": "😌 Menüyü kapat",
        "custom_emojis": "✅ Özel emojiler",
        "no_custom_emojis": "🚫 Özel Emojiler",
        "suggest_subscribe": "✅ Kanal aboneliği öner",
        "do_not_suggest_subscribe": "🚫 Kanal aboneliği öner",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Bu komut gerekiyor"
            " sohbette yürüt</b>"
        ),
        "_cls_doc": "Gelişmiş Hikka Ayarları",
        "nonick_warning": (
            "Dikkat! NoNick'i standart önekle eklediniz!"
            "Hikka sohbetlerinde sesiniz kapatılmış olabilir. Ön eki değiştirin veya "
            "küresel NoNick'i kapatın!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Mesajı yanıtla"
            "NoNick'i etkinleştirmek için kullanıcı</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>Bu işlem Hikka'yı bu hesaptan tamamen kaldıracak! Yapamaz"
            "iptal</b>\n\n<i>- Hikka ile ilgili tüm sohbetler silinecek\n- Oturum"
            " Hikka sıfırlanacak\n- Hikka'nın satır içi botu silinecek</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>Hikka'yı kaldırmak istediğinizden emin misiniz?</b>"
        ),
        "deauth_yes": "Eminim",
        "deauth_no_1": "Emin değilim",
        "deauth_no_2": "Emin değilim",
        "deauth_no_3": "Hayır",
        "deauth_cancel": "🚫 İptal",
        "deauth_confirm_btn": "😢 Sil",
        "uninstall": "😢 <b>Hikka'yı Kaldırılıyor...</b>",
        "uninstalled": (
            "😢 <b>Hikka kaldırıldı. Web arayüzü hala aktif, başkaları eklenebilir"
            "hesaplar!</b>"
        ),
        "logs_cleared": "🗑 <b>Günlükler temizlendi</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick için"
            " etkinleştirildi bu komutlar:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick için"
            " etkinleştirildi bu kullanıcılar:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick için"
            " etkinleştirildi bu sohbetler:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Hiçbir şey"
            "göster...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>Bu komut, Hikka web arayüzüne erişim sağlar. YürütülmesiGenel"
            " sohbetler bir güvenlik riskidir. Tercihen gerçekleştirin <a"
            " href='tg://openmessage?user_id={}'>Öne Çıkan Mesajlar</a> içinde.Devre"
            " dışı bırakmak için </b><code>{}proxypass force_insecure</code><b>"
            " çalıştırınbu bir uyarıdır</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>Bu komut, Hikka web arayüzüne erişim sağlar. Yürütülmesi"
            "Genel sohbetler bir güvenlik riskidir. Tercihen gerçekleştirin"
            " onu <a href='tg://openmessage?user_id={}'>Öne Çıkan Mesajlar</a>'da.</b>"
        ),
    }

    strings_uz = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Kuzatuvchilar:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Kuzuvchi {} emas"
            " topildi</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Kuzatuvchi {} hozir"
            " <u>o'chirilgan</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>Kuzatuvchi {} hozir"
            " <u>yoqilgan</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Iltimos, nom kiriting"
            "qorovul</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick holati uchun"
            " bu foydalanuvchi: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Buyruqni belgilang"
            "bu NoNick</b>ni yoqish/o'chirish kerak"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick holati uchun"
            " </b><code>{}</code><b>: {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Buyruq topilmadi</b>"
        ),
        "inline_settings": (
            "⚙️ <b>Bu yerda siz Hikka sozlamalaringizni boshqarishingiz mumkin</b>"
        ),
        "confirm_update": (
            "🧭 <b>Yangilanishni tasdiqlang. Userbot qayta ishga tushiriladi</b>"
        ),
        "confirm_restart": "🔄 <b>Qayta ishga tushirishni tasdiqlang</b>",
        "suggest_fs": "✅ Modullarni saqlashni taklif qilish",
        "do_not_suggest_fs": "🚫 Modullarni saqlashni taklif qilish",
        "use_fs": "✅ Modullarni doimo saqlash",
        "do_not_use_fs": "🚫 Har doim modullarni saqlang",
        "btn_restart": "🔄 Qayta ishga tushirish",
        "btn_update": "🧭 Yangilash",
        "close_menu": "😌 Menyuni yopish",
        "custom_emojis": "✅ Maxsus emojilar",
        "no_custom_emojis": "🚫 Maxsus kulgichlar",
        "suggest_subscribe": "✅ Kanalga obuna bo'lishni taklif qilish",
        "do_not_suggest_subscribe": "🚫 Kanalga obuna bo'lishni taklif qilish",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Bu buyruq kerak"
            " chatda bajarish</b>"
        ),
        "_cls_doc": "Kengaytirilgan Hikka sozlamalari",
        "nonick_warning": (
            "Diqqat! NoNickni standart prefiks bilan kiritdingiz!Hikka chatlarida"
            " ovozingiz o'chirilgan bo'lishi mumkin. Prefiksni o'zgartiring yoki global"
            " NoNickni o'chiring!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Xatga javob berish"
            "foydalanuvchi NoNick</b>ni yoqish uchun"
        ),
        "deauth_confirm": (
            "⚠️ <b>Bu amal Hikkani ushbu hisobdan butunlay olib tashlaydi! U qila"
            " olmaydiBekor qilish</b>\n\n<i>- Hikka bilan bog'liq barcha chatlar"
            " o'chiriladi\n- Sessiya Hikka qayta tiklanadi\n- Hikkaning ichki boti"
            " o'chiriladi</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>Haqiqatan ham Hikkani oʻchirib tashlamoqchimisiz?</b>"
        ),
        "deauth_yes": "Ishonchim komil",
        "deauth_no_1": "Imonim yo'q",
        "deauth_no_2": "Ishonasiz",
        "deauth_no_3": "Yo'q",
        "deauth_cancel": "🚫 Bekor qilish",
        "deauth_confirm_btn": "😢 O'chirish",
        "uninstall": "😢 <b>Hikka o'chirilmoqda...</b>",
        "uninstalled": (
            "😢 <b>Hikka oʻchirildi. Veb-interfeys hali ham faol, boshqalarni qoʻshish"
            " mumkinhisoblar!</b>"
        ),
        "logs_cleared": "🗑 <b>Jurnallar tozalandi</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick yoqilgan"
            " bu buyruqlar:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick yoqilgan"
            " bu foydalanuvchilar:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick yoqilgan"
            " bu chatlar:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷‍♀️</emoji> <b>Hech narsa"
            "ko'rsatish...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>Ushbu buyruq Hikka veb-interfeysiga kirish imkonini beradi. Uning"
            " bajarilishiOmmaviy chatlar xavfsizlikka xavf tug'diradi. Afzal bajaring"
            " Bu <a href='tg://openmessage?user_id={}'>Taniqli xabarlar</a>da.O'chirish"
            " uchun </b><code>{}proxypass force_insecure</code><b>ni ishga tushiring bu"
            " ogohlantirish</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>Ushbu buyruq Hikka veb-interfeysiga kirish imkonini beradi. Uning"
            " bajarilishiOmmaviy chatlar xavfsizlikka xavf tug'diradi. Afzal bajaring u"
            " <a href='tg://openmessage?user_id={}'>Mazkur xabarlarda</a>.</b>"
        ),
        "opening_tunnel": "🔁 <b>Hikka veb-interfeysiga tunnel ochilmoqda...</b>",
        "tunnel_opened": (
            "🎉 <b>Tunnel ochiq. Bu havola bir soatdan ko'p bo'lmagan vaqt davomida faol"
            " bo'ladi</b>"
        ),
        "web_btn": "🌍 Veb interfeysi",
        "btn_yes": "🚸 Baribir ochiq",
        "btn_no": "🔻 Yopish",
        "lavhost_web": (
            "✌️ <b>Ushbu havola sizni Hikka veb-interfeysiga olib boradi"
            " lavHost</b>\n\n<i>💡 Hisob ma'lumotlaringizdan foydalanib tizimga"
            " kirishingiz kerak,lavHost</i>ni sozlashda ko'rsatilgan"
        ),
        "disable_stats": "✅ Anonim statistika ruxsat berildi",
        "enable_stats": "🚫 Anonim statistika o'chirilgan",
    }

    strings_ja = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>視聴者:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>非閲覧者{}見つかりました</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>ウォッチャー {} は現在"
            "<u>オフ</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>ウォッチャー {} は現在"
            "<u>有効</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>名前を入力してください世話人</b>"
        ),
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> のニックネームはありません <b>"
            "このユーザーではありません: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>コマンド"
            " NoNick を有効/\\無効にするユーザーを指定</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> のニックネームはありません <b>"
            " </b><code>{}</code><b>: {}</b> ではありません"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>コマンドが見つかりません</b>"
        ),
        "inline_settings": "⚙️ <b>ここで Hikka の設定を管理できます</b>",
        "confirm_update": "🧭 <b>更新を確認します。ユーザーボットが再起動します</b>",
        "confirm_restart": "🔄 <b>再起動を確認</b>",
        "suggest_fs": " モジュールの保存を提案する",
        "do_not_suggest_fs": "🚫 保存モジュールの提案",
        "use_fs": "✅ 常にモジュールを保存",
        "do_not_use_fs": "🚫 常にモジュールを保存",
        "btn_restart": "再起動",
        "btn_update": "🧭更新",
        "close_menu": "メニューを閉じる",
        "custom_emojis": "✅ カスタム絵文字",
        "no_custom_emojis": "🚫カスタム絵文字",
        "suggest_subscribe": " チャンネル登録を提案する",
        "do_not_suggest_subscribe": " チャンネル登録を提案する",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>このコマンドが必要ですチャットで実行</b>"
        ),
        "_cls_doc": "ヒッカの詳細設定",
        "nonick_warning": (
            "注意! 標準のプレフィックスに NoNick が含まれています!"
            "Hikka Chat でミュートすることができます。プレフィックスを変更するか, "
            "グローバル NoNick をオフにします!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>メッセージに返信"
            "ユーザーは NoNick を有効にします</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>このアクションにより, このアカウントから Hikka が完全に削除されます! 彼は削除できません"
            "キャンセル</b>\n\n<i>- Hikka に関連するすべてのチャットが削除されます\n- セッション"
            "ヒッカはリセットされます\n- ヒッカのインライン ボットは削除されます</i>"
        ),
        "deauth_confirm_step2": "⚠️ <b>Hikka をアンインストールしてもよろしいですか?</b>",
        "deauth_yes": "確かに",
        "deauth_no_1": "わからない",
        "deauth_no_2": "わかりません",
        "deauth_no_3": "いいえ",
        "deauth_cancel": "🚫キャンセル",
        "deauth_confirm_btn": "😢削除",
        "uninstall": "😢 <b>Hikka をアンインストールしています...</b>",
        "uninstalled": (
            "😢 <b>Hikka' は廃止されました。Web インターフェースはまだアクティブです。その他アカウントを追加できます!</b>"
        ),
        "logs_cleared": "🗑 <b>ログを消去</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>これには NoNick が有効になっています"
            " これらのコマンド:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>これには NoNick が有効になっています"
            "このユーザー:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>これには NoNick が有効になっています"
            "このチャット:</b>\n\n{}"
        ),
        "nothing": "<emoji document_id=5427052514094619126>🤷️</emoji> <b>なし表示...</b>",
        "privacy_leak": (
            "⚠️ <b>このコマンドは, Hikka Web インターフェイスへのアクセスを提供します。その実行"
            "公開チャットはセキュリティ上のリスクです。できれば実行してください"
            "<a href='tg://openmessage?user_id={}'>選択したメッセージ</a>にあります。"
            "</b><code>{}proxypass force_insecure</code><b> を実行して無効にします"
            "これは警告です</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>このコマンドは, Hikka Web インターフェイスへのアクセスを提供します。その実行"
            "公開チャットはセキュリティ上のリスクです。できれば実行してください"
            " <a href='tg://openmessage?user_id={}'>メッセージを選択</a>インチ</b>"
        ),
        "opening_tunnel": "🔁 <b>Hikka ウェブ インターフェースへのトンネルを開いています...</b>",
        "tunnel_opened": "🎉 <b>トンネルが開いています。このリンクは 1 時間以上アクティブになりません</b",
        "web_btn": "🌍ウェブインターフェース",
        "btn_yes": "とにかく開く",
        "btn_no": "閉じる",
        "lavhost_web": (
            "✌️ <b>このリンクをクリックすると, Hikka Web インターフェイス lvHost に移動します</b>\n\n<i>💡"
            "lavHost をセットアップするときは, 資格情報を使用してログインする必要があります"
            "指定</i>"
        ),
        "disable_stats": "✅ 匿名統計を許可",
        "enable_stats": "🚫 匿名統計は無効",
    }

    strings_kr = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>시청자:</b>\n\n<b>{}</b>"
        ),
        "mod404": "<emoji document_id=5447207618793708263>🚫</emoji> <b>뷰어 아님{}찾았다</b>",
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>감시자 {}이(가) 현재 있습니다"
            " <u>꺼짐</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>감시자 {}이(가) 현재 있습니다"
            " <u>활성화</u></b>"
        ),
        "args": "<emoji document_id=5447207618793708263>🚫</emoji> <b>이름을 입력하세요.관리인</b>",
        "user_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>에 대한 닉네임 위치가 없습니다."
            " 이 사용자가 아닙니다: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>명령어"
            " 누가 NoNick을 활성화/\\비활성화할지 지정</b>"
        ),
        "cmd_nn": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>에 대한 닉네임 위치가 없습니다."
            " </b><code>{}</code><b>가 아닙니다: {}</b>"
        ),
        "cmd404": "<emoji document_id=5469791106591890404>🪄</emoji> <b>명령을 찾을 수 없음</b>",
        "inline_settings": "⚙️ <b>여기에서 Hikka 설정을 관리할 수 있습니다.</b>",
        "confirm_update": "🧭 <b>업데이트를 확인하십시오. Userbot이 다시 시작됩니다</b>",
        "confirm_restart": "🔄 <b>다시 시작 확인</b>",
        "suggest_fs": " 저장 모듈 제안",
        "do_not_suggest_fs": "🚫 모듈 저장 제안",
        "use_fs": "✅ 항상 모듈 저장",
        "do_not_use_fs": "🚫 항상 모듈 저장",
        "btn_restart": " 다시 시작",
        "btn_update": "🧭 업데이트",
        "close_menu": " 메뉴 닫기",
        "custom_emojis": "✅ 사용자 정의 그림 이모티콘",
        "no_custom_emojis": "🚫 맞춤 이모티콘",
        "suggest_subscribe": " 채널 구독 제안",
        "do_not_suggest_subscribe": " 채널 구독 제안",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>이 명령이 필요합니다."
            "채팅에서 실행</b>"
        ),
        "_cls_doc": "고급 Hikka 설정",
        "nonick_warning": (
            "주의! 표준 접두사에 NoNick을 포함했습니다!Hikka 채팅에서 음소거할 수 있습니다. 접두사를 변경하거나 글로벌 노닉 꺼!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>메시지에 답장"
            "사용자가 NoNick을 활성화합니다</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>이 작업은 이 계정에서 Hikka를 완전히 제거합니다! 그는 할 수 없습니다."
            "취소</b>\n\n<i>- Hikka와 관련된 모든 채팅이 삭제됩니다\n- 세션"
            " Hikka가 재설정됩니다\n- Hikka의 인라인 봇이 제거됩니다</i>"
        ),
        "deauth_confirm_step2": "⚠️ <b>Hikka를 제거하시겠습니까?</b>",
        "deauth_yes": "확실합니다",
        "deauth_no_1": "잘 모르겠습니다",
        "deauth_no_2": "확실하지 않음",
        "deauth_no_3": "아니요",
        "deauth_cancel": "🚫 취소",
        "deauth_confirm_btn": "😢 삭제",
        "uninstalling": "😢 <b>Hikka 제거 중...</b>",
        "uninstalled": (
            "😢 <b>Hikka'는 더 이상 사용되지 않습니다. 웹 인터페이스는 여전히 활성화되어 있습니다. 계정을 추가할 수 있습니다!</b>"
        ),
        "logs_cleared": "🗑 <b>로그 삭제</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick이 활성화되었습니다."
            " 다음 명령:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick이 활성화되었습니다."
            " 이 사용자:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick이 활성화되었습니다."
            " 이 채팅:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷️</emoji> <b>아무것도 없음보여줘...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>이 명령은 Hikka 웹 인터페이스에 대한 액세스를 제공합니다. 실행"
            "공개채팅은 보안상 위험합니다. 가급적이면 수행하세요."
            "<a href='tg://openmessage?user_id={}'>메시지 선택</a>에 있습니다."
            "</b><code>{}proxypass force_insecure</code><b>를 실행하여 비활성화"
            "경고입니다</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>이 명령은 Hikka 웹 인터페이스에 대한 액세스를 제공합니다. 실행"
            "공개채팅은 보안상 위험합니다. 가급적이면 수행하세요."
            " <a href='tg://openmessage?user_id={}'>메시지 선택</a> 안에.</b>"
        ),
        "opening_tunnel": "🔁 <b>Hikka 웹 인터페이스에 터널을 여는 중...</b>",
        "tunnel_opened": "🎉 <b>터널이 열려 있습니다. 이 링크는 1시간 이상 활성화되지 않습니다</b>",
        "web_btn": "🌍 웹 인터페이스",
        "btn_yes": " 어쨌든 열기",
        "btn_no": " 닫기",
        "lavhost_web": (
            "✌️ <b>이 링크는 Hikka 웹 인터페이스 lvHost</b>로 이동합니다.\n\n<i>💡"
            "lavHost를 설정할 때 자격 증명을 사용하여 로그인해야 합니다"
            "지정됨</i>"
        ),
        "disable_stats": "✅ 익명 통계 허용됨",
        "enable_stats": "🚫 익명 통계 비활성화됨",
    }

    strings_ar = {
        "watchers": (
            "<emoji document_id=5424885441100782420> 👀 </emoji>"
            "<b> المشاهد, ن: </b>\n\n<b> {} </b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b> ليس عارض {}"
            "تم العث, ر عليه </b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420> 👀 </emoji> <b> المشاهد {} الآن"
            "<u> إيقاف </u> </b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420> 👀 </emoji> <b> المشاهد {} الآن"
            "<u> ممكّن </u> </b>"
        ),
        "أرغس": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b> الرجاء إدخال اسم"
            "مشرف </b>"
        ),
        "user_nn": (
            "لا ي, جد م, ضع لقب لـ <emoji document_id=5469791106591890404>🪄</emoji> <b>"
            "ليس هذا المستخدم: {} </b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b> أمر خاص بها"
            "تحديد من يجب عليه تمكين / \\ تعطيل NoNick </b>"
        ),
        "cmd_nn": (
            "لا ي, جد م, ضع لقب لـ <emoji document_id=5469791106591890404>🪄</emoji> <b>"
            "ليس </b> <code> {} </code> <b>: {} </b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b> الأمر غير م, ج, د"
            " </b>"
        ),
        "inline_settings": "⚙️ <b> هنا يمكنك إدارة إعدادات Hikka </b>",
        "Confirm_update": "🧭 <b> أكد التحديث. سيعيد Userbot إعادة التشغيل </b>",
        "irm_restart ": " 🔄 <b> تأكيد إعادة التشغيل </b> ",
        "Suggest_fs": "اقتراح , حدة حفظ",
        "do_not_suggest_fs": "🚫 اقتراح , حدة حفظ",
        "use_fs": "✅ احفظ ال, حدات دائمًا",
        "do_not_use_fs": "🚫 احفظ ال, حدات دائمًا",
        "btn_restart": "إعادة التشغيل",
        "btn_update": "🧭 تحديث",
        "close_menu": "إغلاق القائمة",
        "custom_emojis": "✅ Custom Emoji",
        "no_custom_emojis": "🚫 Custom Emoji",
        "suggest_subscribe": "اقتراح اشتراك قناة",
        "do_not_suggest_subscribe": "اقتراح اشتراك قناة",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b> هذا الأمر مطل, ب"
            "تنفيذ في الدردشة </b>"
        ),
        "_cls_doc": "إعدادات Hikka المتقدمة",
        "nonick_warning": (
            "تنبيه! لقد قمت بتضمين NoNick مع البادئة القياسية!"
            "يمكن كتم ص, تك في Hikka Chat. قم بتغيير البادئة أ, "
            "إيقاف تشغيل NoNick العالمية!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b> الرد على الرسالة"
            "سيق, م المستخدم بتمكين NoNick </b>"
        ),
        "deauth_confirm": (
            "⚠️ <b> سيؤدي هذا الإجراء إلى إزالة Hikka تمامًا من هذا الحساب! لا يمكنه"
            " ذلكإلغاء </b>\n\n<i> - سيتم حذف كافة الدردشات المتعلقة بهيكا\n-"
            " الجلسةستتم إعادة تعيين Hikka\n- ستتم إزالة برنامج Hikka المضمن </i>"
        ),
        "deauth_confirm_step2": "⚠️ <b> هل أنت متأكد من أنك تريد إزالة Hikka؟ </b>",
        "deauth_yes": "أنا متأكد",
        "deauth_no_1": "لست متأكدًا",
        "deauth_no_2": "لست متأكدًا",
        "deauth_no_3": "لا",
        "deauth_cancel": "🚫 إلغاء",
        "deauth_confirm_btn": "😢 حذف",
        "uninstalling": "😢 <b> إزالة Hikka ... </b>",
        "uninstalled": (
            "<b>تم إهمال  Hikka. , اجهة ال, يب لا تزال نشطة ,  , البعض الآخر"
            "يمكن أن تضاف حسابات! </b>"
        ),
        "logs_cleared": "🗑 <b> تم مسح السجلات </b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b> تم تمكين NoNick لهذا"
            "هذه الأ, امر: </b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b> تم تمكين NoNick لهذا"
            "هذا المستخدم: </b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b> تم تمكين NoNick لهذا"
            "هذه الدردشة: </b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126> 🤷️ </emoji> <b> لا شيءعرض ... </b>"
        ),
        "privacy_leak": (
            "⚠️ <b> ي, فر هذا الأمر ال, ص, ل إلى , اجهة , يب Hikka. تنفيذه"
            "الدردشة العامة تشكل مخاطرة أمنية. , يفضل أن تؤدي"
            "إنه م, ج, د في <a href='tg://openmessage؟user_id={}'> حدد الرسائل </a>."
            "تشغيل </b> <code> {proxypass force_insecure </code> <b> للتعطيل"
            "هذا تحذير </b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b> ي, فر هذا الأمر ال, ص, ل إلى , اجهة , يب Hikka. تنفيذه"
            "الدردشة العامة تشكل مخاطرة أمنية. , يفضل أن تؤدي"
            "<a href='tg://openmessage؟user_id={}'> حدد الرسائل</a> في. </b> "
        ),
        "open_tunnel": "🔁 <b> فتح نفق ل, اجهة , يب Hikka ... </b>",
        "tunnel_opened": (
            "🎉 <b> النفق مفت, ح. لن يك, ن هذا الرابط نشطًا لأكثر من ساعة </b>"
        ),
        "web_btn": "🌍 , اجهة ال, يب",
        "btn_yes": "فتح على أي حال",
        "btn_no": "إغلاق",
        "lavhost_web": (
            "✌️ <b> سينقلك هذا الارتباط إلى , اجهة , يب Hikka lvHost </b>\n\n<i> 💡"
            "يجب تسجيل الدخ, ل باستخدام بيانات الاعتماد الخاصة بك عند إعداد lavHost"
            "محدد </ i>"
        ),
        "disable_stats": "✅ يسمح بإحصاءات مجه, لة",
        "enable_stats": "🚫 تم تعطيل الإحصائيات المجه, لة",
    }

    strings_es = {
        "watchers": (
            "<emoji document_id=5424885441100782420>👀</emoji>"
            " <b>Espectadores:</b>\n\n<b>{}</b>"
        ),
        "mod404": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>No visor {}"
            "Encontrado</b>"
        ),
        "disabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>observador {} ya está"
            " <u>apagado</u></b>"
        ),
        "enabled": (
            "<emoji document_id=5424885441100782420>👀</emoji> <b>observador {} ya está"
            " <u>habilitado</u></b>"
        ),
        "args": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Por favor ingrese un"
            " nombrecuidador</b>"
        ),
        "user_nn": (
            "No hay posición de nick para <emoji"
            " document_id=5469791106591890404>🪄</emoji> <b> no es este usuario: {}</b>"
        ),
        "no_cmd": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Un comando para ello"
            " Especificar quién debe activar/desactivar NoNick</b>"
        ),
        "cmd_nn": (
            "No hay posición de nick para <emoji"
            " document_id=5469791106591890404>🪄</emoji> <b> no es"
            " </b><código>{}</código><b>: {}</b>"
        ),
        "cmd404": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>Comando no"
            " encontrado</b>"
        ),
        "inline_settings": (
            "⚙️ <b>Aquí puedes administrar la configuración de Hikka</b>"
        ),
        "confirm_update": "🧭 <b>Confirmar actualización. Userbot se reiniciará</b>",
        "confirm_restart": "🔄 <b>Confirmar reinicio</b>",
        "suggest_fs": " Sugerir guardar módulo",
        "do_not_suggest_fs": "🚫 Sugerir guardar módulo",
        "use_fs": "✅ Guardar siempre los módulos",
        "do_not_use_fs": "🚫 Guardar siempre los módulos",
        "btn_restart": "reiniciar",
        "btn_update": "🧭 actualizar",
        "close_menu": " Cerrar Menú",
        "custom_emojis": "✅ Emoji personalizado",
        "no_custom_emojis": "🚫Emoji personalizado",
        "suggest_subscribe": "Sugerir suscripción al canal",
        "do_not_suggest_subscribe": " Sugerir suscripción al canal",
        "private_not_allowed": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>Este comando es"
            " necesarioEjecutar en el chat</b>"
        ),
        "_cls_doc": "Configuración avanzada de Hikka",
        "nonick_warning": (
            "¡Atención! ¡Has incluido NoNick con el prefijo estándar!"
            "Puedes silenciarte en Hikka Chat. Cambia el prefijo o "
            "¡Apaga el NoNick global!"
        ),
        "reply_required": (
            "<emoji document_id=5447207618793708263>🚫</emoji> <b>responder al mensaje"
            "El usuario habilitará NoNick</b>"
        ),
        "deauth_confirm": (
            "⚠️ <b>¡Esta acción eliminará completamente a Hikka de esta cuenta! Él no"
            " puedeCancelar</b>\n\n<i>- Se eliminarán todos los chats relacionados con"
            " Hikka\n- Sesión Hikka se reiniciará\n- El bot en línea de Hikka se"
            " eliminará</i>"
        ),
        "deauth_confirm_step2": (
            "⚠️ <b>¿Está seguro de que desea desinstalar Hikka?</b>"
        ),
        "deauth_yes": "Estoy seguro",
        "deauth_no_1": "No estoy seguro",
        "deauth_no_2": "No estoy seguro",
        "deauth_no_3": "No",
        "deauth_cancel": "🚫 Cancelar",
        "deauth_confirm_btn": "😢 Eliminar",
        "uninstall": "😢 <b>Desinstalando Hikka...</b>",
        "uninstalled": (
            "😢 <b>Hikka' ha quedado obsoleto. La interfaz web todavía está activa,"
            " otros¡Se pueden agregar cuentas!</b>"
        ),
        "logs_cleared": "🗑 <b>Registros borrados</b>",
        "cmd_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick habilitado para"
            " esto Estos comandos:</b>\n\n{}"
        ),
        "user_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick habilitado para"
            " estoEste usuario:</b>\n\n{}"
        ),
        "chat_nn_list": (
            "<emoji document_id=5469791106591890404>🪄</emoji> <b>NoNick habilitado para"
            " esto Este chat:</b>\n\n{}"
        ),
        "nothing": (
            "<emoji document_id=5427052514094619126>🤷️</emoji> <b>nadaMostrar...</b>"
        ),
        "privacy_leak": (
            "⚠️ <b>Este comando proporciona acceso a la interfaz web de Hikka. Su"
            " ejecuciónEl chat público es un riesgo de seguridad. Preferiblemente"
            " realizarEstá en <a href='tg://openmessage?user_id={}'>mensajes"
            " seleccionados</a>Ejecute </b><code>{}proxypass force_insecure</code><b>"
            " para desactivarEsto es una advertencia</b>"
        ),
        "privacy_leak_nowarn": (
            "⚠️ <b>Este comando proporciona acceso a la interfaz web de Hikka. Su"
            " ejecuciónEl chat público es un riesgo de seguridad. Preferiblemente"
            " realizar <a href='tg://openmessage?user_id={}'>seleccionar mensajes</a>"
            " pulg.</b>"
        ),
        "opening_tunnel": "🔁 <b>Abriendo un túnel a la interfaz web de Hikka...</b>",
        "túnel_abierto": (
            "🎉 <b>el túnel está abierto. Este enlace no estará activo durante más de"
            " una hora</b>"
        ),
        "web_btn": "🌍 Interfaz web",
        "btn_yes": " Abrir de todos modos",
        "btn_no": "Cerrar",
        "lavhost_web": (
            "✌️ <b>Este enlace lo llevará a la interfaz web de Hikka lvHost</b>\n\n<i>💡"
            "debe iniciar sesión con sus credenciales al configurar lavHost"
            "Especificado</i>"
        ),
        "disable_stats": "✅ Estadísticas anónimas permitidas",
        "enable_stats": "🚫 Estadísticas anónimas deshabilitadas",
    }

    def get_watchers(self) -> tuple:
        return [
            str(watcher.__self__.__class__.strings["name"])
            for watcher in self.allmodules.watchers
            if watcher.__self__.__class__.strings is not None
        ], self._db.get(main.__name__, "disabled_watchers", {})

    async def _uninstall(self, call: InlineCall):
        await call.edit(self.strings("uninstall"))

        async with self._client.conversation("@BotFather") as conv:
            for msg in [
                "/deletebot",
                f"@{self.inline.bot_username}",
                "Yes, I am totally sure.",
            ]:
                m = await conv.send_message(msg)
                r = await conv.get_response()

                logger.debug(">> %s", m.raw_text)
                logger.debug("<< %s", r.raw_text)

                await m.delete()
                await r.delete()

        async for dialog in self._client.iter_dialogs(
            None,
            ignore_migrated=True,
        ):
            if (
                dialog.name
                in {
                    "hikka-logs",
                    "hikka-onload",
                    "hikka-assets",
                    "hikka-backups",
                    "hikka-acc-switcher",
                    "silent-tags",
                }
                and dialog.is_channel
                and (
                    dialog.entity.participants_count == 1
                    or dialog.entity.participants_count == 2
                    and dialog.name in {"hikka-logs", "silent-tags"}
                )
                or (
                    self._client.loader.inline.init_complete
                    and dialog.entity.id == self._client.loader.inline.bot_id
                )
            ):
                await self._client.delete_dialog(dialog.entity)

        folders = await self._client(GetDialogFiltersRequest())

        if any(folder.title == "hikka" for folder in folders):
            folder_id = max(
                folders,
                key=lambda x: x.id,
            ).id

            await self._client(UpdateDialogFilterRequest(id=folder_id))

        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.CRITICAL)

        await self._client.log_out()

        await call.edit(self.strings("uninstalled"))

        if "LAVHOST" in os.environ:
            os.system("lavhost restart")
            return

        atexit.register(restart, *sys.argv[1:])
        sys.exit(0)

    async def _uninstall_confirm_step_2(self, call: InlineCall):
        await call.edit(
            self.strings("deauth_confirm_step2"),
            utils.chunks(
                list(
                    sorted(
                        [
                            {
                                "text": self.strings("deauth_yes"),
                                "callback": self._uninstall,
                            },
                            *[
                                {
                                    "text": self.strings(f"deauth_no_{i}"),
                                    "action": "close",
                                }
                                for i in range(1, 4)
                            ],
                        ],
                        key=lambda _: random.random(),
                    )
                ),
                2,
            )
            + [
                [
                    {
                        "text": self.strings("deauth_cancel"),
                        "action": "close",
                    }
                ]
            ],
        )

    @loader.owner
    @loader.command(
        ru_doc="Удалить Hikka",
        de_doc="Hikka deinstallieren",
        tr_doc="Hikka'yı kaldır",
        uz_doc="Hikka'ni o'chirish",
        ja_doc="Hikkaをアンインストールします",
        kr_doc="Hikka를 제거합니다",
        ar_doc="إلغاء تثبيت هيكا",
        es_doc="Desinstalar Hikka",
    )
    async def uninstall_hikka(self, message: Message):
        """Uninstall Hikka"""
        await self.inline.form(
            self.strings("deauth_confirm"),
            message,
            [
                {
                    "text": self.strings("deauth_confirm_btn"),
                    "callback": self._uninstall_confirm_step_2,
                },
                {"text": self.strings("deauth_cancel"), "action": "close"},
            ],
        )

    @loader.command(
        ru_doc="Очистить логи",
        de_doc="Logs löschen",
        tr_doc="Günlükleri temizle",
        uz_doc="Jurnalni tozalash",
        ja_doc="ログをクリアする",
        kr_doc="로그 지우기",
        ar_doc="مسح السجلات",
        es_doc="Limpiar registros",
    )
    async def clearlogs(self, message: Message):
        """Clear logs"""
        for handler in logging.getLogger().handlers:
            handler.buffer = []
            handler.handledbuffer = []
            handler.tg_buff = ""

        await utils.answer(message, self.strings("logs_cleared"))

    @loader.command(
        ru_doc="Показать активные смотрители",
        de_doc="Aktive Beobachter anzeigen",
        tr_doc="Etkin gözlemcileri göster",
        uz_doc="Faol ko'rib chiqqanlarni ko'rsatish",
        ja_doc="アクティブな観察者を表示する",
        kr_doc="활성 관찰자 표시",
        ar_doc="عرض المراقبين النشطين",
        es_doc="Mostrar observadores activos",
    )
    async def watchers(self, message: Message):
        """List current watchers"""
        watchers, disabled_watchers = self.get_watchers()
        watchers = [
            f"♻️ {watcher}"
            for watcher in watchers
            if watcher not in list(disabled_watchers.keys())
        ]
        watchers += [f"💢 {k} {v}" for k, v in disabled_watchers.items()]
        await utils.answer(
            message, self.strings("watchers").format("\n".join(watchers))
        )

    @loader.command(
        ru_doc="<module> - Включить/выключить смотрителя в текущем чате",
        de_doc="<module> - Aktiviere/Deaktiviere Beobachter in diesem Chat",
        tr_doc="<module> - Bu sohbetteki gözlemciyi etkinleştirin/devre dışı bırakın",
        uz_doc="<module> - Joriy suhbatda ko'rib chiqqanlarni yoqish/yopish",
        ja_doc="<module> - このチャットで観察者を有効/無効にする",
        kr_doc="<module> -이 채팅에서 관찰자를 활성화 / 비활성화",
        ar_doc="<module> - تمكين / تعطيل المراقب في الدردشة الحالية",
        es_doc="<module> - Habilitar / deshabilitar observador en este chat",
    )
    async def watcherbl(self, message: Message):
        """<module> - Toggle watcher in current chat"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in map(lambda x: x.lower(), watchers):
            await utils.answer(message, self.strings("mod404").format(args))
            return

        args = next((x.lower() == args.lower() for x in watchers), False)

        current_bl = [
            v for k, v in disabled_watchers.items() if k.lower() == args.lower()
        ]
        current_bl = current_bl[0] if current_bl else []

        chat = utils.get_chat_id(message)
        if chat not in current_bl:
            if args in disabled_watchers:
                for k in disabled_watchers:
                    if k.lower() == args.lower():
                        disabled_watchers[k].append(chat)
                        break
            else:
                disabled_watchers[args] = [chat]

            await utils.answer(
                message,
                self.strings("disabled").format(args) + " <b>in current chat</b>",
            )
        else:
            for k in disabled_watchers.copy():
                if k.lower() == args.lower():
                    disabled_watchers[k].remove(chat)
                    if not disabled_watchers[k]:
                        del disabled_watchers[k]
                    break

            await utils.answer(
                message,
                self.strings("enabled").format(args) + " <b>in current chat</b>",
            )

        self._db.set(main.__name__, "disabled_watchers", disabled_watchers)

    @loader.command(
        ru_doc=(
            "<модуль> - Управление глобальными правилами смотрителя\n"
            "Аргументы:\n"
            "[-c - только в чатах]\n"
            "[-p - только в лс]\n"
            "[-o - только исходящие]\n"
            "[-i - только входящие]"
        ),
        de_doc=(
            "<module> - Verwalte globale Beobachterregeln\n"
            "Argumente:\n"
            "[-c - Nur in Chats]\n"
            "[-p - Nur in privaten Chats]\n"
            "[-o - Nur ausgehende Nachrichten]\n"
            "[-i - Nur eingehende Nachrichten]"
        ),
        tr_doc=(
            "<module> - Genel gözlemci kurallarını yönetin\n"
            "Argümanlar:\n"
            "[-c - Yalnızca sohbetlerde]\n"
            "[-p - Yalnızca özel sohbetlerde]\n"
            "[-o - Yalnızca giden mesajlar]\n"
            "[-i - Yalnızca gelen mesajlar]"
        ),
        uz_doc=(
            "<module> - Umumiy ko'rib chiqqan qoidalarni boshqarish\n"
            "Argumentlar:\n"
            "[-c - Faqat suhbatlarda]\n"
            "[-p - Faqat shaxsiy suhbatlarda]\n"
            "[-o - Faqat chiqarilgan xabarlar]\n"
            "[-i - Faqat kelgan xabarlar]"
        ),
        ja_doc=(
            "<module> - グローバル観察者ルールを管理します\n"
            "引数:\n"
            "[-c - チャットのみ]\n"
            "[-p - プライベートチャットのみ]\n"
            "[-o - 送信メッセージのみ]\n"
            "[-i - 受信メッセージのみ]"
        ),
        kr_doc=(
            "<module> - 전역 관찰자 규칙을 관리합니다\n"
            "인수:\n"
            "[-c - 채팅 만]\n"
            "[-p - 개인 채팅 만]\n"
            "[-o - 보낸 메시지 만]\n"
            "[-i - 수신 메시지 만]"
        ),
        ar_doc=(
            "<module> - إدارة قواعد المراقب العامة\n"
            "الوسائط:\n"
            "[-c - فقط الدردشات]\n"
            "[-p - فقط الدردشات الخاصة]\n"
            "[-o - فقط الرسائل الصادرة]\n"
            "[-i - الرسائل الواردة فقط]"
        ),
        es_doc=(
            "<module> - Administre las reglas del observador global\n"
            "Argumentos:\n"
            "[-c - Solo en chats]\n"
            "[-p - Solo en chats privados]\n"
            "[-o - Solo mensajes salientes]\n"
            "[-i - Solo mensajes entrantes]"
        ),
    )
    async def watchercmd(self, message: Message):
        """<module> - Toggle global watcher rules
        Args:
        [-c - only in chats]
        [-p - only in pm]
        [-o - only out]
        [-i - only incoming]"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        chats, pm, out, incoming = False, False, False, False

        if "-c" in args:
            args = args.replace("-c", "").replace("  ", " ").strip()
            chats = True

        if "-p" in args:
            args = args.replace("-p", "").replace("  ", " ").strip()
            pm = True

        if "-o" in args:
            args = args.replace("-o", "").replace("  ", " ").strip()
            out = True

        if "-i" in args:
            args = args.replace("-i", "").replace("  ", " ").strip()
            incoming = True

        if chats and pm:
            pm = False
        if out and incoming:
            incoming = False

        watchers, disabled_watchers = self.get_watchers()

        if args.lower() not in [watcher.lower() for watcher in watchers]:
            return await utils.answer(message, self.strings("mod404").format(args))

        args = [watcher for watcher in watchers if watcher.lower() == args.lower()][0]

        if chats or pm or out or incoming:
            disabled_watchers[args] = [
                *(["only_chats"] if chats else []),
                *(["only_pm"] if pm else []),
                *(["out"] if out else []),
                *(["in"] if incoming else []),
            ]
            self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
            await utils.answer(
                message,
                self.strings("enabled").format(args)
                + f" (<code>{disabled_watchers[args]}</code>)",
            )
            return

        if args in disabled_watchers and "*" in disabled_watchers[args]:
            await utils.answer(message, self.strings("enabled").format(args))
            del disabled_watchers[args]
            self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
            return

        disabled_watchers[args] = ["*"]
        self._db.set(main.__name__, "disabled_watchers", disabled_watchers)
        await utils.answer(message, self.strings("disabled").format(args))

    @loader.command(
        ru_doc="Включить NoNick для определенного пользователя",
        de_doc="Aktiviere NoNick für einen bestimmten Benutzer",
        tr_doc="Belirli bir kullanıcı için NoNick'i etkinleştirin",
        uz_doc="Belgilangan foydalanuvchi uchun NoNickni yoqish",
        ja_doc="特定のユーザーのNoNickを有効にします",
        kr_doc="특정 사용자의 NoNick를 활성화합니다",
        ar_doc="تمكين NoNick لمستخدم معين",
        es_doc="Habilitar NoNick para un usuario específico",
    )
    async def nonickuser(self, message: Message):
        """Allow no nickname for certain user"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings("reply_required"))
            return

        u = reply.sender_id
        if not isinstance(u, int):
            u = u.user_id

        nn = self._db.get(main.__name__, "nonickusers", [])
        if u not in nn:
            nn += [u]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(message, self.strings("user_nn").format("on"))
        else:
            nn = list(set(nn) - {u})
            await utils.answer(message, self.strings("user_nn").format("off"))

        self._db.set(main.__name__, "nonickusers", nn)

    @loader.command(
        ru_doc="Включить NoNick для определенного чата",
        de_doc="Aktiviere NoNick für einen bestimmten Chat",
        tr_doc="Belirli bir sohbet için NoNick'i etkinleştirin",
        uz_doc="Belgilangan suhbat uchun NoNickni yoqish",
        ja_doc="特定のチャットのNoNickを有効にします",
        kr_doc="특정 채팅의 NoNick를 활성화합니다",
        ar_doc="تمكين NoNick لدردشة معينة",
        es_doc="Habilitar NoNick para un chat específico",
    )
    async def nonickchat(self, message: Message):
        """Allow no nickname in certain chat"""
        if message.is_private:
            await utils.answer(message, self.strings("private_not_allowed"))
            return

        chat = utils.get_chat_id(message)

        nn = self._db.get(main.__name__, "nonickchats", [])
        if chat not in nn:
            nn += [chat]
            nn = list(set(nn))  # skipcq: PTC-W0018
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "on",
                ),
            )
        else:
            nn = list(set(nn) - {chat})
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    utils.escape_html((await message.get_chat()).title),
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickchats", nn)

    @loader.command(
        ru_doc="Включить NoNick для определенной команды",
        de_doc="Aktiviere NoNick für einen bestimmten Befehl",
        tr_doc="Belirli bir komut için NoNick'i etkinleştirin",
        uz_doc="Belgilangan buyruq uchun NoNickni yoqish",
        ja_doc="特定のコマンドのNoNickを有効にします",
        kr_doc="특정 명령의 NoNick를 활성화합니다",
        ar_doc="تمكين NoNick لأمر معين",
        es_doc="Habilitar NoNick para un comando específico",
    )
    async def nonickcmdcmd(self, message: Message):
        """Allow certain command to be executed without nickname"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_cmd"))
            return

        if args not in self.allmodules.commands:
            await utils.answer(message, self.strings("cmd404"))
            return

        nn = self._db.get(main.__name__, "nonickcmds", [])
        if args not in nn:
            nn += [args]
            nn = list(set(nn))
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "on",
                ),
            )
        else:
            nn = list(set(nn) - {args})
            await utils.answer(
                message,
                self.strings("cmd_nn").format(
                    self.get_prefix() + args,
                    "off",
                ),
            )

        self._db.set(main.__name__, "nonickcmds", nn)

    @loader.command(
        ru_doc="Показать список активных NoNick команд",
        de_doc="Zeige eine Liste der aktiven NoNick Befehle",
        tr_doc="Etkin NoNick komutlarının listesini göster",
        uz_doc="Yoqilgan NoNick buyruqlar ro'yxatini ko'rsatish",
        ja_doc="アクティブなNoNickコマンドのリストを表示します",
        kr_doc="활성 NoNick 명령 목록 표시",
        ar_doc="عرض قائمة أوامر NoNick النشطة",
        es_doc="Mostrar una lista de comandos NoNick activos",
    )
    async def nonickcmds(self, message: Message):
        """Returns the list of NoNick commands"""
        if not self._db.get(main.__name__, "nonickcmds", []):
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("cmd_nn_list").format(
                "\n".join(
                    [
                        f"▫️ <code>{self.get_prefix()}{cmd}</code>"
                        for cmd in self._db.get(main.__name__, "nonickcmds", [])
                    ]
                )
            ),
        )

    @loader.command(
        ru_doc="Показать список активных NoNick пользователей",
        de_doc="Zeige eine Liste der aktiven NoNick Benutzer",
        tr_doc="Etkin NoNick kullanıcılarının listesini göster",
        uz_doc="Yoqilgan NoNick foydalanuvchilar ro'yxatini ko'rsatish",
        ja_doc="アクティブなNoNickユーザーのリストを表示します",
        kr_doc="활성 NoNick 사용자 목록 표시",
        ar_doc="عرض قائمة مستخدمي NoNick النشطة",
        es_doc="Mostrar una lista de usuarios NoNick activos",
    )
    async def nonickusers(self, message: Message):
        """Returns the list of NoNick users"""
        users = []
        for user_id in self._db.get(main.__name__, "nonickusers", []).copy():
            try:
                user = await self._client.get_entity(user_id)
            except Exception:
                self._db.set(
                    main.__name__,
                    "nonickusers",
                    list(
                        (
                            set(self._db.get(main.__name__, "nonickusers", []))
                            - {user_id}
                        )
                    ),
                )

                logger.warning("User %s removed from nonickusers list", user_id)
                continue

            users += [
                '▫️ <b><a href="tg://user?id={}">{}</a></b>'.format(
                    user_id,
                    utils.escape_html(get_display_name(user)),
                )
            ]

        if not users:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(users)),
        )

    @loader.command(
        ru_doc="Показать список активных NoNick чатов",
        de_doc="Zeige eine Liste der aktiven NoNick Chats",
        tr_doc="Etkin NoNick sohbetlerinin listesini göster",
        uz_doc="Yoqilgan NoNick suhbatlar ro'yxatini ko'rsatish",
        ja_doc="アクティブなNoNickチャットのリストを表示します",
        kr_doc="활성 NoNick 채팅 목록 표시",
        ar_doc="عرض قائمة الدردشات NoNick النشطة",
        es_doc="Mostrar una lista de chats NoNick activos",
    )
    async def nonickchats(self, message: Message):
        """Returns the list of NoNick chats"""
        chats = []
        for chat in self._db.get(main.__name__, "nonickchats", []):
            try:
                chat_entity = await self._client.get_entity(int(chat))
            except Exception:
                self._db.set(
                    main.__name__,
                    "nonickchats",
                    list(
                        (set(self._db.get(main.__name__, "nonickchats", [])) - {chat})
                    ),
                )

                logger.warning("Chat %s removed from nonickchats list", chat)
                continue

            chats += [
                '▫️ <b><a href="{}">{}</a></b>'.format(
                    utils.get_entity_url(chat_entity),
                    utils.escape_html(get_display_name(chat_entity)),
                )
            ]

        if not chats:
            await utils.answer(message, self.strings("nothing"))
            return

        await utils.answer(
            message,
            self.strings("user_nn_list").format("\n".join(chats)),
        )

    async def inline__setting(self, call: InlineCall, key: str, state: bool = False):
        if callable(key):
            key()
            telethon.extensions.html.CUSTOM_EMOJIS = not main.get_config_key(
                "disable_custom_emojis"
            )
        else:
            self._db.set(main.__name__, key, state)

        if key == "no_nickname" and state and self.get_prefix() == ".":
            await call.answer(
                self.strings("nonick_warning"),
                show_alert=True,
            )
        else:
            await call.answer("Configuration value saved!")

        await call.edit(
            self.strings("inline_settings"),
            reply_markup=self._get_settings_markup(),
        )

    async def inline__update(
        self,
        call: InlineCall,
        confirm_required: bool = False,
    ):
        if confirm_required:
            await call.edit(
                self.strings("confirm_update"),
                reply_markup=[
                    {"text": "🪂 Update", "callback": self.inline__update},
                    {"text": "🚫 Cancel", "action": "close"},
                ],
            )
            return

        await call.answer("You userbot is being updated...", show_alert=True)
        await call.delete()
        m = await self._client.send_message("me", f"{self.get_prefix()}update --force")
        await self.allmodules.commands["update"](m)

    async def inline__restart(
        self,
        call: InlineCall,
        confirm_required: bool = False,
    ):
        if confirm_required:
            await call.edit(
                self.strings("confirm_restart"),
                reply_markup=[
                    {"text": "🔄 Restart", "callback": self.inline__restart},
                    {"text": "🚫 Cancel", "action": "close"},
                ],
            )
            return

        await call.answer("You userbot is being restarted...", show_alert=True)
        await call.delete()
        await self.allmodules.commands["restart"](
            await self._client.send_message("me", f"{self.get_prefix()}restart --force")
        )

    def _get_settings_markup(self) -> list:
        return [
            [
                (
                    {
                        "text": "✅ NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "no_nickname", False)
                    else {
                        "text": "🚫 NoNick",
                        "callback": self.inline__setting,
                        "args": (
                            "no_nickname",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "✅ Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "grep", False)
                    else {
                        "text": "🚫 Grep",
                        "callback": self.inline__setting,
                        "args": (
                            "grep",
                            True,
                        ),
                    }
                ),
                (
                    {
                        "text": "✅ InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "inlinelogs", True)
                    else {
                        "text": "🚫 InlineLogs",
                        "callback": self.inline__setting,
                        "args": (
                            "inlinelogs",
                            True,
                        ),
                    }
                ),
            ],
            [
                {
                    "text": self.strings("do_not_suggest_fs"),
                    "callback": self.inline__setting,
                    "args": (
                        "disable_modules_fs",
                        False,
                    ),
                }
                if self._db.get(main.__name__, "disable_modules_fs", False)
                else {
                    "text": self.strings("suggest_fs"),
                    "callback": self.inline__setting,
                    "args": (
                        "disable_modules_fs",
                        True,
                    ),
                }
            ],
            [
                (
                    {
                        "text": self.strings("use_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "permanent_modules_fs",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "permanent_modules_fs", False)
                    else {
                        "text": self.strings("do_not_use_fs"),
                        "callback": self.inline__setting,
                        "args": (
                            "permanent_modules_fs",
                            True,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("suggest_subscribe"),
                        "callback": self.inline__setting,
                        "args": (
                            "suggest_subscribe",
                            False,
                        ),
                    }
                    if self._db.get(main.__name__, "suggest_subscribe", True)
                    else {
                        "text": self.strings("do_not_suggest_subscribe"),
                        "callback": self.inline__setting,
                        "args": (
                            "suggest_subscribe",
                            True,
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("no_custom_emojis"),
                        "callback": self.inline__setting,
                        "args": (
                            lambda: main.save_config_key(
                                "disable_custom_emojis", False
                            ),
                        ),
                    }
                    if main.get_config_key("disable_custom_emojis")
                    else {
                        "text": self.strings("custom_emojis"),
                        "callback": self.inline__setting,
                        "args": (
                            lambda: main.save_config_key("disable_custom_emojis", True),
                        ),
                    }
                ),
            ],
            [
                (
                    {
                        "text": self.strings("disable_stats"),
                        "callback": self.inline__setting,
                        "args": ("stats", False),
                    }
                    if self._db.get(main.__name__, "stats", True)
                    else {
                        "text": self.strings("enable_stats"),
                        "callback": self.inline__setting,
                        "args": (
                            "stats",
                            True,
                        ),
                    }
                ),
            ],
            [
                {
                    "text": self.strings("btn_restart"),
                    "callback": self.inline__restart,
                    "args": (True,),
                },
                {
                    "text": self.strings("btn_update"),
                    "callback": self.inline__update,
                    "args": (True,),
                },
            ],
            [{"text": self.strings("close_menu"), "action": "close"}],
        ]

    @loader.owner
    @loader.command(
        ru_doc="Показать настройки",
        de_doc="Zeige die Einstellungen",
        tr_doc="Ayarları göster",
        uz_doc="Sozlamalarni ko'rsatish",
        ja_doc="設定を表示",
        kr_doc="설정 표시",
        ar_doc="إظهار الإعدادات",
        es_doc="Mostrar configuración",
    )
    async def settings(self, message: Message):
        """Show settings menu"""
        await self.inline.form(
            self.strings("inline_settings"),
            message=message,
            reply_markup=self._get_settings_markup(),
        )

    @loader.owner
    @loader.command(
        ru_doc="Открыть тоннель к веб-интерфейсу Hikka",
        de_doc="Öffne einen Tunnel zum Hikka Webinterface",
        tr_doc="Hikka Web Arayüzüne bir tünel aç",
        uz_doc="Hikka veb-interfeysi uchun tunel ochish",
        ja_doc="Hikka Webインターフェイスにトンネルを開く",
        kr_doc="Hikka 웹 인터페이스에 터널 열기",
        ar_doc="افتح نفقًا إلى واجهة Hikka الويب",
        es_doc="Abrir un túnel al interfaz web de Hikka",
    )
    async def weburl(self, message: Message, force: bool = False):
        """Opens web tunnel to your Hikka web interface"""
        if "LAVHOST" in os.environ:
            form = await self.inline.form(
                self.strings("lavhost_web"),
                message=message,
                reply_markup={
                    "text": self.strings("web_btn"),
                    "url": await main.hikka.web.get_url(proxy_pass=False),
                },
                gif="https://t.me/hikari_assets/28",
            )
            return

        if (
            not force
            and not message.is_private
            and "force_insecure" not in message.raw_text.lower()
        ):
            try:
                if not await self.inline.form(
                    self.strings("privacy_leak_nowarn").format(self._client.tg_id),
                    message=message,
                    reply_markup=[
                        {
                            "text": self.strings("btn_yes"),
                            "callback": self.weburl,
                            "args": (True,),
                        },
                        {"text": self.strings("btn_no"), "action": "close"},
                    ],
                    gif="https://i.gifer.com/embedded/download/Z5tS.gif",
                ):
                    raise Exception
            except Exception:
                await utils.answer(
                    message,
                    self.strings("privacy_leak").format(
                        self._client.tg_id,
                        self.get_prefix(),
                    ),
                )

            return

        if force:
            form = message
            await form.edit(
                self.strings("opening_tunnel"),
                reply_markup={"text": "🕔 Wait...", "data": "empty"},
                gif=(
                    "https://i.gifer.com/origin/e4/e43e1b221fd960003dc27d2f2f1b8ce1.gif"
                ),
            )
        else:
            form = await self.inline.form(
                self.strings("opening_tunnel"),
                message=message,
                reply_markup={"text": "🕔 Wait...", "data": "empty"},
                gif=(
                    "https://i.gifer.com/origin/e4/e43e1b221fd960003dc27d2f2f1b8ce1.gif"
                ),
            )

        url = await main.hikka.web.get_url(proxy_pass=True)

        await form.edit(
            self.strings("tunnel_opened"),
            reply_markup={"text": self.strings("web_btn"), "url": url},
            gif="https://t.me/hikari_assets/48",
        )

    @loader.loop(interval=1, autostart=True)
    async def loop(self):
        obj = self.allmodules.get_approved_channel
        if not obj:
            return

        channel, event = obj

        try:
            await self._client(JoinChannelRequest(channel))
        except Exception:
            logger.exception("Failed to join channel")
            event.status = False
            event.set()
        else:
            event.status = True
            event.set()

    def _get_all_IDM(self, module: str):
        return {
            getattr(getattr(self.lookup(module), name), "name", name): getattr(
                self.lookup(module), name
            )
            for name in dir(self.lookup(module))
            if getattr(getattr(self.lookup(module), name), "is_debug_method", False)
        }

    @loader.command()
    async def invoke(self, message: Message):
        """<module or `core` for built-in methods> <method> - Only for debugging purposes. DO NOT USE IF YOU'RE NOT A DEVELOPER
        """
        args = utils.get_args_raw(message)
        if not args or len(args.split()) < 2:
            await utils.answer(message, self.strings("no_args"))
            return

        module = args.split()[0]
        method = args.split(maxsplit=1)[1]

        if module != "core" and not self.lookup(module):
            await utils.answer(message, self.strings("module404").format(module))
            return

        if (
            module == "core"
            and method not in ALL_INVOKES
            or module != "core"
            and method not in self._get_all_IDM(module)
        ):
            await utils.answer(message, self.strings("invoke404").format(method))
            return

        message = await utils.answer(
            message, self.strings("invoking").format(method, module)
        )
        result = ""

        if module == "core":
            if method == "clear_entity_cache":
                result = (
                    f"Dropped {len(self._client._hikka_entity_cache)} cache records"
                )
                self._client._hikka_entity_cache = {}
            elif method == "clear_fulluser_cache":
                result = (
                    f"Dropped {len(self._client._hikka_fulluser_cache)} cache records"
                )
                self._client._hikka_fulluser_cache = {}
            elif method == "clear_fullchannel_cache":
                result = (
                    f"Dropped {len(self._client._hikka_fullchannel_cache)} cache"
                    " records"
                )
                self._client._hikka_fullchannel_cache = {}
            elif method == "clear_perms_cache":
                result = f"Dropped {len(self._client._hikka_perms_cache)} cache records"
                self._client._hikka_perms_cache = {}
            elif method == "clear_cache":
                result = (
                    f"Dropped {len(self._client._hikka_entity_cache)} entity cache"
                    " records\nDropped"
                    f" {len(self._client._hikka_fulluser_cache)} fulluser cache"
                    " records\nDropped"
                    f" {len(self._client._hikka_fullchannel_cache)} fullchannel cache"
                    " records"
                )
                self._client._hikka_entity_cache = {}
                self._client._hikka_fulluser_cache = {}
                self._client._hikka_fullchannel_cache = {}
            elif method == "reload_core":
                core_quantity = await self.lookup("loader").reload_core()
                result = f"Reloaded {core_quantity} core modules"
            elif method == "inspect_cache":
                result = (
                    "Entity cache:"
                    f" {len(self._client._hikka_entity_cache)} records\nFulluser cache:"
                    f" {len(self._client._hikka_fulluser_cache)} records\nFullchannel"
                    f" cache: {len(self._client._hikka_fullchannel_cache)} records"
                )
            elif method == "inspect_modules":
                result = (
                    "Loaded modules: {}\nLoaded core modules: {}\nLoaded user"
                    " modules: {}"
                ).format(
                    len(self.allmodules.modules),
                    sum(
                        module.__origin__.startswith("<core")
                        for module in self.allmodules.modules
                    ),
                    sum(
                        not module.__origin__.startswith("<core")
                        for module in self.allmodules.modules
                    ),
                )
        else:
            result = await self._get_all_IDM(module)[method](message)

        await utils.answer(
            message,
            self.strings("invoke").format(method, utils.escape_html(result)),
        )
