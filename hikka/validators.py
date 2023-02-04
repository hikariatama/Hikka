# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import functools
import re
import typing

import grapheme
from emoji import get_emoji_unicode_dict

from . import utils

ConfigAllowedTypes = typing.Union[tuple, list, str, int, bool, None]

ALLOWED_EMOJIS = set(get_emoji_unicode_dict("en").values())


class ValidationError(Exception):
    """
    Is being raised when config value passed can't be converted properly
    Must be raised with string, describing why value is incorrect
    It will be shown in .config, if user tries to set incorrect value
    """


class Validator:
    """
    Class used as validator of config value
    :param validator: Sync function, which raises `ValidationError` if passed
                      value is incorrect (with explanation) and returns converted
                      value if it is semantically correct.
                      ⚠️ If validator returns `None`, value will always be set to `None`
    :param doc: Docstrings for this validator as string, or dict in format:
                {
                    "en": "docstring",
                    "ru": "докстрингом",
                    "fr": "chaîne de documentation",
                    "it": "docstring",
                    "de": "Dokumentation",
                    "tr": "dökümantasyon",
                    "uz": "hujjat",
                    "es": "documentación",
                    "kk": "құжат",
                }
                Use instrumental case with lowercase
    :param _internal_id: Do not pass anything here, or things will break
    """

    def __init__(
        self,
        validator: callable,
        doc: typing.Optional[typing.Union[str, dict]] = None,
        _internal_id: typing.Optional[int] = None,
    ):
        self.validate = validator

        if isinstance(doc, str):
            doc = {
                "en": doc,
                "ru": doc,
                "fr": doc,
                "it": doc,
                "de": doc,
                "tr": doc,
                "uz": doc,
            }

        self.doc = doc
        self.internal_id = _internal_id


class Boolean(Validator):
    """
    Any logical value to be passed
    `1`, `"1"` etc. will be automatically converted to bool
    """

    def __init__(self):
        super().__init__(
            self._validate,
            {
                "en": "boolean",
                "ru": "логическим значением",
                "fr": "booléen",
                "it": "booleano",
                "de": "logischen Wert",
                "tr": "mantıksal değer",
                "uz": "mantiqiy qiymat",
                "es": "valor lógico",
                "kk": "логикалық мән",
            },
            _internal_id="Boolean",
        )

    @staticmethod
    def _validate(value: ConfigAllowedTypes, /) -> bool:
        true = ["True", "true", "1", 1, True, "yes", "Yes", "on", "On", "y", "Y"]
        false = ["False", "false", "0", 0, False, "no", "No", "off", "Off", "n", "N"]
        if value not in true + false:
            raise ValidationError("Passed value must be a boolean")

        return value in true


