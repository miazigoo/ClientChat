import os
from dataclasses import dataclass

@dataclass
class AgentIDs:
    instance_id: str
    operator_id: str

def read_agent_ids(path: str = None) -> AgentIDs:
    # По умолчанию ./agent/agent_ids.txt
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "agent_ids.txt")
    inst = None
    oper = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.lower().startswith("instance="):
                    inst = line.split("=", 1)[1].strip()
                elif line.lower().startswith("operator="):
                    oper = line.split("=", 1)[1].strip()
    except Exception:
        pass
    # Фоллбек для dev
    inst = inst or "INST-LOCAL-DEV"
    oper = oper or "OPER-LOCAL-DEV"
    return AgentIDs(inst, oper)