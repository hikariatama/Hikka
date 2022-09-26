"""Entry point. Checks for user and starts main script"""

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import getpass
import os
import subprocess
import sys

from ._internal import restart

if (
    getpass.getuser() == "root"
    and "--root" not in " ".join(sys.argv)
    and all(trigger not in os.environ for trigger in {"OKTETO", "DOCKER", "GOORM"})
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
                check=False,
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
    except ModuleNotFoundError as e:
        deps(e)
    except ImportError as e:
        deps(e)

    if __name__ == "__main__":
        if "HIKKA_DO_NOT_RESTART" in os.environ:
            del os.environ["HIKKA_DO_NOT_RESTART"]

        main.hikka.main()  # Execute main function
