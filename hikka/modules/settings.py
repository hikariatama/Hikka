# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import os

import pyrogram
import telethon
from telethon.extensions.html import CUSTOM_EMOJIS
from telethon.tl.types import Message

from .. import loader, main, utils, version
from ..compat.dragon import DRAGON_EMOJI
from ..inline.types import InlineCall


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Too many args</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Chat {} blacklisted"
            " from userbot</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Chat {}"
            " unblacklisted from userbot</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>User {} blacklisted"
            " from userbot</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>User {}"
            " unblacklisted from userbot</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>What should the prefix"
            " be set to?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Prefix must be one"
            " symbol in length</b>"
        ),
        "prefix_set": (
            "{} <b>Command prefix"
            " updated. Type</b> <code>{newprefix}setprefix {oldprefix}</code> <b>to"
            " change it back</b>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Alias created."
            " Access it with</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Aliases:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Command</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You must provide a"
            " command and the alias for it</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You must provide the"
            " alias name</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Alias</b>"
            " <code>{}</code> <b>removed</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Alias</b>"
            " <code>{}</code> <b>does not exist</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Database cleared</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:</b> <i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Developer:"
            " t.me/hikariatama</b>"
        ),
        "confirm_cleardb": "⚠️ <b>Are you sure, that you want to clear database?</b>",
        "cleardb_confirm": "🗑 Clear database",
        "cancel": "🚫 Cancel",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Who to blacklist?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Who to"
            " unblacklist?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>You are using an"
            " unstable branch</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Your Dragon and Hikka"
            " prefixes must be different!</b>"
        ),
    }

    strings_ru = {
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Слишком много"
            " аргументов</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Чат {} добавлен в"
            " черный список юзербота</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Чат {} удален из"
            " черного списка юзербота</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Пользователь {}"
            " добавлен в черный список юзербота</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Пользователь {}"
            " удален из черного списка юзербота</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>А какой префикс"
            " ставить то?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Префикс должен"
            " состоять только из одного символа</b>"
        ),
        "prefix_set": (
            "{} <b>Префикс обновлен."
            " Чтобы вернуть его, используй</b> <code>{newprefix}setprefix"
            " {oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Алиас создан."
            " Используй его через</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Алиасы:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Команда</b>"
            " <code>{}</code> <b>не существует</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Требуется ввести"
            " команду и алиас для нее</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Требуется имя"
            " алиаса</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Алиас</b>"
            " <code>{}</code> <b>удален</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Алиас</b>"
            " <code>{}</code> <b>не существует</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>База очищена</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:</b> <i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Developer:"
            " t.me/hikariatama</b>"
        ),
        "_cls_doc": "Управление базовыми настройками юзербота",
        "confirm_cleardb": "⚠️ <b>Вы уверены, что хотите сбросить базу данных?</b>",
        "cleardb_confirm": "🗑 Очистить базу",
        "cancel": "🚫 Отмена",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Кого заблокировать"
            " то?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Кого разблокировать"
            " то?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Ты используешь"
            " нестабильную ветку</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Префиксы Dragon и"
            " Hikka должны отличаться!</b>"
        ),
    }

    strings_it = {
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Troppi argomenti</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Il gruppo {} è stato"
            " aggiunto alla lista nera del bot</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Il gruppo {} è stato"
            " rimosso dalla lista nera del bot</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>L'utente {} è stato"
            " aggiunto alla lista nera del bot</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>L'utente {} è stato"
            " rimosso dalla lista nera del bot</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Che prefisso devo"
            " usare?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Il prefisso deve"
            " essere di un solo carattere</b>"
        ),
        "prefix_set": (
            "{} <b>Il prefisso è stato aggiornato."
            " Per ripristinarlo, usa</b> <code>{newprefix}setprefix"
            " {oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>L'alias è stato"
            " creato. Usa il comando con</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Alias:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Il comando</b>"
            " <code>{}</code> <b>non esiste</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>È necessario"
            " specificare un comando e un alias per questo</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Nome alias"
            " richiesto</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Alias</b>"
            " <code>{}</code> <b>rimosso</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Alias</b>"
            " <code>{}</code> <b>non esiste</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Database"
            " cancellato</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:</b> <i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Developer:"
            " t.me/hikariatama</b>"
        ),
        "_cls_doc": "Gestisci le impostazioni base del bot utente",
        "confirm_cleardb": "⚠️ <b>Sei sicuro di voler cancellare il database?</b>",
        "cleardb_confirm": "🗑 Cancella il database",
        "cancel": "🚫 Annulla",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Chi vuoi bloccare?"
            " </b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Chi vuoi sbloccare?"
            " </b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Stai usando una"
            " versione instabile</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>I prefissi Dragon e"
            " Hikka devono essere diversi!</b>"
        ),
    }

    strings_de = {
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Zu vieleArgumente</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Chat {} hinzugefügt"
            " zuUserbot-Blacklist</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Chat {} entfernt aus"
            "Blacklist für Userbots</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Benutzer {}"
            "Von Userbot auf die schwarze Liste gesetzt</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Benutzer {}"
            " von Userbot-Blacklist entfernt</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Welches Präfix soll"
            " ich setzen?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Präfix muss"
            "bestehen nur aus einem Zeichen</b>"
        ),
        "prefix_set": (
            "{} <b>Präfix aktualisiert."
            " Um es zurückzugeben, verwenden Sie</b> <code>{newprefix}setprefix"
            "{oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Alias ​​erstellt."
            " Verwenden Sie es über</b> <code>{}</code>"
        ),
        "aliases": "<b>🔗 Aliasse:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Befehl</b>"
            " <code>{}</code> <b>existiert nicht</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Eingabe erforderlich"
            "Befehl und Alias ​​dafür</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Name erforderlich"
            "alias</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Alias</b>"
            " <code>{}</code> <b>gelöscht</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji><b>Alias</b>"
            " <code>{}</code> <b>existiert nicht</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji><b>Basis gelöscht</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:"
            "</b> <i>{}</i>\n\n<emoji document_id=5454182070156794055>⌨️</emoji>"
            " <b>Entwickler: t.me/hikariatama</b>"
        ),
        "_cls_doc": "Verwaltung der Grundeinstellungen des Userbots",
        "confirm_cleardb": (
            "⚠️ <b>Sind Sie sicher, dass Sie die Datenbank zurücksetzen möchten?</b>"
        ),
        "cleardb_confirm": "🗑 Basis löschen",
        "cancel": "🚫 Stornieren",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Zu blockierende"
            " Personendann?"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Wen entsperrendann?"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Sie verwenden"
            "instabiler Zweig</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Präfixe"
            "Dragon und Hikka müssen sich unterscheiden!</b>"
        ),
    }

    strings_tr = {
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Çok fazla"
            " argüman var</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>{} adlı sohbet,"
            " kullanıcı botu kara listesine eklendi</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>{} adlı sohbet,"
            " kullanıcı botu kara listesinden çıkartıldı</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>{} adlı kişi,"
            " kullanıcı botu kara listesine eklendi</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>{} adlı kişi,"
            " kullanıcı botu kara listesine eklendi</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Hangi öneki"
            " ayarlamalıyım?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Önek sadece"
            " bir karakterden oluşabilir</b>"
        ),
        "prefix_set": (
            "{} <b>Komut öneki güncellendi. Yeniden değiştirmek için"
            " için,</b> <code>{newprefix}setprefix {oldprefix}</code> <b>komutunu"
            " kullanın</b>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Komut için takma ad"
            " oluşturuldu.</b> <code>{}</code> <b>komutuyla kullanabilirsiniz</b>"
        ),
        "aliases": "<b>🔗 Takma adlar:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Komut</b>"
            " <code>{}</code> <b>mevcut değil</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bunun için bir komut"
            " ve takma ad girmeniz gerekmektedir</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bunun için bir takma "
            " ad girmeniz gerekmektedir</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Takma ad</b>"
            " <code>{}</code> <b>kaldırıldı</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Takma Ad</b>"
            " <code>{}</code> <b>mevcut değil</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Veri Tabanı"
            " sıfırlandı</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:"
            "</b> <i>{}</i>\n\n<emoji document_id=5454182070156794055>⌨️</emoji>"
            " <b>Geliştirici: t.me/hikariatama</b>"
        ),
        "_cls_doc": "Userbot temel ayar yönetimi",
        "confirm_cleardb": (
            "⚠️ <b>Veritabanını sıfırlamak istediğinizden emin misiniz?</b>"
        ),
        "cleardb_confirm": "🗑 Veri Tabanını sıfırla",
        "cancel": "🚫 İptal",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Kimler engellenir"
            "sonra?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Kimin engellemesi"
            " kaldırılsın?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Hikka'nın kararsız"
            " bir sürümü olan <code>{}</code></b>  sürümünü kullanıyorsunuz!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Önekler çakışıyor!</b>"
        ),
    }

    strings_uz = {
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Juda ko'p"
            " argumentlar</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Chat {} qo'shildi"
            " userbot qora ro' yxati</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Chat {} o'chirildi"
            "Userbot qora ro'yxati</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Foydalanuvchi {}"
            " userbot tomonidan qora ro'yxatga kiritilgan</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Foydalanuvchi {}"
            " userbot qora ro'yxatidan olib tashlandi</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Qaysi prefiksni"
            " o'rnatishim kerak?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Prefiks kerak"
            "faqat bitta belgidan iborat</b>"
        ),
        "prefix_set": (
            "{} <b>Prefiks yangilandi."
            " Uni qaytarish uchun</b> <code>{newprefix}setprefix dan foydalaning."
            "{oldprefix}</code>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Taxallus yaratildi."
            "</b> <code>{}</code> <b>orqali foydalaning</b>"
        ),
        "aliases": "<b>🔗 Taxalluslar:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Buyruq</b>"
            " <code>{}</code> <b>mavjud</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Kirish kerak"
            "buyruq va uning taxallusi</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ism keraktaxallus</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Taxallus</b>"
            " <code>{}</code> <b>o'chirildi</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Taxallus</b>"
            " <code>{}</code> <b>mavjud</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Baza tozalandi</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:</b> <i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Ishlab chiquvchi:"
            " t.me/hikariatama</b>"
        ),
        "_cls_doc": "Userbot asosiy sozlamalarini boshqarish",
        "confirm_cleardb": (
            "⚠️ <b>Siz maʼlumotlar bazasini qayta o'rnatmoqchimisiz?</b>"
        ),
        "cleardb_confirm": "🗑 Bazani tozalash",
        "cancel": "🚫 Bekor qilish",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Kimni bloklash kerak"
            "keyin?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Kimni blokdan"
            " chiqarish kerakkeyin?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Siz"
            " foydalanayotgan versiya</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Dragon va Hikka"
            " prefikslari boshqacha bo'lishi kerak!</b>"
        ),
    }

    strings_es = {
        "chat_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>El chat {} ha sido"
            " añadido a la lista negra</b>"
        ),
        "chat_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>El chat {} ha sido"
            " removido de la lista negra</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>El usuario {} ha sido"
            " añadido a la lista negra</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>El usuario {} ha sido"
            " removido de la lista negra</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>¿Cuál es el prefijo"
            " que quieres establecer?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>El prefijo debe ser"
            " un solo carácter</b>"
        ),
        "prefix_set": (
            "{} <b>El prefijo ha sido"
            " establecido. El nuevo prefijo es</b> <code>{newprefix}setprefix"
            " {oldprefix}</code> <b>para restablecerlo</b>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>El alias</b>"
            " <code>{}</code> <b>ha sido creado</b>"
        ),
        "alias_deleted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>El alias</b>"
            " <code>{}</code> <b>ha sido eliminado</b>"
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Alias</b>"
            " <code>{}</code> <b>no existe</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji><b>Base de datos"
            " borrada</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:</b> <i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Desarrollador:"
            " t.me/hikariatama</b>"
        ),
        "_cls_doc": "Los ajustes básicos del usuario del bot",
        "confirm_cleardb": "⚠️ <b>¿Quieres borrar la base de datos?</b>",
        "cleardb_confirm": "🗑 Borrar base de datos",
        "cancel": "🚫 Cancelar",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>¿Quién quieres"
            " añadir a la lista negra?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>¿Quién quieres"
            " eliminar de la lista negra?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Estás usando la"
            " rama inestable</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>¡Dragon y Hikka deben"
            " tener prefijos diferentes!</b>"
        ),
    }

    strings_kk = {
        "too_many_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Тым көп"
            " аргументтер</b>"
        ),
        "blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Чат {} чаттар"
            "дың көрсеткішінің күйіне қосылды</b>"
        ),
        "unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Чат {} чаттар"
            "дың көрсеткішінің күйінен алынды</b>"
        ),
        "user_blacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Пайдаланушы {}"
            " пайдаланушылардың көрсеткішінің күйіне қосылды</b>"
        ),
        "user_unblacklisted": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Пайдаланушы {}"
            " пайдаланушылардың көрсеткішінің күйінен алынды</b>"
        ),
        "what_prefix": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Бірақ"
            " қандай әліпби беремін?</b>"
        ),
        "prefix_incorrect": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Әліпби тек"
            " бір таңбадан тұруы керек</b>"
        ),
        "prefix_set": (
            "{} <b>Әліпби жаңартылды."
            " Қайтару үшін</b> <code>{newprefix}setprefix {oldprefix}</code>"
            " <b>пайдаланыңыз</b>"
        ),
        "alias_created": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Алиас жасалды."
            " Оны</b> <code>{}</code> <b>пайдаланыңыз</b>"
        ),
        "aliases": "<b>🔗 Алиастар:</b>\n",
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Команда</b>"
            " <code>{}</code> <b>жоқ</b>"
        ),
        "alias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Команда мен"
            " оның алиасын енгізуіңіз керек</b>"
        ),
        "delalias_args": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Алиас атауы"
            " енгізуіңіз керек</b>"
        ),
        "alias_removed": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>Алиас</b>"
            " <code>{}</code> <b>жойылды</b>."
        ),
        "no_alias": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Алиас</b>"
            " <code>{}</code> <b>жоқ</b>"
        ),
        "db_cleared": (
            "<emoji document_id=5197474765387864959>👍</emoji> <b>База тазаланды</b>"
        ),
        "hikka": (
            "{} <b>{}.{}.{}</b> <i>{}</i>\n\n<b><emoji"
            " document_id=5377437404078546699>💜</emoji> <b>Hikka-TL:"
            "</b> <i>{}</i>\n{}"
            " <b>Hikka-Pyro:</b> <i>{}</i>\n\n<emoji"
            " document_id=5454182070156794055>⌨️</emoji> <b>Әзірлеуші:"
            " t.me/hikariatama</b>"
        ),
        "_cls_doc": "Жүйе бастапқы параметрлерін басқару",
        "confirm_cleardb": (
            "⚠️ <b>Сіз дейінгі база деректерін тазалауға сенімдісіз бе?</b>"
        ),
        "cleardb_confirm": "🗑 База деректерін тазалау",
        "cancel": "🚫 Болдырмау",
        "who_to_blacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Кімді блога қою"
            " керек?</b>"
        ),
        "who_to_unblacklist": (
            "<emoji document_id=5382187118216879236>❓</emoji> <b>Кімді блога қоюды"
            " болдырмау керек?</b>"
        ),
        "unstable": (
            "\n\n<emoji document_id=5467370583282950466>🙈</emoji> <b>Сіз қолданбаған"
            " белгісіз қосымша</b> <code>{}</code><b>!</b>"
        ),
        "prefix_collision": (
            "<emoji document_id=5469654973308476699>💣</emoji> <b>Dragon және"
            " Hikka префикстері айырмасы керек!</b>"
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
        it_doc="Mostra la versione di Hikka",
        de_doc="Zeige die Hikka-Version an",
        tr_doc="Hikka sürümünü gösterir",
        uz_doc="Hikka versiyasini ko'rsatish",
        es_doc="Mostrar la versión de Hikka",
        kk_doc="Hikka нұсқасын көрсету",
    )
    async def hikkacmd(self, message: Message):
        """Get Hikka version"""
        await utils.answer_file(
            message,
            "https://github.com/hikariatama/assets/raw/master/hikka_cat_banner.mp4",
            self.strings("hikka").format(
                (
                    (
                        utils.get_platform_emoji(self._client)
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
                    else "🌘 <b>Hikka userbot</b>"
                ),
                *version.__version__,
                utils.get_commit_url(),
                f"{telethon.__version__} #{telethon.tl.alltlobjects.LAYER}",
                (
                    "<emoji document_id=5377399247589088543>🔥</emoji>"
                    if self._client.pyro_proxy
                    else "<emoji document_id=5418308381586759720>📴</emoji>"
                ),
                f"{pyrogram.__version__} #{pyrogram.raw.all.layer}",
            )
            + (
                ""
                if version.branch == "master"
                else self.strings("unstable").format(version.branch)
            ),
        )

    @loader.command(
        ru_doc="[чат] [модуль] - Отключить бота где-либо",
        it_doc="[chat] [module] - Disattiva il bot ovunque",
        de_doc="[chat] [Modul] - Deaktiviere den Bot irgendwo",
        tr_doc="[sohbet] [modül] - Botu herhangi bir yerde devre dışı bırakın",
        uz_doc="[chat] [modul] - Botni hozircha o'chirish",
        es_doc="[chat] [módulo] - Desactivar el bot en cualquier lugar",
        kk_doc="[сөйлесу] [модуль] - Ботты қайда болса болсын өшіру",
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
        it_doc="[chat] - Attiva il bot ovunque",
        de_doc="[chat] - Aktiviere den Bot irgendwo",
        tr_doc="[sohbet] - Botu herhangi bir yerde etkinleştirin",
        uz_doc="[chat] - Botni hozircha yoqish",
        es_doc="[chat] - Activar el bot en cualquier lugar",
        kk_doc="[сөйлесу] - Ботты қайда болса болсын қосу",
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
        it_doc="[utente] - Impedisci all'utente di eseguire comandi",
        de_doc="[Benutzer] - Verbiete dem Benutzer, Befehle auszuführen",
        tr_doc="[kullanıcı] - Kullanıcıya komutları yürütmeyi yasakla",
        uz_doc="[foydalanuvchi] - Foydalanuvchiga buyruqlarni bajarishni taqiqlash",
        es_doc="[usuario] - Prohibir al usuario ejecutar comandos",
        kk_doc="[пайдаланушы] - Пайдаланушыға командаларды орындауға рұқсат бермеу",
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
        it_doc="[utente] - Consenti all'utente di eseguire comandi",
        de_doc="[Benutzer] - Erlaube dem Benutzer, Befehle auszuführen",
        tr_doc="[kullanıcı] - Kullanıcıya komutları yürütmeyi yasakla",
        uz_doc="[foydalanuvchi] - Foydalanuvchiga buyruqlarni bajarishni taqiqlash",
        es_doc="[usuario] - Prohibir al usuario ejecutar comandos",
        kk_doc="[пайдаланушы] - Пайдаланушыға командаларды орындауға рұқсат бермеу",
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
        ru_doc="[dragon] <префикс> - Установить префикс команд",
        it_doc="[dragon] <prefisso> - Imposta il prefisso dei comandi",
        de_doc="[dragon] <Präfix> - Setze das Befehlspräfix",
        tr_doc="[dragon] <önek> - Komut öneki ayarla",
        uz_doc="[dragon] <avvalgi> - Buyruqlar uchun avvalgi belgilash",
        es_doc="[dragon] <prefijo> - Establecer el prefijo de comandos",
        kk_doc="[dragon] <бастауыш> - Командалардың бастауышын орнату",
    )
    async def setprefix(self, message: Message):
        """[dragon] <prefix> - Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args.split()) == 2 and args.split()[0] == "dragon":
            args = args.split()[1]
            is_dragon = True
        else:
            is_dragon = False

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        if (
            not is_dragon
            and args[0] == self._db.get("dragon.prefix", "command_prefix", ",")
            or is_dragon
            and args[0] == self._db.get(main.__name__, "command_prefix", ".")
        ):
            await utils.answer(message, self.strings("prefix_collision"))
            return

        oldprefix = (
            f"dragon {self.get_prefix('dragon')}" if is_dragon else self.get_prefix()
        )
        self._db.set(
            "dragon.prefix" if is_dragon else main.__name__,
            "command_prefix",
            args,
        )
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                (
                    DRAGON_EMOJI
                    if is_dragon
                    else "<emoji document_id=5197474765387864959>👍</emoji>"
                ),
                newprefix=utils.escape_html(
                    self.get_prefix() if is_dragon else args[0]
                ),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    @loader.command(
        ru_doc="Показать список алиасов",
        it_doc="Mostra la lista degli alias",
        de_doc="Zeige Aliase",
        tr_doc="Takma adları göster",
        uz_doc="Aliaslarni ko'rsatish",
        es_doc="Mostrar lista de alias",
        kk_doc="Айланыстарды көрсету",
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
        it_doc="Imposta un alias per il comando",
        de_doc="Setze einen Alias für einen Befehl",
        tr_doc="Bir komut için takma ad ayarla",
        uz_doc="Buyrug' uchun alias belgilash",
        es_doc="Establecer alias para el comando",
        kk_doc="Команда үшін айланыс орнату",
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
        it_doc="Rimuovi un alias per il comando",
        de_doc="Entferne einen Alias für einen Befehl",
        tr_doc="Bir komut için takma ad kaldır",
        uz_doc="Buyrug' uchun aliasni o'chirish",
        es_doc="Eliminar alias para el comando",
        kk_doc="Команда үшін айланысты жою",
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
        it_doc="Cancella il database",
        de_doc="Datenbank leeren",
        tr_doc="Veritabanını temizle",
        uz_doc="Ma'lumotlar bazasini tozalash",
        es_doc="Limpiar la base de datos",
        kk_doc="Деректер базасын тазалау",
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
