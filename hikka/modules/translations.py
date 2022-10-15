#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

from .. import loader, utils, translations
from telethon.tl.types import Message
import logging

logger = logging.getLogger(__name__)


@loader.tds
class Translations(loader.Module):
    """Processes internal translations"""

    strings = {
        "name": "Translations",
        "lang_saved": "{} <b>Language saved!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Translate pack"
            " saved!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Incorrect language"
            " specified</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Translations reset"
            " to default ones</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Invalid pack format"
            " in url</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You need to specify"
            " valid url containing a langpack</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Command output seems"
            " to be too long, so it's sent in file.</b>"
        ),
        "opening_form": " <b>Opening form...</b>",
        "opening_gallery": " <b>Opening gallery...</b>",
        "opening_list": " <b>Opening list...</b>",
        "inline403": "🚫 <b>You can't send inline units in this chat</b>",
        "invoke_failed": "<b>🚫 Unit invoke failed! More info in logs</b>",
    }

    strings_ru = {
        "lang_saved": "{} <b>Язык сохранён!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Пакет переводов"
            " сохранён!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Указан неверный"
            " язык</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Переводы сброшены"
            " на стандартные</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Неверный формат"
            " пакета переводов в ссылке</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Вы должны указать"
            " ссылку, содержащую пакет переводов</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Вывод команды слишком"
            " длинный, поэтому он отправлен в файле.</b>"
        ),
        "opening_form": " <b>Открываю форму...</b>",
        "opening_gallery": " <b>Открываю галерею...</b>",
        "opening_list": " <b>Открываю список...</b>",
        "inline403": "🚫 <b>Вы не можете отправлять встроенные элементы в этом чате</b>",
        "invoke_failed": "<b>🚫 Вызов модуля не удался! Подробнее в логах</b>",
    }

    strings_de = {
        "lang_saved": "{} <b>Sprache gespeichert!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Übersetzungs"
            " Paket gespeichert!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Falsche Sprache"
            " angegeben</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Übersetzungen"
            " auf Standard zurückgesetzt</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Ungültiges"
            " Übersetzungs Paket in der URL</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Sie müssen eine"
            " gültige URL angeben, die ein Übersetzungs Paket enthält</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Befehlsausgabe scheint"
            " zu lang zu sein, daher wird sie in einer Datei gesendet.</b>"
        ),
        "opening_form": " <b>Formular wird geöffnet...</b>",
        "opening_gallery": " <b>Galerie wird geöffnet...</b>",
        "opening_list": " <b>Liste wird geöffnet...</b>",
        "inline403": "🚫 <b>Sie können Inline-Einheiten in diesem Chat nicht senden</b>",
        "invoke_failed": (
            "<b>🚫 Modulaufruf fehlgeschlagen! Weitere Informationen in den"
            " Protokollen</b>"
        ),
    }

    strings_tr = {
        "lang_saved": "{} <b>Dil kaydedildi!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Çeviri paketi"
            " kaydedildi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Yanlış dil"
            " belirtildi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Çeviriler varsayılan"
            " hale getirildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL'deki çeviri"
            " paketi geçersiz</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Geçerli bir URL"
            " belirtmelisiniz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Komut çıktısı çok uzun"
            " görünüyor, bu yüzden dosya olarak gönderildi.</b>"
        ),
        "opening_form": " <b>Form açılıyor...</b>",
        "opening_gallery": " <b>Galeri açılıyor...</b>",
        "opening_list": " <b>Liste açılıyor...</b>",
        "inline403": "🚫 <b>Bu sohbette inline öğeleri gönderemezsiniz</b>",
        "invoke_failed": "<b>🚫 Modül çağrısı başarısız! Ayrıntılar günlüklerde</b>",
    }

    strings_uz = {
        "lang_saved": "{} <b>Til saqlandi!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Tarjima paketi"
            " saqlandi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Noto'g'ri til"
            " belgilandi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Tarjimalar"
            " standart holatga qaytarildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL'dagi tarjima"
            " paketi noto'g'ri</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Siz noto'g'ri URL"
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
            "<b>🚫 Modulni chaqirish muvaffaqiyatsiz! Batafsil ma'lumotlar"
            " jurnallarda</b>"
        ),
    }

    strings_hi = {
        "lang_saved": "{} <b>भाषा सहेजा गया!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>अनुवाद पैक"
            " सहेजा गया!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>गलत भाषा"
            " निर्दिष्ट किया गया</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>अनुवाद डिफ़ॉल्ट"
            " पर रीसेट किए गए</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>यूआरएल में गलत"
            " अनुवाद पैक निर्दिष्ट किया गया</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>आपने गलत यूआरएल"
            " निर्दिष्ट किया है</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>कमांड आउटपुट बहुत लंबा"
            " लगता है, इसलिए फ़ाइल में भेजा जाता है.</b>"
        ),
        "opening_form": " <b>फॉर्म खोल रहा है...</b>",
        "opening_gallery": " <b>गैलरी खोल रहा है...</b>",
        "opening_list": " <b>सूची खोल रहा है...</b>",
        "inline403": "🚫 <b>आप इस ग्रुप में इनलाइन आइटम नहीं भेज सकते हैं</b>",
        "invoke_failed": "<b>🚫 मॉड्यूल इन्वोक विफल! विस्तृत जानकारी लॉग में है</b>",
    }

    @loader.command(
        ru_doc="[языки] - Изменить стандартный язык",
        de_doc="[Sprachen] - Ändere die Standard-Sprache",
        tr_doc="[Diller] - Varsayılan dil değiştir",
        uz_doc="[til] - Standart tili o'zgartirish",
        hi_doc="[भाषाएं] - डिफ़ॉल्ट भाषा बदलें",
    )
    async def setlang(self, message: Message):
        """[languages in the order of priority] - Change default language"""
        args = utils.get_args_raw(message)
        if not args or any(len(i) != 2 for i in args.split(" ")):
            await utils.answer(message, self.strings("incorrect_language"))
            return

        self._db.set(translations.__name__, "lang", args.lower())
        await self.translator.init()

        for module in self.allmodules.modules:
            try:
                module.config_complete(reload_dynamic_translate=True)
            except Exception as e:
                logger.debug("Can't complete dynamic translations reload of %s due to %s", module, e)

        fixmap = {"en": "gb", "hi": "in"}

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                "".join(
                    [
                        utils.get_lang_flag(fixmap.get(lang, lang))
                        for lang in args.lower().split(" ")
                    ]
                )
            ),
        )

    @loader.command(
        ru_doc="[ссылка на пак | пустое чтобы удалить] - Изменить внешний пак перевода",
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
        hi_doc="[अनुवाद पैक का लिंक | खाली छोड़ दें] - बाहरी अनुवाद पैक बदलें",
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
        success = await self.translator.init()

        for module in self.allmodules.modules:
            try:
                module.config_complete(reload_dynamic_translate=True)
            except Exception as e:
                logger.debug("Can't complete dynamic translations reload of %s due to %s", module, e)

        await utils.answer(
            message,
            self.strings("pack_saved" if success else "check_pack"),
        )
