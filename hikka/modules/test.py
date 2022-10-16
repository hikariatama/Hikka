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
from io import BytesIO
import typing

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

    strings_hi = {
        "set_loglevel": (
            "🚫 <b>कृपया लॉग स्तर को संख्या या स्ट्रिंग के रूप में निर्दिष्ट करें</b>"
        ),
        "no_logs": "ℹ️ <b>कोई {} स्तर के लॉग नहीं मिला।</b>",
        "logs_filename": "hikka-logs.txt",
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka लॉग</b>"
            " </code>\n\n<emoji document_id=5454390891466726015>👋</emoji>"
            " <b>Hikka संस्करण: {}.{}.{}</b>{}\n<Emoji"
            "document_id=6321050180095313397>⏱</emoji> <b>वेळ:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "bad_module": "🚫 <b>मॉड्यूल नहीं मिला</b>",
        "debugging_enabled": (
            (
                "🧑‍💻 <b>मॉड्यूल के लिए डिबगिंग सक्षम कर दिया गया है"
                " </b><code>{0}</code>\n<i>`debug_modules` फ़ोल्डर में जाएँ"
            ),
            "`{0}.py` फ़ाइल को संपादित करें और परिवर्तनों को सहेजें</i>",
        ),
        "debugging_disabled": "✅ <b>डिबगिंग डिसेबल कर दिया गया है</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>अमान्य समय"
            "दर्ज किया गया।</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>बॉट निलंबित कर दिया"
            " गया है</b> <code>{}</code> <b>सेकंड</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>टेलीग्राम"
            "गति:</b> <code>{}</code> <b>मिलीसेकंड</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>अंतिम अपडेट से बाद:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>टेलीग्राम गति"
            "टेलीग्राम सर्वर को शुरू करने और अन्य बाहरी वजहों से जुड़ा है"
            "और आपके उपयोगकर्ता बॉट स्थापना के सर्वर सेटिंग्स से संबंधित नहीं है</i>"
        ),
        "confidential": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>वेळ:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "confidential_text": (
            "⚠️ <b>लॉग स्तर </b><code>{0}</code><b> में गोपनीय जानकारी हो सकती है"
            "अपनी सुरक्षा के लिए</b>\n<b>लिखें </b><code>.logs {0}"
            "force_insecure</code><b> लॉग"
            "चेतावनी</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>कृपया लॉग लेवल चुनें</b>",
        "_cmd_doc_dump": "संदेश के बारे में जानकारी दिखाएं",
        "_cmd_doc_logs": "<Ebene> - लॉग फ़ाइल भेजता है। स्तर छिपे हुए हैंसूचनाएं।",
        "_cmd_doc_suspend": "<समय> - बॉट को थोड़ी देर के लिए फ़्रीज़ करें",
        "_cmd_doc_ping": "यूजरबॉट रिस्पॉन्सिबिलिटी चेक करें",
        "_cls_doc": "संबंधित परीक्षण संसाधित किए जा रहे हैं",
        "send_anyway": "📤 फिर भी भेजें",
        "cancel": "🚫 रद्द करें",
    }

    strings_ja = {
        "debugging_enabled": "✅ <b>デバッグが有効になりました</b>",
        "debugging_disabled": "✅ <b>デバッグが無効になりました</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>無効な時間入力されました。</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>ボットが"
            "一時停止されました</b> <code>{}</code> <b>秒</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>テレグラム"
            "速度:</b> <code>{}</code> <b>ミリ秒</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>最後の更新からの経過時間:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>テレグラム速度"
            "テレグラムサーバーを起動し、他の外部要因により"
            "あなたのユーザーボットのセットアップとは関係がありません</i>"
        ),
        "confidential": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>時間:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "confidential_text": (
            "⚠️ <b>ログレベル </b><code>{0}</code><b>には機密情報が含まれている可能性があります"
            "セキュリティ上の理由で</b>\n<b>書き込み</b><code>.logs {0}"
            "force_insecure</code><b>ログ"
            "警告</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>ログレベルを選択してください</b>",
        "_cmd_doc_dump": "メッセージに関する情報を表示します",
        "_cmd_doc_logs": "<レベル> - ログファイルを送信します。隠されたレベルは通知されません。",
        "_cmd_doc_suspend": "<時間> - ボットを一時停止します",
        "_cmd_doc_ping": "ユーザーボットのレスポンス能力をチェックします",
        "_cls_doc": "関連するテストが実行されています",
        "send_anyway": "📤 それでも送信する",
        "cancel": "🚫 キャンセル",
    }

    strings_kr = {
        "debugging_enabled": "✅ <b>디버깅이 활성화되었습니다</b>",
        "debugging_disabled": "✅ <b>디버깅이 비활성화되었습니다</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>잘못된 시간입력되었습니다</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>봇이"
            "일시 중지되었습니다</b> <code>{}</code> <b>초</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>텔레그램"
            "속도:</b> <code>{}</code> <b>밀리 초</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>마지막 업데이트 이후 경과 시간:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>텔레그램 속도"
            "텔레그램 서버를 시작하고 다른 외부 요인에 의해"
            "당신의 사용자 봇의 설정과는 관련이 없습니다</i>"
        ),
        "confidential": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>시간:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "confidential_text": (
            "⚠️ <b>로그 레벨 </b><code>{0}</code><b>에는 기밀 정보가 포함될 수 있으므로"
            "보안상의 이유로</b>\n<b>작성</b><code>.logs {0}"
            "force_insecure</code><b>로그"
            "경고</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>로그 레벨을 선택하세요</b>",
        "_cmd_doc_dump": "메시지에 대한 정보를 표시합니다",
        "_cmd_doc_logs": "<레벨> - 로그 파일을 보냅니다. 숨겨진 레벨은 알림되지 않습니다.",
        "_cmd_doc_suspend": "<시간> - 봇을 일시 중지합니다",
        "_cmd_doc_ping": "사용자 봇의 응답 능력을 확인합니다",
        "_cls_doc": "관련된 테스트가 실행 중입니다",
        "send_anyway": "📤 그래도 보내기",
        "cancel": "🚫 취소",
    }

    strings_ar = {
        "debugging_enabled": "✅ <b>تم تمكين التصحيح</b>",
        "debugging_disabled": "✅ <b>تم تعطيل التصحيح</b>",
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>أدخلالوقت الصحيح</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>تم إيقاف"
            "البوت</b> <code>{}</code> <b>ثوانٍ</b>"
        ),
        "results_ping": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>سرعةتيليجرام:</b>"
            " <code>{}</code> <b>مللي ثانية</b>\n<emoji"
            " document_id=5377371691078916778>😎</emoji> <b>مدة الوقت منذ آخر"
            " تحديث:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>سرعة"
            "تيليجرام ليست عبارة عن الوقت الذي يستغرقه البوت للرد على الرسائل"
            "لكنها هي الوقت الذي يستغرقه البوت للرد على الرسائل الخاصة بك من"
            "بدء تشغيل البوت وليس بسبب أي عوامل خارجية أخرى"
            "مثل إعدادات البوت الخاص بك</i>"
        ),
        "confidential": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>الوقت:"
            " {}</b>\n<b>{}</b>\n\n<b>{} NoNick</b>\n<b>{} Grep</b>\n<b>{ }"
            "InlineLogs</b>"
        ),
        "confidential_text": (
            "⚠️ <b>يحتوي مستوى السجلات </b><code>{0}</code><b>على معلومات"
            "سرية ولذلك</b>\n<b>اكتب</b><code>.logs {0}"
            "force_insecure</code><b>لإرسال السجلات"
            "معلومات سرية</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>اختر مستوى السجلات</b>",
        "_cmd_doc_dump": "عرض معلومات الرسالة",
        "_cmd_doc_logs": (
            "<مستوى> - إرسال ملفات السجلات. المستويات المخفية لا يتم إخطارك عنها."
        ),
        "_cmd_doc_suspend": "<وقت> - إيقاف البوت مؤقتًا",
        "_cmd_doc_ping": "تحقق من سرعة البوت",
        "_cls_doc": "تم تشغيل اختبارات ذات صلة",
        "send_anyway": "📤 إرسالها على أية حال",
        "cancel": "🚫 إلغاء",
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
        hi_doc="किसी संदेश का उत्तर उसके डंप को दिखाने के लिए दें",
        uz_doc="Xabarning axlatini ko'rsatish uchun unga javob bering",
        ja_doc="メッセージに返信してそのダンプを表示します",
        kr_doc="메시지에 답장하여 그 덤프를 표시합니다",
        ar_doc="أرسل رسالة لعرض نسخة منها",
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
                logger.debug(f"Reloading debug module {cls_}")
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
        hi_doc=(
            "[मॉड्यूल] - डेवलपर्स के लिए: एक मॉड्यूल को डिबग मोड में खोलें और"
            " वास्तविक समय में इसके परिवर्तनों को लागू करें"
        ),
        ja_doc="[モジュール] - 開発者向け：モジュールをデバッグモードで開き、変更をリアルタイムで適用します",
        kr_doc="[모듈] - 개발자용: 모듈을 디버그 모드로 열고 실시간으로 변경을 적용합니다",
        ar_doc=(
            "[وحدة] - للمطورين: فتح وحدة في وضع تصحيح الأخطاء وتطبيق"
            " التغييرات منه في الوقت الحقيقي"
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
        hi_doc="<स्तर> - लॉग दिखाएं",
        ja_doc="<レベル> - ログを表示します",
        kr_doc="<레벨> - 로그 표시",
        ar_doc="<مستوى> - إظهار السجلات",
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
        hi_doc="<समय> - बॉट को N सेकंड तक ठहराएं",
        ja_doc="<時間> - ボットをN秒間停止します",
        kr_doc="<시간> - 봇을 N 초 동안 정지",
        ar_doc="<الوقت> - تجميد البوت لمدة N ثانية",
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
        hi_doc="उपयोगकर्ता बॉट की प्रतिक्रिया गति की जांच करें",
        ja_doc="ユーザーボットの応答速度を確認します",
        kr_doc="사용자 봇의 응답 속도를 확인하십시오",
        ar_doc="تحقق من سرعة استجابة بوت المستخدم",
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
