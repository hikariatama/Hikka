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

from telethon.tl.types import Message
from telethon.tl import functions
from telethon.tl.tlobject import TLRequest

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
            "<emoji document_id=6319093650693293883>☣️</emoji>"
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
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Invalid arguments</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood Protection"
            " is disabled for {} seconds</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>This action will"
            " expose your account to flooding Telegram API.</b> <i>In order to confirm,"
            " that you really know, what you are doing, complete this simple test -"
            " find the emoji, differing from others</i>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protection enabled</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protection"
            " disabled</b>"
        ),
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Are you sure?</b>"
        ),
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
    }

    strings_ru = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
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
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Неверные"
            " аргументы</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Защита API отключена"
            " на {} секунд</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Это действие"
            " открывает юзерботу возможность флудить Telegram API.</b> <i>Для того,"
            " чтобы убедиться, что ты действительно уверен в том, что делаешь - реши"
            " простенький тест - найди отличающийся эмодзи.</i>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>Защита включена</b>",
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Защита отключена</b>"
        ),
        "u_sure": "<emoji document_id=6319093650693293883>☣️</emoji> <b>Ты уверен?</b>",
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
    }

    strings_de = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
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
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Ungültige"
            " Argumente</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood"
            " Protection ist für {} Sekunden deaktiviert</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Dieser"
            " Vorgang wird deinen Account ermöglichen, die Telegram API zu"
            " überfluten.</b> <i>Um sicherzustellen, dass du wirklich weißt, was"
            " du tust, beende diesen einfachen Test - findest du das Emoji, das von"
            " den anderen abweicht?</i>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Schutz aktiviert</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Schutz deaktiviert</b>"
        ),
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Bist du sicher?</b>"
        ),
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
    }

    strings_tr = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
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
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Geçersiz"
            " argümanlar</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood koruması {}"
            " saniyeliğine durduruldu.</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Bu eylem"
            " Thesabınızın Telegram API Flood’u yapabilmesine izin verecektir.</b>"
            " <i>Ne yaptığını bildiğinizi onaylamak için bu basit testi çözün."
            " - Diğerlerinden farklı olan emojiyi seç</i>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Koruma"
            " aktifleştirildi.</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Koruma"
            " de-aktifleştirildi</b>"
        ),
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Emin misin?</b>"
        ),
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
    }

    strings_hi = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
            " <b>चेतावनी!</b>\n\nइस खाते के लिए विन्यास में निर्दिष्ट सीमा सीमा"
            " पार कर गए हैं। टेलीग्राम एपीआई फ्लडिंग को रोकने के लिए, यह"
            " <b>सभी userbot</b> को {} सेकंड तक जमा कर दिया गया है। अधिक"
            " जानकारी के लिए नीचे दिए गए फ़ाइल पढ़ें।\n\nअपनी सहायता के लिए"
            " <code>{prefix}support</code> समूह का उपयोग करें!\n\nयदि आपको लगता है"
            " यह उपयोगकर्ता बॉट की योजित व्यवहार है, तो बस टाइमर समाप्त होने"
            " तक इंतजार करें और अगली बार एक ऐसी संसाधन ज्यादा खर्च करने वाली"
            " ऑपरेशन को योजित करने के लिए <code>{prefix}suspend_api_protect</code>"
            " &lt;सेकंड&gt; का उपयोग करें।"
        ),
        "args_invalid": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>अमान्य तर्क</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood"
            " सुरक्षा को {} सेकंड के लिए अक्षम कर दिया गया है</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>यह ऑपरेशन"
            " टेलीग्राम एपीआई को फ्लड करने की अनुमति देगा।</b> <i>आप क्या कर रहे हैं"
            " यह सुनिश्चित करने के लिए एक आसान परीक्षण को हल करें, जिसमें अलग"
            " एमोजी का पता लगाएं?</i>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>सुरक्षा सक्षम</b>",
        "off": "<emoji document_id=5458450833857322148>👌</emoji> <b>सुरक्षा अक्षम</b>",
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>क्या आप"
            " सुनिश्चित हैं?</b>"
        ),
        "_cfg_time_sample": "प्रति सेकंड गिने जाने वाले अनुरोधों की समय सीमा",
        "_cfg_threshold": "सुरक्षा सक्षम करने के लिए मान सीमित करें",
        "_cfg_local_floodwait": (
            "यूजरबॉट को इस संख्या के सेकंड के लिए फ्रीज करें जब सीमा मान पार हो जाए"
        ),
        "_cfg_forbidden_methods": "सभी बाहरी मॉड्यूल में निषिद्ध तरीके",
        "btn_no": "🚫 नहीं",
        "btn_yes": "✅ हाँ",
    }

    strings_uz = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
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
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Noto'g'ri"
            " argument</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>API Flood"
            " himoya {} sekund uchun to'xtatildi</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Ushbu amal Telegram"
            " API-ni flood qilishga ruxsat beradi.</b> <i>Siz qanday ish"
            " bajarayotganingizni tekshirish uchun oson testni bajarishga harakat"
            " qiling, emojilarni aniqlash uchun?</i>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>Himoya yoqildi</b>",
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Himoya o'chirildi</b>"
        ),
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Siz"
            " ishonchingiz komilmi?</b>"
        ),
        "_cfg_time_sample": "Sekundda qabul qilinadigan so'rovlar soni chegarasi",
        "_cfg_threshold": "Himoya yoqish uchun qiymatni chegaralash",
        "_cfg_local_floodwait": (
            "Foydalanuvchi botni ushbu soniya davomida blokirovka qiladi, agar"
            " chegaralar qiymati oshsa"
        ),
        "_cfg_forbidden_methods": "Barcha tashqi modullarda taqiqlangan usullar",
        "btn_no": "🚫 Yo'q",
        "btn_yes": "✅ Ha",
    }

    strings_jp = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
            " <b>警告！</b>\n\nこのアカウントの設定では、以下の制限が設定されています。\n\n"
            "Telegram APIのフラッドを防ぐために、この<b>すべてのユーザーボット</b>は"
            " {}秒間ブロックされます。詳細については、下記のファイルをご覧ください。\n\n"
            "サポートについては、<code>{prefix}support</code>グループをご利用ください！\n\n"
            "アカウントが実行する必要のあるアクションを許可する場合は、"
            "<code>{prefix}suspend_api_protect</code>を使用してブロックを解除するだけです。"
        ),
        "args_invalid": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>無効な引数</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji>"
            " <b>APIフラッド保護が{}秒間無効になりました</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>このアクションは、"
            "Telegram APIをフラッドさせることができます。</b> <i>あなたが何をしているかを"
            "確認するために、簡単なテストを実行するには、次のように入力してください。</i>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>保護が有効になりました</b>",
        "off": "<emoji document_id=5458450833857322148>👌</emoji> <b>保護が無効になりました</b>",
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>本当によろしいですか？</b>"
        ),
        "_cfg_time_sample": "秒あたりの許可されたリクエスト数の制限",
        "_cfg_threshold": "制限を超えた場合の値",
        "_cfg_local_floodwait": "ユーザーがこの秒数以内にボットをブロックする場合",
        "_cfg_forbidden_methods": "すべての外部モジュールで禁止されているメソッド",
        "btn_no": "🚫 いいえ",
        "btn_yes": "✅ はい",
    }

    strings_kr = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
            " <b>경고！</b>\n\n이 계정의 설정에 따르면, 다음 제한이 설정됩니다.\n\n"
            "이 <b>모든 사용자 봇</b>은 Telegram API의 플러드를 방지하기 위해"
            " {}초 동안 차단됩니다. 자세한 내용은 아래 파일을 참조하십시오.\n\n"
            "지원에 대해서는 <code>{prefix}support</code> 그룹을 사용하십시오!\n\n"
            "계정이 실행해야하는 작업을 허용하려면, <code>{prefix}suspend_api_protect</code>를"
            "사용하여 차단을 해제하십시오."
        ),
        "args_invalid": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>잘못된인수</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji>"
            " <b>API 플러드 보호가 {}초간 비활성화되었습니다</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>이 작업은"
            "Telegram API를 플러드시킬 수 있습니다.</b> <i>당신이 무엇을 하는지 확인하기 위해,"
            "간단한 테스트를 실행하려면 다음과 같이 입력하십시오.</i>"
        ),
        "on": "<emoji document_id=5458450833857322148>👌</emoji> <b>보호가 활성화되었습니다</b>",
        "off": "<emoji document_id=5458450833857322148>👌</emoji> <b>보호가 비활성화되었습니다</b>",
        "u_sure": "<emoji document_id=6319093650693293883>☣️</emoji> <b>확실합니까?</b>",
        "_cfg_time_sample": "허용되는 요청 수의 제한 초",
        "_cfg_threshold": "제한을 초과한 경우의 값",
        "_cfg_local_floodwait": "사용자가 이 초 이내에 봇을 차단하는 경우",
        "_cfg_forbidden_methods": "모든 외부 모듈에서 금지된 메서드",
        "btn_no": "🚫 아니요",
        "btn_yes": "✅ 예",
    }

    strings_ar = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>تحذير!</b>\n\nحسب"
            " إعدادات هذا الحساب، فإن الحدود التالية ستتم تطبيقها.\n\nسيتم حظر <b>جميع"
            " بوتات المستخدمين</b> لمدة {} ثانية لمنع تجاوز الحد الأقصى لمتطلبات"
            " Telegram API. لمزيد من المعلومات، راجع الملف التالي.\n\nللمساعدة، استخدم"
            " مجموعة <code>{prefix}support</code>!\n\nللسماح للحساب بالعمل، استخدم"
            " <code>{prefix}suspend_api_protect</code> لإلغاء الحظر."
        ),
        "args_invalid": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>معلمات غير صالحة</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji>"
            " <b>تم تعطيل حماية API لمدة {} ثانية</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>هذا الأمر قد يؤدي"
            " إلىتجاوز حدود Telegram API.</b> <i>للتحقق من ما تفعله، يمكنك تشغيل اختبار"
            " بسيطبالإضافة إلى الأمر التالي.</i>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>تم تفعيل الحماية</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>تم تعطيل الحماية</b>"
        ),
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>هل أنت متأكد؟</b>"
        ),
        "_cfg_time_sample": "المدة بالثواني التي يتم فيها تجاوزها حد المتطلبات",
        "_cfg_threshold": "قيمة تجاوزها الحد",
        "_cfg_local_floodwait": "المدة بالثواني التي يتم فيها حظر المستخدم للبوت",
        "_cfg_forbidden_methods": "الأوامر الممنوعة من قبل كل الإضافات الخارجية",
        "btn_no": "🚫 لا",
        "btn_yes": "✅ نعم",
    }

    strings_es = {
        "warning": (
            "<emoji document_id=6319093650693293883>☣️</emoji>"
            " <b>¡Advertencia!</b>\n\nDe acuerdo con la configuración de esta cuenta,"
            " las siguientes limitaciones serán aplicadas.\n\nSe bloqueará <b>a todos"
            " los bots de los usuarios</b> por {} segundos para evitar el exceso de las"
            " limitaciones de Telegram API. Para más información, consulta el archivo"
            " siguiente.\n\nPara obtener ayuda, use el grupo"
            " <code>{prefix}support</code>!\n\nPara permitir que la cuenta funcione,"
            " use <code>{prefix}suspend_api_protect</code> para desbloquear."
        ),
        "args_invalid": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Argumentos"
            " inválidos</b>"
        ),
        "suspended_for": (
            "<emoji document_id=5458450833857322148>👌</emoji>"
            " <b>Se ha desactivado la protección de API por {} segundos</b>"
        ),
        "test": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>Este comando puede"
            " llevar a exceder las limitaciones de Telegram API.</b> <i>Para comprobar"
            " que estás haciendo, puedes ejecutar una prueba simple agregando el"
            " siguiente comando.</i>"
        ),
        "on": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protección"
            " activada</b>"
        ),
        "off": (
            "<emoji document_id=5458450833857322148>👌</emoji> <b>Protección"
            " desactivada</b>"
        ),
        "u_sure": (
            "<emoji document_id=6319093650693293883>☣️</emoji> <b>¿Estás seguro?</b>"
        ),
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
        hi_doc="<सेकंड> - API सुरक्षा को N सेकंड जमा करें",
        uz_doc="<soniya> - API himoyasini N soniya o'zgartirish",
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
        hi_doc="API सुरक्षा चालू / बंद करें",
        uz_doc="API himoyasini yoqish / o'chirish",
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

    async def _finish(self, call: InlineCall):
        state = self.get("disable_protection", True)
        self.set("disable_protection", not state)
        await call.edit(self.strings("on" if state else "off"))
