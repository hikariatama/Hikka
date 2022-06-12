import functools
from typing import Any, Optional, Union

from . import utils
import grapheme
import re


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
                    "ua": "докстрiнгом",
                    "jp": "ヒント",
                }
                Use instrumental case with lowercase
    :param _internal_id: Do not pass anything here, or things will break
    """

    def __init__(
        self,
        validator: callable,
        doc: Union[str, dict] = None,
        _internal_id: int = None,
    ):
        self.validate = validator

        if isinstance(doc, str):
            doc = {"en": doc, "ru": doc}

        self.doc = doc
        self.internal_id = _internal_id


def _Boolean(value: Any, /) -> bool:
    true_cases = ["True", "true", "1", 1, True]
    false_cases = ["False", "false", "0", 0, False]
    if value not in true_cases + false_cases:
        raise ValidationError("Passed value must be a boolean")

    return value in true_cases


def Boolean() -> Validator:
    """
    Any logical value to be passed
    `1`, `"1"` etc. will be automatically converted to bool
    """
    return Validator(
        _Boolean,
        {"en": "boolean", "ru": "логическим значением"},
        _internal_id="Boolean",
    )


def _Integer(
    value: Any,
    /,
    *,
    digits: int,
    minimum: int,
    maximum: int,
) -> Union[int, None]:
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


def Integer(
    *,
    digits: Optional[int] = None,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> Validator:
    """
    Checks whether passed argument is an integer value
    :param digits: Digits quantity, which must be passed
    :param minimum: Minimal number to be passed
    :param maximum: Maximum number to be passed
    """
    _sign_en = "positive " if minimum is not None and minimum == 0 else ""
    _sign_ru = "положительным " if minimum is not None and minimum == 0 else ""

    _sign_en = "negative " if maximum is not None and maximum == 0 else _sign_en
    _sign_ru = "отрицательным " if maximum is not None and maximum == 0 else _sign_ru

    _digits_en = f" with exactly {digits} digits" if digits is not None else ""
    _digits_ru = f", в котором ровно {digits} цифр " if digits is not None else ""

    if minimum is not None and minimum != 0:
        if maximum is None and maximum != 0:
            doc = {
                "en": f"{_sign_en}integer greater than {minimum}{_digits_en}",
                "ru": f"{_sign_ru}целым числом больше {minimum}{_digits_ru}",
            }
        else:
            doc = {
                "en": f"{_sign_en}integer from {minimum} to {maximum}{_digits_en}",
                "ru": f"{_sign_ru}целым числом в промежутке от {minimum} до {maximum}{_digits_ru}",
            }
    else:
        if maximum is None and maximum != 0:
            doc = {
                "en": f"{_sign_en}integer{_digits_en}",
                "ru": f"{_sign_ru}целым числом{_digits_ru}",
            }
        else:
            doc = {
                "en": f"{_sign_en}integer less than {maximum}{_digits_en}",
                "ru": f"{_sign_ru}целым числом меньше {maximum}{_digits_ru}",
            }

    return Validator(
        functools.partial(
            _Integer,
            digits=digits,
            minimum=minimum,
            maximum=maximum,
        ),
        doc,
        _internal_id="Integer",
    )


def _Choice(value: Any, /, *, possible_values: list) -> Any:
    if value not in possible_values:
        raise ValidationError(
            f"Passed value ({value}) is not one of the following: {'/'.join(list(map(str, possible_values)))}"
        )

    return value


def Choice(possible_values: list, /) -> Validator:
    """
    Check whether entered value is in the allowed list
    :param possible_values: Allowed values to be passed to config param
    """
    return Validator(
        functools.partial(_Choice, possible_values=possible_values),
        {
            "en": f"one of the following: {'/'.join(list(map(str, possible_values)))}",
            "ru": f"одним из: {'/'.join(list(map(str, possible_values)))}",
        },
        _internal_id="Choice",
    )


def _Series(
    value: Any,
    /,
    *,
    validator: Optional[Validator],
    min_len: Optional[int],
    max_len: Optional[int],
    fixed_len: Optional[int],
):
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
                    f"Passed value ({value}) contains invalid item ({str(item).strip()}), which must be {validator.doc['en']}"
                )

    value = list(filter(lambda x: x, value))

    return value


def Series(
    validator: Optional[Validator] = None,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
    fixed_len: Optional[int] = None,
) -> Validator:
    """
    Represents the series of value (simply `list`)
    :param separator: With which separator values must be separated
    :param validator: Internal validator for each sequence value
    :param min_len: Minimal number of series items to be passed
    :param max_len: Maximum number of series items to be passed
    :param fixed_len: Fixed number of series items to be passed
    """

    _each_en = f" (each must be {validator.doc['en']})" if validator is not None else ""
    _each_ru = f" (каждое должно быть {validator.doc['ru']})" if validator is not None else ""  # fmt: skip

    if fixed_len is not None:
        _len_en = f" (exactly {fixed_len} pcs.)"
        _len_ru = f" (ровно {fixed_len} шт.)"
    else:
        if min_len is not None:
            if max_len is not None:
                _len_en = f" (from {min_len} to {max_len} pcs.)"
                _len_ru = f" (от {min_len} до {max_len} шт.)"
            else:
                _len_en = f" (at least {min_len} pcs.)"
                _len_ru = f" (как минимум {min_len} шт.)"
        else:
            if max_len is not None:
                _len_en = f" (up to {max_len} pcs.)"
                _len_ru = f" (до {max_len} шт.)"
            else:
                _len_en = ""
                _len_ru = ""

    doc = {
        "en": f"series of values{_len_en}{_each_en}, separated with «,»",
        "ru": f"списком значений{_len_ru}{_each_ru}, разделенных «,»",
    }

    return Validator(
        functools.partial(
            _Series,
            validator=validator,
            min_len=min_len,
            max_len=max_len,
            fixed_len=fixed_len,
        ),
        doc,
        _internal_id="Series",
    )


def _Link(value: Any, /) -> str:
    try:
        assert utils.check_url(value)
    except Exception:
        raise ValidationError(f"Passed value ({value}) is not a valid URL")

    return value


def Link() -> Validator:
    """Valid url must be specified"""
    return Validator(
        lambda value: _Link(value),
        {
            "en": "link",
            "ru": "ссылкой",
        },
        _internal_id="Link",
    )


def _String(value: Any, /, *, length: int) -> str:
    if isinstance(length, int) and len(list(grapheme.graphemes(str(value)))) != length:
        raise ValidationError(f"Passed value ({value}) must be a length of {length}")

    return str(value)


def String(length: Optional[int] = None) -> Validator:
    """
    Checks for length of passed value and automatically converts it to string
    :param length: Exact length of string
    """

    if length is not None:
        doc = {
            "en": f"string of length {length}",
            "ru": f"строкой из {length} символа(-ов)",
        }
    else:
        doc = {
            "en": "string",
            "ru": "строкой",
        }

    return Validator(
        functools.partial(_String, length=length),
        doc,
        _internal_id="String",
    )


def _RegExp(value: Any, /, *, regex: str) -> str:
    if not re.match(regex, value):
        raise ValidationError(f"Passed value ({value}) must follow pattern {regex}")

    return value


def RegExp(regex: str) -> Validator:
    """
    Checks if value matches the regex
    :param regex: Regex to match
    """

    try:
        re.compile(regex)
    except re.error as e:
        raise Exception(f"{regex} is not a valid regex") from e

    doc = {
        "en": f"string matching pattern «{regex}»",
        "ru": f"строкой, соответствующей шаблону «{regex}»",
    }

    return Validator(
        functools.partial(_RegExp, regex=regex),
        doc,
        _internal_id="RegExp",
    )


def _Float(
    value: Any,
    /,
    *,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> Union[int, None]:
    try:
        value = float(str(value).strip().replace(",", "."))
    except ValueError:
        raise ValidationError(f"Passed value ({value}) must be a float")

    if minimum is not None and value < minimum:
        raise ValidationError(f"Passed value ({value}) is lower than minimum one")

    if maximum is not None and value > maximum:
        raise ValidationError(f"Passed value ({value}) is greater than maximum one")

    return value


def Float(
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> Validator:
    """
    Checks whether passed argument is a float value
    :param minimum: Minimal number to be passed
    :param maximum: Maximum number to be passed
    """
    _sign_en = "positive " if minimum is not None and minimum == 0 else ""
    _sign_ru = "положительным " if minimum is not None and minimum == 0 else ""

    _sign_en = "negative " if maximum is not None and maximum == 0 else _sign_en
    _sign_ru = "отрицательным " if maximum is not None and maximum == 0 else _sign_ru

    if minimum is not None and minimum != 0:
        if maximum is None and maximum != 0:
            doc = {
                "en": f"{_sign_en}float greater than {minimum}",
                "ru": f"{_sign_ru}дробным числом больше {minimum}",
            }
        else:
            doc = {
                "en": f"{_sign_en}float from {minimum} to {maximum}",
                "ru": f"{_sign_ru}дробным числом в промежутке от {minimum} до {maximum}",
            }
    else:
        if maximum is None and maximum != 0:
            doc = {
                "en": f"{_sign_en}float",
                "ru": f"{_sign_ru}дробным числом",
            }
        else:
            doc = {
                "en": f"{_sign_en}float less than {maximum}",
                "ru": f"{_sign_ru}дробным числом меньше {maximum}",
            }

    return Validator(
        functools.partial(
            _Float,
            minimum=minimum,
            maximum=maximum,
        ),
        doc,
        _internal_id="Float",
    )


def _TelegramID(value: Any, /):
    e = ValidationError(f"Passed value ({value}) is not a valid telegram id")

    try:
        value = int(str(value).strip())
    except Exception:
        raise e

    if str(value).startswith("-100"):
        value = int(str(value)[4:])

    if value > 2**32 - 1 or value < 0:
        raise e

    return value


def TelegramID() -> Validator:
    return Validator(
        _TelegramID,
        "Telegram ID",
        _internal_id="TelegramID",
    )


def _Union(value: Any, /, *, validators: list):
    for validator in validators:
        try:
            return validator.validate(value)
        except ValidationError:
            pass

    raise ValidationError(f"Passed value ({value}) is not valid")


def Union(*validators) -> Validator:
    doc = {
        "en": "one of the following:\n",
        "ru": "одним из следующего:\n",
    }

    case = lambda x: x[0].upper() + x[1:]

    for validator in validators:
        doc["en"] += f"- {case(validator.doc['en'])}\n"
        doc["ru"] += f"- {case(validator.doc['ru'])}\n"

    doc["en"] = doc["en"].strip()
    doc["ru"] = doc["ru"].strip()

    return Validator(
        functools.partial(_Union, validators=validators),
        doc,
        _internal_id="Union",
    )


def _NoneType(value: Any, /) -> None:
    if value not in {None, False, ""}:
        raise ValidationError(f"Passed value ({value}) is not None")

    return None


def NoneType() -> Validator:
    return Validator(
        _NoneType,
        "`None`",
        _internal_id="NoneType",
    )


def _Hidden(value: Any, /, *, validator: Validator) -> Any:
    return validator.validate(value)


def Hidden(validator: Optional[Validator] = None) -> Validator:
    if not validator:
        validator = String()

    return Validator(
        functools.partial(_Hidden, validator=validator),
        validator.doc,
        _internal_id="Hidden",
    )
