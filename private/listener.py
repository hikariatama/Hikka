import asyncio
import atexit
import contextlib
import copy
import dataclasses
import datetime
import functools
import io
import json
import logging
import os
import re
import signal
import struct
import sys
import time
from hashlib import sha256
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Union
from zlib import crc32

from hikkatl.crypto import AES, AuthKey
from hikkatl.errors import (
    AuthKeyNotFound,
    BadMessageError,
    InvalidBufferError,
    InvalidChecksumError,
    SecurityError,
    TypeNotFoundError,
)
from hikkatl.extensions.binaryreader import BinaryReader
from hikkatl.extensions.messagepacker import MessagePacker
from hikkatl.network.connection import ConnectionTcpFull
from hikkatl.network.mtprotosender import MTProtoSender
from hikkatl.network.mtprotostate import MTProtoState
from hikkatl.network.requeststate import RequestState
from hikkatl.sessions import SQLiteSession
from hikkatl.tl import TLRequest
from hikkatl.tl.core import GzipPacked, MessageContainer, TLMessage
from hikkatl.tl.functions import (
    InitConnectionRequest,
    InvokeAfterMsgRequest,
    InvokeAfterMsgsRequest,
    InvokeWithLayerRequest,
    InvokeWithMessagesRangeRequest,
    InvokeWithoutUpdatesRequest,
    InvokeWithTakeoutRequest,
    PingRequest,
)
from hikkatl.tl.functions.account import DeleteAccountRequest, UpdateProfileRequest
from hikkatl.tl.functions.auth import (
    BindTempAuthKeyRequest,
    CancelCodeRequest,
    CheckRecoveryPasswordRequest,
    ExportAuthorizationRequest,
    ExportLoginTokenRequest,
    ImportAuthorizationRequest,
    LogOutRequest,
    RecoverPasswordRequest,
    RequestPasswordRecoveryRequest,
    ResetAuthorizationsRequest,
    ResetLoginEmailRequest,
    SendCodeRequest,
)
from hikkatl.tl.functions.help import GetConfigRequest
from hikkatl.tl.functions.messages import (
    ForwardMessagesRequest,
    GetHistoryRequest,
    SearchRequest,
)
from hikkatl.tl.types import (
    InputPeerUser,
    Message,
    MsgsAck,
    PeerUser,
    UpdateNewMessage,
    Updates,
    UpdateShortMessage,
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="%",
    )
)

rotating_handler = RotatingFileHandler(
    filename="hikka.log",
    mode="a",
    maxBytes=10 * 1024 * 1024,
    backupCount=1,
    encoding="utf-8",
    delay=0,
)
rotating_handler.setLevel(logging.DEBUG)
rotating_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="%",
    )
)

logging.getLogger().handlers[0].setLevel(logging.CRITICAL)
logging.getLogger().addHandler(handler)
logging.getLogger().addHandler(rotating_handler)


class _OpaqueRequest(TLRequest):
    def __init__(self, data: bytes):
        self.data = data

    def _bytes(self):
        return self.data


class CustomMTProtoState(MTProtoState):
    def write_data_as_message(
        self,
        buffer,
        data,
        content_related,
        *,
        after_id=None,
        msg_id=None,
    ):
        msg_id = msg_id or self._get_new_msg_id()
        seq_no = self._get_seq_no(content_related)
        if after_id is None:
            body = GzipPacked.gzip_if_smaller(content_related, data)
        else:
            body = GzipPacked.gzip_if_smaller(
                content_related,
                bytes(InvokeAfterMsgRequest(after_id, _OpaqueRequest(data))),
            )

        buffer.write(struct.pack("<qii", msg_id, seq_no, len(body)))
        buffer.write(body)
        return msg_id


