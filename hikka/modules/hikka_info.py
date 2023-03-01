# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import git
from hikkatl.tl.types import Message
from hikkatl.utils import get_display_name

from .. import loader, utils, version
from ..inline.types import InlineQuery


@loader.tds
class HikkaInfoMod(loader.Module):
    """Show userbot info"""

    strings = {
        "name": "HikkaInfo",
        "owner": "Owner",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "branch": "Branch",
        "cpu_usage": "CPU usage",
        "ram_usage": "RAM usage",
        "send_info": "Send userbot info",
        "description": "ℹ This will not compromise any sensitive info",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Up-to-date</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Update required"
            "</b> <code>.update</code>"
        ),
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>You need to specify"
            " text to change info to</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Info changed"
            " successfully</b>"
        ),
        "_cfg_cst_msg": (
            "Custom message for info. May contain {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {cpu_usage}, {ram_usage}, {branch} keywords"
        ),
        "_cfg_cst_btn": "Custom button for info. Leave empty to remove button",
        "_cfg_banner": "URL to image banner",
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Userbot — what is"
            " it?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> A userbot"
            " refers to a <b>third-party program</b> that interacts with the Telegram"
            " API to perform <b>automated tasks on behalf of a user</b>. These userbots"
            " can be used to automate various tasks such as <b>sending messages,"
            " joining channels, downloading media, and much more</b>.\n\n<emoji"
            " document_id=5474667187258006816>😎</emoji> Userbots are different from"
            " regular Telegram bots as <b>they run on the user's account</b> rather"
            " than a bot account. This means that userbots can access more features and"
            " have greater flexibility in terms of the actions they can"
            " perform.\n\n<emoji document_id=5472267631979405211>🚫</emoji> However, it"
            " is important to note that <b>userbots are not officially supported by"
            " Telegram</b> and their use may violate the platform's terms of service."
            " As such, <b>users should exercise caution when using userbots</b> and"
            " ensure that they are not being used for malicious purposes.\n\n"
        ),
    }

    strings_ru = {
        "owner": "Владелец",
        "version": "Версия",
        "build": "Сборка",
        "prefix": "Префикс",
        "uptime": "Аптайм",
        "branch": "Ветка",
        "cpu_usage": "Использование CPU",
        "ram_usage": "Использование RAM",
        "send_info": "Отправить информацию о юзерботе",
        "description": "ℹ Это не раскроет никакой личной информации",
        "_ihandle_doc_info": "Отправить информацию о юзерботе",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Актуальная версия</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Требуется обновление"
            "</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Кастомный текст сообщения в info. Может содержать ключевые слова {me},"
            " {version}, {build}, {prefix}, {platform}, {upd}, {uptime}, {cpu_usage},"
            " {ram_usage}, {branch}"
        ),
        "_cfg_cst_btn": (
            "Кастомная кнопка в сообщении в info. Оставь пустым, чтобы убрать кнопку"
        ),
        "_cfg_banner": "Ссылка на баннер-картинку",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Тебе нужно указать"
            " текст для кастомного инфо</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Текст инфо успешно"
            " изменен</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Что такое"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Userbot"
            " - это <b>сторонняя программа</b>, которая взаимодействует с Telegram API"
            " для выполнения <b>автоматизированных задач от имени пользователя</b>."
            " Юзерботы могут использоваться для автоматизации различных задач, таких"
            " как <b>отправка сообщений, присоединение к каналам, загрузка медиафайлов"
            " и многое другое</b>.\n\n<emoji document_id=5474667187258006816>😎</emoji>"
            " Юзерботы отличаются от обычных ботов в Telegram тем, что <b>они работают"
            " на аккаунте пользователя</b>, а не на бот-аккаунте. Это означает, что они"
            " могут иметь доступ к большему количеству функций и обладают большей"
            " гибкостью в плане выполнения действий.\n\n<emoji"
            " document_id=5472267631979405211>🚫</emoji> Однако важно отметить, что"
            " <b>юзерботы официально не поддерживаются Telegram</b> и их использование"
            " может нарушать условия использования платформы. Поэтому <b>пользователи"
            " должны быть осторожны при их использовании</b> и убедиться, что на их"
            " аккаунте не выполняется вредоносный код.\n\n"
        ),
    }

    strings_fr = {
        "owner": "Propriétaire",
        "version": "Version",
        "build": "Construire",
        "prefix": "Préfixe",
        "uptime": "Uptime",
        "branch": "Branche",
        "cpu_usage": "Utilisation du CPU",
        "ram_usage": "Utilisation de la RAM",
        "send_info": "Envoyer des informations sur l'utilisateurbot",
        "description": "ℹ Cela ne révélera aucune information personnelle",
        "_ihandle_doc_info": "Envoyer des informations sur l'utilisateurbot",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Version à jour</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Mise à jour"
            " requise</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Texte de message personnalisé dans info. Peut contenir les mots clés"
            " {me}, {version}, {build}, {prefix}, {platform}, {upd}, {uptime},"
            " {cpu_usage}, {ram_usage}, {branch}"
        ),
        "_cfg_cst_btn": (
            "Bouton personnalisé dans le message dans info. Laissez vide pour supprimer"
            " le bouton"
        ),
        "_cfg_banner": "Lien vers la bannière de l'image",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Vous devez spécifier"
            " le texte pour l'info personnalisée</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>L'info personnalisée"
            " a bien été modifiée</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Qu'est-ce qu'un"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Userbot"
            " est un <b>programme tiers</b> qui interagit avec l'API Telegram pour"
            " exécuter des <b>tâches automatisées au nom de l'utilisateur</b>. Les"
            " userbots peuvent être utilisés pour automatiser diverses tâches, telles"
            " que <b>l'envoi de messages, l'adhésion aux canaux, le téléchargement de"
            " fichiers multimédias et bien plus encore</b>.\n\n<emoji"
            " document_id=5474667187258006816>😎</emoji> Les userbots diffèrent des bots"
            " Telegram classiques dans le sens où <b>ils fonctionnent sur le compte de"
            " l'utilisateur</b> et non sur un compte de bot. Cela signifie qu'ils"
            " peuvent avoir accès à plus de fonctions et être plus flexibles dans"
            " l'exécution de leurs actions.\n\n<emoji"
            " document_id=5472267631979405211>🚫</emoji> Cependant, il est important de"
            " noter que <b>les userbots ne sont pas officiellement pris en charge par"
            " Telegram</b> et leur utilisation peut enfreindre les conditions"
            " d'utilisation de la plateforme. Par conséquent, <b>les utilisateurs"
            " doivent faire preuve de prudence lors de leur utilisation</b> et"
            " s'assurer que le code malveillant n'est pas exécuté sur leur compte.\n\n"
        ),
    }

    strings_it = {
        "owner": "Proprietario",
        "version": "Versione",
        "build": "Build",
        "prefix": "Prefisso",
        "uptime": "Uptime",
        "branch": "Branch",
        "cpu_usage": "Uso CPU",
        "ram_usage": "Uso RAM",
        "send_info": "Invia info del bot",
        "description": "ℹ Questo non rivelera' alcuna informazione personale",
        "_ihandle_doc_info": "Invia info del bot",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Versione"
            " aggiornata</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Aggiornamento"
            " richiesto</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Messaggio personalizzato per info. Puo' contenere {me}, {version},"
            " {build}, {prefix}, {platform}, {upd}, {uptime}, {cpu_usage}, {ram_usage},"
            " {branch} keywords"
        ),
        "_cfg_cst_btn": "Bottone personalizzato per info. Lascia vuoto per rimuovere",
        "_cfg_banner": "URL dell'immagine banner",
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Che cos'è un"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Il"
            " Userbot è un <b>programma esterno</b> che interagisce con l'API di"
            " Telegram per eseguire <b>compiti automatizzati</b> a nome dell'utente. I"
            " userbot possono essere utilizzati per automatizzare diversi compiti, come"
            " <b>invio di messaggi, iscrizione a canali, caricamento di file"
            " multimediali e molto altro ancora</b>.\n\n<emoji"
            " document_id=5474667187258006816>😎</emoji> I userbot differiscono dai bot"
            " di Telegram nel fatto che <b>funzionano con gli account utente</b> e non"
            " con quelli di bot. Ciò significa che possono avere accesso a più"
            " funzionalità e una maggiore flessibilità nella loro esecuzione.\n\n<emoji"
            " document_id=5472267631979405211>🚫</emoji> Tuttavia, è importante notare"
            " che <b>i userbot non sono supportati ufficialmente da Telegram</b> e"
            " l'utilizzo di quest'ultimi può violare i termini di utilizzo della"
            " piattaforma. Pertanto, <b>gli utenti devono essere cautelosi quando li"
            " utilizzano e assicurarsi che sul loro account non venga eseguito codice"
            " malevolo</b>.\n\n"
        ),
    }

    strings_de = {
        "owner": "Besitzer",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "branch": "Branch",
        "cpu_usage": "CPU Nutzung",
        "ram_usage": "RAM Nutzung",
        "send_info": "Botinfo senden",
        "description": "ℹ Dies enthüllt keine persönlichen Informationen",
        "_ihandle_doc_info": "Sende Botinfo",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji> <b>Aktuell</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Update benötigt"
            "</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Custom message for info. May contain {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {cpu_usage}, {ram_usage}, {branch} keywords"
        ),
        "_cfg_cst_btn": "Custom button for info. Leave empty to remove button",
        "_cfg_banner": "URL to image banner",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Bitte gib einen"
            " Text an, um die Info zu ändern</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Info geändert</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Was ist ein"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Userbot"
            " ist ein <b>externe Programm</b>, welches mit der Telegram API"
            " kommuniziert, um <b>automatisierte Aufgaben</b> für den Benutzer"
            " auszuführen. Userbots können benutzt werden, um verschiedene Aufgaben zu"
            " automatisieren, wie zum Beispiel <b>Nachrichten senden, Kanäle beitreten,"
            " Medien hochladen und vieles mehr</b>.\n\n<emoji"
            " document_id=5474667187258006816>😎</emoji> Userbots unterscheiden sich von"
            " normalen Telegram Bots darin, dass <b>sie auf einem Benutzerkonto"
            " laufen</b> und nicht auf einem Botkonto. Das bedeutet, dass sie mehr"
            " Funktionen haben und mehr Flexibilität bei der Ausführung von Aktionen"
            " haben.\n\n<emoji document_id=5472267631979405211>🚫</emoji> Es ist jedoch"
            " wichtig zu beachten, dass <b>Userbots nicht offiziell von Telegram"
            " unterstützt werden</b> und ihre Verwendung gegen die Nutzungsbedingungen"
            " von Telegram verstoßen kann. Deshalb <b>müssen Benutzer vorsichtig sein,"
            " wenn sie Userbots benutzen</b> und sicherstellen, dass auf ihrem Konto"
            " kein schädlicher Code ausgeführt wird.\n\n"
        ),
    }

    strings_uz = {
        "owner": "Egasi",
        "version": "Versiya",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Ishlash vaqti",
        "branch": "Vetkasi",
        "cpu_usage": "CPU foydalanish",
        "ram_usage": "RAM foydalanish",
        "send_info": "Bot haqida ma'lumot",
        "description": "ℹ Bu shaxsiy ma'lumot emas",
        "_ihandle_doc_info": "Bot haqida ma'lumot",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>So'ngi versia</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Yangilash"
            " kerak</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Xabar uchun shaxsiy xabar. {me}, {version}, {build}, {prefix}, {platform},"
            " {upd}, {uptime}, {cpu_usage}, {ram_usage}, {branch} kalit so'zlarni"
            " ishlatishingiz mumkin"
        ),
        "_cfg_cst_btn": (
            "Xabar uchun shaxsiy tugma. Tugmani o'chirish uchun bo'sh qoldiring"
        ),
        "_cfg_banner": "URL uchun rasmi",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Ma'lumotni"
            " o'zgartirish uchun matn kiriting</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Ma'lumotlar"
            " o'zgartirildi</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Userbot"
            " nima?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Userbot -"
            " bu <b>tashqi dastur</b>, <b>foydalanuvchi tomonidan</b> ishlaydigan"
            " Telegram API bilan aloqa qilish uchun ishlatiladi. Userbotlarni"
            " <b>avtomatlashtirilgan vazifalarni bajarish</b> uchun ishlatish mumkin."
            " Userbotlar <b>habarlarni yuborish, kanallarga ulanish, media fayllarni"
            " yuklash va boshqa biror vazifa bajarish</b> uchun ishlatilishi"
            " mumkin.\n\n<emoji document_id=5474667187258006816>😎</emoji> Userbotlar"
            " Telegramda obyektiv bo'lgan botlardan farqli. Userbotlar"
            " <b>bot-hisobotlaridan</b> ishlaydi, <b>foydalanuvchi hisobotidan</b>"
            " ishlaydi. Bu shuni anglatadiki, userbotlar <b>Telegram platformasida"
            " ishlash</b> uchun kerakli funksiyalarga ega va ular <b>qanday vazifalarni"
            " bajarishni</b> xohlayotgan bo'lishi mumkin.\n\n<emoji"
            " document_id=5472267631979405211>🚫</emoji> Lekin shuni unutmangki,"
            " <b>userbotlar Telegram tomonidan rasmiylashtirilmagan</b> va ularni"
            " ishlatish <b>Telegram shartlari bilan</b> bir-biriga mos kelmaydi."
            " Shuning uchun <b>foydalanuvchilar userbotlarni ishlatishda</b> qattiq"
            " bo'lishi lozim va <b>ularning hisobotlari</b> bo'lmaguncha biror zararli"
            " kod yuklamasini tekshirish kerak.\n\n"
        ),
    }

    strings_tr = {
        "owner": "Sahip",
        "version": "Sürüm",
        "build": "Derleme",
        "prefix": "Önek",
        "uptime": "Aktif Süre",
        "branch": "Dal",
        "cpu_usage": "CPU Kullanımı",
        "ram_usage": "RAM Kullanımı",
        "send_info": "Bot hakkında bilgi",
        "description": "ℹ️ Kişisel bilgileri tehlikeye atmaz",
        "_ihandle_doc_info": "Bot hakkında bilgi",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji> <b>Güncel</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Güncelleme"
            " gerekli</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Kişisel mesaj için bilgi. {me}, {version}, {build}, {prefix}, {platform},"
            " {upd}, {uptime}, {cpu_usage}, {ram_usage}, {branch} anahtar kelimeleri"
            " kullanılabilir"
        ),
        "_cfg_cst_btn": "Kişisel tuş için bilgi. Tuşu kaldırmak için boş bırakın",
        "_cfg_banner": "Resim için URL",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Bilgiyi değiştirmek"
            " için herhangi bir metin girin</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Bilgiler"
            " değiştirildi</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Neden"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Userbot"
            " - <b>Telegram API ile</b> <b>Kullanıcı adına</b> <b>otomatikleştirilmiş"
            " işlemleri</b> yürüten bir <b>üçüncü taraf programıdır</b>. Userbotlar,"
            " <b>mesaj gönderme, kanallara katılma, medya yükleme ve diğer işlemleri"
            " otomatize etmek için kullanılabilecek</b> birçok işi otomatize etmenizi"
            " sağlar.\n\n<emoji document_id=5474667187258006816>😎</emoji> Userbotlar,"
            " <b>normal Telegram botlarından farklı olarak</b>, <b>Kullanıcı hesabında"
            " çalışırlar</b>. Bu, <b>daha fazla iş yapmalarına</b> ve <b>daha esnek"
            " olmalarına</b> olanak verir.\n\n<emoji"
            " document_id=5472267631979405211>🚫</emoji> Bununla birlikte, <b>Userbotlar"
            " Telegram tarafından resmi olarak desteklenmez</b> ve bunların kullanımı"
            " platformun kullanım koşullarını ihlal edebilir. Kullanıcılar <b>bu"
            " nedenle Userbotların kullanımını dikkatli bir şekilde yapmalıdır</b> ve"
            " kullanıcı hesaplarında kötü niyetli kodun çalıştırılmadığından emin"
            " olmalıdırlar.\n\n"
        ),
    }

    strings_es = {
        "owner": "Propietario",
        "version": "Versión",
        "build": "Construir",
        "prefix": "Prefijo",
        "uptime": "Tiempo de actividad",
        "branch": "Rama",
        "cpu_usage": "Uso de CPU",
        "ram_usage": "Uso de RAM",
        "send_info": "Enviar información del bot",
        "description": "ℹ️ No exponga su información personal",
        "_ihandle_doc_info": "Información del bot",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Actualizado</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Actualización"
            " necesaria</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Información del mensaje personalizado. Puede usar las palabras clave {me},"
            " {version}, {build}, {prefix}, {platform}, {upd}, {uptime}, {cpu_usage},"
            " {ram_usage}, {branch}"
        ),
        "_cfg_cst_btn": (
            "Información del botón personalizado. Eliminar el botón deje en blanco"
        ),
        "_cfg_banner": "URL de la imagen",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Para cambiar la"
            " información, ingrese algún texto</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Información cambiada"
            " con éxito</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>¿Qué es un"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Un"
            " Userbot es un <b>programa externo</b> que interactúa con la API de"
            " Telegram para realizar <b>tareas automatizadas en nombre del usuario</b>."
            " Los userbots pueden utilizarse para automatizar diversas tareas, como"
            " <b>envío de mensajes, unirse a canales, subir archivos multimedia y mucho"
            " más</b>.\n\n<emoji document_id=5474667187258006816>😎</emoji> Los userbots"
            " se diferencian de los bots normales de Telegram en que <b>trabajan en la"
            " cuenta del usuario</b> en lugar de en una cuenta de bot. Esto significa"
            " que tienen acceso a más funciones y son más flexibles a la hora de"
            " realizar acciones.\n\n<emoji document_id=5472267631979405211>🚫</emoji>"
            " Sin embargo, es importante señalar que <b>los userbots no son oficiales y"
            " no son compatibles con Telegram</b> y su uso puede violar los términos de"
            " servicio de la plataforma. Por lo tanto, <b>los usuarios deben tener"
            " cuidado al usarlos</b> y asegurarse de que en su cuenta no se ejecute"
            " código malicioso.\n\n"
        ),
    }

    strings_kk = {
        "owner": "Әкімші",
        "version": "Нұсқасы",
        "build": "Құрылған",
        "prefix": "Бастауыш",
        "uptime": "Қосылған кезең",
        "branch": "Бөлімі",
        "cpu_usage": "CPU қолданымы",
        "ram_usage": "RAM қолданымы",
        "send_info": "Бот туралы ақпарат",
        "description": "ℹ️ Жеке мәліметтеріңізді қорғау",
        "_ihandle_doc_info": "Бот туралы ақпарат",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Жаңартылған</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Жаңарту"
            " талап етіледі</b> <code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Жеке хабарлама үшін ақпарат. {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {cpu_usage}, {ram_usage}, {branch} кілт"
            " сөздерді қолдана аласыз"
        ),
        "_cfg_cst_btn": "Жеке түйме үшін ақпарат. Түймесін жою үшін бос қалдырыңыз",
        "_cfg_banner": "Сурет үшін URL",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Ақпаратты өзгерту үшін"
            " ештеңе енгізбеңіз</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Ақпарат сәтті"
            " өзгертілді</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Пайдаланушы боттарды"
            " қандай болады?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji>"
            " Пайдаланушы боттар - <b>шетел программа</b>, ол Telegram API мен"
            " қолданушының атымен байланысады және <b>автоматтандырылған жұмыстарды"
            " өткізеді</b>. Пайдаланушы боттар <b>хабарламаларды жіберу, каналға"
            " қосылу, медиа файлдарды жүктеу және басқа қарастырылмаған жұмыстарды"
            " жасау</b> үшін пайдаланылады.\n\n<emoji"
            " document_id=5474667187258006816>😎</emoji> Пайдаланушы боттар Telegram"
            " боттарынан айырмалы, себебі олар <b>пайдаланушының аккаунтымен жұмыс"
            " істейді</b>, бот-аккаунтпен жұмыс істеуге берілмейді. Бұл оларға"
            " <b>қатысуға болатын көп көрсеткіштерге және жұмыс істеуге көп"
            " құралдарға</b> болатын жақсы құралдарды береді.\n\n<emoji"
            " document_id=5472267631979405211>🚫</emoji> Одан қосымша, <b>пайдаланушы"
            " боттардың Telegram үшін официалды қолдау көрсетуі жоқ</b> және оларды"
            " пайдалану орталығының қолдану шарттарын бүгінге дейін бұзуы мүмкін."
            " Оларды пайдалану <b>қолданушыларға қатысатын нәтижелердің барлығын"
            " қарауға</b> мүмкіндік береді.\n\n"
        ),
    }

    strings_tt = {
        "owner": "Идарәче",
        "version": "Версия",
        "build": "Билд",
        "prefix": "Префикс",
        "uptime": "Тәртиби вакыты",
        "branch": "Кишелек",
        "cpu_usage": "CPU җыелмасы",
        "ram_usage": "RAM җыелмасы",
        "send_info": "Бот турында мәгълүматны җибәрү",
        "description": "ℹ️ Шәхси мәгълүматыңызны тыяу",
        "_ihandle_doc_info": "Бот турында мәгълүмат",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji> <b>Яңартылган</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji> <b>Яңартылу"
            " таләп ителә</b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Шәхси хәбәр мәгълүматы. {me}, {version}, {build}, {prefix}, {platform},"
            " {upd}, {uptime}, {cpu_usage}, {ram_usage}, {branch} күчермәләрен җибәрү"
            " мөмкин"
        ),
        "_cfg_cst_btn": "Шәхси төймә мәгълүматы. Төймәне юймагыч, буш җибәрү",
        "_cfg_banner": "Сүрәт URL-ы",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Мәгълүматны"
            " үзгәртү өчен, мәгълүматны кертегез</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Мәгълүмат"
            " мөмкин булды</b>"
        ),
        "desc": (
            "<emoji document_id=5188377234380954537>🌘</emoji> <b>Катта"
            " Userbot?</b>\n\n<emoji document_id=5472238129849048175>😎</emoji> Userbot"
            " - бу <b>сайлама программа</b>, калан <b>Telegram API</b> ишләп <b>хисап"
            " язмасы исеме</b> белән <b>автоматик өтәргә</b> мөмкин. Юзерботлар <b>хат"
            " җибәрү, каналга җибәрү, медиа файлларны юкләү вә күбрәк башка"
            " мәгълүматлар</b> ны автоматик өтәргә мөмкин.\n\n<emoji"
            " document_id=5474667187258006816>😎</emoji> Юзерботлар <b>хисап язмасы"
            " исеме</b> белән бергәндә, <b>бот исеме</b> белән бермәгәндән яңа"
            " исемлектә булыр.\n\n<emoji document_id=5472267631979405211>🚫</emoji>"
            " <b>Юзерботлар Telegram</b> тарафыннан <b>дөрес ярдәмендәр</b> булганында"
            " ясалган. <b>Юзерботлар</b> <b>хисап язмасы исеме</b> белән бергәндә,"
            " <b>бот исеме</b> белән бермәгәндән яңа исемлектә булыр. <b>Юзерботлар</b>"
            " <b>хисап язмасы исеме</b> белән бергәндә, <b>бот исеме</b> белән"
            " бермәгәндән яңа исемлектә булыр.\n\n"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button",
                ["🌘 Support chat", "https://t.me/hikka_talks"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Union(
                    loader.validators.Series(fixed_len=2),
                    loader.validators.NoneType(),
                ),
            ),
            loader.ConfigValue(
                "banner_url",
                "https://github.com/hikariatama/assets/raw/master/hikka_banner.mp4",
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Link(),
            ),
        )

    def _render_info(self, inline: bool) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = '<b><a href="tg://user?id={}">{}</a></b>'.format(
            self._client.hikka_me.id,
            utils.escape_html(get_display_name(self._client.hikka_me)),
        )
        build = utils.get_commit_url()
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"

        platform = utils.get_named_platform()

        for emoji, icon in {
            "🍊": "<emoji document_id=5449599833973203438>🧡</emoji>",
            "🍇": "<emoji document_id=5449468596952507859>💜</emoji>",
            "❓": "<emoji document_id=5407025283456835913>📱</emoji>",
            "🍁": "<emoji document_id=6332120630099445554>🍁</emoji>",
            "🦾": "<emoji document_id=5386766919154016047>🦾</emoji>",
            "🚂": "<emoji document_id=5359595190807962128>🚂</emoji>",
            "🐳": "<emoji document_id=5431815452437257407>🐳</emoji>",
            "🕶": "<emoji document_id=5407025283456835913>📱</emoji>",
            "🐈‍⬛": "<emoji document_id=6334750507294262724>🐈‍⬛</emoji>",
            "✌️": "<emoji document_id=5469986291380657759>✌️</emoji>",
            "📻": "<emoji document_id=5471952986970267163>💎</emoji>",
            "🎃": "<emoji document_id=5370610867094166617>🎃</emoji>",
        }.items():
            platform = platform.replace(emoji, icon)

        return (
            (
                "<b>🌘 Hikka</b>\n"
                if "hikka" not in self.config["custom_message"].lower()
                else ""
            )
            + self.config["custom_message"].format(
                me=me,
                version=_version,
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=utils.formatted_uptime(),
                cpu_usage=utils.get_cpu_usage(),
                ram_usage=f"{utils.get_ram_usage()} MB",
                branch=version.branch,
            )
            if self.config["custom_message"]
            else (
                f'<b>{{}}</b>\n\n<b>{{}} {self.strings("owner")}:</b> {me}\n\n<b>{{}}'
                f' {self.strings("version")}:</b> {_version} {build}\n<b>{{}}'
                f' {self.strings("branch")}:'
                f"</b> <code>{version.branch}</code>\n{upd}\n\n<b>{{}}"
                f' {self.strings("prefix")}:</b> {prefix}\n<b>{{}}'
                f' {self.strings("uptime")}:'
                f"</b> {utils.formatted_uptime()}\n\n<b>{{}}"
                f' {self.strings("cpu_usage")}:'
                f"</b> <i>~{utils.get_cpu_usage()} %</i>\n<b>{{}}"
                f' {self.strings("ram_usage")}:'
                f"</b> <i>~{utils.get_ram_usage()} MB</i>\n<b>{{}}</b>"
            ).format(
                *map(
                    lambda x: utils.remove_html(x) if inline else x,
                    (
                        (
                            utils.get_platform_emoji()
                            if self._client.hikka_me.premium and not inline
                            else "🌘 Hikka"
                        ),
                        "<emoji document_id=5373141891321699086>😎</emoji>",
                        "<emoji document_id=5469741319330996757>💫</emoji>",
                        "<emoji document_id=5449918202718985124>🌳</emoji>",
                        "<emoji document_id=5472111548572900003>⌨️</emoji>",
                        "<emoji document_id=5451646226975955576>⌛️</emoji>",
                        "<emoji document_id=5431449001532594346>⚡️</emoji>",
                        "<emoji document_id=5359785904535774578>💼</emoji>",
                        platform,
                    ),
                )
            )
        )

    def _get_mark(self):
        return (
            {
                "text": self.config["custom_button"][0],
                "url": self.config["custom_button"][1],
            }
            if self.config["custom_button"]
            else None
        )

    @loader.inline_handler(
        thumb_url="https://img.icons8.com/external-others-inmotus-design/344/external-Moon-round-icons-others-inmotus-design-2.png"
    )
    @loader.inline_everyone
    async def info(self, _: InlineQuery) -> dict:
        """Send userbot info"""

        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            **(
                {"photo": self.config["banner_url"], "caption": self._render_info(True)}
                if self.config["banner_url"]
                else {"message": self._render_info(True)}
            ),
            "thumb": (
                "https://github.com/hikariatama/Hikka/raw/master/assets/hikka_pfp.png"
            ),
            "reply_markup": self._get_mark(),
        }

    @loader.command(
        ru_doc="Отправляет информацию о боте",
        fr_doc="Envoie des informations sur le bot",
        it_doc="Invia informazioni sul bot",
        de_doc="Sendet Informationen über den Bot",
        tr_doc="Bot hakkında bilgi gönderir",
        uz_doc="Bot haqida ma'lumot yuboradi",
        es_doc="Envía información sobre el bot",
        kk_doc="Бот туралы ақпарат жібереді",
    )
    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Send userbot info"""

        if self.config["custom_button"]:
            await self.inline.form(
                message=message,
                text=self._render_info(True),
                reply_markup=self._get_mark(),
                **(
                    {"photo": self.config["banner_url"]}
                    if self.config["banner_url"]
                    else {}
                ),
            )
        else:
            await utils.answer_file(
                message,
                self.config["banner_url"],
                self._render_info(False),
            )

    @loader.unrestricted
    @loader.command(
        ru_doc="Отправить информацию по типу 'Что такое Хикка?'",
        fr_doc="Envoyer des informations du type 'Qu'est-ce que Hikka?'",
        it_doc="Invia informazioni del tipo 'Cosa è Hikka?'",
        de_doc="Sende Informationen über den Bot",
        tr_doc="Bot hakkında bilgi gönderir",
        uz_doc="Bot haqida ma'lumot yuborish",
        es_doc="Enviar información sobre el bot",
        kk_doc="Бот туралы ақпарат жіберу",
    )
    async def hikkainfo(self, message: Message):
        """Send info aka 'What is Hikka?'"""
        await utils.answer(message, self.strings("desc"))

    @loader.command(
        ru_doc="<текст> - Изменить текст в .info",
        fr_doc="<texte> - Changer le texte dans .info",
        it_doc="<testo> - Cambia il testo in .info",
        de_doc="<text> - Ändere den Text in .info",
        tr_doc="<metin> - .info'da metni değiştir",
        uz_doc="<matn> - .info'dagi matnni o'zgartirish",
        es_doc="<texto> - Cambiar el texto en .info",
        kk_doc="<мәтін> - .info мәтінін өзгерту",
    )
    async def setinfo(self, message: Message):
        """<text> - Change text in .info"""
        args = utils.get_args_html(message)
        if not args:
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))
