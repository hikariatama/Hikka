# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

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
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nTelegram юзербот с огромным количеством функций, из"
            " которых: инлайн галереи, формы, списки, а также поддержка"
            " анимированных эмодзи. Юзербот - программа, которая запускается на"
            " твоем Telegram-аккаунте. Когда ты пишешь команду в любом чате, она"
            " сразу же выполняется. Обрати внимание на живые примеры на <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
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
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nUn bot utilisateur de Telegram avec beaucoup de"
            " fonctions, y compris des galeries en ligne, des formulaires, des"
            " listes, et également la prise en charge des émoticônes animées."
            " Le bot utilisateur est un programme qui s'exécute sur votre compte"
            " de Telegram. Lorsque vous tapez une commande dans n'importe quel"
            " chat, elle est exécutée immédiatement. Notez les exemples en"
            ' direct sur <a href="https://github.com/hikariatama/Hikka">GitHub</a>'
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
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Hikka</b>\n\nUserbot di Telegram con molte funzioni, come gallerie"
            " inline, form, liste e supporto ad emoji animate. Userbot - software"
            " che gira sul tuo account Telegram. Se scrivi un comando in qualsiasi"
            " chat, viene eseguito lì. Controlla gli esempi in <a"
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
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\\Çok fazla"
            " özellik barındıran Telegram kullanıcı botu, örneğin Çevrimiçi galeri,"
            " formlar, listeler ve animasyonlu emoji desteği gibi. Kullanıcı botu -"
            " Telegram hesabınızda çalışan bir yazılımdır. Bir sohbete bir komut"
            " yazarsanız, hemen orada çalışacaktır. Örnekleri görmek için <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub\'ı ziyaret'
            " edebilirsin</a>"
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
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nEl bot de"
            " usuario proporciona varias funciones. Por ejemplo: Galería en línea,"
            " formulario, lista, Emoji animado y más. El bot de usuario es una"
            " aplicación que funciona dentro de una cuenta de Telegram. Las órdenes de"
            " chat se ejecutan de inmediato. Para obtener más información, consulte <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
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
            "<emoji document_id=6318565919471699564>🌌</emoji> <b>Hikka</b>\n\nПайдалы"
            " бот қосымшалары бар. Мысалы: Онлайн галерея, форма, тізім, анимациялы"
            " emoji және басқалар. Пайдалы бот - телеграм аккаунтында іске қосылған"
            " бағдарлама. Сөйлесу бойынша әрекетті қылуға болады. Қосымша ақпарат үшін"
            ' <a href="https://github.com/hikariatama/Hikka">GitHub</a>'
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

    def _render_info(self, inline: bool) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = f'<b><a href="tg://user?id={self._client.hikka_me.id}">{utils.escape_html(get_display_name(self._client.hikka_me))}</a></b>'
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
                f" {self.strings('version')}:</b> {_version} {build}\n<b>{{}}"
                f" {self.strings('branch')}:"
                f"</b> <code>{version.branch}</code>\n{upd}\n\n<b>{{}}"
                f" {self.strings('prefix')}:</b> {prefix}\n<b>{{}}"
                f" {self.strings('uptime')}:"
                f"</b> {utils.formatted_uptime()}\n\n<b>{{}}"
                f" {self.strings('cpu_usage')}:"
                f"</b> <i>~{utils.get_cpu_usage()} %</i>\n<b>{{}}"
                f" {self.strings('ram_usage')}:"
                f"</b> <i>~{utils.get_ram_usage()} MB</i>\n<b>{{}}</b>"
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
