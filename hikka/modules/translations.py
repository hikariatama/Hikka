#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

from .. import loader, utils, translations
from telethon.tl.types import Message
import logging

logger = logging.getLogger(__name__)


@loader.tds
class Translations(loader.Module):
    """Processes internal translations"""

    strings = {
        "name": "Translations",
        "lang_saved": "{} <b>Language saved!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Translate pack"
            " saved!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Incorrect language"
            " specified</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Translations reset"
            " to default ones</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Invalid pack format"
            " in url</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>You need to specify"
            " valid url containing a langpack</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Command output seems"
            " to be too long, so it's sent in file.</b>"
        ),
        "opening_form": " <b>Opening form...</b>",
        "opening_gallery": " <b>Opening gallery...</b>",
        "opening_list": " <b>Opening list...</b>",
        "inline403": "🚫 <b>You can't send inline units in this chat</b>",
        "invoke_failed": "<b>🚫 Unit invoke failed! More info in logs</b>",
        "show_inline_cmds": "📄 Show all available inline commands",
        "no_inline_cmds": "You have no available commands",
        "no_inline_cmds_msg": (
            "<b>😔 There are no available inline commands or you lack access to them</b>"
        ),
        "inline_cmds": "ℹ️ You have {} available command(-s)",
        "inline_cmds_msg": "<b>ℹ️ Available inline commands:</b>\n\n{}",
        "run_command": "🏌️ Run command",
        "command_msg": "<b>🌘 Command «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Command «{}»",
        "button403": "You are not allowed to press this button!",
        "keep_id": "⚠️ Do not remove ID! {}",
    }

    strings_ru = {
        "lang_saved": "{} <b>Язык сохранён!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Пакет переводов"
            " сохранён!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Указан неверный"
            " язык</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Переводы сброшены"
            " на стандартные</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Неверный формат"
            " пакета переводов в ссылке</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Вы должны указать"
            " ссылку, содержащую пакет переводов</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Вывод команды слишком"
            " длинный, поэтому он отправлен в файле.</b>"
        ),
        "opening_form": " <b>Открываю форму...</b>",
        "opening_gallery": " <b>Открываю галерею...</b>",
        "opening_list": " <b>Открываю список...</b>",
        "inline403": "🚫 <b>Вы не можете отправлять встроенные элементы в этом чате</b>",
        "invoke_failed": "<b>🚫 Вызов модуля не удался! Подробнее в логах</b>",
        "show_inline_cmds": "📄 Показать все доступные встроенные команды",
        "no_inline_cmds": "У вас нет доступных inline команд",
        "no_inline_cmds_msg": (
            "<b>😔 Нет доступных inline команд или у вас нет доступа к ним</b>"
        ),
        "inline_cmds": "ℹ️ У вас {} доступная(-ых) команда(-ы)",
        "inline_cmds_msg": "<b>ℹ️ Доступные inline команды:</b>\n\n{}",
        "run_command": "🏌️ Выполнить команду",
        "command_msg": "<b>🌘 Команда «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Команда «{}»",
        "button403": "Вы не можете нажать на эту кнопку!",
        "keep_id": "⚠️ Не удаляйте ID! {}",
    }

    strings_de = {
        "lang_saved": "{} <b>Sprache gespeichert!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Übersetzungs"
            " Paket gespeichert!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Falsche Sprache"
            " angegeben</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Übersetzungen"
            " auf Standard zurückgesetzt</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Ungültiges"
            " Übersetzungs Paket in der URL</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Sie müssen eine"
            " gültige URL angeben, die ein Übersetzungs Paket enthält</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Befehlsausgabe scheint"
            " zu lang zu sein, daher wird sie in einer Datei gesendet.</b>"
        ),
        "opening_form": " <b>Formular wird geöffnet...</b>",
        "opening_gallery": " <b>Galerie wird geöffnet...</b>",
        "opening_list": " <b>Liste wird geöffnet...</b>",
        "inline403": "🚫 <b>Sie können Inline-Einheiten in diesem Chat nicht senden</b>",
        "invoke_failed": (
            "<b>🚫 Modulaufruf fehlgeschlagen! Weitere Informationen in den"
            " Protokollen</b>"
        ),
        "show_inline_cmds": "📄 Zeige alle verfügbaren Inline-Befehle",
        "no_inline_cmds": "Sie haben keine verfügbaren Inline-Befehle",
        "no_inline_cmds_msg": (
            "<b>😔 Keine verfügbaren Inline-Befehle oder Sie haben keinen Zugriff"
            " auf sie</b>"
        ),
        "inline_cmds": "ℹ️ Sie haben {} verfügbare(n) Befehl(e)",
        "inline_cmds_msg": "<b>ℹ️ Verfügbare Inline-Befehle:</b>\n\n{}",
        "run_command": "🏌️ Befehl ausführen",
        "command_msg": "<b>🌘 Befehl «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Befehl «{}»",
        "button403": "Sie können auf diese Schaltfläche nicht klicken!",
        "keep_id": "⚠️ Löschen sie das ID nicht! {}",
    }

    strings_tr = {
        "lang_saved": "{} <b>Dil kaydedildi!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Çeviri paketi"
            " kaydedildi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Yanlış dil"
            " belirtildi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Çeviriler varsayılan"
            " hale getirildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL'deki çeviri"
            " paketi geçersiz</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Geçerli bir URL"
            " belirtmelisiniz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Komut çıktısı çok uzun"
            " görünüyor, bu yüzden dosya olarak gönderildi.</b>"
        ),
        "opening_form": " <b>Form açılıyor...</b>",
        "opening_gallery": " <b>Galeri açılıyor...</b>",
        "opening_list": " <b>Liste açılıyor...</b>",
        "inline403": "🚫 <b>Bu sohbete satır içi birimler gönderemezsin</b>",
        "invoke_failed": (
            "<b>🚫 Modül çağrısı başarısız! Kayıtlardan daha fazla bilgiye"
            " erişebilirsin</b>"
        ),
        "show_inline_cmds": "📄 Tüm kullanılabilir inline komutlarını göster",
        "no_inline_cmds": "Kullanılabilir inline komutunuz yok",
        "no_inline_cmds_msg": (
            "<b>😔 Kullanılabilir inline komutunuz yok veya erişiminiz yok</b>"
        ),
        "inline_cmds": "ℹ️ {} kullanılabilir komutunuz var",
        "inline_cmds_msg": "<b>ℹ️ Kullanılabilir inline komutlar:</b>\n\n{}",
        "run_command": "🏌️ Komutu çalıştır",
        "command_msg": "<b>🌘 Komut «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Komut «{}»",
        "button403": "Bu düğmeye basamazsınız!",
        "keep_id": "⚠️ ID'yi silmeyin! {}",
    }

    strings_uz = {
        "lang_saved": "{} <b>Til saqlandi!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Tarjima paketi"
            " saqlandi!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Noto'g'ri til"
            " belgilandi</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Tarjimalar"
            " standart holatga qaytarildi</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL'dagi tarjima"
            " paketi noto'g'ri</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Siz noto'g'ri URL"
            " belirtdingiz</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>Bajarilgan buyruq"
            " natijasi juda uzun, shuning uchun fayl sifatida yuborildi.</b>"
        ),
        "opening_form": " <b>Formani ochish...</b>",
        "opening_gallery": " <b>Galeriyani ochish...</b>",
        "opening_list": " <b>Ro'yxatni ochish...</b>",
        "inline403": (
            "🚫 <b>Siz bu guruhda inline obyektlarni yuborishingiz mumkin emas</b>"
        ),
        "invoke_failed": (
            "<b>🚫 Modulni chaqirish muvaffaqiyatsiz! Batafsil ma'lumotlar"
            " jurnallarda</b>"
        ),
        "show_inline_cmds": "📄 Barcha mavjud inline buyruqlarini ko'rsatish",
        "no_inline_cmds": "Sizda mavjud inline buyruqlar yo'q",
        "no_inline_cmds_msg": (
            "<b>😔 Sizda mavjud inline buyruqlar yo'q yoki ularga kirish huquqingiz"
            " yo'q</b>"
        ),
        "inline_cmds": "ℹ️ Sizda {} mavjud buyruq bor",
        "inline_cmds_msg": "<b>ℹ️ Mavjud inline buyruqlar:</b>\n\n{}",
        "run_command": "🏌️ Buyruqni bajarish",
        "command_msg": "<b>🌘 Buyruq «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 Buyruq «{}»",
        "button403": "Siz ushbu tugmani bosib bo'lmaysiz!",
        "keep_id": "⚠️ ID-ni o'chirmang! {}",
    }

    strings_hi = {
        "lang_saved": "{} <b>भाषा सहेजा गया!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>अनुवाद पैक"
            " सहेजा गया!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>गलत भाषा"
            " निर्दिष्ट किया गया</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>अनुवाद डिफ़ॉल्ट"
            " पर रीसेट किए गए</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>यूआरएल में गलत"
            " अनुवाद पैक निर्दिष्ट किया गया</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>आपने गलत यूआरएल"
            " निर्दिष्ट किया है</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>कमांड आउटपुट बहुत लंबा"
            " लगता है, इसलिए फ़ाइल में भेजा जाता है.</b>"
        ),
        "opening_form": " <b>फॉर्म खोल रहा है...</b>",
        "opening_gallery": " <b>गैलरी खोल रहा है...</b>",
        "opening_list": " <b>सूची खोल रहा है...</b>",
        "inline403": "🚫 <b>आप इस ग्रुप में इनलाइन आइटम नहीं भेज सकते हैं</b>",
        "invoke_failed": "<b>🚫 मॉड्यूल इन्वोक विफल! विस्तृत जानकारी लॉग में है</b>",
        "show_inline_cmds": "📄 सभी उपलब्ध इनलाइन कमांड दिखाएं",
        "no_inline_cmds": "आपके पास कोई उपलब्ध इनलाइन कमांड नहीं हैं",
        "no_inline_cmds_msg": (
            "<b>😔 आपके पास कोई उपलब्ध इनलाइन कमांड या इनलाइन कमांड के लिए अनुमति नहीं"
            " हैं</b>"
        ),
        "inline_cmds": "ℹ️ आपके पास {} उपलब्ध कमांड हैं",
        "inline_cmds_msg": "<b>ℹ️ उपलब्ध इनलाइन कमांड:</b>\n\n{}",
        "run_command": "🏌️ कमांड चलाएं",
        "command_msg": "<b>🌘 कमांड «{}»</b>\n\n<i>{}</i>",
        "command": "🌘 कमांड «{}»",
        "button403": "आप इस बटन को दबा नहीं सकते!",
        "button404": "यह बटन अब उपलब्ध नहीं है!",
    }

    strings_jp = {
        "lang_saved": "{} <b>言語が保存されました！</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>翻訳パック が保存されました！</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>不正確な言語 が指定されました</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>翻訳がデフォルトに"
            " リセットされました</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URLの翻訳パックが 不正確です</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>不正確なURLを指定しました</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>コマンドの出力が"
            " 長すぎるため、ファイルとして送信されました.</b>"
        ),
        "opening_form": " <b>フォームを開いています...</b>",
        "opening_gallery": " <b>ギャラリーを開いています...</b>",
        "opening_list": " <b>リストを開いています...</b>",
        "inline403": "🚫 <b>あなたはこのグループでインラインアイテムを送信することはできません</b>",
        "invoke_failed": "<b>🚫 モジュールの呼び出しが失敗しました！ 詳細はログに記録されています</b>",
        "show_inline_cmds": "📄 すべての利用可能なインラインコマンドを表示",
        "no_inline_cmds": "利用可能なインラインコマンドはありません",
        "no_inline_cmds_msg": "<b>😔 利用可能なインラインコマンドまたはインラインコマンドへのアクセス権がありません</b>",
        "inline_cmds": "ℹ️ 利用可能なコマンドが {} あります",
        "inline_cmds_msg": "<b>ℹ️ 利用可能なインラインコマンド:</b>\n\n{}",
        "run_command": "🏌️ コマンドを実行",
        "command_msg": "<b>🌘 コマンド「{}」</b>\n\n<i>{}</i>",
        "command": "🌘 コマンド「{}」",
        "button403": "あなたはこのボタンを押すことはできません！",
        "button404": "このボタンはもう利用できません！",
    }

    strings_kr = {
        "lang_saved": "{} <b>언어가 저장되었습니다!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>번역 팩이 저장되었습니다!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>잘못된 언어가 지정되었습니다</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>번역이 기본값으로 재설정되었습니다</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL의 번역 팩이 잘못되었습니다</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>잘못된 URL을 지정하셨습니다</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>명령의 출력이"
            " 너무 깁니다. 파일로 전송되었습니다.</b>"
        ),
        "opening_form": " <b>폼을 열고 있습니다...</b>",
        "opening_gallery": " <b>갤러리를 열고 있습니다...</b>",
        "opening_list": " <b>리스트를 열고 있습니다...</b>",
        "inline403": "🚫 <b>이 그룹에서 인라인 아이템을 보내는 것은 허용되지 않습니다</b>",
        "invoke_failed": "<b>🚫 모듈 호출이 실패했습니다! 자세한 내용은 로그에 기록되어 있습니다</b>",
        "show_inline_cmds": "📄 모든 사용 가능한 인라인 명령을 표시",
        "no_inline_cmds": "사용 가능한 인라인 명령이 없습니다",
        "no_inline_cmds_msg": "<b>😔 사용 가능한 인라인 명령이 없거나 인라인 명령에 대한 액세스 권한이 없습니다</b>",
        "inline_cmds": "ℹ️ 사용 가능한 명령이 {} 개 있습니다",
        "inline_cmds_msg": "<b>ℹ️ 사용 가능한 인라인 명령:</b>\n\n{}",
        "run_command": "🏌️ 명령을 실행",
        "command_msg": "<b>🌘 명령 '{}' </b>\n\n<i>{}</i>",
        "command": "🌘 명령 '{}'",
        "button403": "이 버튼을 누를 수 없습니다!",
        "button404": "이 버튼은 더 이상 사용할 수 없습니다!",
    }

    strings_ar = {
        "lang_saved": "{} <b>تم حفظ اللغة!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>تم حفظ حزمة"
            " الترجمة!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>تم تحديد لغة"
            " غير صحيحة</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>تم إعادة تعيين"
            " الترجمة إلى الافتراضي</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>تم تحديد حزمة"
            " الترجمة غير صحيحة</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>تم تحديد URL"
            " غير صحيح</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>تم تجاوز الناتج"
            " للأمر. تم إرساله كملف.</b>"
        ),
        "opening_form": " <b>يتم فتح النموذج...</b>",
        "opening_gallery": " <b>يتم فتح الصالة...</b>",
        "opening_list": " <b>يتم فتح القائمة...</b>",
        "inline403": "🚫 <b>لا يسمح بإرسال عناصر الواجهة السطحية في هذه المجموعة</b>",
        "invoke_failed": "<b>🚫 فشل استدعاء الوحدة! انظر السجل للحصول على تفاصيل</b>",
        "show_inline_cmds": "📄 عرض جميع الأوامر المتاحة",
        "no_inline_cmds": "لا توجد أوامر متاحة",
        "no_inline_cmds_msg": (
            "<b>😔 لا توجد أوامر متاحة أو ليس لديك إذن للوصول إلى الأوامر</b>"
        ),
        "inline_cmds": "ℹ️ {} أوامر متاحة",
        "inline_cmds_msg": "<b>ℹ️ أوامر متاحة:</b>\n\n{}",
        "run_command": "🏌️ تشغيل الأمر",
        "command_msg": "<b>🌘 الأمر '{}' </b>\n\n<i>{}</i>",
        "command": "🌘 الأمر '{}'",
        "button403": "لا يمكنك الضغط على هذا الزر!",
        "button404": "لا يمكنك الضغط على هذا الزر بعد الآن!",
    }

    strings_es = {
        "lang_saved": "{} <b>¡Idioma guardado!</b>",
        "pack_saved": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>¡Paquete de"
            " traducción guardado!</b>"
        ),
        "incorrect_language": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Idioma"
            " incorrecto seleccionado</b>"
        ),
        "lang_removed": (
            "<emoji document_id=5368324170671202286>👍</emoji> <b>Restablecer la"
            " traducción a los valores predeterminados</b>"
        ),
        "check_pack": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>Paquete de"
            " traducción seleccionado incorrecto</b>"
        ),
        "check_url": (
            "<emoji document_id=5436162517686557387>🚫</emoji> <b>URL incorrecta"
            " seleccionada</b>"
        ),
        "too_long": (
            "<emoji document_id=5433653135799228968>📁</emoji> <b>El resultado del"
            " comando excede el límite. Enviado como archivo.</b>"
        ),
        "opening_form": " <b>Abriendo formulario...</b>",
        "opening_gallery": " <b>Abriendo galería...</b>",
        "opening_list": " <b>Abriendo lista...</b>",
        "inline403": (
            "🚫 <b>No se permiten elementos de interfaz de usuario en este grupo</b>"
        ),
        "invoke_failed": (
            "<b>🚫 ¡Error al invocar la unidad! Consulte el registro"
            " para obtener más detalles</b>"
        ),
        "show_inline_cmds": "📄 Mostrar todos los comandos disponibles",
        "no_inline_cmds": "No hay comandos disponibles",
        "no_inline_cmds_msg": (
            "<b>😔 No hay comandos disponibles o no tienes permiso para acceder a"
            " los comandos</b>"
        ),
        "inline_cmds": "ℹ️ {} comandos disponibles",
        "inline_cmds_msg": "<b>ℹ️ Comandos disponibles:</b>\n\n{}",
        "run_command": "🏌️ Ejecutar comando",
        "command_msg": "<b>🌘 Comando '{}'</b>\n\n<i>{}</i>",
        "command": "🌘 Comando '{}'",
        "button403": "¡No puedes presionar este botón!",
        "button404": "¡No puedes presionar este botón ahora!",
    }

    @loader.command(
        ru_doc="[языки] - Изменить стандартный язык",
        de_doc="[Sprachen] - Ändere die Standard-Sprache",
        tr_doc="[Diller] - Varsayılan dili değiştir",
        uz_doc="[til] - Standart tili o'zgartirish",
        hi_doc="[भाषाएं] - डिफ़ॉल्ट भाषा बदलें",
        jp_doc="[言語] - デフォルトの言語を変更します",
        kr_doc="[언어] - 기본 언어를 변경합니다",
        ar_doc="[اللغات] - تغيير اللغة الافتراضية",
        es_doc="[Idiomas] - Cambiar el idioma predeterminado",
    )
    async def setlang(self, message: Message):
        """[languages in the order of priority] - Change default language"""
        args = utils.get_args_raw(message)
        if not args or any(len(i) != 2 for i in args.split(" ")):
            await utils.answer(message, self.strings("incorrect_language"))
            return

        self._db.set(translations.__name__, "lang", args.lower())
        await self.translator.init()

        for module in self.allmodules.modules:
            try:
                module.config_complete(reload_dynamic_translate=True)
            except Exception as e:
                logger.debug(
                    "Can't complete dynamic translations reload of %s due to %s",
                    module,
                    e,
                )

        fixmap = {"en": "gb", "hi": "in"}

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                "".join(
                    [
                        utils.get_lang_flag(fixmap.get(lang, lang))
                        for lang in args.lower().split(" ")
                    ]
                )
            ),
        )

    @loader.command(
        ru_doc="[ссылка на пак | пустое чтобы удалить] - Изменить внешний пак перевода",
        de_doc=(
            "[Link zum Paket | leer um zu entfernen] - Ändere das externe Übersetzungs"
            " Paket"
        ),
        tr_doc=(
            "[Çeviri paketi bağlantısı | boş bırakmak varsayılan hale getirir] - Harici"
            " çeviri paketini değiştir"
        ),
        uz_doc=(
            "[tarjima paketi havolasini | bo'sh qoldirish standart holatga qaytaradi] -"
            " Tashqi tarjima paketini o'zgartirish"
        ),
        hi_doc="[अनुवाद पैक का लिंक | खाली छोड़ दें] - बाहरी अनुवाद पैक बदलें",
        jp_doc="[パッケージへのリンク | 空白で削除] - 外部翻訳パッケージを変更します",
        kr_doc="[패키지 링크 | 비워두면 삭제] - 외부 번역 패키지를 변경합니다",
        ar_doc="[رابط الحزمة | اتركه فارغا لحذفه] - تغيير حزمة الترجمة الخارجية",
        es_doc="[Enlace al paquete | vacío para eliminar] - Cambiar el paquete de",
    )
    async def dllangpackcmd(self, message: Message):
        """[link to a langpack | empty to remove] - Change Hikka translate pack (external)
        """
        args = utils.get_args_raw(message)

        if not args:
            self._db.set(translations.__name__, "pack", False)
            await self.translator.init()
            await utils.answer(message, self.strings("lang_removed"))
            return

        if not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        self._db.set(translations.__name__, "pack", args)
        success = await self.translator.init()

        for module in self.allmodules.modules:
            try:
                module.config_complete(reload_dynamic_translate=True)
            except Exception as e:
                logger.debug(
                    "Can't complete dynamic translations reload of %s due to %s",
                    module,
                    e,
                )

        await utils.answer(
            message,
            self.strings("pack_saved" if success else "check_pack"),
        )
