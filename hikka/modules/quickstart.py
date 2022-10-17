#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import os
from random import choice
import logging

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

1️⃣ <b>Type </b><code>.help</code> <b>to see modules list</b>
2️⃣ <b>Type </b><code>.help &lt;ModuleName/command&gt;</code> <b>to see help of module ModuleName</b>
3️⃣ <b>Type </b><code>.dlmod &lt;link&gt;</code> <b>to load module from link</b>
4️⃣ <b>Type </b><code>.loadmod</code> <b>with reply to file to install module from it</b>
5️⃣ <b>Type </b><code>.unloadmod &lt;ModuleName&gt;</code> <b>to unload module ModuleName</b>

💡 <b>Hikka supports modules from Friendly-Telegram and GeekTG, as well as its own ones.</b>""",
        "okteto": (
            "☁️ <b>Your userbot is installed on Okteto</b>. You will get notifications"
            " from @WebpageBot. Do not block him."
        ),
        "railway": (
            "🚂 <b>Your userbot is installed on Railway</b>. This platform has only"
            " <b>500 free hours per month</b>. Once this limit is reached, your"
            " <b>Hikka will be frozen</b>. Next month <b>you will need to go to"
            " https://railway.app and restart it</b>."
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

1️⃣ <b>Напиши </b><code>.help</code> <b>чтобы увидеть список модулей</b>
2️⃣ <b>Напиши </b><code>.help &lt;Название модуля/команда&gt;</code> <b>чтобы увидеть описание модуля</b>
3️⃣ <b>Напиши </b><code>.dlmod &lt;ссылка&gt;</code> <b>чтобы загрузить модуль из ссылка</b>
4️⃣ <b>Напиши </b><code>.loadmod</code> <b>ответом на файл, чтобы загрузить модуль из него</b>
5️⃣ <b>Напиши </b><code>.unloadmod &lt;Название модуля&gt;</code> <b>чтобы выгрузить модуль</b>

💡 <b>Hikka поддерживает модули из Friendly-Telegram и GeekTG, а также свои собственные.</b>
""",
        "okteto": (
            "☁️ <b>Твой юзербот установлен на Okteto</b>. Ты будешь получать"
            " уведомления от @WebpageBot. Не блокируй его."
        ),
        "railway": (
            "🚂 <b>Твой юзербот установлен на Railway</b>. На этой платформе ты"
            " получаешь только <b>500 бесплатных часов в месяц</b>. Когда лимит будет"
            " достигнет, твой <b>юзербот будет заморожен</b>. В следующем месяце <b>ты"
            " должен будешь перейти на https://railway.app и перезапустить его</b>."
        ),
        "language_saved": "🇷🇺 Язык сохранен!",
        "language": "🇷🇺 Русский",
        "btn_support": "🥷 Чат поддержки",
    }

    strings_de = {
        "base": """🌘🇩🇪 <b>Hallo.</b> Dein Userbot <b>Hikka</b> ist installiert.

❓ <b>Brauchst du Hilfe?</b> Trete unserem Support-Chat bei. Wir helfen <b>allen</b>.

📼 <b>Du kannst Module über @hikkamods_bot suchen und installieren. Gib einfach einen Suchbegriff ein und drücke auf ⛩ Install auf dem gewünschten Modul</b>

📣 <b>Schaue dir die Module-Kanäle an, die von der Community erstellt wurden: <a href="https://t.me/hikka_ub/126">anzeigen</a></b>

💁‍♀️ <b>Schnellstart:</b>

1️⃣ <b>Schreibe </b><code>.help</code> <b>um eine Liste der Module zu sehen</b>
2️⃣ <b>Schreibe </b><code>.help &lt;Modulname/Befehl&gt;</code> <b>um die Beschreibung des Moduls zu sehen</b>
3️⃣ <b>Schreibe </b><code>.dlmod &lt;Link&gt;</code> <b>um ein Modul aus dem Link zu laden</b>
4️⃣ <b>Schreibe </b><code>.loadmod</code> <b>als Antwort auf eine Datei, um ein Modul aus der Datei zu laden</b>
5️⃣ <b>Schreibe </b><code>.unloadmod &lt;Modulname&gt;</code> <b>um ein Modul zu entladen</b>

💡 <b>Hikka unterstützt Module von Friendly-Telegram und GeekTG sowie eigene Module.</b>
""",
        "okteto": (
            "☁️ <b>Dein Userbot ist auf Okteto installiert</b>. Du wirst"
            " Benachrichtigungen von @WebpageBot erhalten. Blockiere ihn nicht."
        ),
        "railway": (
            "🚂 <b>Dein Userbot ist auf Railway installiert</b>. Du erhältst nur <b>500"
            " kostenlose Stunden pro Monat</b> auf dieser Plattform. Wenn das Limit"
            " erreicht ist, wird dein <b>Userbot eingefroren</b>. Im nächsten Monat"
            " musst du zu https://railway.app gehen und ihn neu starten.</b>"
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
1️⃣ <b>Modullar royhatini ko'rish uchun </b><code>.help buyrug'ini</code> <b>yozing</b>
2️⃣ <b>Modul haqida ma'lumot olish uchun </b><code>.help &lt;Modul nomi/buyruq&gt;</code> <b>yozing</b>
3️⃣ <b>Modulni havola orqali o'rnatish uchun </b><code>.dlmod &lt;Link&gt;</code> <b>yozing</b>
4️⃣ <b>Modulni fayl orqali yuklash uchun </b><code>.loadmod</code> <b>faylga javoban yozing</b>
5️⃣ <b>Modulni olib tashlash uchun </b><code>.unloadmod &lt;Modul nomi&gt;</code> <b>yozing</b>
💡 <b>Hikka Friendly-Telegram ve GeekTG O'z Modullarini qollab quvvatlaydi.</b>
""",
        "okteto": (
            "☁️ <b>Sizning yuzerbotingiz oktetoda o'rnatilgan</b>. @WebpageBot'dan"
            " xabarlar qabul qilasiz uni bloklamang."
        ),
        "railway": (
            "🚂 <b>Sizning yuzerbotingiz Railwayda o'rnatilgan</b>. Bu platforma,"
            " <b>oyiga atigi 500 soat bepul jihati</b> Railway bergan muddat tugagandan"
            " so'ng sizning bo'tingiz  <b>to'xtatiladi</b>. Keyingi oy,"
            " https://railway.app havolasi orqali yuzerbotingizni qayta ishga tushira"
            " olasiz.</b>"
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
1️⃣ <b>Modüller listesini görmek için </b><code>.help</code> <b>yazın</b>
2️⃣ <b>Modül hakkında bilgi almak için </b><code>.help &lt;Modul adı/Komut&gt;</code> <b>yazın</b>
3️⃣ <b>Bir bağlantıdan modül yüklemek için </b><code>.dlmod &lt;Link&gt;</code> <b>yazın</b>
4️⃣ <b>Bir modülü bir dosyadan yüklemek için </b><code>.loadmod</code> <b>bir dosyanın yanıtını yazın</b>
5️⃣ <b>Bir modülü kaldırmak için </b><code>.unloadmod &lt;Modul adı&gt;</code> <b>yazın</b>
💡 <b>Hikka Friendly-Telegram ve GeekTG modüllerini de dahil olmak üzere kendi modüllerini destekler.</b>
""",
        "okteto": (
            "☁️ <b>Kullanıcı botunuz Okteto'da kuruldu</b>. @WebpageBot'dan mesajlar"
            " alacaksınız. Onları engellemeyin."
        ),
        "railway": (
            "🚂 <b>Kullanıcı botunuz Railway'de kuruldu</b>. Bu platform, <b>aylık"
            " sadece 500 saati ücretsiz olarak</b> sağlamaktadır. Sınırı aştığınızda,"
            " kullanıcı botunuz <b>durdurulur</b>. Gelecek ay, https://railway.app"
            " adresinden botunuzu yeniden başlatmanız gerekmektedir.</b>"
        ),
        "language_saved": "🇹🇷 Dil kaydedildi!",
        "language": "🇹🇷 Türkçe",
        "btn_support": "🥷 Destek grubu",
    }

    strings_hi = {
        "base": """🌘🇮🇳 <b>नमस्ते.</b> आपका <b>Hikka</b> उपयोगकर्ता बॉट स्थापित किया गया है.

❓ <b>क्या आपको मदद की आवश्यकता है?</b> हमारे साथ मदद ग्रुप में शामिल हों. हम सब कुछ साझा करेंगे.

📼 <b>मॉड्यूल्स को @hikkamods_bot से खोजें और इंस्टॉल करें. केवल एक खोज शब्द दर्ज करें और आपके लिए उपलब्ध मॉड्यूल पर ⛩ इंस्टॉल बटन पर क्लिक करें</b>

📣 <b>समुदाय द्वारा बनाए गए चैनल देखें: <a href="https://t.me/hikka_ub/126">दिखाएं</a></b>

💁‍♀️ <b>त्वरित शुरुआत:</b>

1️⃣ <b>मॉड्यूलों की सूची देखने के लिए </b><code>.help</code> <b>टाइप करें</b>
2️⃣ <b>मॉड्यूल के बारे में जानकारी प्राप्त करने के लिए </b><code>.help &lt;मॉड्यूल नाम/कमांड&gt;</code> <b>टाइप करें</b>
3️⃣ <b>लिंक से मॉड्यूल इंस्टॉल करने के लिए </b><code>.dlmod &lt;लिंक&gt;</code> <b>टाइप करें</b>
4️⃣ <b>एक मॉड्यूल को फाइल से लोड करने के लिए </b><code>.loadmod</code> <b>एक फ़ाइल का उत्तर दर्ज करें</b>
5️⃣ <b>एक मॉड्यूल को हटाने के लिए </b><code>.unloadmod &lt;मॉड्यूल नाम&gt;</code> <b>टाइप करें</b>

💡 <b>अपने मॉड्यूल को समर्थित करने के लिए, Hikka Friendly-Telegram और GeekTG मॉड्यूल भी शामिल हैं.</b>
""",
        "okteto": (
            "☁️ <b>आपका उपयोगकर्ता बॉट Okteto पर स्थापित किया गया है</b>. आपको"
            " @WebpageBot से संदेश प्राप्त होते ही आपका उपयोगकर्ता बॉट <b>अवरोधित कर"
            " दिया जाएगा</b>. अगले महीने, https://railway.app पर जाएं और इसे फिर से"
            " शुरू करें.</b>"
        ),
        "language_saved": "🇮🇳 भाषा सहेजा गया!",
        "language": "🇮🇳 हिंदी",
        "btn_support": "🥷 समर्थन समूह",
    }

    strings_ja = {
        "base": """
📼 <b>モジュールを検索してインストールするには @hikkamods_bot から検索してください。検索ワードを1つ入力してください。</b>

📣 <b>コミュニティで作成されたチャンネルを見るには、こちらをクリックしてください: <a href="https://t.me/hikka_ub/126">表示</a></b>

💁‍♀️ <b>すぐに始めるには:</b>

1️⃣ <b>モジュールのリストを表示するには </b><code>.help</code> <b>を入力します</b>
2️⃣ <b>モジュールについての情報を取得するには </b><code>.help &lt;モジュール名/コマンド&gt;</code> <b>を入力します</b>
3️⃣ <b>リンクからモジュールをインストールするには </b><code>.dlmod &lt;リンク&gt;</code> <b>を入力します</b>
4️⃣ <b>モジュールをファイルからロードするには </b><code>.loadmod</code> <b>ファイルの返信を入力します</b>
5️⃣ <b>モジュールを削除するには </b><code>.unloadmod &lt;モジュール名&gt;</code> <b>を入力します</b>

💡 <b>モジュールをサポートするには、Hikka Friendly-Telegram と GeekTG モジュールも含まれています。</b>
""",
        "okteto": (
            "☁️ <b>あなたのユーザーボットは、Okteto にインストールされています</b>. あなたは"
            " @WebpageBot からメッセージを受け取ると、あなたのユーザーボットが <b>ブロックされます</b>. 次の月に、"
            " https://railway.app にアクセスして、再度開始してください.</b>"
        ),
        "language_saved": "🇯🇵 言語が保存されました!",
        "language": "🇯🇵 日本語",
        "btn_support": "🥷 サポートグループ",
    }

    strings_kr = {
        "base": """
📼 <b>모듈을 검색하고 설치하려면 @hikkamods_bot 에서 검색하십시오. 검색어를 입력하십시오.</b>

📣 <b>커뮤니티에서 생성된 채널을 보려면 여기를 클릭하십시오: <a href="https://t.me/hikka_ub/126">보기</a></b>

💁‍♀️ <b>즉시 시작하려면:</b>

1️⃣ <b>모듈 목록을 표시하려면 </b><code>.help</code> <b>를 입력하십시오</b>
2️⃣ <b>모듈에 대한 정보를 가져 오려면 </b><code>.help &lt;모듈 이름/명령&gt;</code> <b>를 입력하십시오</b>
3️⃣ <b>링크에서 모듈을 설치하려면 </b><code>.dlmod &lt;링크&gt;</code> <b>를 입력하십시오</b>
4️⃣ <b>모듈을 파일에서로드하려면 </b><code>.loadmod</code> <b>파일에 응답을 입력하십시오</b>
5️⃣ <b>모듈을 제거하려면 </b><code>.unloadmod &lt;모듈 이름&gt;</code> <b>를 입력하십시오</b>

💡 <b>모듈을 지원하려면 Hikka Friendly-Telegram 및 GeekTG 모듈도 포함됩니다.</b>
""",
        "okteto": (
            "☁️ <b>사용자 봇은 Okteto에 설치되었습니다</b>.  메시지를받으면"
            " @WebpageBot 당신의 사용자 봇은 <b>차단됩니다</b>. 다음 달에,"
            " https://railway.app 에 액세스하고 다시 시작하십시오.</b>"
        ),
        "language_saved": "🇰🇷 언어가 저장되었습니다!",
        "language": "🇰🇷 한국어",
        "btn_support": "🥷 지원 그룹",
    }

    strings_ar = {
        "base": """
📼 <b>للبحث عن وتثبيت الوحدات، يرجى الذهاب إلى @hikkamods_bot وإدخال الكلمات المفتاحية.</b>

📣 <b>لمشاهدة قنوات المجتمع التي تم إنشاؤها، انقر هنا: <a href="https://t.me/hikka_ub/126">عرض</a></b>

💁‍♀️ <b>للبدء فورًا:</b>

1️⃣ <b>لعرض قائمة الوحدات، اكتب </b><code>.help</code> <b>وأدخل</b>
2️⃣ <b>للحصول على معلومات عن الوحدة، اكتب </b><code>.help &lt;اسم الوحدة/الأمر&gt;</code> <b>وأدخل</b>
3️⃣ <b>لتثبيت الوحدة من الرابط، اكتب </b><code>.dlmod &lt;الرابط&gt;</code> <b>وأدخل</b>
4️⃣ <b>لتحميل الوحدة من الملف، اكتب </b><code>.loadmod</code> <b>وأرسل الملف المراد تحميله</b>
5️⃣ <b>لإزالة الوحدة، اكتب </b><code>.unloadmod &lt;اسم الوحدة&gt;</code> <b>وأدخل</b>

💡 <b>لدعم الوحدات، يتضمن Hikka Friendly-Telegram و GeekTG أيضًا.</b>
""",
        "okteto": (
            "☁️ <b>البوت المستخدم تم تثبيته على Okteto</b>. عند استلامك"
            " @WebpageBot سيتم حظر البوت المستخدم <b>من البوتات</b>. في الشهر المقبل،"
            " انتقل إلى https://railway.app وابدأ من جديد.</b>"
        ),
        "language_saved": "🇸🇦 تم حفظ اللغة!",
        "language": "🇸🇦 العربية",
        "btn_support": "🥷 مجموعة الدعم",
    }

    strings_es = {
        "base": """
📼 <b>Para buscar e instalar módulos, vaya a @hikkamods_bot y escriba las palabras clave.</b>

📣 <b>Para ver los canales de la comunidad creados, haga clic aquí: <a href="https://t.me/hikka_ub/126">Ver</a></b>

💁‍♀️ <b>Para comenzar de inmediato:</b>

1️⃣ <b>Para ver la lista de módulos, escriba </b><code>.help</code> <b>y presione</b>
2️⃣ <b>Para obtener información sobre el módulo, escriba </b><code>.help &lt;nombre del módulo/comando&gt;</code> <b>y presione</b>
3️⃣ <b>Para instalar el módulo desde el enlace, escriba </b><code>.dlmod &lt;enlace&gt;</code> <b>y presione</b>
4️⃣ <b>Para cargar el módulo desde el archivo, escriba </b><code>.loadmod</code> <b>y responda al archivo que desea cargar</b>
5️⃣ <b>Para eliminar el módulo, escriba </b><code>.unloadmod &lt;nombre del módulo&gt;</code> <b>y presione</b>

💡 <b>Para admitir módulos, también incluye Hikka Friendly-Telegram y GeekTG.</b>
""",
        "okteto": (
            "☁️ <b>El bot de usuario se ha instalado en Okteto</b>. Cuando lo reciba"
            " @WebpageBot su bot de usuario será <b>bloqueado por bots</b>. El mes que"
            " viene, vaya a https://railway.app y comience de nuevo.</b>"
        ),
        "language_saved": "🇪🇸 ¡El idioma se ha guardado!",
        "language": "🇪🇸 Español",
        "btn_support": "🥷 Grupo de soporte",
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
                        "ru",
                        "en",
                        "uz",
                        "tr",
                        "hi",
                        "de",
                        "ja",
                        "kr",
                        "ar",
                        "es",
                    ]
                ],
                2,
            )
        )

        self.text = (
            lambda: self.strings("base")
            + (self.strings("okteto") if "OKTETO" in os.environ else "")
            + (self.strings("railway") if "RAILWAY" in os.environ else "")
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
        await self.translator.init()

        for module in self.allmodules.modules:
            try:
                module.config_complete(reload_dynamic_translate=True)
            except Exception as e:
                logger.debug(
                    "Can't complete dynamic translations reload of %s due to %s",
                    module,
                    e,
                )

        await call.answer(self.strings("language_saved"))
        await call.edit(text=self.text(), reply_markup=self.mark())
