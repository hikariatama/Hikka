# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

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
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Please specify"
            " verbosity as an integer or string</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>You don't have any"
            " logs at verbosity</b> <code>{}</code><b>.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka logs with"
            " verbosity</b> <code>{}</code>\n\n<emoji"
            " document_id=6318902906900711458>⚪️</emoji> <b>Version:"
            " {}.{}.{}</b>{}"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Invalid time to"
            " suspend</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot suspended"
            " for</b> <code>{}</code> <b>seconds</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Telegram ping:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Uptime: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram ping mostly"
            " depends on Telegram servers latency and other external factors and has"
            " nothing to do with the parameters of server on which userbot is"
            " installed</i>"
        ),
        "confidential": (
            "⚠️ <b>Log level</b> <code>{}</code> <b>may reveal your confidential info,"
            " be careful</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Log level</b> <code>{0}</code> <b>may reveal your confidential info,"
            " be careful</b>\n<b>Type</b> <code>.logs {0} force_insecure</code> <b>to"
            " ignore this warning</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Choose log level</b>",
        "bad_module": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Module not found</b>"
        ),
        "debugging_enabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Debugging mode enabled"
            " for module</b> <code>{0}</code>\n<i>Go to directory named"
            " `debug_modules`, edit file named `{0}.py` and see changes in real"
            " time</i>"
        ),
        "debugging_disabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Debugging disabled</b>"
        ),
        "send_anyway": "📤 Send anyway",
        "cancel": "🚫 Cancel",
        "logs_cleared": "🗑 <b>Logs cleared</b>",
    }

    strings_ru = {
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Укажи уровень логов"
            " числом или строкой</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>У тебя нет логов"
            " уровня</b> <code>{}</code><b>.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Логи Hikka уровня"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Версия: {}.{}.{}</b>{}"
        ),
        "debugging_enabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Режим разработчика"
            " включен для модуля</b> <code>{0}</code>\n<i>Отправляйся в директорию"
            " `debug_modules`, изменяй файл `{0}.py`, и смотри изменения в режиме"
            " реального времени</i>"
        ),
        "debugging_disabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Режим разработчика"
            " выключен</b>"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Неверное время"
            " заморозки</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Бот заморожен на</b>"
            " <code>{}</code> <b>секунд</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Скорость отклика"
            " Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Прошло с последней"
            " перезагрузки: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Скорость отклика"
            " Telegram в большей степени зависит от загруженности серверов Telegram и"
            " других внешних факторов и никак не связана с параметрами сервера, на"
            " который установлен юзербот</i>"
        ),
        "confidential": (
            "⚠️ <b>Уровень логов</b> <code>{}</code> <b>может содержать личную"
            " информацию, будь осторожен</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Уровень логов</b> <code>{0}</code> <b>может содержать личную"
            " информацию, будь осторожен</b>\n<b>Напиши</b> <code>.logs {0}"
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
        "logs_cleared": "🗑 <b>Логи очищены</b>",
    }

    strings_fr = {
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Spécifiez le niveau de"
            " journalisation en nombre ou en chaîne</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>Vous n'avez pas de"
            " journaux niveau</b> <code>{}</code><b>.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Journal Hikka niveau"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Version: {}.{}.{}</b>{}"
        ),
        "debugging_enabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Mode développeur"
            " activé pour le module</b> <code>{0}</code>\n<i>Allez dans le dossier"
            " `debug_modules`, modifier le fichier `{0}.py`, et voir les modifications"
            " en temps réel</i>"
        ),
        "debugging_disabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Mode développeur"
            " désactivé</b>"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Temps de suspension"
            " invalide</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Le bot est suspendu"
            " pour</b> <code>{}</code> <b>secondes</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Vitesse de réponse"
            " Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Passé depuis la dernière"
            " redémarrage: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>La vitesse de réponse"
            " Telegram est en grande partie dépendante de la charge des serveurs"
            " Telegram et d'autres facteurs externes et n'a aucun rapport avec les"
            " paramètres du serveur, sur lequel l'usagerbot est installé</i>"
        ),
        "confidential": (
            "⚠️ <b>Niveau de journaux</b> <code>{}</code> <b>peut contenir des"
            " informations personnelles, soyez prudent</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Niveau de journaux</b> <code>{0}</code> <b>peut contenir des"
            " informations personnelles, soyez prudent</b>\n<b>Ecris</b> <code>.logs"
            " {0} force_insecure</code><b>, pour envoyer les journaux en ignorant"
            " l'avertissement</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Choisissez le niveau de journaux</b>",
        "_cmd_doc_dump": "Afficher les informations du message",
        "_cmd_doc_logs": (
            "<niveau> - Envoyer le fichier journal. Les niveaux inférieurs à WARNING"
            " peuvent contenir des informations personnelles."
        ),
        "_cmd_doc_suspend": (
            "<temps> - Mettre en pause l'utilisateurbot pendant un certain temps"
        ),
        "_cmd_doc_ping": "Vérifie la vitesse de réponse de l'utilisateurbot",
        "_cls_doc": "Opérations liées à l'auto-test",
        "send_anyway": "📤 Envoyer quand même",
        "cancel": "🚫 Annuler",
        "logs_cleared": "🗑 <b>Les journaux ont été nettoyés</b>",
    }

    strings_it = {
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Specifica il livello"
            " dei log</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>Non hai log"
            " di livello</b> <code>{}</code><b>.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Log di Hikka a livello"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Versione: {}.{}.{}</b>{}"
        ),
        "debugging_enabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Modalità sviluppatore"
            " abilitata per il modulo</b> <code>{0}</code>\n<i>Vai nella cartella"
            " `debug_modules`, modifica il file `{0}.py`, e guarda i cambiamenti in"
            " tempo reale</i>"
        ),
        "debugging_disabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Modalità sviluppatore"
            " disabilitata</b>"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Tempo di sospensione"
            " non valido</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Il bot è stato sospeso"
            " per</b> <code>{}</code> <b>secondi</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Velocità di risposta"
            " di Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Tempo trascorso dalla"
            " ultima riavvio: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>La velocità di"
            " risposta di Telegram dipende maggiormente dalla carica dei server di"
            " Telegram e da altri fattori esterni e non è in alcun modo correlata ai"
            " parametri del server su cui è installato lo UserBot</i>"
        ),
        "confidential": (
            "⚠️ <b>Il livello di log</b> <code>{}</code> <b>può contenere informazioni"
            " personali, fai attenzione</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Il livello di log</b> <code>{0}</code> <b>può contenere informazioni"
            " personali, fai attenzione</b>\n<b>Scrivi</b> <code>.logs {0}"
            " force_insecure</code><b>, per inviare i log ignorando l'avviso</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Scegli il livello di log</b>",
        "_cmd_doc_dump": "Mostra le informazioni sul messaggio",
        "_cmd_doc_logs": (
            "<livello> - Invia il file di log. I livelli inferiori a WARNING possono"
            " contenere informazioni personali."
        ),
        "_cmd_doc_suspend": "<tempo> - Ferma lo UserBot per un certo tempo",
        "_cmd_doc_ping": "Controlla la velocità di risposta dello UserBot",
        "_cls_doc": "Operazioni relative alle prove di autotest",
        "send_anyway": "📤 Invia comunque",
        "cancel": "🚫 Annulla",
        "logs_cleared": "🗑 <b>Log cancellati</b>",
    }

    strings_de = {
        "set_loglevel": (
            "🚫 <b>Geben Sie die Protokollebene als Zahl oder Zeichenfolge an</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>Du hast kein"
            " Protokollnachrichten des</b> <code>{}</code> <b>Ebene.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka-Level-Protokolle"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Version: {}.{}.{}</b>{}"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Falsche Zeit"
            "einfrieren</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot ist"
            " eingefroren</b> <code>{}</code> <b>Sekunden</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Reaktionszeit des"
            " Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Zeit seit dem letzten"
            " Neustart: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Reaktionsfähigkeit"
            " Telegram ist stärker abhängig von der Auslastung der Telegram-Server und"
            " Andere externe Faktoren und steht in keinem Zusammenhang mit den"
            " Servereinstellungen welcher Userbot installiert ist</i>"
        ),
        "confidential": (
            "⚠️ <b>Protokollebene</b> <code>{}</code> <b>kann privat enthalten"
            "Informationen, seien Sie vorsichtig</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Protokollebene</b> <code>{0}</code> <b>kann privat"
            " enthaltenInformationen, seien Sie vorsichtig</b>\n<b>Schreiben Sie"
            "</b> <code>.logs {0} force_insecure</code> <b>um Protokolle zu"
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
        "logs_cleared": "🗑 <b>Protokolle gelöscht</b>",
    }

    strings_uz = {
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Log darajasini raqam"
            " yoki satr sifatida ko'rsating</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>Siz"
            "</b> <code>{}</code> <b>darajadagi hech qanday loglaringiz yo'q.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka Loglari"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Versiyasi: {}.{}.{}</b>{}"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Noto'g'ri vaqt"
            "qo'ymoq</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot chiqarildi</b>"
            " <code>{}</code> <b>Soniyalar</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Telegram tezligi:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Soʻngi marotaba qayta ishga"
            " tushirilgan vaqti:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram"
            " tezligi Telegram serverlarining ishga tushishi va boshqa tashqi"
            " faktorlariga bog'liq va Userbot o'rnatilgan serverlarining sozlamalari"
            " bilan bog'liq emas</i>"
        ),
        "confidential": (
            "⚠️ <b>Log darajasi</b> <code>{}</code> <b>shaxsiy ma'lumotlarga ega"
            " bo'lishi mumkinO'zingizni xavfsizligi uchun</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Log darajasi</b> <code>{0}</code> <b>shaxsiy ma'lumotlarga ega"
            " bo'lishi mumkinO'zingizni xavfsizligi uchun</b>\n<b>Yozing"
            "</b> <code>.logs {0} force_insecure</code> <b>loglarniOgohlantirish</b>"
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
        "logs_cleared": "🗑 <b>Günlükler temizlendi</b>",
    }

    strings_tr = {
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Lütfen kayıt"
            " seviyesini sayı veya metin olarak belirtin</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <code>{}</code>"
            " <b>seviyesinde hiçbir kayıt bulunmuyor.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka Kayıtları"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Versiyası: {}.{}.{}</b>{}"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5416024721705673488>💀</emoji> <b>Durdurma için geçersiz"
            " zaman girdiniz</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Kullanıcı botu</b>"
            " <code>{}</code> <b>saniyeliğine durduruldu</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Telegram ping:</b>"
            " <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Çalışma Süresi:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram pingi"
            " çoğunlukla Telegram sunucularının gecikmesine ve diğer dış etkenlere"
            " bağlıdır ve userbot'un kurulu olduğu sunucunun parametreleriyle hiçbir"
            " ilgisi yoktur.</i>"
        ),
        "confidential": (
            "⚠️ <b>Kayıt seviyesi</b> <code>{}</code> <b>gizli bilgilere sahip"
            " olabilir, kendi güvenliğiniz için dikkatli olun</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Kayıt seviyesi</b> <code>{0}</code> <b>gizli bilgilere sahip"
            " olabilir, dikkatli olun. \n<b>Bu mesajı görmezden gelmek için"
            "</b> <code>.logs {0} force_insecure</code> <b>yazınız</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Lütfen Kayıt seviyesini seçin</b>",
        "_cmd_doc_dump": "Mesaj hakkında bilgi göster",
        "_cmd_doc_logs": "<Ebene> - Kayıt dosyasını gönderir. Seviyeler gizlibilgiler.",
        "_cmd_doc_suspend": "<Zaman> - Botu bir süreliğine durdurun",
        "_cmd_doc_ping": "Kullanıcı botunun yanıt verme hızını kontrol edin",
        "_cls_doc": "İlgili testlerle ilgili işlemler",
        "send_anyway": "📤 Gönder",
        "cancel": "🚫 İptal",
    }

    strings_es = {
        "set_loglevel": (
            "🚫 <b>Por favor, indique el nivel de registro como número o cadena</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>No hay registros"
            "</b> <code>{}</code> <b>nivel.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Registros de"
            "</b> <code>{}</code>\n\n<emoji document_id=6318902906900711458>⚪️</emoji>"
            " <b>Versión: {}.{}.{}</b>{}"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Has introducido un"
            " tiempo no válido</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Bot suspendido</b>"
            " <code>{}</code> <b>segundos</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Retraso del"
            " Telegram:</b> <code>{}</code> <b>ms</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Desde la última"
            " actualización:</b> {}"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>La velocidad de"
            " Telegram depende de la inicialización de los servidores de Telegram y"
            " otros factores externosy no de la configuración de su servidor de"
            " Userbot</i>"
        ),
        "confidential": (
            "⚠️ <b>Nivel de registro</b> <code>{}</code> <b>puede contener información"
            " confidencial asegúrate de proteger tu privacidad</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Nivel de registro</b> <code>{0}</code> <b>puede contener información"
            " confidencial asegúrate de proteger tu privacidad</b>\n<b>Escribe"
            "</b> <code>.logs {0} force_insecure</code> <b>para enviar los"
            " registros</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Por favor, elige el nivel de registro</b>",
        "_cmd_doc_dump": "Muestra información sobre el mensaje",
        "_cmd_doc_logs": (
            "<Nivel> - Envía el archivo de registro. Los niveles confidenciales"
            "pueden contener información confidencial"
        ),
        "_cmd_doc_suspend": "<Tiempo> - Suspende el bot durante un tiempo",
        "_cmd_doc_ping": "Comprueba la velocidad de respuesta de su Userbot",
        "_cls_doc": "Procesos relacionados con los tests",
        "send_anyway": "📤 Enviar de todos modos",
        "cancel": "🚫 Cancelar",
        "logs_cleared": "🗑 <b>Registros borrados</b>",
    }

    strings_kk = {
        "set_loglevel": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Лог түрін сан немесе"
            " жолмен енгізіңіз</b>"
        ),
        "no_logs": (
            "<emoji document_id=5363948200291998612>🤷‍♀️</emoji> <b>Сізде"
            "</b> <code>{}</code> <b>деңгейіндегі лог жоқ.</b>"
        ),
        "logs_caption": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Hikka логтарының"
            " деңгейі</b> <code>{}</code>\n\n<emoji"
            " document_id=6318902906900711458>⚪️</emoji> <b>Нұсқауы: {}.{}.{}</b>{}"
        ),
        "debugging_enabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Модуль"
            "</b> <code>{0}</code> <b>үшін дебаг режимі қосылды</b>\n<i>`debug_modules`"
            " директориясына өтуіңіз керек, файлды өзгертіңіз, әрбір өзгерісті алдын"
            " ала қараңыз</i>"
        ),
        "debugging_disabled": (
            "<emoji document_id=5332533929020761310>✅</emoji> <b>Дебаг режимі"
            " өшірілді</b>"
        ),
        "suspend_invalid_time": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Жарамсыз уақыт</b>"
        ),
        "suspended": (
            "<emoji document_id=5452023368054216810>🥶</emoji> <b>Бот"
            "</b> <code>{}</code> <b>секунд құлыпталды</b>"
        ),
        "results_ping": (
            "<emoji document_id=5431449001532594346>⚡️</emoji> <b>Telegram жауап беру"
            " уақыты:</b> <code>{}</code> <b>мс</b>\n<emoji"
            " document_id=5445284980978621387>🚀</emoji> <b>Соңғы рестарттан бұрын"
            " уақыты: {}</b>"
        ),
        "ping_hint": (
            "<emoji document_id=5472146462362048818>💡</emoji> <i>Telegram жауап"
            " беру уақыты серверлердің жүйелігі мен басқа сыртқы әсерлерге қарсы"
            " өзгереді және серверіңізге қанша жақсартылғанымен қатарын болмайды</i>"
        ),
        "confidential": (
            "⚠️ <b>Лог түрі</b> <code>{}</code> <b>сіздің жеке мәліметіңізге қатысты"
            " болуы мүмкін, сенімді болыңыз</b>"
        ),
        "confidential_text": (
            "⚠️ <b>Лог түрі</b> <code>{0}</code> <b>сіздің жеке мәліметіңізге қатысты"
            " болуы мүмкін, сенімді болыңыз</b>\n<b>Жолдан</b> <code>.logs {0}"
            " force_insecure</code><b>, келесі сияқтық бойынша логтарды жіберу"
            " үшін сенімді болыңыз</b>"
        ),
        "choose_loglevel": "💁‍♂️ <b>Лог түрін таңдаңыз</b>",
        "_cmd_doc_dump": "Хабарлама туралы ақпаратты көрсету",
        "_cmd_doc_logs": (
            "<түр> - Лог файлын жіберу. WARNING түрінен кейінгі түрлер сіздің"
            " жеке мәліметіңізге қатысты болуы мүмкін."
        ),
        "_cmd_doc_suspend": "<уақыт> - Ботты бірнеше уақыт қойып қалдыру",
        "_cmd_doc_ping": "Юзерботтың жауап беру уақытын тексеру",
        "_cls_doc": "Өздіктік сынауға қатысты әрекеттер",
        "send_anyway": "📤 Жіберу",
        "cancel": "🚫 Болдырмау",
        "logs_cleared": "🗑 <b>Логтар тазартылды</b>",
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
        fr_doc="Répondre au message pour montrer sa décharge",
        it_doc="Rispondi al messaggio per mostrare il suo dump",
        de_doc="Antworten Sie auf eine Nachricht, um ihren Dump anzuzeigen",
        tr_doc="Dökümünü göstermek için bir iletiyi yanıtlayın",
        uz_doc="Xabarning axlatini ko'rsatish uchun unga javob bering",
        es_doc="Responde a un mensaje para mostrar su volcado",
        kk_doc="Дампын көрсету үшін хабарламаға жауап беріңіз",
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

    @loader.command(
        ru_doc="Очистить логи",
        fr_doc="Effacer les journaux",
        it_doc="Cancella i log",
        de_doc="Logs löschen",
        tr_doc="Günlükleri temizle",
        uz_doc="Jurnalni tozalash",
        es_doc="Limpiar registros",
        kk_doc="Логтарды тазалау",
    )
    async def clearlogs(self, message: Message):
        """Clear logs"""
        for handler in logging.getLogger().handlers:
            handler.buffer = []
            handler.handledbuffer = []
            handler.tg_buff = ""

        await utils.answer(message, self.strings("logs_cleared"))

    @loader.loop(interval=1, autostart=True)
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

    @loader.command()
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
        fr_doc="<niveau> - Afficher les journaux",
        it_doc="<livello> - Mostra i log",
        de_doc="<Level> - Zeige Logs",
        uz_doc="<daraja> - Loglarni ko'rsatish",
        tr_doc="<seviye> - Günlükleri göster",
        es_doc="<nivel> - Mostrar registros",
        kk_doc="<деңгей> - Логтарды көрсету",
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
                    reply_markup=utils.chunks(
                        [
                            {
                                "text": name,
                                "callback": self.logs,
                                "args": (False, level),
                            }
                            for name, level in [
                                ("🚫 Error", 40),
                                ("⚠️ Warning", 30),
                                ("ℹ️ Info", 20),
                                ("🧑‍💻 All", 0),
                            ]
                        ],
                        2,
                    )
                    + [[{"text": self.strings("cancel"), "action": "close"}]],
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

        logs = self.lookup("python").censor(logs)

        logs = BytesIO(logs.encode("utf-16"))
        logs.name = "hikka-logs.txt"

        ghash = utils.get_git_hash()

        other = (
            *main.__version__,
            (
                " <a"
                f' href="https://github.com/hikariatama/Hikka/commit/{ghash}">@{ghash[:8]}</a>'
                if ghash
                else ""
            ),
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
                reply_to=message.form["top_msg_id"],
            )

    @loader.owner
    @loader.command(
        ru_doc="<время> - Заморозить бота на N секунд",
        fr_doc="<temps> - Congeler le bot pendant N secondes",
        it_doc="<tempo> - Congela il bot per N secondi",
        de_doc="<Zeit> - Stoppe den Bot für N Sekunden",
        tr_doc="<süre> - Botu N saniye boyunca durdur",
        uz_doc="<vaqt> - Botni N soniya davomida to'xtatish",
        es_doc="<tiempo> - Congela el bot durante N segundos",
        kk_doc="<уақыт> - Ботты N секунд ұзақтығында тұзатып қой",
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
        fr_doc="Vérifiez la vitesse de réponse du bot utilisateur",
        it_doc="Controlla la velocità di risposta del userbot",
        de_doc="Überprüfe die Antwortgeschwindigkeit des Userbots",
        tr_doc="Kullanıcı botunun yanıt hızını kontrol edin",
        uz_doc="Foydalanuvchi botining javob tezligini tekshiring",
        es_doc="Comprueba la velocidad de respuesta del bot de usuario",
        kk_doc="Қолданушы ботының жауап шығу уақытын тексеру",
    )
    async def ping(self, message: Message):
        """Test your userbot ping"""
        start = time.perf_counter_ns()
        message = await utils.answer(message, "🌘")

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

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug("Bot logging installed for %s", self._logchat)

        self._pass_config_to_logger()
