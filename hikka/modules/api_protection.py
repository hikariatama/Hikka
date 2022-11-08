#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import io
import json
import logging
import time

from telethon.tl import functions
from telethon.tl.tlobject import TLRequest
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

GROUPS = [
    "auth",
    "account",
    "users",
    "contacts",
    "messages",
    "updates",
    "photos",
    "upload",
    "help",
    "channels",
    "bots",
    "payments",
    "stickers",
    "phone",
    "langpack",
    "folders",
    "stats",
]


def decapitalize(string: str) -> str:
    return string[0].lower() + string[1:]


CONSTRUCTORS = {
    decapitalize(
        method.__class__.__name__.rsplit("Request", 1)[0]
    ): method.CONSTRUCTOR_ID
    for method in utils.array_sum(
        [
            [
                method
                for method in dir(getattr(functions, group))
                if isinstance(method, TLRequest)
            ]
            for group in GROUPS
        ]
    )
}


@loader.tds
class APIRatelimiterMod(loader.Module):
    """Helps userbot avoid spamming Telegram API"""

    strings = {
        "name": "APILimiter",
        "warning": (
            "<emoji document_id=5312383351217201533>⚠️</emoji>"
            " <b>WARNING!</b>\n\nYour account exceeded the limit of requests, specified"
            " in config. In order to prevent Telegram API Flood, userbot has been"
            " <b>fully frozen</b> for {} seconds. Further info is provided in attached"
            " file. \n\nIt is recommended to get help in <code>{prefix}support</code>"
            " group!\n\nIf you think, that it is an intended behavior, then wait until"
            " userbot gets unlocked and next time, when you will be going to perform"
            " such an operation, use <code>{prefix}suspend_api_protect</code> &lt;time"
            " in seconds&gt;"
        ),
        "args_invalid": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Invalid arguments</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood Protection"
            " is disabled for {} seconds</b>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protection enabled</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protection"
            " disabled</b>"
        ),
        "u_sure": "⚠️ <b>Are you sure?</b>",
        "_cfg_time_sample": "Time sample through which the bot will count requests",
        "_cfg_threshold": "Threshold of requests to trigger protection",
        "_cfg_local_floodwait": (
            "Freeze userbot for this amount of time, if request limit exceeds"
        ),
        "_cfg_forbidden_methods": (
            "Forbid specified methods from being executed throughout external modules"
        ),
        "btn_no": "🚫 No",
        "btn_yes": "✅ Yes",
        "web_pin": (
            "🔓 <b>Click the button below to show Werkzeug debug PIN. Do not give it to"
            " anyone.</b>"
        ),
        "web_pin_btn": "🐞 Show Werkzeug PIN",
    }

    strings_ru = {
        "warning": (
            "<emoji document_id=5312383351217201533>⚠️</emoji>"
            " <b>ВНИМАНИЕ!</b>\n\nАккаунт вышел за лимиты запросов, указанные в"
            " конфиге. С целью предотвращения флуда Telegram API, юзербот был"
            " <b>полностью заморожен</b> на {} секунд. Дополнительная информация"
            " прикреплена в файле ниже. \n\nРекомендуется обратиться за помощью в"
            " <code>{prefix}support</code> группу!\n\nЕсли ты считаешь, что это"
            " запланированное поведение юзербота, просто подожди, пока закончится"
            " таймер и в следующий раз, когда запланируешь выполнять такую"
            " ресурсозатратную операцию, используй"
            " <code>{prefix}suspend_api_protect</code> &lt;время в секундах&gt;"
        ),
        "args_invalid": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Неверные аргументы</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Защита API отключена"
            " на {} секунд</b>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>Защита включена</b>",
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Защита отключена</b>"
        ),
        "u_sure": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Ты уверен?</b>",
        "_cfg_time_sample": (
            "Временной промежуток, по которому будет считаться количество запросов"
        ),
        "_cfg_threshold": "Порог запросов, при котором будет срабатывать защита",
        "_cfg_local_floodwait": (
            "Заморозить юзербота на это количество секунд, если лимит запросов превышен"
        ),
        "_cfg_forbidden_methods": (
            "Запретить выполнение указанных методов во всех внешних модулях"
        ),
        "btn_no": "🚫 Нет",
        "btn_yes": "✅ Да",
        "web_pin": (
            "🔓 <b>Нажми на кнопку ниже, чтобы показать Werkzeug debug PIN. Не давай его"
            " никому.</b>"
        ),
        "web_pin_btn": "🐞 Показать Werkzeug PIN",
    }

    strings_de = {
        "warning": (
            "<emoji document_id=5312383351217201533>⚠️</emoji>"
            " <b>Achtung!</b>\n\nDas Konto hat die in der Konfiguration angegebenen"
            " Grenzwerte für Anfragen überschritten. Um Telegram API-Flooding zu"
            " verhindern, wurde der <b>ganze Userbot</b> für {} Sekunden"
            " eingefroren. Weitere Informationen finden Sie im unten angefügten"
            " Datei.\n\nWir empfehlen Ihnen, sich mit Hilfe der <code>{prefix}"
            "support</code> Gruppe zu helfen!\n\nWenn du denkst, dass dies"
            " geplantes Verhalten des Userbots ist, dann warte einfach, bis der"
            " Timer abläuft und versuche beim nächsten Mal, eine so ressourcen"
            " intensive Operation wie <code>{prefix}suspend_api_protect</code>"
            " &lt;Zeit in Sekunden&gt; zu planen."
        ),
        "args_invalid": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ungültige"
            " Argumente</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood"
            " Protection ist für {} Sekunden deaktiviert</b>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Schutz aktiviert</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Schutz deaktiviert</b>"
        ),
        "u_sure": "⚠️ <b>Bist du sicher?</b>",
        "_cfg_time_sample": "Zeitintervall, in dem die Anfragen gezählt werden",
        "_cfg_threshold": (
            "Schwellenwert für Anfragen, ab dem der Schutz aktiviert wird"
        ),
        "_cfg_local_floodwait": (
            "Einfrieren des Userbots für diese Anzahl von Sekunden, wenn der Grenzwert"
            " überschritten wird"
        ),
        "_cfg_forbidden_methods": "Verbotene Methoden in allen externen Modulen",
        "btn_no": "🚫 Nein",
        "btn_yes": "✅ Ja",
        "web_pin": (
            "🔓 <b>Drücke auf die Schaltfläche unten, um den Werkzeug debug PIN"
            " anzuzeigen. Gib ihn niemandem.</b>"
        ),
        "web_pin_btn": "🐞 Werkzeug PIN anzeigen",
    }

    strings_tr = {
        "warning": (
            "<emoji document_id=5312383351217201533>⚠️</emoji>"
            " <b>Dikkat!</b>\n\nHesabın ayarlarda belirtilmiş istek sınırını aştı."
            " Telegram API Flood’unu önlemek için tüm <b>kullanıcı botu<b> {} saniye"
            " boyunca durduruldu. Daha fazla bilgi almak için ekteki dosyayı"
            " inceleyebilirsiniz. /n/ Ayrıca <code>{prefix}Destek</code> grubundan"
            " yardım almanız önerilmektedir. Eğer bu işlemin kasıtlı bir işlem olduğunu"
            " düşünüyorsanız, kullanıcı botunuzun açılmasının bekleyin ve bu tarz bir"
            " işlem gerçekleştireceğiniz sıradaki sefer"
            " <code>{prefix}suspend_api_protect</code> &lt;saniye&gt; kodunu kullanın."
        ),
        "args_invalid": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Geçersiz"
            " argümanlar</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood koruması {}"
            " saniyeliğine durduruldu.</b>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Koruma"
            " aktifleştirildi.</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Koruma"
            " de-aktifleştirildi</b>"
        ),
        "u_sure": "⚠️ <b>Emin misin?</b>",
        "_cfg_time_sample": "Saniyede sayılan isteklerin zaman aralığı",
        "_cfg_threshold": "Korumanın etkinleşeceği sınır değeri",
        "_cfg_local_floodwait": (
            "Telegram API sınır değeri aşıldığında kullanıcı botu bir süre durdurulur"
        ),
        "_cfg_forbidden_methods": (
            "Belirtili metodların harici modüller tarafından çalıştırılmasını yasakla"
        ),
        "btn_no": "🚫 Hayır",
        "btn_yes": "✅ Evet",
        "web_pin": (
            "🔓 <b>Werkzeug hata ayıklama PIN'ini göstermek için aşağıdaki düğmeyi"
            " tıklayın. Onu kimseye vermeyin.</b>"
        ),
        "web_pin_btn": "🐞 Werkzeug PIN'ini göster",
    }

    strings_uz = {
        "warning": (
            "<emoji document_id=5312383351217201533>⚠️</emoji>"
            " <b>Ogohlantirish!</b>\n\nBu hisob uchun konfiguratsiyada ko'rsatilgan"
            " chegaralar chegarani o'zgartirgan.\n\nTelegram API Flood"
            " to'xtatish uchun, bu <b>hammasi userbot</b> uchun {} sekundni"
            " blokirovka qilindi. Batafsil ma'lumot uchun pastdagi faylni o'qing.\n\n"
            "Yordam uchun <code>{prefix}support</code> guruhidan foydalaning!\n\nAgar"
            " siz hisobni botning yordamchisi bo'lishi kerak bo'lgan amalni bajarishga"
            " imkoniyat berishga o'xshaysiz, unda faqat blokirovkani to'xtatish uchun"
            " <code>{prefix}suspend_api_protect</code> &lt;sekund&gt; dan foydalaning."
        ),
        "args_invalid": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Noto'g'ri argument</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood"
            " himoya {} sekund uchun to'xtatildi</b>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>Himoya yoqildi</b>",
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Himoya o'chirildi</b>"
        ),
        "u_sure": "⚠️ <b>Siz ishonchingiz komilmi?</b>",
        "_cfg_time_sample": "Sekundda qabul qilinadigan so'rovlar soni chegarasi",
        "_cfg_threshold": "Himoya yoqish uchun qiymatni chegaralash",
        "_cfg_local_floodwait": (
            "Foydalanuvchi botni ushbu soniya davomida blokirovka qiladi, agar"
            " chegaralar qiymati oshsa"
        ),
        "_cfg_forbidden_methods": "Barcha tashqi modullarda taqiqlangan usullar",
        "btn_no": "🚫 Yo'q",
        "btn_yes": "✅ Ha",
        "web_pin": (
            "🔓 <b>Werkzeug Debug PIN kodini ko'rsatish uchun quyidagi tugmani bosing."
            " Uni hech kimga bermang.</b>"
        ),
        "web_pin_btn": "🐞 Werkzeug PIN-ni ko'rsatish",
    }

    strings_es = {
        "warning": (
            "<emoji document_id=5312383351217201533>⚠️</emoji>"
            " <b>¡Advertencia!</b>\n\nDe acuerdo con la configuración de esta cuenta,"
            " las siguientes limitaciones serán aplicadas.\n\nSe bloqueará <b>a todos"
            " los bots de los usuarios</b> por {} segundos para evitar el exceso de las"
            " limitaciones de Telegram API. Para más información, consulta el archivo"
            " siguiente.\n\nPara obtener ayuda, use el grupo"
            " <code>{prefix}support</code>!\n\nPara permitir que la cuenta funcione,"
            " use <code>{prefix}suspend_api_protect</code> para desbloquear."
        ),
        "args_invalid": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Argumentos"
            " inválidos</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji>"
            " <b>Se ha desactivado la protección de API por {} segundos</b>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protección"
            " activada</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protección"
            " desactivada</b>"
        ),
        "u_sure": "⚠️ <b>¿Estás seguro?</b>",
        "_cfg_time_sample": (
            "El tiempo en segundos durante el cual se exceden las limitaciones"
        ),
        "_cfg_threshold": "El valor por encima del cual se exceden las limitaciones",
        "_cfg_local_floodwait": (
            "El tiempo en segundos durante el cual se bloquea al usuario para el bot"
        ),
        "_cfg_forbidden_methods": (
            "Los comandos prohibidos por todas las extensiones externas"
        ),
        "btn_no": "🚫 No",
        "btn_yes": "✅ Sí",
        "web_pin": (
            "🔓 <b>Haga clic en el botón de abajo para mostrar el PIN de depuración de"
            " Werkzeug. No se lo des a nadie.</b>"
        ),
        "web_pin_btn": "🐞 Mostrar el PIN de Werkzeug",
    }

    _ratelimiter = []
    _suspend_until = 0
    _lock = False

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "time_sample",
                15,
                lambda: self.strings("_cfg_time_sample"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "threshold",
                100,
                lambda: self.strings("_cfg_threshold"),
                validator=loader.validators.Integer(minimum=10),
            ),
            loader.ConfigValue(
                "local_floodwait",
                30,
                lambda: self.strings("_cfg_local_floodwait"),
                validator=loader.validators.Integer(minimum=10, maximum=3600),
            ),
            loader.ConfigValue(
                "forbidden_methods",
                ["joinChannel", "importChatInvite"],
                lambda: self.strings("_cfg_forbidden_methods"),
                validator=loader.validators.MultiChoice(
                    [
                        "sendReaction",
                        "joinChannel",
                        "importChatInvite",
                    ]
                ),
                on_change=lambda: self._client.forbid_constructors(
                    map(
                        lambda x: CONSTRUCTORS[x], self.config["forbidden_constructors"]
                    )
                ),
            ),
        )

    async def client_ready(self):
        asyncio.ensure_future(self._install_protection())

    async def _install_protection(self):
        await asyncio.sleep(30)  # Restart lock
        if hasattr(self._client._call, "_old_call_rewritten"):
            raise loader.SelfUnload("Already installed")

        old_call = self._client._call

        async def new_call(
            sender: "MTProtoSender",  # type: ignore
            request: "TLRequest",  # type: ignore
            ordered: bool = False,
            flood_sleep_threshold: int = None,
        ):
            if time.perf_counter() > self._suspend_until and not self.get(
                "disable_protection",
                True,
            ):
                request_name = type(request).__name__
                self._ratelimiter += [[request_name, time.perf_counter()]]

                self._ratelimiter = list(
                    filter(
                        lambda x: time.perf_counter() - x[1]
                        < int(self.config["time_sample"]),
                        self._ratelimiter,
                    )
                )

                if (
                    len(self._ratelimiter) > int(self.config["threshold"])
                    and not self._lock
                ):
                    self._lock = True
                    report = io.BytesIO(
                        json.dumps(
                            self._ratelimiter,
                            indent=4,
                        ).encode("utf-8")
                    )
                    report.name = "local_fw_report.json"

                    await self.inline.bot.send_document(
                        self.tg_id,
                        report,
                        caption=self.strings("warning").format(
                            self.config["local_floodwait"],
                            prefix=self.get_prefix(),
                        ),
                    )

                    # It is intented to use time.sleep instead of asyncio.sleep
                    time.sleep(int(self.config["local_floodwait"]))
                    self._lock = False

            return await old_call(sender, request, ordered, flood_sleep_threshold)

        self._client._call = new_call
        self._client._old_call_rewritten = old_call
        self._client._call._hikka_overwritten = True
        logger.debug("Successfully installed ratelimiter")

    async def on_unload(self):
        if hasattr(self._client, "_old_call_rewritten"):
            self._client._call = self._client._old_call_rewritten
            delattr(self._client, "_old_call_rewritten")
            logger.debug("Successfully uninstalled ratelimiter")

    @loader.command(
        ru_doc="<время в секундах> - Заморозить защиту API на N секунд",
        de_doc="<Sekunden> - API-Schutz für N Sekunden einfrieren",
        tr_doc="<saniye> - API korumasını N saniye dondur",
        uz_doc="<soniya> - API himoyasini N soniya o'zgartirish",
        es_doc="<segundos> - Congela la protección de la API durante N segundos",
    )
    async def suspend_api_protect(self, message: Message):
        """<time in seconds> - Suspend API Ratelimiter for n seconds"""
        args = utils.get_args_raw(message)

        if not args or not args.isdigit():
            await utils.answer(message, self.strings("args_invalid"))
            return

        self._suspend_until = time.perf_counter() + int(args)
        await utils.answer(message, self.strings("suspended_for").format(args))

    @loader.command(
        ru_doc="Включить/выключить защиту API",
        de_doc="API-Schutz einschalten / ausschalten",
        tr_doc="API korumasını aç / kapat",
        uz_doc="API himoyasini yoqish / o'chirish",
        es_doc="Activar / desactivar la protección de API",
    )
    async def api_fw_protection(self, message: Message):
        """Toggle API Ratelimiter"""
        await self.inline.form(
            message=message,
            text=self.strings("u_sure"),
            reply_markup=[
                {"text": self.strings("btn_no"), "action": "close"},
                {"text": self.strings("btn_yes"), "callback": self._finish},
            ],
        )

    @property
    def _pin(self) -> str:
        return logging.getLogger().handlers[0].web_debugger.pin

    async def _show_pin(self, call: InlineCall):
        await call.answer(f"Werkzeug PIN: {self._pin}", show_alert=True)

    @loader.command(
        ru_doc="Показать PIN Werkzeug",
        de_doc="PIN-Werkzeug anzeigen",
        tr_doc="PIN aracını göster",
        uz_doc="PIN vositasi ko'rsatish",
        es_doc="Mostrar herramienta PIN",
    )
    async def debugpin(self, message: Message):
        """Show the Werkzeug PIN"""
        await self.inline.form(
            message=message,
            text=self.strings("web_pin"),
            reply_markup={
                "text": self.strings("web_pin_btn"),
                "callback": self._show_pin,
            },
        )

    async def _finish(self, call: InlineCall):
        state = self.get("disable_protection", True)
        self.set("disable_protection", not state)
        await call.edit(self.strings("on" if state else "off"))
