"""Entry point. Checks for user and starts main script"""

import getpass
import os
import subprocess
import sys

from ._internal import restart

if (
    getpass.getuser() == "root"
    and "--root" not in " ".join(sys.argv)
    and all(trigger not in os.environ for trigger in {"DOCKER", "GOORM"})
):
    print("🚫" * 15)
    print("You attempted to run Huikka on behalf of root user")
    print("Please, create a new user and restart script")
    print("If this action was intentional, pass --root argument instead")
    print("🚫" * 15)
    print()
    print("Type force_insecure to ignore this warning")
    if input("> ").lower() != "force_insecure":
        sys.exit(1)


def deps():
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


if sys.version_info < (3, 8, 0):
    print("🚫 Error: you must use at least Python version 3.8.0")
elif __package__ != "huikka":  # In case they did python __main__.py
    print("🚫 Error: you cannot run this as a script; you must execute as a package")
else:
    try:
        import huikkatl
    except Exception:
        pass
    else:
        try:
            import huikkatl  # noqa: F811

            if tuple(map(int, huikkatl.__version__.split("."))) < (2, 0, 7):
                raise ImportError
        except ImportError:
            print("🔄 Installing dependencies...")
            deps()
            restart()

    try:
        from . import log

        log.init()

        from . import main
    except ImportError as e:
        print(f"{str(e)}\n🔄 Attempting dependencies installation... Just wait ⏱")
        deps()
        restart()

    if "HIKKA_DO_NOT_RESTART" in os.environ:
        del os.environ["HIKKA_DO_NOT_RESTART"]

    if "HIKKA_DO_NOT_RESTART2" in os.environ:
        del os.environ["HIKKA_DO_NOT_RESTART2"]

    main.huikka.main()  # Execute main function
