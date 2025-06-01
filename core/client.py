import json
import socket
import threading

from PyQt5.QtCore import QObject, pyqtSignal, Qt

from core.game_controller import GameController
from core.network_utils import find_server_by_port
from logger import logger


class Client(QObject):
    gui_cmd = pyqtSignal(str)
    gui_requested = pyqtSignal(int)

    def __init__(self, session_code, nickname, join_window):
        super().__init__()
        self.gui = None
        self.join_window = join_window
        self.nickname = nickname

        self.ctrl = GameController(
            mode="",
            time=0,
            nickname=nickname,
            on_send=self._send_to_srv,
            on_close=self.close
        )

        self.gui_requested.connect(self.join_window.start_game)
        self.ctrl.state_ready = self.gui_cmd.emit
        self.gui_cmd.connect(self._apply_state, Qt.QueuedConnection)

        self.server_ip, self.server_port = find_server_by_port(int(session_code))
        if not self.server_ip:
            return self.join_window.show_error("Ошибка: сервер не найден!")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.server_ip, self.server_port))
            self.join_window.show_status("Подключение установлено...")
        except Exception:
            return self.join_window.show_error("Ошибка подключения к серверу!")

        self.send_message(nickname)
        resp = self.sock.recv(1024).decode("utf-8")
        if resp == "INVALID_NICKNAME":
            return self.join_window.show_error("Никнейм уже занят!")

        self.join_window.show_success("Вы успешно подключились! Ожидайте начала игры.")

        threading.Thread(target=self._recv_loop, daemon=True).start()

    def send_message(self, msg: str):
        self.sock.send(msg.encode("utf-8"))

    def _recv_loop(self):
        while True:
            try:
                raw = self.sock.recv(32768)
                if not raw:
                    self.ctrl.handle_error()
                    break
            except ConnectionResetError:

                self.ctrl.handle_error()
                break

            try:
                data = json.loads(raw.decode("utf-8"))
                logger.info(f"Принята команда {data}")
            except Exception:
                continue

            players = self.ctrl.handle_command(data)
            if players:
                self.gui_requested.emit(players)

    def _send_to_srv(self, raw: bytes):
        self.sock.sendall(raw)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            logger.error("Error on close sock", OSError)

    def _apply_state(self, cmd: str):
        if not self.gui:
            return
        self.gui.apply_state(cmd)
