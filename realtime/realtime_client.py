"""заглушка"""
from PySide6.QtCore import QObject, Signal, QTimer
import random

class FakeRealtimeClient(QObject):
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str, dict)   # chat_id, message dict
    status_changed = Signal(str, str)      # chat_id, new_status

    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self._connected = False
        self._hb = QTimer(self)
        self._hb.setInterval(30000)
        self._hb.timeout.connect(self._heartbeat)

    def connect(self):
        self._connected = True
        self._hb.start()
        QTimer.singleShot(100, self.connected.emit)

    def disconnect(self):
        self._hb.stop()
        if self._connected:
            self._connected = False
            self.disconnected.emit()

    def send_message(self, chat_id: str, text: str):
        # Эмуляция ответа оператора через ~1.5 сек
        QTimer.singleShot(1500, lambda: self._emit_operator_reply(chat_id))

    def _heartbeat(self):
        # здесь можно эмитить периодические события
        pass

    def _emit_operator_reply(self, chat_id: str):
        responses = [
            "Принято, обрабатываем.",
            "Передаю инженеру.",
            "На вашей стороне все ок, проверим у нас."
        ]
        msg = {"sender": "operator", "operator": "Головач Лена", "text": random.choice(responses)}
        self.message_received.emit(chat_id, msg)
        self.status_changed.emit(chat_id, "В работе")