class Integer(Validator):
    """
    Checks whether passed argument is an integer value
    :param digits: Digits quantity, which must be passed
    :param minimum: Minimal number to be passed
    :param maximum: Maximum number to be passed
    """

    def __init__(
        self,
        *,
        digits: typing.Optional[int] = None,
        minimum: typing.Optional[int] = None,
        maximum: typing.Optional[int] = None,
    ):
        _sign_en = "positive " if minimum is not None and minimum == 0 else ""
        _sign_ru = "положительным " if minimum is not None and minimum == 0 else ""
        _sign_fr = "positif " if minimum is not None and minimum == 0 else ""
        _sign_it = "positivo " if minimum is not None and minimum == 0 else ""
        _sign_de = "positiv " if minimum is not None and minimum == 0 else ""
        _sign_tr = "pozitif " if minimum is not None and minimum == 0 else ""
        _sign_uz = "musbat " if minimum is not None and minimum == 0 else ""
        _sign_es = "positivo " if minimum is not None and minimum == 0 else ""
        _sign_kk = "мәндік " if minimum is not None and minimum == 0 else ""

        _sign_en = "negative " if maximum is not None and maximum == 0 else _sign_en
        _sign_ru = (
            "отрицательным " if maximum is not None and maximum == 0 else _sign_ru
        )
        _sign_fr = "négatif " if maximum is not None and maximum == 0 else _sign_fr
        _sign_it = "negativo " if maximum is not None and maximum == 0 else _sign_it
        _sign_de = "negativ " if maximum is not None and maximum == 0 else _sign_de
        _sign_tr = "negatif " if maximum is not None and maximum == 0 else _sign_tr
        _sign_uz = "manfiy " if maximum is not None and maximum == 0 else _sign_uz
        _sign_es = "negativo " if maximum is not None and maximum == 0 else _sign_es
        _sign_kk = "мәнсіздік " if maximum is not None and maximum == 0 else _sign_kk

        _digits_en = f" with exactly {digits} digits" if digits is not None else ""
        _digits_ru = f", в котором ровно {digits} цифр " if digits is not None else ""
        _digits_fr = f" avec exactement {digits} chiffres" if digits is not None else ""
        _digits_it = f" con esattamente {digits} cifre" if digits is not None else ""
        _digits_de = f" mit genau {digits} Ziffern" if digits is not None else ""
        _digits_tr = f" tam olarak {digits} basamaklı" if digits is not None else ""
        _digits_uz = f" to'g'ri {digits} raqamlar bilan" if digits is not None else ""
        _digits_es = f" con exactamente {digits} dígitos" if digits is not None else ""
        _digits_kk = f" тең {digits} сандық" if digits is not None else ""

        if minimum is not None and minimum != 0:
            doc = (
                {
                    "en": f"{_sign_en}integer greater than {minimum}{_digits_en}",
                    "ru": f"{_sign_ru}целым числом больше {minimum}{_digits_ru}",
                    "fr": f"{_sign_fr}entier supérieur à {minimum}{_digits_fr}",
                    "it": f"{_sign_it}intero maggiore di {minimum}{_digits_it}",
                    "de": f"{_sign_de}ganze Zahl größer als {minimum}{_digits_de}",
                    "tr": f"{_sign_tr}tam sayı {minimum} den büyük{_digits_tr}",
                    "uz": f"{_sign_uz}butun son {minimum} dan katta{_digits_uz}",
                    "es": f"{_sign_es}número entero mayor que {minimum}{_digits_es}",
                    "kk": f"{_sign_kk}толық сан {minimum} тан көп{_digits_kk}",
                }
                if maximum is None and maximum != 0
                else {
                    "en": f"{_sign_en}integer from {minimum} to {maximum}{_digits_en}",
                    "ru": (
                        f"{_sign_ru}целым числом в промежутке от {minimum} до"
                        f" {maximum}{_digits_ru}"
                    ),
                    "fr": (
                        f"{_sign_fr}entier compris entre {minimum} et {maximum}"
                        f"{_digits_fr}"
                    ),
                    "it": (
                        f"{_sign_it}intero compreso tra {minimum} e {maximum}"
                        f"{_digits_it}"
                    ),
                    "de": (
                        f"{_sign_de}ganze Zahl von {minimum} bis {maximum}{_digits_de}"
                    ),
                    "tr": (
                        f"{_sign_tr}tam sayı {minimum} ile {maximum} arasında"
                        f"{_digits_tr}"
                    ),
                    "uz": (
                        f"{_sign_uz}butun son {minimum} dan {maximum} gacha{_digits_uz}"
                    ),
                    "es": (
                        f"{_sign_es}número entero de {minimum} a {maximum}{_digits_es}"
                    ),
                    "kk": (
                        f"{_sign_kk}толық сан {minimum} ден {maximum} қарай{_digits_kk}"
                    ),
                }
            )

        elif maximum is None and maximum != 0:
            doc = {
                "en": f"{_sign_en}integer{_digits_en}",
                "ru": f"{_sign_ru}целым числом{_digits_ru}",
                "fr": f"{_sign_fr}entier{_digits_fr}",
                "it": f"{_sign_it}intero{_digits_it}",
                "de": f"{_sign_de}ganze Zahl{_digits_de}",
                "tr": f"{_sign_tr}tam sayı{_digits_tr}",
                "uz": f"{_sign_uz}butun son{_digits_uz}",
                "es": f"{_sign_es}número entero{_digits_es}",
                "kk": f"{_sign_kk}толық сан{_digits_kk}",
            }
        else:
            doc = {
                "en": f"{_sign_en}integer less than {maximum}{_digits_en}",
                "ru": f"{_sign_ru}целым числом меньше {maximum}{_digits_ru}",
                "fr": f"{_sign_fr}entier inférieur à {maximum}{_digits_fr}",
                "it": f"{_sign_it}intero minore di {maximum}{_digits_it}",
                "de": f"{_sign_de}ganze Zahl kleiner als {maximum}{_digits_de}",
                "tr": f"{_sign_tr}tam sayı {maximum} den küçük{_digits_tr}",
                "uz": f"{_sign_uz}butun son {maximum} dan kichik{_digits_uz}",
                "es": f"{_sign_es}número entero menor que {maximum}{_digits_es}",
                "kk": f"{_sign_kk}толық сан {maximum} тан кем{_digits_kk}",
            }
        super().__init__(
            functools.partial(
                self._validate,
                digits=digits,
                minimum=minimum,
                maximum=maximum,
            ),
            doc,
            _internal_id="Integer",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        digits: int,
        minimum: int,
        maximum: int,
    ) -> typing.Union[int, None]:
        try:
            value = int(str(value).strip())
        except ValueError:
            raise ValidationError(f"Passed value ({value}) must be a number")

        if minimum is not None and value < minimum:
            raise ValidationError(f"Passed value ({value}) is lower than minimum one")

        if maximum is not None and value > maximum:
            raise ValidationError(f"Passed value ({value}) is greater than maximum one")

        if digits is not None and len(str(value)) != digits:
            raise ValidationError(
                f"The length of passed value ({value}) is incorrect "
                f"(Must be exactly {digits} digits)"
            )

        return value


