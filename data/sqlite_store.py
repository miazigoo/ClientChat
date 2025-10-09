import os
import sqlite3
import random
from datetime import datetime
from .test_data import TEST_CHATS
from os import environ

OPERATORS = ["Петрова Аня", "Сидоров Михаил", "Головач Лена"]

def _now_dt_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def _now_time_str():
    return datetime.now().strftime("%H:%M")

def _now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class SQLiteRepo:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "support_chat.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.ensure_schema()
        self.seed_if_empty()

    def ensure_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            text TEXT,
            time TEXT,               -- "hh:mm" для отображения
            operator TEXT,
            attachment_path TEXT,
            attachment_name TEXT,
            attachment_size TEXT,
            is_image INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def seed_if_empty(self):
        # В "боевом" режиме сидинг тестовыми данными отключён
        if os.environ.get("SEED_TEST_DATA", "0") != "1":
            return
        cur = self.conn.cursor()
        cnt = cur.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
        if cnt:
            return
        # Первичная загрузка из TEST_CHATS
        for c in TEST_CHATS:
            cur.execute(
                "INSERT INTO chats (id,user_id,title,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (c["id"], c["user_id"], c["title"], c["status"],
                 c.get("created_at") or _now_dt_str(),
                 c.get("updated_at") or _now_dt_str())
            )
            for m in c.get("messages", []):
                cur.execute(
                    """INSERT INTO messages (chat_id,sender,text,time,operator,created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (c["id"], m.get("sender","user"), m.get("text"),
                     m.get("time") or _now_time_str(), m.get("operator"),
                     _now_ts())
                )
        self.conn.commit()

    def _chat_row_to_dict(self, row):
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": []
        }

    def _message_row_to_dict(self, row):
        if row["attachment_path"]:
            attach = {
                "path": row["attachment_path"],
                "name": row["attachment_name"],
                "size": row["attachment_size"],
                "is_image": bool(row["is_image"])
            }
            return {"sender": row["sender"], "attachment": attach, "time": row["time"]}
        msg = {"sender": row["sender"], "text": row["text"], "time": row["time"]}
        if row["operator"]:
            msg["operator"] = row["operator"]
        return msg

    def load_user_chats(self, user_id: str):
        cur = self.conn.cursor()
        chats = []
        for crow in cur.execute("SELECT * FROM chats WHERE user_id=? ORDER BY updated_at DESC", (user_id,)):
            chat = self._chat_row_to_dict(crow)
            mrows = cur.execute("SELECT * FROM messages WHERE chat_id=? ORDER BY id ASC", (crow["id"],)).fetchall()
            chat["messages"] = [self._message_row_to_dict(r) for r in mrows]
            chats.append(chat)
        return chats

    def get_chat(self, chat_id: str):
        cur = self.conn.cursor()
        crow = cur.execute("SELECT * FROM chats WHERE id=?", (chat_id,)).fetchone()
        if not crow:
            return None
        chat = self._chat_row_to_dict(crow)
        mrows = cur.execute("SELECT * FROM messages WHERE chat_id=? ORDER BY id ASC", (chat_id,)).fetchall()
        chat["messages"] = [self._message_row_to_dict(r) for r in mrows]
        return chat

    def _next_chat_id(self):
        cur = self.conn.cursor()
        row = cur.execute("SELECT MAX(CAST(SUBSTR(id,4) AS INTEGER)) FROM chats WHERE id LIKE 'CH-%'").fetchone()
        n = row[0] or 0
        return f"CH-{n+1:04d}"

    def create_chat(self, user_id: str, title: str):
        chat_id = self._next_chat_id()
        now_dt = _now_dt_str()
        cur = self.conn.cursor()
        cur.execute("INSERT INTO chats (id,user_id,title,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                    (chat_id, user_id, (title or "Новая заявка"), "Новая", now_dt, now_dt))
        # Приветствие оператора
        op = random.choice(OPERATORS)
        cur.execute(
            """INSERT INTO messages (chat_id,sender,text,time,operator,created_at)
               VALUES (?,?,?,?,?,?)""",
            (chat_id, "operator", "Здравствуйте! Чем можем помочь?", _now_time_str(), op, _now_ts())
        )
        self.conn.commit()
        return self.get_chat(chat_id)

    def add_message(self, chat_id: str, sender: str, text: str = None, operator: str = None,
                    attachment: dict = None, time_str: str = None):
        cur = self.conn.cursor()
        t = time_str or _now_time_str()
        if attachment:
            cur.execute(
                """INSERT INTO messages
                   (chat_id,sender,time,operator,attachment_path,attachment_name,attachment_size,is_image,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (chat_id, sender, t, operator,
                 attachment.get("path"), attachment.get("name"), attachment.get("size"),
                 1 if attachment.get("is_image") else 0, _now_ts())
            )
        else:
            cur.execute(
                """INSERT INTO messages (chat_id,sender,text,time,operator,created_at)
                   VALUES (?,?,?,?,?,?)""",
                (chat_id, sender, text, t, operator, _now_ts())
            )
        cur.execute("UPDATE chats SET updated_at=? WHERE id=?", (_now_dt_str(), chat_id))
        self.conn.commit()

    def update_chat_status(self, chat_id: str, status: str):
        cur = self.conn.cursor()
        cur.execute("UPDATE chats SET status=?, updated_at=? WHERE id=?", (status, _now_dt_str(), chat_id))
        self.conn.commit()

    def rename_chat(self, chat_id: str, title: str):
        cur = self.conn.cursor()
        cur.execute("UPDATE chats SET title=?, updated_at=? WHERE id=?", (title, _now_dt_str(), chat_id))
        self.conn.commit()

    def delete_chat(self, chat_id: str):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM chats WHERE id=?", (chat_id,))
        self.conn.commit()

# Глобальный экземпляр
repo = SQLiteRepo()
