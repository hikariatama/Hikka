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
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji><b> So'ngi versia</b>"
        ),
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
            " o'zgartirish uchun matn kiriting</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>Ma'lumotlar"
            " o'zgartirildi</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nKo'p"
            " funksiyali userbot, buning ichida: ichki-gallereya, formalar, ro'yhatlar,"
            " hamda animatsiyalangan emojilar. Userbot - bu sening"
            " telegram-akkauntingni ichida ishlaydigan ilova. Hohlagan chatga komanda"
            " yozsangiz, tez orada bu komanda ishlaydi. <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a> da misollarni'
            " ko'rishingiz mumkin"
        ),
    }

    strings_tr = {
        "owner": "Sahip",
        "version": "Sürüm",
        "build": "Derleme",
        "prefix": "Önek",
        "uptime": "Aktif Süre",
        "branch": "Dal",
        "send_info": "Bot hakkında bilgi",
        "description": "ℹ️ Kişisel bilgileri tehlikeye atmaz",
        "_ihandle_doc_info": "Bot hakkında bilgi",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> Güncel</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Güncelleme"
            " gerekli </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Kişisel mesaj için bilgi. {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} anahtar kelimeleri kullanılabilir"
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
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\\Çok fazla"
            " özellik barındıran Telegram kullanıcı botu, örneğin Çevrimiçi galeri,"
            " formlar, listeler ve animasyonlu emoji desteği gibi. Kullanıcı botu -"
            " Telegram hesabınızda çalışan bir yazılımdır. Bir sohbete bir komut"
            " yazarsanız, hemen orada çalışacaktır. Örnekleri görmek için <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub\'ı ziyaret'
            " edebilirsin</a>"
        ),
    }

    strings_ja = {
        "owner": "オーナー",
        "version": "バージョン",
        "build": "ビルド",
        "prefix": "プレフィックス",
        "uptime": "稼働時間",
        "branch": "ブランチ",
        "send_info": "ボットについての情報",
        "description": "ℹ️ 個人情報を危険に晒しません",
        "_ihandle_doc_info": "ボットについての情報",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> 最新</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> 更新が必要です"
            " </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "個人メッセージのための情報。 {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} キーワードを使用できます"
        ),
        "_cfg_cst_btn": "個人ボタンのための情報。ボタンを削除するには空白にします",
        "_cfg_banner": "画像のためのURL",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>情報を変更するには"
            " 何かテキストを入力します</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>情報が変更されました</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\n多機能な"
            " ユーザーボットです。例えばオンラインギャラリー、フォーム、リスト、"
            " アニメーション付きの絵文字など。ユーザーボットは、Telegramアカウント内で"
            " 動作するアプリケーションです。チャットにコマンドを入力すると、すぐに"
            " そのコマンドが実行されます。例を見るには、<a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>を参照してください'
        ),
    }

    strings_kr = {
        "owner": "소유자",
        "version": "버전",
        "build": "빌드",
        "prefix": "접두사",
        "uptime": "가동 시간",
        "branch": "브랜치",
        "send_info": "봇에 대한 정보",
        "description": "ℹ️ 개인 정보를 위험에 노출하지 않습니다",
        "_ihandle_doc_info": "봇에 대한 정보",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> 최신</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> 업데이트가 필요합니다"
            " </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "개인 메시지를 위한 정보. {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch} 키워드를 사용할 수 있습니다"
        ),
        "_cfg_cst_btn": "개인 버튼을 위한 정보. 버튼을 제거하려면 비워 둡니다",
        "_cfg_banner": "이미지를 위한 URL",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>정보를 변경하려면"
            " 어떤 텍스트를 입력하십시오</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>정보가 변경되었습니다</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\n다양한 기능을"
            " 제공하는 사용자 봇입니다. 예를 들어 온라인 갤러리, 양식, 목록, 애니메이션"
            " Emoji 등. 사용자 봇은 Telegram 계정 내에서 작동하는 애플리케이션입니다."
            " 채팅에 명령을 입력하면 즉시 해당 명령이 실행됩니다. 예를 보려면 <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>를 참조하십시오'
        ),
    }

    strings_ar = {
        "owner": "المالك",
        "version": "الإصدار",
        "build": "بناء",
        "prefix": "بادئة",
        "uptime": "وقت التشغيل",
        "branch": "فرع",
        "send_info": "إرسال معلومات البوت",
        "description": "ℹ️ لا تعرض البيانات الشخصية للخطر",
        "_ihandle_doc_info": "معلومات البوت",
        "up-to-date": "<emoji document_id=5370699111492229743>😌</emoji><b> محدث</b>",
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> يتطلب التحديث"
            " </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "معلومات الرسالة الشخصية. يمكنك استخدام الكلمات الرئيسية {me}, {version},"
            " {build}, {prefix}, {platform}, {upd}, {uptime}, {branch}"
        ),
        "_cfg_cst_btn": "معلومات الزر الشخصية. إزالة الزر يرجى تركه فارغًا",
        "_cfg_banner": "URL للصورة",
        "setinfo_no_args": (
            "<emoji document_id=5370881342659631698>😢</emoji> <b>لتغيير المعلومات،"
            " يرجى إدخال بعض النص</b>"
        ),
        "setinfo_success": (
            "<emoji document_id=5436040291507247633>🎉</emoji> <b>تم تغيير المعلومات"
            " بنجاح</b>"
        ),
        "desc": (
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nبوت"
            " مستخدم يوفر ميزات متعددة. على سبيل المثال: معرض عبر الإنترنت، نموذج،"
            " قائمة، Emoji الرسوم المتحركة وغيرها. بوت المستخدم هو تطبيق يعمل داخل حساب"
            " Telegram. يتم تنفيذ أوامر الدردشة على الفور. لمزيد من المعلومات، يرجى"
            ' زيارة <a href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_es = {
        "owner": "Propietario",
        "version": "Versión",
        "build": "Construir",
        "prefix": "Prefijo",
        "uptime": "Tiempo de actividad",
        "branch": "Rama",
        "send_info": "Enviar información del bot",
        "description": "ℹ️ No exponga su información personal",
        "_ihandle_doc_info": "Información del bot",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji><b> Actualizado</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Actualización"
            " necesaria </b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Información del mensaje personalizado. Puede usar las palabras clave {me},"
            " {version}, {build}, {prefix}, {platform}, {upd}, {uptime}, {branch}"
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
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nEl bot de"
            " usuario proporciona varias funciones. Por ejemplo: Galería en línea,"
            " formulario, lista, Emoji animado y más. El bot de usuario es una"
            " aplicación que funciona dentro de una cuenta de Telegram. Las órdenes de"
            " chat se ejecutan de inmediato. Para obtener más información, consulte <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
        ),
    }

    strings_tt = {
        "owner": "Идарәче",
        "version": "Версия",
        "build": "Билд",
        "prefix": "Префикс",
        "uptime": "Тәртиби вакыты",
        "branch": "Кишелек",
        "send_info": "Бот турында мәгълүматны җибәрү",
        "description": "ℹ️ Шәхси мәгълүматыңызны тыяу",
        "_ihandle_doc_info": "Бот турында мәгълүмат",
        "up-to-date": (
            "<emoji document_id=5370699111492229743>😌</emoji><b> Яңартылган</b>"
        ),
        "update_required": (
            "<emoji document_id=5424728541650494040>😕</emoji><b> Яңартылу"
            " таләп ителә</b><code>.update</code>"
        ),
        "_cfg_cst_msg": (
            "Шәхси хәбәр мәгълүматы. {me}, {version}, {build}, {prefix}, {platform},"
            " {upd}, {uptime}, {branch} күчермәләрен җибәрү мөмкин"
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
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nКулланучы"
            " боты монда бер көйләүләрне күрсәтә: онлайн галерея, форма, рәвештә,"
            " эмоджи һәм башкалары. Кулланучы боты Telegram аккаунтында исәпләнә. Чат"
            " өчен күрсәтмәләр асабынча исәпләнә. Башка мәгълүмат өчен <a href="
            '"https://github.com/hikariatama/Hikka">GitHub</a>'
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

    @loader.command(
        ru_doc="Отправляет информацию о боте",
        de_doc="Sendet Informationen über den Bot",
        tr_doc="Bot hakkında bilgi gönderir",
        uz_doc="Bot haqida ma'lumot yuboradi",
        kr_doc="봇 정보를 보냅니다",
        ja_doc="ボットの情報を送信します",
        ar_doc="يرسل معلومات عن البوت",
        tt_doc="Бот турында мәгълүмат җибәрергә",
        es_doc="Envía información sobre el bot",
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
        uz_doc="Bot haqida ma'lumot yuborish",
        ja_doc="ボットについての情報を送信します",
        kr_doc="봇에 대한 정보를 보냅니다",
        ar_doc="إرسال معلومات حول البوت",
        es_doc="Enviar información sobre el bot",
        tt_doc="Бот турында мәгълүмат җибәрергә",
    )
    async def hikkainfocmd(self, message: Message):
        """Send info aka 'What is Hikka?'"""
        await utils.answer(message, self.strings("desc"))

    @loader.command(
        ru_doc="<текст> - Изменить текст в .info",
        de_doc="<text> - Ändere den Text in .info",
        tr_doc="<metin> - .info'da metni değiştir",
        uz_doc="<matn> - .info'dagi matnni o'zgartirish",
        ja_doc="<テキスト> - .infoのテキストを変更します",
        kr_doc="<텍스트> - .info의 텍스트를 변경합니다",
        ar_doc="<نص> - تغيير النص في .info",
        es_doc="<texto> - Cambiar el texto en .info",
        tt_doc="<мәтін> - .info дегендегі мәтінді өзгерту",
    )
    async def setinfo(self, message: Message):
        """<text> - Change text in .info"""
        args = utils.get_args_html(message)
        if not args:
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))
