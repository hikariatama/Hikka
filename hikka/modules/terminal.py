#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @bsolute

import asyncio
import contextlib
import logging
import os
import re
import typing

import hikkatl

from .. import loader, utils

logger = logging.getLogger(__name__)


def hash_msg(message):
    return f"{str(utils.get_chat_id(message))}/{str(message.id)}"


async def read_stream(func: callable, stream, delay: float):
    last_task = None
    data = b""
    while True:
        dat = await stream.read(1)

        if not dat:
            # EOF
            if last_task:
                # Send all pending data
                last_task.cancel()
                await func(data.decode())
                # If there is no last task there is inherently no data, so theres no point sending a blank string
            break

        data += dat

        if last_task:
            last_task.cancel()

        last_task = asyncio.ensure_future(sleep_for_task(func, data, delay))


async def sleep_for_task(func: callable, data: bytes, delay: float):
    await asyncio.sleep(delay)
    await func(data.decode())


class MessageEditor:
    def __init__(
        self,
        message: hikkatl.tl.types.Message,
        command: str,
        config,
        strings,
        request_message,
    ):
        self.message = message
        self.command = command
        self.stdout = ""
        self.stderr = ""
        self.rc = None
        self.redraws = 0
        self.config = config
        self.strings = strings
        self.request_message = request_message

    async def update_stdout(self, stdout):
        self.stdout = stdout
        await self.redraw()

    async def update_stderr(self, stderr):
        self.stderr = stderr
        await self.redraw()

    async def redraw(self):
        text = self.strings("running").format(utils.escape_html(self.command))  # fmt: skip

        if self.rc is not None:
            text += self.strings("finished").format(utils.escape_html(str(self.rc)))

        text += self.strings("stdout")
        text += utils.escape_html(self.stdout[max(len(self.stdout) - 2048, 0) :])
        stderr = utils.escape_html(self.stderr[max(len(self.stderr) - 1024, 0) :])
        text += (self.strings("stderr") + stderr) if stderr else ""
        text += self.strings("end")

        with contextlib.suppress(hikkatl.errors.rpcerrorlist.MessageNotModifiedError):
            try:
                self.message = await utils.answer(self.message, text)
            except hikkatl.errors.rpcerrorlist.MessageTooLongError as e:
                logger.error(e)
                logger.error(text)
        # The message is never empty due to the template header

    async def cmd_ended(self, rc):
        self.rc = rc
        self.state = 4
        await self.redraw()

    def update_process(self, process):
        pass


class SudoMessageEditor(MessageEditor):
    # Let's just hope these are safe to parse
    PASS_REQ = "[sudo] password for"
    WRONG_PASS = r"\[sudo\] password for (.*): Sorry, try again\."
    TOO_MANY_TRIES = (r"\[sudo\] password for (.*): sudo: [0-9]+ incorrect password attempts")  # fmt: skip

    def __init__(self, message, command, config, strings, request_message):
        super().__init__(message, command, config, strings, request_message)
        self.process = None
        self.state = 0
        self.authmsg = None

    def update_process(self, process):
        logger.debug("got sproc obj %s", process)
        self.process = process

    async def update_stderr(self, stderr):
        logger.debug("stderr update " + stderr)
        self.stderr = stderr
        lines = stderr.strip().split("\n")
        lastline = lines[-1]
        lastlines = lastline.rsplit(" ", 1)
        handled = False

        if (
            len(lines) > 1
            and re.fullmatch(self.WRONG_PASS, lines[-2])
            and lastlines[0] == self.PASS_REQ
            and self.state == 1
        ):
            logger.debug("switching state to 0")
            await self.authmsg.edit(self.strings("auth_failed"))
            self.state = 0
            handled = True
            await asyncio.sleep(2)
            await self.authmsg.delete()

        if lastlines[0] == self.PASS_REQ and self.state == 0:
            logger.debug("Success to find sudo log!")
            text = self.strings("auth_needed").format(self._tg_id)

            try:
                await utils.answer(self.message, text)
            except hikkatl.errors.rpcerrorlist.MessageNotModifiedError as e:
                logger.debug(e)

            logger.debug("edited message with link to self")
            command = "<code>" + utils.escape_html(self.command) + "</code>"
            user = utils.escape_html(lastlines[1][:-1])

            self.authmsg = await self.message[0].client.send_message(
                "me",
                self.strings("auth_msg").format(command, user),
            )
            logger.debug("sent message to self")

            self.message[0].client.remove_event_handler(self.on_message_edited)
            self.message[0].client.add_event_handler(
                self.on_message_edited,
                hikkatl.events.messageedited.MessageEdited(chats=["me"]),
            )

            logger.debug("registered handler")
            handled = True

        if len(lines) > 1 and (
            re.fullmatch(self.TOO_MANY_TRIES, lastline)
            and (self.state == 1 or self.state == 3 or self.state == 4)
        ):
            logger.debug("password wrong lots of times")
            await utils.answer(self.message, self.strings("auth_locked"))
            await self.authmsg.delete()
            self.state = 2
            handled = True

        if not handled:
            logger.debug("Didn't find sudo log.")
            if self.authmsg is not None:
                await self.authmsg[0].delete()
                self.authmsg = None
            self.state = 2
            await self.redraw()

        logger.debug(self.state)

    async def update_stdout(self, stdout):
        self.stdout = stdout

        if self.state != 2:
            self.state = 3  # Means that we got stdout only

        if self.authmsg is not None:
            await self.authmsg.delete()
            self.authmsg = None

        await self.redraw()

    async def on_message_edited(self, message):
        # Message contains sensitive information.
        if self.authmsg is None:
            return

        logger.debug(f"got message edit update in self {str(message.id)}")

        if hash_msg(message) == hash_msg(self.authmsg):
            # The user has provided interactive authentication. Send password to stdin for sudo.
            try:
                self.authmsg = await utils.answer(message, self.strings("auth_ongoing"))
            except hikkatl.errors.rpcerrorlist.MessageNotModifiedError:
                # Try to clear personal info if the edit fails
                await message.delete()

            self.state = 1
            self.process.stdin.write(
                message.message.message.split("\n", 1)[0].encode() + b"\n"
            )


