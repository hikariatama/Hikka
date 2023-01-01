# ©️ Dan Gazizullin, 2021-2022
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import logging
import os
import subprocess
import sys
import time
import typing

import git
from git import GitCommandError, Repo
from telethon.extensions.html import CUSTOM_EMOJIS
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import DialogFilter, Message

from .. import loader, main, utils, version
from .._internal import restart
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Updates itself"""

    strings = {
        "name": "Updater",
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Read the source code"
            " from</b> <a href='{}'>here</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Your {} is"
            " restarting...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Downloading"
            " updates...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Installing"
            " updates...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Restart successful!"
            " {}</b>\n<i>But still loading modules...</i>\n<i>Restart took {}s</i>"
        ),
        "origin_cfg_doc": "Git origin URL, for where to update from",
        "btn_restart": "🔄 Restart",
        "btn_update": "🧭 Update",
        "restart_confirm": "❓ <b>Are you sure you want to restart?</b>",
        "secure_boot_confirm": (
            "❓ <b>Are you sure you want to restart in secure boot mode?</b>"
        ),
        "update_confirm": (
            "❓ <b>Are you sure you"
            " want to update?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>You are on the latest version, pull updates anyway?</b>",
        "cancel": "🚫 Cancel",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Your {} is"
            " updating...</b>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Userbot is fully"
            " loaded! {}</b>\n<i>Full restart took {}s</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Secure boot completed!"
            " {}</b>\n<i>Restart took {}s</i>"
        ),
    }

    strings_ru = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Исходный код можно"
            " прочитать</b> <a href='{}'>здесь</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Твоя {}"
            " перезагружается...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Скачивание"
            " обновлений...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Установка"
            " обновлений...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Перезагрузка"
            " успешна! {}</b>\n<i>Но модули еще загружаются...</i>\n<i>Перезагрузка"
            " заняла {} сек</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Юзербот полностью"
            " загружен! {}</b>\n<i>Полная перезагрузка заняла {} сек</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Безопасная загрузка"
            " завершена! {}</b>\n<i>Перезагрузка заняла {} сек</i>"
        ),
        "origin_cfg_doc": "Ссылка, из которой будут загружаться обновления",
        "btn_restart": "🔄 Перезагрузиться",
        "btn_update": "🧭 Обновиться",
        "restart_confirm": "❓ <b>Ты уверен, что хочешь перезагрузиться?</b>",
        "secure_boot_confirm": (
            "❓ <b>Ты уверен, что"
            " хочешь перезагрузиться в режиме безопасной загрузки?</b>"
        ),
        "update_confirm": (
            "❓ <b>Ты уверен, что"
            " хочешь обновиться?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>У тебя последняя версия. Обновиться принудительно?</b>",
        "cancel": "🚫 Отмена",
        "_cls_doc": "Обновляет юзербот",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Твой {}"
            " обновляется...</b>"
        ),
    }

    strings_it = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Il codice sorgente può"
            " essere letto</b> <a href='{}'>qui</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Il tuo {}"
            " si sta riavviando...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Download"
            " aggiornamenti in corso...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Installazione"
            " aggiornamenti in corso...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Riavvio"
            " completato! {}</b>\n<i>Ma i moduli stanno ancora caricando...</i>\n<i>Il"
            " riavvio ha richiesto {} secondi</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Hikka è stato"
            " completamente caricato! {}</b>\n<i>Il riavvio completo ha richiesto {}"
            " secondi</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Avvio sicuro"
            " completato! {}</b>\n<i>Il riavvio ha richiesto {} secondi</i>"
        ),
        "origin_cfg_doc": "Il link da cui scaricare gli aggiornamenti",
        "btn_restart": "🔄 Riavvio",
        "btn_update": "🧭 Aggiorna",
        "restart_confirm": "❓ <b>Sei sicuro di voler riavviare?</b>",
        "secure_boot_confirm": (
            "❓ <b>Sei sicuro di voler riavviare in modalità avvio sicuro?</b>"
        ),
        "update_confirm": (
            "❓ <b>Sei sicuro di"
            " voler aggiornare?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>Sei già aggiornato. Forzare l'aggiornamento?</b>",
        "cancel": "🚫 Annulla",
        "_cls_doc": "Aggiorna il tuo userbot",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Il tuo {}"
            " sta per essere aggiornato...</b>"
        ),
    }

    strings_de = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Der Quellcode kann"
            " hier</b> <a href='{}'>gelesen</a> <b>werden</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Dein {}"
            " wird neugestartet...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Updates"
            " werden heruntergeladen...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Updates"
            " werden installiert...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Neustart erfolgreich!"
            " {}</b>\n<i>Aber Module werden noch geladen...</i>\n<i>Neustart dauerte {}"
            " Sekunden</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Dein Userbot ist"
            " vollständig geladen! {}</b>\n<i>Vollständiger Neustart dauerte {}"
            " Sekunden</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Sicherer Bootvorgang"
            " abgeschlossen! {}</b>\n<i>Neustart dauerte {} Sekunden</i>"
        ),
        "origin_cfg_doc": "Link, von dem Updates heruntergeladen werden",
        "btn_restart": "🔄 Neustart",
        "btn_update": "🧭 Update",
        "restart_confirm": "❓ <b>Bist du sicher, dass du neustarten willst?</b>",
        "secure_boot_confirm": (
            "❓ <b>Bist du sicher, dass du in den sicheren Modus neustarten willst?</b>"
        ),
        "update_confirm": (
            "❓ <b>Bist du sicher, dass"
            " du updaten willst?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": (
            "🚸 <b>Du hast die neueste Version. Willst du trotzdem updaten?</b>"
        ),
        "cancel": "🚫 Abbrechen",
        "_cls_doc": "Aktualisiert den Userbot",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Dein {}"
            " wird aktualisiert...</b>"
        ),
    }

    strings_tr = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Kaynak kodunu"
            "</b>  <a href='{}'>buradan oku</a>"
        ),
        "restarting": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>{}"
            " yeniden başlatılıyor...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>{}"
            " yeniden başlatılıyor...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Güncelleme"
            " indiriliyor...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Güncelleme"
            " kuruluyor...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Yeniden başlatma"
            " başarılı! {}</b>\n<i>Modüller yükleniyor...</i>\n<i>Yeniden başlatma {}"
            " saniye sürdü</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Kullanıcı botunuz"
            " tamamen yüklendi! {}</b>\n<i>Toplam yeniden başlatma {} saniye sürdü</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Güvenli mod başarıyla"
            " tamamlandı! {}</b>\n<i>Yeniden başlatma {} saniye sürdü</i>"
        ),
        "origin_cfg_doc": "Git kaynak URL, güncelleme indirilecek kaynak",
        "btn_restart": "🔄 Yeniden başlat",
        "btn_update": "🧭 Güncelle",
        "restart_confirm": "❓ <b>Gerçekten yeniden başlatmak istiyor musunuz?</b>",
        "secure_boot_confirm": (
            "❓ <b>Gerçekten güvenli modda yeniden başlatmak istiyor musunuz?</b>"
        ),
        "update_confirm": (
            "❓ <b>Gerçekten güncellemek istiyor musunuz?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>Zaten son sürümünüz. Güncelleme yapmak ister misiniz?</b>",
        "cancel": "🚫 İptal",
        "_cls_doc": "Kullanıcı botunu günceller",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>{}"
            " güncelleniyor...</b>"
        ),
    }

    strings_uz = {
        "restarting": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>{}"
            " qayta ishga tushirilmoqda...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>{}"
            " qayta ishga tushirilmoqda...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Yangilanish"
            " yuklanmoqda...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Yangilanish"
            " o'rnatilmoqda...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Qayta ishga tushirish"
            " muvaffaqiyatli yakunlandi! {}</b>\n<i>Modullar"
            " yuklanmoqda...</i>\n<i>Qayta ishga tushirish {} soniya davom etdi</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Sizning botingiz"
            " to'liq yuklandi! {}</b>\n<i>Jami qayta ishga tushirish {} soniya davom"
            " etdi</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Xavfsiz rejim"
            " muvaffaqiyatli yakunlandi! {}</b>\n<i>Qayta ishga tushirish {} soniya"
            " davom etdi</i>"
        ),
        "origin_cfg_doc": "dan yangilanish yuklanadi",
        "btn_restart": "🔄 Qayta ishga tushirish",
        "btn_update": "🧭 Yangilash",
        "restart_confirm": "❓ <b>Haqiqatan ham qayta ishga tushirmoqchimisiz?</b>",
        "secure_boot_confirm": (
            "❓ <b>Haqiqatan ham xavfsiz rejimda qayta ishga tushirmoqchimisiz?</b>"
        ),
        "update_confirm": (
            "❓ <b>Haqiqatan ham yangilamoqchimisiz?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": (
            "🚸 <b>Siz allaqachon eng so'nggi versiyasiz. Yangilamoqchimisiz?</b>"
        ),
        "cancel": "🚫 Bekor qilish",
        "_cls_doc": "Foydalanuvchi botini yangilaydi",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>{}"
            " yangilanmoqda...</b>"
        ),
    }

    strings_es = {
        "restarting": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>{} Reiniciando...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>{} Reiniciando...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Descargando la"
            " actualización...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Instalando la"
            " actualización...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Reiniciado con éxito!"
            " {}</b>\n<i>Descargando módulos...</i>\n<i>Reiniciado en {} segundos</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>¡Bot actualizado con"
            " éxito! {}</b>\n<i>Reiniciado en {} segundos</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>¡Modo de arranque"
            " seguro activado! {}</b>\n<i>Reiniciado en {} segundos</i>"
        ),
        "origin_cfg_doc": "Descargar actualización desde",
        "btn_restart": "🔄 Reiniciar",
        "btn_update": "🧭 Actualizar",
        "restart_confirm": "❓ <b>¿Quieres reiniciar?</b>",
        "secure_boot_confirm": (
            "❓ <b>¿Quieres reiniciar en modo de arranque seguro?</b>"
        ),
        "update_confirm": (
            "❓ <b>¿Quieres actualizar?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>Esta es la última versión. ¿Quieres actualizar?</b>",
        "cancel": "🚫 Cancelar",
        "_cls_doc": "El usuario reinicia el bot",
        "lavhost_update": (
            "<emoji document_id=5328274090262275771>✌️</emoji> <b>{}"
            " Actualizando...</b>"
        ),
    }

    strings_kk = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Бастапқы коды</b> <a"
            ' href="{}">бұл жерде</a> қарауға болады'
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Твой {}"
            " перезагружается...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Жаңартуларды"
            " жүктеу...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Жаңартуларды"
            " орнату...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Жаңарту сәтті"
            " аяқталды! {}</b>\n<i>Бірақ модульдер әлі жүктелуде...</i>\n<i>Жаңарту"
            " {} секундқа аяқталды</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Юзербот толық"
            " жүктелді! {}</b>\n<i>Толық жаңарту {} секундқа аяқталды</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Безпеке режимі"
            " аяқталды! {}</b>\n<i>Жаңарту {} секундқа аяқталды</i>"
        ),
        "origin_cfg_doc": "Жаңартуларды жүктеу үшін сілтеме",
        "btn_restart": "🔄 Жаңарту",
        "btn_update": "🧭 Жаңарту",
        "restart_confirm": "❓ <b>Сен жаңартуға сенімдісін бе?</b>",
        "secure_boot_confirm": (
            "❓ <b>Сен бұл бетті безпеке режимінде жаңартуға сенімдісін бе?</b>"
        ),
        "update_confirm": (
            "❓ <b>Сен жаңартуға сенімдісін бе?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": (
            "🚸 <b>Сіздің соңғы нұсқаныңыз бар. Сіз жаңартуға мүмкіндік береді ме?</b>"
        ),
        "cancel": "🚫 Бас тарту",
        "_cls_doc": "Юзерботты жаңарту",
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Сіздің {}"
            " жаңартуға басталды...</b>"
        ),
    }

    strings_tt = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Чыганак кодын <a"
            " href='{}'>монда</a> укып була</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Сезнең {} яңадан"
            " башлана...</b>"
        ),
        "downloading": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Яңартуларны"
            " йөкләү...</b>"
        ),
        "installing": (
            "<emoji document_id=5328274090262275771>🕗</emoji> <b>Яңартулар"
            " урнаштыру...</b>"
        ),
        "success": (
            "<emoji document_id=5326015457155620929>⏱</emoji> <b>Яңарту бетте! {}</b>\n"
            "<i>Ләкин модульләр әле йөкләнә...</i>\n<i>Яңарту {} сек дәвам итте</i>"
        ),
        "full_success": (
            "<emoji document_id=5301096082674032190>👍</emoji> <b>Юзербот тулысынча"
            " йөкләнгән! {}</b>\n<i>Тулы яңадан башлау {} сек дәвам итте</i>"
        ),
        "secure_boot_complete": (
            "<emoji document_id=5472308992514464048>🔐</emoji> <b>Куркынычсыз йөкләү"
            " тәмамланды! {}</b>\n<i>Яңарту {} сек дәвам итте</i>"
        ),
        "origin_cfg_doc": "Яңартулар йөкләнәчәк сылтама",
        "btn_restart": "🔄 Кабызу",
        "btn_update": "🧭 Яңару",
        "restart_confirm": "❓ <b>Ты уверен, что хочешь перезагрузиться?</b>",
        "secure_boot_confirm": "❓ <b>Сез яңадан башларга телисезме?</b>",
        "update_confirm": (
            "❓ <b>Сез яңартырга телисезме?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>Сезнең соңгы версиягез бар. Яңарту мәҗбүриме?</b>",
        "cancel": "🚫 Бетерү",
        "_cls_doc": "Юзерботны яңарта",
        "lavhost_update": (
            "<emoji document_id=5328274090262275771>✌️</emoji> <b>Сезнең {}"
            " яңартыла...</b>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "GIT_ORIGIN_URL",
                "https://github.com/hikariatama/Hikka",
                lambda: self.strings("origin_cfg_doc"),
                validator=loader.validators.Link(),
            )
        )

    @loader.owner
    @loader.command(
        ru_doc="Перезагружает юзербот",
        it_doc="Riavvia il bot",
        de_doc="Startet den Userbot neu",
        tr_doc="Kullanıcı botunu yeniden başlatır",
        uz_doc="Foydalanuvchi botini qayta ishga tushiradi",
        es_doc="Reinicia el bot",
        kk_doc="Жүктеген ботты қайта жүктейді",
    )
    async def restart(self, message: Message):
        """Restarts the userbot"""
        args = utils.get_args_raw(message)
        secure_boot = any(trigger in args for trigger in {"--secure-boot", "-sb"})
        try:
            if (
                "-f" in args
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings(
                        "secure_boot_confirm" if secure_boot else "restart_confirm"
                    ),
                    reply_markup=[
                        {
                            "text": self.strings("btn_restart"),
                            "callback": self.inline_restart,
                            "args": (secure_boot,),
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                )
            ):
                raise
        except Exception:
            await self.restart_common(message, secure_boot)

    async def inline_restart(self, call: InlineCall, secure_boot: bool = False):
        await self.restart_common(call, secure_boot=secure_boot)

    async def process_restart_message(self, msg_obj: typing.Union[InlineCall, Message]):
        self.set(
            "selfupdatemsg",
            msg_obj.inline_message_id
            if hasattr(msg_obj, "inline_message_id")
            else f"{utils.get_chat_id(msg_obj)}:{msg_obj.id}",
        )

    async def restart_common(
        self,
        msg_obj: typing.Union[InlineCall, Message],
        secure_boot: bool = False,
    ):
        if (
            hasattr(msg_obj, "form")
            and isinstance(msg_obj.form, dict)
            and "uid" in msg_obj.form
            and msg_obj.form["uid"] in self.inline._units
            and "message" in self.inline._units[msg_obj.form["uid"]]
        ):
            message = self.inline._units[msg_obj.form["uid"]]["message"]
        else:
            message = msg_obj

        if secure_boot:
            self._db.set(loader.__name__, "secure_boot", True)

        msg_obj = await utils.answer(
            msg_obj,
            self.strings("restarting_caption").format(
                utils.get_platform_emoji()
                if self._client.hikka_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "Hikka"
            ),
        )

        await self.process_restart_message(msg_obj)

        self.set("restart_ts", time.time())

        await self._db.remote_force_save()

        if "LAVHOST" in os.environ:
            os.system("lavhost restart")
            return

        with contextlib.suppress(Exception):
            await main.hikka.web.stop()

        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)

        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()

        await message.client.disconnect()
        restart()

    async def download_common(self):
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            r = origin.pull()
            new_commit = repo.head.commit
            for info in r:
                if info.old_commit:
                    for d in new_commit.diff(info.old_commit):
                        if d.b_path == "requirements.txt":
                            return True
            return False
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)
            return False

    @staticmethod
    def req_common():
        # Now we have downloaded new code, install requirements
        logger.debug("Installing new requirements...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(
                        os.path.dirname(utils.get_base_dir()),
                        "requirements.txt",
                    ),
                    "--user",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            logger.exception("Req install failed")

    @loader.owner
    @loader.command(
        ru_doc="Скачивает обновления юзербота",
        it_doc="Scarica gli aggiornamenti del bot",
        de_doc="Lädt Updates für den Userbot herunter",
        tr_doc="Userbot güncellemelerini indirir",
        uz_doc="Userbot yangilanishlarini yuklaydi",
        es_doc="Descarga las actualizaciones del bot",
        kk_doc="Жүйе жаңартуларын жүктейді",
    )
    async def update(self, message: Message):
        """Downloads userbot updates"""
        try:
            args = utils.get_args_raw(message)
            current = utils.get_git_hash()
            upcoming = next(
                git.Repo().iter_commits(f"origin/{version.branch}", max_count=1)
            ).hexsha
            if (
                "-f" in args
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("update_confirm").format(
                        current, current[:8], upcoming, upcoming[:8]
                    )
                    if upcoming != current
                    else self.strings("no_update"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_update"),
                            "callback": self.inline_update,
                        },
                        {"text": self.strings("cancel"), "action": "close"},
                    ],
                )
            ):
                raise
        except Exception:
            await self.inline_update(message)

    async def inline_update(
        self,
        msg_obj: typing.Union[InlineCall, Message],
        hard: bool = False,
    ):
        # We don't really care about asyncio at this point, as we are shutting down
        if hard:
            os.system(f"cd {utils.get_base_dir()} && cd .. && git reset --hard HEAD")

        try:
            if "LAVHOST" in os.environ:
                msg_obj = await utils.answer(
                    msg_obj,
                    self.strings("lavhost_update").format(
                        "</b><emoji document_id=5192756799647785066>✌️</emoji><emoji"
                        " document_id=5193117564015747203>✌️</emoji><emoji"
                        " document_id=5195050806105087456>✌️</emoji><emoji"
                        " document_id=5195457642587233944>✌️</emoji><b>"
                        if self._client.hikka_me.premium
                        and CUSTOM_EMOJIS
                        and isinstance(msg_obj, Message)
                        else "lavHost"
                    ),
                )
                await self.process_restart_message(msg_obj)
                os.system("lavhost update")
                return

            with contextlib.suppress(Exception):
                msg_obj = await utils.answer(msg_obj, self.strings("downloading"))

            req_update = await self.download_common()

            with contextlib.suppress(Exception):
                msg_obj = await utils.answer(msg_obj, self.strings("installing"))

            if req_update:
                self.req_common()

            await self.restart_common(msg_obj)
        except GitCommandError:
            if not hard:
                await self.inline_update(msg_obj, True)
                return

            logger.critical("Got update loop. Update manually via .terminal")

    @loader.unrestricted
    @loader.command(
        ru_doc="Показать ссылку на исходный код проекта",
        it_doc="Mostra il link al codice sorgente del progetto",
        de_doc="Zeigt den Link zum Quellcode des Projekts an",
        tr_doc="Proje kaynak kodu bağlantısını gösterir",
        uz_doc="Loyihaning manba kodiga havola ko'rsatadi",
        es_doc="Muestra el enlace al código fuente del proyecto",
        kk_doc="Жобаның қайнар кодына сілтеме көрсетеді",
    )
    async def source(self, message: Message):
        """Links the source code of this project"""
        await utils.answer(
            message,
            self.strings("source").format(self.config["GIT_ORIGIN_URL"]),
        )

    async def client_ready(self):
        if self.get("selfupdatemsg") is not None:
            try:
                await self.update_complete()
            except Exception:
                logger.exception("Failed to complete update!")

        if self.get("do_not_create", False):
            return

        try:
            await self._add_folder()
        except Exception:
            logger.exception("Failed to add folder!")

        self.set("do_not_create", True)

    async def _add_folder(self):
        folders = await self._client(GetDialogFiltersRequest())

        if any(getattr(folder, "title", None) == "hikka" for folder in folders):
            return

        try:
            folder_id = (
                max(
                    folders,
                    key=lambda x: x.id,
                ).id
                + 1
            )
        except ValueError:
            folder_id = 2

        try:
            await self._client(
                UpdateDialogFilterRequest(
                    folder_id,
                    DialogFilter(
                        folder_id,
                        title="hikka",
                        pinned_peers=(
                            [
                                await self._client.get_input_entity(
                                    self._client.loader.inline.bot_id
                                )
                            ]
                            if self._client.loader.inline.init_complete
                            else []
                        ),
                        include_peers=[
                            await self._client.get_input_entity(dialog.entity)
                            async for dialog in self._client.iter_dialogs(
                                None,
                                ignore_migrated=True,
                            )
                            if dialog.name
                            in {
                                "hikka-logs",
                                "hikka-onload",
                                "hikka-assets",
                                "hikka-backups",
                                "hikka-acc-switcher",
                                "silent-tags",
                            }
                            and dialog.is_channel
                            and (
                                dialog.entity.participants_count == 1
                                or dialog.entity.participants_count == 2
                                and dialog.name in {"hikka-logs", "silent-tags"}
                            )
                            or (
                                self._client.loader.inline.init_complete
                                and dialog.entity.id
                                == self._client.loader.inline.bot_id
                            )
                            or dialog.entity.id
                            in [
                                1554874075,
                                1697279580,
                                1679998924,
                            ]  # official hikka chats
                        ],
                        emoticon="🐱",
                        exclude_peers=[],
                        contacts=False,
                        non_contacts=False,
                        groups=False,
                        broadcasts=False,
                        bots=False,
                        exclude_muted=False,
                        exclude_read=False,
                        exclude_archived=False,
                    ),
                )
            )
        except Exception:
            logger.critical(
                "Can't create Hikka folder. Possible reasons are:\n"
                "- User reached the limit of folders in Telegram\n"
                "- User got floodwait\n"
                "Ignoring error and adding folder addition to ignore list"
            )

    async def update_complete(self):
        logger.debug("Self update successful! Edit message")
        start = self.get("restart_ts")
        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        msg = self.strings("success").format(utils.ascii_face(), took)
        ms = self.get("selfupdatemsg")

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=self.inline.sanitise_text(msg),
        )

    async def full_restart_complete(self, secure_boot: bool = False):
        start = self.get("restart_ts")

        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        self.set("restart_ts", None)

        ms = self.get("selfupdatemsg")
        msg = self.strings(
            "secure_boot_complete" if secure_boot else "full_success"
        ).format(utils.ascii_face(), took)

        if ms is None:
            return

        self.set("selfupdatemsg", None)

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            await asyncio.sleep(60)
            await self._client.delete_messages(chat_id, message_id)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=self.inline.sanitise_text(msg),
        )
