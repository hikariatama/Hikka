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

# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import os
import string


def api_config():
    """Request API config from user and set"""
    from . import main

    with open(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "banner.txt")
        ),
        "r",
    ) as banner:
        print(banner.read().replace("\\033", "\033"))

    print("\033[0;96mWelcome to Hikka Userbot!\033[0m")

    while api_hash := input("\033[0;96mEnter API hash: \033[0m"):
        if len(api_hash) == 32 and all(
            symbol in string.hexdigits for symbol in api_hash
        ):
            break

        print("\033[0;91mInvalid hash\033[0m")

    if not api_hash:
        print("\033[0;91mCancelled\033[0m")
        exit(0)

    while api_id := input("\033[0;96mEnter API ID: \033[0m"):
        if api_id.isdigit():
            break

        print("\033[0;91mInvalid ID\033[0m")

    if not api_id:
        print("\033[0;91mCancelled\033[0m")
        exit(0)

    (main.BASE_PATH / "api_token.txt").write_text(api_id + "\n" + api_hash)
    print("\033[0;92mAPI config saved\033[0m")
