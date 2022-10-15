#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import os

import telethon
from telethon.tl.types import Message
from telethon.extensions.html import CUSTOM_EMOJIS

from .. import loader, main, translations, utils, version
from ..inline.types import InlineCall


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Too many args</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Chat {} blacklisted"
            " from userbot</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Chat {}"
            " unblacklisted from userbot</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>User {} blacklisted"
            " from userbot</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>User {}"
            " unblacklisted from userbot</b>"
        ),
        "what_prefix": "❓ <b>What should the prefix be set to?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Prefix must be one"
            " symbol in length</b>"
        ),
        "prefix_set": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Command prefix"
            " updated. Type</b> <code>{newprefix}setprefix {oldprefix}</code> <b>to"
            " change it back</b>"
        ),
        "alias_created": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Alias created."
            " Access it with</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Aliases:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Command</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You must provide a"
            " command and the alias for it</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You must provide the"
            " alias name</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Alias</b>"
            " <code>{}</code> <b>removed</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Alias</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5368324170671202286>👍</emoji><b> Database cleared</b>"
        ),
        "hikka": (
            "{}\n\n<emoji document_id=5406931726184225260>🧐</emoji> <b>Version:"
            " {}.{}.{}</b>\n<emoji document_id=6318902906900711458>🧱</emoji> <b>Build:"
            " </b><i>{}</i>\n\n<emoji document_id=5233346091725888979>⚙️</emoji>"
            " <b>Hikka-TL: </b><i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Developer:"
            " t.me/hikariatama</b>"
        ),
        "confirm_cleardb": "⚠️ <b>Are you sure, that you want to clear database?</b>",
        "cleardb_confirm": "🗑 Clear database",
        "cancel": "🚫 Cancel",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Who to blacklist?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Who to"
            " unblacklist?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>You are using an"
            " unstable branch </b><code>{}</code><b>!</b>"
        ),
    }

    strings_ru = {
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Слишком много"
            " аргументов</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Чат {} добавлен в"
            " черный список юзербота</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Чат {} удален из"
            " черного списка юзербота</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Пользователь {}"
            " добавлен в черный список юзербота</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Пользователь {}"
            " удален из черного списка юзербота</b>"
        ),
        "what_prefix": "❓ <b>А какой префикс ставить то?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Префикс должен"
            " состоять только из одного символа</b>"
        ),
        "prefix_set": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Префикс обновлен."
            " Чтобы вернуть его, используй</b> <code>{newprefix}setprefix"
            " {oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Алиас создан."
            " Используй его через</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Алиасы:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Команда</b>"
            " <code>{}</code> <b>не существует</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Требуется ввести"
            " команду и алиас для нее</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Требуется имя"
            " алиаса</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Алиас</b>"
            " <code>{}</code> <b>удален</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji><b> Алиас</b>"
            " <code>{}</code> <b>не существует</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5368324170671202286>👍</emoji><b> База очищена</b>"
        ),
        "hikka": (
            "{}\n\n<emoji document_id=5406931726184225260>🧐</emoji> <b>Версия:"
            " {}.{}.{}</b>\n<emoji document_id=6318902906900711458>🧱</emoji> <b>Сборка:"
            " </b><i>{}</i>\n\n<emoji document_id=5233346091725888979>⚙️</emoji>"
            " <b>Hikka-TL: </b><i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Developer:"
            " t.me/hikariatama</b>"
        ),
        "_cls_doc": "Управление базовыми настройками юзербота",
        "confirm_cleardb": "⚠️ <b>Вы уверены, что хотите сбросить базу данных?</b>",
        "cleardb_confirm": "🗑 Очистить базу",
        "cancel": "🚫 Отмена",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Кого заблокировать"
            " то?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Кого разблокировать"
            " то?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Ты используешь"
            " нестабильную ветку </b><code>{}</code><b>!</b>"
        ),
    }

    strings_de = {
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Zu vieleArgumente</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Chat {} hinzugefügt"
            " zuUserbot-Blacklist</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Chat {} entfernt aus"
            "Blacklist für Userbots</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Benutzer {}"
            "Von Userbot auf die schwarze Liste gesetzt</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Benutzer {}"
            " von Userbot-Blacklist entfernt</b>"
        ),
        "what_prefix": "❓ <b>Welches Präfix soll ich setzen?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Präfix muss"
            "bestehen nur aus einem Zeichen</b>"
        ),
        "prefix_set": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Präfix aktualisiert."
            " Um es zurückzugeben, verwenden Sie</b> <code>{newprefix}setprefix"
            "{oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Alias ​​erstellt."
            " Verwenden Sie es über</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Aliasse:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Befehl</b>"
            " <code>{}</code> <b>existiert nicht</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Eingabe erforderlich"
            "Befehl und Alias ​​dafür</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Name erforderlich"
            "alias</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Alias</b>"
            " <code>{}</code> <b>gelöscht</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji><b>Alias</b>"
            " <code>{}</code> <b>existiert nicht</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5368324170671202286>👍</emoji><b>Basis gelöscht</b>"
        ),
        "hikka": (
            "{}\n\n<emoji document_id=5406931726184225260>🧐</emoji> <b>Version:"
            " {}.{}.{}</b>\n<emoji document_id=6318902906900711458>🧱</emoji> <b>Build:"
            " </b><i>{}</i>\n\n<emoji document_id=5233346091725888979>⚙️</emoji>"
            " <b>Hikka-TL: </b><i>{}</i>\n\n<emoji"
            "document_id=5454182070156794055>⌨️</emoji> <b>Entwickler:"
            "t.me/hikariyatama</b>"
        ),
        "_cls_doc": "Verwaltung der Grundeinstellungen des Userbots",
        "confirm_cleardb": (
            "⚠️ <b>Sind Sie sicher, dass Sie die Datenbank zurücksetzen möchten?</b>"
        ),
        "cleardb_confirm": "🗑 Basis löschen",
        "cancel": "🚫 Stornieren",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Zu blockierende"
            " Personendann?"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Wen entsperrendann?"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Sie verwenden"
            "instabiler Zweig </b><code>{}</code><b>!</b>"
        ),
    }

    strings_tr = {
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Çok fazla"
            " argümanlar</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Sohbet {} eklendi"
            "userbot kara listesi</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Sohbet {} şuradan"
            " kaldırıldıUserbot Kara Listesi</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Kullanıcı {}"
            " userbot tarafından kara listeye alındı</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Kullanıcı {}"
            " userbot kara listesinden kaldırıldı</b>"
        ),
        "what_prefix": "❓ <b>Hangi öneki ayarlamalıyım?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Önek olmalıdır"
            "sadece bir karakterden oluşur</b>"
        ),
        "prefix_set": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Önek güncellendi."
            " Geri vermek için,</b> <code>{newprefix}setprefix'i kullanın"
            "{oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Takma ad"
            " oluşturuldu.</b> <code>{}</code> yoluyla kullanın"
        ),
        "aliases": "<b>🔗 Takma adlar:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Komut</b>"
            " <code>{}</code> <b>yok</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Gerekli girin"
            "komut ve bunun için takma ad</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Ad gereklitakma ad</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Takma ad</b>"
            " <code>{}</code> <b>silindi</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji><b> Takma Ad</b>"
            " <code>{}</code> <b>yok</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5368324170671202286>👍</emoji><b> Taban temizlendi</b>"
        ),
        "hikka": (
            "{}\n\n<emoji document_id=5406931726184225260>🧐</emoji> <b>Sürüm:"
            " {}.{}.{}</b>\n<emoji document_id=6318902906900711458>🧱</emoji> <b>Yapı:"
            " </b><i>{}</i>\n\n<emoji document_id=5233346091725888979>⚙️</emoji>"
            " <b>Hikka-TL: </b><i>{}</i>\n\n<emoji"
            "document_id=5454182070156794055>⌨️</emoji> <b>Geliştirici:"
            "t.me/hikariyatama</b>"
        ),
        "_cls_doc": "Userbot temel ayar yönetimi",
        "confirm_cleardb": (
            "⚠️ <b>Veritabanını sıfırlamak istediğinizden emin misiniz?</b>"
        ),
        "cleardb_confirm": "🗑 Tabanı temizle",
        "cancel": "🚫 İptal",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Kimler engellenir"
            "sonra?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Kimin engellemesi"
            " kaldırılırsonra?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Kullanıyorsunuz"
            "kararsız dal </b><code>{}</code><b>!</b>"
        ),
    }

    strings_hi = {
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>बहुत अधिकतर्क</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>चैट {} इसमें जोड़ा"
            " गयायूजरबॉट ब्लैकलिस्ट</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>चैट {} से हटा दिया"
            " गयायूजरबॉट ब्लैकलिस्ट</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>उपयोगकर्ता {}"
            "userbot द्वारा काली सूची में डाला गया</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>उपयोगकर्ता {}"
            "userbot ब्लैकलिस्ट से हटाया गया</b>"
        ),
        "what_prefix": "❓ <b>मुझे कौन सा उपसर्ग सेट करना चाहिए?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>उपसर्ग अवश्य होना"
            " चाहिएकेवल एक वर्ण से मिलकर बनता है</b>"
        ),
        "prefix_set": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>उपसर्ग अपडेट किया"
            " गया। इसे वापस करने के लिए, उपयोग करें</b>"
            " <code>{newprefix}setprefix{oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>उपनाम बनाया गया।"
            "</b> <code>{}</code> के माध्यम से इसका उपयोग करें"
        ),
        "aliases": "<b>🔗 उपनाम:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>कमांड</b>"
            " <code>{}</code> <b>मौजूद नहीं है</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>आवश्यक दर्ज करें"
            "इसके लिए आदेश और उपनाम</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>नाम की आवश्यकता है"
            "उपनाम</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>उपनाम</b>"
            " <code>{}</code> <b>हटाया</b>।"
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji><b> उपनाम</b>"
            " <code>{}</code> <b>मौजूद नहीं है</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5368324170671202286>👍</emoji><b> आधार साफ़ हो गया</b>"
        ),
        "hikka": (
            "{}\n\n<emoji document_id=5406931726184225260>🧐</emoji> <b>वर्शन:"
            " {}.{}.{}</b>\n<emoji document_id=6318902906900711458>🧱</emoji> <b>बिल्ड:"
            " </b><i>{}</i>\n\n<emoji document_id=5233346091725888979>⚙️</emoji>"
            " <b>हिक्का-टीएल: </b><i>{}</i>\n\n<emoji"
            "document_id=5454182070156794055>⌨️</emoji> <b>डेवलपर:"
            "t.me/hikariyatama</b>"
        ),
        "_cls_doc": "Userbot मूलभूत सेटिंग प्रबंधन",
        "confirm_cleardb": "⚠️ <b>क्या आप वाकई डेटाबेस को रीसेट करना चाहते हैं?</b>",
        "cleardb_confirm": "🗑 आधार साफ़ करें",
        "cancel": "🚫 रद्द करें",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>किसे ब्लॉक करना है"
            "तो?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>किसको अनब्लॉक करना है"
            "तो?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>आप उपयोग कर रहे"
            " हैंअस्थिर शाखा </b><code>{}</code><b>!</b>"
        ),
    }

    strings_uz = {
        "too_many_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Juda ko'p"
            " argumentlar</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Chat {} qo'shildi"
            " userbot qora ro' yxati</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Chat {} o'chirildi"
            "Userbot qora ro'yxati</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Foydalanuvchi {}"
            " userbot tomonidan qora ro'yxatga kiritilgan</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Foydalanuvchi {}"
            " userbot qora ro'yxatidan olib tashlandi</b>"
        ),
        "what_prefix": "❓ <b>Qaysi prefiksni o'rnatishim kerak?</b>",
        "prefix_incorrect": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Prefiks kerak"
            "faqat bitta belgidan iborat</b>"
        ),
        "prefix_set": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Prefiks yangilandi."
            " Uni qaytarish uchun</b> <code>{newprefix}setprefix dan foydalaning."
            "{oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Taxallus yaratildi."
            "</b> <code>{}</code> orqali foydalaning"
        ),
        "aliases": "<b>🔗 Taxalluslar:</b>\n",
        "no_command": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Buyruq</b>"
            " <code>{}</code> <b>mavjud</b>"
        ),
        "alias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Kirish kerak"
            "buyruq va uning taxallusi</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Ism keraktaxallus</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Taxallus</b>"
            " <code>{}</code> <b>o'chirildi</b>."
        ),
        "no_alias": (
            "<emoji document_id=5436162517686557387>🚫</emoji><b> Taxallus</b>"
            " <code>{}</code> <b>mavjud</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5368324170671202286>👍</emoji><b> Baza tozalandi</b>"
        ),
        "hikka": (
            "{}\n\n<emoji document_id=5406931726184225260>🧐</emoji> <b>Versiya:"
            " {}.{}.{}</b>\n<emoji document_id=6318902906900711458>🧱</emoji>"
            " <b>Yaratish: </b><i>{}</i>\n\n<emoji"
            " document_id=5233346091725888979>⚙️</emoji> <b>Hikka-TL:"
            " </b><i>{}</i>\n\n<emojidocument_id=5454182070156794055>⌨️</emoji>"
            " <b>Ishlab chiquvchi:t.me/hikariyatama</b>"
        ),
        "_cls_doc": "Userbot asosiy sozlamalarini boshqarish",
        "confirm_cleardb": (
            "⚠️ <b>Siz maʼlumotlar bazasini qayta o'rnatmoqchimisiz?</b>"
        ),
        "cleardb_confirm": "🗑 Bazani tozalash",
        "cancel": "🚫 Bekor qilish",
        "who_to_blacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Kimni bloklash kerak"
            "keyin?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5384612769716774600>❓</emoji> <b>Kimni blokdan"
            " chiqarish kerakkeyin?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Siz"
            " foydalanmoqdasizbarqaror filial </b><code>{}</code><b>!</b>"
        ),
    }

    async def blacklistcommon(self, message: Message):
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args"))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid

    @loader.command(
        ru_doc="Показать версию Hikka",
        de_doc="Zeige die Hikka-Version an",
        tr_doc="Hikka sürümünü gösterir",
        uz_doc="Hikka versiyasini ko'rsatish",
        hi_doc="Hikka का संस्करण दिखाएं",
    )
    async def hikkacmd(self, message: Message):
        """Get Hikka version"""
        await utils.answer(
            message,
            self.strings("hikka").format(
                (
                    utils.get_platform_emoji()
                    + (
                        "<emoji document_id=5192756799647785066>✌️</emoji><emoji"
                        " document_id=5193117564015747203>✌️</emoji><emoji"
                        " document_id=5195050806105087456>✌️</emoji><emoji"
                        " document_id=5195457642587233944>✌️</emoji>"
                        if "LAVHOST" in os.environ
                        else ""
                    )
                )
                if self._client.hikka_me.premium and CUSTOM_EMOJIS
                else "🌘 <b>Hikka userbot</b>",
                *version.__version__,
                utils.get_commit_url(),
                f"{telethon.__version__} #{telethon.tl.alltlobjects.LAYER}",
            )
            + (
                ""
                if version.branch == "master"
                else self.strings("unstable").format(version.branch)
            ),
        )

    @loader.command(
        ru_doc="[чат] [модуль] - Отключить бота где-либо",
        de_doc="[chat] [Modul] - Deaktiviere den Bot irgendwo",
        tr_doc="[sohbet] [modül] - Botu herhangi bir yerde devre dışı bırakın",
        uz_doc="[chat] [modul] - Botni hozircha o'chirish",
        hi_doc="[चैट] [मॉड्यूल] - कहीं भी बॉट निष्क्रिय करें",
    )
    async def blacklist(self, message: Message):
        """[chat_id] [module] - Blacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    @loader.command(
        ru_doc="[чат] - Включить бота где-либо",
        de_doc="[chat] - Aktiviere den Bot irgendwo",
        tr_doc="[sohbet] - Botu herhangi bir yerde etkinleştirin",
        uz_doc="[chat] - Botni hozircha yoqish",
        hi_doc="[चैट] - कहीं भी बॉट सक्रिय करें",
    )
    async def unblacklist(self, message: Message):
        """<chat_id> - Unblacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            list(set(self._db.get(main.__name__, "blacklist_chats", [])) - {chatid}),
        )

        await utils.answer(message, self.strings("unblacklisted").format(chatid))

    async def getuser(self, message: Message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()

            if reply:
                return reply.sender_id

            return message.to_id.user_id if message.is_private else False

    @loader.command(
        ru_doc="[пользователь] - Запретить пользователю выполнять команды",
        de_doc="[Benutzer] - Verbiete dem Benutzer, Befehle auszuführen",
        tr_doc="[kullanıcı] - Kullanıcıya komutları yürütmeyi yasakla",
        uz_doc="[foydalanuvchi] - Foydalanuvchiga buyruqlarni bajarishni taqiqlash",
        hi_doc="[उपयोगकर्ता] - उपयोगकर्ता को कमांड चलाने से रोकें",
    )
    async def blacklistuser(self, message: Message):
        """[user_id] - Prevent this user from running any commands"""
        user = await self.getuser(message)

        if not user:
            await utils.answer(message, self.strings("who_to_blacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(message, self.strings("user_blacklisted").format(user))

    @loader.command(
        ru_doc="[пользователь] - Разрешить пользователю выполнять команды",
        de_doc="[Benutzer] - Erlaube dem Benutzer, Befehle auszuführen",
        tr_doc="[kullanıcı] - Kullanıcıya komutları yürütmeyi yasakla",
        uz_doc="[foydalanuvchi] - Foydalanuvchiga buyruqlarni bajarishni taqiqlash",
        hi_doc="[उपयोगकर्ता] - उपयोगकर्ता को कमांड चलाने से रोकें",
    )
    async def unblacklistuser(self, message: Message):
        """[user_id] - Allow this user to run permitted commands"""
        user = await self.getuser(message)

        if not user:
            await utils.answer(message, self.strings("who_to_unblacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            list(set(self._db.get(main.__name__, "blacklist_users", [])) - {user}),
        )

        await utils.answer(
            message,
            self.strings("user_unblacklisted").format(user),
        )

    @loader.owner
    @loader.command(
        ru_doc="<префикс> - Установить префикс команд",
        de_doc="<Präfix> - Setze das Befehlspräfix",
        tr_doc="<önek> - Komut öneki ayarla",
        uz_doc="<avvalgi> - Buyruqlar uchun avvalgi belgilash",
        hi_doc="<उपसर्ग> - कमांड उपसर्ग सेट करें",
    )
    async def setprefix(self, message: Message):
        """<prefix> - Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = self.get_prefix()
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    @loader.command(
        ru_doc="Показать список алиасов",
        de_doc="Zeige Aliase",
        tr_doc="Takma adları göster",
        uz_doc="Aliaslarni ko'rsatish",
        hi_doc="उपनामों की सूची दिखाएं",
    )
    async def aliases(self, message: Message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases")

        string += "\n".join(
            [f"▫️ <code>{i}</code> &lt;- {y}" for i, y in aliases.items()]
        )

        await utils.answer(message, string)

    @loader.owner
    @loader.command(
        ru_doc="Установить алиас для команды",
        de_doc="Setze einen Alias für einen Befehl",
        tr_doc="Bir komut için takma ad ayarla",
        uz_doc="Buyrug' uchun alias belgilash",
        hi_doc="एक कमांड के लिए उपनाम सेट करें",
    )
    async def addalias(self, message: Message):
        """Set an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd = args
        if self.allmodules.add_alias(alias, cmd):
            self.set(
                "aliases",
                {
                    **self.get("aliases", {}),
                    alias: cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command").format(utils.escape_html(cmd)),
            )

    @loader.owner
    @loader.command(
        ru_doc="Удалить алиас для команды",
        de_doc="Entferne einen Alias für einen Befehl",
        tr_doc="Bir komut için takma ad kaldır",
        uz_doc="Buyrug' uchun aliasni o'chirish",
        hi_doc="एक कमांड के लिए उपनाम हटाएं",
    )
    async def delalias(self, message: Message):
        """Remove an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]
        removed = self.allmodules.remove_alias(alias)

        if not removed:
            await utils.answer(
                message,
                self.strings("no_alias").format(utils.escape_html(alias)),
            )
            return

        current = self.get("aliases", {})
        del current[alias]
        self.set("aliases", current)
        await utils.answer(
            message,
            self.strings("alias_removed").format(utils.escape_html(alias)),
        )

    @loader.owner
    @loader.command(
        ru_doc="Очистить базу данных",
        de_doc="Datenbank leeren",
        tr_doc="Veritabanını temizle",
        uz_doc="Ma'lumotlar bazasini tozalash",
        hi_doc="डेटाबेस साफ़ करें",
    )
    async def cleardb(self, message: Message):
        """Clear the entire database, effectively performing a factory reset"""
        await self.inline.form(
            self.strings("confirm_cleardb"),
            message,
            reply_markup=[
                {
                    "text": self.strings("cleardb_confirm"),
                    "callback": self._inline__cleardb,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    async def _inline__cleardb(self, call: InlineCall):
        self._db.clear()
        self._db.save()
        await utils.answer(call, self.strings("db_cleared"))