class Choice(Validator):
    """
    Check whether entered value is in the allowed list
    :param possible_values: Allowed values to be passed to config param
    """

    def __init__(
        self,
        possible_values: typing.List[ConfigAllowedTypes],
        /,
    ):
        possible = " / ".join(list(map(str, possible_values)))

        super().__init__(
            functools.partial(self._validate, possible_values=possible_values),
            {
                "en": f"one of the following: {possible}",
                "ru": f"одним из: {possible}",
                "fr": f"un des suivants: {possible}",
                "it": f"uno dei seguenti: {possible}",
                "de": f"einer der folgenden: {possible}",
                "tr": f"şunlardan biri: {possible}",
                "uz": f"quyidagilardan biri: {possible}",
                "es": f"uno de los siguientes: {possible}",
                "kk": f"келесілердің бірі: {possible}",
            },
            _internal_id="Choice",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        possible_values: typing.List[ConfigAllowedTypes],
    ) -> ConfigAllowedTypes:
        if value not in possible_values:
            raise ValidationError(
                f"Passed value ({value}) is not one of the following:"
                f" {' / '.join(list(map(str, possible_values)))}"
            )

        return value


class MultiChoice(Validator):
    """
    Check whether every entered value is in the allowed list
    :param possible_values: Allowed values to be passed to config param
    """

    def __init__(
        self,
        possible_values: typing.List[ConfigAllowedTypes],
        /,
    ):
        possible = " / ".join(list(map(str, possible_values)))
        super().__init__(
            functools.partial(self._validate, possible_values=possible_values),
            {
                "en": f"list of values, where each one must be one of: {possible}",
                "ru": (
                    "список значений, каждое из которых должно быть одним из"
                    f" следующего: {possible}"
                ),
                "fr": (
                    "liste de valeurs, chacune d'elles doit être l'une des"
                    f" suivant: {possible}"
                ),
                "it": (
                    "elenco di valori, ognuno dei quali deve essere uno dei"
                    f" seguenti: {possible}"
                ),
                "de": (
                    "Liste von Werten, bei denen jeder einer der folgenden sein muss:"
                    f" {possible}"
                ),
                "tr": (
                    "değerlerin listesi, her birinin şunlardan biri olması gerekir:"
                    f" {possible}"
                ),
                "uz": (
                    "qiymatlar ro'yxati, har biri quyidagilardan biri bo'lishi kerak:"
                    f" {possible}"
                ),
                "es": f"lista de valores, donde cada uno debe ser uno de: {possible}",
                "kk": (
                    "мәндер тізімі, әрбірінің келесілердің бірі болуы керек:"
                    f" {possible}"
                ),
            },
            _internal_id="MultiChoice",
        )

    @staticmethod
    def _validate(
        value: typing.List[ConfigAllowedTypes],
        /,
        *,
        possible_values: typing.List[ConfigAllowedTypes],
    ) -> typing.List[ConfigAllowedTypes]:
        if not isinstance(value, (list, tuple)):
            value = [value]

        for item in value:
            if item not in possible_values:
                raise ValidationError(
                    f"One of passed values ({item}) is not one of the following:"
                    f" {' / '.join(list(map(str, possible_values)))}"
                )

        return list(set(value))


