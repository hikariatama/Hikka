import asyncio
import atexit
import logging
import os
import random
import signal
import sys


async def fw_protect():
    await asyncio.sleep(random.randint(1000, 3000) / 1000)


def get_startup_callback() -> callable:
    return lambda *_: os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(os.path.abspath(os.path.dirname(os.path.abspath(__file__)))),
        *sys.argv[1:],
    )


def die():
    """Platform-dependent way to kill the current process group"""
    if "DOCKER" in os.environ:
        sys.exit(0)
    else:
        # This one is actually better, because it kills all subprocesses
        # but it can't be used inside the Docker
        os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)


def restart():
    if "HIKKA_DO_NOT_RESTART2" in os.environ:
        print(
            "Got in a loop, exiting\nYou probably need to manually remove existing"
            " packages and then restart Huikka. Run `pip uninstall -y telethon"
            " telethon-mod huikka-tl`, then restart Huikka."
        )
        sys.exit(0)

    logging.getLogger().setLevel(logging.CRITICAL)

    print("🔄 Restarting...")

    if "LAVHOST" in os.environ:
        os.system("lavhost restart")
        return

    if "HIKKA_DO_NOT_RESTART" not in os.environ:
        os.environ["HIKKA_DO_NOT_RESTART"] = "1"
    else:
        os.environ["HIKKA_DO_NOT_RESTART2"] = "1"

    if "DOCKER" in os.environ:
        atexit.register(get_startup_callback())
    else:
        # This one is requried for better way of killing to work properly,
        # since we kill the process group using unix signals
        signal.signal(signal.SIGTERM, get_startup_callback())

    die()


def print_banner(banner: str):
    print("\033[2J\033[3;1f")
    with open(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                banner,
            )
        ),
        "r",
    ) as f:
        print(f.read())
