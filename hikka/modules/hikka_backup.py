#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import datetime
import io
import json
import logging
import time

from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)


@loader.tds
class HikkaBackupMod(loader.Module):
    """Automatic database backup"""

    strings = {
        "name": "HikkaBackup",
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> creates database backups periodically. You can"
            " change this behavior later.\n\nPlease, select the periodicity of"
            " automatic database backups"
        ),
        "saved": (
            "✅ Backup period saved. You can re-configure it later with"
            " .set_backup_period"
        ),
        "never": (
            "✅ I will not make automatic backups. You can re-configure it later with"
            " .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Specify correct backup period in hours, or `0` to disable</b>"
        ),
    }

    strings_ru = {
        "period": (
            "⌚️ <b>Юнит «ALPHA»</b> создает регулярные резервные копии. Эти настройки"
            " можно изменить позже.\n\nПожалуйста, выберите периодичность резервного"
            " копирования"
        ),
        "saved": (
            "✅ Периодичность сохранена! Ее можно изменить с помощью .set_backup_period"
        ),
        "never": (
            "✅ Я не буду делать автоматические резервные копии. Можно отменить"
            " используя .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Укажи правильную периодичность в часах, или `0` для отключения</b>"
        ),
    }

    strings_de = {
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> erstellt regelmäßige Backups. Diese Einstellungen"
            " können später geändert werden.\n\nBitte wählen Sie die Periodizität"
            " des Backups"
        ),
        "saved": (
            "✅ Periodizität gespeichert! Sie können es mit .set_backup_period ändern"
        ),
        "never": (
            "✅ Ich werde keine automatischen Backups erstellen. Sie können es mit"
            " .set_backup_period ändern"
        ),
        "invalid_args": (
            "🚫 <b>Geben Sie die korrekte Periodizität in Stunden an, oder `0` zum"
            " Deaktivieren</b>"
        ),
    }

    strings_tr = {
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> otomatik olarak yedekler oluşturur. Bu ayarları"
            " daha sonra değiştirebilirsiniz.\n\nLütfen otomatik yedekleme"
            " periyodunu seçin"
        ),
        "saved": (
            "✅ Yedekleme periyodu kaydedildi! .set_backup_period ile"
            " değiştirebilirsiniz"
        ),
        "never": (
            "✅ Otomatik yedekleme yapmayacağım. .set_backup_period ile"
            " değiştirebilirsiniz"
        ),
        "invalid_args": (
            "🚫 <b>Geçerli bir yedekleme periyodu saat cinsinden belirtin, veya `0` ile"
            " devre dışı bırakın</b>"
        ),
    }

    strings_hi = {
        "period": (
            "⌚️ <b>यूनिट «ALPHA»</b> स्वचालित रूप से बैकअप बनाता है। आप इस विशेषता को"
            " बाद में बदल सकते हैं।\n\nकृपया बैकअप की अनुमति देने के लिए एक अनुमति दें"
        ),
        "saved": (
            "✅ बैकअप अनुमति सहेजी गई! आप इसे .set_backup_period के साथ बदल सकते हैं"
        ),
        "never": (
            "✅ मैं स्वचालित रूप से बैकअप नहीं बनाऊंगा। आप इसे .set_backup_period के साथ"
            " बदल सकते हैं"
        ),
        "invalid_args": (
            "🚫 <b>सही बैकअप अनुमति देने के लिए एक घंटे में दर दर्ज करें, या इसे अक्षम"
            " करने के लिए `0` दर्ज करें</b>"
        ),
    }

    strings_uz = {
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> avtomatik ravishda e'lon qiladi. Ushbu sozlamalarni"
            " keyinroq o'zgartirishingiz mumkin.\n\nIltimos, avtomatik e'lon qilish"
            " davom ettirish tartibini tanlang"
        ),
        "saved": (
            "✅ E'lon davom ettirish tartibi saqlandi! Uni .set_backup_period orqali"
            " o'zgartirishingiz mumkin"
        ),
        "hech qachon": (
            "✅ Avtomatik zahira nusxasini yaratmayman. Uni .set_backup_period bilan"
            " o'zgartirishingiz mumkin"
        ),
        "invalid_args": (
            '🚫 <b>Yaroqli zaxira muddatini soat yoki "0" bilan belgilang o\'chirish</b>'
        ),
    }

    async def client_ready(self):
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self.tg_id,
                photo="https://github.com/hikariatama/assets/raw/master/unit_alpha.png",
                caption=self.strings("period"),
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {
                                "text": f"🕰 {i} h",
                                "callback": self._set_backup_period,
                                "args": (i,),
                            }
                            for i in {1, 2, 4, 6, 8, 12, 24, 48, 168}
                        ],
                        3,
                    )
                    + [
                        [
                            {
                                "text": "🚫 Never",
                                "callback": self._set_backup_period,
                                "args": (0,),
                            }
                        ]
                    ]
                ),
            )

        self._backup_channel, _ = await utils.asset_channel(
            self._client,
            "hikka-backups",
            "📼 Your database backups will appear there",
            silent=True,
            archive=True,
            avatar="https://github.com/hikariatama/assets/raw/master/hikka-backups.png",
            _folder="hikka",
        )

        self.handler.start()

    async def _set_backup_period(self, call: BotInlineCall, value: int):
        if not value:
            self.set("period", "disabled")
            await call.answer(self.strings("never"), show_alert=True)
            await call.delete()
            return

        self.set("period", value * 60 * 60)
        self.set("last_backup", round(time.time()))

        await call.answer(self.strings("saved"), show_alert=True)
        await call.delete()

    @loader.command(
        ru_doc="<время в часах> - Установить частоту бэкапов",
        de_doc="<Stunden> - Setze die Backup-Frequenz",
        tr_doc="<saat cinsinden zaman> - Yedekleme periyodunu ayarla",
        hi_doc="<घंटों में समय> - बैकअप अनुमति सेट करें",
        uz_doc="<soatda vaqt> - E'lon tartibini belgilash",
    )
    async def set_backup_period(self, message: Message):
        """<time in hours> - Change backup frequency"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit() or int(args) not in range(200):
            await utils.answer(message, self.strings("invalid_args"))
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(message, f"<b>{self.strings('never')}</b>")
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(message, f"<b>{self.strings('saved')}</b>")

    @loader.loop(interval=1)
    async def handler(self):
        try:
            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            if self.get("period") == "disabled":
                raise loader.StopLoop

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
            backup.name = "hikka-db-backup-{}.json".format(
                getattr(datetime, "datetime", datetime).now().strftime("%d-%m-%Y-%H-%M")
            )

            await self._client.send_file(self._backup_channel, backup)
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("HikkaBackup failed")
            await asyncio.sleep(60)