class Series(Validator):
    """
    Represents the series of value (simply `list`)
    :param separator: With which separator values must be separated
    :param validator: Internal validator for each sequence value
    :param min_len: Minimal number of series items to be passed
    :param max_len: Maximum number of series items to be passed
    :param fixed_len: Fixed number of series items to be passed
    """

    def __init__(
        self,
        validator: typing.Optional[Validator] = None,
        min_len: typing.Optional[int] = None,
        max_len: typing.Optional[int] = None,
        fixed_len: typing.Optional[int] = None,
    ):
        def trans(lang: str) -> str:
            return validator.doc.get(lang, validator.doc["en"])

        _each_en = f" (each must be {trans('en')})" if validator is not None else ""
        _each_ru = (
            f" (каждое должно быть {trans('ru')})" if validator is not None else ""
        )
        _each_fr = f" (chaque doit être {trans('fr')})" if validator is not None else ""
        _each_it = (
            f" (ognuno deve essere {trans('it')})" if validator is not None else ""
        )
        _each_de = f" (jedes muss {trans('de')})" if validator is not None else ""
        _each_tr = f" (her biri {trans('tr')})" if validator is not None else ""
        _each_uz = f" (har biri {trans('uz')})" if validator is not None else ""
        _each_es = f" (cada uno {trans('es')})" if validator is not None else ""
        _each_kk = f" (әрбірі {trans('kk')})" if validator is not None else ""

        if fixed_len is not None:
            _len_en = f" (exactly {fixed_len} pcs.)"
            _len_ru = f" (ровно {fixed_len} шт.)"
            _len_fr = f" (exactement {fixed_len} pcs.)"
            _len_it = f" (esattamente {fixed_len} pezzi)"
            _len_de = f" (genau {fixed_len} Stück)"
            _len_tr = f" (tam olarak {fixed_len} adet)"
            _len_uz = f" (to'g'ri {fixed_len} ta)"
            _len_es = f" (exactamente {fixed_len} piezas)"
            _len_kk = f" (тоғыз {fixed_len} құны)"
        elif min_len is None:
            if max_len is None:
                _len_en = ""
                _len_ru = ""
                _len_fr = ""
                _len_it = ""
                _len_de = ""
                _len_tr = ""
                _len_uz = ""
                _len_es = ""
                _len_kk = ""
            else:
                _len_en = f" (up to {max_len} pcs.)"
                _len_ru = f" (до {max_len} шт.)"
                _len_fr = f" (jusqu'à {max_len} pcs.)"
                _len_it = f" (fino a {max_len} pezzi)"
                _len_de = f" (bis zu {max_len} Stück)"
                _len_tr = f" (en fazla {max_len} adet)"
                _len_uz = f" (eng ko'p {max_len} ta)"
                _len_es = f" (hasta {max_len} piezas)"
                _len_kk = f" (көптегенде {max_len} құны)"
        elif max_len is not None:
            _len_en = f" (from {min_len} to {max_len} pcs.)"
            _len_ru = f" (от {min_len} до {max_len} шт.)"
            _len_fr = f" (de {min_len} à {max_len} pcs.)"
            _len_it = f" (da {min_len} a {max_len} pezzi)"
            _len_de = f" (von {min_len} bis {max_len} Stück)"
            _len_tr = f" ({min_len} ile {max_len} arasında {max_len} adet)"
            _len_uz = f" ({min_len} dan {max_len} gacha {max_len} ta)"
            _len_es = f" (desde {min_len} hasta {max_len} piezas)"
            _len_kk = f" ({min_len} ден {max_len} ге {max_len} құны)"
        else:
            _len_en = f" (at least {min_len} pcs.)"
            _len_ru = f" (как минимум {min_len} шт.)"
            _len_fr = f" (au moins {min_len} pcs.)"
            _len_it = f" (almeno {min_len} pezzi)"
            _len_de = f" (mindestens {min_len} Stück)"
            _len_tr = f" (en az {min_len} adet)"
            _len_uz = f" (kamida {min_len} ta)"
            _len_es = f" (al menos {min_len} piezas)"
            _len_kk = f" (кем дегенде {min_len} құны)"

        super().__init__(
            functools.partial(
                self._validate,
                validator=validator,
                min_len=min_len,
                max_len=max_len,
                fixed_len=fixed_len,
            ),
            {
                "en": f"series of values{_len_en}{_each_en}, separated with «,»",
                "ru": f"списком значений{_len_ru}{_each_ru}, разделенных «,»",
                "fr": f"série de valeurs{_len_fr}{_each_fr}, séparées par «,»",
                "it": f"serie di valori{_len_it}{_each_it}, separati con «,»",
                "de": f"Liste von Werten{_len_de}{_each_de}, getrennt mit «,»",
                "tr": f"değerlerin listesi{_len_tr}{_each_tr}, «,» ile ayrılmış",
                "uz": f"qiymatlar ro'yxati{_len_uz}{_each_uz}, «,» bilan ajratilgan",
                "es": f"lista de valores{_len_es}{_each_es}, separados con «,»",
                "kk": f"мәндер тізімі{_len_kk}{_each_kk}, «,» бойынша бөлінген",
            },
            _internal_id="Series",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        validator: typing.Optional[Validator] = None,
        min_len: typing.Optional[int] = None,
        max_len: typing.Optional[int] = None,
        fixed_len: typing.Optional[int] = None,
    ) -> typing.List[ConfigAllowedTypes]:
        if not isinstance(value, (list, tuple, set)):
            value = str(value).split(",")

        if isinstance(value, (tuple, set)):
            value = list(value)

        if min_len is not None and len(value) < min_len:
            raise ValidationError(
                f"Passed value ({value}) contains less than {min_len} items"
            )

        if max_len is not None and len(value) > max_len:
            raise ValidationError(
                f"Passed value ({value}) contains more than {max_len} items"
            )

        if fixed_len is not None and len(value) != fixed_len:
            raise ValidationError(
                f"Passed value ({value}) must contain exactly {fixed_len} items"
            )

        value = [item.strip() if isinstance(item, str) else item for item in value]

        if isinstance(validator, Validator):
            for i, item in enumerate(value):
                try:
                    value[i] = validator.validate(item)
                except ValidationError:
                    raise ValidationError(
                        f"Passed value ({value}) contains invalid item"
                        f" ({str(item).strip()}), which must be {validator.doc['en']}"
                    )

        value = list(filter(lambda x: x, value))

        return value