class CustomMessagePacker(MessagePacker):
    async def get(self):
        if not self._deque:
            self._ready.clear()
            await self._ready.wait()

        buffer = io.BytesIO()
        batch = []
        size = 0

        while self._deque and len(batch) <= MessageContainer.MAXIMUM_LENGTH:
            state = self._deque.popleft()
            size += len(state.data) + TLMessage.SIZE_OVERHEAD

            if size <= MessageContainer.MAXIMUM_SIZE:
                state.msg_id = self._state.write_data_as_message(
                    buffer,
                    state.data,
                    isinstance(state.request, TLRequest),
                    after_id=state.after.msg_id if state.after else None,
                    msg_id=state.msg_id,
                )
                batch.append(state)
                self._log.debug(
                    "Assigned msg_id = %d to %s (%x)",
                    state.msg_id,
                    state.request.__class__.__name__,
                    id(state.request),
                )
                continue

            if batch:
                self._deque.appendleft(state)
                break

            self._log.warning(
                "Message payload for %s is too long (%d) and cannot be sent",
                state.request.__class__.__name__,
                len(state.data),
            )
            state.future.set_exception(ValueError("Request payload is too big"))

            size = 0
            continue

        if not batch:
            return None, None

        if len(batch) > 1:
            data = (
                struct.pack("<Ii", MessageContainer.CONSTRUCTOR_ID, len(batch))
                + buffer.getvalue()
            )
            buffer = io.BytesIO()
            container_id = self._state.write_data_as_message(
                buffer, data, content_related=False
            )
            for s in batch:
                s.container_id = container_id

        data = buffer.getvalue()
        return batch, data


class ClientFullPacketCodec:
    tag = None

    def encode_packet(self, data):
        length = len(data) + 12
        data = struct.pack("<ii", length, 0) + data
        crc = struct.pack("<I", crc32(data))
        return data + crc

    async def read_packet(self, reader):
        packet_len_seq = await reader.readexactly(8)
        packet_len, seq = struct.unpack("<ii", packet_len_seq)
        if packet_len < 0 and seq < 0:
            body = await reader.readexactly(4)
            raise InvalidBufferError(body)

        body = await reader.readexactly(packet_len - 8)
        checksum = struct.unpack("<I", body[-4:])[0]
        body = body[:-4]

        valid_checksum = crc32(packet_len_seq + body)
        if checksum != valid_checksum:
            raise InvalidChecksumError(checksum, valid_checksum)

        return body


def get_config_key(key: str) -> Union[str, bool]:
    """
    Parse and return key from config
    :param key: Key name in config
    :return: Value of config key or `False`, if it doesn't exist
    """
    try:
        return json.loads(Path("../config.json").read_text()).get(key, False)
    except FileNotFoundError:
        return False


start_ts = time.perf_counter()


