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

#    Friendly Telegram Userbot
#    by GeekTG Team


class Strings:
    def __init__(self, prefix, strings, babel):
        self._prefix = prefix
        self._strings = strings
        self._babel = babel

    def __getitem__(self, key):
        return self._babel.getkey(self._prefix + key) or self._strings[key]

    def __call__(self, key, message=None):
        if isinstance(message, str):
            lang_code = message
        elif message is None:
            lang_code = None
        else:
            lang_code = getattr(getattr(message, "sender", None), "lang_code", None)
        return (
            self._babel.getkey(f'{self._prefix}.{key}', lang_code)
            or self._strings[key]
        )

    def __iter__(self):
        return self._strings.__iter__()
