import asyncio
import logging
import struct
import time

from hikkatl.errors import InvalidBufferError, SecurityError
from hikkatl.extensions import BinaryReader
from hikkatl.network.connection import ConnectionTcpFull as ConnectionTcpFullOrig
from hikkatl.network.mtprotostate import MTProtoState as MTProtoStateOrig
from hikkatl.tl.core import TLMessage
from hikkatl.tl.types import BadMsgNotification, BadServerSalt

MSG_TOO_NEW_DELTA = 30
MSG_TOO_OLD_DELTA = 300


class MTProtoState(MTProtoStateOrig):
    def encrypt_message_data(self, data):
        logging.debug("Skipping encryption...")
        return data

    def decrypt_message_data(self, body):
        now = time.time() + self.time_offset

        if len(body) < 8:
            raise InvalidBufferError(body)

        logging.debug("Got raw data: %s", body)

        reader = BinaryReader(body)
        remote_msg_id = reader.read_long()

        if remote_msg_id % 2 != 1:
            raise SecurityError("Server sent an even msg_id")

        if (
            remote_msg_id <= self._highest_remote_id
            and remote_msg_id in self._recent_remote_ids
        ):
            self._log.warning(
                "Server resent the older message %d, ignoring", remote_msg_id
            )
            self._count_ignored()
            return None

        remote_sequence = reader.read_int()
        reader.read_int()
        obj = reader.tgread_object()
        if obj.CONSTRUCTOR_ID not in (
            BadServerSalt.CONSTRUCTOR_ID,
            BadMsgNotification.CONSTRUCTOR_ID,
        ):
            remote_msg_time = remote_msg_id >> 32
            time_delta = now - remote_msg_time

            if time_delta > MSG_TOO_OLD_DELTA:
                self._log.warning(
                    "Server sent a very old message with ID %d, ignoring", remote_msg_id
                )
                self._count_ignored()
                return None

            if -time_delta > MSG_TOO_NEW_DELTA:
                self._log.warning(
                    "Server sent a very new message with ID %d, ignoring", remote_msg_id
                )
                self._count_ignored()
                return None

        self._recent_remote_ids.append(remote_msg_id)
        self._highest_remote_id = remote_msg_id
        self._ignore_count = 0

        return TLMessage(remote_msg_id, remote_sequence, obj)


class ConnectionTcpFull(ConnectionTcpFullOrig):
    def set_unix_socket(self, unix_socket_path):
        self._unix_socket_path = unix_socket_path

    async def _connect(self, timeout=None, ssl=None):
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_unix_connection(path=self._unix_socket_path, ssl=None),
            timeout=timeout,
        )

        self._codec = self.packet_codec(self)
        self._init_conn()
        await self._writer.drain()