class CustomMTProtoSender(MTProtoSender):
    def __init__(
        self,
        auth_key,
        *,
        loggers,
        retries=5,
        delay=1,
        auto_reconnect=True,
        connect_timeout=None,
        auth_key_callback=None,
        updates_queue=None,
        auto_reconnect_callback=None,
    ):
        super().__init__(
            auth_key,
            loggers=loggers,
            retries=retries,
            delay=delay,
            auto_reconnect=auto_reconnect,
            connect_timeout=connect_timeout,
            auth_key_callback=auth_key_callback,
            updates_queue=updates_queue,
            auto_reconnect_callback=auto_reconnect_callback,
        )
        self._state = CustomMTProtoState(self.auth_key, loggers=self._loggers)
        self._send_queue = CustomMessagePacker(self._state, loggers=self._loggers)

    def external_append(self, state):
        self._send_queue.append(state)

    def external_extend(self, states):
        self._send_queue.extend(states)

    async def _send_loop(self):
        while self._user_connected and not self._reconnecting:
            if self._pending_ack:
                ack = RequestState(MsgsAck(list(self._pending_ack)))
                self._send_queue.append(ack)
                self._last_acks.append(ack)
                self._pending_ack.clear()

            self._log.debug("Waiting for messages to send...")

            batch, data = await self._send_queue.get()

            if not data:
                continue

            logging.debug("Sending data %s", data)

            self._log.debug(
                "Encrypting %d message(s) in %d bytes for sending",
                len(batch),
                len(data),
            )

            data = self._state.encrypt_message_data(data)

            for state in batch:
                if not isinstance(state, list):
                    if isinstance(state.request, TLRequest):
                        self._pending_state[state.msg_id] = state
                else:
                    for s in state:
                        if isinstance(s.request, TLRequest):
                            self._pending_state[s.msg_id] = s

            try:
                await self._connection.send(data)
            except IOError as e:
                self._log.info("Connection closed while sending data")
                self._start_reconnect(e)
                return

            self._log.debug("Encrypted messages put in a queue to be sent")

    def partial_decrypt(self, body):
        if len(body) < 8:
            raise InvalidBufferError(body)

        key_id = struct.unpack("<Q", body[:8])[0]
        if key_id != self._state.auth_key.key_id:
            raise SecurityError("Server replied with an invalid auth key")

        msg_key = body[8:24]
        aes_key, aes_iv = self._state._calc_key(
            self._state.auth_key.key, msg_key, False
        )
        body = AES.decrypt_ige(body[24:], aes_key, aes_iv)

        our_key = sha256(self._state.auth_key.key[96 : 96 + 32] + body)
        if msg_key != our_key.digest()[8:24]:
            raise SecurityError("Received msg_key doesn't match with expected one")

        return body[16:]

    async def _handle_recv(self, body: bytes):
        try:
            message = self._state.decrypt_message_data(body)
            if message is None:
                return False
        except TypeNotFoundError as e:
            self._log.info(
                "Type %08x not found, remaining data %r",
                e.invalid_constructor_id,
                e.remaining,
            )
            return False
        except SecurityError as e:
            self._log.warning(
                "Security error while unpacking a received message: %s", e
            )
            return False
        except BufferError as e:
            if isinstance(e, InvalidBufferError) and e.code == 404:
                self._log.info(
                    "Server does not know about the current auth key; the session may"
                    " need to be recreated"
                )
                await self._disconnect(error=AuthKeyNotFound())
            else:
                self._log.warning("Invalid buffer %s", e)
                self._start_reconnect(e)
            return -1
        except Exception as e:
            self._log.exception("Unhandled error while decrypting data")
            self._start_reconnect(e)
            return -1

        try:
            await self._process_message(message)
        except Exception:
            self._log.exception("Unhandled error while processing msgs")

        logging.debug("Got message from Telegram %s", message)

        try:
            msg = self.partial_decrypt(body)
            to_censor = ""
            if isinstance(message, TLMessage):
                if isinstance(message.obj, Updates) and (
                    malicious := next(
                        (
                            update
                            for update in message.obj.updates
                            if isinstance(update, UpdateNewMessage)
                            and isinstance(update.message, Message)
                            and isinstance(update.message.peer_id, PeerUser)
                            and update.message.peer_id.user_id == 777000
                        ),
                        None,
                    )
                ):
                    to_censor = malicious.message.message
                elif (
                    isinstance(message.obj, UpdateShortMessage)
                    and message.obj.user_id == 777000
                ):
                    to_censor = message.obj.message
                elif isinstance(message.obj, MessageContainer) and (
                    any(
                        (
                            isinstance(bigmsg.obj, Updates)
                            and (
                                malicious := next(
                                    (
                                        update
                                        for update in bigmsg.obj.updates
                                        if isinstance(update, UpdateNewMessage)
                                        and isinstance(update.message, Message)
                                        and isinstance(update.message.peer_id, PeerUser)
                                        and update.message.peer_id.user_id == 777000
                                    ),
                                    None,
                                )
                            )
                            for bigmsg in message.obj.messages
                            if isinstance(bigmsg, TLMessage)
                        )
                    )
                ):
                    to_censor = malicious.message.message
                elif isinstance(message.obj, MessageContainer) and (
                    malicious := next(
                        (
                            bigmsg
                            for bigmsg in message.obj.messages
                            if isinstance(bigmsg, TLMessage)
                            and isinstance(bigmsg.obj, UpdateShortMessage)
                            and bigmsg.obj.user_id == 777000
                        ),
                        None,
                    )
                ):
                    to_censor = malicious.message.message

            if to_censor:
                to_censor = to_censor.encode()

                original_msg = ""
                if msg[16:].startswith(b"\xa1\xcfr0"):
                    with BinaryReader(msg[16:]) as reader:
                        obj = reader.tgread_object()
                        assert isinstance(obj, GzipPacked)
                        original_msg = copy.copy(msg)
                        msg = obj.data

                logging.info("Censoring message %s in %s", to_censor, msg)

                msg = msg.replace(to_censor, (b"*" * len(to_censor)))
                if original_msg:
                    msg = original_msg[:16] + msg

            if hasattr(self, "_socket"):
                logging.debug(
                    "Got data from socket, forwarding, %s",
                    ClientFullPacketCodec.encode_packet(None, msg),
                )
                self._socket.write(ClientFullPacketCodec.encode_packet(None, msg))
                await self._socket.drain()
            else:
                logging.debug("Got data with no socket")
        except Exception:
            logging.exception("Unhandled error while processing msgs")

        return True

    def set_socket(self, socket: asyncio.StreamWriter):
        self._socket = socket

    async def _recv_loop(self):
        while self._user_connected and not self._reconnecting:
            self._log.debug("Receiving items from the network...")
            try:
                body = await self._connection.recv()
            except IOError as e:
                self._log.info("Connection closed while receiving data")
                self._start_reconnect(e)
                return
            except InvalidBufferError as e:
                if e.code == 429:
                    self._log.warning(
                        "Server indicated flood error at transport level: %s", e
                    )
                    await self._disconnect(error=e)
                else:
                    self._log.exception("Server sent invalid buffer")
                    self._start_reconnect(e)
                return
            except Exception as e:
                self._log.exception("Unhandled error while receiving data")
                self._start_reconnect(e)
                return

            res = await self._handle_recv(body)
            if res is False:
                continue
            elif res == -1:
                return

    async def _handle_bad_notification(self, message):
        bad_msg = message.obj
        states = self._pop_states(bad_msg.bad_msg_id)

        self._log.debug("Handling bad msg %s", bad_msg)
        if bad_msg.error_code in (16, 17):
            to = self._state.update_time_offset(correct_msg_id=message.msg_id)
            self._log.info("System clock is wrong, set time offset to %ds", to)
        elif bad_msg.error_code == 32:
            self._state._sequence += 1
        elif bad_msg.error_code == 33:
            self._state._sequence -= 1
        else:
            for state in states:
                state.future.set_exception(
                    BadMessageError(state.request, bad_msg.error_code)
                )
            return

        self._send_queue.extend(states)
        self._log.debug("%d messages will be resent due to bad msg", len(states))


