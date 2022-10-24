#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import atexit
import contextlib
import logging
import os
import subprocess
import sys
import time
import typing

import git
from git import GitCommandError, Repo

from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import DialogFilter, Message
from telethon.extensions.html import CUSTOM_EMOJIS

from .. import loader, utils, main, version

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
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Your {} is"
            " restarting...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Downloading"
            " updates...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Installing"
            " updates...</b>"
        ),
        "success": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Restart successful!"
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
        "lavhost_restart": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Your {} is"
            " restarting...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Your {} is"
            " updating...</b>"
        ),
        "full_success": (
            "<emoji document_id=6323332130579416910>👍</emoji> <b>Userbot is fully"
            " loaded! {}</b>\n<i>Full restart took {}s</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Secure boot completed! {}</b>\n<i>Restart took {}s</i>"
        ),
    }

    strings_ru = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Исходный код можно"
            " прочитать</b> <a href='{}'>здесь</a>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Твоя {}"
            " перезагружается...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Скачивание"
            " обновлений...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Установка"
            " обновлений...</b>"
        ),
        "success": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Перезагрузка"
            " успешна! {}</b>\n<i>Но модули еще загружаются...</i>\n<i>Перезагрузка"
            " заняла {} сек</i>"
        ),
        "full_success": (
            "<emoji document_id=6323332130579416910>👍</emoji> <b>Юзербот полностью"
            " загружен! {}</b>\n<i>Полная перезагрузка заняла {} сек</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Безопасная загрузка завершена! {}</b>\n<i>Перезагрузка заняла {}"
            " сек</i>"
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
            " хочешь обновиться??\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>У тебя последняя версия. Обновиться принудительно?</b>",
        "cancel": "🚫 Отмена",
        "_cls_doc": "Обновляет юзербот",
        "lavhost_restart": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Твой {}"
            " перезагружается...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Твой {}"
            " обновляется...</b>"
        ),
    }

    strings_de = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Der Quellcode kann"
            " hier</b> <a href='{}'>gelesen</a> <b>werden</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Dein {}"
            " wird neugestartet...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Updates"
            " werden heruntergeladen...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Updates"
            " werden installiert...</b>"
        ),
        "success": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Neustart erfolgreich!"
            " {}</b>\n<i>Aber Module werden noch geladen...</i>\n<i>Neustart dauerte {}"
            " Sekunden</i>"
        ),
        "full_success": (
            "<emoji document_id=6323332130579416910>👍</emoji> <b>Dein Userbot ist"
            " vollständig geladen! {}</b>\n<i>Vollständiger Neustart dauerte {}"
            " Sekunden</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Sicherer Bootvorgang abgeschlossen! {}</b>\n<i>Neustart dauerte"
            " {} Sekunden</i>"
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
            " du updaten willst??\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": (
            "🚸 <b>Du hast die neueste Version. Willst du trotzdem updaten?</b>"
        ),
        "cancel": "🚫 Abbrechen",
        "_cls_doc": "Aktualisiert den Userbot",
        "lavhost_restart": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Dein {}"
            " wird neugestartet...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>Dein {}"
            " wird aktualisiert...</b>"
        ),
    }

    strings_tr = {
        "source": (
            "<emoji document_id=5456255401194429832>📖</emoji> <b>Manba kodini shu <a"
            " href='{}'>yerdan</a> oʻqing</b>"
        ),
        "restarting": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{}"
            " yeniden başlatılıyor...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{}"
            " yeniden başlatılıyor...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Güncelleme"
            " indiriliyor...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Güncelleme"
            " yükleniyor...</b>"
        ),
        "success": (
            "<emoji document_id=6321050180095313397>⏱</emoji> <b>Yeniden başlatma"
            " başarılı! {}</b>\n<i>Modüller yükleniyor...</i>\n<i>Yeniden başlatma {}"
            " saniye sürdü</i>"
        ),
        "full_success": (
            "<emoji document_id=6323332130579416910>👍</emoji> <b>Botunuz tamamen"
            " yüklendi! {}</b>\n<i>Toplam yeniden başlatma {} saniye sürdü</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Güvenli mod başarıyla tamamlandı! {}</b>\n<i>Yeniden başlatma {}"
            " saniye sürdü</i>"
        ),
        "origin_cfg_doc": "dan güncelleme indirilecek",
        "btn_restart": "🔄 Yeniden başlat",
        "btn_update": "🧭 Güncelle",
        "restart_confirm": "❓ <b>Gerçekten yeniden başlatmak istiyor musunuz?</b>",
        "secure_boot_confirm": (
            "❓ <b>Gerçekten güvenli modda yeniden başlatmak istiyor musunuz?</b>"
        ),
        "update_confirm": (
            "❓ <b>Gerçekten güncellemek istiyor musunuz??\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>Zaten son sürümünüz. Güncelleme yapmak ister misiniz?</b>",
        "cancel": "🚫 İptal",
        "_cls_doc": "Kullanıcı botunu günceller",
        "lavhost_restart": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{}"
            " yeniden başlatılıyor...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{}"
            " güncelleniyor...</b>"
        ),
    }

    strings_uz = {
        "restarting": (
            "<emoji document_id=5469986291380657759>🕗</emoji> <b>{}"
            " qayta ishga tushirilmoqda...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=5469986291380657759>🕗</emoji> <b>{}"
            " qayta ishga tushirilmoqda...</b>"
        ),
        "downloading": (
            "<emoji document_id=5469986291380657759>🕗</emoji> <b>Yangilanish"
            " yuklanmoqda...</b>"
        ),
        "installing": (
            "<emoji document_id=5469986291380657759>🕗</emoji> <b>Yangilanish"
            " o'rnatilmoqda...</b>"
        ),
        "success": (
            "<emoji document_id=5469986291380657759>⏱</emoji> <b>Qayta ishga tushirish"
            " muvaffaqiyatli yakunlandi! {}</b>\n<i>Modullar"
            " yuklanmoqda...</i>\n<i>Qayta ishga tushirish {} soniya davom etdi</i>"
        ),
        "full_success": (
            "<emoji document_id=5469986291380657759>👍</emoji> <b>Sizning botingiz"
            " to'liq yuklandi! {}</b>\n<i>Jami qayta ishga tushirish {} soniya davom"
            " etdi</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>Xavfsiz rejim muvaffaqiyatli yakunlandi! {}</b>\n<i>Qayta ishga"
            " tushirish {} soniya davom etdi</i>"
        ),
        "origin_cfg_doc": "dan yangilanish yuklanadi",
        "btn_restart": "🔄 Qayta ishga tushirish",
        "btn_update": "🧭 Yangilash",
        "restart_confirm": "❓ <b>Haqiqatan ham qayta ishga tushirmoqchimisiz?</b>",
        "secure_boot_confirm": (
            "❓ <b>Haqiqatan ham xavfsiz rejimda qayta ishga tushirmoqchimisiz?</b>"
        ),
        "update_confirm": (
            "❓ <b>Haqiqatan ham yangilamoqchimisiz??\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": (
            "🚸 <b>Siz allaqachon eng so'nggi versiyasiz. Yangilamoqchimisiz?</b>"
        ),
        "cancel": "🚫 Bekor qilish",
        "_cls_doc": "Foydalanuvchi botini yangilaydi",
        "lavhost_restart": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>{}"
            " qayta ishga tushirilmoqda...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=5469986291380657759>✌️</emoji> <b>{}"
            " yangilanmoqda...</b>"
        ),
    }

    strings_ja = {
        "restarting": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{} 再起動中...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{} 再起動中...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>アップデートをダウンロード中...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>アップデートをインストール中...</b>"
        ),
        "success": (
            "<emoji document_id=6318970114548958978>⏱</emoji> <b>再起動が完了しました!"
            " {}</b>\n<i>モジュールをダウンロード中...</i>\n<i>再起動 {} 秒かかりました</i>"
        ),
        "full_success": (
            "<emoji document_id=6318970114548958978>👍</emoji> <b>あなたのボットは完全に"
            "ダウンロードされました! {}</b>\n<i>再起動 {} 秒かかりました</i>"
        ),
        "secure_boot_complete": "🔒 <b>セキュアモードが完了しました! {}</b>\n<i>再起動 {} 秒かかりました</i>",
        "origin_cfg_doc": "からアップデートをダウンロード",
        "btn_restart": "🔄 再起動",
        "btn_update": "🧭 アップデート",
        "restart_confirm": "❓ <b>本当に再起動しますか？</b>",
        "secure_boot_confirm": "❓ <b>本当にセキュアモードで再起動しますか？</b>",
        "update_confirm": (
            "❓ <b>本当にアップデートしますか？\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>すでに最新バージョンです。アップデートしますか？</b>",
        "cancel": "🚫 キャンセル",
        "_cls_doc": "ユーザーがボットをアップデートします",
        "lavhost_restart": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{} 再起動中...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{} アップデート中...</b>"
        ),
    }

    strings_kr = {
        "restarting": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{} 재시작 중...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{} 재시작 중...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>업데이트 다운로드 중...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>업데이트 설치 중...</b>"
        ),
        "success": (
            "<emoji document_id=6318970114548958978>⏱</emoji> <b>재시작이 완료되었습니다!"
            " {}</b>\n<i>모듈을다운로드 중...</i>\n<i>재시작 {} 초 걸렸습니다</i>"
        ),
        "full_success": (
            "<emoji document_id=6318970114548958978>👍</emoji> <b>당신의 봇은 완전히"
            "다운로드 되었습니다! {}</b>\n<i>재시작 {} 초 걸렸습니다</i>"
        ),
        "secure_boot_complete": "🔒 <b>보안 모드가 완료되었습니다! {}</b>\n<i>재시작 {} 초 걸렸습니다</i>",
        "origin_cfg_doc": "에서 업데이트 다운로드",
        "btn_restart": "🔄 재시작",
        "btn_update": "🧭 업데이트",
        "restart_confirm": "❓ <b>재시작 하시겠습니까?</b>",
        "secure_boot_confirm": "❓ <b>보안 모드로 재시작 하시겠습니까?</b>",
        "update_confirm": (
            "❓ <b>업데이트 하시겠습니까?\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>이미 최신 버전입니다. 업데이트 하시겠습니까?</b>",
        "cancel": "🚫 취소",
        "_cls_doc": "사용자가 봇 업데이트",
        "lavhost_restart": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{} 재시작 중...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{} 업데이트 중...</b>"
        ),
    }

    strings_ar = {
        "restarting": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{}"
            " إعادة التشغيل...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{}"
            " إعادة التشغيل...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>تحميل التحديث...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>تثبيت التحديث...</b>"
        ),
        "success": (
            "<emoji document_id=6318970114548958978>⏱</emoji> <b>تم إعادة التشغيل"
            " بنجاح! {}</b>\n<i>جاري تنزيلالوحدات...</i>\n<i>أستغرق إعادة التشغيل {}"
            " ثانية</i>"
        ),
        "full_success": (
            "<emoji document_id=6318970114548958978>👍</emoji> <b>تم تحميل البوت بنجاح!"
            " {}</b>\n<i>أستغرق إعادة التشغيل {} ثانية</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>تم إكمال وضع الإقلاع الآمن! {}</b>\n<i>أستغرق إعادة التشغيل {}"
            " ثانية</i>"
        ),
        "origin_cfg_doc": "تحميل التحديث من",
        "btn_restart": "🔄 إعادة التشغيل",
        "btn_update": "🧭 تحديث",
        "restart_confirm": "❓ <b>هل تريد إعادة التشغيل؟</b>",
        "secure_boot_confirm": "❓ <b>هل تريد إعادة التشغيل في وضع الإقلاع الآمن؟</b>",
        "update_confirm": (
            "❓ <b>هل تريد تحديث؟\n\n<a"
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a> ⤑ <a'
            ' href="https://github.com/hikariatama/Hikka/commit/{}">{}</a></b>'
        ),
        "no_update": "🚸 <b>هذا هو آخر إصدار. هل تريد تحديث؟</b>",
        "cancel": "🚫 إلغاء",
        "_cls_doc": "المستخدم يعيد تشغيل البوت",
        "lavhost_restart": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{}"
            " إعادة التشغيل...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{} تحديث...</b>"
        ),
    }

    strings_es = {
        "restarting": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{} Reiniciando...</b>"
        ),
        "restarting_caption": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>{} Reiniciando...</b>"
        ),
        "downloading": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Descargando la"
            " actualización...</b>"
        ),
        "installing": (
            "<emoji document_id=6318970114548958978>🕗</emoji> <b>Instalando la"
            " actualización...</b>"
        ),
        "success": (
            "<emoji document_id=6318970114548958978>⏱</emoji> <b>Reiniciado con éxito!"
            " {}</b>\n<i>Descargandomódulos...</i>\n<i>Reiniciado en {} segundos</i>"
        ),
        "full_success": (
            "<emoji document_id=6318970114548958978>👍</emoji> <b>¡Bot actualizado con"
            " éxito! {}</b>\n<i>Reiniciado en {} segundos</i>"
        ),
        "secure_boot_complete": (
            "🔒 <b>¡Modo de arranque seguro activado! {}</b>\n<i>Reiniciado en {}"
            " segundos</i>"
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
        "lavhost_restart": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{} Reiniciando...</b>"
        ),
        "lavhost_update": (
            "<emoji document_id=6318970114548958978>✌️</emoji> <b>{}"
            " Actualizando...</b>"
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
        de_doc="Startet den Userbot neu",
        tr_doc="Kullanıcı botunu yeniden başlatır",
        uz_doc="Foydalanuvchi botini qayta ishga tushiradi",
        ja_doc="ユーザーボットを再起動します",
        kr_doc="사용자 봇을 다시 시작합니다",
        ar_doc="يعيد تشغيل البوت",
        es_doc="Reinicia el bot",
    )
    async def restart(self, message: Message):
        """Restarts the userbot"""
        secure_boot = "--secure-boot" in utils.get_args_raw(message)
        try:
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or "-f" in (utils.get_args_raw(message) or "")
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
                utils.get_platform_emoji(self._client)
                if self._client.hikka_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "Hikka"
            )
            if "LAVHOST" not in os.environ
            else self.strings("lavhost_restart").format(
                '</b><emoji document_id="5192756799647785066">✌️</emoji><emoji'
                ' document_id="5193117564015747203">✌️</emoji><emoji'
                ' document_id="5195050806105087456">✌️</emoji><emoji'
                ' document_id="5195457642587233944">✌️</emoji><b>'
                if self._client.hikka_me.premium
                and CUSTOM_EMOJIS
                and isinstance(msg_obj, Message)
                else "lavHost"
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

        atexit.register(restart, *sys.argv[1:])
        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)

        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()

        await message.client.disconnect()
        sys.exit(0)

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
        de_doc="Lädt Updates für den Userbot herunter",
        tr_doc="Userbot güncellemelerini indirir",
        uz_doc="Userbot yangilanishlarini yuklaydi",
        ja_doc="ユーザーボットのアップデートをダウンロードします",
        kr_doc="유저봇 업데이트를 다운로드합니다",
        ar_doc="يقوم بتحميل تحديثات البوت",
        es_doc="Descarga las actualizaciones del bot",
    )
    async def update(self, message: Message):
        """Downloads userbot updates"""
        try:
            current = utils.get_git_hash()
            upcoming = next(
                git.Repo().iter_commits(f"origin/{version.branch}", max_count=1)
            ).hexsha
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or "-f" in (utils.get_args_raw(message) or "")
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
            return

    @loader.unrestricted
    @loader.command(
        ru_doc="Показать ссылку на исходный код проекта",
        de_doc="Zeigt den Link zum Quellcode des Projekts an",
        tr_doc="Proje kaynak kodu bağlantısını gösterir",
        uz_doc="Loyihaning manba kodiga havola ko'rsatadi",
        ja_doc="プロジェクトのソースコードへのリンクを表示します",
        kr_doc="프로젝트 소스 코드 링크를 표시합니다",
        ar_doc="يعرض رابط مصدر البوت",
        es_doc="Muestra el enlace al código fuente del proyecto",
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
        finally:
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


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )
