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

# █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
# █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█
#
#              © Copyright 2022
#
#          https://t.me/hikariatama
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import sys
import getpass
import os
import subprocess
import atexit

if (
    getpass.getuser() == "root"
    and "--root" not in " ".join(sys.argv)
    and "OKTETO" not in os.environ
):
    print("🚫" * 30)
    print("NEVER EVER RUN USERBOT FROM ROOT")
    print("THIS IS THE THREAD FOR NOT ONLY YOUR DATA, ")
    print("BUT ALSO FOR YOUR DEVICE ITSELF!")
    print("🚫" * 30)
    print()
    print("TYPE force_insecure TO IGNORE THIS WARNING")
    print("TYPE ANYTHING ELSE TO EXIT:")
    if input("> ").lower() != "force_insecure":
        sys.exit(1)


def deps(e):
    print(
        "🚫 Error: you have not installed all dependencies correctly.\n"
        f"{str(e)}\n"
        "🔄 Attempting dependencies installation... Just wait ⏱"
    )

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
        ]
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
    print("🚫 Error: you cannot run this as a script; you must execute as a package")  # fmt: skip
else:
    try:
        import telethon  # noqa: F401
    except Exception:
        pass
    else:
        try:
            from telethon.tl.functions.messages import SendReactionRequest  # noqa: F401
        except ImportError:
            print("⚠️ Warning: Default telethon is used as main one. This can cause errors and enables DAR. Attempting to reinstall telethon-mod...")  # fmt: skip
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "uninstall",
                    "-y",
                    "telethon",
                ]
            )

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-U",
                    "-q",
                    "--disable-pip-version-check",
                    "--no-warn-script-location",
                    "telethon-mod",
                ]
            )

            restart()

    try:
        from . import log

        log.init()
    except ModuleNotFoundError as e:  # pragma: no cover
        deps(e)
        sys.exit(1)

    try:
        from . import main
    except ModuleNotFoundError as e:  # pragma: no cover
        deps(e)
        sys.exit(1)

    if __name__ == "__main__":
        if "HIKKA_DO_NOT_RESTART" in os.environ:
            del os.environ["HIKKA_DO_NOT_RESTART"]

        main.hikka.main()  # Execute main function