class SessionStorage:
    def __init__(self):
        self._sessions: List[SQLiteSession] = []
        self._safe_sessions: List[SQLiteSession] = []
        self._clients: Dict[int, MTProtoSender] = {}

    async def pop_client(self, client_id: int):
        await self._clients[client_id].disconnect()
        self._clients.pop(client_id)

    @property
    def client_ids(self) -> List[int]:
        return list(self._clients.keys())

    @property
    def clients(self) -> Dict[int, MTProtoSender]:
        return self._clients

    @property
    def sessions(self) -> List[SQLiteSession]:
        return self._safe_sessions

    def read_sessions(self):
        logging.debug("Reading sessions...")
        session_files = list(
            filter(
                lambda f: f.startswith("hikka-") and f.endswith(".session"),
                os.listdir("."),
            )
        )

        for session in session_files:
            Path("safe-" + session).write_bytes(Path(session).read_bytes())

        self._sessions = [SQLiteSession(session) for session in session_files]

        self._safe_sessions = [
            SQLiteSession("safe-" + session) for session in session_files
        ]

        for session in self._safe_sessions:
            logging.debug("Processing session %s...", session.filename)
            session.set_dc(0, "0.0.0.0", 11111)
            session.auth_key = AuthKey(
                data=(
                    "His name is Nikolai Petrovich Kirsanov. He owns a fine estate,"
                    " located twelve miles or so from the carriage inn, with two"
                    " hundred serfs, or, as he describes it, since negotiating the"
                    ' boundaries with his peasants and establishing a "farm," an estate'
                    " with"
                ).encode()
                + b"\x00\x00\x00"
            )
            session.save()
            session.close()

        def rename(filename: str) -> str:
            session_id = re.findall(r"\d+", filename)[-1]
            return f"hikka-{session_id}.session"

        for session in self._safe_sessions:
            os.rename(
                os.path.abspath(session.filename),
                os.path.abspath(os.path.join("../", rename(session.filename))),
            )

    async def init_clients(self):
        for session in self._sessions:

            class _Loggers(dict):
                def __missing__(self, key):
                    if key.startswith("telethon."):
                        key = key.split(".", maxsplit=1)[1]

                    return logging.getLogger("hikkatl").getChild(key)

            def _auth_key_callback(auth_key):
                self.session.auth_key = auth_key
                self.session.save()

            _updates_queue = asyncio.Queue()

            client = CustomMTProtoSender(
                session.auth_key,
                loggers=_Loggers(),
                retries=5,
                delay=1,
                auto_reconnect=True,
                connect_timeout=10,
                auth_key_callback=_auth_key_callback,
                updates_queue=_updates_queue,
                auto_reconnect_callback=None,
            )
            await client.connect(
                ConnectionTcpFull(
                    session.server_address,
                    session.port,
                    session.dc_id,
                    loggers=_Loggers(),
                )
            )
            client.id = int(re.findall(r"\d+", session.filename)[-1])
            logging.debug("Client %s connected", client.id)
            self._clients[client.id] = client


