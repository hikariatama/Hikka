#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib

import git

from .. import loader, utils, version
from ..inline.types import InlineCall


@loader.tds
class UpdateNotifierMod(loader.Module):
    """Tracks latest Hikka releases, and notifies you, if update is required"""

    strings = {
        "name": "UpdateNotifier",
        "update_required": (
            "🌘 <b>Hikka Update available!</b>\n\nNew Hikka version released.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 And {} more...</b></i>",
        "_cfg_doc_disable_notifications": "Disable update notifications",
        "latest_disabled": "Notifications about the latest update have been suppressed",
        "update": "🔄 Update",
        "ignore": "🚫 Ignore",
    }

    strings_ru = {
        "update_required": (
            "🌘 <b>Доступно обновление Hikka!</b>\n\nОпубликована новая версия Hikka.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 И еще {}...</b></i>",
        "_cfg_doc_disable_notifications": "Отключить уведомления об обновлениях",
        "latest_disabled": "Уведомления о последнем обновлении были отключены",
        "update": "🔄 Обновить",
        "ignore": "🚫 Игнорировать",
    }

    strings_de = {
        "update_required": (
            "🌘 <b>Hikka Update verfügbar!</b>\n\nNeue Hikka Version veröffentlicht.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 Und {} mehr...</b></i>",
        "_cfg_doc_disable_notifications": "Deaktiviere Update Benachrichtigungen",
        "latest_disabled": (
            "Benachrichtigungen über das letzte Update wurden unterdrückt"
        ),
        "update": "🔄 Update",
        "ignore": "🚫 Ignorieren",
    }

    strings_uz = {
        "update_required": (
            "🌘 <b>Hikka yangilash mavjud!</b>\n\nYangi Hikka versiyasi chiqdi.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 Va {} boshqa...</b></i>",
        "_cfg_doc_disable_notifications": "Yangilash xabarlarini o'chirish",
        "latest_disabled": "Yangi yangilash haqida xabarlar o'chirildi",
        "update": "🔄 Yangilash",
        "ignore": "🚫 E'tiborsiz qoldirish",
    }

    strings_tr = {
        "update_required": (
            "🌘 <b>Hikka güncellemesi mevcut!</b>\n\nYeni bir Hikka sürümü"
            " yayınlandı.\n🔮 <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 Ve {} daha fazlası...</b></i>",
        "_cfg_doc_disable_notifications": "Güncelleme bildirimlerini devre dışı bırak",
        "latest_disabled": "Son güncelleme hakkında bildirimler engellendi",
        "update": "🔄 Güncelle",
        "ignore": "🚫 Yoksay",
    }

    strings_ja = {
        "update_required": (
            "🌘 <b>Hikkaの更新があります！</b>\n新しいHikkaバージョンがリリースされました。\n🔮 <b>Hikka <s>{}</s> ->"
            " {}</b>\n{}"
        ),
        "more": "\n<i><b>🎥 そして{}も...</b></i>",
        "_cfg_doc_disable_notifications": "更新通知を無効にする",
        "latest_disabled": "最新の更新に関する通知が抑制されました",
        "update": "🔄 更新",
        "ignore": "🚫 無視する",
    }

    strings_kr = {
        "update_required": (
            "🌘 <b>Hikka 업데이트가 있습니다!</b>\n새로운 Hikka 버전이 출시되었습니다.\n🔮 <b>Hikka <s>{}</s>"
            " -> {}</b>\n{}"
        ),
        "more": "\n<i><b>🎥 그리고 {} 더...</b></i>",
        "_cfg_doc_disable_notifications": "업데이트 알림 비활성화",
        "latest_disabled": "최신 업데이트에 대한 알림이 비활성화되었습니다",
        "update": "🔄 업데이트",
        "ignore": "🚫 무시",
    }

    strings_ar = {
        "update_required": (
            "🌘 <b>يوجد تحديث لـ Hikka!</b>\n\nتم إصدار إصدار جديد من Hikka.\n🔮"
            " <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 و {} أكثر...</b></i>",
        "_cfg_doc_disable_notifications": "تعطيل إشعارات التحديث",
        "latest_disabled": "تم تعطيل إشعارات آخر تحديث",
        "update": "🔄 تحديث",
        "ignore": "🚫 تجاهل",
    }

    strings_es = {
        "update_required": (
            "🌘 <b>¡Actualización de Hikka disponible!</b>\n\nSe ha publicado una nueva"
            " versión de Hikka.\n🔮 <b>Hikka <s>{}</s> -> {}</b>\n\n{}"
        ),
        "more": "\n<i><b>🎥 Y {} más...</b></i>",
        "_cfg_doc_disable_notifications": "Desactivar notificaciones de actualización",
        "latest_disabled": "Notificaciones de última actualización desactivadas",
        "update": "🔄 Actualizar",
        "ignore": "🚫 Ignorar",
    }

    _notified = None

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "disable_notifications",
                doc=lambda: self.strings("_cfg_doc_disable_notifications"),
                validator=loader.validators.Boolean(),
            )
        )

    def get_changelog(self) -> str:
        try:
            repo = git.Repo()

            for remote in repo.remotes:
                remote.fetch()

            if not (
                diff := repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            ):
                return False
        except Exception:
            return False

        res = "\n".join(
            f"<b>{commit.split()[0]}</b>:"
            f" <i>{utils.escape_html(' '.join(commit.split()[1:]))}</i>"
            for commit in diff.splitlines()[:10]
        )

        if diff.count("\n") >= 10:
            res += self.strings("more").format(len(diff.splitlines()) - 10)

        return res

    def get_latest(self) -> str:
        try:
            return list(
                git.Repo().iter_commits(f"origin/{version.branch}", max_count=1)
            )[0].hexsha
        except Exception:
            return ""

    async def client_ready(self):
        try:
            git.Repo()
        except Exception as e:
            raise loader.LoadError("Can't load due to repo init error") from e

        self._markup = lambda: self.inline.generate_markup(
            [
                {"text": self.strings("update"), "data": "hikka_update"},
                {"text": self.strings("ignore"), "data": "hikka_upd_ignore"},
            ]
        )

        self.poller.start()

    @loader.loop(interval=60)
    async def poller(self):
        if self.config["disable_notifications"] or not self.get_changelog():
            return

        self._pending = self.get_latest()

        if (
            self.get("ignore_permanent", False)
            and self.get("ignore_permanent") == self._pending
        ):
            await asyncio.sleep(60)
            return

        if self._pending not in [utils.get_git_hash(), self._notified]:
            m = await self.inline.bot.send_message(
                self.tg_id,
                self.strings("update_required").format(
                    utils.get_git_hash()[:6],
                    '<a href="https://github.com/hikariatama/Hikka/compare/{}...{}">{}</a>'
                    .format(
                        utils.get_git_hash()[:12],
                        self.get_latest()[:12],
                        self.get_latest()[:6],
                    ),
                    self.get_changelog(),
                ),
                disable_web_page_preview=True,
                reply_markup=self._markup(),
            )

            self._notified = self._pending
            self.set("ignore_permanent", False)

            await self._delete_all_upd_messages()

            self.set("upd_msg", m.message_id)

    async def _delete_all_upd_messages(self):
        for client in self.allclients:
            with contextlib.suppress(Exception):
                await client.loader.inline.bot.delete_message(
                    client.tg_id,
                    client.loader.db.get("UpdateNotifierMod", "upd_msg"),
                )

    @loader.callback_handler()
    async def update(self, call: InlineCall):
        """Process update buttons clicks"""
        if call.data not in {"hikka_update", "hikka_upd_ignore"}:
            return

        if call.data == "hikka_upd_ignore":
            self.set("ignore_permanent", self.get_latest())
            await call.answer(self.strings("latest_disabled"))
            return

        await self._delete_all_upd_messages()

        with contextlib.suppress(Exception):
            await call.delete()

        await self.allmodules.commands["update"](
            await self._client.send_message(
                self.inline.bot_username,
                f"<code>{self.get_prefix()}update --force</code>",
            )
        )
