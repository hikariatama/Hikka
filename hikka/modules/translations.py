#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging

from telethon.tl.types import Message

from .. import loader, translations, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "it": "🇮🇹 Italiano",
    "de": "🇩🇪 Deutsch",
    "tr": "🇹🇷 Türkçe",
    "uz": "🇺🇿 O'zbekcha",
    "es": "🇪🇸 Español",
    "kk": "🇰🇿 Қазақша",
    "tt": "🥟 Татарча",
}


@loader.tds
class Translations(loader.Module):
    """Processes internal translations"""

    strings = {
        "name": "Translations",
        "lang_saved": "{} <b>Language saved!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Translate pack"
            " saved!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Incorrect language"
            " specified</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Translations reset"
            " to default ones</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Invalid pack format"
            " in url</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You need to specify"
            " valid url containing a langpack</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Command output seems"
            " to be too long, so it's sent in file.</b>"
        ),
        "opening_form": " <b>Opening form...</b>",
        "opening_gallery": " <b>Opening gallery...</b>",
        "opening_list": " <b>Opening list...</b>",
        "inline403": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You can't send inline"
            " units in this chat</b>"
        ),
        "invoke_failed": "<b>🚫 Unit invoke failed! More info in logs</b>",
        "show_inline_cmds": "📄 Show all available inline commands",
        "no_inline_cmds": "You have no available commands",
        "no_inline_cmds_msg": (
            "<b>😔 There are no available inline commands or you lack access to them</b>"
        ),
        "inline_cmds": "ℹ️ You have {} available command(-s)",
        "inline_cmds_msg": "<b>ℹ️ Available inline commands:</b>\n\n{}",
        "run_command": "🏌️ Run command",
        "command_msg": "<b>🌘 Command «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Command «{}»",
        "button403": "You are not allowed to press this button!",
        "keep_id": "⚠️ Do not remove ID! {}",
        "choose_language": "🗽 <b>Choose language</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>This language is not"
            " officially supported</b>"
        ),
        "requested_join": (
            "💫 <b>Module</b> <code>{}</code> <b>requested to join channel <a"
            " href='https://t.me/{}'>{}</a></b>\n\n<b>❓ Reason:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Call"
            "</b> <code>{}</code> <b>caused FloodWait of {} on method"
            "</b> <code>{}</code>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Call"
            "</b> <code>{}</code> <b>failed due to RPC error:</b>"
            " <code>{}</code>"
        ),
    }

    strings_ru = {
        "lang_saved": "{} <b>Язык сохранён!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Пакет переводов"
            " сохранён!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Указан неверный"
            " язык</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Переводы сброшены"
            " на стандартные</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Неверный формат"
            " пакета переводов в ссылке</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Вы должны указать"
            " ссылку, содержащую пакет переводов</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Вывод команды слишком"
            " длинный, поэтому он отправлен в файле.</b>"
        ),
        "opening_form": " <b>Открываю форму...</b>",
        "opening_gallery": " <b>Открываю галерею...</b>",
        "opening_list": " <b>Открываю список...</b>",
        "inline403": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Вы не можете"
            " отправлять встроенные элементы в этом чате</b>"
        ),
        "invoke_failed": "<b>🚫 Вызов модуля не удался! Подробнее в логах</b>",
        "show_inline_cmds": "📄 Показать все доступные встроенные команды",
        "no_inline_cmds": "У вас нет доступных inline команд",
        "no_inline_cmds_msg": (
            "<b>😔 Нет доступных inline команд или у вас нет доступа к ним</b>"
        ),
        "inline_cmds": "ℹ️ У вас {} доступная(-ых) команда(-ы)",
        "inline_cmds_msg": "<b>ℹ️ Доступные inline команды:</b>\n\n{}",
        "run_command": "🏌️ Выполнить команду",
        "command_msg": "<b>🌘 Команда «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Команда «{}»",
        "button403": "Вы не можете нажать на эту кнопку!",
        "keep_id": "⚠️ Не удаляйте ID! {}",
        "choose_language": "🗽 <b>Выберите язык</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Этот язык не"
            " поддерживается официально</b>"
        ),
        "requested_join": (
            "💫 <b>Модуль</b> <code>{}</code> <b>запросил присоединение к каналу <a"
            " href='https://t.me/{}'>{}</a></b>\n\n<b>❓ Причина:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Команда"
            "</b> <code>{}</code> <b>вызвал FloodWait {} в методе</b> <code> {}</code>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Команда"
            "</b> <code>{}</code> <b>не удалась из-за ошибки RPC:</b>"
            " <code>{}</code>"
        ),
    }

    strings_it = {
        "lang_saved": "{} <b>Lingua salvata!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Pacchetto di"
            " traduzione salvato!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Lingua specificata"
            " non corretta</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Traduzioni"
            " ripristinate</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Formato pacchetto di"
            " traduzione specificato errato</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Deve essere"
            " specificata un url contenente il pacchetto di traduzione</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Output della stringa"
            " troppo lungo, viene inviato in un file</b>"
        ),
        "opening_form": " <b>Apertura form...</b>",
        "opening_gallery": " <b>Apertura galleria...</b>",
        "opening_list": " <b>Apertura lista...</b>",
        "inline403": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Non puoi"
            " inviare inline in questo chat</b>"
        ),
        "invoke_failed": "<b>🚫 Invocazione modulo fallita! controlla i log</b>",
        "show_inline_cmds": "📄 Mostra tutti i comandi inline disponibili",
        "no_inline_cmds": "Non hai comandi inline disponibili",
        "no_inline_cmds_msg": (
            "<b>😔 Non hai comandi inline disponibili o non hai accesso a loro</b>"
        ),
        "inline_cmds": "ℹ️ Hai {} comando(-i) disponibili",
        "inline_cmds_msg": "<b>ℹ️ Comandi inline disponibili:</b>\n\n{}",
        "run_command": "🏌️ Esegui comando",
        "command_msg": "<b>🌘 Comando «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Comando «{}»",
        "button403": "Non puoi premere questo pulsante!",
        "keep_id": "⚠️ Non cancellare ID! {}",
        "choose_language": "🗽 <b>Scegli la lingua</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Questa lingua non"
            " è supportata ufficialmente</b>"
        ),
        "requested_join": (
            "💫 <b>Il modulo</b> <code>{}</code> <b>ha richiesto di unirsi al canale <a"
            " href='https://t.me/{}'>{}</a></b>\n\n<b>❓ Motivo:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Il comando</b>"
            " <code>{}</code> <b>ha causato un FloodWait di {} nel metodo</b> <code>"
            " {}</code>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Il comando"
            "</b> <code>{}</code> <b>non è riuscito a causa di un RPC error:</b>"
            " <code>{}</code>"
        ),
    }

    strings_de = {
        "lang_saved": "{} <b>Sprache gespeichert!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Übersetzungs"
            " Paket gespeichert!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Falsche Sprache"
            " angegeben</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Übersetzungen"
            " auf Standard zurückgesetzt</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ungültiges"
            " Übersetzungs Paket in der URL</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Sie müssen eine"
            " gültige URL angeben, die ein Übersetzungs Paket enthält</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Befehlsausgabe scheint"
            " zu lang zu sein, daher wird sie in einer Datei gesendet.</b>"
        ),
        "opening_form": " <b>Formular wird geöffnet...</b>",
        "opening_gallery": " <b>Galerie wird geöffnet...</b>",
        "opening_list": " <b>Liste wird geöffnet...</b>",
        "inline403": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Sie können"
            " Inline-Einheiten in diesem Chat nicht senden</b>"
        ),
        "invoke_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modulaufruf"
            " fehlgeschlagen! Weitere Informationen in den Protokollen</b>"
        ),
        "show_inline_cmds": "📄 Zeige alle verfügbaren Inline-Befehle",
        "no_inline_cmds": "Sie haben keine verfügbaren Inline-Befehle",
        "no_inline_cmds_msg": (
            "<b>😔 Keine verfügbaren Inline-Befehle oder Sie haben keinen Zugriff"
            " auf sie</b>"
        ),
        "inline_cmds": "ℹ️ Sie haben {} verfügbare(n) Befehl(e)",
        "inline_cmds_msg": "<b>ℹ️ Verfügbare Inline-Befehle:</b>\n\n{}",
        "run_command": "🏌️ Befehl ausführen",
        "command_msg": "<b>🌘 Befehl «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Befehl «{}»",
        "button403": "Sie können auf diese Schaltfläche nicht klicken!",
        "keep_id": "⚠️ Löschen sie das ID nicht! {}",
        "choose_language": "🗽 <b>Wählen Sie eine Sprache</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Diese Sprache wird"
            " nicht offiziell unterstützt</b>"
        ),
        "requested_join": (
            "💫 <b>Modul</b> <code>{}</code> <b>hat den Beitritt zum Kanal <a"
            " href='https://t.me/{}'>{}</a> angefordert</b>\n\n<b>❓ Grund:"
            "</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Befehl"
            "</b> <code>{}</code> <b>hat FloodWait {} in der Methode"
            "</b> <code>{}</code>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Befehl"
            "</b> <code>{}</code> <b>ist fehlgeschlagen wegen RPC-Fehler"
            ":</b> <code>{}</code>"
        ),
    }

    strings_tr = {
        "lang_saved": "{} <b>Dil kaydedildi!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Çeviri paketi"
            " kaydedildi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Yanlış dil"
            " belirtildi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Çeviriler varsayılan"
            " hale getirildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>URL'deki çeviri"
            " paketi geçersiz</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Geçerli bir dil paketi"
            " içeren URL belirtmelisiniz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Komut çıktısı çok uzun"
            " görünüyor, bu yüzden dosya olarak gönderildi.</b>"
        ),
        "opening_form": " <b>Form açılıyor...</b>",
        "opening_gallery": " <b>Galeri açılıyor...</b>",
        "opening_list": " <b>Liste açılıyor...</b>",
        "inline403": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bu sohbete satır içi"
            " birimler gönderemezsin</b>"
        ),
        "invoke_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modül çağrısı"
            " başarısız! Kayıtlardan daha fazla bilgiye erişebilirsin</b>"
        ),
        "show_inline_cmds": "📄 Tüm kullanılabilir satır içi komutlarını göster",
        "no_inline_cmds": "Kullanılabilir satır içi komutunuz yok",
        "no_inline_cmds_msg": (
            "<b>😔 Kullanılabilir satır içi komutunuz yok veya erişiminiz yok</b>"
        ),
        "inline_cmds": "ℹ️ {} adet kullanılabilir komutunuz var",
        "inline_cmds_msg": "<b>ℹ️ Kullanılabilir satır içi komutlar:</b>\n\n{}",
        "run_command": "🏌️ Komutu çalıştır",
        "command_msg": "<b>🌘 Komut «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Komut «{}»",
        "button403": "Bu düğmeye basamazsınız!",
        "keep_id": "⚠️ ID'yi silmeyin! {}",
        "choose_language": "🗽 <b>Bir dil seçin</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Bu dil resmi olarak"
            " desteklenmiyor</b>"
        ),
        "requested_join": (
            "💫 <b>Modül</b> <code>{}</code> <b><a href='https://t.me/{}'>{}</a>"
            " kanalına katılma isteği gönderdi</b>\n\n<b>❓ Sebep:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Komut"
            "</b> <code>{}</code> <b>FloodWait {} nedeniyle</b> <code>{}</code><b>"
            " yönteminde başarısız oldu</b>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Komut"
            "</b> <code>{}</code> <b>RPC hatası nedeniyle başarısız"
            " oldu:</b> <code>{}</code>"
        ),
    }

    strings_uz = {
        "lang_saved": "{} <b>Til saqlandi!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Tarjima paketi"
            " saqlandi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Noto'g'ri til"
            " belgilandi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Tarjimalar"
            " standart holatga qaytarildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>URL'dagi tarjima"
            " paketi noto'g'ri</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Siz noto'g'ri URL"
            " belirtdingiz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Bajarilgan buyruq"
            " natijasi juda uzun, shuning uchun fayl sifatida yuborildi.</b>"
        ),
        "opening_form": " <b>Formani ochish...</b>",
        "opening_gallery": " <b>Galeriyani ochish...</b>",
        "opening_list": " <b>Ro'yxatni ochish...</b>",
        "inline403": (
            "🚫 <b>Siz bu guruhda inline obyektlarni yuborishingiz mumkin emas</b>"
        ),
        "invoke_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Modulni chaqirish"
            " muvaffaqiyatsiz! Batafsil ma'lumotlar jurnallarda</b>"
        ),
        "show_inline_cmds": "📄 Barcha mavjud inline buyruqlarini ko'rsatish",
        "no_inline_cmds": "Sizda mavjud inline buyruqlar yo'q",
        "no_inline_cmds_msg": (
            "<b>😔 Sizda mavjud inline buyruqlar yo'q yoki ularga kirish huquqingiz"
            " yo'q</b>"
        ),
        "inline_cmds": "ℹ️ Sizda {} mavjud buyruq bor",
        "inline_cmds_msg": "<b>ℹ️ Mavjud inline buyruqlar:</b>\n\n{}",
        "run_command": "🏌️ Buyruqni bajarish",
        "command_msg": "<b>🌘 Buyruq «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Buyruq «{}»",
        "button403": "Siz ushbu tugmani bosib bo'lmaysiz!",
        "keep_id": "⚠️ ID-ni o'chirmang! {}",
        "choose_language": "🗽 <b>Tilni tanlang</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Ushbu til"
            " rasmiylashtirilmagan</b>"
        ),
        "requested_join": (
            "💫 <b>Modul</b> <code>{}</code> <b><a href='https://t.me/{}'>{}</a>"
            " guruhiga qo'shilish so'rovi yubordi</b>\n\n<b>❓ Sababi:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Buyruq"
            "</b> <code>{}</code> <b>FloodWait {} sababli</b> <code>{}</code> <b>usuli"
            " bilan muvaffaqiyatsiz bo'ldi</b>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Buyruq"
            "</b> <code>{}</code> <b>RPC xatosi sababli muvaffaqiyatsiz"
            " bo'ldi:</b> <code>{}</code>"
        ),
    }

    strings_es = {
        "lang_saved": "{} <b>¡Idioma guardado!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>¡Paquete de"
            " traducción guardado!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Idioma"
            " incorrecto seleccionado</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Restablecer la"
            " traducción a los valores predeterminados</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Paquete de"
            " traducción seleccionado incorrecto</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>URL incorrecta"
            " seleccionada</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>El resultado del"
            " comando excede el límite. Enviado como archivo.</b>"
        ),
        "opening_form": " <b>Abriendo formulario...</b>",
        "opening_gallery": " <b>Abriendo galería...</b>",
        "opening_list": " <b>Abriendo lista...</b>",
        "inline403": (
            "🚫 <b>No se permiten elementos de interfaz de usuario en este grupo</b>"
        ),
        "invoke_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>¡Error al invocar la"
            " unidad! Consulte el registro para obtener más detalles</b>"
        ),
        "show_inline_cmds": "📄 Mostrar todos los comandos disponibles",
        "no_inline_cmds": "No hay comandos disponibles",
        "no_inline_cmds_msg": (
            "<b>😔 No hay comandos disponibles o no tienes permiso para acceder a"
            " los comandos</b>"
        ),
        "inline_cmds": "ℹ️ {} comandos disponibles",
        "inline_cmds_msg": "<b>ℹ️ Comandos disponibles:</b>\n\n{}",
        "run_command": "🏌️ Ejecutar comando",
        "command_msg": "<b>🌘 Comando '{}'</b>\n\n<i>{}</i>",
        "command": "🌘 Comando '{}'",
        "button403": "¡No puedes presionar este botón!",
        "button404": "¡No puedes presionar este botón ahora!",
        "keep_id": "⚠️ ¡No elimines el ID! {}",
        "choose_language": "🗽 <b>Elige un idioma</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Este idioma no está"
            " oficialmente respaldado</b>"
        ),
        "requested_join": (
            "💫 <b>El módulo</b> <code>{}</code> <b><a href='https://t.me/{}'>{}</a>"
            " solicitó unirse al grupo</b>\n\n<b>❓ Razón:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>El comando"
            "</b> <code>{}</code> <b>falló debido a FloodWait {}:</b> <code>{}</code>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>El comando"
            "</b> <code>{}</code> <b>falló debido a un error RPC:</b>"
            " <code>{}</code>"
        ),
    }

    strings_kk = {
        "lang_saved": "{} <b>Тіл сақталды!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Аударма пакеті"
            " сақталды!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Жарамсыз тіл"
            " белгіленді</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Аударма пакеті"
            " өшірілді</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Аударма пакеті"
            " сілтемесінің пішімі жарамсыз</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Сіз аударма пакеті"
            " бар сілтемені көрсетуіңіз керек</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Команда жауап"
            " өте ұзын, ол файлда жіберілді.</b>"
        ),
        "opening_form": " <b>Форманы ашу...</b>",
        "opening_gallery": " <b>Галереяны ашу...</b>",
        "opening_list": " <b>Тізімні ашу...</b>",
        "inline403": (
            "🚫 <b>Сіз бұл сөйлесуде кірістірілген элементтерді жібере алмайсыз</b>"
        ),
        "invoke_failed": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Модульді іске қосу"
            " сәтсіз аяқталды! Толығырақ құжаттың журналында</b>"
        ),
        "show_inline_cmds": "📄 Барлық қол жетімді кірістірілген командаларды көрсету",
        "no_inline_cmds": "Сіздің қол жетімді inline командаларыңыз жоқ",
        "no_inline_cmds_msg": (
            "<b>😔 Қол жетімді inline командалар жоқ немесе Сізге оларға қатынасуға"
            " рұқсат жоқ</b>"
        ),
        "inline_cmds": "ℹ️ Сіздің {} қол жетімді команда(-лар)ыңыз бар",
        "inline_cmds_msg": "<b>ℹ️ Қол жетімді inline командалар:</b>\n\n{}",
        "run_command": "🏌️ Команданы іске қосу",
        "command_msg": "<b>🌘 «{}» командасы</b>\n\n<i>{}</i>",
        "command": "🌘 «{}» командасы",
        "button403": "Сіз бұл түймешіге баса алмайсыз!",
        "keep_id": "⚠️ ID тастамаңыз! {}",
        "choose_language": "🗽 <b>Тілді таңдаңыз</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Бұл тіл официалдықтың"
            " тағы да қолдауы көрсетілмейді</b>"
        ),
        "requested_join": (
            "💫 <b>Модуль</b> <code>{}</code> <b><a href='https://t.me/{}'>{}< арнаға"
            " қосылуды сұрады. /a></b>\n\n<b>❓ Себебі:</b> <i>{}</i>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Команда"
            "</b> <code>{}</code> <b>{} секундтан кейін қайталап көрінеді</b>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Команда"
            "</b> <code>{}</code> <b>RPC қатесінен қате орындалды:</b>"
            " <code>{}</code>"
        ),
    }

    strings_tt = {
        "lang_saved": "{} <b>Тел сакланган!</b>",
        "pack_saved": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Тәрҗемә пакеты"
            " сакланган!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Дөрес булмаган тел"
            " күрсәтелгән</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Тәрҗемәләр стандартка"
            " ташланган</b>"
        ),
        "check_pack": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Сылтамада тәрҗемә"
            " пакетларының дөрес булмаган форматы</b>"
        ),
        "check_url": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Сез тәрҗемә пакеты"
            " булган сылтаманы кертергә тиеш/b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Команда чыгышы бик"
            " озын, шуңа күрә ул файлда җибәрелә.</b>"
        ),
        "opening_form": " <b>Мин форманы ачам...</b>",
        "opening_gallery": " <b>Мин галереяны ачам...</b>",
        "opening_list": " <b>Исемлекне ачу...</b>",
        "inline403": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Сез бу чатта"
            " урнаштырылган элементларны җибәрә алмыйсыз</b>"
        ),
        "invoke_failed": "<b>🚫 Модуль проблемасы уңышлы булмады! Логларда тулырак</b>",
        "show_inline_cmds": "📄 Барлык урнаштырылган командаларны күрсәтегез",
        "no_inline_cmds": "Сезнең inline командаларыгыз юк",
        "no_inline_cmds_msg": (
            "<b>😔 Inline командалар юк яисә аларга керү мөмкинлеге юк</b>"
        ),
        "inline_cmds": "ℹ️ Сездә {} уңайлы командалар бар",
        "inline_cmds_msg": "<b>ℹ️ Inline командалар:</b>\n\n{}",
        "run_command": "🏌️ Команданы үтәгез",
        "command_msg": "<b>🌘 Команда «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Команда «{}»",
        "button403": "Сез төймәгә баса алмыйсыз!",
        "keep_id": "⚠️ ID'ны бетеремэгез {}",
        "choose_language": "🗽 <b>Телне таңдаңыз</b>",
        "not_official": (
            "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Бу тел официалдықтың"
            " тағы да қолдауы көрсетілмейді</b>"
        ),
        "fw_error": (
            "<emoji document_id=5877458226823302157>🕒</emoji> <b>Команда"
            "</b> <code>{}</code> <b>FloodWait {} методына туры"
            " килде</b><code>{}</code>"
        ),
        "rpc_error": (
            "<emoji document_id=5877477244938489129>🚫</emoji> <b>Команда"
            "</b> <code>{}</code> <b>RPC хатасынан баш тартылды:</b>"
            " <code>{}</code>"
        ),
    }

    async def _change_language(self, call: InlineCall, lang: str):
        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.edit(self.strings("lang_saved").format(self._get_flag(lang)))

    def _get_flag(self, lang: str) -> str:
        emoji_flags = {
            "🇬🇧": "<emoji document_id=6323589145717376403>🇬🇧</emoji>",
            "🇺🇿": "<emoji document_id=6323430017179059570>🇺🇿</emoji>",
            "🇷🇺": "<emoji document_id=6323139226418284334>🇷🇺</emoji>",
            "🇮🇹": "<emoji document_id=6323471399188957082>🇮🇹</emoji>",
            "🇩🇪": "<emoji document_id=6320817337033295141>🇩🇪</emoji>",
            "🇪🇸": "<emoji document_id=6323315062379382237>🇪🇸</emoji>",
            "🇹🇷": "<emoji document_id=6321003171678259486>🇹🇷</emoji>",
            "🇰🇿": "<emoji document_id=6323135275048371614>🇰🇿</emoji>",
            "🥟": "<emoji document_id=5382337996123020810>🥟</emoji>",
        }

        lang2country = {"en": "🇬🇧", "tt": "🥟", "kk": "🇰🇿"}

        lang = lang2country.get(lang) or utils.get_lang_flag(lang)
        return emoji_flags.get(lang, lang)

    @loader.command(
        ru_doc="[языки] - Изменить стандартный язык",
        it_doc="[lingue] - Cambia la lingua predefinita",
        de_doc="[Sprachen] - Ändere die Standard-Sprache",
        tr_doc="[Diller] - Varsayılan dili değiştir",
        uz_doc="[til] - Standart tili o'zgartirish",
        es_doc="[Idiomas] - Cambiar el idioma predeterminado",
        kk_doc="[тілдер] - Бастапқы тілді өзгерту",
    )
    async def setlang(self, message: Message):
        """[languages in the order of priority] - Change default language"""
        args = utils.get_args_raw(message)
        if not args:
            await self.inline.form(
                message=message,
                text=self.strings("choose_language"),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": text,
                            "callback": self._change_language,
                            "args": (lang,),
                        }
                        for lang, text in SUPPORTED_LANGUAGES.items()
                    ],
                    2,
                ),
            )
            return

        if any(len(i) != 2 for i in args.split(" ")):
            await utils.answer(message, self.strings("incorrect_language"))
            return

        self._db.set(translations.__name__, "lang", args.lower())
        await self.allmodules.reload_translations()

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                "".join([self._get_flag(lang) for lang in args.lower().split()])
            )
            + (
                ("\n\n" + self.strings("not_official"))
                if any(lang not in SUPPORTED_LANGUAGES for lang in args.lower().split())
                else ""
            ),
        )

    @loader.command(
        ru_doc="[ссылка на пак | пустое чтобы удалить] - Изменить внешний пак перевода",
        it_doc=(
            "[link al pacchetto | vuoto per rimuovere] - Cambia il pacchetto di"
            " traduzione esterno"
        ),
        de_doc=(
            "[Link zum Paket | leer um zu entfernen] - Ändere das externe Übersetzungs"
            " Paket"
        ),
        tr_doc=(
            "[Çeviri paketi bağlantısı | boş bırakmak varsayılan hale getirir] - Harici"
            " çeviri paketini değiştir"
        ),
        uz_doc=(
            "[tarjima paketi havolasini | bo'sh qoldirish standart holatga qaytaradi] -"
            " Tashqi tarjima paketini o'zgartirish"
        ),
        es_doc="[Enlace al paquete | vacío para eliminar] - Cambiar el paquete de",
        kk_doc=(
            "[тілдік пакеттің сілтемесі | бос қалдырып бастапқы қалдыру] - Сыртқы"
            " тілдік пакетін өзгерту"
        ),
    )
    async def dllangpackcmd(self, message: Message):
        """[link to a langpack | empty to remove] - Change Hikka translate pack (external)
        """
        args = utils.get_args_raw(message)

        if not args:
            self._db.set(translations.__name__, "pack", False)
            await self.translator.init()
            await utils.answer(message, self.strings("lang_removed"))
            return

        if not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        self._db.set(translations.__name__, "pack", args)
        await utils.answer(
            message,
            self.strings(
                "pack_saved"
                if await self.allmodules.reload_translations()
                else "check_pack"
            ),
        )
