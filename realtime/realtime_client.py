"""Заглушка RT клиента без тестовых автоответов"""
from PySide6.QtCore import QObject, Signal, QTimer
import random

class FakeRealtimeClient(QObject):
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str, dict)   # chat_id, message dict
    status_changed = Signal(str, str)      # chat_id, new_status
    connection_error = Signal(str)         # error message

    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self._connected = False
        self._connection_attempts = 0
        self._max_attempts = 5

        # Таймер для попыток переподключения
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)

        # Heartbeat таймер
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(30000)  # 30 секунд
        self._heartbeat_timer.timeout.connect(self._heartbeat)

    def connect(self):
        """Попытка подключения"""
        self._connection_attempts += 1

        # Симулируем возможную неудачу подключения
        if self._connection_attempts <= 2:  # первые 2 попытки могут провалиться
            if random.random() < 0.3:  # 30% шанс неудачи
                self.connection_error.emit(f"Попытка {self._connection_attempts}: Не удалось подключиться к серверу")
                self._schedule_reconnect()
                return

        self._connected = True
        self._connection_attempts = 0  # сбрасываем счетчик при успешном подключении
        self._heartbeat_timer.start()
        QTimer.singleShot(100, self.connected.emit)

    def disconnect(self):
        """Отключение"""
        self._heartbeat_timer.stop()
        self._reconnect_timer.stop()
        if self._connected:
            self._connected = False
            self.disconnected.emit()

    def send_message(self, chat_id: str, text: str):
        """Отправка сообщения (без автоответа)"""
        if not self._connected:
            self.connection_error.emit("Нет подключения к серверу")
            return

        # Больше не генерируем автоматические ответы операторов
        # Сообщение просто отправлено
        pass

    def is_connected(self):
        """Проверка состояния подключения"""
        return self._connected

    def _schedule_reconnect(self):
        """Планирование переподключения"""
        if self._connection_attempts < self._max_attempts:
            delay = min(1000 * (2 ** self._connection_attempts), 30000)  # экспоненциальная задержка, макс 30 сек
            self._reconnect_timer.start(delay)
        else:
            self.connection_error.emit("Достигнуто максимальное количество попыток подключения")

    def _attempt_reconnect(self):
        """Попытка переподключения"""
        if not self._connected:
            self.connect()

    def _heartbeat(self):
        """Проверка соединения"""
        # Симулируем возможную потерю соединения
        if random.random() < 0.05:  # 5% шанс потери соединения
            self._connected = False
            self._heartbeat_timer.stop()
            self.disconnected.emit()
            self.connection_error.emit("Потеряно соединение с сервером")
            self._schedule_reconnect()