class RawMessageEditor(SudoMessageEditor):
    def __init__(
        self,
        message,
        command,
        config,
        strings,
        request_message,
        show_done=False,
    ):
        super().__init__(message, command, config, strings, request_message)
        self.show_done = show_done

    async def redraw(self):
        logger.debug(self.rc)

        if self.rc is None:
            text = (
                "<code>"
                + utils.escape_html(self.stdout[max(len(self.stdout) - 4095, 0) :])
                + "</code>"
            )
        elif self.rc == 0:
            text = (
                "<code>"
                + utils.escape_html(self.stdout[max(len(self.stdout) - 4090, 0) :])
                + "</code>"
            )
        else:
            text = (
                "<code>"
                + utils.escape_html(self.stderr[max(len(self.stderr) - 4095, 0) :])
                + "</code>"
            )

        if self.rc is not None and self.show_done:
            text += "\n" + self.strings("done")

        logger.debug(text)

        with contextlib.suppress(
            hikkatl.errors.rpcerrorlist.MessageNotModifiedError,
            hikkatl.errors.rpcerrorlist.MessageEmptyError,
            ValueError,
        ):
            try:
                await utils.answer(self.message, text)
            except hikkatl.errors.rpcerrorlist.MessageTooLongError as e:
                logger.error(e)
                logger.error(text)


