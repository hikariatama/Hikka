import functools
from typing import Any, Optional, Union
from . import utils
import grapheme


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
    """

    def __init__(self, validator: callable, doc: Union[str, dict] = None):
        self.validate = validator

        if isinstance(doc, str):
            doc = {"en": doc}

        self.doc = doc


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
    )


def _Integer(
    value: Any,
    /,
    *,
    digits: int,
    minimum: int,
    maximum: int,
    positive: bool,
) -> Union[int, None]:
    try:
        value = int(value)
    except ValueError:
        raise ValidationError(f"Passed value ({value}) must be a number")

    if minimum is not None and value < minimum:
        raise ValidationError(f"Passed value ({value}) is lower than minimum one")

    if maximum is not None and value > maximum:
        raise ValidationError(f"Passed value ({value}) is greater than maximum one")

    if positive is not None:
        if positive and value < 0:
            raise ValidationError(f"Passed value ({value}) is not positive")
        elif not positive and value >= 0:
            raise ValidationError(f"Passed value ({value}) is not negative")

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
    positive: Optional[bool] = None,
) -> Validator:
    """
    Checks wheter passed argument is an integer value
    :param digits: Digits quantity, which must be passed
    :param minimum: Minimal number to be passed
    :param maximum: Maximum number to be passed
    :param positive: Whether the number needs to be positive.
                     If `False` is passed, it is considered that number
                     needs to be negative. If `True` is passed, it is
                     considered that number needs to be positive.
    """
    if digits is not None:
        doc = {
            "en": f"number with exactly {digits} digits",
            "ru": f"числом, в котором {digits} цифр",
        }
    else:
        if positive is None:
            if minimum is not None:
                if maximum is None:
                    doc = {
                        "en": f"number >{minimum}",
                        "ru": f"числом >{minimum}",
                    }
                else:
                    doc = {
                        "en": f"number in range [{minimum}, {maximum}]",
                        "ru": f"числом в промежутке [{minimum}, {maximum}]",
                    }
            else:
                if maximum is None:
                    doc = {
                        "en": "number",
                        "ru": "числом",
                    }
                else:
                    doc = {
                        "en": f"number <{maximum}",
                        "ru": f"числом <{maximum}",
                    }
        else:
            if positive:
                doc = {"en": "positive number", "ru": "положительным числом"}
            else:
                doc = {"en": "negative number", "ru": "отрицательным числом"}

    return Validator(
        functools.partial(
            _Integer,
            digits=digits,
            minimum=minimum,
            maximum=maximum,
            positive=positive,
        ),
        doc,
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
    )


def Series(separator: str = ",") -> Validator:
    """Just a placeholder to let user know about the format of input data for config value"""
    return Validator(
        lambda value: value,
        {
            "en": f"series of values, separated with «{separator}»",
            "ru": f"списком значений, разделенных «{separator}»",
        },
    )


def _Link(value: Any, /) -> str:
    if not utils.check_url(value):
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
    )


def _String(value: Any, /, *, length: int) -> str:
    if isinstance(length, int) and len(list(grapheme.graphemes(value))) != length:
        raise ValidationError(f"Passed value ({value}) must be a length of {length}")

    return value


def String(length: Optional[int] = None) -> Validator:
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

    return Validator(functools.partial(_String, length=length), doc)
