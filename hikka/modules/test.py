#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import inspect
import logging
import os
import random
import time
import typing
from io import BytesIO

from telethon.tl.types import Message

from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

DEBUG_MODS_DIR = os.path.join(utils.get_base_dir(), "debug_modules")

if not os.path.isdir(DEBUG_MODS_DIR):
    os.mkdir(DEBUG_MODS_DIR, mode=0o755)

for mod in os.scandir(DEBUG_MODS_DIR):
    os.remove(mod.path)


@loader.tds
class TestMod(loader.Module):
    """Perform operations based on userbot self-testing"""

    _memory = {}

    strings = {
        "name": "Tester",
        "set_loglevel": "🚫 <b>Please specify verbosity as an integer or string</b>",
        "no_logs": "ℹ️ <b>You don't have any logs at verbosity {}.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka logs with"
            " verbosity </b><code>{}</code>\n\n<emoji"
            " document_id=5454390891466726015>👋</emoji> <b>Hikka version:"
            " {}.{}.{}</b>{}\n<emoji document_id=6321050180095313397>⏱</emoji>"
            " <b>Uptime: {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{}"
            " InlineLogs</b>"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Invalid time to"
            " suspend</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot suspended"
            " for</b> <code>{}</code> <b>seconds</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Telegram ping:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>Uptime: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram ping mostly"
            " depends on Telegram servers latency and other external factors and has"
            " nothing to do with the parameters of server on which userbot is"
            " installed</i>"
        ),
        "confidential": (
            "⚠️ <b>Log level </b><code>{}</code><b> may reveal your confidential info,"
            " be careful</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Log level </b><code>{0}</code><b> may reveal your confidential info,"
            " be careful</b>\n<b>Type </b><code>.logs {0} force_insecure</code><b> to"
            " ignore this warning</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Choose log level</b>",
        "bad_module": "🚫 <b>Module not found</b>",
        "debugging_enabled": (
            "🧑‍💻 <b>Debugging mode enabled for module </b><code>{0}</code>\n<i>Go to"
            " directory named `debug_modules`, edit file named `{0}.py` and see changes"
            " in real time</i>"
        ),
        "debugging_disabled": "✅ <b>Debugging disabled</b>",
        "send_anyway": "📤 Send anyway",
        "cancel": "🚫 Cancel",
    }

    strings_ru = {
        "set_loglevel": "🚫 <b>Укажи уровень логов числом или строкой</b>",
        "no_logs": "ℹ️ <b>У тебя нет логов уровня {}.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Логи Hikka уровня"
            " </b><code>{}</code>\n\n<emoji document_id=5454390891466726015>👋</emoji>"
            " <b>Версия Hikka: {}.{}.{}</b>{}\n<emoji"
            " document_id=6321050180095313397>⏱</emoji> <b>Uptime:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{}"
            " InlineLogs</b>"
        ),
        "bad_module": "🚫 <b>Модуль не найден</b>",
        "debugging_enabled": (
            "🧑‍💻 <b>Режим разработчика включен для модуля"
            " </b><code>{0}</code>\n<i>Отправляйся в директорию `debug_modules`,"
            " изменяй файл `{0}.py`, и смотри изменения в режиме реального времени</i>"
        ),
        "debugging_disabled": "✅ <b>Режим разработчика выключен</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Неверное время"
            " заморозки</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Бот заморожен на</b>"
            " <code>{}</code> <b>секунд</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Скорость отклика"
            " Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>Прошло с последней"
            " перезагрузки: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Скорость отклика"
            " Telegram в большей степени зависит от загруженности серверов Telegram и"
            " других внешних факторов и никак не связана с параметрами сервера, на"
            " который установлен юзербот</i>"
        ),
        "confidential": (
            "⚠️ <b>Уровень логов </b><code>{}</code><b> может содержать личную"
            " информацию, будь осторожен</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Уровень логов </b><code>{0}</code><b> может содержать личную"
            " информацию, будь осторожен</b>\n<b>Напиши </b><code>.logs {0}"
            " force_insecure</code><b>, чтобы отправить логи игнорируя"
            " предупреждение</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Выбери уровень логов</b>",
        "_cmd_doc_dump": "Показать информацию о сообщении",
        "_cmd_doc_logs": (
            "<уровень> - Отправляет лог-файл. Уровни ниже WARNING могут содержать"
            " личную инфомрацию."
        ),
        "_cmd_doc_suspend": "<время> - Заморозить бота на некоторое время",
        "_cmd_doc_ping": "Проверяет скорость отклика юзербота",
        "_cls_doc": "Операции, связанные с самотестированием",
        "send_anyway": "📤 Все равно отправить",
        "cancel": "🚫 Отмена",
    }

    strings_de = {
        "set_loglevel": (
            "🚫 <b>Geben Sie die Protokollebene als Zahl oder Zeichenfolge an</b>"
        ),
        "no_logs": "ℹ️ <b>Du hast kein Protokollnachrichten des {} Ebene.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka-Level-Protokolle"
            " </b><code>{}</code>\n\n<emoji document_id=5454390891466726015>👋</emoji>"
            " <b>Hikka-Version: {}.{}.{}</b>{}\n<Emoji"
            "document_id=6321050180095313397>⏱</emoji> <b>Verfügbarkeit:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "bad_module": "🚫 <b>Modul nicht gefunden</b>",
        "debugging_enabled": (
            (
                "🧑‍💻 <b>Entwicklermodus für Modul aktiviert"
                " </b><code>{0}</code>\n<i>Gehe zum Verzeichnis `debug_modules`"
            ),
            (
                "Ändern Sie die `{0}.py`-Datei und sehen Sie sich die Änderungen in"
                " Echtzeit an</i>"
            ),
        ),
        "debugging_disabled": "✅ <b>Entwicklermodus deaktiviert</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Falsche Zeit"
            "einfrieren</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot ist"
            " eingefroren</b> <code>{}</code> <b>Sekunden</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Reaktionszeit des"
            " Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>Zeit seit dem letzten"
            " Neustart: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji>"
            " <i>ReaktionsfähigkeitTelegram ist stärker abhängig von der Auslastung der"
            " Telegram-Server undAndere externe Faktoren und steht in keinem"
            " Zusammenhang mit den Servereinstellungen welcher Userbot installiert"
            " ist</i>"
        ),
        "confidential": (
            "⚠️ <b>Protokollebene </b><code>{}</code><b> kann privat enthalten"
            "Informationen, seien Sie vorsichtig</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Protokollebene </b><code>{0}</code><b> kann privat"
            " enthaltenInformationen, seien Sie vorsichtig</b>\n<b>Schreiben Sie"
            " </b><code>.logs {0} force_insecure</code><b> um Protokolle zu"
            " ignorierenWarnung</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Wähle eine Protokollebene</b>",
        "_cmd_doc_dump": "Nachrichteninformationen anzeigen",
        "_cmd_doc_logs": (
            "<Ebene> - Sendet eine Protokolldatei. Ebenen unterhalb von WARNUNG können"
            " enthaltenpersönliche Informationen."
        ),
        "_cmd_doc_suspend": "<Zeit> - Bot für eine Weile einfrieren",
        "_cmd_doc_ping": "Überprüft die Antwortgeschwindigkeit des Userbots",
        "_cls_doc": "Selbsttestbezogene Operationen",
        "send_anyway": "📤 Trotzdem senden",
        "cancel": "🚫 Abbrechen",
    }

    strings_uz = {
        "set_loglevel": "🚫 <b>Log darajasini raqam yoki satr sifatida ko'rsating</b>",
        "no_logs": "ℹ️ <b>Siz {} darajadagi hech qanday loglaringiz yo'q.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka Loglari"
            " </b><code>{}</code>\n\n<emoji document_id=5454390891466726015>👋</emoji>"
            " <b>Hikka-versiyasi: {}.{}.{}</b>{}\n<Emoji"
            "document_id=6321050180095313397>⏱</emoji> <b>Mavjudligi:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "bad_module": "🚫 <b>Modul topilmadi</b>",
        "debugging_enabled": (
            (
                "🧑‍💻 <b>Modul uchun ishlab chiqarish rejimi yoqildi"
                " </b><code>{0}</code>\n<i>`debug_modules` papkasiga o'ting"
            ),
            "`{0}.py` faylini o'zgartiring va o'zgarishlarni reallaqam ko'ring</i>",
        ),
        "debugging_disabled": "✅ <b>Ishtirok rejimi o'chirildi</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Noto'g'ri vaqt"
            "qo'ymoq</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot chiqarildi</b>"
            " <code>{}</code> <b>Soniyalar</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Telegram tezligi:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>Soʻngi marotaba qayta ishga"
            " tushirilgan vaqti:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram"
            " tezligiTelegram serverlarining ishga tushishi va boshqa tashqi"
            " faktorlariga bog'liq va Userbot o'rnatilgan serverlarining sozlamalari"
            " bilan bog'liq emas</i>"
        ),
        "confidential": (
            "⚠️ <b>Log darajasi </b><code>{}</code><b> shaxsiy ma'lumotlarga ega"
            " bo'lishi mumkinO'zingizni xavfsizligi uchun</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Log darajasi </b><code>{0}</code><b> shaxsiy ma'lumotlarga ega"
            " bo'lishi mumkinO'zingizni xavfsizligi uchun</b>\n<b>Yozing"
            " </b><code>.logs {0} force_insecure</code><b> loglarniOgohlantirish</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Log darajasini tanlang</b>",
        "_cmd_doc_dump": "Xabar haqida ma'lumotlarni ko'rsatish",
        "_cmd_doc_logs": (
            "<Ebene> - Log faylini yuboradi. O'rin darajalari xavfsizlikma'lumotlar."
        ),
        "_cmd_doc_suspend": "<Vaqt> - Botni bir necha vaqtga o'chirish",
        "_cmd_doc_ping": "Userbotning javob berish tezligini tekshirish",
        "_cls_doc": "O'z testi bilan bog'liq operatsiyalar",
        "send_anyway": "📤 Baribir yuborish",
        "cancel": "🚫 Bekor qilish",
    }

    strings_tr = {
        "set_loglevel": (
            "🚫 <b>Lütfen günlük seviyesini sayı veya dize olarak belirtin</b>"
        ),
        "no_logs": "ℹ️ <b>Hiçbir {} seviyesindeki günlük bulunmuyor.</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka Günlükleri"
            " </b><code>{}</code>\n\n<emoji document_id=5454390891466726015>👋</emoji>"
            " <b>Hikka versiyası: {}.{}.{}</b>{}\n<Emoji"
            "document_id=6321050180095313397>⏱</emoji> <b>Süre:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "bad_module": "🚫 <b>Modül bulunamadı</b>",
        "debugging_enabled": (
            (
                "🧑‍💻 <b>Geliştirme modu modül için etkinleştirildi"
                " </b><code>{0}</code>\n<i>`debug_modules` klasörüne gidin"
            ),
            (
                "`{0}.py` dosyasını düzenleyin ve değişiklikleri gerçekleştirmek için"
                " kaydedin</i>"
            ),
        ),
        "debugging_disabled": "✅ <b>Geliştirme modu devre dışı bırakıldı</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Geçersiz zaman"
            "girdiniz</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot donduruldu</b>"
            " <code>{}</code> <b>saniye</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Telegramhızı:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>Son güncellemeden"
            " sonra:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram hızı"
            "Telegram sunucularının başlatılması ve diğer dış faktörler ile alakalıdır"
            "ve Userbot kurulumunuzun sunucu ayarlarıyla alakalı değildir</i>"
        ),
        "confidential": (
            "⚠️ <b>Günlük seviyesi </b><code>{}</code><b> gizli bilgilere sahip"
            " olabilirKendi güvenliğiniz için</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Günlük seviyesi </b><code>{0}</code><b> gizli bilgilere sahip"
            " olabilirKendi güvenliğiniz için</b>\n<b>Yazın </b><code>.logs {0}"
            " force_insecure</code><b> günlükleriuyarı</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Lütfen günlük seviyesini seçin</b>",
        "_cmd_doc_dump": "Mesaj hakkında bilgi göster",
        "_cmd_doc_logs": (
            "<Ebene> - Günlük dosyasını gönderir. Seviyeler gizlibilgiler."
        ),
        "_cmd_doc_suspend": "<Zaman> - Botu bir süreliğine dondurun",
        "_cmd_doc_ping": "Userbotun yanıt verme hızını kontrol edin",
        "_cls_doc": "İlgili testlerle ilgili işlemler",
        "send_anyway": "📤 Gönder",
        "cancel": "🚫 İptal",
    }

    strings_es = {
        "debugging_enabled": "✅ <b>Depuración habilitada</b>",
        "debugging_disabled": "✅ <b>Depuración deshabilitada</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Ingrese"
            "el tiempo correcto</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot"
            "suspendido</b> <code>{}</code> <b>segundos</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Velocidad"
            "de Telegram:</b> <code>{}</code> <b>milisegundos</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>Desde el último"
            "actualización:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>La velocidad"
            "de Telegram no es el tiempo que toma en responder el bot a los mensajes"
            "pero es el tiempo que toma en responder a tus mensajes desde que"
            "el bot se inició y no por cualquier otra razón externa"
            "como la configuración de tu bot</i>"
        ),
        "confidential": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Tiempo:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "confidential_text": (
            "⚠️ <b>El nivel de registro </b><code>{0}</code><b>contiene"
            "información confidencial y por lo tanto</b>\n<b>escribe</b><code>.logs {0}"
            "force_insecure</code><b>para enviar los registros"
            "información confidencial</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Elige el nivel de registro</b>",
        "_cmd_doc_dump": "Mostrar información del mensaje",
        "_cmd_doc_logs": (
            "<nivel> - Envía archivos de registro. Los niveles ocultos no se"
            " notificarán."
        ),
        "_cmd_doc_suspend": "<tiempo> - Suspende el bot temporalmente",
        "_cmd_doc_ping": "Verifique la velocidad del bot",
        "_cls_doc": "Se ejecutaron pruebas relacionadas",
        "send_anyway": "📤 Enviar de todos modos",
        "cancel": "🚫 Cancelar",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "force_send_all",
                False,
                "⚠️ Do not touch, if you don't know what it does!\nBy default, Hikka"
                " will try to determine, which client caused logs. E.g. there is a"
                " module TestModule installed on Client1 and TestModule2 on Client2. By"
                " default, Client2 will get logs from TestModule2, and Client1 will get"
                " logs from TestModule. If this option is enabled, Hikka will send all"
                " logs to Client1 and Client2, even if it is not the one that caused"
                " the log.",
                validator=loader.validators.Boolean(),
                on_change=self._pass_config_to_logger,
            ),
            loader.ConfigValue(
                "tglog_level",
                "INFO",
                "⚠️ Do not touch, if you don't know what it does!\n"
                "Minimal loglevel for records to be sent in Telegram.",
                validator=loader.validators.Choice(
                    ["INFO", "WARNING", "ERROR", "CRITICAL"]
                ),
                on_change=self._pass_config_to_logger,
            ),
        )

    def _pass_config_to_logger(self):
        logging.getLogger().handlers[0].force_send_all = self.config["force_send_all"]
        logging.getLogger().handlers[0].tg_level = {
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }[self.config["tglog_level"]]

    @loader.command(
        ru_doc="Ответь на сообщение, чтобы показать его дамп",
        de_doc="Antworten Sie auf eine Nachricht, um ihren Dump anzuzeigen",
        tr_doc="Dökümünü göstermek için bir iletiyi yanıtlayın",
        uz_doc="Xabarning axlatini ko'rsatish uchun unga javob bering",
        es_doc="Responde a un mensaje para mostrar su volcado",
    )
    async def dump(self, message: Message):
        """Use in reply to get a dump of a message"""
        if not message.is_reply:
            return

        await utils.answer(
            message,
            "<code>"
            + utils.escape_html((await message.get_reply_message()).stringify())
            + "</code>",
        )

    @loader.loop(interval=1)
    async def watchdog(self):
        if not os.path.isdir(DEBUG_MODS_DIR):
            return

        try:
            for module in os.scandir(DEBUG_MODS_DIR):
                last_modified = os.stat(module.path).st_mtime
                cls_ = module.path.split("/")[-1].split(".py")[0]

                if cls_ not in self._memory:
                    self._memory[cls_] = last_modified
                    continue

                if self._memory[cls_] == last_modified:
                    continue

                self._memory[cls_] = last_modified
                logger.debug("Reloading debug module %s", cls_)
                with open(module.path, "r") as f:
                    try:
                        await next(
                            module
                            for module in self.allmodules.modules
                            if module.__class__.__name__ == "LoaderMod"
                        ).load_module(
                            f.read(),
                            None,
                            save_fs=False,
                        )
                    except Exception:
                        logger.exception("Failed to reload module in watchdog")
        except Exception:
            logger.exception("Failed debugging watchdog")
            return

    @loader.command(
        ru_doc=(
            "[модуль] - Для разработчиков: открыть модуль в режиме дебага и применять"
            " изменения из него в режиме реального времени"
        ),
        de_doc=(
            "[Modul] - Für Entwickler: Öffnet ein Modul im Debug-Modus und"
            " wendet Änderungen aus ihm in Echtzeit an"
        ),
        uz_doc=(
            "[modul] - Dasturchaklar uchun: modulni debug rejimida ochib, va uni"
            " real vaqtda ishga tushirish"
        ),
        tr_doc=(
            "[modul] - Geliştiriciler için: Bir modülü debug modunda açar ve"
            " değişiklikleri gerçek zamanlı uygular"
        ),
        es_doc=(
            "[módulo] - Para desarrolladores: abre un módulo en modo de depuración y"
            " aplica los cambios de él en tiempo real"
        ),
    )
    async def debugmod(self, message: Message):
        """[module] - For developers: Open module for debugging
        You will be able to track changes in real-time"""
        args = utils.get_args_raw(message)
        instance = None
        for module in self.allmodules.modules:
            if (
                module.__class__.__name__.lower() == args.lower()
                or module.strings["name"].lower() == args.lower()
            ):
                if os.path.isfile(
                    os.path.join(
                        DEBUG_MODS_DIR,
                        f"{module.__class__.__name__}.py",
                    )
                ):
                    os.remove(
                        os.path.join(
                            DEBUG_MODS_DIR,
                            f"{module.__class__.__name__}.py",
                        )
                    )

                    try:
                        delattr(module, "hikka_debug")
                    except AttributeError:
                        pass

                    await utils.answer(message, self.strings("debugging_disabled"))
                    return

                module.hikka_debug = True
                instance = module
                break

        if not instance:
            await utils.answer(message, self.strings("bad_module"))
            return

        with open(
            os.path.join(
                DEBUG_MODS_DIR,
                f"{instance.__class__.__name__}.py",
            ),
            "wb",
        ) as f:
            f.write(inspect.getmodule(instance).__loader__.data)

        await utils.answer(
            message,
            self.strings("debugging_enabled").format(instance.__class__.__name__),
        )

    @loader.command(
        ru_doc="<уровень> - Показать логи",
        de_doc="<Level> - Zeige Logs",
        uz_doc="<daraja> - Loglarni ko'rsatish",
        tr_doc="<seviye> - Günlükleri göster",
        es_doc="<nivel> - Mostrar registros",
    )
    async def logs(
        self,
        message: typing.Union[Message, InlineCall],
        force: bool = False,
        lvl: typing.Union[int, None] = None,
    ):
        """<level> - Dump logs"""
        if not isinstance(lvl, int):
            args = utils.get_args_raw(message)
            try:
                try:
                    lvl = int(args.split()[0])
                except ValueError:
                    lvl = getattr(logging, args.split()[0].upper(), None)
            except IndexError:
                lvl = None

        if not isinstance(lvl, int):
            try:
                if not self.inline.init_complete or not await self.inline.form(
                    text=self.strings("choose_loglevel"),
                    reply_markup=[
                        [
                            {
                                "text": "🚨 Critical",
                                "callback": self.logs,
                                "args": (False, 50),
                            },
                            {
                                "text": "🚫 Error",
                                "callback": self.logs,
                                "args": (False, 40),
                            },
                        ],
                        [
                            {
                                "text": "⚠️ Warning",
                                "callback": self.logs,
                                "args": (False, 30),
                            },
                            {
                                "text": "ℹ️ Info",
                                "callback": self.logs,
                                "args": (False, 20),
                            },
                        ],
                        [
                            {
                                "text": "🧑‍💻 Debug",
                                "callback": self.logs,
                                "args": (False, 10),
                            },
                            {
                                "text": "👁 All",
                                "callback": self.logs,
                                "args": (False, 0),
                            },
                        ],
                        [{"text": "🚫 Cancel", "action": "close"}],
                    ],
                    message=message,
                ):
                    raise
            except Exception:
                await utils.answer(message, self.strings("set_loglevel"))

            return

        logs = "\n\n".join(
            [
                "\n".join(
                    handler.dumps(lvl, client_id=self._client.tg_id)
                    if "client_id" in inspect.signature(handler.dumps).parameters
                    else handler.dumps(lvl)
                )
                for handler in logging.getLogger().handlers
            ]
        )

        named_lvl = (
            lvl
            if lvl not in logging._levelToName
            else logging._levelToName[lvl]  # skipcq: PYL-W0212
        )

        if (
            lvl < logging.WARNING
            and not force
            and (
                not isinstance(message, Message)
                or "force_insecure" not in message.raw_text.lower()
            )
        ):
            try:
                if not self.inline.init_complete:
                    raise

                cfg = {
                    "text": self.strings("confidential").format(named_lvl),
                    "reply_markup": [
                        {
                            "text": self.strings("send_anyway"),
                            "callback": self.logs,
                            "args": [True, lvl],
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                }
                if isinstance(message, Message):
                    if not await self.inline.form(**cfg, message=message):
                        raise
                else:
                    await message.edit(**cfg)
            except Exception:
                await utils.answer(
                    message,
                    self.strings("confidential_text").format(named_lvl),
                )

            return

        if len(logs) <= 2:
            if isinstance(message, Message):
                await utils.answer(message, self.strings("no_logs").format(named_lvl))
            else:
                await message.edit(self.strings("no_logs").format(named_lvl))
                await message.unload()

            return

        if btoken := self._db.get("hikka.inline", "bot_token", False):
            logs = logs.replace(
                btoken,
                f'{btoken.split(":")[0]}:***************************',
            )

        if hikka_token := self._db.get("HikkaDL", "token", False):
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")[0]}_********************************',
            )

        if hikka_token := self._db.get("Kirito", "token", False):
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")[0]}_********************************',
            )

        if os.environ.get("DATABASE_URL"):
            logs = logs.replace(
                os.environ.get("DATABASE_URL"),
                "postgre://**************************",
            )

        if os.environ.get("REDIS_URL"):
            logs = logs.replace(
                os.environ.get("REDIS_URL"),
                "postgre://**************************",
            )

        if os.environ.get("hikka_session"):
            logs = logs.replace(
                os.environ.get("hikka_session"),
                "StringSession(**************************)",
            )

        logs = BytesIO(logs.encode("utf-16"))
        logs.name = self.strings("logs_filename")

        ghash = utils.get_git_hash()

        other = (
            *main.__version__,
            " <i><a"
            f' href="https://github.com/hikariatama/Hikka/commit/{ghash}">({ghash[:8]})</a></i>'
            if ghash
            else "",
            utils.formatted_uptime(),
            utils.get_named_platform(),
            "✅" if self._db.get(main.__name__, "no_nickname", False) else "🚫",
            "✅" if self._db.get(main.__name__, "grep", False) else "🚫",
            "✅" if self._db.get(main.__name__, "inlinelogs", False) else "🚫",
        )

        if getattr(message, "out", True):
            await message.delete()

        if isinstance(message, Message):
            await utils.answer(
                message,
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )
        else:
            await self._client.send_file(
                message.form["chat"],
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )

    @loader.owner
    @loader.command(
        ru_doc="<время> - Заморозить бота на N секунд",
        de_doc="<Zeit> - Stoppe den Bot für N Sekunden",
        tr_doc="<süre> - Botu N saniye boyunca durdur",
        uz_doc="<vaqt> - Botni N soniya davomida to'xtatish",
        es_doc="<tiempo> - Congela el bot durante N segundos",
    )
    async def suspend(self, message: Message):
        """<time> - Suspends the bot for N seconds"""
        try:
            time_sleep = float(utils.get_args_raw(message))
            await utils.answer(
                message,
                self.strings("suspended").format(time_sleep),
            )
            time.sleep(time_sleep)
        except ValueError:
            await utils.answer(message, self.strings("suspend_invalid_time"))

    @loader.command(
        ru_doc="Проверить скорость отклика юзербота",
        de_doc="Überprüfe die Antwortgeschwindigkeit des Userbots",
        tr_doc="Kullanıcı botunun yanıt hızını kontrol edin",
        uz_doc="Foydalanuvchi botining javob tezligini tekshiring",
        es_doc="Comprueba la velocidad de respuesta del bot de usuario",
    )
    async def ping(self, message: Message):
        """Test your userbot ping"""
        start = time.perf_counter_ns()
        message = await utils.answer(message, "<code>🐻 Nofin...</code>")

        await utils.answer(
            message,
            self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**6, 3),
                utils.formatted_uptime(),
            )
            + (
                ("\n\n" + self.strings("ping_hint"))
                if random.choice([0, 0, 1]) == 1
                else ""
            ),
        )

    async def client_ready(self):
        chat, _ = await utils.asset_channel(
            self._client,
            "hikka-logs",
            "🌘 Your Hikka logs will appear in this chat",
            silent=True,
            invite_bot=True,
            avatar="https://github.com/hikariatama/assets/raw/master/hikka-logs.png",
        )

        self._logchat = int(f"-100{chat.id}")

        self.watchdog.start()

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug("Bot logging installed for %s", self._logchat)

        self._pass_config_to_logger()
