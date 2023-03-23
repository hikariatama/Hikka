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
from .translations import SUPPORTED_LANGUAGES, translator

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
            doc = {lang: doc for lang in SUPPORTED_LANGUAGES}

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
            translator.getdict("validators.boolean"),
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
        _signs = (
            translator.getdict("validators.positive")
            if minimum is not None and minimum == 0
            else (
                translator.getdict("validators.negative")
                if maximum is not None and maximum == 0
                else {}
            )
        )
        _digits = (
            translator.getdict("validators.digits", digits=digits)
            if digits is not None
            else {}
        )

        if minimum is not None and minimum != 0:
            doc = (
                {
                    lang: text.format(
                        sign=_signs.get(lang, ""),
                        digits=_digits.get(lang, ""),
                        minimum=minimum,
                    )
                    for lang, text in translator.getdict(
                        "validators.integer_min"
                    ).items()
                }
                if maximum is None and maximum != 0
                else {
                    lang: text.format(
                        sign=_signs.get(lang, ""),
                        digits=_digits.get(lang, ""),
                        minimum=minimum,
                        maximum=maximum,
                    )
                    for lang, text in translator.getdict(
                        "validators.integer_range"
                    ).items()
                }
            )
        elif maximum is None and maximum != 0:
            doc = {
                lang: text.format(
                    sign=_signs.get(lang, ""), digits=_digits.get(lang, "")
                )
                for lang, text in translator.getdict("validators.integer").items()
            }
        else:
            doc = {
                lang: text.format(
                    sign=_signs.get(lang, ""),
                    digits=_digits.get(lang, ""),
                    maximum=maximum,
                )
                for lang, text in translator.getdict("validators.integer_max").items()
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
        super().__init__(
            functools.partial(self._validate, possible_values=possible_values),
            translator.getdict(
                "validators.choice",
                possible=" / ".join(list(map(str, possible_values))),
            ),
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
            translator.getdict("validators.multichoice", possible=possible),
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

        _each = (
            {
                lang: text.format(each=trans(lang))
                for lang, text in translator.getdict("validators.each").items()
            }
            if validator is not None
            else {}
        )

        if fixed_len is not None:
            _len = translator.getdict("validators.fixed_len", fixed_len=fixed_len)
        elif min_len is None:
            if max_len is None:
                _len = {}
            else:
                _len = translator.getdict("validators.max_len", max_len=max_len)
        elif max_len is not None:
            _len = translator.getdict(
                "validators.len_range", min_len=min_len, max_len=max_len
            )
        else:
            _len = translator.getdict("validators.min_len", min_len=min_len)

        super().__init__(
            functools.partial(
                self._validate,
                validator=validator,
                min_len=min_len,
                max_len=max_len,
                fixed_len=fixed_len,
            ),
            {
                lang: text.format(each=_each.get(lang, ""), len=_len.get(lang, ""))
                for lang, text in translator.getdict("validators.series").items()
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
            translator.getdict("validators.link"),
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
            doc = translator.getdict("validators.string_fixed_len", length=length)
        else:
            if min_len is None:
                if max_len is None:
                    doc = translator.getdict("validators.string")
                else:
                    doc = translator.getdict(
                        "validators.string_max_len", max_len=max_len
                    )
            elif max_len is not None:
                doc = translator.getdict(
                    "validators.string_len_range", min_len=min_len, max_len=max_len
                )
            else:
                doc = translator.getdict("validators.string_min_len", min_len=min_len)

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
            doc = translator.getdict("validators.regex", regex=regex)
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
        _signs = (
            translator.getdict("validators.positive")
            if minimum is not None and minimum == 0
            else (
                translator.getdict("validators.negative")
                if maximum is not None and maximum == 0
                else {}
            )
        )

        if minimum is not None and minimum != 0:
            doc = (
                {
                    lang: text.format(sign=_signs.get(lang, ""), minimum=minimum)
                    for lang, text in translator.getdict("validators.float_min").items()
                }
                if maximum is None and maximum != 0
                else {
                    lang: text.format(
                        sign=_signs.get(lang, ""), minimum=minimum, maximum=maximum
                    )
                    for lang, text in translator.getdict(
                        "validators.float_range"
                    ).items()
                }
            )

        elif maximum is None and maximum != 0:
            doc = {
                lang: text.format(sign=_signs.get(lang, ""))
                for lang, text in translator.getdict("validators.float").items()
            }
        else:
            doc = {
                lang: text.format(sign=_signs.get(lang, ""), maximum=maximum)
                for lang, text in translator.getdict("validators.float_max").items()
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
        doc = translator.getdict("validators.union")

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
            translator.getdict("validators.empty"),
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
            doc = translator.getdict("validators.emoji_fixed_len", length=length)
        elif min_len is not None and max_len is not None:
            doc = translator.getdict(
                "validators.emoji_len_range", min_len=min_len, max_len=max_len
            )
        elif min_len is not None:
            doc = translator.getdict("validators.emoji_min_len", min_len=min_len)
        elif max_len is not None:
            doc = translator.getdict("validators.emoji_max_len", max_len=max_len)
        else:
            doc = translator.getdict("validators.emoji")

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
            description=translator.getdict("validators.entity_like"),
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
