# data/dialog_store.py
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .test_data import TEST_USERS

class DialogStore:
    def __init__(self):
        # { user_id: { dialog_id: dialog_dict } }
        self._by_user: Dict[str, Dict[str, dict]] = {}
        self._seed_from_test_users(TEST_USERS)

    @staticmethod
    def _now_iso() -> str:
        return datetime.utcnow().isoformat()

    def _seed_from_test_users(self, users: List[dict]):
        subjects = [
            "Проблема со входом",
            "Вопрос по оплате",
            "Ошибка при оформлении заказа",
            "Настройка уведомлений",
            "Смена номера телефона",
        ]
        for u in users:
            user_id = u["id"]
            self._by_user[user_id] = {}
            # 2-3 тестовых диалога на пользователя
            for i in range(random.randint(2, 3)):
                dlg_id = self._new_id()
                created_at = datetime.utcnow() - timedelta(days=random.randint(0, 15), hours=random.randint(0, 23))
                dialog = {
                    "id": dlg_id,
                    "user_id": user_id,
                    "subject": random.choice(subjects),
                    "status": random.choice(["open", "closed"]),
                    "created_at": created_at.isoformat(),
                    "updated_at": created_at.isoformat(),
                    "operator_name": random.choice(["Петрова Аня", "Сидоров Михаил", "Головач Лена"]),
                    "messages": []
                }
                # Сообщения в диалоге
                base_time = created_at
                msgs = [
                    {"sender": "operator", "text": "Здравствуйте! Чем могу помочь?", "ts": (base_time + timedelta(minutes=1)).isoformat(), "operator_name": dialog["operator_name"]},
                    {"sender": "user", "text": "Добрый день! " + random.choice(["Не могу войти в аккаунт.", "Не проходит оплата.", "Приложение выдает ошибку."]), "ts": (base_time + timedelta(minutes=2)).isoformat()},
                    {"sender": "operator", "text": "Понимаю, уточните детали, пожалуйста.", "ts": (base_time + timedelta(minutes=3)).isoformat(), "operator_name": dialog["operator_name"]},
                ]
                dialog["messages"].extend(msgs)
                dialog["updated_at"] = msgs[-1]["ts"]
                self._by_user[user_id][dlg_id] = dialog

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:8].upper()

    def get_dialogs(self, user_id: str) -> List[dict]:
        lst = list(self._by_user.get(user_id, {}).values())
        lst.sort(key=lambda d: d["updated_at"], reverse=True)
        return lst

    def get_dialog(self, user_id: str, dialog_id: str) -> Optional[dict]:
        return self._by_user.get(user_id, {}).get(dialog_id)

    def create_dialog(self, user_id: str, subject: str, operator_name: Optional[str] = None) -> dict:
        dlg_id = self._new_id()
        dialog = {
            "id": dlg_id,
            "user_id": user_id,
            "subject": subject or "Без темы",
            "status": "open",
            "created_at": self._now_iso(),
            "updated_at": self._now_iso(),
            "operator_name": operator_name or random.choice(["Петрова Аня", "Сидоров Михаил", "Головач Лена"]),
            "messages": [
                {"sender": "operator", "text": "Оператор подключился к чату. Здравствуйте!", "ts": self._now_iso(), "operator_name": operator_name or "Оператор"}
            ]
        }
        self._by_user.setdefault(user_id, {})[dlg_id] = dialog
        return dialog

    def delete_dialog(self, user_id: str, dialog_id: str) -> bool:
        user_map = self._by_user.get(user_id, {})
        if dialog_id in user_map:
            del user_map[dialog_id]
            return True
        return False

    def add_message(self, user_id: str, dialog_id: str, sender: str, text: str, operator_name: Optional[str] = None, ts: Optional[str] = None):
        dlg = self.get_dialog(user_id, dialog_id)
        if not dlg:
            return
        msg = {"sender": sender, "text": text, "ts": ts or self._now_iso()}
        if sender == "operator" and operator_name:
            msg["operator_name"] = operator_name
        dlg["messages"].append(msg)
        dlg["updated_at"] = msg["ts"]

# Глобальный экземпляр
dialog_store = DialogStore()
