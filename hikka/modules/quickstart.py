# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import os
from random import choice

from .. import loader, translations, utils
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)

imgs = [
    "https://i.gifer.com/GmUB.gif",
    "https://i.gifer.com/Afdn.gif",
    "https://i.gifer.com/3uvT.gif",
    "https://i.gifer.com/2qQQ.gif",
    "https://i.gifer.com/Lym6.gif",
    "https://i.gifer.com/IjT4.gif",
    "https://i.gifer.com/A9H.gif",
]


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    strings = {
        "name": "Quickstart",
        "base": """🌘🇬🇧 <b>Hello.</b> You've just installed <b>Hikka</b> userbot.

❓ <b>Need help?</b> Feel free to join our support chat. We help <b>everyone</b>.

📼 <b>You can find and install modules using @hikkamods_bot. Simply enter your search query and click ⛩ Install on needed module</b>

📣 <b>Check out community made channels with modules: <a href="https://t.me/hikka_ub/126">show</a></b>

💁‍♀️ <b>Quickstart:</b>

1️⃣ <b>Type</b> <code>.help</code> <b>to see modules list</b>
2️⃣ <b>Type</b> <code>.help &lt;ModuleName/command&gt;</code> <b>to see help of module ModuleName</b>
3️⃣ <b>Type</b> <code>.dlmod &lt;link&gt;</code> <b>to load module from link</b>
4️⃣ <b>Type</b> <code>.loadmod</code> <b>with reply to file to install module from it</b>
5️⃣ <b>Type</b> <code>.unloadmod &lt;ModuleName&gt;</code> <b>to unload module ModuleName</b>

💡 <b>Hikka supports modules from Friendly-Telegram, DragonUserbot and GeekTG, as well as its own ones.</b>""",
        "railway": (
            "🚂 <b>Your userbot is installed on Railway</b>. This platform has only"
            " <b>500 free hours per month</b>. Once this limit is reached, your"
            " <b>Hikka will be frozen</b>. Next month <b>you will need to go to"
            " https://railway.app and restart it</b>."
        ),
        "lavhost": (
            "✌️ <b>Your userbot is installed on lavHost</b>. Make sure to join @lavhost"
            " for important notifications and updates. All questions regarding the"
            " platform should be asked in @lavhostchat."
        ),
        "miyahost": (
            "🎃 <b>Your userbot is installed on MiyaHost</b>. Make sure to join"
            " @miyahost for important notifications and updates. All questions"
            " regarding the platform should be asked in @miyahost_support."
        ),
        "language_saved": "🇬🇧 Language saved!",
        "language": "🇬🇧 English",
        "btn_support": "🥷 Support chat",
    }

    strings_ru = {
        "base": """🌘🇷🇺 <b>Привет.</b> Твой юзербот <b>Hikka</b> установлен.

❓ <b>Нужна помощь?</b> Вступай в наш чат поддержки. Мы помогаем <b>всем</b>.

📼 <b>Ты можешь искать и устанавливать модули через @hikkamods_bot. Просто введи поисковый запрос и нажми ⛩ Install на нужном модуле</b>

📣 <b>Загляни в каналы с модулями, созданными комьюнити: <a href="https://t.me/hikka_ub/126">показать</a></b>

💁‍♀️ <b>Быстрый гайд:</b>

1️⃣ <b>Напиши</b> <code>.help</code> <b>чтобы увидеть список модулей</b>
2️⃣ <b>Напиши</b> <code>.help &lt;Название модуля/команда&gt;</code> <b>чтобы увидеть описание модуля</b>
3️⃣ <b>Напиши</b> <code>.dlmod &lt;ссылка&gt;</code> <b>чтобы загрузить модуль из ссылка</b>
4️⃣ <b>Напиши</b> <code>.loadmod</code> <b>ответом на файл, чтобы загрузить модуль из него</b>
5️⃣ <b>Напиши</b> <code>.unloadmod &lt;Название модуля&gt;</code> <b>чтобы выгрузить модуль</b>

💡 <b>Hikka поддерживает модули из Friendly-Telegram, DragonUserbot и GeekTG, а также свои собственные.</b>
""",
        "railway": (
            "🚂 <b>Твой юзербот установлен на Railway</b>. На этой платформе ты"
            " получаешь только <b>500 бесплатных часов в месяц</b>. Когда лимит будет"
            " достигнет, твой <b>юзербот будет заморожен</b>. В следующем месяце <b>ты"
            " должен будешь перейти на https://railway.app и перезапустить его</b>."
        ),
        "lavhost": (
            "✌️ <b>Твой юзербот установлен на lavHost</b>. Вступи в @lavhost, чтобы"
            " получать важные уведомления и обновления. Все вопросы, связанные с"
            " платформой, следует задавать в @lavhostchat."
        ),
        "miyahost": (
            "🎃 <b>Твой юзербот установлен на MiyaHost</b>. Вступи в @miyahost, чтобы"
            " получать важные уведомления и обновления. Все вопросы, связанные с"
            " платформой, следует задавать в @miyahost_support."
        ),
        "language_saved": "🇷🇺 Язык сохранен!",
        "language": "🇷🇺 Русский",
        "btn_support": "🥷 Чат поддержки",
    }

    strings_it = {
        "base": """🌘🇮🇹 <b>Ciao.</b> Il tuo userbot <b>Hikka</b> è stato installato.

❓ <b>Hai bisogno di aiuto?</b> Entra nel nostro gruppo di supporto. Aiutiamo <b>tutti</b>.

📼 <b>Puoi cercare e installare moduli tramite @hikkamods_bot. Basta inserire una richiesta di ricerca e premere ⛩ Installa sul modulo desiderato</b>

📣 <b>Guarda i canali dei moduli creati dalla community: <a href="https://t.me/hikka_ub/126">mostra</a></b>

💁‍♀️ <b>Guida rapida:</b>

1️⃣ <b>Scrivi</b> <code>.help</code> <b>per vedere l'elenco dei moduli</b>
2️⃣ <b>Scrivi</b> <code>.help &lt;Nome del modulo/comando&gt;</code> <b>per vedere la descrizione del modulo</b>
3️⃣ <b>Scrivi</b> <code>.dlmod &lt;link&gt;</code> <b>per caricare il modulo dal link</b>
4️⃣ <b>Scrivi</b> <code>.loadmod</code> <b>come risposta al file per caricare il modulo da esso</b>
5️⃣ <b>Scrivi</b> <code>.unloadmod &lt;Nome del modulo&gt;</code> <b>per scaricare il modulo</b>

💡 <b>Hikka supporta i moduli di Friendly-Telegram, DragonUserbot e GeekTG, oltre ai suoi moduli personali.</b>
""",
        "railway": (
            "🚂 <b>Il tuo userbot è stato installato su Railway.</b> Su questa"
            " piattaforma ricevi solo <b>500 ore gratuite al mese</b>. Quando il limite"
            " verrà raggiunto, <b>il tuo userbot verrà congelato</b>. Nel mese"
            " successivo <b>devi andare su https://railway.app e riavviarlo</b>."
        ),
        "lavhost": (
            "✌️ <b>Il tuo userbot è installato su lavHost</b>. Unisciti a @lavhost, per"
            " ricevere importanti notifiche e aggiornamenti. Tutte le domande relative"
            " alla piattaforma devono essere poste in @lavhostchat."
        ),
        "miyahost": (
            "🎃 <b>Il tuo userbot è installato su MiyaHost</b>. Unisciti a @miyahost,"
            " per ricevere importanti notifiche e aggiornamenti. Tutte le domande"
            " relative alla piattaforma devono essere poste in @miyahost_support."
        ),
        "language_saved": "🇮🇹 Lingua salvata!",
        "language": "🇮🇹 Italiano",
        "btn_support": "🥷 Gruppo di supporto",
    }

    strings_de = {
        "base": """🌘🇩🇪 <b>Hallo.</b> Dein Userbot <b>Hikka</b> ist installiert.

❓ <b>Brauchst du Hilfe?</b> Trete unserem Support-Chat bei. Wir helfen <b>allen</b>.

📼 <b>Du kannst Module über @hikkamods_bot suchen und installieren. Gib einfach einen Suchbegriff ein und drücke auf ⛩ Install auf dem gewünschten Modul</b>

📣 <b>Schaue dir die Module-Kanäle an, die von der Community erstellt wurden: <a href="https://t.me/hikka_ub/126">anzeigen</a></b>

💁‍♀️ <b>Schnellstart:</b>

1️⃣ <b>Schreibe</b> <code>.help</code> <b>um eine Liste der Module zu sehen</b>
2️⃣ <b>Schreibe</b> <code>.help &lt;Modulname/Befehl&gt;</code> <b>um die Beschreibung des Moduls zu sehen</b>
3️⃣ <b>Schreibe</b> <code>.dlmod &lt;Link&gt;</code> <b>um ein Modul aus dem Link zu laden</b>
4️⃣ <b>Schreibe</b> <code>.loadmod</code> <b>als Antwort auf eine Datei, um ein Modul aus der Datei zu laden</b>
5️⃣ <b>Schreibe</b> <code>.unloadmod &lt;Modulname&gt;</code> <b>um ein Modul zu entladen</b>

💡 <b>Hikka unterstützt Module von Friendly-Telegram, DragonUserbot und GeekTG sowie eigene Module.</b>
""",
        "railway": (
            "🚂 <b>Dein Userbot ist auf Railway installiert</b>. Du erhältst nur <b>500"
            " kostenlose Stunden pro Monat</b> auf dieser Plattform. Wenn das Limit"
            " erreicht ist, wird dein <b>Userbot eingefroren</b>. Im nächsten Monat"
            " musst du zu https://railway.app gehen und ihn neu starten.</b>"
        ),
        "lavhost": (
            "✌️ <b>Dein Userbot ist auf lavHost installiert</b>. Trete @lavhost bei, um"
            " wichtige Benachrichtigungen und Updates zu erhalten. Alle Fragen, die"
            " sich auf die Plattform beziehen, sollten im @lavhostchat gestellt werden."
        ),
        "miyahost": (
            "🎃 <b>Dein Userbot ist auf MiyaHost installiert</b>. Trete @miyahost bei,"
            " um wichtige Benachrichtigungen und Updates zu erhalten. Alle Fragen, die"
            " sich auf die Plattform beziehen, sollten im @miyahost_support gestellt"
            " werden."
        ),
        "language_saved": "🇩🇪 Sprache gespeichert!",
        "language": "🇩🇪 Deutsch",
        "btn_support": "🥷 Support-Chat",
    }

    strings_uz = {
        "base": """🌘🇺🇿 <b>Salom.</b> <b>Hikka</b> Sizning yuzer botingiz sozlandi.

❓ <b>Yordam kerakmi?</b> Siz bizning qollab quvvatlash guruhimizga qo'shilishingiz mumkin. guruhimzda  <b>barcha savollaringizga javob olasiz</b>.

📼 <b>Modullar @hikkamods_bot ushbu botimiz orqali siz har qanday yuzerbotga tegishli bo'lgan modullarni o'rnatishingiz mumkun botga kalit so'zni yuboring va  ⛩ O'rnatish tugmasini bosing</b>

📣 <b>Homiylar tomonidan yaratilgan modullar kanalini ko'rish: <a href="https://t.me/hikka_ub/126">kanalni ko'rish</a></b>

💁‍♀️ <b>Tez ishga tushurish:</b>

1️⃣ <b>Modullar royhatini ko'rish uchun</b> <code>.help buyrug'ini</code> <b>yozing</b>
2️⃣ <b>Modul haqida ma'lumot olish uchun</b> <code>.help &lt;Modul nomi/buyruq&gt;</code> <b>yozing</b>
3️⃣ <b>Modulni havola orqali o'rnatish uchun</b> <code>.dlmod &lt;Link&gt;</code> <b>yozing</b>
4️⃣ <b>Modulni fayl orqali yuklash uchun</b> <code>.loadmod</code> <b>faylga javoban yozing</b>
5️⃣ <b>Modulni olib tashlash uchun</b> <code>.unloadmod &lt;Modul nomi&gt;</code> <b>yozing</b>

💡 <b>Hikka, Friendly-Telegram, DragonUserbot ve GeekTG O'z Modullarini qollab quvvatlaydi.</b>
""",
        "railway": (
            "🚂 <b>Sizning yuzerbotingiz Railwayda o'rnatilgan</b>. Bu platforma,"
            " <b>oyiga atigi 500 soat bepul jihati</b> Railway bergan muddat tugagandan"
            " so'ng sizning bo'tingiz  <b>to'xtatiladi</b>. Keyingi oy,"
            " https://railway.app havolasi orqali yuzerbotingizni qayta ishga tushira"
            " olasiz.</b>"
        ),
        "lavhost": (
            "✌️ <b>Sizning foydalanuvchi botingiz lavHost-da o'rnatildi</b>. Kiritish"
            " uchun @lavhost ga a'zo bo'ling, shuningdek muhim xabarlar va"
            " yangilanishlar olishingiz mumkin. Platforma haqida savollaringizni"
            " @lavhostchat ga yozing."
        ),
        "miyahost": (
            "🎃 <b>Sizning foydalanuvchi botingiz MiyaHost-da o'rnatildi</b>. Kiritish"
            " uchun @miyahost ga a'zo bo'ling, shuningdek muhim xabarlar va"
            " yangilanishlar olishingiz mumkin. Platforma haqida savollaringizni"
            " @miyahost_support ga yozing."
        ),
        "language_saved": "🇺🇿 Til saqlandi!",
        "language": "🇺🇿 O'zbekcha",
        "btn_support": "🥷 Qo'llab-quvvatlash guruhi",
    }

    strings_tr = {
        "base": """🌘🇹🇷 <b>Merhaba.</b> <b>Hikka</b> kullanıcı botunuz kuruldu.

❓ <b>Yardıma mı ihtiyacınız var?</b> Yardım grubumuza katılabilirsin. Herkese <b>yardım ediyoruz</b>.

📼 <b>Modülleri @hikkamods_bot ile arayabilir ve kurabilirsiniz. Sadece anahtar kelimeleri girin ve istediğiniz modülün ⛩ Kur butonuna basın</b>

📣 <b>Topluluk tarafından oluşturulan modül kanalları görüntüleyin: <a href="https://t.me/hikka_ub/126">göster</a></b>

💁‍♀️ <b>Hızlı başlangıç:</b>

1️⃣ <b>Modüller listesini görmek için</b> <code>.help</code> <b>yazın</b>
2️⃣ <b>Modül hakkında bilgi almak için</b> <code>.help &lt;Modul adı/Komut&gt;</code> <b>yazın</b>
3️⃣ <b>Bir bağlantıdan modül yüklemek için</b> <code>.dlmod &lt;Link&gt;</code> <b>yazın</b>
4️⃣ <b>Bir modülü bir dosyadan yüklemek için</b> <code>.loadmod</code> <b>bir dosyanın yanıtını yazın</b>
5️⃣ <b>Bir modülü kaldırmak için</b> <code>.unloadmod &lt;Modul adı&gt;</code> <b>yazın</b>

💡 <b>Hikka, Friendly-Telegram, DragonUserbot ve GeekTG modüllerini de dahil olmak üzere kendi modüllerini destekler.</b>
""",
        "railway": (
            "🚂 <b>Kullanıcı botunuz Railway'de kuruldu</b>. Bu platform, <b>aylık"
            " sadece 500 saati ücretsiz olarak</b> sağlamaktadır. Sınırı aştığınızda,"
            " kullanıcı botunuz <b>durdurulur</b>. Gelecek ay, https://railway.app"
            " adresinden botunuzu yeniden başlatmanız gerekmektedir.</b>"
        ),
        "lavhost": (
            "✌️ <b>lavHost'a kurulumunuz tamamlandı.</b> Önemli duyurular ve"
            " güncellemeleri almak için @lavhost'a katılın. Platformla ilgili"
            " sorularınızı @lavhostchat'da sorabilirsiniz."
        ),
        "miyahost": (
            "🎃 <b>MiyaHost'a kurulumunuz tamamlandı.</b> Önemli duyurular ve"
            " güncellemeleri almak için @miyahost'a katılın. Platformla ilgili"
            " sorularınızı @miyahost_support'da sorabilirsiniz."
        ),
        "language_saved": "🇹🇷 Dil kaydedildi!",
        "language": "🇹🇷 Türkçe",
        "btn_support": "🥷 Destek grubu",
    }

    strings_es = {
        "base": """
📼 <b>Para buscar e instalar módulos, vaya a @hikkamods_bot y escriba las palabras clave.</b>

📣 <b>Para ver los canales de la comunidad creados, haga clic aquí: <a href="https://t.me/hikka_ub/126">Ver</a></b>

💁‍♀️ <b>Para comenzar de inmediato:</b>

1️⃣ <b>Para ver la lista de módulos, escriba</b> <code>.help</code> <b>y presione</b>
2️⃣ <b>Para obtener información sobre el módulo, escriba</b> <code>.help &lt;nombre del módulo/comando&gt;</code> <b>y presione</b>
3️⃣ <b>Para instalar el módulo desde el enlace, escriba</b> <code>.dlmod &lt;enlace&gt;</code> <b>y presione</b>
4️⃣ <b>Para cargar el módulo desde el archivo, escriba</b> <code>.loadmod</code> <b>y responda al archivo que desea cargar</b>
5️⃣ <b>Para eliminar el módulo, escriba</b> <code>.unloadmod &lt;nombre del módulo&gt;</code> <b>y presione</b>

💡 <b>Para admitir módulos, también incluye Hikka, Friendly-Telegram, DragonUserbot y GeekTG.</b>
""",
        "railway": (
            "🚂 <b>Se ha creado el bot de usuario en Railway</b> esta plataforma ofrece"
            " <b>500 horas gratis al mes</b> una vez que llegue al límite, el <b>bot de"
            " usuario será bloqueado hasta el próximo mes</b> por favor, reinicie <b>el"
            " bot de usuario en https://railway.app</b>"
        ),
        "lavhost": (
            "✌️ <b>Tu bot de usuario está instalado en lavHost</b>. Únete a @lavhost"
            " para recibir notificaciones y actualizaciones importantes. Todas las"
            " preguntas relacionadas con la plataforma deben hacerse en @lavhostchat."
        ),
        "miyahost": (
            "🎃 <b>Tu bot de usuario está instalado en MiyaHost</b>. Únete a @miyahost"
            " para recibir notificaciones y actualizaciones importantes. Todas las"
            " preguntas relacionadas con la plataforma deben hacerse en"
            " @miyahost_support."
        ),
        "language_saved": "🇪🇸 ¡El idioma se ha guardado!",
        "language": "🇪🇸 Español",
        "btn_support": "🥷 Grupo de soporte",
    }

    strings_kk = {
        "base": """🌘🇰🇿 <b>Сәлеметсіз бе.</b> Сіздің <b>Hikka</b> ботыңыз орнатылды.

❓ <b>Көмек керек пе?</b> Біздің көмек сөйлесу кітабына кіріңіз. Біз <b>барлық</b>ға көмектесеміз.

📼 <b>Сіз @hikkamods_bot арқылы модульді іздеу және орнатуға болады. Тапсырыс іздеу құралын енгізіңіз және керек модульдің үстіндегі ⛩ Install түймесін басыңыз</b>

📣 <b>Комьюнити жасаған модульдердің каналына кіріңіз: <a href="https://t.me/hikka_ub/126">көрсету</a></b>

💁‍♀️ <b>Жылдам құрал:</b>

1️⃣ <b>Модульдер тізімін көру үшін</b> <code>.help</code> <b>жазыңыз</b>
2️⃣ <b>Модульдің сипаттамасын көру үшін</b> <code>.help &lt;Модуль/команда атауы&gt;</code> <b>жазыңыз</b>
3️⃣ <b>Сілтемеден модульді орнату үшін</b> <code>.dlmod &lt;сілтеме&gt;</code> <b>жазыңыз</b>
4️⃣ <b>Файлдан модульді орнату үшін</b> <code>.loadmod</code> <b>жазыңыз</b>
5️⃣ <b>Модульді жою үшін</b> <code>.unloadmod &lt;Модуль атауы&gt;</code> <b>жазыңыз</b>

💡 <b>Hikka Friendly-Telegram, DragonUserbot және GeekTG модулдерінен, әйтпесе жеңіл модулдерден қамтамасыз етеді.</b>
""",
        "railway": (
            "🚂 <b>Сіздің ботыңыз Railway платформасында орнатылды.</b> Бұл платформа"
            " <b>айдағы 500 сағаттың бесплаттығын</b> береді. Лимит аяқталғанда,"
            " <b>ботыңыз құлыпталады</b>. Келесі айда <b>https://railway.app және оны"
            " қайта жүктеу қажет</b>."
        ),
        "lavhost": (
            "✌️ <b>Сіздің Жеке ботыңыз lavHost-та орнатылған</b>. Маңызды"
            " хабарландырулар мен жаңартулар алу үшін @lavhost-ға кіріңіз. Платформа"
            " және қателер туралы барлық сұрақтарды @lavhostchat-ға жіберіңіз."
        ),
        "miyahost": (
            "🎃 <b>Сіздің Жеке ботыңыз MiyaHost-та орнатылған</b>. Маңызды"
            " хабарландырулар мен жаңартулар алу үшін @miyahost-ға кіріңіз. Платформа"
            " және қателер туралы барлық сұрақтарды @miyahost_support-ға жіберіңіз."
        ),
        "language_saved": "🇰🇿 Тіл сақталды!",
        "language": "🇰🇿 Қазақша",
        "btn_support": "🥷 Қолдау сөйлесу кітабы",
    }

    strings_tt = {
        "base": """🌘🥟 <b>Сәлам.</b> Сезнең юзербот <b>Hikka</b> урнаштырылган.
❓ <b>Ярдәм кирәкме?</b> Безнең ярдәм чатына керегез. Без <b>һәркемгә</b> булышабыз.
📼 <b>Сез модульләрне @hikkamods_bot аша эзли һәм урнаштыра аласыз. Гади языгыз эзләү запрос һәм басыгыз ⛩ install бу кирәкле модуле</b>
📣 <b>Комьюнити ясаган модульләр белән каналларны карагыз: <a href="https://t.me/hikka_ub/126">күрсәтергә</a></b>
💁‍♀️ <b>Тиз белешмәлек:</b>
1️⃣ <b>Языгыз <b><code>.help</code></b> модульләр исемлеген күрү өчен</b>
2️⃣ <b>Языгыз</b> <code>.help &lt;Модуль исеме/командасы&gt;</code> <b>модуль тасвирламасын күрү өчен</b>
3️⃣ <b>Языгыз</b> <code>.dlmod &lt;сылтама&gt;</code> <b>сылтамадан модульне йөкләү өчен</b>
4️⃣ <b>Языгыз</b> <code>.loadmod</code> <b>файлга җавап, аннан модульне йөкләү өчен</b>
5️⃣ <b>Языгыз</b> <code>.unloadmod &lt;модуль исеме&gt;</code> <b>модульне бушату өчен</b>
💡 <b>Hikka Friendly-Telegram һәм GeekTG модульләрен, шулай ук үзенекен хуплый.</b>
""",
        "railway": (
            "🚂 <b>Синең юзербот Railway сайтында урнаштырылган</b>. Бу платформада сез"
            " айга <b>500 бушлай сәгать аласыз</b>. Лимит җиткәч, сезнең <b>юзербот"
            " туңдырылачак</b>. Киләсе айда <b>сез күчәргә тиеш https://railway.app һәм"
            " аны яңадан эшләтеп җибәрү</b>."
        ),
        "lavhost": (
            "✌️ <b>Сезерботың сез lavHost җибәрелде</b>. Ләкин @lavhost җибәрелгән"
            " хәбәрләр һәм яңа яңалыклар үзенә алу өчен керегез. Сезербот җибәрелгән"
            " хәбәрләр һәм яңа яңалыклар турында сорауларны @lavhostchat җибәрегез."
        ),
        "miyahost": (
            "🎃 <b>Сезерботың сез MiyaHost җибәрелде</b>. Ләкин @miyahost җибәрелгән"
            " хәбәрләр һәм яңа яңалыклар үзенә алу өчен керегез. Сезербот җибәрелгән"
            " хәбәрләр һәм яңа яңалыклар турында сорауларны @miyahost_support"
            " җибәрегез."
        ),
        "language_saved": "🥟 Тел сакланган!",
        "language": "🥟 Татар теле",
        "btn_support": "🥷 Ярдәм чаты",
    }

    async def client_ready(self):
        if self.get("disable_quickstart"):
            raise loader.SelfUnload

        self.mark = (
            lambda: [
                [
                    {
                        "text": self.strings("btn_support"),
                        "url": "https://t.me/hikka_talks",
                    }
                ],
            ]
            + [
                [
                    {
                        "text": "👩‍⚖️ Privacy Policy",
                        "url": "https://docs.google.com/document/d/15m6-pb1Eya8Zn4y0_7JEdvMLAo_v050rFMaWrjDjvMs/edit?usp=sharing",
                    },
                    {
                        "text": "📜 EULA",
                        "url": "https://docs.google.com/document/d/1sZBk24SWLBLoGxcsZHW8yP7yLncToPGUP1FJ4dS6z5I/edit?usp=sharing",
                    },
                ]
            ]
            + utils.chunks(
                [
                    {
                        "text": (
                            getattr(self, f"strings_{lang}")
                            if lang != "en"
                            else self.strings._base_strings
                        )["language"],
                        "callback": self._change_lang,
                        "args": (lang,),
                    }
                    for lang in [
                        "en",
                        "ru",
                        "it",
                        "de",
                        "uz",
                        "tr",
                        "es",
                        "kk",
                        "tt",
                    ]
                ],
                3,
            )
        )

        self.text = (
            lambda: self.strings("base")
            + (
                "\n"
                + (
                    self.strings("railway")
                    if "RAILWAY" in os.environ
                    else (
                        self.strings("lavhost")
                        if "LAVHOST" in os.environ
                        else (
                            self.strings("miyahost") if "MIYAHOST" in os.environ else ""
                        )
                    )
                )
            ).rstrip()
        )

        await self.inline.bot.send_animation(self._client.tg_id, animation=choice(imgs))
        await self.inline.bot.send_message(
            self._client.tg_id,
            self.text(),
            reply_markup=self.inline.generate_markup(self.mark()),
            disable_web_page_preview=True,
        )

        self.set("disable_quickstart", True)

    async def _change_lang(self, call: BotInlineCall, lang: str):
        self._db.set(translations.__name__, "lang", lang)
        await self.allmodules.reload_translations()

        await call.answer(self.strings("language_saved"))
        await call.edit(text=self.text(), reply_markup=self.mark())
