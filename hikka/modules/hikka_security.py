#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import time
import typing

from telethon.tl.types import Message, PeerUser, User
from telethon.utils import get_display_name
from telethon.hints import EntityLike

from .. import loader, security, utils, main
from ..inline.types import InlineCall, InlineMessage
from ..security import (
    DEFAULT_PERMISSIONS,
    EVERYONE,
    GROUP_ADMIN,
    GROUP_ADMIN_ADD_ADMINS,
    GROUP_ADMIN_BAN_USERS,
    GROUP_ADMIN_CHANGE_INFO,
    GROUP_ADMIN_DELETE_MESSAGES,
    GROUP_ADMIN_INVITE_USERS,
    GROUP_ADMIN_PIN_MESSAGES,
    GROUP_MEMBER,
    GROUP_OWNER,
    PM,
    SUDO,
    SUPPORT,
)


@loader.tds
class HikkaSecurityMod(loader.Module):
    """Control security settings"""

    service_strings = {
        "for": "for",
        "forever": "forever",
        "user": "user",
        "chat": "chat",
        "command": "command",
        "module": "module",
        "day": "day",
        "days": "days",
        "hour": "hour",
        "hours": "hours",
        "minute": "minute",
        "minutes": "minutes",
        "second": "second",
        "seconds": "seconds",
    }

    service_strings_ru = {
        "for": "на",
        "forever": "навсегда",
        "command": "команду",
        "module": "модуль",
        "chat": "чату",
        "user": "пользователю",
        "day": "день",
        "days": "дня(-ей)",
        "hour": "час",
        "hours": "часа(-ов)",
        "minute": "минута",
        "minutes": "минут(-ы)",
        "second": "секунда",
        "seconds": "секунд(-ы)",
    }

    service_strings_de = {
        "for": "für",
        "forever": "für immer",
        "command": "Befehl",
        "module": "Modul",
        "chat": "Chat",
        "user": "Benutzer",
        "day": "Tag",
        "days": "Tage",
        "hour": "Stunde",
        "hours": "Stunden",
        "minute": "Minute",
        "minutes": "Minuten",
        "second": "Sekunde",
        "seconds": "Sekunden",
    }

    service_strings_uz = {
        "for": "uchun",
        "forever": "doimiy",
        "command": "buyruq",
        "module": "modul",
        "chat": "guruh",
        "user": "foydalanuvchi",
        "day": "kun",
        "days": "kun",
        "hour": "soat",
        "hours": "soat",
        "minute": "daqiqa",
        "minutes": "daqiqa",
        "second": "soniya",
        "seconds": "soniya",
    }

    service_strings_tr = {
        "for": "için",
        "forever": "sürekli",
        "command": "komut",
        "module": "modül",
        "chat": "sohbet",
        "user": "kullanıcı",
        "day": "gün",
        "days": "gün",
        "hour": "saat",
        "hours": "saat",
        "minute": "dakika",
        "minutes": "dakika",
        "second": "saniye",
        "seconds": "saniye",
    }

    service_strings_ja = {
        "for": "のために",
        "forever": "永遠に",
        "command": "コマンド",
        "module": "モジュール",
        "chat": "チャット",
        "user": "ユーザー",
        "day": "日",
        "days": "日",
        "hour": "時間",
        "hours": "時間",
        "minute": "分",
        "minutes": "分",
        "second": "秒",
        "seconds": "秒",
    }

    service_strings_kr = {
        "for": "에 대한",
        "forever": "영원히",
        "command": "명령",
        "module": "모듈",
        "chat": "채팅",
        "user": "사용자",
        "day": "일",
        "days": "일",
        "hour": "시간",
        "hours": "시간",
        "minute": "분",
        "minutes": "분",
        "second": "초",
        "seconds": "초",
    }

    service_strings_ar = {
        "for": "ل",
        "forever": "للأبد",
        "command": "أمر",
        "module": "وحدة",
        "chat": "دردشة",
        "user": "مستخدم",
        "day": "يوم",
        "days": "أيام",
        "hour": "ساعة",
        "hours": "ساعات",
        "minute": "دقيقة",
        "minutes": "دقائق",
        "second": "ثانية",
        "seconds": "ثواني",
    }

    service_strings_es = {
        "for": "para",
        "forever": "para siempre",
        "command": "comando",
        "module": "módulo",
        "chat": "chat",
        "user": "usuario",
        "day": "día",
        "days": "días",
        "hour": "hora",
        "hours": "horas",
        "minute": "minuto",
        "minutes": "minutos",
        "second": "segundo",
        "seconds": "segundos",
    }

    strings = {
        "name": "HikkaSecurity",
        "no_command": "🚫 <b>Command </b><code>{}</code><b> not found!</b>",
        "permissions": (
            "🔐 <b>Here you can configure permissions for </b><code>{}{}</code>"
        ),
        "close_menu": "🙈 Close this menu",
        "global": (
            "🔐 <b>Here you can configure global bounding mask. If the permission is"
            " excluded here, it is excluded everywhere!</b>"
        ),
        "owner": "😎 Owner",
        "sudo": "🧐 Sudo",
        "support": "🤓 Support",
        "group_owner": "🧛‍♂️ Group owner",
        "group_admin_add_admins": "🧑‍⚖️ Admin (add members)",
        "group_admin_change_info": "🧑‍⚖️ Admin (change info)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (ban)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (delete msgs)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (pin)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (invite)",
        "group_admin": "🧑‍⚖️ Admin (any)",
        "group_member": "👥 In group",
        "pm": "🤙 In PM",
        "everyone": "🌍 Everyone (Inline)",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Users in group"
            " </b><code>owner</code><b>:</b>\n\n{}"
        ),
        "sudo_list": (
            "<emoji document_id=5418133868475587618>🧐</emoji> <b>Users in group"
            " </b><code>sudo</code><b>:</b>\n\n{}"
        ),
        "support_list": (
            "<emoji document_id=5415729507128580146>🤓</emoji> <b>Users in group"
            " </b><code>support</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>There is no users in"
            " group </b><code>owner</code>"
        ),
        "no_sudo": (
            "<emoji document_id=5418133868475587618>🧐</emoji> <b>There is no users in"
            " group </b><code>sudo</code>"
        ),
        "no_support": (
            "<emoji document_id=5415729507128580146>🤓</emoji> <b>There is no users in"
            " group </b><code>support</code>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>owner</code>'
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>sudo</code>'
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group </b><code>support</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>owner</code>'
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>sudo</code>'
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group </b><code>support</code>'
        ),
        "no_user": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Specify user to"
            " permit</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Specified entity is"
            " not a user</b>"
        ),
        "li": '⦿ <b><a href="tg://user?id={}">{}</a></b>',
        "warning": (
            "⚠️ <b>Please, confirm, that you want to add <a"
            ' href="tg://user?id={}">{}</a> to group </b><code>{}</code><b>!\nThis'
            " action may reveal personal info and grant full or partial access to"
            " userbot to this user</b>"
        ),
        "cancel": "🚫 Cancel",
        "confirm": "👑 Confirm",
        "enable_nonick_btn": "🔰 Enable",
        "self": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>You can't"
            " promote/demote yourself!</b>"
        ),
        "suggest_nonick": "🔰 <i>Do you want to enable NoNick for this user?</i>",
        "user_nn": '🔰 <b>NoNick for <a href="tg://user?id={}">{}</a> enabled</b>',
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>You need to specify"
            " the type of target as first argument (</b><code>user</code><b> or"
            " </b><code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>You didn't specify"
            " the target of security rule</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>You didn't specify"
            " the rule (module or command)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Please, confirm that you want to give {} <a href='{}'>{}</a> a"
            " permission to use {} </b><code>{}</code><b> {}?</b>"
        ),
        "rule_added": (
            "🔐 <b>You gave {} <a href='{}'>{}</a> a"
            " permission to use {} </b><code>{}</code><b> {}</b>"
        ),
        "confirm_btn": "👑 Confirm",
        "cancel_btn": "🚫 Cancel",
        "multiple_rules": (
            "🔐 <b>Unable to unambiguously determine the security rule. Please, choose"
            " the one you meant:</b>\n\n{}"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Targeted security"
            " rules:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No targeted security"
            " rules</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>This user is owner"
            " and can't be promoted by targeted security</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Targeted security"
            ' rules for <a href="{}">{}</a> removed</b>'
        ),
        **service_strings,
    }

    strings_ru = {
        "no_command": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Команда"
            " </b><code>{}</code><b> не найдена!</b>"
        ),
        "permissions": (
            "🔐 <b>Здесь можно настроить разрешения для команды </b><code>{}{}</code>"
        ),
        "close_menu": "🙈 Закрыть это меню",
        "global": (
            "🔐 <b>Здесь можно настроить глобальную исключающую маску. Если тумблер"
            " выключен здесь, он выключен для всех команд</b>"
        ),
        "owner": "😎 Владелец",
        "sudo": "🧐 Sudo",
        "support": "🤓 Помощник",
        "group_owner": "🧛‍♂️ Влад. группы",
        "group_admin_add_admins": "🧑‍⚖️ Админ (добавлять участников)",
        "group_admin_change_info": "🧑‍⚖️ Админ (изменять инфо)",
        "group_admin_ban_users": "🧑‍⚖️ Админ (банить)",
        "group_admin_delete_messages": "🧑‍⚖️ Админ (удалять сообщения)",
        "group_admin_pin_messages": "🧑‍⚖️ Админ (закреплять)",
        "group_admin_invite_users": "🧑‍⚖️ Админ (приглашать)",
        "group_admin": "🧑‍⚖️ Админ (любой)",
        "group_member": "👥 В группе",
        "pm": "🤙 В лс",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Пользователи группы"
            " </b><code>owner</code><b>:</b>\n\n{}"
        ),
        "sudo_list": (
            "<emoji document_id=5418133868475587618>🧐</emoji> <b>Пользователи группы"
            " </b><code>sudo</code><b>:</b>\n\n{}"
        ),
        "support_list": (
            "<emoji document_id=5415729507128580146>🤓</emoji> <b>Пользователи группы"
            " </b><code>support</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Нет пользователей в"
            " группе </b><code>owner</code>"
        ),
        "no_sudo": (
            "<emoji document_id=5418133868475587618>🧐</emoji> <b>Нет пользователей в"
            " группе </b><code>sudo</code>"
        ),
        "no_support": (
            "<emoji document_id=5415729507128580146>🤓</emoji> <b>Нет пользователей в"
            " группе </b><code>support</code>"
        ),
        "no_user": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Укажи, кому выдавать"
            " права</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Указанная цель - не"
            " пользователь</b>"
        ),
        "cancel": "🚫 Отмена",
        "confirm": "👑 Подтвердить",
        "self": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Нельзя управлять"
            " своими правами!</b>"
        ),
        "warning": (
            '⚠️ <b>Ты действительно хочешь добавить <a href="tg://user?id={}">{}</a> в'
            " группу </b><code>{}</code><b>!\nЭто действие может передать частичный или"
            " полный доступ к юзерботу этому пользователю!</b>"
        ),
        "suggest_nonick": (
            "🔰 <i>Хочешь ли ты включить NoNick для этого пользователя?</i>"
        ),
        "user_nn": '🔰 <b>NoNick для <a href="tg://user?id={}">{}</a> включен</b>',
        "enable_nonick_btn": "🔰 Включить",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу </b><code>owner</code>'
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу </b><code>sudo</code>'
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу </b><code>support</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы </b><code>owner</code>'
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы </b><code>sudo</code>'
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы </b><code>support</code>'
        ),
        "_cls_doc": "Управление настройками безопасности",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Вам нужно указать"
            " тип цели первым аргументов (</b><code>user</code><b> or"
            " </b><code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Не указана цель"
            " правила безопасности</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Не указано правило"
            " безопасности (модуль или команда)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Пожалуйста, подтвердите что хотите выдать {} <a href='{}'>{}</a>"
            " право использовать {} </b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Не получилось однозначно распознать правила безопасности. Выберите"
            " то, которое имели ввиду:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Вы выдали {} <a href='{}'>{}</a> право"
            " использовать {} </b><code>{}</code><b> {}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Таргетированные"
            " правила безопасности:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Нет таргетированных"
            " правил безопасности</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Этот пользователь -"
            " владелец, его права не могут управляться таргетированной"
            " безопасностью</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Правила"
            ' таргетированной безопасности для <a href="{}">{}</a> удалены</b>'
        ),
        **service_strings_ru,
    }

    strings_de = {
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde der Gruppe </b><code>owner</code>'
            "<b> hinzugefügt</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde der Gruppe </b><code>sudo</code>'
            "<b> hinzugefügt</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde der Gruppe </b><code>support</code>'
            "<b> hinzugefügt</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde aus der Gruppe </b><code>owner</code>'
            "<b> entfernt</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde aus der Gruppe </b><code>sudo</code>'
            "<b> entfernt</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde aus der Gruppe'
            " </b><code>support</code><b> entfernt</b>"
        ),
        "_cls_doc": "Verwalten Sie die Sicherheitseinstellungen",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Erstes Argument"
            " (</b><code>user</code><b> or </b><code>chat</code><b>)"
            " fehlt</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Benutzer nicht"
            " gefunden</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Chat nicht"
            " gefunden</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Keine Regel"
            " angegeben (Modul oder Kommando)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Keine Regel"
            " angegeben (Modul oder Kommando)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Bitte bestätigen Sie, dass Sie {} <a href='{}'>{}</a>"
            " die Berechtigung erteilen möchten </b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Es war nicht möglich, die Sicherheitsregeln eindeutig zu erkennen."
            " Wählen Sie das aus, was Sie wollten:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Sie haben {} <a href='{}'>{}</a> die Berechtigung"
            " erteilt </b><code>{}</code><b> {}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Regeln für die"
            " Sicherheit:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Keine Regeln für die"
            " Sicherheit</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Dieser Benutzer ist"
            " der Besitzer, seine Rechte können nicht mit Sicherheitszielen"
            " verwaltet werden</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Die Sicherheitsregeln"
            " für <a href='{}'>{}</a> wurden entfernt</b>"
        ),
        **service_strings_de,
    }

    strings_tr = {
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı </b><code>sahip</code>'
            "<b> grubuna eklendi</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı </b><code>yönetici</code>'
            "<b> grubuna eklendi</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı </b><code>destek</code>'
            "<b> grubuna eklendi</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı </b><code>sahip</code>'
            "<b> grubundan çıkartıldı</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı </b><code>yönetici</code>'
            "<b> grubundan çıkartıldı</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı </b><code>destek</code>'
            "<b> grubundan çıkartıldı</b>"
        ),
        "_cls_doc": "Güvenlik ayarlarını yönet",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>İlk argüman"
            " (</b><code>user</code><b> veya </b><code>chat</code><b>) bulunamadı</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Kullanıcı"
            " bulunamadı</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Sohbet bulunamadı</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Hiçbir kural"
            " belirtilmedi (modül veya komut)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Hiçbir kural"
            " belirtilmedi (modül veya komut)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Lütfen {} <a href='{}'>{}</a> için izin vermek istediğinize emin olun"
            " </b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": "🔐 <b>Güvenlik kurallarını yönetin</b>\n\n{}",
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Hiçbir güvenlik kuralı"
            " yok</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Bu kullanıcı sahiptir,"
            " izinleri güvenlik hedefleriyle yönetilemez</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b><a href='{}'>{}</a>"
            " için güvenlik kuralları kaldırıldı</b>"
        ),
        **service_strings_tr,
    }

    strings_uz = {
        "global": (
            "🔐 <b>Bu erda siz global chegaralash maskasini ta'hrirlashingiz mumkin."
            " Agar bu erda ruxsat berilmasa, qolgan joylarda ham ruxsat berilmaydi!</b>"
        ),
        "warning": (
            '⚠️ <b>Iltimos, ta\'sdiqlang, siz <a href="tg://user?id={}">{}</a>'
            " </b><code>{}</code><b> ega gruppasiga qushmoqchimisiz? Bu harakat shaxsiy"
            " ma'lumotni oshkor va foydalanuvchiga userbot ishlatishiga toʻliq yoki"
            " qisman ruxsat berishi mumkin</b>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>owner</code>'
            "<b> qo'shildi</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> qo'shildi</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>support</code>'
            "<b> qo'shildi</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>owner</code>'
            "<b> o'chirildi</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> o'chirildi</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>support</code>'
            "<b> o'chirildi</b>"
        ),
        "_cls_doc": "Xavfsizlik sozlamalarini boshqarish",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Ilk argument"
            " (</b><code>user</code><b> yoki </b><code>chat</code><b>) topilmadi</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Foydalanuvchi"
            " topilmadi</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Guruh topilmadi</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Hech qanday qoida"
            " belgilanmadi (modul yoki buyruq)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Hech qanday qoida"
            " belgilanmadi (modul yoki buyruq)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Iltimos {} <a href='{}'>{}</a> uchun ruxsat berishni"
            " istaysizmi</b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": "🔐 <b>Xavfsizlik qoidalarni boshqarish</b>\n\n{}",
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Hech qanday xavfsizlik"
            " qoidasi yo'q</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>Ushbu foydalanuvchi"
            " egasi, ruxsatlar xavfsizlik maqsadlari bilan boshqarilishi mumkin"
            " emas</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b><a href='{}'>{}</a>"
            " uchun xavfsizlik qoidalari o'chirildi</b>"
        ),
        **service_strings_uz,
    }

    strings_ja = {
        "global": (
            "🔐 <b>このグループでは、グローバルなセキュリティ設定を変更できます。このグループで許可されない場合、他のグループでも許可されません！</b>"
        ),
        "warning": (
            '⚠️ <b>本当に、<a href="tg://user?id={}">{}</a> '
            " </b><code>{}</code><b>グループに追加しますか？ この操作は、個人情報を"
            "漏洩させ、ユーザーボットを完全または部分的に許可する可能性があります</b>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>owner</code>'
            "<b> 追加されました</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> 追加されました</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>support</code>'
            "<b> 追加されました</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>owner</code>'
            "<b> 削除されました</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> 削除されました</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>support</code>'
            "<b> 削除されました</b>"
        ),
        "_cls_doc": "セキュリティ設定を管理する",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>最初の引数"
            " (</b><code>user</code><b> または </b><code>chat</code><b>) が見つかりません</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>ユーザーが見つかりません</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>グループが見つかりません</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>どのルールも指定されていません"
            " (モジュールまたはコマンド)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>どのルールも指定されていません"
            " (モジュールまたはコマンド)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>本当に {} <a href='{}'>{}</a>  </b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": "🔐 <b>セキュリティルールを管理する</b>\n\n{}",
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>セキュリティルールがありません</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>このユーザーは"
            "所有者であり、セキュリティ目的で管理できません</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>安全規則"
            " for <a href='{}'>{}</a> は削除されました</b>"
        ),
        **service_strings_ja,
    }

    strings_kr = {
        "global": (
            "🔐 <b>이 그룹에서는 전역 보안 설정을 변경할 수 있습니다."
            "이 그룹에서 허용되지 않은 경우 다른 그룹에서도 허용되지 않습니다!</b>"
        ),
        "warning": (
            '⚠️ <b>정말로 <a href="tg://user?id={}">{}</a> '
            " </b><code>{}</code><b> 그룹에 추가 하시겠습니까? 이 작업은 개인 정보를"
            "유출시키고 사용자 봇을 완전히 또는 부분적으로 허용할 수 있습니다</b>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>owner</code>'
            "<b> 추가되었습니다</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> 추가되었습니다</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>support</code>'
            "<b> 추가되었습니다</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>owner</code>'
            "<b> 제거되었습니다</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> 제거되었습니다</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>support</code>'
            "<b> 제거되었습니다</b>"
        ),
        "_cls_doc": "보안 설정을 관리합니다",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>첫 번째 인수"
            " (</b><code>user</code><b> 또는 </b><code>chat</code><b>)를 찾을 수 없습니다</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>사용자를 찾을 수 없습니다</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>그룹을 찾을 수 없습니다</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>어떤 규칙도 지정되지 않았습니다 (모듈"
            " 또는 명령)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>어떤 규칙도 지정되지 않았습니다 (모듈"
            " 또는 명령)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>정말로 {} <a href='{}'>{}</a>  </b><code>{}</code><b> {}</b>"
        ),
        "multiple_rules": "🔐 <b>보안 규칙을 관리합니다</b>\n\n{}",
        "no_rules": "<emoji document_id=6053166094816905153>🚫</emoji> <b>보안 규칙 없음</b>",
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>이 사용자는"
            "소유자이며 보안 목적으로 관리할 수 없습니다.</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>안전 규칙"
            "for <a href='{}'>{}</a>이(가) 삭제되었습니다</b>"
        ),
        **service_strings_kr,
    }

    strings_ar = {
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>مالك</code>'
            "<b> تمت إضافته</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>سودو</code>'
            "<b> تمت إضافته</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>مساعد</code>'
            "<b> تمت إضافته</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>مالك</code>'
            "<b> تمت إزالته</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>سودو</code>'
            "<b> تمت إزالته</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>مساعد</code>'
            "<b> تمت إزالته</b>"
        ),
        "_cls_doc": "إدارة إعدادات الأمان",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لم يتم"
            " العثور على الوسيط الأول (</b><code>user</code><b> أو </b>"
            "<code>chat</code><b>)</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لم يتم"
            " العثور على المستخدم</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لم يتم"
            " العثور على الدردشة</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لم يتم"
            " تحديد أي قاعدة (الوحدة أو الأمر)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لم يتم"
            " تحديد أي قاعدة (الوحدة أو الأمر)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>هل أنت متأكد من أنك تريد {} <a href='{}'>{}</a>  </b>"
            "<code>{}</code><b> {}</b>"
        ),
        "multiple_rules": "🔐 <b>إدارة قواعد الأمان</b>\n\n{}",
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لا توجد قواعد أمان</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>لا يمكن"
            " إدارة هذا المستخدم لأنه مالك.</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>تم"
            " إزالة قواعد الأمان لـ <a href='{}'>{}</a></b>"
        ),
        **service_strings_ar,
    }

    strings_es = {
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>propietario</code>'
            "<b> añadido</b>"
        ),
        "sudo_added": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> añadido</b>"
        ),
        "support_added": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>soporte</code>'
            "<b> añadido</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>propietario</code>'
            "<b> eliminado</b>"
        ),
        "sudo_removed": (
            '<emoji document_id="5418133868475587618">🧐</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>sudo</code>'
            "<b> eliminado</b>"
        ),
        "support_removed": (
            '<emoji document_id="5415729507128580146">🤓</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> </b><code>soporte</code>'
            "<b> eliminado</b>"
        ),
        "_cls_doc": "Administra los ajustes de seguridad",
        "what": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No se"
            " encontró el primer medio (</b><code>usuario</code><b> o </b>"
            "<code>chat</code><b>)</b>"
        ),
        "no_user": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No se"
            " encontró el usuario</b>"
        ),
        "no_chat": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No se"
            " encontró el chat</b>"
        ),
        "what_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No se"
            " especificó ninguna regla (módulo o comando)</b>"
        ),
        "no_rule": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No se"
            " especificó ninguna regla (módulo o comando)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>¿Estás seguro de que quieres {} <a href='{}'>{}</a>  </b>"
            "<code>{}</code><b> {}</b>"
        ),
        "multiple_rules": "🔐 <b>Administración de reglas de seguridad</b>\n\n{}",
        "no_rules": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No hay"
            " reglas de seguridad</b>"
        ),
        "owner_target": (
            "<emoji document_id=6053166094816905153>🚫</emoji> <b>No se"
            " puede administrar este usuario porque es el propietario.</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Reglas"
            " de seguridad eliminadas para <a href='{}'>{}</a></b>"
        ),
        **service_strings_es,
    }

    async def inline__switch_perm(
        self,
        call: InlineCall,
        command: str,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        cmd = (
            self.allmodules.inline_handlers[command]
            if is_inline
            else self.allmodules.commands[command]
        )

        mask = self._db.get(security.__name__, "masks", {}).get(
            f"{cmd.__module__}.{cmd.__name__}",
            getattr(cmd, "security", security.DEFAULT_PERMISSIONS),
        )

        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        masks = self._db.get(security.__name__, "masks", {})
        masks[f"{cmd.__module__}.{cmd.__name__}"] = mask
        self._db.set(security.__name__, "masks", masks)

        if (
            not self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS)
            & bit
            and level
        ):
            await call.answer(
                "Security value set but not applied. Consider enabling this value in"
                f" .{'inlinesec' if is_inline else 'security'}",
                show_alert=True,
            )
        else:
            await call.answer("Security value set!")

        await call.edit(
            self.strings("permissions").format(
                f"@{self.inline.bot_username} " if is_inline else self.get_prefix(),
                command,
            ),
            reply_markup=self._build_markup(cmd, is_inline),
        )

    async def inline__switch_perm_bm(
        self,
        call: InlineCall,
        group: str,
        level: bool,
        is_inline: bool,
    ):
        mask = self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS)
        bit = security.BITMAP[group.upper()]

        if level:
            mask |= bit
        else:
            mask &= ~bit

        self._db.set(security.__name__, "bounding_mask", mask)

        await call.answer("Bounding mask value set!")
        await call.edit(
            self.strings("global"),
            reply_markup=self._build_markup_global(is_inline),
        )

    def _build_markup(
        self,
        command: callable,
        is_inline: bool = False,
    ) -> typing.List[typing.List[dict]]:
        perms = self._get_current_perms(command, is_inline)
        return (
            utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                        "callback": self.inline__switch_perm,
                        "args": (
                            command.__name__.rsplit("_inline_handler", maxsplit=1)[0],
                            group,
                            not level,
                            is_inline,
                        ),
                    }
                    for group, level in perms.items()
                ],
                2,
            )
            + [[{"text": self.strings("close_menu"), "action": "close"}]]
            if is_inline
            else utils.chunks(
                [
                    {
                        "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                        "callback": self.inline__switch_perm,
                        "args": (
                            command.__name__.rsplit("cmd", maxsplit=1)[0],
                            group,
                            not level,
                            is_inline,
                        ),
                    }
                    for group, level in perms.items()
                ],
                2,
            )
            + [
                [
                    {
                        "text": self.strings("close_menu"),
                        "action": "close",
                    }
                ]
            ]
        )

    def _build_markup_global(
        self, is_inline: bool = False
    ) -> typing.List[typing.List[dict]]:
        perms = self._get_current_bm(is_inline)
        return utils.chunks(
            [
                {
                    "text": f"{'✅' if level else '🚫'} {self.strings[group]}",
                    "callback": self.inline__switch_perm_bm,
                    "args": (group, not level, is_inline),
                }
                for group, level in perms.items()
            ],
            2,
        ) + [[{"text": self.strings("close_menu"), "action": "close"}]]

    def _get_current_bm(self, is_inline: bool = False) -> dict:
        return self._perms_map(
            self._db.get(security.__name__, "bounding_mask", DEFAULT_PERMISSIONS),
            is_inline,
        )

    @staticmethod
    def _perms_map(perms: int, is_inline: bool) -> dict:
        return (
            {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
                "everyone": bool(perms & EVERYONE),
            }
            if is_inline
            else {
                "sudo": bool(perms & SUDO),
                "support": bool(perms & SUPPORT),
                "group_owner": bool(perms & GROUP_OWNER),
                "group_admin_add_admins": bool(perms & GROUP_ADMIN_ADD_ADMINS),
                "group_admin_change_info": bool(perms & GROUP_ADMIN_CHANGE_INFO),
                "group_admin_ban_users": bool(perms & GROUP_ADMIN_BAN_USERS),
                "group_admin_delete_messages": bool(
                    perms & GROUP_ADMIN_DELETE_MESSAGES
                ),
                "group_admin_pin_messages": bool(perms & GROUP_ADMIN_PIN_MESSAGES),
                "group_admin_invite_users": bool(perms & GROUP_ADMIN_INVITE_USERS),
                "group_admin": bool(perms & GROUP_ADMIN),
                "group_member": bool(perms & GROUP_MEMBER),
                "pm": bool(perms & PM),
                "everyone": bool(perms & EVERYONE),
            }
        )

    def _get_current_perms(
        self,
        command: callable,
        is_inline: bool = False,
    ) -> dict:
        config = self._db.get(security.__name__, "masks", {}).get(
            f"{command.__module__}.{command.__name__}",
            getattr(command, "security", self._client.dispatcher.security.default),
        )

        return self._perms_map(config, is_inline)

    @loader.owner
    @loader.command(
        ru_doc="[команда] - Настроить разрешения для команды",
        de_doc="[command] - Einstellungen für Befehle ändern",
        tr_doc="[command] - Komut için izinleri ayarla",
        uz_doc="[command] - Buyruq uchun ruxsatlarini sozlash",
        ja_doc="[command] - コマンドの権限を設定します",
        kr_doc="[command] - 명령어 권한 설정",
        ar_doc="[command] - تعيين الأذونات للأوامر",
        es_doc="[command] - Configurar permisos para comandos",
    )
    async def security(self, message: Message):
        """[command] - Configure command's security settings"""
        args = utils.get_args_raw(message).lower().strip()
        if args and args not in self.allmodules.commands:
            await utils.answer(message, self.strings("no_command").format(args))
            return

        if not args:
            await self.inline.form(
                self.strings("global"),
                reply_markup=self._build_markup_global(),
                message=message,
                ttl=5 * 60,
            )
            return

        cmd = self.allmodules.commands[args]

        await self.inline.form(
            self.strings("permissions").format(self.get_prefix(), args),
            reply_markup=self._build_markup(cmd),
            message=message,
            ttl=5 * 60,
        )

    @loader.owner
    @loader.command(
        ru_doc="[команда] - Настроить разрешения для инлайн команды",
        de_doc="[command] - Einstellungen für Inline-Befehle ändern",
        tr_doc="[command] - Inline komut için izinleri ayarla",
        uz_doc="[command] - Inline buyruq uchun ruxsatlarini sozlash",
        ja_doc="[command] - インラインコマンドの権限を設定します",
        kr_doc="[command] - 인라인 명령어 권한 설정",
        ar_doc="[command] - تعيين الأذونات للأوامر الخطية",
        es_doc="[command] - Configurar permisos para comandos inline",
    )
    async def inlinesec(self, message: Message):
        """[command] - Configure inline command's security settings"""
        args = utils.get_args_raw(message).lower().strip()
        if not args:
            await self.inline.form(
                self.strings("global"),
                reply_markup=self._build_markup_global(True),
                message=message,
                ttl=5 * 60,
            )
            return

        if args not in self.allmodules.inline_handlers:
            await utils.answer(message, self.strings("no_command").format(args))
            return

        i_handler = self.allmodules.inline_handlers[args]
        await self.inline.form(
            self.strings("permissions").format(f"@{self.inline.bot_username} ", args),
            reply_markup=self._build_markup(i_handler, True),
            message=message,
            ttl=5 * 60,
        )

    async def _resolve_user(self, message: Message):
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)

        if not args and not reply:
            await utils.answer(message, self.strings("no_user"))
            return

        user = None

        if args:
            try:
                if str(args).isdigit():
                    args = int(args)

                user = await self._client.get_entity(args)
            except Exception:
                pass

        if user is None:
            user = await self._client.get_entity(reply.sender_id)

        if not isinstance(user, (User, PeerUser)):
            await utils.answer(message, self.strings("not_a_user"))
            return

        if user.id == self.tg_id:
            await utils.answer(message, self.strings("self"))
            return

        return user

    async def _add_to_group(
        self,
        message: typing.Union[Message, InlineCall],
        group: str,
        confirmed: bool = False,
        user: int = None,
    ):
        if user is None:
            user = await self._resolve_user(message)
            if not user:
                return

        if isinstance(user, int):
            user = await self._client.get_entity(user)

        if not confirmed:
            await self.inline.form(
                self.strings("warning").format(
                    user.id,
                    utils.escape_html(get_display_name(user)),
                    group,
                ),
                message=message,
                ttl=10 * 60,
                reply_markup=[
                    {
                        "text": self.strings("cancel"),
                        "action": "close",
                    },
                    {
                        "text": self.strings("confirm"),
                        "callback": self._add_to_group,
                        "args": (group, True, user.id),
                    },
                ],
            )
            return

        if user.id not in getattr(self._client.dispatcher.security, group):
            getattr(self._client.dispatcher.security, group).append(user.id)

        m = (
            self.strings(f"{group}_added").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            )
            + "\n\n"
            + self.strings("suggest_nonick")
        )

        await utils.answer(message, m)
        await message.edit(
            m,
            reply_markup=[
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
                {
                    "text": self.strings("enable_nonick_btn"),
                    "callback": self._enable_nonick,
                    "args": (user,),
                },
            ],
        )

    async def _enable_nonick(self, call: InlineCall, user: User):
        self._db.set(
            main.__name__,
            "nonickusers",
            list(set(self._db.get(main.__name__, "nonickusers", []) + [user.id])),
        )

        await call.edit(
            self.strings("user_nn").format(
                user.id,
                utils.escape_html(get_display_name(user)),
            )
        )

        await call.unload()

    async def _remove_from_group(self, message: Message, group: str):
        user = await self._resolve_user(message)
        if not user:
            return

        if user.id in getattr(self._client.dispatcher.security, group):
            getattr(self._client.dispatcher.security, group).remove(user.id)

        m = self.strings(f"{group}_removed").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        await utils.answer(message, m)

    async def _list_group(self, message: Message, group: str):
        _resolved_users = []
        for user in getattr(self._client.dispatcher.security, group) + (
            [self.tg_id] if group == "owner" else []
        ):
            try:
                _resolved_users += [await self._client.get_entity(user)]
            except Exception:
                pass

        if _resolved_users:
            await utils.answer(
                message,
                self.strings(f"{group}_list").format(
                    "\n".join(
                        [
                            self.strings("li").format(
                                i.id, utils.escape_html(get_display_name(i))
                            )
                            for i in _resolved_users
                        ]
                    )
                ),
            )
        else:
            await utils.answer(message, self.strings(f"no_{group}"))

    @loader.command(
        ru_doc="<пользователь> - Добавить пользователя в группу `sudo`",
        de_doc="<Benutzer> - Füge Benutzer zur `sudo`-Gruppe hinzu",
        tr_doc="<kullanıcı> - Kullanıcıyı `sudo` grubuna ekle",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `sudo` guruhiga qo'shish",
        ja_doc="<ユーザー> - ユーザーを `sudo` グループに追加",
        kr_doc="<사용자> - 사용자를 `sudo` 그룹에 추가",
        ar_doc="<مستخدم> - إضافة مستخدم إلى مجموعة `sudo`",
        es_doc="<usuario> - Agregar usuario al grupo `sudo`",
    )
    async def sudoadd(self, message: Message):
        """<user> - Add user to `sudo`"""
        await self._add_to_group(message, "sudo")

    @loader.command(
        ru_doc="<пользователь> - Добавить пользователя в группу `owner`",
        de_doc="<Benutzer> - Füge Benutzer zur `owner`-Gruppe hinzu",
        tr_doc="<kullanıcı> - Kullanıcıyı `owner` grubuna ekle",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `owner` guruhiga qo'shish",
        ja_doc="<ユーザー> - ユーザーを `owner` グループに追加",
        kr_doc="<사용자> - 사용자를 `owner` 그룹에 추가",
        ar_doc="<مستخدم> - إضافة مستخدم إلى مجموعة `owner`",
        es_doc="<usuario> - Agregar usuario al grupo `owner`",
    )
    async def owneradd(self, message: Message):
        """<user> - Add user to `owner`"""
        await self._add_to_group(message, "owner")

    @loader.command(
        ru_doc="<пользователь> - Добавить пользователя в группу `support`",
        de_doc="<Benutzer> - Füge Benutzer zur `support`-Gruppe hinzu",
        tr_doc="<kullanıcı> - Kullanıcıyı `support` grubuna ekle",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `support` guruhiga qo'shish",
        ja_doc="<ユーザー> - ユーザーを `support` グループに追加",
        kr_doc="<사용자> - 사용자를 `support` 그룹에 추가",
        ar_doc="<مستخدم> - إضافة مستخدم إلى مجموعة `support`",
        es_doc="<usuario> - Agregar usuario al grupo `support`",
    )
    async def supportadd(self, message: Message):
        """<user> - Add user to `support`"""
        await self._add_to_group(message, "support")

    @loader.command(
        ru_doc="<пользователь> - Удалить пользователя из группы `sudo`",
        de_doc="<Benutzer> - Entferne Benutzer aus der `sudo`-Gruppe",
        tr_doc="<kullanıcı> - Kullanıcıyı `sudo` grubundan kaldır",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `sudo` guruhidan olib tashlash",
        ja_doc="<ユーザー> - ユーザーを `sudo` グループから削除",
        kr_doc="<사용자> - 사용자를 `sudo` 그룹에서 제거",
        ar_doc="<مستخدم> - إزالة مستخدم من مجموعة `sudo`",
        es_doc="<usuario> - Eliminar usuario del grupo `sudo`",
    )
    async def sudorm(self, message: Message):
        """<user> - Remove user from `sudo`"""
        await self._remove_from_group(message, "sudo")

    @loader.command(
        ru_doc="<пользователь> - Удалить пользователя из группы `owner`",
        de_doc="<Benutzer> - Entferne Benutzer aus der `owner`-Gruppe",
        tr_doc="<kullanıcı> - Kullanıcıyı `owner` grubundan kaldır",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `owner` guruhidan olib tashlash",
        ja_doc="<ユーザー> - ユーザーを `owner` グループから削除",
        kr_doc="<사용자> - 사용자를 `owner` 그룹에서 제거",
        ar_doc="<مستخدم> - إزالة مستخدم من مجموعة `owner`",
        es_doc="<usuario> - Eliminar usuario del grupo `owner`",
    )
    async def ownerrm(self, message: Message):
        """<user> - Remove user from `owner`"""
        await self._remove_from_group(message, "owner")

    @loader.command(
        ru_doc="<пользователь> - Удалить пользователя из группы `support`",
        de_doc="<Benutzer> - Entferne Benutzer aus der `support`-Gruppe",
        tr_doc="<kullanıcı> - Kullanıcıyı `support` grubundan kaldır",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `support` guruhidan olib tashlash",
        ja_doc="<ユーザー> - ユーザーを `support` グループから削除",
        kr_doc="<사용자> - 사용자를 `support` 그룹에서 제거",
        ar_doc="<مستخدم> - إزالة مستخدم من مجموعة `support`",
        es_doc="<usuario> - Eliminar usuario del grupo `support`",
    )
    async def supportrm(self, message: Message):
        """<user> - Remove user from `support`"""
        await self._remove_from_group(message, "support")

    @loader.command(
        ru_doc="Показать список пользователей в группе `sudo`",
        de_doc="Zeige Liste der Benutzer in der `sudo`-Gruppe",
        tr_doc="`sudo` grubundaki kullanıcıların listesini göster",
        uz_doc="`sudo` guruhidagi foydalanuvchilar ro'yxatini ko'rsatish",
        ja_doc="`sudo` グループのユーザー一覧を表示",
        kr_doc="`sudo` 그룹의 사용자 목록 표시",
        ar_doc="عرض قائمة المستخدمين في مجموعة `sudo`",
        es_doc="Mostrar lista de usuarios en el grupo `sudo`",
    )
    async def sudolist(self, message: Message):
        """List users in `sudo`"""
        await self._list_group(message, "sudo")

    @loader.command(
        ru_doc="Показать список пользователей в группе `owner`",
        de_doc="Zeige Liste der Benutzer in der `owner`-Gruppe",
        tr_doc="`owner` grubundaki kullanıcıların listesini göster",
        uz_doc="`owner` guruhidagi foydalanuvchilar ro'yxatini ko'rsatish",
        ja_doc="`owner` グループのユーザー一覧を表示",
        kr_doc="`owner` 그룹의 사용자 목록 표시",
        ar_doc="عرض قائمة المستخدمين في مجموعة `owner`",
        es_doc="Mostrar lista de usuarios en el grupo `owner`",
    )
    async def ownerlist(self, message: Message):
        """List users in `owner`"""
        await self._list_group(message, "owner")

    @loader.command(
        ru_doc="Показать список пользователей в группе `support`",
        de_doc="Zeige Liste der Benutzer in der `support`-Gruppe",
        tr_doc="`support` grubundaki kullanıcıların listesini göster",
        uz_doc="`support` guruhidagi foydalanuvchilar ro'yxatini ko'rsatish",
        ja_doc="`support` グループのユーザー一覧を表示",
        kr_doc="`support` 그룹의 사용자 목록 표시",
        ar_doc="عرض قائمة المستخدمين في مجموعة `support`",
        es_doc="Mostrar lista de usuarios en el grupo `support`",
    )
    async def supportlist(self, message: Message):
        """List users in `support`"""
        await self._list_group(message, "support")

    def _lookup(self, needle: str) -> str:
        return (
            []
            if needle.lower().startswith(self.get_prefix())
            else (
                [f"module/{self.lookup(needle).__class__.__name__}"]
                if self.lookup(needle)
                else []
            )
        ) + (
            [f"command/{needle.lower().strip(self.get_prefix())}"]
            if needle.lower().strip(self.get_prefix()) in self.allmodules.commands
            else []
        )

    @staticmethod
    def _extract_time(args: list) -> int:
        suffixes = {
            "d": 24 * 60 * 60,
            "h": 60 * 60,
            "m": 60,
            "s": 1,
        }
        for suffix, quantifier in suffixes.items():
            duration = next(
                (
                    int(arg.rsplit(suffix, maxsplit=1)[0])
                    for arg in args
                    if arg.endswith(suffix)
                    and arg.rsplit(suffix, maxsplit=1)[0].isdigit()
                ),
                None,
            )
            if duration is not None:
                return duration * quantifier

        return 0

    def _convert_time(self, duration: int) -> str:
        return (
            self.strings("forever")
            if not duration or duration < 0
            else (
                (
                    f"{duration // (24 * 60 * 60)} "
                    + self.strings(
                        f"day{'s' if duration // (24 * 60 * 60) > 1 else ''}"
                    )
                )
                if duration >= 24 * 60 * 60
                else (
                    (
                        f"{duration // (60 * 60)} "
                        + self.strings(
                            f"hour{'s' if duration // (60 * 60) > 1 else ''}"
                        )
                    )
                    if duration >= 60 * 60
                    else (
                        (
                            f"{duration // 60} "
                            + self.strings(f"minute{'s' if duration // 60 > 1 else ''}")
                        )
                        if duration >= 60
                        else (
                            f"{duration} "
                            + self.strings(f"second{'s' if duration > 1 else ''}")
                        )
                    )
                )
            )
        )

    async def _add_rule(
        self,
        call: InlineCall,
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
        self._client.dispatcher.security.add_rule(
            target_type,
            target,
            rule,
            duration,
        )

        await call.edit(
            self.strings("rule_added").format(
                self.strings(target_type),
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                self.strings(rule.split("/", maxsplit=1)[0]),
                rule.split("/", maxsplit=1)[1],
                (self.strings("for") + " " + self._convert_time(duration))
                if duration
                else self.strings("forever"),
            )
        )

    async def _confirm(
        self,
        obj: typing.Union[Message, InlineMessage],
        target_type: str,
        target: EntityLike,
        rule: str,
        duration: int,
    ):
        await utils.answer(
            obj,
            self.strings("confirm_rule").format(
                self.strings(target_type),
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                self.strings(rule.split("/", maxsplit=1)[0]),
                rule.split("/", maxsplit=1)[1],
                (self.strings("for") + " " + self._convert_time(duration))
                if duration
                else self.strings("forever"),
            ),
            reply_markup=[
                {
                    "text": self.strings("confirm_btn"),
                    "callback": self._add_rule,
                    "args": (target_type, target, rule, duration),
                },
                {"text": self.strings("cancel_btn"), "action": "close"},
            ],
        )

    async def _tsec_chat(self, message: Message, args: list):
        if len(args) == 1 and message.is_private:
            await utils.answer(message, self.strings("no_target"))
            return

        if len(args) >= 2:
            try:
                if not args[1].isdigit() and not args[1].startswith("@"):
                    raise ValueError

                target = await self._client.get_entity(
                    int(args[1]) if args[1].isdigit() else args[1]
                )
            except (ValueError, TypeError):
                if not message.is_private:
                    target = await self._client.get_entity(message.peer_id)
                else:
                    await utils.answer(message, self.strings("no_target"))
                    return

        duration = self._extract_time(args)

        possible_rules = utils.array_sum([self._lookup(arg) for arg in args])
        if not possible_rules:
            await utils.answer(message, self.strings("no_rule"))
            return

        if len(possible_rules) > 1:

            def case(text: str) -> str:
                return text.upper()[0] + text[1:]

            await self.inline.form(
                message=message,
                text=self.strings("multiple_rules").format(
                    "\n".join(
                        "🛡 <b>{} </b><code>{}</code>".format(
                            case(self.strings(rule.split("/")[0])),
                            rule.split("/", maxsplit=1)[1],
                        )
                        for rule in possible_rules
                    )
                ),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": "🛡 {} {}".format(
                                case(self.strings(rule.split("/")[0])),
                                rule.split("/", maxsplit=1)[1],
                            ),
                            "callback": self._confirm,
                            "args": ("chat", target, rule, duration),
                        }
                        for rule in possible_rules
                    ],
                    3,
                ),
            )
            return

        await self._confirm(message, "chat", target, possible_rules[0], duration)

    async def _tsec_user(self, message: Message, args: list):
        if len(args) == 1 and not message.is_private and not message.is_reply:
            await utils.answer(message, self.strings("no_target"))
            return

        if len(args) >= 2:
            try:
                if not args[1].isdigit() and not args[1].startswith("@"):
                    raise ValueError

                target = await self._client.get_entity(
                    int(args[1]) if args[1].isdigit() else args[1]
                )
            except (ValueError, TypeError):
                if message.is_private:
                    target = await self._client.get_entity(message.peer_id)
                elif message.is_reply:
                    target = await self._client.get_entity(
                        (await message.get_reply_message()).sender_id
                    )
                else:
                    await utils.answer(message, self.strings("no_target"))
                    return

        if target.id in self._client.dispatcher.security.owner:
            await utils.answer(message, self.strings("owner_target"))
            return

        duration = self._extract_time(args)

        possible_rules = utils.array_sum([self._lookup(arg) for arg in args])
        if not possible_rules:
            await utils.answer(message, self.strings("no_rule"))
            return

        if len(possible_rules) > 1:

            def case(text: str) -> str:
                return text.upper()[0] + text[1:]

            await self.inline.form(
                message=message,
                text=self.strings("multiple_rules").format(
                    "\n".join(
                        "🛡 <b>{} </b><code>{}</code>".format(
                            case(self.strings(rule.split("/")[0])),
                            rule.split("/", maxsplit=1)[1],
                        )
                        for rule in possible_rules
                    )
                ),
                reply_markup=utils.chunks(
                    [
                        {
                            "text": "🛡 {} {}".format(
                                case(self.strings(rule.split("/")[0])),
                                rule.split("/", maxsplit=1)[1],
                            ),
                            "callback": self._confirm,
                            "args": ("user", target, rule, duration),
                        }
                        for rule in possible_rules
                    ],
                    3,
                ),
            )
            return

        await self._confirm(message, "user", target, possible_rules[0], duration)

    @loader.command(
        ru_doc='<"user"/"chat"> - Удалить правило таргетированной безопасности',
        de_doc='<"user"/"chat"> - Entferne eine Regel für die gezielte Sicherheit',
        tr_doc='<"user"/"chat"> - Hedefli güvenlik için bir kural kaldırın',
        uz_doc='<"user"/"chat"> - Maqsadli xavfsizlik uchun bir qoidani olib tashlang',
        ja_doc='<"user"/"chat"> - 対象セキュリティのルールを削除します',
        kr_doc='<"user"/"chat"> - 대상 보안 규칙을 제거합니다',
        ar_doc='<"user"/"chat"> - إزالة قاعدة أمنية مستهدفة',
        es_doc='<"user"/"chat"> - Eliminar una regla de seguridad dirigida',
    )
    async def tsecrm(self, message: Message):
        """<"user"/"chat"> - Remove targeted security rule"""
        if (
            not self._client.dispatcher.security.tsec_chat
            and not self._client.dispatcher.security.tsec_user
        ):
            await utils.answer(message, self.strings("no_rules"))
            return

        args = utils.get_args_raw(message)
        if not args or args not in {"user", "chat"}:
            await utils.answer(message, self.strings("no_target"))
            return

        if args == "user":
            if not message.is_private and not message.is_reply:
                await utils.answer(message, self.strings("no_target"))
                return

            if message.is_private:
                target = await self._client.get_entity(message.peer_id)
            elif message.is_reply:
                target = await self._client.get_entity(
                    (await message.get_reply_message()).sender_id
                )

            if not self._client.dispatcher.security.remove_rules("user", target.id):
                await utils.answer(message, self.strings("no_rules"))
                return

            await utils.answer(
                message,
                self.strings("rules_removed").format(
                    utils.get_entity_url(target),
                    utils.escape_html(get_display_name(target)),
                ),
            )
            return

        if message.is_private:
            await utils.answer(message, self.strings("no_target"))
            return

        target = await self._client.get_entity(message.peer_id)

        if not self._client.dispatcher.security.remove_rules("chat", target.id):
            await utils.answer(message, self.strings("no_rules"))
            return

        await utils.answer(
            message,
            self.strings("rules_removed").format(
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
            ),
        )

    @loader.command(
        ru_doc=(
            '<"user"/"chat"> [цель - пользователь или чат] [правило - команда или'
            " модуль] [время] - Настроить таргетированную безопасность"
        ),
        de_doc=(
            '<"user"/"chat"> [Ziel - Benutzer oder Chat] [Regel - Befehl oder'
            " Modul] [Zeit] - Targeted-Sicherheit einstellen"
        ),
        tr_doc=(
            '<"user"/"chat"> [hedef - kullanıcı veya sohbet] [kural - komut veya'
            " modül] [zaman] - Hedefli güvenliği ayarla"
        ),
        uz_doc=(
            '<"user"/"chat"> [maqsad - foydalanuvchi yoki chat] [qoida - buyruq yoki'
            " modul] [vaqt] - Maqsadli xavfsizlikni sozlash"
        ),
        ja_doc=(
            '<"user"/"chat"> [ターゲット - ユーザーまたはチャット] [ルール - コマンドまたは'
            " モジュール] [時間] - ターゲットセキュリティを設定します"
        ),
        kr_doc='<"user"/"chat"> [대상 - 사용자 또는 채팅] [규칙 - 명령 또는 모듈] [시간] - 타겟 보안 설정',
        ar_doc=(
            '<"user"/"chat"> [الهدف - المستخدم أو الدردشة] [القاعدة - الأمر أو'
            " وحدة] [الوقت] - تعيين الأمن المستهدف"
        ),
        es_doc=(
            '<"user"/"chat"> [objetivo - usuario o chat] [regla - comando o'
            " módulo] [tiempo] - Establecer seguridad dirigida"
        ),
    )
    async def tsec(self, message: Message):
        """<"user"/"chat"> [target user or chat] [rule (command/module)] [time] - Add new targeted security rule
        """
        args = utils.get_args(message)
        if not args:
            if (
                not self._client.dispatcher.security.tsec_chat
                and not self._client.dispatcher.security.tsec_user
            ):
                await utils.answer(message, self.strings("no_rules"))
                return

            await utils.answer(
                message,
                self.strings("rules").format(
                    "\n".join(
                        [
                            "<emoji document_id=6037355667365300960>👥</emoji> <b><a"
                            " href='{}'>{}</a> {} {} {}</b> <code>{}</code>".format(
                                rule["entity_url"],
                                utils.escape_html(rule["entity_name"]),
                                self._convert_time(int(rule["expires"] - time.time())),
                                self.strings("for"),
                                self.strings(rule["rule_type"]),
                                rule["rule"],
                            )
                            for rule in self._client.dispatcher.security.tsec_chat
                        ]
                        + [
                            "<emoji document_id=6037122016849432064>👤</emoji> <b><a"
                            " href='{}'>{}</a> {} {} {}</b> <code>{}</code>".format(
                                rule["entity_url"],
                                utils.escape_html(rule["entity_name"]),
                                self._convert_time(int(rule["expires"] - time.time())),
                                self.strings("for"),
                                self.strings(rule["rule_type"]),
                                rule["rule"],
                            )
                            for rule in self._client.dispatcher.security.tsec_user
                        ]
                    )
                ),
            )
            return

        if args[0] not in {"user", "chat"}:
            await utils.answer(message, self.strings("what"))
            return

        await getattr(self, f"_tsec_{args[0]}")(message, args)
