import json
import os
import tempfile
from datetime import datetime
from threading import Lock

_DB_DIR = os.environ.get("ROBO_DB_DIR") or os.environ.get("STREAMLIT_TMP_PATH") or tempfile.gettempdir()
_DB_DIR = os.path.join(_DB_DIR, "robo-advisor-data")
_DB_PATH = os.path.join(_DB_DIR, "data.json")
_WRITE_LOCK = Lock()

BETA_MAX = 1000

def _read():
    try:
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": [], "sessions": {}, "chats": {}}

def _write(data):
    os.makedirs(_DB_DIR, exist_ok=True)
    with _WRITE_LOCK:
        with open(_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def _next_id(users):
    return max((u["id"] for u in users), default=0) + 1

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def count_users():
    data = _read()
    return len(data["users"])

def register_beta_user(username, password=""):
    data = _read()
    users = data["users"]
    if len(users) >= BETA_MAX:
        return False, 0
    if any(u["username"] == username for u in users):
        return False, len(users) + 1
    slot = len(users) + 1
    users.append({
        "id": _next_id(users),
        "username": username,
        "beta_slot": slot,
        "created_at": _now()
    })
    data["sessions"].setdefault(username, {})["password"] = password
    _write(data)
    return True, slot

def verify_user(username, password):
    data = _read()
    pw = data.get("sessions", {}).get(username, {}).get("password")
    return pw == password

def is_founding_member(username):
    data = _read()
    for u in data["users"]:
        if u["username"] == username:
            slot = u.get("beta_slot")
            return slot is not None and 1 <= slot <= BETA_MAX
    return False

def get_beta_progress():
    data = _read()
    return len(data["users"]), BETA_MAX

def save_state(username, data_dict):
    data = _read()
    sessions = data["sessions"].setdefault(username, {})
    for k, v in data_dict.items():
        sessions[k] = v
    _write(data)

def load_state(username):
    data = _read()
    return dict(data.get("sessions", {}).get(username, {}))

def save_chat(username, role, content):
    data = _read()
    chats = data["chats"].setdefault(username, [])
    chats.append({"role": role, "content": content, "time": _now()})
    _write(data)

def load_chat(username, limit=50):
    data = _read()
    chats = data.get("chats", {}).get(username, [])
    return list(reversed(chats[-limit:]))

def ensure_user(username):
    data = _read()
    if not any(u["username"] == username for u in data["users"]):
        data["users"].append({
            "id": _next_id(data["users"]),
            "username": username,
            "created_at": _now()
        })
        _write(data)

def reset_password(username, new_password):
    data = _read()
    if not any(u["username"] == username for u in data["users"]):
        return False
    data["sessions"].setdefault(username, {})["password"] = new_password
    _write(data)
    return True

try:
    os.makedirs(_DB_DIR, exist_ok=True)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning("DB dir create failed: %s", e)

def _seed_default_user():
    try:
        data = _read()
        username = "SÓI CÔ ĐỘC"
        password = "MiWzF5e9LyhXE8S"
        if not any(u["username"] == username for u in data["users"]):
            slot = len(data["users"]) + 1
            data["users"].append({
                "id": _next_id(data["users"]),
                "username": username,
                "beta_slot": slot if slot <= BETA_MAX else None,
                "created_at": _now()
            })
        data["sessions"].setdefault(username, {})["password"] = password
        _write(data)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Default user seed failed: %s", e)

_seed_default_user()