class Link(Validator):
    """Valid url must be specified"""

    def __init__(self):
        super().__init__(
            lambda value: self._validate(value),
            {
                "en": "link",
                "ru": "ссылкой",
                "it": "collegamento",
                "de": "Link",
                "tr": "bağlantı",
                "uz": "havola",
                "es": "enlace",
                "kk": "сілтеме",
            },
            _internal_id="Link",
        )

    @staticmethod
    def _validate(value: ConfigAllowedTypes, /) -> str:
        try:
            if not utils.check_url(value):
                raise Exception("Invalid URL")
        except Exception:
            raise ValidationError(f"Passed value ({value}) is not a valid URL")

        return value


class String(Validator):
    """
    Checks for length of passed value and automatically converts it to string
    :param length: Exact length of string
    :param min_len: Minimal length of string
    :param max_len: Maximum length of string
    """

    def __init__(
        self,
        length: typing.Optional[int] = None,
        min_len: typing.Optional[int] = None,
        max_len: typing.Optional[int] = None,
    ):
        if length is not None:
            doc = {
                "en": f"string of length {length}",
                "ru": f"строкой из {length} символа(-ов)",
                "it": f"stringa di lunghezza {length}",
                "de": f"Zeichenkette mit Länge {length}",
                "tr": f"{length} karakter uzunluğunda dize",
                "uz": f"{length} ta belgi uzunlig'ida satr",
                "es": f"cadena de longitud {length}",
                "kk": f"{length} ұзындығында сөз",
            }
        else:
            if min_len is None:
                if max_len is None:
                    doc = {
                        "en": "string",
                        "ru": "строкой",
                        "it": "stringa",
                        "de": "Zeichenkette",
                        "tr": "dize",
                        "uz": "satr",
                        "es": "cadena",
                        "kk": "сөз",
                    }
                else:
                    doc = {
                        "en": f"string of length up to {max_len}",
                        "ru": f"строкой не более чем из {max_len} символа(-ов)",
                        "it": f"stringa di lunghezza massima {max_len}",
                        "de": f"Zeichenkette mit Länge bis zu {max_len}",
                        "tr": f"{max_len} karakter uzunluğunda dize",
                        "uz": f"{max_len} ta belgi uzunlig'ida satr",
                        "es": f"cadena de longitud {max_len}",
                        "kk": f"{max_len} ұзындығында сөз",
                    }
            elif max_len is not None:
                doc = {
                    "en": f"string of length from {min_len} to {max_len}",
                    "ru": f"строкой из {min_len}-{max_len} символа(-ов)",
                    "it": f"stringa di lunghezza da {min_len} a {max_len}",
                    "de": f"Zeichenkette mit Länge von {min_len} bis {max_len}",
                    "tr": f"{min_len}-{max_len} karakter uzunluğunda dize",
                    "uz": f"{min_len}-{max_len} ta belgi uzunlig'ida satr",
                    "es": f"cadena de longitud {min_len}-{max_len}",
                    "kk": f"{min_len}-{max_len} ұзындығында сөз",
                }
            else:
                doc = {
                    "en": f"string of length at least {min_len}",
                    "ru": f"строкой не менее чем из {min_len} символа(-ов)",
                    "it": f"stringa di lunghezza minima {min_len}",
                    "de": f"Zeichenkette mit Länge mindestens {min_len}",
                    "tr": f"{min_len} karakter uzunluğunda dize",
                    "uz": f"{min_len} ta belgi uzunlig'ida satr",
                    "es": f"cadena de longitud {min_len}",
                    "kk": f"{min_len} ұзындығында сөз",
                }

        super().__init__(
            functools.partial(
                self._validate,
                length=length,
                min_len=min_len,
                max_len=max_len,
            ),
            doc,
            _internal_id="String",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        length: typing.Optional[int],
        min_len: typing.Optional[int],
        max_len: typing.Optional[int],
    ) -> str:
        if (
            isinstance(length, int)
            and len(list(grapheme.graphemes(str(value)))) != length
        ):
            raise ValidationError(
                f"Passed value ({value}) must be a length of {length}"
            )

        if (
            isinstance(min_len, int)
            and len(list(grapheme.graphemes(str(value)))) < min_len
        ):
            raise ValidationError(
                f"Passed value ({value}) must be a length of at least {min_len}"
            )

        if (
            isinstance(max_len, int)
            and len(list(grapheme.graphemes(str(value)))) > max_len
        ):
            raise ValidationError(
                f"Passed value ({value}) must be a length of up to {max_len}"
            )

        return str(value)


