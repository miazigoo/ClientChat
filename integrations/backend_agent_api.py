import os
import requests

DEFAULT_BASE = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1/api/v1")

class BackendAgentAPI:
    def __init__(self, base_url: str = None):
        self.base = (base_url or DEFAULT_BASE).rstrip("/")

    def start_chat(self, instance_uid: str, crm_operator_fio: str, title: str, message: str = "", files: list[str] | None = None):
        url = f"{self.base}/agent/start-chat/"
        data = {
            "instance_uid": instance_uid,
            "crm_operator_fio": crm_operator_fio,
            "title": title,
            "message": message or title,
        }
        files_arg = []
        for p in files or []:
            files_arg.append(("files", (os.path.basename(p), open(p, "rb"), "application/octet-stream")))
        try:
            resp = requests.post(url, data=data, files=files_arg or None, timeout=15)
            return resp.status_code, (resp.json() if resp.content else {})
        except Exception as e:
            return 0, {"error": str(e)}

    def send_message(self, room_id: str | int, instance_uid: str, message: str = "", files: list[str] | None = None):
        url = f"{self.base}/agent/rooms/{room_id}/send/"
        data = {"instance_uid": instance_uid, "message": message or ""}
        files_arg = []
        for p in files or []:
            files_arg.append(("files", (os.path.basename(p), open(p, "rb"), "application/octet-stream")))
        try:
            resp = requests.post(url, data=data, files=files_arg or None, timeout=15)
            return resp.status_code, (resp.json() if resp.content else {})
        except Exception as e:
            return 0, {"error": str(e)}