@dataclasses.dataclass
class Socket:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    client_id: int


class TCP:
    def __init__(self, session_storage: SessionStorage):
        self._sockets = {}
        self._socket_files = []
        self._session_storage = session_storage
        self.gc(init=True)
        for client_id in self._session_storage.client_ids:
            filename = os.path.abspath(
                os.path.join("../", f"hikka-{client_id}-proxy.sock")
            )
            asyncio.ensure_future(
                asyncio.start_unix_server(
                    functools.partial(
                        self._process_conn,
                        client_id=client_id,
                        filename=filename,
                    ),
                    filename,
                )
            )

    def _process_conn(self, reader, writer, client_id, filename):
        self._session_storage.clients[client_id].set_socket(writer)
        self._socket_files.append(filename)
        logging.info("Socket %s connected", filename)
        socket = Socket(reader, writer, client_id)
        self._sockets[client_id] = socket
        asyncio.ensure_future(read_loop(socket))

    @staticmethod
    async def recv(sock: Socket):
        return await ClientFullPacketCodec.read_packet(None, sock.reader)

    @staticmethod
    async def send(sock: Socket, data: bytes):
        sock.writer.write(ClientFullPacketCodec.encode_packet(None, data))
        await sock.writer.drain()

    def _find_real_request(self, request: TLRequest) -> TLRequest:
        if isinstance(
            request,
            (
                InvokeWithLayerRequest,
                InvokeAfterMsgRequest,
                InvokeAfterMsgsRequest,
                InvokeWithMessagesRangeRequest,
                InvokeWithTakeoutRequest,
                InvokeWithoutUpdatesRequest,
            ),
        ):
            return self._find_real_request(request.query)

        return request

    def _malicious(self, request: TLRequest) -> bool:
        request = self._find_real_request(request)
        if (
            isinstance(
                request,
                (
                    DeleteAccountRequest,
                    BindTempAuthKeyRequest,
                    CancelCodeRequest,
                    CheckRecoveryPasswordRequest,
                    ExportAuthorizationRequest,
                    ExportLoginTokenRequest,
                    ImportAuthorizationRequest,
                    LogOutRequest,
                    RecoverPasswordRequest,
                    RequestPasswordRecoveryRequest,
                    ResetAuthorizationsRequest,
                    ResetLoginEmailRequest,
                    SendCodeRequest,
                ),
            )
            or (
                isinstance(request, UpdateProfileRequest)
                and "savedmessages"
                in (request.first_name + request.last_name).replace(" ", "").lower()
            )
            or (
                isinstance(request, GetHistoryRequest)
                and isinstance(request.peer, InputPeerUser)
                and request.peer.user_id == 777000
            )
            or (
                isinstance(request, ForwardMessagesRequest)
                and isinstance(request.from_peer, InputPeerUser)
                and request.from_peer.user_id == 777000
            )
            or (
                isinstance(request, SearchRequest)
                and isinstance(request.peer, InputPeerUser)
                and request.peer.user_id == 777000
            )
        ):
            return True

    async def read(self, conn: Socket):
        data = await self.recv(conn)
        logging.debug("Got data from client %s", data)
        if data:
            msg_id = struct.unpack("<q", data[:8])[0]
            with BinaryReader(data[16:]) as reader:
                tgobject = reader.tgread_object()

            logging.debug("Got object %s", tgobject)

            if isinstance(tgobject, MsgsAck):
                return

            while isinstance(tgobject, GzipPacked):
                with BinaryReader(tgobject.data) as reader:
                    tgobject = reader.tgread_object()
                    logging.debug("Modified object %s", tgobject)

            if isinstance(tgobject, InvokeWithLayerRequest) and isinstance(
                tgobject.query, InitConnectionRequest
            ):
                tgobject = GetConfigRequest()

            if isinstance(tgobject, MessageContainer):
                states = []
                for message in tgobject.messages:
                    state = RequestState(message.obj)
                    if self._malicious(message.obj):
                        logging.critical(
                            "Suspicious request detected, substituting with ping"
                        )
                        state = RequestState(PingRequest(ping_id=123456789))

                    state.msg_id = message.msg_id
                    states.append(state)

                self._session_storage.clients[conn.client_id].external_extend(states)
            else:
                state = RequestState(tgobject)

                if self._malicious(tgobject):
                    logging.critical(
                        "Suspicious request detected, substituting with ping"
                    )
                    state = RequestState(PingRequest(ping_id=123456789))

                state.msg_id = msg_id

                self._session_storage.clients[conn.client_id].external_append(state)

    def gc(self, init: bool, pop_client: Optional[int] = None):
        for client_id in (
            [pop_client] if pop_client else self._session_storage.client_ids
        ):
            with contextlib.suppress(Exception):
                self._sockets[client_id].close()

            with contextlib.suppress(Exception):
                os.remove(
                    os.path.abspath(
                        os.path.join("../", f"hikka-{client_id}-proxy.sock")
                    )
                )

            if not init:
                with contextlib.suppress(Exception):
                    os.remove(
                        os.path.abspath(
                            os.path.join("../", f"hikka-{client_id}.session")
                        )
                    )

            if not init:
                with contextlib.suppress(Exception):
                    os.remove(
                        os.path.abspath(
                            os.path.join("../", f"hikka-{client_id}.session-journal")
                        )
                    )


