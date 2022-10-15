#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import git
from telethon.tl.types import Message
from telethon.utils import get_display_name

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
        "send_info": "Send userbot info",
        "description": "ℹ This will not compromise any sensitive info",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji><b> Up-to-date</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Update required"
            " </b><code>.update</code>"
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
            " {platform}, {upd}, {uptime}, {branch} keywords"
        ),
        "_cfg_cst_btn": "Custom button for info. Leave empty to remove button",
        "_cfg_banner": "URL to image banner",
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nTelegram userbot with a lot of features, like inline"
            " galleries, forms, lists and animated emojis support. Userbot - software,"
            " running on your Telegram account. If you write a command to any chat, it"
            " will get executed right there. Check out live examples at <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_ru = {
        "owner": "Владелец",
        "version": "Версия",
        "build": "Сборка",
        "prefix": "Префикс",
        "uptime": "Аптайм",
        "branch": "Ветка",
        "send_info": "Отправить информацию о юзерботе",
        "description": "ℹ Это не раскроет никакой личной информации",
        "_ihandle_doc_info": "Отправить информацию о юзерботе",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji><b> Актуальная версия</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Требуется обновление"
            " </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Кастомный текст сообщения в info. Может содержать ключевые слова {me},"
            " {version}, {build}, {prefix}, {platform}, {upd}, {uptime}, {branch}"
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
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nTelegram юзербот с огромным количеством функций, из"
            " которых: инлайн галереи, формы, списки, а также поддержка"
            " анимированных эмодзи. Юзербот - программа, которая запускается на"
            " твоем Telegram-аккаунте. Когда ты пишешь команду в любом чате, она"
            " сразу же выполняется. Обрати внимание на живые примеры на <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_de = {
        "owner": "Besitzer",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "branch": "Branch",
        "send_info": "Botinfo senden",
        "description": "ℹ Dies enthüllt keine persönlichen Informationen",
        "_ihandle_doc_info": "Sende Botinfo",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> Aktuell</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Update benötigt"
            " </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Custom message for info. May contain {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} keywords"
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
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nTelegram userbot mit vielen Funktionen, wie z.B. Inline"
            " Galerien, Formulare, Listen und Unterstützung für animierte Emojis."
            " Userbot - Software, die auf deinem Telegram-Account läuft. Wenn du"
            " einen Befehl in irgendeinem Chat schreibst, wird er dort ausgeführt."
            " Sieh dir Live-Beispiele auf <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_hi = {
        "owner": "मालिक",
        "version": "संस्करण",
        "build": "बिल्ड",
        "prefix": "उपसर्ग",
        "uptime": "उपटाइम",
        "branch": "शाखा",
        "send_info": "बॉट जानकारी भेजें",
        "description": "ℹ यह व्यक्तिगत जानकारी नहीं खोलता है",
        "_ihandle_doc_info": "बॉट जानकारी भेजें",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji><b> अपडेट है</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> अपडेट आवश्यक"
            " </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "सूचना के लिए कस्टम संदेश। {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} कीवर्ड का उपयोग कर सकते हैं"
        ),
        "_cfg_cst_btn": "सूचना के लिए कस्टम बटन। बटन को हटाने के लिए खाली छोड़ दें",
        "_cfg_banner": "छवि बैनर के लिए URL",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>जानकारी बदलने के"
            " लिए कोई पाठ दर्ज करें</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>जानकारी बदल गई</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nटेलीग्राम यूजरबॉट जिसमें इनलाइन गैलरी, फॉर्म, सूची और"
            " एनीमेटेड इमोजी की समर्थन के साथ अनेक सुविधाएं हैं। यूजरबॉट - सॉफ़्टवेयर"
            " जो आपके टेलीग्राम अकाउंट पर चलती है। जब आप किसी चैट में किसी आदेश"
            " लिखते हैं, तो वह तुरंत उसे देखता है। जाँच करें <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_uz = {
        "owner": "Egasi",
        "version": "Versiya",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Ishlash vaqti",
        "branch": "Vetkasi",
        "send_info": "Bot haqida ma'lumot",
        "description": "ℹ Bu shaxsiy ma'lumot emas",
        "_ihandle_doc_info": "Bot haqida ma'lumot",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> So'ngi versia</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Yangilash"
            " kerak </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Xabar uchun shaxsiy xabar. {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} kalit so'zlarni ishlatishingiz"
            " mumkin"
        ),
        "_cfg_cst_btn": (
            "Xabar uchun shaxsiy tugma. Tugmani o'chirish uchun bo'sh qoldiring"
        ),
        "_cfg_banner": "URL uchun rasmi",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Ma'lumotni"
            " o'zgartirish uchun hech qanday matn kiriting</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Ma'lumotlar"
            " o'zgartirildi</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nTelegram"
            " userbot ko'plab funksiyalar bilan, masalan, Inline-galereya, shakllar,"
            " ro'yxat va animatsiya emoji qo'llab-quvvatlanadi. Userbot - Telegram"
            " hisobingizda ishlaydigan dastur. Agar siz bir chatga buyruq yozsangiz,"
            " unda tez orada ko'rasiz. <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_tr = {
        "owner": "Sahip",
        "version": "Versiyon",
        "build": "Derleme",
        "prefix": "Önek",
        "uptime": "Çalışma Süresi",
        "branch": "Dal",
        "send_info": "Bot hakkında bilgi",
        "description": "ℹ Kişisel bilgi değil",
        "_ihandle_doc_info": "Bot hakkında bilgi",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> Güncel</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Güncelleme"
            " gerekli </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Kişisel mesaj için mesaj. {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} anahtar kelimeleri kullanılabilir"
        ),
        "_cfg_cst_btn": "Kişisel tuş için tuş. Tuşu kaldırmak için boş bırakın",
        "_cfg_banner": "URL için resim",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>Bilgiyi değiştirmek"
            " için herhangi bir metin girin</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Bilgiler"
            " değiştirildi</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nÇoklu"
            " özellikli Telegram kullanıcı botu, örneğin Çevrimiçi galeri, formlar,"
            " listeler ve animasyonlu emoji desteği. Kullanıcı botu - Telegram"
            " hesabınızda çalışan bir yazılımdır. Bir sohbete bir komut yazarsanız,"
            " hemen görebilirsiniz. <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
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

    async def client_ready(self):
        self._me = await self._client.get_me()

        # Legacy migration
        if (
            self.config["banner_url"]
            == "https://github.com/hikariatama/assets/raw/master/hikka_banner.png"
        ):
            self.config[
                "banner_url"
            ] = "https://github.com/hikariatama/assets/raw/master/hikka_banner.mp4"

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
            self._me.id,
            utils.escape_html(get_display_name(self._me)),
        )
        build = utils.get_commit_url()
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"
        platform = utils.get_named_platform()

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
                branch=version.branch,
            )
            if self.config["custom_message"]
            else (
                "<b>{}</b>\n\n"
                f'<b>{{}} {self.strings("owner")}: </b>{me}\n\n'
                f"<b>{{}} {self.strings('version')}: </b>{_version} {build}\n"
                f"<b>{{}} {self.strings('branch')}: </b><code>{version.branch}</code>\n"
                f"{upd}\n\n"
                f"<b>{{}} {self.strings('prefix')}: </b>{prefix}\n"
                f"<b>{{}} {self.strings('uptime')}: </b>{utils.formatted_uptime()}\n"
                f"<b>{platform}</b>\n"
            ).format(
                *map(
                    lambda x: utils.remove_html(x) if inline else x,
                    (
                        utils.get_platform_emoji()
                        if self._client.hikka_me.premium and not inline
                        else "🌘 Hikka",
                        "<emoji document_id=5373141891321699086>😎</emoji>",
                        "<emoji document_id=5469741319330996757>💫</emoji>",
                        "<emoji document_id=5449918202718985124>🌳</emoji>",
                        "<emoji document_id=5472111548572900003>⌨️</emoji>",
                        "<emoji document_id=5451646226975955576>⌛️</emoji>",
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
            try:
                await self._client.send_file(
                    message.peer_id,
                    self.config["banner_url"],
                    caption=self._render_info(False),
                )
            except Exception:
                await utils.answer(message, self._render_info(False))
            else:
                if message.out:
                    await message.delete()

    @loader.unrestricted
    @loader.command(
        ru_doc="Отправить информацию по типу 'Что такое Хикка?'",
        de_doc="Sende Informationen über den Bot",
        tr_doc="Bot hakkında bilgi gönderir",
        hi_doc="बॉट के बारे में जानकारी भेजें",
        uz_doc="Bot haqida ma'lumot yuborish",
    )
    async def hikkainfocmd(self, message: Message):
        """Send info aka 'What is Hikka?'"""
        await utils.answer(message, self.strings("desc"))

    @loader.command(
        ru_doc="<текст> - Изменить текст в .info",
        de_doc="<text> - Ändere den Text in .info",
        tr_doc="<metin> - .info'da metni değiştir",
        uz_doc="<matn> - .info'dagi matnni o'zgartirish",
        hi_doc="<पाठ> - .info में पाठ बदलें",
    )
    async def setinfo(self, message: Message):
        """<text> - Change text in .info"""
        args = utils.get_args_html(message)
        if not args:
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))
