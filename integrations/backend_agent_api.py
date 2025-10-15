import os
import requests

# DEFAULT_BASE = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1/api/v1")
DEFAULT_BASE = os.environ.get("BACKEND_BASE_URL", "http://89.104.67.225/api/v1")

class BackendAgentAPI:
    def __init__(self, base_url: str = None):
        self.base = (base_url or DEFAULT_BASE).rstrip("/")

        self._jwt = None  # access token для WS

    def start_chat(self, instance_uid: str, crm_client_fio: str, title: str, message: str = "", files: list[str] | None = None):
        url = f"{self.base}/clients/start-chat/"
        data = {
            "instance_uid": instance_uid,
            "crm_client_fio": crm_client_fio,  # это ФИО клиента из CRM
            "title": title,
            "message": message or title,
        }
        files_arg = []
        fobjs = []
        for p in files or []:
            f = open(p, "rb")
            fobjs.append(f)
            files_arg.append(("files", (os.path.basename(p), f, "application/octet-stream")))
        try:
            resp = requests.post(url, data=data, files=files_arg or None, timeout=15)
            return resp.status_code, (resp.json() if resp.content else {})
        except Exception as e:
            return 0, {"error": str(e)}
        finally:
            for f in fobjs:
                try:
                    f.close()
                except Exception:
                    pass

    def send_message(self, room_id: str | int, instance_uid: str, message: str = "", files: list[str] | None = None):
        url = f"{self.base}/clients/rooms/{room_id}/send/"
        data = {"instance_uid": instance_uid, "message": message or ""}
        files_arg = []
        fobjs = []
        for p in files or []:
            f = open(p, "rb")
            fobjs.append(f)
            files_arg.append(("files", (os.path.basename(p), f, "application/octet-stream")))
        try:
            resp = requests.post(url, data=data, files=files_arg or None, timeout=15)
            return resp.status_code, (resp.json() if resp.content else {})
        except Exception as e:
            return 0, {"error": str(e)}
        finally:
            for f in fobjs:
                try:
                    f.close()
                except Exception:
                    pass

    def login(self, username: str, password: str):
        url = f"{self.base}/auth/login"
        try:
            resp = requests.post(url, json={"username": username, "password": password}, timeout=10)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                self._jwt = data.get("access")
            return resp.status_code, data
        except Exception as e:
            return 0, {"error": str(e)}

    def send_files(self, room_id: str | int, instance_uid: str, files: list[str]):
        url = f"{self.base}/clients/rooms/{room_id}/files/"
        data = {"instance_uid": instance_uid}
        files_arg, fobjs = [], []
        for p in files or []:
            f = open(p, "rb")
            fobjs.append(f)
            files_arg.append(("files", (os.path.basename(p), f, "application/octet-stream")))
        try:
            resp = requests.post(url, data=data, files=files_arg or None, timeout=30)
            return resp.status_code, (resp.json() if resp.content else {})
        except Exception as e:
            return 0, {"error": str(e)}
        finally:
            for f in fobjs:
                try:
                    f.close()
                except Exception:
                    pass

    def login_client_instance(self, instance: str):
        """Логин клиента по instance (get_or_create на бэке). Возвращает JWT."""
        url = f"{self.base}/clients/auth/login"
        try:
            resp = requests.post(url, json={"instance": str(instance)}, timeout=10)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                self._jwt = data.get("access")
            return resp.status_code, data
        except Exception as e:
            return 0, {"error": str(e)}

    def fx_login(self, fx_id: str, operator_id: str):
        url = f"{self.base}/clients/auth/fx-login"
        try:
            resp = requests.post(url, json={"fx_id": fx_id, "operator_id": operator_id}, timeout=10)
            data = resp.json() if resp.content else {}
            if 200 <= resp.status_code < 300:
                self._jwt = data.get("access")
            return resp.status_code, data
        except Exception as e:
            return 0, {"error": str(e)}

    def client_leave(self, room_id: str | int, instance_uid: str):
        url = f"{self.base}/clients/rooms/{room_id}/leave/"
        data = {"instance_uid": instance_uid}
        try:
            resp = requests.post(url, data=data, timeout=10)
            return resp.status_code, (resp.json() if resp.content else {})
        except Exception as e:
            return 0, {"error": str(e)}
