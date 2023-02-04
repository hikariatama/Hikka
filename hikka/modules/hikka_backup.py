# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

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

    strings_fr = {
        "period": (
            "⌚️ <b>Unité «ALPHA»</b> crée des sauvegardes régulières. Ces paramètres"
            " peuvent être modifiés ultérieurement.\n\nVeuillez choisir la périodicité"
            " de sauvegarde"
        ),
        "saved": (
            "✅ La périodicité a été enregistrée! Il peut être modifié en utilisant"
            " .set_backup_period"
        ),
        "never": (
            "✅ Je ne vais pas faire des sauvegardes automatiques. Peut être annulé"
            " en utilisant .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Indiquez la périodicité correcte en heures, ou `0` pour"
            " désactiver</b>"
        ),
    }

    strings_it = {
        "period": (
            "⌚️ <b>Unità «ALPHA»</b> crea backup del database periodicamente. Puoi"
            " modificare questo comportamento in seguito.\n\nPer favore, seleziona"
            " la periodicità dei backup automatici"
        ),
        "saved": (
            "✅ Periodo di backup salvato. Puoi modificarlo in seguito con"
            " .set_backup_period"
        ),
        "never": (
            "✅ Non farò backup automatici. Puoi modificarlo in seguito con"
            " .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Specifica il periodo di backup corretto in ore, o `0` per"
            " disabilitarlo</b>"
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
            "⌚️ <b>Unit «ALPHA»</b> otomatik olarak yedekler oluşturur. Ayarlarını"
            " daha sonradan değiştirebilirsiniz.\n\nLütfen otomatik yedekleme"
            " için periyot seçin"
        ),
        "saved": (
            "✅ Yedekleme periyodu kaydedildi! .set_backup_period komutu ile"
            " daha sonradan tekrar değiştirebilirsin"
        ),
        "never": (
            "✅ Otomatik yedekleme yapmayacağım. .set_backup_period komutu ile"
            " daha sonradan tekrar değiştirebilirsin"
        ),
        "invalid_args": (
            "🚫 <b>Geçerli bir yedekleme periyodunu saat cinsinden belirtin, ya da `0`"
            " ile devre dışı bırakın</b>"
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

    strings_es = {
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> crea automáticamente copias de seguridad. Puede"
            " cambiar estos ajustes más tarde.\n\nPor favor, seleccione el período de"
            " copia de seguridad"
        ),
        "saved": (
            "✅ ¡Se ha guardado el período de copia de seguridad! Puede cambiarlo"
            " con .set_backup_period más tarde"
        ),
        "never": (
            "✅ No crear copias de seguridad automáticamente. Puede cambiarlo"
            " con .set_backup_period más tarde"
        ),
        "invalid_args": (
            "🚫 <b>Por favor, introduzca un período de copia de seguridad correcto en"
            " horas, o `0` para desactivarlo</b>"
        ),
    }

    strings_kk = {
        "period": (
            "⌚️ <b>Unit «ALPHA»</b> автоматты резервтік көшірмелер жасайды. Бұл"
            " параметрлерді кейінірек өзгерте аласыз.\n\nӨтініш, резервтік көшірмелер"
            " қайдағы кезеңдерде жасалады"
        ),
        "saved": (
            "✅ Резервтік көшірмелер қайдағы кезеңдерде жасалады! Бұл параметрлерді"
            " .set_backup_period командасымен кейінірек өзгерте аласыз"
        ),
        "never": (
            "✅ Автоматты резервтік көшірмелер жасауға болмайды. Бұл параметрлерді"
            " .set_backup_period командасымен кейінірек өзгерте аласыз"
        ),
        "invalid_args": (
            "🚫 <b>Жарамды резервтік көшірмелер қайдағы кезеңдерде жасалады, немесе"
            " өшіріледі</b>"
        ),
    }

    strings_tt = {
        "period": (
            "⌚️ <b>«ALPHA» берәмлеге</b> регуляр резервлар тудыра."
            " Бу көйләүләрне соңрак үзгәртергә мөмкин."
            "\n\nЗинһар, резерв ешлыкны сайлагыз"
        ),
        "saved": "✅ Вакытлылык сакланган! Аны үзгәртеп була .set_backup_period",
        "never": (
            "✅ Мин автоматик резерв ясамыйм. Аны кулланып юкка"
            " чыгарырга мөмкин .set_backup_period"
        ),
        "invalid_args": (
            "🚫 <b>Сәгатьләрдә дөрес ешлыкны күрсәтегез, яки сүндерү өчен 0</b>"
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
                            for i in [1, 2, 4, 6, 8, 12, 24, 48, 168]
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
            "📼 Your database backups will appear here",
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
        fr_doc="<heures> - Définir la fréquence des sauvegardes",
        it_doc="<tempo in ore> - Imposta la frequenza dei backup",
        de_doc="<Stunden> - Setze die Backup-Frequenz",
        tr_doc="<saat cinsinden zaman> - Yedekleme periyodunu ayarla",
        uz_doc="<soatda vaqt> - E'lon tartibini belgilash",
        es_doc="<horas> - Establecer la frecuencia de copia de seguridad",
        kk_doc="<сағатты уақыт> - Резервтік көшірмелер қайдағы кезеңдерде жасалады",
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
            if self.get("period") == "disabled":
                raise loader.StopLoop

            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
            backup.name = f'hikka-db-backup-{getattr(datetime, "datetime", datetime).now().strftime("%d-%m-%Y-%H-%M")}.json'

            await self._client.send_file(self._backup_channel, backup)
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("HikkaBackup failed")
            await asyncio.sleep(60)