class RegExp(Validator):
    """
    Checks if value matches the regex
    :param regex: Regex to match
    :param flags: Flags to pass to re.compile
    :param description: Description of regex
    """

    def __init__(
        self,
        regex: str,
        flags: typing.Optional[re.RegexFlag] = None,
        description: typing.Optional[typing.Union[dict, str]] = None,
    ):
        if not flags:
            flags = 0

        try:
            re.compile(regex, flags=flags)
        except re.error as e:
            raise Exception(f"{regex} is not a valid regex") from e

        if description is None:
            doc = {
                "en": f"string matching pattern «{regex}»",
                "ru": f"строкой, соответствующей шаблону «{regex}»",
                "it": f"stringa che corrisponde al modello «{regex}»",
                "de": f"Zeichenkette, die dem Muster «{regex}» entspricht",
                "tr": f"«{regex}» kalıbına uygun dize",
                "uz": f"«{regex}» shabloniga mos matn",
                "es": f"cadena que coincide con el patrón «{regex}»",
                "kk": f"«{regex}» үлгісіне сәйкес сөз",
            }
        else:
            if isinstance(description, str):
                doc = {"en": description}
            else:
                doc = description

        super().__init__(
            functools.partial(self._validate, regex=regex, flags=flags),
            doc,
            _internal_id="RegExp",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        regex: str,
        flags: typing.Optional[re.RegexFlag],
    ) -> str:
        if not re.match(regex, str(value), flags=flags):
            raise ValidationError(f"Passed value ({value}) must follow pattern {regex}")

        return str(value)


class Float(Validator):
    """
    Checks whether passed argument is a float value
    :param minimum: Minimal number to be passed
    :param maximum: Maximum number to be passed
    """

    def __init__(
        self,
        minimum: typing.Optional[float] = None,
        maximum: typing.Optional[float] = None,
    ):
        _sign_en = "positive " if minimum is not None and minimum == 0 else ""
        _sign_ru = "положительным " if minimum is not None and minimum == 0 else ""
        _sign_fr = "positif " if minimum is not None and minimum == 0 else ""
        _sign_it = "positivo " if minimum is not None and minimum == 0 else ""
        _sign_de = "positiv " if minimum is not None and minimum == 0 else ""
        _sign_tr = "pozitif " if minimum is not None and minimum == 0 else ""
        _sign_uz = "musbat " if minimum is not None and minimum == 0 else ""
        _sign_es = "positivo " if minimum is not None and minimum == 0 else ""
        _sign_kk = "мың " if minimum is not None and minimum == 0 else ""

        _sign_en = "negative " if maximum is not None and maximum == 0 else _sign_en
        _sign_ru = (
            "отрицательным " if maximum is not None and maximum == 0 else _sign_ru
        )
        _sign_fr = "négatif " if maximum is not None and maximum == 0 else _sign_fr
        _sign_it = "negativo " if maximum is not None and maximum == 0 else _sign_it
        _sign_de = "negativ " if maximum is not None and maximum == 0 else _sign_de
        _sign_tr = "negatif " if maximum is not None and maximum == 0 else _sign_tr
        _sign_uz = "manfiy " if maximum is not None and maximum == 0 else _sign_uz
        _sign_es = "negativo " if maximum is not None and maximum == 0 else _sign_es
        _sign_kk = "мінус " if maximum is not None and maximum == 0 else _sign_kk

        if minimum is not None and minimum != 0:
            doc = (
                {
                    "en": f"{_sign_en}float greater than {minimum}",
                    "ru": f"{_sign_ru}дробным числом больше {minimum}",
                    "fr": f"{_sign_fr}flottant supérieur à {minimum}",
                    "it": f"{_sign_it}numero decimale maggiore di {minimum}",
                    "de": f"{_sign_de}Fließkommazahl größer als {minimum}",
                    "tr": f"{_sign_tr}ondalık sayı {minimum} dan büyük",
                    "uz": f"{_sign_uz}butun son {minimum} dan katta",
                    "es": f"{_sign_es}número decimal mayor que {minimum}",
                    "kk": f"{_sign_kk}сандық сан {minimum} тан аспау",
                }
                if maximum is None and maximum != 0
                else {
                    "en": f"{_sign_en}float from {minimum} to {maximum}",
                    "ru": (
                        f"{_sign_ru}дробным числом в промежутке от {minimum} до"
                        f" {maximum}"
                    ),
                    "fr": f"{_sign_fr}flottant de {minimum} à {maximum}",
                    "it": (
                        f"{_sign_it}numero decimale compreso tra {minimum} e {maximum}"
                    ),
                    "de": f"{_sign_de}Fließkommazahl von {minimum} bis {maximum}",
                    "tr": f"{_sign_tr}ondalık sayı {minimum} ile {maximum} arasında",
                    "uz": f"{_sign_uz}butun son {minimum} dan {maximum} gacha",
                    "es": f"{_sign_es}número decimal de {minimum} a {maximum}",
                    "kk": f"{_sign_kk}сандық сан {minimum} ден {maximum} ге",
                }
            )

        elif maximum is None and maximum != 0:
            doc = {
                "en": f"{_sign_en}float",
                "ru": f"{_sign_ru}дробным числом",
                "fr": f"{_sign_fr}flottant",
                "it": f"{_sign_it}numero decimale",
                "de": f"{_sign_de}Fließkommazahl",
                "tr": f"{_sign_tr}ondalık sayı",
                "uz": f"{_sign_uz}butun son",
                "es": f"{_sign_es}número decimal",
                "kk": f"{_sign_kk}сандық сан",
            }
        else:
            doc = {
                "en": f"{_sign_en}float less than {maximum}",
                "ru": f"{_sign_ru}дробным числом меньше {maximum}",
                "fr": f"{_sign_fr}flottant inférieur à {maximum}",
                "it": f"{_sign_it}numero decimale minore di {maximum}",
                "de": f"{_sign_de}Fließkommazahl kleiner als {maximum}",
                "tr": f"{_sign_tr}ondalık sayı {maximum} dan küçük",
                "uz": f"{_sign_uz}butun son {maximum} dan kichik",
                "es": f"{_sign_es}número decimal menor que {maximum}",
                "kk": f"{_sign_kk}сандық сан {maximum} тан кіші",
            }

        super().__init__(
            functools.partial(
                self._validate,
                minimum=minimum,
                maximum=maximum,
            ),
            doc,
            _internal_id="Float",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        minimum: typing.Optional[float] = None,
        maximum: typing.Optional[float] = None,
    ) -> float:
        try:
            value = float(str(value).strip().replace(",", "."))
        except ValueError:
            raise ValidationError(f"Passed value ({value}) must be a float")

        if minimum is not None and value < minimum:
            raise ValidationError(f"Passed value ({value}) is lower than minimum one")

        if maximum is not None and value > maximum:
            raise ValidationError(f"Passed value ({value}) is greater than maximum one")

        return value


