import os
import sys
import signal
import logging


def restart():
    if "HIKKA_DO_NOT_RESTART" in os.environ:
        print("Got in a loop, exiting")
        sys.exit(0)

    logging.getLogger().setLevel(logging.CRITICAL)

    print("🔄 Restarting...")

    if "LAVHOST" in os.environ:
        os.system("lavhost restart")
        return

    signal.signal(
        signal.SIGTERM,
        lambda *_: os.execl(
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
        ),
    )

    os.environ["HIKKA_DO_NOT_RESTART"] = "1"

    os.kill(os.getpid(), signal.SIGTERM)
