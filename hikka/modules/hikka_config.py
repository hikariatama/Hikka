#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import ast
import functools
from math import ceil
import typing

from telethon.tl.types import Message

from .. import loader, utils, translations
from ..inline.types import InlineCall

# Everywhere in this module, we use the following naming convention:
# `obj_type` of non-core module = False
# `obj_type` of core module = True
# `obj_type` of library = "library"


@loader.tds
class HikkaConfigMod(loader.Module):
    """Interactive configurator for Hikka Userbot"""

    strings = {
        "name": "HikkaConfig",
        "choose_core": "🎚 <b>Choose a category</b>",
        "configure": "🎚 <b>Choose a module to configure</b>",
        "configure_lib": "🪴 <b>Choose a library to configure</b>",
        "configuring_mod": (
            "🎚 <b>Choose config option for mod</b> <code>{}</code>\n\n<b>Current"
            " options:</b>\n\n{}"
        ),
        "configuring_lib": (
            "🪴 <b>Choose config option for library</b> <code>{}</code>\n\n<b>Current"
            " options:</b>\n\n{}"
        ),
        "configuring_option": (
            "🎚 <b>Configuring option </b><code>{}</code><b> of mod"
            " </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Default: {}</b>\n\n<b>Current:"
            " {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>Configuring option </b><code>{}</code><b> of library"
            " </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Default: {}</b>\n\n<b>Current:"
            " {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>Option </b><code>{}</code><b> of module </b><code>{}</code><b>"
            " saved!</b>\n<b>Current: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>Option </b><code>{}</code><b> of library </b><code>{}</code><b>"
            " saved!</b>\n<b>Current: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>Option </b><code>{}</code><b> of module </b><code>{}</code><b> has"
            " been reset to default</b>\n<b>Current: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>Option </b><code>{}</code><b> of library </b><code>{}</code><b> has"
            " been reset to default</b>\n<b>Current: {}</b>"
        ),
        "args": "🚫 <b>You specified incorrect args</b>",
        "no_mod": "🚫 <b>Module doesn't exist</b>",
        "no_option": "🚫 <b>Configuration option doesn't exist</b>",
        "validation_error": "🚫 <b>You entered incorrect config value. \nError: {}</b>",
        "try_again": "🔁 Try again",
        "typehint": "🕵️ <b>Must be a{eng_art} {}</b>",
        "set": "set",
        "set_default_btn": "♻️ Reset default",
        "enter_value_btn": "✍️ Enter value",
        "enter_value_desc": "✍️ Enter new configuration value for this option",
        "add_item_desc": "✍️ Enter item to add",
        "remove_item_desc": "✍️ Enter item to remove",
        "back_btn": "👈 Back",
        "close_btn": "🔻 Close",
        "add_item_btn": "➕ Add item",
        "remove_item_btn": "➖ Remove item",
        "show_hidden": "🚸 Show value",
        "hide_value": "🔒 Hide value",
        "builtin": "🛰 Built-in",
        "external": "🛸 External",
        "libraries": "🪴 Libraries",
    }

    strings_ru = {
        "choose_core": "🎚 <b>Выбери категорию</b>",
        "configure": "🎚 <b>Выбери модуль для настройки</b>",
        "configure_lib": "🪴 <b>Выбери библиотеку для настройки</b>",
        "configuring_mod": (
            "🎚 <b>Выбери параметр для модуля</b> <code>{}</code>\n\n<b>Текущие"
            " настройки:</b>\n\n{}"
        ),
        "configuring_lib": (
            "🪴 <b>Выбери параметр для библиотеки</b> <code>{}</code>\n\n<b>Текущие"
            " настройки:</b>\n\n{}"
        ),
        "configuring_option": (
            "🎚 <b>Управление параметром </b><code>{}</code><b> модуля"
            " </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Стандартное:"
            " {}</b>\n\n<b>Текущее: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>Управление параметром </b><code>{}</code><b> библиотеки"
            " </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Стандартное:"
            " {}</b>\n\n<b>Текущее: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>Параметр </b><code>{}</code><b> модуля </b><code>{}</code><b>"
            " сохранен!</b>\n<b>Текущее: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>Параметр </b><code>{}</code><b> библиотеки </b><code>{}</code><b>"
            " сохранен!</b>\n<b>Текущее: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>Параметр </b><code>{}</code><b> модуля </b><code>{}</code><b>"
            " сброшен до значения по умолчанию</b>\n<b>Текущее: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>Параметр </b><code>{}</code><b> библиотеки </b><code>{}</code><b>"
            " сброшен до значения по умолчанию</b>\n<b>Текущее: {}</b>"
        ),
        "_cls_doc": "Интерактивный конфигуратор Hikka",
        "args": "🚫 <b>Ты указал неверные аргументы</b>",
        "no_mod": "🚫 <b>Модуль не существует</b>",
        "no_option": "🚫 <b>У модуля нет такого значения конфига</b>",
        "validation_error": (
            "🚫 <b>Введено некорректное значение конфига. \nОшибка: {}</b>"
        ),
        "try_again": "🔁 Попробовать еще раз",
        "typehint": "🕵️ <b>Должно быть {}</b>",
        "set": "поставить",
        "set_default_btn": "♻️ Значение по умолчанию",
        "enter_value_btn": "✍️ Ввести значение",
        "enter_value_desc": "✍️ Введи новое значение этого параметра",
        "add_item_desc": "✍️ Введи элемент, который нужно добавить",
        "remove_item_desc": "✍️ Введи элемент, который нужно удалить",
        "back_btn": "👈 Назад",
        "close_btn": "🔻 Закрыть",
        "add_item_btn": "➕ Добавить элемент",
        "remove_item_btn": "➖ Удалить элемент",
        "show_hidden": "🚸 Показать значение",
        "hide_value": "🔒 Скрыть значение",
        "builtin": "🛰 Встроенные",
        "external": "🛸 Внешние",
        "libraries": "🪴 Библиотеки",
    }

    strings_de = {
        "choose_core": "🎚 <b>Wähle eine Kategorie</b>",
        "configure": "🎚 <b>Modul zum Konfigurieren auswählen</b>",
        "configure_lib": "🪴 <b>Wählen Sie eine zu konfigurierende Bibliothek aus</b>",
        "configuring_mod": (
            "🎚 <b>Wählen Sie einen Parameter für das Modul aus</b>"
            " <code>{}</code>\n\n<b>Aktuell Einstellungen:</b>\n\n{}"
        ),
        "configuring_lib": (
            "🪴 <b>Wählen Sie eine Option für die Bibliothek aus</b>"
            " <code>{}</code>\n\n<b>Aktuell Einstellungen:</b>\n\n{}"
        ),
        "configuring_option": (
            "🎚 <b>Option </b><code>{}</code><b> des Moduls </b><code>{}</code>"
            "<b> konfigurieren</b>\n<i>ℹ️ {}</i>\n\n<b>Standard: {}</b>\n\n<b>"
            "Aktuell: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>Option </b><code>{}</code><b> der Bibliothek </b><code>{}</code>"
            "<b> konfigurieren</b>\n<i>ℹ️ {}</i>\n\n<b>Standard: {}</b>\n\n<b>"
            "Aktuell: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>Option </b><code>{}</code><b> des Moduls </b><code>{}</code>"
            "<b> gespeichert!</b>\n<b>Aktuell: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>Option </b><code>{}</code><b> der Bibliothek </b><code>{}</code>"
            "<b> gespeichert!</b>\n<b>Aktuell: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>Option </b><code>{}</code><b> des Moduls </b><code>{}</code>"
            "<b> auf den Standardwert zurückgesetzt</b>\n<b>Aktuell: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>Option </b><code>{}</code><b> der Bibliothek </b><code>{}</code>"
            "<b> auf den Standardwert zurückgesetzt</b>\n<b>Aktuell: {}</b>"
        ),
        "_cls_doc": "Interaktiver Konfigurator von Hikka",
        "args": "🚫 <b>Du hast falsche Argumente angegeben</b>",
        "no_mod": "🚫 <b>Modul existiert nicht</b>",
        "no_option": "🚫 <b>Modul hat keine solche Konfigurationsoption</b>",
        "validation_error": (
            "🚫 <b>Ungültiger Konfigurationswert eingegeben. \nFehler: {}</b>"
        ),
        "try_again": "🔁 Versuche es noch einmal",
        "typehint": "🕵️ <b>Sollte {} sein</b>",
        "set": "setzen",
        "set_default_btn": "♻️ Standardwert",
        "enter_value_btn": "✍️ Wert eingeben",
        "enter_value_desc": "✍️ Gib einen neuen Wert für diese Option ein",
        "add_item_desc": "✍️ Gib den hinzuzufügenden Eintrag ein",
        "remove_item_desc": "✍️ Gib den zu entfernenden Eintrag ein",
        "back_btn": "👈 Zurück",
        "close_btn": "🔻 Schließen",
        "add_item_btn": "➕ Element hinzufügen",
        "remove_item_btn": "➖ Element entfernen",
        "show_hidden": "🚸 Wert anzeigen",
        "hide_value": "🔒 Wert verbergen",
        "builtin": "🛰 Ingebaut",
        "external": "🛸 Extern",
        "libraries": "🪴 Bibliotheken",
    }

    strings_hi = {
        "choose_core": "🎚 <b>एक श्रेणी चुनें</b>",
        "configure": "🎚 <b>कॉन्फ़िगर करने के लिए एक मॉड्यूल चुनें</b>",
        "configure_lib": "🪴 <b>कॉन्फ़िगर करने के लिए लाइब्रेरी का चयन करें</b>",
        "configuring_mod": (
            "🎚 <b>मॉड्यूल के लिए एक पैरामीटर चुनें</b> <code>{}</code>\n\n<b>वर्तमान"
            " सेटिंग:</b>\n\n{}"
        ),
        "configuring_lib": (
            "🪴 <b>लाइब्रेरी के लिए एक विकल्प चुनें</b> <code>{}</code>\n\n<b>वर्तमान"
            " सेटिंग:</b>\n\n{}"
        ),
        "configuring_option": (
            "🎚 <b>विकल्प </b><code>{}</code><b> मॉड्यूल </b><code>{}</code>"
            "<b> कॉन्फ़िगर कर रहा है</b>\n<i>ℹ️ {}</i>\n\n<b>डिफ़ॉल्ट: {}</b>\n\n<b>"
            "वर्तमान: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>विकल्प </b><code>{}</code><b> लाइब्रेरी </b><code>{}</code>"
            "<b> कॉन्फ़िगर कर रहा है</b>\n<i>ℹ️ {}</i>\n\n<b>डिफ़ॉल्ट: {}</b>\n\n<b>"
            "वर्तमान: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>विकल्प </b><code>{}</code><b> मॉड्यूल </b><code>{}</code>"
            "<b> सहेजा गया!</b>\n<b>वर्तमान: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>विकल्प </b><code>{}</code><b> लाइब्रेरी </b><code>{}</code>"
            "<b> सहेजा गया!</b>\n<b>वर्तमान: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>विकल्प </b><code>{}</code><b> मॉड्यूल </b><code>{}</code>"
            "<b> डिफ़ॉल्ट मान पर रीसेट कर दिया गया</b>\n<b>वर्तमान: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>विकल्प </b><code>{}</code><b> लाइब्रेरी </b><code>{}</code>"
            "<b> डिफ़ॉल्ट मान पर रीसेट कर दिया गया</b>\n<b>वर्तमान: {}</b>"
        ),
        "_cls_doc": "Hikka की इंटरैक्टिव कॉन्फ़िगरेशन",
        "args": "🚫 <b>आपने गलत तर्क प्रदान किए हैं</b>",
        "no_mod": "🚫 <b>मॉड्यूल मौजूद नहीं है</b>",
        "no_option": "🚫 <b>मॉड्यूल में ऐसा कोई विकल्प नहीं है</b>",
        "validation_error": (
            "🚫 <b>अमान्य कॉन्फ़िगरेशन मान दर्ज किया गया। \nत्रुटि: {}</b>"
        ),
        "try_again": "🔁 पुन: प्रयास करें",
        "typehint": "🕵️ <b>यह {} होना चाहिए</b>",
        "set": "सेट करें",
        "set_default_btn": "♻️ डिफ़ॉल्ट",
        "enter_value_btn": "✍️ मूल्य दर्ज करें",
        "remove_item_btn": "➖ आइटम हटाएं",
        "show_hidden": "🚸 मूल्य दिखाएं",
        "hide_value": "🔒 मूल्य छिपाएं",
        "builtin": "🛰 बिल्ट-इन",
        "external": "🛸 बाहरी",
        "libraries": "🪴 लाइब्रेरी",
        "close_btn": "🔻 बंद करें",
        "back_btn": "👈 पीछे",
    }

    strings_uz = {
        "choose_core": "🎚 <b>Kurum tanlang</b>",
        "configure": "🎚 <b>Sozlash uchun modulni tanlang</b>",
        "configure_lib": "🪴 <b>Sozlash uchun kutubxonani tanlang</b>",
        "configuring_mod": (
            "🎚 <b>Modul uchun parametrni tanlang</b> <code>{}</code>\n\n<b>Joriy"
            " sozlamalar:</b>\n\n{}"
        ),
        "configuring_lib": (
            "🪴 <b>Kutubxona uchun variantni tanlang</b> <code>{}</code>\n\n<b>Hozirgi"
            " sozlamalar:</b>\n\n{}"
        ),
        "configuring_option": (
            "🎚 <b>Modul </b><code>{}</code><b> sozlamasi </b><code>{}</code><b>"
            " konfiguratsiya qilinmoqda</b>\n<i>ℹ️ {}</i>\n\n<b>Default:"
            " {}</b>\n\n<b>Hozirgi: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>Modul </b><code>{}</code><b> kutubxonasi sozlamasi"
            " </b><code>{}</code><b> konfiguratsiya qilinmoqda</b>\n<i>ℹ️"
            " {}</i>\n\n<b>Default: {}</b>\n\n<b>Hozirgi: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>Modul </b><code>{}</code><b> sozlamasi saqlandi!</b>\n<b>Hozirgi:"
            " {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>Modul </b><code>{}</code><b> kutubxonasi sozlamasi"
            " saqlandi!</b>\n<b>Hozirgi: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>Modul </b><code>{}</code><b> sozlamasi standart qiymatga"
            " tiklandi</b>\n<b>Hozirgi: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>Modul </b><code>{}</code><b> kutubxonasi sozlamasi standart qiymatga"
            " tiklandi</b>\n<b>Hozirgi: {}</b>"
        ),
        "_cls_doc": "Hikka interaktiv konfiguratsiyasi",
        "args": "🚫 <b>Siz noto'g'ri ma'lumot kiritdingiz</b>",
        "no_mod": "🚫 <b>Modul mavjud emas</b>",
        "no_option": "🚫 <b>Modulda bunday sozlamalar mavjud emas</b>",
        "validation_error": (
            "🚫 <b>Noto'g'ri konfiguratsiya ma'lumotlari kiritildi. \nXatolik: {}</b>"
        ),
        "try_again": "🔁 Qayta urinib ko'ring",
        "typehint": "🕵️ <b>Buni {} bo'lishi kerak</b>",
        "set": "Sozlash",
        "set_default_btn": "♻️ Standart",
        "enter_value_btn": "✍️ Qiymat kiriting",
        "remove_item_btn": "➖ Elementni o'chirish",
        "show_hidden": "🚸 Qiymatni ko'rsatish",
        "hide_value": "🔒 Qiymatni yashirish",
        "builtin": "🛰 Ichki",
        "external": "🛸 Tashqi",
        "libraries": "🪴 Kutubxona",
        "close_btn": "🔻 Yopish",
        "back_btn": "👈 Orqaga",
    }

    strings_tr = {
        "configuring_option": (
            "🎚 <b>Modül </b><code>{}</code><b> seçeneği </b><code>{}</code>"
            "<b> yapılandırılıyor</b>\n<i>ℹ️ {}</i>\n\n<b>Varsayılan: {}</b>\n\n<b>"
            "Mevcut: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>Modül </b><code>{}</code><b> kütüphanesi seçeneği </b><code>{}</code>"
            "<b> yapılandırılıyor</b>\n<i>ℹ️ {}</i>\n\n<b>Varsayılan: {}</b>\n\n<b>"
            "Mevcut: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>Modül </b><code>{}</code><b> seçeneği kaydedildi!</b>\n<b>Mevcut:"
            " {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>Modül </b><code>{}</code><b> kütüphanesi seçeneği"
            " kaydedildi!</b>\n<b>Mevcut: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>Modül </b><code>{}</code><b> seçeneği varsayılan değere"
            " sıfırlandı</b>\n<b>Mevcut: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>Modül </b><code>{}</code><b> kütüphanesi seçeneği varsayılan değere"
            " sıfırlandı</b>\n<b>Mevcut: {}</b>"
        ),
        "_cls_doc": "Hikka etkileşimli yapılandırması",
        "args": "🚫 <b>Yanlış argüman girdiniz</b>",
        "no_mod": "🚫 <b>Modül bulunamadı</b>",
        "no_option": "🚫 <b>Modülde böyle bir seçenek bulunamadı</b>",
        "validation_error": "🚫 <b>Yanlış ayarlama bilgileri girildi. \nHata: {}</b>",
        "try_again": "🔁 Tekrar deneyin",
        "typehint": "🕵️ <b>Değer {} türünde olmalıdır</b>",
        "set": "Ayarla",
        "set_default_btn": "♻️ Varsayılan",
        "enter_value_btn": "✍️ Değer girin",
        "remove_item_btn": "➖ Öğeyi kaldır",
        "show_hidden": "🚸 Değeri göster",
        "hide_value": "🔒 Değeri gizle",
        "builtin": "🛰 Dahili",
        "external": "🛸 Harici",
        "libraries": "🪴 Kütüphane",
        "back_btn": "👈 Geri",
    }

    strings_ja = {
        "configuring_option": (
            "🎚 <b>モジュール </b><code>{}</code><b> オプション </b><code>{}</code>"
            "<b> を設定しています</b>\n<i>ℹ️ {}</i>\n\n<b>デフォルト: {}</b>\n\n<b>"
            "現在: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>モジュール </b><code>{}</code><b> ライブラリオプション </b><code>{}</code>"
            "<b> を設定しています</b>\n<i>ℹ️ {}</i>\n\n<b>デフォルト: {}</b>\n\n<b>"
            "現在: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>モジュール </b><code>{}</code><b> オプションが保存されました！</b>\n<b>現在: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>モジュール </b><code>{}</code><b> ライブラリオプション が保存されました！</b>\n<b>現在: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>モジュール </b><code>{}</code><b> オプションがデフォルト値に"
            " リセットされました</b>\n<b>現在: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>モジュール </b><code>{}</code><b> ライブラリオプションがデフォルト値に"
            " リセットされました</b>\n<b>現在: {}</b>"
        ),
        "_cls_doc": "Hikka対話的な設定",
        "args": "🚫 <b>引数が間違っています</b>",
        "no_mod": "🚫 <b>モジュールが見つかりません</b>",
        "no_option": "🚫 <b>モジュールにこのオプションはありません</b>",
        "validation_error": "🚫 <b>設定情報が間違っています。 \nエラー: {}</b>",
        "try_again": "🔁 もう一度試してください",
        "typehint": "🕵️ <b>値 {} は型でなければなりません</b>",
        "set": "設定",
        "set_default_btn": "♻️ デフォルト",
        "enter_value_btn": "✍️ 値を入力",
        "remove_item_btn": "➖ 項目を削除",
        "show_hidden": "🚸 値を表示",
        "hide_value": "🔒 値を隠す",
        "builtin": "🛰 ビルトイン",
        "external": "🛸 エクステンション",
        "libraries": "🪴 ライブラリ",
        "back_btn": "👈 戻る",
    }

    strings_kr = {
        "configuring_option": (
            "🎚 <b>모듈 </b><code>{}</code><b> 옵션 </b><code>{}</code>"
            "<b> 를 설정합니다</b>\n<i>ℹ️ {}</i>\n\n<b>기본값: {}</b>\n\n<b>"
            "현재: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>모듈 </b><code>{}</code><b> 라이브러리 옵션 </b><code>{}</code>"
            "<b> 를 설정합니다</b>\n<i>ℹ️ {}</i>\n\n<b>기본값: {}</b>\n\n<b>"
            "현재: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>모듈 </b><code>{}</code><b> 옵션이 저장되었습니다!</b>\n<b>현재: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>모듈 </b><code>{}</code><b> 라이브러리 옵션이 저장되었습니다!</b>\n<b>현재: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>모듈 </b><code>{}</code><b> 옵션이 기본값으로 재설정되었습니다</b>\n<b>현재: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>모듈 </b><code>{}</code><b> 라이브러리 옵션이 기본값으로"
            " 재설정되었습니다</b>\n<b>현재: {}</b>"
        ),
        "_cls_doc": "Hikka 대화형 설정",
        "args": "🚫 <b>잘못된 인수입니다</b>",
        "no_mod": "🚫 <b>모듈을 찾을 수 없습니다</b>",
        "no_option": "🚫 <b>모듈에 이 옵션이 없습니다</b>",
        "validation_error": "🚫 <b>설정 정보가 잘못되었습니다. \n오류: {}</b>",
        "try_again": "🔁 다시 시도하십시오",
        "typehint": "🕵️ <b>값 {} 은(는) 타입이어야 합니다</b>",
        "set": "설정",
        "set_default_btn": "♻️ 기본값",
        "enter_value_btn": "✍️ 값 입력",
        "remove_item_btn": "➖ 항목 제거",
        "show_hidden": "🚸 값 표시",
        "hide_value": "🔒 값 숨기기",
        "builtin": "🛰 빌트인",
        "external": "🛸 확장",
        "libraries": "🪴 라이브러리",
        "back_btn": "👈 뒤로",
    }

    strings_ar = {
        "configuring_option": (
            "🎚 <b>إعداد خيار </b><code>{}</code><b> للموديول </b><code>{}</code>"
            "<b> </b>\n<i>ℹ️ {}</i>\n\n<b>الافتراضي: {}</b>\n\n<b>"
            "الحالي: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>إعداد خيار </b><code>{}</code><b> لمكتبة الموديول </b><code>{}</code>"
            "<b> </b>\n<i>ℹ️ {}</i>\n\n<b>الافتراضي: {}</b>\n\n<b>"
            "الحالي: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>تم حفظ خيار الموديول </b><code>{}</code><b> !</b>\n<b>الحالي: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>تم حفظ خيار مكتبة الموديول </b><code>{}</code><b> !</b>\n<b>الحالي:"
            " {}</b>"
        ),
        "option_reset": (
            "♻️ <b>تمت إعادة تعيين خيار الموديول </b><code>{}</code><b> إلى"
            " الافتراضي</b>\n<b>الحالي: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>تمت إعادة تعيين خيار مكتبة الموديول </b><code>{}</code><b> إلى"
            " الافتراضي</b>\n<b>الحالي: {}</b>"
        ),
        "_cls_doc": "إعدادات Hikka التفاعلية",
        "args": "🚫 <b>معلمات غير صحيحة</b>",
        "no_mod": "🚫 <b>لم يتم العثور على الموديول</b>",
        "no_option": "🚫 <b>لا يوجد خيار بهذا الاسم في الموديول</b>",
        "validation_error": "🚫 <b>تعذر تحليل المعلومات. \nالخطأ: {}</b>",
        "try_again": "🔁 حاول مرة أخرى",
        "typehint": "🕵️ <b>يجب أن يكون القيمة {} من نوع {}</b>",
        "set": "تعيين",
        "set_default_btn": "♻️ الافتراضي",
        "enter_value_btn": "✍️ إدخال القيمة",
        "remove_item_btn": "➖ حذف العنصر",
        "show_hidden": "🚸 إظهار القيم",
        "hide_value": "🔒 إخفاء القيم",
        "builtin": "🛰 مدمج",
        "external": "🛸 خارجي",
        "libraries": "🪴 مكتبات",
        "back_btn": "👈 رجوع",
    }

    strings_es = {
        "configuring_option": (
            "🎚 <b>Configurando la opción </b><code>{}</code><b> del módulo"
            " </b><code>{}</code><b> </b>\n<i>ℹ️ {}</i>\n\n<b>Por defecto:"
            " {}</b>\n\n<b>Actual: {}</b>\n\n{}"
        ),
        "configuring_option_lib": (
            "🪴 <b>Configurando la opción </b><code>{}</code><b> de la librería del"
            " módulo </b><code>{}</code><b> </b>\n<i>ℹ️ {}</i>\n\n<b>Por defecto:"
            " {}</b>\n\n<b>Actual: {}</b>\n\n{}"
        ),
        "option_saved": (
            "🎚 <b>¡Guardada la opción del módulo"
            " </b><code>{}</code><b>!</b>\n<b>Actual: {}</b>"
        ),
        "option_saved_lib": (
            "🪴 <b>¡Guardada la opción de la librería del módulo"
            " </b><code>{}</code><b>!</b>\n<b>Actual: {}</b>"
        ),
        "option_reset": (
            "♻️ <b>La opción del módulo </b><code>{}</code><b> se ha reiniciado a su"
            " valor por defecto</b>\n<b>Actual: {}</b>"
        ),
        "option_reset_lib": (
            "♻️ <b>La opción de la librería del módulo </b><code>{}</code><b> se ha"
            " reiniciado a su valor por defecto</b>\n<b>Actual: {}</b>"
        ),
        "_cls_doc": "Configuraciones interactivas de Hikka",
        "args": "🚫 <b>Argumentos no válidos</b>",
        "no_mod": "🚫 <b>No se encontró el módulo</b>",
        "no_option": "🚫 <b>El módulo no tiene esta opción</b>",
        "validation_error": "🚫 <b>No se pudo analizar la información. \nError: {}</b>",
        "try_again": "🔁 Intentar de nuevo",
        "typehint": "🕵️ <b>El valor debe ser de tipo {}</b>",
        "set": "Establecer",
        "set_default_btn": "♻️ Por defecto",
        "enter_value_btn": "✍️ Introducir valor",
        "remove_item_btn": "➖ Eliminar elemento",
        "show_hidden": "🚸 Mostrar valores",
        "hide_value": "🔒 Ocultar valores",
        "builtin": "🛰 Integrado",
        "external": "🛸 Externo",
        "libraries": "🪴 Librerías",
        "back_btn": "👈 Volver",
    }

    _row_size = 3
    _num_rows = 5

    @staticmethod
    def prep_value(value: typing.Any) -> typing.Any:
        if isinstance(value, str):
            return f"</b><code>{utils.escape_html(value.strip())}</code><b>"

        if isinstance(value, list) and value:
            return (
                "</b><code>[</code>\n    "
                + "\n    ".join(
                    [f"<code>{utils.escape_html(str(item))}</code>" for item in value]
                )
                + "\n<code>]</code><b>"
            )

        return f"</b><code>{utils.escape_html(value)}</code><b>"

    def hide_value(self, value: typing.Any) -> str:
        if isinstance(value, list) and value:
            return self.prep_value(["*" * len(str(i)) for i in value])

        return self.prep_value("*" * len(str(value)))

    async def inline__set_config(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            self.lookup(mod).config[option] = query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings(
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__reset_default(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        mod_instance = self.lookup(mod)
        mod_instance.config[option] = mod_instance.config.getdef(option)

        await call.edit(
            self.strings(
                "option_reset" if isinstance(obj_type, bool) else "option_reset_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
        )

    async def inline__set_bool(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        validator = self.lookup(mod).config._config[option].validator
        doc = utils.escape_html(
            next(
                (
                    validator.doc[lang]
                    for lang in self._db.get(translations.__name__, "lang", "en").split(
                        " "
                    )
                    if lang in validator.doc
                ),
                validator.doc["en"],
            )
        )

        await call.edit(
            self.strings(
                "configuring_option"
                if isinstance(obj_type, bool)
                else "configuring_option_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                utils.escape_html(self.lookup(mod).config.getdoc(option)),
                self.prep_value(self.lookup(mod).config.getdef(option)),
                self.prep_value(self.lookup(mod).config[option])
                if not validator or validator.internal_id != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
                self.strings("typehint").format(
                    doc,
                    eng_art="n" if doc.lower().startswith(tuple("euioay")) else "",
                )
                if doc
                else "",
            ),
            reply_markup=self._generate_bool_markup(mod, option, obj_type),
        )

        await call.answer("✅")

    def _generate_bool_markup(
        self,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        return [
            [
                *(
                    [
                        {
                            "text": f"❌ {self.strings('set')} `False`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, False),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    else [
                        {
                            "text": f"✅ {self.strings('set')} `True`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, True),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                )
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ],
        ]

    async def inline__add_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            try:
                query = ast.literal_eval(query)
            except Exception:
                pass

            if isinstance(query, (set, tuple)):
                query = list(query)

            if not isinstance(query, list):
                query = [query]

            self.lookup(mod).config[option] = self.lookup(mod).config[option] + query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings(
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__remove_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            try:
                query = ast.literal_eval(query)
            except Exception:
                pass

            if isinstance(query, (set, tuple)):
                query = list(query)

            if not isinstance(query, list):
                query = [query]

            query = list(map(str, query))

            old_config_len = len(self.lookup(mod).config[option])

            self.lookup(mod).config[option] = [
                i for i in self.lookup(mod).config[option] if str(i) not in query
            ]

            if old_config_len == len(self.lookup(mod).config[option]):
                raise loader.validators.ValidationError(
                    f"Nothing from passed value ({self.prep_value(query)}) is not in"
                    " target list"
                )
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await call.edit(
            self.strings(
                "option_saved" if isinstance(obj_type, bool) else "option_saved_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    def _generate_series_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        return [
            [
                {
                    "text": self.strings("enter_value_btn"),
                    "input": self.strings("enter_value_desc"),
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"obj_type": obj_type},
                }
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("remove_item_btn"),
                            "input": self.strings("remove_item_desc"),
                            "handler": self.inline__remove_item,
                            "args": (mod, option, call.inline_message_id),
                            "kwargs": {"obj_type": obj_type},
                        },
                        {
                            "text": self.strings("add_item_btn"),
                            "input": self.strings("add_item_desc"),
                            "handler": self.inline__add_item,
                            "args": (mod, option, call.inline_message_id),
                            "kwargs": {"obj_type": obj_type},
                        },
                    ]
                    if self.lookup(mod).config[option]
                    else []
                ),
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ],
        ]

    async def _choice_set_value(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        validator = self.lookup(mod).config._config[option].validator

        await call.edit(
            self.strings(
                "option_saved"
                if isinstance(obj_type, bool)
                else "option_saved_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(self.lookup(mod).config[option])
                if validator.internal_id != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
        )


        await call.answer("✅")

    async def _multi_choice_set_value(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        obj_type: typing.Union[bool, str] = False,
    ):
        try:
            if value in self.lookup(mod).config._config[option].value:
                self.lookup(mod).config._config[option].value.remove(value)
            else:
                self.lookup(mod).config._config[option].value += [value]

            self.lookup(mod).config.reload()
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"obj_type": obj_type},
                },
            )
            return

        await self.inline__configure_option(call, mod, option, False, obj_type)
        await call.answer("✅")

    def _generate_choice_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        possible_values = list(
            self.lookup(mod)
            .config._config[option]
            .validator.validate.keywords["possible_values"]
        )
        return [
            [
                {
                    "text": self.strings("enter_value_btn"),
                    "input": self.strings("enter_value_desc"),
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"obj_type": obj_type},
                }
            ],
            *utils.chunks(
                [
                    {
                        "text": (
                            f"{'☑️' if self.lookup(mod).config[option] == value else '🔘'} "
                            f"{value if len(str(value)) < 20 else str(value)[:20]}"
                        ),
                        "callback": self._choice_set_value,
                        "args": (mod, option, value, obj_type),
                    }
                    for value in possible_values
                ],
                2,
            )[
                : 6
                if self.lookup(mod).config[option]
                != self.lookup(mod).config.getdef(option)
                else 7
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ],
        ]

    def _generate_multi_choice_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        obj_type: typing.Union[bool, str] = False,
    ) -> list:
        possible_values = list(
            self.lookup(mod)
            .config._config[option]
            .validator.validate.keywords["possible_values"]
        )
        return [
            [
                {
                    "text": self.strings("enter_value_btn"),
                    "input": self.strings("enter_value_desc"),
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"obj_type": obj_type},
                }
            ],
            *utils.chunks(
                [
                    {
                        "text": (
                            f"{'☑️' if value in self.lookup(mod).config[option] else '◻️'} "
                            f"{value if len(str(value)) < 20 else str(value)[:20]}"
                        ),
                        "callback": self._multi_choice_set_value,
                        "args": (mod, option, value, obj_type),
                    }
                    for value in possible_values
                ],
                2,
            )[
                : 6
                if self.lookup(mod).config[option]
                != self.lookup(mod).config.getdef(option)
                else 7
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"obj_type": obj_type},
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ],
        ]

    async def inline__configure_option(
        self,
        call: InlineCall,
        mod: str,
        config_opt: str,
        force_hidden: bool = False,
        obj_type: typing.Union[bool, str] = False,
    ):
        module = self.lookup(mod)
        args = [
            utils.escape_html(config_opt),
            utils.escape_html(mod),
            utils.escape_html(module.config.getdoc(config_opt)),
            self.prep_value(module.config.getdef(config_opt)),
            self.prep_value(module.config[config_opt])
            if not module.config._config[config_opt].validator
            or module.config._config[config_opt].validator.internal_id != "Hidden"
            or force_hidden
            else self.hide_value(module.config[config_opt]),
        ]

        if (
            module.config._config[config_opt].validator
            and module.config._config[config_opt].validator.internal_id == "Hidden"
        ):
            additonal_button_row = (
                [
                    [
                        {
                            "text": self.strings("hide_value"),
                            "callback": self.inline__configure_option,
                            "args": (mod, config_opt, False),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                ]
                if force_hidden
                else [
                    [
                        {
                            "text": self.strings("show_hidden"),
                            "callback": self.inline__configure_option,
                            "args": (mod, config_opt, True),
                            "kwargs": {"obj_type": obj_type},
                        }
                    ]
                ]
            )
        else:
            additonal_button_row = []

        try:
            validator = module.config._config[config_opt].validator
            doc = utils.escape_html(
                next(
                    (
                        validator.doc[lang]
                        for lang in self._db.get(
                            translations.__name__, "lang", "en"
                        ).split(" ")
                        if lang in validator.doc
                    ),
                    validator.doc["en"],
                )
            )
        except Exception:
            doc = None
            validator = None
            args += [""]
        else:
            args += [
                self.strings("typehint").format(
                    doc,
                    eng_art="n" if doc.lower().startswith(tuple("euioay")) else "",
                )
            ]
            if validator.internal_id == "Boolean":
                await call.edit(
                    self.strings(
                        "configuring_option"
                        if isinstance(obj_type, bool)
                        else "configuring_option_lib"
                    ).format(*args),
                    reply_markup=additonal_button_row
                    + self._generate_bool_markup(mod, config_opt, obj_type),
                )
                return

            if validator.internal_id == "Series":
                await call.edit(
                    self.strings(
                        "configuring_option"
                        if isinstance(obj_type, bool)
                        else "configuring_option_lib"
                    ).format(*args),
                    reply_markup=additonal_button_row
                    + self._generate_series_markup(call, mod, config_opt, obj_type),
                )
                return

            if validator.internal_id == "Choice":
                await call.edit(
                    self.strings(
                        "configuring_option"
                        if isinstance(obj_type, bool)
                        else "configuring_option_lib"
                    ).format(*args),
                    reply_markup=additonal_button_row
                    + self._generate_choice_markup(call, mod, config_opt, obj_type),
                )
                return

            if validator.internal_id == "MultiChoice":
                await call.edit(
                    self.strings(
                        "configuring_option"
                        if isinstance(obj_type, bool)
                        else "configuring_option_lib"
                    ).format(*args),
                    reply_markup=additonal_button_row
                    + self._generate_multi_choice_markup(
                        call, mod, config_opt, obj_type
                    ),
                )
                return

        await call.edit(
            self.strings(
                "configuring_option"
                if isinstance(obj_type, bool)
                else "configuring_option_lib"
            ).format(*args),
            reply_markup=additonal_button_row
            + [
                [
                    {
                        "text": self.strings("enter_value_btn"),
                        "input": self.strings("enter_value_desc"),
                        "handler": self.inline__set_config,
                        "args": (mod, config_opt, call.inline_message_id),
                        "kwargs": {"obj_type": obj_type},
                    }
                ],
                [
                    {
                        "text": self.strings("set_default_btn"),
                        "callback": self.inline__reset_default,
                        "args": (mod, config_opt),
                        "kwargs": {"obj_type": obj_type},
                    }
                ],
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ],
            ],
        )

    async def inline__configure(
        self,
        call: InlineCall,
        mod: str,
        obj_type: typing.Union[bool, str] = False,
    ):
        btns = [
            {
                "text": param,
                "callback": self.inline__configure_option,
                "args": (mod, param),
                "kwargs": {"obj_type": obj_type},
            }
            for param in self.lookup(mod).config
        ]

        await call.edit(
            self.strings(
                "configuring_mod" if isinstance(obj_type, bool) else "configuring_lib"
            ).format(
                utils.escape_html(mod),
                "\n".join(
                    [
                        f"▫️ <code>{utils.escape_html(key)}</code>: <b>{{}}</b>".format(
                            self.prep_value(value)
                            if (
                                not self.lookup(mod).config._config[key].validator
                                or self.lookup(mod)
                                .config._config[key]
                                .validator.internal_id
                                != "Hidden"
                            )
                            else self.hide_value(value)
                        )
                        for key, value in self.lookup(mod).config.items()
                    ]
                ),
            ),
            reply_markup=list(utils.chunks(btns, 2))
            + [
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__global_config,
                        "kwargs": {"obj_type": obj_type},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
        )

    async def inline__choose_category(self, call: typing.Union[Message, InlineCall]):
        await utils.answer(
            call,
            self.strings("choose_core"),
            reply_markup=[
                [
                    {
                        "text": self.strings("builtin"),
                        "callback": self.inline__global_config,
                        "kwargs": {"obj_type": True},
                    },
                    {
                        "text": self.strings("external"),
                        "callback": self.inline__global_config,
                    },
                ],
                *(
                    [
                        [
                            {
                                "text": self.strings("libraries"),
                                "callback": self.inline__global_config,
                                "kwargs": {"obj_type": "library"},
                            }
                        ]
                    ]
                    if self.allmodules.libraries
                    and any(hasattr(lib, "config") for lib in self.allmodules.libraries)
                    else []
                ),
                [{"text": self.strings("close_btn"), "action": "close"}],
            ],
        )

    async def inline__global_config(
        self,
        call: InlineCall,
        page: int = 0,
        obj_type: typing.Union[bool, str] = False,
    ):
        if isinstance(obj_type, bool):
            to_config = [
                mod.strings("name")
                for mod in self.allmodules.modules
                if hasattr(mod, "config")
                and callable(mod.strings)
                and (mod.__origin__.startswith("<core") or not obj_type)
                and (not mod.__origin__.startswith("<core") or obj_type)
            ]
        else:
            to_config = [
                lib.name for lib in self.allmodules.libraries if hasattr(lib, "config")
            ]

        to_config.sort()

        kb = []
        for mod_row in utils.chunks(
            to_config[
                page
                * self._num_rows
                * self._row_size : (page + 1)
                * self._num_rows
                * self._row_size
            ],
            3,
        ):
            row = [
                {
                    "text": btn,
                    "callback": self.inline__configure,
                    "args": (btn,),
                    "kwargs": {"obj_type": obj_type},
                }
                for btn in mod_row
            ]
            kb += [row]

        if len(to_config) > self._num_rows * self._row_size:
            kb += self.inline.build_pagination(
                callback=functools.partial(
                    self.inline__global_config, obj_type=obj_type
                ),
                total_pages=ceil(len(to_config) / (self._num_rows * self._row_size)),
                current_page=page + 1,
            )

        kb += [
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__choose_category,
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ]
        ]

        await call.edit(
            self.strings(
                "configure" if isinstance(obj_type, bool) else "configure_lib"
            ),
            reply_markup=kb,
        )

    @loader.command(
        ru_doc="Настроить модули",
        de_doc="Konfiguriere Module",
        tr_doc="Modülleri yapılandır",
        hi_doc="मॉड्यूल कॉन्फ़िगर करें",
        uz_doc="Modullarni sozlash",
        ja_doc="モジュールを設定します",
        kr_doc="모듈 설정",
        ar_doc="تكوين الوحدات",
        es_doc="Configurar módulos",
    )
    async def configcmd(self, message: Message):
        """Configure modules"""
        args = utils.get_args_raw(message)
        if self.lookup(args) and hasattr(self.lookup(args), "config"):
            form = await self.inline.form("🌘", message)
            mod = self.lookup(args)
            if isinstance(mod, loader.Library):
                type_ = "library"
            else:
                type_ = mod.__origin__.startswith("<core")

            await self.inline__configure(form, args, obj_type=type_)
            return

        await self.inline__choose_category(message)

    @loader.command(
        ru_doc=(
            "<модуль> <настройка> <значение> - установить значение конфига для модуля"
        ),
        de_doc=(
            "<Modul> <Einstellung> <Wert> - Setze den Wert der Konfiguration für das"
            " Modul"
        ),
        tr_doc="<modül> <ayar> <değer> - Modül için yapılandırma değerini ayarla",
        hi_doc="<मॉड्यूल> <सेटिंग> <मान> - मॉड्यूल के लिए कॉन्फ़िगरेशन मान सेट करें",
        uz_doc="<modul> <sozlash> <qiymat> - modul uchun sozlash qiymatini o'rnatish",
        ja_doc="<モジュール> <設定> <値> - モジュールの設定値を設定します",
        kr_doc="<모듈> <설정> <값> - 모듈의 구성 값을 설정합니다",
        ar_doc="<وحدة> <إعداد> <قيمة> - تعيين قيمة التكوين للوحدة",
        es_doc=(
            "<módulo> <configuración> <valor> - Establecer el valor de configuración"
        ),
    )
    async def fconfig(self, message: Message):
        """<module_name> <property_name> <config_value> - set the config value for the module
        """
        args = utils.get_args_raw(message).split(maxsplit=2)

        if len(args) < 3:
            await utils.answer(message, self.strings("args"))
            return

        mod, option, value = args

        instance = self.lookup(mod)
        if not instance:
            await utils.answer(message, self.strings("no_mod"))
            return

        if option not in instance.config:
            await utils.answer(message, self.strings("no_option"))
            return

        instance.config[option] = value
        await utils.answer(
            message,
            self.strings(
                "option_saved"
                if isinstance(instance, loader.Module)
                else "option_saved_lib"
            ).format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(instance.config[option])
                if not instance.config._config[option].validator
                or instance.config._config[option].validator.internal_id != "Hidden"
                else self.hide_value(instance.config[option]),
            ),
        )
