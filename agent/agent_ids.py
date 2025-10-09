import os
from dataclasses import dataclass
import json

@dataclass
class AgentIDs:
    instance_id: str
    operator_id: str

def read_agent_ids(path: str = None) -> AgentIDs:
    # По умолчанию ./agent/agent_ids.json
    inst = None
    oper = None
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "agent_ids.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)  # { "Client_1": {"instance": 3442, "operator": "..."}, ... }
            # Можно выбрать запись по переменной окружения CLIENT_KEY, иначе берем первую
        key = os.environ.get("CLIENT_KEY")
        item = None
        if key and key in data:
            item = data[key]
        else:
            # первая попавшаяся
            first_key = next(iter(data.keys()))
            item = data[first_key]
        inst = str(item.get("instance"))
        oper = str(item.get("operator") or "")
    except Exception:
        pass
    # Фоллбек для dev
    inst = inst or "INST-LOCAL-DEV"
    oper = oper or "OPER-LOCAL-DEV"
    return AgentIDs(inst, oper)