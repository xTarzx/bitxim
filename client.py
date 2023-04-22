import socket
from network import MSG_TYPE, Message, recv_from, send_to
from threading import Thread
from enum import Enum, auto


class ActionType(Enum):
    PLAY = auto()
    PASS = auto()


class State(Enum):
    WAITING = auto()
    END = auto()
    UPDATE_GAME = auto()
    PLAY_MF = auto()


class Client:
    def __init__(self, addr="127.0.0.1", PORT=42069):
        self.addr = addr
        self.PORT = PORT
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.addr, PORT))

        self.data = {}

        self.should_end = False
        self.state = []
        self.recv_thread = Thread(target=self.recv_worker, daemon=True)
        self.recv_thread.start()

    def recv_worker(self):
        while True:
            msg: Message = recv_from(self.conn)

            if msg.typ == MSG_TYPE.SYSTEM_WAIT:
                self.state.append(State.WAITING)

            elif msg.typ == MSG_TYPE.SYSTEM_END:
                self.state.append(State.END)
                break

            elif msg.typ == MSG_TYPE.GAME_DATA:
                self.data.update(msg.data)
                self.state.append(State.UPDATE_GAME)

            elif msg.typ == MSG_TYPE.PLAY_MF:
                self.state.append(State.PLAY_MF)

            else:
                print(f"UNHANDLED MESSAGE {msg.typ} {msg.data}")

    def send(self, msg: Message):
        send_to(self.conn, msg)

    def do_action(self, action: ActionType, data=None):
        if data is None:
            data = {}
        if action == ActionType.PASS:
            action_type = "pass"
        elif action == ActionType.PLAY:
            action_type = "play"

        data.update({"action_type": action_type})
        self.send(Message(MSG_TYPE.PLAYER_ACTION, data=data))
