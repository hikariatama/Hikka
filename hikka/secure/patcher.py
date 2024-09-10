import functools
import logging
import re
from pathlib import Path

from hikkatl.sessions import SQLiteSession

from ..tl_cache import CustomTelegramClient
from .customtl import ConnectionTcpFull, MTProtoState


def patch(client: CustomTelegramClient, session: SQLiteSession):
    session_id = re.findall(r"\d+", session.filename)[-1]
    client._sender._state = MTProtoState(session.auth_key, client._sender._loggers)
    client._connection = ConnectionTcpFull
    client.connect = functools.partial(
        client.connect,
        unix_socket_path=(
            Path(__file__).parent.parent.parent / f"hikka-{session_id}-proxy.sock"
        ),
    )

    logging.warning("Patched mtprotostate")
