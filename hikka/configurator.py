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

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import locale
import os
import string
import sys
import typing

from dialog import Dialog, ExecutableNotFound

from . import utils


def _safe_input(*args, **kwargs):
    """Try to invoke input(*), print an error message if an EOFError or OSError occurs)
    """
    try:
        return input(*args, **kwargs)
    except (EOFError, OSError):
        raise
    except KeyboardInterrupt:
        print()
        return None


class TDialog:
    """Reimplementation of dialog.Dialog without external dependencies"""

    def inputbox(self, query: str) -> typing.Tuple[bool, str]:
        """Get a text input of the query"""
        print(query)
        print()
        inp = _safe_input("Please enter your response, or type nothing to cancel: ")
        return (False, "Cancelled") if not inp else (True, inp)

    def msgbox(self, msg: str) -> bool:
        """Print some info"""
        print(msg)
        return True


TITLE = ""

if sys.stdout.isatty():
    try:
        DIALOG = Dialog(dialog="dialog", autowidgetsize=True)
        locale.setlocale(locale.LC_ALL, "")
    except (ExecutableNotFound, locale.Error):
        # Fall back to a terminal based configurator.
        DIALOG = TDialog()
else:
    DIALOG = TDialog()


def api_config(data_root: str):
    """Request API config from user and set"""
    code, hash_value = DIALOG.inputbox("Enter your API Hash")
    if not code:
        return

    if len(hash_value) != 32 or any(it not in string.hexdigits for it in hash_value):
        DIALOG.msgbox("Invalid hash")
        return

    code, id_value = DIALOG.inputbox("Enter your API ID")

    if not id_value or any(it not in string.digits for it in id_value):
        DIALOG.msgbox("Invalid ID")
        return

    with open(
        os.path.join(
            data_root or os.path.dirname(utils.get_base_dir()), "api_token.txt"
        ),
        "w",
    ) as file:
        file.write(id_value + "\n" + hash_value)

    DIALOG.msgbox("API Token and ID set.")
