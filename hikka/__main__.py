"""Entry point. Checks for user and starts main script"""

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

import atexit
import getpass
import os
import subprocess
import sys

if (
    getpass.getuser() == "root"
    and "--root" not in " ".join(sys.argv)
    and "OKTETO" not in os.environ
    and "DOCKER" not in os.environ
):
    print("🚫" * 15)
    print("You attempted to run Hikka on behalf of root user")
    print("Please, create a new user and restart script")
    print("If this action was intentional, pass --root argument instead")
    print("🚫" * 15)
    print()
    print("Type force_insecure to ignore this warning")
    if input("> ").lower() != "force_insecure":
        sys.exit(1)


def deps(error):
    print(f"{str(error)}\n🔄 Attempting dependencies installation... Just wait ⏱")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-q",
            "--disable-pip-version-check",
            "--no-warn-script-location",
            "-r",
            "requirements.txt",
        ],
        check=True,
    )

    restart()


def restart():
    if "HIKKA_DO_NOT_RESTART" in os.environ:
        print("Got in a loop, exiting")
        sys.exit(0)

    print("🔄 Restarting...")

    atexit.register(
        lambda: os.execl(
            sys.executable,
            sys.executable,
            "-m",
            os.path.relpath(
                os.path.abspath(
                    os.path.dirname(
                        os.path.abspath(__file__),
                    ),
                ),
            ),
            *(sys.argv[1:]),
        )
    )

    os.environ["HIKKA_DO_NOT_RESTART"] = "1"

    sys.exit(0)


if sys.version_info < (3, 8, 0):
    print("🚫 Error: you must use at least Python version 3.8.0")
elif __package__ != "hikka":  # In case they did python __main__.py
    print("🚫 Error: you cannot run this as a script; you must execute as a package")
else:
    try:
        # If telethon is not installed, just skip to a part of main startup
        # then main.py will through an error and re-install all deps
        import telethon
    except Exception:
        pass
    else:
        try:
            # This is used as verification markers to ensure that supported
            # version is installed
            from telethon.tl.types import MessageEntityCustomEmoji  # skipcq
            from telethon.extensions.html import CUSTOM_EMOJIS  # skipcq
            import telethon

            if tuple(map(int, telethon.__version__.split("."))) < (1, 24, 10):
                raise ImportError
        except ImportError:
            print("🔄 Reinstalling Hikka-TL...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "uninstall",
                    "-y",
                    "telethon",
                    "telethon-mod",
                ],
                check=True,
            )

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--force-reinstall",
                    "-q",
                    "--disable-pip-version-check",
                    "--no-warn-script-location",
                    "hikka-tl",
                ],
                check=True,
            )

            restart()

    try:
        from . import log

        log.init()

        from . import main
    except ModuleNotFoundError as e:  # pragma: no cover
        deps(e)

    if __name__ == "__main__":
        if "HIKKA_DO_NOT_RESTART" in os.environ:
            del os.environ["HIKKA_DO_NOT_RESTART"]

        main.hikka.main()  # Execute main function