class TelegramID(Validator):
    def __init__(self):
        super().__init__(
            self._validate,
            "Telegram ID",
            _internal_id="TelegramID",
        )

    @staticmethod
    def _validate(value: ConfigAllowedTypes, /) -> int:
        e = ValidationError(f"Passed value ({value}) is not a valid telegram id")

        try:
            value = int(str(value).strip())
        except Exception:
            raise e

        if str(value).startswith("-100"):
            value = int(str(value)[4:])

        if value > 2**64 - 1 or value < 0:
            raise e

        return value


class Union(Validator):
    def __init__(self, *validators):
        doc = {
            "en": "one of the following:\n",
            "ru": "одним из следующего:\n",
            "it": "uno dei seguenti:\n",
            "de": "einer der folgenden:\n",
            "tr": "aşağıdakilerden biri:\n",
            "uz": "quyidagi biri:\n",
            "es": "uno de los siguientes:\n",
            "kk": "келесілердің бірі:\n",
        }

        def case(x: str) -> str:
            return x[0].upper() + x[1:]

        for validator in validators:
            for key in doc:
                doc[key] += f"- {case(validator.doc.get(key, validator.doc['en']))}\n"

        for key, value in doc.items():
            doc[key] = value.strip()

        super().__init__(
            functools.partial(self._validate, validators=validators),
            doc,
            _internal_id="Union",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        validators: list,
    ) -> ConfigAllowedTypes:
        for validator in validators:
            try:
                return validator.validate(value)
            except ValidationError:
                pass

        raise ValidationError(f"Passed value ({value}) is not valid")


class NoneType(Validator):
    def __init__(self):
        super().__init__(
            self._validate,
            {
                "en": "empty value",
                "ru": "пустым значением",
                "it": "valore vuoto",
                "de": "leeren Wert",
                "tr": "boş değer",
                "uz": "bo'sh qiymat",
                "es": "valor vacío",
                "kk": "бос мән",
            },
            _internal_id="NoneType",
        )

    @staticmethod
    def _validate(value: ConfigAllowedTypes, /) -> None:
        if not value:
            raise ValidationError(f"Passed value ({value}) is not None")

        return None


class Hidden(Validator):
    def __init__(self, validator: typing.Optional[Validator] = None):
        if not validator:
            validator = String()

        super().__init__(
            functools.partial(self._validate, validator=validator),
            validator.doc,
            _internal_id="Hidden",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        validator: Validator,
    ) -> ConfigAllowedTypes:
        return validator.validate(value)


