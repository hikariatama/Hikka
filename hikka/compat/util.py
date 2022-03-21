#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2021 The Authors

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

#    Modded by GeekTG Team

import inspect
import logging

from telethon.extensions import markdown

logger = logging.getLogger(__name__)

COMMAND_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789_"


def get_cmd_name(pattern):
    """Get the first word out of a regex, hoping that it is easy to parse"""
    # Find command string: ugly af :)
    logger.debug(pattern)
    if pattern.startswith("(?i)"):
        pattern = pattern[4:]

    if pattern.startswith("^"):
        pattern = pattern[1:]

    if pattern.startswith("."):
        # That seems to be the normal command prefix
        pattern = pattern[1:]
    elif pattern.startswith(r"\."):
        # That seems to be the normal command prefix
        pattern = pattern[2:]
    else:
        logger.info(
            "Unable to register for non-command-based outgoing messages, pattern=%s",
            pattern,
        )
        return False

    # Find first non-alpha character and get all chars before it
    i = 0
    cmd = ""
    while i < len(pattern) and pattern[i] in COMMAND_CHARS:
        i += 1
        cmd = pattern[:i]

    if not cmd:
        logger.info(
            "Unable to identify command correctly, i=%d, pattern=%s", i, pattern
        )
        return False

    return cmd


class MarkdownBotPassthrough:
    """Passthrough class that forces markdown mode"""

    def __init__(self, under):
        self.__under = under

    def __function(self, func, *args, **kwargs):
        args = list(args)
        kwargs = dict(kwargs)
        for i, arg in enumerate(args):
            if isinstance(arg, type(self)):
                args[i] = arg.__under

        for key, arg in kwargs.items():
            if isinstance(arg, type(self)):
                kwargs[key] = arg.__under

        kwargs.setdefault("parse_mode", "markdown")

        try:
            ret = func(*args, **kwargs)
        except TypeError:
            del kwargs["parse_mode"]
            ret = func(*args, **kwargs)
        else:
            if inspect.iscoroutine(ret):

                async def wrapper():
                    try:
                        ret2 = await ret
                    except TypeError:
                        del kwargs["parse_mode"]
                        ret2 = await func(*args, **kwargs)
                    return self.__convert(ret2)

                return wrapper()

        return self.__convert(ret)

    def __convert(self, ret):
        if inspect.iscoroutine(ret):

            async def wrapper():
                return self.__convert(await ret)

            return wrapper()

        if isinstance(ret, list):
            for i, thing in enumerate(ret):
                ret[i] = self.__convert(thing)
        elif getattr(
            getattr(getattr(ret, "__self__", ret), "__class__", None), "__module__", ""
        ).startswith("telethon"):
            ret = MarkdownBotPassthrough(ret)
            if hasattr(ret, "text"):
                logger.debug(
                    "%r(%s) %r(%s)",
                    ret.entities,
                    type(ret.entities),
                    ret.message,
                    type(ret.message),
                )
                ret.text = markdown.unparse(
                    ret.message, [x.__under for x in ret.entities or []]
                )

        return ret

    def __repr__(self):
        return repr(self.__under)

    def __str__(self):
        return str(self.__under)

    def __bytes__(self):
        return bytes(self.__under)

    def __format__(self, *args, **kwargs):
        return format(self.__under)

    def __hash__(self):
        return hash(self.__under)

    def __bool__(self):
        return bool(self.__under)

    def __dir__(self):
        return dir(self.__under)

    def __call__(self, *args, **kwargs):
        return self.__function(self.__under, *args, **kwargs)

    def __len__(self):
        return len(self.__under)

    def __iter__(self):
        return iter(self.__under)

    def __reversed__(self):
        return reversed(self.__under)

    def __contains__(self, other):
        return other in self.__under

    def __enter__(self, *args, **kwargs):
        try:
            return self.__under.__enter__(*args, **kwargs)
        except AttributeError:
            return super().__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        try:
            return self.__under.__exit__(*args, **kwargs)
        except AttributeError:
            return super().__exit__(*args, **kwargs)

    def __aenter__(self, *args, **kwargs):
        try:
            return self.__under.__aenter__(*args, **kwargs)
        except AttributeError:
            return super().__aenter__(*args, **kwargs)

    def __aexit__(self, *args, **kwargs):
        try:
            return self.__under.__aexit__(*args, **kwargs)
        except AttributeError:
            return super().__aexit__(*args, **kwargs)

    def __aiter__(self, *args, **kwargs):
        try:
            return self.__under.__aiter__(*args, **kwargs)
        except AttributeError:
            return super().__aiter__(*args, **kwargs)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        return self.__convert(getattr(self.__under, name))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
