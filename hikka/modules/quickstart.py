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
    }

    strings_uz = {
        "base": """🌘🇺🇿 <b>Salom.</b> Sizning <b>Hikka</b> userbotingiz o'rnatildi.

❓ <b>Yordam kerakmi?</b> Bizning qo'llab-quvvatlash chatingizga qo'shiling. Bizga <b>hamma</b> yordam bering.

📼 <b>Siz @hikkamods_bot orqali modullarni qidirib va o'rnatishingiz mumkin. Faqat qidiruv so'zini kiriting va kerakli modulni ⛩ Install tugmasini bosing</b>

📣 <b>Bizning modullar kanallari bilan tanishing. Bizning jamoa tomonidan yaratilgan kanallarni ko'rish uchun <a href="https://t.me/hikka_ub/126">bosing</a></b>

💁‍♀️ <b>Tezkor boshlash:</b>

1️⃣ <b>Modullar ro'yxatini ko'rish uchun </b><code>.help</code> <b>yozing</b>
2️⃣ <b>Modul haqida ma'lumot olish uchun </b><code>.help &lt;Modul nomi/Buyruq&gt;</code> <b>yozing</b>
3️⃣ <b>Modulni yuklash uchun </b><code>.dlmod &lt;Link&gt;</code> <b>modulni linkidan yuklash uchun yozing</b>
4️⃣ <b>Modulni yuklash uchun </b><code>.loadmod</code> <b>modulni fayldan yuklash uchun faylni javob qilib yozing</b>
5️⃣ <b>Modulni o'chirish uchun </b><code>.unloadmod &lt;Modul nomi&gt;</code> <b>yozing</b>

💡 <b>Hikka Friendly-Telegram va GeekTG modullarini hamda o'z modullarini qo'llab-quvvatlaydi.</b>
""",
        "okteto": (
            "☁️ <b>Sizning userbotingiz Okteto platformasida o'rnatilgan</b>."
            " Sizdan @WebpageBotga xabarlar keladi. Uni bloklashmaslik."
        ),
        "railway": (
            "🚂 <b>Sizning userbotingiz Railway platformasida o'rnatilgan</b>."
            " Sizga bu platformada <b>500 ta bepul soat</b> beriladi. Agar limit o'tgan"
            " bo'lsa, <b>userbotingiz bloklanadi</b>. Keyingi oyda"
            " https://railway.app ga o'tib, uni qayta ishga tushiring.</b>"
        ),
        "language_saved": "🇺🇿 Til saqlandi!",
        "language": "🇺🇿 O'zbekcha",
    }

    strings_tr = {
        "base": """🌘🇹🇷 <b>Merhaba.</b> <b>Hikka</b> kullanıcı botunuz kuruldu.

❓ <b>Yardıma mı ihtiyacınız var?</b> Yardım grubumuza katılın. Bizimle <b>her şeyi</b> paylaşın.

📼 <b>Modülleri @hikkamods_bot ile arayabilir ve kurabilirsiniz. Sadece bir arama kelimesi girin ve istediğiniz modüle ⛩ Install tuşuna basın</b>

📣 <b>Topluluk tarafından oluşturulan kanalları görün: <a href="https://t.me/hikka_ub/126">göster</a></b>

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
            " alırsınız. Onları engellemeyin."
        ),
        "railway": (
            "🚂 <b>Kullanıcı botunuz Railway'de kuruldu</b>. Sizden <b>500 saat ücretsiz"
            " saat</b> alırsınız. Sınır aşıldığında, kullanıcı botunuz"
            " <b>engellenir</b>. Gelecek ay, https://railway.app'a gidin ve onu yeniden"
            " başlatın.</b>"
        ),
        "language_saved": "🇹🇷 Dil kaydedildi!",
        "language": "🇹🇷 Türkçe",
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
    }

    async def client_ready(self):
        if self.get("disable_quickstart"):
            raise loader.SelfUnload

        self.mark = lambda: [
            [{"text": "🥷 Support chat", "url": "https://t.me/hikka_talks"}],
        ] + utils.chunks(
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
                for lang in ["ru", "en", "uz", "tr", "hi", "de"]
            ],
            2,
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
                logger.debug("Can't complete dynamic translations reload of %s due to %s", module, e)

        await call.answer(self.strings("language_saved"))
        await call.edit(text=self.text(), reply_markup=self.mark())
