# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import time
import typing

from hikkatl.hints import EntityLike
from hikkatl.tl.types import Message, PeerUser, User
from hikkatl.utils import get_display_name

from .. import loader, main, security, utils
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
        "inline": "inline command",
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
        "inline": "инлайн-команду",
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

    service_strings_fr = {
        "for": "pour",
        "forever": "pour toujours",
        "command": "commande",
        "module": "module",
        "inline": "commande en ligne",
        "chat": "chat",
        "user": "utilisateur",
        "day": "jour",
        "days": "jours",
        "hour": "heure",
        "hours": "heures",
        "minute": "minute",
        "minutes": "minutes",
        "second": "seconde",
        "seconds": "secondes",
    }

    service_strings_it = {
        "for": "per",
        "forever": "per sempre",
        "command": "comando",
        "module": "modulo",
        "inline": "comando inline",
        "chat": "chat",
        "user": "utente",
        "day": "giorno",
        "days": "giorni",
        "hour": "ora",
        "hours": "ore",
        "minute": "minuto",
        "minutes": "minuti",
        "second": "secondo",
        "seconds": "secondi",
    }

    service_strings_de = {
        "for": "für",
        "forever": "für immer",
        "command": "Befehl",
        "module": "Modul",
        "inline": "Inline-Befehl",
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
        "inline": "inline buyruq",
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
        "inline": "satır içi komut",
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

    service_strings_es = {
        "for": "para",
        "forever": "para siempre",
        "command": "comando",
        "module": "módulo",
        "inline": "comando en línea",
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

    service_strings_kk = {
        "for": "үшін",
        "forever": "әрқашан",
        "command": "команда",
        "module": "модуль",
        "inline": "inline команда",
        "chat": "сөйлесу",
        "user": "пайдаланушы",
        "day": "күн",
        "days": "күн",
        "hour": "сағат",
        "hours": "сағат",
        "minute": "мұнай",
        "minutes": "мұнай",
        "second": "секунд",
        "seconds": "секунд",
    }

    strings = {
        "name": "HikkaSecurity",
        "no_command": "🚫 <b>Command</b> <code>{}</code> <b>not found!</b>",
        "permissions": (
            "🔐 <b>Here you can configure permissions for</b> <code>{}{}</code>"
        ),
        "close_menu": "🙈 Close this menu",
        "global": (
            "🔐 <b>Here you can configure global bounding mask. If the permission is"
            " excluded here, it is excluded everywhere!</b>"
        ),
        "owner": "😎 Owner",
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
            "</b> <code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>There is no users in"
            " group</b> <code>owner</code>"
        ),
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> added to group</b> <code>owner</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> removed from group</b> <code>owner</code>'
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Specify user to"
            " permit</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Specified entity is"
            " not a user</b>"
        ),
        "li": (
            "<emoji document_id=4974307891025543730>▫️</emoji> <b><a"
            ' href="tg://user?id={}">{}</a></b>'
        ),
        "warning": (
            "⚠️ <b>Please, confirm, that you want to add <a"
            ' href="tg://user?id={}">{}</a> to group</b> <code>{}</code><b>!\nThis'
            " action may reveal personal info and grant full or partial access to"
            " userbot to this user</b>"
        ),
        "cancel": "🚫 Cancel",
        "confirm": "👑 Confirm",
        "enable_nonick_btn": "🔰 Enable",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>You can't"
            " promote/demote yourself!</b>"
        ),
        "suggest_nonick": "🔰 <i>Do you want to enable NoNick for this user?</i>",
        "user_nn": '🔰 <b>NoNick for <a href="tg://user?id={}">{}</a> enabled</b>',
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You need to specify"
            " the type of target as first argument (</b><code>user</code> <b>or"
            "</b> <code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You didn't specify"
            " the target of security rule</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You didn't specify"
            " the rule (module or command)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Please, confirm that you want to give {} <a href='{}'>{}</a> a"
            " permission to use {}</b> <code>{}</code> <b>{}?</b>"
        ),
        "rule_added": (
            "🔐 <b>You gave {} <a href='{}'>{}</a> a"
            " permission to use {}</b> <code>{}</code> <b>{}</b>"
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
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No targeted security"
            " rules</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>This user is owner"
            " and can't be promoted by targeted security</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Targeted security"
            ' rules for <a href="{}">{}</a> removed</b>'
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Targeted security"
            ' rule for <a href="{}">{}</a> (</b><code>{}</code><b>) removed</b>'
        ),
        "chat_inline": "⚠️ <b>You can't create an inline command rule for chats!</b>",
        **service_strings,
    }

    strings_ru = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Команда"
            "</b> <code>{}</code> <b>не найдена!</b>"
        ),
        "permissions": (
            "🔐 <b>Здесь можно настроить разрешения для команды</b> <code>{}{}</code>"
        ),
        "close_menu": "🙈 Закрыть это меню",
        "global": (
            "🔐 <b>Здесь можно настроить глобальную исключающую маску. Если тумблер"
            " выключен здесь, он выключен для всех команд</b>"
        ),
        "owner": "😎 Владелец",
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
            "</b> <code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Нет пользователей в"
            " группе</b> <code>owner</code>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Укажи, кому выдавать"
            " права</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Указанная цель - не"
            " пользователь</b>"
        ),
        "cancel": "🚫 Отмена",
        "confirm": "👑 Подтвердить",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Нельзя управлять"
            " своими правами!</b>"
        ),
        "warning": (
            '⚠️ <b>Ты действительно хочешь добавить <a href="tg://user?id={}">{}</a> в'
            " группу</b> <code>{}</code><b>!\nЭто действие может передать частичный или"
            " полный доступ к юзерботу этому пользователю!</b>"
        ),
        "suggest_nonick": (
            "🔰 <i>Хочешь ли ты включить NoNick для этого пользователя?</i>"
        ),
        "user_nn": '🔰 <b>NoNick для <a href="tg://user?id={}">{}</a> включен</b>',
        "enable_nonick_btn": "🔰 Включить",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> добавлен в группу</b> <code>owner</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> удален из группы</b> <code>owner</code>'
        ),
        "_cls_doc": "Управление настройками безопасности",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Вам нужно указать"
            " тип цели первым аргументов (</b><code>user</code> <b>or"
            "</b> <code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Не указана цель"
            " правила безопасности</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Не указано правило"
            " безопасности (модуль или команда)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Пожалуйста, подтвердите что хотите выдать {} <a href='{}'>{}</a>"
            " право использовать {}</b> <code>{}</code> <b>{}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Не получилось однозначно распознать правила безопасности. Выберите"
            " то, которое имели ввиду:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Вы выдали {} <a href='{}'>{}</a> право"
            " использовать {}</b> <code>{}</code> <b>{}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Таргетированные"
            " правила безопасности:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Нет таргетированных"
            " правил безопасности</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Этот пользователь -"
            " владелец, его права не могут управляться таргетированной"
            " безопасностью</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Правила"
            ' таргетированной безопасности для <a href="{}">{}</a> удалены</b>'
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Удалено правило"
            ' безопасности для <a href="{}">{}</a> (</b><code>{}</code><b>)</b>'
        ),
        "chat_inline": (
            "⚠️ <b>Вы не можете создать правило inline-команды для чатов!</b>"
        ),
        **service_strings_ru,
    }

    strings_fr = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>La commande</b>"
            " <code>{}</code> <b>est introuvable !</b>"
        ),
        "permissions": (
            "🔐 <b>Vous pouvez régler les autorisations pour la commande</b>"
            " <code>{}{}</code>"
        ),
        "close_menu": "🙈 Fermer ce menu",
        "global": (
            "🔐 <b>Vous pouvez régler la masque d'exclusion globale ici. Si le bouton"
            " est désactivé ici, il est désactivé pour toutes les commandes</b>"
        ),
        "owner": "😎 Propriétaire",
        "group_owner": "🧛‍♂️ Propriétaire du groupe",
        "group_admin_add_admins": "🧑‍⚖️ Admin (ajouter des membres)",
        "group_admin_change_info": "🧑‍⚖️ Admin (modifier les infos)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (bannir)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (supprimer les messages)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (épingler)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (inviter)",
        "group_admin": "🧑‍⚖️ Admin (tous)",
        "group_member": "👥 Dans un groupe",
        "pm": "🤙 Dans un message privé",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Utilisateurs du"
            " groupe</b> <code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Aucun utilisateur dans"
            " le groupe</b> <code>owner</code>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Spécifiez à qui"
            " accorder les droits</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>La cible spécifiée"
            " n'est pas un utilisateur</b>"
        ),
        "cancel": "🚫 Annuler",
        "confirm": "👑 Confirmer",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Vous ne pouvez pas"
            " gérer vos propres droits!</b>"
        ),
        "warning": (
            '⚠️ <b>Es-tu vraiment prêt à ajouter <a href="tg://user?id={}">{}</a> dans'
            " le groupe</b> <code>{}</code><b>!\nCela peut permettre à cet utilisateur"
            " d'accéder partiellement ou entièrement au bot utilisateur!</b>"
        ),
        "suggest_nonick": "🔰 <i>Voulez-vous activer NoNick pour cet utilisateur?</i>",
        "user_nn": '🔰 <b>NoNick pour <a href="tg://user?id={}">{}</a> activé</b>',
        "enable_nonick_btn": "🔰 Activer",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> ajouté au groupe</b> <code>owner</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> supprimé du groupe</b> <code>owner</code>'
        ),
        "_cls_doc": "Gérer les paramètres de sécurité",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Vous devez spécifier"
            " le type de cible en premier argument (</b><code>user</code> <b>ou"
            "</b> <code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Aucune cible"
            " spécifiée pour la règle de sécurité</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Aucune règle de"
            " sécurité n'a été spécifiée (module ou commande)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Veuillez confirmer que vous souhaitez donner {} <a href='{}'>{}</a>"
            " le droit d'utiliser {}</b> <code>{}</code> <b>{}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Impossible de reconnaître clairement les règles de sécurité. Veuillez"
            " sélectionner celle que vous vouliez:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Vous avez donné {} <a href='{}'>{}</a> le droit"
            " d'utiliser {}</b> <code>{}</code> <b>{}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Règles de sécurité"
            " ciblées:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Aucune règle de"
            " sécurité ciblée</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Cet utilisateur est"
            " le propriétaire, ses droits ne peuvent pas être gérés par la sécurité"
            " ciblée</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Les règles de sécurité"
            ' ciblées pour <a href="{}">{}</a> ont été supprimées</b>'
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Supprimé la règle de"
            ' sécurité pour <a href="{}">{}</a> (</b><code>{}</code><b>)</b>'
        ),
        "chat_inline": (
            "⚠️ <b>Vous ne pouvez pas créer de règle de commande inline pour les"
            " groupes!</b>"
        ),
        **service_strings_fr,
    }

    strings_it = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Comando non"
            " trovato</b> <code>{}</code> <b>!</b>"
        ),
        "permissions": (
            "🔐 <b>Qui puoi impostare i permessi per il comando</b> <code>{}{}</code>"
        ),
        "close_menu": "🙈 Chiudi questo menu",
        "global": (
            "🔐 <b>Qui puoi impostare la maschera di esclusione globale. Se il"
            " commutatore è spento qui, è spento per tutti i comandi</b>"
        ),
        "owner": "😎 Proprietario",
        "group_owner": "🧛‍♂️ Proprietario del gruppo",
        "group_admin_add_admins": "🧑‍⚖️ Amministratore (aggiungere membri)",
        "group_admin_change_info": "🧑‍⚖️ Amministratore (cambiare info)",
        "group_admin_ban_users": "🧑‍⚖️ Amministratore (bannare)",
        "group_admin_delete_messages": "🧑‍⚖️ Amministratore (eliminare messaggi)",
        "group_admin_pin_messages": "🧑‍⚖️ Amministratore (appuntare)",
        "group_admin_invite_users": "🧑‍⚖️ Amministratore (invitare)",
        "group_admin": "🧑‍⚖️ Amministratore (qualsiasi)",
        "group_member": "👥 Nel gruppo",
        "pm": "🤙 In pm",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Utenti del gruppo</b>"
            " <code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Nessun utente nel"
            " gruppo</b> <code>owner</code>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Specifica a chi dare i"
            " permessi</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>La destinazione"
            " specificata non è un utente</b>"
        ),
        "cancel": "🚫 Annulla",
        "confirm": "👑 Conferma",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Non puoi modificare i"
            " tuoi permessi!</b>"
        ),
        "warning": (
            '⚠️ <b>Sei sicuro di voler aggiungere <a href="tg://user?id={}">{}</a> nel'
            " gruppo</b> <code>{}</code><b>!\nQuesto potrebbe dare a questo utente"
            " accesso parziale o totale al tuo bot!</b>"
        ),
        "suggest_nonick": "🔰 <i>Vuoi abilitare NoNick per questo utente?</i>",
        "user_nn": '🔰 <b>Abilitato NoNick per <a href="tg://user?id={}">{}</a></b>',
        "enable_nonick_btn": "🔰 Attiva",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> aggiunto nel gruppo</b> <code>owner</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> rimosso dal gruppo</b> <code>owner</code>'
        ),
        "_cls_doc": "Gestisci le impostazioni di sicurezza",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Devi specificare il"
            " tipo di destinatario come primo argomento (</b><code>user</code> <b>o"
            "</b> <code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Non hai specificato"
            " il destinatario delle impostazioni di sicurezza</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Non hai specificato"
            " la regola di sicurezza (modulo o comando)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Conferma che vuoi dare a {} <a href='{}'>{}</a> il permesso di"
            " usare {}</b> <code>{}</code> <b>{}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Non sono riuscito a identificare la regola di sicurezza con"
            " precisione. Scegli quella che intendevi:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Hai dato a {} <a href='{}'>{}</a> il permesso di"
            " usare {}</b> <code>{}</code> <b>{}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Regole di sicurezza"
            " specifiche:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Nessuna regola di"
            " sicurezza specifica</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Questo utente è"
            " il proprietario, i suoi permessi non possono essere controllati"
            " dalla sicurezza mirata</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Le regole di sicurezza"
            ' mirate per <a href="{}">{}</a> sono state eliminate</b>'
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Regola di sicurezza"
            ' rimossa per <a href="{}">{}</a> (</b><code>{}</code><b>)</b>'
        ),
        "chat_inline": "⚠️ <b>Non puoi creare una regola inline per i gruppi!</b>",
        **service_strings_it,
    }

    strings_de = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Befehl"
            "</b> <code>{}</code> <b>nicht gefunden!</b>"
        ),
        "permissions": (
            "🔐 <b>Hier können Sie die Berechtigungen für den Befehl"
            "</b> <code>{}{}</code> <b>konfigurieren</b>"
        ),
        "close_menu": "🙈 Schließen Sie dieses Menü",
        "global": (
            "🔐 <b>Hier können Sie die globale Ausschlussmaske einstellen. Wenn der"
            " Schalter hier deaktiviert ist, ist er für alle Befehle deaktiviert</b>"
        ),
        "owner": "👑 Besitzer",
        "group_owner": "🧛‍♂️ Gruppenbesitzer",
        "group_admin_add_admins": "🧑‍⚖️ Admin (Mitglieder hinzufügen)",
        "group_admin_change_info": "🧑‍⚖️ Admin (Info ändern)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (Bannen)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (Nachrichten löschen)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (Anheften)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (Einladen)",
        "group_admin": "🧑‍⚖️ Admin (beliebig)",
        "group_member": "👥 In der Gruppe",
        "pm": "🤙 In Privatnachrichten",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji>"
            " <b>Gruppenbesitzer</b><code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Es gibt keine"
            " Gruppenbesitzer</b><code>owner</code>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bitte gib an, wem du"
            " Rechte geben willst</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Die angegebene Person"
            " ist kein Benutzer</b>"
        ),
        "cancel": "🚫 Abbrechen",
        "confirm": "👑 Bestätigen",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Du kannst deine"
            " eigenen Rechte nicht verwalten!</b>"
        ),
        "warning": (
            '⚠️ <b>Bist du sicher, dass du <a href="tg://user?id={}">{}</a> in die'
            " Gruppe</b> <code>{}</code> <b>hinzufügen willst?\nDieser Vorgang kann"
            " einen Teil- oder vollen Zugriff auf den Userbot für diesen Benutzer"
            " ermöglichen!</b>"
        ),
        "suggest_nonick": "🔰 <i>Möchtest du NoNick für diesen Benutzer aktivieren?</i>",
        "user_nn": '🔰 <b>NoNick für <a href="tg://user?id={}">{}</a> aktiviert</b>',
        "enable_nonick_btn": "🔰 Aktivieren",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde der Gruppe</b> <code>owner</code>'
            " <b>hinzugefügt</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> wurde aus der Gruppe</b> <code>owner</code>'
            " <b>entfernt</b>"
        ),
        "_cls_doc": "Verwalten Sie die Sicherheitseinstellungen",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Erstes Argument"
            " (</b><code>user</code> <b>or</b> <code>chat</code><b>)"
            " fehlt</b>"
        ),
        "no_chat": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Chat nicht"
            " gefunden</b>"
        ),
        "what_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Keine Regel"
            " angegeben (Modul oder Kommando)</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Keine Regel"
            " angegeben (Modul oder Kommando)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Bitte bestätigen Sie, dass Sie {} <a href='{}'>{}</a>"
            " die Berechtigung erteilen möchten {}</b> <code>{}</code> <b>{}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Es war nicht möglich, die Sicherheitsregeln eindeutig zu erkennen."
            " Wählen Sie das aus, was Sie wollten:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Sie haben {} <a href='{}'>{}</a> die Berechtigung"
            " erteilt</b> <code>{}</code> <b>{}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Regeln für die"
            " Sicherheit:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Keine Regeln für die"
            " Sicherheit</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Dieser Benutzer ist"
            " der Besitzer, seine Rechte können nicht mit Sicherheitszielen"
            " verwaltet werden</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Die Sicherheitsregeln"
            " für <a href='{}'>{}</a> wurden entfernt</b>"
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Sicherheitsregel"
            ' entfernt für <a href="{}">{}</a> (</b><code>{}</code><b>)</b>'
        ),
        "chat_inline": (
            "⚠️ <b>Du kannst keine Regel für inline-Befehle für Chats erstellen!</b>"
        ),
        **service_strings_de,
    }

    strings_tr = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Komut"
            "</b> <code>{}</code> <b>bulunamadı!</b>"
        ),
        "permissions": (
            "🔐 <b>Bu komut için</b><code>{}{}</code> <b>izinlerini"
            " yapılandırabilirsiniz</b>"
        ),
        "close_menu": "🙈 Bu menüyü kapat",
        "global": (
            "🔐 <b>Bu, tüm komutlar için devre dışı bırakılmışsa, genel yasaklama"
            " maskesini ayarlamanıza olanak tanır</b>"
        ),
        "owner": "👑 Sahip",
        "group_owner": "🧛‍♂️ Grup Sahibi",
        "group_admin_add_admins": "🧑‍⚖️ Yönetici (Üyeleri ekle)",
        "group_admin_change_info": "🧑‍⚖️ Yönetici (Bilgi değiştir)",
        "group_admin_ban_users": "🧑‍⚖️ Yönetici (Yasakla)",
        "group_admin_delete_messages": "🧑‍⚖️ Yönetici (Mesajları sil)",
        "group_admin_pin_messages": "🧑‍⚖️ Yönetici (Sabitler)",
        "group_admin_invite_users": "🧑‍⚖️ Yönetici (Davet et)",
        "group_admin": "🧑‍⚖️ Yönetici (herhangi)",
        "group_member": "👥 Grup içinde",
        "pm": "🤙 Özel mesajlarda",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji>"
            " <b>Grup Sahibi</b><code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Grup Sahibi"
            " yok</b><code>owner</code>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Lütfen hangi"
            " kullanıcıya izin vereceğinizi belirtin</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Belirtilen kişi bir"
            " kullanıcı değil</b>"
        ),
        "cancel": "🚫 İptal",
        "confirm": "👑 Onayla",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Kendi izinlerini"
            " yönetemezsin!</b>"
        ),
        "warning": (
            '⚠️ <b><a href="tg://user?id={}">{}</a> kullanıcısını</b><code>{}</code><b>'
            " grubuna eklemek istediğinden emin misin?\nBu, kullanıcı için Userbot için"
            " bir bölünmüş veya tam erişim sağlayabilir!</b>"
        ),
        "suggest_nonick": (
            "🔰 <i>Bu kullanıcı için NoNick'i etkinleştirmek ister misin?</i>"
        ),
        "user_nn": (
            '🔰 <b>NoNick <a href="tg://user?id={}">{}</a> için etkinleştirildi</b>'
        ),
        "enable_nonick_btn": "🔰 Etkinleştir",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı</b> <code>sahip</code>'
            " <b>grubuna eklendi</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> adlı kullanıcı</b> <code>sahip</code>'
            " <b>grubundan çıkartıldı</b>"
        ),
        "_cls_doc": "Güvenlik ayarlarını yönet",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>İlk argüman"
            " (</b><code>user</code> <b>veya</b> <code>chat</code><b>) bulunamadı</b>"
        ),
        "no_chat": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Sohbet bulunamadı</b>"
        ),
        "what_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Hiçbir kural"
            " belirtilmedi (modül veya komut)</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Hiçbir kural"
            " belirtilmedi (modül veya komut)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Lütfen {} <a href='{}'>{}</a> için izin vermek istediğinize emin olun"
            " {}</b> <code>{}</code> <b>{}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Güvenlik kuralları tek bir şekilde tanımlanamadı."
            " İstediğinizi seçin:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>{} <a href='{}'>{}</a> için izin verildi</b> <code>{}</code><b>"
            " {}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Güvenlik"
            " kuralları:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Güvenlik kuralları"
            " yok</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Bu kullanıcı sahip,"
            " güvenlik hedefleriyle yönetilemeyen hakları vardır</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b><a"
            ' href="{}">{}</a> için güvenlik kuralları kaldırıldı</b>'
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>İzin kaldırıldı"
            ' <a href="{}">{}</a> (</b><code>{}</code><b>)</b>'
        ),
        "chat_inline": (
            "⚠️ <b>Inline komutu için bir sohbet kuralı oluşturamazsınız!</b>"
        ),
        **service_strings_tr,
    }

    strings_uz = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bunday"
            " buyruq</b> <code>{}</code> <b>topilmadi!</b>"
        ),
        "permissions": (
            "🔐 <b>Bu yerda</b> <code>{}{}</code> <b>buyrug'i uchun ruxsatlar"
            " o'zgartirilishi mumkin</b>"
        ),
        "close_menu": "🙈 Menuni yopish",
        "global": (
            "🔐 <b>Bu yerda umumiy cheklash maskasini o'zgartirish mumkin. Agar"
            " tugmani bu yerda o'chirilgan bo'lsa, unda bu barcha buyruqlar uchun"
            " o'chirilgan bo'ladi</b>"
        ),
        "owner": "😎 Sahib",
        "group_owner": "🧛‍♂️ Guruh egasi",
        "group_admin_add_admins": "🧑‍⚖️ Admin (qo'shish)",
        "group_admin_change_info": "🧑‍⚖️ Admin (info o'zgartirish)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (banning)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (o'chirish)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (qulflash)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (qo'shish)",
        "group_admin": "🧑‍⚖️ Admin (har qanday)",
        "group_member": "👥 Guruhda",
        "pm": "🤙 Shaxsiy habarlar",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Guruh</b> <code>sahibi"
            "</code> <b>foydalanuvchilari:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Guruhda"
            "</b> <code>sahib</code> <b>foydalanuvchilar yo'q</b>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Qaysi foydalanuvchiga"
            " huquqlarni berishni xohlaysiz</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Tayinlangan maqsad -"
            " foydalanuvchi emas</b>"
        ),
        "cancel": "🚫 Bekor qilish",
        "confirm": "👑 Tasdiqlash",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>O'zingizning"
            " huquqlaringizni boshqalariga bermang!</b>"
        ),
        "warning": (
            '⚠️ <b>Siz haqiqatdan ham <a href="tg://user?id={}">{}</a> ni guruhga'
            "</b> <code>{}</code> <b>qo'shmoqchimisiz!\nBu harakat bu foydalanuvchiga"
            " qismi yoki to'liq huquqlarni o'tkazishi mumkin!</b>"
        ),
        "suggest_nonick": (
            "🔰 <i>Siz buni foydalanuvchiga NoNickni yoqishni xohlaysizmi?</i>"
        ),
        "user_nn": '🔰 <b><a href="tg://user?id={}">{}</a> uchun NoNick yoqildi</b>',
        "enable_nonick_btn": "🔰 Yoqish",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> guruhga</b> <code>owner</code>'
            " <b>qo'shildi</b>"
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> guruhdan</b> <code>owner</code>'
            " <b>o'chirildi</b>"
        ),
        "_cls_doc": "Xavfsizlik sozlamalarini boshqarish",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Siz boshqarish"
            " uchun biror narsani ko'rsatmadingiz</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Siz boshqarish"
            " uchun biror narsani ko'rsatmadingiz</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Xavfsizlik"
            " qoidasi (modul yoki buyruq) ko'rsatilmagan</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Iltimos, tasdiqlang {} <a href='{}'>{}</a> uchun {}"
            "</b> <code>{}</code> <b>{}</b> <b>huquqini berishni</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Xavfsizlik qoidalarini aniq tartibda aniqlab bo'lmadi."
            " Sizga kerakli qoidani tanlang:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Siz {} <a href='{}'>{}</a> uchun {}"
            "</b> <code>{}</code> <b>{}</b> <b>huquqini berdingiz</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Targ'etlangan"
            " xavfsizlik qoidalari:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Targ'etlangan"
            " xavfsizlik qoidalari yo'q</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Ushbu foydalanuvchi"
            " guruhning egasi, u uchun targ'etlangan xavfsizlik qoidalari"
            " boshqarilishi mumkin emas</b>"
        ),
        "rules_removed": (
            '<emoji document_id=5472308992514464048>🔐</emoji> <b><a href="{}">{}</a>'
            " uchun targ'etlangan xavfsizlik qoidalari o'chirildi</b>"
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Qo'shimcha tizim "
            'xavfsizligi uchun <a href="{}">{}</a> (<code>{}</code>)</b> o\'chirildi'
        ),
        "chat_inline": (
            "⚠️ <b>Siz chatlar uchun inline buyruqini yaratib bo'lmaysiz!</b>"
        ),
        **service_strings_uz,
    }

    strings_es = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Comando"
            "</b> <code>{}</code> <b>no encontrado!</b>"
        ),
        "permissions": (
            "🔐 <b>Aquí puede configurar los permisos para el comando"
            "</b> <code>{}{}</code>"
        ),
        "close_menu": "🙈 Cerrar este menú",
        "global": (
            "🔐 <b>Aquí puede configurar la máscara de exclusión global. Si el"
            " interruptor está apagado aquí, está apagado para todos los comandos</b>"
        ),
        "owner": "😎 Dueño",
        "group_owner": "🧛‍♂️ Dueño del grupo",
        "group_admin_add_admins": "🧑‍⚖️ Admin (agregar miembros)",
        "group_admin_change_info": "🧑‍⚖️ Admin (cambiar información)",
        "group_admin_ban_users": "🧑‍⚖️ Admin (banear)",
        "group_admin_delete_messages": "🧑‍⚖️ Admin (eliminar mensajes)",
        "group_admin_pin_messages": "🧑‍⚖️ Admin (anclar)",
        "group_admin_invite_users": "🧑‍⚖️ Admin (invitar)",
        "group_admin": "🧑‍⚖️ Admin (cualquiera)",
        "group_member": "👥 En el grupo",
        "pm": "🤙 En el pm",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Usuarios del grupo"
            "</b> <code>owner</code><b>:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>No hay usuarios en el"
            " grupo</b> <code>owner</code>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Indica a quien"
            " otorgarle permisos</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>La meta indicada no"
            " es un usuario</b>"
        ),
        "cancel": "🚫 Cancelar",
        "confirm": "👑 Confirmar",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>No puedes administrar"
            " tus propios permisos!</b>"
        ),
        "warning": (
            "⚠️ <b>Estas seguro de que quieres agregar a <a"
            ' href="tg://user?id={}">{}</a> al grupo</b> <code>{}</code><b>!\nEste'
            " proceso puede otorgar acceso parcial o total a este usuario al bot!</b>"
        ),
        "suggest_nonick": "🔰 <i>Quieres activar NoNick para este usuario?</i>",
        "user_nn": '🔰 <b>NoNick para <a href="tg://user?id={}">{}</a> activado</b>',
        "enable_nonick_btn": "🔰 Activar",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> añadido al grupo</b> <code>owner</code>'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> eliminado del grupo</b> <code>owner</code>'
        ),
        "_cls_doc": "Administrar configuraciones de seguridad",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Necesitas especificar"
            " el tipo de objetivo como primer argumento (</b><code>user</code> <b>o"
            "</b> <code>chat</code><b>)</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No se ha especificado"
            " el objetivo de la regla de seguridad</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No se ha especificado"
            " la regla de seguridad (módulo o comando)</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Confirme que desea otorgar {} <a href='{}'>{}</a> el derecho a"
            " usar {}</b> <code>{}</code> <b>{}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>No se pudo identificar con seguridad la regla. Seleccione la que"
            " tenías en mente:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Has otorgado {} <a href='{}'>{}</a> el derecho a usar {}</b> "
            "<code>{}</code> <b>{}</b>"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Reglas de seguridad"
            " dirigidas:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>No hay reglas de"
            " seguridad dirigidas</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Este usuario es el"
            " propietario, sus derechos no pueden ser manejados por reglas de"
            " seguridad dirigidas</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Reglas de seguridad"
            " dirigidas para <a href='{}'>{}</a> eliminadas</b>"
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Regla de seguridad"
            ' eliminada para <a href="{}">{}</a> (</b><code>{}</code><b>)</b>'
        ),
        "chat_inline": (
            "⚠️ <b>¡No puedes crear una regla de comando inline para chats!</b>"
        ),
        **service_strings_es,
    }

    strings_kk = {
        "no_command": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Команда"
            "</b> <code>{}</code> <b>табылмады!</b>"
        ),
        "permissions": (
            "🔐 <b>Мұнда команда</b> <code>{}{}</code> <b>үшін рұқсаттарды баптау"
            " жасай аласыз</b>"
        ),
        "close_menu": "🙈 Мәзірді жабу",
        "global": (
            "🔐 <b>Мұнда қосымша үйлесімдік масканы баптауға болады. Егер түймешік"
            " бұл жерде өшірілген болса, барлық командалар үшін өшіріледі</b>"
        ),
        "owner": "😎 Есімші",
        "group_owner": "🧛‍♂️ Топ есімшісі",
        "group_admin_add_admins": "🧑‍⚖️ Админ (қатысушыларды қосу)",
        "group_admin_change_info": "🧑‍⚖️ Админ (ақпаратты өзгерту)",
        "group_admin_ban_users": "🧑‍⚖️ Админ (қатысушыларды бұғаттау)",
        "group_admin_delete_messages": "🧑‍⚖️ Админ (хабарларды жою)",
        "group_admin_pin_messages": "🧑‍⚖️ Админ (белгілеу)",
        "group_admin_invite_users": "🧑‍⚖️ Админ (қатысушыларды шақыру)",
        "group_admin": "🧑‍⚖️ Админ (барлығы)",
        "group_member": "👥 Топта",
        "pm": "🤙 ЛС",
        "owner_list": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Топ"
            "</b> <code>owner</code><b>дегендері:</b>\n\n{}"
        ),
        "no_owner": (
            "<emoji document_id=5386399931378440814>😎</emoji> <b>Топ"
            "</b> <code>owner</code><b>дегендері жоқ</b>"
        ),
        "no_user": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Құқықтарды беру үшін"
            " қатысушыны көрсет</b>"
        ),
        "not_a_user": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Көрсетілген мақсат -"
            " қатысушы емес</b>"
        ),
        "cancel": "🚫 Болдырмау",
        "confirm": "👑 Растау",
        "self": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Өзіңіздің құқықтарын"
            " басқаруға болмайды!</b>"
        ),
        "warning": (
            '⚠️ <b>Сіз <a href="tg://user?id={}">{}</a>ді топ</b> <code>{}</code><b>ға'
            " қосу келісімін қалайсыз?\nБұл әрекетті қайтару мүмкін емес!</b>"
        ),
        "suggest_nonick": "🔰 <i>Бұл пайдаланушы үшін NoNick қосыңыз келеді ме?</i>",
        "user_nn": '🔰 <b><a href="tg://user?id={}">{}</a> үшін NoNick қосылды</b>',
        "enable_nonick_btn": "🔰 Қосу",
        "owner_added": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> қосылды</b> <code>owner</code> топқа'
        ),
        "owner_removed": (
            '<emoji document_id="5386399931378440814">😎</emoji> <b><a'
            ' href="tg://user?id={}">{}</a> алынды</b> <code>owner</code> топтан'
        ),
        "_cls_doc": "Безпеке баптауларын басқару",
        "what": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Басқауыңызға бұрын"
            " баптау түрін (</b><code>user</code> <b>немесе</b> <code>chat</code><b>)"
            " көрсетіңіз</b>"
        ),
        "no_target": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Безпекаға қатысу"
            " үшін құжаттама берілмейді</b>"
        ),
        "no_rule": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Безпекаға қатысу"
            " үшін модуль немесе команда белгіленмейді</b>"
        ),
        "confirm_rule": (
            "🔐 <b>Өзгерістерді растау үшін, келесі құжаттамаға қатысуыңызға"
            " рұқсат беру үшін {} <a href='{}'>{}</a> {}</b> <code>{}</code><b>"
            " {}</b>"
        ),
        "multiple_rules": (
            "🔐 <b>Безпекаға қатысу үшін құжаттамаға қатысуыңызға рұқсат беру"
            " үшін бірнеше құжаттама белгіленген. Келесінен бірін таңдаңыз:</b>\n\n{}"
        ),
        "rule_added": (
            "🔐 <b>Сіз {} <a href='{}'>{}</a> {}</b> <code>{}</code> <b>{}</b>"
            " үшін құжаттамаға қатысуыңызға рұқсат бердіңіз"
        ),
        "rules": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Құжаттамаға"
            " қатысу үшін белгіленген баптаулар:</b>\n\n{}"
        ),
        "no_rules": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Құжаттамаға"
            " қатысу үшін белгіленген баптаулар жоқ</b>"
        ),
        "owner_target": (
            "<emoji document_id=5447644880824181073>⚠️</emoji> <b>Бұл пайдаланушы"
            " босқа құжаттамаларға қатысу үшін баптауларды белгілеуі мүмкін"
            " емес</b>"
        ),
        "rules_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Құжаттамаға"
            " қатысу үшін <a href='{}'>{}</a> үшін белгіленген баптаулар"
            " жойылды</b>"
        ),
        "rule_removed": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Қауіпсіздік"
            ' қауіпсіздік қауіпсіздік қауіпсіздік <a href="{}">{}</a>'
            " (</b><code>{}</code><b>)</b>"
        ),
        "chat_inline": (
            "⚠️ <b>Сіз inline-командасының чаттар үшін ережесін жасай алмайсыз!</b>"
        ),
        **service_strings_kk,
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
                (
                    "Security value set but not applied. Consider enabling this value"
                    f" in .{'inlinesec' if is_inline else 'security'}"
                ),
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
            {"everyone": bool(perms & EVERYONE)}
            if is_inline
            else {
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
        fr_doc="[command] - Configure les permissions pour les commandes",
        it_doc="[comando] - Imposta i permessi per il comando",
        de_doc="[command] - Einstellungen für Befehle ändern",
        tr_doc="[command] - Komut için izinleri ayarla",
        uz_doc="[command] - Buyruq uchun ruxsatlarini sozlash",
        es_doc="[command] - Configurar permisos para comandos",
        kk_doc="[command] - Команданың рұқсаттарын баптау",
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
        fr_doc="[command] - Configure les permissions pour les commandes inline",
        it_doc="[comando] - Imposta i permessi per il comando inline",
        de_doc="[command] - Einstellungen für Inline-Befehle ändern",
        tr_doc="[command] - Inline komut için izinleri ayarla",
        uz_doc="[command] - Inline buyruq uchun ruxsatlarini sozlash",
        es_doc="[command] - Configurar permisos para comandos inline",
        kk_doc="[command] - Инлайн команданың рұқсаттарын баптау",
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
            with contextlib.suppress(Exception):
                if str(args).isdigit():
                    args = int(args)

                user = await self._client.get_entity(args, exp=0)

        if user is None:
            user = await self._client.get_entity(reply.sender_id, exp=0)

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
            if not (user := await self._resolve_user(message)):
                return

        if isinstance(user, int):
            user = await self._client.get_entity(user, exp=0)

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

    @loader.command(
        ru_doc="<пользователь> - Добавить пользователя в группу `owner`",
        fr_doc="<utilisateur> - Ajouter un utilisateur au groupe `owner`",
        it_doc="<utente> - Aggiungi utente al gruppo `owner`",
        de_doc="<Benutzer> - Füge Benutzer zur `owner`-Gruppe hinzu",
        tr_doc="<kullanıcı> - Kullanıcıyı `owner` grubuna ekle",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `owner` guruhiga qo'shish",
        es_doc="<usuario> - Agregar usuario al grupo `owner`",
        kk_doc="<пайдаланушы> - Пайдаланушыны `owner` тобына қосу",
    )
    async def owneradd(self, message: Message):
        """<user> - Add user to `owner`"""
        await self._add_to_group(message, "owner")

    @loader.command(
        ru_doc="<пользователь> - Удалить пользователя из группы `owner`",
        fr_doc="<utilisateur> - Supprimer un utilisateur du groupe `owner`",
        it_doc="<utente> - Rimuovi utente dal gruppo `owner`",
        de_doc="<Benutzer> - Entferne Benutzer aus der `owner`-Gruppe",
        tr_doc="<kullanıcı> - Kullanıcıyı `owner` grubundan kaldır",
        uz_doc="<foydalanuvchi> - Foydalanuvchini `owner` guruhidan olib tashlash",
        es_doc="<usuario> - Eliminar usuario del grupo `owner`",
        kk_doc="<пайдаланушы> - Пайдаланушыны `owner` тобынан алып тастау",
    )
    async def ownerrm(self, message: Message):
        """<user> - Remove user from `owner`"""
        if not (user := await self._resolve_user(message)):
            return

        if user.id in getattr(self._client.dispatcher.security, "owner"):
            getattr(self._client.dispatcher.security, "owner").remove(user.id)

        m = self.strings("owner_removed").format(
            user.id,
            utils.escape_html(get_display_name(user)),
        )

        await utils.answer(message, m)

    @loader.command(
        ru_doc="Показать список пользователей в группе `owner`",
        fr_doc="Afficher la liste des utilisateurs dans le groupe `owner`",
        it_doc="Mostra la lista degli utenti nel gruppo `owner`",
        de_doc="Zeige Liste der Benutzer in der `owner`-Gruppe",
        tr_doc="`owner` grubundaki kullanıcıların listesini göster",
        uz_doc="`owner` guruhidagi foydalanuvchilar ro'yxatini ko'rsatish",
        es_doc="Mostrar lista de usuarios en el grupo `owner`",
        kk_doc="`owner` тобындағы пайдаланушылар тізімін көрсету",
    )
    async def ownerlist(self, message: Message):
        """List users in `owner`"""
        _resolved_users = []
        for user in set(
            getattr(self._client.dispatcher.security, "owner") + [self.tg_id]
        ):
            with contextlib.suppress(Exception):
                _resolved_users += [await self._client.get_entity(user, exp=0)]

        if not _resolved_users:
            await utils.answer(message, self.strings("no_owner"))
            return

        await utils.answer(
            message,
            self.strings("owner_list").format(
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

    def _lookup(self, needle: str) -> str:
        return (
            (
                []
                if needle.lower().startswith(self.get_prefix())
                else (
                    [f"module/{self.lookup(needle).__class__.__name__}"]
                    if self.lookup(needle)
                    else []
                )
            )
            + (
                [f"command/{needle.lower().strip(self.get_prefix())}"]
                if needle.lower().strip(self.get_prefix()) in self.allmodules.commands
                else []
            )
            + (
                [f"inline/{needle.lower().strip('@')}"]
                if needle.lower().strip("@") in self.allmodules.inline_handlers
                else []
            )
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
        if rule.startswith("inline") and target_type == "chat":
            await call.edit(self.strings("chat_inline"))
            return

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
                (
                    (
                        f"@{self.inline.bot_username} "
                        if rule.split("/", maxsplit=1)[0] == "inline"
                        else ""
                    )
                    + rule.split("/", maxsplit=1)[1]
                ),
                (
                    (self.strings("for") + " " + self._convert_time(duration))
                    if duration
                    else self.strings("forever")
                ),
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
                (
                    (
                        f"@{self.inline.bot_username} "
                        if rule.split("/", maxsplit=1)[0] == "inline"
                        else ""
                    )
                    + rule.split("/", maxsplit=1)[1]
                ),
                (
                    (self.strings("for") + " " + self._convert_time(duration))
                    if duration
                    else self.strings("forever")
                ),
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
                    int(args[1]) if args[1].isdigit() else args[1],
                    exp=0,
                )
            except (ValueError, TypeError):
                if not message.is_private:
                    target = await self._client.get_entity(message.peer_id, exp=0)
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
                        "🛡 <b>{}</b> <code>{}</code>".format(
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
                    int(args[1]) if args[1].isdigit() else args[1],
                    exp=0,
                )
            except (ValueError, TypeError):
                if message.is_private:
                    target = await self._client.get_entity(message.peer_id, exp=0)
                elif message.is_reply:
                    target = await self._client.get_entity(
                        (await message.get_reply_message()).sender_id,
                        exp=0,
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
                        "🛡 <b>{}</b> <code>{}</code>".format(
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
        ru_doc=(
            '<"user"/"chat"> <правило - модуль или команда> - Удалить правило'
            " таргетированной безопасности\nНапример: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        fr_doc=(
            '<"user"/"chat"> <règle - module ou commande> - Supprimer la règle de'
            " sécurité ciblée\nPar exemple: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        es_doc=(
            '<"user"/"chat"> <regla - módulo o comando> - Eliminar la regla de'
            " seguridad dirigida\nPor ejemplo: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        de_doc=(
            '<"user"/"chat"> <Regel - Modul oder Befehl> - Entferne die Regel der'
            " zielgerichteten Sicherheit\nBeispiel: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        it_doc=(
            '<"user"/"chat"> <regola - modulo o comando> - Rimuovi la regola di'
            " sicurezza mirata\nEsempio: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        tr_doc=(
            '<"user"/"chat"> <kural - modül veya komut> - Hedefli güvenlik kuralını'
            " kaldır\nÖrnek: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
        uz_doc=(
            '<"user"/"chat"> <qoida - modul yoki buyruq> - Maqsadli xavfsizlik'
            " qoidasini olib tashlang\nMasalan: .tsecrm user ban, .tsecrm chat"
            " HikariChat"
        ),
        kk_doc=(
            '<"user"/"chat"> <құқық - модуль немесе команда> - Мақсатты қауіпсіздік'
            " құқығын өшіріңіз\nМысалы: .tsecrm user ban, .tsecrm chat HikariChat"
        ),
    )
    async def tsecrm(self, message: Message):
        """
        <"user"/"chat"> <rule - command or module> - Remove targeted security rule
        For example: .tsecrm user ban, .tsecrm chat HikariChat
        """
        if (
            not self._client.dispatcher.security.tsec_chat
            and not self._client.dispatcher.security.tsec_user
        ):
            await utils.answer(message, self.strings("no_rules"))
            return

        args = utils.get_args(message)
        if not args or args[0] not in {"user", "chat"}:
            await utils.answer(message, self.strings("no_target"))
            return

        if args[0] == "user":
            if not message.is_private and not message.is_reply:
                await utils.answer(message, self.strings("no_target"))
                return

            if message.is_private:
                target = await self._client.get_entity(message.peer_id, exp=0)
            elif message.is_reply:
                target = await self._client.get_entity(
                    (await message.get_reply_message()).sender_id,
                    exp=0,
                )

            if not self._client.dispatcher.security.remove_rule(
                "user",
                target.id,
                args[1],
            ):
                await utils.answer(message, self.strings("no_rules"))
                return

            await utils.answer(
                message,
                self.strings("rule_removed").format(
                    utils.get_entity_url(target),
                    utils.escape_html(get_display_name(target)),
                    utils.escape_html(args[1]),
                ),
            )
            return

        if message.is_private:
            await utils.answer(message, self.strings("no_target"))
            return

        target = await self._client.get_entity(message.peer_id, exp=0)

        if not self._client.dispatcher.security.remove_rule("chat", target.id, args[1]):
            await utils.answer(message, self.strings("no_rules"))
            return

        await utils.answer(
            message,
            self.strings("rule_removed").format(
                utils.get_entity_url(target),
                utils.escape_html(get_display_name(target)),
                utils.escape_html(args[1]),
            ),
        )

    @loader.command(
        ru_doc=(
            '<"user"/"chat"> - Очистить правила таргетированной безопасности\nНапример:'
            " .tsecclr user, .tsecclr chat"
        ),
        fr_doc=(
            '<"user"/"chat"> - Supprimer les règles de sécurité ciblées\nPar exemple:'
            " .tsecclr user, .tsecclr chat"
        ),
        es_doc=(
            '<"user"/"chat"> - Eliminar las reglas de seguridad dirigidas\nPor ejemplo:'
            " .tsecclr user, .tsecclr chat"
        ),
        de_doc=(
            '<"user"/"chat"> - Entferne die Regeln der zielgerichteten'
            " Sicherheit\nBeispiel: .tsecclr user, .tsecclr chat"
        ),
        it_doc=(
            '<"user"/"chat"> - Rimuovi le regole di sicurezza mirate\nEsempio: .tsecclr'
            " user, .tsecclr chat"
        ),
        tr_doc=(
            '<"user"/"chat"> - Hedefli güvenlik kurallarını temizle\nÖrnek: .tsecclr'
            " user, .tsecclr chat"
        ),
        uz_doc=(
            '<"user"/"chat"> - Maqsadli xavfsizlik qoidalarini tozalash\nMasalan:'
            " .tsecclr user, .tsecclr chat"
        ),
        kk_doc=(
            '<"user"/"chat"> - Мақсатты қауіпсіздік құқығын тазалаңыз\nМысалы: .tsecclr'
            " user, .tsecclr chat"
        ),
    )
    async def tsecclr(self, message: Message):
        """
        <"user"/"chat"> - Clear targeted security rules
        For example: .tsecclr user, .tsecclr chat
        """
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
                target = await self._client.get_entity(message.peer_id, exp=0)
            elif message.is_reply:
                target = await self._client.get_entity(
                    (await message.get_reply_message()).sender_id,
                    exp=0,
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

        target = await self._client.get_entity(message.peer_id, exp=0)

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
            '<"user"/"chat"> [цель пользователя или чата] [правило (команда/модуль)]'
            " [время] - Добавить новое правило таргетированной безопасности\nНапример:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        fr_doc=(
            '<"user"/"chat"> [cible utilisateur ou chat] [règle (commande/module)]'
            " [temps] - Ajouter une nouvelle règle de sécurité ciblée\nPar exemple:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        es_doc=(
            '<"user"/"chat"> [objetivo de usuario o chat] [regla (comando/módulo)]'
            " [tiempo] - Agregar una nueva regla de seguridad dirigida\nPor ejemplo:"
            " .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        de_doc=(
            '<"user"/"chat"> [Zielbenutzer oder Chat] [Regel (Befehl/Modul)] [Zeit] -'
            " Füge eine neue zielgerichtete Sicherheitsregel hinzu\nBeispiel: .tsec"
            " user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        it_doc=(
            '<"user"/"chat"> [utente o chat di destinazione] [regola (comando/modulo)]'
            " [tempo] - Aggiungi una nuova regola di sicurezza mirata\nEsempio: .tsec"
            " user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        tr_doc=(
            '<"user"/"chat"> [hedef kullanıcı veya sohbet] [kural (komut/modül)]'
            " [zaman] - Yeni hedefli güvenlik kuralı ekleyin\nÖrnek: .tsec user ban 1d,"
            " .tsec chat weather 1h, .tsec user HikariChat"
        ),
        uz_doc=(
            '<"user"/"chat"> [maqsadli foydalanuvchi yoki chat] [qoida (buyruq/modul)]'
            " [vaqt] - Yangi maqsadli xavfsizlik qoidasini qo`shing\nMasalan: .tsec"
            " user ban 1d, .tsec chat weather 1h, .tsec user HikariChat"
        ),
        kk_doc=(
            '<"user"/"chat"> [мақсатты пайдаланушы немесе сөйлесу] [құқық'
            " (команда/модуль)] [уақыт] - Жаңа мақсатты қауіпсіздік құқығын"
            " қосыңыз\nМысалы: .tsec user ban 1d, .tsec chat weather 1h, .tsec user"
            " HikariChat"
        ),
    )
    async def tsec(self, message: Message):
        """
        <"user"/"chat"> [target user or chat] [rule (command/module)] [time] - Add new targeted security rule
        For example: .tsec user ban 1d, .tsec chat weather 1h, .tsec user HikariChat
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
