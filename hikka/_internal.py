import atexit
import functools
import logging
import os
import sys


def get_startup_callback() -> callable:
    return functools.partial(
        os.execl,
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


def restart():
    if "HIKKA_DO_NOT_RESTART" in os.environ:
        print("Got in a loop, exiting")
        sys.exit(0)

    logging.getLogger().setLevel(logging.CRITICAL)

    print("🔄 Restarting...")

    if "LAVHOST" in os.environ:
        os.system("lavhost restart")
        return

    atexit.register(get_startup_callback())

    os.environ["HIKKA_DO_NOT_RESTART"] = "1"

    sys.exit(0)
