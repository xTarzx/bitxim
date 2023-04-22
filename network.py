import socket
import struct
import pickle

from enum import Enum, auto
from typing import Dict, Any, Union
from dataclasses import dataclass


class MSG_TYPE(Enum):
    SYSTEM_WAIT = auto()
    SYSTEM_END = auto()
    GAME_DATA = auto()
    PLAYER_ACTION = auto()
    PLAY_MF = auto()


@dataclass
class Message:
    typ: MSG_TYPE
    data: Dict[str, Any] = None


def send_msg(conn: socket.socket, data: bytes):
    data_len = len(data)

    package = struct.pack("!I", data_len)
    package += data

    conn.sendall(package)


def recv_msg(conn: socket.socket):
    data_len = conn.recv(struct.calcsize("!I"))
    data_len = struct.unpack("!I", data_len)[0]

    return recv_all(conn, data_len)


def recv_all(conn: socket.socket, n: int):
    data = bytearray()

    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def send_to(conn: socket.socket, data):
    data = pickle.dumps(data)
    send_msg(conn, data)


def recv_from(conn):
    return pickle.loads(recv_msg(conn))
