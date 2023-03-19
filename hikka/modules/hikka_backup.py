# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import datetime
import io
import json
import logging
import os
import time
import zipfile
from pathlib import Path

from hikkatl.tl.types import Message

from .. import loader, utils
from ..inline.types import BotInlineCall

logger = logging.getLogger(__name__)


@loader.tds
class HikkaBackupMod(loader.Module):
    """Handles database and modules backups"""

    p = "<emoji document_id=5469718869536940860>👆</emoji>"
    e = "<emoji document_id=5312526098750252863>🚫</emoji>"
    r = "<emoji document_id=5774134533590880843>🔄</emoji>"
    m = "<emoji document_id=5431736674147114227>🗂</emoji>"

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
        "backup_caption": (
            f"{p} <b>This is your database backup. Do not give it to anyone, it"
            " contains personal info. If you need to restore it, you can use</b>"
            " <code>{prefix}restoredb</code> <b>in reply to this file.</b>"
        ),
        "reply_to_file": f"{e} <b>Reply to .json or .zip file</b>",
        "db_restored": f"{r} <b>Database updated, restarting...</b>",
        "modules_backup": f"{m} <b>Backup of modules ({{}})</b>",
        "mods_restored": f"{r} <b>Mods restored, restarting</b>",
        "backup_sent": f"{m} <b>Backup has been sent to saved messages</b>",
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
        "backup_caption": (
            f"{p} <b>Это твоя резервная копия базы данных. Не передавай ее никому, она"
            " содержит личную информацию. Если тебе нужно ее восстановить,"
            " используй</b> <code>{prefix}restoredb</code> <b>в ответ на этот"
            " файл.</b>"
        ),
        "reply_to_file": f"{e} <b>Ответь на .json или .zip файл</b>",
        "db_restored": f"{r} <b>База данных обновлена, перезапуск...</b>",
        "modules_backup": f"{m} <b>Резервная копия модулей ({{}})</b>",
        "mods_restored": f"{r} <b>Модули восстановлены, перезапуск</b>",
        "backup_sent": f"{m} <b>Резервная копия отправлена в сохраненные сообщения</b>",
        "_cls_doc": "Обрабатывает резервные копии базы данных и модулей",
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
        "backup_caption": (
            f"{p} <b>Ceci est votre sauvegarde de la base de données. Ne le donnez"
            " à personne, il contient des informations personnelles. Si vous avez"
            " besoin de le restaurer, vous pouvez utiliser</b> <code>{prefix}"
            "restoredb</code> <b>en réponse à ce fichier.</b>"
        ),
        "reply_to_file": f"{e} <b>Répondre à un fichier .json ou .zip</b>",
        "db_restored": f"{r} <b>Base de données mise à jour, redémarrage...</b>",
        "modules_backup": f"{m} <b>Sauvegarde des modules ({{}})</b>",
        "mods_restored": f"{r} <b>Modules restaurés, redémarrage</b>",
        "backup_sent": f"{m} <b>Sauvegarde envoyée aux messages enregistrés</b>",
        "_cls_doc": "Gère les sauvegardes de la base de données et des modules",
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
        "backup_caption": (
            f"{p} <b>Questo è il tuo backup del database. Non condividerlo con"
            " nessuno, contiene informazioni personali. Se hai bisogno di"
            " ripristinarlo, puoi usare</b> <code>{prefix}restoredb</code> <b>in"
            " risposta a questo file.</b>"
        ),
        "reply_to_file": f"{e} <b>Rispondi a un file .json o .zip</b>",
        "db_restored": f"{r} <b>Database aggiornato, riavvio...</b>",
        "modules_backup": f"{m} <b>Backup dei moduli ({{}})</b>",
        "mods_restored": f"{r} <b>Moduli ripristinati, riavvio</b>",
        "backup_sent": f"{m} <b>Backup inviato ai messaggi salvati</b>",
        "_cls_doc": "Gestisce i backup del database e dei moduli",
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
        "backup_caption": (
            f"{p} <b>Dies ist dein Backup der Datenbank. Teile es niemandem mit, es"
            " enthält persönliche Informationen. Wenn du es wiederherstellen"
            " musst, kannst du</b> <code>{prefix}restoredb</code> <b>in Antwort"
            " auf diese Datei verwenden.</b>"
        ),
        "reply_to_file": f"{e} <b>Antworte auf eine .json oder .zip Datei</b>",
        "db_restored": f"{r} <b>Datenbank aktualisiert, Neustart...</b>",
        "modules_backup": f"{m} <b>Modul-Backup ({{}})</b>",
        "mods_restored": f"{r} <b>Module wiederhergestellt, Neustart</b>",
        "backup_sent": f"{m} <b>Backup an gespeicherte Nachrichten gesendet</b>",
        "_cls_doc": "Verwaltet Backups der Datenbank und Module",
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
        "backup_caption": (
            f"{p} <b>Bu, veritabanının yedeğidir. Kimseyle paylaşmayın, kişisel"
            " bilgiler içerir. Geri yüklemek istediğinizde</b>"
            " <code>{prefix}restoredb</code> <b>komutunu bu dosyaya yanıt olarak"
            " kullanabilirsiniz.</b>"
        ),
        "reply_to_file": f"{e} <b>Bir .json veya .zip dosyasına yanıt verin</b>",
        "db_restored": f"{r} <b>Veritabanı güncellendi, yeniden başlatılıyor...</b>",
        "modules_backup": f"{m} <b>Modül yedeği ({{}})</b>",
        "mods_restored": f"{r} <b>Modüller geri yüklendi, yeniden başlatılıyor</b>",
        "backup_sent": f"{m} <b>Yedek kaydedilen mesajlara gönderildi</b>",
        "_cls_doc": "Veritabanı ve modüllerin yedeklerini yönetir",
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
        "backup_caption": (
            f"{p} <b>Bu sizning ma'lumotlar bazasining zahira nusxasi. Uni hech qachon"
            " boshqa shaxs bilan baham ko'rsatmasangiz, shaxsiy ma'lumotlar"
            " mavjud. Siz uni qayta tiklash uchun, uni</b> <code>{prefix}"
            "restoredb</code> <b>buyruqini ushbu faylga javob qilib belgilashingiz"
            " mumkin.</b>"
        ),
        "reply_to_file": f"{e} <b>Bir .json yoki .zip fayliga javob qiling</b>",
        "db_restored": (
            f"{r} <b>Ma'lumotlar bazasi yangilandi, qayta ishga tushirilmoqda...</b>"
        ),
        "modules_backup": f"{m} <b>Modul zahira nusxasi ({{}})</b>",
        "mods_restored": (
            f"{r} <b>Modullar qayta tiklandi, qayta ishga tushirilmoqda</b>"
        ),
        "backup_sent": f"{m} <b>Zahira nusxasi saqlangan xabarlarga yuborildi</b>",
        "_cls_doc": "Ma'lumotlar bazasi va modullar zahira nusxalarini boshqaradi",
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
        "backup_caption": (
            f"{p} <b>Esto es una copia de seguridad de su base de datos. No lo comparta"
            " con nadie, contiene información personal. Puede usar el comando</b>"
            " <code>{prefix}restoredb</code> <b>en respuesta a este archivo para"
            " restaurarlo.</b>"
        ),
        "reply_to_file": f"{e} <b>Responda a un archivo .json o .zip</b>",
        "db_restored": f"{r} <b>La base de datos se ha actualizado, reiniciando...</b>",
        "modules_backup": f"{m} <b>Copia de seguridad de los módulos ({{}})</b>",
        "mods_restored": f"{r} <b>Módulos restaurados, reiniciando</b>",
        "backup_sent": (
            f"{m} <b>La copia de seguridad se ha enviado a los mensajes guardados</b>"
        ),
        "_cls_doc": "Administra las copias de seguridad de la base de datos y los",
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
        "backup_caption": (
            f"{p} <b>Бұл сіздің деректер базасыңыздың резервтік көшірмесі. Оны басқа"
            " адаммен бөліспесеңіз, сіздің жеке деректеріңіз бар. Оны қалпына келтіру"
            " үшін, оны</b> <code>{prefix}restoredb</code> <b>командасымен жауап"
            " беріп, оны қалпына келтіріңіз.</b>"
        ),
        "reply_to_file": (
            f"{e} <b>Жауап берілген файлыңыз .json немесе .zip болуы керек</b>"
        ),
        "db_restored": (
            f"{r} <b>Деректер базасы жаңартылды, қайта іске қосылымын...</b>"
        ),
        "modules_backup": f"{m} <b>Модульдердің резервтік көшірмесі ({{}})</b>",
        "mods_restored": (
            f"{r} <b>Модульдер қалпына келтірілді, қайта іске қосылымын</b>"
        ),
        "backup_sent": f"{m} <b>Резервтік көшірме сақталған хабарларға жіберілді</b>",
        "_cls_doc": "Деректер базасы мен модульдердің резервтік көшірмелерін",
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
        "backup_caption": (
            f"{p} <b>Бу сезнең мәгълүмат базасының резерв көшәрмәсе. Егер башка"
            " берсәгез, сезнең шәхси мәгълүматыңыз бар. Шуны калпына келтерү өчен,"
            " шуны</b> <code>{prefix}restoredb</code> <b>командасында җавап биреп,"
            " калпына келтерегез.</b>"
        ),
        "reply_to_file": f"{e} <b>Җавап бирелгән файл .json яки .zip булырга тиеш</b>",
        "db_restored": f"{r} <b>Мәгълүмат базасы яңартылды, җибәрү башкаруны...</b>",
        "modules_backup": f"{m} <b>Модульләрнең резерв көшәрмәсе ({{}})</b>",
        "mods_restored": f"{r} <b>Модульләр калпына келтелде, җибәрү башкаруны</b>",
        "backup_sent": f"{m} <b>Резерв көшәрмә сакланган хәбәрләргә җибәрелде</b>",
        "_cls_doc": "Мәгълүмат базасы мен модульләрнең резерв көшәрмәләре",
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
        tt_doc="<сәгатьләр вакыты> - Резерв ешлыкны куегыз",
    )
    async def set_backup_period(self, message: Message):
        """<time in hours> - Change backup frequency"""
        if (
            not (args := utils.get_args_raw(message))
            or not args.isdigit()
            or int(args) not in range(200)
        ):
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

            backup = io.BytesIO(json.dumps(self._db).encode())
            backup.name = (
                f"hikka-db-backup-{datetime.datetime.now():%d-%m-%Y-%H-%M}.json"
            )

            await self._client.send_file(self._backup_channel, backup)
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("HikkaBackup failed")
            await asyncio.sleep(60)

    @loader.command(
        ru_doc="Создать бэкап базы данных [будет отправлено в лс]",
        fr_doc="Créer une sauvegarde de la base de données [sera envoyé en mp]",
        it_doc="Crea un backup del database [viene inviato in pm]",
        de_doc="Erstelle eine Datenbank-Sicherung [wird in pm gesendet]",
        tr_doc="Veritabanı yedeğini oluştur [pm olarak gönderilecek]",
        uz_doc="Ma'lumotlar bazasini e'lon qilish [pm ga jo'natiladi]",
        es_doc="Crear copia de seguridad de la base de datos [se enviará en pm]",
        kk_doc="Деректер базасын резервтік көшіру [pm жіберіледі]",
        tt_doc="Мәгълүмат базасын резервтә күчер [pm күчерелә]",
    )
    async def backupdb(self, message: Message):
        """Create database backup [will be sent in pm]"""
        txt = io.BytesIO(json.dumps(self._db).encode())
        txt.name = f"db-backup-{datetime.datetime.now():%d-%m-%Y-%H-%M}.json"
        await self._client.send_file(
            "me",
            txt,
            caption=self.strings("backup_caption").format(
                prefix=utils.escape_html(self.get_prefix())
            ),
        )
        await utils.answer(message, self.strings("backup_sent"))

    @loader.command(
        ru_doc="Восстановить базу данных из файла",
        fr_doc="Restaurer la base de données à partir d'un fichier",
        it_doc="Ripristina il database da un file",
        de_doc="Stelle die Datenbank aus einer Datei wieder her",
        tr_doc="Veritabanını dosyadan geri yükle",
        uz_doc="Ma'lumotlar bazasini fayldan tiklash",
        es_doc="Restaurar la base de datos desde un archivo",
        kk_doc="Файлдан деректер базасын қалпына келтіру",
        tt_doc="Файлдан мәгълүмат базасын кайтару",
    )
    async def restoredb(self, message: Message):
        """Restore database from file"""
        if not (reply := await message.get_reply_message()) or not reply.media:
            await utils.answer(
                message,
                self.strings("reply_to_file"),
            )
            return

        file = await reply.download_media(bytes)
        decoded_text = json.loads(file.decode())

        with contextlib.suppress(KeyError):
            decoded_text["hikka.inline"].pop("bot_token")

        if not self._db.process_db_autofix(decoded_text):
            raise RuntimeError("Attempted to restore broken database")

        self._db.clear()
        self._db.update(**decoded_text)
        self._db.save()

        await utils.answer(message, self.strings("db_restored"))
        await self.invoke("restart", "-f", peer=message.peer_id)

    @loader.command(
        ru_doc="Создать бэкап модов [будет отправлено в лс]",
        fr_doc="Créer une sauvegarde des mods [sera envoyé en mp]",
        it_doc="Crea un backup dei mods [viene inviato in pm]",
        de_doc="Erstelle eine Mod-Sicherung [wird in pm gesendet]",
        tr_doc="Modları yedekle [pm olarak gönderilecek]",
        uz_doc="Modlarni e'lon qilish [pm ga jo'natiladi]",
        es_doc="Crear copia de seguridad de los mods [se enviará en pm]",
        kk_doc="Моддерді резервтік көшіру [pm жіберіледі]",
        tt_doc="Моддәрне резервтә күчер [pm күчерелә]",
    )
    async def backupmods(self, message: Message):
        """Create backup of modules"""
        mods_quantity = len(self.lookup("Loader").get("loaded_modules", {}))

        result = io.BytesIO()
        result.name = "mods.zip"

        db_mods = json.dumps(self.lookup("Loader").get("loaded_modules", {})).encode()

        with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(loader.LOADED_MODULES_DIR):
                for file in files:
                    with open(os.path.join(root, file), "rb") as f:
                        zipf.writestr(file, f.read())
                        mods_quantity += 1

            zipf.writestr("db_mods.json", db_mods)

        archive = io.BytesIO(result.getvalue())
        archive.name = f"mods-{datetime.datetime.now():%d-%m-%Y-%H-%M}.zip"

        await utils.answer_file(
            message,
            archive,
            caption=self.strings("modules_backup").format(mods_quantity),
        )

    @loader.command(
        ru_doc="<ответ на файл> - Восстановить моды из бэкапа",
        fr_doc="<répondre au fichier> - Restaurer les mods à partir de la sauvegarde",
        it_doc="<rispondi al file> - Ripristina i mod dal backup",
        de_doc="<auf Datei antworten> - Stelle die Module aus dem Backup wieder her",
        tr_doc="<dosyaya yanıtla> - Yedekten modları geri yükle",
        uz_doc="<faylga javob> - E'lon qilingan modlarni tiklash",
        es_doc=(
            "<responder al archivo> - Restaurar los mods desde la copia de seguridad"
        ),
        kk_doc="<файлға жауап> - Ескертпен моддерді қалпына келтіру",
        tt_doc="<файлга яуап> - Ескертпен моддәрне кайтару",
    )
    async def restoremods(self, message: Message):
        """<reply to file> - Restore modules from backup"""
        if not (reply := await message.get_reply_message()) or not reply.media:
            await utils.answer(message, self.strings("reply_to_file"))
            return

        file = await reply.download_media(bytes)
        try:
            decoded_text = json.loads(file.decode())
        except Exception:
            try:
                file = io.BytesIO(file)
                file.name = "mods.zip"

                with zipfile.ZipFile(file) as zf:
                    for name in zf.namelist():
                        with zf.open(name, "r") as module:
                            content = module.read()

                        if name != "db_mods.json":
                            (
                                loader.LOADED_MODULES_DIR_PATH / Path(name).name
                            ).write_bytes(content)
                            continue

                        db_mods = json.loads(content.decode())
                        if isinstance(db_mods, dict) and all(
                            isinstance(key, str) and isinstance(value, str)
                            for key, value in db_mods.items()
                        ):
                            self.lookup("Loader").set("loaded_modules", db_mods)
            except Exception:
                logger.exception("Unable to restore modules")
                await utils.answer(message, self.strings("reply_to_file"))
                return
        else:
            if not isinstance(decoded_text, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in decoded_text.items()
            ):
                raise RuntimeError("Invalid backup")

            self.lookup("Loader").set("loaded_modules", decoded_text)

        await utils.answer(message, self.strings("mods_restored"))
        await self.invoke("restart", "-f", peer=message.peer_id)