@loader.tds
class TerminalMod(loader.Module):
    """Runs commands"""

    e = "<emoji document_id=5210952531676504517>🚫</emoji>"
    c = "<emoji document_id=5472111548572900003>⌨️</emoji>"
    s = "<emoji document_id=5472308992514464048>🔐</emoji>"
    d = "<emoji document_id=5314250708508220914>✅</emoji>"
    w = "<emoji document_id=5213452215527677338>⏳</emoji>"

    strings = {
        "name": "Terminal",
        "fw_protect": "How long to wait in seconds between edits in commands",
        "what_to_kill": f"{e} <b>Reply to a terminal command to terminate it</b>",
        "kill_fail": f"{e} <b>Could not kill process</b>",
        "killed": f"{e} <b>Killed</b>",
        "no_cmd": f"{e} <b>No command is running in that message</b>",
        "running": f"{c}<b> System call</b> <code>{{}}</code>",
        "finished": "\n<b>Exit code</b> <code>{}</code>",
        "stdout": "\n<b>📼 Stdout:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Stderr:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Authentication failed, please try again</b>",
        "auth_needed": (
            f'{s}<a href="tg://user?id={{}}"> Interactive authentication required</a>'
        ),
        "auth_msg": (
            f"{s} <b>Please edit this"
            " message to the password for</b> <code>{}</code> <b>to run</b>"
            " <code>{}</code>"
        ),
        "auth_locked": f"{e} <b>Authentication failed, please try again later</b>",
        "auth_ongoing": f"{w} <b>Authenticating...</b>",
        "done": f"{d} <b>Done</b>",
    }

    strings_ru = {
        "fw_protect": "Задержка между редактированиями",
        "what_to_kill": f"{e} <b>Ответь на выполняемую команду для ее завершения</b>",
        "kill_fail": f"{e} <b>Не могу убить процесс</b>",
        "killed": "<b>Убит</b>",
        "no_cmd": f"{e} <b>В этом сообщении не выполняется команда</b>",
        "running": f"{c}<b> Системная команда</b> <code>{{}}</code>",
        "finished": "\n<b>Код выхода </b> <code>{}</code>",
        "stdout": "\n<b>📼 Вывод:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Ошибки:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Аутентификация неуспешна, попробуй еще раз</b>",
        "auth_needed": f'{s}<a href="tg://user?id={{}}"> Необходима аутентификация</a>',
        "auth_msg": (
            f"{s} <b>Пожалуйста, отредактируй это сообщение с паролем от рута для</b>"
            " <code>{}</code> <b>, чтобы выполнить</b> <code>{}</code>"
        ),
        "auth_locked": f"{e} <b>Аутентификация не удалась. Попробуй позже</b>",
        "auth_ongoing": f"{w} <b>Аутентификация...</b>",
        "done": f"{d} <b>Ура</b>",
    }

    strings_de = {
        "fw_protect": (
            "Wie lange soll zwischen den Editierungen in Befehlen gewartet werden"
        ),
        "what_to_kill": (
            f"{e} <b>Antworte auf einen Terminal-Befehl um ihn zu stoppen</b>"
        ),
        "kill_fail": f"{e} <b>Konnte den Prozess nicht stoppen</b>",
        "killed": f"{e} <b>Gestoppt</b>",
        "no_cmd": f"{e} <b>Kein Befehl wird in dieser Nachricht ausgeführt</b>",
        "running": f"{c}<b> Systemaufruf</b> <code>{{}}</code>",
        "finished": "\n<b>Exit-Code</b> <code>{}</code>",
        "stdout": "\n<b>📼 Stdout:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Stderr:</b>\n<code>",
        "end": "</code>",
        "auth_fail": (
            f"{e} <b>Authentifizierung fehlgeschlagen, bitte versuche es erneut</b>"
        ),
        "auth_needed": (
            f'{s}<a href="tg://user?id={{}}">'
            " Interaktive Authentifizierung benötigt</a>"
        ),
        "auth_msg": (
            f"{s} <b>Bitte bearbeite diese"
            " Nachricht mit dem Passwort für</b> <code>{}</code> <b>um</b>"
            " <code>{}</code> <b>auszuführen</b>"
        ),
        "auth_locked": (
            f"{e} <b>Authentifizierung"
            " fehlgeschlagen, bitte versuche es später erneut</b>"
        ),
        "auth_ongoing": f"{w} <b>Authentifizierung läuft...</b>",
        "done": f"{d} <b>Fertig</b>",
    }

    strings_tr = {
        "fw_protect": "Bir komut arasındaki düzenleme süresi",
        "what_to_kill": f"{e} <b>Çalışan bir komutu durdurmak için yanıtlayın</b>",
        "kill_fail": f"{e} <b>İşlemi durduramadım</b>",
        "killed": "<b>Durduruldu</b>",
        "no_cmd": f"{e} <b>Bu mesajda çalışan bir komut yok</b>",
        "running": f"{c}<b> Sistem komutu</b> <code>{{}}</code>",
        "finished": "\n<b>Çıkış kodu</b> <code>{}</code>",
        "stdout": "\n<b>📼 Stdout:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Stderr:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Kimlik doğrulama başarısız, lütfen tekrar deneyin</b>",
        "auth_needed": (
            f'{s}<a href="tg://user?id={{}}">'
            " Etkileşimli kimlik doğrulaması gerekli</a>"
        ),
        "auth_msg": (
            f"{s} <b>Lütfen bu mesajı</b> <code>{{}}</code> <b>için</b>"
            " <code>{}</code> <b>çalıştırmak için parola olarak düzenleyin</b>"
        ),
        "auth_locked": (
            f"{e} <b>Kimlik doğrulama başarısız, lütfen daha sonra tekrar deneyin</b>"
        ),
        "auth_ongoing": f"{w} <b>Kimlik doğrulaması sürüyor...</b>",
        "done": f"{d} <b>Bitti</b>",
    }

    strings_uz = {
        "fw_protect": "Buyruqlar orasidagi tahrirlash vaqti",
        "what_to_kill": (
            f"{e} <b>Ishga tushgan buyruqni"
            " to'xtatish uchun uni javob qilib yuboring</b>"
        ),
        "kill_fail": f"{e} <b>Protsessni to'xtatib bo'lmadi</b>",
        "killed": f"{e} <b>To'xtatildi</b>",
        "no_cmd": f"{e} <b>Ushbu xabarda ishga tushgan buyruq yo'q</b>",
        "running": f"{c}<b> Tizim buyrug'i</b> <code>{{}}</code>",
        "finished": "\n<b>Chiqish kodi</b> <code>{}</code>",
        "stdout": "\n<b>📼 Stdout:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Stderr:</b>\n<code>",
        "end": "</code>",
        "auth_fail": (
            f"{e} <b>Autentifikatsiya muvaffaqiyatsiz, iltimos qayta urinib ko'ring</b>"
        ),
        "auth_needed": (
            f'{s}<a href="tg://user?id={{}}">'
            " Ishlanadigan autentifikatsiya talab qilinadi</a>"
        ),
        "auth_msg": (
            f"{s} <b>Iltimos, ushbu"
            " xabarni</b> <code>{}</code> <b>uchun</b> <code>{}</code> <b>ishga"
            " tushurish uchun parolasi sifatida tahrirlang</b>"
        ),
        "auth_locked": (
            f"{e} <b>Autentifikatsiya"
            " muvaffaqiyatsiz, iltimos keyinroq qayta urinib ko'ring</b>"
        ),
        "auth_ongoing": f"{w} <b>Autentifikatsiya davom etmoqda...</b>",
        "done": f"{d} <b>Tugadi</b>",
    }

    strings_fr = {
        "fw_protect": "Délai entre les modifications",
        "what_to_kill": (
            f"{e} <b>Répondez à la commande en cours pour l'interrompre</b>"
        ),
        "kill_fail": f"{e} <b>Impossible de tuer le processus</b>",
        "killed": "<b>Tué</b>",
        "no_cmd": f"{e} <b>Aucune commande n'est exécutée dans ce message</b>",
        "running": f"{c}<b> Commande système</b> <code>{{}}</code>",
        "finished": "\n<b>Code de sortie </b> <code>{}</code>",
        "stdout": "\n<b>📼 Sortie:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Erreurs:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>L'authentification a échoué, essayez à nouveau</b>",
        "auth_needed": f'{s}<a href="tg://user?id={{}}"> Authentification requise</a>',
        "auth_msg": (
            f"{s} <b>Veuillez modifier ce message avec le mot de passe de root pour</b>"
            " <code>{}</code> <b>, pour exécuter</b> <code>{}</code>"
        ),
        "auth_locked": f"{e} <b>L'authentification a échoué. Réessayez plus tard</b>",
        "auth_ongoing": f"{w} <b>Authentification en cours...</b>",
        "done": f"{d} <b>Terminé</b>",
    }

    strings_it = {
        "fw_protect": "Ritardo tra le modifiche",
        "what_to_kill": f"{e} <b>Rispondi al comando in esecuzione per terminarlo</b>",
        "kill_fail": f"{e} <b>Non posso uccidere il processo</b>",
        "killed": "<b>ucciso</b>",
        "no_cmd": f"{e} <b>Non è in esecuzione alcun comando in questo messaggio</b>",
        "running": f"{c}<b> Comando di sistema</b> <code>{{}}</code>",
        "finished": "\n<b>codice di uscita</b> <code>{}</code>",
        "stdout": "\n<b>📼 Output:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Errori:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Autenticazione non riuscita, riprova</b>",
        "auth_needed": f'{s}<a href="tg://user?id={{}}"> Autenticazione richiesta</a>',
        "auth_msg": (
            f"{s} <b>Si prega di modificare questo messaggio con la password di root"
            " per</b> <code>{}</code> <b>, per eseguire</b> <code>{}</code>"
        ),
        "auth_locked": f"{e} <b>Autenticazione non riuscita. Riprova più tardi</b>",
        "auth_ongoing": f"{w} <b>Autenticazione...</b>",
        "done": f"{d} <b>Yay</b>",
    }

    strings_es = {
        "fw_protect": "Retraso entre ediciones",
        "what_to_kill": f"{e} <b>Responda a la orden en ejecución para detenerla</b>",
        "kill_fail": f"{e} <b>No puedo matar el proceso</b>",
        "killed": "<b>Muerto</b>",
        "no_cmd": f"{e} <b>No hay ninguna orden en este mensaje</b>",
        "running": f"{c}<b> Orden de sistema</b> <code>{{}}</code>",
        "finished": "\n<b>Código de salida </b> <code>{}</code>",
        "stdout": "\n<b>📼 Salida:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Errores:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Autenticación fallida, inténtelo de nuevo</b>",
        "auth_needed": f'{s}<a href="tg://user?id={{}}"> Autenticación necesaria</a>',
        "auth_msg": (
            f"{s} <b>Por favor, edite este mensaje con la contraseña de root para</b>"
            " <code>{}</code> <b>, para ejecutar</b> <code>{}</code>"
        ),
        "auth_locked": (
            f"{e} <b>Autenticación fallida. Inténtelo de nuevo más tarde</b>"
        ),
        "auth_ongoing": f"{w} <b>Autenticación...</b>",
        "done": f"{d} <b>Wuhu</b>",
    }

    strings_kk = {
        "fw_protect": "Өңдеулер арасында бекіту",
        "what_to_kill": f"{e} <b>Барлығын өшіру үшін әрекеттің жауапсын жазыңыз</b>",
        "kill_fail": f"{e} <b>Процессті өшіру мүмкін емес</b>",
        "killed": "<b>Өшірілді</b>",
        "no_cmd": f"{e} <b>Бұл жазбада әрекет жоқ</b>",
        "running": f"{c}<b> Системалық әрекет</b> <code>{{}}</code>",
        "finished": "\n<b>Шығыс коды </b> <code>{}</code>",
        "stdout": "\n<b>📼 Шығыс:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Қателер:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Авторизациясы сәтсіз аяқталды, қайталап көріңіз</b>",
        "auth_needed": f'{s}<a href="tg://user?id={{}}"> Авторизация керек</a>',
        "auth_msg": (
            f"{s} <b>Бұл әрекетті өзгерту үшін өзіңіздің рут паролын</b>"
            " <code>{}</code> <b>, осы жазбаны түзетіңіз</b> <code>{}</code>"
        ),
        "auth_locked": (
            f"{e} <b>Авторизация сәтсіз аяқталды. Кейінірек әрекетті қайталаңыз</b>"
        ),
        "auth_ongoing": f"{w} <b>Авторизация...</b>",
        "done": f"{d} <b>Жақсы жақсы</b>",
    }

    strings_tt = {
        "fw_protect": "Итервал алышуы",
        "what_to_kill": (
            f"{e} <b>Шул урнаштыруучыны тамамлап торган хатны жаваб бер</b>"
        ),
        "kill_fail": f"{e} <b>Шул урнаштыруучыны урнаштыра алмыйм</b>",
        "killed": "<b>Урнаштырылган</b>",
        "no_cmd": f"{e} <b>Бу хатта урнаштыруучы юк</b>",
        "running": f"{c}<b> Система коммандасы</b> <code>{{}}</code>",
        "finished": "\n<b>Чыгу коды </b> <code>{}</code>",
        "stdout": "\n<b>📼 Шығару:</b>\n<code>",
        "stderr": f"</code>\n\n<b>{e} Хаталар:</b>\n<code>",
        "end": "</code>",
        "auth_fail": f"{e} <b>Аутентификация тамамланмады, кайтадан көрөргә кирәк</b>",
        "auth_needed": (
            f'{s}<a href="tg://user?id={{}}"> Аутентификация талап ителә</a>'
        ),
        "auth_msg": (
            f"{s} <b>Өчен</b> <code>{{}}</code> <b>урынында бу хатны төзегез</b>"
            " <code>{}</code>"
        ),
        "auth_locked": (
            f"{e} <b>Аутентификация тамамланмады. Кайтадан көрөргә кирәк</b>"
        ),
        "auth_ongoing": f"{w} <b>Аутентификация...</b>",
        "done": f"{d} <b>Ура</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "FLOOD_WAIT_PROTECT",
                2,
                lambda: self.strings("fw_protect"),
                validator=loader.validators.Integer(minimum=0),
            ),
        )
        self.activecmds = {}

    @loader.command(
        ru_doc="<команда> - Запустить команду в системе",
        de_doc="<Befehl> - Führt einen Befehl im System aus",
        tr_doc="<komut> - Sistemde komutu çalıştırır",
        uz_doc="<buyruq> - Tizimda buyruqni ishga tushiradi",
        es_doc="<comando> - Ejecuta un comando en el sistema",
        fr_doc="<commande> - Exécute une commande dans le système",
        it_doc="<comando> - Esegui un comando nel sistema",
        kk_doc="<команда> - Системада команданы іске қосу",
        tt_doc="<команда> - Системада команданы ишке қосу",
    )
    async def terminalcmd(self, message):
        """<command> - Execute bash command"""
        await self.run_command(message, utils.get_args_raw(message))

    @loader.command(
        ru_doc="Сокращение для '.terminal apt'",
        de_doc="Abkürzung für '.terminal apt'",
        tr_doc="'terminal apt' kısaltması",
        uz_doc="'terminal apt' qisqartmasi",
        es_doc="Atajo para '.terminal apt'",
        fr_doc="Raccourci pour '.terminal apt'",
        it_doc="Scorciatoia per '.terminal apt'",
        kk_doc="'terminal apt' қысқартмасы",
        tt_doc="'terminal apt' қысқартмасы",
    )
    async def aptcmd(self, message):
        """Shorthand for '.terminal apt'"""
        await self.run_command(
            message,
            ("apt " if os.geteuid() == 0 else "sudo -S apt ")
            + utils.get_args_raw(message)
            + " -y",
            RawMessageEditor(
                message,
                f"apt {utils.get_args_raw(message)}",
                self.config,
                self.strings,
                message,
                True,
            ),
        )

    async def run_command(
        self,
        message: hikkatl.tl.types.Message,
        cmd: str,
        editor: typing.Optional[MessageEditor] = None,
    ):
        if len(cmd.split(" ")) > 1 and cmd.split(" ")[0] == "sudo":
            needsswitch = True

            for word in cmd.split(" ", 1)[1].split(" "):
                if word[0] != "-":
                    break

                if word == "-S":
                    needsswitch = False

            if needsswitch:
                cmd = " ".join([cmd.split(" ", 1)[0], "-S", cmd.split(" ", 1)[1]])

        sproc = await asyncio.create_subprocess_shell(
            cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=utils.get_base_dir(),
        )

        if editor is None:
            editor = SudoMessageEditor(message, cmd, self.config, self.strings, message)

        editor.update_process(sproc)

        self.activecmds[hash_msg(message)] = sproc

        await editor.redraw()

        await asyncio.gather(
            read_stream(
                editor.update_stdout,
                sproc.stdout,
                self.config["FLOOD_WAIT_PROTECT"],
            ),
            read_stream(
                editor.update_stderr,
                sproc.stderr,
                self.config["FLOOD_WAIT_PROTECT"],
            ),
        )

        await editor.cmd_ended(await sproc.wait())
        del self.activecmds[hash_msg(message)]

    @loader.command(
        ru_doc="[-f to force kill] - Ответьте на сообщение, чтобы убить процесс",
        de_doc=(
            "[-f zum erzwingen] - Antwort auf eine Nachricht, um den Prozess zu beenden"
        ),
        tr_doc="[-f zorla öldürmek] - Bir işlemi öldürmek için bir mesaja yanıt verin",
        uz_doc=(
            "[-f qo‘llab-quvvatlash] - Protsessni o‘chirish uchun xabarga javob bering"
        ),
        es_doc="[-f para forzar] - Responda a un mensaje para matar un proceso",
        fr_doc="[-f pour forcer] - Répondez à un message pour tuer un processus",
        it_doc="[-f per forzare] - Rispondi a un messaggio per uccidere un processo",
        kk_doc="[-f жақсылау] - Процессті жойу үшін хабарға жауап беріңіз",
        tt_doc="[-f турында] - Процессне өчүрү үчүн хабарга жауап бериңиз",
    )
    async def terminatecmd(self, message):
        """[-f to force kill] - Use in reply to send SIGTERM to a process"""
        if not message.is_reply:
            await utils.answer(message, self.strings("what_to_kill"))
            return

        if hash_msg(await message.get_reply_message()) in self.activecmds:
            try:
                if "-f" not in utils.get_args_raw(message):
                    self.activecmds[
                        hash_msg(await message.get_reply_message())
                    ].terminate()
                else:
                    self.activecmds[hash_msg(await message.get_reply_message())].kill()
            except Exception:
                logger.exception("Killing process failed")
                await utils.answer(message, self.strings("kill_fail"))
            else:
                await utils.answer(message, self.strings("killed"))
        else:
            await utils.answer(message, self.strings("no_cmd"))