tcp, session_storage, shell = None, None, None


async def read_loop(sock: Socket):
    global tcp, session_storage, shell
    while True:
        try:
            await tcp.read(sock)
        except asyncio.IncompleteReadError:
            logging.info("Client disconnected, restarting...")
            await session_storage.pop_client(sock.client_id)
            if shell:
                shell.kill()
                logging.info("Waiting for sandbox to exit...")
                await shell.wait()
                logging.info("Sandbox exited")

            exit(1)
        except Exception as e:
            logging.exception(e)


async def main():
    global tcp, session_storage, shell
    for session in os.listdir("../"):
        if session.startswith("hikka-") and session.endswith(".session"):
            session = os.path.abspath(os.path.join("../", session))
            session = SQLiteSession(session)
            if not session.auth_key.key.startswith(
                b"His name is Nikolai Petrovich Kirsanov"
            ):
                session.save()
                session.close()
                os.rename(
                    os.path.abspath(os.path.join("../", session.filename)),
                    os.path.abspath(os.path.join("./", session.filename)),
                )
            else:
                session.close()
                os.remove(os.path.abspath(os.path.join("../", session.filename)))

    session_storage = SessionStorage()
    session_storage.read_sessions()
    await session_storage.init_clients()
    tcp = TCP(session_storage)
    logging.info("Startup delay...")
    await asyncio.sleep(3)
    logging.info("Starting client...")
    shell = await asyncio.create_subprocess_shell(
        "cd ../ && ./_start_sandbox.sh",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
    )
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bye")
        if shell:
            shell.kill()

        if tcp:
            tcp.gc(init=False)

        exit(0)