class Emoji(Validator):
    """
    Checks whether passed argument is a valid emoji
    :param quantity: Number of emojis to be passed
    :param min_len: Minimum number of emojis
    :param max_len: Maximum number of emojis
    """

    def __init__(
        self,
        length: typing.Optional[int] = None,
        min_len: typing.Optional[int] = None,
        max_len: typing.Optional[int] = None,
    ):
        if length is not None:
            doc = {
                "en": f"{length} emojis",
                "ru": f"ровно {length} эмодзи",
                "it": f"{length} emoji",
                "de": f"genau {length} Emojis",
                "tr": f"tam {length} emoji",
                "uz": f"to'g'ri {length} emoji",
                "es": f"exactamente {length} emojis",
                "kk": f"тоғыз {length} емодзи",
            }
        elif min_len is not None and max_len is not None:
            doc = {
                "en": f"{min_len} to {max_len} emojis",
                "ru": f"от {min_len} до {max_len} эмодзи",
                "it": f"{min_len} a {max_len} emoji",
                "de": f"zwischen {min_len} und {max_len} Emojis",
                "tr": f"{min_len} ile {max_len} arasında emoji",
                "uz": f"{min_len} dan {max_len} gacha emoji",
                "es": f"entre {min_len} y {max_len} emojis",
                "kk": f"{min_len} ден {max_len} ге емодзи",
            }
        elif min_len is not None:
            doc = {
                "en": f"at least {min_len} emoji",
                "ru": f"не менее {min_len} эмодзи",
                "it": f"almeno {min_len} emoji",
                "de": f"mindestens {min_len} Emojis",
                "tr": f"en az {min_len} emoji",
                "uz": f"kamida {min_len} emoji",
                "es": f"al menos {min_len} emojis",
                "kk": f"кем дегенде {min_len} емодзи",
            }
        elif max_len is not None:
            doc = {
                "en": f"no more than {max_len} emojis",
                "ru": f"не более {max_len} эмодзи",
                "it": f"non più di {max_len} emoji",
                "de": f"maximal {max_len} Emojis",
                "tr": f"en fazla {max_len} emoji",
                "uz": f"{max_len} dan ko'proq emoji",
                "es": f"no más de {max_len} emojis",
                "kk": f"{max_len} ден асты емодзи",
            }
        else:
            doc = {
                "en": "emoji",
                "ru": "эмодзи",
                "it": "emoji",
                "de": "Emoji",
                "tr": "emoji",
                "uz": "emoji",
                "es": "emojis",
                "kk": "емодзи",
            }

        super().__init__(
            functools.partial(
                self._validate,
                length=length,
                min_len=min_len,
                max_len=max_len,
            ),
            doc,
            _internal_id="Emoji",
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        length: typing.Optional[int],
        min_len: typing.Optional[int],
        max_len: typing.Optional[int],
    ) -> str:
        value = str(value)
        passed_length = len(list(grapheme.graphemes(value)))

        if length is not None and passed_length != length:
            raise ValidationError(f"Passed value ({value}) is not {length} emojis long")

        if (
            min_len is not None
            and max_len is not None
            and (passed_length < min_len or passed_length > max_len)
        ):
            raise ValidationError(
                f"Passed value ({value}) is not between {min_len} and {max_len} emojis"
                " long"
            )

        if min_len is not None and passed_length < min_len:
            raise ValidationError(
                f"Passed value ({value}) is not at least {min_len} emojis long"
            )

        if max_len is not None and passed_length > max_len:
            raise ValidationError(
                f"Passed value ({value}) is not no more than {max_len} emojis long"
            )

        if any(emoji not in ALLOWED_EMOJIS for emoji in grapheme.graphemes(value)):
            raise ValidationError(
                f"Passed value ({value}) is not a valid string with emojis"
            )

        return value


class EntityLike(RegExp):
    def __init__(self):
        super().__init__(
            regex=r"^(?:@|https?://t\.me/)?(?:[a-zA-Z0-9_]{5,32}|[a-zA-Z0-9_]{1,32}\?[a-zA-Z0-9_]{1,32})$",
            description={
                "en": "link to entity, username or Telegram ID",
                "ru": "ссылка на сущность, имя пользователя или Telegram ID",
                "it": "link all'ent entità, nome utente o ID Telegram",
                "de": "Link zu einer Entität, Benutzername oder Telegram-ID",
                "tr": "bir varlığa bağlantı, kullanıcı adı veya Telegram kimliği",
                "uz": "entityga havola, foydalanuvchi nomi yoki Telegram ID",
                "es": "enlace a la entidad, nombre de usuario o ID de Telegram",
                "kk": "сынаққа сілтеме, пайдаланушы аты немесе Telegram ID",
            },
        )

    @staticmethod
    def _validate(
        value: ConfigAllowedTypes,
        /,
        *,
        regex: str,
        flags: typing.Optional[re.RegexFlag],
    ) -> typing.Union[str, int]:
        value = super()._validate(value, regex=regex, flags=flags)

        if value.isdigit():
            if value.startswith("-100"):
                value = value[4:]

            value = int(value)

        if value.startswith("https://t.me/"):
            value = value.split("https://t.me/")[1]

        if not value.startswith("@"):
            value = f"@{value}"

        return value
